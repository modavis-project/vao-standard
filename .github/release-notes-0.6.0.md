VAO 0.6.0 adds the independently versioned MMIC 1.0.0 profile for Mechanical Music Information Carriers, with documentation, decoding, comparison and generation conformance.

The release adds native mechanical signals and explicit MIDI bindings; complete model identity and exact output-byte checks; geometry/timing and full helical traversal; qualified alignment and immutable corrections; separate design/fabrication lineage; lossless ordered JSON/RDF/JSON-LD projection, SHACL and local dependency catalogs; bounded offline validation; synthetic carriers, cross-language reference traces and explicit 0.5 migration.

The versioned 0.5.0 and 0.4.0 specifications, schemas, readers and fixtures remain unchanged. Entity `kind` remains open as in 0.5.0; exact independent profile `specificationVersion` is new. See [the complete changelog](https://github.com/modavis-project/vao-standard/blob/v0.6.0/Docs/VAO_0.6.0_CHANGELOG.md) and [migration contract](https://github.com/modavis-project/vao-standard/blob/v0.6.0/Docs/MIGRATION_0.5_TO_0.6.0.md).

Version 0.6.0 resolver routing is pending. The release includes all local normative resources. Historical accuracy and physical playability require separate certification; execution outside the declared reference subset reports unsupported.

Normative resources use CC BY 4.0; software uses Apache-2.0; original MMIC synthetic data uses CC0-1.0 with code/lock exceptions. `REUSE.toml` defines the per-file mapping.

Version DOI: [10.5281/zenodo.23287792](https://doi.org/10.5281/zenodo.23287792). The [concept DOI](https://doi.org/10.5281/zenodo.22122773) identifies the release series.

The locked build environment updates `urllib3` to 2.8.0 and `setuptools` to 83.0.0, addressing the upstream streaming and source-distribution advisories documented in the changelog. MMIC environment assets and hashes are regenerated; historical 0.4/0.5 fixture bytes remain unchanged.
