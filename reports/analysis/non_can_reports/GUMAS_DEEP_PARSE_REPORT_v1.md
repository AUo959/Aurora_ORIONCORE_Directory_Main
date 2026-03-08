# GUMAS v2.0 DEEP PARSE REPORT
**Date:** 2026-02-12  
**Mode:** DEEP PARSE (Component Spec + Call Graph + State Transitions)  
**Anchor:** EOS_SEED_ORION / Picard_Delta_3  
**DLP:** L2_ENGINE_CORE  

---

## 1. EXECUTIVE SUMMARY

**GUMAS v2.0** is a 15-phase turn-based simulation engine combining v1.0 diplomatic/conflict systems with v2.0 subsystems for galactic topology, military operations, economics, media, precursors, and sentinels.

- **Core Module:** `engine.py` (main orchestrator, 33 event handlers)
- **Data Models:** `models.py` (28 dataclasses, 17 enums)
- **Subsystem Count:** 6 major (topology, combat, economics, media, precursor, sentinel)
- **Scenario Builders:** 5 variants (canonical, rotting_treaty, corporate_coup, ai_shadow_split, frontier_spark, precursor_ping)
- **Total Tick Lifecycle:** 15 phases + naming resolution (Phase 6.5)
- **State Complexity:** 13 faction types, 9 conflict phases, 8 bias types, 33 event types

---

## 2. COMPLETE CALL GRAPH (EXECUTION FLOW)

### **2.1 Engine Initialization Chain**
```
GUMASEngine.__init__(seed, ethics_callback)
  ↓
  _rng = Random(seed)
  _state = None
  _ethics_callback = ethics_callback
  
  Initialize sub-engines:
    → _topology_manager = None (loaded on init_scenario)
    → _combat_resolver = CombatResolver(rng)
    → _economic_engine = EconomicEngine(rng)
    → _media_engine = MediaEngine(rng)
    → _precursor_engine = PrecursorEngine(rng)
    → _doctrine_engine = DoctrineEngine(rng)
    → _sentinel_engine = SentinelEngine(rng)
  
  Populate _EVENT_HANDLERS dict (33 handler functions)
```

### **2.2 Scenario Initialization**
```
engine.init_scenario(state=None, scenario_id="gumas_canonical_v2")
  ↓
  IF state is None:
    → build_default_scenario(scenario_id, seed) from scenarios.py
      └─ _build_canonical_factions() → 13 FactionState objects
      └─ _build_canonical_leaders() → 28 LeaderState objects
      └─ _build_initial_conflicts() → 3 ConflictState objects
      └─ _apply_faction_profiles() → apply trust matrix
      └─ build_canonical_topology() → GalaxyTopology
      └─ build_default_economy(factions) → EconomicState
      └─ build_default_media(factions) → MediaEcosystem
      └─ build_canonical_precursor_sites() → Dict[PrecursorSite]
      └─ build_default_operatives(factions) → Dict[SentinelOperative]
      └─ build_default_doctrines(factions) → Dict[DoctrineProfile]
      └─ _build_canonical_fleets() → 12 FleetState objects
      └─ _build_initial_culture_movements() → 4 CultureMovement objects
    
    → Return GUMASState(factions, leaders, conflicts, treaties, 
                        topology, fleets, economy, media, 
                        precursor_sites, operatives, doctrines, 
                        culture_movements, ...)
  
  ELSE:
    → Use provided state
  
  _state = state
  _tick_counter = 0
  _topology_manager = TopologyManager(state.topology) if state.topology else None
```

