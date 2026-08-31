# Virtual Acoustic Object Standard 0.5.0

VAO 0.5.0 adds an exact cross-carrier delivery contract to the Virtual Acoustic Object Standard. A small bootstrap carrier can locate selected realizations inside a complete preservation carrier without changing the identity of the semantic release.

The release adds:

- stable carrier identifiers;
- `carrier-member` distributions;
- carrier mode, outer-file fixity, manifest fixity, descriptor fixity, and complete-group declarations in the release inventory;
- release, manifest, carrier-descriptor, and carrier-file cross-validation;
- a two-carrier Zenodo profile for bootstrap and preservation delivery;
- the `vao05` reference tools, schemas, profiles, fixtures, and migration guidance.

VAO 0.4.0 remains valid and immutable under its versioned schemas and tools.

Persistent identifiers:

- DOI: [10.5281/zenodo.22214248](https://doi.org/10.5281/zenodo.22214248)
- W3ID: [https://w3id.org/modavis/vao/0.5.0/](https://w3id.org/modavis/vao/0.5.0/)

The release ZIP is deterministic. Verify it with the attached `.sha256` file. Documentation, schemas, semantic artifacts, fixtures, and knowledge documents are CC BY 4.0; reference software, tests, and automation are Apache-2.0. `REUSE.toml` contains the authoritative per-file mapping.
