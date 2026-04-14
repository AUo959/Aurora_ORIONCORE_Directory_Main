# Aurora CloudBank Fresh Gap Issue Packet

Generated: 2026-04-10
Updated: 2026-04-11
Target repo: `AUo959/aurora-cloudbank-symbolic`
Scope: current-code gaps and integration issues identified after the initial control-plane mapping pass
Method: nested-repo code inspection plus live open-issue de-duplication

## Summary

This pass did not rely on historical reports alone.

Several previously documented integration gaps are no longer true in current code:

- `hr_system` is included in `api/aurora_api.py`
- Resilience Sentinel is included in `api/aurora_api.py`
- Monitoring Dashboard is included in `api/aurora_api.py`
- GUMAS API routes are included in `api/aurora_api.py`
- `/agent/stream` WebSocket authentication is now present in `api/aurora_api.py`

The fresh issue candidates below are limited to gaps still visible in current implementation.

## Nested Repo State

Observed repo path:
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`

Observed branch:
- `codex/cloudbank-command-chain-workflow-repair-2026-04-10`

Observed state:
- dirty worktree with existing user changes in `.github/` workflows and `scripts/build-web.js`

No nested-repo files were modified during this mapping pass.

## Candidate 1

Title:
- `fix: cross-repo handshake stage 5 reports success without transferring thread context`

Why it qualifies:
- the API surface exposes a 7-stage cross-repository handshake through `/api/v2/bridges/{bridge_id}/handshake`
- stage 5 is still placeholder logic in the implementation
- success can be reported without actual thread payload transfer

Current evidence:
- `api/aurora_api.py:1989` exposes `/api/v2/bridges/{bridge_id}/handshake`
- `modules/reflective_autonomy/thread_transfer/v2/cross_repo_bridge.py:420-431` sets:
  - `bridge.metadata["thread_context_transferred"] = True`
  - `bridge.metadata["transfer_timestamp"] = ...`
  - returns `{"success": True, "stage": "thread_transfer"}`
- the code comment states this is placeholder logic and would integrate with actual thread transfer

Risk:
- the handshake endpoint can claim continuity success while transferring no real thread context
- downstream stages can execute against false state

De-duplication result:
- checked open issues for `thread transfer`, `cross_repo_bridge`, `v2_execute_cross_repo_handshake`, `thread_context_transferred`, `reflective_autonomy`
- no open issue found for this exact gap

## Candidate 2

Title:
- `fix: /collab/workflow/trigger returns success without dispatching any external workflow`

Why it qualifies:
- the route is publicly exposed through the integrated collaboration router
- the handler explicitly states actual workflow triggering would require GitHub API integration
- it still returns `success=True`

Current evidence:
- `api/aurora_api.py:586` includes `collab_router`
- `src/collab/api_routes.py:322-355` defines `POST /collab/workflow/trigger`
- `src/collab/api_routes.py:347-349` documents placeholder behavior
- `src/collab/api_routes.py:351-356` returns `WorkflowTriggerResponse(success=True, ...)` with generated `event_chain_id`

Risk:
- callers receive a success response and tracking chain for a workflow that was never dispatched
- multi-repo automation can drift because the audit trail claims an event occurred when it did not

De-duplication result:
- checked open issues for `workflow trigger`, `repository_dispatch`, `WorkflowTriggerResponse`, `event_chain_id`, `collab`
- no open issue found for this exact route behavior

## Candidate 3

Title:
- `fix: CloudHub VSA API exposes demo bind/similarity routes with placeholder results`

Why it qualifies:
- this is not the same as the core VSA math issue already tracked in `#623`
- the exposed CloudHub API routes bypass real operations and still return demo behavior

Current evidence:
- `api/aurora_gui_cloudhub_fastapi.py:615-629`:
  - `vsa_operation` returns demo strings for `bind`, `unbind`, and `similarity`
