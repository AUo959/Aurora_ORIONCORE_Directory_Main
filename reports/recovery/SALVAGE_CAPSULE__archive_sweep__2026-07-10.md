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
- **4 low-priority archive-only artifacts** catalogued for owner decision.
- **Bulk of the zip surface is noise** (repo snapshots + third-party deps).

## CORRECTION — content-based re-investigation (2026-07-10, later same day)

The findings above were derived by **filename** matching, which is unsound for a
completeness claim: it produces false negatives (content that landed under a
different name) and false positives (same name, different content). Redone by
**content**:

- Built a content-hash index of all live-repo files (8,222 files → 7,317 unique
  sha256), excluding `archives/`, `.git`, and dependency trees.
- Hashed the unpacked archive code/spec tree (643 `.py/.json/.md/.yaml` files,
  excluding repo snapshots + deps + `__MACOSX`).
- **450 of 643 archive files have content that is byte-identically present
  nowhere in the live repos** — not the 5 the filename skim implied.

Breakdown of the 450: **294 JSON, 77 MD, 66 PY (21 unique module names), 13 YAML**.
Full inventory: `reports/recovery/data/archive_content_not_live__2026-07-10.tsv`;
module list: `reports/recovery/data/archive_py_modules_not_live__2026-07-10.txt`.

**Sampled content-fingerprint check** (distinctive class/def symbols vs CloudBank
`src/`): `loom_gitbridge_wiring.py` (`LoomEventRegistry`), `anchor_validator.py`
(`validate_anchor_integrity`), and `gumas_memory_core.py` (`MemoryItem`) all have
their distinctive top-level symbol **absent from CloudBank source** — i.e. genuine
un-landed code logic, not just renamed copies.

**Correction to the record:** the earlier "one genuine recovery (SNPM); archive
mostly explored; diminishing returns" conclusion was **wrong and premature**.
There is a substantial early-generation code/spec corpus (~21 distinct Python
modules — runtime loader, memory core, loom git-bridge, anchor validator, ZipWiz
optimizer/bridge, benchmark/model tooling — plus hundreds of JSON/MD) whose
content is not present in the live repos.

**Caveat (still needs per-item judgment):** "content not byte-identically live"
is an **upper bound** on unrecovered material. It includes (a) reformatted or
lightly-edited versions of content that *did* land, and (b) early-gen designs that
were deliberately superseded by CloudBank's current implementation. The genuine
*recoverable-value* count is smaller than 450 and requires a per-module
supersession assessment (does the current CloudBank implementation already cover
this behavior?). What the content pass establishes is only that **recovery is not
complete** and cannot be judged complete from filenames.

## Recommended next steps (revised)

1. Owner review of the SNPM staging note; promote via canon-reconciler if wanted.
2. **Systematic content-based triage** of the 450-file inventory, batched by
   cluster (start with the 21 Python modules — highest signal), each assessed for
   supersession against current CloudBank/CanonRec by symbol/behavior, not name.
   Queued as `archive-content-triage-450`.
3. Treat the `.tsv` inventory as the working set; retire the filename-based
   "mostly explored" framing.
