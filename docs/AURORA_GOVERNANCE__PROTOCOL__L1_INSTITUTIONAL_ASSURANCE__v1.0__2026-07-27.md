# L1 Institutional Assurance Protocol

**Document ID:** `AURORA_GOVERNANCE__PROTOCOL__L1_INSTITUTIONAL_ASSURANCE`  
**Version:** v1.0  
**Date:** 2026-07-27  
**Authority:** Governance Layer  
**Status:** Proposed governance canon until merged  
**Related:** `Aurora_ORIONCORE_Directory_Main#44`, `aurora-cloudbank-symbolic#1350`

---

## 1. Purpose

This protocol defines how Aurora creates, preserves, validates, and reuses institutional-assurance events across contexts.

It applies to simulated and real-world workflows including external security reviews, internal red-team exercises, incident response, audit committees, procurement, evidence intake, remediation, and retesting.

The protocol is designed around a non-negotiable distinction:

- simulation output is first-class operational data;
- simulation output is not evidence that a real-world actor performed the simulated interaction.

---

## 2. Institutional Event Modes

### 2.1 L1 simulated institutional rehearsal

A deterministic L1 execution using simulated institutional roles. It may produce:

- findings,
- evidence ledgers,
- risk ratings,
- issue proposals,
- remediation plans,
- retest results,
- approval-path analysis,
- simulated engagement reports.

These outputs enter normal operational workflows and are retained as first-class data.

Every person, team, firm, agency, signature, communication, and decision represented by the simulation must be identifiable as simulated in the bound metadata. The body of the artifact should remain readable and operational rather than being flooded with repetitive disclaimers.

### 2.2 Real-world internal exercise

An exercise performed by identifiable Aurora participants or an accountable internal team. It produces internal assessment evidence, not independent external assurance.

### 2.3 Real-world external engagement

An engagement performed by a verified external organization or independently accountable external assessor. Its claims require external primary evidence, a defined scope, an identified baseline, and attributable findings or attestation.

---

## 3. Labeling Without Abstraction

Labels belong in a stable header or bound metadata record. They must be visible, machine-readable, and preserved across exports.

Labels must not replace the institutional content with abstract commentary. A simulated report should still contain the complete scope, methods, evidence, findings, deliberations, remediation, and retest record.

Use concise in-body language where identity could otherwise be mistaken, for example:

- `Simulated assessor role: Red Team Lead`
- `Simulated institutional decision`
- `No real-world vendor interaction occurred in this event`

Do not prepend every paragraph with a disclaimer. The metadata and role labels carry the boundary while the report remains useful.

---

## 4. Required Event Envelope

Every institutional-assurance event must conform to the contract at:

`catalog/contracts/AURORA_L1__CONTRACT__INSTITUTIONAL_ASSURANCE_EVENT__v1.0__2026-07-27.json`

Required dimensions include:

- canon status,
- layer,
- execution mode,
- evidence authority,
- data treatment,
- Gate track,
- real-world interaction flag,
- independent assurance flag,
- non-substitution flag,
- deterministic provenance,
- institutional role representation,
- evidence references.

---

## 5. Deterministic Rehearsal Requirements

Gate-001A and similar rehearsals must preserve:

1. Baseline commit or immutable system-state reference.
2. Scenario ID and version.
3. Deterministic seed or replay key.
4. Tool and tool version.
5. Inputs, constraints, and role assignments.
6. Ordered event and decision trace.
7. Evidence produced and evidence consumed.
8. Findings, severity method, and rationale.
9. Remediation and retest state.
10. Complete source artifacts plus any summaries.

The same envelope must remain valid when the artifact is copied into another context, converted to another format, or incorporated into a later institutional workflow.

---

## 6. First-Class Data Guarantees

Conforming simulated output must not be:

- automatically downranked in search or analysis,
- quarantined solely because it is simulated,
- reduced to a prose abstraction while the source is discarded,
- excluded from issue creation or remediation workflows,
- prevented from establishing deterministic capability evidence,
- silently relabeled as experimental.

It may be superseded by later runs, but supersession must preserve lineage and history.

---

## 7. Non-Substitution Rules

A Gate-001A event cannot satisfy Gate-001B.

A real-world engagement record may cite Gate-001A artifacts as:

- scope preparation,
- threat-model input,
- candidate test cases,
- prior internal findings,
- remediation evidence,
- replay fixtures.

It must still include new external primary evidence. The real-world record receives a new event ID and its own provenance.

Forbidden actions include:

- changing `execution_mode` on an existing event,
- changing simulated role representation to verified real identity,
- treating a simulated signature as approval,
- claiming external discovery from a simulation-only evidence chain,
- using canon promotion to rewrite event history.

---

## 8. Gate-001

### Gate-001A — Deterministic institutional rehearsal capability

Pass conditions:

- a complete security-review workflow can be executed deterministically;
- outputs conform to the event contract;
- evidence, findings, decisions, remediation, and retest steps are preserved;
- replay produces the same decision path for the same baseline and seed;
- context transfer preserves mode, authority, provenance, and source artifacts;
- no output claims real-world interaction or independent external assurance.

### Gate-001B — Independently evidenced real-world engagement

Pass conditions:

- a verified external assessor or organization is identified;
- scope and baseline are recorded;
- authorization and engagement evidence are attributable;
- findings or attestation originate from the external engagement;
- remediation and retest records preserve external provenance;
- no Gate-001A artifact is substituted for missing external evidence.

Gate-001A is a maintained capability, not a one-time checklist. Gate-001B is a separately evidenced engagement state.

---

## 9. Context Transfer

When an event moves between chat, repository, report, simulation harness, issue, PR, or archive:

- retain the stable event and run IDs;
- retain the source artifact or durable link;
- retain all classification dimensions;
- retain the baseline and seed;
- record the transformation that created the new representation;
- never infer real-world interaction from institutional realism.

If a receiving context cannot preserve the envelope, the transfer is incomplete and must be marked Blocked.

---

## 10. Promotion and Canon

Committing an event makes the artifact canonical as a record of what its envelope says occurred.

Promotion may make a simulated event authoritative evidence that the simulation ran, produced specific findings, and exercised a capability. Promotion does not make the represented interaction real-world.

Real-world assurance requires a separate event with external provenance.

---

## 11. Validation

Run:

```bash
python3 tools/l1_institutional_assurance_validate.py <event.json>
```

The validator fails closed on:

- missing dimensions,
- execution-mode and authority mismatches,
- simulation claiming real-world interaction,
- simulation claiming independent assurance,
- non-first-class treatment for Gate-001A output,
- missing deterministic provenance,
- simulated roles represented as verified real entities,
- Gate-001B records without external primary evidence.

---

## 12. Rollback

Rollback removes this protocol, contract, validator, and tests through a normal revert. Existing simulation artifacts retain their historical provenance and are not reclassified silently.
