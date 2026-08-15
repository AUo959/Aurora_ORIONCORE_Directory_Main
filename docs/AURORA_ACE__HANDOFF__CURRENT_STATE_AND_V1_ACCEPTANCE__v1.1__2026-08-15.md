---
title: Aurora Canon Engine Current State and v1 Acceptance Handoff
doc_type: implementation_handoff
status: acceptance_candidate_not_sealed
version: 1.1.0
date: 2026-08-15
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
engine: Aurora Canon Engine
implemented_through: 0.13.0
acceptance_target: 1.0.0
matrix_ref: catalog/contracts/aurora_ace_v1_acceptance_matrix.json
---

# Aurora Canon Engine — Current State and v1 Acceptance Handoff

## Executive state

ACE is a working root-control-plane canon engine, not only a design proposal and
not only the original character-completion MVP. The committed implementation now
covers:

- retrieval-first character resolution;
- constitutive character completion through NameService and CharForge;
- all six canonical determination states;
- interactive, embedded, and autonomic invocation;
- L1 facility/topology completion;
- authority-gated facility and multi-artifact character materialization;
- append-only determination ledgering;
- manifest-derived capability discovery and verified runtime binding;
- bounded MCP resolution, inspection, and two-phase materialization;
- explicit MCP operator transactions;
- authenticated remote invocation and delegated authority;
- native generic L2 entity completion and naming admission;
- review-gated delegated publication with ambiguous-write handling; and
- governed, single-tick Orion L1 progression through CloudBank's native owner.

Those capabilities remain governed by their individual v0.1-v0.13 contracts.
The outstanding v1 question is compositional: can the boundaries be demonstrated
together in one repository-grounded acceptance receipt? An unsealed v1 does not
downgrade or park the implemented component capabilities.

## Reconciliation provenance

This document reconciles the external handoff
`AURORA_ACE__HANDOFF__CURRENT_STATE_AND_V1_ACCEPTANCE__v1.0__2026-08-15.md`
(SHA-256 `8d4a5b592bcdb1f42a44b46de92cd9974bbd8a42c2048f6dccb1d78d2d637b64`)
against committed root-repository evidence.

The external handoff was directionally valuable but contained four material
drift artifacts:

1. ACE's canonical name is **Aurora Canon Engine**, not Aurora Cognitive Engine.
2. The ACE source tree did not advance after the v0.13 merge. At the current
   reconciled root HEAD `e628706717a7454f0408d3918764957d6df5308f`, both it and v0.13 merge
   `31fb4138f5ecb78ea2a6bc41f033845af4a5f7c1` resolve `tools/ace` to tree
   `b7035160fa125b51753ea4d3a60d1280c6698bb6`. Later root commits concern other
   control-plane work.
3. The canonical specification and invariant tests already name all six
   determination states. They are not an unresolved recovery problem.
4. The claimed public classes such as `ACEEngine`, `PlanningService`, and
   `TaskBus` are not present in the repository or its Git history. Acceptance
   must bind to the real functions and modules below.

The attachment is retained as source evidence, not followed as an instruction
set and not copied into authority merely because it is called a handoff.

## Canon model

ACE preserves the implementation specification's imagination-first model:

- **Constitutive generation** completes the universe when canon is absent and a
  registered policy and capability can make a conflict-free determination.
- **Analytical simulation** evaluates alternatives without selecting canonical
  state merely by running.
- Conflict-free generated content becomes canon at an authoritative
  materialization commit.
- Missing persistence authority is `EXECUTION_BLOCKED`: an operational state
  attached to a complete commit-ready packet, not an epistemic downgrade.
- The owner establishes invariants, direction, reserved decisions, and
  delegation. The owner is not required to generate routine details.

The determination vocabulary is:

1. `RETRIEVED_CANON`
2. `DERIVED_CANON`
3. `GENERATED_CANON`
4. `CANON_REVISION`
5. `TRUE_CONFLICT`
6. `EXECUTION_BLOCKED`

