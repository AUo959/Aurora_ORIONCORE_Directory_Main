# Peer review: CloudBank MCP SDK v2 migration

- **Review id:** `pr-20261108-mcp-v2-migration` · **Reviewer:** claude-code · **Author:** codex
- **Reviewed at:** 2026-11-09T05:14:16Z · **Warrant level:** artifact
- **Verdict:** **approve-with-notes** · **Debt:** `rd-20261108-mcp-v2-migration` cleared
- **Implementation:** <https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1691> · **Root sync:** <https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/110> (`f2425a73`)
- **Target:** base `28db5950e404ca2ec9fc007a1b5c6c114c3641dd` → merged `f289f69c7e843678ae0d882f25862d38c0883084`

## Summary

The SDK 2.3 migration does what it claims. Using my own harness (an SDK 1.30 client in a separate environment, a loopback fixture backend, stdio, SSE and an installed wheel outside the checkout) the five tool wire schemas and descriptions are byte-identical to the pre-migration v1 server's; invalid arguments produced zero backend requests; backend bearer and identifying headers are correct; execution errors are sanitized; a missing jsonschema fails closed; the wheel contains all modules and its console entry works; the hash-verified binary-only install is clean. CloudBank make check reproduced the author's full-suite totals exactly. One note-level security finding: the SSE listener, now loopback-only, accepts any Host and Origin header, so it has no DNS-rebinding guard (f1, follow-up queued). It is not a regression: the base bound every interface, and its SSE route returned HTTP 500 under SDK 1.30. Error-envelope semantics changed in two small ways (f2). The root suite's author totals could not be reproduced without nested repos (f4).

## Independently executed verification

