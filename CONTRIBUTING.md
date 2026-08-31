# Contributing to VAO

Contributions to specification text, schemas, fixtures, tools, and implementation evidence are welcome after the repository becomes public.

## Before proposing a change

Search existing issues and read the [standard](Docs/VAO_STANDARD_0.5.0.md), [conformance rules](Docs/VAO_CONFORMANCE_0.5.0.md), and [governance](GOVERNANCE.md). Security vulnerabilities must follow [SECURITY.md](SECURITY.md), not a public issue.

Substantive format proposals should explain:

- the user or preservation problem;
- why existing fields, profiles, or extensions are insufficient;
- syntax and semantics, including absence/null/empty behaviour;
- identifier, privacy, and security consequences;
- backward/forward compatibility and migration;
- at least one realistic example and conformance test;
- relationships to relevant external standards.

## Local checks

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python Tools/check_release.py
python -m unittest discover -s tests -v
```

Generated files must be regenerated with their checked-in tool. Do not edit `Docs/VAO_SCHEMA_REFERENCE_0.5.0.md` or release-bundle digests by hand.

## Pull requests

Keep commits focused. Update normative text, schema, semantic checks, fixtures, generated reference, and changelog in the same pull request when they describe one contract change. A schema-only change is incomplete.

Commits should include a Developer Certificate of Origin sign-off:

```text
Signed-off-by: Your Name <your-address@example.org>
```

By signing off, you certify that you have the right to submit the contribution under the repository's applicable license. Do not submit confidential data, personal research data, or third-party media without permission.

## Style

- Use BCP 14 terms only for enforceable normative requirements.
- Give every normative requirement an observable conformance condition.
- Use absolute, versioned IRIs in serialized examples.
- Prefer synthetic, small, openly licensed fixtures.
- Preserve exact evidence and record transformations instead of silently normalizing it.
- Keep Python compatible with supported versions and avoid network access during validation.

## Attribution

Accepted contributors are credited through Git history and release notes. Substantial specification authorship may also be added to citation metadata with the contributor's consent.
