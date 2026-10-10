#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Lossless, ordered MMIC JSON/RDF projection with bounded offline inversion."""

from __future__ import annotations

from urllib.parse import quote

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

import mmic

M = Namespace(mmic.NS)
MAX_TRIPLES = 250000


def project(data):
    errors = mmic.schema_errors(data)
    mmic.require(not errors, "MMIC-03", "; ".join(errors[:3]))
    graph = Graph()
    graph.bind("mmic", M)
    root = URIRef(data["id"])
    counter = [0]

    def node():
        counter[0] += 1
        return BNode(f"mmic{counter[0]}")

    def encode(value, subject=None, reference=False, opaque=False):
        if isinstance(value, dict):
            subject = subject or (
                URIRef(value["id"]) if "id" in value and not opaque else node()
            )
            graph.add((subject, RDF.type, M.Object))
            if (
                not opaque
                and "start" in value
                and "end" in value
                and value.get("kind") in ("point", "interval")
            ):
                graph.add((subject, RDF.type, M.GeometryLocation))
            keys = []
            for key, child in sorted(value.items()):
                predicate = URIRef(mmic.NS + quote(key, safe=""))
                keys.append(Literal(key))
                graph.add(
                    (
                        subject,
                        predicate,
                        encode(
                            child,
                            reference=key.endswith(("Id", "Ids", "IRI"))
                            and key != "id"
                            and not opaque,
                            opaque=opaque or key == "extensions",
                        ),
                    )
                )
            graph.add((subject, M.keys, encode(keys)))
            return subject
        if isinstance(value, list):
            subject = node()
            graph.add((subject, RDF.type, M.Array))
            graph.add((subject, M.length, Literal(len(value))))
            for index, child in enumerate(value):
                graph.add(
                    (
                        subject,
                        URIRef(mmic.NS + "index/" + str(index)),
                        child
                        if isinstance(child, Literal)
                        else encode(child, reference=reference, opaque=opaque),
                    )
                )
            return subject
        if value is None:
            return M.Null
        return URIRef(value) if reference and isinstance(value, str) else Literal(value)

    encode(data, root)
    classes = {
        "carriers": "PhysicalCarrier",
        "states": "CarrierState",
        "programmes": "EncodedProgramme",
        "parts": "CarrierPart",
        "observations": "Observation",
        "features": "ObservedFeature",
        "models": "ReadingModel",
        "assignments": "ModelAssignment",
        "tracks": "Track",
        "roleAssignments": "RoleAssignment",
        "interpretations": "Interpretation",
        "playbacks": "ObservedPlayback",
        "comparisons": "Comparison",
        "designs": "CarrierDesign",
        "fabrications": "FabricationActivity",
        "evidence": "EvidenceClaim",
        "corrections": "Correction",
    }
    for registry, classname in classes.items():
        for record in data[registry]:
            graph.add((URIRef(record["id"]), RDF.type, M[classname]))
    for model in data["models"]:
        for binding in model["spec"]["exportBindings"]:
            graph.add((URIRef(binding["id"]), RDF.type, M.MidiExportBinding))
    for interpretation in data["interpretations"]:
        for event in interpretation["events"]:
            graph.add((URIRef(event["id"]), RDF.type, M.NativeSignal))
    graph.add((root, RDF.type, M.DomainDocument))
    mmic.require(
        len(graph) <= MAX_TRIPLES, "MMIC-15", "projection exceeds graph budget"
    )
    return graph


