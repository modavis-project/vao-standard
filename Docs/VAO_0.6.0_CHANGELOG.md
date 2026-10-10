# VAO 0.6.0 changes from 0.5.0

Released 10 October 2026. Envelope: VAO 0.6.0. Application profile: MMIC 1.0.0.

## New mechanical-music contract

0.5.0 supplied a general preservation envelope and identified cross-carrier delivery.
It had no accepted MMIC application profile. 0.6.0 adds a separately versioned MMIC
profile and a self-contained VAO-owned vocabulary for physical information carriers,
their historical states, observations, programs, interpretations and digital designs.
Rolls, perforated disks, projection disks, pinned/helical barrels and multipart
collections can be represented without assigning them a fictitious instrument identity.

The profile defines four independent levels: documentation, decoding, comparison
and generation. Documentation permits explicitly qualified unknowns; decoding requires
an operational model and checked outputs; comparison requires qualified takes and
actual alignment evidence; generation requires reproducible source/model/layout/report
lineage, with separate evidence for any fabricated physical carrier.

## Core and profile versioning

Profile declarations may carry an exact `specificationVersion` independently of
the enclosing VAO format version. The profile registry, declaration, domain document
and local dependency catalog must agree. Capability groups cover transitive input
closures and support explicit partial materialization.

Entity `kind` remains an open string, as it already was in 0.5.0. The new contract
clarifies physical carriers, designs and collections, and verifies that selected
MMIC subjects actually belong to the claimed MMIC domain.

## Mechanical semantics and operational validation

- Physical/digital identities, registry identifiers and predecessor chains remain
  distinct; collisions and lifecycle cycles are rejected.
- Physical documentation requires a qualified state, geometry and coverage.
  Acquisition selectors, units, coordinate domains, seams, turns and the entire
  helical trajectory are checked against declared sources and models.
- Complete model identity includes operational reader geometry, role offsets and
  units, clock/timing functions, bindings, export policy and execution dependencies.
  Canonical JSON hashing prevents untracked operational changes.
- Native gate, impulse, latch and envelope signals preserve mechanical controls.
  MIDI requires explicit pitch/channel/controller bindings, initial/reset policy,
  rounding and disclosed loss. The actual SMF bytes must match the selected binding.
- Native event times are recomputed from geometry and timing. Forward/reverse
  envelopes retain the appropriate traversal and time order.
- Playback comparison distinguishes actual, simulated and unknown takes. Alignment
  bytes, anchors, pairs, gaps, coverage and residuals are checked; simulation cannot
  silently become physical ground truth.
- Corrections retain exact prior and replacement decisions with evidence and
  attributable immutable lineage.
- Generation recomputes reference layouts from fixed MIDI inputs and constraints.
  A digital design remains distinct from a fabricated carrier and its inspection.

## Linked data and processor behavior

The release adds a closed normalized JSON schema, protected JSON-LD context,
mechanical-music vocabulary, SHACL shapes and hash-pinned local dependency catalog.
Ordered JSON/RDF/JSON-LD projections retain the full native model and opaque extension
content. RDF point coincidence requires agreement on all coordinate axes.
CIDOC-CRM 7.1.3 and EDM 5.2.8 mappings are conservative and informative, without
receiving-profile, entailment or equivalence claims.

Reference reports distinguish core transport validity from MMIC domain validity.
Unsupported versions or operations, absent materializations and unavailable access
have explicit statuses. Incoming profile resources do not select executable code.
The trusted worker uses isolation, input/depth/graph budgets and a deadline; effective
platform limits are reported. Normative dependencies are resolved from pinned local
resources rather than fetched during validation.

## Tools, examples and migration

The release adds a 0.6 validator and version dispatcher while retaining the existing
0.4/0.5 readers. A separate JavaScript consumer checks native/MIDI/layout/comparison
reference traces. The fixture set contains 16 original synthetic examples and 32
complete/bootstrap carriers, with deterministic generation and packing. Negative
coverage exercises controller/timing/model/identity/geometry/fabrication mismatches,
subject scope, malformed data, resource limits, access and version disagreement.

Explicit complete-closure migration from 0.5 creates new manifest, release and carrier
identities while retaining original asset bytes, realization identities and unknown
extensions. It records fixity and provenance in a migration receipt. It does not
promote provisional MMIC annotations automatically.

## Preserved behavior and limits

The versioned 0.5.0 and 0.4.0 normative artifacts, schemas, readers and fixtures remain
unchanged. Existing cross-carrier delivery, exact-byte identity and the MODAVIS 0.1.0
binding are retained. Common release metadata, documentation indexes, site generation
and signed publication automation advance to 0.6.0.

Reference execution covers declared linear forward/reverse and cyclic/multi-turn
helical models, supported fixed-tempo PPQN SMF 0/1 bindings, qualified comparisons
and linear-layout note generation. Segmented/repeated transport execution,
uncalibrated clocks and other MIDI bindings report unsupported. Historical accuracy
and physical playability require separate empirical certification.

The MMIC module is governed by VAO and is not an accepted MODAVIS Ontology Network
module. Version 0.6.0 resolver routing is pending. The immutable GitHub release and
Zenodo version provide the release files; no change to W3ID routing is part of this
release. Documentation and normative resources are CC BY 4.0, software is Apache-2.0,
and original MMIC synthetic data is CC0-1.0 with explicit code/lock exceptions.
