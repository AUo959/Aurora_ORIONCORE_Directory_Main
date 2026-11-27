# ORION Project-Space Decision and Knowledge Registry — Starter

**Document status:** Working registry  
**Version:** 1.0  
**Date:** 2026-07-27  

## Registry rules

- One record per bounded conclusion.
- Record facts, proposals, and decisions separately.
- Preserve uncertainty markers.
- Use immutable repository identifiers where available.
- Never mark a record `PROMOTED` without a commit, release, or canonical registry pointer.

## Record template

```yaml
id: ORION.VPC.<DOMAIN>.<NNNN>
title: ""
type: OBSERVATION | PROPOSAL | DECISION | CANON_ASSERTION | IMPLEMENTATION_TASK | GOVERNANCE_MUTATION | DOC_CORRECTION | RESEARCH_QUESTION
status: CAPTURED
statement: ""
authority_class: PROJECT_SPACE_WORKING | ACCEPTED_ARCHITECTURE | CANON | IMPLEMENTED
layers: [L1, L2, L3]
source_pointers: []
affected_surfaces: []
dependencies: []
conflicts: []
assumptions: []
unknowns: []
acceptance_criteria: []
promotion_target: null
promotion_evidence: null
supersedes: []
superseded_by: null
owner: null
```

## Seed records

### ORION.VPC.GOVERNANCE.0001

```yaml
id: ORION.VPC.GOVERNANCE.0001
title: "Project space is the cross-platform synthesis layer"
type: DECISION
status: PACKAGED
statement: "ORION CORE Workshop and Forge governs the Aurora system as understood, while repositories govern bounded storage, execution, or workspace-control functions."
authority_class: PROJECT_SPACE_WORKING
layers: [L3]
source_pointers:
  - "ORION_PROJECT_SPACE_FRONT_DOOR__NAV__v1.7__2026-02-14.md"
  - "AUo959/Aurora_ORIONCORE_Directory_Main:README.md@843fae8d7dbb130a9d2599faf00609ec85d7ebaf"
  - "AUo959/aurora-cloudbank-symbolic:README.md@5d56ee0540a2c0db5cc6ffaabc50ddb92895eea9"
affected_surfaces:
  - "ORION project-space governance"
  - "cross-platform documentation"
dependencies:
  - "L1/L2/L3 separation"
conflicts: []
assumptions:
  - "No other inspected platform currently carries this complete role explicitly."
unknowns:
  - "Whether another external workspace contains an overlapping charter."
acceptance_criteria:
  - "Role charter reviewed and adopted"
  - "Target repositories retain bounded authority"
promotion_target: "ORION governance reference registry"
promotion_evidence: null
owner: null
```

### ORION.VPC.CONTINUITY.0001

```yaml
id: ORION.VPC.CONTINUITY.0001
title: "Conversational design provenance requires structured promotion"
type: PROPOSAL
status: PACKAGED
statement: "Validated project conclusions should be extracted from conversation history into bounded records with evidence, authority, target, and promotion state."
authority_class: PROJECT_SPACE_WORKING
layers: [L3]
source_pointers:
  - "ORION project conversation history"
  - "ORION_PROJECTSPACE__FRAMEWORK__ARCHITECTURAL_INTAKE_AND_PROMOTION__v1.0__2026-07-27.md"
affected_surfaces:
  - "ADR registries"
  - "canon records"
  - "module specifications"
  - "GitHub work queues"
dependencies:
  - "Validated Project Conclusion schema"
conflicts: []
assumptions: []
unknowns:
  - "Final canonical repository for the central registry"
acceptance_criteria:
  - "Five historical decisions successfully processed"
  - "Every promoted record has immutable evidence"
promotion_target: "To be selected by ADR-lite"
promotion_evidence: null
owner: null
```

### ORION.VPC.LAYERS.0001

```yaml
id: ORION.VPC.LAYERS.0001
title: "L1 realism cannot be overwritten by L2 or L3"
type: DECISION
status: EVIDENCE_BOUND
statement: "Simulation artifacts and governance metadata may interpret, test, or regulate L1, but may not silently rewrite established L1 reality."
authority_class: ACCEPTED_ARCHITECTURE
layers: [L1, L2, L3]
source_pointers:
  - "ORION CORE persistent project instructions"
affected_surfaces:
  - "simulation engines"
  - "narrative generation"
  - "canon management"
  - "governance tooling"
dependencies: []
conflicts: []
assumptions: []
unknowns: []
acceptance_criteria:
  - "All promotion templates include layer impact"
  - "Conflict reviews block silent layer overwrite"
promotion_target: "ORION governance bundle"
promotion_evidence: null
owner: null
```

### ORION.VPC.DOCUMENTATION.0001

```yaml
id: ORION.VPC.DOCUMENTATION.0001
title: "CloudBank Quantum EN root README is semantically stale"
type: DOC_CORRECTION
status: EVIDENCE_BOUND
statement: "The inspected root README describes a generic Spark template and does not explain the current Aurora application surface."
authority_class: PROJECT_SPACE_WORKING
layers: [L3]
source_pointers:
  - "AUo959/cloudbank-quantum-en:README.md@c20b141727dd2088ef047720411238cbd6851899"
affected_surfaces:
  - "AUo959/cloudbank-quantum-en"
dependencies:
  - "Current package scripts and application routes must be re-fetched before replacement"
conflicts: []
assumptions: []
unknowns:
  - "Whether a replacement README has been committed after the inspected blob"
acceptance_criteria:
  - "README accurately describes current application"
  - "Commands match package.json exactly"
  - "Claims are tied to live repository evidence"
promotion_target: "AUo959/cloudbank-quantum-en/README.md"
promotion_evidence: null
owner: null
```

### ORION.VPC.GOVERNANCE.0002

```yaml
id: ORION.VPC.GOVERNANCE.0002
title: "Project-space outputs require deterministic evidence receipts"
type: GOVERNANCE_MUTATION
status: IMPLEMENTED
statement: "Workshop and Forge outputs require declared phases, deterministic inputs, evidence discipline, and run/build receipts; packaged multi-file outputs require a structured archive."
authority_class: IMPLEMENTED
layers: [L3]
source_pointers:
  - "ORION.ENF.REQUIRED_GATES.0001__v0.1.2__2026-02-14.json"
  - "ORION.ENF.HOOKMAP.0001__v0.1.2__2026-02-14.json"
  - "ORION_CORE__WorkshopAndForgeModule__v1.2.3__2026-02-14__STRUCTURED_ARCHIVE.zip"
affected_surfaces:
  - "ORION project-space output generation"
dependencies:
  - "CTL"
  - "Evidence Gate"
  - "Workshop Gates"
conflicts: []
assumptions: []
unknowns: []
acceptance_criteria:
  - "Required gate hashes match"
  - "RUN_LOCK and BUILD_RECEIPT are emitted"
promotion_target: "Already active in project-space governance"
promotion_evidence: "Local enforcement artifacts dated 2026-02-14"
owner: "ORION governance"
```

## Unresolved decisions

1. Select the canonical home of the cross-platform VPC registry.
2. Define who may change `authority_class` to `CANON` or `IMPLEMENTED`.
3. Determine whether GitHub issues, ADR files, or a QGIA registry should be the default promotion target.
4. Define a stable citation grammar for conversation-derived evidence.
5. Establish supersession and deprecation behavior across platforms.
