---
type: "VAO Reference Concept"
title: "Spatial and acoustic validity boundaries"
description: "What VAO spatial/acoustic conformance establishes and what remains empirical."
status: "stable"
sources:
  - id: "vao-spatial-profile"
    resource: "../../Docs/VAO_SPATIAL_PROFILE_0.4.0.md"
    title: "VAO Spatial profile 0.4.0"
  - id: "vao-acoustics-profile"
    resource: "../../Docs/VAO_ACOUSTICS_PROFILE_0.4.0.md"
    title: "VAO Acoustics profile 0.4.0"
---

# Spatial and acoustic validity

Coordinate Frames, Poses, transforms, material bands, measurements, response mappings, interpolation evidence, scenes, and render policies are explicit and cross-checked. Singular/ill-conditioned transforms, dimensional contradictions, registration RMS without a metric/residual method, ambiguous material uncertainty, untyped or unit-inconsistent metric uncertainty, channel selection across variants with inconsistent channel counts, duplicate response addresses, and cyclic fallbacks are invalid.

This establishes an internally consistent exchange contract. It does not establish survey accuracy, physical scale, calibration quality, compliance with a cited standard, simulation validity, perceptual equivalence, or truth of an acoustic result.
