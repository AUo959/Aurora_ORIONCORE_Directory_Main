# PARAMETERS TO NARRATIVE ENGINE

## Core Specification

**Version:** 0.1\
**Date:** 2026-04-12

---

## Overview

### Working Purpose

Design an engine that can accept heterogeneous inputs, recover or receive layered structure, normalize that structure into a canonical internal model, and then either:

1. **generate** narrative expressions from that model, or
2. **validate** proposed narrative moves against that model.

This is not a prompt wrapper, nor is it merely a story generator. It is a narrative reasoning system.

### Core Equation

**heterogeneous input → structural recovery → canonical state model → narrative expression / narrative validation**

A shorter mnemonic:

**signal → meaning → state → story**

---

## Design Principles

### 1. Input Agnosticism

The engine must function from almost any input type:

- raw data
- notes
- maps
- historical summaries
- novels
- transcripts
- scenario fragments
- worldbuilding materials
- a single sentence
- a proposed next event

No single input format is privileged.

### 2. Layer Awareness Without Layer Dependence

The engine must be able to:

- operate with explicit layered user input
- infer latent layers when layers are not provided
- merge declared and inferred layers without flattening either

### 3. Scale Invariance

The engine must work across radically different scales:

- substrate level: geology, climate, resources, orbital conditions
- system level: institutions, trade networks, military structure, ecology
- human level: motives, loyalties, fears, incentives, identities
- event level: conflicts, discoveries, betrayals, reversals
- scene level: moments, actions, choices, symbols

### 4. Structural Honesty

Sparse inputs must remain sparse unless they are responsibly expanded. The engine should distinguish between:

- explicit support
- structural inference
- archetypal inference
- stylized extrapolation

### 5. Coherence Preservation

Narrative outputs must preserve:

- causal continuity
- temporal continuity
- spatial continuity
- character continuity
- world continuity
- consequence continuity
- thematic continuity
- knowledge continuity

### 6. Bidirectionality

The engine should support both:

- **forward generation**: state → narrative
- **reverse tracing**: narrative element → underlying causes and constraints

---

## Primary Operating Modes

### A. Expansion Mode

Used when the system is asked to build narrative space.

Typical questions:

- What civilization might arise here?
- What kind of conflict follows from these conditions?
- Expand this one-line prompt into an arc.
- What myths would emerge from this environment?

#### Expansion Objective

Move from partial or structured input into a larger but coherent narrative possibility space.

### B. Validation Mode

Used when the system is asked to evaluate a proposed narrative move.

Typical questions:

- Would this action make sense for this character?
- Is this event historically plausible?
- Can this be the next scene?
- Does this betrayal fit the established arc?

#### Validation Objective

Compare a proposed action, event, or development against the current canonical state model and return a reasoned verdict.

### C. Translation Mode

Used when converting one representational form into another without losing structural logic.

Examples:

- raw data → scenario narrative
- novel passage → structural model
- setting notes → civilization sketch
- scene fragment → inferred tensions and branch points
- historical account → generalized scenario archetype

---

## Input Handling Model

Every input should be processed through these stages.

### 1. Intake Classification

Determine what kind of thing the input is.

Possible modes:

- structured data
- semi-structured notes
- prose narrative
- dialogue or transcript
- worldbuilding fragment
- scene seed
- proposed action or event
- mixed-source bundle

### 2. Evidence Density Assessment

Estimate how much reliable structure is present.

Possible levels:

- minimal
- sparse
- moderate
- rich
- dense

### 3. Layer Detection

Determine whether layers are:

- explicitly declared by the user
- implicitly detectable
- missing
- conflicting
- mixed

### 4. Extraction Strategy Selection

Choose extraction behavior based on input class and evidence density.

Examples:

- dataset → state and trend extraction
- novel chapter → entities, motives, events, tone, symbolic cues
- sentence fragment → minimal structural seed with high uncertainty
- historical summary → institutions, logistics, constraints, event chain

---

## Layer Protocol

The engine maintains two parallel structures.

### Declared Layers

What the user explicitly states.

### Recovered Layers

What the engine directly extracts from the source material.

### Inferred Layers

What the engine derives by structural reasoning when the source or the user has not made something explicit.

The engine then compares these.

### Possible Relationships Between Layers

- aligned
- complementary
- underspecified
- disconnected
- in tension
- contradictory

### Rule

Declared layers should be preserved unless the user explicitly requests reinterpretation. Recovered layers may connect, pressure-test, or expose gaps in the declared model, but they should not casually overwrite it.

---

## Canonical State Model

This is the normalized internal representation that all inputs should resolve into as far as possible.

### 1. Entities

Anything with identity or persistence.

Examples:

- characters
- factions
- cultures
- institutions
- cities
- ecosystems
- technologies
- symbolic objects

#### Fields

- identifier
- type
- scale
- persistence
- salient traits
- current condition

### 2. Relations

How entities connect.

Examples:

- kinship
- alliance
- rivalry
- dependence
- hierarchy
- trade linkage
- symbolic association

#### Fields

- source
- target
- relation type
- strength
- directionality
- stability

### 3. Pressures

Forces acting on entities or systems.

Examples:

- scarcity
- invasion threat
- succession instability
- guilt
- social shame
- ecological collapse
- ideological contradiction

#### Fields

- pressure type
- affected entities
- intensity
- duration
- direction
- source

### 4. Constraints

What limits or shapes possible action.

Examples:

- geography
- law
- oath
- supply limits
- custom
- weather window
- social taboo
- ignorance

#### Fields

- constraint type
- scope
- severity
- enforceability
- duration

### 5. Motives

What actors want or are driven by.

Examples:

- ambition
- duty
- revenge
- survival
- belonging
- piety
- curiosity
- fear of disgrace

#### Fields

- actor
- motive type
- priority
- stability
- visibility to others

### 6. Events

Discrete happenings or transitions.

Examples:

- coronation
- flood
- betrayal
- migration
- treaty
- revelation
- duel

#### Fields

- event type
- participants
- trigger
- consequences
- temporal position
- certainty

### 7. Temporal Position

Where something sits in sequence.

#### Fields

- order
- duration
- recurrence
- pacing relevance
- dependencies

### 8. Knowledge Distribution

Who knows what, when, and how reliably.

#### Fields

- knower
- proposition
- certainty
- acquisition source
- timing

### 9. Symbolic Load

Narrative or civilizational meaning attached to entities, events, places, or actions.

Examples:

- sacred mountain
- cursed bloodline
- road as fate
- sea as judgment

#### Fields

- symbol carrier
- meaning cluster
- cultural scope
- stability
- interpretive variance

### 10. Uncertainty

What remains missing, underdetermined, or contested.

#### Fields

- unknown area
- ambiguity class
- candidate interpretations
- confidence level

---

## Provenance and Status Tags

Every recovered element should carry both a source tag and a status tag.

### Source Tag

- user\_declared
- directly\_extracted
- structurally\_inferred
- archetypally\_inferred
- stylized\_extrapolation

### Status Tag

- explicit
- derived
- provisional
- contested
- unknown

This keeps the engine adaptable without pretending all details are equally grounded.

---

## Expansion Operator Library

Expansion operators are the controlled transformations the engine may use.

### 1. Derivation Operators

Move from condition to implication.

Examples:

- geology → resource distribution
- scarcity → competition
- isolation → local identity formation
- succession ambiguity → factional maneuvering

### 2. Constraint Operators

Identify what is limited, forced, blocked, or shaped.

Examples:

- mountain barrier → communication limits
- oath → behavior restriction
- storm season → campaign limits

### 3. Pressure Operators

Turn static state into dynamic tension.

Examples:

- low food reserve + rising population → social strain
- divided loyalty + urgent threat → internal conflict

### 4. Agency Operators

Generate actor roles appropriate to the state field.

Examples:

- chokepoint economy → brokers, toll lords, smugglers
- ritualized catastrophe → prophets, skeptics, engineer-priests
- frontier volatility → scouts, raiders, mediators

### 5. Event Operators

Convert pressure into happenings.

Examples:

- prolonged drought → migration wave, hoarding, revolt
- dynastic uncertainty → coup, regency, pretender claim

### 6. Symbolic Operators

Map repeated realities into narrative meaning.

Examples:

- annual flood → cosmology
- road bifurcation → fate or choice symbolism
- island fragmentation → myths of separation and reunion

### 7. Rendering Operators

Select output form without changing the underlying state.

Examples:

- the same state rendered as a scene
- the same state rendered as a myth
- the same state rendered as a strategic brief
- the same state rendered as a character arc note

---

## Directional Moves

Operators can be used in different directions.

### Upward Expansion

substrate → system → culture → character → event → scene

### Downward Compression

scene fragment → motive or conflict structure → world implications

### Outward Expansion

one state node → adjacent systems and consequences

### Inward Refinement

broad condition → intimate, local, character-level manifestation

### Reverse Tracing

generated or proposed narrative move → underlying supporting causes

---

## Validation Framework

Validation mode evaluates a proposal against the canonical state model.

### Validation Targets

- character action
- event plausibility
- historical plausibility
- continuity of the next move
- symbolic fit
- pacing fit
- world-logic fit

### Validation Axes

#### 1. Motivation Coherence

Does this action fit the actor’s current motives, fears, loyalties, and pressures?

#### 2. World Plausibility

Does this event fit the physical, logistical, social, and institutional conditions?

#### 3. Continuity Integrity

Does the proposal follow from prior events without breaking established sequence or consequence?

#### 4. Knowledge Validity

Is the proposed action based on information the actor plausibly has?

#### 5. Setup Sufficiency

Has enough groundwork been established for this move to feel earned?

#### 6. Thematic Compatibility

Does the move fit or meaningfully challenge the narrative’s established symbolic and thematic pattern?

#### 7. Scale Consistency

Is this proposal appropriate to the current level of abstraction and scope?

---

## Verdict Language

The engine should avoid flat yes-or-no responses whenever richer adjudication is possible.

### Preferred Verdict Set

- **supported**
- **plausible**
- **possible with setup**
- **strained**
- **contradictory**

### Verdict Naming Note

In prose, use **possible with setup**. In structured payloads and schema fields, use `possible_with_setup`.

### Optional Supplements

- what supports the verdict
- what weakens the verdict
- what must be added to strengthen it
- what alternative next moves are more natural

---

## Example Applications

### 1. Planetary Substrate to Civilization

**Input:**

- unstable tectonics
- mineral-rich mountain chains
- narrow coastal plains
- frequent storms

**Possible engine path:**

- derive fragmented settlement and maritime adaptation
- infer chokepoint trade and local defensive cultures
- generate ritual systems around disaster and navigation
- render civilization types, myths, hero roles, and conflict patterns

### 2. Minimal Constraint to Arc Space

**Input:**

- “a hero came to a fork in the road”

**Possible engine path:**

- identify choice-point structure
- infer branching obligation and consequence pressure
- expand into a scene, parable, symbolic hinge, or broader world divergence

### 3. Author Motivation Audit

**Input:**

- character profile
- current scene state
- proposed betrayal

**Engine task:**

- check motive stack, emotional timing, knowledge state, and recent pressures
- return whether the betrayal is supported, possible with setup, strained, or contradictory

### 4. Historical Fiction Plausibility

**Input:**

- location, period, factional situation, proposed event

**Engine task:**

- check logistics, institutions, communications, technology, geography, and social norms
- return a plausibility verdict with caveats

### 5. Next-Event Continuity Check

**Input:**

- current narrative state
- proposed next beat

**Engine task:**

- assess causal continuity, emotional continuity, knowledge continuity, pacing, and consequence alignment
- identify whether the event is natural now, premature, or incoherent

---

## Minimal Viable Engine

A first working version should support the following.

### Intake

- sentence fragment
- prose passage
- structured notes
- parameter bundle
- proposed action or event

### Internal Core

- entity extraction
- motive extraction
- pressure extraction
- constraint extraction
- event sequence tracking
- uncertainty tagging
- provenance tagging

### Output Modes

- scene expansion
- world or civilization expansion
- character action validation
- next-event validation
- plausibility commentary

### Verdicts

- supported
- plausible
- possible with setup
- strained
- contradictory

---

## Immediate Build Priorities

### Priority 1: Canonical Schema

Lock the minimum state model fields and tags.

### Priority 2: Layer Protocol

Define how declared layers and inferred layers coexist.

### Priority 3: Operator Library v1

Create the smallest reusable set of expansion operators.

### Priority 4: Validation Engine

Define the checks, verdict rules, and explanation structure.

### Priority 5: Interaction Patterns

Design standard user queries and expected output templates.

---

## Working Thesis

This engine is best understood as a narrative reasoning instrument that:

- accepts almost any meaningful input
- recovers or receives structure from that input
- normalizes it into a coherent internal state model
- either expands that state into narrative space or validates narrative moves against it

Its purpose is not simply to write stories.\
Its purpose is to preserve and adjudicate narrative reality.

---

# CANONICAL SCHEMA V1

## Strict Field Form

This section defines the minimum normalized representation the engine should use internally.

### Schema Design Rules

1. Every object must carry a stable identifier.
2. Every object must carry provenance and confidence.
3. Every object may be partial. Missing fields should remain null or unknown rather than being silently invented.
4. Declared and inferred content must be distinguishable.
5. Layer membership must be explicit.
6. Temporal position must be attachable to any persistent or eventful object where relevant.

---

## Root State Object

```json
{
  "state_id": "string",
  "state_version": "string",
  "input_profile": {
    "input_mode": "structured_data | notes | prose_narrative | transcript | worldbuilding_fragment | scene_seed | proposed_action | mixed_bundle",
    "evidence_density": "minimal | sparse | moderate | rich | dense",
    "layer_mode": "declared | recovered | mixed | unknown"
  },
  "layers": [],
  "entities": [],
  "relations": [],
  "pressures": [],
  "constraints": [],
  "motives": [],
  "events": [],
  "knowledge_states": [],
  "symbolic_loads": [],
  "uncertainties": [],
  "continuity": {},
  "narrative_context": {},
  "provenance_log": []
}
```

---

## Common Metadata Block

Every recoverable object should include this metadata shape.

```json
{
  "id": "string",
  "layer": "physical | ecological | social | institutional | political | economic | cultural | symbolic | character | event | scene | multi | unknown",
  "source_tag": "user_declared | directly_extracted | structurally_inferred | archetypally_inferred | stylized_extrapolation",
  "status_tag": "explicit | derived | provisional | contested | unknown",
  "confidence": 0.0,
  "evidence_refs": ["string"],
  "notes": "string | null"
}
```

### Metadata Notes

- `confidence` is not truth. It is a handling signal about support strength.
- `evidence_refs` should point to source spans, source objects, or input fragments when available.
- `layer` may be `multi` when an object genuinely spans domains.

---

## Layer Object

```json
{
  "id": "layer_001",
  "name": "Political Layer",
  "layer_type": "political",
  "origin": "declared | recovered",
  "description": "string",
  "related_object_ids": ["string"],
  "relationship_to_other_layers": [
    {
      "target_layer_id": "string",
      "relation": "aligned | complementary | underspecified | disconnected | in_tension | contradictory",
      "notes": "string | null"
    }
  ],
  "confidence": 0.0,
  "evidence_refs": ["string"]
}
```

---

## Entity Object

```json
{
  "id": "entity_001",
  "label": "string",
  "entity_type": "character | faction | institution | city | culture | ecosystem | technology | artifact | location | abstract_force | unknown",
  "scale": "micro | local | regional | civilizational | planetary | unknown",
  "persistence": "momentary | recurring | persistent | structural | unknown",
  "salient_traits": ["string"],
  "current_condition": ["string"],
  "temporal_position": {
    "start": "string | null",
    "end": "string | null",
    "sequence_index": "number | null"
  },
  "metadata": {}
}
```

### Entity Minimum Requirement

At minimum, an entity needs:

- id
- label
- entity\_type
- metadata

---

## Relation Object

```json
{
  "id": "relation_001",
  "source_entity_id": "string",
  "target_entity_id": "string",
  "relation_type": "kinship | alliance | rivalry | dependence | hierarchy | trade | control | symbolic_association | spatial_link | unknown",
  "strength": 0.0,
  "directionality": "undirected | source_to_target | bidirectional | asymmetrical | unknown",
  "stability": "fragile | situational | durable | structural | unknown",
  "active": true,
  "metadata": {}
}
```

---

## Pressure Object

```json
{
  "id": "pressure_001",
  "pressure_type": "scarcity | invasion_threat | succession_instability | shame | grief | ecological_stress | ideological_conflict | time_pressure | unknown",
  "affected_object_ids": ["string"],
  "source_object_ids": ["string"],
  "intensity": 0.0,
  "duration": "momentary | short | extended | chronic | unknown",
  "direction": "rising | stable | falling | cyclical | unknown",
  "description": "string",
  "metadata": {}
}
```

---

## Constraint Object

```json
{
  "id": "constraint_001",
  "constraint_type": "geography | law | oath | supply_limit | taboo | weather_window | ignorance | injury | institution | unknown",
  "scope": "individual | group | system | environmental | unknown",
  "affected_object_ids": ["string"],
  "severity": 0.0,
  "enforceability": "soft | social | legal | physical | absolute | unknown",
  "duration": "momentary | seasonal | ongoing | structural | unknown",
  "description": "string",
  "metadata": {}
}
```

---

## Motive Object

```json
{
  "id": "motive_001",
  "actor_entity_id": "string",
  "motive_type": "ambition | duty | revenge | survival | belonging | piety | curiosity | fear_of_disgrace | love | unknown",
  "priority": 0.0,
  "stability": "volatile | situational | durable | core | unknown",
  "visibility_to_others": "hidden | partially_visible | visible | public | unknown",
  "conflicts_with": ["string"],
  "description": "string",
  "metadata": {}
}
```

---

## Event Object

```json
{
  "id": "event_001",
  "event_type": "coronation | flood | betrayal | migration | treaty | revelation | duel | decision_point | unknown",
  "participant_ids": ["string"],
  "trigger_ids": ["string"],
  "consequence_ids": ["string"],
  "precondition_ids": ["string"],
  "temporal_position": {
    "sequence_index": "number | null",
    "relative_phase": "setup | escalation | hinge | aftermath | unknown",
    "duration": "instant | scene | episode | extended | unknown"
  },
  "certainty": 0.0,
  "description": "string",
  "metadata": {}
}
```

### Event Notes

- `trigger_ids` may point to pressures, constraints, motives, or prior events.
- `consequence_ids` may point to new events, changed pressures, broken relations, or state updates.

---

## Knowledge State Object

```json
{
  "id": "knowledge_001",
  "knower_entity_id": "string",
  "proposition": "string",
  "certainty": 0.0,
  "acquisition_source": "observed | told | inferred | suspected | institutional_record | unknown",
  "timing": {
    "sequence_index": "number | null",
    "relative_to_event_id": "string | null"
  },
  "metadata": {}
}
```

