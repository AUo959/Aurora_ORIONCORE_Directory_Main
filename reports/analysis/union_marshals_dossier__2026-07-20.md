# Union Marshals — Institutional Dossier (L2 / Galactic Union)

**Date:** 2026-07-20 | **Scope:** Everything in the workspace about the Marshals/Marshalls, with naming-inconsistency resolution.

---

## 1. Summary & naming resolution (actionable)

- **Canonical name: "Union Marshals"** — locked CANON entity `org_union_marshals` (L2 Full Promotion Pass 2026-03-19, locked 2026-03-20T02:03:35Z). Registered alias: **"Galactic Marshals"**.
- **"Marshalls" (double L) is a misspelling**, appearing in exactly two repo places, both informal prose — never in a canonical entity, parser, or data file. *(Correction 2026-07-20: origin traced to the Mar-2025 source conversations — 45 instances incl. "Marshalls Division" — so it is source-era spelling carried into later prose, see DRIFT_LOG entry.)*:
  - `reports/analysis/l2_canon_promotion__2026-06-13.md:5` — quoting the owner ruling ("narratives like the Marshalls and the sentinel suits")
  - `reports/recovered_canon/ORION_STATION_STAFF_REGISTRY_INTEGRATION_COMPLETE.md:135` — "Simulated NPCs (Chancellor, Marshalls, faction leaders)"
- The Forge normalization map already enforces the canonical form: `l2_state.py:69-70` maps both `"galactic marshals"` and `"union marshals"` → `"Union Marshals"`.
- **Do not confuse** with "Lord Marshal Virex Tal'Varen" (Velar Imperium strongman) — "Marshal" there is a title of a rival-faction leader, unrelated to the institution.
- **Recommended fix:** correct the two "Marshalls" prose instances (or annotate the quoted ruling `[sic]`); no entity/data changes needed.

---

## 2. Canonical identity

| Field | Value |
|---|---|
| Entity ID | `org_union_marshals` |
| Kind / type | organization / `law_enforcement` |
| Name / aliases | Union Marshals / Galactic Marshals |
| Certainty | **CANON** (canon_lock: true) |
| Faction binding | `galactic_union` |
| Status | active |
| Promotion | "L2 Full Promotion Pass — 2026-03-19"; note: "World Bible + 4 Marshals ledger refs; law enforcement corps. CANON." |
| Canonical file | `GUMAS_SIM_2.5/CanonRec/canon/L2/entities/organizations/org_union_marshals.json` (mirror: `SIM_ENGINE_OUTPUTS/L2_CANON__2026-03-19/organizations/`) |

