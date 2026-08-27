---
title: Aurora Canon Engine MCP Exposure Addendum
doc_type: normative_addendum
status: owner_directed_implementation
version: 0.7.0
date: 2026-08-12
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
augments:
  - docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md
  - docs/AURORA_ACE__ADDENDUM__FIRST_CLASS_INVOCATION__v0.2__2026-08-11.md
  - docs/AURORA_ACE__CAPABILITY_DISCOVERY__v0.6__2026-08-12.md
---

# ACE v0.7 — MCP Exposure

## Purpose

ACE v0.7 exposes the stabilized ACE engine to MCP hosts without making MCP part
of ACE's internal capability architecture.

The invariant is:

`MCP caller -> thin MCP adapter -> ACE invocation envelope -> validated manifest router -> shared ACE resolver -> determination + provenance`

MCP is transport. It does not own retrieval rules, capability registration,
entity synthesis, authority, or determination semantics.

## Initial tool surface

v0.7 exposes exactly four tools:

1. `ace_capabilities` — returns the validated manifest-derived capability index.
2. `ace_plan` — validates an existing inspectable invocation and selects the
   runtime capability without executing it.
3. `ace_resolve` — executes the same shared ACE invocation engine used by the
   CLI and writes only into the bounded MCP runtime packet directory.
4. `ace_inspect` — retrieves recorded invocation/determination provenance by
   stable reference.

No tool in v0.7 grants canonical materialization authority.

## Transport boundary

The first MCP surface is stdio-only.

v0.7 MUST NOT start an HTTP listener, expose a network socket, or introduce a
remote authentication model. Network deployment is a separate security and
operations decision.

The MCP SDK dependency is isolated from the core ACE package. OrionCore's
Python 3.9 compatibility lane can continue to import and test ACE without
installing MCP, while a dedicated Python 3.12 workflow validates the real SDK
registration surface.

## Filesystem boundary

MCP resolution packets are restricted to:

`reports/ace/mcp_runtime/<output_name>`

`output_name` is an identifier, not a path. Absolute paths, separators,
traversal tokens, and targets outside the bounded runtime directory are
rejected.

This ensures that a transport caller cannot repoint ACE resolution directly at
CanonRec, CloudBank, OrionCore source paths, or another arbitrary filesystem
location.

## Authority boundary

v0.7 does not expose:

- `materialize_packet`;
- CanonRec Git writes;
- generic entity publication;
- arbitrary Python entrypoints or imports;
- direct manipulation of the ACE runtime binding allowlist.

A normal ACE determination may still report that canonical materialization is
available, blocked, or requires authority. MCP may inspect that state, but it
cannot trigger materialization in v0.7.

Authorized MCP materialization, if adopted, is a later version with its own
explicit authority receipt, side-effect declaration, confirmation semantics,
and transaction tests.

## Inspectability boundary

MCP does not create a private provenance system.

`ace_inspect` reads the existing inspectable invocation sidecars, bounded MCP
runtime packet JSON, and append-only ACE determination ledger. It accepts one
stable invocation or determination reference at a time and is bounded by a
finite JSON scan limit.

## SDK contract

The official Model Context Protocol Python SDK v2 line is used for protocol
registration. The executable server uses `MCPServer` and stdio transport.
Protocol validation runs on Python 3.12 and enumerates the registered tools
through the SDK client against the in-memory server object.

The transport-specific module is:

`tools/aurora_ace_mcp.py`

The dependency-free trust boundary is:

`tools/ace/mcp_adapter.py`

## Acceptance criteria

v0.7 is complete only when:

- exactly four tools are registered;
- plan and resolve require normal ACE invocation envelopes;
- routing remains manifest-backed;
- resolve writes only under the bounded MCP runtime root;
- path traversal and arbitrary targets fail closed;
- inspect can recover invocation/determination provenance;
- no MCP tool exposes canonical materialization;
- Python 3.9 ACE unit tests remain independent of the MCP SDK;
- Python 3.12 protocol validation enumerates the real registered tools;
- normal OrionCore CI and gitleaks remain green.

## Runtime invariant

This addendum and its implementation do not INIT Orion, resume simulation,
activate providers, advance a tick, or advance L1 station time.
