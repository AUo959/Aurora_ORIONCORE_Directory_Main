# Aurora_ORIONCORE_Directory_Main#46: governance(continuity): define canonical trust, consent, retention, revocation, and execution-risk policy

- URL: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/46
- State at archive: open
- Author: AUo959
- Created: 2026-07-28T01:13:53Z
- Updated: 2026-07-28T01:28:54Z
- Labels: none
- Milestone: none

## Linked pull requests (head SHA at archive time)

- Aurora_ORIONCORE_Directory_Main#119 — Define continuity package governance policy — merged — `codex/continuity-package-policy` @ `1adebbc8d6666d9b5e5d36b29da90c045f320c90`

## Branches named in the issue

- none

## Original body

## Purpose

Establish the normative governance model for continuity-package trust, consent, authorization, retention, revocation, deletion evidence, and execution-risk classification.

This issue is the control-plane companion to `AUo959/aurora-cloudbank-symbolic#1380`. ORIONCORE owns the canonical definitions and permitted transitions. CloudBank owns schemas, validators, persistence mappings, APIs, enforcement, and tests.

## Current state

**Observed:** The State Classification Model requires architecture-sensitive records to classify independent dimensions separately. Canon status, layer, execution mode, evidence authority, data treatment, and provenance must not be inferred from one another.

**Observed:** CloudBank issue #1380 proposes preservation security and ethics contracts, but its initial trust-level list combines integrity verification, signature verification, organizational trust, and revocation into one enum.

**Derived:** A canonical control-plane policy is needed before implementation so CloudBank does not create an incompatible trust or consent vocabulary.

## Normative ownership

ORIONCORE governs:

- canonical definitions and terminology;
- independent classification dimensions;
- permitted and prohibited state transitions;
- consent scope and authority rules;
- retention, archive, redaction, revocation, destruction, and purge distinctions;
- non-substitution boundaries between integrity, authentication, trust, authorization, and consent;
- cross-repository synchronization requirements;
- real/simulated and L1/L2/L3 authority boundaries.

CloudBank implements:

- JSON schemas and data models;
- validators and negative fixtures;
- persistence and Insight Ledger mappings;
- authenticated APIs and policy enforcement;
- DLP, tenant-isolation, safe-logging, and secret-reference controls;
- audit receipts, tests, and rollback behavior.

## Required independent dimensions

```yaml
integrity_status:
  unverified | verified | failed

signature_status:
  unsigned | unverified | verified | revoked

organizational_trust:
  none | pending | trusted | suspended | revoked

authorization_status:
  absent | active | expired | revoked

consent_status:
  not_required | absent | active | expired | revoked

package_lifecycle:
  active | superseded | archived | withdrawn
```

These fields are independent. For example:

- a package may have verified integrity but no verified signer;
- a verified signature does not grant authorization;
- organizational trust does not imply consent;
- revoking authorization does not rewrite historical integrity evidence;
- archival state is not proof of deletion.

## Consent contract

A consent record must identify:

- consenting party or authoritative identity reference;
- authority basis;
- purpose and granted scope;
- permitted operations: reference, copy, replay, inheritance, relay, publication, execution;
- prohibited downstream uses;
- issue and expiry timestamps;
- revocation method and revocation evidence;
- content classifications covered and excluded;
- relationship to tenant, user, repository, and continuity-object scope.

Consent must fail closed when absent, expired, revoked, unverifiable, or outside scope.

Simulated consent, fictional-role consent, presentation metadata, symbolic ethics language, repository ownership, shared anchors, or signatures cannot substitute for real authorization.

## Trust and signature boundaries

- Integrity proves content consistency against a digest; it does not identify a signer.
- Signature verification requires an identified key, supported algorithm, verification result, and revocation posture.
- Organizational trust requires an independently governed trust decision.
- Authorization is operation- and scope-specific.
- Consent applies to the relevant person, data, purpose, and downstream use.
- No field may self-authorize execution, relay activation, publication, deletion, or canon promotion.

## Retention and deletion model

