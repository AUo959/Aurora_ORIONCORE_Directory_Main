# ORD Drone Fleet — Complementary-Work Scan + Clean Integration Staging — 2026-06-12

## Complementary-work scan (pre-integration)

Sweep terms: ORD, drone, dispatch, Shadowfax, Gamma Swarm, Delta Scout,
policy engine — filenames and content, whole iCloud tree.

**Confirmed single-copy salvage:** the ORD policy modules
(`ord_threshold_registry`, `ord_policy_engine`, `ord_inspection_policy`,
`ord_receipts`) exist only in `_staging/orion_ord_review_fix/package/` —
no copies elsewhere, no ORD commits in any repo history. Pure uncommitted
cargo.

**Already integrated counterpart:** CloudBank `src/entities/fleet/`
(registry accessors for ORD-1/2/3 + Wisp) — the entity layer the policy
family drives. `docs/ARTIFACT_README_SHADOWFAX.md` and
`SRB_SHADOWFAX_Stillness_v1.0.zip` already in-repo.

**Complementary uncommitted siblings (staged, not yet integrated):**

| Artifact | Location | Disposition |
|---|---|---|
| `ord_drone_fleet_v1.0.py` (939 lines, Apple Notes Nov 2025) | `_staging/apple_notes_recovery__2026-03-16/L1/` | Earlier generation of the dispatch system; superseded by workbench v0.5.0; keep staged per promotion queue |
| `SOURCE__Recovered__ORD_DroneDispatch__v0.1` (1,349 lines) | workbench `staging/legacy_pack/` | Legacy source; promotion queue: staging only |
| Legacy pack L3 normalized docs (AuroraLiteBridge, ContinuitySeed, CloudBank Normalized spec, LegacyCommandNormalization, THREADCORE SidebarAlias v0.2) | workbench `staging/legacy_pack/` | Separate promotion lane; not ORD-blocking |
| `AURORA_SEED_PROTOCOL_v1.0.md`, `QUANTUM_AGENT_FORGE_PROTOCOL_v1.0.md`, `GUMAS_DEPARTMENT_REGISTRY_v1.0.md`, `MULTILINGUAL_BEAMFORMING_ARRAY_SEED.md`, `THREADCORE_v3.6_macrodrift_plus.js` | apple notes recovery L1/L2/L3 | Candidate complements to existing `modules/quantum_forge`, `modules/reflective_autonomy`, GUMAS — owner triage |
| L3 governance library (evidence gate, narrative style control, workshop gates) | workbench `library/L3_governance/` | Governance-doc lane; route via CanonRec when promoted |

Excluded after inspection: `intake/text_au_dispatch_trilux.txt` (narrative
continuity dispatch log — narrative-layer cargo, not ORD code),
`Dispatch_Protocol_v2.3.0_Patch007_SignalCleanse.md` (newsletter-style
Global Dispatch guide, unrelated domain).

## Integration staging

CloudBank branch `feat/ord-policy-family` → **PR #1016**, layout per the
workbench's own `PROMOTION_QUEUE.md` (modules/ord + governance registry +
docs/ord specs + tests/ord). 15 tests marked `critical` (CI gate grows
128 → 143). Posture preserved: policy-library candidate; live MCP dispatch
wiring is a deliberate later step.
