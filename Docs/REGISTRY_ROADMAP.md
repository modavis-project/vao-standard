# Registry and persistent-identifier status

VAO uses immutable version identifiers for the standard and its machine-readable artifacts. Registry assignments that have not been completed are not implied by the release.

## Release identifiers

| System | VAO 0.5.0 record | Status |
| --- | --- | --- |
| GitHub | signed tag, release archive, and publication site | released |
| Zenodo | `10.5281/zenodo.22214248` | released under concept DOI `10.5281/zenodo.22122773` |
| W3ID | `https://w3id.org/modavis/vao/0.5.0/` | active, version-pinned redirects |
| IANA | `application/vnd.modavis.vao+zip` | not assigned; identifier remains provisional |
| PRONOM | VAO format and container signature | not assigned |
| Shared MIME-info | `.vao` and internal `mimetype` recognition | not assigned |

## W3ID

The `w3id.org/modavis/vao/` namespace is maintained in the public `perma-id/w3id.org` repository. Versioned routes derive their targets from the requested semantic version and resolve to the matching immutable Git tag. The namespace covers schemas, JSON-LD context, RDF vocabulary, SHACL shapes, profiles, the MODAVIS mapping, the specification bundle, security guidance, and the specification.

The unversioned namespace root is a project discovery link. No moving `latest` identifier is defined for normative use.

## Media type and file identification

VAO 0.5.0 uses the provisional media type `application/vnd.modavis.vao+zip` and the recommended extension `.vao`. Neither string constitutes an IANA, PRONOM, or Shared MIME-info assignment. The container is identified more reliably by its ZIP structure and the required first `mimetype` member than by its extension alone.

## Zenodo record

The 0.5.0 version record contains the same deterministic source archive as the GitHub `v0.5.0` release. The repository contains CC BY 4.0 and Apache-2.0 material; `REUSE.toml` is the authoritative per-file rights mapping.