- `api/aurora_gui_cloudhub_fastapi.py:641-660`:
  - `vsa_bind` stores `vec_a` unchanged as the bound result
- `api/aurora_gui_cloudhub_fastapi.py:672-690`:
  - `vsa_similarity` returns `float(_rng.random())`

Risk:
- API consumers can get deterministic-looking success responses for semantically incorrect VSA operations
- fixing `modules/symbolic_core/vsa.py` alone would not correct this API surface

De-duplication result:
- checked open issues for `aurora_gui_cloudhub_fastapi.py`, `vsa_operation`, `vsa_bind`, `vsa_similarity`, `CloudHub`, `VSA`
- open issue `#623` exists for `modules/symbolic_core/vsa.py` core bind/superpose correctness
- no open issue found for the CloudHub API route layer that still returns placeholder/demo results

## Candidate 4

Title:
- `fix: /api/l2-agents activation and relay are simulated, not backed by real transport`

Why it qualifies:
- the L2 meta-agent router is mounted into the canonical API app
- the activation and relay handlers delegate into a bridge implementation that still simulates handshake state locally
- the relay path returns success without any real downstream dispatch

Current evidence:
- `api/aurora_api.py:703-704` includes `l2_meta_agent_router`
- `src/api/l2_meta_agent_api.py:265-317` exposes `POST /api/l2-agents/activate`
- `src/api/l2_meta_agent_api.py:352-404` exposes `POST /api/l2-agents/relay`
- `src/bridges/l2_meta_agent_bridge.py:245-324` simulates handshake stages with `asyncio.sleep(...)`, locally constructed beacon/anchor/ethics payloads, hard-coded `drift = 0.000`, and `timeline_sync = True`
- `src/bridges/l2_meta_agent_bridge.py:402-411` explicitly notes real relay is not implemented yet and still returns `success=True`, `processed=True`

Risk:
- callers can receive a full success envelope for activation, ZIPWIZ handshake completion, and relay processing without any real agent transport
- audit trails built from these responses overstate the actual integration state

De-duplication result:
- checked open issues for `l2-agents`, `L2 Meta-Agent`, `l2_meta_agent_api`, `ZIPWIZ`, `HALO_CONTINUITY_GRAFT_005`
- closest open issue is `#529`, but that only tracks `MockARCHY` removal in `triplex_handshake.py`
- no open issue found for the mounted `/api/l2-agents` route layer backed by `src/bridges/l2_meta_agent_bridge.py`

## Candidate 5

Title:
- `fix: /simulate/progress streams synthetic 50% heartbeat instead of real simulation status`

Why it qualifies:
- the quantum simulator router is mounted into the canonical API app
- the progress WebSocket does not query real active-run state when no completed result is cached
- unknown or inactive simulation ids can still look half complete forever

Current evidence:
- `api/aurora_api.py:157` imports `quantum_simulator_router`
- `api/aurora_api.py:558` includes `QUANTUM_SIMULATOR_ROUTER`
- `modules/quantum_simulator/api.py:319-390` defines `/simulate/progress/{simulation_id}`
- `modules/quantum_simulator/api.py:378-379` states:
  - `# For active simulations, would query engine status`
  - `# For now, send periodic heartbeat`
- `modules/quantum_simulator/api.py:380-388` returns fixed `status="running"`, `progress=0.5`, `elapsed_time_seconds=0.0`, `message="Simulation in progress..."`

Risk:
- clients cannot distinguish unknown ids from real in-flight runs
- the progress stream looks authoritative while being synthetic
- UI and automation consumers can make decisions from false runtime status

De-duplication result:
- checked open issues for `/simulate/progress`, `quantum simulator`, `simulation progress websocket`, `Simulation in progress...`
- no open issue found for this mounted progress-stream behavior

## Candidate 6

Title:
- `security: /sentinel/ws/metrics exposes live system health without authentication`

