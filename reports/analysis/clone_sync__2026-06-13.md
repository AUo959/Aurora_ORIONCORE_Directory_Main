# CloudBank Clone Sync + ORD Flight Declaration — 2026-06-13

## Sync

Clone fast-forwarded `602a12e7 → 3494e5ac` (10 commits, including ORD merge
#1016). Codex's in-progress `tests/test_mesh_router_v1.py` adaptation was
preserved losslessly (backup: `_staging/codex_wip/test_mesh_router_v1__codex_wip_preserved_2026-06-13.py`),
stashed for the pull, and re-applied cleanly on top — it remains in the
working tree exactly as Codex left it, now based on current main. Registry
re-pinned. Critical tier on the synced clone: 143 passed.

## Defect found on main (not yet filed — owner authorization needed for issue)

The `/api/mesh/agents` routes from `32760cdb` (#764) fail their own tests on
clean main (5 of 9):

1. `GET/POST /api/mesh/agents/{unknown}` returns **500 instead of 404**
   (unhandled error in `create_app()`, `l2_integration_server.py` — needs an
   unknown-id guard).
2. `test_mesh_agents_list` hardcodes `total == 6` but repo manifests carry
   the 47-agent crew.

Codex's WIP adaptation (dynamic manifest-derived ids) fixes class 2:
with it applied, failures drop to 3 (the two 404 defects + one residual).
The new tests are not critical-marked, so CI Check does not gate them —
mark them critical once green. Test-file work stays in Codex's lane; the
404 route guard is a small independent src fix.

## ORD flight

`ord-policy-dispatch` declared in the flight contract and flown:
MissionBrief → DispatchOrder through the live merged module — 3 drones
required for a 0.55-risk external write, canonical SHA-256 receipt cut.
The module is exercised, not just merged.