def inverse(graph):
    mmic.require(len(graph) <= MAX_TRIPLES, "MMIC-15", "graph exceeds triple budget")
    mmic.require(
        not list(
            graph.triples((None, URIRef("http://www.w3.org/2002/07/owl#imports"), None))
        ),
        "MMIC-15",
        "untrusted RDF imports are forbidden",
    )
    roots = list(graph.subjects(RDF.type, M.DomainDocument))
    mmic.require(len(roots) == 1, "MMIC-03", "RDF must have one MMIC document root")
    active = set()
    visited = set()

    def one(subject, predicate):
        values = list(graph.objects(subject, predicate))
        mmic.require(len(values) == 1, "MMIC-03", "missing or ambiguous RDF field")
        return values[0]

    def decode(subject, depth=0, reference=False):
        if reference and isinstance(subject, URIRef):
            return str(subject)
        mmic.require(
            depth <= mmic.MAX_DEPTH and subject not in active,
            "MMIC-15",
            "RDF structure has a cycle or excessive depth",
        )
        if subject == M.Null:
            return None
        if isinstance(subject, Literal):
            value = subject.toPython()
            mmic.require(
                isinstance(value, (str, int, float, bool)),
                "MMIC-03",
                "unsupported RDF literal datatype",
            )
            return value
        visited.add(subject)
        active.add(subject)
        types = set(graph.objects(subject, RDF.type))
        if M.Array in types:
            length = int(one(subject, M.length))
            mmic.require(
                0 <= length <= 10000, "MMIC-15", "RDF array outside length budget"
            )
            predicates = {str(p) for p in graph.predicates(subject)}
            expected = {str(RDF.type), str(M.length)} | {
                mmic.NS + "index/" + str(i) for i in range(length)
            }
            mmic.require(
                predicates == expected,
                "MMIC-03",
                "RDF array has extra/missing ordered members",
            )
            result = [
                decode(
                    one(subject, URIRef(mmic.NS + "index/" + str(i))),
                    depth + 1,
                    reference=reference,
                )
                for i in range(length)
            ]
        else:
            mmic.require(
                M.Object in types,
                "MMIC-03",
                "RDF resource is not an encoded domain object",
            )
            keys = decode(one(subject, M.keys), depth + 1)
            mmic.require(
                isinstance(keys, list)
                and all(isinstance(k, str) for k in keys)
                and len(keys) == len(set(keys)),
                "MMIC-03",
                "RDF field ordering has duplicate/invalid keys",
            )
            expected = {str(RDF.type), str(M.keys)} | {
                mmic.NS + quote(k, safe="") for k in keys
            }
            mmic.require(
                {str(p) for p in graph.predicates(subject)} == expected,
                "MMIC-03",
                "RDF object has undeclared fields",
            )
            result = {
                k: decode(
                    one(subject, URIRef(mmic.NS + quote(k, safe=""))),
                    depth + 1,
                    reference=k.endswith(("Id", "Ids", "IRI")) and k != "id",
                )
                for k in keys
            }
        active.remove(subject)
        return result

    result = decode(roots[0])
    mmic._domain(result)
    mmic.require(
        all(s in visited for s in graph.subjects()),
        "MMIC-03",
        "unreachable RDF claims are not part of the normalized projection",
    )
    errors = mmic.schema_errors(result)
    mmic.require(not errors, "MMIC-03", "; ".join(errors[:3]))
    from rdflib.compare import isomorphic

    mmic.require(
        isomorphic(graph, project(result)),
        "MMIC-03",
        "RDF contains undeclared or inconsistent projection claims",
    )
    return result


def validate(data, manifest, read_asset):
    from pyshacl import validate as shacl_validate

    mmic.require(
        len(data) <= mmic.MAX_BYTES, "MMIC-15", "RDF source exceeds byte budget"
    )
    graph = Graph().parse(data=data, format="turtle")
    mmic.require(len(graph) <= MAX_TRIPLES, "MMIC-15", "RDF exceeds graph budget")
    shapes = Graph().parse(mmic.resource_directory() / "shapes.ttl", format="turtle")
    ontology = Graph().parse(
        mmic.resource_directory() / "mechanical-music.ttl", format="turtle"
    )
    conforms, _, report = shacl_validate(
        graph,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="rdfs",
        do_owl_imports=False,
        advanced=False,
    )
    mmic.require(conforms, "MMIC-03/07", str(report))
    return mmic.validate_domain(inverse(graph), manifest, read_asset)