---

## Symbolic Load Object

```json
{
  "id": "symbol_001",
  "carrier_object_id": "string",
  "meaning_cluster": ["string"],
  "cultural_scope": "personal | local | factional | civilizational | transhistorical | unknown",
  "stability": "emergent | unstable | durable | canonical | unknown",
  "interpretive_variance": "low | medium | high | unknown",
  "description": "string",
  "metadata": {}
}
```

---

## Uncertainty Object

```json
{
  "id": "uncertainty_001",
  "unknown_area": "identity | motive | timeline | causality | world_condition | symbolism | logistics | continuity | unknown",
  "affected_object_ids": ["string"],
  "ambiguity_class": "missing | underdetermined | conflicting | low_support | interpretive_opening | unknown",
  "candidate_interpretations": ["string"],
  "recommended_handling": "leave_open | infer_cautiously | request_input | branch_multiple | block_validation | unknown",
  "metadata": {}
}
```

---

## Continuity Object

This object stores the active continuity conditions for validation.

```json
{
  "causal_continuity": {
    "status": "stable | stressed | broken | unknown",
    "notes": "string | null"
  },
  "temporal_continuity": {
    "status": "stable | compressed | ambiguous | broken | unknown",
    "notes": "string | null"
  },
  "spatial_continuity": {
    "status": "stable | ambiguous | broken | unknown",
    "notes": "string | null"
  },
  "character_continuity": {
    "status": "stable | stressed | broken | unknown",
    "notes": "string | null"
  },
  "knowledge_continuity": {
    "status": "stable | asymmetric | broken | unknown",
    "notes": "string | null"
  },
  "thematic_continuity": {
    "status": "stable | evolving | fractured | unknown",
    "notes": "string | null"
  },
  "consequence_continuity": {
    "status": "stable | delayed | missing | broken | unknown",
    "notes": "string | null"
  }
}
```

---

## Narrative Context Object

This object stores rendering and interpretive context without contaminating the underlying state model.

```json
{
  "current_mode": "expansion | validation | translation | mixed",
  "requested_output_form": "scene | arc | myth | briefing | audit | commentary | unknown",
  "tone_profile": ["string"],
  "genre_frame": ["string"],
  "historical_frame": "string | null",
  "scale_focus": "substrate | system | character | event | scene | mixed | unknown",
  "user_constraints": ["string"]
}
```

---

## Provenance Log Entry

```json
{
  "id": "prov_001",
  "object_id": "string",
  "operation": "declared | extracted | inferred | expanded | validated | revised",
  "method": "string",
  "input_refs": ["string"],
  "notes": "string | null"
}
```

---

## Minimum Viable Population Rules

A usable state model does not require every array to be populated.

### Minimal Scene Seed

A state may be valid with only:

- one entity
- one event or implied decision point
- one uncertainty
- narrative\_context

### Minimal Character Audit

A state may be valid with only:

- one character entity
- one or more motives
- one proposed event
- one continuity object

### Minimal World Seed

A state may be valid with only:

- one environmental or structural entity
- one or more pressures or constraints
- one uncertainty block

This preserves sparse-input usability.

---

## State Hygiene Rules

1. Never upgrade `stylized_extrapolation` into `directly_extracted` later without explicit replacement.
2. Never erase uncertainty just because a fluent narrative can be written.
3. Do not collapse symbolic meaning into material causality or vice versa; both may coexist.
4. Do not let rendering preferences mutate the underlying world model.
5. Validation verdicts must cite the specific objects they rely on.

---

# LAYER PROTOCOL V1

## Explicit Rules

This protocol defines how the engine handles layered input when layers are:

- explicitly declared by the user
- recovered from source material
- inferred by structural reasoning
- mixed or partially conflicting

The aim is to keep layered reasoning usable without allowing layer confusion, silent overwrite, or uncontrolled invention.

---

## Layer Protocol Objectives

The layer protocol must ensure that the engine can:

1. operate from explicit layered user input
2. operate when no layers are given
3. operate when some layers are given and others must be recovered
4. preserve distinctions between material, social, symbolic, character, and event logic
5. expose tensions across layers without flattening them

---

## Core Rule

**The engine may connect layers, infer missing links between layers, and pressure-test relationships across layers, but it may not silently overwrite explicitly declared layers unless the user explicitly requests reinterpretation or revision.**

This is the governing rule.

---

## Layer Sources

Each layer in the model must carry an origin.

### Allowed Origins

- `declared` — explicitly provided by the user
- `recovered` — directly extracted from input material
- `inferred` — produced by engine reasoning from available structure

### Operational Meaning

- `declared` has priority as stated input
- `recovered` has priority as evidentiary structure found in source material
- `inferred` is the most flexible and the most constrained; it exists to connect and extend, not to impersonate evidence

---

## Layer Precedence Rules

When tensions arise, precedence should be handled by object class, not by engine confidence alone.

### Rule 1: Declared User Layer Priority

If the user explicitly declares a layer, that declaration remains authoritative as input.

The engine may:

- connect it to other layers
- identify implications
- identify tension with recovered material
- mark it as underspecified

The engine may not:

- replace it with a different layer claim
- “correct” it implicitly
- dissolve it into a more convenient interpretation

### Rule 2: Recovered Layer Priority Over Inference

If a layer is directly recoverable from the provided material, recovered structure outranks purely inferred structure.

**Example:**\
If a novel chapter explicitly shows divided loyalties, the engine should not replace that with a cleaner inferred loyalty map just because the latter is tidier.

### Rule 3: Inference Is Connective, Not Sovereign

Inferred layers are used to:

- bridge gaps
- expose consequences
- generate possibilities
- create provisional scaffolding

They are not used to erase declared or recovered structure.

---

## Layer Relationships

Each layer-to-layer relationship should be classified explicitly.

### Relationship Types

- `aligned`
- `complementary`
- `underspecified`
- `disconnected`
- `in_tension`
- `contradictory`

### Meanings

#### aligned

The layers mutually support the same state picture.

#### complementary

The layers address different aspects of the same state and fit together without strain.

#### underspecified

One or both layers are too thin to establish a strong relation.

#### disconnected

The layers exist but currently show no clear operational link.

#### in\_tension

The layers can coexist, but their coexistence generates meaningful strain.

#### contradictory

The layers cannot both be true in the same current state without revision, branching, or explicit uncertainty marking.

---

## Allowed Cross-Layer Moves

The engine may perform the following moves.

### 1. Upward Moves

From lower or deeper layers to higher or more human-readable layers.

Examples:

- geology → settlement structure
- settlement structure → trade dependency
- trade dependency → political rivalry
- political rivalry → character burden

### 2. Downward Moves

From surface narrative material into deeper structural implications.

Examples:

- scene hesitation → motive conflict
- public ritual → symbolic order
- betrayal → prior pressure and relation strain

### 3. Lateral Moves

Across layers of similar depth but different domains.

Examples:

- political layer ↔ symbolic layer
- ecological layer ↔ economic layer
- character layer ↔ social layer

### 4. Bridge Moves

Introduce an inferred linking structure between layers that do not yet connect clearly.

Examples:

- geography and myth connected through recurring seasonal catastrophe
- institutional law and character fear connected through punishment norms

### Rule

Every bridge move must be marked as inferred unless directly supported.

---

## Forbidden Layer Behaviors

The engine must not perform the following.

### 1. Silent Overwrite

Do not replace a declared or recovered layer with an inferred one without making the change explicit.

### 2. Layer Collapse

Do not reduce one layer entirely to another when both are materially active.

Examples:

- do not treat symbolic meaning as nothing but propaganda by default
- do not treat material pressure as irrelevant because symbolic rhetoric is vivid

### 3. Layer Bleed

Do not let one layer’s vocabulary masquerade as another layer’s evidence.

Examples:

- a mythic framing does not by itself prove logistics
- a logistics report does not by itself explain symbolic resonance

### 4. Exhaustive Pretending

Do not behave as if missing layers are fully known merely because adjacent layers are rich.

Example: A rich character layer does not automatically yield a rich institutional layer.

---

## Mixed Input Protocol

Many useful inputs will be mixed.

**Example mixed bundle:**

- user declares political and symbolic layers
- source text provides character and event material
- the engine infers economic and social linkages

In mixed mode, the engine should process in this order.

### Step 1: Register Declared Layers

Store all user-declared layers as explicit inputs.

### Step 2: Recover Available Layers

Extract layers that are directly present in the source material.

### Step 3: Map Relations Among Existing Layers

Determine whether the current layers are aligned, complementary, underspecified, disconnected, in tension, or contradictory.

### Step 4: Infer Missing Bridge Layers Cautiously

Only infer new layers when needed for coherence, expansion, or validation.

### Step 5: Tag All New Material by Origin and Confidence

Do not let inferred bridges become invisible.

---

## Missing Layer Protocol

When one or more expected layers are absent, the engine should not panic and should not overfill the gap.

### Missing Layer Handling Options

- `leave_open`
- `infer_cautiously`
- `branch_multiple`
- `block_specific_validation`
- `request_input` when interaction allows it

### Rule

The handling choice depends on task type.

#### For expansion tasks

Missing layers may often be bridged provisionally.

#### For validation tasks

Missing layers may require stronger restraint. A motivation audit with no motive data should not pretend to certainty. A continuity check with no timeline should not give a confident verdict.

---

## Contradiction Protocol

When layers contradict, the engine should not smooth over the contradiction.

### Allowed Responses to Contradiction

- mark contradiction explicitly
- preserve both claims as contested
- branch the state into alternate models
- identify the minimum revision needed to reconcile them

### Contradiction Example

- declared symbolic layer: “the kingdom stands for sacred unity”
- recovered political layer: provinces are openly defiant and semi-autonomous

**Correct response:**

- mark these as `in_tension` or `contradictory`, depending on framing
- do not erase either
- identify a possible reconciliation: sacred unity as ideological claim despite political fragmentation

---

## Layer Integrity by Task Type

Different tasks allow different levels of layer aggressiveness.

### Expansion Mode

May tolerate more inferred bridge structure, as long as provenance remains visible.

### Validation Mode

Must be stricter. Validation requires identifiable support from relevant layers. If a required layer is absent, the verdict should weaken accordingly.

### Translation Mode

Must preserve source-layer distinctions while moving between forms. A translated strategic brief should not silently lose the symbolic layer if it materially affects action.

---

## Required Layer Sets by Common Use Case

These are not absolute requirements, but they indicate which layers are usually load-bearing.

### Character Motivation Audit

Load-bearing layers:

- character
- event
- motive
- knowledge
- continuity

### Historical Plausibility Check

Load-bearing layers:

- physical or geographic
- institutional
- political
- economic or logistical
- temporal

### Civilization Emergence Build

Load-bearing layers:

- physical
- ecological
- economic
- social
- symbolic

### Next-Event Continuity Check

Load-bearing layers:

- event
- temporal
- character
- knowledge
- consequence continuity

### Symbolic Resonance Analysis

Load-bearing layers:

- symbolic
- event
- cultural or social
- character or civilizational identity

### Rule

If a load-bearing layer is absent, the engine must say so in the analysis or verdict.

---

## Layer Confidence Rules

Confidence should be assessed per layer and per relationship, not only globally.

### High Confidence

- the layer is explicitly declared by the user
- or it is directly recoverable from source material

### Medium Confidence

- strong structural inference with multiple supporting signals

### Low Confidence

- weak or sparse inference
- archetypal expansion with limited direct support

### Rule

A vivid render should not raise confidence by itself. Fluency is not evidence.

---

## Cross-Layer Audit Questions

For each substantial output, the engine should be able to answer some or all of these:

1. Which layers are explicit?
2. Which layers are recovered?
3. Which layers are inferred?
4. Which layer relationships are load-bearing here?
5. Are any key layers missing?
6. Are any layers in tension or contradiction?
7. Did any inferred bridge materially shape the output?
8. What would change if one layer were revised?

These questions make the engine inspectable.

---

## Minimal Layer Contract for Output

Any serious engine output should preserve, internally or visibly, at least this information:

- active layers used
- origin of those layers
- any major inferred bridges
- any unresolved layer gaps
- any major tensions or contradictions

This prevents the engine from presenting a clean narrative built on hidden structural guesswork.

---

## Layer Protocol Summary

The engine is allowed to reason across layers, but not to flatten them. It is allowed to infer missing bridges, but not to disguise those bridges as evidence. It is allowed to expose contradiction, but not to dissolve contradiction for convenience.

In short:

**preserve declared structure, recover present structure, infer missing structure cautiously, and keep all cross-layer moves legible.**

---

# OPERATOR LIBRARY V1

## Reusable Transformation Mechanics

This library defines the standard transformation operators the engine may use to move from input structure to expanded narrative space or to reverse-trace narrative moves back to supporting structure.

Each operator should specify:

- what it consumes
- what it produces
- what directional moves it supports
- how speculative it is
- when restraint is required

The purpose of the operator library is to make expansion disciplined, reusable, and inspectable.

---

## Operator Fields

Each operator can be described in the following form.

```json
{
  "operator_id": "string",
  "name": "string",
  "class": "derivation | constraint | pressure | agency | event | symbolic | rendering | continuity | branching | reverse_trace",
  "consumes": ["string"],
  "produces": ["string"],
  "direction": ["upward | downward | lateral | outward | inward | reverse"],
  "support_level": "direct | structural | archetypal | stylized",
  "requires": ["string"],
  "forbidden_when": ["string"],
  "notes": "string | null"
}
```

---

## Operator Table

| Operator                    | Class          | Consumes                                                        | Produces                                                                          | Directions                | Typical Support Level    | Use Case                                            | Restraint Rule                                                                       |
| --------------------------- | -------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------- | ------------------------ | --------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Substrate Derivation        | derivation     | physical or environmental conditions                            | resources, mobility patterns, habitability, settlement pressures                  | upward, outward           | direct to structural     | geology or climate to civilization seeds            | Do not jump directly from terrain to named cultural specifics without bridge layers  |
| System Derivation           | derivation     | institutions, economy, ecology, logistics                       | systemic implications, dependencies, stress points                                | upward, lateral, outward  | structural               | polity or society modeling                          | Keep causal chains explicit; do not compress multiple invisible steps                |
| Constraint Projection       | constraint     | entities, settings, laws, geography, vows, injuries             | blocked options, narrowed possibility space, forced tradeoffs                     | upward, downward, inward  | direct to structural     | “what cannot happen” checks                         | Constraints must remain active until explicitly changed                              |
| Pressure Formation          | pressure       | constraints, scarcity, conflict, contradiction, delay           | dynamic tension, urgency, strain, risk accumulation                               | outward, upward, inward   | structural               | converting static state into dramatic energy        | Avoid inventing pressure where no scarcity, conflict, or contradiction exists        |
| Pressure Escalation         | pressure       | existing pressures over time                                    | intensified stakes, instability, probable rupture points                          | upward, outward, temporal | structural               | conflict growth and crisis modeling                 | Requires temporal continuity; do not escalate instantaneously without cause          |
| Agency Emergence            | agency         | pressures, constraints, social roles, environments              | actor-types, role opportunities, burden-bearing positions                         | upward, inward            | structural to archetypal | generating hero roles, institutions, intermediaries | Create roles before highly specific identities unless identities are already present |
| Motive Inference            | agency         | actions, stated goals, relational stakes, fears, context        | probable motive stack, motive conflict, priority ordering                         | downward, inward, reverse | structural               | author audits and character modeling                | Mark clearly when inferred from behavior rather than declared by text or user        |
| Relation Formation          | derivation     | entities, co-presence, dependencies, conflict patterns          | alliances, rivalries, kinship, dependence, hierarchy                              | lateral, outward          | direct to structural     | building social and political meshes                | Avoid overstating relation strength from a single weak signal                        |
| Event Triggering            | event          | pressure, motive, relation strain, constraints, opportunities   | plausible event candidates                                                        | upward, outward, inward   | structural               | “what happens next” generation                      | Proposed events must reference active triggers, not only style or genre expectation  |
| Event Consequence Mapping   | event          | events, participants, prior state                               | downstream effects, changed relations, new pressures, aftermath                   | outward, upward, reverse  | structural               | continuity tracking                                 | Consequences should persist until resolved; do not evaporate them for convenience    |
| Decision Expansion          | branching      | decision point, actor, constraints, motives                     | branch options, tradeoffs, divergent paths                                        | outward, inward           | structural to archetypal | fork-in-the-road prompts                            | Branches must differ meaningfully in cost, value, or consequence                     |
| Branch Pruning              | branching      | candidate branches, constraints, continuity, plausibility       | narrowed possible next-event space                                                | inward, reverse           | structural               | validation and scenario reduction                   | Do not preserve branches that violate known hard constraints                         |
| Symbolic Crystallization    | symbolic       | recurring event patterns, places, objects, burdens, rituals     | symbolic meaning clusters, myths, identity motifs                                 | upward, lateral           | structural to archetypal | myth generation, resonance analysis                 | Do not treat symbolism as mandatory if repetition or interpretation support is weak  |
| Symbolic Translation        | symbolic       | material pattern plus cultural interpretation                   | symbolic framing linked to state conditions                                       | lateral, upward           | structural               | connecting logistics to myth or identity            | Preserve the difference between symbolic reading and physical cause                  |
| Scale Descent               | continuity     | broad systems, civilizations, wars, ideologies                  | localized scenes, individuals, concrete manifestations                            | inward, downward          | structural               | turning world logic into scenes                     | Maintain linkage to higher-level state; do not create isolated vignettes             |
| Scale Ascent                | continuity     | scenes, fragments, actions, symbols                             | broader arc, system implication, culture pattern                                  | upward, outward           | structural to archetypal | inferring larger meaning from fragments             | Signal ambiguity when small samples do not warrant broad claims                      |
| Temporal Sequencing         | continuity     | events, durations, dependencies, knowledge timing               | ordered chain, pacing logic, next-valid windows                                   | forward, reverse          | direct to structural     | continuity and next-event checks                    | Do not allow events to rely on knowledge or conditions not yet established           |
| Knowledge Propagation       | continuity     | events, observers, institutions, secrecy, transmission paths    | who knows what, when, and how reliably                                            | outward, reverse          | structural               | dramatic irony, plausibility, continuity            | Do not spread information magically across the state model                           |
| Setup Sufficiency Check     | continuity     | proposed event or action, prior signals, motives, foreshadowing | whether the move is earned, premature, or unsupported                             | reverse                   | structural               | writer advisory use cases                           | A vivid twist is not sufficient setup                                                |
| Plausibility Envelope Check | continuity     | proposal plus relevant world layers                             | support range: supported, plausible, possible-with-setup, strained, contradictory | reverse                   | direct to structural     | historical fiction, world logic, timeline checks    | Must cite the specific load-bearing layers used                                      |
| Reverse Trace               | reverse\_trace | scene, event, symbol, action, cultural claim                    | supporting causes, missing supports, hidden dependencies                          | reverse, downward         | structural               | explanation and debugging                           | Prefer the shortest sufficient chain over maximal explanation                        |
| Rendering Selection         | rendering      | normalized state model plus requested form                      | scene, arc note, myth, briefing, audit, commentary                                | presentation only         | direct                   | output shaping                                      | Must not mutate the underlying state model                                           |
| Tone Framing                | rendering      | narrative context, genre frame, tone profile                    | stylistic framing of the same state                                               | presentation only         | stylized                 | genre-sensitive output                              | Tone cannot overrule continuity or plausibility                                      |

