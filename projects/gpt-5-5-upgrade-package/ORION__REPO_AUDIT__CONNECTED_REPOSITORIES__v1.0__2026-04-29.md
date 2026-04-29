# Connected Repository Audit — GPT-5.5 Aurora/ORION Upgrade

**Document ID:** `ORION__REPO_AUDIT__CONNECTED_REPOSITORIES__v1.0__2026-04-29`  
**Version:** v1.0  
**Date:** 2026-04-29  
**Status:** Review draft  
**Scope:** GitHub repositories visible through the connected GitHub tool

## Executive Finding

The repository set already contains the beginning of a coherent Aurora Constellation:

- `aurora-cloudbank-symbolic` is the technical and symbolic hub.
- `Aurora_ORIONCORE_Directory_Main` is the workspace control plane.
- `AuroraOS` is the runtime spoke.
- `qgia-knowledge-spine` and `qgia-knowledge-library` form a closed-loop knowledge pair.
- `zip_wizard` is a strong candidate for archive intake and recovery tooling, but needs constellation registration before it is treated as an active Aurora node.
- `CanonRec` and `DuelSim_v2.0` are registered nested repositories, but need lightweight discovery docs before reliable integration.

The right GPT-5.5 upgrade move is to stage a control-plane package first, then promote targeted implementation tickets into the correct repositories.

## Repository Map

| Repository | Current role | Upgrade implication | Priority |
|---|---|---|---|
| `AUo959/Aurora_ORIONCORE_Directory_Main` | Workspace control plane | Home for upgrade package, review docs, manifests, and adoption plan | P0 |
| `AUo959/aurora-cloudbank-symbolic` | Constellation hub / production platform | Canonical technical contract source for memory, ethics, L1/L2/L3 layering, and constellation health | P0 |
| `AUo959/AuroraOS` | Runtime spoke | Needs smoke test and runtime-charter binding | P1 |
| `AUo959/qgia-knowledge-spine` | Methodology backbone | Source for forecasting, priors, calibration, and resolution-policy contracts | P1 |
| `AUo959/qgia-knowledge-library` | Domain corpus | Source for evidence and outcome ledgers | P1 |
| `AUo959/zip_wizard` | Archive management application | Candidate for THREADCORE archive/export recovery surface; needs constellation registration | P1 |
| `AUo959/CanonRec` | Registered nested canon reconciliation repo | Needs README / interface discovery | P2 |
| `AUo959/DuelSim_v2.0` | Registered nested simulation repo | Needs scenario-validator interface map | P2 |
| `AUo959/cloudbank-quantum-en` | Spark/template-style app | Peripheral until scope is clarified | P3 |
| `AUo959/aurora-cloudbank-symbolic1` | ChatGPT ProBot fork/template | Peripheral; likely legacy or experimental | P3 |

## Evidence Notes

### `Aurora_ORIONCORE_Directory_Main`

The root repository describes itself as the workspace control plane and explicitly says it tracks workspace docs, manifests, policies, reports, and tooling without replacing active nested Git repositories. It also defines logical zones such as `docs`, `catalog`, `tools`, `reports`, `repos`, `archives`, and `_staging`.

**Upgrade conclusion:** this is the safest repository for the package spine. Do not hand-edit generated manifests. Do add human-readable package documents under `projects/gpt-5-5-upgrade-package/`.

### `aurora-cloudbank-symbolic`

This is the central hub for the Aurora CloudBank Symbolic platform. It includes quantum memory, drift detection, ethics and safety, observability, multi-model AI, and the constellation hub manifest. Its `.aurora/constellation.json` identifies it as `CONSTELLATION-PRIME`, publishing core contracts such as `forecast-request`, `forecast-result`, `constellation-event`, `knowledge-index`, and `constellation-health`.

**Upgrade conclusion:** use this repo as the canonical technical contract source, not as the first staging location for the upgrade package.

### `AuroraOS`

The runtime manifest identifies `AuroraOS` as `AURORA-RUNTIME`, a TypeScript/Mastra spoke for MCP server, Slack integration, Inngest workflows, and constellation tool gateway. The current `package.json` contains a placeholder failing test command.

**Upgrade conclusion:** add a minimal smoke test and bind the runtime charter to this repo in a follow-up PR.

### QGIA repositories

The QGIA spine and library are already paired through constellation manifests and complementary closed-loop artifacts:

- spine publishes forecast ledger, prior table, calibration report, and resolution policy;
- library publishes evidence records and outcome records;
- both consume constellation events and health signals.

**Upgrade conclusion:** this pair is the best existing model for the kind of accountable closed-loop pattern Aurora/ORION should adopt more broadly.

### `zip_wizard`

ZIP Wizard has strong archive management, file exploration, comparison, security scanning, audit, and analytics features. It is technically relevant to THREADCORE exports and recovery, but it does not appear to be registered as a constellation node yet.

**Upgrade conclusion:** create `.aurora/constellation.json` for `ZIPWIZ-ENGINE` as follow-up work before treating it as part of the active constellation.

### `CanonRec` and `DuelSim_v2.0`

Both are registered in the workspace repo as active nested repos, but initial direct file discovery did not expose obvious README or manifest entry points through the connector.

**Upgrade conclusion:** do a repo-local discovery pass and add minimal README/interface maps before wiring them into the upgrade package.

## Recommended Package Adoption Path

1. Stage the package in `Aurora_ORIONCORE_Directory_Main`.
2. Review and approve the upgrade package documents.
3. Open implementation issues in the target repos.
4. Add smoke tests and manifests before deeper code integration.
5. Convert Picard_Delta_3 and THREADCORE rules into validators only after the document spine is accepted.

## Risk Register

| Risk | Why it matters | Mitigation |
|---|---|---|
| Layer bleed | Aurora/ORION uses L1/L2/L3 semantics that can drift in docs and code | Enforce runtime charter and canon registry status fields |
| Symbolic overreach | Rich symbolic language can hide missing implementation | Require every protocol to map to a file, test, or issue |
| Repo sprawl | Multiple similar repos can create false continuity | Use control-plane registry first, then repo-specific PRs |
| Generated manifest damage | Root repo warns not to hand-edit generated manifests | Keep package docs under project path until tools regenerate manifests |
| Placeholder tests | AuroraOS currently has placeholder test script | Add minimal smoke test before claiming runtime health |

## Immediate Decisions

- Treat `Aurora_ORIONCORE_Directory_Main` as the package home.
- Treat `aurora-cloudbank-symbolic` as the canonical hub source.
- Treat `AuroraOS`, QGIA, ZIPWIZ, CanonRec, and DuelSim as follow-up implementation surfaces.
- Do not merge this package as final canon until review confirms naming, layer semantics, and repository boundaries.

---

Built for consistency, clarity, and care.
