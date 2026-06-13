# L2 Raw-Archive Mining Pass — 2026-06-13

Completes the L2 promotion by mining the April-2025 session-archive zips (the
raw corpus flagged in `l2_canon_promotion__2026-06-13.md`).

## Method

Extracted the **structured** files (not the 19MB conversation dumps) from
`archives/session_archives/Au_Archive_*/` zips → /tmp scratch → deduped →
routed the unique galaxy artifacts.

## Promoted to canon (CanonRec `2dcb313`)

- **`canon/L2/timeline/`** — `GUMAS_Galactic_Timeline_Detailed_Enhanced.json`
  (v2.0): the galaxy's history in eras — Precursor Era (Orak-Thuun Ascendancy
  >10M yrs ago, Dyson swarms/ringworlds, megastructures in the **Hollow
  Expanse** — which is also a promoted L2 location), each event scored with
  cultural/technological impact metrics. Contextualizes `entities/locations/`.
- **`canon/L2/factions/`** — `GUMAS_Factions.json` (Galactic Union with
  substructures Union Intelligence / **Union Marshals** / Diplomatic Corps /
  **Sentinels**; AI Warlords; …) + the faction relationship web (HTML) +
  relationship diagram (PNG).

## Staged for MECH-GOV-001 (the headline find)

- **`GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/recovered_reference/memory_system__recovered_2025.py`**
  — the file shipped mislabeled as `Galactic_Union_Python.py` is actually the
  **original `memory_system.py`**: `MemoryItem` (content/type/owner/importance,
  timestamp), importance-based **decay** (half-life), **reinforcement** on
  recall, tag-relevance matching, and a `MemoryStore`. **This is the memory
  substrate MECH-GOV-001 ("Faction Decision Retrieval Model") was designed to
  run on** — factions remembering events with decay and recalling them to
  decide. The next task (implement MECH-GOV-001) builds on this, not from
  scratch.

## Documented, not promoted (raw source-of-record)

- `chat.html` (20MB) / `conversations.json` (19MB) in
  `archives/session_archives/Au_Archive_323_41/` — the raw ChatGPT exports the
  whole L2 corpus derives from. Retained as archival source-of-record; not
  routed into canon (raw mixed conversation, already distilled into the
  structured artifacts above and the recovered_textAu dossiers).
- `MAS - Glactic Union ships factions .pdf` (6.5MB) — ships/factions visual
  reference; the same data is in `canon/L2/marshals_sentinels/` CSV tables.
- Duplicate timeline/registry variants across archives — canonical copies kept.

## Status

L2 galactic canon is now comprehensively promoted (entities, world bible, map,
marshals/sentinels, operations, mechanics, primary sources, timeline,
factions). Remaining: the engine still does not implement memory-driven faction
decisions — **MECH-GOV-001 is the next task**, with the recovered memory_system
as its reference substrate.
