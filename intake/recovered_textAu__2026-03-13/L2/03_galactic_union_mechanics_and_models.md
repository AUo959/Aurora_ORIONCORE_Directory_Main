# Galactic Union Mechanics And Models

Layer: L2  
Status: STAGING / conceptual  
Primary source spans: `intake/textAu.txt:87-166`, `375-1437`

## Scope

This document gathers the recovered simulation mechanics into one organized L2 reference.
It preserves the design intent while stripping out conversational filler and repeated
"memory updated" claims.

## Core Simulation Categories

The recovery consistently organizes the simulation around these domains:

- governance and faction structure
- political and diplomatic memory
- military doctrine and war strategy
- economics and technological progression
- event-driven history storage
- character-level decision modeling

That six-part frame is the clearest structural contribution of the early material.

## Core Formulas Recovered

### Political support

```text
P(support) = ideological_alignment + political_ambition - risk_assessment
```

### Event pressure

```text
event_trigger = P(scientific_breakthrough) + P(economic_collapse) + P(civil_war)
```

### Loyalty

```text
political_loyalty = ideological_alignment - past_betrayals + personal_relationships
```

### Diplomatic trust update

```text
T_new = T_old - lambda(betrayal_penalty) + delta(alliance_gain)
```

### Sentinel adaptation

```text
S_new = S_old + alpha(successes) - beta(failures)
```

### Reinforcement-style doctrine update

```text
Q(s, a) = Q(s, a) + alpha * (R + gamma * max_a'(Q(s', a')) - Q(s, a))
```

## Major Mechanics Families

### Faction decision-making

The recovery repeatedly returns to a memory-aware faction model:

- faction action depends on current scenario plus retrieved historical context
- betrayal history raises the odds of future betrayal
- weakness increases the odds of negotiation
- PMCs use profit-weighted risk rather than ideology

### Diplomatic memory

Diplomacy is modeled as durable rather than disposable:

- betrayals have long tails
- alliances build trust slowly
- reputation is a state variable, not just prose

### Combat resolution

The recovered battle model is a weighted comparison of:

- fleet strength
- tactical adaptation
- AI or strategic superiority
- battlefield conditions

Cleaned expression:

```text
W = (FS_U * TA_U * AS_U * BC) / (FS_E * TA_E * AS_E * BC)
```

The exact formula is simplistic as written, but the design intent is clear: battles should
turn on doctrine and conditions, not raw unit counts alone.

### Sentinel learning

Sentinel-class forces are treated as special operators that improve through mission outcome
history and degrade under repeated failure.

### War doctrine evolution

The recovery wants doctrine to shift through feedback:

- failed frontal assaults should push factions toward asymmetric methods
- successful cyberwarfare should increase future cyber preference
- learning happens at the doctrine layer, not only at the unit layer

### Economic and trade logic

Recovered economic signals include:

- supply and demand equilibrium
- wartime manufacturing pressure
- resource pipeline shifts
- contractor pricing under elevated risk
- sanctions and post-war trade realignment

## Non-War Progression Refinements

One of the strongest recovered design corrections is the explicit move away from war-only
simulation. The recovery argues that most major events in a healthy cycle should be:

- diplomatic
- scientific
- economic
- cultural

Key non-war mechanics proposed:

- Diplomatic Stability Index (DSI)
- economic booms and recessions without automatic conflict
- cultural movements as galaxy-shaping events
- technological revolutions with social and ethical consequences
- exploration and anomaly research as cooperation drivers
- soft power through education, science, and institutions

Recovered stability model:

```text
DSI = (political_unity + economic_prosperity + social_cohesion) / (corruption + militarization)
```

Recovered growth model:

```text
GDP_growth = resource_wealth + innovation - disruptive_forces
```

Recovered peace-weight model:

```text
P_stability = economic_health + technological_progress - corruption
```

## Memory Optimization Concepts

The source also proposes a storage logic for long-running simulations:

- tiered memory: core, dynamic, archived
- decay of low-impact events
- event-triggered recall instead of full log retention
- summarized diplomacy and battle history
- macro-trend compression for politics and economics
- tiered intelligence retention for espionage and covert operations

Recovered formulas include:

```text
M_faction = B + alpha * R + beta * I + gamma * P
```

```text
D = exp(-lambda * t) * M_event
```

```text
P_recall = (E_impact * T_relevance) / (D_decay + C)
```

```text
M_intelligence = (L_importance * A_relevance) / (T_decay + S)
```

These should be treated as concept notes, not final implementation formulas.

## Mechanics That Appear To Have Later Echoes

The current engine already reflects some of this thinking at a higher level:

- trust and treaty systems
- bias-driven leadership behavior
- constructive, destructive, and balanced event generation
- culture, precursor, doctrine, and media subsystems
- multi-faction topology and coalition logic

That does not prove direct one-to-one implementation, but it does make this recovery
important as design lineage.

## Recommendations

- keep this document as a design-reference layer, not a source of truth for exact equations
- reuse the non-war progression section when balancing scenario generation
- keep the memory-optimization section adjacent to L3 engineering docs rather than folding
  it into hard canon
