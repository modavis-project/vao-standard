# VAO release procedure

This procedure separates technical verification from the authority to publish. Passing the automated gate does not create a tag, release, deployment, DOI record, or registry submission.

## 1. Verify the reviewed source

From a clean clone of the candidate commit:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python Tools/check_release.py
git status --short
git diff --check
```

The gate covers schema validity, fixtures, conformance and security rules, deterministic carriers, RDF/SHACL, metadata, licensing, the installed tools wheel, dependency locks, and the deterministic publication surface.

The responsible editor should additionally confirm the normative prose, affiliations, licensing, media type, file extension, DOI, repository URL, W3ID target, MODAVIS binding, and release notes. Independent implementation and security review remain advisable for software that accepts untrusted carriers.

## 2. Record the candidate

Record:

- the reviewed commit identifier;
- the normative specification-bundle SHA-256 values;
- the deterministic source-archive SHA-256 value;
- the reviewer and review date;
- any explicitly accepted limitations.

`Tools/build_release.py` refuses a dirty repository, pre-existing output files, and tracked links or non-regular files. Archive entries use fixed metadata and stored compression so identical tracked bytes produce identical output independently of the host's zlib implementation.

## 3. Prepare GitHub without publishing

Before changing repository visibility:

1. push the reviewed commit to the private repository;
2. require the validation workflow on `main` and protect the branch as appropriate;
3. set the repository description and website URL;
4. confirm that no release tag, GitHub Release, Pages deployment, or public artifact exists;
5. inspect the locally generated site at desktop and narrow viewport widths.

The publication workflow accepts only the signed annotated tag `v0.4.0`. It verifies the tag and target commit against the editor's allowed SSH signing key and refuses to run while the repository is private.

## 4. Enact the GitHub release

After explicit publication approval:

1. make the repository public;
2. configure GitHub Pages to use **GitHub Actions** as its source;
3. create and push the signed annotated tag `v0.4.0` from the reviewed commit;
4. follow the fresh tag-triggered workflow run; do not rely on a job rerun after changing repository or Pages settings;
5. verify the deployed site, its versioned artifacts, and `release-site-manifest.json`;
6. verify the GitHub Release source archive against its attached checksum.

The workflow builds every artifact again from the signed tag, creates a draft GitHub Release, deploys the verified Pages artifact, and publishes the GitHub Release only after deployment succeeds. A failed deployment therefore leaves a draft release that can be inspected without presenting it as final.

## 5. Complete the archival record

Upload the exact GitHub Release ZIP to the prepared Zenodo record for DOI `10.5281/zenodo.22122774`. Verify SHA-256 equality before publishing the record. Do not enable automatic GitHub ingestion for this release because it cannot preserve a separately reserved DOI.

The Zenodo metadata should identify the GitHub release as an identical version only after byte equality is established. It should represent the per-file CC BY 4.0 and Apache-2.0 licensing accurately; a repository-wide fallback license must not obscure the file-class mapping.

## 6. Establish persistent identifiers and registrations

After the GitHub and Zenodo records resolve:

1. deploy and test the W3ID redirects;
2. submit the media type to IANA;
3. submit the format and signature evidence to PRONOM and other appropriate registries;
4. archive submitted forms, correspondence, and assigned identifiers;
5. announce the release only after links, downloads, checksums, and citations have been verified from an unauthenticated browser session.

Registry review can change the provisional media type or extension. Such an external assignment should be documented through the versioning and change-control policy rather than silently altering the released 0.4.0 record.
