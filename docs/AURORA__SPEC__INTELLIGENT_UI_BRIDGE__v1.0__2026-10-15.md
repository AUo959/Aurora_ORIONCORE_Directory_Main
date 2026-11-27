# Aurora Intelligent UI Bridge — v1

Owner: ORIONCORE root control plane
Posture: read-only snapshot projection; advisory only
Status: pilot / review candidate
Date: 2026-10-15

## Purpose

Translate an existing, saved Aurora Mission Control report into a versioned
allowlisted JSON snapshot for ChatGPT Intelligent UI or another authorized
read-only visual consumer. Reuse Mission Control; do not build another
dashboard runtime, score system, canon producer, or model router.

## Source and contract

- Producer: tools/aurora_mission_control.py
- Input: reports/analysis/aurora_mission_control_latest.json
- Source contract: catalog/schemas/aurora_mission_control_report.schema.json
- Adapter: tools/aurora_intelligent_ui_bridge.py
- UI contract: catalog/schemas/aurora_intelligent_ui_snapshot.schema.json
- Tests: tests/test_aurora_intelligent_ui_bridge.py

## Usage

Default: python3 tools/aurora_intelligent_ui_bridge.py

Explicit export: python3 tools/aurora_intelligent_ui_bridge.py --output /tmp/aurora-intelligent-ui.json

Test: python3 -m pytest -q tests/test_aurora_intelligent_ui_bridge.py

The default emits only JSON to stdout. It reads, but never refreshes or modifies,
the saved Mission Control source. --output writes a derived presentation artifact
only when explicitly requested, and never changes the source or canon.

The latest filename does not imply freshness. The source generated_at is
compared with the current UTC time and labeled stale after 48 hours by default.
Always display this date in any native ChatGPT UI. The generated_at of the
bridge payload is the conversion time, NOT a Mission Control recomputation.

## Authority boundary

- Require version 1 and read_only/advisory_only source metadata.
- Reject malformed/future timestamps, unknown status and inconsistent totals.
- Project allowlisted information only; omit suggested commands, absolute paths,
  raw source reports, and private state.
- Recovery-review/restricted inbox evidence is withheld, with generic routing
  to the governed source workspace instead.
- Expose evidence refs as opaque identifiers, never executable instructions.
- Preserve canon_write=false, runtime_execution=false, nested_repo_mutation=false.
- The SHA-256 value fingerprints bytes, not source authenticity or factual truth.
- Do not use this adapter to invoke GUMAS, ACE, CanonRec, or other live runtimes.
- Do not label snapshots as current operations without independent freshness check.

## Follow-on

An authenticated, read-only snapshot retrieval tool could later refresh data
from an authorized owner surface; native ChatGPT views should then render
the same stable contract. Simulation and canon adapters remain independently
governed work items, and the GPT-6 model-routing tickets are not modified.
