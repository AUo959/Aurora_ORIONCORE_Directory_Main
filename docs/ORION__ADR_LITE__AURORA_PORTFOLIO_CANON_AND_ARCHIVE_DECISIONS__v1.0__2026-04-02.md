---
title: ADR-Lite — Aurora Portfolio Canon and Archive Decisions
doc_type: adr_lite
status: accepted
version: 1.0
date: 2026-04-02
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
decision_scope: portfolio_structure
---

# ADR-Lite — Aurora Portfolio Canon and Archive Decisions

## Status
Accepted

## Context
The active Aurora / ORION repo surface contains a real control-plane layer, a real platform hub, multiple spoke repos, several satellites, and some naming/documentation drift.

The core problem is not lack of architecture. The core problem is uneven declaration of role across repos, which creates unnecessary canon drift.

## Decision
The portfolio is declared as follows:

- `Aurora_ORIONCORE_Directory_Main` is the **portfolio root / control plane**.
- `aurora-cloudbank-symbolic` is the **platform hub / CONSTELLATION-PRIME**.
- `AuroraOS` is the **runtime spoke / AURORA-RUNTIME**.
- `cloudbank-quantum-en` remains **active** as the frontend/workstation spoke **QUANTUM-VAULT**, despite stale root README drift.
- `qgia-knowledge-library` and `qgia-knowledge-spine` are accepted as active knowledge spokes.
- `zip_wizard` is treated as tooling-adjacent until it carries a local constellation receipt.
- `DuelSim_v2.0` and `CanonRec` remain active satellites under workspace management.
- `aurora-cloudbank-symbolic1` is approved for archive.

## Rationale
This decision preserves the architecture already visible in control-plane materials and repo-local manifests while reducing ambiguity created by stale names and stale root documentation.

The most important separations are:
- control-plane truth vs platform truth
- spoke declaration vs implied adjacency
- active satellites vs core canon
- stale documentation vs actual current role

## Evidence sources consulted
### Control-plane repo
- `README.md`
- `catalog/repo_registry.yaml`
- `docs/workspace-map.md`

### Related repositories
- `AUo959/aurora-cloudbank-symbolic/.aurora/constellation.json`
- `AUo959/AuroraOS/.aurora/constellation.json`
- `AUo959/cloudbank-quantum-en/.aurora/constellation.json`
- `AUo959/qgia-knowledge-library/.aurora/constellation.json`
- `AUo959/qgia-knowledge-spine/.aurora/constellation.json`
- visible root `README.md` files where present

## Consequences
### Positive
- Portfolio governance becomes explicit.
- Repo naming drift loses power to distort canon.
- The hub-and-spoke constellation becomes documentable and maintainable.
- Archive action on `aurora-cloudbank-symbolic1` reduces noise immediately.

### Costs
- Some repos still need root-document cleanup.
- `zip_wizard` still needs a local node receipt if it is to be treated as fully integrated.
- `CanonRec` still needs a basic identity document.
- `cloudbank-quantum-en` still needs README repair to match its live role.

## Immediate follow-on
1. Archive `aurora-cloudbank-symbolic1`.
2. Refresh `cloudbank-quantum-en` root README.
3. Decide whether `zip_wizard` should be promoted to a declared spoke.
4. Add `CanonRec` root identity documentation.
5. Keep future portfolio changes gated through explicit registry updates.

## Canon guardrail
No repository is considered canonical because of its name alone.

Role must be supported by one or more of:
1. control-plane registration,
2. repo-local declaration,
3. stable cross-repo contract evidence.

## Review note
This ADR-lite is intentionally compact. It records the portfolio decision boundary and the archive decision for `aurora-cloudbank-symbolic1` without replacing the more detailed registry document.
