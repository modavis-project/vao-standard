# VAO 0.6.0 release guide

VAO 0.6.0 bundles the independently versioned MMIC 1.0.0 profile. The signed
release commit and annotated `v0.6.0` tag identify exact source bytes. The normative
bundle inventories versioned schemas, semantic artifacts, profiles, the MMIC module,
local catalog and migration contract. The [coverage map](MMIC_CONFORMANCE_1.0.0.md)
links all 17 requirements and 36 competency questions to their supported scope.

## Reproduction

Use the hash-locked Python dependencies and Node.js 18 or newer:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python Tools/check_release.py
python Tools/build_release.py --output-directory path/to/unused-output
```

The gate covers retained 0.4/0.5 behavior, complete/partial MMIC carriers, semantic
negative cases, actual native and MIDI bytes, geometry/timing, JSON/RDF/JSON-LD
parity, migration, access/resource bounds and cross-language reference traces.
Generated resources, fixture carriers, the normative bundle, publication site and
wheel resource/runtime checks must reproduce from the exact source.

## Release identity and access

The [release record](../RELEASE_STATUS.md), [citation metadata](../CITATION.cff)
and [0.5.0-to-0.6.0 changelog](VAO_0.6.0_CHANGELOG.md) identify the edition.
GitHub and [Zenodo version `10.5281/zenodo.23287792`](https://doi.org/10.5281/zenodo.23287792) distribute
matching release artifacts. The concept DOI `10.5281/zenodo.22122773` identifies the release series. SHA-256 companions identify exact bytes.

Version 0.6.0 W3ID routing is pending. Use the immutable GitHub tag and Zenodo version
as access points. Older published routes and artifact bytes are preserved.

## Conformance boundary

Reference execution covers declared unsegmented linear forward/reverse and cyclic
or multi-turn helical clocks, supported fixed-tempo PPQN SMF 0/1 bindings, qualified
alignment and linear-layout note generation. Other clocks, segmented/repeated
transport execution and additional MIDI bindings report unsupported. Documentary
claims may record qualified unknowns. Historical accuracy, physical playability
and empirical performance require separate evidence and certification.

The separate JavaScript reference consumer demonstrates its declared trace subset;
it is not independent institutional approval. The MMIC module remains VAO-owned,
without claiming acceptance into the MODAVIS Ontology Network or compliance with
receiving CRM/EDM profiles. Code and normative resources retain their stated
licenses; original MMIC synthetic data is CC0-1.0 with code/lock exceptions.
