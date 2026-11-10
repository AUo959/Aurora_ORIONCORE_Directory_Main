# MCP connector SSE DNS-rebinding guard: author validation receipt

November 10, 2026 (UTC). Scope: root task `connector-sse-dns-rebinding-guard`
(finding f1 of `reports/analysis/peer_reviews/pr-20261108-mcp-v2-migration`).
Implementation: <https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1699>,
branch `claude/connector-sse-dns-rebinding-guard` from CloudBank main
`fe99f3e5a300ecdc21c9fdf86563834d9e782568` (includes #1693). **Not merged.**
Author: claude-code. Independent reviewer: Codex (`review-mcp-sse-dns-rebinding-guard-20261110`).

## Reviewable patch

Head `d01a6853dd3552cd4059f54e87914fe527662e79`; commits `6aba33d6` (guard, tests, docs),
`163e614b` (SonarCloud: explicit loopback origin literals, split assertions),
`e603c29f` (review findings), `d01a6853` (Codacy complexity split). Files:
`connector/server.py`, `connector/README.md`, `tests/connector/test_sse_transport_security.py` (new, 45 cases),
`tests/connector/test_protocol_transports.py` (one assertion), and
`docs/operations/MCP_SSE_DNS_REBINDING_GUARD_2026-11-09.md`. No dependency, lock, simulation or tool-schema change.

## Design

The SDK's `TransportSecuritySettings` is passed to `SseServerTransport`; its `connect_sse` and
`handle_post_message` both validate, so `/sse` and `/messages/` are covered by the same settings.
Host must be `127.0.0.1`, `localhost` or `[::1]` on the listen port (also the portless spelling on
port 80), a concrete non-loopback `--host`, or an exact `--allowed-host`; refusal is 421. Origin may be
absent; otherwise loopback web origins (any port, or portless) or exact `--allowed-origin`; refusal is 403.
Unspecified binds (IPv4 or IPv6, any spelling) trust nothing extra, wildcards are rejected at startup, and
the allowlist flags are refused for stdio. `SseEndpoint` absorbs the `ValueError` the SDK raises after it
has already sent the refusal.

## Verification (author)

| Check | Result |
|---|---|
| New transport-boundary tests (real uvicorn socket, both endpoints, IPv4/localhost/`[::1]`, real `::1` listener, absent Origin, hostile Host/Origin, missing Host, refused POST not delivered, remote allowlists, bad entries, CLI) | pass |
| Mutation: remove settings from `SseServerTransport` | 18 of 44 then-current cases fail |
| `tests/connector` + `tests/test_mcp_connector_wired.py` on final head | 99 passed, 73 skipped (live-backend tests) |
| `make check` on `e603c29f` (hash-installed env) | 3863 passed, 92 skipped, 9 xfailed, 2 xpassed (baseline 3818 + 45 new) |
| SDK 1.30 client vs guarded server over stdio and SSE, from checkout and installed wheel (`aurora-mcp`, `-m connector.server`) | pass; five tool schemas identical to the reviewed v2 target; zero backend calls on invalid arguments; no traceback on SSE shutdown |
| curl matrix on the installed wheel (default, `--host ::`) | 127.0.0.1/localhost/`[::1]` 200; `[::]`, foreign Host 421; foreign Origin 403; POST hostile Host 421 |
| Hosted checks on `d01a6853` | all green after fixing: SonarCloud (explicit loopback literals, assertions), Codacy (complexity), CodeQL (no all-interface bind in tests), and Copilot/Codex findings (IPv6 `[::]` implicit trust, port-80 default-port spellings) |

## Limitations

- `make check` was run on `e603c29f`; `d01a6853` only splits validation helpers, covered by the connector suite and hosted `test`.
- Header validation is not authentication; the gateway requirement for non-loopback deployments is unchanged.
- Any local web app on a loopback origin is accepted (SDK localhost profile); Host matching is case-sensitive; a client omitting `Host` is refused.
- Python 3.12 only. Root suites were not rerun: no root code changed.

## Root follow-through

Review debt `rd-20261110-mcp-sse-dns-rebinding-guard` is pending and independent of the cleared
`rd-20261108-mcp-v2-migration`. The registry pin, ACE policy `cloudbank_repository_sha` and the
progression-test constant are **not** moved here: CloudBank squash-merges, so the merged SHA does not
exist yet. After review and merge run `make registry-sync`, update those two attestation fields to the
merged SHA, and re-verify that `simulation/` and the `l1_runtime.py` blob (`5b6d9351...`) are unchanged
(task `sync-cloudbank-pin-sse-guard-20261110`).
