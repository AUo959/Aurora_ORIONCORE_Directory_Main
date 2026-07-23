# L2 Named-Character Salvage Audit — 2026-07-21

**Scope:** filesystem-wide sweep (5,711 files across every repo, projects/, archives/,
and note dumps) for L2 named characters with defined GUMAS character profiles, diffed
against the ~47-record CanonRec L2 character roster.
**Finding in one line:** three genuinely new, well-defined L2 characters exist only in the
archives — each filling a real faction-leadership gap — plus a "Vos/Voss" surname cluster
that needs disambiguation and alias enrichment.

## Method

- Roster built from all CanonRec L2 entity names + aliases (191 name strings, 286 tokens)
  and capsule directory slugs.
- Extraction targeted the distinctive GUMAS character-profile block
  (`Name:` + `Role:` + `Allegiance:` within a few lines) rather than free-text title
  matching, which the roster-closure audit showed produces heavy false positives.
- Sources swept: structured registries, the World Bible, the runtime packet, the raw
  archive corpus (`Complete Archive 4_19`, ZIP_Archives, snapshot exports), and the
  `projects/*/Note*.txt` dumps the owner flagged.

**Note dumps:** the three `Note *.txt` files carry zero GUMAS character content — unrelated
material. No structured characters anywhere in the notes.

## Findings

### A. Three new characters (genuine gaps, full profiles)

Each has a complete profile block (Role, Allegiance, Traits, Reputation, Relationships,
Recent Actions, Decision Style) and fills a leadership slot no existing record occupies:

| Candidate | Role | Faction slot (currently empty) | Certainty read |
|---|---|---|---|
| **Director Eriana Vos** | Intelligence Chief of the PMC Syndicate | PMC has a CEO (Vailen Rix) but no intel chief | STAGING-ready |
| **Governor Selia Trask** | Political Leader of the Separatist Confederation | Separatists have a military commander (Rhaegon Torr-Kai) but no political head | STAGING-ready |
| **Admiral Haden Korr** | Fleet Admiral, Union Navy | Union Navy has no named fleet admiral | **UNCONFIRMED** — see note |

Corroboration beyond the profile blocks: Eriana Vos and Selia Trask both appear as actors
in a simulation log (the "Separatist Diplomatic Summit – Outer Fringe" compressed entry),
which raises them above mere character-sheet drafts.

**Haden Korr caveat:** his profile block appears inside a passage *demonstrating on-demand
character generation* — "Characters are generated when needed, rather than stored
permanently … without me needing to store excessive historical data." He reads as an
illustrative example of the generation mechanic, not necessarily a fixed canon actor.
Recommend **UNCONFIRMED** unless the owner affirms him as standing canon.

### B. Vos / Voss surname cluster — disambiguation needed

Four distinct characters carry confusable surnames; two are drift aliases of existing canon:

| Draft name | Resolves to | Status |
|---|---|---|
| **Lyra Voss** | `lyra_voss` (Judicator XO) | recorded, distinct |
| **Lirian Vos** | `lirian_vael_torin` (Grand Strategist, Covert Advisor to Zylox) | **drift alias** — same role; "Vos" is the early surname, "Vael-Torin" canonical |
| **Rhaegon Voss** | `rhaegon_torr_kai` (Separatist Supreme Commander) | **drift alias** — same office; "Voss" early, "Torr-Kai" canonical |
| **Eriana Vos** | *(no record — candidate A above)* | genuinely new |

"Vos"/"Voss" recurs throughout the recovered registries as a bare relationship reference
("Respected by Vos", "Intellectual Rival of Vos", "Political Confidant of Vos"). Given the
above, unqualified "Vos" in Union-command context = **Lirian Vael-Torin**. This is the same
class of drift the DRIFT-002-b resolution already handled for Lyra Voss/Veylan.

## Recommended rulings

1. **RULING-CHAR-NEW** — promote the three (or two) candidates as STAGING entity records:
   Eriana Vos → PMC Syndicate, Selia Trask → Separatist Confederation. Haden Korr's tier is
   the owner's call (UNCONFIRMED example vs STAGING canon).
2. **RULING-CHAR-ALIAS** — register drift aliases so references resolve: add "Lirian Vos"/
   "Vos" to `lirian_vael_torin`, and "Rhaegon Voss" to `rhaegon_torr_kai`.
3. **RULING-CHAR-CAPSULES** — whether new records also get CharForge capsules (engine-
   instantiable, as done for the Cross crew and Sentinel team).

No records created by this audit — owner rules first (canon discipline: never silently
promote recovered material).

## Source register

- Primary profiles: `archives/unzipped/ZIP_Archives/AU_Archive_330only/GUMAS_Extracted_Simulation_Modules.txt` and `Complete Archive 4_19` copies
- Recovered registries: `GUMAS_SIM_2.5/draft_worldbuilding/recovered/{galactic_union_character_registry,zylox_and_union_command_character_profiles}.md`
- Roster baseline: `GUMAS_SIM_2.5/CanonRec/canon/L2/entities/`
- Alias precedent: DRIFT-002-b (Lyra Voss/Veylan), `L2_GUMAS_RUNTIME_REFERENCE_PACKET_v0.4.md`
