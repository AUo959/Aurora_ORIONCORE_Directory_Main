# AURORA Drive Intake — Read-Only Provenance Workflow v1.0 (2026-10-15)

## Purpose

Expose metadata about legacy Aurora files stored in the owner's connected Google Drive
to the **existing** Aurora root recovery-index review process. This is an external
discovery lane, **not** a replacement recovery indexer, runtime integration, canon
import, replication system, or evidence of content equivalence.

Current owner surfaces:
- Root control plane: `AUo959/Aurora_ORIONCORE_Directory_Main`
- Recovery policy: `docs/CONTROL_PLANE_PROVENANCE.md`
- Existing local recovery workflow: `docs/RECOVERY_INDEX_WORKFLOW_v1.md`
- Authority system: `AUo959/CanonRec` (not touched)
- CloudBank runtime: `AUo959/aurora-cloudbank-symbolic` (not touched)

## Private intake contract

A locally-held JSON export may contain:
- `schema_version: 1`, `provider: "google_drive"`, `access_class: "private"`;
- `observed_at`, `scope`, and an array `records`;
- each record's `source_id`, `title`, `mime_type`, `source_url`,
  optional Drive `modified_time`, optional `size_bytes`, `content_sha256: null`,
  `review_status: "pending_review"`, `promotion_status: "not_promoted"`;
- optional `repository_matches` with `repository`, `path`, `relationship`
  (`keyword_reference`, `verified_path`, or `candidate`), `authority: "none"`.

No file content or metadata snapshot from a private Drive is committed to this
public repository. Google Drive modification timestamps may reflect upload time
rather than original authorship. No content hash is claimed unless source bytes
are separately authenticated and evaluated in a later approved review.

## Run locally

Keep the exported JSON outside the published working tree.

```sh
python3 tools/drive_recovery_snapshot.py /private/path/drive-snapshot.json
python3 -m unittest discover -s tests -p 'test_drive_recovery_snapshot.py'
```

The tool reads a local JSON file and prints only aggregate counts; no network
calls, file writes, or state changes. It neither needs nor stores Google tokens.

## Triage / promotion separation

1. Discover source metadata with an authorized Drive connector.
2. Save a private metadata-only snapshot, marked `pending_review`.
3. Validate offline with `tools/drive_recovery_snapshot.py`.
4. Compare selected candidates with existing recovery index signals and verified
   GitHub code paths. A same-name or keyword hit is **not** proof of equivalence.
5. Any content comparison, extraction, reuse, or canonical promotion needs a
   separate reviewed decision and an evidence receipt.
6. Preserve CanonRec authority and the deterministic L1 runtime. No action in
   this workflow mutates either.

Security rules: no secrets, private text, personal data, file identifiers, or
shareable Drive URLs in public issues/PRs. Do not interpret Drive access as
permission to publish its contents. Treat archived Copilot transcripts and
executable source as potentially sensitive until reviewed.

## Known limitations of this first stage

- Inventory covers discovered sources in the authorized scope, not all of Drive.
- Paths and keyword overlaps support triage, not runtime capability verification.
- There is no automated polling, synchronization, embedding, canonical promotion,
  runtime loader, or in-repo storage of the private snapshot.
- This route intentionally complements the existing `workspace_recovery_index`
  rather than altering its scoring or reports.