| Gate | Command | Result | Evidence |
|---|---|---|---|
| environment | `python3.12 venvs: env-ci (hash install), env-v1 (mcp==1.30.0 client), env-wh (wheel); root repo venv Python 3.12.13` | pass | Network available. CloudBank was cloned fresh; no live Aurora, model-provider credentials or production services were used. All backend traffic went to a 127.0.0.1 fixture. |
| target-diff | `git diff --stat 28db5950 f289f69c` | pass | 20 files, +616/-562. Nothing outside connector/, tests/connector, docs/operations and requirements-*; simulation/ is untouched. |
| hash-verified install | `pip install --require-hashes --only-binary=:all: -r requirements-ci-hashed.txt (fresh py3.12 venv); pip check` | pass | Exit 0; 'No broken requirements found'. mcp 2.3.0, mcp-types 2.3.0, httpx 0.28.1, httpx2 2.12.0, jsonschema 4.26.0, starlette 1.6.0, uvicorn 0.52.4. |
| requirement agreement | `parse requirements-lock.txt and requirements-ci-hashed.txt; read connector/pyproject.toml, requirements-optional.txt, requirements-test.txt` | pass | pyproject mcp>=2.3.0,<3.0.0 (httpx>=0.27,<1.0 retained); optional mcp>=2.3.0,<3.0.0; test mcp==2.3.0; lock and CI-hashed both mcp==2.3.0, mcp-types==2.3.0, httpx==0.28.1, httpx2==2.12.0, opentelemetry-api==1.45.2. The two lock files differ only in four platform-conditional packages (tzdata, colorama, httpx2-jsfetch, pywin32). |
| connector tests | `python -m pytest tests/connector tests/test_mcp_connector_wired.py -q (CI-hashed env)` | pass | 71 passed, 73 skipped (the skips are the legacy live-backend tests that need AURORA_CONNECTOR_TOKEN and a running Aurora API). |
| make check | `make check (CloudBank, .venv -> the hash-installed env)` | pass | exit 0: 3818 passed, 92 skipped, 9 xfailed, 2 xpassed, 61 warnings in 364s. Identical to the author's 3,818/92/9/2 (the 101 subtests are GitHub-only). |
| wire-schema parity | `SDK 1.30 client (env-v1) -> base v1 server (28db5950, SDK 1.30) vs target v2 server (SDK 2.3); compare tools/list over stdio and SSE` | pass | tools/list inputSchema and description are identical for all five tools (aurora_get_state, _get_agents, _get_drift, _get_ethics_log, _get_capsules) in base-stdio, target-stdio and target-SSE. Independent of the author's fixture file. |
| current + legacy discovery/dispatch | `same harness (legacy initialize/initialized client against the v2 server); plus tests/connector protocol tests run in both client modes` | pass | All five tools return non-error results through the legacy SDK 1.30 client over stdio and SSE; the repo's mcp_client fixture also runs 'auto' and 'legacy' modes. |
| invalid arguments never reach backend | `5 invalid calls (limit 0, 101, 'x'; bogus severity_filter; bogus visibility_filter) + unknown tool, counting fixture requests` | pass | All six isError:true with 'TOOL_VALIDATION_ERROR: ... (path: ...)' or 'ERROR: Unknown tool'; backend request count 0 over stdio and SSE. Valid calls hit /health, /api/drift/alerts, /api/crew/all, /gumas/violations (POST), /synergy/components. |
| fail closed without validator | `block 'jsonschema' in sys.modules then import connector.server` | pass | Prints 'ERROR: MCP SDK dependencies not installed...' and exits 1 before any server is built (see f3 for message wording). |
| sanitized execution errors | `in-process mcp.Client; replace a tool's run() with one raising RuntimeError('SECRET-DETAIL /etc/passwd'); also a fixture HTTP 500 body 'SECRET-BACKEND-DETAIL' over stdio and SSE` | pass | In-process: isError true, text "TOOL_EXECUTION_ERROR: tool 'aurora_get_state' failed; check server logs", no secret text. Over the wire the 500 body never appears in results. |
| backend headers | `fixture backend logs every request header` | pass | Authorization: Bearer <token> and X-Source-Client: aurora-mcp-connector on every request, all five tools, stdio and SSE. |
| real stdio session cleanup | `mcp 1.30 stdio_client context exit; observe process` | pass | Exits 0 in every stdio run; no stray connector.server processes. |
| real SSE session + cleanup | `start server with --transport sse --port N, connect SDK 1.30 sse_client to /sse, SIGTERM server` | pass | Works, including /messages/ posting. Server logs orderly 'Shutting down / Application shutdown complete'; no traceback. Contrast: the base (v1) SSE endpoint returned HTTP 500 on /sse with SDK 1.30, so the SSE fix is real. |
| SSE listener default | `lsof -iTCP -sTCP:LISTEN for default and --host 0.0.0.0; --help` | pass | Default: 127.0.0.1:PORT only. --host 0.0.0.0: *:PORT. --help documents --host default 127.0.0.1. README and migration doc say SSE defaults to loopback, that backend bearer credentials authenticate to the backend only, and that gateways must protect both /sse and /messages/. |
| DNS-rebinding probe | `curl -H 'Host: evil.example.com' -H 'Origin: http://evil.example.com' http://127.0.0.1:PORT/sse` | fail | HTTP 200 for a foreign Host and Origin. SseServerTransport is built without security_settings (its constructor accepts them). See f1. |
| installed wheel | `pip wheel --no-deps ./connector; unzip -l; fresh venv pip install '<wheel>[sse]'; pip check; run from an empty directory outside the checkout` | pass | Wheel contains connector/{__init__,server}.py, auth/, tools/ (5 modules + __init__), transport/. pip check clean. 'python -I -c import connector.server' resolves to site-packages. SDK 1.30 client passes the same probe through `aurora-mcp` (console script), `python -m connector.server` and SSE, with schemas identical to the checkout's. |
| legacy client interop | `env-v1 (mcp==1.30.0) client against env-ci / env-wh (mcp 2.3.0) servers` | pass | Separate environments; stdio and SSE; discovery, dispatch, validation errors all work. |
| simulation owner unchanged | `git rev-parse 28db5950:simulation vs f289f69c:simulation, and :simulation/l1_runtime.py` | pass | Tree 0ac84cbb... unchanged; blob 5b6d93515fb219cb26d267db6c6df6c052413ae1 unchanged and equal to owner.git_blob_sha in catalog/ace/policies/orion_progression_v0_13.json. |
| root pins agree | `git show f2425a73 (PR #110); grep pins` | pass | catalog/repo_registry.yaml head_sha, policy cloudbank_repository_sha and tests/test_aurora_ace_orion_progression.py CLOUDBANK_SHA are all f289f69c...; no other repository pin moved in #110. |
| progression test vs real checkout | `temporary symlink of the target checkout at GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main; pytest tests/test_aurora_ace_orion_progression.py; link removed` | pass | 10 passed. Worktree clean afterwards. |
| session-state-check | `make session-state-check` | pass | OK. |
| registry-sync-check | `make registry-sync-check (fresh worktree and canonical checkout)` | pass | Fresh worktree: 0 in sync, 0 drifted, 9 skipped (nested repos absent). Canonical checkout: 5 in sync, 0 drifted, 4 skipped. The canonical CloudBank path is not a usable git repo here, so the pin is verified by the checks above, not by this tool. |
| integration gate | `python tools/aurora_integration_gate.py` | pass | Verdict warn (existing advisories: command_gateway_safety, manifest/registry coverage, queue_review_due), exit 0, all six subprocesses returned 0. Its session_claim_check fails while the reviewer's own mutating claim is active, as in the previous review, so the claim was released first. |
| root full suite | `python -m pytest tests -q (fresh root worktree at 1bbc7424)` | fail | 726 passed, 74 skipped, 8 failed; all 8 require nested repos absent from a fresh worktree (CloudBank checkout, sim tree). See f4. The author's 773 passed, 41 skipped was in a provisioned checkout. |

