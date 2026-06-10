# Recovered Canon — March 2026 Rescue Lineage Extraction

- **Recovered:** 2026-06-10, owner-approved narrative-cargo recovery session
- **Source:** `aurora-cloudbank-symbolic-main` branch
  `codex/cloudbank-reconstruct-aurora-state-2026-03-26` (lineage tip,
  commit `7a5e95a9`), preserved before the March main reset and never
  re-landed upstream.
- **Security:** entire lineage gitleaks-scanned 2026-06-10 — no leaks
  (two benign test placeholders; see
  `reports/analysis/unlanded_work_audit__2026-06-10.md`).
- **Method:** file-level extraction (no history merge), per the
  control-plane recovery rule in `docs/CONTROL_PLANE_PROVENANCE.md`.
- **Status:** recovered, NOT yet canon. Promotion to CanonRec / canonical
  surfaces still requires owner review through the aurora-canon-reconciler
  path. This directory is the durable review surface.

## Why this matters

The L1 Entity Ledger (`reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md`)
cites canonical sources (e.g. `ORION.ENT.REGISTRY.0001`-class material) that
did not resolve to any tracked path in this workspace. Several of those
sources are in this directory — most importantly the canonical staff
registry. This extraction closes the "canon citations point at sealed boxes"
gap identified in the 2026-06 narrative-layer review.

## Inventory

### L1 canon sources

| File | What it is |
|---|---|
| `ORION_STATION_CANONICAL_STAFF_REGISTRY.json` | Canonical staff & bridge-node registry, manifest v2.4.1 — command structure, clearances, all operational/command/agent seats. A primary L1 source cited by the entity ledger. |
| `ORION_STATION_STAFF_REGISTRY_INTEGRATION_COMPLETE.md` | Integration record for the registry (named in the ledger's legacy-drift sources). |
| `INTEGRATED_GPRS_CREW_STAFF_L3_AGENTS_COMPREHENSIVE_ANALYSIS.md` | Cross-layer crew/staff/L3-agent analysis. |
| `ORION_CORE_VALIDATION_REPORT.md` | ORION core validation record. |
| `ORION_STATION_DEPLOYMENT_READY.md` | Station deployment-readiness guide. |

### Canon-as-code (the practical promotion path)

| File | What it is |
|---|---|
| `canonical_validation.yaml` | Machine-readable canon contract: anchor seed `EOS_SEED_ORION`, continuity seal, `Picard_Delta_3` ethics protocol, THREADCORE `v3.5.1_macroready`, staff-registry mapping, drift lock. Input format for validation tooling. |
| `setup_canonical_validation.py` | Installer for the canonical validation system (git hooks, validation scripts, directories, usage docs). |
| `CANONICAL_VALIDATION_USAGE.md` / `CANONICAL_VALIDATION_SYSTEM_COMPLETE.md` / `CANONICAL_INTEGRATION_COMPLETE.md` / `CANONICAL_LAYER_ARCHITECTURE_INTEGRATION_COMPLETE.md` | Usage + completion records for the canonical validation system. |
| `THREADCORE_UPGRADED_PAYLOAD_v3.5.1_loom_unification.json` | THREADCORE capsule (Symbolic Constellation Loom + Reflection Module), version-matched to the validation contract. Validate with the `threadcore-governor` skill. Original filename carried a glyph prefix; renamed for path safety. |
| `symbolic_core_symbolicvector.schema.json` / `symbolic_core_upload_response.schema.json` | Symbolic core JSON schemas. |
| `symbolic_integration_manifest.json` | Symbolic integration manifest. |

### Collaboration chamber (crew interaction surface)

| File | What it is |
|---|---|
| `AURORA_COLLABORATION_CHAMBER_GUIDE.md` | Operating guide for the mesh collaboration chamber. |
| `AURORA_ENHANCED_COLLABORATION_CHAMBER_V2_GUIDE.md` | V2 chamber guide. |
| `MESH_AGENT_INTEGRATION_COMPLETE.md` | Mesh agent integration record. |
| `PR77_BASELINE.md` | Glyphcard baseline. |

## Related recoveries (same session)

- CloudBank PR #979 — narrative validation engine phase one (revived from
  closed PR #640).
- CloudBank PR #980 — V1 mesh contract tests + `/health` factory route +
  anti-flourish Thorne persona memory.
- `intake/recovered_mesh_runtime_2026-06-10/` (untracked, local-only) —
  mesh runtime DB and conversation transcripts from the rescue snapshot
  (`rescue/cloudbank-dirty-workingcopy-2026-03-25`). Kept out of Git
  pending owner privacy review; includes `private_captain_alex.jsonl`.

## Not extracted (verified already landed or superseded)

- Aurora command grammar module — byte-identical on CloudBank main.
- Aurora Fusion composition layer + memory optimizer — byte-identical on main.
- `src/mesh/live_agents.py` lineage delta — superseded by main's newer
  prompt-safety hardening.
- Pre-reset infrastructure clutter (old workflows, `.security/*` configs,
  status reports) — deliberately removed in the reset; not re-imported.
