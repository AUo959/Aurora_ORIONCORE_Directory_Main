# Aurora ACE v0.10 Addendum — Authenticated Remote Service and Verified Runtime Bindings

Date: 2026-08-13  
Status: implementation contract

## Purpose

ACE v0.10 makes the existing ACE engine remotely addressable without turning network access into canonical authority and without allowing capability metadata to become arbitrary code execution.

The remote path is:

`authenticated HTTPS caller -> principal/scopes -> ACE invocation envelope -> validated manifest -> verified runtime binding -> shared resolver -> determination`

Canonical materialization remains the v0.8/v0.9 two-phase native transaction. Remote transport only adds an authenticated doorway to it.

## Authentication

The service refuses startup unless `ACE_REMOTE_PRINCIPALS_JSON` contains at least one valid principal. Entries contain a principal identifier, a SHA-256 digest of the bearer token, explicit scopes, and optional materialization authority references. Plaintext tokens or secrets in the configuration are rejected.

Every `/v1/*` route requires bearer authentication. The authenticated principal replaces any caller identity claimed by the incoming invocation. Autonomic invocations additionally require `ace:autonomic`. Materialization requires `ace:materialize` and the requested `authority_ref` must be explicitly bound to that principal.

The v0.8 preview token remains a transaction confirmation receipt, not an authentication credential.

## Network boundary

The standalone server binds to loopback by default. Non-loopback binding is refused unless both TLS certificate and key files are provided. CORS is not enabled. Request bodies are capped at 1 MiB.

Deployment behind a separate reverse proxy is possible by keeping ACE itself loopback-bound; proxy identity does not replace ACE bearer authentication.

## Verified dynamic execution

ACE no longer needs router source edits for each registered root-owned Python resolver. A separate committed registry at `catalog/ace/runtime_bindings.json` identifies the module/callable for each executable capability.

Execution requires all of the following to agree:

1. a schema-valid, integrity-valid, active and allowlisted ACE capability manifest;
2. the selected manifest digest;
3. a binding-registry record for that exact capability ID;
4. identical repository, source path, and entrypoint declarations;
5. an `ace.*` import namespace;
6. the exact pinned Git blob identity of the source file; and
7. the imported module's `__file__` resolving to that source.

A capability manifest by itself still cannot import Python. A binding registry entry by itself cannot execute an unmanifested capability. This is dynamic registration under two independent committed control-plane receipts, not arbitrary plugin loading.

## Authority boundary

v0.10 does not add new CanonRec serializers, autonomous Git publication, Orion INIT/resume/advancement, provider activation, or GUMAS mutation authority. Those remain later v1.0 program slices.
