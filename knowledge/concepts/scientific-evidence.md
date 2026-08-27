---
type: "VAO Reference Concept"
title: "Scientific evidence, provenance, and review"
description: "How VAO separates recorded evidence, generation, interpretation, and review."
status: "stable"
generated: { by: "process:codex-rc2-hardening", at: "2026-08-27T00:00:00+02:00" }
sources:
  - id: "vao-scientific-standard"
    resource: "../../Docs/VAO_STANDARD_0.4.0.md#12-scientific-profile"
    title: "VAO 0.4.0 scientific contract"
  - id: "vao-scientific-profile"
    resource: "../../Docs/VAO_SCIENTIFIC_PROFILE_0.4.0.md"
    title: "VAO Scientific profile 0.4.0"
---

# Scientific evidence and review

Observations preserve measured results, units, uncertainty, time, protocol, and Activity context. A registration RMS is meaningful only with an explicit metric space and residual method. Analyses bind exact inputs/outputs, software, parameters, reproducibility, and any declared random source. Generating links are reciprocal with Activity outputs.

Software provenance distinguishes executable, source-file, source-bundle, environment-lock, container, model-weight, and declaration identities. Each digest says what it covers; dependencies are independently typed and hashed. A declaration-only identity, an environment lock without code identity, or source without an environment lock cannot support a deterministic or seeded Analysis or a deterministic Renderer.

Claims express interpretation. Inference names an inference Activity; accepted, rejected, and reviewed Claims cite matching assessed Reviews. Structural conformance proves an internally consistent evidence chain, not calibration quality, method adequacy, peer review, causality, or scientific truth.

Immutable Activity inputs and outputs are disjoint. Observation generation, processed evidence, Sensors, and time-valid Calibrations agree; Analysis parameters and validation evidence are present in Activity provenance. Claim evidence is acyclic, and Reviews cannot predate a temporally identified target.
