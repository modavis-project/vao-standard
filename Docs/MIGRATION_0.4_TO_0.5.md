# Migrating VAO 0.4.0 releases to 0.5.0

VAO 0.5.0 changes transport and publication identity without changing the meaning of existing scientific, physical-system, playable, or provenance records.

1. Change the immutable manifest schema, context, format version, profile IRIs, and embedded profile versions to 0.5.0.
2. Give every generated carrier descriptor a stable absolute `id`.
3. For realizations supplied by another deposited carrier, add a `carrier-member` Distribution and list its ID on those Realizations.
4. Describe each deposited carrier in `vao-release.json`, including its carrier ID/mode, outer-file fixity, embedded manifest fixity, descriptor fixity, and complete groups.
5. Cross-validate the release descriptor and manifest, then validate each carrier and its exact payload bytes.

The source 0.4.0 release remains immutable. Migration creates a new semantic release ID/content version and records provenance from the earlier release when applicable.
