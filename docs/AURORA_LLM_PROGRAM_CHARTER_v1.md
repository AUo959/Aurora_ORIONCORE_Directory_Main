# Aurora LLM Program Charter v1

Status: ACTIVE PROGRAM CHARTER
Canon status: non-canonical operating document
Machine-readable registry: `catalog/aurora_llm_program.json`
Steward: `aurora-llm-steward` (skill `skills/aurora-llm-steward/`, Claude Code agent `.claude/agents/aurora-llm-steward.md`)
Status instrument: `python3 tools/aurora_llm_program_status.py --cloudbank <CloudBank checkout>`

## 1. What "the Aurora LLM" means here

No artifact in the four project repositories is named "Aurora LLM". The phrase
covers four existing bodies of work, inventoried on 2026-11-28:

| Track | What it is | Where it lives | State on 2026-11-28 |
| --- | --- | --- | --- |
| **T1 Model routing and catalog** | The provider LLMs Aurora runtimes call today (Claude, GPT) behind one routing interface | CloudBank `modules/ai_core/`, `scripts/validate_model_catalog.py`, weekly `model-catalog-validation.yml` | Live. Four available entries (Claude Opus 5, Claude Sonnet 5, GPT-6.1 Sol, GPT-6 Astra), all verified 2026-11-07/08. GPT-4 and GPT-4o disabled. Work orders #90 (GPT-6 role routing and eval gate) and #95 (delegated-agent state-delta contract) are open in the task queue. |
| **T2 Aurora State Model (ASM)** | Aurora's own learned model: predicts simulated world and belief state, not prose | Root `catalog/contracts/aurora_state_model_contract_v0_1.json`, 4 schemas, fixtures, white paper, spec, implementation plan | Design-ready, not implemented. Root contract tests (G0) pass. No nested repo has adopted it. No dataset exists. Training is not authorized. |
| **T3 Native learner experiment program** | Phase 0 baseline, passive RiverCycle telemetry, and the learner design gate | Archived CloudBank issues #1466, #1467, #1468 (`catalog/backlog_archive/`) | #1466's blocker (#1461) merged 2026-08-08, so Phase 0 is unblocked. #1467 and #1468 wait on it. |
| **T4 LLM-facing runtime surfaces** | Code that sends prompts to a model and consumes the output | CloudBank `modules/narrative_river/`, `modules/ai_core/rag_chat.py`, `prompt_safety.py`, `token_budget.py`, `services/nemo_service/`; root ACE sandbox | Present. Changes here route through T1 for model selection. |

T2 and T3 are the same goal seen from two repos. #1468 itself requires
reusing the Aurora State Model rather than creating a parallel learner
authority, so this charter treats **ASM as the learner contract** and #1468 as
its CloudBank-side design gate. Anything #1468 needs that ASM lacks is
proposed as an ASM contract revision in the root repo.

## 2. Governing rule

**Models reason; Aurora governs.** (Work order #90.)

- A model's output is never canon. CanonRec stays canon authority.
- Deterministic L1 transitions and GUMAS simulation authority stay deterministic.
- Learner output carries `simulation` authority only and is `ineligible` for promotion by default (ASM contract `authority_model`).
- RiverCycle and other telemetry are read-only observation surfaces. They never become rewards for the run they measure.
- No online learning, recursive training, or self-modification path.

## 3. Gate ladder

The program advances by gates, never by intent. Each gate is evidence in Git.

| Gate | Meaning | Unlocks | Current |
| --- | --- | --- | --- |
| G0 | Contract conformance (schemas, fixtures, authority rules) | Repo-local adapter work | Root passes (`tests/test_aurora_state_model_contract.py`) |
| G1 | Generator reproducibility | Dataset sealing | Not started |
| G1.5 | Teacher sufficiency (entropy, trajectory spread, scenario-family count) | Adapter expansion or training proposal | Not started |
| G2 | Dataset integrity (no split leakage, hashes, disclosure review) | Model training (with owner authorization) | Not started |
| G3 | Baseline utility (beats no-change and majority-class) | Multi-step training | Not started |
| G4 | Rollout utility | Serving work | Not started |
| G5 | Simulation-only serving readiness | Controlled runtime activation | Not started |

T1 has its own gate from #90: no change to default production routing until
representative Aurora tasks are run across the candidate models and the
current baseline, tracking task success, canon drift, tool-call correctness,
latency, tokens, cache use, and cost per successful task.

## 4. Ordered next work

1. **ASM root contract review** (`aurora-llm-asm-root-contract-review`). Independent review of the design package under the peer review protocol. Moves root adoption from `proposal_committed` to `reviewed`.
2. **CloudBank Phase 0 baseline** (`gh-cloudbank-1466`). Record the baseline SHA and a read-only L1 preflight receipt. Its blocker has merged.
3. **ASM adapter discovery** (`aurora-llm-asm-adapter-discovery`). Read-only field maps for ASM-002 (GUMAS state) and ASM-003 (QSFE belief), and recorded decisions for D1 to D3 from the implementation plan.
4. **T1 eval harness** (`gh-orioncore-90`). A small, representative Aurora task set scored across the available catalog models. Results go into a dated receipt before any routing default changes.
5. **RiverCycle Phase 1** (`gh-cloudbank-1467`), after step 2.
6. **ASM-001 generator** in a clean integration branch, then G1.5. Stop after 12 episodes if G1.5 fails.
7. **Learner design gate** (`gh-cloudbank-1468`), mapped onto ASM per section 1.

Steps 1 to 4 are independent and may run in parallel.

## 5. Who decides what

Resolvable questions go to their process, not to the owner (root `CLAUDE.md`,
`GUMAS_SIM_2.5/CanonRec/canon/L2/RESOLUTION_ROUTING__2026-07-21.md`). The steward runs that process.

Owner-only gates (`catalog/aurora_llm_program.json → owner_gates`):

- merging or committing to main;
- authorizing any model training run;
- public release of any dataset or checkpoint;
- licensing of training sources and derivative artifacts;
- paid provider spend beyond the existing weekly catalog check.

A task's exit condition must not be written as "owner review before X".

## 6. Steward operating loop

Each check-in, the steward:

1. Runs `tools/aurora_llm_program_status.py --cloudbank <path>` and reads its findings.
2. Reads the task queue items linked in the registry, plus any new item whose text touches the tracks.
3. Picks the highest ordered item from section 4 that is unblocked, and either does it or hands it to the better-suited platform (Codex for GUMAS simulation runs and intake; Claude Code for CI, lint, and multi-file edits).
4. Records outcomes through `tools/session_state_io.py`, never by hand-editing JSON.
5. Updates this charter's section 1 table and section 3 "Current" column when a gate moves, in the same PR as the evidence.

## 7. Change control

- Editing this charter or the registry is a **significant** change under the peer review protocol (recommended review).
- Editing the ASM contract's authority model or invariants is **floor-touching** (mandatory review).
- Flipping `first_slice.model_training_authorized` requires a linked, owner-approved training issue. The status tool flags it otherwise.
