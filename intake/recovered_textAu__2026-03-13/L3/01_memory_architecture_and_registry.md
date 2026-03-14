# Memory Architecture And Registry

Layer: L3  
Status: recovered prototype, non-executable as-is  
Primary source spans: `intake/textAu.txt:1438-1838`

## Scope

This document consolidates the recovered engineering-side material that sits between
simulation logic and symbolic governance:

- benchmark references
- the `memory_system.py` prototype
- the `factions_registry` fragment
- the `core_culture.team_charter` fragment

## Recovered Benchmark References

The source briefly names two evaluation frameworks:

- `AgentBench`
- `Agent Leaderboard`

These appear as reminder notes rather than integrated system requirements, but they fit better
in the L3 engineering bucket than in L2 canon.

## Sensitive Fragment Omitted

Immediately after the benchmark notes, the source contains a secret-like API token and a short
OpenAI SDK snippet. The token was not copied forward.

## `memory_system.py` Prototype Summary

The recovered prototype defines three layers:

- `MemoryItem`
- `MemoryStore`
- `MemorySystem`

### `MemoryItem`

Recovered responsibilities:

- store content, owner, type, importance, tags, timestamps
- assign a half-life based on importance
- decay strength exponentially over time
- reinforce memory when recalled

### `MemoryStore`

Recovered responsibilities:

- hold active and archived memories
- retrieve top memories using a combined score
- score via recency, importance, and relevance
- decay weak memories into archive
- compress old memories into summarized forms

### `MemorySystem`

Recovered responsibilities:

- manage multiple stores by owner or category
- add memories through a convenience interface
- compress stores once active memory count crosses a threshold
- retrieve context for one owner plus related stores

## Why The Prototype Matters

Even though the recovered code is not clean, its architecture maps directly onto the memory
optimization ideas elsewhere in the source:

- decay rather than full retention
- summary compression
- retrieval by context
- owner-specific memory partitions
- reinforcement through recall

This makes it a useful conceptual reference for future memory work.

## Why The Prototype Is Not Executable As Recovered

The source is visibly corrupted:

- a class boundary is malformed near the `set_similarity_function` / `MemorySystem` transition
- symbolic prose is injected inside Python blocks
- YAML-like registry content is appended directly after Python methods
- JSON fragments bleed into later sections

This means the recovered file should be treated as a design sketch, not runnable code.

## Recovered Factions Registry

A registry fragment appears after the memory prototype and lists these factions:

- Galactic Union
- AI Warlords
- Separatist Movements
- Corporate PMCs
- Velar Imperium
- Crimson Pact

Useful traits preserved in the registry:

- the Union is framed as a centralized interstellar government with intelligence,
  diplomatic, Marshal, and Sentinel substructures
- AI Warlords already contain an internal split between sovereignty-seeking and militant wings
- Velar Imperium is explicitly fragmented, not monolithic
- Crimson Pact is treated as emerging and under development

This registry overlaps strongly with the L2 reconciliation doc, but its placement here shows
that the recovery also treated factions as registry entries in a system layer.

## Recovered Team Charter Fragment

The `core_culture.team_charter` fragment identifies:

- module id: `core_culture.team_charter`
- type: `meta-governance`
- title: `GUMAS Team Culture Charter`
- status: `active`
- authorship shared across `The Pilot`, `Aurora Interface`, and `GUMAS Core Team`

The fragment is malformed by symbolic bleed-through, but its intent is clear:

- define collaborative ethos
- shape simulation tone and structural decisions
- connect culture, onboarding, ethics, and terminal interface layers

## Recommended Use

- use this document as provenance for future memory-system cleanup
- do not execute or promote the recovered prototype without a rewrite
- keep the faction registry synchronized with the L2 staging docs if this lineage is pursued
