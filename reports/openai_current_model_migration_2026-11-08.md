# Direct current OpenAI capability — migration receipt

Requested by the owner after the development restart: replace GPT-4o with
direct capability for OpenAI's current models.

## Delivered behavior

CloudBank PR #1680 replaces default OpenAI routing with GPT-6.1 Sol and adds
explicit GPT-6 Astra selection. General/code tasks start with Sol; Claude-first
reasoning/math chains use Sol as their OpenAI fallback. GPT hub code/reasoning/
agent routes and Claude's OpenAI fallback no longer route to GPT-4o. Astra is
explicit-only in the shipped defaults. GPT-4o is disabled; compatibility enum
and hub names remain.

The adapter calls OpenAI's Responses API directly with supported reasoning and
output controls, non-strict legacy function-schema compatibility, no unsupported
sampling parameters, and provider storage disabled. Text, tool calls, usage,
and completion status are decoded. Incomplete billed output counts against the
token budget. Tools are returned, not executed by the adapter.

The primary completion API forwards explicit current-model and reasoning
preferences. Existing server-side OPENAI_API_KEY configuration is honored when
no constructor key is supplied. Secrets were not created, persisted, or exposed.

## Sources and tests

Official catalog, model specification/pricing, and migration pages were fetched
and inspected. CloudBank's docs/OPENAI_CURRENT_MODEL_MIGRATION_2026-11-08.md
records the URLs and source digests. Catalog verification occurred November 8
UTC (November 7 in New York).

Final CloudBank CI at af5f0e84: 3,704 passed / 113 skipped / 9 xfailed /
2 xpassed, plus 101 subtests passed. Existing unexpected-pass markers were
retained. Focused tests: 112 passed / 1 optional aiohttp skip. All nine adapter/routing/
budget tests also pass with the repository's pinned OpenAI SDK 3.6.0. Two
parameterized HTTP-mock cases use the real SDK to serialize both model IDs and
decode text/tools/usage; the others cover retirement routing, credential
precedence, failure fallback, explicit-only Astra, incomplete accounting, and a real
remaining-budget block before provider fallback.
Primary API forwarding is covered separately. No paid provider call or account
entitlement is claimed. Independent mesh/GitHub Models integrations are outside
this direct AI-core migration.

## Landing and root integration

CloudBank [PR #1680](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1680)
merged at `6defaef0c5304b94ad8d82e30fd66c32975fa1a4` after all applicable checks passed.
Staging deployment was skipped; no production deployment is claimed.

The GPT-4o retirement queue item is completed by this migration. Other queue
items retain their status and review dates. Root registry, Orion repository
policy pin, and independent preflight test attestation are aligned with the
merged CloudBank revision. Runtime owner source is unchanged; the attested blob
remains 5b6d93515fb219cb26d267db6c6df6c052413ae1. No live Orion simulation was advanced or
canon promoted.

Root validation: 728 passed / 41 skipped. Explicit registry-pin and session-state
checks pass. Queue: 38 open items (32 ready, 6 waiting), with the existing 38
overdue reviews retained. Root commit metadata uses the actual Git commit date
to avoid the known sync-time provenance stamping bug tracked in PR #87.

Confidence: 0.98 for documented catalog and offline contract observations.
Live provider account access and output quality remain untested here.
