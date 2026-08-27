---
type: "VAO Reference Concept"
title: "Semantic release, logical asset, and realization"
description: "How VAO separates identity from exact bytes."
status: "stable"
generated: { by: "process:codex-rc2-hardening", at: "2026-08-26T00:00:00+02:00" }
sources:
  - id: "vao-core-concepts"
    resource: "../../Docs/VAO_STANDARD_0.4.0.md#3-core-concepts"
    title: "VAO 0.4.0 core concepts"
---

# Semantic release and realizations

A VAO semantic release is immutable and independent of transport. A logical asset is a meaningful unit; a realization is one exact byte sequence for it. Different encodings or derivatives are different realizations even when they share a logical asset.

Every realization has byte size and SHA-256. Filenames, locations, media types, repository checksums, and signatures do not replace this identity.