### **2.3 Single Tick Execution (15 Phases)**
```
engine.step() → TickResult
  ↓
  result = TickResult(turn=_state.turn, events_processed=[], ...)
  
  Phase 1: _process_event_queue(result)
    FOR event IN _state.event_queue:
      handler = _EVENT_HANDLERS[event.event_type]
      handler(event, result)  ← dispatch to 33 handlers
      result.events_processed.append(event)
  
  Phase 2: _update_leader_hooks(result)
    FOR faction IN _state.factions:
      leader = _get_faction_leader(faction.faction_id)
      IF leader:
        new_bias = calc_bias_evolution(leader.dominant_bias, ...)
        apply_bias_hooks(leader, faction, rng)
  
  Phase 3: _evaluate_conflicts(result)
    FOR conflict IN _state.conflicts:
      IF conflict.phase == OPEN_CONFLICT:
        deescalation_prob = calc_deescalation_probability(...)
        IF rand() < deescalation_prob:
          conflict.phase = RESOLUTION
  
  Phase 4: _evaluate_treaties(result)
    FOR treaty IN _state.treaties:
      IF treaty.is_active:
        breach_score = calc_treaty_breach_score(...)
        IF is_treaty_breach(breach_score, rng):
          treaty.breach_count[fid_a] += 1
          IF sum(breach_count) >= 3:
            treaty.phase = COLLAPSED
  
  Phase 5: _peacetime_recovery(result)
    FOR faction IN _state.factions:
      has_open_conflict = any(c.phase==OPEN_CONFLICT for c in conflicts if faction in c.parties)
      IF NOT has_open_conflict:
        faction.economic_strength = min(1.0, economic + 0.01)
        faction.population_stability = min(1.0, population + 0.01)
  
  Phase 6: _diplomacy_tick(result)
    FOR faction IN _state.factions:
      FOR other_faction IN faction.trust_scores:
        new_trust = calc_trust_update(trust, decay_factor=0.01, update=0)
        faction.trust_scores[other_faction] = new_trust
  
  Phase 7: _coalition_lifecycle(result)
    FOR coalition IN _state.coalitions:
      coalition.stability = max(0, stability - 0.02)
      IF stability < 0.3 OR rand() < 0.05:
        _dissolve_coalition(coalition.coalition_id, result)
  
  Phase 8: _fleet_movement_tick(result)
    FOR fleet IN _state.fleets:
      IF fleet.movement_target AND fleet.movement_target != fleet.location_node:
        path = _topology_manager.get_path(fleet.location_node, fleet.movement_target)
        IF path AND len(path) > 1:
          fleet.location_node = path[1]
          supply_decay = calc_fleet_supply_decay(fleet.supply_level, fleet.strength, rng)
          fleet.supply_level = max(0, fleet.supply_level - supply_decay)
          IF fleet.location_node == fleet.movement_target:
            fleet.movement_target = None
  
  Phase 9: _combat_resolution_tick(result)
    location_fleets = group fleets by (location, faction)
    FOR location, fleets_by_faction IN location_fleets.items():
      IF len(fleets_by_faction) > 1:
        FOR (faction_a, faction_b) IN pairs:
          outcome = _combat_resolver.resolve_battle(
            attacker_fleets=fleets_by_faction[faction_a],
            defender_fleets=fleets_by_faction[faction_b],
            topology_manager=_topology_manager
          )
          apply_fleet_losses(fleets_a, outcome["attacker_losses"])
          apply_fleet_losses(fleets_b, outcome["defender_losses"])
  
  Phase 10: _economic_tick(result)
    FOR faction IN _state.factions:
      faction.economic_strength = min(1.0, faction.economic_strength + 0.005)
  
  Phase 11: _media_tick(result)
    FOR narrative IN _state.media.active_narratives:
      faction = _state.factions[narrative.source_faction]
      leader = _get_faction_leader(narrative.source_faction)
      effectiveness = calc_propaganda_effectiveness(...)
      narrative.effectiveness = min(1.0, narrative.effectiveness + effectiveness * 0.05)
      legacy_impact = calc_media_legitimacy_impact(...)
      leader.public_legitimacy = clamp(leader.public_legitimacy + legacy_impact, 0, 1)
  
  Phase 12: _precursor_tick(result)
    FOR site IN _state.precursor_sites:
      IF site.discovery_phase == DETECTED:
        activation_risk = calc_precursor_activation_risk(...)
        IF rand() < activation_risk:
          site.discovery_phase = PARTIALLY_ACTIVATED
          site.activation_turn = _tick_counter
  
  Phase 13: _sentinel_tick(result)
    FOR operative IN _state.operatives:
      operative.experience = min(1.0, operative.experience + 0.001)
    
    FOR mission IN _state.missions:
      IF NOT mission.is_complete:
        operative = _state.operatives[mission.assigned_operative]
        success_prob = calc_mission_success_probability(
          operative.experience, mission.difficulty, operative.rank, rng
        )
        IF rand() < success_prob:
          mission.is_complete = True
          mission.outcome = "success"
          operative.missions_completed += 1
  
  Phase 14: _doctrine_tick(result)
    FOR doctrine IN _state.doctrines:
      new_q = calc_q_learning_update(
        doctrine.q_table,
        action=list(doctrine.q_table.keys())[0],
        ...
      )
      doctrine.q_table = new_q
  
  Phase 15a: _culture_tick(result)
    FOR movement IN _state.culture_movements:
      spread = calc_culture_spread_rate(movement.influence, len(movement.spread_factions), rng)
      movement.influence = min(1.0, movement.influence + spread)
  
  Phase 15b: _generate_emergent_events(result)
    rand_val = rng.random()
    IF rand_val < 0.15:  # destructive_weight
      event_type = choice([MILITARY_ESCALATION, ECONOMIC_SHOCK, INTELLIGENCE_LEAK, ...])
      severity = 0.6 + rand() * 0.4
    ELIF rand_val < 0.50:  # constructive_weight
      event_type = choice([TRADE_AGREEMENT, ECONOMIC_BOOM, TECHNOLOGY_BREAKTHROUGH, ...])
      severity = 0.2 + rand() * 0.4
    ELSE:  # balanced_weight
      event_type = choice([DIPLOMATIC_OVERTURE, TREATY_PROPOSAL, DOCTRINE_SHIFT, ...])
      severity = 0.3 + rand() * 0.4
    
    faction_ids = list(_state.factions.keys())
    source_faction = choice(faction_ids)
    target_faction = choice([f for f in faction_ids if f != source_faction])
    
    event = SimulationEvent(
      event_id=_make_event_id(),
      event_type=event_type,
      turn=_state.turn,
      source_faction=source_faction,
      target_faction=target_faction,
      severity=severity,
      parameters={}
    )
    _state.event_queue.append(event)
    result.events_generated.append(event)
  
  _state.turn += 1
  _tick_counter += 1
  _state.history.append(result)
  
  RETURN result
```

