# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))

import vao05  # noqa: E402


class VAO05Tests(unittest.TestCase):
    def test_schemas_are_valid_draft_2020_12(self) -> None:
        schemas = sorted((ROOT / "Schemas").glob("*0.5.0.schema.json"))
        self.assertEqual(6, len(schemas))
        for path in schemas:
            Draft202012Validator.check_schema(
                json.loads(path.read_text(encoding="utf-8"))
            )

    def test_fixtures_and_companions(self) -> None:
        for path in (
            ROOT / "Fixtures/VAO05/workspaces/minimal",
            ROOT / "Fixtures/VAO05/carriers/minimal.vao",
            ROOT
            / "Fixtures/VAO05/descriptors/kinoorgel-multimodal-scientific.example.json",
            ROOT / "Fixtures/VAO05/descriptors/cuntz-positiv-acoustic.example.json",
        ):
            report = vao05.validate(path)
            self.assertTrue(report["valid"], (path, report["errors"]))

        companions = ROOT / "Fixtures/VAO05/companions"
        release_report = vao05.validate_release_manifest_set(
            companions / "release.example.json",
            ROOT / "Fixtures/VAO05/workspaces/minimal/vao-manifest.json",
        )
        self.assertTrue(release_report["valid"], release_report["errors"])
        carrier_report = vao05.validate_release_carrier_set(
            companions / "release.example.json",
            ROOT / "Fixtures/VAO05/workspaces/minimal/vao-manifest.json",
            [ROOT / "Fixtures/VAO05/carriers/minimal.vao"],
        )
        self.assertTrue(carrier_report["valid"], carrier_report["errors"])

    def test_carrier_member_resolves_through_release_descriptor(self) -> None:
        workspace = ROOT / "Fixtures/VAO05/workspaces/minimal"
        release_fixture = ROOT / "Fixtures/VAO05/companions/release.example.json"
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = json.loads(
                (workspace / vao05.MANIFEST_NAME).read_text(encoding="utf-8")
            )
            release = json.loads(release_fixture.read_text(encoding="utf-8"))
            record = release["publication"]["rootRecord"]
            record["repositoryType"] = "https://example.org/repository/test"
            record["instance"] = "https://example.org/repository"
            carrier = next(
                item for item in record["files"] if item["role"] == "carrier"
            )
            binding_id = "urn:uuid:05000000-0000-4000-8000-000000000001"
            distribution_id = "urn:uuid:05000000-0000-4000-8000-000000000002"
            manifest["repositoryBindings"].append(
                {
                    "id": binding_id,
                    "repositoryType": record["repositoryType"],
                    "instance": record["instance"],
                    "apiProfile": "https://example.org/repository/api/v1",
                    "resolutionPolicy": "version-pid-record-file",
                }
            )
            manifest["distributions"].append(
                {
                    "id": distribution_id,
                    "kind": "carrier-member",
                    "carrierId": carrier["carrierId"],
                    "repositoryBindingId": binding_id,
                    "persistentIdentifier": record["versionPersistentIdentifier"],
                    "conceptIdentifier": record["conceptPersistentIdentifier"],
                    "recordIdentifier": record["recordIdentifier"],
                    "fileIdentifier": carrier["fileIdentifier"],
                    "access": "public",
                }
            )
            manifest["realizations"][0]["distributionIds"] = [distribution_id]
            manifest_bytes = vao05.json_bytes(manifest)
            manifest_path = directory / "vao-manifest.json"
            manifest_path.write_bytes(manifest_bytes)
            manifest_file = next(
                item for item in record["files"] if item["role"] == "manifest"
            )
            manifest_file["byteSize"] = len(manifest_bytes)
            manifest_file["sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
            release_path = directory / "vao-release.json"
            release_path.write_bytes(vao05.json_bytes(release))

            report = vao05.validate_release_manifest_set(release_path, manifest_path)
            self.assertTrue(report["valid"], report["errors"])

            manifest["distributions"][0]["carrierId"] = (
                "urn:uuid:05000000-0000-4000-8000-000000000099"
            )
            manifest_bytes = vao05.json_bytes(manifest)
            manifest_path.write_bytes(manifest_bytes)
            manifest_file["byteSize"] = len(manifest_bytes)
            manifest_file["sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
            release_path.write_bytes(vao05.json_bytes(release))
            report = vao05.validate_release_manifest_set(release_path, manifest_path)
            self.assertFalse(report["valid"])
            self.assertIn(
                "does not resolve to a carrier file", "\n".join(report["errors"])
            )

    def test_release_rejects_duplicate_carrier_ids(self) -> None:
        release = json.loads(
            (ROOT / "Fixtures/VAO05/companions/release.example.json").read_text(
                encoding="utf-8"
            )
        )
        record = release["publication"]["rootRecord"]
        carrier = next(item for item in record["files"] if item["role"] == "carrier")
        duplicate = copy.deepcopy(carrier)
        duplicate["fileIdentifier"] = "duplicate.vao"
        record["files"].append(duplicate)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vao-release.json"
            path.write_bytes(vao05.json_bytes(release))
            report = vao05.validate_release_descriptor(path)
        self.assertFalse(report["valid"])
        self.assertIn("assigned to both", "\n".join(report["errors"]))

    def test_reference_writer_is_byte_deterministic(self) -> None:
        workspace = ROOT / "Fixtures/VAO05/workspaces/minimal"
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.vao"
            second = Path(temporary) / "second.vao"
            vao05.pack_workspace(workspace, first)
            vao05.pack_workspace(workspace, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first.read_bytes(),
                (ROOT / "Fixtures/VAO05/carriers/minimal.vao").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
