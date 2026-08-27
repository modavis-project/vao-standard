# Security policy

## Supported versions

Before the first public release, only the current review candidate receives security fixes. After publication, this table will identify supported released lines.

| Version | Supported |
| --- | --- |
| 0.4.0 review candidate | Yes |
| unpublished 0.3 drafts | No |

## Reporting a vulnerability

Do not disclose a VAO parser, extraction, integrity, materialization, or runtime vulnerability in a public issue. Once the public repository enables private vulnerability reporting, use its **Security → Report a vulnerability** workflow. Before then, contact the responsible editor through the contact route on the editor's [ORCID record](https://orcid.org/0000-0002-7904-3892).

Include the affected artifact/version, minimal reproduction, impact, and any suggested mitigation. Do not include sensitive third-party content. Receipt should be acknowledged within seven days; timing for remediation and coordinated disclosure depends on severity and affected implementations.

## Processor baseline

VAO files are untrusted containers. Implementations must follow [SECURITY_CONSIDERATIONS.md](Docs/SECURITY_CONSIDERATIONS.md), including path/link checks, decompression and resource budgets, strict JSON, exact digest verification, non-execution by default, controlled network acquisition, and safe extraction.
