# aurora-cloudbank-symbolic#1380: security(continuity): define trust, consent, revocation, retention, and execution-default-off controls

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1380
- State at archive: open
- Author: AUo959
- Created: 2026-07-28T00:56:44Z
- Updated: 2026-09-14T09:17:40Z
- Labels: stale, backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- Aurora_ORIONCORE_Directory_Main#119 — Define continuity package governance policy — merged — `codex/continuity-package-policy` @ `1adebbc8d6666d9b5e5d36b29da90c045f320c90`
- aurora-cloudbank-symbolic#46 — deps: bump dotenv from 17.0.0 to 17.0.1 — closed — `dependabot/npm_and_yarn/dotenv-17.0.1` @ `71b5dfce8e55d94042850236ccd674aa4cb6f213`
- aurora-cloudbank-symbolic#1381 — feat(continuity): add neutral Universal Thread Beacon schema and offline validator — merged — `feat/1377-utb-neutral-schema` @ `83dcf25f8e092e8295b76f1302a30fd955e54710`
- aurora-cloudbank-symbolic#1511 — feat(contracts): OPAL2 shipment-manifest schema with worked example (#1510) — merged — `codex/cloudbank-issue-1510-shipment-manifest` @ `86fde15158c5b5b02dc904c2f9d469f397c1df82`
- aurora-cloudbank-symbolic#1533 — feat(salvage): add deterministic corpus archaeology Phase 1 — merged — `feat/1526-corpus-archaeology-phase1` @ `6b7dffdd94dedce920223addc37497380dc5ad62`
- aurora-cloudbank-symbolic#1536 — feat(salvage): add custody-release corpus adapter — merged — `feat/1535-corpus-custody-release-adapter` @ `f22f48a0dd91479dd30047ce08adafc2259e8bb2`

## Branches named in the issue

- none

## Original body

## Parent

Part of #1376 — Universal Thread Beacon preservation profile.

Normative governance companion: `AUo959/Aurora_ORIONCORE_Directory_Main#46`.

Related CloudBank foundations:

- #1377 for beacon policy references and extension fields;
- #1378 for consent-constrained replay and inheritance;
- #1379 for relay, transfer, registry, and discovery;
- #1374 for integrity, restore staging, and mutation receipts;
- existing authentication, CSRF, tenant-isolation, DLP, safe-logging, and Insight Ledger controls.

## Ownership boundary

ORIONCORE #46 owns:

- canonical definitions;
- independent policy dimensions;
- permitted and prohibited transitions;
- consent, retention, revocation, deletion, and execution-risk doctrine;
- real/simulated and L1/L2/L3 authority boundaries.

This CloudBank issue owns:

- JSON schemas and models;
- validators and negative fixtures;
- persistence and Insight Ledger mappings;
- authenticated API and enforcement integration;
- DLP, tenant-isolation, safe-logging, and secret-reference controls;
- implementation tests and receipts.

CloudBank must map to ORIONCORE policy rather than define competing semantics.

## Current state

**Observed:** Aurora capsule exchange includes trust-related fields, anchor checks, ethics checks, content digests, DLP tags, and authenticated routes.

**Observed:** Existing fields do not yet form a complete preservation-policy implementation for explicit consent, independent trust dimensions, execution-default-off behavior, secret references, revocation, retention, deletion evidence, and high-impact confirmation gates.

**Derived:** The package contributes a valuable implementation layer, but documentation fields alone cannot substantiate enforcement. Every enforced claim must map to code and tests in the owning implementation surface.

## Required independent fields

Do not use a single trust-level ladder. Integrity, signer verification, organizational trust, authorization, consent, and lifecycle are independent.

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

Rules:

- verified integrity does not identify a signer;
- a verified signature does not grant authorization;
- organizational trust does not imply consent;
- consent does not grant operations outside its scope;
- revoking authorization does not rewrite historical integrity evidence;
- archival state is not proof of deletion;
- no field self-authorizes replay, inheritance, relay, publication, execution, deletion, or canon promotion.

## Consent records

Consent is required when preservation, replay, inheritance, registry, relay, or publication includes:

- personal information;
- private communications;
- identity-linked memory;
- confidential work;
- cross-user context;
- restricted intellectual property;
- sensitive operational context.

A consent record must identify:

- consenting party or authoritative identity reference;
- authority basis;
- granted scope and purpose;
- permitted operations: reference, copy, replay, inheritance, relay, publication, execution;
- prohibited downstream uses;
- issue and expiry timestamps;
- revocation method and evidence;
- content classifications included and excluded;
- tenant, user, repository, and continuity-object scope.

Consent fails closed when absent, expired, revoked, unverifiable, or outside scope.

Simulated consent, fictional-role consent, presentation metadata, symbolic ethics language, repository ownership, shared anchors, aliases, digests, or signatures cannot substitute for real authorization.

## Integrity and signature handling

- Current SHA-256 capsule values are treated as content-integrity digests.
- `signature_status=verified` requires an identified key, supported algorithm, signer identity reference, verification evidence, and revocation posture.
- A content digest must not be displayed or logged as an authenticated signature.
- Organizational trust must not be inferred from repository ownership or a shared symbolic anchor.

## Secret handling

