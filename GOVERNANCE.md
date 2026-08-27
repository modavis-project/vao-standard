# Governance

## Scope

This document governs the VAO specification, normative schemas, vocabularies, conformance suite, reference tools, and official profiles in this repository.

## Roles

- **Responsible editor:** owns release integrity, chairs technical decisions, and is the final change controller while VAO is in its initial public-review phase.
- **Maintainers:** contributors granted merge and release-review authority by the responsible editor.
- **Contributors and reviewers:** anyone submitting issues, proposals, tests, implementation reports, or pull requests.

Dominik Ukolov is the initial responsible editor. The named academic affiliations identify the editor; neither institution is represented as a standards body or change controller.

## Decision process

Routine corrections may be accepted through normal review. A change that affects serialized data, conformance, security, identifiers, licensing, governance, or compatibility requires:

1. a public issue describing the problem, alternatives, and compatibility impact;
2. a pull request containing specification, schema, tests, examples, migration guidance, and changelog updates together;
3. at least one maintainer review and all automated checks passing;
4. explicit approval by the responsible editor for a release candidate.

Consensus is preferred and objections must be answered on their technical merits. When consensus cannot be reached, the responsible editor records the decision and rationale. Decisions may be revisited when new implementation evidence appears.

## Compatibility and releases

- Patch releases clarify or correct without intentionally invalidating conforming documents.
- Minor releases may add backward-compatible vocabulary or optional capabilities.
- Major releases may change required structure or semantics and require migration guidance.
- An unpublished editor draft creates no public compatibility promise, but its changes must still be documented.

Normative versioned URLs are immutable after publication. Errata that cannot be resolved without changing conformance produce a new version. Moving aliases such as `latest` are discovery conveniences and must not occur in preserved manifests.

## Appeals and conflicts of interest

A contributor may request reconsideration in the relevant issue, citing specification text or implementation evidence. Reviewers disclose material conflicts. Conduct complaints are handled separately under [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and are not decided in technical threads.

## Succession

The responsible editor may appoint additional maintainers or a successor in a recorded repository decision. A future community governance revision should establish multiple release approvers and a transparent voting/appeal mechanism before VAO claims standards-organization status.
