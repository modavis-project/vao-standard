# Reference tools

All code in this directory is Apache-2.0 licensed reference software.

| Tool | Purpose |
| --- | --- |
| `vao.py` | version dispatch for retained contracts and 0.6 |
| `vao06.py` | core carrier validation, deterministic packing and MMIC integration |
| `mmic.py`, `mmic_worker.py` | MMIC semantics, native/MIDI checks and trusted isolated validation |
| `mmic_rdf.py` | ordered JSON/RDF/JSON-LD projection and SHACL validation |
| `mmic_consumer.mjs` | separate JavaScript native/MIDI/layout/comparison reference consumer |
| `migrate_vao05.py` | complete 0.5-to-0.6 migration with unchanged asset bytes and receipt |
| `build_mmic_schema.py`, `build_mmic_resources.py`, `build_mmic_fixtures.py` | deterministic MMIC normative resources and synthetic fixtures |
| `generate_schema_reference06.py`, `update_release_bundle06.py` | current 0.6 field reference and normative fixity |
| `vao05.py` | validate/pack 0.5 carriers, cross-validate publications, migrate 0.3 |
| `vao05_runtime.py` | 0.5 deterministic trace interpreter and random generators |
| `vao05_rdf.py` | 0.5 annotated JSON-LD semantic projection |
| `vao05_interop.py` | 0.5 RO-Crate/DataCite/IIIF/OCFL projections |
| `vao04.py` | validate manifest/workspace/carrier, deterministically pack, migrate 0.3 |
| `vao04_runtime.py` | 0.4 deterministic trace interpreter and random generators |
| `vao04_rdf.py` | annotated JSON-LD semantic projection |
| `vao04_interop.py` | reference RO-Crate/DataCite/IIIF/OCFL projections |
| `generate_schema_reference.py` | derive Markdown field reference from JSON Schema |
| `update_release_bundle.py` | derive/check normative artifact checksums |
| `check_release.py` | run all release gates |
| `vao03.py`, `vaom.py` | private-draft migration/regression compatibility |

Reference tools do not redefine the standard. Production deployments should add process isolation, use-case-specific resource limits, structured logging, and independent security review.