---

## Operator Class Notes

### Derivation Operators

These move from conditions to implications. They are most useful when building from physical, ecological, political, or institutional substrate.

### Constraint Operators

These identify what is blocked, forced, narrowed, or made costly. They are essential for both expansion and validation because they define the shape of possibility.

### Pressure Operators

These turn static state into dynamic instability. They are often the bridge between background conditions and narrative movement.

### Agency Operators

These create actors, roles, motive structures, and burden-bearing positions appropriate to the current state. They should prefer role formation before highly specific identity invention.

### Event Operators

These convert pressure and motive into happenings and track consequences through the state model. They are central to continuity logic.

### Symbolic Operators

These connect repeated realities to meaning, ritual, memory, and myth. They should preserve the distinction between interpretation and causation.

### Continuity Operators

These maintain sequence, consequence, setup, and knowledge integrity. They are heavily load-bearing for writer advisory use cases.

### Branching Operators

These generate and then narrow nearby possibility space. They are especially useful for “what could happen next?” and “does this event fit here?” queries.

### Reverse Trace Operators

These walk backward from surface narrative elements to the deeper supports or missing supports underneath them. They are essential for explanation and debugging.

### Rendering Operators

These determine presentation layer only. They must never contaminate the canonical state model.

---

## Support Level Definitions

### direct

The operator relies on strong explicit signals or declared structure.

### structural

The operator relies on plausible implication chains from multiple grounded elements.

### archetypal

The operator extends from structural reality into recurring human or civilizational patterns.

### stylized

The operator is presentation-heavy and should be treated as the least evidentiary.

### Rule

Higher stylization does not imply lower value, but it does imply weaker evidentiary force.

---

## Operator Safety Rules

### 1. No Invisible Multi-Step Leaps

If an operator chain requires three hidden transitions, the engine should either surface them or weaken confidence.

### 2. No Genre-Only Logic

An event may not occur solely because it “feels right for the genre” if the state model does not support it.

### 3. No Style-Based Promotion

A beautifully rendered inference is still an inference. Fluency does not upgrade provenance.

### 4. Respect Task Strictness

Expansion mode may use broader operator chains. Validation mode must use stricter operator paths and identify missing supports.

### 5. Preserve Causal Legibility

Where possible, the engine should be able to say which operator chain produced a major output claim.

---

## Example Operator Chains

### A. Geology to Civilization

- Substrate Derivation
- Constraint Projection
- Pressure Formation
- Agency Emergence
- Symbolic Crystallization
- Rendering Selection

### B. Single Scene Fragment to Arc Possibility

- Scale Ascent
- Motive Inference
- Decision Expansion
- Event Triggering
- Branch Pruning
- Rendering Selection

### C. Character Action Audit

- Motive Inference
- Knowledge Propagation
- Setup Sufficiency Check
- Plausibility Envelope Check

### D. Historical Fiction Plausibility

- System Derivation
- Constraint Projection
- Temporal Sequencing
- Knowledge Propagation
- Plausibility Envelope Check

### E. “What Happens Next?” Query

- Event Consequence Mapping
- Temporal Sequencing
- Decision Expansion
- Branch Pruning
- Rendering Selection

---

## Minimal Operator Set for MVP

A first working implementation only needs a small, strong subset.

### MVP Operators

- Substrate Derivation
- Constraint Projection
- Pressure Formation
- Motive Inference
- Event Triggering
- Event Consequence Mapping
- Decision Expansion
- Branch Pruning
- Temporal Sequencing
- Knowledge Propagation
- Setup Sufficiency Check
- Plausibility Envelope Check
- Rendering Selection

This is enough to support:

- civilization emergence sketches
- scene expansion
- motivation audits
- next-event validation
- plausibility checks

---

## Operator Library Summary

The engine does not “expand” by vague creativity. It expands by applying a legible series of operators that transform one kind of structure into another.

In short:

**state becomes narrative through reusable transformations, not mystical leaps.**

---

# VALIDATION RULES V1

## Decision-Tree Adjudication

This section defines how the engine evaluates a proposed narrative move against the current canonical state model.

A proposed move may be:

- a character action
- a next event
- a scene transition
- a historical claim
- a worldbuilding assertion
- a symbolic interpretation

The engine should not reduce these to a flat yes or no whenever richer adjudication is possible. It should determine what kind of claim is being made, which layers are load-bearing, whether the state model is sufficient to judge it, and what verdict is warranted.

---

## Validation Objective

Validation is not merely contradiction detection. It is the process of determining whether a proposed move is:

- supported by the current state model
- plausible within it
- possible only with additional setup
- strained against it
- contradictory to it

This is the engine’s advisory core.

---

## Validation Inputs

A validation pass consumes:

1. the **current canonical state model**
2. a **proposal**
3. the **task frame**
4. the **relevant layer set**
5. the **current uncertainty profile**

### Proposal Object — Minimal Shape

```json
{
  "proposal_id": "proposal_001",
  "proposal_type": "character_action | next_event | scene_transition | historical_claim | symbolic_claim | world_assertion | mixed",
  "description": "string",
  "target_object_ids": ["string"],
  "claimed_effects": ["string"],
  "requested_strictness": "default | lenient | strict"
}
```

---

## Verdict Set

### supported

The proposal is directly backed by the current state model and does not require major unstated bridges.

### plausible

The proposal fits the current state model and is consistent with established conditions, though not tightly compelled.

### possible\_with\_setup

The proposal could work, but one or more missing supports, transitions, or enabling conditions need to be established.

### strained

The proposal is not impossible, but it pushes against the current state model in a way that will feel weak, abrupt, or under-argued unless revised.

### contradictory

The proposal conflicts with active constraints, established continuity, known motives, or other load-bearing state elements.

---

## Validation Output Shape

```json
{
  "proposal_id": "proposal_001",
  "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
  "task_frame": "string",
  "load_bearing_layers": ["string"],
  "supporting_object_ids": ["string"],
  "blocking_object_ids": ["string"],
  "missing_requirements": ["string"],
  "reasoning_path": ["string"],
  "confidence": 0.0,
  "notes": "string | null"
}
```

---

## Global Validation Decision Tree

Every validation pass should follow this sequence.

### Step 1: Classify the Proposal

What kind of thing is being judged?

Options include:

- character action
- next event
- continuity move
- world plausibility claim
- historical plausibility claim
- symbolic claim
- mixed proposal

### Step 2: Identify Load-Bearing Layers

Which layers must be consulted for this proposal type?

Examples:

- character action → character, motive, event, knowledge, continuity
- historical claim → physical, institutional, economic or logistical, temporal, political
- symbolic claim → symbolic, event, cultural or social, continuity

### Step 3: Check State Sufficiency

Are the required layers present with enough support to issue a meaningful verdict?

Possible outcomes:

- sufficient
- partially sufficient
- insufficient

### Step 4: Check Hard Blocks

Before nuanced judgment, check whether any active state elements flatly block the proposal.

Hard blocks may include:

- impossible timing
- impossible knowledge access
- absolute physical constraint
- direct contradiction with a declared fact
- unresolved prior consequence that prevents the proposal

### Step 5: Check Positive Supports

What in the state model actively supports the proposal?

Supports may include:

- declared motive alignment
- prior setup
- active pressure leading toward the move
- continuity of consequence
- relevant symbolic or social framing

### Step 6: Check Missing Bridges

Would the proposal work only if one or more additional state elements were established?

Examples:

- a betrayal needs more emotional setup
- a military movement needs more logistical preparation
- a revelation needs an information path

### Step 7: Determine Verdict

Map the support, block, and missing-bridge profile to one of the core verdicts.

### Step 8: Return Constructive Guidance

Where useful, explain:

- what supports the move
- what weakens it
- what would strengthen it
- what nearby alternatives are more natural

---

## State Sufficiency Rules

The engine must not overjudge thin inputs.

### sufficient

Relevant load-bearing layers are present and materially usable.

### partially\_sufficient

Some layers are present, but at least one important layer is sparse, inferred, or ambiguous.

### insufficient

One or more required layers are absent or too uncertain for a responsible verdict.

### Rule

If state sufficiency is insufficient, the engine may still offer:

- a provisional plausibility comment
- a list of missing requirements
- branch alternatives

But it should weaken confidence and avoid definitive judgment.

---

## Hard Block Rules

A hard block is a condition that prevents a verdict above `strained` and usually forces `contradictory` unless the proposal is explicitly reframed.

### Hard Block Categories

#### Physical Block

The world’s physical conditions make the proposal unworkable.

#### Temporal Block

The proposal depends on time that has not passed, on events that have not occurred, or on a broken sequence.

#### Knowledge Block

The actor does not plausibly know what the proposal requires them to know.

#### Constraint Block

An active rule, oath, law, injury, or other hard constraint prevents the move.

#### Continuity Block

A major unresolved consequence or prior event state makes the proposal incompatible.

#### Declared Fact Block

The proposal directly contradicts an explicit user-declared or source-recovered fact that remains active.

### Rule

A single hard block does not always force total rejection if the proposal can be reframed, but it must be surfaced explicitly.

---

## Positive Support Rules

Positive support is what lifts a proposal from merely imaginable to structurally grounded.

### Support Classes

- motive support
- continuity support
- setup support
- pressure support
- world support
- symbolic support
- precedent support

### Notes

A proposal can be plausible with only moderate support. A proposal should usually need strong support to be called supported.

---

## Missing Bridge Rules

A missing bridge is not a contradiction. It is a required but absent connective element.

### Common Missing Bridges

- motive escalation not yet shown
- relationship deterioration not yet established
- information acquisition path missing
- logistical preparation missing
- symbolic framing not yet earned
- time passage insufficiently represented
- consequence chain skipped

### Rule

If the move can work once the missing bridge is added, the usual verdict is `possible_with_setup`. If too many missing bridges are required, the verdict may degrade to `strained`.

---

## Verdict Mapping Rules

These rules are meant to be simple enough for implementation.

### supported

Use when:

- no hard blocks are active
- relevant layers are sufficient
- multiple positive supports exist
- no major missing bridge is required
- the move follows naturally from current continuity

### plausible

Use when:

- no hard blocks are active
- relevant layers are at least partially sufficient
- the proposal fits the state model
- support exists, but not enough to say the move is strongly prepared
- missing bridges are minor or optional

### possible\_with\_setup

Use when:

- no hard blocks are active
- the proposal can fit the state model
- one or more meaningful bridges are missing
- the move would work if setup were added explicitly

### strained

Use when:

- support is weak or thin
- important layers are sparse or ambiguous
- multiple bridges are missing
- the move pushes against continuity, motive, or plausibility even if it is not fully impossible

### contradictory

Use when:

- one or more hard blocks remain active without resolution
- the proposal directly breaks established continuity or declared fact
- the move depends on absent knowledge, impossible timing, or a negated constraint with no bridge supplied

---

## Decision Trees by Use Case

### A. Character Action Validation

**Question forms:**

- Would this character do this?
- Does this betrayal make sense?
- Would she forgive him here?

#### Required Layers

- character
- motive
- event
- knowledge
- continuity

#### Character Action Tree

1. Is the actor identified?
   - if no → insufficient state
2. Are active motives present or inferable?
   - if no → weaken verdict substantially
3. Does the action align with at least one high-priority motive or credible motive conflict?
   - if no → likely strained or contradictory
4. Does the actor have the knowledge required for the action?
   - if no → hard block
5. Has enough emotional or relational setup occurred?
   - if no → possible\_with\_setup or strained
6. Does the action violate active constraints or continuity?
   - if yes → contradictory unless bridged
7. Return verdict.

#### Typical Guidance Output

- what motive supports the action
- what emotional or relational setup is missing
- what earlier beat would make the action feel earned

---

### B. Next-Event Validation

**Question forms:**

- Can this happen next?
- Is this the right next beat?
- Does this scene follow?

#### Required Layers

- event
- temporal
- continuity
- knowledge
- consequence chain
- character, when agency matters

#### Next-Event Tree

1. Does the proposal follow from the immediately prior state?
2. Are unresolved consequences from prior events being ignored?
   - if yes → continuity block
3. Has enough time passed, if required?
   - if no → temporal block
4. Does the event require knowledge or positioning not yet established?
   - if yes → knowledge or spatial block
5. Is the move a natural escalation, reversal, or hinge from current pressures?
   - if yes → support rises
6. Is connective tissue missing?
   - if yes → possible\_with\_setup
7. Return verdict.

#### Typical Guidance Output

- whether the move is natural now or premature
- what intermediate beat would bridge it
- what alternate next moves are more supported

---

### C. Historical Plausibility Validation

**Question forms:**

- Could this happen in this setting?
- Is this historically plausible?
- Would this institution act this way?

#### Required Layers

- physical or geographic
- institutional
- political
- economic or logistical
- temporal
- social or cultural, when relevant

#### Historical Plausibility Tree

1. Does the claim depend on geography, logistics, communications, or technology?
2. Are those conditions present and compatible?
   - if no → hard plausibility block
3. Does the proposal fit the institutional and political incentives?
   - if no → support weakens sharply
4. Does the timeline permit the event?
   - if no → temporal block
5. Does the claim violate established norms or structures without transitional explanation?
   - if yes → possible\_with\_setup, strained, or contradictory depending on severity
6. Return verdict.

#### Typical Guidance Output

- what makes the event plausible
- what logistical or institutional problem weakens it
- what adjustment would restore plausibility

---

### D. Symbolic Fit Validation

**Question forms:**

- Does this symbol work here?
- Is this mythic reading earned?
- Can this object carry this meaning now?

#### Required Layers

- symbolic
- event
- cultural or social
- continuity
- character or civilizational identity, when relevant

#### Symbolic Fit Tree

1. Has the carrier object, action, or place recurred enough to bear symbolic load?
2. Is there a cultural or narrative frame that can interpret it meaningfully?
3. Does the proposed symbolism resonate with established themes?
4. Is the symbolism explanatory, additive, or arbitrary decoration?
5. If the symbolism is beautiful but unsupported → strained rather than supported
6. Return verdict.

---

### E. World Assertion Validation

**Question forms:**

- Would this civilization emerge here?
- Could this faction exist under these conditions?
- Does this social order make sense?

#### Required Layers

- physical or substrate
- ecological or economic
- social or institutional
- symbolic, when culture claims are strong

#### World Assertion Tree

1. Are the substrate and resource conditions compatible with the claim?
2. Do the institutions or social structures have plausible supports?
3. Are there missing bridge layers between environment and culture?
4. Is the proposal overspecified relative to available evidence?
   - if yes → weaken verdict or split into a supported core plus speculative details
5. Return verdict.

---

## Confidence Rules for Validation

Confidence depends on both support quality and state sufficiency.

### Raise confidence when:

- relevant layers are explicit or directly recovered
- multiple supports converge
- continuity is stable
- missing bridges are small

### Lower confidence when:

- key layers are inferred only
- required layers are missing or ambiguous
- the proposal depends on symbolic or archetypal expansion more than grounded state
- multiple branches remain viable

### Rule

Confidence must never exceed the least-supported load-bearing layer by too much. In practice, a verdict should not sound certain when its key supports are provisional.

---

## Constructive Response Rules

A useful validation output should usually include some combination of:

- the verdict
- the main supporting reasons
- the main blocking reasons
- the missing setup, if any
- the simplest revision that would improve support
- nearby alternative moves when the current one is weak

### Rule

Do not stop at “no.” Where possible, say what would make it work.

---

## Validation Style Rules

### 1. Distinguish “possible” from “earned”

Something can be mechanically possible but dramatically unsupported.

### 2. Distinguish “surprising” from “incoherent”

A good twist may look unlikely until the setup is traced properly.

### 3. Distinguish “historically rare” from “historically impossible”

Rare events may still be plausible with the right enabling conditions.

### 4. Distinguish “symbolically resonant” from “structurally grounded”

A strong symbol does not repair a broken continuity chain.

### 5. Distinguish “underexplained” from “contradictory”

Writers often need bridge diagnosis, not binary rejection.

---

## Minimal Validation Workflow for MVP

A first implementation only needs this path:

1. classify proposal
2. select load-bearing layers
3. check state sufficiency
4. detect hard blocks
5. collect supports
6. detect missing bridges
7. assign verdict
8. return a short reasoning trace

This is enough for:

- character action audits
- next-event checks
- historical plausibility checks
- civilization plausibility checks

---

## Validation Rules Summary

The engine validates by checking whether a proposal is supported by the state model, blocked by it, or merely underprepared within it.

In short:

**the engine does not ask only “can this happen?” it asks “what supports it, what blocks it, and what would make it feel true?”**

---

# INTERACTION TEMPLATES V1

## User-Facing Query and Response Patterns

This section defines how different user types interact with the engine in practice.

The goal is to ensure that the engine’s internal rigor becomes operationally useful. Different users ask different kinds of questions, provide different kinds of inputs, and need different output shapes.

The engine should therefore expose recognizable interaction templates rather than forcing every query into the same generic format.

---

## Interaction Design Objectives

The interaction layer should:

1. accept partial or rich inputs
2. identify the user’s real task
3. select the right operating mode
4. preserve uncertainty when input is thin
5. return outputs that match the user’s actual workflow

---

## Common Interaction Contract

Every interaction, regardless of user type, can be reduced to this pattern.

### User Supplies

- source input
- task request
- optional constraints
- optional desired output form
- optional desired strictness

### Engine Performs

- intake classification
- layer detection
- state population
- operator selection
- expansion and/or validation
- response rendering

### Engine Returns

- answer
- reasoning basis
- uncertainty or gaps
- next useful move, when appropriate

---

## Standard Query Envelope

A generalized query can be represented like this.

```json
{
  "user_type": "writer | worldbuilder | scenario_designer | analyst | mixed",
  "task_type": "expand | validate | translate | compare | branch | diagnose",
  "source_input": "string | object | bundle",
  "proposal": "string | null",
  "constraints": ["string"],
  "desired_output_form": "scene | arc_note | audit | world_sketch | branch_map | commentary | structured_report | unknown",
  "strictness": "default | lenient | strict"
}
```

---

## Writer Interaction Templates

Writers usually care about:

