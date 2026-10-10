# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from jsonschema import Draft202012Validator
from rdflib import Graph, Literal
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))
import build_mmic_fixtures as fixtures  # noqa: E402
import build_mmic_schema  # noqa: E402
import mmic  # noqa: E402
import mmic_rdf  # noqa: E402
import migrate_vao05  # noqa: E402
import vao  # noqa: E402
import vao05  # noqa: E402
import vao06  # noqa: E402
import vao06_rdf  # noqa: E402

FIXTURES = ROOT / "Fixtures/MMIC" / mmic.VERSION


def bundle(name="roll"):
    folder = FIXTURES / name / "preservation-closure"
    manifest = json.loads((folder / "vao-manifest.json").read_text())
    carrier = json.loads((folder / "META-INF/vao-carrier.json").read_text())
    assets = {
        x["realizationId"]: (folder / x["path"]).read_bytes()
        for x in carrier["embeddedRealizations"]
    }
    data = mmic.strict_json(
        assets[manifest["extensions"][mmic.PROFILE]["semanticRealizationId"]]
    )
    return data, manifest, assets


def repin(data):
    for model in data["models"]:
        model["specSHA256"] = mmic.model_digest(model)
        for interpretation in data["interpretations"]:
            if interpretation["modelId"] == model["id"]:
                interpretation["modelSHA256"] = model["specSHA256"]
                interpretation["execution"]["modelSHA256"] = model["specSHA256"]
        for design in data["designs"]:
            if design["modelId"] == model["id"]:
                design["execution"]["modelSHA256"] = model["specSHA256"]


