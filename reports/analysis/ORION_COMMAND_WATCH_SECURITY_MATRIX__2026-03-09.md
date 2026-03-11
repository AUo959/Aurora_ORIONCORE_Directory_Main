# Orion Command, Watch, and Security Matrix

Generated: 2026-03-09

Purpose: reconcile Orion Station command hierarchy, duty-watch structure, and L1 security ownership without clipping parallel canon threads.

## Source Basis

Primary runtime-facing sources:

- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/docs/operational/reports/ORION_STATION_CANONICAL_STAFF_REGISTRY.json`
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/docs/operational/guides/L2_META_AGENT_INTEGRATION_CONFIG.json`
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/modules/symbolic_core/mcp_bridge_core.json`
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/config/shuttle_bay/tool_routing.json`
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/config/shuttle_bay/policy_matrix.json`

Adjacent L1 operations context:

- `Aurora_New_11_9/01_OPERATIONS/Station_Infrastructure/ORION_STATION_CREW_MANIFEST.md`
- `Aurora_New_11_9/01_OPERATIONS/Fleet_Management/fleet_manifest.json`

Related root artifact:

- `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md`

## Reconciliation Rulings

1. `Alex Thorne` remains `Station Commander` in all states. Off-station status or temporary absence does not vacate the office.
2. `Maya Shepard` is `Executive Officer / Deputy Commander` and the default `acting command` holder when Alex is absent, unavailable, or has delegated operational control.
3. `Duty shifts` are real and should be modeled explicitly. Watch authority rotates; command ownership does not.
4. `Runtime-facing staff registry` governs live L1 system ownership.
5. `Broader crew manifest` governs mission, vessel, and day-to-day operational presence.
6. Where two sources assign different named people to adjacent seats, preserve both as parallel threads and distinguish `office holder`, `operational counterpart`, and `watch authority`.

## Merged Command Hierarchy

### Permanent Chain of Command

1. `Station Commander`: Alex Thorne
2. `Executive Officer / Deputy Commander`: Maya Shepard
3. `Department Heads`
   - `Chief Science Officer`: Dr. Varya Lin
   - `Chief Ethics & Compliance Officer`: Dr. Amira Sato
   - `Chief Security Officer`: Julian Markov
   - `Chief Systems Engineer`: Jiro Tanaka
   - `Bridge Operations Officer`: Leena Porter

### Acting and Watch Authority

- `Acting Commander`: Maya Shepard whenever Alex Thorne is absent or operational control is delegated.
- `Officer of the Watch`: rotating duty assignment; this is watch command, not station ownership.
- `Duty Security Officer`: rotating shift lead under Julian Markov.
- `Duty Systems Officer`: rotating shift engineer under Jiro Tanaka, with Marcus Chen preserved as the mission-manifest engineering counterpart.
- `Duty Science Officer`: rotating science lead under Dr. Varya Lin, with Dr. Amina Velin preserved as the mission-manifest science counterpart.
- `Duty Ethics Officer`: rotating ethics/compliance watch under Dr. Amira Sato, with Dr. Elira Noor preserved as the mission-manifest ethics counterpart.

## L1 Security Ownership

| Security / Control Domain | Primary L1 Owner | Acting / Watch Owner | Operational Counterpart Thread | Systems / Surface |
|---|---|---|---|---|
| Station-wide command and emergency override | Alex Thorne | Maya Shepard / Officer of the Watch | None | All L1 critical systems |
| Physical and digital security | Julian Markov | Duty Security Officer | Lt. Nakamura for perimeter response | Access control, quarantine, incident response |
| Bridge health and technical containment | Jiro Tanaka | Duty Systems Officer | Marcus Chen | `OPPY_VECTOR_LOADER_L1`, `system_status`, `symbolic_processing` |
| Research validation and safe compute | Dr. Varya Lin | Duty Science Officer | Dr. Amina Velin | `ARCHY_BRIDGE_L1`, `LIORA_HANDSHAKE_L1`, `aurora_command_grammar`, `geometric_algebra`, `session_management` |
| Ethics lock, continuity, anchor integrity | Dr. Amira Sato | Duty Ethics Officer | Dr. Elira Noor | `Picard_Delta_3`, `EOS_SEED_ORION`, `Riverthread_808` |
| Communications routing and external dispatch | Leena Porter | Officer of the Watch | Samantha Lee for mission comms context | `API_BRIDGE_SERVER`, `Aurora Command Router`, `Starling_AU` |

## L1 Node and Meta-Agent Ownership

| L1 Node / Bridge | Connected Agent | Authority Role | Named L1 Owner | Notes |
|---|---|---|---|---|
| `Aurora (AU)` | Core station orchestration | Command + ethics + systems | Alex Thorne / Dr. Amira Sato / Jiro Tanaka | Shared ownership chain, not a single-seat system |
| `ARCHY_BRIDGE_L1` | `Archy` | Chief Science Officer | Dr. Varya Lin | Science-led reasoning and planning bridge |
| `LIORA_HANDSHAKE_L1` | `Liora` | Chief Science Officer | Dr. Varya Lin | Research and mediation bridge |
| `OPPY_VECTOR_LOADER_L1` | `Oppy` | Chief Systems Engineer | Jiro Tanaka | Marcus Chen preserved as mission-thread engineering counterpart |
| `Aurora Command Router` | `Starling_AU` | Bridge Operations Officer | Leena Porter | Dispatch and external protocol routing |
| `Aurora Command Router` | `Riverthread_808` | Chief Ethics Officer | Dr. Amira Sato | Continuity and temporal-flow authority |

## Shuttle Bay Tool Ownership

| Tool | Lane | Authority Role | Named L1 Owner | Security / Ethics Partners |
|---|---|---|---|---|
| `system_status` | `green` | Chief Systems Engineer | Jiro Tanaka | Julian Markov |
| `aurora_command_grammar` | `green` | Chief Science Officer | Dr. Varya Lin | Julian Markov |
| `geometric_algebra` | `green` | Chief Science Officer | Dr. Varya Lin | Julian Markov |
| `session_management` | `green` | Chief Science Officer | Dr. Varya Lin | Leena Porter, Julian Markov |
| `symbolic_processing` | `gray` | Chief Systems Engineer | Jiro Tanaka | Dr. Amira Sato, Julian Markov |

## Known Named Crew Across Reconciled Sources

Note: the broad crew manifest reports `67 total personnel`, but it does not name all 67 individually. The list below includes the named crew and named command seats surfaced by the currently reconciled L1 sources.

### Command and Department Leadership

- Alex Thorne
- Maya Shepard
- Dr. Varya Lin
- Dr. Amira Sato
- Julian Markov
- Jiro Tanaka
- Leena Porter
- Dr. Elena Vasquez
- Dr. Ren Feldman

### Mission and Operations Counterpart Thread

- Marcus Chen
- Dr. Amina Velin
- Dr. Elira Noor
- Naomi Vell
- Carmen Rivas
- Olivia Nguyen
- Samantha Lee
- Agent Naomi
- Samantha Gray
- Ren Takahashi

### Security, Fleet, and Support Commanders

- Lt. Nakamura
- Lt. Hassan
- Chief Thomson
- Cadet Mira Chen

### Named L1 AI / Autonomous Roles

- Aurora Core / Aurora (AU)
- Athena
- Liora AI
- Daedalus
- Mercury
- Helion
- OPPY
- ARCHY
- Delta Scout
- Shadowfax
- Wisp

## Open Parallel Threads Preserved

- `Station Commander`: resolved in favor of Alex Thorne as permanent office holder. The older "vacant / rotating command structure" wording is reinterpreted as watch rotation, not title vacancy.
- `Chief Systems Engineer`: `Jiro Tanaka` is the runtime-facing owner of live L1 systems; `Marcus Chen` remains preserved as the mission-manifest engineering thread.
- `Chief Science Officer / Research Lead`: `Dr. Varya Lin` is the runtime-facing science authority; `Dr. Amina Velin` remains preserved as the mission-manifest science thread.
- `Chief Ethics Officer / Ethics Lead`: `Dr. Amira Sato` is the runtime-facing ethics authority; `Dr. Elira Noor` remains preserved as the mission-manifest ethics/reflexivity thread.

## Practical Canon Use

- Use `catalog/orion_command_watch_security_matrix.yaml` when a future thread needs a structured command or security lookup.
- Use this report when a future thread needs the reasoning behind the merged model.
- Use `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md` when a broader named-human roster is needed beyond the command and security chain.
