# VAO persistent identifier routing

[W3ID pull request 7235](https://github.com/perma-id/w3id.org/pull/7235) went
live on 19 November 2026. The following routes were checked after the merge.

| Resource | Identifier |
| --- | --- |
| VAO 0.6.0 specification | [`/0.6.0/`](https://w3id.org/modavis/vao/0.6.0/) |
| VAO 0.6.0 manifest schema | [`/0.6.0/schema/manifest.json`](https://w3id.org/modavis/vao/0.6.0/schema/manifest.json) |
| VAO 0.6.0 vocabulary | [`/0.6.0/vocabulary`](https://w3id.org/modavis/vao/0.6.0/vocabulary) |
| VAO 0.6.0 MODAVIS mapping | [`/0.6.0/modavis-mapping`](https://w3id.org/modavis/vao/0.6.0/modavis-mapping) |
| MMIC 1.0.0 specification | [`/profile/mmic/1.0.0`](https://w3id.org/modavis/vao/profile/mmic/1.0.0) |
| MMIC 1.0.0 schema | [`/profile/mmic/1.0.0/schema.json`](https://w3id.org/modavis/vao/profile/mmic/1.0.0/schema.json) |
| MMIC 1.0.0 ontology | [`/profile/mmic/1.0.0/ontology`](https://w3id.org/modavis/vao/profile/mmic/1.0.0/ontology) |

The unversioned [`/ontology`](https://w3id.org/modavis/vao/ontology) and
`/vocab/…` routes now serve the 0.6.0 vocabulary. The unversioned
[`/mmic`](https://w3id.org/modavis/vao/mmic) route serves the MMIC 1.0.0
ontology. Use versioned identifiers when pinning a dependency. The 0.4.0 and
0.5.0 routes retain their release targets.

The schema and Turtle responses were compared with the release files
byte for byte. Offline validation uses the dependency catalog bundled with
the release. MMIC remains a VAO vocabulary.