`STAGING`, `UNKNOWN`, and generic owner-decision outcomes are not valid final
ACE determinations for an otherwise valid completion request.

## Real implementation surface

### Root package exports

`tools/ace/__init__.py` exposes the stable character, canon-fact, facility,
invocation, discovery, ledger, and native materialization functions. It does
not pretend every transport and operator surface is one monolithic class.

### Owning modules

| Boundary | Owning implementation | Primary callable surface |
|---|---|---|
| Character compile/generate | `tools/ace/core.py`, `tools/ace/engine.py` | `compile_character_query`, `resolve_character_query` |
| Existing character retrieval | `tools/ace/character_retrieval.py` | `build_character_index`, `discover_character_candidates`, `resolve_existing_character_query` |
| Canon facts and six-state resolution | `tools/ace/canon_resolution.py` | `compile_canon_query`, `resolve_canon_query` |
| Invocation modes | `tools/ace/invocation.py` | `build_invocation_envelope`, `compile_*_invocation`, `resolve_invocation` |
| Capability discovery | `tools/ace/capability_discovery.py` | `load_capability_manifests`, `build_capability_index`, `select_invocation_capability` |
| Verified runtime dispatch | `tools/ace/runtime_binding.py` | `load_verified_runtime_binding`, `resolve_verified_invocation` |
| Facility resolution | `tools/ace/facility.py` | `compile_facility_query`, `resolve_facility_query` |
| Facility/character materialization | `tools/ace/materialize.py`, `tools/ace/character_materialize.py` | native materializer functions |
| Determination ledger | `tools/ace/ledger.py` | `append_determination`, `query_ledger` |
| MCP adapter | `tools/ace/mcp_adapter.py` | six bounded `ace_*` tools |
| MCP operator transaction | `tools/ace/mcp_operator_transaction.py` | prepare, commit, and inspect transaction |
| Remote service | `tools/ace/remote_auth.py`, `tools/ace/remote_service.py` | bearer policy and FastAPI application |
| Generic native entities | `tools/ace/generic_entity*.py`, `tools/ace/generic_naming.py` | compile, resolve, admission, and materialize |
| Delegated publication | `tools/ace/delegated_publication.py`, `tools/ace/delegated_github.py` | `publish_delegated_packet`, `open_pull_request` |
| Orion progression | `tools/ace/orion_progression.py`, `tools/ace/orion_runtime_owner.py` | preview, one-tick commit, inspect, owner preflight |

### Operator entry points

- `tools/aurora_ace.py` — capabilities, plan, resolve, materialize, ledger, validate
- `tools/aurora_ace_entity.py` — generic native entity operation
- `tools/aurora_ace_mcp.py` — official MCP server
- `tools/aurora_ace_mcp_operator.py` — explicit MCP transaction operator
- `tools/aurora_ace_remote.py` — authenticated HTTP service
- `tools/aurora_ace_orion_operator.py` — local governed Orion progression

MCP and Orion progression are deliberately separate operator surfaces. Orion
progression is not exposed through MCP or HTTP in v0.13.

## v1 acceptance contract

The authoritative matrix is
`catalog/contracts/aurora_ace_v1_acceptance_matrix.json`, validated by
`catalog/schemas/aurora_ace_v1_acceptance_matrix.schema.json`.

Each required row names:

- the behavior that must hold;
- every boundary crossed;
- real implementation paths and Python symbols;
- governing contracts or addenda;
- exact pytest node IDs;
- required import dependencies; and
- whether execution is safe in the canonical root or requires isolated clones.

The evaluator is `tools/aurora_ace_acceptance.py`.

