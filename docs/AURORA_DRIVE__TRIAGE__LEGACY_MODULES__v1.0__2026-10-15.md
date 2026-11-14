# Aurora Drive legacy-module triage (2026-10-15)

This is a read-only recovery assessment. The underlying Drive source data and hashes remain private. Nothing below promotes canon or changes runtime behavior.

| Historical module | Current GitHub evidence | Recommendation |
| --- | --- | --- |
| TaggingEngineV2_Oppy.py | CloudBank modules/reflective_autonomy/threadcore_tagging.py and tests/test_threadcore_tagging.py implement the same weighted-category classification pattern. | Preserve existing tested classifier; do not reimport historical source. |
| reflective_autonomy_loop.py | CloudBank modules/reflective_autonomy/reflective_autonomy_loop.py and tests/test_reflective_autonomy_runtime.py implement audited linting and correction planning. | Preserve non-mutating approach; do not introduce historical automatic anchor restoration. |
| working_group_engine.py | CloudBank modules/crew_agents/api.py supports ad hoc task collaboration and src/collaboration/collaborative_research_framework.js provides another collaboration surface. No persistent membership/history lifecycle established by the inspected code. | Design-only recovery candidate, subject to fuller overlap review. |

The older group code silently resets storage on read errors, uses timestamp-derived identifiers, lacks a verified authorization gate, and audits some mutations only after they occur. Do not port it into production. A safer successor would first define read-only group and event schemas with identity validation and explicit authority boundaries.

Comparison method: retrieved historical code was statically parsed and syntax-compiled without execution. Selected current CloudBank sources and tests were inspected using authenticated GitHub access. Search misses do not prove absence. The historical sources were not live-tested.

References: docs/RECOVERY_INDEX_WORKFLOW_v1.md; docs/CONTROL_PLANE_PROVENANCE.md; reports/analysis/simulation_discovery_index__2026-06-13.md.

Status: pending_review / not_promoted. No CanonRec or deterministic L1 changes.