Why it qualifies:
- the Resilience Sentinel router is mounted into the canonical API app
- its WebSocket accepts before any auth or verified connection gate
- the handler then streams dashboard state and alerts

Current evidence:
- `api/aurora_api.py:648-649` includes `sentinel_router`
- `modules/resilience_sentinel/api.py:451-454` immediately accepts connections in `ConnectionManager.connect()`
- `modules/resilience_sentinel/api.py:473-518` exposes `/sentinel/ws/metrics` and sends `dashboard_update` plus `new_alerts`

Risk:
- unauthenticated clients can subscribe to live system-health and alert telemetry
- this leaks operational runtime state from a mounted API surface

De-duplication result:
- checked open issues for `/ws/metrics`, `Resilience Sentinel`, `sentinel websocket`, `monitoring websocket`
- no open issue found for this route
- this is not a duplicate of `#641`, which tracks separate CloudHub WebSocket endpoints in `api/aurora_gui_cloudhub_fastapi.py`

## Candidate 7

Title:
- `security: /api/auth/token ships known default credentials through mounted auth router`

Why it qualifies:
- the auth router is mounted into the canonical API app
- the live token endpoint authenticates against an in-memory user database with known default usernames and passwords
- this is a production-surface security issue rather than a test-only fixture

Current evidence:
- `api/aurora_api.py:679-682` includes `auth_router`
- `src/security/auth_routes.py:110-156` exposes `POST /api/auth/token`
- `src/security/auth_routes.py:46-73` seeds:
  - `admin` / `admin123`
  - `operator` / `operator123`
  - `observer` / `observer123`
- the same file explicitly notes the database is for demonstration and should be replaced in production

Risk:
- known static credentials remain valid for the mounted token flow unless separately neutralized at deployment time
- the default auth posture is insecure by construction

De-duplication result:
- checked open issues for `auth`, `OAuth2`, `/api/auth/token`, `hardcoded password`, `admin123`, `in-memory user database`
- no open issue found for this mounted hardcoded-credential condition

## Candidate 8

Title:
- `fix: /api/synergy/components reports placeholder health and resource status as live data`

Why it qualifies:
- the synergy dashboard router is mounted into the canonical API app
- the route advertises real-time component status
- the returned health, uptime, heartbeat, and resource values are still synthetic

Current evidence:
- `api/aurora_api.py:637-640` includes `synergy_router` and `dashboard_router`
- `src/synergy/dashboard_api.py:222-269` exposes `GET /api/synergy/components`
- `src/synergy/dashboard_api.py:143-156` marks `calculate_component_health()` as a placeholder implementation with hardcoded scores
- `src/synergy/dashboard_api.py:255-260` sets:
  - `last_heartbeat` to the current request time for every component
  - `uptime_seconds=86400`
  - CPU and memory from `hash(comp["id"])`

Risk:
- the route presents operational-looking status as if it were live telemetry
- dashboarding and automation consumers can mistake static/demo topology data for real runtime health

De-duplication result:
- checked open issues for `synergy`, `/api/synergy/components`, `calculate_component_health`, `uptime_seconds`, `placeholder`
- no open issue found for this mounted route behavior

## Candidate 9

Title:
- `security: /synergy mutation routes allow unauthenticated component registry writes`

Why it qualifies:
- the synergy registry router is mounted into the canonical API app
- it exposes component registration and status mutation routes
- those write paths have no auth or CSRF gate

Current evidence:
- `api/aurora_api.py:637-640` includes `synergy_router`
- `src/synergy/api.py:27` sets prefix `/synergy`
- `src/synergy/api.py:108-140` exposes `POST /synergy/components`
- `src/synergy/api.py:159-180` exposes `PUT /synergy/components/{name}/status`
- neither handler uses `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can register arbitrary components and alter recorded component state
- the integrity of the component registry and dependent tooling can be manipulated without identity verification

De-duplication result:
- checked open issues for `synergy`, `/synergy/components`, `component status`, `register component`
- no open issue found for this unauthenticated mutation surface
- this is not a duplicate of `#647`, which tracks placeholder live-status data in the separate dashboard route behavior