def replace(value, old, new):
    if isinstance(value, dict):
        return {k: replace(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [replace(v, old, new) for v in value]
    return new if value == old else value


def pin_sidecar(data, manifest, assets):
    rid = manifest["extensions"][mmic.PROFILE]["semanticRealizationId"]
    assets[rid] = vao06.json_bytes(data)
    realization = next(r for r in manifest["realizations"] if r["id"] == rid)
    realization.update(sha256=mmic.digest(assets[rid]), byteSize=len(assets[rid]))
    manifest["extensions"][mmic.PROFILE]["semanticSHA256"] = realization["sha256"]


def fixed_negative_archive(data, manifest, assets, output, label):
    """Create a newly identified, core-fixed adversarial carrier without validating its domain."""
    old_activity = manifest["scientific"]["activities"][0]["id"]
    activity = fixtures.uid(label + "/construction")
    manifest = replace(manifest, old_activity, activity)
    data = replace(data, old_activity, activity)
    data["id"] = fixtures.uid(label + "/domain")
    for registry in ("models", "states", "interpretations"):
        for old in [r["id"] for r in data[registry]]:
            data = replace(data, old, fixtures.uid(label + "/" + old))
    old_env = manifest["scientific"]["softwareEnvironments"][0]["id"]
    manifest = replace(manifest, old_env, fixtures.uid(label + "/environment"))
    manifest["scientific"]["softwareEnvironments"][0].update(
        name="Adversarial MMIC carrier constructor",
        identity={
            "algorithm": "sha256",
            "value": mmic.digest(Path(__file__).read_bytes()),
        },
        identityDescription="Exact tests/test_mmic.py bytes",
    )
    manifest = replace(manifest, manifest["id"], fixtures.uid(label + "/manifest"))
    manifest["release"]["id"] = fixtures.uid(label + "/release")
    old = manifest["extensions"][mmic.PROFILE]["semanticRealizationId"]
    raw = vao06.json_bytes(data)
    new = fixtures.uid(label + "/semantic/" + mmic.digest(raw))
    manifest = replace(manifest, old, new)
    assets[new] = raw
    assets.pop(old)
    pin_sidecar(data, manifest, assets)
    for group in manifest["assetGroups"]:
        group["totalByteSize"] = sum(
            len(assets[rid]) for rid in group["realizationIds"]
        )
    encoded = vao06.json_bytes(manifest)
    carrier = {
        "$schema": vao06.BASE + "/schema/carrier.json",
        "formatVersion": vao06.FORMAT_VERSION,
        "type": "VAOCarrier",
        "id": fixtures.uid(label + "/carrier"),
        "releaseId": manifest["release"]["id"],
        "carrierMode": "preservation-closure",
        "manifestByteSize": len(encoded),
        "manifestSHA256": mmic.digest(encoded),
        "embeddedRealizations": [
            {"realizationId": rid, "path": f"payload/asset-{i}"}
            for i, rid in enumerate(assets)
        ],
        "completeGroupIds": [g["id"] for g in manifest["assetGroups"]],
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(vao06.vao03.zip_info("mimetype"), vao06.MIMETYPE.encode())
        archive.writestr(vao06.vao03.zip_info("vao-manifest.json"), encoded)
        archive.writestr(
            vao06.vao03.zip_info(vao06.CARRIER_NAME), vao06.json_bytes(carrier)
        )
        for mapping in carrier["embeddedRealizations"]:
            archive.writestr(
                vao06.vao03.zip_info(mapping["path"]), assets[mapping["realizationId"]]
            )


class MMICConformanceTests(unittest.TestCase):
    def test_schema_and_local_dependency_closure(self):
        schema = build_mmic_schema.build()
        Draft202012Validator.check_schema(schema)
        self.assertEqual(
            schema,
            json.loads((mmic.resource_directory() / "mmic.schema.json").read_text()),
        )
        mmic.check_resources()
        graph = Graph().parse(
            mmic.resource_directory() / "mechanical-music.ttl", format="turtle"
        )
        self.assertGreater(len(graph), 300)
        self.assertFalse(
            list(
                graph.triples(
                    (
                        None,
                        mmic_rdf.URIRef("http://www.w3.org/2002/07/owl#imports"),
                        None,
                    )
                )
            )
        )

    def test_complete_and_partial_carriers_and_deterministic_pack(self):
        for folder in sorted(FIXTURES.glob("*/preservation-closure")):
            with (
                self.subTest(fixture=folder.parent.name),
                tempfile.TemporaryDirectory() as tmp,
            ):
                report = vao06.validate(folder)
                self.assertTrue(report["valid"], report)
                self.assertEqual("valid", report["mmic"]["status"])
                self.assertEqual(
                    "not established", report["mmic"]["historicalCertification"]
                )
                bootstrap = folder.parent / "bootstrap"
                self.assertEqual(
                    (folder / "vao-manifest.json").read_bytes(),
                    (bootstrap / "vao-manifest.json").read_bytes(),
                )
                partial = vao06.validate(bootstrap)
                self.assertTrue(partial["coreValid"], partial)
                self.assertEqual("unmaterialized", partial["mmic"]["status"])
                self.assertEqual("valid", partial["mmic"]["levels"]["documentation"])
                for workspace in (folder, bootstrap):
                    first = Path(tmp) / f"{workspace.name}.vao"
                    second = Path(tmp) / f"{workspace.name}-repeat.vao"
                    vao06.pack_workspace(workspace, first)
                    vao06.pack_workspace(workspace, second)
                    self.assertEqual(first.read_bytes(), second.read_bytes())
                    self.assertEqual(
                        first.read_bytes(),
                        (folder.parent / f"{workspace.name}.vao").read_bytes(),
                    )
                    self.assertTrue(vao.validate(first)["valid"])
                    self.assertFalse(vao05.validate(first)["valid"])

    def test_normative_json_rdf_json_and_jsonld_parity(self):
        for folder in sorted(FIXTURES.glob("*/preservation-closure")):
            with self.subTest(fixture=folder.parent.name):
                data, manifest, assets = bundle(folder.parent.name)
                graph = mmic_rdf.project(data)
                self.assertEqual(data, mmic_rdf.inverse(graph))
                ttl = (folder.parent / "projection.ttl").read_text()
                self.assertTrue(
                    isomorphic(graph, Graph().parse(data=ttl, format="turtle"))
                )
                ld = Graph().parse(
                    folder.parent / "projection.jsonld", format="json-ld"
                )
                self.assertTrue(isomorphic(graph, ld))
                self.assertEqual(
                    "valid", mmic_rdf.validate(ttl, manifest, assets.get)["status"]
                )
                data["extensions"] = {
                    "https://example.org/unrecognized": {
                        "array": [1, None, {"ordered": True}],
                        "identifier": "external",
                        "id": "uninterpreted local value",
                        "collision": {
                            "id": data["id"],
                            "kind": "point",
                            "start": 0,
                            "end": 1,
                        },
                    }
                }
                self.assertEqual(data, mmic_rdf.inverse(mmic_rdf.project(data)))

    def test_R01_point_shape_rejects_axial_mismatch(self):
        data, manifest, assets = bundle("helical-barrel")
        graph = mmic_rdf.project(data)
        location = next(
            s
            for s in graph.subjects(mmic_rdf.M.kind, Literal("point"))
            if list(graph.objects(s, mmic_rdf.M.axialEnd))
        )
        graph.set((location, mmic_rdf.M.axialEnd, Literal(43.0)))
        with self.assertRaisesRegex(mmic.MMICError, "Point endpoints"):
            mmic_rdf.validate(graph.serialize(format="turtle"), manifest, assets.get)

    def test_reference_gaps_rejected_after_operational_repins(self):
        cases = [
            (
                "T01",
                "roll",
                lambda d: d["models"][0]["spec"]["timing"]["anchors"][-1].update(
                    seconds=300
                ),
                "MMIC-08",
            ),
            (
                "H01",
                "helical-barrel",
                lambda d: d["models"][0]["spec"]["reader"]["trajectory"][-1].update(
                    position=1
                ),
                "MMIC-07",
            ),
            (
                "I01",
                "roll",
                lambda d: d["interpretations"][0]["events"][0].update(
                    id=d["carriers"][0]["id"]
                ),
                "MMIC-01",
            ),
            (
                "D01",
                "roll",
                lambda d: d.update(
                    states=[], programmes=[], observations=[], features=[]
                ),
                "MMIC-02",
            ),
            (
                "G01",
                "fabricated-design",
                lambda d: d.update(fabrications=[]),
                "MMIC-11",
            ),
        ]
        for name, source, mutate, requirement in cases:
            with self.subTest(probe=name):
                data, manifest, assets = bundle(source)
                mutate(data)
                repin(data)
                with self.assertRaisesRegex(mmic.MMICError, requirement):
                    mmic.validate_domain(data, manifest, assets.get)
        data, manifest, assets = bundle()
        data["models"][0]["spec"]["reader"]["delaySeconds"] = 1
        with self.assertRaisesRegex(mmic.MMICError, "MMIC-04"):
            mmic.validate_domain(data, manifest, assets.get)
        data, manifest, assets = bundle()
        first = data["states"][0]
        second = {
            **copy.deepcopy(first),
            "id": fixtures.uid("negative/state2"),
            "predecessorId": first["id"],
        }
        first["predecessorId"] = second["id"]
        data["states"].append(second)
        with self.assertRaisesRegex(mmic.MMICError, "cyclic predecessor"):
            mmic.validate_domain(data, manifest, assets.get)

    def test_C01_fixity_consistent_complete_carrier_rejected(self):
        data, manifest, assets = bundle()
        midi_id = data["interpretations"][0]["exports"][0]["realizationId"]
        division, tempo, messages = mmic.midi_messages(assets[midi_id])
        changed = [
            (
                t,
                command,
                channel,
                67 if command == 11 and target == 64 else target,
                value,
            )
            for t, command, channel, target, value in messages
        ]
        assets[midi_id] = mmic.write_midi(division, tempo, changed)
        new_midi_id = fixtures.uid("C01/midi/" + mmic.digest(assets[midi_id]))
        data = replace(data, midi_id, new_midi_id)
        manifest = replace(manifest, midi_id, new_midi_id)
        assets[new_midi_id] = assets.pop(midi_id)
        for registry in ("interpretations", "comparisons"):
            for old in [r["id"] for r in data[registry]]:
                data = replace(data, old, fixtures.uid("C01/" + old))
        semantic_id = manifest["extensions"][mmic.PROFILE]["semanticRealizationId"]
        new_semantic = vao06.json_bytes(data)
        new_id = fixtures.uid("C01/semantic/" + mmic.digest(new_semantic))
        manifest = replace(manifest, semantic_id, new_id)
        assets[new_id] = new_semantic
        assets.pop(semantic_id)
        manifest = replace(manifest, manifest["id"], fixtures.uid("C01/manifest"))
        manifest["release"]["id"] = fixtures.uid("C01/release")
        for realization in manifest["realizations"]:
            realization["byteSize"] = len(assets[realization["id"]])
            realization["sha256"] = mmic.digest(assets[realization["id"]])
        manifest["extensions"][mmic.PROFILE]["semanticSHA256"] = mmic.digest(
            new_semantic
        )
        for group in manifest["assetGroups"]:
            group["totalByteSize"] = sum(
                len(assets[x]) for x in group["realizationIds"]
            )
        # A new constructor record pins this regression's exact source.
        activity = manifest["scientific"]["activities"][0]
        new_activity = fixtures.uid("C01/construction")
        manifest = replace(manifest, activity["id"], new_activity)
        data = replace(data, activity["id"], new_activity)
        old_environment = manifest["scientific"]["softwareEnvironments"][0]["id"]
        manifest = replace(manifest, old_environment, fixtures.uid("C01/environment"))
        env = manifest["scientific"]["softwareEnvironments"][0]
        env.update(
            name="MMIC C01 regression constructor",
            identity={
                "algorithm": "sha256",
                "value": mmic.digest(Path(__file__).read_bytes()),
            },
            identityDescription="Exact tests/test_mmic.py bytes",
        )
        # Changing the activity in the sidecar changes its exact realization again.
        new_semantic = vao06.json_bytes(data)
        final_id = fixtures.uid("C01/semantic/" + mmic.digest(new_semantic))
        manifest = replace(manifest, new_id, final_id)
        assets[final_id] = new_semantic
        assets.pop(new_id)
        r = next(r for r in manifest["realizations"] if r["id"] == final_id)
        r.update(byteSize=len(new_semantic), sha256=mmic.digest(new_semantic))
        manifest["extensions"][mmic.PROFILE]["semanticSHA256"] = mmic.digest(
            new_semantic
        )
        for group in manifest["assetGroups"]:
            group["totalByteSize"] = sum(
                len(assets[x]) for x in group["realizationIds"]
            )
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "candidate"
            folder.mkdir()
            raw = vao06.json_bytes(manifest)
            carrier = {
                "$schema": vao06.BASE + "/schema/carrier.json",
                "formatVersion": vao06.FORMAT_VERSION,
                "type": "VAOCarrier",
                "id": fixtures.uid("C01/carrier"),
                "releaseId": manifest["release"]["id"],
                "carrierMode": "preservation-closure",
                "manifestByteSize": len(raw),
                "manifestSHA256": mmic.digest(raw),
                "embeddedRealizations": [],
                "completeGroupIds": [x["id"] for x in manifest["assetGroups"]],
            }
            (folder / "mimetype").write_bytes(vao06.MIMETYPE.encode())
            (folder / "vao-manifest.json").write_bytes(raw)
            for index, (rid, value) in enumerate(assets.items()):
                path = f"payload/asset-{index}"
                (folder / path).parent.mkdir(exist_ok=True)
                (folder / path).write_bytes(value)
                carrier["embeddedRealizations"].append(
                    {"realizationId": rid, "path": path}
                )
            (folder / "META-INF").mkdir()
            vao06.write_json(folder / vao06.CARRIER_NAME, carrier)
            result = vao06.validate(folder)
            self.assertTrue(result.get("coreValid", False), result)
            self.assertFalse(result["valid"], result)
            self.assertEqual("invalid", result["mmic"]["status"])
            self.assertIn("SMF bytes disagree", str(result["errors"]))

    def test_semantic_negative_matrix(self):
        def change(d, registry, field, value):
            d[registry][0][field] = value

        def spec_change(d, field, value):
            d["models"][0]["spec"][field] = value
            repin(d)

        cases = [
            (
                "physical/digital identity conflated",
                "roll",
                lambda d: d["carriers"][0].update(
                    digitalEntityId=d["carriers"][0]["id"]
                ),
            ),
            ("missing evidence", "roll", lambda d: d.update(evidence=[])),
            (
                "missing evidence reference",
                "roll",
                lambda d: change(
                    d, "carriers", "evidenceIds", ["urn:unknown:evidence"]
                ),
            ),
            ("missing capability declaration", "roll", lambda d: d.update(levels=[])),
            ("missing state", "roll", lambda d: d.update(states=[])),
            (
                "missing geometry units",
                "roll",
                lambda d: d["states"][0]["geometry"].pop("unit"),
            ),
            (
                "invalid source bounds",
                "roll",
                lambda d: change(d, "observations", "sourceBounds", [[100, 0]]),
            ),
            (
                "source selector outside acquisition",
                "roll",
                lambda d: change(d, "features", "selector", [[101, 120], [0, 1]]),
            ),
            (
                "wrong state programme",
                "roll",
                lambda d: change(d, "programmes", "stateId", "urn:unknown:state"),
            ),
            (
                "negative feature interval",
                "roll",
                lambda d: d["features"][0]["location"].update(start=-1),
            ),
            (
                "zero feature interval",
                "roll",
                lambda d: d["features"][0]["location"].update(end=10),
            ),
            (
                "false cyclic seam",
                "disc",
                lambda d: d["features"][0]["location"].update(wrapsSeam=False),
            ),
            (
                "lost wrap turn",
                "disc",
                lambda d: d["features"][0]["location"].update(endTurn=0),
            ),
            (
                "out-of-period position",
                "disc",
                lambda d: d["features"][0]["location"].update(start=360),
            ),
            (
                "missing cylindrical axial",
                "helical-barrel",
                lambda d: d["features"][0]["location"].pop("axialStart"),
            ),
            (
                "cylindrical point has axial extent",
                "helical-barrel",
                lambda d: d["features"][0]["location"].update(axialEnd=43),
            ),
            (
                "helical path absent",
                "helical-barrel",
                lambda d: (
                    d["models"][0]["spec"]["reader"].update(trajectory=[]),
                    repin(d),
                ),
            ),
            (
                "helical interpolation unresolved",
                "helical-barrel",
                lambda d: (
                    d["models"][0]["spec"]["reader"].update(
                        interpolation="undetermined"
                    ),
                    repin(d),
                ),
            ),
            (
                "helical path wrong axial",
                "helical-barrel",
                lambda d: (
                    d["models"][0]["spec"]["reader"]["trajectory"][-1].update(axial=30),
                    repin(d),
                ),
            ),
            (
                "event missing feature",
                "roll",
                lambda d: d["interpretations"][0]["events"][0].update(
                    sourceFeatureIds=[]
                ),
            ),
            (
                "control role emitted note",
                "roll",
                lambda d: d["interpretations"][0]["events"][1].update(
                    roleAssignmentId=d["roleAssignments"][0]["id"]
                ),
            ),
            (
                "unknown role emits",
                "roll",
                lambda d: d["interpretations"][0]["events"][0].update(
                    roleAssignmentId=d["roleAssignments"][-1]["id"]
                ),
            ),
            (
                "rejected model",
                "roll",
                lambda d: change(d, "assignments", "status", "rejected"),
            ),
            (
                "unselected hypothesis",
                "roll",
                lambda d: change(d, "assignments", "selected", False),
            ),
            (
                "rejected role",
                "roll",
                lambda d: change(d, "roleAssignments", "status", "rejected"),
            ),
            (
                "excluded feature emitted",
                "roll",
                lambda d: d["interpretations"][0]["excludedFeatureIds"].append(
                    d["features"][0]["id"]
                ),
            ),
            (
                "source feature unaccounted",
                "roll",
                lambda d: d["interpretations"][0].update(excludedFeatureIds=[]),
            ),
            (
                "printed guidance emitted",
                "roll",
                lambda d: change(d, "features", "kind", "print"),
            ),
            ("duplicate track index", "roll", lambda d: d["tracks"][1].update(index=0)),
            (
                "reader offset wrong unit",
                "roll",
                lambda d: (
                    d["models"][0]["spec"]["roles"][0].update(
                        readerOffsetUnit="http://qudt.org/vocab/unit/SEC"
                    ),
                    repin(d),
                ),
            ),
            (
                "reader offset outside full digest",
                "roll",
                lambda d: d["models"][0]["spec"]["roles"][0].update(readerOffset=1),
            ),
            (
                "stale full model hash",
                "roll",
                lambda d: d["models"][0]["spec"]["reader"].update(response="changed"),
            ),
            (
                "stale execution model hash",
                "roll",
                lambda d: d["interpretations"][0]["execution"].update(
                    modelSHA256="0" * 64
                ),
            ),
            (
                "missing code pin",
                "roll",
                lambda d: (
                    d["models"][0]["spec"].update(
                        artifactPins=d["models"][0]["spec"]["artifactPins"][1:]
                    ),
                    repin(d),
                ),
            ),
            (
                "wrong code pin",
                "roll",
                lambda d: (
                    d["models"][0]["spec"]["artifactPins"][0].update(sha256="0" * 64),
                    repin(d),
                ),
            ),
            (
                "clock wrong units",
                "roll",
                lambda d: (
                    d["models"][0]["spec"]["timing"].update(
                        unit="http://qudt.org/vocab/unit/SEC"
                    ),
                    repin(d),
                ),
            ),
            (
                "clock reversed without direction",
                "roll",
                lambda d: (
                    d["models"][0]["spec"]["timing"]["anchors"][-1].update(seconds=0),
                    repin(d),
                ),
            ),
            (
                "reader domain lacks coverage",
                "roll",
                lambda d: (
                    d["models"][0]["spec"]["reader"].update(domain=[0, 5]),
                    repin(d),
                ),
            ),
            (
                "event time differs",
                "roll",
                lambda d: d["interpretations"][0]["events"][0].update(onsetSeconds=2),
            ),
            (
                "event duration differs",
                "roll",
                lambda d: d["interpretations"][0]["events"][0].update(
                    durationSeconds=2
                ),
            ),
            (
                "known sustain binding is soft pedal",
                "roll",
                lambda d: (
                    d["models"][0]["spec"]["exportBindings"][1].update(controller=67),
                    repin(d),
                ),
            ),
            (
                "control assigned a pitch",
                "roll",
                lambda d: d["roleAssignments"][1].update(midiPitch=60),
            ),
            (
                "ordinary controller channel-mode",
                "roll",
                lambda d: d["models"][0]["spec"]["exportBindings"][1].update(
                    controller=120
                ),
            ),
            (
                "MIDI channel outside wire range",
                "roll",
                lambda d: d["models"][0]["spec"]["exportBindings"][0].update(
                    channel=16
                ),
            ),
            (
                "MIDI pitch outside wire range",
                "roll",
                lambda d: d["models"][0]["spec"]["exportBindings"][0].update(pitch=128),
            ),
            (
                "no export loss report",
                "roll",
                lambda d: d["interpretations"][0]["exports"][0].update(losses=[]),
            ),
            (
                "latch missing command",
                "native-latch",
                lambda d: d["features"][0].pop("value"),
            ),
            (
                "envelope unordered samples",
                "native-envelope",
                lambda d: d["features"][0]["samples"].reverse(),
            ),
            (
                "envelope missing unit",
                "native-envelope",
                lambda d: (
                    d["models"][0]["spec"]["roles"][0].pop("quantityUnit"),
                    repin(d),
                ),
            ),
            (
                "impulse exports engagement duration",
                "projection-disc",
                lambda d: (
                    d["models"][0]["spec"]["exportBindings"][0].update(
                        durationPolicy={"kind": "engagement"}
                    ),
                    repin(d),
                ),
            ),
            (
                "event native kind mismatched",
                "roll",
                lambda d: d["interpretations"][0]["events"][0].update(kind="impulse"),
            ),
            (
                "audio input differs from take",
                "roll",
                lambda d: d["playbacks"][0].update(
                    recordingRealizationId=d["interpretations"][0][
                        "sourceRealizationIds"
                    ][0]
                ),
            ),
            (
                "synthetic audio as physical",
                "roll",
                lambda d: d["playbacks"][0].update(recordingKind="physical"),
            ),
            (
                "audio automatically ground truth",
                "roll",
                lambda d: d["comparisons"][0].update(groundTruth=True),
            ),
            (
                "same comparison sources",
                "roll",
                lambda d: d["comparisons"][0].update(
                    rightInterpretationId=d["comparisons"][0]["leftInterpretationId"]
                ),
            ),
            (
                "comparison lacks alignment",
                "roll",
                lambda d: d["comparisons"][0].pop("alignment"),
            ),
            (
                "comparison impossible coverage",
                "roll",
                lambda d: d["comparisons"][0]["metrics"].update(matchedCoverage=-1),
            ),
            (
                "comparison invented residual",
                "roll",
                lambda d: d["comparisons"][0]["metrics"].update(maxResidualSeconds=1),
            ),
            (
                "comparison silently omits pair",
                "roll",
                lambda d: d["comparisons"][0]["pairs"].pop(),
            ),
            (
                "comparison without decoding",
                "roll",
                lambda d: d.update(levels=["documentation", "comparison"]),
            ),
            (
                "fabrication missing inspection",
                "fabricated-design",
                lambda d: d["fabrications"][0].pop("inspectionRealizationId"),
            ),
            (
                "fabrication wrong design",
                "fabricated-design",
                lambda d: d["fabrications"][0].update(designId="urn:missing:design"),
            ),
            (
                "design lacks source",
                "design-only",
                lambda d: d["designs"][0].pop("sourceRealizationId"),
            ),
            (
                "design lacks target model",
                "design-only",
                lambda d: d["designs"][0].pop("modelId"),
            ),
            (
                "fabricated design no process",
                "fabricated-design",
                lambda d: d.update(fabrications=[]),
            ),
            (
                "model reader redundant copy",
                "roll",
                lambda d: d["models"][0].update(reader={}),
            ),
            (
                "undocumented confidence",
                "roll",
                lambda d: d["evidence"][0].update(confidence=0.9),
            ),
            ("unsafe integer", "roll", lambda d: d.update(extensions={"x": 2**60})),
            (
                "NaN input",
                "roll",
                lambda d: d["features"][0]["location"].update(start=float("nan")),
            ),
        ]
        self.assertGreaterEqual(len(cases), 51)
        for label, source, mutate in cases:
            with self.subTest(case=label):
                data, manifest, assets = bundle(source)
                mutate(data)
                with self.assertRaises(mmic.MMICError):
                    mmic.validate_domain(data, manifest, assets.get)

    def test_gap_regressions_through_fixity_consistent_archives(self):
        def cycle(d):
            first = d["states"][0]
            second = {
                **copy.deepcopy(first),
                "id": fixtures.uid("I02/state2"),
                "predecessorId": first["id"],
            }
            first["predecessorId"] = second["id"]
            d["states"].append(second)

        cases = [
            (
                "T01",
                "roll",
                lambda d: (
                    d["models"][0]["spec"]["timing"]["anchors"][-1].update(seconds=300),
                    repin(d),
                ),
                "MMIC-08",
            ),
            (
                "H01",
                "helical-barrel",
                lambda d: (
                    d["models"][0]["spec"]["reader"]["trajectory"][-1].update(
                        position=1
                    ),
                    repin(d),
                ),
                "MMIC-07",
            ),
            (
                "M01",
                "roll",
                lambda d: d["models"][0]["spec"]["reader"].update(delaySeconds=1),
                "MMIC-04",
            ),
            (
                "I01",
                "roll",
                lambda d: d["interpretations"][0]["events"][0].update(
                    id=d["carriers"][0]["id"]
                ),
                "MMIC-01",
            ),
            ("I02", "roll", cycle, "MMIC-01"),
            (
                "D01",
                "roll",
                lambda d: d.update(
                    states=[], programmes=[], observations=[], features=[]
                ),
                "MMIC-02",
            ),
            (
                "G01",
                "fabricated-design",
                lambda d: d.update(fabrications=[]),
                "MMIC-11",
            ),
        ]
        for label, source, mutation, requirement in cases:
            with self.subTest(probe=label), tempfile.TemporaryDirectory() as tmp:
                data, manifest, assets = bundle(source)
                mutation(data)
                archive = Path(tmp) / "probe.vao"
                fixed_negative_archive(data, manifest, assets, archive, label)
                result = vao06.validate(archive)
                self.assertTrue(result.get("coreValid", False), result)
                self.assertFalse(result["valid"], result)
                self.assertEqual("invalid", result["mmic"]["status"])
                self.assertIn(requirement, str(result["mmic"]["errors"]))

    def test_version_capability_and_group_contract_negatives(self):
        data, manifest, assets = bundle()
        wrong_scope = copy.deepcopy(manifest)
        unrelated = fixtures.uid("negative/unrelated-subject")
        wrong_scope["entities"].append(
            {
                "id": unrelated,
                "kind": "related-source",
                "types": ["http://www.w3.org/ns/prov#Entity"],
                "labels": {"en": "Unrelated synthetic entity"},
            }
        )
        wrong_scope["extensions"][mmic.PROFILE]["subjectEntityIds"] = [unrelated]
        self.assertTrue(vao06.validate_manifest(wrong_scope)["valid"])
        self.assertEqual(
            "invalid", mmic.validate_materialized(wrong_scope, assets.get)["status"]
        )
        with self.assertRaisesRegex(mmic.MMICError, "MMIC-02"):
            mmic.validate_domain(data, wrong_scope, assets.get)
        with self.assertRaisesRegex(mmic.MMICError, "MMIC-02"):
            mmic_rdf.validate(
                mmic_rdf.project(data).serialize(format="turtle"),
                wrong_scope,
                assets.get,
            )
        mutations = [
            lambda m: m["materializableProfiles"][0].update(
                specificationVersion="1.0.1"
            ),
            lambda m: m["extensions"][mmic.PROFILE].update(profileVersion="0.6.0"),
            lambda m: m["extensions"][mmic.PROFILE].update(semanticSHA256="0" * 64),
            lambda m: m["extensions"][mmic.PROFILE].update(
                dependencyCatalogSHA256="0" * 64
            ),
            lambda m: m["profiles"].append(
                copy.deepcopy(m["materializableProfiles"][0])
            ),
            lambda m: m["materializableProfiles"][0].update(requiredCapabilities=[]),
            lambda m: m["extensions"][mmic.PROFILE].update(
                subjectEntityIds=["urn:unknown:subject"]
            ),
        ]
        for mutate in mutations:
            bad = copy.deepcopy(manifest)
            mutate(bad)
            self.assertEqual(
                "invalid", mmic.validate_materialized(bad, assets.get)["status"]
            )
        bad = copy.deepcopy(manifest)
        bad["assetGroups"][1]["realizationIds"] = []
        self.assertEqual(
            "invalid", mmic.validate_materialized(bad, assets.get)["status"]
        )
        future = replace(manifest, mmic.PROFILE, mmic.PROFILE.replace("1.0.0", "1.1.0"))
        future_profile = mmic.PROFILE.replace("1.0.0", "1.1.0")
        future["extensions"][future_profile] = future["extensions"].pop(mmic.PROFILE)
        self.assertTrue(vao06.validate_manifest(future)["valid"])
        self.assertEqual(
            "unsupported", mmic.validate_isolated(future, assets.get)["status"]
        )

    def test_resource_limits_duplicates_and_unsupported_distinction(self):
        for raw in [
            b'{"id":1,"id":2}',
            b'{"number":NaN}',
            b'{"a":' + b"[" * 40 + b"0" + b"]" * 40 + b"}",
        ]:
            with self.assertRaises(mmic.MMICError):
                mmic.strict_json(raw)
        with self.assertRaises(mmic.MMICError):
            mmic.strict_json(b" " * (mmic.MAX_BYTES + 1))
        data, manifest, assets = bundle()
        data["models"][0]["spec"]["reader"]["segmented"] = True
        repin(data)
        with self.assertRaises(mmic.Unsupported):
            mmic.validate_domain(data, manifest, assets.get)
        for bad in [b"not midi", mmic.write_midi(480, 500000, [])[:-1]]:
            with self.assertRaises(mmic.MMICError):
                mmic.midi_messages(bad)

    def test_original_05_dispatch_and_immutable_byte_preservation_migration(self):
        for path in (ROOT / "Fixtures/VAO05/carriers").glob("*.vao"):
            self.assertTrue(vao.validate(path)["valid"])
        source = ROOT / "Fixtures/VAO05/workspaces/minimal"
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "migrated"
            receipt = Path(tmp) / "receipt.json"
            result = migrate_vao05.migrate(source, destination, receipt)
            self.assertTrue(result["validation"]["valid"])
            old = json.loads((source / "vao-manifest.json").read_text())
            new = json.loads((destination / "vao-manifest.json").read_text())
            self.assertEqual(
                [r["id"] for r in old["realizations"]],
                [r["id"] for r in new["realizations"]],
            )
            for path in (source / "payload").rglob("*"):
                if path.is_file():
                    self.assertEqual(
                        path.read_bytes(),
                        (destination / path.relative_to(source)).read_bytes(),
                    )
            self.assertFalse(result["prototypeMMICPromoted"])
            with self.assertRaises(ValueError):
                migrate_vao05.migrate(source, destination, receipt)

    def test_independent_javascript_consumer(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Release interoperability gate requires Node.js")
        for folder in sorted(FIXTURES.glob("*/preservation-closure")):
            with self.subTest(fixture=folder.parent.name):
                result = subprocess.run(
                    [node, str(ROOT / "Tools/mmic_consumer.mjs"), str(folder)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual("valid", report["status"])
                data, _, _ = bundle(folder.parent.name)
                expected = []
                for interpretation in data["interpretations"]:
                    if interpretation["sourceKind"] != "carrier-derived":
                        continue
                    for event in interpretation["events"]:
                        expected.append(
                            {
                                "eventId": event["id"],
                                **{
                                    k: event[k]
                                    for k in (
                                        "kind",
                                        "onsetSeconds",
                                        "durationSeconds",
                                        "value",
                                        "unit",
                                        "samples",
                                    )
                                    if k in event
                                },
                            }
                        )
                self.assertTrue(mmic._close(report["traces"], expected, 1e-9))
                self.assertEqual(
                    [c["id"] for c in data["carriers"]], report["physicalCarrierIds"]
                )
                self.assertEqual([p["id"] for p in data["parts"]], report["partIds"])
                self.assertEqual(
                    [d["id"] for d in data["designs"]],
                    [d["designId"] for d in report["designs"]],
                )
                self.assertEqual(
                    [c["id"] for c in data["comparisons"]],
                    [c["comparisonId"] for c in report["comparisons"]],
                )

    def test_06_core_semantic_projection_and_legacy_descriptor_regressions(self):
        for path in (ROOT / "Fixtures/VAO05/descriptors").glob("*.json"):
            value = json.loads(path.read_text().replace("0.5.0", vao06.FORMAT_VERSION))
            self.assertTrue(vao06.validate_manifest(value)["valid"])
            self.assertEqual(
                value, vao06_rdf.inverse_projection(vao06_rdf.project_jsonld(value))
            )
        _, manifest, _ = bundle()
        self.assertEqual(
            manifest, vao06_rdf.inverse_projection(vao06_rdf.project_jsonld(manifest))
        )
        manifest["entities"][0]["kind"] = "physical-carrier"
        self.assertTrue(vao06.validate_manifest(manifest)["valid"])

    def test_corrections_retain_exact_prior_and_replacement_values(self):
        data, manifest, assets = bundle("corrected-interpretation")
        mmic.validate_domain(data, manifest, assets.get)
        for mutation in (
            lambda d: d["corrections"][0].update(
                replacementTargetId=d["corrections"][0]["targetId"]
            ),
            lambda d: d["corrections"][0].update(
                previousValue={"sourceKind": "unknown"}
            ),
            lambda d: d["interpretations"][1].pop("predecessorId"),
            lambda d: d["corrections"][0].update(agentId="urn:unknown:agent"),
        ):
            changed = copy.deepcopy(data)
            mutation(changed)
            with self.assertRaisesRegex(mmic.MMICError, "MMIC-10"):
                mmic.validate_domain(changed, manifest, assets.get)

    def test_generation_constraints_and_byte_artifacts_are_operational(self):
        data, manifest, assets = bundle("design-only")
        for artifact_field, changed_field, value in (
            ("layoutRealizationId", "commands", []),
            ("reportRealizationId", "acceptedCount", 99),
            ("reportRealizationId", "fabricated", True),
            ("reportRealizationId", "adaptations", ["implicit-clipping"]),
        ):
            changed_assets = dict(assets)
            changed_manifest = copy.deepcopy(manifest)
            rid = data["designs"][0][artifact_field]
            artifact = json.loads(assets[rid])
            artifact[changed_field] = value
            changed_assets[rid] = vao06.json_bytes(artifact)
            r = next(r for r in changed_manifest["realizations"] if r["id"] == rid)
            r.update(
                sha256=mmic.digest(changed_assets[rid]),
                byteSize=len(changed_assets[rid]),
            )
            with self.assertRaisesRegex(mmic.MMICError, "MMIC-11"):
                mmic.validate_domain(data, changed_manifest, changed_assets.get)
        for constraint, value in (("minimumClearance", 1000), ("minimumTarget", 61)):
            changed = copy.deepcopy(data)
            changed_assets = dict(assets)
            changed_manifest = copy.deepcopy(manifest)
            changed["models"][0]["spec"]["constraints"][constraint] = value
            repin(changed)
            for field in ("layoutRealizationId", "reportRealizationId"):
                rid = changed["designs"][0][field]
                artifact = json.loads(changed_assets[rid])
                artifact["modelSHA256"] = changed["models"][0]["specSHA256"]
                changed_assets[rid] = vao06.json_bytes(artifact)
                r = next(r for r in changed_manifest["realizations"] if r["id"] == rid)
                r.update(
                    sha256=mmic.digest(changed_assets[rid]),
                    byteSize=len(changed_assets[rid]),
                )
            with self.assertRaisesRegex(mmic.MMICError, "MMIC-11"):
                mmic.validate_domain(changed, changed_manifest, changed_assets.get)
        changed = copy.deepcopy(data)
        changed["designs"][0]["execution"]["codeRealizationId"] = "urn:wrong:code"
        with self.assertRaisesRegex(mmic.MMICError, "MMIC-11"):
            mmic.validate_domain(changed, manifest, assets.get)

    def test_access_redaction_and_preservation_of_unknown_extensions(self):
        data, manifest, assets = bundle()
        recording = data["playbacks"][0]["recordingRealizationId"]
        data["redactions"] = [
            {
                "realizationId": recording,
                "reason": "Synthetic access-control regression",
            }
        ]
        manifest["rights"][0]["access"] = "restricted"
        with self.assertRaisesRegex(mmic.MMICError, "redacted bytes"):
            mmic.validate_domain(data, manifest, assets.get)
        assets.pop(recording)
        pin_sidecar(data, manifest, assets)
        report = mmic.validate_materialized(manifest, assets.get)
        self.assertEqual("access-unavailable", report["status"], report)
        self.assertEqual("valid", report["levels"]["documentation"])
        data["extensions"] = {
            "https://example.org/unknown": {"realizationId": "urn:uninterpreted:opaque"}
        }
        self.assertNotIn("urn:uninterpreted:opaque", mmic.asset_dependencies(data))
        self.assertEqual(data, mmic_rdf.inverse(mmic_rdf.project(data)))

    def test_worker_closure_opaque_proofs_and_timeout_status(self):
        data, manifest, assets = bundle()
        source = data["observations"][0]["sourceRealizationId"]
        r = next(r for r in manifest["realizations"] if r["id"] == source)
        r.update(byteSize=12 * 1024 * 1024, sha256="a" * 64)
        assets[source] = {
            "coreVerified": True,
            "sha256": r["sha256"],
            "byteSize": r["byteSize"],
        }
        # The availability proof is accepted only after the core has streamed these bytes.
        report = mmic.validate_isolated(manifest, assets.get)
        self.assertEqual("valid", report["status"], report)
        manifest["realizations"].append(
            {"id": "urn:unused:large", "byteSize": 20 * 1024 * 1024}
        )

        def read_asset(rid):
            self.assertNotEqual("urn:unused:large", rid)
            return assets.get(rid)

        self.assertEqual(
            "valid", mmic.validate_isolated(manifest, read_asset)["status"]
        )
        with mock.patch(
            "mmic.subprocess.run",
            side_effect=subprocess.TimeoutExpired("trusted worker", 15),
        ):
            self.assertEqual(
                "unsupported", mmic.validate_isolated(manifest, assets.get)["status"]
            )


if __name__ == "__main__":
    unittest.main()