## Findings

### f1 — note (accepted-with-note)

The SSE transport has no DNS-rebinding or Origin protection. build_sse_app constructs SseServerTransport('/messages/') with no security_settings, so a browser page that rebinds a hostname to 127.0.0.1 could open /sse and /messages/ on the default loopback listener and call the read-only tools with the connector's backend bearer token. Loopback-by-default (the documented control) stops network peers, not browser-mediated access. The migration did not introduce this: the base bound all interfaces, and its SSE route did not work at all. The README's authenticated-gateway guidance covers external deployments only.

**Evidence:** curl -H 'Host: evil.example.com' -H 'Origin: http://evil.example.com' http://127.0.0.1:18773/sse -> 200 (also 200 with Host 127.0.0.1:18773 and the foreign Origin). connector/server.py build_sse_app: SseServerTransport('/messages/'); mcp.server.sse.SseServerTransport.__init__(self, endpoint, security_settings=None, max_request_body_size=4194304) accepts mcp.server.transport_security.TransportSecuritySettings.

**Correction:** Pass TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=[loopback names with port], allowed_origins=[...]) for the loopback default, make --host deployments extend the allow-list explicitly, add a test that a foreign Host/Origin gets 4xx, and document it. Queued as connector-sse-dns-rebinding-guard.

### f2 — note (accepted-with-note)

Error-envelope semantics changed slightly for clients. An unknown tool now returns isError:true (v1 server: isError:false with the same 'ERROR: Unknown tool' text), and argument-validation failures now read 'TOOL_VALIDATION_ERROR: <msg> (path: ...)' instead of the SDK 1.30 text 'Input validation error: <msg>'. Both are consistent with the README ('existing error prefixes and isError: true') and are arguably more correct, and the five tool schemas are unchanged, but a consumer that matched the old text or relied on isError:false for unknown tools will notice. The migration doc's 'retain' wording slightly understates this.

**Evidence:** Same SDK 1.30 client against base and target: base nonexistent -> isError False; target -> isError True. base aurora_get_ethics_log {limit:0} -> 'Input validation error: 0 is less than the minimum of 1'; target -> 'TOOL_VALIDATION_ERROR: 0 is less than the minimum of 1 (path: limit)'. Probe output files base_stdio.json / v2_stdio.json in the reviewer scratchpad.

**Correction:** None required; note the changed envelope in the connector README on the next touch.

### f3 — nit (accepted-with-note)

The fail-closed import guard prints 'Run: pip install "mcp>=2.3.0,<3.0.0"' for any missing dependency, including jsonschema, which is a separate direct requirement of the standalone package. The behaviour (exit 1 before startup) is correct; only the hint is imprecise.

**Evidence:** With sys.modules['jsonschema']=None, importing connector.server prints that message and raises SystemExit(1). connector/server.py lines 22-40.

**Correction:** Name the missing module from the ImportError in the message. Optional.

### f4 — note (accepted-with-note)

Root-suite totals could not be reproduced in a fresh worktree: 8 failures, all caused by absent nested repos, and 808 collected tests against the 814 implied by the author's 773 + 41 (6 unexplained, same discrepancy as the previous review). The one MCP-relevant failure (progression owner binding, which needs the registered CloudBank checkout) passes when the real target checkout is provided. No evidence the migration changes any of them.

**Evidence:** pytest tests: 8 failed, 726 passed, 74 skipped; each failure reads 'registered CloudBank checkout is unavailable' or FileNotFoundError under GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main. With the checkout symlinked: tests/test_aurora_ace_orion_progression.py 10 passed.

**Correction:** None for this PR. Environment note only.

## Not verified

- The author's GitHub canonical-suite count (with 101 subtests) and the root 773/41 totals: CI results were not reproduced locally beyond make check in CloudBank.
- Behaviour against a live Aurora API, model-provider hosts or any production service (out of scope by instruction); backend traffic was a loopback fixture.
- SDK 1.30 against an SDK 2.x streamable-HTTP transport (the connector exposes only stdio and SSE).
- Python 3.11 (pyproject floor); all runs used 3.12.
- Lint (ruff) and Windows/wasm lock branches.

## Decision

Approve with notes. No finding blocks the migration: the five frozen tool schemas, validation, sanitization, headers, wheel, locks and legacy-client interoperability all reproduced independently, and the loopback default is a strict improvement over the base. `rd-20261108-mcp-v2-migration` is cleared and `review-mcp-v2-migration-20261108` completed. The DNS-rebinding hardening (f1) is queued as `connector-sse-dns-rebinding-guard`; it is a further change in the mcp-connector domain, so under the protocol it incurs its own review debt and needs the complementary reviewer (whichever platform does not implement it).