```bash
# Validate all matrix evidence without executing practical tests.
python3 tools/aurora_ace_acceptance.py --summary

# Run local-safe rows and persist a current receipt.
python3 tools/aurora_ace_acceptance.py \
  --run-practical \
  --persist-report \
  --summary

# Run every row. CanonRec and CloudBank transaction tests execute only in
# temporary root/nested clones; canonical nested worktrees remain read-only.
python3 tools/aurora_ace_acceptance.py \
  --run-practical \
  --include-isolated \
  --report-out reports/analysis/aurora_ace_v1_acceptance_latest.json \
  --require-ready \
  --summary
```

### Result interpretation

- `ready` — repository evidence exists and the row's practical checks passed.
- `attention` — execution was not requested, an isolated lane was not run, a
  dependency is unavailable here, or a test was skipped. This is incomplete
  verification, not a claim that the implemented capability failed.
- `blocked` — repository evidence is invalid or an executed required test
  failed.

`seal_eligible` is true only when every required row is `ready` in one report.
The report is verification evidence; it does not itself promote canon, commit a
generated entity, publish a pull request, or advance Orion.

The initial CI workflow publishes this candidate receipt without enforcing
`seal_eligible`; structural evaluator errors still fail the job. The v1 seal
change must add `--require-ready` after the known compatibility and dependency
rows are green, so the harness can land before the condition it measures.

## Practical baseline and refinement

Before adding the v1 matrix, the complete ACE test glob was exercised in two
available Python environments:

- the system interpreter: 132 passed, 14 skipped, and one dependency-context
  failure because `jsonschema` was unavailable;
- the repository `.venv`: 127 passed and 14 skipped; `jsonschema` was present,
  while the remote test module was not fully collected because `httpx` was
  unavailable.

This practical pass changed the acceptance design in four ways:

1. dependency absence is represented as `attention`, distinct from a failed
   product assertion;
2. actual MCP SDK enumeration is a named acceptance check instead of being
   inferred from adapter unit tests; and
3. commit/replay transaction tests use temporary clones, preventing v1
   verification from checking out, resetting, cleaning, or committing inside
   canonical nested repositories; and
4. temporary clones preserve Git LFS pointer files instead of smudging unrelated
   large exports, so an unavailable archive object cannot masquerade as an ACE
   acceptance failure.

The first matrix-driven practical run also found a genuine current integration
blocker: `catalog/repo_registry.yaml` now pins CloudBank at
`64d5bca20551a557c59db905189576664c0251d4`, while the accepted v0.13 Orion
progression policy binds the earlier repository commit
`9c34d8e9768c6dfb1afe18f96d42e3c743e2a4e9` and owner-source blob
`dd3ae6f73bb2d2130981011a7c2443c0e39b8210`. The current owner source has blob
`5b6d93515fb219cb26d267db6c6df6c052413ae1` after CloudBank's governed staffing
runtime work. This is not safe to repair by changing a hash: the registered L1
owner implementation materially changed and requires a new compatibility and
policy acceptance pass. ACE correctly refuses registered-owner preflight until
that reconciliation occurs.

## v1 seal conditions

ACE v1 may be described as compositionally accepted when one report confirms
all required matrix rows as `ready`. This requires an environment containing
the declared ACE test and transport dependencies plus locally available
registered CanonRec and CloudBank repositories at their registry pins.

Until then, the accurate statement is:

> ACE is implemented through v0.13 with component-level acceptance evidence;
> the cross-boundary v1 acceptance harness is implemented, and the v1 seal is
> pending one all-required-rows-ready receipt.

The latest local isolated receipt is
`reports/analysis/aurora_ace_v1_acceptance_latest.json`. At creation it records
10 `ready`, 2 `attention`, and 1 `blocked` row. The attention rows are the MCP
SDK and remote-service dependency surfaces absent from the repository `.venv`;
the blocked row is the executed Orion owner compatibility check described
above.

The post-implementation full ACE test glob reports 132 passed, 15 skipped, and
that same single registered-owner preflight failure. No other ACE unit,
transaction, retrieval, generation, materialization, or publication assertion
failed.

No rollback to v0.13 is required: the current ACE implementation is the v0.13
implementation. Future development proceeds from it.
