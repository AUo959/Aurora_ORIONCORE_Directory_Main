# Session Claims

This directory stores machine-local live coordination claims for concurrent
Codex and Claude Code work.

Claim JSON files are intentionally ignored by Git. Use:

```bash
python3 tools/session_claim.py list
python3 tools/session_claim.py check --repo root --paths . --json
```

See `docs/SESSION_CLAIMS_WORKFLOW_v1.md` for the workflow contract.
