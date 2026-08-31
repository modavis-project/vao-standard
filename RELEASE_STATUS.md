# VAO 0.5.0 release record

- Repository version: **0.5.0**
- VAO format version: **0.5.0**
- Specification status: **final**
- Publication date: **2026-08-31**
- Version DOI: **[10.5281/zenodo.22214248](https://doi.org/10.5281/zenodo.22214248)**
- Concept DOI: **[10.5281/zenodo.22122773](https://doi.org/10.5281/zenodo.22122773)**
- Release tag: **[`v0.5.0`](https://github.com/modavis-project/vao-standard/releases/tag/v0.5.0)**

VAO 0.5.0 extends the immutable 0.4.0 contract with identified cross-carrier delivery. A bootstrap carrier can locate and verify exact members of a preservation carrier while the semantic release remains independent of either transport container.

## Release contents

- normative specification, conformance rules, security requirements, and profiles;
- Draft 2020-12 JSON Schemas and exact release/carrier validation;
- JSON-LD context, RDF vocabulary, SHACL shapes, and the MODAVIS mapping;
- deterministic carrier writers and reference validators for VAO 0.4 and 0.5;
- positive, negative, migration, security, linked-data, and reproducibility fixtures;
- deterministic source archive and publication-site builders;
- citation, licensing, governance, and release metadata.

## Release integrity

The signed annotated tag `v0.5.0` identifies the release commit. The GitHub release and Zenodo version contain the same deterministic archive, `vao-standard-0.5.0.zip`. Its companion checksum file on GitHub records the SHA-256 digest.

The publication site exposes immutable 0.5.0 artifacts below `/0.5.0/` and retains the 0.4.0 artifacts below `/0.4.0/`. The W3ID namespace resolves versioned identifiers to files from the matching signed release tag.

## Compatibility

VAO 0.4.0 remains valid under its versioned schemas and tools. Migration to 0.5.0 creates a new semantic release and adds carrier identity, cross-carrier distributions, and the corresponding release-inventory fixity. The scientific, physical, playable, and provenance meanings retained from 0.4.0 are unchanged.