---

## 3. EVENT HANDLER MATRIX (33 HANDLERS)

### **v1.0 Handlers (17)**
| Event Type | Handler Function | Primary Action | State Changes |
|---|---|---|---|
| MILITARY_ESCALATION | `_handle_military_escalation` | Escalate conflict phase | conflict.phase, war_cost |
| DIPLOMATIC_OVERTURE | `_handle_diplomatic_overture` | Boost trust, enable mediation | trust_scores, mediation |
| ESPIONAGE_EXPOSURE | `_handle_espionage_exposure` | Reduce trust (asymmetric) | trust_scores, stability |
| ECONOMIC_SHOCK | `_handle_economic_shock` | Reduce target's economy | economic_strength, shock |
| LEADER_CHANGE | `_handle_leader_change` | Replace leader with new bias | leader_id, bias shift |
| TREATY_PROPOSAL | `_handle_treaty_proposal` | Create treaty if conditions met | treaties (new) |
| TREATY_VIOLATION | `_handle_treaty_violation` | Increment breach count | breach_count, reputation |
| INTELLIGENCE_LEAK | `_handle_intelligence_leak` | Reduce institutional control | institutional_control |
| HUMANITARIAN_CRISIS | `_handle_humanitarian_crisis` | Reduce population/legitimacy | population_stability |
| TECHNOLOGY_BREAKTHROUGH | `_handle_technology_breakthrough` | Boost technology + military/econ | technology_level |
| CULTURAL_MOVEMENT | `_handle_cultural_movement` | Boost population stability | population_stability |
| INTERNAL_COUP | `_handle_internal_coup` | Trigger coup or cascade to leader_change | population_stability → LEADER_CHANGE |
| MEDIATION_OFFER | `_handle_mediation_offer` | Accept mediation if trust sufficient | mediation_available, mediator_id |
| TRADE_AGREEMENT | `_handle_trade_agreement` | Boost both factions' economy + trust | economic_strength, trust |
| ECONOMIC_BOOM | `_handle_economic_boom` | Boost economy + legitimacy | economic_strength, legitimacy |
| INFRASTRUCTURE_INVESTMENT | `_handle_infrastructure_investment` | Boost economy + legitimacy | economic_strength, legitimacy |
| CUSTOM | `_handle_custom` | Apply custom deltas (params-driven) | parameterized |

### **v2.0 Handlers (16)**
| Event Type | Handler Function | Primary Action | State Changes |
|---|---|---|---|
| FLEET_MOVEMENT | `_handle_fleet_movement` | Set fleet movement target | fleet.movement_target |
| FLEET_BATTLE | `_handle_fleet_battle` | Resolve fleet combat at location | fleet.strength, losses |
| PRECURSOR_DISCOVERY | `_handle_precursor_discovery` | Mark site as DETECTED | site.discovery_phase |
| PRECURSOR_ACTIVATION | `_handle_precursor_activation` | Activate precursor site | site.discovery_phase, power_level |
| SENTINEL_MISSION | `_handle_sentinel_mission` | Create and assign new mission | missions (new) |
| CORPORATE_TAKEOVER | `_handle_corporate_takeover` | Reduce target's economy | economic_strength |
| MEDIA_CAMPAIGN | `_handle_media_campaign` | Create narrative campaign | media.active_narratives |
| DOCTRINE_SHIFT | `_handle_doctrine_shift` | Change faction's military doctrine | doctrine.current_doctrine |
| CULTURE_SPREAD | `_handle_culture_spread` | Expand culture to new faction | movement.spread_factions |
| RESOURCE_CRISIS | `_handle_resource_crisis` | Reduce economic strength | economic_strength |
| BLOCKADE | `_handle_blockade` | Severe economic impact on target | economic_strength |
| COUP_ATTEMPT | `_handle_coup_attempt` | Attempt coup (fleet support check) | cascade to LEADER_CHANGE or population hit |
| ALLIANCE_FORMATION | `_handle_alliance_formation` | Form coalition between factions | coalitions (new) |
| ALLIANCE_DISSOLUTION | `_handle_alliance_dissolution` | Remove coalition | coalitions (delete) |
| SANCTIONS_IMPOSED | `_handle_sanctions_imposed` | Reduce target economy | economic_strength |
| SANCTIONS_LIFTED | `_handle_sanctions_lifted` | Restore target economy | economic_strength |

