# Security Policy

## Supported version

Security fixes target the current `main` branch. Historical reports, recovery
artifacts, and generated receipts are retained for provenance but are not
separately supported software releases.

## Reporting a vulnerability

Do not open a public issue containing a vulnerability, credential, private
source, or exploit detail. Use GitHub private vulnerability reporting from the
repository's **Security** tab and include the affected path, impact, and a
minimal reproduction.

If the finding is in a nested repository, report it to that repository rather
than this control plane. In particular, CloudBank runtime findings belong in
`AUo959/aurora-cloudbank-symbolic`, while canon-integrity findings belong in
`AUo959/CanonRec`.

## Repository security boundary

This repository is the Aurora workspace control plane. It contains governance
tools, manifests, validation reports, simulation harnesses, and coordination
policy; it is not a hosted service or a published Python package. Nested
repositories have independent Git histories, release decisions, and security
policies.

Repository policy prohibits operational credentials. Deterministic test values
are confined to clearly scoped fixtures and excluded from deployments.
Exact historical false positives may be recorded by fingerprint in
`.gitleaksignore`; broad rules and path-wide exclusions are not accepted.

The GitHub secret-scan workflow inspects every pushed branch and pull request.
For a local history scan with the repository-pinned configuration, run:

```bash
gitleaks git --redact --config .gitleaks.toml .
```

If a real credential is found, revoke or rotate it first. Removing a value
from the current tree does not remove it from Git history.
