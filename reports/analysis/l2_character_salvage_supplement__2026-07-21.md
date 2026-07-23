# L2 Character Salvage — Supplement (Prose / Mixed-Source Tail) — 2026-07-21

**Trigger:** owner asked "what about the pirate queen" after the main salvage pass.
**Two findings:** (1) the Pirate Queen *is* already canon; (2) the question correctly exposes
a real gap in the main pass's method — a tail of characters described in prose / relationship
fields, not in `Name:/Role:/Allegiance:` blocks, concentrated in one mixed-content knowledge core.

## 1. The Pirate Queen — already recorded

**Theryn Kael'Vakar** = `theryn_kaelvakar` (CANON): "Pirate Queen … Confederation Leader and
Commanding Officer of the Khar'Thyrix." She commands `vessel_oc_001` ("The Star-Eater"). The
main pass caught her because she carries a structured entry in the runtime packet. No gap.

## 2. Method gap the question exposed

The main pass keyed on the GUMAS character-profile block (Name + Role + Allegiance). That
misses characters who appear only as:
- **relationship-prose references** inside *other* characters' records ("open rivalry with
  Warlord Jaxx Tyren", "mentored by exiled Grand Duke Talyx Velkonn"), and
- **entries in mixed-content files** the block-scan skipped to avoid noise.

The main offender is `projects/GUI_Cloudhub/…/Aurora_Master_Knowledge_Core_v2.2.6b_CLEANED.md`
— a 2025-04-09 export that interleaves genuine GUMAS characters with real-world news snippets
(Gavin Newsom, Keir Starmer, Rachel Reeves) and meta/design chatter. The block-scan correctly
avoided the noise but lost the real characters with it.

## 3. Candidates surfaced (v2.2.6b core, not in roster)

After filtering real-world names, common-noun false positives, and already-recorded/variant
spellings, ~14 plausible new GUMAS characters remain:

| Candidate | Title | Faction / role signal |
|---|---|---|
| Jaxx Tyren | Warlord / Commander | Outer Colonies warlord |
| Talyx Velkonn | (exiled) Grand Duke | Velar Imperial restorationist / mentor figure |
| Orin Vex | Vice Chancellor | Union political leadership |
| Thalen Rynn | Councillor | Union council |
| Vaxtan Rhel | General | military |
| Aria Lenix | Commander | military |
| Deyan Orros | Captain | vessel command |
| Joran Malik | Commander | military |
| Karn Vos | Admiral | Union navy (another "Vos" — disambiguation needed) |
| Mara Velthis | Captain | vessel command |
| Saela Corven | Admiral | Union navy |
| Sarina Vael | Director | agency/intel |
| Selene Rho | Admiral | Union navy (distinct from Selene Arcturus) |
| Iskar Veyr | Commander | **framed generatively** ("we'll introduce a noble-born commander…") — likely example, not standing canon |

## 4. Continuity caveat — needs an owner ruling before promotion

This is **not** a clean promote. Three unknowns are genuinely the owner's call:

1. **Generation/continuity.** v2.2.6b is a **2025-04 export**, predating the 2026 canon
   promotions. It also carries **alternate leadership names** — "High Chancellor Valcor",
   "High Chancellor Zylox **Verrin**", "Chancellor Zylox **Kryon**" — that read as an early,
   fuller (or divergent) characterization of Chancellor Zylox. Whether the v2.2.6b roster is
   *current canon*, an *early generation to mine selectively*, or a *superseded alternate* is
   undetermined. Records should not be minted until that's settled.
2. **Zylox variants.** "Zylox Verrin" / "Zylox Kryon" almost certainly = canonical
   `zylox_rhaegos` (Merchant-Chancellor characterization). Alias enrichment, not new records.
3. **Generative examples.** At least Iskar Veyr is introduced as a to-be-generated character
   ("we'll introduce…"), the same class as Haden Korr — UNCONFIRMED at most.

## 5. Recommendation

Run a dedicated supplementary pass **after an owner ruling on the v2.2.6b generation's
status**, mirroring the main pass: STAGING for clearly-established GUMAS characters,
UNCONFIRMED for generative ones, alias enrichment for Zylox variants. No records created by
this supplement — flagged for decision (canon discipline: never silently promote recovered
material, especially across an uncertain continuity boundary).

## Source register

- `projects/GUI_Cloudhub/T1_Symbolic_Continuum_Export_20250409_FULLSCAN_LOCKED/Aurora_Master_Knowledge_Core_v2.2.6b_CLEANED.md`
- Roster baseline + Pirate Queen record: `GUMAS_SIM_2.5/CanonRec/canon/L2/entities/theryn_kaelvakar/`
- Main pass: `reports/analysis/l2_character_salvage_audit__2026-07-21.md`
