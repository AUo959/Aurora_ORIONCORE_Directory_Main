# G.U.S. Judicator Prime — Context Recovery Report — 2026-07-21

**Pattern:** same arc as the Spatha pass (mine → gap-analyse → owner rulings → promotion).
**Finding in one line:** the Judicator Prime has a **complete specification and an eight-person
senior staff in unpromoted sources**, plus a dedicated 718-line ship registry that was written
to be promoted and never was — and one **numeric conflict** that needs your ruling.

## 1. What canon currently holds

`vessel_gu_001.json` (CANON): name, aliases, `CLASS-JUDICATOR-01`, allegiance,
`commanding_officer_id: alric_tann`, flagship significance, Marshal-integration block
(embarked `elias_drayen`, hosts a Sentinel strike unit), `crew_approx: 12000` (APPROX),
`class_hull_type: supercarrier`, `placement_rule`.

**Absent:** all specifications (weapons, defences, propulsion, support craft, cyberwarfare),
any crew roster beyond the CO, and any record of the ship *class* itself.

## 2. Recovered context

### 2.1 Full specification — World Bible + Ship Registry (identical, mutually corroborating)

| System | Established value |
|---|---|
| Primary weapons | Long-range plasma lances; AI-coordinated point defence |
| Defensive systems | Multi-layered energy shields; ablative armour plating |
| Propulsion | Dual FTL cores with emergency jump capability |
| Support craft | Full Sentinel deployment wing; tactical interceptors |
| Cyberwarfare / special | AI-Vanguard countermeasures; encrypted battle network |
| Class role | Strategic fleet coordination, high-level diplomacy, cyberwarfare ops |
| Class features | Heavily armoured, FTL-capable, Sentinel deployment bays, AI-resistant command systems, dual FTL cores |

### 2.2 Senior staff — eight officers, World Bible §4.2

Every one **already has a CanonRec entity record and a built capsule**, and every one is
described by role *as Judicator Prime crew* — but **no record links them to the ship**:

| Officer | Role aboard | Record | Capsule | Bound to ship? |
|---|---|---|---|---|
| Alric Tann | Commanding Officer | ✓ | ✓ | CO field only |
| Lyra Voss | Executive Officer | ✓ | ✓ | **No** |
| Elias Radek | Sentinel-Commander | ✓ | ✓ | **No** |
| Adrienne Kovas | Chief Science Officer | ✓ | ✓ | **No** |
| Nia Veran | Chief Medical Officer | ✓ | ✓ | **No** |
| Rhen Kailo | Chief Engineer | ✓ | ✓ | **No** |
| Arin Tavos | Tactical Ops & Gunnery Chief | ✓ | ✓ | **No** |
| Elias Drayen | Marshal-Captain, Sentinel SpecOps | ✓ | ✓ | In Marshal block only |

### 2.3 The Ship Registry (`L2_GUMAS_SHIP_REGISTRY_v1.0.md`, 718 lines, unpromoted)

A finished artifact: JSON schema for classes and vessels, **12 ship classes**, **16 named
vessels**, registry statistics, a "Resolve Before CANON_PROMOTE" open-items section, integration
notes, and a senior-staff sign-off block still marked ☐ PENDING. Status line reads
*"STAGING — Awaiting review. Next Action: Senior staff approval → merge into machine-readable packet §3.5."*

It also independently confirms two current canon gaps: `G.U.S. Kharon` and `G.U.S. Sablewake`
class unknown — matching `vessel_gu_013`/`vessel_gu_014`, which carry `class_id: null` today.

## 3. Gap analysis

| # | Gap | Severity | Detail |
|---|---|---|---|
| J1 | **Specifications never promoted** | HIGH | Weapons/defence/propulsion/support/cyberwarfare exist identically in two sources; canon record has none. |
| J2 | **Crew roster not linked** | HIGH | Eight officers defined as Judicator Prime staff; the vessel has no `crew_ids` and no officer capsule carries a `location_binding`. This is the single largest concentration of unbound C1 capsules in the workspace. |
| J3 | **Ship Registry unpromoted** | HIGH | A promotion-ready registry (12 classes, 16 vessels) sat at STAGING since authoring. Same pattern as the sim capture in the Spatha pass. |
| J4 | **No ship-class records** | MEDIUM | `CLASS-JUDICATOR-01` (and 11 sibling classes) have no entity records — vessels reference class IDs that resolve to nothing. Directly analogous to the equipment-record gap closed in G5. |
| J5 | **Crew-count conflict** | MEDIUM | Canon `crew_approx: 12000` (APPROX, April-2025 archive mining, owner-approved 2026-07-20) vs registry `typical_complement: 2500` for the class. **~4.8× discrepancy.** Reconcilable (class baseline vs flagship/supercarrier loadout incl. embarked Sentinel wing) but currently unstated — needs a ruling, not a silent pick. |
| J6 | **Kharon / Sablewake classless** | LOW | Registry flags both P2-unknown; canon records carry `class_id: null`. Consistent, but open. |

## 4. Recommended rulings

1. **RULING-JUDICATOR-SPECS (J1)** — promote the specification block into `vessel_gu_001`
   (two corroborating sources, no contradiction).
2. **RULING-JUDICATOR-CREW (J2)** — add `crew_ids` to the vessel and `location_binding` to the
   eight officer capsules (rebuild required — capsules are sha256-manifested). Closes eight C1
   gaps at once and would leave only ~9 legacy capsules unbound workspace-wide.
3. **RULING-SHIP-REGISTRY (J3)** — land the registry in CanonRec, either promoted or explicitly
   recorded as STAGING-with-receipt. Its sign-off block is unsigned; owner gate applies.
4. **RULING-SHIP-CLASSES (J4)** — create ship-class entity records (Judicator-only, or all 12).
5. **RULING-JUDICATOR-CREW-COUNT (J5)** — resolve 12,000 vs 2,500: either state the reconciliation
   (class baseline vs flagship complement) or pick one and mark the other superseded.

## 5. Source register

- Canon: `GUMAS_SIM_2.5/CanonRec/canon/L2/entities/mobile_assets/vessel_gu_001.json`
- Ship registry: `projects/GUMAS_SIM_2.0/04_DOCUMENTATION/GUMAS_Legacy/Original_Materials/GUMAS_OG/L2_GUMAS_SHIP_REGISTRY_v1.0.md`
- World Bible §4.2 senior staff + fleet: `…/GUMAS_OG/GUMAS_L2_World_Bible.md`
- Runtime packet (cited canon source): `projects/GUMAS_SIM_2.0/02_DEVELOPMENT/…/L2_GUMAS_RUNTIME_REFERENCE_PACKET_v0.4.md`
- Marshal integration: `canon/L2/marshals_sentinels/ARCHIVE_MINING_ADDENDUM__2026-07-20.md` (LEDGER-ASSETS-0002)
