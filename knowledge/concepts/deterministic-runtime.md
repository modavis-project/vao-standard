---
type: "VAO Reference Concept"
title: "Deterministic runtime and offline trace scope"
description: "Boundary between full host behaviour and the supplied offline verifier."
status: "stable"
sources:
  - id: "vao-runtime-standard"
    resource: "../../Docs/VAO_STANDARD_0.4.0.md#17-deterministic-runtime-profile"
    title: "VAO 0.4.0 deterministic runtime contract"
  - id: "vao-runtime-profile"
    resource: "../../Docs/VAO_DETERMINISTIC_RUNTIME_PROFILE_0.4.0.md"
    title: "VAO Deterministic Runtime profile 0.4.0"
---

# Deterministic runtime scope

VAO fixes locale-independent string/event/action ordering, snapshot guards, conflict policies, per-event microstep bounds, PCG/xoshiro generation, and unbiased integer stochastic selection. A stochastic Process selects from its direct actions followed by direct children before expanding the selected child. A full live host additionally implements declared queue, lateness, delay, process, and voice policies.

The supplied offline verifier covers already-available events, transition state/actions, immediate completed one-shot/compound/stochastic Process expansion, stochastic choice, emitted records, and render-binding selection. Expanded Process actions are losslessly recorded requests rather than applied transition effects. It rejects timing-constrained or lifecycle Processes and does not prove live scheduling, voice lifecycle, media rendering, perceptual equivalence, or bit-identical audio.