- character motivation
- next-event continuity
- scene plausibility
- symbolic resonance
- branch alternatives
- whether something feels earned

### Writer Template A — Character Action Audit

#### Typical Query Forms

- Would this character do this?
- Does this betrayal make sense?
- Would she forgive him here?
- Is this reaction believable?

#### Preferred Inputs

- character profile or prior behavior
- current scene or recent events
- proposed action
- optional emotional or thematic intention

#### Engine Mode

- validation

#### Load-Bearing Layers

- character
- motive
- event
- knowledge
- continuity

#### Preferred Output Shape

```json
{
  "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
  "why_it_tracks": ["string"],
  "what_weakens_it": ["string"],
  "what_setup_is_missing": ["string"],
  "smallest_fix": ["string"],
  "alternate_actions": ["string"]
}
```

#### Response Style

Direct, diagnostic, and non-performative. The engine should help the writer preserve surprise without sacrificing coherence.

---

### Writer Template B — Next Beat Check

#### Typical Query Forms

- Can this happen next?
- Is this the right next scene?
- What is the most natural next beat from here?

#### Preferred Inputs

- current narrative state or recent scene summary
- proposed next beat or a request for likely next beats

#### Engine Mode

- validation or branch generation

#### Preferred Output Shape

```json
{
  "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
  "naturalness_assessment": "string",
  "blocking_gaps": ["string"],
  "bridge_beats": ["string"],
  "most_supported_alternatives": ["string"]
}
```

#### Response Style

Sequence-aware and consequence-aware. It should distinguish “possible next” from “best next” and from “earned next.”

---

### Writer Template C — Symbolic Fit Check

#### Typical Query Forms

- Does this symbol work here?
- Is this image too on the nose?
- Can this object carry this meaning yet?

#### Preferred Inputs

- relevant object, scene, or recurring element
- proposed meaning
- recent thematic context

#### Engine Mode

- validation

#### Preferred Output Shape

```json
{
  "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
  "symbolic_supports": ["string"],
  "why_it_resonates_or_not": ["string"],
  "what_repetition_or_context_is_missing": ["string"],
  "subtler_variants": ["string"]
}
```

---

### Writer Template D — Scene Expansion

#### Typical Query Forms

- Expand this into a scene.
- Build a scene from this constraint.
- Render this state as a confrontation.

#### Preferred Inputs

- scene seed, line, event, or pressure field
- optional tone, genre, point of view, or scale preference

#### Engine Mode

- expansion

#### Preferred Output Shape

```json
{
  "scene_premise": "string",
  "active_pressures": ["string"],
  "actor_positions": ["string"],
  "probable_turn": ["string"],
  "scene_render": "string"
}
```

### Rule

When the writer asks for generation, the engine should still preserve structural logic beneath the surface.

---

## Worldbuilder Interaction Templates

Worldbuilders usually care about:

- emergence from substrate
- plausibility of institutions and cultures
- the relation between environment and civilization
- symbolic systems
- consistency across layers

### Worldbuilder Template A — Civilization Emergence

#### Typical Query Forms

- What kind of civilization would arise here?
- What societies emerge from these conditions?
- Build a culture from this planet.

#### Preferred Inputs

- environment, geography, ecology, resources, hazards
- optional desired scale or genre frame

#### Engine Mode

- expansion

#### Preferred Output Shape

```json
{
  "derived_pressures": ["string"],
  "likely_settlement_patterns": ["string"],
  "institutional_tendencies": ["string"],
  "cultural_or_symbolic_forms": ["string"],
  "hero_roles_or_conflict_types": ["string"],
  "world_sketch": "string"
}
```

---

### Worldbuilder Template B — World Logic Audit

#### Typical Query Forms

- Does this culture make sense under these conditions?
- Could this faction exist here?
- Is this social order plausible?

#### Preferred Inputs

- proposed culture, faction, or system
- relevant environmental, economic, institutional, or symbolic context

#### Engine Mode

- validation

#### Preferred Output Shape

```json
{
  "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
  "supporting_conditions": ["string"],
  "missing_bridges": ["string"],
  "layer_tensions": ["string"],
  "minimal_revisions": ["string"]
}
```

---

### Worldbuilder Template C — Layer Completion

#### Typical Query Forms

- I have the political and symbolic layers; what physical or economic layers are missing?
- Fill in the likely connective tissue here.

#### Preferred Inputs

- declared layers
- known facts
- optional request for strict or imaginative completion

#### Engine Mode

- translation plus expansion

#### Preferred Output Shape

```json
{
  "declared_layers": ["string"],
  "missing_or_thin_layers": ["string"],
  "inferred_bridge_layers": ["string"],
  "confidence_notes": ["string"],
  "recommended_next_specifications": ["string"]
}
```

### Rule

When completing worlds, inferred layers must remain visibly inferred.

---

## Scenario Designer Interaction Templates

Scenario designers usually care about:

- branching futures
- systemic reaction to conditions
- stress testing
- escalation paths
- generalized patterns from real or fictional cases

### Scenario Template A — Branch Map

#### Typical Query Forms

- What happens next from here?
- What are the most likely branches?
- Map the nearby possibility space.

#### Preferred Inputs

- current state summary
- optional proposal or focal actor or faction
- optional strictness level

#### Engine Mode

- branch generation plus pruning

#### Preferred Output Shape

```json
{
  "high_support_branches": ["string"],
  "conditional_branches": ["string"],
  "low_support_branches": ["string"],
  "blocked_branches": ["string"],
  "branch_drivers": ["string"]
}
```

---

### Scenario Template B — Scenario Plausibility Audit

#### Typical Query Forms

- Is this scenario internally plausible?
- Which part of this chain breaks first?
- Where is the weak link?

#### Preferred Inputs

- scenario chain or sequence of proposed developments
- environment, actors, constraints, and timing, if available

#### Engine Mode

- validation plus reverse trace

#### Preferred Output Shape

```json
{
  "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
  "strong_links": ["string"],
  "weak_links": ["string"],
  "hard_blocks": ["string"],
  "repair_options": ["string"],
  "critical_dependency": ["string"]
}
```

---

### Scenario Template C — Generalized Pattern Extraction

#### Typical Query Forms

- What generalized scenario does this historical case instantiate?
- Abstract this conflict into reusable narrative structure.

#### Preferred Inputs

- case summary, historical account, fictional arc, or event chain

#### Engine Mode

- translation

#### Preferred Output Shape

```json
{
  "case_specific_elements": ["string"],
  "structural_pattern": ["string"],
  "generalized_pressures": ["string"],
  "portable_scenario_form": "string",
  "potential_reapplications": ["string"]
}
```

---

## Mixed-Mode Interaction Templates

Many real uses combine expansion and validation.

### Mixed Template A — Expand Then Audit

#### Typical Query Form

- Build the next three likely directions, then tell me which one feels most earned.

#### Engine Mode

- branch generation → pruning → validation

#### Preferred Output Shape

```json
{
  "candidate_paths": ["string"],
  "comparative_support": ["string"],
  "most_earned_path": ["string"],
  "why": ["string"]
}
```

---

### Mixed Template B — Translate Then Test

#### Typical Query Form

- Turn this historical case into a generalized scenario and then tell me whether this fictional variant still makes sense.

#### Engine Mode

- translation → state modeling → validation

---

## Interaction-Level Strictness Settings

The engine should support at least three practical strictness modes.

### lenient

Useful for ideation and exploratory worldbuilding. Allows more archetypal bridging, as long as provenance is visible.

### default

Balanced mode. Good for most writing support and scenario development.

### strict

Useful for continuity checks, historical plausibility, and author audits. Reduces speculative bridging and penalizes missing supports more strongly.

### Rule

Strictness changes the engine’s tolerance for missing bridges. It should not rewrite explicit facts.

---

## Preferred Response Structure by Task Type

### Expansion Responses Should Usually Include

- what the engine is building from
- the main derived pressures or structures
- the resulting narrative space
- uncertainty markers when input is thin

### Validation Responses Should Usually Include

- verdict
- primary supports
- primary blockers
- missing setup or missing layers
- the smallest strengthening revision

### Translation Responses Should Usually Include

- source-specific structure
- normalized structure
- transformed output
- what was preserved versus abstracted

---

## Fail-Soft Interaction Rules

The engine should degrade gracefully when inputs are weak.

### When Input Is Minimal

Return:

- a sparse state reading
- one or more plausible paths
- a clear uncertainty note

### When a Validation Question Lacks Required Layers

Return:

- a provisional verdict or restraint
- exactly what is missing
- what kind of input would make the judgment stronger

### When Mixed Layers Contradict

Return:

- the contradiction explicitly
- possible branch models or minimal revisions

---

## Example Query Patterns

### Writer

- “Would Mara really abandon her brother here?”
- “Is this apology too early?”
- “Expand this into a scene: ‘He opened the letter and smiled for the wrong reason.’”

### Worldbuilder

- “Given these tectonics and sea patterns, what kind of trade civilization emerges?”
- “Does this priest-engineer caste make sense here?”
- “What symbolic layer would likely arise from annual volcanic ashfall?”

### Scenario Designer

- “Map the three most supported next branches from this crisis state.”
- “Which part of this coup scenario is weakest?”
- “Abstract this war into a reusable generalized scenario.”

---

## Interaction Templates Summary

The engine should not expose its full internal machinery every time, but it should adapt its interface to the user’s real job.

In short:

**writers need coherence and earnedness, worldbuilders need layered plausibility, and scenario designers need branch logic and structural stress testing.**

---

# EXAMPLE POPULATED STATE OBJECTS V1

## Prototype Fixtures

This section provides concrete example state objects for major engine use cases.

The goal is not exhaustive realism. The goal is to prove that the schema can hold real narrative structure at different scales without collapsing into either vagueness or overclaim.

These examples are deliberately partial. They demonstrate sparse-state usability, provenance tagging, layer handling, and validation readiness.

---

## Fixture A — Minimal Scene Seed

### Source Prompt

`"a hero came to a fork in the road"`

### Use Case

- fragment expansion
- symbolic potential detection
- branch generation

### Example State Object

```json
{
  "state_id": "state_scene_seed_001",
  "state_version": "0.1",
  "input_profile": {
    "input_mode": "scene_seed",
    "evidence_density": "minimal",
    "layer_mode": "recovered"
  },
  "layers": [
    {
      "id": "layer_scene",
      "name": "Scene Layer",
      "layer_type": "scene",
      "origin": "recovered",
      "description": "A lone actor faces a branching decision point.",
      "related_object_ids": ["entity_hero_001", "event_fork_001", "constraint_choice_001", "symbol_fork_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_symbolic",
          "relation": "complementary",
          "notes": "The physical fork may carry symbolic meaning about choice, duty, or fate."
        }
      ],
      "confidence": 0.91,
      "evidence_refs": ["prompt:0"]
    },
    {
      "id": "layer_symbolic",
      "name": "Symbolic Layer",
      "layer_type": "symbolic",
      "origin": "inferred",
      "description": "The fork plausibly functions as a symbolic choice point.",
      "related_object_ids": ["symbol_fork_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_scene",
          "relation": "complementary",
          "notes": "Symbolic reading depends on scene framing and repetition."
        }
      ],
      "confidence": 0.48,
      "evidence_refs": ["prompt:0"]
    }
  ],
  "entities": [
    {
      "id": "entity_hero_001",
      "label": "Hero",
      "entity_type": "character",
      "scale": "micro",
      "persistence": "persistent",
      "salient_traits": ["heroic_role"],
      "current_condition": ["at_decision_point"],
      "temporal_position": {
        "start": null,
        "end": null,
        "sequence_index": 1
      },
      "metadata": {
        "id": "entity_hero_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.95,
        "evidence_refs": ["prompt:0"],
        "notes": "No identity, motive, or context is specified beyond the role label."
      }
    }
  ],
  "relations": [],
  "pressures": [
    {
      "id": "pressure_decision_001",
      "pressure_type": "time_pressure",
      "affected_object_ids": ["entity_hero_001"],
      "source_object_ids": ["event_fork_001"],
      "intensity": 0.34,
      "duration": "momentary",
      "direction": "stable",
      "description": "Progress requires choosing a path.",
      "metadata": {
        "id": "pressure_decision_001",
        "layer": "scene",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.62,
        "evidence_refs": ["prompt:0"],
        "notes": "The pressure is mild because urgency is implied rather than stated."
      }
    }
  ],
  "constraints": [
    {
      "id": "constraint_choice_001",
      "constraint_type": "geography",
      "scope": "individual",
      "affected_object_ids": ["entity_hero_001"],
      "severity": 0.67,
      "enforceability": "physical",
      "duration": "momentary",
      "description": "The road physically branches; forward movement requires selecting a route.",
      "metadata": {
        "id": "constraint_choice_001",
        "layer": "scene",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.86,
        "evidence_refs": ["prompt:0"],
        "notes": null
      }
    }
  ],
  "motives": [],
  "events": [
    {
      "id": "event_fork_001",
      "event_type": "decision_point",
      "participant_ids": ["entity_hero_001"],
      "trigger_ids": [],
      "consequence_ids": [],
      "precondition_ids": [],
      "temporal_position": {
        "sequence_index": 1,
        "relative_phase": "hinge",
        "duration": "scene"
      },
      "certainty": 0.98,
      "description": "The hero arrives at a fork in the road.",
      "metadata": {
        "id": "event_fork_001",
        "layer": "scene",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.98,
        "evidence_refs": ["prompt:0"],
        "notes": null
      }
    }
  ],
  "knowledge_states": [],
  "symbolic_loads": [
    {
      "id": "symbol_fork_001",
      "carrier_object_id": "event_fork_001",
      "meaning_cluster": ["choice", "divergence", "fate_vs_agency"],
      "cultural_scope": "personal",
      "stability": "emergent",
      "interpretive_variance": "high",
      "description": "The fork may symbolize a consequential branching of identity or duty.",
      "metadata": {
        "id": "symbol_fork_001",
        "layer": "symbolic",
        "source_tag": "archetypally_inferred",
        "status_tag": "provisional",
        "confidence": 0.44,
        "evidence_refs": ["prompt:0"],
        "notes": "The symbolism is plausible but not yet earned through repetition or context."
      }
    }
  ],
  "uncertainties": [
    {
      "id": "uncertainty_scene_001",
      "unknown_area": "motive",
      "affected_object_ids": ["entity_hero_001", "event_fork_001"],
      "ambiguity_class": "missing",
      "candidate_interpretations": [
        "The choice is strategic.",
        "The choice is moral.",
        "The choice is symbolic."
      ],
      "recommended_handling": "branch_multiple",
      "metadata": {
        "id": "uncertainty_scene_001",
        "layer": "multi",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.99,
        "evidence_refs": ["prompt:0"],
        "notes": "The source gives no motive context."
      }
    }
  ],
  "continuity": {
    "causal_continuity": {"status": "stable", "notes": "A decision point naturally follows from travel."},
    "temporal_continuity": {"status": "stable", "notes": null},
    "spatial_continuity": {"status": "stable", "notes": null},
    "character_continuity": {"status": "unknown", "notes": "No prior behavior is established."},
    "knowledge_continuity": {"status": "unknown", "notes": null},
    "thematic_continuity": {"status": "unknown", "notes": null},
    "consequence_continuity": {"status": "unknown", "notes": "Consequences are not yet specified."}
  },
  "narrative_context": {
    "current_mode": "expansion",
    "requested_output_form": "branch_map",
    "tone_profile": [],
    "genre_frame": [],
    "historical_frame": null,
    "scale_focus": "scene",
    "user_constraints": []
  },
  "provenance_log": [
    {
      "id": "prov_scene_001",
      "object_id": "state_scene_seed_001",
      "operation": "extracted",
      "method": "minimal scene-seed parsing",
      "input_refs": ["prompt:0"],
      "notes": "Sparse state intentionally preserved."
    }
  ]
}
```

### Why This Fixture Matters

- proves that a one-line input can populate a valid state
- preserves uncertainty instead of inventing motive detail
- supports branch generation without overclaiming narrative depth

---

## Fixture B — Character Action Audit

### Source Situation

A commander named Mara has spent three chapters protecting her younger brother, Teren. After a failed escape and a public humiliation, the author proposes: `"Mara abandons Teren to save the rebellion."`

### Use Case

- motivation coherence audit
- setup sufficiency diagnosis
- continuity check

### Example State Object

