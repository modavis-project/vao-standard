#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Create a new unpublished 0.6 candidate from a complete local 0.5 workspace."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import uuid

import vao05
import vao06


def migrate(source, destination, receipt):
    started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = vao05.validate(source)
    if not report["valid"] or not source.is_dir():
        raise ValueError("Migration requires a valid original 0.5 workspace")
    if (
        destination.resolve().is_relative_to(source.resolve())
        or receipt.resolve().is_relative_to(source.resolve())
        or receipt.resolve().is_relative_to(destination.resolve())
    ):
        raise ValueError(
            "Migration outputs must be separate from source and receipt separate from carrier workspace"
        )
    if (
        destination.exists()
        or destination.is_symlink()
        or receipt.exists()
        or receipt.is_symlink()
    ):
        raise ValueError("Migration output/receipt already exists")
    before_bytes = (source / "vao-manifest.json").read_bytes()
    before = vao05.strict_json_bytes(before_bytes, "source manifest")
    carrier, _ = vao05.load_json(source / vao05.CARRIER_NAME)
    if {x["id"] for x in before["realizations"]} != {
        x["realizationId"] for x in carrier["embeddedRealizations"]
    }:
        raise ValueError("Materialize the original complete closure before migration")
    source_hash = hashlib.sha256(before_bytes).hexdigest()
    uid = lambda key: (
        "urn:uuid:"
        + str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"VAO/migration/{source_hash}/{started}/{key}/0.6.0",
            )
        )
    )
    value = copy.deepcopy(before)
    value["id"] = uid("manifest")
    for rights in value["rights"]:
        if before["id"] in rights["appliesToIds"]:
            rights["appliesToIds"].append(value["id"])
    value["$schema"] = vao06.SCHEMA_URI
    value["@context"][0] = vao06.CONTEXT_URI
    value["formatVersion"] = vao06.FORMAT_VERSION
    value["release"] = {
        **value["release"],
        "id": uid("release"),
        "revision": value["release"]["revision"] + 1,
        "migratedFromManifestSHA256": source_hash,
    }
    changed_profiles = {}
    for registry in ("profiles", "materializableProfiles"):
        for profile in value[registry]:
            old = profile["id"]
            if old in vao05.REQUIRED_PROFILE_CAPABILITIES or old in (
                vao05.ACOUSTICS_PROFILE,
                vao05.ZENODO_PROFILE,
            ):
                profile["id"] = old.rsplit("/", 1)[0] + "/" + vao06.FORMAT_VERSION
                changed_profiles[old] = profile["id"]
            profile["version"] = vao06.FORMAT_VERSION
    value["conformsTo"] = [changed_profiles.get(x, x) for x in value["conformsTo"]]
    for group in value["assetGroups"]:
        group["materializesProfileIds"] = [
            changed_profiles.get(x, x) for x in group["materializesProfileIds"]
        ]
    value["modavisBinding"]["mappingIRI"] = vao06.BASE + "/modavis-mapping"
    value["modavisBinding"]["mappingVersion"] = vao06.FORMAT_VERSION
    value["integrity"].pop("schemaBundleDigest", None)
    # Keep every original byte realization and identifier. Old delivery locators
    # describe old carriers and are preserved in the migration snapshot, not
    # misrepresented as the new release's delivery infrastructure.
    old_distributions = value["distributions"]
    value["distributions"] = []
    for realization in value["realizations"]:
        realization["distributionIds"] = []
    value.setdefault("extensions", {})[
        "https://w3id.org/modavis/vao/ontology#migrationSource"
    ] = {
        "manifestSHA256": source_hash,
        "originalReleaseId": before["release"]["id"],
        "originalDistributions": old_distributions,
        "originalExtensions": copy.deepcopy(before.get("extensions", {})),
        "prototypeMMICPromoted": False,
    }
    value["entities"].append(
        {
            "id": before["id"],
            "kind": "source-manifest",
            "types": ["http://www.w3.org/ns/prov#Entity"],
            "labels": {"en": "Exact preserved migration source manifest"},
        }
    )
    value["entities"].append(
        {
            "id": before["release"]["id"],
            "kind": "source-release",
            "types": ["http://www.w3.org/ns/prov#Entity"],
            "labels": {"en": "Original preserved semantic release"},
        }
    )
    agent, activity, protocol, environment = (
        uid(x) for x in ("agent", "activity", "protocol", "environment")
    )
    value["scientific"]["agents"].append(
        {
            "id": agent,
            "agentKind": "software-agent",
            "labels": {"en": "VAO candidate metadata migrator"},
        }
    )
    value["scientific"]["protocols"].append(
        {
            "id": protocol,
            "version": vao06.FORMAT_VERSION,
            "labels": {"en": "Complete-closure 0.5 migration"},
            "procedure": "Preserve exact asset bytes and continuing identities; create new envelope/release/carrier; retain source hash, extensions and old delivery declarations.",
        }
    )
    value["scientific"]["softwareEnvironments"].append(
        {
            "id": environment,
            "name": "VAO 0.5 metadata migrator",
            "version": vao06.FORMAT_VERSION,
            "identity": {
                "algorithm": "sha256",
                "value": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
            "identityScope": "source-file",
            "identityDescription": "Exact distributed Tools/migrate_vao05.py bytes",
            "runtimeDescription": "CPython >=3.11; no MIDI regeneration",
        }
    )
    value["scientific"]["activities"].append(
        {
            "id": activity,
            "activityKind": "migration",
            "startedAt": started,
            "endedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agentIds": [agent],
            "inputIds": [before["id"]],
            "outputIds": [value["release"]["id"]],
            "protocolId": protocol,
            "softwareEnvironmentId": environment,
            "parameterValues": {
                "https://w3id.org/modavis/vao/ontology#sourceManifestSHA256": source_hash
            },
        }
    )
    result = vao06.validate_manifest(value)
    if not result["valid"]:
        raise ValueError(
            "Migration requires additional explicit domain/delivery decisions: "
            + "; ".join(result["errors"][:5])
        )
    created = False
    receipt_created = False
    try:
        destination.mkdir(parents=True)
        created = True
        (destination / "mimetype").write_bytes(vao06.MIMETYPE.encode())
        (destination / "META-INF").mkdir()
        for mapping in carrier["embeddedRealizations"]:
            path = mapping["path"]
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / path, target)
        raw = vao06.json_bytes(value)
        carrier.update(
            {
                "$schema": vao06.BASE + "/schema/carrier.json",
                "formatVersion": vao06.FORMAT_VERSION,
                "id": uid("carrier"),
                "releaseId": value["release"]["id"],
                "manifestSHA256": hashlib.sha256(raw).hexdigest(),
                "manifestByteSize": len(raw),
                "carrierMode": "preservation-closure",
            }
        )
        (destination / "vao-manifest.json").write_bytes(raw)
        vao06.write_json(destination / vao06.CARRIER_NAME, carrier)
        validated = vao06.validate(destination)
        if not validated["valid"]:
            raise ValueError(
                "New migration workspace invalid: " + "; ".join(validated["errors"][:5])
            )
        output = {
            "sourceSHA256": source_hash,
            "outputSHA256": hashlib.sha256(raw).hexdigest(),
            "sourceFormatVersion": "0.5.0",
            "outputFormatVersion": vao06.FORMAT_VERSION,
            "newIds": [value["id"], value["release"]["id"], carrier["id"]],
            "unchangedRealizationIds": [x["id"] for x in before["realizations"]],
            "profileMappings": changed_profiles,
            "losses": [],
            "omissions": [],
            "deliveryChange": "Original distributions retained as source evidence; complete new local closure",
            "prototypeMMICPromoted": False,
            "validation": validated,
        }
        receipt.parent.mkdir(parents=True, exist_ok=True)
        with receipt.open("x", encoding="utf-8") as stream:
            receipt_created = True
            stream.write(json.dumps(output, indent=2) + "\n")
        return output
    except Exception:
        if receipt_created:
            receipt.unlink()
        if created:
            shutil.rmtree(destination)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    migrate(args.source, args.destination, args.receipt)


if __name__ == "__main__":
    main()
