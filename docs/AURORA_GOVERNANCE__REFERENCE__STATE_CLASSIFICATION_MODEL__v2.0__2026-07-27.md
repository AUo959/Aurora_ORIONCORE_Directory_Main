# State Classification Model

**Document ID:** `AURORA_GOVERNANCE__REFERENCE__STATE_CLASSIFICATION_MODEL`  
**Version:** v2.0  
**Date:** 2026-07-27  
**Authority:** Governance Layer  
**Status:** Proposed governance canon until merged  
**Supersedes:** Pre-canonical v1.0 dated 2026-06-12  
**Related:** `Aurora_ORIONCORE_Directory_Main#44`

---

## 1. Purpose

This reference defines how Aurora classifies artifacts, events, claims, and evidence without collapsing distinct questions into a single hierarchy.

The model protects two truths at once:

1. Deterministic L1 simulations are capable of producing durable, first-class operational data.
2. Simulated institutional activity must never be represented as real-world interaction or independent external assurance.

The word **simulated** describes execution mode and provenance. It does not make an artifact disposable, decorative, abstract, or analytically inferior.

---

## 2. Core Rule: Classify on Independent Dimensions

Every architecture-sensitive artifact should record these dimensions separately:

| Dimension | Question answered |
|---|---|
| Canon status | Has the artifact itself entered committed governance or implementation history? |
| Layer | Does the activity belong to L1, L2, or L3? |
| Execution mode | Was the recorded activity simulated, internally performed in the real world, or externally performed in the real world? |
| Evidence authority | What claims may the evidence support? |
| Data treatment | How must the data be retained and made available? |
| Provenance and determinism | Can the event be attributed, replayed, and audited? |

No one dimension may be inferred from another.

A committed deterministic simulation record may therefore be:

- **Current Canon** as an artifact,
- **L1** in layer,
- **L1 simulated institutional rehearsal** in execution mode,
- **operational simulation evidence** in evidence authority, and
- **first-class operational data** in data treatment.

None of those labels implies that a real external organization acted.

---

## 3. Canon Status

| Value | Meaning | Authority |
|---|---|---|
| Current Canon | Committed repository truth or accepted committed governance record | Authoritative within its declared scope |
| Proposed Design | Intended future state not yet merged or accepted | Pre-canonical |
| Experimental Concept | Speculative research or prototype whose structure or use remains unsettled | Non-canonical |
| Historical State | Previously true or contextually relevant prior state | Reference |
| Assumption | Unverified working hypothesis | Unsafe for mutation |
| Deprecated | Explicitly retired or replaced material | Do not use for new work unless revived |

### 3.1 Simulation is not a canon-status category

Do not classify an artifact as `Experimental Concept` merely because it was produced by simulation.

Use `Experimental Concept` only when the artifact's design or intended use is genuinely experimental. A stable, deterministic, committed L1 simulation output is Current Canon as a record of that simulated event.

Canon status answers whether the artifact is authoritative as a record. It does not answer whether the event recorded was simulated or real-world.

---

## 4. Layer

| Value | Meaning |
|---|---|
| L1 | Orion Station operational reality anchor, including deterministic simulation of real institutional workflows |
| L2 | GUMAS simulation and research sandbox |
| L3 | THREADCORE symbolic mesh, capsules, drift, ethics, and continuity governance |

### 4.1 L1 institutional simulation

L1 may simulate institutional workflows such as:

- security reviews and penetration-test engagements,
- internal red-team exercises,
- incident response,
- audit committees,
- procurement and vendor selection,
- approval chains,
- evidence intake and chain of custody,
- remediation and retest cycles.

These remain L1 because they model operational institutions and decisions. They do not become L2 merely because the execution is simulated.

---

## 5. Execution Mode

| Value | Meaning |
|---|---|
| `l1_simulated_institutional_rehearsal` | Deterministic or bounded-replay L1 execution of an institutional workflow using simulated roles and interactions |
| `real_world_internal_exercise` | Activity performed by real Aurora participants or an accountable internal team |
| `real_world_external_engagement` | Activity performed by a verified external organization or independently accountable external assessor |
| `not_applicable` | Artifact does not represent an institutional event |

Execution mode must be explicit in the artifact itself or in a directly bound metadata record.

A context change, summary, export, or downstream transformation must preserve this mode. Silence is not inheritance.

---

## 6. Evidence Authority

| Value | May support | May not support |
|---|---|---|
| `operational_simulation_evidence` | Capability validation, workflow analysis, deterministic findings, issue creation, remediation planning, retest design, readiness assessment | Claims that a real person, firm, agency, regulator, or independent assessor acted |
| `internal_assessment_evidence` | Claims about work performed by an identified internal team, internal findings, internal control operation | Independent external assurance or third-party attestation |
| `independent_external_assurance` | Claims supported by attributable external evidence within the engagement scope | Claims beyond the assessor's scope, evidence, or accountability |
| `reference_evidence` | Historical or contextual interpretation | Current operational or assurance claims without fresh support |

Evidence authority is not a quality ranking. It is a boundary on the claims the evidence can support.

A simulated finding may be technically strong, reproducible, and operationally urgent. It remains `operational_simulation_evidence` because of who or what performed the event, not because the finding is weak.