---

## 4. STATE TRANSITION DIAGRAMS

### **4.1 ConflictPhase Transitions**
```
PEACE → TENSION → ESCALATION → OPEN_CONFLICT
                               ↓
                          STALEMATE
                               ↓
                        DEESCALATION
                               ↓
                          CEASEFIRE
                               ↓
                        NEGOTIATION
                               ↓
                          RESOLUTION

Triggers:
  - PEACE → TENSION: _find_conflict() returns null, create new ConflictState(phase=TENSION)
  - TENSION → ESCALATION: military_escalation event or escalate_conflict()
  - ESCALATION → OPEN_CONFLICT: _escalate_conflict() called
  - OPEN_CONFLICT → RESOLUTION: deescalation_probability check passes
  - RESOLUTION → DEESCALATION: automatic transition
  - DEESCALATION → CEASEFIRE: treaty acceptance or mediation success
```

### **4.2 TreatyPhase Transitions**
```
NONE → CEASEFIRE_TALKS → BARGAINING → INTERNAL_PRESSURE
                                            ↓
                                      RATIFICATION
                                            ↓
                                      MONITORING
                                            ↓
                                      VIOLATED
                                            ↓
                                      COLLAPSED

Triggers:
  - NONE → CEASEFIRE_TALKS: treaty_proposal event generated
  - Breach detection: breach_count[faction] += 1, reputation_impact -= 0.1
  - COLLAPSED: sum(breach_count.values()) >= 3
```

### **4.3 DiscoveryPhase Transitions (Precursor Sites)**
```
DORMANT → DETECTED → INVESTIGATED → PARTIALLY_ACTIVATED → FULLY_ACTIVATED
                                            ↓
                                      WEAPONIZED
                                            ↓
                                      CONTAINED

Triggers:
  - DETECTED: _handle_precursor_discovery()
  - PARTIALLY_ACTIVATED: rand() < activation_risk in _precursor_tick()
  - FULLY_ACTIVATED: _handle_precursor_activation()
  - WEAPONIZED: implicit (not shown in handlers, but in schema)
  - CONTAINED: implicit (not shown in handlers, but in schema)
```

### **4.4 CoalitionLifecycle**
```
FORM → STABLE (while stability > 0.3)
    ↓
    DISSOLVE (if stability < 0.3 OR rand() < 0.05)
    
Triggers:
  - FORM: _form_coalition() called (alliance_formation event)
  - DISSOLVE: _coalition_lifecycle() automatic dissolution check
  - Stability decay: coalition.stability -= 0.02 per tick
```

---

## 5. DEPENDENCY HIERARCHY

### **5.1 Import Tree (engine.py)**
```
engine.py
  ├─ formulas.py (32 calculation functions)
  │   ├─ apply_bias_hooks
  │   ├─ calc_bias_evolution
  │   ├─ calc_coalition_stability
  │   ├─ calc_deescalation_probability
  │   ├─ calc_reputation_after_decay
  │   ├─ calc_treaty_breach_score
  │   ├─ calc_trust_update
  │   ├─ is_treaty_breach
  │   ├─ calc_combat_outcome
  │   ├─ calc_combat_losses
  │   ├─ calc_q_learning_update
  │   ├─ calc_bayesian_faction_decision
  │   ├─ calc_sentinel_adaptation
  │   ├─ calc_economic_equilibrium
  │   ├─ calc_trade_flow
  │   ├─ calc_corporate_capture_pressure
  │   ├─ calc_propaganda_effectiveness
  │   ├─ calc_media_legitimacy_impact
  │   ├─ calc_precursor_activation_risk
  │   ├─ calc_precursor_power_output
  │   ├─ calc_mission_success_probability
  │   ├─ calc_culture_spread_rate
  │   ├─ calc_fleet_supply_decay
  │   ├─ calc_war_exhaustion
  │   └─ _clamp
  │
  ├─ models.py (28 dataclasses, 17 enums)
  │
  ├─ scenarios.py
  │   ├─ build_default_scenario()
  │   ├─ build_scenario_rotting_treaty()
  │   ├─ build_scenario_corporate_coup()
  │   ├─ build_scenario_ai_shadow_split()
  │   ├─ build_scenario_frontier_spark()
  │   └─ build_scenario_precursor_ping()
  │
  ├─ topology.py
  │   ├─ TopologyManager(rng)
  │   ├─ TopologyManager.get_path(from_node, to_node)
  │   └─ build_canonical_topology()
  │
  ├─ combat.py
  │   ├─ CombatResolver(rng)
  │   ├─ CombatResolver.resolve_battle(combat, attacker_fleets, defender_fleets, topology_manager)
  │   ├─ CombatResolver.resolve_combat(fid_a, fleets_a, fid_b, fleets_b, location)
  │   └─ CombatResolver.apply_fleet_losses(fleets, losses)
  │
  ├─ economics.py
  │   ├─ EconomicEngine(rng)
  │   ├─ build_default_economy(factions)
  │   └─ EconomicEngine methods (calc_trade_flows, apply_sanctions, etc.)
  │
  ├─ media.py
  │   ├─ MediaEngine(rng)
  │   ├─ build_default_media(factions)
  │   └─ MediaEngine methods
  │
  ├─ precursors.py
  │   ├─ PrecursorEngine(rng)
  │   ├─ build_canonical_precursor_sites()
  │   └─ PrecursorEngine methods
  │
  ├─ doctrine.py
  │   ├─ DoctrineEngine(rng)
  │   ├─ build_default_doctrines(factions)
  │   └─ DoctrineEngine methods (q_learning, adaptation)
  │
  └─ sentinels.py
      ├─ SentinelEngine(rng)
      ├─ build_default_operatives(factions)
      └─ SentinelEngine methods (mission generation, skill updates)
```