## Candidate 10

Title:
- `security: /api/coordination mutation routes allow unauthenticated workflow and lock changes`

Why it qualifies:
- the coordination router is mounted into the canonical API app
- it exposes multiple state-changing workflow, lock, subscription, and conflict-resolution routes
- those write paths have no auth or CSRF gate

Current evidence:
- `api/aurora_api.py:611-612` includes `EVENT_COORDINATION_ROUTER`
- `src/coordination/event_api.py:29` sets prefix `/api/coordination`
- unauthenticated mutation routes include:
  - `POST /api/coordination/events/publish`
  - `POST /api/coordination/subscriptions/subscribe`
  - `DELETE /api/coordination/subscriptions/{subscription_id}`
  - `POST /api/coordination/conflicts/resolve`
  - `POST /api/coordination/locks/acquire`
  - `DELETE /api/coordination/locks/{resource_id}`
  - `POST /api/coordination/workflows/create`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can alter coordination state, lock ownership, and workflow orchestration
- coordination surfaces become writable without identity verification

De-duplication result:
- checked open issues for `/api/coordination`, `coordination`, `workflow`, `lock`, `subscription`
- no open issue found for this unauthenticated mutation surface

## Candidate 11

Title:
- `security: /sentinel alert mutation routes lack authentication and CSRF protection`

Why it qualifies:
- the Resilience Sentinel router is mounted into the canonical API app
- it exposes alert acknowledgment, resolution, and rule-management writes
- those write paths have no auth or CSRF gate

Current evidence:
- `api/aurora_api.py:648-649` includes `sentinel_router`
- `modules/resilience_sentinel/api.py:124` sets prefix `/sentinel`
- unauthenticated mutation routes include:
  - `POST /sentinel/alerts/acknowledge`
  - `POST /sentinel/alerts/resolve`
  - `POST /sentinel/alerts/rules`
  - `DELETE /sentinel/alerts/rules/{rule_name}`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can mutate alert lifecycle state and alert rules
- trust in the monitoring and alerting surface is weakened

De-duplication result:
- checked open issues for `/sentinel`, `sentinel`, `alert rule`, `acknowledge`, `resolve`
- no open issue found for this unauthenticated mutation surface
- this is not a duplicate of `#645`, which tracks the separate unauthenticated `/sentinel/ws/metrics` WebSocket stream

## Candidate 12

Title:
- `security: /gumas rule and violation mutation routes lack authentication and CSRF protection`

Why it qualifies:
- the GUMAS router is mounted into the canonical API app
- it exposes rule-creation, rule-deletion, and violation-clearing writes
- those write paths have no auth or CSRF gate

Current evidence:
- `api/aurora_api.py:670-672` includes `gumas_router`
- `modules/gumas/api/routes.py:28` sets prefix `/gumas`
- unauthenticated mutation routes include:
  - `POST /gumas/rules`
  - `DELETE /gumas/rules/{rule_id}`
  - `DELETE /gumas/violations`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can alter ethics-engine rules and recorded violation history
- the integrity of policy enforcement and audit flows is weakened

De-duplication result:
- checked open issues for `/gumas`, `gumas`, `rules`, `violations`, `delete`
- no open issue found for this unauthenticated mutation surface

## Candidate 13

Title:
- `security: /playground exposes unauthenticated code execution, sharing, and session streaming`

Why it qualifies:
- the playground router is mounted into the canonical API app
- it exposes session creation, code execution, sharing, and WebSocket streaming without auth or ownership checks
- when Docker is unavailable, sandbox execution falls back to a local subprocess runner

