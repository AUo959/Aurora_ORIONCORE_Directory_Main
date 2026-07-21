# Roster Closure Audit — 2026-07-21

**Trigger:** the union-domain fabric linter flagged Grand Marshal Aric Thal as CANON with no
entity record (C4 roster closure). Owner directed a full sweep for similar issues.
**Result:** two gap classes found, both closed. **Canon now has zero unrecorded named actors.**

## Method

Deterministic sweep across all of `canon/` (L1 + L2 + L3, all `.md`/`.json`/`.jsonl`/`.yaml`):

1. **Roster built** from every L2 entity record (name + aliases, tokenized) *plus* all 41
   L1 character files (`ORION.ENTITY.NNNN__slug.md`).
2. **Extraction patterns:** (a) title-prefixed names — Grand/Chief/Lord Marshal, Chancellor,
   Commander, General, Admiral, Director, Captain, Senator, Justice, Magistrate;
   (b) bolded roster-bullet names (`- **Name Name** —`), which is how mission rosters are written.
3. **Stopword filter** for title-compound role strings ("Chief Science Officer", "Charter
   Articles", "Starship Classes") that pattern-match as names but are not people.
4. Diff extraction against roster; classify each residual.

## Findings

### Class 1 — Charter incumbent (1)

| Actor | Canon basis | Status |
|---|---|---|
| **Aric Thal** | Marshal Charter Article V (**CANON**, owner-approved 2026-07-20) names him Grand Marshal of Sentinel High Command; also referenced in `org_sentinel_high_command.json` and `char_kade` knowledge | **No record — CLOSED** |

Notable: Aric Thal holds a **dual-role career**, both canon-established — Commander /
Sentinel-Praetor and mission lead of Operation Silent Dagger (LEDGER-MISSIONS-0001), later
Grand Marshal of SHC (Charter Art. V). The Charter's deterministic selection rule chose him
*because* of the Silent Dagger record, so the two roles corroborate rather than conflict.

### Class 2 — Operation Silent Dagger team (4)

`LEDGER-MISSIONS-0001` (canon ledger, SRC-0005 primary excerpt) names a full five-operative
Sentinel team. None had records:

| Actor | Variant | Role in mission | Status |
|---|---|---|---|
| Lior Serath | Sentinel-Phantom | Infiltrator; compromised Blackreach security grid | CLOSED |
| Veyna Koris | Sentinel-Striker | Breach + close-quarters eliminations | CLOSED |
| Kael Voss | Sentinel-Stalker | Comms monitoring, hacking/entry, AI core shutdown | CLOSED |
| Darek Voss | Sentinel-Vanguard | Shockwave weapons, rear-guard — **KIA** | CLOSED |

### False positives (excluded, no action)

Role strings and document titles that match name patterns: "Chief Science/Medical [Officer]",
"Charter Articles", "Starship Classes/Capabilities", "Field Equipment", "Simulation
Structure", "Front Door" (doc title), "Zylox's" (possessive — `zylox_rhaegos` exists).
The C4 linter check now carries this stopword list.

## Records created (5, CANON, `canon/L2/entities/characters/`)

`char_aric_thal`, `char_lior_serath`, `char_veyna_koris`, `char_kael_voss`, `char_darek_voss`.

Discipline applied — recording existing canon, not inventing:

- Every field traces to the ledger, the Charter, or SRC-0005. Unestablished details
  (full histories, ages, origins, ranks beyond those stated) explicitly marked absent.
- **C2 terminal status honored:** Darek Voss recorded `status: deceased` (KIA), the mission's
  single fatality — no canonical revival mechanism exists.
- **Ambiguity flagged, not resolved:** Kael Voss / Darek Voss share a surname; the records
  note this with an explicit "relationship NOT established — do not infer kinship." Kael Voss
  is also disambiguated from Kael Durn (GU Supreme Military Commander).

## Verification

- Post-closure sweep: **0 true gaps** (sole residual is the "Front Door" document title).
- `tools/fabric_invariants_check.py --domain union`: **0 violations** across 78 entities
  (was 1 C4 violation pre-closure). `--domain velar`: 0 violations, regression clean.
- Remaining union-domain C1 gaps (17) are the legacy capsules still lacking `location_binding`
  — tracked separately as `capsule-location-binding-rebuild`.

## Follow-on candidates (not actioned)

1. **Capsules for the Sentinel team** — the five new records are entity JSONs only. Capsule
   builds would make them engine-instantiable (as done for the Cross crew).
2. **Sentinel variant cross-link** — the five carry variant strings (Praetor/Phantom/Striker/
   Stalker/Vanguard) that could link to the canonical seven-variant taxonomy as equipment records.
3. **L1 sweep depth** — this audit verified L1 names resolve to `ORION.ENTITY` files; it did
   not audit L1 records for internal field completeness.
