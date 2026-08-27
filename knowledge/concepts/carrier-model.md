---
type: "VAO Reference Concept"
title: "Carrier and materialization model"
description: "How VAO embeds or acquires exact realizations."
status: "stable"
generated: { by: "process:codex-rc2-hardening", at: "2026-08-26T00:00:00+02:00" }
sources:
  - id: "vao-standard-carrier"
    resource: "../../Docs/VAO_STANDARD_0.4.0.md#19-carrier-and-workspace-format"
    title: "VAO 0.4.0 carrier and workspace contract"
  - id: "vao-dynamic-profile"
    resource: "../../Docs/VAO_DYNAMIC_DELIVERY_PROFILE_0.4.0.md"
    title: "VAO Dynamic Delivery profile 0.4.0"
---

# Carriers and materialization

A carrier transports an immutable manifest plus selected exact files. Bootstrap carriers include at least one realization; custom carriers include an explicit subset; preservation closures include every realization and mark all groups complete.

Remote materialization is optional and untrusted until decoded byte size and SHA-256 match. Cache state is recorded in a receipt, not by modifying the release.
