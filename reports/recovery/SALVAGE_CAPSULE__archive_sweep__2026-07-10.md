# Salvage Capsule — Archive Sweep 2026-07-10

**Scope:** a deeper pass beyond the June salvage docket (P1–P7) and the recovery
indexer's top-10 (N1–N9), targeting material the indexer never inspected — the
**605 ZIP archives** and early-generation project bundles. Control-plane
inventory only; no canon promotion here.

## Method

The recovery indexer scans loose/intake/staged files by extension and does **not
unpack zips**. This sweep classified the zip surface and sampled the
early-generation bundles (GUMAS_SIM_2.0, Aurora v2.2.6b, GUMAS+AUR Dev File
Archives), then checked each distinctive artifact against the live repos (root,
CloudBank, CanonRec) — the "check nested repos before treating as unrecovered"
rule that resolved nearly every prior find.

## Zip surface — mostly noise

| Class | Examples | Disposition |
|---|---|---|
| Full CloudBank repo snapshots | `aurora-cloudbank-symbolic-main*.zip` (×many), `bundles/…main.zip` | Already on GitHub — **not salvage** |
| Third-party dependencies | `site-packages.zip` (2168 files), `openai-cookbook-main.zip` | **Not salvage** |
| Early-gen project bundles | `GUMAS_SIM_2.0.zip`, `Aurora_v2.2.6b_*.zip`, `GUMAS+AUR Dev File Archive *.zip` | **Sampled below** |

## Early-gen bundle contents — landed vs archive-only

Sampled the v2.2.6b / GUMAS_SIM_2.0 bundles. Most worldbuilding is **already
canonized**; a short list is genuinely archive-only.

**Already landed (superseded — no action):**

- ORION Operational Library / `L1_SYSTEMS_BIBLE` → `projects/GUMAS_SIM_2.0/…` and
  CanonRec `canon/L1/station/operational_library_v2_2/`.
- Galactic-union worldbuilding (character roster, mechanics-and-models, sim math
  framework, timeline, organizations, 41 characters) → CanonRec `canon/L2/`.
- `gumas_recovery_wizard.py` → this is the docket **P6** artifact (unsafe archive
  extraction; backup_only, blocked on security review).

**Genuinely unrecovered (archive-only, in no live repo):**

| Artifact | Type | Disposition (2026-07-10) |
|---|---|---|
| `SNPM_Scalable_Narrative_Model` | narrative-sim mechanic | 🟢 **RECOVERED** → CanonRec `canon/L2/mechanics/SNPM_Scalable_Narrative_Probability_Model__v1.0.json` (byte-identical `4c43699b…`) **STAGED** with reconciliation note. Owner promotes via canon-reconciler. Complements the narrative-engine spec. |
| `galactic_union_core_ships_module.py` | early-gen code module | 🔵 archive-only; likely superseded by CanonRec `l2_ship_dossiers__recovered_textAu.json`. Verify before any recovery; low priority. |
| `galactic_union_characters_master_list.json` | character roster | 🟢 superseded — CanonRec has the canonical roster + 41 characters. No action. |
| `Meta_Reflection_Layer_Module_v1.md` | early-gen spec | 🔵 archive-only; check against CloudBank narrative/reflection surfaces before recovery; low priority. |
| `Aurora_Unified_Process_Architecture_Principle.md` | architecture principle | 🔵 archive-only; candidate for root `docs/` if not superseded by the narrative-promotion ADR. Low priority. |
| `STW_Patch_Spec_v2.2.6.json` | patch spec | 🔵 archive-only, version-specific (v2.2.6); likely historical. Low priority. |

## Outcome

- **1 genuine recovery:** SNPM, staged into CanonRec L2 (its own nested-repo
  commit; push separately). It is a distinct galaxy-scale narrative-plausibility
  mechanic, verified absent from all landed L2 canon.
- **4 low-priority archive-only artifacts** catalogued for owner decision; each
  needs a "check nested repos first" pass before any recovery, and all are
  early-generation (v2.2.6b) and plausibly superseded.
- **Bulk of the zip surface is noise** (repo snapshots + third-party deps).

## Recommended next steps

1. Owner review of the SNPM staging note; promote via canon-reconciler if wanted.
2. Optional: quick supersession check on the 4 archive-only artifacts (ships
   module, meta-reflection, unified-process principle, STW patch) — recover only
   any that are both non-duplicate and still relevant.
3. The remaining early-gen bundles are unlikely to hold much beyond duplicates;
   further digging has diminishing returns given the observed hit rate.
