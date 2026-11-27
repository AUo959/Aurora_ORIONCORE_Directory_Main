# Canon Operations Bridge

The read adapter implements the pinned CanonRec v1 query contract against a local Git object database. Supply the full CanonRec data commit and explicit paths within one canon layer. The adapter reads committed JSON and newline-delimited JSON records. It checks request and result shapes against the published schemas at the separate, fixed contract revision. [CanonRec contract](https://github.com/AUo959/CanonRec/tree/778ba3b3aced338f30bc4b35accecf14ecf419a3/contracts/canon-ops/v1) · [Bridge issue #48](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/48)

```bash
python tools/canon_ops_query.py --canonrec /path/to/CanonRec query.json
```

The local Python environment needs `jsonschema` and its date-time format support. The CanonRec clone must contain the contract and data commits before the command runs. The query itself makes no network requests.

Entity IDs use the canonical record identifier. Aliases match names, recorded alternate identifiers, and aliases case-insensitively. Relationship filters match an explicit relationship pair or a matching native field ending in `_id` or `_ids`. Time filters use inclusive bounds. The adapter returns a source repository, path, layer, commit, and SHA-256 for each result. Requests with the same scope and pinned data return the same ordered page and cursor.

Station Chronicle entries are operational atoms. For a record without a native certainty tag, the adapter uses `UNCONFIRMED` and preserves the original record in the result. Collection labels distinguish sources by evidence status. CanonRec continues to own certainty and promotion decisions.

## Staging intake and receipts

Run intake from a trusted local operator context. The caller supplies the authenticated principal separately from the proposed request. The operator-owned policy binds exact grants to a principal, represented actor, submitting system, layer, and operation. It also pins the CanonRec data commit, target paths by layer, approving identities by layer, and trusted receipt origins by gate. Each origin is a repository and full commit. Paths must cover the target namespace used for revision comparisons.

| Policy field | Value |
| --- | --- |
| `version` | `"1.0"` |
| `canon_commit` | Full local CanonRec data commit |
| `target_paths` | Map from layer to paths within that layer |
| `grants` | Objects with `principal`, `actor_id`, `system`, `layer`, and `operation` |
| `approvers` | Map from layer to approved authority IDs |
| `gate_origins` | Map from gate name to lists of trusted origin objects with `repository` and `commit` |

The CanonRec validator checks the request against the fixed contract and verifies artifact bytes and receipt identity. For bridge intake, gate payloads also carry `subject_sha256`. Compute it from the request with `content_hash` and `gate_receipts` omitted, using the CanonRec canonical JSON encoding. The authorization receipt records `decision` and `authority` from the approved, pending, or rejected determination. The final reconciliation receipt records its `recommendation`. Acceptance requires approved authority, passing gates, and a recommendation of `STAGING`. The bridge retains all receipt references.

An accepted request records a local staging revision after comparing the expected state with the journal or the pinned CanonRec record. A pending decision or promotion-review request records a review disposition with no target change. Replaying an identical request returns the original receipt with `DUPLICATE`. An altered request needs a new request ID. The journal retains the pinned source and expected-state evidence, and CanonRec continues to control promotion.

When the final reconciliation gate includes a verified `entity_profile`, intake runs the CanonRec advisor at the pinned contract commit. It excludes promotion and map-lock recommendations and records the semantic result under `reconciliation_advisory`. The issued verdict and the bridge's staging disposition retain their original authority. A receipt without a profile retains the issuing gate's recommendation. A replay returns the original advisory without recalculating it.

```bash
python tools/canon_ops_intake.py --journal /path/to/staging.db submit request.json \
  --canonrec /path/to/CanonRec --policy policy.json --principal l1-relay \
  --repository Org/Source=/path/to/Source
python tools/canon_ops_intake.py --journal /path/to/staging.db status request-id
python tools/canon_ops_intake.py --journal /path/to/staging.db provenance L1 forecast forecast-id \
  --canonrec /path/to/CanonRec --policy policy.json
python tools/canon_ops_intake.py --journal /path/to/staging.db export > intake.json
python tools/canon_ops_intake.py --journal /path/to/restored.db rebuild intake.json \
  --expected-tip "$trusted_terminal_sha256"
```

Keep the journal outside the source checkouts. Use one journal per pinned CanonRec data snapshot. Save the exported history and its terminal digest in trusted custody. Reconstruction validates sequence, content identity, and the trusted terminal digest before publishing a new database.

`provenance` verifies the journal and returns the pinned CanonRec record, when present, and the ordered request and receipt entries for the exact layer, kind, and record ID. Entries retain the expected revisions, gate and source references, advisory results, and outcome links. Its policy must pin the same CanonRec commit as the journal. Use the full `export` to verify a terminal digest or rebuild the journal.

## Outcomes and Chronicle input

An approved `attach_outcome` receipt retains the verified source references and links each target to its recorded staging origin when available. This supports QGIA outcome and calibration attachments alongside the originating approval and forecast evidence. It preserves the target revision.

To register a GUMAS run, submit an approved L2 `attach_outcome` request in `deterministic_simulation` mode. Its pinned `deterministic_run` gate payload includes a normalized `run` object with `version`, `run_id`, `origin_request_id`, `origin_content_hash`, `engine_commit`, `seed`, `event_count`, and `completed_at`. The origin must match the approved staging revision of every target. A distinct request cannot register the same run ID again. The journal retains a reference to the original pinned receipt.

```bash
python tools/canon_ops_intake.py --journal /path/to/staging.db chronicle > chronicle-input.ndjson
```

The command emits sorted `STAGING` atoms using the Station Chronicle format. Each atom carries the approving actor and the pinned run receipt with its digest. A journal rebuilt from the same export produces the same atoms.

## Approved native GUMAS runs

The local run adapter accepts an L2 `scenario_seed` that is still at the approved staging revision. The mutation's sources must include the exact seed artifact. The run request identifies the accepted `origin_request_id` and `origin_content_hash`, sets `version` to `1.0` and `layer` to `L2`, and supplies that same pinned artifact as `scenario_seed`.

The seed artifact carries `version`, `seed_id`, optional `forecast_id`, `parameters`, and `engine`. The first supported parameter set contains `scenario_id` (`gumas_canonical_v1`), integer `seed`, positive integer `turns`, and `fabric_domain` (`union` or `velar`). The engine object pins `version` (`4.0.0-synth`) and the full Git `commit`. The operator policy uses the bridge trust pins and adds the permitted `engine_commit` and a list of authorized `l1_relays`. The CLI checks the journal's trusted terminal digest and re-reads the pinned authorization receipt before invoking GUMAS.

```bash
python tools/canon_ops_gumas.py run-request.json \
  --journal /path/to/staging.db --journal-tip "$trusted_terminal_sha256" \
  --policy policy.json --engine-repository /path/to/ORIONCORE --canonrec /path/to/CanonRec \
  --repository Org/Evidence=/path/to/evidence-git --run-root /path/to/run-artifacts
```

Each run directory contains the start and end state, the native event ledger, the Fabric Invariants report, and a semantic receipt. The receipt records the approval, approved inputs, exact engine files, state pointers, and artifact hashes. The state and ledger are checked against the approved scenario, seed, engine version, and turn interval.

The pinned Fabric checker audits the approved domain's source records at the approved CanonRec commit. It applies the project's static temporal, physical, and corporeal checks. Its findings cover that source scope. The native event ledger is verified separately. Source gaps remain visible in the receipt. A Fabric violation returns `NEEDS_REVIEW` with the findings before starting the simulation or publishing a run.

An ordinary repeat verifies the existing inventory. Add `--replay` to run the same inputs again and compare the resulting semantic receipt. The identity excludes the output path and wall-clock execution time. Reproducibility is scoped to the supported engine version and Python runtime. The adapter only publishes a completed run directory after verifying its native files.

To register the run in Chronicle, include the pinned `receipt.json` as a source in the approved `attach_outcome` request. Set the `deterministic_run` gate's `run_receipt` to that same artifact. Supply the normalized `run` fields described above, including the authorized completion time. Intake verifies the native receipt's semantic digest and compares its run identity, origin, seed, engine commit, and ledger count with the gate. The Chronicle atom then preserves both the native source and the registration gate.

## Authenticated local reads

The optional HTTP reader uses the FastAPI and Uvicorn dependencies in `requirements-ace-mcp.txt`. It binds to `127.0.0.1`. Configure the existing `ACE_REMOTE_PRINCIPALS_JSON` policy with a principal identifier, a bearer token SHA-256 digest, and the `ace:read` scope. A browser client requires its exact origin on the command line.

```bash
python -m tools.canon_ops_http --canonrec /path/to/CanonRec \
  --journal /path/to/staging.db --policy policy.json \
  --browser-origin http://localhost:4177
```

Send JSON requests with `Authorization: Bearer <token>`. `POST /v1/query` accepts a Canon Operations query within the configured snapshot and source scope. `POST /v1/provenance` accepts `layer`, `kind`, and `record_id`. `POST /v1/status` accepts `request_id` and returns the pinned journal entry with its receipt. Missing requests return an `unknown` finding. Staging and execution continue through the operator CLI.