---

## 7. Data Treatment

| Value | Required treatment |
|---|---|
| `first_class_operational_data` | Durable, queryable, attributable, retainable, eligible for analysis, issue creation, comparison, remediation, and replay |
| `reference_data` | Preserved for context but not used as current operational evidence without revalidation |
| `ephemeral_working_data` | Temporary intermediate data that may be discarded under an explicit retention policy |

### 7.1 First-class simulated data

Artifacts produced by a conforming L1 institutional rehearsal must use `first_class_operational_data` unless a narrower retention rule is explicitly justified.

First-class treatment requires:

- preserving the full source artifact rather than only an abstracted summary,
- retaining provenance, seed, baseline commit, scenario, tool version, and role representation,
- keeping the artifact available across contexts,
- allowing findings to enter normal issue, remediation, and retest workflows,
- avoiding automatic downranking, quarantine, or deletion solely because execution was simulated,
- preserving the original mode and authority labels in excerpts, exports, and derived products.

Aggregations and summaries are allowed, but they may not replace or erase the source artifact.

---

## 8. Provenance and Determinism

A deterministic L1 institutional event must record at minimum:

- event and run identifiers,
- scenario identifier,
- deterministic seed or replay key,
- baseline repository commit or immutable state reference,
- tool and tool version,
- execution timestamp,
- operator or invoking agent,
- institutional roles and whether each role is simulated or verified real-world,
- evidence inputs and outputs,
- execution mode,
- evidence authority,
- data treatment.

A run that cannot be replayed exactly must declare the bounded source of nondeterminism and preserve enough state to reproduce the decision path.

---

## 9. Non-Substitution Boundary

The following transitions are prohibited by relabeling, copying, summarizing, or canon promotion:

- simulated reviewer → real reviewer,
- simulated firm or agency → verified external organization,
- simulated signature → real approval,
- simulated finding → independently discovered finding,
- simulated engagement report → third-party attestation,
- Gate-001A completion → Gate-001B completion.

A real-world event requires a new evidence event with independently attributable provenance. It may reference earlier simulated artifacts as preparation or supporting analysis, but it does not inherit their execution mode.

No artifact may set `substitutes_for_real_world_review: true`.

---

## 10. Gate-001 Classification

| Track | Purpose | Execution mode | Evidence authority | Completion meaning |
|---|---|---|---|---|
| Gate-001A | Deterministic institutional rehearsal capability | `l1_simulated_institutional_rehearsal` | `operational_simulation_evidence` | Aurora can execute, preserve, inspect, and replay the security-review workflow |
| Gate-001B | Independently evidenced external engagement | `real_world_external_engagement` | `independent_external_assurance` | A verified external assessor performed a scoped real-world engagement |

The tracks are linked and mutually informative. They are not interchangeable.

Gate-001A artifacts are first-class operational data and may materially improve Gate-001B scope, readiness, finding triage, and remediation. They cannot satisfy Gate-001B.

---

## 11. Relationship to Evidence Labels

State dimensions describe what the artifact and event are. Evidence labels describe how a report's claim was reached.

| Example claim | Canon status | Execution mode | Evidence authority | Evidence label |
|---|---|---|---|---|
| A committed rehearsal found an auth bypass in seed 808 | Current Canon | L1 simulated institutional rehearsal | Operational simulation evidence | Observed |
| The bypass probably affects deployment configuration | Current Canon artifact; claim may remain Assumption | L1 simulated institutional rehearsal | Operational simulation evidence | Derived or Assumption |
| An external assessor reported the bypass | Current Canon only after evidence is committed | Real-world external engagement | Independent external assurance | Observed only with attributable evidence |

---

## 12. Required Artifact Block

```yaml
state_classification:
  canon_status: current_canon
  layer: L1
  execution_mode: l1_simulated_institutional_rehearsal
  evidence_authority: operational_simulation_evidence
  data_treatment: first_class_operational_data
  real_world_interaction: false
  independent_external_assurance: false
  substitutes_for_real_world_review: false

provenance:
  event_id: <stable-id>
  run_id: <stable-run-id>
  scenario_id: <scenario>
  deterministic: true
  seed: <seed-or-replay-key>
  baseline_commit: <git-sha>
  tool: <tool>
  tool_version: <version>
```

Use the institutional-assurance event contract for machine validation.

---

## 13. Red Flags

Pause when an artifact or report:

- uses `external`, `independent`, `agency`, `vendor`, or `assessor` without verified provenance,
- labels a simulated role with a real organization's identity without `simulated_role` representation,
- omits execution mode after a context transfer,
- preserves a summary but discards the source simulation output,
- calls a simulation merely hypothetical when it produced deterministic operational evidence,
- treats Gate-001A as satisfying Gate-001B,
- claims that canon promotion changed the historical mode of an event.

---

## 14. Hard Rules

- A simulated event may be canon as a simulated event.
- Simulated provenance does not reduce data treatment.
- Evidence authority constrains claims; it does not rank data quality.
- No simulation artifact becomes real-world evidence by implication or relabeling.
- No external assurance claim is valid without independently attributable external evidence.
- Repository commit is required before any governance artifact becomes canon.
