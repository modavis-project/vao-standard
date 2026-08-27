# Virtual Acoustic Object (VAO) Standard

VAO is an open, preservation-oriented exchange standard for virtual representations of musical instruments and other acoustic objects. It binds semantic identity, scientific evidence, multimodal media, physical topology, interaction behaviour, rights, and exact file bytes in one verifiable release model.

**Version 0.4.0 · Final specification · 27 August 2026**

[Publication site](https://modavis-project.github.io/vao-standard/) · [DOI 10.5281/zenodo.22122774](https://doi.org/10.5281/zenodo.22122774) · [Release record](RELEASE_STATUS.md)

The [editorial provenance](Docs/EDITORIAL_PROVENANCE.md) records why 0.4.0 is the current development baseline and how unpublished 0.3 material is treated.

## What VAO provides

- immutable semantic releases separated from their transport carriers;
- exact SHA-256 identity for every realization and optional SHA-512/chunk/Merkle verification;
- typed provenance, protocols, observations, calibrations, analyses, claims, reviews, and consent;
- audio, video, geometry, depth, motion, sensor, event, score, annotation, and trajectory tracks with explicit clocks;
- physical components, ports, connections, sensors, actuators, and state bindings;
- declarative playable behaviour, deterministic scheduling, random-source declarations, and machine-checked conformance traces;
- spatial/acoustic scenes, measured responses, render configurations, and repository-neutral discovery metadata;
- safe ZIP-based `.vao` carriers, partial/bootstrap delivery, and preservation closures;
- JSON Schema as the authoritative machine-validation layer plus an RDF/JSON-LD semantic projection.

VAO composes with established formats—including AES69-SOFA, ADM, glTF, MEI, MIDI, IIIF, RO-Crate, BagIt, OCFL, PROV-O, SOSA/SSN, QUDT, DataCite, and Local Contexts—without replacing them.

## Authoritative 0.4.0 artifacts

| Artifact | Purpose |
| --- | --- |
| [VAO_STANDARD_0.4.0.md](Docs/VAO_STANDARD_0.4.0.md) | normative specification |
| [vao-manifest-0.4.0.schema.json](Schemas/vao-manifest-0.4.0.schema.json) | normative manifest syntax |
| [vao-carrier-0.4.0.schema.json](Schemas/vao-carrier-0.4.0.schema.json) | normative carrier descriptor |
| [VAO_CONFORMANCE_0.4.0.md](Docs/VAO_CONFORMANCE_0.4.0.md) | roles, validation order, and claims |
| [SECURITY_CONSIDERATIONS.md](Docs/SECURITY_CONSIDERATIONS.md) | normative processor safety and privacy requirements |
| [VAO_PROFILE_INDEX_0.4.0.md](Docs/VAO_PROFILE_INDEX_0.4.0.md) | versioned profile contracts, including Spatial and Acoustics |
| [vao-context-0.4.0.jsonld](Schemas/vao-context-0.4.0.jsonld) | normative JSON-LD term mapping |
| [vao-vocabulary-0.4.0.ttl](Schemas/vao-vocabulary-0.4.0.ttl) | semantic projection vocabulary |
| [vao-modavis-mapping-0.4.0.ttl](Schemas/vao-modavis-mapping-0.4.0.ttl) | exact downstream binding to MODAVIS Ontology Network 0.1.0 |
| [vao-shapes-0.4.0.ttl](Schemas/vao-shapes-0.4.0.ttl) | SHACL validation of the projection |
| [vao-release-bundle-0.4.0.json](Schemas/vao-release-bundle-0.4.0.json) | checksums for the specification bundle |

The human-readable [schema reference](Docs/VAO_SCHEMA_REFERENCE_0.4.0.md) is generated from the normative JSON Schema. The checked-in 0.3 schemas are non-normative compatibility dependencies used only by the migrator and mature retained-semantic checks; see [Schemas/README.md](Schemas/README.md).

## Quick start

Python 3.11 or newer is recommended.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt

python Tools/vao04.py validate Fixtures/VAO04/descriptors/kinoorgel-multimodal-scientific.example.json
python Tools/vao04.py validate Fixtures/VAO04/descriptors/cuntz-positiv-acoustic.example.json
python Tools/vao04.py validate Fixtures/VAO04/workspaces/minimal
python Tools/vao04.py validate Fixtures/VAO04/carriers/minimal.vao
python Tools/vao04.py validate-descriptor release Fixtures/VAO04/companions/release.example.json
python Tools/vao04.py validate-descriptor pack Fixtures/VAO04/companions/pack-manifest.example.json
python Tools/vao04.py validate-descriptor receipt Fixtures/VAO04/companions/materialization-receipt.example.json
python Tools/vao04.py validate-descriptor zenodo-metadata Fixtures/VAO04/companions/zenodo-metadata-legacy.example.json
python Tools/vao04.py validate-publication Fixtures/VAO04/companions/release.example.json Fixtures/VAO04/companions/zenodo-metadata-legacy.example.json
python Tools/vao04.py validate-release Fixtures/VAO04/companions/release.example.json Fixtures/VAO04/workspaces/minimal/vao-manifest.json
python Tools/vao04.py validate-pack Fixtures/VAO04/companions/pack-manifest.example.json Fixtures/VAO04/workspaces/minimal/vao-manifest.json
python Tools/vao04.py validate-receipt Fixtures/VAO04/companions/materialization-receipt-minimal.example.json Fixtures/VAO04/workspaces/minimal/vao-manifest.json Fixtures/VAO04/carriers/minimal.vao
python Tools/check_release.py
```

An installed tools wheel exposes the equivalent `vao04` command and bundles all schemas required for offline validation. The wheel deliberately does not claim the source checkout's exact dependency lock; deterministic scientific claims should cite a released source bundle and lock together.

To create a deterministic carrier from a valid workspace:

```sh
python Tools/vao04.py pack path/to/workspace path/to/output.vao
```

To migrate a VAO 0.3 workspace without overwriting the source:

```sh
python Tools/vao04.py migrate-0.3 path/to/vao03 path/to/new-vao04-workspace
```

The [implementer guide](Docs/IMPLEMENTER_GUIDE.md) covers construction, validation, safe extraction, materialization, and canonical bytes. The [security considerations](Docs/SECURITY_CONSIDERATIONS.md) are required reading for processors of untrusted carriers.

## Publication site

The academic publication surface is built deterministically from the reviewed repository content. It publishes the complete human-readable documentation and stable, versioned copies of the normative machine-readable artifacts.

To inspect it locally:

```sh
python Tools/build_site.py --output site/vao-standard
python Tools/check_site.py --site site/vao-standard --publication-state prepared
python -m http.server 8000 --directory site
```

Then open `http://127.0.0.1:8000/vao-standard/`. The release workflow produces the public form of the same site from the signed tag. It cannot deploy while the repository is private.

## Release and carrier model

A VAO semantic release is the manifest and its referenced exact realizations. A carrier is only one transport of that release:

- `bootstrap` embeds at least one realization and may enable later verified materialization;
- `custom` embeds an explicitly selected subset;
- `preservation-closure` embeds every realization and marks every asset group complete.

Every `.vao` is a ZIP container with this root layout:

```text
mimetype                         first entry; stored; exact media-type bytes
vao-manifest.json                canonical semantic manifest
META-INF/vao-carrier.json        manifest pin and payload mapping
payload/...                      exact embedded realization bytes
```

The provisional media type is `application/vnd.modavis.vao+zip`; the recommended extension is `.vao`. These identifiers remain provisional until the prepared registrations are reviewed and submitted.

Structural/semantic conformance is not a scientific-validity certificate. VAO can prove that evidence, units, uncertainty, provenance, frames, and declared standards are represented consistently; the truth and adequacy of a measurement, simulation, interpretation, or rights assertion still require qualified review and source evidence.

## Linked data

Canonical VAO JSON and its exact bytes are authoritative. The JSON-LD context maps VAO records to RDF nodes, and the projection helper adds types and source JSON pointers. Adding and removing those annotations is reversible as JSON. An RDF graph is a semantic projection and does not preserve JSON member order, array order, number lexical form, or the original manifest bytes; processors must never reconstruct fixity claims from RDF alone.

## Open Knowledge Format companion

The non-normative [knowledge bundle](knowledge/index.md) follows [Google Cloud's Open Knowledge Format (OKF) 0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). It provides short, machine-discoverable explanations of VAO concepts and points back to normative sources. OKF complements VAO documentation; it does not replace the schemas or conformance rules.

## Repository map

```text
Docs/          specification, profiles, guides, and policy
Schemas/       normative 0.4.0 schemas and linked-data artifacts
Tools/         reference validator, deterministic writer, migration, projections
Fixtures/      conformance manifests, companion descriptors, and a deterministic `.vao`
tests/         release, security, conformance, RDF, and reproducibility tests
knowledge/     optional OKF 0.2 knowledge bundle
.github/       CI, issue forms, and contribution templates
```

Registry submission working files are maintained separately from the versioned standard. The repository contains only the standard, implementation resources, public project policies, and reproducible release automation.

## Governance, contributing, and citation

The responsible editor and main developer is **Dominik Ukolov** ([ORCID](https://orcid.org/0000-0002-7904-3892)), Digital Humanities (Image/Object), Friedrich Schiller University Jena; also Research Group DIGITAL ORGANOLOGY, Leipzig University. Affiliations identify the editor and do not imply institutional endorsement.

Please read [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Citation metadata is available in [CITATION.cff](CITATION.cff) and [codemeta.json](codemeta.json).

## License

Documentation, schemas, semantic artifacts, fixtures, and the OKF bundle are licensed under [CC BY 4.0](LICENSES/CC-BY-4.0.txt). Reference software, tests, and automation are licensed under [Apache-2.0](LICENSES/Apache-2.0.txt). File-class details are in [LICENSE](LICENSE) and [REUSE.toml](REUSE.toml).
