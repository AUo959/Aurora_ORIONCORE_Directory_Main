# Aurora Intelligent UI — Authenticated Snapshot Retrieval v1

Date: 2026-10-15
Owner: ORIONCORE root control plane
Status: draft, review-gated
Depends on: Aurora Intelligent UI Snapshot Bridge v1 (PR #97)
Permission: one dedicated read-only bearer token; no canon/runtime permissions

## Implemented surface

- tools/aurora_intelligent_ui_service.py: authenticated local HTTP transport.
- GET /v1/mission-control/snapshot: returns existing versioned aurora.mission_control.snapshot data
  derived from the saved Mission Control report.
- tests/test_aurora_intelligent_ui_service.py: authentication, redaction,
  bounded file access, freshness, failure, and read-only behavior.
- Underlying projection: tools/aurora_intelligent_ui_bridge.py
- Data contract: catalog/schemas/aurora_intelligent_ui_snapshot.schema.json

This retrieves the latest *saved* report, not a new live report. The name
latest.json is not an assurance of freshness. Check source.generated_at
and source.freshness before describing Aurora's status.

## Run locally

Requirements: Python with fastapi and uvicorn (already used by ORIONCORE ACE
remote tooling). Install through the approved environment process.

Generate a high-entropy bearer token and SHA-256 digest on a trusted terminal:

    python3 -c "import secrets,hashlib; t=secrets.token_urlsafe(40); print('TOKEN (store privately):', t); print('DIGEST:',hashlib.sha256(t.encode()).hexdigest())"

Store the token privately in your client/connector configuration, NEVER
in Git, URL query parameters, CI logs, or shared chat. Set only its lowercase
digest in the service environment (never a repository file):

    export AURORA_UI_READ_TOKEN_SHA256="<64-char-digest>"
    python3 tools/aurora_intelligent_ui_service.py

The service always binds 127.0.0.1:8766 by default. No --host override
and no broad CORS policy are provided. On the same trusted host:

    curl --fail --silent --show-error -H "Authorization: Bearer <PRIVATE_TOKEN>" http://127.0.0.1:8766/v1/mission-control/snapshot

Use --port 8767 for an alternate local port. --root is only for
a trusted operator's checkout, not a request parameter.
Ensure the token is not exposed in saved command history; a secure
credential store is preferred.

Run regression tests:

    python3 -m pytest -q tests/test_aurora_intelligent_ui_bridge.py tests/test_aurora_intelligent_ui_service.py

## Safety boundary

- Fail closed at startup without a valid lowercase SHA-256 token digest.
- Check bearer header using a constant-time digest comparison.
- Unauthorized request: 401; invalid/missing source: generic 503, no path leakage.
- No unauthenticated health route, Swagger/OpenAPI docs, broad CORS,
  POST/write method or remote host binding.
- Read only one fixed saved report, rejecting symlinks, paths outside
  the repository, and files larger than 2 MiB.
- Return Cache-Control: no-store and X-Content-Type-Options: nosniff.
- Reads never trigger report regeneration or Aurora state mutation.
- Recovery-review evidence stays withheld by the existing bridge adapter.
- Bearer token grants ONLY derived snapshot read, not ACE/CanonRec
  authority, simulation execution or a GitHub credential.
- No public plaintext HTTP; remote deployment requires a separate
  TLS and connector-security review. This PR is NOT that deployment.
- Source SHA-256 records input bytes but cannot attest truth or freshness.

## ChatGPT integration boundary

ChatGPT's native interface cannot directly invoke arbitrary localhost
services. The next operational step is an explicitly approved tool/connector
registration behind TLS and proper authentication. Until then, ChatGPT
can present repository-backed snapshot values with historical timestamps.
No live connection is claimed by this PR.

PR #97, model routing, canon, L1 deterministic runtime and simulation
control operations remain unchanged.
