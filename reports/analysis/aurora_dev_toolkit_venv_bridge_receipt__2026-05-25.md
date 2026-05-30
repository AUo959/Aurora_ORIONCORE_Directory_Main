# Aurora Dev Toolkit / CloudBank Venv Bridge Receipt - 2026-05-25

## Scope

This receipt covers the bounded bridge between the root Aurora Dev Toolkit and
the registered CloudBank repo-local Python environment.

Root control-plane changes:

- `tools/aurora_devkit.py`
- `catalog/dev_toolkit_manifest.json`
- `docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md`
- `tests/test_aurora_devkit.py`
- generated reports under `reports/analysis/`

CloudBank nested-repo changes:

- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/middleware/fastapi_security.py`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/tests/test_security_middleware.py`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/.env_status.json`

## Problem

Plain `python3` on this machine is Apple/Xcode Python 3.9.6. It is suitable for
root control-plane scripts after local user-site packages are present, but it is
not the CloudBank runtime interpreter. CloudBank already has a repo-local
`.venv` with FastAPI, httpx, slowapi, and pytest installed.

The previous validation failure came from running CloudBank tests with plain
`python3`, bypassing CloudBank's `.venv`.

## Changes

- Added `registered_repo_python_environments` to the devkit manifest for
  `aurora-cloudbank-symbolic-main`.
- Extended `tools/aurora_devkit.py` to run registered repo `.venv` checks:
  Python version, pip version, required imports, `pip check`, and
  `.env_status.json` freshness.
- Documented the CloudBank `.venv` validation path in
  `docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md`.
- Refreshed CloudBank `.env_status.json` to the actual local `.venv`.
- Updated CloudBank CSRF bearer handling to preserve the existing 403 contract
  under newer FastAPI/Starlette.

## Validation

- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/.venv/bin/python -m pytest -q tests/test_security_middleware.py`
  - result: `19 passed`
- `python3 -m pytest tests/test_aurora_devkit.py -q`
  - result: `5 passed`
- `python3 tools/aurora_devkit.py --persist-report`
  - result: `READY`, `Tools: 19/19 ok`, `Findings: none`
- `python3 tools/aurora_devkit.py --install-plan --persist-install-plan`
  - result: no missing or broken tools
- `git diff --check`
  - result: clean in root and CloudBank

## Boundary Notes

- Root devkit remains control-plane tooling.
- CloudBank remains a nested repo with its own `.venv`, validation commands,
  Git boundary, and publication decision.
- Plain root `python3` should not be used as evidence that CloudBank runtime
  dependencies are missing when CloudBank's `.venv` passes its own checks.
