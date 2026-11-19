# VAO 0.6.0 release record

- Repository and format version: **0.6.0**
- MMIC profile specification version: **1.0.0**
- Specification status: **final**
- Publication date: **2026-10-10**
- Version DOI: **[10.5281/zenodo.23287792](https://doi.org/10.5281/zenodo.23287792)**
- Concept DOI: **[10.5281/zenodo.22122773](https://doi.org/10.5281/zenodo.22122773)**
- Release tag: **[`v0.6.0`](https://github.com/modavis-project/vao-standard/releases/tag/v0.6.0)**
- W3ID routing for 0.6.0 and MMIC 1.0.0: **live since 2026-11-19**

VAO 0.6.0 integrates Mechanical Music Information Carriers through MMIC 1.0.0,
with documentation, decoding, comparison and generation contracts. Read the
[detailed 0.5.0-to-0.6.0 changes](Docs/VAO_0.6.0_CHANGELOG.md).

## Contents and integrity

The release contains versioned core and MMIC specifications, schemas, contexts,
vocabularies, SHACL shapes and local catalogs; exact-byte validators, migration and
projections; 16 original synthetic MMIC examples and 32 complete/bootstrap carriers;
and conformance, security, metadata, licensing, wheel/site and reproducibility gates.

The signed release commit and annotated `v0.6.0` tag identify the release tree.
The deterministic source ZIP is `vao-standard-0.6.0.zip`; its SHA-256 companion
provides the exact digest. GitHub and the Zenodo version distribute matching files.

## Compatibility and scope

The versioned [0.5.0](https://doi.org/10.5281/zenodo.22214248) and
[0.4.0](https://doi.org/10.5281/zenodo.22122774) releases remain unchanged.
Migration is explicit and preserves asset bytes and realization identities.
MMIC native semantics are primary; MIDI export is optional and model-bound.
Historical accuracy and physical playability are not certified. Unsupported
execution and unavailable materializations remain explicit report states.

## Identifiers

The [VAO 0.6.0](https://w3id.org/modavis/vao/0.6.0/) and
[MMIC 1.0.0](https://w3id.org/modavis/vao/profile/mmic/1.0.0) identifiers resolve
following [W3ID pull request 7235](https://github.com/perma-id/w3id.org/pull/7235).
The [routing record](w3id/README.md) lists the endpoints. The immutable GitHub
release and versioned Zenodo record retain the resources used by the offline
catalog. Existing published 0.4/0.5 routes are preserved.