Current evidence:
- `api/aurora_api.py:721-725` includes `playground_router`
- `src/playground/api.py:37-46` exposes `POST /playground/session`
- `src/playground/api.py:49-61` exposes `POST /playground/execute`
- `src/playground/api.py:69-89` exposes `POST /playground/share`
- `src/playground/api.py:117-126` exposes `GET /playground/ws/{session_id}`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, session ownership checks, or an authenticated user dependency
- `src/playground/sandbox.py:53-58` logs Docker unavailability and falls back to local execution
- `src/playground/sandbox.py:105-147` executes code via local `subprocess.run(...)`

Risk:
- unauthenticated callers can create sessions, execute arbitrary playground code, and subscribe to session event streams
- fallback to local subprocess execution increases impact when the Docker sandbox is unavailable

De-duplication result:
- checked open issues for `playground`, `/playground/execute`, `sandbox`, `session streaming`, `share`
- no open issue found for this mounted playground surface
- this is not a duplicate of `#597` or `#598`, which already track the separate `/subroutines` register/execute chain

## Candidate 14

Title:
- `security: /memory mutation and export routes lack authentication and CSRF protection`

Why it qualifies:
- the AuMemManager router is mounted into the canonical API app
- it exposes state-changing memory, quantum-vector, lifecycle, and export operations
- those routes have no auth or CSRF gate

Current evidence:
- `api/aurora_api.py:125-127` imports `aumemmanager_router`
- `api/aurora_api.py:529` includes `AUMEMMANAGER_ROUTER`
- `modules/aumemmanager/api_integration.py:20` sets prefix `/memory`
- unauthenticated mutation and export routes include:
  - `POST /memory/create`
  - `POST /memory/quantum/create_vector`
  - `POST /memory/quantum/entangle`
  - `POST /memory/quantum/trajectory`
  - `POST /memory/lifecycle/batch_process`
  - `POST /memory/compress`
  - `GET /memory/export`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can create memories, mutate quantum-vector state, trigger lifecycle/compression workflows, and export system state
- memory integrity and confidentiality can be altered or exfiltrated without identity verification

De-duplication result:
- checked open issues for `aumemmanager`, `/memory`, `memory export`, `memory auth`, `quantum entangle`
- no open issue found for this unauthenticated mutation and export surface

## Candidate 15

Title:
- `security: /ledger write, query, and export routes lack authentication and CSRF protection`

Why it qualifies:
- the Insight Ledger router is mounted into the canonical API app
- it exposes ledger writes, flexible history queries, and export behavior without auth
- those routes handle integrity-sensitive and potentially sensitive audit data

Current evidence:
- `api/aurora_api.py:145-148` imports `insight_ledger_router`
- `api/aurora_api.py:547-549` includes `INSIGHT_LEDGER_ROUTER` and initializes ledger storage
- `modules/insight_ledger/api.py:19` sets prefix `/ledger`
- unauthenticated routes include:
  - `POST /ledger/insight`
  - `POST /ledger/history`
  - `POST /ledger/export`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can append audit records, query ledger history, and export ledger contents
- the integrity and confidentiality posture of the ledger is weakened at the API layer

De-duplication result:
- checked open issues for `insight ledger`, `/ledger`, `ledger export`, `ledger auth`, `record insight`
- no open issue found for this unauthenticated ledger surface

## Candidate 16

Title:
- `security: /simulate execution and cache mutation routes lack authentication and CSRF protection`

Why it qualifies:
- the quantum simulator router is mounted into the canonical API app
- it exposes scenario execution, forecast execution, result deletion, and cache clearing without auth
- these are state-changing compute and cache-management operations

Current evidence:
- `api/aurora_api.py:157-159` imports `quantum_simulator_router`
- `api/aurora_api.py:558` includes `QUANTUM_SIMULATOR_ROUTER`
- `modules/quantum_simulator/api.py:21` sets prefix `/simulate`
- unauthenticated mutation routes include:
  - `POST /simulate/scenario`
  - `DELETE /simulate/results/{simulation_id}`
  - `POST /simulate/forecast`
  - `POST /simulate/cache/clear`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can trigger compute-heavy simulations, delete cached results, and clear cache state