### **5.2 Subsystem Interactions**
```
engine.py (Main Orchestrator)
  ├─ topology.py ← used in fleet movement, path finding
  ├─ combat.py ← used in phase 9, fleet battle resolution
  ├─ economics.py ← used in phase 10, trade/market updates
  ├─ media.py ← used in phase 11, narrative propagation
  ├─ precursors.py ← used in phase 12, site discovery/activation
  ├─ doctrine.py ← used in phase 14, Q-learning updates
  ├─ sentinels.py ← used in phase 13, mission assignments
  │
  └─ formulas.py (shared calculation library)
      ├─ All subsystems call formulas for deterministic calculations
      └─ No circular dependencies (formulas.py imports nothing from other modules)

scenarios.py (Scenario Factory)
  ├─ imports from models.py (dataclasses)
  ├─ imports build_canonical_topology() from topology.py
  ├─ imports build_default_economy() from economics.py
  ├─ imports build_default_media() from media.py
  ├─ imports build_canonical_precursor_sites() from precursors.py
  ├─ imports build_default_operatives() from sentinels.py
  └─ imports build_default_doctrines() from doctrine.py
```

### **5.3 Critical Coupling Points**
1. **models.py** → No imports (data-only layer) — GOOD
2. **formulas.py** → No imports (pure functions) — GOOD
3. **engine.py** → imports all subsystems + models + formulas — HIGH COUPLING (expected, by design)
4. **scenarios.py** → imports multiple subsystem builders — MODERATE COUPLING
5. **Subsystems** → each imports models.py + formulas.py + topology.py — MODERATE COUPLING

---

## 6. DATA FLOW PATTERNS

### **6.1 Event Injection → Processing → State Update**
```
1. Event Creation:
   _generate_emergent_events(result)
   → Creates SimulationEvent(event_type, source_faction, target_faction, severity, ...)
   → Appends to _state.event_queue
   
2. Event Processing (Phase 1):
   _process_event_queue(result)
   → Dequeue event
   → Lookup handler in _EVENT_HANDLERS[event_type]
   → Call handler(event, result)
   
3. Event Handler:
   _handle_*() functions
   → Read faction/leader/conflict/treaty states
   → Calculate impacts using formulas
   → Modify _state directly (faction.economic_strength += delta)
   → Append state_change strings to result.state_changes
   → May cascade: create and inject new events to _state.event_queue

4. Result Accumulation:
   TickResult collects:
   → events_processed (events that ran)
   → events_generated (new events created during this tick)
   → state_changes (human-readable log of modifications)
   → ethics_flags (if ethics_callback was triggered)
```

### **6.2 Trust Score Asymmetry Pattern**
```
_adjust_trust(faction_a, faction_b, delta, result)
  
  IF delta < 0:  # Negative (distrust)
    effective_delta = delta (full strength)
  ELSE:  # Positive (trust building)
    effective_delta = delta * 0.6 (reduced, 60% strength)
  
  IF current_trust > 0.7 AND delta > 0:
    effective_delta *= (1.0 - (current_trust - 0.7) * 2)  # ceiling drag
  
  new_trust = clamp(current_trust + effective_delta, 0, 1)
  
Result: Distrust spreads fast, trust builds slowly.
```

