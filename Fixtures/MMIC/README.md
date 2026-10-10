# MMIC 1.0.0 conformance fixtures

Sixteen original synthetic examples cover rolls, perforated and projection disks,
multi-turn helical barrels, reverse traversal, controls, native-only signals,
reader-offset and reverse envelopes, multipart collections, selected hypotheses,
retained corrections, designs and fabrication inspection lineage.

Each example under `1.0.0` contains a complete workspace and `.vao` carrier,
a partial bootstrap with identical manifest bytes, and lossless RDF/JSON-LD
projections. Complete carriers claim only their stated reference capabilities.
The bootstrap reports unmaterialized execution capabilities while checking the
available documentary projection. No fixture certifies a historical object or
physical performance.

```sh
python Tools/vao.py validate Fixtures/MMIC/1.0.0/roll/preservation-closure.vao --json
python Tools/build_mmic_fixtures.py --check
```

Rebuild with `Tools/build_mmic_fixtures.py` only in an unsealed development copy;
the builder replaces its versioned synthetic output directory. Deterministic
archive bytes are compared with the reference packer during the release gate.
[Conformance coverage](../../Docs/MMIC_CONFORMANCE_1.0.0.md) records scope.

Fixture metadata, SVG sources, audio and numeric data are CC0-1.0. Embedded
`reference.py` and `requirements-lock.txt` retain Apache-2.0; each realization
records its own rights. No third-party images or publications are redistributed.
