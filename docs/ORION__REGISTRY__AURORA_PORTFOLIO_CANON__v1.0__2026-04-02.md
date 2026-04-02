---
title: Aurora Portfolio Registry
doc_type: portfolio_registry
status: canonical_working_registry
version: 1.0
date: 2026-04-02
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
scope: active_non_lafinca_constellation
authoring_mode: evidence_grounded
---

# Aurora Portfolio Registry

## Purpose
This document declares the current portfolio structure for the Aurora / ORION constellation.

It separates:
- the **workspace control plane**
- the **platform hub**
- the **attached spoke repos**
- the **tooling-adjacent repos**
- the **satellites**
- the **archive lane**

This registry is grounded in the current workspace-control documentation and repo-local constellation manifests where present.

## Scope and evidence basis
The role assignments below were derived from the following sources available at review time:
- `README.md` in `AUo959/Aurora_ORIONCORE_Directory_Main`
- `catalog/repo_registry.yaml` in `AUo959/Aurora_ORIONCORE_Directory_Main`
- `docs/workspace-map.md` in `AUo959/Aurora_ORIONCORE_Directory_Main`
- `.aurora/constellation.json` where present in related repositories
- root `README.md` files in related repositories where present

This document is intended to stabilize portfolio truth, not to replace repo-local documentation.

## Canonical structure

### Portfolio root / control plane
**Repo:** `AUo959/Aurora_ORIONCORE_Directory_Main`  
**Role:** Workspace control plane, registry, manifests, move planning, verification surface  
**Canon class:** `CANONICAL_PORTFOLIO_ROOT`  
**Operational status:** `active`

**Basis**
- Declares itself the workspace control plane.
- Tracks workspace manifests, repo registry, relocation plan, and verification tooling.
- Identifies currently tracked active nested repos under workspace management.

**Rule**
- Portfolio truth lives here.
- This repo is the authoritative portfolio map and governance surface.
- This repo is not the main application runtime or the main implementation hub.

---

### Platform hub
**Repo:** `AUo959/aurora-cloudbank-symbolic`  
**Role:** Central platform hub  
**Constellation designation:** `CONSTELLATION-PRIME`  
**Canon class:** `CANONICAL_PLATFORM_HUB`  
**Operational status:** `active`

**Basis**
- Repo-local constellation manifest declares this repository as `CONSTELLATION-PRIME` with role `hub`.
- Hub manifest references runtime, quantum vault, knowledge corpus, knowledge spine, and zipwiz engine as downstream constellation surfaces.
- Root README presents this repo as the main Aurora CloudBank Symbolic platform.

**Rule**
- Platform truth lives here.
- Spoke integrations should target this hub unless a narrower contract is explicitly declared.

---

### Runtime spoke
**Repo:** `AUo959/AuroraOS`  
**Role:** Agent runtime / tool gateway  
**Constellation designation:** `AURORA-RUNTIME`  
**Canon class:** `ACTIVE_SPOKE_RUNTIME`  
**Operational status:** `active`

**Basis**
- Repo-local constellation manifest declares `AuroraOS` as `AURORA-RUNTIME` with role `spoke`.
- Current stated role includes agent runtime, MCP server, Slack integration, Inngest workflows, and constellation tool gateway.

**Rule**
- Runtime, orchestration, and tool-gateway concerns belong here unless they are truly hub-level platform concerns.

---

### Frontend / analyst workstation spoke
**Repo:** `AUo959/cloudbank-quantum-en`  
**Role:** Frontend interface / analyst workstation / simulation dashboard  
**Constellation designation:** `QUANTUM-VAULT`  
**Canon class:** `ACTIVE_SPOKE_FRONTEND`  
**Operational status:** `active_with_doc_drift`

**Basis**
- Repo-local constellation manifest declares this repo as `QUANTUM-VAULT` with role `spoke`.
- Current role is a frontend interface and command/workstation surface.
- Root README still reflects an older starter-template state, so this repo currently has documentation drift.

**Rule**
- Treat this repo as an active frontend spoke.
- Root documentation should be updated to match its current role.

---

### Knowledge corpus spoke
**Repo:** `AUo959/qgia-knowledge-library`  
**Role:** Curated knowledge corpus  
**Constellation designation:** `QGIA-CORPUS`  
**Canon class:** `ACTIVE_SPOKE_KNOWLEDGE_CORPUS`  
**Operational status:** `active`

**Basis**
- Repo-local constellation manifest declares this repository as `QGIA-CORPUS` with role `spoke`.
- Current role is the curated domain corpus / reference layer.

**Rule**
- Curated domain knowledge, structured references, and corpus-level artifacts live here.

---

