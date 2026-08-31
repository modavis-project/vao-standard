---
type: "VAO Reference Concept"
title: "Role-specific conformance"
description: "Why VAO support is stated by implementation role and profile."
status: "stable"
sources:
  - id: "vao-conformance"
    resource: "../../Docs/VAO_CONFORMANCE_0.4.0.md"
    title: "VAO 0.4.0 conformance specification"
---

# Conformance roles

Validator, reader, writer, carrier writer, extractor, materializer, linked-data projector, repository projector, deterministic runtime, and profile processor are separate claims. An implementation states exact roles, profiles, capabilities, resource limits, and known limitations.

Schema validity alone is not VAO conformance: semantic references, profiles, carrier closure, exact bytes, and claimed capabilities also pass.
