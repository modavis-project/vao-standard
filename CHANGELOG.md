# Changelog

- Final 0.4.0 co-release hardening binds examples to MODAVIS Ontology Network
  0.1.0, corrects obsolete pipe-organ class IRIs, and adds a conservative
  VAO-owned mapping graph to the immutable specification bundle.

All notable public changes will be recorded here. The project follows semantic versioning for the specification bundle as described in [VERSIONING.md](Docs/VERSIONING.md).

## [0.4.0] - 2026-08-27

First public release of the VAO standard.

- Promoted the reviewed `0.4.0-rc.2` content without changing the serialized `formatVersion` or immutable 0.4.0 identifiers.
- Recorded the public release date, final citation metadata, prospective `v0.4.0` GitHub release identity, and reserved Zenodo DOI `10.5281/zenodo.22122774`.
- Required the reserved DOI to be completed through a manual Zenodo deposit of the exact GitHub release artifact; automatic GitHub ingestion would mint a different DOI.
- Marked the optional OKF 0.2 knowledge documents stable and retained rc.1/rc.2 history as pre-publication provenance.

## [0.4.0-rc.2] - 2026-08-27

Prepared for editorial review; not published.

- Closed cross-module identifier collisions and unresolved local references, including typed scientific, spatial/acoustic, physical, runtime, review, and provenance links.
- Made quantity/uncertainty values numeric and dimension-aware; added non-negative magnitude, coverage/confidence, covariance symmetry/PSD, and heterogeneous-axis unit rules.
- Corrected RFC 3339 chronological comparison across offsets and rejected unknown `-00:00` offsets.
- Defined invertible row-major affine transforms, 2D embedding, geodetic-frame boundaries, unit quaternions, pose dimensions, acoustic band dimensions, material/metric/scene/render references, and topology acyclicity/inverse ports.
- Corrected PCG/xoshiro contracts and replaced floating-point stochastic selection with exact raw-integer interval selection; completed conflict, state/event/action, and trace rules.
- Controlled DataCite 4.7 fields and added ORCID/ROR check-digit validation without overstating registry identity verification.
- Bound release, pack, and receipt assertions to exact manifest/carrier bytes; corrected receipt Distribution linkage, failure evidence, chronology, and implementation/source-carrier provenance.
- Required registration-RMS methods, unambiguous logical-asset channel layouts, bounded structural archive reads, hard-link rejection, control-character exclusion, and NFC/case-fold-distinct portable paths.
- Completed JSON-LD IRI mappings, RDF type projection, vocabulary term coverage, and spatial/acoustic/runtime SHACL shapes with positive and negative tests.
- Added standalone normative Spatial and Acoustics profiles, a positive spatial/acoustic fixture, adversarial regression tests, and OKF 0.2-conformant knowledge documentation.
- Made Timebase rates dimensioned and exactly rational where needed; enforced track/realization modality, clock, coordinate-frame, annotation, and synchronization provenance consistency.
- Added reciprocal Activity/output and Claim/Review evidence chains, status-to-Activity compatibility, property-specific material uncertainty, learned-response evidence, acyclic response fallback, and exact measurement/channel coverage.
- Closed technical metadata contradictions (typed clock/frame/trajectory references, geometry-frame agreement, channel/Ambisonics cardinality, and media-rate agreement) and made annotation provenance mandatory.
- Scoped `maximumMicrosteps` per input-event run-to-completion cycle, counted stochastic redraws/process expansion, and explicitly bounded what offline traces do and do not demonstrate.
- Required explicit continuous clock boundaries, preserved Process-request lineage and operands in traces, and rejected unsupported scheduling/delay semantics in the offline interpreter.
- Replaced bare acoustic metric uncertainty vectors with the structured, unit-aware uncertainty contract and pinned all CI actions to immutable release commits.
- Made timestamp ordering exact through 18 decimal places, excluded ambiguous leap-second lexical normalization, and required explicit time-scale identity for absolute clocks/timecode.
- Eliminated cross-language numeric ambiguity with finite-binary64/safe-integer rules, underflow rejection, and a fixed-width hexadecimal PCG stream selector.
- Required exact equality between technical media rates and their Timebases instead of accepting near-but-different clocks.
- Made software digest scope explicit, replaced opaque dependency strings with typed independently hashed dependencies, separated software `runtimeDescription` from the root Runtime object, and barred declaration-only environments from deterministic Analysis/Renderer claims.
- Closed scientific provenance loopholes for in-place identities, Observation generation/processing, Sensor/Calibration agreement and validity, Analysis parameters/validation, circular Claim evidence, and temporally impossible Reviews.
- Removed the migration API's normalized-reserialization digest fallback; `migratedFromManifestSHA256` now always comes from explicitly supplied original bytes.
- Hardened the source-archive builder to require a clean repository and regular tracked files and to refuse overwriting either archive or checksum.
- Required the protected VAO JSON-LD context first and made the reference RDF projection embed its pinned local context instead of permitting network-dependent expansion.
- Rejected escaped unpaired Unicode surrogates so every accepted manifest remains valid Unicode for UTF-8, RFC 8785 canonicalization, and RDF projection.
- Replaced dimensionally invalid synchronization-boundary tolerance with exact rational comparison of the declared binary64/integer operands.
- Made covariance validation unit-coherent through pairwise symmetry and correlation normalization, rejected negative/invalid zero variances, and bounded inline cubic work.
- Aligned trace JSON Schema with the normative SHA-256-only digest rule and added algorithm-correct general digest/dependency SHACL shapes.
- Tightened reproducibility eligibility so source-only identities require an independently hashed environment lock, and stopped describing a dependency lock as a fully resolved OS/interpreter environment.
- Required separate code and environment evidence for environment-lock reproducibility claims; an environment lock alone no longer qualifies.
- Defined stochastic Process candidates and selection-before-expansion ordering, removed recursive/exponential candidate counting, bounded expansion by microsteps, and made all runtime string tie-breaks locale-independent.
- Replaced overflow/underflow-prone affine determinant arithmetic with a scale-invariant reciprocal-condition test and corrected impossible temporal provenance in the acoustic fixture.
- Applied structural size/depth budgets to standalone manifests and workspaces, made graph/process expansion iterative, and hardened malformed ZIP size handling.
- Made source-review archives cross-zlib byte-stable by using stored entries with fixed ZIP metadata.
- Required JSON Schema formats to be asserted, pinned the normative security requirements in the specification bundle, and rejected evidence or reviews that predate the declared availability of their targets.
- Removed orientation-basis ambiguity by requiring explicit compatible local/target frames for every Pose orientation and defining affine coefficient units and Hamilton quaternion direction.
- Prevented overclaiming of external unit/quantity-kind validation by separating IRI syntax from pinned-vocabulary dimensional verification.
- Replaced ambiguous logical-asset trajectory references with exact trajectory-realization references for Pose interpolation and tracked listeners.
- Defined position/orientation interpolation combinations and forbade unused trajectory references, eliminating implementation-dependent quaternion and listener behavior.
- Corrected an enriched fixture that attributed one immutable release identity to both migration and later integration; only the final integration now generates that release.
- Made the declared Python wheel operational outside a source checkout by bundling every required schema, adding a `vao04` entry point, distinguishing installed from source-locked software evidence, and adding an offline wheel smoke test to both release-gate environments.
- Corrected repository-deposit licensing metadata so a single CC BY assertion no longer mischaracterizes the Apache-2.0 tools; the integration fallback is explicitly mixed/open and the publication checklist requires both file-specific rights entries.
- Upgraded the informative RO-Crate projection to the current 1.3 Recommendation and supplied its mandatory root description/date/license metadata, typed profile entities, file-level rights, software/provenance links, and descriptions for otherwise dangling Activity references.
- Made RO-Crate publication dates explicit rather than deriving them from modification time, fixed geodetic scalar registration RMS validation, and made spatial tolerances and acoustic band-axis authority normative.
- Closed the companion-contract validation gap with safe-integer schema bounds, semantic/chronological/topology checks, complete CLI/release-gate coverage, and an explicit legacy Zenodo API target.

## [0.4.0-rc.1] - 2026-08-26

Prepared for editorial review; not published.

- Consolidated the latest 0.4.0 development into a standalone standards repository.
- Made the specification self-contained instead of normatively relying on unpublished 0.3 drafts.
- Hardened archive/workspace validation and deterministic carrier production.
- Corrected JSON-LD registry predicates and bounded the RDF round-trip claim.
- Added real RDF parsing and SHACL conformance checks.
- Added complete project governance, licensing, security, citation, release, and registry preparation.
- Added an optional OKF 0.2 documentation bundle.

The detailed format-level changes from the unpublished 0.3.3 editor snapshot are in [VAO_0.4.0_CHANGELOG.md](Docs/VAO_0.4.0_CHANGELOG.md).
