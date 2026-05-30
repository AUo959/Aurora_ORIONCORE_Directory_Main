# Script Governance Playbook

## Objective
Keep Aurora script surfaces safe and predictable by enforcing three controls:
- setup scripts default to diagnostics (not mutation)
- branch cleanup has one canonical implementation with compatibility wrappers
- risky command/string patterns are triaged in a focused batch

## Remediation Order
1. `setup_zero_byte` and high-risk hazards
2. canonical branch-cleanup entrypoint selection
3. duplicate-to-wrapper conversions
4. medium/low hazards in touched script families

## Canonical No-Op Setup Template
```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "[setup] Diagnostic mode (no changes applied)."

if [ -f requirements.txt ]; then
  echo "- requirements.txt present"
else
  echo "- requirements.txt missing"
fi

echo "Guidance: run project-approved install commands manually."
```

## Branch Cleanup Wrapper Template
```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[branch-cleanup] Delegating to branch_manager.py (default dry-run)."
exec python3 "$SCRIPT_DIR/branch_manager.py" --cleanup "$@"
```

## Hazard Fix Rules
- Brace-literal logs: `print("Value: {x}")` -> `print(f"Value: {x}")`
- Git typos: replace malformed subcommands with explicit valid git invocations
- `shell=True`: prefer argument arrays and `shell=False`
- Piping a download directly into a shell interpreter (forbidden): split into separate download, checksum-verify, then execute steps
- broad `rm -rf`: constrain targets to explicit repo-controlled paths

## Reporting Contract
When using this skill, return:
1. high-risk findings with file paths and line references
2. exact minimal edits applied
3. residual risks intentionally deferred
