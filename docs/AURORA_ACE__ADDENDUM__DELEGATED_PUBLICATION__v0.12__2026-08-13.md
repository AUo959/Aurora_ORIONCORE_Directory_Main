# Aurora Canon Engine — Delegated Publication Addendum v0.12

**Status:** implementation contract  
**Date:** 2026-08-13  
**Capability:** `ace.capability.canonrec.publish.delegated_pr`

## Purpose

ACE v0.12 adds a governed publication step above the native materializers introduced in v0.2–v0.11.

The publication sequence is:

```text
validated commit-ready packet
  -> authenticated remote principal
  -> ace:publish + ace:autonomic + ace:materialize
  -> authority_ref binding
  -> committed publication policy
  -> exact-source verified publisher
  -> registered CanonRec baseline check
  -> remote main equality check
  -> isolated ACE feature branch
  -> existing native materializer
  -> one proposal commit
  -> push feature branch
  -> open draft CanonRec PR
  -> restore local CanonRec checkout
```

Publication does **not** merge the pull request or advance CanonRec `main`.

## Authority boundary

Network authentication, materialization authority, autonomic execution, and publication authority are separate controls.

A remote caller must possess all three scopes:

- `ace:publish`
- `ace:autonomic`
- `ace:materialize`

The requested `authority_ref` must also be explicitly bound to that authenticated principal.

The endpoint cannot select another repository, remote, base branch, feature-branch namespace, materializer, or merge behavior. Those are fixed by `ace.policy.publication.delegated-pr.v1`.

## CanonRec naming admission

CanonRec requires every new named L2 referent to carry a native `naming_receipt` or a permitted naming exemption.

v0.12 therefore repairs the generic L2 completion boundary introduced in v0.11:

- generic names are passed through CloudBank's deterministic `NameService` against the registered CanonRec name registry;
- a caller-supplied name is treated as a forced NameService candidate, not as an implicit exemption;
- the resulting native `naming_receipt` is embedded in the generic entity candidate;
- owner-gated generic preview/commit re-runs CanonRec's naming validator;
- delegated publication refuses any generic naming warning and routes that case to human review instead of autonomously opening a proposal.

Characters retain the existing CharForge + NameService publication path. L1 facility bindings do not use the L2 naming-admission gate.

## Publication invariants

A delegated publication may proceed only when:

1. the packet is already `commit_ready`;
2. the packet's CanonRec baseline equals the registered CanonRec baseline;
3. the local CanonRec checkout is clean and on registered `main`;
4. CanonRec `origin` is exactly `AUo959/CanonRec`;
5. remote `main` still equals the registered baseline;
6. the deterministic proposal branch does not already exist locally or remotely;
7. the existing native materializer produces exactly one proposal commit;
8. the resulting worktree is clean;
9. the feature branch push succeeds; and
10. a draft PR is opened successfully.

If a branch push succeeds but PR creation fails, ACE attempts to delete the orphan remote branch. The local registered CanonRec checkout is restored after every attempt.

## Replay semantics

The proposal branch name is derived deterministically from the packet kind, subject, and source determination. If that branch already exists, publication fails closed. Reusing a packet cannot silently create another independent canon proposal.

## Review remains sovereign

A successful v0.12 response means:

> ACE created a reviewable CanonRec proposal from validated material under explicit delegated authority.

It does **not** mean:

> CanonRec main has changed.

The publication receipt therefore records `status: review_pending` and `mainline_canon_advanced: false`. CanonRec CI and human/project review remain the authority that determines whether the proposal is promoted.

## Deliberate exclusions

v0.12 does not:

- auto-merge CanonRec pull requests;
- bypass branch protection;
- accept arbitrary Git remotes or repository paths;
- convert a manifest into arbitrary Python execution;
- expose delegated publication through the six-tool stdio MCP surface;
- grant Orion INIT, resume, provider-activation, or tick-advance authority.

Those boundaries are intentional and are covered by adversarial tests.