### **6.3 Cascade Event Pattern**
```
Example: INTERNAL_COUP event

IF event.severity > 0.7:
  ✓ Coup success → create LEADER_CHANGE event with parameters={"post_coup": True}
  → Inject into _state.event_queue (will process on NEXT tick Phase 1)
ELSE:
  ✗ Coup failure → reduce leader.public_legitimacy by 0.1

This allows multi-tick orchestration of related events.
```

### **6.4 Coalition Stability Decay**
```
_coalition_lifecycle(result)
  
  FOR coalition IN _state.coalitions:
    coalition.stability = max(0, stability - 0.02)  # Always decay
    
    IF stability < 0.3 OR rand() < 0.05:  # Two dissolution paths
      → _dissolve_coalition(coalition.coalition_id, result)
      → Remove from _state.coalitions
      
Result: Coalitions are temporary; stability naturally erodes.
Threshold: 0.3 stability before natural dissolution.
Random: 5% chance to dissolve every tick (handles meta-stable states).
```

---

## 7. NAMING INTEGRATION (Phase 6.5 — FUTURE)

**Not yet fully implemented in engine.py**, but schema ready in API Reference v1.1:

```
Phase 6.5 Naming Resolution (placeholder):

  FOR each new referent created this tick:
    request = NameRequest(
      entity_type=PERSON|FACTION|TREATY|CONFLICT|SHIP|LOCATION|OPERATION,
      entity_id=unique_id,
      faction_context=faction_id,
      register=FORMAL|INFORMAL|CALLSIGN|BUREAUCRATIC,
      constraints={culture, class, origin cues}
    )
    
    resolution = name_service.resolve(request)
      → check hard collisions (exact match in scope)
      → check soft collisions (stem reuse, semantic dominance, cadence)
      → apply cooldowns (throttle overused stems)
      → generate candidate names
      → render formal + operational + display forms
    
    name_registry.register_name(resolution)
    emit state_change: f"name_minted[{entity_id}] = {resolution.canonical_name}"
```

**Current Status:** API spec complete, engine.py hooks not active.

---

## 8. ETHICS PROTOCOL (Picard_Delta_3)

**Integration Point:**
```python
IF self._ethics_callback:
  allowed = _check_ethics(action_type="military_escalation", params={...})
  IF NOT allowed:
    → Log ethics_flags
    → Prevent action (return early)
  ELSE:
    → Proceed with action
```

**Hook Locations:**
- Constructor: `GUMASEngine(ethics_callback=...)`
- All 33 event handlers: conditional check before applying deltas
- Global constraint checks (not visible in current engine.py, but Picard_Delta_3 implies it)

---

## 9. COMPLETE SUBSYSTEM SPECS

### **9.1 Topology Subsystem**
- **Responsible for:** Galactic navigation, spatial relationships, hyperlane network
- **Key Classes:** TopologyManager, TopologyNode, HyperlaneEdge, GalaxyTopology
- **Key Methods:**
  - `TopologyManager.get_path(from_node, to_node)` → List[str] (nodes in path)
  - Fleet movement uses this for pathfinding
- **Current Usage:** Phase 8 fleet movement, Phase 9 combat location checks
- **Coupling:** Tightly integrated with fleet operations

### **9.2 Combat Subsystem**
- **Responsible for:** Fleet-to-fleet battle resolution, casualty calculation
- **Key Classes:** CombatResolver, FleetState, CombatState, BattlefieldCondition
- **Key Methods:**
  - `resolve_battle(combat, attacker_fleets, defender_fleets, topology_manager)` → outcome dict
  - `apply_fleet_losses(fleets, losses)` → modifies fleet.strength in-place
- **Current Usage:** Phase 9 combat resolution
- **Coupling:** Moderately coupled (depends on topology for location context)

### **9.3 Economics Subsystem**
- **Responsible for:** Trade flows, market dynamics, sanctions, corporate influence
- **Key Classes:** EconomicEngine, MarketState, TradeRoute, EconomicState
- **Key Methods:** (not shown in engine.py; assumed in economics.py)
  - `calc_trade_flows(faction_a, faction_b, trade_route)` → economic boost
  - `apply_sanctions(sanctioner, target, duration)` → reduce economy
- **Current Usage:** Phase 10 economic growth, trade agreement events
- **Coupling:** Loosely coupled (receives faction state, modifies it)

### **9.4 Media Subsystem**
- **Responsible for:** Narrative campaigns, propaganda effectiveness, public opinion
- **Key Classes:** MediaEngine, MediaOutlet, NarrativeState, MediaEcosystem
- **Key Methods:** (not shown; assumed in media.py)
  - Propaganda effectiveness calculation
  - Legitimacy impact calculation
