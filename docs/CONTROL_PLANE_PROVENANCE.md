# Control Plane Provenance and Recovery Role

This document records project provenance supplied by the workspace owner. It is
an operating note for the root control-plane repo, not a canon promotion receipt
and not evidence that any recovered item is already authoritative.

## Origin

The root control-plane repository began as a local file archive on the owner's
machine. It did not begin as a GitHub-native source repository.

Before the root control plane and GitHub workflows were connected, Aurora
CloudBank existed on GitHub as its own implementation repo. The local archive
and the CloudBank GitHub repo were not initially connected, so their histories
and contents may diverge.

During early development, work was saved locally. Some of that work later made
it into GitHub-backed repos, including CloudBank, but not all of it did.
Therefore:

- absence from GitHub is not evidence that early local material has no value
- presence in root archive, intake, staging, or recovered material is not
  evidence that the material is canonical
- recovered material must keep its source, status, and promotion path explicit

## Control-Plane Recovery Role

A key purpose of the root control plane is to recover, index, and classify early
local work so high-value logic, code, contracts, design decisions, and evidence
can be identified without damaging repo boundaries or canon authority.

The persistent recovery workflow lives in `docs/RECOVERY_INDEX_WORKFLOW_v1.md`.
Its manifest-driven tool is `tools/workspace_recovery_index.py`, and the latest
tracked report is `reports/analysis/workspace_recovery_index_latest.json`.

Recovery work should preserve these labels until a separate promotion decision
is made:

- `intake`
- `archive`
- `staged`
- `recovered`
- `draft`
- `superseded`
- `canonical`

High-value material should be extracted only into the repo or control surface
that owns it:

- CloudBank runtime or parser logic belongs in the canonical CloudBank nested
  repo, not in root control-plane docs or tools by default.
- Cross-repo contracts, routing rules, validation rules, and workspace
  governance belong in root control-plane metadata, docs, tools, or receipts.
- Canon, corpus, simulation, and archive material must follow their own
  authority boundaries before promotion.

## Extraction Expectations

When early local material is recovered or indexed, leave enough evidence for a
future agent or maintainer to understand the decision:

- source path and source status
- hash, size, timestamp, or other stable evidence when available
- why the material appears valuable
- target repo or control surface
- promotion status: pending, rejected, extracted, superseded, or canonical
- validation commands and receipt path when extraction occurs

Do not silently promote recovered material into canon. Recovery and indexing
make early work visible; promotion requires explicit authority, validation, and
an audit trail.
