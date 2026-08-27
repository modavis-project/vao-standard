---
type: "VAO Reference Concept"
title: "Canonical JSON and linked-data projection"
description: "Boundary between authoritative VAO JSON and RDF semantics."
status: "stable"
generated: { by: "process:codex-rc2-hardening", at: "2026-08-26T00:00:00+02:00" }
sources:
  - id: "vao-linked-data"
    resource: "../../Docs/VAO_STANDARD_0.4.0.md#21-linked-data-projection"
    title: "VAO 0.4.0 linked-data projection contract"
---

# JSON and linked data

Canonical VAO JSON and exact manifest bytes are authoritative. JSON-LD maps records to RDF nodes, and SHACL validates the semantic projection. RDF does not retain JSON ordering, lexical number form, whitespace, or original bytes, so it cannot recreate or verify the carrier's manifest digest.
