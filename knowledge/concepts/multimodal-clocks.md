---
type: "VAO Reference Concept"
title: "Multimodal clocks and synchronization"
description: "How VAO dimensions clocks and preserves synchronization evidence."
status: "stable"
generated: { by: "process:codex-rc2-hardening", at: "2026-08-27T00:00:00+02:00" }
sources:
  - id: "vao-multimodal-standard"
    resource: "../../Docs/VAO_STANDARD_0.4.0.md#13-multimodal-timeline-profile"
    title: "VAO 0.4.0 multimodal timeline contract"
  - id: "vao-multimodal-profile"
    resource: "../../Docs/VAO_MULTIMODAL_PROFILE_0.4.0.md"
    title: "VAO Multimodal Timeline profile 0.4.0"
---

# Multimodal clocks and synchronization

A Timebase separates coordinate unit from its dimensioned rate and may use a lowest-terms exact rational. Wall clocks and external timecode identify their time scale, preventing UTC, TAI, GPS, POSIX, or SMPTE coordinates from being conflated. RFC 3339-subset instants are compared at their full declared decimal precision; leap-sensitive series use explicit Timebase and discontinuity evidence. Tracks bind exact realizations whose modality, technical kind, rate, clock, and coordinate frame agree.

Piecewise mappings use `target = source × scale + offset`. Segment bounds are source coordinates; offset, residual uncertainty, and jitter are target coordinates. Every following boundary is explicit; a boundary declared `none` is continuous, while reset, dropout, pause, or unknown prevents undocumented interpolation.
