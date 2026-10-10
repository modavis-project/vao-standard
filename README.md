# Virtual Acoustic Object (VAO) Standard

**Version 0.6.0 · final specification · 10 October 2026**

The Virtual Acoustic Object (VAO) Standard is an open exchange and preservation
standard for digital representations of musical instruments, mechanical music
information carriers and other acoustic objects. A release connects descriptions,
observations, recordings, images, geometry, interpretations, provenance, rights
and exact file identities while retaining the established formats of those resources.

VAO 0.6.0 integrates the independently versioned **MMIC 1.0.0** application profile
and its VAO-owned mechanical-music vocabulary. It covers rolls, perforated and
projection disks, pinned barrels, carrier collections and digital designs, with
separate documentation, decoding, comparison and generation conformance. Native
mechanical signals remain primary; MIDI is an optional, explicit interpretation.

Read the [0.5.0-to-0.6.0 changelog](Docs/VAO_0.6.0_CHANGELOG.md) and
[migration contract](Docs/MIGRATION_0.5_TO_0.6.0.md).
The [GitHub release](https://github.com/modavis-project/vao-standard/releases/tag/v0.6.0)
contains the immutable release files. The
[Zenodo version DOI](https://doi.org/10.5281/zenodo.23287792) identifies this edition; the
[concept DOI](https://doi.org/10.5281/zenodo.22122773) identifies the release series.
Version 0.6.0 W3ID routing is pending; the release includes all normative resources
and an offline dependency catalog.

## Start here

| Purpose | Document |
| --- | --- |
| Understand the format | [VAO Standard 0.6.0](Docs/VAO_STANDARD_0.6.0.md) |
| Implement mechanical music carriers | [MMIC 1.0.0](Docs/VAO_MMIC_PROFILE_1.0.0.md) |
| Review supported capabilities | [MMIC conformance map](Docs/MMIC_CONFORMANCE_1.0.0.md) |
| Implement selective delivery | [Dynamic Delivery profile](Docs/VAO_DYNAMIC_DELIVERY_PROFILE_0.6.0.md) |
| Prepare repository deposits | [Zenodo profile](Docs/VAO_ZENODO_PROFILE_0.6.0.md) |
| Migrate a 0.5 release | [0.5-to-0.6 migration](Docs/MIGRATION_0.5_TO_0.6.0.md) |
| Assess core conformance | [Conformance specification](Docs/VAO_CONFORMANCE_0.6.0.md) |
| Process untrusted carriers | [Security and privacy requirements](Docs/SECURITY_CONSIDERATIONS.md) |

The [schema reference](Docs/VAO_SCHEMA_REFERENCE_0.6.0.md) describes manifest fields.
The [profile index](Docs/VAO_PROFILE_INDEX_0.6.0.md) lists optional domain contracts.
The [release record](RELEASE_STATUS.md) documents identity and integrity.

## Release and carrier model

A semantic release is one immutable manifest and its identified exact realizations.
Several carriers can transport that release:

- `bootstrap` embeds a small discovery/evidence entry point;
- `preservation-closure` embeds every realization and completes every group;
- `custom` materializes a selected closure for a use case or byte budget.

Identified cross-carrier delivery from 0.5 remains available. A `carrier-member`
distribution pins the enclosing carrier, manifest, descriptor and exact member
identity. Selective materialization verifies byte size and SHA-256 before use.

```text
mimetype                         first entry; stored; exact media-type bytes
vao-manifest.json                canonical semantic manifest
META-INF/vao-carrier.json        carrier ID, manifest pin, payload mapping
payload/...                      exact embedded realization bytes
```

The provisional media type is `application/vnd.modavis.vao+zip`; the extension is `.vao`.

## Validation and migration

Use Python 3.11 or newer and Node.js 18 or newer for the complete source gate.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python Tools/vao.py validate Fixtures/MMIC/1.0.0/roll/preservation-closure.vao
python Tools/vao05.py validate Fixtures/VAO05/workspaces/minimal
python Tools/check_release.py
```

The installed package provides `vao` for version dispatch and `vao06`, `vao05`
and `vao04` for their respective contracts. MMIC reports preserve separate core
and domain results, claimed conformance levels and explicit unsupported,
unmaterialized or access-unavailable states.

An explicit migration accepts a valid complete 0.5 workspace, preserves asset
bytes and realization identities, and records a new manifest/release/carrier:

```sh
python Tools/migrate_vao05.py path/to/complete-0.5-workspace path/to/new-0.6-workspace \
  --receipt path/to/migration-receipt.json
```

Migration does not automatically promote provisional mechanical-music annotations
into a validated MMIC claim. New claims must meet MMIC 1.0.0 independently.

## Compatibility and scientific scope

The [0.5.0 release](https://doi.org/10.5281/zenodo.22214248), its versioned schemas,
specification, readers and fixtures remain unchanged. The
[0.4.0 release](https://doi.org/10.5281/zenodo.22122774) remains available under its
versioned paths. Private-draft 0.3 artifacts remain compatibility dependencies.

Conformance verifies the declared structure, semantics, provenance and exact bytes.
It does not certify historical accuracy, physical playability or empirical performance.
Reference execution supports declared forward/reverse linear clocks, cyclic and
multi-turn helical traversal, selected fixed-tempo PPQN SMF 0/1 bindings, qualified
alignment and linear-layout note generation. Segmented/repeated transport execution,
uncalibrated clocks and bindings beyond that subset report unsupported.

The bundled MMIC vocabulary is VAO-owned. It is not an accepted MODAVIS Ontology
Network module. The existing MODAVIS 0.1.0 binding is retained; conservative
CIDOC-CRM 7.1.3 and EDM 5.2.8 mappings are informative.

## Repository layout

```text
Docs/          specifications, profiles and implementation guides
Schemas/       versioned core schemas and linked-data artifacts
Profiles/      MMIC schema, vocabulary, context, shapes and local catalog
Tools/         validators, writers, migration and projections
Fixtures/      conformance records and synthetic sample carriers
tests/         release, security, semantic and reproducibility tests
knowledge/     informative Open Knowledge Format companion
```

## Governance, citation and licensing

The responsible editor and main developer is **Dominik Ukolov**
([ORCID](https://orcid.org/0000-0002-7904-3892)). VAO was developed in the MODAVIS
doctoral research project (2022–2026), supported by the German Academic Scholarship
Foundation (*Studienstiftung des deutschen Volkes*).

See [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md),
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md) and
[SUPPORT.md](SUPPORT.md). Normative resources use CC BY 4.0; software, tests and
automation use Apache-2.0; new MMIC synthetic fixture data uses CC0-1.0 with explicit
reference-code and dependency-lock exceptions. [LICENSE](LICENSE) and
[REUSE.toml](REUSE.toml) define the authoritative per-file mapping.
