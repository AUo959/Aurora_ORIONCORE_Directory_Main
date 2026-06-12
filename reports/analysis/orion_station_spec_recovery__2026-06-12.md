# Orion Station Spec Recovery — 2026-06-12

The iCloud filesystem predates the control plane and served as project-output
storage; this sweep confirmed the Pilot's hypothesis that completed station
work was stranded there outside every repo.

## Recovered and landed (CanonRec `1eda2b2`, STAGING pending owner promotion)

1. **ORION Operational Library v2.2** → `canon/L1/station/operational_library_v2_2/`
   The complete 49-doc space-ready spec set (2026-02-08): L1 Station
   Overview/Systems Bible/Command Structure/Dispatch/Emergency
   Protocols/Operations Runbook v1.1, Station Canvas, Architecture Contract
   L1↔L2↔L3, Canon Policy, Picard Delta 3 ethics layer, entity registry,
   GUMAS L2 schemas, master + category indices v2.2, drift/promotion/conflict
   logs. **No surviving copy was complete** — recovered as a hash-verified
   union of three partial archive copies (49/49 byte-exact vs
   `STAGING_MANIFEST__v2.2.json`), plus the two v1.1 NAMING_INTEGRATED
   engine-doc successors from the Engine Room.
2. **L1 physical configuration** → `canon/L1/station/physical_space/`
   `DATA__OrionStationPhysicalSpace__v1.0__2026-02-15.md` (372-line
   multi-pass mapping: ring 2 RPM / ~0.3g / ~67 m derived radius,
   non-rotating core, 4+8 docking bays, the Dome at ring Deck 4) plus the
   location authority table, GUMAS L2 World Bible v0.2, and the staging-bay
   conflict matrix + promotion queue frozen when work paused.
3. **April 2026 canon packets** → `canon/L1/station/staging_2026-04/`
   STATION_ENVIRONMENT v2.0, L1_ENTITY_REGISTRY v2.0, NAV front door v2.0
   (2026-04-08 authoring pass — the newest station-environment canon found).

## Relevant open work surfaced (work-through queue)

| Item | Where | Why relevant |
|---|---|---|
| ORD-Series Drone Fleet package | `_staging/orion_ord_review_fix/package/` (+ `_staging/apple_notes_recovery__2026-03-16/L1/ord_drone_fleet_v1.0.py`) | L1 Orion Station autonomous MCP validation layer (ORD-1 Gamma Swarm, ORD-2 Delta Scout, ORD-3 Shadowfax); full governed package with specs, tests, audit spine; never integrated into CloudBank |
| Issue #1015 (CloudBank) | open, owner-assigned | "Classify stale status reports and recover clues to missing work" + Missing Reference Ledger follow-up — same salvage doctrine, control-plane scan lane |
| AuroraOS PRs #3, #4, #5 | open since ~March | Stranded feature PRs: symbolic core utilities (DLP manifests, sealing, drift detection), Glyphcard + Export Guard, Glyphnet beacon-pulse vector chain — the no-PR-merge failure mode on a spoke |
| Issue #993 (CloudBank) | open | Promote recovered Sherlock/Watson/Moriarty/Tribunal/SHADOWFAX ethics protocols (ORD-3 Shadowfax cross-reference) |
| quantum-en PRs #11–13 | open | Three competing lockfile-drift-checker PRs need a pick-one decision |

## Promotion path

Library + physical space + April packets are STAGING in CanonRec. Promotion
to CANON requires reconciling: (a) April ENTITY_REGISTRY v2.0 against the
owner-confirmed L1 Entity Ledger v2 (must not regress); (b) physical-space
parameters against CloudBank `simulation/ORION_STATION_MASTER_DOSSIER_v2.6`
and `ORION_STATION_TECHNICAL_REGISTER_v2.6.json`; (c) any Captain-era
nomenclature stays verbatim per `PILOT_ROLE_DEFINITION.md`.
