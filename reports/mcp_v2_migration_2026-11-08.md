# MCP SDK v2 migration completion

November 8, 2026 (New York). Scope: the requested CloudBank connector migration;
Claude's coordination review remains in its independent PR #109.

## Connector and compatibility

CloudBank PR #1691 replaces SDK v1 decorators/private handler access with SDK
2.3 typed constructor callbacks and explicit result envelopes. All five
read-only tool schemas retain their v1 wire format. Python model fields use
SDK v2 snake_case names. Validation is mandatory, rejected calls do not reach
the backend, and execution failures keep sanitized model-facing errors.

Stdio remains the default. The SSE endpoint now uses a valid ASGI callable and
consistent message routing. SSE binds to loopback by default; `--host` is an
explicit deployment setting. External gateways must authenticate both `/sse`
and `/messages/`; the backend bearer token does not authenticate MCP clients.
The standalone wheel now includes the connector modules and console entry point.

## Dependencies and verification

SDK support is `mcp>=2.3.0,<3.0.0`, with an exact 2.3.0 CI test pin. Standalone,
optional, hashed CI and plain Linux locks agree. MCP is the only existing CI
package whose pinned version changes. SDK types/telemetry and platform-specific
closure are documented in the migration guide; core runtime hashes are retained.

- Local `make check`: 3,818 passed, 92 skipped, nine expected failures, two
  existing expected-test passes (308.40 seconds). Numerical-library threads
  were limited to one on this host, consistent with prior dependency checks.
- Real current/legacy sessions verify frozen schemas, discovery, dispatch,
  sanitized errors and input constraints. Real stdio/SSE use a controlled
  loopback API with verified bearer/identifying headers. CLI startup fails
  before protocol output when required credentials or validator are missing.
- An actual SDK 1.30 client calls the rebuilt SDK 2.3 wheel from outside the
  source checkout. Installed CLI help exposes the loopback/host contract.
- Fresh hash-verified binary installation, dependency/lock checks pass. Audits
  of MCP, mcp-types, opentelemetry-api and httpx2-jsfetch report no findings;
  this is a point-in-time dependency check, not a whole-repository audit.
- GitHub PR canonical run `42545604540`: 3,818 passed, 92 skipped, nine
  expected failures, two existing expected-test passes and 101 subtests
  (374.98 seconds). Both consumers verified exact synthetic merge checkout
  `4843263f58e31784f0a1a8ca3a0e528fc8152773`. All checks passed and #1691
  merged as `f289f69c7e843678ae0d882f25862d38c0883084`.
- Root full suite with the registered reference checkouts present: 773 passed,
  41 skipped (36.04 seconds). This is the provisioned multi-repository context;
  a clean worktree without nested repositories is a different test context.
- Main-push canonical run `42546455793` and both dependent consumers passed.
  Their exact checkout is `f289f69c7e843678ae0d882f25862d38c0883084`, matching
  the deliberately refreshed registry and independent owner attestation.
- Root integration gate: all six subprocesses return zero; existing environment,
  installed-skill and queue-review advisories remain. Registry drift is zero.

## Root synchronization and review

The root registry and independent policy/test attestation bind
`f289f69c7e843678ae0d882f25862d38c0883084`. The complete simulation tree diff
against the prior pin is empty, and the owner blob remains
`5b6d93515fb219cb26d267db6c6df6c052413ae1`. CanonRec remains on its prior
read-only pin.
Coordination-review state is carried forward from the current root main.
The migration gets its own complementary-review handoff under the adopted
asynchronous peer-review protocol, separate from session coordination.

The migration guide contains setup changes, upstream references and rollback.
Tests use controlled fixtures, without live Aurora or model-provider calls.

## Complementary review handoff

Under the adopted asynchronous peer-review protocol, the cross-repository
migration records `rd-20261108-mcp-v2-migration` in domain `mcp-connector`.
The concrete `review-mcp-v2-migration-20261108` task is assigned to Claude Code
for independent gates and a warrant-grounded receipt. This is separate from the
coordination review in PR #109; its debt and queue state are retained from main.