```json
{
  "state_id": "state_character_audit_001",
  "state_version": "0.1",
  "input_profile": {
    "input_mode": "mixed_bundle",
    "evidence_density": "moderate",
    "layer_mode": "mixed"
  },
  "layers": [
    {
      "id": "layer_character",
      "name": "Character Layer",
      "layer_type": "character",
      "origin": "recovered",
      "description": "Mara is loyal, burdened, strategically capable, and emotionally protective toward Teren.",
      "related_object_ids": ["entity_mara_001", "entity_teren_001", "motive_mara_protect_001", "motive_mara_rebellion_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_event",
          "relation": "in_tension",
          "notes": "Recent failure increases pressure toward strategic sacrifice."
        }
      ],
      "confidence": 0.84,
      "evidence_refs": ["chapter_summary:0-3"]
    },
    {
      "id": "layer_event",
      "name": "Event Layer",
      "layer_type": "event",
      "origin": "recovered",
      "description": "A failed escape and a public humiliation have raised the stakes and exposed the group.",
      "related_object_ids": ["event_escape_fail_001", "event_humiliation_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_character",
          "relation": "in_tension",
          "notes": "The rebellion imperative is beginning to compete with personal loyalty."
        }
      ],
      "confidence": 0.87,
      "evidence_refs": ["chapter_summary:0-3"]
    }
  ],
  "entities": [
    {
      "id": "entity_mara_001",
      "label": "Mara",
      "entity_type": "character",
      "scale": "micro",
      "persistence": "persistent",
      "salient_traits": ["disciplined", "protective", "strategic", "duty-bound"],
      "current_condition": ["exhausted", "under_public_pressure", "morally_split"],
      "temporal_position": {"start": null, "end": null, "sequence_index": 12},
      "metadata": {
        "id": "entity_mara_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.9,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    },
    {
      "id": "entity_teren_001",
      "label": "Teren",
      "entity_type": "character",
      "scale": "micro",
      "persistence": "persistent",
      "salient_traits": ["younger_brother", "vulnerable", "symbol_of_past_loyalty"],
      "current_condition": ["captured_risk", "dependent_on_mara"],
      "temporal_position": {"start": null, "end": null, "sequence_index": 12},
      "metadata": {
        "id": "entity_teren_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.84,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    },
    {
      "id": "entity_rebellion_001",
      "label": "The Rebellion",
      "entity_type": "faction",
      "scale": "regional",
      "persistence": "structural",
      "salient_traits": ["fragile", "resource-poor", "morally_serious"],
      "current_condition": ["compromised", "needs_leadership"],
      "temporal_position": {"start": null, "end": null, "sequence_index": 12},
      "metadata": {
        "id": "entity_rebellion_001",
        "layer": "political",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.81,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    }
  ],
  "relations": [
    {
      "id": "relation_mara_teren_001",
      "source_entity_id": "entity_mara_001",
      "target_entity_id": "entity_teren_001",
      "relation_type": "kinship",
      "strength": 0.95,
      "directionality": "bidirectional",
      "stability": "durable",
      "active": true,
      "metadata": {
        "id": "relation_mara_teren_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.96,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": "This relationship is one of the narrative anchors."
      }
    },
    {
      "id": "relation_mara_rebellion_001",
      "source_entity_id": "entity_mara_001",
      "target_entity_id": "entity_rebellion_001",
      "relation_type": "alliance",
      "strength": 0.82,
      "directionality": "source_to_target",
      "stability": "durable",
      "active": true,
      "metadata": {
        "id": "relation_mara_rebellion_001",
        "layer": "political",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.83,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": "Mara is tied to the cause, but family loyalty remains stronger so far."
      }
    }
  ],
  "pressures": [
    {
      "id": "pressure_exposure_001",
      "pressure_type": "time_pressure",
      "affected_object_ids": ["entity_mara_001", "entity_rebellion_001"],
      "source_object_ids": ["event_escape_fail_001", "event_humiliation_001"],
      "intensity": 0.88,
      "duration": "short",
      "direction": "rising",
      "description": "The rebellion is newly exposed and must move quickly.",
      "metadata": {
        "id": "pressure_exposure_001",
        "layer": "event",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.83,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    }
  ],
  "constraints": [
    {
      "id": "constraint_visibility_001",
      "constraint_type": "institution",
      "scope": "group",
      "affected_object_ids": ["entity_rebellion_001", "entity_mara_001"],
      "severity": 0.73,
      "enforceability": "physical",
      "duration": "ongoing",
      "description": "Open rescue efforts now threaten the entire rebel network.",
      "metadata": {
        "id": "constraint_visibility_001",
        "layer": "political",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.79,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    }
  ],
  "motives": [
    {
      "id": "motive_mara_protect_001",
      "actor_entity_id": "entity_mara_001",
      "motive_type": "love",
      "priority": 0.94,
      "stability": "core",
      "visibility_to_others": "partially_visible",
      "conflicts_with": ["motive_mara_rebellion_001"],
      "description": "Mara is strongly motivated to protect Teren.",
      "metadata": {
        "id": "motive_mara_protect_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.93,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    },
    {
      "id": "motive_mara_rebellion_001",
      "actor_entity_id": "entity_mara_001",
      "motive_type": "duty",
      "priority": 0.81,
      "stability": "durable",
      "visibility_to_others": "public",
      "conflicts_with": ["motive_mara_protect_001"],
      "description": "Mara is committed to the rebellion’s survival.",
      "metadata": {
        "id": "motive_mara_rebellion_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.87,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    }
  ],
  "events": [
    {
      "id": "event_escape_fail_001",
      "event_type": "decision_point",
      "participant_ids": ["entity_mara_001", "entity_teren_001"],
      "trigger_ids": [],
      "consequence_ids": ["pressure_exposure_001", "constraint_visibility_001"],
      "precondition_ids": [],
      "temporal_position": {"sequence_index": 10, "relative_phase": "escalation", "duration": "scene"},
      "certainty": 0.92,
      "description": "The attempted escape failed and worsened the group’s position.",
      "metadata": {
        "id": "event_escape_fail_001",
        "layer": "event",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.91,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    },
    {
      "id": "event_humiliation_001",
      "event_type": "revelation",
      "participant_ids": ["entity_mara_001"],
      "trigger_ids": ["event_escape_fail_001"],
      "consequence_ids": ["pressure_exposure_001"],
      "precondition_ids": [],
      "temporal_position": {"sequence_index": 11, "relative_phase": "escalation", "duration": "scene"},
      "certainty": 0.88,
      "description": "Mara was publicly humiliated, narrowing her room for open defiance.",
      "metadata": {
        "id": "event_humiliation_001",
        "layer": "event",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.86,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    },
    {
      "id": "event_proposal_abandon_001",
      "event_type": "decision_point",
      "participant_ids": ["entity_mara_001", "entity_teren_001", "entity_rebellion_001"],
      "trigger_ids": ["pressure_exposure_001", "constraint_visibility_001", "motive_mara_rebellion_001"],
      "consequence_ids": [],
      "precondition_ids": ["event_escape_fail_001", "event_humiliation_001"],
      "temporal_position": {"sequence_index": 12, "relative_phase": "hinge", "duration": "scene"},
      "certainty": 0.0,
      "description": "Proposal: Mara abandons Teren to save the rebellion.",
      "metadata": {
        "id": "event_proposal_abandon_001",
        "layer": "event",
        "source_tag": "user_declared",
        "status_tag": "provisional",
        "confidence": 0.0,
        "evidence_refs": ["author_query:0"],
        "notes": "This is the proposal under validation, not an accepted event."
      }
    }
  ],
  "knowledge_states": [
    {
      "id": "knowledge_mara_001",
      "knower_entity_id": "entity_mara_001",
      "proposition": "A rescue attempt now endangers the broader network.",
      "certainty": 0.9,
      "acquisition_source": "observed",
      "timing": {"sequence_index": 11, "relative_to_event_id": "event_humiliation_001"},
      "metadata": {
        "id": "knowledge_mara_001",
        "layer": "knowledge",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.87,
        "evidence_refs": ["chapter_summary:0-3"],
        "notes": null
      }
    }
  ],
  "symbolic_loads": [],
  "uncertainties": [
    {
      "id": "uncertainty_mara_001",
      "unknown_area": "motive",
      "affected_object_ids": ["entity_mara_001", "event_proposal_abandon_001"],
      "ambiguity_class": "underdetermined",
      "candidate_interpretations": [
        "She chooses duty over family.",
        "She only appears to abandon him.",
        "She breaks under accumulated shame and pressure."
      ],
      "recommended_handling": "infer_cautiously",
      "metadata": {
        "id": "uncertainty_mara_001",
        "layer": "character",
        "source_tag": "structurally_inferred",
        "status_tag": "provisional",
        "confidence": 0.56,
        "evidence_refs": ["author_query:0", "chapter_summary:0-3"],
        "notes": "The proposal is imaginable, but the current setup still favors protection."
      }
    }
  ],
  "continuity": {
    "causal_continuity": {"status": "stable", "notes": "The proposed move is causally linked to increased pressure."},
    "temporal_continuity": {"status": "stable", "notes": null},
    "spatial_continuity": {"status": "stable", "notes": null},
    "character_continuity": {"status": "stressed", "notes": "The proposal cuts against Mara’s strongest established pattern."},
    "knowledge_continuity": {"status": "stable", "notes": "Mara has the knowledge required for the choice."},
    "thematic_continuity": {"status": "evolving", "notes": "The duty-versus-bloodline theme supports the possibility, but not yet as the dominant resolution."},
    "consequence_continuity": {"status": "stable", "notes": "Prior failure meaningfully pressures the decision."}
  },
  "narrative_context": {
    "current_mode": "validation",
    "requested_output_form": "audit",
    "tone_profile": [],
    "genre_frame": ["rebellion_drama"],
    "historical_frame": null,
    "scale_focus": "character",
    "user_constraints": []
  },
  "provenance_log": [
    {
      "id": "prov_mara_001",
      "object_id": "event_proposal_abandon_001",
      "operation": "validated",
      "method": "motivation coherence and setup sufficiency pass",
      "input_refs": ["author_query:0", "chapter_summary:0-3"],
      "notes": "Likely verdict: possible_with_setup or strained, depending on the desired sharpness of the reversal."
    }
  ]
}
```

### Likely Validation Reading

- **not contradictory**, because strong pressure and duty motives exist
- **not supported yet**, because the protective motive remains dominant
- likely verdict: **possible\_with\_setup**
- needed bridge: one more beat showing Mara accepting irreversible strategic sacrifice, or a prior crack in the sibling-protection logic

---

## Fixture C — Planetary Substrate to Civilization

### Source Conditions

- tectonically unstable island chain
- rich coastal fisheries
- poor interior farmland
- frequent storm seasons
- mineral-rich volcanic ridges

### Use Case

- civilization emergence
- worldbuilding expansion
- symbolic layer generation

### Example State Object

```json
{
  "state_id": "state_worldbuild_001",
  "state_version": "0.1",
  "input_profile": {
    "input_mode": "structured_data",
    "evidence_density": "sparse",
    "layer_mode": "recovered"
  },
  "layers": [
    {
      "id": "layer_physical",
      "name": "Physical Layer",
      "layer_type": "physical",
      "origin": "recovered",
      "description": "Fragmented islands, unstable geology, harsh storm cycles, and mineral-rich volcanic ridges.",
      "related_object_ids": ["entity_archipelago_001", "pressure_storm_001", "constraint_farmland_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_economic",
          "relation": "aligned",
          "notes": "The environment strongly favors maritime adaptation and extractive activity."
        },
        {
          "target_layer_id": "layer_symbolic",
          "relation": "complementary",
          "notes": "Repeated exposure to storms and volcanoes supports strong sacred interpretations."
        }
      ],
      "confidence": 0.93,
      "evidence_refs": ["world_seed:0"]
    },
    {
      "id": "layer_economic",
      "name": "Economic Layer",
      "layer_type": "economic",
      "origin": "inferred",
      "description": "Maritime trade, salvage, fisheries, and controlled mineral extraction are likely economic anchors.",
      "related_object_ids": ["pressure_maritime_dependence_001", "entity_harbor_leagues_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_physical",
          "relation": "aligned",
          "notes": null
        }
      ],
      "confidence": 0.74,
      "evidence_refs": ["world_seed:0"]
    },
    {
      "id": "layer_symbolic",
      "name": "Symbolic Layer",
      "layer_type": "symbolic",
      "origin": "inferred",
      "description": "Storms and volcanic ridges likely become associated with judgment, sacrifice, or navigation rites.",
      "related_object_ids": ["symbol_sea_judgment_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_physical",
          "relation": "complementary",
          "notes": null
        }
      ],
      "confidence": 0.58,
      "evidence_refs": ["world_seed:0"]
    }
  ],
  "entities": [
    {
      "id": "entity_archipelago_001",
      "label": "The Shattered Archipelago",
      "entity_type": "location",
      "scale": "regional",
      "persistence": "structural",
      "salient_traits": ["island_fragmentation", "volcanic_ridges", "storm_exposure"],
      "current_condition": ["geologically_unstable", "maritime_linked"],
      "temporal_position": {"start": null, "end": null, "sequence_index": null},
      "metadata": {
        "id": "entity_archipelago_001",
        "layer": "physical",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.96,
        "evidence_refs": ["world_seed:0"],
        "notes": null
      }
    },
    {
      "id": "entity_harbor_leagues_001",
      "label": "Harbor Leagues",
      "entity_type": "institution",
      "scale": "regional",
      "persistence": "structural",
      "salient_traits": ["port_federation", "salvage_rights", "storm-season_governance"],
      "current_condition": ["likely_emergent"],
      "temporal_position": {"start": null, "end": null, "sequence_index": null},
      "metadata": {
        "id": "entity_harbor_leagues_001",
        "layer": "institutional",
        "source_tag": "structurally_inferred",
        "status_tag": "provisional",
        "confidence": 0.67,
        "evidence_refs": ["world_seed:0"],
        "notes": "An example institutional outcome, not a required one."
      }
    }
  ],
  "relations": [],
  "pressures": [
    {
      "id": "pressure_storm_001",
      "pressure_type": "ecological_stress",
      "affected_object_ids": ["entity_archipelago_001"],
      "source_object_ids": [],
      "intensity": 0.89,
      "duration": "chronic",
      "direction": "cyclical",
      "description": "Frequent storms create recurring maritime danger and seasonal instability.",
      "metadata": {
        "id": "pressure_storm_001",
        "layer": "physical",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.94,
        "evidence_refs": ["world_seed:0"],
        "notes": null
      }
    },
    {
      "id": "pressure_maritime_dependence_001",
      "pressure_type": "scarcity",
      "affected_object_ids": ["entity_archipelago_001", "entity_harbor_leagues_001"],
      "source_object_ids": ["constraint_farmland_001", "pressure_storm_001"],
      "intensity": 0.72,
      "duration": "chronic",
      "direction": "stable",
      "description": "Poor farmland increases dependence on the sea, trade, and preserved food systems.",
      "metadata": {
        "id": "pressure_maritime_dependence_001",
        "layer": "economic",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.8,
        "evidence_refs": ["world_seed:0"],
        "notes": null
      }
    }
  ],
  "constraints": [
    {
      "id": "constraint_farmland_001",
      "constraint_type": "geography",
      "scope": "system",
      "affected_object_ids": ["entity_archipelago_001"],
      "severity": 0.77,
      "enforceability": "physical",
      "duration": "structural",
      "description": "Poor interior farmland constrains agrarian population concentration.",
      "metadata": {
        "id": "constraint_farmland_001",
        "layer": "physical",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.91,
        "evidence_refs": ["world_seed:0"],
        "notes": null
      }
    }
  ],
  "motives": [],
  "events": [],
  "knowledge_states": [],
  "symbolic_loads": [
    {
      "id": "symbol_sea_judgment_001",
      "carrier_object_id": "entity_archipelago_001",
      "meaning_cluster": ["judgment", "trial", "worthiness_through_navigation"],
      "cultural_scope": "civilizational",
      "stability": "emergent",
      "interpretive_variance": "medium",
      "description": "The sea may become interpreted as an adjudicator of worth and oathfulness.",
      "metadata": {
        "id": "symbol_sea_judgment_001",
        "layer": "symbolic",
        "source_tag": "archetypally_inferred",
        "status_tag": "provisional",
        "confidence": 0.55,
        "evidence_refs": ["world_seed:0"],
        "notes": "This meaning is plausible because danger is cyclical, communal, and legible."
      }
    }
  ],
  "uncertainties": [
    {
      "id": "uncertainty_world_001",
      "unknown_area": "institution",
      "affected_object_ids": ["entity_harbor_leagues_001"],
      "ambiguity_class": "interpretive_opening",
      "candidate_interpretations": [
        "Loose harbor confederacies emerge.",
        "Temple-navigation guilds dominate.",
        "Storm kings centralize rule by controlling ports."
      ],
      "recommended_handling": "branch_multiple",
      "metadata": {
        "id": "uncertainty_world_001",
        "layer": "institutional",
        "source_tag": "structurally_inferred",
        "status_tag": "provisional",
        "confidence": 0.61,
        "evidence_refs": ["world_seed:0"],
        "notes": "Environmental substrate supports several political outcomes."
      }
    }
  ],
  "continuity": {
    "causal_continuity": {"status": "stable", "notes": "The inferred economy follows from the substrate."},
    "temporal_continuity": {"status": "unknown", "notes": "No specific historical stage is supplied."},
    "spatial_continuity": {"status": "stable", "notes": null},
    "character_continuity": {"status": "unknown", "notes": null},
    "knowledge_continuity": {"status": "unknown", "notes": null},
    "thematic_continuity": {"status": "evolving", "notes": "Symbolic readings are emerging from recurring hazard."},
    "consequence_continuity": {"status": "stable", "notes": "Storm and scarcity pressures imply durable social adaptation."}
  },
  "narrative_context": {
    "current_mode": "expansion",
    "requested_output_form": "world_sketch",
    "tone_profile": [],
    "genre_frame": ["civilization_emergence"],
    "historical_frame": null,
    "scale_focus": "substrate",
    "user_constraints": []
  },
  "provenance_log": [
    {
      "id": "prov_world_001",
      "object_id": "state_worldbuild_001",
      "operation": "expanded",
      "method": "substrate derivation and symbolic crystallization chain",
      "input_refs": ["world_seed:0"],
      "notes": "Institutional outcomes remain branchable rather than fixed."
    }
  ]
}
```

### Why This Fixture Matters

- exercises substrate → system → symbolic movement
- shows how rich outputs can emerge without inventing named characters
- keeps institutions branchable rather than falsely settled

---

## Fixture D — Next-Event Continuity Check

### Source Situation

A detective has just discovered that her chief suspect is innocent. The proposed next event is: `"She publicly accuses him anyway at the gala that same night."`

### Use Case

- next-event validation
- knowledge continuity
- setup sufficiency and pressure diagnosis

### Example State Object

