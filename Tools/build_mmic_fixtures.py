#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build original, explicitly synthetic MMIC conformance fixtures offline."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import io
import math
import struct
import wave
import uuid
import zipfile

import mmic
import mmic_rdf
import vao06

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "Fixtures/MMIC" / mmic.VERSION
UNIT = "http://qudt.org/vocab/unit/MilliM"
DEGREE = "http://qudt.org/vocab/unit/DEG"


def uid(text):
    return "urn:uuid:" + str(
        uuid.uuid5(
            uuid.NAMESPACE_URL, "VAO/MMIC/candidate/" + mmic.VERSION + "/" + text
        )
    )


def encoded(value):
    return vao06.json_bytes(value)


def make(
    name,
    kind="linear",
    signal="gate",
    reverse=False,
    design=False,
    fabricated=False,
    controls=False,
    documentary=False,
    comparison=False,
    native_only=False,
    reader_offset=0,
):
    identifier = lambda x: uid(name + "/" + x)
    entity, digital, activity, agent, protocol, software = map(
        identifier, ("physical", "digital", "activity", "agent", "protocol", "software")
    )
    evidence = identifier("evidence")
    state, programme, model_id, assignment_id = map(
        identifier, ("state", "programme", "model", "assignment")
    )
    manifest = json.loads(
        (ROOT / "Fixtures/VAO05/workspaces/minimal/vao-manifest.json")
        .read_text()
        .replace("0.5.0", vao06.FORMAT_VERSION)
    )
    manifest.update(
        id=identifier("manifest"),
        title={"en": f"Synthetic MMIC {name}"},
        description={
            "en": "CC0 synthetic structural test; no historical object, measured take or accuracy certification."
        },
        createdAt="2026-10-10T00:00:00Z",
        modifiedAt="2026-10-10T00:00:00Z",
        primaryEntityId=entity,
        focusEntityIds=[entity],
        entities=[],
        logicalAssets=[],
        realizations=[],
        assetGroups=[],
        relations=[],
        extensions={},
        release={
            "id": identifier("release"),
            "contentVersion": "1.0.0",
            "revision": 1,
        },
        rights=[],
    )
    manifest["discovery"]["creatorAgentIds"] = [agent]
    manifest["modavisBinding"]["notes"] = (
        "Existing released MODAVIS 0.1.0 binding; MMIC module is an independent unpublished VAO-owned dependency."
    )
    metadata_rights, software_rights = (
        identifier("rights/cc0"),
        identifier("rights/apache"),
    )
    manifest["rights"] = [
        {
            "id": metadata_rights,
            "access": "open",
            "appliesToIds": [manifest["id"]],
            "license": "https://creativecommons.org/publicdomain/zero/1.0/",
            "statement": {"en": "Synthetic fixture data dedicated under CC0."},
        },
        {
            "id": software_rights,
            "access": "open",
            "appliesToIds": [],
            "license": "https://spdx.org/licenses/Apache-2.0",
            "statement": {
                "en": "Reference source and dependency declarations retain Apache-2.0."
            },
        },
    ]
    scientific = manifest["scientific"]
    for k in scientific:
        scientific[k] = []
    scientific["agents"] = [
        {
            "id": agent,
            "agentKind": "software-agent",
            "labels": {"en": "Synthetic fixture constructor"},
        }
    ]
    scientific["protocols"] = [
        {
            "id": protocol,
            "labels": {"en": "Synthetic conformance construction"},
            "procedure": "Construct and replay declared synthetic MMIC traces; no historic calibration or actual fabrication claim.",
            "version": mmic.VERSION,
        }
    ]
    scientific["softwareEnvironments"] = [
        {
            "id": software,
            "name": "MMIC conformance fixture constructor",
            "version": mmic.VERSION,
            "identity": {
                "algorithm": "sha256",
                "value": mmic.digest(Path(__file__).read_bytes()),
            },
            "identityScope": "source-file",
            "identityDescription": "Exact distributed Tools/build_mmic_fixtures.py bytes.",
            "runtimeDescription": "CPython >=3.11 with hash-locked source dependencies.",
        }
    ]
    scientific["activities"] = [
        {
            "id": activity,
            "activityKind": "authoring",
            "agentIds": [agent],
            "inputIds": [],
            "outputIds": [],
            "startedAt": "2026-10-10T00:00:00Z",
            "endedAt": "2026-10-10T00:00:00Z",
            "protocolId": protocol,
            "softwareEnvironmentId": software,
            "parameterValues": {mmic.NS + "synthetic": True},
        }
    ]
    payload = {}
    names = {}

    def asset(
        label, data, media="application/json", source=False, software_asset=False
    ):
        rid = identifier("bytes/" + label + "/" + mmic.digest(data))
        aid = identifier("asset/" + label)
        path = "payload/" + label
        rights_id = software_rights if software_asset else metadata_rights
        manifest["logicalAssets"].append(
            {
                "id": aid,
                "type": "LogicalAsset",
                "labels": {"en": label},
                "roles": [
                    "https://w3id.org/modavis/vao/vocab/" + "asset-role/source-evidence"
                ],
                "aboutEntityIds": [entity],
                "realizationIds": [rid],
            }
        )
        manifest["realizations"].append(
            {
                "id": rid,
                "type": "Realization",
                "assetId": aid,
                "variantSetId": label,
                "qualityTier": "preservation",
                "mediaType": media,
                "byteSize": len(data),
                "sha256": mmic.digest(data),
                "representationStatus": "https://w3id.org/modavis/vao/vocab/"
                + "representation-status/authored",
                "rightsIds": [rights_id],
                "provenanceIds": [activity],
                "technicalMetadata": {"kind": "software" if software_asset else "data"},
                "distributionIds": [],
                "extensions": {mmic.NS + "synthetic": not software_asset},
            }
        )
        manifest["rights"][1 if software_asset else 0]["appliesToIds"] += [aid, rid]
        scientific["activities"][0]["outputIds"].append(rid)
        payload[rid] = data
        names[rid] = path
        return rid

    code = asset(
        "reference.py",
        (ROOT / "Tools/mmic.py").read_bytes(),
        "text/x-python",
        software_asset=True,
    )
    environment = asset(
        "requirements-lock.txt",
        (ROOT / "requirements-lock.txt").read_bytes(),
        "text/plain",
        software_asset=True,
    )
    source = asset(
        "observation.svg",
        b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><title>CC0 synthetic marks, not a historic scan</title><path d="M10 10h20v5H10z"/></svg>',
        "image/svg+xml",
        source=True,
    )
    evidence_source = asset(
        "evidence.txt",
        b"CC0 synthetic fixture; dimensions and clock are assumptions. No physical object, historical reader or accuracy claim.\n",
        "text/plain",
    )
    geometry = {
        "kind": kind,
        "status": "assumed",
        "unit": UNIT if kind == "linear" else DEGREE,
        "bounds": [0, 100] if kind == "linear" else [0, 1080],
        "origin": "Synthetic registration origin",
        "orientation": "Declared increasing coordinate on observed face",
        "direction": "reverse" if reverse else "forward",
    }
    if kind != "linear":
        geometry["period"] = 360
    if kind == "cylindrical":
        geometry.update(axialUnit=UNIT, axialBounds=[0, 60])
    high = geometry["bounds"][1]
    roles, bindings, tracks, role_assignments = [], [], [], []
    for index, role_name in enumerate(
        ["note", "performance-control", "unknown"] if controls else ["note", "unknown"]
    ):
        role_id = identifier(f"model-role/{index}")
        binding_id = identifier(f"binding/{index}")
        current_signal = "unresolved" if role_name == "unknown" else signal
        if role_name == "performance-control" and signal == "impulse":
            current_signal = "gate"
        role = {
            "id": role_id,
            "trackIndex": index,
            "readerOffset": reader_offset,
            "readerOffsetUnit": geometry["unit"],
            "role": role_name,
            "signalKind": current_signal,
            "bindingIds": [] if role_name == "unknown" else [binding_id],
            "responseAssumption": "Synthetic response; feature engagement and acoustic duration are distinct.",
        }
        if role_name != "unknown":
            role["target"] = (
                "https://example.org/mmic/synthetic-target/pitch60"
                if role_name == "note"
                else mmic.NS + "Sustain"
            )
            role["quantityUnit"] = "http://qudt.org/vocab/unit/UNITLESS"
            role["initialValue"] = 0
            binding = {
                "id": binding_id,
                "roleId": role_id,
                "protocol": "smf-ppqn",
                "message": "note" if role_name == "note" else "control-change",
                "channel": 0,
                "ticksPerBeat": 480,
                "tempoMicroseconds": 500000,
                "rounding": "nearest-ties-even",
            }
            if role_name == "note":
                if current_signal in ("latch", "envelope"):
                    role["role"] = "performance-control"
                    binding["message"] = "control-change"
                    role["target"] = mmic.NS + "Sustain"
                else:
                    binding.update(
                        pitch=60,
                        velocity=80,
                        durationPolicy={"kind": "fixed", "seconds": 0.2}
                        if current_signal == "impulse"
                        else {"kind": "engagement"},
                    )
            if binding["message"] == "control-change":
                binding.update(
                    controller=64,
                    initialValue=0,
                    onValue=127,
                    offValue=0,
                    resetPolicy="explicit-final-reset"
                    if current_signal == "latch"
                    else "event-release",
                )
            bindings.append(binding)
        roles.append(role)
        tracks.append(
            {
                "id": identifier(f"track/{index}"),
                "modelId": model_id,
                "index": index,
                "evidenceIds": [evidence],
            }
        )
        role_assignments.append(
            {
                "id": identifier(f"role-assignment/{index}"),
                "assignmentId": assignment_id,
                "trackId": tracks[-1]["id"],
                "modelRoleId": role_id,
                "status": "undetermined" if role_name == "unknown" else "accepted",
                "evidenceIds": [evidence],
            }
        )
    if native_only:
        bindings = []
        for role in roles:
            role["bindingIds"] = []
            if role["role"] == "note":
                role["target"] = "https://example.org/mmic/synthetic-target/pipe"
    spec = {
        "geometry": copy.deepcopy(geometry),
        "reader": {
            "domain": [0, high],
            "trajectory": [{"position": 0, "axial": 0}, {"position": high, "axial": 60}]
            if kind == "cylindrical"
            else [],
            "interpolation": "linear" if kind == "cylindrical" else "none",
            "delaySeconds": 0,
            "response": "Synthetic transfer; no acoustic response claim",
            "segmented": False,
        },
        "timing": {
            "anchors": [
                {
                    "position": 0,
                    "seconds": 3 if reverse else 0,
                    "uncertaintySeconds": 0.001,
                },
                {
                    "position": high,
                    "seconds": 0 if reverse else 3,
                    "uncertaintySeconds": 0.001,
                },
            ],
            "method": "piecewise-linear",
            "unit": geometry["unit"],
            "timeUnit": "http://qudt.org/vocab/unit/SEC",
            "calibrationStatus": "assumed",
            "interpolation": "linear",
            "extrapolation": "forbidden",
            "toleranceSeconds": 1e-9,
            "basis": "Synthetic clock only",
        },
        "roles": roles,
        "exportBindings": bindings,
        "constraints": {
            "minimumTarget": 48,
            "maximumTarget": 72,
            "minimumRepeatSeconds": 0.05,
            "minimumClearance": 0.01,
            "material": "synthetic sheet",
            "tool": "synthetic layout",
            "unsupportedPolicy": "reject",
        },
        "artifactPins": [
            {"realizationId": code, "sha256": mmic.digest(payload[code])},
            {"realizationId": environment, "sha256": mmic.digest(payload[environment])},
        ],
        "runtime": {
            "codeRealizationId": code,
            "environmentRealizationId": environment,
            "algorithm": "mmic-piecewise-reference-1",
            "deterministic": True,
        },
        "initialState": {"latches": "zero"},
        "historicalApplicability": "none; synthetic conformance construction",
    }
    model = {
        "id": model_id,
        "version": "synthetic-1",
        "spec": spec,
        "specSHA256": mmic.digest(mmic.canonical(spec)),
        "canonicalization": "RFC8785",
        "evidenceIds": [evidence],
    }
    data = {
        "id": identifier("domain"),
        "schemaVersion": mmic.VERSION,
        "synthetic": True,
        "levels": ["documentation"]
        if documentary
        else ["documentation", "generation"]
        if design
        else ["documentation", "decoding"],
        **{k: [] for k in mmic.REGISTRIES},
    }
    data["evidence"] = [
        {
            "id": evidence,
            "sourceIRI": "https://example.org/vao/mmic/synthetic-fixture",
            "locator": "Complete synthetic fixture",
            "basis": "synthetic",
            "scope": "Structural checks only; not historical accuracy",
            "agentId": agent,
            "reviewStatus": "reviewed",
            "sourceRealizationId": evidence_source,
        }
    ]
    data["models"] = [] if documentary else [model]
    data["assignments"] = (
        []
        if documentary
        else [
            {
                "id": assignment_id,
                "modelId": model_id,
                "status": "accepted",
                "selected": True,
                "evidenceIds": [evidence],
                **({} if design else {"stateId": state, "programmeId": programme}),
            }
        ]
    )
    data["tracks"] = [] if documentary else tracks
    data["roleAssignments"] = [] if documentary else role_assignments

    def entity_record(ident, label, entity_type):
        return {
            "id": ident,
            "kind": label,
            "types": [mmic.NS + entity_type],
            "labels": {"en": "Synthetic " + label},
        }

    if not design:
        manifest["entities"] = [
            entity_record(entity, "physical-carrier", "PhysicalCarrier"),
            entity_record(digital, "digital-surrogate", "DigitalCarrier"),
        ]
        data["carriers"] = [
            {
                "id": entity,
                "digitalEntityId": digital,
                "encoding": "perforated-roll"
                if kind == "linear"
                else "pinned-barrel"
                if kind == "cylindrical"
                else "projection-disc"
                if signal == "impulse"
                else "perforated-disc",
                "origin": "synthetic",
                "evidenceIds": [evidence],
            }
        ]
        data["states"] = [
            {
                "id": state,
                "carrierId": entity,
                "geometry": geometry,
                "coverage": {"status": "complete", "scope": "Whole synthetic carrier"},
                "evidenceIds": [evidence],
            }
        ]
        data["programmes"] = [
            {
                "id": programme,
                "stateId": state,
                "extent": [0, high],
                "selection": {
                    "kind": "helical" if kind == "cylindrical" else "whole",
                    "label": "Synthetic programme A",
                },
                "evidenceIds": [evidence],
            }
        ]
        data["observations"] = [
            {
                "id": identifier("observation"),
                "stateId": state,
                "sourceRealizationId": source,
                "activityId": activity,
                "sourceBounds": [[0, 100], [0, 100]],
                "coverage": {"status": "complete", "scope": "Whole source view"},
                "evidenceIds": [evidence],
            }
        ]
        if not documentary:
            for index, role in enumerate(roles):
                a = high * (
                    (
                        0.7
                        if kind == "cylindrical"
                        else 0.32
                        if kind == "cyclic"
                        else 0.1
                    )
                    + index * 0.1
                )
                b = (
                    a
                    if role["signalKind"] in ("impulse", "latch", "unresolved")
                    else a + high * 0.05
                )
                if reverse:
                    a, b = high - a, high - b
                location = {
                    "kind": "point" if a == b else "interval",
                    "start": a,
                    "end": b,
                }
                if kind != "linear":
                    location.update(
                        start=a % 360,
                        end=b % 360,
                        startTurn=int(a // 360),
                        endTurn=int(b // 360),
                        wrapsSeam=int(a // 360) != int(b // 360),
                    )
                if kind == "cylindrical":
                    location.update(axialStart=a / high * 60, axialEnd=b / high * 60)
                feature = {
                    "id": identifier(f"feature/{index}"),
                    "observationId": identifier("observation"),
                    "stateId": state,
                    "programmeId": programme,
                    "trackId": tracks[index]["id"],
                    "kind": "print"
                    if role["role"] == "unknown"
                    else "projection"
                    if signal == "impulse"
                    else "perforation",
                    "location": location,
                    "selector": [[10 + index, 15 + index], [10, 20]],
                    "evidenceIds": [evidence],
                }
                if role["signalKind"] == "latch":
                    feature["value"] = 127
                if role["signalKind"] == "envelope":
                    feature["samples"] = [
                        {"position": a, "value": 20},
                        {"position": b, "value": 90},
                    ]
                data["features"].append(feature)
            events, excluded = [], []
            for index, feature in enumerate(data["features"]):
                if roles[index]["role"] == "unknown":
                    excluded.append(feature["id"])
                    continue
                events.append(
                    {
                        "id": identifier(f"event/{index}"),
                        "roleAssignmentId": role_assignments[index]["id"],
                        "sourceFeatureIds": [feature["id"]],
                        **mmic.expected_event(
                            feature, tracks[index], roles[index], spec
                        ),
                    }
                )
            events.sort(key=lambda e: e["onsetSeconds"])
            native = asset("native.json", encoded(events))
            binding_ids = [b["id"] for b in bindings]
            midi = (
                asset(
                    "export.mid",
                    mmic.write_midi(
                        *mmic.export_messages(
                            events,
                            {a["id"]: r for a, r in zip(role_assignments, roles)},
                            spec,
                            binding_ids,
                        )
                    ),
                    "audio/midi",
                )
                if binding_ids
                else None
            )
            execution = {
                "activityId": activity,
                "modelSHA256": model["specSHA256"],
                "codeRealizationId": code,
                "environmentRealizationId": environment,
                "reproducibility": "deterministic",
            }
            data["interpretations"] = [
                {
                    "id": identifier("interpretation"),
                    "modelId": model_id,
                    "assignmentId": assignment_id,
                    "modelSHA256": model["specSHA256"],
                    "sourceKind": "carrier-derived",
                    "sourceRealizationIds": [source],
                    "nativeRealizationId": native,
                    "events": events,
                    "excludedFeatureIds": excluded,
                    "execution": execution,
                    "exports": [
                        {
                            "bindingIds": binding_ids,
                            "realizationId": midi,
                            "losses": [
                                "Synthetic export duration/velocity; no measured acoustic response or historical calibration."
                            ],
                        }
                    ]
                    if midi
                    else [],
                    "evidenceIds": [evidence],
                }
            ]
        if comparison:
            samples = io.BytesIO()
            with wave.open(samples, "wb") as stream:
                stream.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                stream.writeframes(
                    b"".join(
                        struct.pack(
                            "<h", int(1000 * math.sin(i * 2 * math.pi * 440 / 8000))
                        )
                        for i in range(8000)
                    )
                )
            recording = asset("simulation.wav", samples.getvalue(), "audio/wav")
            simulated_events = copy.deepcopy(events)
            for index, event in enumerate(simulated_events):
                event["id"] = identifier(f"simulated-event/{index}")
                event["sourceFeatureIds"] = []
                event["onsetSeconds"] += 0.03
                for sample in event.get("samples", []):
                    sample["seconds"] += 0.03
            simulated_native = asset("simulated-native.json", encoded(simulated_events))
            simulated_id = identifier("simulated-interpretation")
            data["interpretations"].append(
                {
                    "id": simulated_id,
                    "modelId": model_id,
                    "assignmentId": assignment_id,
                    "modelSHA256": model["specSHA256"],
                    "sourceKind": "simulated",
                    "sourceRealizationIds": [recording],
                    "nativeRealizationId": simulated_native,
                    "events": simulated_events,
                    "excludedFeatureIds": [],
                    "execution": execution,
                    "exports": [],
                    "evidenceIds": [evidence],
                }
            )
            playback_id = identifier("simulated-playback")
            data["playbacks"] = [
                {
                    "id": playback_id,
                    "recordingKind": "simulated",
                    "recordingRealizationId": recording,
                    "operatorAgentId": agent,
                    "protocol": "Construct a non-silent sine-wave placeholder and synthetic event trace; no audio transcription claim.",
                    "conditions": "Synthetic processor interoperability test only",
                    "evidenceIds": [evidence],
                }
            ]
            alignment = {
                "anchors": [{"left": 0, "right": 0.03}, {"left": 3, "right": 3.03}],
                "domain": [0, 3],
                "gapPolicy": "none",
                "unmatchedLeftEventIds": [],
                "unmatchedRightEventIds": [],
                "toleranceSeconds": 1e-9,
            }
            alignment_id = asset("alignment.json", encoded(alignment))
            data["comparisons"] = [
                {
                    "id": identifier("comparison"),
                    "leftInterpretationId": identifier("interpretation"),
                    "rightInterpretationId": simulated_id,
                    "playbackId": playback_id,
                    "alignmentRealizationId": alignment_id,
                    "alignment": alignment,
                    "pairs": [
                        {"leftEventId": a["id"], "rightEventId": b["id"]}
                        for a, b in zip(events, simulated_events)
                    ],
                    "metrics": {"matchedCoverage": 1, "maxResidualSeconds": 0},
                    "referenceStatus": "synthetic-test",
                    "evidenceIds": [evidence],
                }
            ]
            data["levels"].append("comparison")
    else:
        entity = identifier("design")
        manifest["primaryEntityId"] = entity
        manifest["focusEntityIds"] = [entity]
        manifest["entities"] = [
            entity_record(entity, "carrier-design", "CarrierDesign")
        ]
        for asset_record in manifest["logicalAssets"]:
            asset_record["aboutEntityIds"] = [entity]
        input_midi = asset(
            "input.mid",
            mmic.write_midi(480, 500000, [(288, 9, 0, 60, 80), (480, 8, 0, 60, 0)]),
            "audio/midi",
        )
        layout = {
            "sourceSHA256": mmic.digest(payload[input_midi]),
            "modelSHA256": model["specSHA256"],
            "commands": [{"channel": 0, "target": 60, "start": 10.0, "end": 50 / 3}],
        }
        report = {
            "sourceSHA256": layout["sourceSHA256"],
            "modelSHA256": model["specSHA256"],
            "acceptedCount": 1,
            "excludedCommands": [],
            "adaptations": [],
            "fabricated": False,
        }
        layout_id = asset("layout.json", encoded(layout))
        report_id = asset("generation-report.json", encoded(report))
        data["designs"] = [
            {
                "id": entity,
                "sourceRealizationId": input_midi,
                "modelId": model_id,
                "layoutRealizationId": layout_id,
                "reportRealizationId": report_id,
                "execution": {
                    "activityId": activity,
                    "modelSHA256": model["specSHA256"],
                    "codeRealizationId": code,
                    "environmentRealizationId": environment,
                    "reproducibility": "deterministic",
                },
                "purpose": "Synthetic layout to test source/model/design lineage",
                "fabricationStatus": "fabricated" if fabricated else "design-only",
                "evidenceIds": [evidence],
            }
        ]
        if fabricated:
            physical = identifier("fabricated-physical")
            manifest["entities"] += [
                entity_record(physical, "physical-carrier", "PhysicalCarrier"),
                entity_record(digital, "digital-surrogate", "DigitalCarrier"),
            ]
            data["carriers"] = [
                {
                    "id": physical,
                    "digitalEntityId": digital,
                    "encoding": "perforated-roll",
                    "origin": "generated",
                    "evidenceIds": [evidence],
                }
            ]
            measured = {**geometry, "status": "estimated"}
            data["states"] = [
                {
                    "id": state,
                    "carrierId": physical,
                    "geometry": measured,
                    "coverage": {
                        "status": "complete",
                        "scope": "Whole synthetic fabrication state",
                    },
                    "evidenceIds": [evidence],
                }
            ]
            inspection = asset("inspection.json", encoded(measured))
            data["fabrications"] = [
                {
                    "id": identifier("fabrication"),
                    "designId": entity,
                    "carrierId": physical,
                    "stateId": state,
                    "activityId": activity,
                    "inspectionRealizationId": inspection,
                    "measuredGeometry": measured,
                    "evidenceIds": [evidence],
                }
            ]
    return data, manifest, payload, names, asset


def seal(data, manifest, payload, names, asset):
    semantic = asset("semantic.json", encoded(data))
    documentation_ids = [semantic] + [
        rid
        for rid, path in names.items()
        if path.endswith(("evidence.txt", "reference.py", "requirements-lock.txt"))
    ]
    doc_group, execution_group = (
        uid(data["id"] + "/documentation"),
        uid(data["id"] + "/execution"),
    )
    for gid, label, rids, dependencies, availability in [
        (doc_group, "Documentation", documentation_ids, [], "offline-required"),
        (
            execution_group,
            "Complete capability inputs and outputs",
            sorted(set(payload) - set(documentation_ids)),
            [doc_group],
            "remote-optional",
        ),
    ]:
        manifest["assetGroups"].append(
            {
                "id": gid,
                "type": "AssetGroup",
                "labels": {"en": label},
                "selectionSetId": label,
                "qualityTier": "bootstrap" if not dependencies else "preservation",
                "availability": availability,
                "selectionPolicy": "independent",
                "realizationIds": rids,
                "dependsOnGroupIds": dependencies,
                "totalByteSize": sum(len(payload[x]) for x in rids),
                "requiredCapabilities": [],
                "materializesProfileIds": [mmic.PROFILE] if dependencies else [],
                "cachePolicy": {
                    "evictable": bool(dependencies),
                    "priority": 50 if dependencies else 100,
                },
            }
        )
    manifest["materializableProfiles"] = [
        {
            "id": mmic.PROFILE,
            "version": vao06.FORMAT_VERSION,
            "specificationVersion": mmic.VERSION,
            "requiredCapabilities": [mmic.CAPABILITIES[x] for x in data["levels"]],
            "groupIds": [execution_group],
        }
    ]
    manifest["conformsTo"].append(mmic.PROFILE)
    manifest["extensions"][mmic.PROFILE] = {
        "profileVersion": mmic.VERSION,
        "ontologyVersionIRI": mmic.ONTOLOGY_VERSION,
        "semanticRealizationId": semantic,
        "semanticSHA256": mmic.digest(payload[semantic]),
        "dependencyCatalogSHA256": mmic.digest(
            (mmic.resource_directory() / "dependencies.json").read_bytes()
        ),
        "levels": data["levels"],
        "subjectEntityIds": [manifest["primaryEntityId"]],
    }
    raw_manifest = encoded(manifest)
    workspaces = {}
    for mode, selected, completed in [
        ("bootstrap", documentation_ids, [doc_group]),
        ("preservation-closure", sorted(payload), [doc_group, execution_group]),
    ]:
        carrier = {
            "$schema": vao06.BASE + "/schema/carrier.json",
            "formatVersion": vao06.FORMAT_VERSION,
            "type": "VAOCarrier",
            "id": uid(data["id"] + "/" + mode),
            "releaseId": manifest["release"]["id"],
            "carrierMode": mode,
            "manifestByteSize": len(raw_manifest),
            "manifestSHA256": mmic.digest(raw_manifest),
            "embeddedRealizations": [
                {"realizationId": rid, "path": names[rid]} for rid in selected
            ],
            "completeGroupIds": completed,
        }
        workspaces[mode] = {
            "mimetype": vao06.MIMETYPE.encode(),
            "vao-manifest.json": raw_manifest,
            "META-INF/vao-carrier.json": encoded(carrier),
            **{names[rid]: payload[rid] for rid in selected},
        }
    return workspaces


def build_all():
    examples = {
        "roll": {"controls": True, "comparison": True},
        "disc": {"kind": "cyclic", "controls": True},
        "projection-disc": {"kind": "cyclic", "signal": "impulse"},
        "helical-barrel": {"kind": "cylindrical", "signal": "impulse"},
        "reverse-roll": {"reverse": True},
        "native-latch": {"signal": "latch"},
        "native-envelope": {"signal": "envelope"},
        "offset-envelope": {"signal": "envelope", "reader_offset": 1},
        "reverse-envelope": {"signal": "envelope", "reverse": True},
        "native-only": {"native_only": True},
        "design-only": {"design": True},
        "fabricated-design": {"design": True, "fabricated": True},
        "documentary-unknown": {"documentary": True},
        "collection-multipart": {"documentary": True},
        "selected-hypothesis": {},
        "corrected-interpretation": {},
    }
    result = {}
    for name, arguments in examples.items():
        data, manifest, payload, names, asset = make(name, **arguments)
        if name == "documentary-unknown":
            data["states"][0]["geometry"]["kind"] = "undetermined"
            data["states"][0]["geometry"]["status"] = "undetermined"
            data["states"][0]["coverage"]["status"] = "unknown"
            data["states"][0]["geometry"].pop("bounds")
            data["states"][0]["geometry"].pop("unit")
            data["states"][0]["geometry"]["direction"] = "undetermined"
            data["programmes"][0]["extent"] = None
        if name == "selected-hypothesis":
            data["assignments"][0]["status"] = "hypothesis"
            data["interpretations"][0]["extensions"] = {mmic.NS + "experimental": True}
        if name == "corrected-interpretation":
            previous = data["interpretations"][0]
            replacement = copy.deepcopy(previous)
            replacement.update(
                id=uid(name + "/replacement"), predecessorId=previous["id"]
            )
            replacement["execution"]["reproducibility"] = "documented"
            for index, event in enumerate(replacement["events"]):
                event["id"] = uid(name + f"/replacement-event/{index}")
            replacement["nativeRealizationId"] = asset(
                "replacement-native.json", encoded(replacement["events"])
            )
            data["interpretations"].append(replacement)
            data["corrections"] = [
                {
                    "id": uid(name + "/correction"),
                    "targetId": previous["id"],
                    "replacementTargetId": replacement["id"],
                    "previousInterpretationId": previous["id"],
                    "replacementInterpretationId": replacement["id"],
                    "agentId": data["evidence"][0]["agentId"],
                    "reason": "Synthetic review qualifies the execution reproducibility claim; retain both versions.",
                    "previousValue": {
                        "execution": copy.deepcopy(previous["execution"])
                    },
                    "replacementValue": {
                        "execution": copy.deepcopy(replacement["execution"])
                    },
                    "evidenceIds": [data["evidence"][0]["id"]],
                }
            ]
        if name == "collection-multipart":
            first = data["carriers"][0]["id"]
            physical2, digital2 = uid(name + "/physical2"), uid(name + "/digital2")
            state2, programme2, observation2 = (
                uid(name + "/" + x) for x in ("state2", "programme2", "observation2")
            )
            c = copy.deepcopy(data["carriers"][0])
            c.update(id=physical2, digitalEntityId=digital2)
            data["carriers"].append(c)
            s = copy.deepcopy(data["states"][0])
            s.update(id=state2, carrierId=physical2)
            data["states"].append(s)
            p = copy.deepcopy(data["programmes"][0])
            p.update(id=programme2, stateId=state2)
            data["programmes"].append(p)
            o = copy.deepcopy(data["observations"][0])
            o.update(id=observation2, stateId=state2)
            data["observations"].append(o)
            for old, new in [
                (first, physical2),
                (data["carriers"][0]["digitalEntityId"], digital2),
            ]:
                e = copy.deepcopy(
                    next(x for x in manifest["entities"] if x["id"] == old)
                )
                e["id"] = new
                manifest["entities"].append(e)
            parts = []
            for index in range(2):
                parts.append(
                    {
                        "id": uid(name + f"/part/{index}"),
                        "stateId": data["states"][0]["id"],
                        "sequence": index,
                        "face": "front",
                        "extent": [index * 50, (index + 1) * 50],
                        "coverage": {
                            "status": "partial",
                            "scope": "Selected panel; joining region unobserved",
                        },
                        "evidenceIds": [data["evidence"][0]["id"]],
                    }
                )
            data["parts"] = parts
            data["programmes"][0]["partIds"] = [x["id"] for x in parts]
            data["programmes"][0]["selection"] = {
                "kind": "multipart",
                "label": "Two ordered panels with incomplete join evidence",
            }
            manifest["focusEntityIds"].append(physical2)
        for mode, files in seal(data, manifest, payload, names, asset).items():
            for path, raw in files.items():
                result[f"{name}/{mode}/{path}"] = raw
            stream = io.BytesIO()
            with zipfile.ZipFile(
                stream, "w", compression=zipfile.ZIP_STORED
            ) as archive:
                for path in (
                    "mimetype",
                    "vao-manifest.json",
                    "META-INF/vao-carrier.json",
                    *sorted(p for p in files if p.startswith("payload/")),
                ):
                    if path.startswith("payload/"):
                        with archive.open(
                            vao06.vao03.zip_info(path), "w", force_zip64=True
                        ) as target:
                            target.write(files[path])
                    else:
                        archive.writestr(vao06.vao03.zip_info(path), files[path])
                archive.comment = b"VAO/0.6.0"
            result[f"{name}/{mode}.vao"] = stream.getvalue()
        graph = mmic_rdf.project(data)
        result[f"{name}/projection.ttl"] = (
            "\n".join(sorted(graph.serialize(format="nt").splitlines())) + "\n"
        ).encode()
        context = json.loads(
            (mmic.resource_directory() / "context.jsonld").read_text()
        )["@context"]

        def sort_ld(value):
            if isinstance(value, dict):
                return {k: sort_ld(v) for k, v in sorted(value.items())}
            if isinstance(value, list):
                return sorted(
                    [sort_ld(v) for v in value],
                    key=lambda v: json.dumps(v, sort_keys=True),
                )
            return value

        result[f"{name}/projection.jsonld"] = encoded(
            sort_ld(
                json.loads(
                    graph.serialize(
                        format="json-ld", context=context, auto_compact=True
                    )
                )
            )
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = build_all()
    if args.check:
        actual = {
            p.relative_to(OUTPUT).as_posix(): p.read_bytes()
            for p in OUTPUT.rglob("*")
            if p.is_file() and p.name != "README.md"
        }
        if actual != files:
            different = sorted(
                k for k in set(actual) | set(files) if actual.get(k) != files.get(k)
            )
            raise SystemExit("MMIC fixtures differ: " + ", ".join(different[:15]))
    else:
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        for path, raw in files.items():
            target = OUTPUT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        for path in sorted(OUTPUT.glob("*/preservation-closure")):
            report = vao06.validate(path)
            if not report["valid"]:
                raise SystemExit(
                    f"Invalid generated fixture {path.parent.name}: {report}"
                )
            print(path.parent.name, report["mmic"]["status"], report["mmic"]["levels"])


if __name__ == "__main__":
    main()
