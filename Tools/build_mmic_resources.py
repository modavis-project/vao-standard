#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate the self-contained, hash-pinned MMIC module and trusted registry."""

from __future__ import annotations

import argparse
import hashlib
import json

import build_mmic_schema
import mmic


def outputs():
    schema = build_mmic_schema.build()
    names = set()

    def walk(value):
        if isinstance(value, dict):
            names.update(value.get("properties", {}))
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(schema)
    prefix = (
        "@prefix mmic: <" + mmic.NS + "> .\n"
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
    )
    vocabulary = (
        prefix
        + f'<{mmic.NS[:-1]}> a owl:Ontology ; owl:versionIRI <{mmic.ONTOLOGY_VERSION}> ; owl:versionInfo "{mmic.VERSION}" ; rdfs:comment "Standalone mechanical-music module governed by VAO maintainers; not an accepted MODAVIS Network module."@en .\n'
    )
    classes = [
        "PhysicalCarrier",
        "DigitalCarrier",
        "CarrierState",
        "CarrierPart",
        "Observation",
        "ModelAssignment",
        "Track",
        "RoleAssignment",
        "Interpretation",
        "Comparison",
        "EvidenceClaim",
        "Correction",
        "EncodedProgramme",
        "ObservedFeature",
        "ReadingModel",
        "NativeSignal",
        "MidiExportBinding",
        "ObservedPlayback",
        "CarrierDesign",
        "FabricationActivity",
        "GeometryLocation",
        "DomainDocument",
        "Object",
        "Array",
    ]
    for name in classes:
        vocabulary += f'mmic:{name} a owl:Class ; rdfs:label "{name}"@en .\n'
    for name in sorted(names | {"keys", "length"}):
        vocabulary += f'mmic:{name} a rdf:Property ; rdfs:label "{name}"@en .\n'
    vocabulary += "mmic:Null a owl:NamedIndividual .\n"
    vocabulary += "mmic:ControlFunction a skos:ConceptScheme .\n"
    vocabulary += 'mmic:Sustain a skos:Concept ; skos:inScheme mmic:ControlFunction ; skos:prefLabel "Sustain"@en ; skos:scopeNote "Use CC64 when the selected export is MIDI 1.0 control change; native mechanical meaning remains model-qualified."@en .\n'
    vocabulary += 'mmic:SoftPedal a skos:Concept ; skos:inScheme mmic:ControlFunction ; skos:prefLabel "Soft pedal"@en ; skos:scopeNote "Use CC67 when the selected export is MIDI 1.0 control change; native mechanical meaning remains model-qualified."@en .\n'
    concepts = {}
    for definition in schema["$defs"].values():
        for field, prop in definition.get("properties", {}).items():
            if "enum" in prop:
                concepts.setdefault(field, set()).update(prop["enum"])
    for field, values in sorted(concepts.items()):
        vocabulary += f'<{mmic.NS}scheme/{field}> a skos:ConceptScheme ; rdfs:label "{field}"@en .\n'
        for value in sorted(values):
            vocabulary += f'<{mmic.NS}concept/{field}/{value}> a skos:Concept ; skos:inScheme <{mmic.NS}scheme/{field}> ; skos:prefLabel "{value}"@en .\n'
    context = {"@context": {"@protected": True, "@vocab": mmic.NS, "mmic": mmic.NS}}
    for name in sorted(names):
        context["@context"][name] = mmic.NS + name
    shapes = (
        prefix
        + '''@prefix sh: <http://www.w3.org/ns/shacl#> .
mmic:LocationShape a sh:NodeShape ; sh:targetClass mmic:GeometryLocation ;
 sh:property [ sh:path mmic:kind ; sh:minCount 1 ; sh:maxCount 1 ; sh:in ("point" "interval") ] ;
 sh:property [ sh:path mmic:start ; sh:minCount 1 ; sh:maxCount 1 ] ;
 sh:property [ sh:path mmic:end ; sh:minCount 1 ; sh:maxCount 1 ] ;
 sh:sparql [ sh:message "Point endpoints must coincide on every axis (MMIC-07)." ; sh:select """
 PREFIX mmic: <https://w3id.org/modavis/vao/mmic#>
 SELECT $this WHERE { $this mmic:kind "point" ; mmic:start ?s ; mmic:end ?e .
 OPTIONAL { $this mmic:axialStart ?a . } OPTIONAL { $this mmic:axialEnd ?b . }
 OPTIONAL { $this mmic:startTurn ?u . } OPTIONAL { $this mmic:endTurn ?v . }
 FILTER(?s != ?e || (BOUND(?a) != BOUND(?b)) || (BOUND(?a) && ?a != ?b) ||
 (BOUND(?u) != BOUND(?v)) || (BOUND(?u) && ?u != ?v)) }
 """ ] .
'''
    )
    mapping = (
        prefix
        + """@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
# Informative mappings only. No imports or subclass entailments are added to core MMIC.
mmic:PhysicalCarrier skos:closeMatch <http://www.cidoc-crm.org/cidoc-crm/E84_Information_Carrier> .
mmic:DigitalCarrier skos:relatedMatch <http://www.europeana.eu/schemas/edm/WebResource> .
"""
    )
    return {
        "mechanical-music.ttl": vocabulary.encode(),
        "context.jsonld": (json.dumps(context, indent=2) + "\n").encode(),
        "shapes.ttl": shapes.encode(),
        "optional-alignments.ttl": mapping.encode(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    directory = mmic.resource_directory()
    generated = outputs()
    for name, data in generated.items():
        if args.check:
            if (directory / name).read_bytes() != data:
                raise SystemExit(f"Generated MMIC resource differs: {name}")
        else:
            (directory / name).write_bytes(data)
    artifacts = []
    for name in ["mmic.schema.json", *generated]:
        data = (directory / name).read_bytes()
        artifacts.append(
            {
                "path": name,
                "byteSize": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    catalog = {
        "profile": mmic.PROFILE,
        "specificationVersion": mmic.VERSION,
        "ontologyVersionIRI": mmic.ONTOLOGY_VERSION,
        "networkResolution": False,
        "normativeImportClosure": ["mechanical-music.ttl"],
        "artifacts": artifacts,
        "optionalAlignments": {
            "CRM": "7.1.3",
            "EDM": "5.2.8",
            "status": "informative mappings only; receiving-profile compliance is not asserted",
        },
    }
    registry = {
        "id": mmic.PROFILE,
        "specificationVersion": mmic.VERSION,
        "status": "released",
        "owner": "VAO maintainers",
        "envelopeVersions": ["0.6.0"],
        "capabilities": mmic.CAPABILITIES,
        "dependencyCatalogSHA256": hashlib.sha256(
            (json.dumps(catalog, indent=2) + "\n").encode()
        ).hexdigest(),
        "supportedTopologies": [
            "linear",
            "cyclic",
            "cylindrical with complete piecewise-linear reader path",
        ],
        "supportedExports": [
            "SMF 0/1 PPQN; explicit fixed initial tempo; note and CC 0..119"
        ],
        "unsupportedExecution": [
            "segmented transport",
            "unknown geometry",
            "uncalibrated timing",
            "SysEx",
            "SMPTE",
            "MPE",
        ],
        "historicalCertification": "not established",
        "resolvableNamespaceClaim": False,
    }
    for name, value in [("dependencies.json", catalog), ("registry.json", registry)]:
        data = (json.dumps(value, indent=2) + "\n").encode()
        if args.check:
            if (directory / name).read_bytes() != data:
                raise SystemExit(f"MMIC catalog/registry differs: {name}")
        else:
            (directory / name).write_bytes(data)


if __name__ == "__main__":
    main()