```json
{
  "state_id": "state_next_event_001",
  "state_version": "0.1",
  "input_profile": {
    "input_mode": "mixed_bundle",
    "evidence_density": "moderate",
    "layer_mode": "mixed"
  },
  "layers": [
    {
      "id": "layer_event",
      "name": "Event Layer",
      "layer_type": "event",
      "origin": "recovered",
      "description": "The investigation has pivoted because the primary suspect was exonerated in private.",
      "related_object_ids": ["event_exoneration_001", "event_proposal_accusation_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_character",
          "relation": "in_tension",
          "notes": "The detective’s public credibility and private knowledge are now misaligned."
        }
      ],
      "confidence": 0.88,
      "evidence_refs": ["case_summary:0-2"]
    },
    {
      "id": "layer_character",
      "name": "Character Layer",
      "layer_type": "character",
      "origin": "recovered",
      "description": "The detective is proud, image-conscious, but still fundamentally evidence-driven.",
      "related_object_ids": ["entity_detective_001", "motive_truth_001", "motive_reputation_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_event",
          "relation": "in_tension",
          "notes": "Public accusation conflicts with fresh exonerating knowledge."
        }
      ],
      "confidence": 0.81,
      "evidence_refs": ["case_summary:0-2"]
    }
  ],
  "entities": [
    {
      "id": "entity_detective_001",
      "label": "Detective Elian",
      "entity_type": "character",
      "scale": "micro",
      "persistence": "persistent",
      "salient_traits": ["evidence_driven", "proud", "socially_visible"],
      "current_condition": ["internally_destabilized", "publicly_committed_to_prior_theory"],
      "temporal_position": {"start": null, "end": null, "sequence_index": 18},
      "metadata": {
        "id": "entity_detective_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.85,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    },
    {
      "id": "entity_suspect_001",
      "label": "Chief Suspect",
      "entity_type": "character",
      "scale": "micro",
      "persistence": "persistent",
      "salient_traits": ["publicly_distrusted", "privately_exonerated"],
      "current_condition": ["socially_exposed"],
      "temporal_position": {"start": null, "end": null, "sequence_index": 18},
      "metadata": {
        "id": "entity_suspect_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.8,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    }
  ],
  "relations": [],
  "pressures": [
    {
      "id": "pressure_reputation_001",
      "pressure_type": "shame",
      "affected_object_ids": ["entity_detective_001"],
      "source_object_ids": ["event_exoneration_001"],
      "intensity": 0.71,
      "duration": "short",
      "direction": "rising",
      "description": "Being wrong threatens the detective’s public authority.",
      "metadata": {
        "id": "pressure_reputation_001",
        "layer": "character",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.75,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    }
  ],
  "constraints": [
    {
      "id": "constraint_truth_001",
      "constraint_type": "institution",
      "scope": "individual",
      "affected_object_ids": ["entity_detective_001"],
      "severity": 0.68,
      "enforceability": "social",
      "duration": "ongoing",
      "description": "The detective’s role is normatively tied to evidence and procedure.",
      "metadata": {
        "id": "constraint_truth_001",
        "layer": "institutional",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.72,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    }
  ],
  "motives": [
    {
      "id": "motive_truth_001",
      "actor_entity_id": "entity_detective_001",
      "motive_type": "duty",
      "priority": 0.86,
      "stability": "core",
      "visibility_to_others": "public",
      "conflicts_with": ["motive_reputation_001"],
      "description": "The detective wants the truth and normally follows evidence.",
      "metadata": {
        "id": "motive_truth_001",
        "layer": "character",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.84,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    },
    {
      "id": "motive_reputation_001",
      "actor_entity_id": "entity_detective_001",
      "motive_type": "fear_of_disgrace",
      "priority": 0.63,
      "stability": "situational",
      "visibility_to_others": "hidden",
      "conflicts_with": ["motive_truth_001"],
      "description": "The detective fears public humiliation if the case collapses.",
      "metadata": {
        "id": "motive_reputation_001",
        "layer": "character",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.7,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    }
  ],
  "events": [
    {
      "id": "event_exoneration_001",
      "event_type": "revelation",
      "participant_ids": ["entity_detective_001", "entity_suspect_001"],
      "trigger_ids": [],
      "consequence_ids": ["pressure_reputation_001"],
      "precondition_ids": [],
      "temporal_position": {"sequence_index": 17, "relative_phase": "hinge", "duration": "scene"},
      "certainty": 0.95,
      "description": "The detective privately discovers that the chief suspect is innocent.",
      "metadata": {
        "id": "event_exoneration_001",
        "layer": "event",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.95,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    },
    {
      "id": "event_proposal_accusation_001",
      "event_type": "revelation",
      "participant_ids": ["entity_detective_001", "entity_suspect_001"],
      "trigger_ids": ["pressure_reputation_001"],
      "consequence_ids": [],
      "precondition_ids": ["event_exoneration_001"],
      "temporal_position": {"sequence_index": 18, "relative_phase": "hinge", "duration": "scene"},
      "certainty": 0.0,
      "description": "Proposal: the detective publicly accuses the innocent suspect at the gala that same night.",
      "metadata": {
        "id": "event_proposal_accusation_001",
        "layer": "event",
        "source_tag": "user_declared",
        "status_tag": "provisional",
        "confidence": 0.0,
        "evidence_refs": ["author_query:1"],
        "notes": null
      }
    }
  ],
  "knowledge_states": [
    {
      "id": "knowledge_detective_001",
      "knower_entity_id": "entity_detective_001",
      "proposition": "The chief suspect is innocent.",
      "certainty": 0.96,
      "acquisition_source": "observed",
      "timing": {"sequence_index": 17, "relative_to_event_id": "event_exoneration_001"},
      "metadata": {
        "id": "knowledge_detective_001",
        "layer": "knowledge",
        "source_tag": "directly_extracted",
        "status_tag": "explicit",
        "confidence": 0.95,
        "evidence_refs": ["case_summary:0-2"],
        "notes": null
      }
    }
  ],
  "symbolic_loads": [],
  "uncertainties": [
    {
      "id": "uncertainty_event_001",
      "unknown_area": "causality",
      "affected_object_ids": ["event_proposal_accusation_001"],
      "ambiguity_class": "low_support",
      "candidate_interpretations": [
        "The accusation is a desperate bluff.",
        "The detective is deliberately protecting someone else.",
        "The detective has not emotionally processed the revelation."
      ],
      "recommended_handling": "infer_cautiously",
      "metadata": {
        "id": "uncertainty_event_001",
        "layer": "event",
        "source_tag": "structurally_inferred",
        "status_tag": "provisional",
        "confidence": 0.42,
        "evidence_refs": ["author_query:1", "case_summary:0-2"],
        "notes": "The proposed event currently lacks a strong bridge from evidence-driven character logic."
      }
    }
  ],
  "continuity": {
    "causal_continuity": {"status": "stressed", "notes": "The proposal requires a stronger causal bridge than reputation pressure alone."},
    "temporal_continuity": {"status": "stable", "notes": "The gala occurs the same night; timing is clear."},
    "spatial_continuity": {"status": "stable", "notes": null},
    "character_continuity": {"status": "stressed", "notes": "A public false accusation conflicts with the evidence-driven identity."},
    "knowledge_continuity": {"status": "stable", "notes": "The character has the relevant knowledge, but that knowledge works against the proposed action."},
    "thematic_continuity": {"status": "evolving", "notes": null},
    "consequence_continuity": {"status": "stable", "notes": "Fresh exoneration should materially affect the next public move."}
  },
  "narrative_context": {
    "current_mode": "validation",
    "requested_output_form": "audit",
    "tone_profile": [],
    "genre_frame": ["mystery_drama"],
    "historical_frame": null,
    "scale_focus": "event",
    "user_constraints": ["same_night_gala"]
  },
  "provenance_log": [
    {
      "id": "prov_next_001",
      "object_id": "event_proposal_accusation_001",
      "operation": "validated",
      "method": "next-event continuity check",
      "input_refs": ["author_query:1", "case_summary:0-2"],
      "notes": "Likely verdict: strained unless a protective or deceptive motive bridge is added."
    }
  ]
}
```

### Likely Validation Reading

- likely verdict: **strained**
- not a hard impossibility, but current support is weak
- easiest repair: make the accusation a tactical misdirection, a coercive performance, or a sign of temporary breakdown

---

## Fixture E — Historical Plausibility Check

### Source Situation

A historical fiction author proposes: `"In a pre-telegraph frontier kingdom, the queen coordinates a same-day synchronized crackdown across six distant provincial cities."`

### Use Case

- historical plausibility audit
- logistics and communications check
- institutional constraint analysis

### Example State Object

```json
{
  "state_id": "state_historical_001",
  "state_version": "0.1",
  "input_profile": {
    "input_mode": "notes",
    "evidence_density": "sparse",
    "layer_mode": "mixed"
  },
  "layers": [
    {
      "id": "layer_historical_frame",
      "name": "Historical Frame",
      "layer_type": "institutional",
      "origin": "declared",
      "description": "Pre-telegraph frontier monarchy with slow message transmission across long distances.",
      "related_object_ids": ["constraint_comms_001", "entity_monarchy_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_event",
          "relation": "in_tension",
          "notes": "Synchronized same-day action across distance conflicts with communication speed."
        }
      ],
      "confidence": 0.95,
      "evidence_refs": ["author_query:2"]
    },
    {
      "id": "layer_event",
      "name": "Event Layer",
      "layer_type": "event",
      "origin": "declared",
      "description": "The queen attempts a same-day coordinated crackdown across six distant cities.",
      "related_object_ids": ["event_proposal_crackdown_001"],
      "relationship_to_other_layers": [
        {
          "target_layer_id": "layer_historical_frame",
          "relation": "contradictory",
          "notes": "As stated, the timing and communications model do not fit."
        }
      ],
      "confidence": 0.93,
      "evidence_refs": ["author_query:2"]
    }
  ],
  "entities": [
    {
      "id": "entity_monarchy_001",
      "label": "Frontier Monarchy",
      "entity_type": "institution",
      "scale": "regional",
      "persistence": "structural",
      "salient_traits": ["centralized_authority", "distance_limited", "pre_telegraph_administration"],
      "current_condition": ["operationally_slow"],
      "temporal_position": {"start": null, "end": null, "sequence_index": null},
      "metadata": {
        "id": "entity_monarchy_001",
        "layer": "institutional",
        "source_tag": "user_declared",
        "status_tag": "explicit",
        "confidence": 0.95,
        "evidence_refs": ["author_query:2"],
        "notes": null
      }
    }
  ],
  "relations": [],
  "pressures": [],
  "constraints": [
    {
      "id": "constraint_comms_001",
      "constraint_type": "institution",
      "scope": "system",
      "affected_object_ids": ["entity_monarchy_001", "event_proposal_crackdown_001"],
      "severity": 0.91,
      "enforceability": "physical",
      "duration": "structural",
      "description": "Communication speed is limited by messenger travel; same-day remote synchronization is severely constrained.",
      "metadata": {
        "id": "constraint_comms_001",
        "layer": "institutional",
        "source_tag": "structurally_inferred",
        "status_tag": "derived",
        "confidence": 0.89,
        "evidence_refs": ["author_query:2"],
        "notes": "This could be softened only if the operations were pre-planned and locally triggered."
      }
    }
  ],
  "motives": [],
  "events": [
    {
      "id": "event_proposal_crackdown_001",
      "event_type": "decision_point",
      "participant_ids": ["entity_monarchy_001"],
      "trigger_ids": [],
      "consequence_ids": [],
      "precondition_ids": [],
      "temporal_position": {"sequence_index": null, "relative_phase": "hinge", "duration": "episode"},
      "certainty": 0.0,
      "description": "Proposal: same-day synchronized crackdown across six distant provincial cities.",
      "metadata": {
        "id": "event_proposal_crackdown_001",
        "layer": "event",
        "source_tag": "user_declared",
        "status_tag": "provisional",
        "confidence": 0.0,
        "evidence_refs": ["author_query:2"],
        "notes": null
      }
    }
  ],
  "knowledge_states": [],
  "symbolic_loads": [],
  "uncertainties": [
    {
      "id": "uncertainty_hist_001",
      "unknown_area": "logistics",
      "affected_object_ids": ["event_proposal_crackdown_001"],
      "ambiguity_class": "underdetermined",
      "candidate_interpretations": [
        "The crackdown is pre-scheduled well in advance.",
        "Local governors act on standing contingency orders.",
        "The action is only same-day within one region, not all six cities."
      ],
      "recommended_handling": "branch_multiple",
      "metadata": {
        "id": "uncertainty_hist_001",
        "layer": "institutional",
        "source_tag": "structurally_inferred",
        "status_tag": "provisional",
        "confidence": 0.64,
        "evidence_refs": ["author_query:2"],
        "notes": "The event could become plausible if reframed as decentralized preplanning rather than live same-day coordination."
      }
    }
  ],
  "continuity": {
    "causal_continuity": {"status": "stable", "notes": null},
    "temporal_continuity": {"status": "broken", "notes": "Same-day synchronization conflicts with communication constraints as stated."},
    "spatial_continuity": {"status": "stable", "notes": null},
    "character_continuity": {"status": "unknown", "notes": null},
    "knowledge_continuity": {"status": "unknown", "notes": null},
    "thematic_continuity": {"status": "unknown", "notes": null},
    "consequence_continuity": {"status": "unknown", "notes": null}
  },
  "narrative_context": {
    "current_mode": "validation",
    "requested_output_form": "audit",
    "tone_profile": [],
    "genre_frame": ["historical_fiction"],
    "historical_frame": "pre-telegraph frontier kingdom",
    "scale_focus": "system",
    "user_constraints": ["same_day", "six_distant_cities"]
  },
  "provenance_log": [
    {
      "id": "prov_hist_001",
      "object_id": "event_proposal_crackdown_001",
      "operation": "validated",
      "method": "historical plausibility pass",
      "input_refs": ["author_query:2"],
      "notes": "Likely verdict: contradictory as stated; plausible with setup if changed to pre-coordinated regional triggers."
    }
  ]
}
```

### Likely Validation Reading

- likely verdict: **contradictory** as currently phrased
- likely repair: **possible\_with\_setup** if the crackdown is preplanned, regionally delegated, or staggered rather than live synchronized

---

## Fixture Design Notes

These fixtures are intentionally varied in scale and purpose.

### Coverage Achieved

- minimal fragment expansion
- character motivation audit
- worldbuilding emergence
- next-event continuity check
- historical plausibility audit

### Schema Pressure-Test Results

The schema appears capable of holding:

- sparse scenes
- mixed recovered and inferred layers
- validation proposals as provisional events
- continuity stress states
- branchable world outcomes

### Emerging Implementation Advice

For a first prototype, proposals should probably be represented as provisional events or assertions attached to the main state rather than as wholly separate structures. That keeps validation close to continuity and consequence tracking.

---

# OUTPUT TEMPLATES V1

## Expansion and Validation Response Shapes

This section defines the standard response formats the engine should use when returning results.

The purpose of output templates is not cosmetic consistency alone. They ensure the following:

- internal rigor is reflected in the response
- support, uncertainty, and constraint remain visible
- different task types produce outputs suited to real user workflows
- the engine does not hide weak grounding behind fluent prose

These templates may be rendered in natural language, semi-structured form, or strict JSON, depending on implementation context.

---

## Output Design Objectives

All engine outputs should aim to be:

1. **readable** — understandable without requiring the user to inspect raw state objects
2. **traceable** — grounded in identifiable supports, constraints, and operator logic
3. **proportionate** — no stronger or more ornate than the underlying support warrants
4. **task-matched** — shaped for the user’s actual job
5. **fail-soft** — capable of returning useful partial results under uncertainty

---

## Common Output Envelope

Every major response may be represented in this generalized form.