### Knowledge spine spoke
**Repo:** `AUo959/qgia-knowledge-spine`  
**Role:** Methodology backbone / taxonomy / index layer  
**Constellation designation:** `QGIA-SPINE`  
**Canon class:** `ACTIVE_SPOKE_KNOWLEDGE_SPINE`  
**Operational status:** `active`

**Basis**
- Repo-local constellation manifest declares this repository as `QGIA-SPINE` with role `spoke`.
- Current role is the methodological backbone, cross-reference structure, and taxonomy layer.

**Rule**
- Methodological frameworks, cross-reference structures, taxonomy, and indexing logic live here.

---

### Tooling-adjacent engine
**Repo:** `AUo959/zip_wizard`  
**Role:** Archive tooling / analysis utility  
**Canon class:** `ACTIVE_TOOLING_ADJACENT`  
**Operational status:** `active_partial_constellation_receipt`

**Basis**
- Root README describes ZIP Wizard as an archive-management and analysis application.
- The platform hub manifest references `zipwiz.engine` as a downstream node.
- This pass did not confirm a local constellation receipt in `zip_wizard` itself.

**Rule**
- Treat this repo as tooling-adjacent and constellation-related.
- Do not mark it as a fully registered spoke until its local node receipt exists.

---

### Active satellites under workspace management

#### `AUo959/DuelSim_v2.0`
**Role:** Domain simulation satellite  
**Canon class:** `ACTIVE_SATELLITE`  
**Operational status:** `active`

**Basis**
- Workspace control-plane files identify `DuelSim_v2.0` as an active nested repo.
- Its own repo identity is mature and independent.

#### `AUo959/CanonRec`
**Role:** Satellite repo under workspace management  
**Canon class:** `ACTIVE_SATELLITE_UNDERDOCUMENTED`  
**Operational status:** `active`

**Basis**
- Workspace control-plane files identify `CanonRec` as an active nested repo.
- Current top-level identity documentation is insufficient.

**Rule**
- Satellites remain in the portfolio registry.
- Satellites are not treated as core hub/spoke constellation nodes unless explicit node registration is added.

---

### Archive lane

#### `AUo959/aurora-cloudbank-symbolic1`
**Role:** Outlier / misnamed / non-canonical repo  
**Canon class:** `ARCHIVE_APPROVED`  
**Operational status:** `pending_archive`

**Basis**
- Visible root identity does not align with Aurora platform canon.
- Portfolio owner approved archive disposition.

**Disposition**
- Archive approved.
- Remove from active naming surface to reduce canon drift.

## Active portfolio table

| Repo | Role | Canon class | Status |
|---|---|---|---|
| `Aurora_ORIONCORE_Directory_Main` | Portfolio root / control plane | `CANONICAL_PORTFOLIO_ROOT` | active |
| `aurora-cloudbank-symbolic` | Platform hub | `CANONICAL_PLATFORM_HUB` | active |
| `AuroraOS` | Runtime spoke | `ACTIVE_SPOKE_RUNTIME` | active |
| `cloudbank-quantum-en` | Frontend / analyst workstation spoke | `ACTIVE_SPOKE_FRONTEND` | active_with_doc_drift |
| `qgia-knowledge-library` | Knowledge corpus spoke | `ACTIVE_SPOKE_KNOWLEDGE_CORPUS` | active |
| `qgia-knowledge-spine` | Knowledge spine spoke | `ACTIVE_SPOKE_KNOWLEDGE_SPINE` | active |
| `zip_wizard` | Tooling-adjacent engine | `ACTIVE_TOOLING_ADJACENT` | active_partial_constellation_receipt |
| `DuelSim_v2.0` | Satellite | `ACTIVE_SATELLITE` | active |
| `CanonRec` | Satellite | `ACTIVE_SATELLITE_UNDERDOCUMENTED` | active |
| `aurora-cloudbank-symbolic1` | Archive lane | `ARCHIVE_APPROVED` | pending_archive |

## Immediate actions
1. Archive `aurora-cloudbank-symbolic1`.
2. Update `cloudbank-quantum-en` root README so it matches the current `QUANTUM-VAULT` role.
3. Add a repo-local node receipt for `zip_wizard` if it is intended to remain part of the constellation surface.
4. Add a proper root identity document for `CanonRec`.
5. Keep portfolio truth in the control-plane repo and do not let naming drift substitute for declared role again.

## Canon rule
- **Portfolio truth** lives in `Aurora_ORIONCORE_Directory_Main`.
- **Platform truth** lives in `aurora-cloudbank-symbolic`.
- **Runtime truth** lives in `AuroraOS`.
- **Knowledge truth** lives in the QGIA spoke pair.
- Satellites and tooling must be labeled as such.
- Naming alone is never enough to establish canon.