The policy must distinguish:

- `retain` — keep under active custody;
- `archive` — preserve with reduced active use;
- `redact` — remove or mask specified content while retaining an accountable record;
- `revoke` — withdraw permission or trust without pretending historical records never existed;
- `supersede` — replace for current use while retaining lineage;
- `destroy` — intentionally remove an identified copy under authority;
- `purge` — verified removal across declared stores, replicas, indexes, and caches.

Deletion evidence must record scope, authority, time, reason, verification method, known replicas and projections, surviving metadata, and unresolved provider-side or third-party copies. Repository-side deletion alone cannot substantiate provider-side credential or data removal.

## Execution-risk policy

Executable content is disabled by default and must declare:

- content identity and integrity reference;
- runtime and dependency requirements;
- filesystem, network, model, and secret needs;
- permissions and expected side effects;
- sandbox requirements;
- approval and reflective-pause requirements;
- rollback or containment behavior.

A manifest declaration cannot activate execution. Natural-language instructions, ritual commands, symbolic seals, embedded prompts, or configuration fields are never authorization by themselves.

## High-impact confirmation gate

Explicit authorization or confirmation is required before:

- exporting sensitive material;
- activating a relay or live synchronization;
- inheriting identity-linked context;
- publishing a package or registry record;
- executing included code;
- deleting or destroying preserved records;
- resolving secret references;
- promoting imported material toward canon.

## Acceptance criteria

- [ ] Integrity, signature, organizational trust, authorization, consent, and lifecycle are separate dimensions.
- [ ] Canonical transition rules and invalid combinations are documented.
- [ ] Consent scope, expiry, revocation, and non-transferable classes are explicit.
- [ ] Simulated or symbolic records cannot become real authorization by relabeling.
- [ ] Retain, archive, redact, revoke, supersede, destroy, and purge are distinct.
- [ ] Deletion evidence accounts for replicas, caches, indexes, and unresolved external copies.
- [ ] Executable content remains disabled by default.
- [ ] High-impact actions require explicit approval or confirmation.
- [ ] L1/L2/L3 and real/simulated authority distinctions remain intact.
- [ ] CloudBank #1380 maps to this policy rather than defining competing semantics.
- [ ] Governance changes land through a reviewed commit before being called canon.

## Non-goals

- implementing a secret vault;
- implementing encryption or key management;
- building runtime enforcement in ORIONCORE;
- inferring consent automatically;
- autonomous deletion;
- provider-side deletion claims without provider evidence;
- treating symbolic ethics labels as security controls.

## Boundary impact

Proposed governance-layer policy. Opening this issue changes no runtime, permissions, encryption, execution, deletion, relay, L1 authority, L2/GUMAS state, or canon. Git commit remains required for governance canon promotion.

## Related

- CloudBank #1380 — implementation schema, validators, enforcement, and tests
- CloudBank #1376 — Universal Thread Beacon interoperability epic
- CloudBank #1378 — replay and inheritance contracts
- CloudBank #1379 — relay and discovery contracts
- CloudBank #1374 — continuity package, restore staging, and mutation receipts
- ORIONCORE State Classification Model v2.0

## Comments (1)

### AUo959 — 2026-07-28T01:28:54Z

<https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/46#issuecomment-5098816467>

## Cross-repository validation status

The CloudBank issue-hardening pass is complete at the proposal level.

Implementation issues now explicitly map to this control-plane authority:

- `aurora-cloudbank-symbolic#1380` — policy schemas, validators, persistence/enforcement mapping, tests, and receipts;
- `#1378` — consent- and authorization-constrained replay/inheritance;
- `#1379` — policy-constrained relay and discovery;
- `#1377` — policy references projected into the neutral beacon profile;
- `#1374` — integrity/signature distinction in package validation.

Required sequencing is now: neutral profile mapping, normative policy mapping, replay/inheritance, then relay/discovery.

No governance definition becomes canon until committed through a reviewed ORIONCORE PR. CloudBank implementation must reference the committed policy version and must not silently fork these enums or transitions.
