# Security policy

## Supported versions

The project provides security fixes for the current public release line.

| Version | Supported |
| --- | --- |
| 0.4.0 | Yes |
| unpublished 0.3 drafts | No |

## Reporting a vulnerability

VAO parser, extraction, integrity, materialization, and runtime vulnerabilities are handled outside public issues. GitHub's **Security → Report a vulnerability** route is the preferred channel when available. The responsible editor's [ORCID record](https://orcid.org/0000-0002-7904-3892) provides the fallback contact route.

Include the affected artifact/version, minimal reproduction, impact, and any suggested mitigation. Do not include sensitive third-party content. Receipt should be acknowledged within seven days; timing for remediation and coordinated disclosure depends on severity and affected implementations.

## Processor baseline

VAO files are untrusted containers. Implementations must follow [SECURITY_CONSIDERATIONS.md](Docs/SECURITY_CONSIDERATIONS.md), including path/link checks, decompression and resource budgets, strict JSON, exact digest verification, non-execution by default, controlled network acquisition, and safe extraction.
