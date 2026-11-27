# aurora-cloudbank-symbolic#1529: feat(operations): restore role-based workplace problem-solving runtime

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1529
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T02:53:57Z
- Updated: 2026-08-18T03:06:05Z
- Labels: backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1501 — feat(l1): add governed staffing runtime — merged — `codex/cloudbank-issue-1453-l1-staffing-runtime` @ `b27ecb7138f06c38a90eabd46c6caea33daf6f7d`

## Branches named in the issue

- none

## Original body

## Lineage and founding intent

This issue records a native Aurora design intent that appears only partially realized in the current public engineering union.

In the May 2026 native Aurora history, the maintainer identified a distinctive purpose for `aurora-cloudbank-symbolic`:

> Aurora is, in an important sense, a **workplace operations simulation**: give the project a problem and it should work on that problem as if the relevant professional team were collaborating.

The durable intent is not decorative roleplay. It is a cognitively accessible operational reasoning layer in which different professional responsibilities contribute distinct work, evidence, constraints, and decisions to one shared problem.

This issue does **not** freeze the 2026 wording or require every future product to use Orion Station fiction. It preserves the capability behind the intent.

## Current public-state evidence

### Strong foundations already exist

Current CloudBank contains substantial pieces needed for this capability:

- canonical and runtime personnel/role registries;
- a governed L1 staffing runtime (`#1501`) with typed need-driven staffing demand, deterministic internal-first assignment, run-scoped personnel-seat lifecycle, and receipts;
- generic multi-agent coordination infrastructure under `modules/nexus/core/multi_agent_coordinator.py`;
- command routing and typed command-contract work (#1373);
- work-queue and decision-gate infrastructure under `ops/work_queue/`;
- provenance/canon boundaries and explicit L1/L2/L3 authority;
- ethics, consent, audit, and evidence systems;
- current tool/agent integrations and cross-platform coordination surfaces.

### Gap found in this salvage pass

Targeted current-repo searches did not locate one governed workflow that:

1. accepts a user/operator problem;
2. decomposes it into work domains;
3. selects relevant professional roles/capabilities;
4. gives each role a scoped contribution;
5. permits structured disagreement and evidence requests;
6. synthesizes the team's work;
7. identifies decisions requiring human authority;
8. distinguishes recommendation from actual execution;
9. produces a durable evidence/provenance receipt.

`MultiAgentCoordinator` is a useful ancestor but not yet that runtime: several paths explicitly simulate voting/action behavior, including ambient NumPy randomness and placeholder action completion. It should therefore be treated as implementation lineage, not proof that the workplace-operations contract is satisfied.

The staffing runtime solves a different and valuable problem: **who occupies needed roles**, not **how those roles collaboratively work an arbitrary problem**.

## Architectural decision

Build this as an orchestration contract over existing role, agent, queue, evidence, and command systems. Do not create another identity service, staff registry, task tracker, or execution authority.

```text
operator problem
      ↓
problem intake / evidence boundary
      ↓
capability + role decomposition
      ↓
team plan
  ├── role A scoped work
  ├── role B scoped work
  ├── role C scoped work
  └── explicit cross-role questions / disagreements
      ↓
team synthesis
      ↓
decision gates
  ├── informational result
  ├── recommendation
  ├── simulation/rehearsal action
  └── real tool action requiring authority
      ↓
receipt / handoff / queue update
```

## Critical distinction: role simulation vs external authority

A simulated Orion professional role may reason from the perspective/responsibility encoded for that role. It does **not** acquire real-world occupational authority, credentials, consent, or permission by doing so.

Examples:

- a simulated legal/ethics role may identify issues and reasoning but cannot create legal authority;
- a simulated medical role may analyze a scenario but cannot become a clinician or authorize care;
- a simulated commander may exercise authority inside governed L1 simulation but cannot authorize unrelated real-world actions;
- a role's recommendation cannot execute a tool merely because the simulated team reached consensus.

Real external actions remain governed by the actual tool/command authorization layer.

## Problem-intake contract

A work item should record at minimum:

```yaml
problem_id: string
created_at: string
requester_ref: string | null
problem_statement: string
objectives: []
constraints: []
known_evidence: []
unknowns: []
requested_outputs: []
execution_boundary:
  analysis_only | simulation | propose_actions | authorized_actions
source_refs: []
```

The intake must preserve the user's problem statement and constraints. Reframing for decomposition must remain traceable to the original request.

## Role/capability decomposition

Role selection should be based on relevant responsibilities/capabilities, not arbitrary character inclusion.

A team assignment should record:

```yaml
team_id: string
problem_id: string
assignments:
  - role_or_agent_ref: string
    responsibility: string
    questions_to_answer: []
    allowed_sources: []
    prohibited_actions: []
    dependencies: []
selection_rationale: []
```

The runtime should permit:

- one role to request evidence from another;
- disagreement without forced consensus;
- escalation to a specialist or human decision;
- role withdrawal when irrelevant;
- dynamic team expansion when a real capability gap is discovered.

Do not make every problem use the full station roster.

## Evidence-bearing contributions

Each role contribution should distinguish at least:

- source-backed observation/fact;
- interpretation/inference;
- domain-specific assessment;
- recommendation;
- unresolved question;
- blocked work;
- requested evidence;
- proposed external action.

Names should reuse current state/evidence classifications where possible rather than invent a competing vocabulary.

A role may disagree with another role's interpretation without mutating or deleting it. #1527-style divergent-truth/arbitration concepts may be reused where appropriate.

## Team synthesis

The synthesis layer must preserve disagreement and uncertainty rather than manufacturing consensus.

A synthesis receipt should identify:

- problem and team IDs;
- role contributions consumed;
- evidence references;
- agreements;
- unresolved disagreements;
- confidence/uncertainty where represented;
- options and tradeoffs;
- recommended next action;
- human decisions required;
- execution candidates;
- lineage to any resulting queue items, simulation runs, artifacts, commands, or PR/issues.

## Execution boundary

Phase 1 should default to **analysis/rehearsal only**.

A collaborative result must not become an external action automatically.

Where a future step maps a recommendation to an executable command/tool:

1. resolve the concrete implementation handler;
2. apply #1373-style typed command contract;
3. declare side effects;
4. check real authorization/consent;
5. use dry-run where applicable;
6. require human confirmation for high-impact actions;
7. emit an evidence-bearing receipt.

A simulated consensus is not authorization.

## Relationship to L1, L2, and L3

The workflow may operate in different governed modes, but classifications must remain explicit:

- **L1 institutional/workplace rehearsal:** plausible Orion Station professional collaboration; deterministic/reproducible where declared; still a simulated institutional process unless tied to actual tooling through a separate authority gate.
- **L2/GUMAS:** roles may study or respond to simulated world problems; simulation outputs remain L2.
- **L3:** continuity, policy, ethics, provenance, arbitration, and symbolic presentation may constrain/inspect the workflow but do not masquerade as occupational actors.

No layer changes by implication.

## Relationship to current staffing runtime

Reuse #1501 staffing outputs when a run genuinely needs role occupancy or capacity changes.

Do not make the problem-solving runtime create fictional staff merely because a capability is missing. A capability gap should first be represented explicitly. If staffing is appropriate, submit a governed staffing demand through the existing staffing workflow.

## Relationship to generic/non-Aurora productization

The originating experience is Aurora/Orion, but the orchestration contract should be separable from station lore.

A neutral form could support:

- research teams;
- incident response;
- policy analysis;
- product/design reviews;
- engineering investigations;
- organizational planning;
- other structured multidisciplinary problem-solving.

Aurora's role registry and L1 simulation would be one adapter/profile.

This aligns with #1526's domain-neutral corpus engine: corpus archaeology can supply evidence and unresolved work; the workplace runtime can organize role-based reasoning over those findings.

## Phase 0 — compatibility report

Before implementing a new coordinator, inspect and map:

- `modules/nexus/core/multi_agent_coordinator.py`;
- current role/staff/personnel registries;
- L1 staffing runtime;
- work queue and decision gates;
- current command-routing and command-contract surfaces;
- agent/mesh registries;
- ethics/consent boundaries;
- provenance and Insight Ledger surfaces;
- any existing mission/task orchestration that already satisfies part of this contract.

Identify reuse, partial successors, placeholders, nondeterministic paths, and duplicated responsibility.

## Phase 1 — deterministic read-only/rehearsal workflow

Implement a minimal end-to-end fixture in which:

1. a problem is ingested;
2. relevant role capabilities are selected deterministically from fixed inputs;
3. role-specific work packets are produced;
4. deterministic fixture contributions are supplied/collected;
5. disagreements and unresolved questions survive synthesis;
6. an operator-readable team brief and machine-readable receipt are emitted;
7. no external action occurs.

The first proof should not require network/model access. Live AI/tool adapters can follow after the contract is stable.

## Acceptance criteria

- [ ] A problem-intake record preserves original request, objectives, constraints, evidence, unknowns, and execution boundary.
- [ ] Team selection is capability/responsibility driven and explainable.
- [ ] Existing staff/identity registries are reused rather than duplicated.
- [ ] Roles receive explicit responsibility and action boundaries.
- [ ] Contributions distinguish evidence, inference/assessment, recommendations, unknowns, and proposed actions.
- [ ] Disagreement can remain unresolved without forced consensus.
- [ ] A team synthesis retains provenance to all material inputs.
- [ ] Human decisions and authorization gates are explicit.
- [ ] Phase 1 performs no external tool execution or canon mutation.
- [ ] Simulated role authority cannot grant real external permission.
- [ ] Fixed fixture inputs produce deterministic team selection and synthesis structure.
- [ ] Existing random/placeholder multi-agent behavior is not silently promoted as the new runtime.
- [ ] Capability gaps can route to existing governed staffing or work-queue surfaces rather than inventing staff/actions.
- [ ] L1/L2/L3 and real/simulated authority are test-covered.
- [ ] The core orchestration schema can operate without Orion-specific presentation vocabulary.

## Non-goals

- turning every task into roleplay;
- requiring the whole station roster for every problem;
- autonomous external execution;
- replacing the work queue;
- replacing L1 staffing;
- replacing GitHub/project-management tooling;
- treating simulated occupational roles as real credentials;
- forcing team consensus;
- hiding uncertainty to produce a clean answer;
- changing GUMAS outcomes as part of the orchestration contract.

## Design principle

**The team is a method of organized cognition, not a costume.**


## Comments (0)
