# Registry and persistent-identifier status

VAO uses immutable versions for the standard, application profiles and machine-readable
artifacts. Registry assignments are not implied by specification publication.

| System | Current edition | Status |
| --- | --- | --- |
| GitHub | signed `v0.6.0` tag and release artifacts | immutable release source |
| Zenodo | VAO 0.6.0, version `10.5281/zenodo.23287792`; concept `10.5281/zenodo.22122773` | versioned release series |
| W3ID 0.6.0/MMIC 1.0.0 | canonical identifiers in the released files | routing pending |
| W3ID 0.4.0/0.5.0 | existing immutable version routes | preserved |
| IANA | `application/vnd.modavis.vao+zip` | provisional; not assigned |
| PRONOM | VAO format/container signature | not assigned |
| Shared MIME-info | `.vao` and internal `mimetype` recognition | not assigned |

The `w3id.org/modavis/vao/` namespace is maintained through `perma-id/w3id.org`.
No W3ID request or resolver deployment is part of this release. Use the immutable
GitHub tag and Zenodo version for direct access, and the released local dependency
catalog for offline validation. Future routing must preserve older targets and
verify exact version, source tag/path, representation and byte identity. See
[the routing status](../w3id/README.md).

The provisional media type and extension do not establish a registry assignment.
Identify a carrier through its ZIP structure and exact first `mimetype` member,
then validate the manifest, carrier descriptor and payload fixity.

The Zenodo release version distributes the reviewed release artifacts without
replacing older published records. CC BY 4.0, Apache-2.0 and CC0-1.0 apply to their
respective files, with reference-code and dependency-lock exceptions in synthetic
examples. `REUSE.toml` is authoritative.
