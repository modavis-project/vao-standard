# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import json
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import warnings

from jsonschema import Draft202012Validator
from rdflib import Dataset, URIRef
from rdflib.namespace import DCTERMS, RDF
from pyshacl import validate as shacl_validate


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))

import generate_schema_reference  # noqa: E402
import update_release_bundle  # noqa: E402
import vao04  # noqa: E402
import vao04_rdf  # noqa: E402


class ReleaseTests(unittest.TestCase):
    def test_all_04_schemas_are_valid_draft_2020_12(self) -> None:
        schemas = sorted((ROOT / "Schemas").glob("*0.4.0.schema.json"))
        self.assertEqual(6, len(schemas))
        for path in schemas:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

    def test_all_integer_subschemas_enforce_interoperable_bounds(self) -> None:
        safe = (1 << 53) - 1
        integer_locations: list[str] = []

        def walk(value: object, location: str) -> None:
            if isinstance(value, dict):
                if value.get("type") == "integer":
                    integer_locations.append(location)
                    self.assertGreaterEqual(value.get("minimum", -safe - 1), -safe)
                    self.assertLessEqual(value.get("maximum", safe + 1), safe)
                for key, child in value.items():
                    walk(child, f"{location}/{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{location}/{index}")

        for path in sorted((ROOT / "Schemas").glob("*0.4.0.schema.json")):
            walk(json.loads(path.read_text(encoding="utf-8")), path.name)
        self.assertGreater(len(integer_locations), 70)

    def test_complex_descriptor(self) -> None:
        fixture = (
            ROOT
            / "Fixtures/VAO04/descriptors/kinoorgel-multimodal-scientific.example.json"
        )
        report = vao04.validate(fixture)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual("0.4.0", report["formatVersion"])
        manifest = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(
            vao04.reference_software_environment("urn:vao:software:vao04-reference"),
            manifest["scientific"]["softwareEnvironments"][0],
        )

    def test_companion_descriptors_and_publication_set(self) -> None:
        directory = ROOT / "Fixtures/VAO04/companions"
        validators = {
            "release.example.json": vao04.validate_release_descriptor,
            "pack-manifest.example.json": lambda path: vao04.validate_descriptor(
                path, vao04.PACK_SCHEMA, vao04.pack_semantic_errors
            ),
            "materialization-receipt.example.json": lambda path: (
                vao04.validate_descriptor(
                    path, vao04.RECEIPT_SCHEMA, vao04.receipt_semantic_errors
                )
            ),
            "materialization-receipt-minimal.example.json": lambda path: (
                vao04.validate_descriptor(
                    path, vao04.RECEIPT_SCHEMA, vao04.receipt_semantic_errors
                )
            ),
            "zenodo-metadata-legacy.example.json": (
                vao04.validate_zenodo_metadata_descriptor
            ),
        }
        for name, validator in validators.items():
            report = validator(directory / name)
            self.assertTrue(report["valid"], (name, report["errors"]))
        publication = vao04.validate_publication_set(
            directory / "release.example.json",
            [directory / "zenodo-metadata-legacy.example.json"],
        )
        self.assertTrue(publication["valid"], publication["errors"])

        manifest = ROOT / "Fixtures/VAO04/workspaces/minimal/vao-manifest.json"
        carrier = ROOT / "Fixtures/VAO04/carriers/minimal.vao"
        cross_reports = (
            vao04.validate_release_manifest_set(
                directory / "release.example.json", manifest
            ),
            vao04.validate_pack_manifest_set(
                directory / "pack-manifest.example.json", manifest
            ),
            vao04.validate_receipt_manifest_set(
                directory / "materialization-receipt-minimal.example.json",
                manifest,
                carrier,
            ),
        )
        for report in cross_reports:
            self.assertTrue(report["valid"], report["errors"])

        release = json.loads(
            (directory / "release.example.json").read_text(encoding="utf-8")
        )
        carrier_inventory = next(
            item
            for item in release["publication"]["rootRecord"]["files"]
            if item["role"] == "carrier"
        )
        carrier_data = carrier.read_bytes()
        self.assertEqual(len(carrier_data), carrier_inventory["byteSize"])
        self.assertEqual(
            hashlib.sha256(carrier_data).hexdigest(), carrier_inventory["sha256"]
        )

    def test_companion_semantics_reject_unsafe_or_ambiguous_records(self) -> None:
        directory = ROOT / "Fixtures/VAO04/companions"
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "descriptor.json"

            pack = json.loads(
                (directory / "pack-manifest.example.json").read_text(encoding="utf-8")
            )
            pack["members"][0]["byteSize"] = 1 << 53
            target.write_text(json.dumps(pack), encoding="utf-8")
            report = vao04.validate_descriptor(
                target, vao04.PACK_SCHEMA, vao04.pack_semantic_errors
            )
            self.assertFalse(report["valid"])
            self.assertIn("2^53-1", "\n".join(report["errors"]))

            release = json.loads(
                (directory / "release.example.json").read_text(encoding="utf-8")
            )
            duplicate = copy.deepcopy(release["publication"]["rootRecord"]["files"][0])
            duplicate["fileIdentifier"] = "payload/cafe\u0301.txt"
            release["publication"]["rootRecord"]["files"].extend(
                [
                    duplicate,
                    {
                        **duplicate,
                        "fileIdentifier": "payload/caf\u00e9.txt",
                        "sha256": "3" * 64,
                    },
                ]
            )
            target.write_text(json.dumps(release), encoding="utf-8")
            report = vao04.validate_release_descriptor(target)
            self.assertFalse(report["valid"])
            self.assertIn("NFC", "\n".join(report["errors"]))

            release = json.loads(
                (directory / "release.example.json").read_text(encoding="utf-8")
            )
            release["publication"]["rootRecord"]["files"].append(
                {
                    "fileIdentifier": "metadata/vao-release.json",
                    "role": "metadata",
                    "byteSize": 1,
                    "sha256": "5" * 64,
                }
            )
            target.write_text(json.dumps(release), encoding="utf-8")
            report = vao04.validate_release_descriptor(target)
            self.assertFalse(report["valid"])
            self.assertIn("self-inventory", "\n".join(report["errors"]))

            receipt = json.loads(
                (directory / "materialization-receipt.example.json").read_text(
                    encoding="utf-8"
                )
            )
            receipt["acquisitions"][0]["verifiedAt"] = "2026-08-27T12:00:01Z"
            target.write_text(json.dumps(receipt), encoding="utf-8")
            report = vao04.validate_descriptor(
                target, vao04.RECEIPT_SCHEMA, vao04.receipt_semantic_errors
            )
            self.assertFalse(report["valid"])
            self.assertIn("after receipt creation", "\n".join(report["errors"]))

            manifest = ROOT / "Fixtures/VAO04/workspaces/minimal/vao-manifest.json"
            carrier = ROOT / "Fixtures/VAO04/carriers/minimal.vao"

            release = json.loads(
                (directory / "release.example.json").read_text(encoding="utf-8")
            )
            release["releaseId"] = "urn:vao:release:contradiction"
            target.write_text(json.dumps(release), encoding="utf-8")
            report = vao04.validate_release_manifest_set(target, manifest)
            self.assertFalse(report["valid"])
            self.assertIn("releaseId", "\n".join(report["errors"]))

            pack = json.loads(
                (directory / "pack-manifest.example.json").read_text(encoding="utf-8")
            )
            pack["members"][0]["sha256"] = "6" * 64
            target.write_text(json.dumps(pack), encoding="utf-8")
            report = vao04.validate_pack_manifest_set(target, manifest)
            self.assertFalse(report["valid"])
            self.assertIn("exact realization", "\n".join(report["errors"]))

            receipt = json.loads(
                (directory / "materialization-receipt-minimal.example.json").read_text(
                    encoding="utf-8"
                )
            )
            receipt["sourceCarrier"]["packedCarrierSHA256"] = "7" * 64
            target.write_text(json.dumps(receipt), encoding="utf-8")
            report = vao04.validate_receipt_manifest_set(target, manifest, carrier)
            self.assertFalse(report["valid"])
            self.assertIn("exact carrier bytes", "\n".join(report["errors"]))

    def test_receipt_distribution_resolves_through_realization(self) -> None:
        fixture = ROOT / "Fixtures/VAO04/workspaces/minimal"
        receipt_fixture = (
            ROOT
            / "Fixtures/VAO04/companions/materialization-receipt-minimal.example.json"
        )
        binding_id = "urn:uuid:00000000-0000-4000-8000-000000000081"
        distribution_id = "urn:uuid:00000000-0000-4000-8000-000000000082"
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            workspace = temporary_path / "workspace"
            shutil.copytree(fixture, workspace)
            manifest_path = workspace / vao04.MANIFEST_NAME
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["repositoryBindings"].append(
                {
                    "id": binding_id,
                    "repositoryType": "https://example.org/repository/test",
                    "instance": "https://example.org/repository",
                    "apiProfile": "https://example.org/repository/api/v1",
                    "resolutionPolicy": "version-pid-record-file",
                }
            )
            manifest["distributions"].append(
                {
                    "id": distribution_id,
                    "kind": "repository",
                    "repositoryBindingId": binding_id,
                    "persistentIdentifier": "https://example.org/repository/records/123456",
                    "recordIdentifier": "123456",
                    "fileIdentifier": "source.txt",
                    "access": "public",
                }
            )
            realization = manifest["realizations"][0]
            realization["distributionIds"] = [distribution_id]
            manifest_data = vao04.json_bytes(manifest)
            manifest_path.write_bytes(manifest_data)

            carrier_path = workspace / vao04.CARRIER_NAME
            carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
            carrier["manifestByteSize"] = len(manifest_data)
            carrier["manifestSHA256"] = hashlib.sha256(manifest_data).hexdigest()
            carrier_data = vao04.json_bytes(carrier)
            carrier_path.write_bytes(carrier_data)
            packed = temporary_path / "source.vao"
            vao04.pack_workspace(workspace, packed)
            packed_data = packed.read_bytes()

            receipt = json.loads(receipt_fixture.read_text(encoding="utf-8"))
            receipt["manifestSHA256"] = hashlib.sha256(manifest_data).hexdigest()
            receipt["sourceCarrier"] = {
                "kind": "packed-carrier",
                "descriptorByteSize": len(carrier_data),
                "descriptorSHA256": hashlib.sha256(carrier_data).hexdigest(),
                "packedCarrierByteSize": len(packed_data),
                "packedCarrierSHA256": hashlib.sha256(packed_data).hexdigest(),
            }
            receipt["acquisitions"] = [
                {
                    "realizationId": realization["id"],
                    "distributionId": distribution_id,
                    "byteSize": realization["byteSize"],
                    "sha256": realization["sha256"],
                    "status": "verified",
                    "attemptedAt": "2026-08-27T11:59:58Z",
                    "verifiedAt": "2026-08-27T11:59:59Z",
                }
            ]
            receipt_path = temporary_path / "receipt.json"
            receipt_path.write_bytes(vao04.json_bytes(receipt))
            report = vao04.validate_receipt_manifest_set(
                receipt_path, manifest_path, packed
            )
            self.assertTrue(report["valid"], report["errors"])

            receipt["acquisitions"][0]["distributionId"] = (
                "urn:uuid:00000000-0000-4000-8000-000000000083"
            )
            receipt_path.write_bytes(vao04.json_bytes(receipt))
            report = vao04.validate_receipt_manifest_set(
                receipt_path, manifest_path, packed
            )
            self.assertFalse(report["valid"])
            self.assertIn("unknown distributionId", "\n".join(report["errors"]))

    def test_spatial_acoustics_descriptor(self) -> None:
        fixture = (
            ROOT / "Fixtures/VAO04/descriptors/cuntz-positiv-acoustic.example.json"
        )
        report = vao04.validate(fixture)
        self.assertTrue(report["valid"], report["errors"])
        manifest = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertTrue(manifest["acoustics"]["materialModels"])
        self.assertTrue(manifest["acoustics"]["measurements"])
        self.assertTrue(manifest["acoustics"]["metricSets"])
        self.assertTrue(manifest["acoustics"]["responseSets"])
        self.assertEqual(
            vao04.reference_software_environment("urn:vao:software:vao04-reference"),
            manifest["scientific"]["softwareEnvironments"][0],
        )

    def test_minimal_workspace_and_carrier(self) -> None:
        for path in (
            ROOT / "Fixtures/VAO04/workspaces/minimal",
            ROOT / "Fixtures/VAO04/carriers/minimal.vao",
        ):
            report = vao04.validate(path)
            self.assertTrue(report["valid"], report["errors"])
            self.assertEqual(69, report["verifiedBytes"])
        manifest = json.loads(
            (ROOT / "Fixtures/VAO04/workspaces/minimal/vao-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            vao04.reference_software_environment("urn:vao:software:vao04-reference"),
            manifest["scientific"]["softwareEnvironments"][0],
        )

    def test_reference_writer_is_byte_deterministic(self) -> None:
        workspace = ROOT / "Fixtures/VAO04/workspaces/minimal"
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.vao"
            second = Path(temporary) / "second.vao"
            vao04.pack_workspace(workspace, first)
            vao04.pack_workspace(workspace, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first.read_bytes(),
                (ROOT / "Fixtures/VAO04/carriers/minimal.vao").read_bytes(),
            )

    def test_generated_schema_reference_is_current(self) -> None:
        schema = json.loads(
            generate_schema_reference.DEFAULT_SCHEMA.read_text(encoding="utf-8")
        )
        actual = generate_schema_reference.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(generate_schema_reference.generate(schema), actual)

    def test_normative_release_bundle_is_current(self) -> None:
        expected = update_release_bundle.encoded(update_release_bundle.build())
        self.assertEqual(expected, update_release_bundle.OUTPUT.read_bytes())

    def test_linked_data_projection_parses_and_conforms(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "Fixtures/VAO04/descriptors/kinoorgel-multimodal-scientific.example.json"
            ).read_text(encoding="utf-8")
        )
        manifest["extensions"] = {
            "https://example.org/vao/test-extension": {
                "vao:jsonPointer": "extension-owned value"
            },
        }
        annotated = vao04_rdf.project_jsonld(manifest)
        self.assertEqual(manifest, vao04_rdf.inverse_projection(annotated))
        projected = vao04_rdf.project_offline_jsonld(manifest)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            graph = Dataset().parse(data=json.dumps(projected), format="json-ld")
            self.assertGreater(len(graph), 500)
            conforms, _, report = shacl_validate(
                graph,
                shacl_graph=str(ROOT / "Schemas/vao-shapes-0.4.0.ttl"),
                ont_graph=str(ROOT / "Schemas/vao-vocabulary-0.4.0.ttl"),
                inference="rdfs",
            )
            self.assertTrue(conforms, report)
            vao_class = URIRef(
                "https://w3id.org/modavis/vao/ontology#VirtualAcousticObject"
            )
            self.assertEqual(
                {URIRef(manifest["id"])}, set(graph.subjects(RDF.type, vao_class))
            )
            graph.remove((URIRef(manifest["id"]), DCTERMS.conformsTo, None))
            negative, _, _ = shacl_validate(
                graph,
                shacl_graph=str(ROOT / "Schemas/vao-shapes-0.4.0.ttl"),
                ont_graph=str(ROOT / "Schemas/vao-vocabulary-0.4.0.ttl"),
                inference="rdfs",
            )
            self.assertFalse(negative)

    def test_acoustic_linked_data_projection_conforms(self) -> None:
        manifest = json.loads(
            (
                ROOT / "Fixtures/VAO04/descriptors/cuntz-positiv-acoustic.example.json"
            ).read_text(encoding="utf-8")
        )
        annotated = vao04_rdf.project_jsonld(manifest)
        self.assertEqual(manifest, vao04_rdf.inverse_projection(annotated))
        projected = vao04_rdf.project_offline_jsonld(manifest)
        graph = Dataset().parse(data=json.dumps(projected), format="json-ld")
        conforms, _, report = shacl_validate(
            graph,
            shacl_graph=str(ROOT / "Schemas/vao-shapes-0.4.0.ttl"),
            ont_graph=str(ROOT / "Schemas/vao-vocabulary-0.4.0.ttl"),
            inference="rdfs",
        )
        self.assertTrue(conforms, report)

        vao = "https://w3id.org/modavis/vao/ontology#"
        acoustic_sets = list(graph.subjects(RDF.type, URIRef(vao + "AcousticModelSet")))
        self.assertEqual(1, len(acoustic_sets))
        graph.remove((acoustic_sets[0], URIRef(vao + "coordinateFrame"), None))
        negative, _, _ = shacl_validate(
            graph,
            shacl_graph=str(ROOT / "Schemas/vao-shapes-0.4.0.ttl"),
            ont_graph=str(ROOT / "Schemas/vao-vocabulary-0.4.0.ttl"),
            inference="rdfs",
        )
        self.assertFalse(negative)

    def test_offline_projection_refuses_unpinned_additional_context(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "Fixtures/VAO04/descriptors/kinoorgel-multimodal-scientific.example.json"
            ).read_text(encoding="utf-8")
        )
        manifest["@context"].append("https://example.org/unpinned-context.jsonld")
        self.assertTrue(vao04.validate_manifest(manifest)["valid"])
        with self.assertRaises(ValueError):
            vao04_rdf.project_offline_jsonld(manifest)

    def test_migration_preserves_original_manifest_digest(self) -> None:
        source = ROOT / "Fixtures/VAO03/valid/embedded-private"
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "migrated"
            vao04.migrate_03_workspace(source, destination)
            report = vao04.validate(destination)
            self.assertTrue(report["valid"], report["errors"])
            manifest = json.loads(
                (destination / "vao-manifest.json").read_text(encoding="utf-8")
            )
            expected = vao04.sha256_bytes((source / "vao-manifest.json").read_bytes())
            self.assertEqual(
                expected, manifest["release"]["migratedFromManifestSHA256"]
            )
            self.assertEqual(
                vao04.reference_software_environment(
                    "urn:vao:software:vao04-reference"
                ),
                manifest["scientific"]["softwareEnvironments"][0],
            )

    def test_parsed_migration_requires_original_byte_digest(self) -> None:
        source_path = ROOT / "Fixtures/VAO03/valid/embedded-private/vao-manifest.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        with self.assertRaises(vao04.VAO04Error):
            vao04.migrate_03_manifest(source, "not-an-original-byte-sha256")

    def test_migration_resolves_only_unambiguous_exact_trajectory(self) -> None:
        source_path = ROOT / "Fixtures/VAO03/valid/embedded-private/vao-manifest.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        asset_id = source["logicalAssets"][0]["id"]
        realization_id = source["realizations"][0]["id"]
        source["realizations"][0]["technicalMetadata"] = {"kind": "trajectory"}
        source["acoustics"] = {
            "poses": [
                {
                    "id": "urn:vao:test:pose:legacy-trajectory",
                    "trajectoryAssetId": asset_id,
                }
            ],
            "renderConfigurations": [],
        }
        migrated = vao04.migrate_03_manifest(source, "0" * 64)
        pose = migrated["acoustics"]["poses"][0]
        self.assertNotIn("trajectoryAssetId", pose)
        self.assertEqual(realization_id, pose["trajectoryRealizationId"])

        ambiguous = copy.deepcopy(source)
        duplicate = copy.deepcopy(ambiguous["realizations"][0])
        duplicate["id"] = "urn:vao:test:realization:second-trajectory"
        ambiguous["realizations"].append(duplicate)
        with self.assertRaisesRegex(vao04.VAO04Error, "curator selection"):
            vao04.migrate_03_manifest(ambiguous, "0" * 64)

        oriented = copy.deepcopy(source)
        oriented["acoustics"]["poses"][0]["orientationXYZW"] = [0, 0, 0, 1]
        with self.assertRaisesRegex(vao04.VAO04Error, "local Coordinate Frame"):
            vao04.migrate_03_manifest(oriented, "0" * 64)

    def test_embedded_chunk_and_merkle_verification(self) -> None:
        source = ROOT / "Fixtures/VAO04/workspaces/minimal"
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(source, workspace)
            manifest_path = workspace / vao04.MANIFEST_NAME
            carrier_path = workspace / vao04.CARRIER_NAME
            payload = (workspace / "payload/evidence/source.txt").read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            chunks = [
                {
                    "index": 0,
                    "offset": 0,
                    "length": len(payload),
                    "digest": {"algorithm": "sha256", "value": digest},
                }
            ]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["realizations"][0]["chunking"] = {
                "strategy": "fixed-size",
                "chunkSize": len(payload),
                "merkleRoot": {
                    "algorithm": "sha256",
                    "value": vao04.merkle_root(chunks, "sha256"),
                },
                "chunks": chunks,
            }
            data = vao04.json_bytes(manifest)
            carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
            carrier["manifestSHA256"] = hashlib.sha256(data).hexdigest()
            carrier["manifestByteSize"] = len(data)
            manifest_path.write_bytes(data)
            carrier_path.write_bytes(vao04.json_bytes(carrier))
            self.assertTrue(vao04.validate_workspace(workspace)["valid"])

            manifest["realizations"][0]["chunking"]["chunks"][0]["digest"]["value"] = (
                "0" * 64
            )
            manifest["realizations"][0]["chunking"]["merkleRoot"]["value"] = (
                vao04.merkle_root(
                    manifest["realizations"][0]["chunking"]["chunks"],
                    "sha256",
                )
            )
            data = vao04.json_bytes(manifest)
            carrier["manifestSHA256"] = hashlib.sha256(data).hexdigest()
            carrier["manifestByteSize"] = len(data)
            manifest_path.write_bytes(data)
            carrier_path.write_bytes(vao04.json_bytes(carrier))
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn("chunk 0 fails", "\n".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
