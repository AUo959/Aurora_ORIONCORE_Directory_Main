# Continuity Package Policy

Version 1.0 · Proposed governance policy pending review

ORIONCORE defines continuity policy for preservation, replay, inheritance, relay, and publication. CloudBank owns schemas, persistence, authenticated enforcement, and audit receipts. Apply this policy alongside the [State Classification Model](AURORA_GOVERNANCE__REFERENCE__STATE_CLASSIFICATION_MODEL__v2.0__2026-07-27.md). [Governance issue #46](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/46) · [CloudBank implementation issue #1380](https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1380)

## Independent dimensions

| Field | Values | Evidence |
| --- | --- | --- |
| `integrity_status` | `unverified`, `verified`, `failed` | A digest comparison tied to a specific package revision and digest algorithm. |
| `signature_status` | `unsigned`, `unverified`, `verified`, `revoked` | A signature verification result tied to the signed revision, identified key, supported algorithm, and current revocation evidence. |
| `organizational_trust` | `none`, `pending`, `trusted`, `suspended`, `revoked` | An accountable organizational decision tied to a subject, scope, and issuing authority. |
| `authorization_status` | `absent`, `active`, `expired`, `revoked` | A grant tied to an authenticated actor, operation, resource, tenant, and validity interval. |
| `consent_status` | `not_required`, `absent`, `active`, `expired`, `revoked` | A scoped consent record or a documented classification decision that exempts the operation from consent. |
| `package_lifecycle` | `active`, `superseded`, `archived`, `withdrawn` | A custody decision recorded for a particular package revision. |

Record the dimensions independently for the subject and scope they describe. For example, verified integrity and an unsigned package can coexist. A verified signature with absent authorization carries signer evidence and grants zero operations. Active authorization and revoked consent can coexist, but consent-dependent operations are denied. Historical integrity and signature evidence survives subsequent revocation.

## Transitions and validation

Every transition records the old and new state, actor or authoritative source, timestamp, relevant scope, reason, and evidence reference. Append a decision or verification record so earlier decisions remain auditable. Re-evaluate effective status before acting.

| Dimension | Permitted transitions and conditions |
| --- | --- |
| Integrity | An unverified revision becomes verified or failed after comparing its digest. A fresh comparison can change either outcome for the same revision. Changed bytes require a new revision with its own verification. A digest alone cannot set signer status. |
| Signature | A presented signature starts unverified. Successful verification against an identified key and a current revocation check can mark it verified. Either signature state becomes revoked on attributable revocation evidence. New signatures carry their own verification records. A revoked signature cannot be restored by rechecking its bytes. |
| Organizational trust | A scoped review moves none to pending, and a documented decision can adopt trust or decline it. Trusted subjects can be suspended or revoked by the governing authority. Suspension can return to trusted after a fresh decision within the same scope. Revoked decisions remain in history, and any subsequent trust requires a new decision. |
| Authorization | Only an authority that can grant the requested operation can turn absent into active. Time expiry or an attributable decision moves active to expired or revoked. Renewal or replacement requires a new grant. |
| Consent | Absent becomes active through attributable consent within scope. Time expiry or a valid revocation moves active to expired or revoked. Fresh consent requires a new record. `not_required` requires a recorded exemption for this operation and must be reevaluated if the operation, recipient, purpose, or data changes. |
| Lifecycle | Active can become archived, superseded, or withdrawn through an attributable custody decision. Restoring an archived revision requires fresh scope and authority validation. A substitute for a superseded or withdrawn revision is a new revision with linked lineage and its own decisions. |

Reject claims of verified integrity without a matching digest check, verified signatures without the corresponding verification evidence, and active grants without a current scope match. Treat missing, conflicting, or unverifiable evidence as insufficient for the requested operation. A declaration of trust, lifecycle, simulation, or canon status cannot supply missing evidence in another dimension.

## Consent and scope

Require consent for continuity operations involving personal data, private communications, identity-linked memory, confidential work, cross-user context, restricted intellectual property, or sensitive operational data. Preserve the classification and purpose limits in copies and derivatives.

A consent record identifies the consenting party or authoritative identity reference, authority basis, purpose, permitted operations, prohibited downstream uses, issue and expiry times, revocation method and applicable evidence, covered and excluded data classifications, and the tenant, user, repository, and continuity-object scope. Permitted operations are explicit and may include reference, copy, replay, inheritance, relay, publication, and execution.

Consent cannot transfer automatically to a different actor, tenant, repository, purpose, or operation. Identity-linked memory, private communications, and restricted material require separate consent for any downstream use outside the original grant. Cross-tenant use also requires independently verified authority in each tenant. Deny the operation when required consent is missing, stale, revoked, unverifiable, or out of scope.

Simulated consent and symbolic records remain evidence within their recorded execution mode. They give zero real-world authority. L1 custody can preserve evidence of institutional rehearsal. L2 research replay and L3 continuity governance each require their own scope and authority. When an artifact crosses a layer or execution mode, keep its source classification and verify the destination operation separately.

## Retention and deletion

| Action | Effect |
| --- | --- |
| Retain | Keep under active custody for an authorized retention period. |
| Archive | Keep under reduced active use and its applicable access and retention controls. |
| Redact | Remove or mask identified content and preserve an accountable record of the redaction. |
| Revoke | Withdraw permission or trust and preserve the historical record. |
| Supersede | Replace the current revision and preserve lineage. |
| Destroy | Remove a named copy under documented authority. |
| Purge | Verify removal across the declared stores and all copies included in the purge scope. |

Deletion evidence records scope, authority, timestamp, reason, verification method, and the outcome for primary stores, replicas, backups, registries, projections, indexes, and caches. It identifies surviving metadata and outstanding provider or third-party copies. Record an outstanding copy as unresolved until the relevant custodian supplies evidence. Archival state, a deletion request, and a repository-side removal receipt each support only their recorded action.

## Execution and high-impact confirmation

Executable content stays disabled by default, including instructions, embedded prompts, symbolic commands, scripts, binaries, and configuration capable of triggering actions. Declare the executable content identity and digest, runtime and dependency requirements, filesystem, network, model and secret-reference needs, requested permissions, expected effects, sandbox, approval and reflective-pause requirements, and rollback or containment. A manifest is descriptive. Activation requires separately verified authority and an enforcement decision for the declared operation. Secret references identify a controlled resolution request. Package records must exclude plaintext secret values.

Export of sensitive material, relay or live synchronization, identity-linked inheritance, publication of a package or registry record, code execution, destruction or deletion, secret resolution, and canon promotion each require an explicit authorization or confirmation from the responsible authority. The approval must name the actor, action, target revision, scope, and expiry. Revalidate consent, layer, and other permissions when the action runs. A positive decision for one action cannot authorize another.

## Implementation and revisions

CloudBank maps its schemas, validators, audit and Insight Ledger events, authenticated endpoints, tenant isolation, DLP, safe logging, and secret-reference handling to the definitions in this policy. Each enforcement claim needs a normal-path test and an applicable denial test. Require evidence for expired or revoked consent and authorization, mismatched scope, digest-as-signature, simulated-as-real authority, unknown external copies, and disabled executable content. Describe encryption, secret resolution, relay, or deletion as active only where implementation evidence supports the claim.

For a policy change, update the ORIONCORE definition through a reviewed commit. The implementing repository pins that revision, updates its mappings and tests, and records rollout status and any unsupported contract fields. Independent review and implementation evidence are tracked in the linked governance and implementation issues.
