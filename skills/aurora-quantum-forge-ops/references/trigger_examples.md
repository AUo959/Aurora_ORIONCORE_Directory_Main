# Trigger Examples

## Should Trigger This Skill

- "Run Quantum Forge validation and give me a machine-readable ops report."
- "Execute 20 turns of GUMAS Forge and summarize event signals."
- "Generate and verify ORION capsules from the current Forge state."
- "Use Quantum Forge ops to produce Markdown + JSON leadership artifacts."
- "Scan this QUANTUM_FORGE manifest and vector injections alongside an engine run."

## Should Not Trigger This Skill

- Governance verdict requests and readiness gating.
- Canonization or narrative continuity reconciliation requests.
- Generic repo script hardening and hook refactoring requests.
- THREADCORE-only or ZIPWIZ-only governance requests.

Route those to:

- `aurora-governance-orchestrator`
- `aurora-canon-reconciler`
- `threadcore-governor`
- `zipwiz-governor`
- `aurora-script-governor`
