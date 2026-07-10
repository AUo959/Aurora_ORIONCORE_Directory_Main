# Recovery Record — P7 Biological Pneumatic Engine Prototype

Date: 2026-07-10
Docket: `reports/analysis/salvage_docket__2026-06-12.md` § P7
Lane decision (owner, 2026-07-10): **root recovered-prototype archive**
Executed by: claude-code (Cowork session), owner-directed

## Provenance

| Artifact | Path | SHA-256 |
|---|---|---|
| Original docket evidence (deleted with iCloud copy 2026-07-04) | `~/Library/Mobile Documents/com~apple~CloudDocs/Downloads/biological_pneumatic_engine.py` | `20df62806321976e63b3c209750b51e67bb34413d4bfbf59b2dd72bab501fe33` |
| Frozen archive snapshot (this directory) | `archives/recovered_prototypes/biological_pneumatic_engine/biological_pneumatic_engine.py` | `20df62806321976e63b3c209750b51e67bb34413d4bfbf59b2dd72bab501fe33` (byte-identical to docket evidence) |
| Operative in-repo copy (live, post-fix) | `projects/Aurora_New_11_9/04_DEVELOPMENT/Python_Modules/biological_pneumatic_engine.py` | see "Post-recovery divergence" below |

The docket evidence path was deleted in the 2026-07-04 iCloud cleanup, but an
identical copy already existed in-repo under `Python_Modules/`. Hash match was
verified 2026-07-10 before any modification; this archive snapshot preserves
the pristine bytes.

## Disposition

- Archive lane selected. Not promoted to canon; not routed to CloudBank.
  CloudBank runtime-experiment routing remains available as a future decision
  and would start from the behavior inventory in this directory.
- The operative copy in `Python_Modules/` remains in place because
  `pdp_v2_mvp/core/pneumatic_engine.py` (`PneumaticEngineAdapter`) imports it
  as its preferred engine. Moving it would break the PDP v2 MVP.
- Two surgical fixes were applied to the operative copy and adapter after this
  snapshot was frozen (see below). The archive copy is intentionally left
  unfixed.

## Post-recovery divergence (operative copy)

Applied 2026-07-10, same commit as this record:

1. `Python_Modules/biological_pneumatic_engine.py`: removed dead
   `from scipy import signal` import (never used). Engine now loads with
   numpy alone, so the adapter's `use_scipy=True` path can select the
   external engine in environments without scipy.
2. `pdp_v2_mvp/core/pneumatic_engine.py`: narrowed the adapter's blanket
   `except Exception` on external-engine import to `except ImportError` so
   real defects in the external engine surface instead of silently degrading
   to fallback mode.

Post-fix hash of the operative copy is recorded in the commit that introduced
this record (`git log --follow` on the operative path is authoritative).

## Companion documents

- `BEHAVIOR_INVENTORY__2026-07-10.md` — component-level behavior inventory
  (docket P7 next-gate requirement), required precursor for any future code
  migration out of this archive lane.
