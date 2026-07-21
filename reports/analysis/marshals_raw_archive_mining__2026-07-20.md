# Marshals Raw-Archive Mining Pass — 2026-07-20

Closes the open item flagged in `l2_canon_promotion__2026-06-13.md` ("Raw 2025
archive corpus … hold further Marshals/galaxy material not yet extracted") for
the **Marshals/Sentinels domain specifically**. Companion to
`union_marshals_dossier__2026-07-20.md`.

## Method

- Sources: `archives/session_archives/Au_Archive_323_41/` — `conversations.json`
  (Mar-26-2025, 3 identical copies, one sha256), `chat.zip`, `conversations (1).zip`,
  and the full ChatGPT export zip dated 2025-04-01 (superset: 87 conversations).
- Deduped by conversation_id preferring latest update_time → **87 unique conversations**.
- Keyword sweep (`marshal|marshall|sentinel|ranger`, case-insensitive) over all
  message parts → 6 conversations with hits; 290 matching messages extracted.
- Diffed against existing canon (`canon/L2/marshals_sentinels/`, entities,
  factions, sim capture) to isolate **new** material.

| Conversation | Date | Matching msgs | Verdict |
|---|---|---|---|
| MAS - Glactic Union | 2025-03-12 | 222 | **Origin thread — new material found** |
| Dev_GUMAS | 2025-03-24 | 25 | Mostly already-promoted roster/memory content |
| Team Dev_GUMAS | 2025-03-27 | 41 | Ship registry + espionage framework (partly new) |
| Galactic Union Summary | 2025-03-30 | 2 | Duplicative |
| Exporting Archived Data | 2025-04-01 | 2 | Meta, no lore |
| Quill.org Overview | 2024-11-23 | 10 | False positive (Thurgood Marshall Middle School) |

## New findings (staged, NOT promoted)

Curated verbatim excerpts:
`_staging/marshals_archive_mining__2026-07-20/marshals_excerpts_curated.md`

1. **Marshals governance model (fills ledger Open Question #1 and grounds
   EXTRAP-0002):** Senate sets budget and confirms the Chief Marshal; Chief
   Marshal **reports to the Judicial Council, not the Chancellor**; Chancellor
   appoints the Chief Marshal with Senate approval and **cannot issue orders in
   criminal investigations**; chain of command separate from military and
   planetary police.
2. **Jurisdiction & mandate:** cross-planetary/sector crimes (organized crime,
   political crimes, fugitives); authority to **override local police**;
   **diplomatic immunity** across borders; weak presence in Outer Colonies.
3. **In-world origin of the Sentinel program and Marshal Academy — the
   Zylox–Durn pact:** Zylox's offer to the Marshals' director included the
   ultra-high-tech **combat-shielded power suit** (→ Sentinel-Class Power
   Suit), an **academy on the capital planet** (→ Marshal Academy), expedited
   funding, and an anti-AI-overreach task force. Outcome: Marshals "now with
   combat power suits and greater authority."
4. **G.U.S. Judicator Prime specs:** Supercarrier-class flagship, crew 12,000,
   command ship for **Marshal-led strike forces**, hosts a full Sentinel-class
   strike unit — enriches the canon mobile asset that is Marshal-Captain Elias
   Drayen's ship assignment.
5. **Sentinel-Class Hunter Vessel** (top-secret covert-ops ship class) — NOT in
   the canon fleet CSVs; either a seventh class or an early name for the
   Phantom-Class Stealth Frigate. Needs reconciliation; also worsens the known
   "Sentinel-Class" suit-vs-ship taxonomy collision.
6. **Doctrine/espionage strings:** "Union Marshals vs Corporate Black Ops",
   "Sentinel-integrated covert units", role descriptor "internal security,
   counterterrorism".
7. **Velar disambiguation:** the Imperium's "Marshal-Council System" is the
   origin of the "Lord Marshal" title (Tal'Varen) — confirms it is unrelated to
   the Union Marshals.

## Drift / conflicts to resolve before any promotion

| Archive (Mar-2025) | Current canon (locked) | Resolution needed |
|---|---|---|
| "Galactic Marshals" (dominant name) | "Union Marshals" (canonical), alias Galactic Marshals | None — alias already registered |
| **Director** of the Galactic Marshals = **General Kael Durn** ("The Iron Sentinel") | Chief Marshal **Vael Saros** leads Union Marshals; Durn is Supreme Military Commander | Early draft superseded; keep as lineage note or retcon as Durn's prior posting |
| High Chancellor **Zylox Verrin** | Chancellor **Zylox Rhaegos** | Surname drift; canon (Rhaegos) prevails |
| Factions Varnak / Threxia / Mek'thor, GSB, CSD, Sheriff Garrisons, TSF | Not in promoted canon | Un-canonized worldbuilding; separate triage if wanted |
| Sentinel-Class Hunter Vessel | 6-class Marshal fleet (no Hunter) | Reconcile vs Phantom-Class frigate |

## Status & recommended next steps

- Mining of the raw archives for **Marshals content is complete**; nothing else
  marshal-relevant remains in the 87 conversations.
- Excerpts are **staged only** — per canon rules, nothing was promoted.
- Recommended: run **aurora-canon-reconciler** over the staged excerpts to
  decide (a) governance model promotion into the Union Marshals entity /
  Marshal Charter, (b) the Zylox–Durn pact as origin lore vs retcon, (c)
  Hunter Vessel disposition, (d) Judicator Prime spec enrichment.
