# VAO 0.5.0 publication record

This document records the controls applied to the VAO 0.5.0 release.

## Release controls

| Control | Result |
| --- | --- |
| Normative specification, schemas, profiles, and generated reference | verified |
| Conformance, security, fixture, RDF/SHACL, and reproducibility tests | passed |
| Deterministic source archive and publication site | verified |
| Citation, licensing, governance, and repository metadata | reviewed |
| Public-text and release-metadata scan | passed |
| Signed release commit and annotated `v0.5.0` tag | required by publication workflow |
| GitHub release assets and Pages deployment | built from the signed tag |
| Zenodo archive | byte-identical to the GitHub release archive |
| W3ID versioned routes | resolved against the immutable tag |

## Local release gate

The release is validated from a clean checkout with the hash-locked dependency set:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python Tools/check_release.py
git status --short
git diff --check
```

The gate covers schema validity, maintained fixtures, conformance and security rules, deterministic carriers, RDF/SHACL, metadata, licensing, the installed tools wheel, dependency locks, source-text hygiene, and the publication surface.

`Tools/build_release.py` accepts only a clean repository for release builds. It refuses existing output targets and non-regular tracked inputs, writes fixed stored ZIP entries, and produces a SHA-256 checksum. Identical tracked bytes therefore produce identical archives independently of ZIP compression libraries.

## GitHub publication

The publication workflow accepts only the signed annotated tag `v0.5.0`. It verifies the tag and release commit against the editor's allowed SSH signing key, repeats the release gate, builds the deterministic source archive and site, and confirms that the repository is public.

The workflow prepares the GitHub release, deploys the verified Pages artifact, and publishes the release only after deployment succeeds. The released archive and checksum are available from the `v0.5.0` release page.

## Zenodo publication

VAO 0.5.0 is the second version of Zenodo concept record `10.5281/zenodo.22122773`. Its version DOI is `10.5281/zenodo.22214248`.

The Zenodo record contains the exact archive downloaded from the GitHub release. Metadata identifies version 0.5.0, the release date, the responsible editor, the W3ID namespace, the GitHub release, the MODAVIS Ontology Network dependency, and the mixed CC BY 4.0 / Apache-2.0 rights statement defined by `REUSE.toml`.

## Persistent identifiers

Versioned W3ID routes resolve schemas, context, vocabulary, SHACL shapes, profiles, the MODAVIS mapping, and the specification to files from `v0.5.0`. VAO documents serialize versioned identifiers; the unversioned namespace remains a discovery route.
