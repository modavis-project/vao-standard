#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the MMIC candidate schema from the original VAO 0.6 domain contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VERSION = "1.0.0"
BASE = f"https://w3id.org/modavis/vao/profile/mmic/{VERSION}"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "Profiles/MMIC" / VERSION / "mmic.schema.json"


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


def array(value, minimum=0):
    return {"type": "array", "items": value, "minItems": minimum, "maxItems": 10000}


def enum(*values):
    return {"enum": list(values)}


def obj(properties, optional=()):
    return {
        "type": "object",
        "required": [k for k in properties if k not in optional],
        "properties": properties,
        "additionalProperties": False,
    }


def build():
    text = {"type": "string", "minLength": 1, "maxLength": 8192}
    number = {"type": "number", "minimum": -1e12, "maximum": 1e12}
    positive = {"type": "number", "exclusiveMinimum": 0, "maximum": 1e12}
    nonnegative = {"type": "number", "minimum": 0, "maximum": 1e12}
    identifier = {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2048}
    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    index = {"type": "integer", "minimum": 0, "maximum": 10000}
    ids = {**array(identifier), "uniqueItems": True}
    evidence = {**ids, "minItems": 1}
    extensions = {"type": "object", "maxProperties": 100}
    defs = {}

    def record(name, fields, optional=(), proof=True):
        fields = {
            "id": identifier,
            **fields,
            **({"evidenceIds": evidence} if proof else {}),
            "extensions": extensions,
        }
        defs[name] = obj(fields, (*optional, "extensions"))

    bounds = array(number, 2)
    bounds["maxItems"] = 2
    defs["geometry"] = obj(
        {
            "kind": enum("linear", "cyclic", "cylindrical", "undetermined"),
            "status": enum("measured", "estimated", "assumed", "undetermined"),
            "unit": identifier,
            "bounds": bounds,
            "origin": text,
            "orientation": text,
            "direction": enum("forward", "reverse"),
            "period": positive,
            "axialUnit": identifier,
            "axialBounds": bounds,
        },
        ("period", "axialUnit", "axialBounds"),
    )
    defs["geometry"]["required"] = [
        "kind",
        "status",
        "origin",
        "orientation",
        "direction",
    ]
    defs["geometry"]["allOf"] = [
        {
            "if": {"properties": {"kind": {"const": "undetermined"}}},
            "then": {"properties": {"status": {"const": "undetermined"}}},
            "else": {"required": ["unit", "bounds"]},
        }
    ]
    defs["geometry"]["properties"]["direction"] = enum(
        "forward", "reverse", "undetermined"
    )
    defs["coverage"] = obj(
        {
            "status": enum("complete", "partial", "unknown"),
            "scope": text,
            "missingRegions": array(bounds),
        },
        ("missingRegions",),
    )
    record(
        "carrier",
        {
            "digitalEntityId": identifier,
            "encoding": enum(
                "perforated-roll",
                "perforated-disc",
                "projection-disc",
                "pinned-barrel",
                "other",
                "undetermined",
            ),
            "origin": enum("historical", "generated", "synthetic", "unknown"),
            "externalIdentifiers": array(
                obj(
                    {
                        "issuer": identifier,
                        "scheme": identifier,
                        "value": text,
                        "scope": text,
                    }
                )
            ),
        },
        ("externalIdentifiers",),
    )
    record(
        "state",
        {
            "carrierId": identifier,
            "geometry": ref("geometry"),
            "coverage": ref("coverage"),
            "predecessorId": identifier,
            "changeKind": enum("description", "physical-intervention"),
            "interventionActivityId": identifier,
        },
        ("predecessorId", "changeKind", "interventionActivityId"),
    )
    record(
        "programme",
        {
            "stateId": identifier,
            "extent": {"anyOf": [bounds, {"type": "null"}]},
            "selection": obj(
                {"kind": enum("whole", "region", "helical", "multipart"), "label": text}
            ),
            "partIds": ids,
        },
        ("partIds",),
    )
    record(
        "part",
        {
            "stateId": identifier,
            "sequence": index,
            "face": text,
            "extent": bounds,
            "coverage": ref("coverage"),
            "joins": ids,
        },
        ("joins",),
    )
    record(
        "observation",
        {
            "stateId": identifier,
            "sourceRealizationId": identifier,
            "activityId": identifier,
            "sourceBounds": array(bounds, 1),
            "coverage": ref("coverage"),
        },
    )
    defs["location"] = obj(
        {
            "kind": enum("point", "interval"),
            "start": number,
            "end": number,
            "startTurn": {"type": "integer", "minimum": -10000, "maximum": 10000},
            "endTurn": {"type": "integer", "minimum": -10000, "maximum": 10000},
            "wrapsSeam": {"type": "boolean"},
            "axialStart": number,
            "axialEnd": number,
        },
        ("startTurn", "endTurn", "wrapsSeam", "axialStart", "axialEnd"),
    )
    record(
        "feature",
        {
            "observationId": identifier,
            "stateId": identifier,
            "programmeId": identifier,
            "trackId": identifier,
            "kind": enum(
                "perforation",
                "slot",
                "projection",
                "pin",
                "bridge",
                "print",
                "damage",
                "unknown",
            ),
            "location": ref("location"),
            "selector": array(bounds, 1),
            "value": number,
            "samples": array(obj({"position": number, "value": number}), 2),
        },
        ("value", "samples"),
    )
    defs["anchor"] = obj(
        {"position": number, "seconds": nonnegative, "uncertaintySeconds": nonnegative}
    )
    defs["trajectoryPoint"] = obj({"position": number, "axial": number})
    defs["timing"] = obj(
        {
            "anchors": array(ref("anchor"), 2),
            "method": {"const": "piecewise-linear"},
            "unit": identifier,
            "timeUnit": {"const": "http://qudt.org/vocab/unit/SEC"},
            "calibrationStatus": enum(
                "measured", "estimated", "assumed", "uncalibrated"
            ),
            "interpolation": {"const": "linear"},
            "extrapolation": {"const": "forbidden"},
            "toleranceSeconds": {"type": "number", "minimum": 0, "maximum": 0.1},
            "basis": text,
        }
    )
    defs["reader"] = obj(
        {
            "domain": bounds,
            "trajectory": array(ref("trajectoryPoint")),
            "interpolation": enum("linear", "none", "undetermined"),
            "delaySeconds": nonnegative,
            "response": text,
            "segmented": {"type": "boolean"},
        }
    )
    defs["binding"] = obj(
        {
            "id": identifier,
            "roleId": identifier,
            "protocol": {"const": "smf-ppqn"},
            "message": enum("note", "control-change"),
            "channel": {"type": "integer", "minimum": 0, "maximum": 15},
            "pitch": {"type": "integer", "minimum": 0, "maximum": 127},
            "controller": {"type": "integer", "minimum": 0, "maximum": 119},
            "velocity": {"type": "integer", "minimum": 1, "maximum": 127},
            "onValue": {"type": "integer", "minimum": 0, "maximum": 127},
            "offValue": {"type": "integer", "minimum": 0, "maximum": 127},
            "initialValue": {"type": "integer", "minimum": 0, "maximum": 127},
            "resetPolicy": enum("event-release", "explicit-final-reset"),
            "durationPolicy": obj(
                {"kind": enum("engagement", "fixed"), "seconds": positive}, ("seconds",)
            ),
            "ticksPerBeat": {"type": "integer", "minimum": 1, "maximum": 32767},
            "tempoMicroseconds": {"type": "integer", "minimum": 1, "maximum": 16777215},
            "rounding": {"const": "nearest-ties-even"},
        },
        (
            "pitch",
            "controller",
            "velocity",
            "onValue",
            "offValue",
            "initialValue",
            "resetPolicy",
            "durationPolicy",
        ),
    )
    defs["modelRole"] = obj(
        {
            "id": identifier,
            "trackIndex": index,
            "readerOffset": number,
            "readerOffsetUnit": identifier,
            "role": enum(
                "note",
                "performance-control",
                "registration",
                "transport",
                "synchronization",
                "guidance",
                "auxiliary",
                "unknown",
            ),
            "target": identifier,
            "signalKind": enum("impulse", "gate", "latch", "envelope", "unresolved"),
            "quantityUnit": identifier,
            "initialValue": number,
            "bindingIds": ids,
            "responseAssumption": text,
        },
        ("target", "quantityUnit", "initialValue"),
    )
    defs["pin"] = obj({"realizationId": identifier, "sha256": digest})
    defs["runtime"] = obj(
        {
            "codeRealizationId": identifier,
            "environmentRealizationId": identifier,
            "algorithm": {"const": "mmic-piecewise-reference-1"},
            "deterministic": {"const": True},
        }
    )
    defs["constraints"] = obj(
        {
            "minimumTarget": number,
            "maximumTarget": number,
            "minimumRepeatSeconds": nonnegative,
            "minimumClearance": nonnegative,
            "material": text,
            "tool": text,
            "unsupportedPolicy": enum("reject", "explicit-exclusions"),
        }
    )
    defs["modelSpec"] = obj(
        {
            "geometry": ref("geometry"),
            "reader": ref("reader"),
            "timing": ref("timing"),
            "roles": array(ref("modelRole"), 1),
            "exportBindings": array(ref("binding")),
            "constraints": ref("constraints"),
            "artifactPins": array(ref("pin"), 1),
            "runtime": ref("runtime"),
            "initialState": extensions,
            "historicalApplicability": text,
        }
    )
    record(
        "model",
        {
            "version": text,
            "spec": ref("modelSpec"),
            "specSHA256": digest,
            "canonicalization": {"const": "RFC8785"},
            "predecessorId": identifier,
        },
        ("predecessorId",),
    )
    record(
        "assignment",
        {
            "modelId": identifier,
            "stateId": identifier,
            "programmeId": identifier,
            "status": enum("accepted", "hypothesis", "rejected", "undetermined"),
            "selected": {"type": "boolean"},
        },
        ("stateId", "programmeId"),
    )
    record(
        "track",
        {
            "modelId": identifier,
            "index": index,
        },
    )
    record(
        "roleAssignment",
        {
            "assignmentId": identifier,
            "trackId": identifier,
            "modelRoleId": identifier,
            "status": enum("accepted", "hypothesis", "rejected", "undetermined"),
        },
    )
    record(
        "event",
        {
            "roleAssignmentId": identifier,
            "sourceFeatureIds": ids,
            "kind": enum("impulse", "gate", "latch", "envelope", "unresolved"),
            "onsetSeconds": nonnegative,
            "durationSeconds": nonnegative,
            "value": number,
            "unit": identifier,
            "samples": array(obj({"seconds": nonnegative, "value": number}), 2),
        },
        ("durationSeconds", "value", "unit", "samples"),
        proof=False,
    )
    defs["execution"] = obj(
        {
            "activityId": identifier,
            "modelSHA256": digest,
            "codeRealizationId": identifier,
            "environmentRealizationId": identifier,
            "reproducibility": enum("deterministic", "documented"),
        }
    )
    defs["export"] = obj(
        {"bindingIds": ids, "realizationId": identifier, "losses": array(text)}
    )
    record(
        "interpretation",
        {
            "modelId": identifier,
            "assignmentId": identifier,
            "modelSHA256": digest,
            "sourceKind": enum("carrier-derived", "audio-derived", "simulated"),
            "sourceRealizationIds": {**ids, "minItems": 1},
            "nativeRealizationId": identifier,
            "events": array(ref("event")),
            "excludedFeatureIds": ids,
            "execution": ref("execution"),
            "exports": array(ref("export")),
            "predecessorId": identifier,
        },
        ("predecessorId",),
    )
    record(
        "playback",
        {
            "recordingKind": enum("physical", "simulated", "unknown"),
            "recordingRealizationId": identifier,
            "instrumentId": identifier,
            "stateId": identifier,
            "programmeId": identifier,
            "operatorAgentId": identifier,
            "protocol": text,
            "conditions": text,
        },
        ("instrumentId", "stateId", "programmeId"),
    )
    defs["alignment"] = obj(
        {
            "anchors": array(obj({"left": nonnegative, "right": nonnegative}), 2),
            "domain": bounds,
            "gapPolicy": enum("explicit-unmatched", "none"),
            "unmatchedLeftEventIds": ids,
            "unmatchedRightEventIds": ids,
            "toleranceSeconds": nonnegative,
        }
    )
    record(
        "comparison",
        {
            "leftInterpretationId": identifier,
            "rightInterpretationId": identifier,
            "playbackId": identifier,
            "alignmentRealizationId": identifier,
            "alignment": ref("alignment"),
            "pairs": array(
                obj({"leftEventId": identifier, "rightEventId": identifier}), 1
            ),
            "metrics": obj(
                {
                    "matchedCoverage": {"type": "number", "minimum": 0, "maximum": 1},
                    "maxResidualSeconds": nonnegative,
                }
            ),
            "referenceStatus": enum("situated-evidence", "synthetic-test"),
        },
    )
    record(
        "design",
        {
            "sourceRealizationId": identifier,
            "modelId": identifier,
            "layoutRealizationId": identifier,
            "reportRealizationId": identifier,
            "execution": ref("execution"),
            "purpose": text,
            "fabricationStatus": enum("design-only", "fabricated"),
        },
    )
    record(
        "fabrication",
        {
            "designId": identifier,
            "carrierId": identifier,
            "stateId": identifier,
            "activityId": identifier,
            "inspectionRealizationId": identifier,
            "measuredGeometry": ref("geometry"),
        },
    )
    record(
        "evidence",
        {
            "sourceIRI": identifier,
            "locator": text,
            "basis": enum("measured", "estimated", "assumed", "synthetic", "unknown"),
            "scope": text,
            "agentId": identifier,
            "reviewStatus": enum("reviewed", "provisional", "unreviewed"),
            "sourceRealizationId": identifier,
            "fragmentBounds": bounds,
        },
        ("sourceRealizationId", "fragmentBounds"),
        proof=False,
    )
    record(
        "correction",
        {
            "targetId": identifier,
            "replacementTargetId": identifier,
            "previousInterpretationId": identifier,
            "replacementInterpretationId": identifier,
            "agentId": identifier,
            "reason": text,
            "previousValue": extensions,
            "replacementValue": extensions,
        },
    )
    fields = {
        "id": identifier,
        "schemaVersion": {"const": VERSION},
        "synthetic": {"type": "boolean"},
        "levels": {
            **array(enum("documentation", "decoding", "comparison", "generation"), 1),
            "uniqueItems": True,
        },
        "extensions": extensions,
        "redactions": array(obj({"realizationId": identifier, "reason": text})),
    }
    registries = {
        "carriers": "carrier",
        "states": "state",
        "programmes": "programme",
        "parts": "part",
        "observations": "observation",
        "features": "feature",
        "models": "model",
        "assignments": "assignment",
        "tracks": "track",
        "roleAssignments": "roleAssignment",
        "interpretations": "interpretation",
        "playbacks": "playback",
        "comparisons": "comparison",
        "designs": "design",
        "fabrications": "fabrication",
        "evidence": "evidence",
        "corrections": "correction",
    }
    fields.update({name: array(ref(kind)) for name, kind in registries.items()})
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + "/schema.json",
        "title": "MMIC 1.0.0 normalized domain model",
        **obj(fields, ("extensions", "redactions")),
        "$defs": defs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = (json.dumps(build(), indent=2, ensure_ascii=False) + "\n").encode()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != data:
            raise SystemExit("MMIC schema differs from its generator")
    else:
        OUTPUT.write_bytes(data)


if __name__ == "__main__":
    main()