- public callers can alter simulator state and service availability without identity verification

De-duplication result:
- checked open issues for `quantum simulator`, `/simulate`, `simulate auth`, `cache clear`, `scenario`
- open issue `#644` exists for the separate `/simulate/progress/{simulation_id}` synthetic heartbeat behavior
- open issue `#642` exists for the separate CloudHub public `/quantum/circuit` placeholder route split
- no open issue found for this unauthenticated `/simulate` execution and cache-mutation surface

## Candidate 17

Title:
- `security: /relay/send allows unauthenticated cross-layer message dispatch`

Why it qualifies:
- the Relay Manager router is mounted into the canonical API app
- it exposes cross-layer message dispatch plus relay status/statistics without auth
- the write surface is publicly callable through `POST /relay/send`

Current evidence:
- `api/aurora_api.py:627-629` includes `RELAY_MANAGER_ROUTER`
- `src/aurora/relays/api_routes.py:23` sets prefix `/relay`
- `src/aurora/relays/api_routes.py:103-166` exposes `POST /relay/send`
- `src/aurora/relays/api_routes.py:169-191` exposes `GET /relay/stats`
- `src/aurora/relays/api_routes.py:194-213` exposes `GET /relay/status`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can inject cross-layer relay messages into the runtime surface
- public callers can inspect relay status/statistics that should be tied to operator identity

De-duplication result:
- checked open issues for `relay manager auth`, `/relay/send`, `cross-layer message`, `relay stats`
- no open issue found for unauthenticated access to the mounted Relay Manager router

## Candidate 18

Title:
- `security: /monitoring mutation and audit routes lack authentication and CSRF protection`

Why it qualifies:
- the monitoring dashboard router is mounted into the canonical API app
- it exposes baseline establishment, behavior recording/checking, action evaluation, and audit/violation retrieval without auth
- this is distinct from the already-open monitoring persistence and ethics-logic bug cluster

Current evidence:
- `api/aurora_api.py:656-661` creates and includes the monitoring router
- `src/monitoring/dashboard_api.py:115` sets prefix `/monitoring`
- state-changing routes include:
  - `POST /monitoring/baseline`
  - `POST /monitoring/behavior/record`
  - `POST /monitoring/behavior/check`
  - `POST /monitoring/action/evaluate`
- sensitive read routes include:
  - `GET /monitoring/alerts`
  - `GET /monitoring/violations`
  - `GET /monitoring/audit`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- unauthenticated callers can mutate agent baselines and behavior records
- public callers can read alerts, violations, and audit history from the monitoring surface

De-duplication result:
- checked open issues for `/monitoring`, `monitoring baseline auth`, `behavior record auth`, `action evaluate auth`
- existing open issues `#593`, `#594`, `#595`, `#599`, `#604`, and `#605` concern persistence and ethics correctness, not missing authentication on the monitoring router

## Candidate 19

Title:
- `security: /r2-telemetry exposes live telemetry and test-operation writes without authentication`

Why it qualifies:
- the R-2 telemetry router is mounted into the canonical API app
- it exposes live metrics, anomaly, and recent-operation data without auth
- it also provides a public test endpoint that mutates telemetry state by generating synthetic events

Current evidence:
- `api/aurora_api.py:688-691` includes `r2_telemetry_router`
- `api/r2_telemetry_routes.py:23` sets prefix `/r2-telemetry`
- unauthenticated telemetry exposure includes:
  - `GET /r2-telemetry/metrics`
  - `GET /r2-telemetry/summary`
  - `GET /r2-telemetry/operations/recent`
  - `GET /r2-telemetry/health`
  - `GET /r2-telemetry/anomalies`
- `api/r2_telemetry_routes.py:175-215` exposes `POST /r2-telemetry/test-operation`
- these handlers do not use `Depends(security)`, `verify_csrf_token`, or an authenticated user dependency