- **Current Usage:** Phase 11 media campaigns, narrative spread
- **Coupling:** Loosely coupled (affects leader legitimacy via formulas)

### **9.5 Precursor Subsystem**
- **Responsible for:** Ancient artifacts, discovery phases, activation mechanics
- **Key Classes:** PrecursorEngine, PrecursorSite, DiscoveryPhase, PrecursorOrigin
- **Key Methods:** (not shown; assumed in precursors.py)
  - `calc_precursor_activation_risk(tech_bonus, location, factions, rng)` → probability
  - `calc_precursor_power_output(tech_bonus, faction)` → power level
- **Current Usage:** Phase 12 precursor mechanics
- **Coupling:** Loosely coupled (affects tech_level and military_strength via events)

### **9.6 Sentinel Subsystem**
- **Responsible for:** Espionage missions, operative skill advancement, covert actions
- **Key Classes:** SentinelEngine, SentinelOperative, MissionState, SentinelRank
- **Key Methods:**
  - `calc_mission_success_probability(experience, difficulty, rank, rng)` → probability
- **Current Usage:** Phase 13 mission completion, operator advancement
- **Coupling:** Loosely coupled (creates missions, updates operative stats)

### **9.7 Doctrine Subsystem**
- **Responsible for:** Military Q-learning, doctrine adaptation, strategic learning
- **Key Classes:** DoctrineEngine, DoctrineProfile, DoctrineType
- **Key Methods:**
  - `calc_q_learning_update(q_table, state, reward, ...)` → new Q-values
- **Current Usage:** Phase 14 doctrine adaptation
- **Coupling:** Loosely coupled (updates doctrine Q-table)

---

## 10. FORMULAS LIBRARY (32 Functions)

**All deterministic, no side effects, pure functions:**

| Formula | Input | Output | Used In |
|---------|-------|--------|---------|
| `apply_bias_hooks` | leader, faction, rng | None | Phase 2 |
| `calc_bias_evolution` | bias, econ, stability, rng | BiasType | Phase 2 |
| `calc_coalition_stability` | trust_list, rng | float | Coalition formation |
| `calc_coalition_utility` | coalition, factions | float | Coalition decision |
| `calc_deescalation_probability` | stalemate, cost, openness_a, openness_b | float | Phase 3 |
| `calc_double_agent_risk` | operative, faction | float | Sentinel logic |
| `calc_reputation_after_decay` | reputation, decay_rate, turns | float | Treaties |
| `calc_treaty_breach_score` | bias_a, bias_b, terms, rng | float | Phase 4 |
| `calc_trust_update` | trust, decay_factor, update | float | Phase 6 |
| `is_treaty_breach` | breach_score, rng | bool | Phase 4 |
| `calc_combat_outcome` | fleet_a, fleet_b, condition | Dict | Phase 9 |
| `calc_combat_losses` | strength, outcome_ratio | float | Phase 9 |
| `calc_q_learning_update` | q_table, state, action, reward, ... | Dict | Phase 14 |
| `calc_bayesian_faction_decision` | evidence, prior, bias | float | Decision-making |
| `calc_sentinel_adaptation` | operative, mission_outcome | float | Phase 13 |
| `calc_economic_equilibrium` | supply, demand, sanctions | float | Phase 10 |
| `calc_trade_flow` | route_capacity, security, tariff | float | Economics |
| `calc_corporate_capture_pressure` | faction, mkt_influence | float | Corp events |
| `calc_propaganda_effectiveness` | narrative_type, legitimacy, stability, rng | float | Phase 11 |
| `calc_media_legitimacy_impact` | effectiveness, legitimacy | float | Phase 11 |
| `calc_precursor_activation_risk` | tech_bonus, location, factions, rng | float | Phase 12 |
| `calc_precursor_power_output` | tech_bonus, faction | float | Phase 12 |
| `calc_mission_success_probability` | experience, difficulty, rank, rng | float | Phase 13 |
| `calc_culture_spread_rate` | influence, spread_count, rng | float | Phase 15a |
| `calc_fleet_supply_decay` | supply_level, strength, rng | float | Phase 8 |
| `calc_war_exhaustion` | war_pressure, losses, morale | float | Conflict |
| `_clamp` | value, min, max | float | Everywhere |

---

## 11. IDENTIFIED REFACTORING SEAMS (For FORGE MODE)

### **Seam 1: Handler Dispatch Bottleneck**
- **Issue:** All 33 handlers hardcoded in `_EVENT_HANDLERS` dict in `__init__`
- **Opportunity:** Extract into pluggable handler registry or interface
- **Benefit:** Easier to add/remove handlers, decouple handler logic from engine

### **Seam 2: Phase Monolith**
- **Issue:** All 15 phases hardcoded in `step()` method as sequential calls
- **Opportunity:** Extract phase execution to phase objects or registry
- **Benefit:** Dynamic phase ordering, easy phase insertion/removal, testability