Faction placement (`canon/L2/factions/GUMAS_Factions.json`): Galactic Union substructures = Union Intelligence, **Union Marshals**, Diplomatic Corps, **Sentinels** (Sentinels listed as a sibling substructure even though operationally the Sentinel program is the Marshals' elite tier — a latent taxonomy tension).

---

## 3. What the institution is

Galaxy-scale law-enforcement / enforcement authority of the Galactic Union ("Union law"). Key characteristics (marshals_sentinel_ledger, LEDGER-MARSHALS-0001):

- Deploys **Sentinel-Class operatives** as its top-tier capability; Sentinel presence in a zone signals "total operational control."
- Civilian perception mixed: protectors *and* enforcers.
- Conducts covert deep-space raids (pirate facilities, rogue AI labs); operations can be "classified – eyes only."
- Sentinel operators are ~5–10% of total Marshal forces (~850–1,000 active Sentinels total ⇒ total Marshal force plausibly ~10–20k, not stated explicitly).

### Force structure

| Tier | Unit | Role |
|---|---|---|
| Elite | Marshal-Operatives (Sentinel Suit users) | Top-tier deployment; 6 suit variants |
| Standard | Marshal-Enforcer Units | Armored strike teams: urban enforcement, riot control, COIN |
| Standard | Tactical Enforcement Officers (TEOs) | Heavy peacekeepers; riot gear, shock batons, energy suppression |
| Specialized | Interceptor Squads | Anti-piracy, orbital zones |
| Covert | Covert Division — **"The Black Hand"** | Deep-cover infiltration, high-risk arrests of Union traitors (also a promoted L2 organization entity) |

Sub-units are canonized with `parent_org_name: "Union Marshals"` (`l2_state.py:1082-1122`).

### Named personnel (canon)

| Character | Role | Canon status |
|---|---|---|
| **Chief Marshal Vael Saros** | Leader of the Union Marshals; Union Loyalist security hardliner, anti-corporate; bias: MORAL_LICENSING (sim engine) | CANON, locked capsule `vael_saros` |
| **Marshal-Captain Elias Drayen** | Ship assignment: **G.U.S. Judicator Prime** | CANON, locked capsule `elias_drayen`, verdict PROMOTE |
| Silent Dagger team (Aric Thal, Lior Serath, Veyna Koris, Kael Voss, Darek Voss †) | Sentinel operatives, Operation Silent Dagger | Ledger characters (tags: silent_dagger, marshals) |
| Cross, Vorn (Marshals), Roake (Ranger logistics), Kade (Sentinel) | L2 sim-capture field team | **Promoted to canon** via sim capture v1.2.0 |

World Bible context: Vael Saros allied with General Kael Durn; Sentinel deployments expanded under Durn and Saros; Grand Strategist Lirian Vos "highly respected by Sentinel Corps."

### Institutions & industry

- **Marshal Academy** (`loc_marshal_academy`, CANON, location_type: academy) — training/selection pipeline for Sentinel operators, on the capital planet.
- **Armada Nova Systems** — military-industrial developer/manufacturer of Sentinel tech (single-contractor bottleneck flagged as political/sabotage risk).
- **Zylox** (Chancellor Zylox Rhaegos) — political authority the Marshals are tied to.

---

## 4. Hardware & doctrine (canon/L2/marshals_sentinels/)

### Sentinel-Class Power Suit — six variants

| Variant | Role | Active |
|---|---|---|
| Praetor | Command & tactical coordination ("Field Marshal") | ~30 |
| Striker | Rapid assault / shock trooper, boarding | ~250 |
| Warden | Defense & crowd control | ~400 |
| Vanguard | Heavy assault & siege (incl. mini jump drive) | <150 |
| Phantom | Stealth / covert ops | classified |
| Stalker | Hunter-killer | <50 |

Constraints: unit cost comparable to small starships; manufacture/deployment strictly limited by the Union; repairs take weeks; loss of one operative ≈ loss of a conventional squad. Typically <100 deployed per battle (500+ only in extreme scenarios).

Weapons (LEDGER-WEAPONS-0001): Arc-Pulse Rifle (standard), Grav-Flux Repeater, Null-Lance, Aegis Gauntlets, Vortex Plasma Carbine, Singularity Warhead Launcher, plus modular attachments.

### Marshal fleet (CSV tables, 8 files)

Sentinel-Class Tactical Carrier, Enforcer-Class Corvette, Warden-Class Cruiser, Phantom-Class Stealth Frigate, Vanguard-Class Battleship, Interceptor-Class Gunship. Capabilities: adaptive shielding, AI targeting, EW suites, AI fleet coordination, boarding deployment, hyperdrive pursuit. Additional vehicles: dropships, orbital bombardment platforms, strike drones, siege walkers, hovercraft.

### Ranger tier (sim capture, promoted to canon)

`l_2_sim_capture_marshals_ranger_sentinel_thread_v_1_0.md` (v1.2.0, status: canonical, promotion_status: promoted_to_canon) establishes the frontier-enforcement escalation ladder: **Ranger-class gunboat** (crew 3: two Marshal field agents + logistics officer; twin wing-embedded 360° quad turrets, human–AI cooperative targeting; not cloaked) → Sentinel intervention as absolute escalation dominance (4 suits routed all hostiles on arrival).

### Marshal Standard Kit (`canon/L2/operations/Marshal_Standard_Kit.md`)

Spatha Moderna ("spade") powered sword; MR-6 heavy service revolver ("iron"); MFR-9 / **Viper** modular energy rifle (anti-armor config observed); wrist-mounted deployable energy shield; modular field armor; grapple, breach tools, multi-spectrum scanner; drone-based combat resupply (homing carrier + high-speed porter drones). Vorn's bracer repulsion device observed in the sim capture.

### Missions on record

- **Operation Silent Dagger** (LEDGER-MISSIONS-0001) — covert strike on Blackreach Station (pirate deep-space facility); rogue-AI lab destroyed, leadership neutralized, intel extracted; 1 KIA (Darek Voss, Vanguard).
- **Frontier Enforcement Escalation Study** — the L2 sim capture above.

---

## 5. Provenance & lineage

| Stage | Artifact | Date |
|---|---|---|
| Primary sources | SRC-0001…0007 excerpts + `Marshals_Sentinels.zip` (8 CSVs) | 2026-01-31 |
| Ledger | `marshals_sentinel_ledger.md` (28KB, source-linked, "Secondary Canon" at the time) | 2026-01-31+ |
| SSOT archive | `ZIPWIZ.ORION.MARSHALS_SENTINELS_SSOT.2026-02-08.BAY02_1706__STRUCTURED_ARCHIVE__r1.zip` | 2026-02-08 |
| World Bible | GUMAS L2 World Bible v0.2 (Vael Saros et al.) | 2026-02-08 |
| Sim capture | Marshals/Rangers/Sentinels thread → canonical | 2026-02-03 |
| Entity promotion | L2 Full Promotion Pass → `org_union_marshals` CANON, locked | 2026-03-19/20 |
| Corpus promotion | Owner ruling → `canon/L2/` incl. `marshals_sentinels/` (~296 files), CanonRec `54e34e8` | 2026-06-13 |
| Archive mining | `canon/L2/factions/` (Union Marshals substructure) + timeline, CanonRec `2dcb313` | 2026-06-13 |

Live source locations: canonical home `GUMAS_SIM_2.5/CanonRec/canon/L2/` (marshals_sentinels/, entities/, operations/, factions/); working originals under `projects/GUMAS_SIM_2.0/03_SIMULATION/Entity_Profiles/Marshals_Sentinels/`. Forge ingestion: `l2_source_manifest.json` (source_ids `marshals_ledger`, `marshals_sim_capture`) parsed by `l2_state.py`; covered by `tests/test_l2_state_bundle.py`.

Note: `projects/Perplexity_Research/.../qgia-marshal-doctrine.md` is unrelated (real-world-style QGIA intelligence-analysis doctrine; "Marshal" is coincidental).

---

## 6. Open questions (from the ledger's own queue + flags)

1. Formal mandate/jurisdiction — Marshal Charter, warrants, oversight (extrapolated only; LEDGER-EXTRAP-0002).
2. Lethal direct action ("assassinate HVT" phrasing) vs Union law — unreconciled continuity flag.
3. Zylox relationship — legitimacy and chain of authority still "details pending" in ledger (World Bible partially answers via Chancellor Zylox Rhaegos).
4. "Sentinel-Class" taxonomy collision — labels both the suit program and a carrier class; proposed fix: *Sentinel Suit Program* vs *Sentinel Fleet Designation*.
5. Factions.json lists "Sentinels" as a GU substructure parallel to Union Marshals — reconcile with ledger's model (Sentinels = Marshals' elite tier).
6. Readiness math, Vanguard jump-drive limits, Black Hand oversight, counter-EMP hardening — all queued.
7. ~~Raw April-2025 archives may hold further Marshals material~~ — **mined 2026-07-20**; see `marshals_raw_archive_mining__2026-07-20.md` (governance model, Sentinel-program origin, drift items staged in `_staging/marshals_archive_mining__2026-07-20/`).