```json
{
  "task_type": "expand | validate | translate | compare | branch | diagnose",
  "mode": "expansion | validation | translation | mixed",
  "summary": "string",
  "result": {},
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

### Notes

- `summary` should be readable and direct.
- `result` contains the task-specific payload.
- `support_basis` lists the main reasons or state anchors.
- `uncertainties` should remain visible whenever load-bearing support is thin.
- `next_useful_moves` should help the user progress rather than merely observe.

---

## Template Family A — Expansion Outputs

Expansion outputs build narrative or structural space from the current state model.

### A1. Scene Expansion Template

#### Use Case

- scene generation
- moment expansion
- turning a fragment into a scene premise or playable beat

#### Template

```json
{
  "task_type": "expand",
  "mode": "expansion",
  "summary": "string",
  "result": {
    "scene_premise": "string",
    "active_pressures": ["string"],
    "active_constraints": ["string"],
    "actor_positions": ["string"],
    "probable_turn": ["string"],
    "scene_render": "string"
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- `scene_render` may be omitted in stricter or more analytical modes.
- `probable_turn` should reflect the state model, not just drama preference.

---

### A2. World Sketch Expansion Template

#### Use Case

- civilization emergence
- culture formation
- setting build from substrate or structural layers

#### Template

```json
{
  "task_type": "expand",
  "mode": "expansion",
  "summary": "string",
  "result": {
    "derived_pressures": ["string"],
    "settlement_patterns": ["string"],
    "institutional_tendencies": ["string"],
    "economic_logics": ["string"],
    "symbolic_forms": ["string"],
    "conflict_types": ["string"],
    "world_sketch": "string"
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- when institutional outcomes remain branchable, the response should say so
- symbolic forms should not be presented as settled if they are only archetypally inferred

---

### A3. Branch Map Template

#### Use Case

- possibility-space exploration
- “what happens next?” queries
- scenario branching

#### Template

```json
{
  "task_type": "branch",
  "mode": "expansion",
  "summary": "string",
  "result": {
    "high_support_branches": ["string"],
    "conditional_branches": ["string"],
    "low_support_branches": ["string"],
    "blocked_branches": ["string"],
    "branch_drivers": ["string"]
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- blocked branches should be included when valuable, especially in design or debugging contexts
- high-support branches should be clearly separated from merely imaginable branches

---

## Template Family B — Validation Outputs

Validation outputs evaluate a proposal against the state model.

### B1. Core Validation Template

#### Use Case

- general-purpose adjudication
- next-event checks
- world plausibility checks
- symbolic fit checks

#### Template

```json
{
  "task_type": "validate",
  "mode": "validation",
  "summary": "string",
  "result": {
    "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
    "load_bearing_layers": ["string"],
    "main_supports": ["string"],
    "main_blockers": ["string"],
    "missing_bridges": ["string"],
    "smallest_fix": ["string"],
    "nearby_alternatives": ["string"]
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- `main_blockers` should include hard blocks or the strongest stresses
- `smallest_fix` should preserve the user’s intention where possible
- `nearby_alternatives` are useful when the proposed move is weak but adjacent stronger moves exist

---

### B2. Character Audit Template

#### Use Case

- “would this character do this?”
- reaction plausibility
- betrayal, forgiveness, sacrifice, refusal, confession, concealment

#### Template

```json
{
  "task_type": "validate",
  "mode": "validation",
  "summary": "string",
  "result": {
    "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
    "motive_alignment": ["string"],
    "knowledge_checks": ["string"],
    "continuity_stresses": ["string"],
    "setup_gaps": ["string"],
    "smallest_fix": ["string"],
    "alternate_actions": ["string"]
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- output should distinguish between motive conflict and outright motive contradiction
- alternate actions should stay near the character’s current state, not jump to a different story entirely

---

### B3. Historical Plausibility Template

#### Use Case

- logistics checks
- communication, technology, institutional, and timing plausibility
- historical fiction audits

#### Template

```json
{
  "task_type": "validate",
  "mode": "validation",
  "summary": "string",
  "result": {
    "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
    "historical_supports": ["string"],
    "logistical_constraints": ["string"],
    "timing_constraints": ["string"],
    "institutional_constraints": ["string"],
    "reframing_options": ["string"]
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- the engine should separate “as stated” plausibility from “with revised framing” plausibility
- rare-but-possible should not be mislabeled as impossible

---

### B4. Continuity Check Template

#### Use Case

- next-scene validation
- pacing checks
- sequence and consequence integrity

#### Template

```json
{
  "task_type": "validate",
  "mode": "validation",
  "summary": "string",
  "result": {
    "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
    "causal_status": ["string"],
    "temporal_status": ["string"],
    "knowledge_status": ["string"],
    "consequence_status": ["string"],
    "bridge_beats": ["string"],
    "stronger_adjacent_moves": ["string"]
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- `bridge_beats` are often the most valuable part of the output
- adjacent moves should feel like natural continuations, not random alternatives

---

## Template Family C — Translation Outputs

Translation outputs preserve structure while moving from one representation into another.

### C1. Structural Translation Template

#### Use Case

- prose to structure
- historical case to generalized scenario
- world notes to state model
- narrative fragment to implied pressures and branches

#### Template

```json
{
  "task_type": "translate",
  "mode": "translation",
  "summary": "string",
  "result": {
    "source_specific_elements": ["string"],
    "normalized_structure": ["string"],
    "preserved_features": ["string"],
    "abstracted_features": ["string"],
    "translated_output": "string"
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- translation should not erase source-layer distinctions
- what was abstracted should remain visible to avoid false equivalence

---

## Template Family D — Comparative Outputs

Comparative outputs help the user weigh multiple options or state variants.

### D1. Path Comparison Template

#### Use Case

- compare multiple next events
- compare alternate world designs
- compare character choices

#### Template

```json
{
  "task_type": "compare",
  "mode": "mixed",
  "summary": "string",
  "result": {
    "options": ["string"],
    "comparative_support": ["string"],
    "best_supported": ["string"],
    "most_thematically_aligned": ["string"],
    "highest_risk_option": ["string"],
    "notes_on_tradeoffs": ["string"]
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

---

## Template Family E — Diagnostic Outputs

Diagnostic outputs are especially useful when something feels wrong but the user cannot yet say why.

### E1. Narrative Problem Diagnosis Template

#### Use Case

- “something feels off here”
- weak scene diagnosis
- implausible chain debugging
- continuity troubleshooting

#### Template

```json
{
  "task_type": "diagnose",
  "mode": "validation",
  "summary": "string",
  "result": {
    "symptom": ["string"],
    "root_causes": ["string"],
    "affected_layers": ["string"],
    "operator_failures_or_gaps": ["string"],
    "smallest_repairs": ["string"],
    "what_not_to_change": ["string"]
  },
  "support_basis": ["string"],
  "uncertainties": ["string"],
  "next_useful_moves": ["string"],
  "confidence": 0.0
}
```

#### Guidance

- `what_not_to_change` is useful because users often need to preserve the good parts of a scene or design while fixing the weak part

---

## Natural Language Rendering Rules

The engine should be able to render the same result in readable prose while preserving structure.

### Expansion Rendering Pattern

Use:

- one concise summary of what the engine built from
- one section on the main derived pressures or structures
- one section on the resulting narrative space
- one section on uncertainty or branchability, when needed

### Validation Rendering Pattern

Use:

- verdict first
- then the strongest support or blocker
- then the missing setup, if relevant
- then the smallest useful fix or nearest stronger alternative

### Translation Rendering Pattern

Use:

- what the source is doing specifically
- what structure it reduces to
- what remains unique after abstraction

### Rule

Readable prose must preserve the same distinctions as the structured payload:

- support vs inference
- blocker vs missing bridge
- possible vs earned
- settled vs branchable

---

## Output Compression Modes

Different contexts require different output density.

### Short Mode

Use when:

- the user asks for fast adjudication
- the proposal is simple
- the main issue is obvious

**Structure:**

- summary
- verdict or primary result
- one or two key reasons
- one next useful move

### Standard Mode

Use by default.

**Structure:**

- summary
- full result payload
- support basis
- uncertainty or gaps
- next moves

### Deep Mode

Use when:

- multiple layers are in tension
- the user is doing design or debugging
- the decision is load-bearing for the larger work

**Structure:**

- standard mode, plus
- explicit load-bearing layers
- missing layers
- reasoning trace or operator chain
- comparison or branch analysis, where useful

---

## Fail-Soft Output Rules

When the engine lacks enough support for a strong answer, it should not fail uselessly.

### Weak Input Expansion

Return:

- a sparse build
- identified uncertainties
- multiple candidate paths, if needed

### Weak Input Validation

Return:

- a provisional verdict or restraint
- what is missing
- what one added detail would most improve the judgment

### Contradictory Mixed Input

Return:

- the contradiction
- the affected layers
- either branch options or the minimum reconciliation move

---

## Output Safety Rules

### 1. Do Not Hide Missing Support

A polished paragraph must not conceal a weak state basis.

### 2. Do Not Over-Promote Inferred Material

If a key idea is inferred, keep it framed as inferred even in prose.

### 3. Do Not Mutate the Underlying State in the Response Layer

Suggestions, alternatives, and render variants should not overwrite the core model unless the user adopts them.

### 4. Do Not Confuse Recommendation with Judgment

“Here is a stronger alternative” is not the same as “your current move is impossible.”

### 5. Keep Recommendations Local When Possible

The best fix is often the smallest plausible bridge, not a total rewrite.

---

## Example Summary Patterns

### Character Audit Summary

`This action is possible with setup: the pressure and duty logic are there, but the character’s strongest established pattern still points the other way.`

### Historical Plausibility Summary

`As stated, this breaks the setting’s communication constraints, but a pre-coordinated version could work.`

### Worldbuilding Expansion Summary

`These substrate conditions strongly favor maritime adaptation, distributed port power, and a symbolic culture shaped by recurring danger.`

### Continuity Summary

`This beat is strained as the immediate next move because the prior revelation should alter the character’s public behavior before escalation resumes.`

---

## Output Templates Summary

The response layer should make the engine feel both sharp and usable. It should not dump raw internals, but it also must not conceal the basis of judgment.

In short:

**the engine should answer in forms people can work with, while keeping support, uncertainty, and repair paths visible.**

---

# MINIMAL END-TO-END WORKFLOW V1

## One Complete Engine Pass

This section defines a minimal but complete operational workflow for the engine.

The purpose is to prove that the current pieces can compose into a coherent run from raw user input to usable output. This is not yet the full production runtime. It is the smallest end-to-end pass that demonstrates the engine’s architecture in action.

---

## Workflow Objective

A complete engine pass should be able to:

1. ingest a user query and source material
2. determine the actual task
3. build or update the canonical state model
4. select the relevant operators and load-bearing layers
5. perform either expansion, validation, translation, or a mixed pass
6. produce a response using the correct output template
7. preserve provenance, uncertainty, and minimal traceability

---

## Minimal Run Signature

A minimal engine pass can be represented like this.

```json
{
  "run_id": "run_001",
  "input_query": "string",
  "source_bundle": "string | object | list",
  "task_type": "expand | validate | translate | compare | branch | diagnose",
  "strictness": "lenient | default | strict",
  "state_before": "state_id | null",
  "state_after": "state_id",
  "selected_layers": ["string"],
  "selected_operators": ["string"],
  "output_template": "string",
  "result": {}
}
```

---

## End-to-End Stages

### Stage 1 — Intake

#### Purpose

Determine what the user is asking for and what material is available.

#### Inputs

- user query
- any attached text, notes, data, story fragments, proposals, or prior state

#### Tasks

- parse the explicit task request
- identify whether the user is asking to expand, validate, translate, compare, branch, or diagnose
- detect whether the query includes a proposal under judgment
- detect desired strictness, if stated
- detect desired output form, if stated

#### Output

An intake summary object.

```json
{
  "task_type": "validate",
  "proposal_present": true,
  "desired_output_form": "audit",
  "strictness": "default",
  "source_inputs": ["chapter summary", "proposed action"]
}
```

#### Minimal Rule

If the query is ambiguous, prefer the task most strongly implied by the phrasing.

**Example:**

- “Would she really do this?” → validate
- “Build from this” → expand
- “What pattern is this?” → translate or diagnose

---

### Stage 2 — Source Classification

#### Purpose

Determine what kind of material the engine is processing.

#### Tasks

- classify each source item
- estimate evidence density
- identify mixed-source conditions
- detect whether the source is mostly declarative, descriptive, narrative, or schematic

#### Output

A source profile.

```json
{
  "input_mode": "mixed_bundle",
  "evidence_density": "moderate",
  "source_classes": ["prose_narrative", "proposal"],
  "layer_mode": "mixed"
}
```

#### Minimal Rule

The engine must not treat all text as the same kind of object. A proposal is not the same as an established event, and a scene seed is not the same as a rich chapter summary.

---

### Stage 3 — Layer Registration

#### Purpose

Capture any explicitly declared layers and recover any clearly present layers.

#### Tasks

- register declared user layers
- recover source-present layers
- note missing but likely load-bearing layers
- identify obvious layer tensions or contradictions

#### Output

A layer map.

```json
{
  "declared_layers": ["symbolic"],
  "recovered_layers": ["character", "event"],
  "missing_load_bearing_layers": ["knowledge"],
  "layer_relations": ["character-event: aligned", "symbolic-event: underspecified"]
}
```

#### Minimal Rule

Do not invent bridge layers yet unless they are needed to perform the task. Registration comes before expansion.

---

### Stage 4 — State Population or State Update

#### Purpose

Create a new canonical state model or update an existing one.

#### Tasks

- create or load the root state object
- populate entities, events, motives, constraints, pressures, uncertainties, and continuity as warranted
- represent proposals as provisional objects when under evaluation
- attach provenance and status tags
- preserve missingness where support is thin

#### Output

A minimally usable state.

#### Minimal Rule

The state should be no richer than the evidence warrants, but it should be rich enough to support the requested task.

---

### Stage 5 — Task Routing

#### Purpose

Map the user’s real task to the correct engine behavior.

#### Routing Table

| User Intent                        | Mode        | Core Subtask                              |
| ---------------------------------- | ----------- | ----------------------------------------- |
| Build from a fragment or condition | expansion   | derive and render                         |
| Judge a proposed move              | validation  | support / block / missing-bridge analysis |
| Convert one form into another      | translation | structural mapping                        |
| Map alternatives                   | branch      | generate and prune branches               |
| Compare options                    | compare     | weighted relative support                 |
| Find what is wrong                 | diagnose    | reverse-trace and stress detection        |

#### Minimal Rule

Mixed queries may chain modes.

**Example:**

- “Give me three possible next moves and tell me which one feels most earned” → branch → validate → compare

---

### Stage 6 — Load-Bearing Layer Selection

#### Purpose

Identify which layers actually matter for the current task.

#### Tasks

- select task-relevant layers
- mark absent but required layers
- weaken confidence if required layers are sparse or inferred only

#### Example

Character action audit:

- character
- motive
- event
- knowledge
- continuity

#### Minimal Rule

Do not consult every layer equally. Use only the layers needed for the task, but surface absent load-bearing layers explicitly.

---

### Stage 7 — Operator Selection

#### Purpose

Choose the smallest sufficient operator chain.

#### Tasks

- select operators based on task type, input richness, and strictness
- avoid unnecessary operator spread
- preserve operator traceability for major results

#### Example Chains

**Character audit**

- Motive Inference
- Knowledge Propagation
- Setup Sufficiency Check
- Plausibility Envelope Check

**World emergence**

- Substrate Derivation
- Constraint Projection
- Pressure Formation
- Agency Emergence
- Symbolic Crystallization
- Rendering Selection

#### Minimal Rule

Prefer the shortest sufficient operator chain over maximal reasoning.

---

### Stage 8 — Core Evaluation or Expansion Pass

#### Purpose

Perform the engine’s main work.

#### For Expansion

- derive pressures, structures, actors, symbols, or branches
- keep branchable outcomes branchable
- preserve uncertainty

#### For Validation

- check state sufficiency
- detect hard blocks
- collect positive supports
- detect missing bridges
- map to verdict

#### For Translation

- recover source-specific structure
- normalize to canonical form
- re-render into target form

#### Minimal Rule

This stage should modify or annotate the state model as needed, but it should not quietly convert provisional inferences into settled facts.

---

### Stage 9 — Result Packaging

#### Purpose

Select the correct output template and assemble the response payload.

#### Tasks

- choose the template family
- fill summary and result fields
- include support basis
- include uncertainty notes
- include next useful moves

#### Minimal Rule

The response should match the user’s workflow. A writer asking for a motivation audit does not need a worldbuilding sketch, and a scenario designer asking for branches does not need a single binary verdict.

---

### Stage 10 — Response Rendering

#### Purpose

Render the result in readable form while preserving distinctions.

#### Tasks

- render the summary
- render the core payload
- preserve support vs inference vs uncertainty distinctions
- choose short, standard, or deep output density

#### Minimal Rule

Do not let prose erase uncertainty or upgrade speculative material.

---

### Stage 11 — Trace and Revision Hooks

#### Purpose

Leave the run in a state that can be iterated on.

#### Tasks

- log selected operators
- log state changes or proposal status
- preserve unresolved uncertainties
- expose the most useful next revision move

#### Minimal Rule

The engine should support iterative work. A good run ends with a better state and a cleaner next move.

---

## Workflow Diagram — Compact Form

```text
User Query + Source Material
    ↓
Intake
    ↓
Source Classification
    ↓
Layer Registration
    ↓
State Population / Update
    ↓
Task Routing
    ↓
Load-Bearing Layer Selection
    ↓
Operator Selection
    ↓
Core Expansion / Validation / Translation Pass
    ↓
Result Packaging
    ↓
Response Rendering
    ↓
Trace + Revision Hooks
```

---

## Worked Example 1 — Character Action Audit

### User Query

`Would Mara really abandon Teren here to save the rebellion?`

### Run Sketch

#### Stage 1 — Intake

- task\_type: validate
- proposal\_present: true
- output\_form: audit

#### Stage 2 — Source Classification

- input\_mode: mixed\_bundle
- evidence\_density: moderate

#### Stage 3 — Layer Registration

- recovered: character, event
- inferred needed: knowledge continuity, motive conflict intensity

#### Stage 4 — State Population

- load prior character and event state
- represent the proposed abandonment as a provisional event

#### Stage 5 — Task Routing

- validation mode

#### Stage 6 — Load-Bearing Layers

- character
- motive
- event
- knowledge
- continuity

#### Stage 7 — Operator Selection

- Motive Inference
- Knowledge Propagation
- Setup Sufficiency Check
- Plausibility Envelope Check

#### Stage 8 — Core Pass

- no hard knowledge block
- strong duty pressure exists
- the protective motive still dominates
- missing bridge: a further emotional or strategic break point

#### Stage 9 — Result Packaging

- output template: Character Audit Template

#### Stage 10 — Response Rendering

Possible summary:\
`This is possible with setup: the strategic pressure is real, but the current character pattern still points toward protection rather than abandonment.`

#### Stage 11 — Revision Hook

- suggested next move: add one scene showing Mara internalize that saving Teren now would doom the wider cause

---

## Worked Example 2 — Civilization Emergence

### User Query

`Given these island conditions, what kind of civilization arises here?`

### Run Sketch

#### Stage 1 — Intake

- task\_type: expand
- proposal\_present: false
- output\_form: world\_sketch

#### Stage 2 — Source Classification

- input\_mode: structured\_data
- evidence\_density: sparse

#### Stage 3 — Layer Registration

- recovered: physical
- inferred likely: economic, symbolic, institutional

#### Stage 4 — State Population

- populate the physical substrate and core pressures
- mark institutional outcomes as branchable

#### Stage 5 — Task Routing

- expansion mode

#### Stage 6 — Load-Bearing Layers

- physical
- ecological or economic
- symbolic

#### Stage 7 — Operator Selection

- Substrate Derivation
- Constraint Projection
- Pressure Formation
- Agency Emergence
- Symbolic Crystallization
- Rendering Selection

#### Stage 8 — Core Pass

- derive maritime dependence
- derive distributed port power
- derive recurring danger as a source of ritual meaning

#### Stage 9 — Result Packaging

- output template: World Sketch Expansion Template

#### Stage 10 — Response Rendering

Possible summary:\
`These conditions strongly favor maritime societies organized around ports, salvage, navigation, and recurring sacred interpretations of danger.`

#### Stage 11 — Revision Hook

- suggested next move: choose whether port governance is league-based, temple-based, or monarchic

---

## Worked Example 3 — Historical Plausibility Check

### User Query

`Could a pre-telegraph queen coordinate a same-day crackdown across six distant cities?`

### Run Sketch

#### Stage 1 — Intake

- task\_type: validate
- proposal\_present: true
- output\_form: audit

#### Stage 2 — Source Classification

- input\_mode: notes
- evidence\_density: sparse

#### Stage 3 — Layer Registration

- declared: institutional, temporal
- missing but required: logistical specifics

#### Stage 4 — State Population

- represent the crackdown as a provisional event
- populate the communications constraint

#### Stage 5 — Task Routing

- validation mode

#### Stage 6 — Load-Bearing Layers

- institutional
- temporal
- logistical
- political

#### Stage 7 — Operator Selection

- Constraint Projection
- Temporal Sequencing
- Plausibility Envelope Check

#### Stage 8 — Core Pass

- hard block: communication speed undercuts same-day live coordination
- possible bridge: decentralized preplanned triggers

#### Stage 9 — Result Packaging

- output template: Historical Plausibility Template

#### Stage 10 — Response Rendering

Possible summary:\
`As stated, this is contradictory to the communication conditions, but a pre-coordinated version could become plausible.`

#### Stage 11 — Revision Hook

- suggested next move: reframe the operation as standing contingency orders executed on a known signal window

---

## Minimal Workflow Guarantees

A valid engine pass should always be able to answer, internally or visibly:

1. What task was performed?
2. What state was used or created?
3. Which layers mattered most?
4. Which operators were applied?
5. What support or blocks determined the result?
6. What remains uncertain?
7. What is the next most useful move?

If the engine cannot answer those, the run is under-instrumented.

---

## Workflow Failure Modes to Avoid

### 1. Premature Richness

Building too much state too early from thin input.

### 2. Operator Flooding

Using too many operators when a short chain would suffice.

### 3. Layer Smearing

Blending symbolic, physical, and character logic into one indistinct explanation.

### 4. Verdict Without Sufficiency

Issuing strong judgment without the needed layers.

### 5. Elegant Output, Hidden Weakness

Producing polished prose that conceals missing supports or contradictions.

---

## End-to-End Workflow Summary

The engine works by moving from user intent and source material into a bounded internal state, then selecting only the layers and operators necessary to produce a grounded expansion or judgment.

In short:

**intake determines the job, state determines the reality, operators do the work, and templates make the result usable.**

---

# MINIMAL IMPLEMENTATION MODULES V1

## First-Prototype Architecture

This section defines the smallest viable module layout for a first working prototype.

The purpose is not architectural grandeur. The purpose is to identify the minimum set of components needed to run a useful validation-first vertical slice.

At this stage, the engine should be treated as a **thin, testable pipeline**, not as a fully generalized platform.

---

## Prototype Boundary

### What the First Prototype Should Do Well

- classify a user request into a task type
- build or update a minimal canonical state from sparse or moderate inputs
- represent a proposal as a provisional object inside the state
- select the load-bearing layers for the task
- run a short operator chain
- return a grounded validation result in a stable output shape

### What the First Prototype Should Not Try to Do Yet

- full open-ended world generation across every mode
- deep autonomous revision planning
- elaborate symbolic systems beyond lightweight support
- long-memory project management
- generalized scoring across every possible narrative dimension
- invisible automatic state mutation without user review

### Prototype Thesis

The first prototype should prioritize **validation over generation**.

That means it should be strongest at:

- character action audits
- next-event continuity checks
- historical plausibility checks

These are the sharpest use cases, the easiest to test, and the hardest to fake with style alone.

---

## Core Module Set

A first prototype should have six primary modules and one optional harness.

1. Intake and Task Router
2. State Builder and Updater
3. Layer Resolver
4. Operator Selector and Runner
5. Validation Engine
6. Response Renderer
7. Optional: Test Harness and Fixture Runner

---

## Module 1 — Intake and Task Router

### Purpose

Convert user input into a normalized task request.

### Responsibilities

- parse the user query
- detect whether the task is expand, validate, translate, compare, branch, or diagnose
- detect whether a proposal is present
- detect explicit strictness or output preferences
- classify source bundle type at a coarse level

### Inputs

- raw user query
- attached source material or prior state reference

### Outputs

```json
{
  "task_type": "validate",
  "proposal_present": true,
  "strictness": "default",
  "desired_output_form": "audit",
  "source_profile": {
    "input_mode": "mixed_bundle",
    "evidence_density": "moderate"
  }
}
```

### Non-Goals

- deep narrative reasoning
- detailed state extraction
- verdict assignment

### Implementation Note

For MVP, this module can be rule-based rather than learned.

---

## Module 2 — State Builder and Updater

### Purpose

Create a new canonical state or update an existing one from the source bundle.

### Responsibilities

- instantiate the root state object
- extract or register entities, events, motives, pressures, constraints, knowledge states, and uncertainties
- represent proposals as provisional events or assertions
- attach provenance and status tags
- preserve missingness where evidence is thin

### Inputs

- normalized task request
- source bundle
- optional prior state

### Outputs

- canonical state object

### Non-Goals

- heavy operator reasoning
- final verdict logic
- prose rendering

### Implementation Note

For MVP, extraction can be shallow and template-driven. The goal is not exhaustive state richness; it is sufficient state for validation.

---

## Module 3 — Layer Resolver

### Purpose

Determine which layers are present, which are inferred, and which are load-bearing for the current task.

### Responsibilities

- register declared layers
- recover source-present layers
- mark inferred bridge layers when needed
- detect missing load-bearing layers
- identify obvious layer tensions and contradictions

### Inputs

- canonical state object
- task type

### Outputs

```json
{
  "active_layers": ["character", "event", "knowledge", "continuity"],
  "missing_layers": ["motive"],
  "layer_tensions": ["character-event: in_tension"]
}
```

### Non-Goals

- final validation
- response formatting

### Implementation Note

This module is where the layer protocol becomes executable rather than merely descriptive.

---

## Module 4 — Operator Selector and Runner

### Purpose

Choose and execute the shortest sufficient operator chain for the task.

### Responsibilities

- select operators based on task type, strictness, and available state
- run only the needed operators
- preserve a minimal reasoning trace
- avoid unnecessary operator spread

### Inputs

- canonical state object
- task type
- active layer set
- strictness

### Outputs

```json
{
  "selected_operators": [
    "Motive Inference",
    "Knowledge Propagation",
    "Setup Sufficiency Check",
    "Plausibility Envelope Check"
  ],
  "operator_trace": ["string"]
}
```

### Non-Goals

- final language rendering
- long multi-branch simulation

### Implementation Note

For MVP, only implement the operator subset required by the validation-first slice.

---

## Module 5 — Validation Engine

### Purpose

Turn evaluated state into a verdict with reasons, blockers, and repair guidance.

### Responsibilities

- check state sufficiency
- detect hard blocks
- collect positive supports
- detect missing bridges
- map findings to the verdict set
- generate the minimal constructive guidance package

### Inputs

- canonical state object
- layer resolution output
- operator output
- proposal object

### Outputs

```json
{
  "verdict": "possible_with_setup",
  "main_supports": ["string"],
  "main_blockers": ["string"],
  "missing_bridges": ["string"],
  "smallest_fix": ["string"],
  "confidence": 0.71
}
```

### Non-Goals

- scene prose generation
- generalized world expansion beyond what the verdict requires

### Implementation Note

This is the core of the first prototype. If this module is weak, the whole system will feel decorative.

---

## Module 6 — Response Renderer

### Purpose

Render the result into the correct output template and natural-language form.

### Responsibilities

- select the matching output template
- populate summary, result, support basis, uncertainties, and next useful moves
- render short, standard, or deep mode
- preserve support vs inference vs missing-bridge distinctions

### Inputs

- validation or expansion result object
- narrative context
- requested output form

### Outputs

- structured payload
- optional natural-language rendering

### Non-Goals

- internal reasoning
- implicit state rewriting

### Implementation Note

This module should stay thin. It is a formatter, not a second reasoning engine.

---

## Optional Module 7 — Test Harness and Fixture Runner

### Purpose

Run golden-path fixtures against the prototype and compare outputs to expected verdict patterns.

### Responsibilities

- load fixture states
- run a module sequence end to end
- record outputs
- compare verdicts and key reasoning features against expectations

### Suggested Initial Fixtures

- Mara abandonment audit
- detective gala accusation continuity check
- pre-telegraph crackdown plausibility check

### Implementation Note

This module is optional in code organization, but it is not optional in practice. Without it, the prototype will drift fast.

---

## Module Dependency Order

The modules should depend on one another in this order:

```text
Intake and Task Router
    ↓
State Builder and Updater
    ↓
Layer Resolver
    ↓
Operator Selector and Runner
    ↓
Validation Engine
    ↓
Response Renderer
```

### Rule

Do not let the renderer or the router perform deep validation logic. Keep responsibility boundaries clean.

---

## Minimal Interfaces

These are the smallest stable interfaces worth preserving in the first prototype.

### Interface A — Normalized Task Request

Produced by the router and consumed by downstream modules.

```json
{
  "task_type": "validate",
  "proposal_present": true,
  "strictness": "default",
  "desired_output_form": "audit"
}
```

### Interface B — Canonical State

Produced by the state builder and consumed by the layer resolver, operator runner, and validation engine.

```json
{
  "state_id": "string",
  "input_profile": {},
  "layers": [],
  "entities": [],
  "relations": [],
  "pressures": [],
  "constraints": [],
  "motives": [],
  "events": [],
  "knowledge_states": [],
  "uncertainties": [],
  "continuity": {},
  "narrative_context": {}
}
```

### Interface C — Evaluation Packet

Produced by the operator runner and layer resolver, then consumed by the validation engine.

```json
{
  "active_layers": ["string"],
  "missing_layers": ["string"],
  "selected_operators": ["string"],
  "supports": ["string"],
  "blocks": ["string"],
  "missing_bridges": ["string"]
}
```

### Interface D — Response Payload

Produced by the validation engine and renderer.

```json
{
  "summary": "string",
  "verdict": "supported | plausible | possible_with_setup | strained | contradictory",
  "main_supports": ["string"],
  "main_blockers": ["string"],
  "missing_bridges": ["string"],
  "smallest_fix": ["string"],
  "confidence": 0.0
}
```

---

## Recommended MVP Build Order

### Step 1

Implement the Intake and Task Router with only three recognized validation tasks:

- character action audit
- next-event continuity check
- historical plausibility check

### Step 2

Implement the State Builder only deeply enough to populate:

- entities
- events
- motives
- constraints
- pressures
- knowledge states
- uncertainties
- continuity

### Step 3

Implement the Layer Resolver with task-specific load-bearing layer sets.

### Step 4

Implement only this operator subset:

- Motive Inference
- Knowledge Propagation
- Setup Sufficiency Check
- Temporal Sequencing
- Plausibility Envelope Check

### Step 5

Implement the Validation Engine and verdict mapping rules.

### Step 6

Implement the Response Renderer for:

- Character Audit Template
- Continuity Check Template
- Historical Plausibility Template

### Step 7

Run the golden fixtures and compare results.

### Rule

Do not implement world-generation modules first. They will make the prototype look more impressive while making it much harder to tell whether the core reasoning is actually working.

---

## Prototype Vertical Slice

The cleanest first slice is:

```text
User asks validation question
    ↓
Router identifies validation task
    ↓
State builder creates or updates minimal state
    ↓
Layer resolver identifies load-bearing layers
    ↓
Operator runner executes short validation chain
    ↓
Validation engine assigns verdict
    ↓
Renderer returns structured audit
```

### Why This Slice First

- it is easy to evaluate
- it rewards discipline over style
- it directly serves author and scenario use cases
- it forces the state model, layer protocol, operator logic, and verdict logic to work together

---

## Prototype Success Criteria

The first prototype is succeeding if it can do the following reliably:

1. classify the three target validation queries correctly
2. produce a minimally sufficient state without overfilling it
3. flag missing load-bearing layers rather than hiding them
4. distinguish hard blocks from missing bridges
5. return one of the five verdicts consistently
6. give a useful smallest-fix recommendation
7. stay consistent across the golden fixtures

### Prototype Failure Signs

- outputs sound persuasive but do not reference real supports or blocks
- the system overuses `possible_with_setup` as a hedge for everything
- hard contradictions are softened into vague plausibility language
- the state builder invents too much unseen motive or world detail
- the renderer upgrades weak inference into confident prose

---

## Build-Now / Build-Later Split

### Build Now

- validation-first vertical slice
- golden fixtures
- module interfaces
- verdict consistency
- reasoning traceability

### Build Later

- broader expansion mode
- multi-branch comparative tooling
- richer symbolic modeling
- revision diffing
- scoring models
- long-session state management

---

## Minimal Implementation Modules Summary

The first prototype should be small, hard-edged, and testable. It should prove that the engine can judge narrative moves against a structured reality model before it tries to become an all-purpose narrative machine.

In short:

**build the adjudication spine first, prove it on fixtures, and let generation wait until the reasoning layer earns it.**

---

# TEST CASES AND EVALUATION CRITERIA V1

## First-Prototype Test Suite

This section defines how the first prototype should be tested and how success should be judged.

The purpose is not to create a large benchmark. The purpose is to create a **small, sharp, reality-checking suite** that can reveal whether the prototype is actually reasoning from state, layers, and constraints rather than merely producing persuasive language.

At this stage, evaluation should focus on the validation-first vertical slice.

---

## Evaluation Objectives

The first prototype should be evaluated on whether it can:

1. classify the user’s task correctly
2. build a minimally sufficient state without overfilling it
3. select the right load-bearing layers
4. distinguish hard blocks from missing bridges
5. assign the right verdict with useful reasoning
6. avoid upgrading weak inference into confident prose
7. provide a small, actionable repair path when the proposal is weak

---

## Golden Test Set

The first prototype should launch with a compact golden set built from the existing fixtures.

### Golden Test 1 — Character Action Audit

**Fixture:** Mara abandons Teren to save the rebellion.

**Primary Question:** Would Mara really do this here?

**Expected Behavior:**

- classify as `validate`
- treat proposal as provisional event
- select character, motive, event, knowledge, and continuity layers
- detect strong duty pressure and strong protective motive conflict
- detect no hard knowledge block
- detect missing setup rather than full contradiction
- likely verdict: `possible_with_setup`

**Failure Signals:**

- returns `supported` too early
- returns `contradictory` without acknowledging real pressure and duty alignment
- invents new motives not present in the fixture

---

### Golden Test 2 — Next-Event Continuity Check

**Fixture:** Detective privately learns suspect is innocent, then is proposed to accuse him publicly that same night.

**Primary Question:** Can this happen next?

**Expected Behavior:**

- classify as `validate`
- select event, temporal, knowledge, continuity, and character layers
- detect that knowledge continuity works against the proposed move
- detect character continuity stress
- identify that the move is not impossible, but weakly supported as stated
- likely verdict: `strained`

**Failure Signals:**

- treats the move as `supported` based only on generic drama logic
- ignores the exonerating knowledge state
- fails to suggest a bridge such as misdirection, coercion, or breakdown

---

### Golden Test 3 — Historical Plausibility Check

**Fixture:** Pre-telegraph queen coordinates same-day crackdown across six distant cities.

**Primary Question:** Could this happen in the setting as stated?

**Expected Behavior:**

- classify as `validate`
- select institutional, temporal, logistical, and political layers
- detect communications constraint as a hard block
- distinguish the phrasing “as stated” from possible reframings
- likely verdict: `contradictory`
- suggest reframing toward pre-coordination or delegated trigger conditions

**Failure Signals:**

- softens the contradiction into vague plausibility
- misses the timing and communication problem
- claims impossibility without offering a workable reframing

---

## Supporting Test Set

Beyond the golden three, the prototype should include a few narrow support tests.

### Support Test 4 — Sparse Input Restraint

**Input:** `"a hero came to a fork in the road"`

**Expected Behavior:**

- build only a sparse state
- preserve uncertainty around motive and stakes
- avoid inventing character identity or backstory
- allow branch generation without pretending to know the meaning of the fork

### Support Test 5 — Missing-Layer Honesty

**Input:** A character action question with no motive data.

**Expected Behavior:**

- identify missing load-bearing motive layer
- weaken confidence
- avoid a strong verdict
- say what additional input would make the judgment stronger

### Support Test 6 — Symbolic Restraint

**Input:** A single striking image with no repetition or thematic frame.

**Expected Behavior:**

- avoid calling symbolism fully supported
- mark any symbolic reading as provisional or archetypal

### Support Test 7 — Proposal vs Established Event Distinction

**Input:** A narrative question containing a proposed action.

**Expected Behavior:**

- preserve the proposed move as provisional
- avoid treating it as if it already occurred in continuity tracking

---

## Test Categories

The prototype should be judged across five categories.

### 1. Routing Accuracy

Did the system identify the correct task type?

### 2. State Discipline

Did the system build enough state to work, without inventing too much?

### 3. Layer Discipline

Did the system consult the right layers and name missing ones?

### 4. Verdict Quality

Did the system distinguish support, strain, contradiction, and missing setup correctly?

### 5. Repair Utility

Did the system provide a useful smallest fix, bridge, or reframing when the proposal was weak?

---

## Evaluation Rubric

Each test case can be scored on a 0–2 basis per category.

### Score Definitions

- **0** = failed or materially misleading
- **1** = partially correct but weak, incomplete, or overly vague
- **2** = clearly correct and operationally useful

### Rubric Table

| Category         | 0                                | 1                                  | 2                                                     |
| ---------------- | -------------------------------- | ---------------------------------- | ----------------------------------------------------- |
| Routing Accuracy | wrong task                       | partly ambiguous                   | correct task                                          |
| State Discipline | major invention or omission      | usable but noisy                   | minimal and well-bounded                              |
| Layer Discipline | wrong layers or missing key ones | partly right                       | correct load-bearing set with missing layers surfaced |
| Verdict Quality  | wrong or mushy verdict           | roughly right but weakly justified | strong verdict with proper support/block distinction  |
| Repair Utility   | no useful fix                    | generic fix                        | precise, minimal, and helpful fix                     |

### Maximum Score Per Test

10

---

## Pass Thresholds

For the first prototype, the threshold should be practical rather than perfectionist.

### Minimum Acceptable Threshold

- average score of **8/10** on the golden three
- no golden test scoring below **7/10**
- zero cases where a hard contradiction is presented as fully supported
- zero cases where missing load-bearing layers are hidden

### Strong Prototype Threshold

- average score of **9/10** on the golden three
- support tests averaging **8/10** or better
- smallest-fix suggestions judged useful by a human reviewer in most cases

---

## Critical Failure Conditions

The prototype should be considered not ready if any of the following occur repeatedly.

### 1. Style Over State

The output sounds persuasive but does not reflect actual state supports or blocks.

### 2. Hedge Collapse

The system overuses `possible_with_setup` whenever it is uncertain, instead of distinguishing strain from contradiction.

### 3. Over-Inference

The system invents motives, themes, institutions, or history not warranted by the source.

### 4. Hidden Missingness

The system produces strong verdicts without surfacing missing load-bearing layers.

### 5. Repair Failure

The system identifies a problem but cannot suggest a minimal actionable repair.

---

## Reasoning Trace Checks

In addition to verdict quality, each test should inspect whether the engine’s explanation preserves core distinctions.

### Required Distinctions

- proposal vs established state
- hard block vs missing bridge
- support vs inference
- possible vs earned
- settled outcome vs branchable outcome

### Rule

A prototype that gets the verdict right for the wrong reasons is still unstable.

---

## Human Review Questions

A lightweight human evaluation should accompany the structured scoring.

For each result, ask:

1. Does this feel grounded in the scenario rather than in generic storytelling habits?
2. Does it preserve the most important tension accurately?
3. Does it diagnose the weakness clearly, if there is one?
4. Does the suggested repair preserve the author’s intent?
5. Would a serious writer or designer find this genuinely useful?

These questions are especially important because a system can pass mechanical checks while still being unhelpful in practice.

---

## Regression Strategy

Every prototype revision should rerun the golden set.

### Required Regression Checks

- verdict stability on the three golden fixtures
- no loss of missing-layer honesty
- no new tendency to over-promote symbolic or motive inference
- no increase in overconfident summaries

### Rule

If a change improves fluency but worsens verdict discipline, it is a regression.

---

## Suggested Evaluation Output Format

A simple test report can use this structure.

```json
{
  "test_id": "golden_001",
  "task_routing": 2,
  "state_discipline": 2,
  "layer_discipline": 2,
  "verdict_quality": 1,
  "repair_utility": 2,
  "total": 9,
  "notes": [
    "Correct task classification.",
    "Correctly treated proposal as provisional.",
    "Verdict slightly soft; could distinguish strain from possible-with-setup more sharply."
  ]
}
```

---

## Evaluation Sequence for the First Prototype

### Step 1

Run the golden three manually and inspect the outputs closely.

### Step 2

Run the four support tests.

### Step 3

Score each test using the 0–2 rubric.

### Step 4

Review whether the reasoning trace preserves the required distinctions.

### Step 5

Revise only the weakest module, not the whole pipeline at once.

### Rule

When a test fails, diagnose whether the failure belongs to:

- routing
- state building
- layer selection
- operator selection
- verdict mapping
- rendering

Do not patch symptoms in the renderer when the actual problem lives upstream.

---

## Stop Rule for Spec Expansion

Once the prototype architecture and evaluation suite are defined, further specification work should slow down sharply.

At that point, the next meaningful progress should come from implementation and testing.

### Practical Stop Condition

If the document can already answer:

- what the prototype does
- which modules it has
- which fixtures it must pass
- how success is scored

then the specification is sufficient for a first build.

This document is now very close to that threshold.

---

## Test and Evaluation Summary

The first prototype should be judged by a small set of hard-edged cases, not by how eloquent it sounds in open-ended prompts.

In short:

**use the golden fixtures to prove that the engine can classify, constrain, judge, and repair narrative moves without hallucinating support.**

---

## Next Draft Candidates

1. Convert the first-prototype architecture into a build checklist.
2. Draft an MVP runtime sequence from intake to verdict or render.
3. Add a compact state-diff protocol for revisions and iterative author use.
4. Draft a lightweight scoring model for support, strain, and setup sufficiency.
5. Stop spec expansion and begin implementation.

