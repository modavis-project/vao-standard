# Tests

Run with:

```sh
python -m unittest discover -s tests -v
```

The suite covers retained 0.4/0.5 behavior, schema meta-validation, descriptors/workspaces/archives, archive attacks, deterministic packing, migration provenance, RFC 8785/runtime generators, JSON-LD parsing, SHACL, OKF structure, generated files, metadata, and release-state invariants.

MMIC tests additionally check complete/partial materialization, native and actual MIDI bytes, operational model hashes, timing and geometry, subject scope and lifecycle identities, qualified alignment, corrections, design/fabrication lineage, ordered JSON/RDF/JSON-LD parity, worker resource/access limits and a separate JavaScript reference consumer. Synthetic conformance tests do not certify historical accuracy or physical playability.

Run `python Tools/check_release.py` for the complete release gate, including licensing, generated resources, deterministic fixtures, the normative bundle, publication site and installed-wheel resource/runtime checks.
