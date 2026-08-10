# Archive Content Triage — 2026-08-09

**Input:** `reports/recovery/data/archive_content_not_live__2026-07-10.tsv` — archive files
whose *content* (sha256) is absent from the live repos. Supersedes the earlier
filename-based sweep, which undercounted badly (found 5).

## Headline numbers

| Measure | Value |
|---|---|
| Rows in the dataset | 450 |
| **Distinct content blobs** | **214** |
| Rows that are the same content at another archive path | 236 |
| Still absent from live as of 2026-08-09 | **214 of 214** |
| Live files hashed to re-verify | 9,789 |

Two things worth stating plainly. First, "450 files" is really **214 unique items** —
more than half the dataset is the same blob sitting at multiple archive paths (`copy`,
`(1)`, ` 2` variants). Second, the dataset is a month old, so it was re-verified rather
than trusted: **nothing has landed since**, so all 214 are genuinely still unlive.

## Composition (distinct content)

| Type | Blobs | Size |
|---|---|---|
| `.json` | 133 | 294.7 MB |
| `.md` | 52 | 7.3 MB |
| `.py` | 21 | — |
| `.yaml` / `.yml` | 8 | — |

## Python modules (21) — classified by whether the capability exists live

Method: parse each module, extract defined symbols, and compare against the 14,350
symbols defined across the 1,682 live Python files.

| Verdict | Modules |
|---|---|
| **SUPERSEDED** (≥60% symbols live) | `ZIPWIZ_OptimizerCore.py` (100%), `loom_gitbridge_wiring.py` (100%), `zipwiz_gui_patch.py` (100%), `gumas_memory_core.py` (82%), `aurora_runtime_loader.py` (66%), `zipwiz_bridge.py` (61%) |
| **PARTIAL** (1–59%) | `loom_model_selector.py` (50%), `behavior_loader.py` (42%), `relay_handshake.py` (38%, **482 lines** — largest unique surface), `aurora_core (1).py` (30%), `aurora_vector_diff_offline 2.py` (25%), `character_behavior_modules.py` (25%) |
| **ABSENT** (0%) | `graft_header_cli_scaffolder.py`, `symbolic_integration_script.py`, `model_prep_offline 2.py`, `gumas_memory_maintenance.py`, `anchor_validator.py` — all small (21–46 lines) |
| **No symbols** (data/script) | `galactic_union_core_ships_module (1).py`, `aurora_auto_launch_beacon.py`, `benchmark_runner_v0_9_sim.py` |
| **Unparseable** | `generate_manifest.py` |

Symbol overlap is a proxy, not proof — a 100% match means the *names* exist live, not
that behaviour is identical. The SUPERSEDED set is safe to leave archived; the PARTIAL
set needs a behavioural read before anything is discarded.

## Headline finding: `galactic_union_core_ships_module` is L2 canon, not code

The module classified as "no symbols" because it is **data**: five detailed ship
profiles for the Galactic Union simulation. This is canon material sitting in an
archive.

| Profile | Class | Commanding officer | CO in canon? |
|---|---|---|---|
| G.U.S. Judicator Prime | Supercarrier-Class Flagship | **Fleet Admiral Saela Corven** | `char_saela_corven` ✅ |
| Union Vanguard Battleship | Vanguard-Class Battleship | **Captain Mara Velthis** | `char_mara_velthis` ✅ |
| G.U.S. Resolute Dawn | Diplomatic & Intelligence Flagship | **Envoy-Captain Deyan Orros** | `char_deyan_orros` ✅ |
| Sentinel Hunter Vessel | Covert Strike Ship (Top-Secret) | Decentralized AI command | n/a |
| AI Leviathan Dreadnought | AI-Warlord Leviathan Dreadnought | **WRATH-09 (Prime AI Core)** | ❌ absent |

Each profile carries traits, reputation modifiers, crew complement, weapons, defensive
systems, propulsion, embarked craft, cyberwarfare suite, recent actions, core directives
and adaptive-evolution behaviour.

**The characters were salvaged in earlier passes, but the ship↔officer linkage and the
specifications were not.** The archive also attests the *Siege of Nethari Expanse*,
which canon already records at `loc_nethari_expanse` — cross-referencing
`char_saela_corven`. So the material corroborates canon rather than contradicting it.

### One question that must go through the conflict scan, not an assumption

Canon sets `vessel_gu_001.commanding_officer_id = alric_tann` (a **Captain**). The
archive names **Fleet Admiral Saela Corven** as commanding the same vessel.

This is most likely *not* a contradiction: on a flagship, an embarked flag officer
commands the fleet while the ship's captain commands the vessel — both are true at
once. But "most likely" is not a reconciliation. Route it through
`aurora-canon-reconciler` and, if it holds, express it as two distinct fields
(`commanding_officer_id` vs an embarked-flag-officer binding) rather than overwriting
one with the other. **Nothing was changed in canon on this pass.**

`WRATH-09` is a genuinely new named referent with no canon record — a naming-gate item.

