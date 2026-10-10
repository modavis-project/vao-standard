# VAO 0.6.0 publication controls

## Local gates

Prepare the exact release tree using the hash-locked dependencies and Node.js 18
or newer. Run `python Tools/check_release.py`, `git diff --check` and verify a clean
source after the signed commit. The full gate covers retained 0.4/0.5 contracts,
MMIC levels and operational checks, projection parity, resource/access boundaries,
migration, metadata/licensing and deterministic fixture/site/wheel behavior.

Source exports must include only reviewed public files. Check nested carrier and
wheel contents, rights and archive metadata. Release artifacts must reproduce from
the clean source, with matching SHA-256 after distribution readback.

## GitHub

The publication workflow accepts only the signed annotated tag `v0.6.0` and verifies
the release commit against the responsible editor's authorized SSH key. It repeats
the complete gate on the source, builds deterministic assets and the current site,
checks repository visibility and publishes the GitHub release after successful site
publication. The 0.4/0.5 raw artifact paths remain present and unchanged.

## Zenodo

Create a new version of the existing VAO concept `10.5281/zenodo.22122773`, whose
0.5.0 record is `22214248`. Set version 0.6.0 and date 2026-10-10, preserve the
responsible editor and release-series identity, and record the version-specific DOI
in citation and repository metadata. Upload the exact reviewed release artifacts,
verify each remote checksum and full readback, and publish the verified version.
Do not replace or modify older published version files.

## Resolver routing

Version 0.6.0 routing remains pending. No W3ID request or resolver deployment is part
of this release. Canonical identifiers are stable, and the released local catalog
supplies normative dependencies for offline validation. Preserve older routes and
use the immutable GitHub tag and Zenodo version as direct access points.

## Scientific scope

Profile conformance does not certify historical accuracy, physical playability or
empirical performance. Advertised execution must remain within the implemented
reference capabilities. Unsupported capabilities, unknown evidence and unavailable
assets must retain their qualified report status.
