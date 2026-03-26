# Generative Forecast Architecture (GFA) Posture

This document defines the root-level posture for future-facing Aurora work.
It standardizes how the workspace talks about forecasting, simulation, and
deliverables so the framing is stable across docs, manifests, and interfaces.

## Canonical Posture

Aurora is not framed here as `simulation as product`.

Aurora is framed as `Generative Forecast Architecture (GFA)`: a governed
architecture for ingesting reality, declaring assumptions, generating possible
futures, comparing outcomes, and producing auditable forecast artifacts and
briefs.

In this posture:

- simulation is a method, not the product
- `Generate Forecast` is the primary governed action
- a `Forecast` is the primary outcome
- a `Forecast Artifact` is the reproducible record of how that forecast was
  generated
- a `Forecast Brief` is the human-facing decision product

## Operating Model

GFA preserves the existing layered discipline already present across Aurora
materials:

- `L1` is the reality base: sources, entities, timestamps, assumptions, and
  audit trails
- `L2` is the simulation layer: causal exploration, scenario generation,
  branching, and intervention testing
- `L3` is the symbolic and governance layer: constraints, ethics, drift
  controls, and orchestration

The product is the full architecture across these layers. Simulation remains a
critical component, but it is contained within the larger forecasting process.

## Canonical Terminology

Use these terms by default in root-level docs and interfaces:

- `Generative Forecast Architecture (GFA)`: the product, posture, or overall
  system
- `Generate Forecast`: the primary action, command, button label, or workflow
  invocation
- `Forecast`: the generated analytical outcome
- `Forecast Artifact`: the saved and reproducible output package for a forecast
- `Forecast Brief`: the summarized decision-facing presentation of a forecast
- `Forecast Architecture`: the technical stack that enables forecast generation
- `Forecast Process`: the governed end-to-end loop from reality ingest through
  briefing and review

## Preferred Language

Prefer:

- `Generate Forecast`
- `forecast generation`
- `forecast artifact`
- `forecast brief`
- `forecast architecture`
- `confidence`, `calibration`, `sensitivity`, and `decision usefulness`

De-emphasize except when describing the specific L2 layer:

- `simulation as product`
- `simulation output`
- `simulation report`
- `simulation accuracy`
- `run a simulation` as the top-level product verb

When speaking precisely about `L2`, `simulation` is still correct and should be
used. The change is not a ban on the term. The change is a scope correction.

## Translation Rules

Use the following replacements when modernizing older language:

- `simulation as product` -> `Generative Forecast Architecture`
- `run a simulation` -> `Generate Forecast`
- `simulation output` -> `Forecast Artifact`
- `simulation report` -> `Forecast Brief`
- `simulation stack` -> `Forecast Architecture`
- `simulation workflow` -> `Forecast Process`
- `simulation accuracy` -> `forecast calibration` or `confidence calibration`

## Naming Guidance

Use `Generate Forecast` when the surface is action-oriented:

- UI buttons
- command names
- operator prompts
- workflow stage labels

Use `Forecast` terms when the surface is artifact-oriented:

- report titles
- saved bundles
- manifest names
- output directories
- review checkpoints

Examples:

- Button: `Generate Forecast`
- Workflow stage: `Generate Forecast`
- Output bundle: `Forecast Artifact`
- Analyst handoff: `Forecast Brief`

## Decision Rule

If a term makes Aurora sound like a standalone simulator, prefer the GFA
equivalent.

If a term refers specifically to the causal exploration engine inside `L2`,
`simulation` remains the right word.