- Plaintext credentials must not be embedded in preservation packages.
- Secret requirements use references such as vault identifiers.
- Package inspection and validation must not resolve secrets automatically.
- Logs, issues, validation errors, fixtures, and receipts must not expose secret values.
- Provider-side credential safety cannot be inferred from repository-side deletion.

## Executable content

Executable content must be:

- explicitly classified;
- separated from documentation where practical;
- integrity-bound;
- disabled by default;
- subject to sandbox and policy review;
- covered by declared runtime, permissions, inputs, outputs, filesystem, network, model, and secret requirements;
- associated with explicit approval and rollback or containment behavior.

No package importer may execute content solely because a manifest declares it executable.

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

## Retention, deletion, and revocation

Implementation must distinguish:

- `retain` — active custody;
- `archive` — preserved with reduced active use;
- `redact` — remove or mask specified content while retaining an accountable record;
- `revoke` — withdraw permission or trust;
- `supersede` — replace for current use while retaining lineage;
- `destroy` — remove an identified copy under authority;
- `purge` — verify removal across declared stores, replicas, indexes, and caches.

Deletion evidence must record:

- scope and authority;
- timestamp and reason;
- verification method;
- replicas, indexes, caches, registries, and projections considered;
- surviving metadata;
- unresolved provider-side or third-party copies.

## Selective-integration boundaries

- A signature, anchor, seal, trust label, persona statement, ethics phrase, or repository relationship is not permission by itself.
- Documentation does not prove enforcement; implementation claims require code and tests.
- Revoked packages, authorizations, or consent fail closed.
- Cross-user and cross-tenant access remains prohibited without independently validated authority.
- Encryption requirements may be declared, but encryption must not be claimed as active without implementation evidence.
- No policy record may collapse L1/L2/L3 boundaries or promote simulated consent into real-world authorization.
- No schema or configuration field activates execution, networking, deletion, secret resolution, or canon promotion.

## Proposed first deliverable

A schema/policy-adapter/validator PR containing:

- mapping to ORIONCORE #46;
- independent integrity, signature, organizational-trust, authorization, consent, and lifecycle fields;
- consent-record schema;
- executable-content risk schema;
- retention/deletion/revocation schema;
- secret-reference validation;
- negative fixtures for embedded secrets, expired consent, revoked authorization, signature-as-permission, digest-as-signature, simulated consent, and configuration-triggered execution;
- mapping to current authentication, DLP, ledger, and capsule controls;
- no encryption service, key management, secret resolution, code execution, deletion, or relay activation.

## Acceptance criteria

- [ ] ORIONCORE #46 is the normative policy source.
- [ ] Integrity, signature, organizational trust, authorization, consent, and lifecycle are separate fields.
- [ ] Trust and authorization transitions are evidence-bearing and auditable.
- [ ] Sensitive transfer or inheritance fails without scoped, unexpired consent and authorization.
- [ ] Plaintext credentials and secret values are rejected or quarantined safely.
- [ ] Current content digests cannot be represented as authenticated signatures.
- [ ] Executable content is explicitly labeled and disabled by default.
- [ ] High-impact actions require explicit authorization or confirmation.
- [ ] Retain, archive, redact, revoke, supersede, destroy, and purge are distinguishable.
- [ ] Deletion records cover surviving indexes, replicas, caches, registries, and unresolved external copies.
- [ ] Policy declarations cannot activate encryption, networking, execution, deletion, secret resolution, or canon promotion.
- [ ] Tenant isolation, safe logging, and DLP boundaries are represented and tested where enforcement is implemented.
- [ ] L1/L2/L3 and real/simulated authority distinctions remain intact.

## Non-goals

- building a secret vault;
- implementing key management or encryption in this issue;
- automatic consent inference;
- autonomous deletion;
- automatic execution or relay activation;
- using symbolic ethics labels as enforcement evidence;
- replacing existing authentication, DLP, or Insight Ledger systems;
- defining policy independently from ORIONCORE #46.

## Boundary impact

L3 policy-schema, validation, and future enforcement integration. Opening or refining this issue performs no execution, encryption, deletion, relay activation, authorization change, L1 authority change, or L2/GUMAS mutation.

## Comments (2)

### AUo959 — 2026-07-28T01:28:37Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1380#issuecomment-5098815002>

## Validation hardening — normative policy mapping and independent trust dimensions

The control-plane companion already exists as `AUo959/Aurora_ORIONCORE_Directory_Main#46`. Reuse it rather than creating a competing policy authority.

For CloudBank implementation, the original single trust-level list is superseded by independent dimensions:

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

These fields must not imply one another:

- verified integrity does not identify a signer;
- a verified signature does not grant authorization;
- organizational trust does not establish consent;
- revocation does not rewrite historical integrity evidence;
- archival state is not deletion evidence.

### Ownership

- ORIONCORE #46 owns canonical definitions, permitted transitions, consent doctrine, retention/deletion semantics, and real/simulated authority boundaries.
- CloudBank #1380 owns JSON schemas, validators, persistence/ledger mappings, authenticated APIs, enforcement, DLP, safe logging, tenant isolation, tests, and receipts.

The first PR remains schema/policy-mapping/validator only. It must not implement secret resolution, encryption, execution, deletion, relay activation, or automatic consent inference.

### github-actions[bot] — 2026-09-14T09:17:39Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1380#issuecomment-5661735687>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.
