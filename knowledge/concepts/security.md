---
type: "VAO Reference Concept"
title: "VAO security boundaries"
description: "Minimum safe treatment of untrusted carriers and realizations."
status: "stable"
sources:
  - id: "vao-security"
    resource: "../../Docs/SECURITY_CONSIDERATIONS.md"
    title: "VAO security considerations"
---

# Security boundaries

VAO is passive data. Validate ZIP paths/types/compression/budgets, strict JSON, references, carrier closure, and exact bytes before extraction or preview. Paths exclude ASCII controls and are distinct under exact, NFC, and NFC-plus-default-case-fold comparison. Structural and payload reads are bounded while streaming; links and shared hard-link inodes are rejected. Network acquisition is off by default. Media and external renderers run only under explicit authorization and isolation.

Fixity, authenticity, authorization, scientific validity, safety, and consent are independent decisions.
