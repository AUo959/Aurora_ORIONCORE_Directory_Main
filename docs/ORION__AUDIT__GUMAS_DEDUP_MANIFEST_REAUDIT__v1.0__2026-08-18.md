# GUMAS Deduplication Manifest — Full Content-Hash Re-audit v1.0

**Date:** 2026-08-18
**Layer:** L2
**Status:** systemic preservation risk confirmed; 169 of 308 records unsound
**Severity:** high — the source manifest still recommends deleting all 308
**Scope:** every record in `projects/GUMAS_SIM_2.0/07_INDICES/Indices/REORGANIZATION_MANIFEST.json`
**Data:** `reports/analysis/gumas_dedup_reaudit__2026-08-18.csv`
**Source:** local forensic sweep. Full record: `GUMAS_RECOVERY_ADDENDUM_E` (cold storage / `recovery/`)
**Repository:** `AUo959/Aurora_ORIONCORE_Directory_Main`
**Frozen source:** `archives/recovered_prototypes/gumas_v2_tactical/`
**Downstream restoration:** `AUo959/aurora-cloudbank-symbolic` → `simulation/runtime/gumas_v2_restored/` (branch `agent/gumas-flash-rebellion-battle-baseline`)

## Executive finding

`GUMAS__RCA__TACTICAL_SOURCE_DEDUP_MISCLASSIFICATION__v1.0` established that the
2026-02-15 pass matched on basename and condemned three v2.0 package files. The
remaining 305 records were re-tested the same way.

**The defect is systemic. 169 of 308 records (54.9%) are wrong** — the named
canonical does not contain the condemned file's content.

| Disposition | Records | Archived bytes |
|---|---:|---:|
| **DO_NOT_DELETE** — content not preserved by the claimed canonical | **169** | **2,014,786** |
| SAFE — byte-identical to canonical (SHA-256 match) | 127 | — |
| SAFE — archived text fully contained in canonical | 7 | — |
| UNVERIFIED — archived file no longer locatable | 5 | — |

The manifest's own `space_savings_potential_bytes: 2,809,019` is therefore
**71.7% content deletion, not deduplication**.
`07_INDICES/Getting_Started/REORGANIZATION_SUMMARY.txt` still reads
*"Safe to delete ✓"* and *"Option 3: Delete all redundant files (recommended)."*

## Method

The manifest stores pre-reorganization paths, so direct path lookup fails on
every record. Resolution is by longest path-suffix match against a basename index
of the 623 files currently present, confirmed by hash. Four tests per record:

| Test | What it establishes |
|---|---|
| SHA-256 equality | genuine duplicate, or not |
| Size delta | direction and magnitude |
| Normalized-text containment (HTML tags stripped, JSON key-sorted, Markdown punctuation normalized) | whether content survives inside the canonical when bytes differ |
| ZIP member set comparison by `(filename, CRC-32)` | which members exist in the condemned bundle but not the canonical |

Containment matters: a `.md` and its `.html` render legitimately differ in bytes.
Testing content rather than bytes is what makes the 169 defensible — and it
cleared 7 records a byte comparison alone would have flagged.

## Failure modes

**Same name, different file (31 records).** Declared format-duplicates where both
files share an extension and differ in bytes.

| Condemned | Size | Claimed canonical | Size |
|---|---:|---|---:|
| `26_engine_1.4/engine.py` | 99,134 | `26_Engine_1.2/engine.py` | 54,786 |
| `26_engine_2.0/modules/gumas/scenarios.py` | 59,277 | `26_Engine_1.2/scenarios.py` | 18,821 |
| `ZIPWIZ__GUMAS_OPTIMAL_EXPORT_PACK__v1.5.0` | 126,974 | `…v1.3.1` | 64,720 |

**Cross-format claims never content-verified (59 records).** Normalized-text
comparison: 47 divergent, 6 genuinely contained, 4 with the canonical a strict
*subset* of the archived file, 2 PDFs not comparable. **Only 6 of 59 hold.**

**Inverted supersession (5 records)** — the smaller file was kept. The clearest:
`modules/gumas/__init__.py` (1,412 B) was condemned in favour of a canonical
`__init__.py` of **zero bytes**. That initializer exports the ten v2.0 subsystem
modules.

**Bundle claims that discard members (10 ZIP records).** Comparing members by
`(filename, CRC-32)`: `ORION_Perplexity_Space_Operational_Library__v2.0` is
missing 43 members from its canonical, `ZIPWIZ…v1.5.0` 30, the four
`ORION_CORE__WorkshopAndForgeModule` bundles 10–14 each.

## Risk

Assessed against the whole Aurora tree, including the two archive witnesses.

| Category | Count | Bytes |
|---|---:|---:|
| Condemned files with a byte-identical copy elsewhere in Aurora | 130 | — |
| **Condemned files surviving ONLY inside `GUMAS_SIM_2.0.zip` / `GUMAS_SIM_2.0 2.zip`** | **29** | **215,299** |
| **ZIP members existing nowhere else** | **68** across 8 bundles | — |

Deleting `_REDUNDANT_FILES_ARCHIVED/` today would not immediately destroy the 169
loose files, because the two witnesses still hold the pre-reorganization tree.
But 29 depend on those two archives alone, and the 68 ZIP members are already
irreversible. The v2.0 package files were in the first category — which is why
recovery was possible on 2026-08-12. That was luck, not design.

The 68 unrecoverable members have been extracted byte-exact with a SHA-256
manifest; the 8 source bundles were opened read-only and re-verified unchanged.

## Consequence

1. `REORGANIZATION_SUMMARY.txt` must not be acted on.
2. Any tool that matches on basename will reproduce this exact failure.
3. `01_OLDER_VERSIONS/` (120 records) is byte-level non-identical for 116 of them;
   whether an older version is worth keeping is a curation judgement, not a
   forensic one, and is left open.

Read the `duplicate_copies_in_project` column of the CSV as *loose-file* copies.
Container-resident copies (files inside uncondemned ZIPs) are counted separately
in the risk table above, not in that column.