Risk:
- public callers can read live telemetry, anomaly, and operation data from the R-2 observability surface
- unauthenticated callers can inject synthetic telemetry through the test-operation endpoint

De-duplication result:
- checked open issues for `/r2-telemetry`, `r2 telemetry auth`, `test-operation auth`, `telemetry metrics auth`
- this is not a duplicate of `#645`, which tracks the separate Sentinel metrics WebSocket surface
- no open issue found for the unauthenticated R-2 telemetry router

## Excluded Candidates

These were investigated and intentionally not opened in this pass:

- monitoring integration gaps
  - current code includes Resilience Sentinel and Monitoring Dashboard in `api/aurora_api.py`
- `hr_system` integration gap
  - current code includes `hr_system_router` in `api/aurora_api.py`
- missing GUMAS API issue
  - current code includes `gumas_router` in `api/aurora_api.py`
- unauthenticated WebSocket issue in `api/aurora_api.py`
  - `/agent/stream` now validates query-token auth before `accept()`
- Data Guardian PII service exposure
  - `modules/data_guardian/api.py` exposes `/data/scan` and `/data/redact` without auth
  - this was not opened in this pass because the stronger remaining findings were routers that mutate internal runtime or observability state rather than stateless scan/redact processing
- `subroutines` unauthenticated register/execute surface
  - `src/subroutines/api.py` still exposes writable and executable endpoints without auth
  - this was not reopened because open issues `#597` and `#598` already cover the mounted `/subroutines` execution and auth gap
- `hr_system` silent mock fallback
  - mounted routes in `modules/hr_system/api/hr_routes.py` still return fabricated staffing, character, and organizational data on `ImportError`
  - this was not opened in this pass because it appears too likely to overlap broader older `hr_system` integration work such as `#380`

## Publication Status

Live issues created from this packet:

1. `#637` `fix: cross-repo handshake stage 5 reports success without transferring thread context`
2. `#638` `fix: /collab/workflow/trigger returns success without dispatching any external workflow`
3. `#639` `fix: CloudHub VSA API exposes placeholder bind and similarity behavior`
4. `#641` `security: CloudHub WebSocket endpoints accept unauthenticated connections`
5. `#642` `fix: public /quantum/circuit route returns placeholder success while /api/quantum/circuit performs real execution`
6. `#643` `fix: /api/l2-agents activation and relay are simulated, not backed by real transport`
7. `#644` `fix: /simulate/progress streams synthetic 50% heartbeat instead of real simulation status`
8. `#645` `security: /sentinel/ws/metrics exposes live system health without authentication`
9. `#646` `security: /api/auth/token ships known default credentials through mounted auth router`
10. `#647` `fix: /api/synergy/components reports placeholder health and resource status as live data`
11. `#648` `security: /synergy mutation routes allow unauthenticated component registry writes`
12. `#649` `security: /api/coordination mutation routes allow unauthenticated workflow and lock changes`
13. `#650` `security: /sentinel alert mutation routes lack authentication and CSRF protection`
14. `#651` `security: /gumas rule and violation mutation routes lack authentication and CSRF protection`
15. `#652` `security: /playground exposes unauthenticated code execution, sharing, and session streaming`
16. `#653` `security: /memory mutation and export routes lack authentication and CSRF protection`
17. `#654` `security: /ledger write, query, and export routes lack authentication and CSRF protection`
18. `#655` `security: /simulate execution and cache mutation routes lack authentication and CSRF protection`
19. `#656` `security: /relay/send allows unauthenticated cross-layer message dispatch`
20. `#657` `security: /monitoring mutation and audit routes lack authentication and CSRF protection`
21. `#658` `security: /r2-telemetry exposes live telemetry and test-operation writes without authentication`

This is the minimal non-duplicate set supported by current code inspection in this pass.
