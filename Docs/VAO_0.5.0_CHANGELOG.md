# VAO 0.5.0 changelog

VAO 0.5.0 is a compatible semantic extension of 0.4.0 with new carrier and publication-descriptor fields. Existing 0.4.0 documents remain governed by their immutable 0.4.0 schemas and tools.

- Added the `carrier-member` distribution for exact realizations embedded in another carrier of the same immutable repository release.
- Added a stable `id` to every carrier descriptor.
- Added carrier identity, mode, manifest fixity, descriptor fixity, and complete-group declarations to carrier entries in the release descriptor.
- Added release/manifest cross-validation so every `carrier-member` distribution resolves to the exact carrier file declared by the publication descriptor.
- Defined a two-carrier Zenodo profile: one bootstrap carrier and one preservation closure in a single record, with a small, fixed companion-file set.
- Defined custom carriers as local materializations of an immutable semantic release, not additional deposited editions.
- Replaced the release recommendation for a legacy Zenodo metadata projection with live-service validation and a repository-neutral release descriptor.
