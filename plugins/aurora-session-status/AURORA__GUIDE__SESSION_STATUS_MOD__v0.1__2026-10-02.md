# Aurora session status mod v0.1

A read-only status band for Claude Code CLI and Desktop, using the host API
demonstrated in Anthropic's official token-weather mod. Requires Claude Code
2.1.287 or later, Python 3.9+, Git, and this ORIONCORE checkout. No npm dependency.

From the ORIONCORE repository root, try it for one session:

```bash
claude --plugin-dir ./plugins/aurora-session-status
```

To disable it, end that session and launch Claude without the plugin-dir argument.
This change does not enable plugins in account settings or replace lifecycle hooks.

The mod samples at session start and after each main-agent turn. It composes with
the existing AbovePrompt output and yields during surveys. It shows the active
task's declared target (or a labeled root default), the **root workspace branch**,
local active/stale claim counts, CloudBank pin/observed-checkout agreement,
the recorded next action, and counts of waiting items in the target repo.
Waiting counts are queue records, not a determination that all waits require approval.

Sources: catalog/session_state.json, catalog/repo_registry.yaml, and the existing
session_claim.list_claims reader. Only local Git reads are performed. The Python
adapter emits JSON to stdout and has no persist option; Python bytecode writes
are disabled by the mod. Missing or unsupported inputs produce explicit warnings.
CloudBank must have its own checkout: a directory in the root Git tree is insufficient.
Registry paths escaping the workspace are not inspected. Older-than-24h session
records get an advisory warning, independent of the repository's commit-count gates.

This is a turn-boundary snapshot, not a live file watcher, a readiness certificate,
a claim acquisition mechanism, or an execution approval. Claims are machine-local:
a cloud checkout cannot observe claims on the owner's Mac. No command-intent
interpretation, permission interception, runtime invocation or public submission occurs.
Mods themselves run with host privileges; review the source before loading it.

Validation:

```bash
python3 -B -m pytest -q tests/test_aurora_session_status.py
node plugins/aurora-session-status/tests/AURORA__TEST__MOD_HOST__v0.1__2026-10-02.mjs
python3 -B tools/AURORA__TOOL__SESSION_STATUS__v0.1__2026-10-02.py
```

Actual CLI/Desktop visual acceptance remains necessary on the owner's installation:
confirm the panel appears, a second AbovePrompt mod stays visible, a narrow window
clips safely, a missing nested checkout warns, a failed reader replaces stale status,
and relaunching without the plugin removes it. Host mocks verify contracts only.

Official API references:
- https://github.com/anthropics/claude-code-playground/tree/main/claude-code/mods/token-weather
- https://github.com/anthropics/claude-code-playground/tree/main/claude-code/mods/blast-radius

Later changes: model migration belongs in a separate CloudBank PR; Claude packaging
of command grammar must reuse its existing gateway and incorporate CloudBank #1622's
identity/provenance reconciliation. Directory publication is a separate release action.