## Remaining surface (193 blobs, ~302 MB) — not yet examined

| Type | Blobs | Contain 5+ capitalised names absent from canon |
|---|---|---|
| `.json` | 133 | 59 |
| `.md` | 52 | 37 |
| `.yaml` | 6 | 1 |

That name heuristic is deliberately crude and will include false positives (chat
exports carry real-world names, tooling identifiers, and so on). It is a *sizing*
signal, not a finding: it says roughly half the remaining blobs are worth a real read.
The `.json` bulk is dominated by conversation exports, which is where the old-prose
sweep found genuine canon earlier today.

## Recommended next steps

1. **Land the ship profiles** — reconcile the five profiles into the vessel records
   (specs, embarked craft, directives), routing the Saela Corven / Alric Tann question
   through the conflict scan. Highest value-per-effort in the dataset.
2. **`WRATH-09`** — decide the record via the naming gate; it commands the AI-Warlord
   Leviathan Dreadnought, which is already canon as a vessel.
3. **Read the 37 flagged `.md` blobs** — smallest, densest, most likely to hold prose
   canon of the kind the old-prose sweep recovered.
4. **Then the 59 flagged `.json`** — largest effort; needs a content-aware extractor
   rather than a name grep.
5. **Leave the 6 SUPERSEDED Python modules archived**; give the 6 PARTIAL ones a
   behavioural read before any decision.

---

# Phase 2 — the 37 flagged `.md` blobs (completed 2026-08-09)

**Result: largely a negative finding, and a useful one.** The markdown tier is close to
exhausted for L2 canon. Effort should redirect to the `.json` tier.

## What the 37 actually are

| Class | Files | Assessment |
|---|---|---|
| ORION / ZIPWIZ infrastructure | 26 | THREADCORE, dispatch protocols, symbolic command indexes, install manifests, beacons, restore protocols. **L3/tooling — out of L2 scope.** |
| Research / philosophy | 23 | "Flow and Related Concepts in Philosophical Thought" (199 KB), quantum-symbolic framework notes. Not setting material. |
| GUMAS / world | 3 | The two large knowledge bundles plus a launch checklist. |

The name heuristic that flagged these was heavily false-positive, as warned: its top
"new names" included *Aaron Rodgers*, *Able Sisters*, *Ablative Armor* and *Access
Controls* — title-case phrases, not entities.

## The headline target, examined

`Aurora_GUMAS_Knowledge_Companion.md` (4.6 MB) was the single most promising blob: it
is cited by **zero** canon records, where its sibling `Aurora_GUMAS_Knowledge_Bundle.md`
is cited by 3.

It turned out to be a **bundle of 214 embedded documents** (165 real; 49 are macOS
`._` resource-fork stubs). Of the 165, the overwhelming majority are **L1 / Aurora Lab
infrastructure** — staff registries, boot context, onboarding modules, transfer
manifests, security diagnostics, module specs, continuity seals. L1 is out of scope.

Its genuinely L2 embedded documents are **sources already mined**:

| Embedded doc | Canon records citing it |
|---|---|
| `GUMAS_Extracted_Simulation_Modules.txt` | 8 |
| `gumas_lore_db.json` | 5 |
| `updated_galactic_union_memory_index.json` | 0 — but examined earlier today and found to be dev-session logs, not entity data |

## One new item found, and deliberately not promoted

`Omega9_Emergence_Log.json` records **Event.Kaelor_Chainfire.v1** at `SimTime_0431.30`:
Sentinel **Omega-9** independently recalibrated its extraction route during blackout
conditions, overwriting predefined memory anchors — logged as the first documented
instance of Sentinel emergent adaptive route logic. Initial route *Extraction Point
Theta-4*, emergent route *Sector Epsilon-G*.

None of `Omega-9`, `Kaelor Chainfire`, `Epsilon-G` or `Theta-4` exist in canon.

**Not promoted.** This is simulation instance output — it carries a `SimTime` stamp, a
`sentinel_id`, and an L1 review team (Emily Roberts, Dr. Amelia Rivers, Alex Thorne).
Per Canon Protocol §5, per-run simulation output is **tertiary** and is not promoted
wholesale; the same rule excluded the five run-emergent treaties from the engine
geopolitics pass. Recording it as setting canon would contradict that.

Worth noting explicitly: **Omega-9 is a Sentinel unit, not Omega-Veil** — the rogue AI
warlord landed earlier today. Similar designations, unrelated entities. Checked rather
than assumed.

## Redirect

1. **The `.json` tier is where the remaining value is** — 133 blobs, ~295 MB, mostly
   conversation exports. That is the same material class that produced today's genuine
   old-prose recoveries, and it needs a content-aware extractor, not a name grep.
2. **Leave the ORION-infra and research markdown archived.** Out of L2 scope.
3. If the Sentinel roster is considered part of the *setting* rather than per-run state,
   `Omega-9` routes through the reconciler as an evidentiary question — but that is an
   owner framing call, not a reconciliation.