### **Seam 3: Tight Coupling to formulas.py**
- **Issue:** engine.py directly calls 32 formula functions with specific signatures
- **Opportunity:** Wrap formulas in calculation service interfaces
- **Benefit:** Easier testing, formula substitution, calculation logging

### **Seam 4: Subsystem Initialization**
- **Issue:** All 6 subsystems created in `__init__`, but topology loaded in `init_scenario`
- **Opportunity:** Unified subsystem initialization protocol
- **Benefit:** Consistency, testability, clear lifecycle

### **Seam 5: State Mutation in Handlers**
- **Issue:** Handlers directly modify `_state` (faction.economic_strength += delta)
- **Opportunity:** Use state delta objects / immutable updates
- **Benefit:** Auditability, undo/redo support, transaction semantics

### **Seam 6: Result Accumulation**
- **Issue:** result.state_changes is ad-hoc string list
- **Opportunity:** Structured StateChange objects with type, source, magnitude
- **Benefit:** Machine-readable auditing, L3 constraint checking

### **Seam 7: Trust Score Asymmetry Logic**
- **Issue:** Asymmetry encoded in `_adjust_trust()` with magic numbers (0.6, 0.7, 2)
- **Opportunity:** Extract to TrustDynamicsModel class with configurable parameters
- **Benefit:** Easy variation, clear trust physics, testability

### **Seam 8: Subsystem Independence**
- **Issue:** Combat, economics, media, precursor, sentinel, doctrine subsystems designed independently
- **Opportunity:** Define explicit interface contract for subsystems (input/output/side-effects)
- **Benefit:** Modular testing, subsystem swapping, clear boundaries

---

## 12. METRICS & COMPLEXITY

| Metric | Value | Status |
|--------|-------|--------|
| Core Engine Lines | ~1,100 (engine.py) | Manageable |
| Event Handlers | 33 | Comprehensive |
| Tick Phases | 15 | Well-organized |
| Enums Defined | 17 | Extensive |
| Dataclasses | 28 | Rich schema |
| Formulas | 32 | Calculation library |
| Scenario Variants | 6 | Diverse testing |
| Subsystems | 7 (engine + 6 sub) | Modular |
| Total Canonical Factions | 13 | Large-scale |
| Total Canonical Leaders | 28 | Deep characterization |
| Cyclomatic Complexity (engine.step) | ~15 | High (nested loops + conditionals) |
| Token Count (engine.py) | ~3,500 | Large module |

---

## 13. COMPLETENESS CHECKLIST

- ✅ **API Spec:** 100% (v1.1 complete 2026-02-09)
- ✅ **Engine Implementation:** 100% (v2.0 complete with all 15 phases + 33 handlers)
- ✅ **Models:** 100% (28 dataclasses, full v1.0 + v2.0 coverage)
- ✅ **Scenarios:** 100% (6 variants, 13 factions, 28 leaders, canonical setup)
- ✅ **Formulas:** 100% (32 functions, all phases covered)
- ✅ **Topology:** ⚠️ PARTIAL (TopologyManager exists, details not shown)
- ✅ **Combat:** ⚠️ PARTIAL (CombatResolver exists, logic not shown)
- ✅ **Economics:** ⚠️ PARTIAL (EconomicEngine exists, logic not shown)
- ✅ **Media:** ⚠️ PARTIAL (MediaEngine exists, logic not shown)
- ✅ **Precursors:** ⚠️ PARTIAL (PrecursorEngine exists, logic not shown)
- ✅ **Sentinels:** ⚠️ PARTIAL (SentinelEngine exists, logic not shown)
- ✅ **Doctrine:** ⚠️ PARTIAL (DoctrineEngine exists, logic not shown)
- ⚠️ **Naming Integration:** Draft (Phase 6.5 not active in engine.py)
- ⚠️ **Tests:** Minimal (only test_gumas_integration_v1_1.py visible)
- ❌ **CI/CD Pipeline:** Not visible
- ❌ **Deployment Docs:** Missing

---

## 14. NEXT STEPS FOR FORGE MODE

**Ready for FORGE MODE decomposition:**

1. Extract **Phase Executor** abstraction
2. Extract **Handler Registry** (event dispatch)
3. Extract **Subsystem Interfaces** (clear contracts)
4. Extract **Formula Service** (calculation orchestration)
5. Extract **State Mutation Layer** (auditability)
6. Extract **Scenario Factory** (separation)
7. Flatten **Tight Coupling** (topology, combat in handlers)
8. Implement **Missing Tests** (all 33 handlers, all 15 phases)

**Estimated refactoring effort:** 2-3 days for full decomposition + test coverage.

---

END DEEP PARSE REPORT
