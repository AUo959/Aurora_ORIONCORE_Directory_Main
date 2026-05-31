#!/usr/bin/env python3
"""Aurora workspace health check — unified diagnostic runner.

Runs tests, workspace verification, catalog lint, schema validation,
and repo sync audit. Produces a JSON summary report.

Usage:
    python tools/workspace_health_check.py            # full health check
    python tools/workspace_health_check.py --lint-only # catalog lint only
    python tools/workspace_health_check.py --json      # JSON output
"""

import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
REPORTS = ROOT / "reports" / "analysis"


def _run(cmd, cwd=None):
    """Run a command, return (returncode, stdout, stderr)."""
    r = subprocess.run(
        cmd, capture_output=True, text=True,
        cwd=cwd or ROOT, timeout=120,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


# ── Lint checks ──────────────────────────────────────────────────────────

def lint_yaml():
    """Validate all YAML files in catalog/."""
    import yaml  # noqa: delayed import
    errors = []
    for f in sorted(CATALOG.glob("*.yaml")) + sorted(CATALOG.glob("*.yml")):
        try:
            yaml.safe_load(f.read_text())
        except Exception as e:
            errors.append({"file": str(f.relative_to(ROOT)), "error": str(e)})
    return errors


def lint_json():
    """Validate all JSON files in catalog/ and subdirs."""
    errors = []
    for pattern in ("*.json", "schemas/*.json", "contracts/*.json"):
        for f in sorted(CATALOG.glob(pattern)):
            try:
                json.loads(f.read_text())
            except Exception as e:
                errors.append({"file": str(f.relative_to(ROOT)), "error": str(e)})
    return errors


def check_schemas():
    """Validate catalog JSON files against their schemas where available."""
    try:
        import jsonschema  # noqa: delayed import
    except ImportError:
        return [{"note": "jsonschema not installed — skipping schema validation"}]

    schema_dir = CATALOG / "schemas"
    if not schema_dir.is_dir():
        return []

    errors = []
    for schema_path in sorted(schema_dir.glob("*.json")):
        try:
            schema = json.loads(schema_path.read_text())
        except Exception:
            continue
        # Attempt to find a matching data file by name convention
        stem = schema_path.stem.replace("_schema", "")
        candidates = list(CATALOG.glob(f"{stem}*.json"))
        for data_path in candidates:
            if data_path.parent.name == "schemas":
                continue
            try:
                data = json.loads(data_path.read_text())
                jsonschema.validate(data, schema)
            except jsonschema.ValidationError as e:
                errors.append({
                    "file": str(data_path.relative_to(ROOT)),
                    "schema": str(schema_path.relative_to(ROOT)),
                    "error": e.message[:200],
                })
            except Exception:
                pass
    return errors


# ── Test runner ──────────────────────────────────────────────────────────

def run_tests():
    """Run pytest and return summary."""
    rc, out, err = _run([sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"])
    return {
        "returncode": rc,
        "summary": out.splitlines()[-1] if out else err.splitlines()[-1] if err else "no output",
    }


# ── Workspace verify ────────────────────────────────────────────────────

def run_verify():
    """Run workspace_verify.py and return summary."""
    rc, out, _ = _run([sys.executable, "tools/workspace_verify.py"])
    report_path = REPORTS / "workspace_verify_latest.json"
    report = None
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text())
        except Exception:
            pass
    return {
        "returncode": rc,
        "report_exists": report_path.exists(),
        "finding_count": len(report.get("findings", [])) if report else None,
    }


# ── Sync audit ───────────────────────────────────────────────────────────

def run_sync_audit():
    """Run gitwiz sync audit for root."""
    script = ROOT / "skills" / "gitwiz-github-manager" / "scripts" / "gitwiz_sync_audit.py"
    if not script.exists():
        return {"error": "sync audit script not found"}
    rc, out, _ = _run([sys.executable, str(script), "--repo", "root"])
    return {"returncode": rc, "output_lines": len(out.splitlines()) if out else 0}


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Aurora workspace health check")
    parser.add_argument("--lint-only", action="store_true", help="Run catalog lint only")
    parser.add_argument("--json", action="store_true", dest="json_out", help="JSON output")
    args = parser.parse_args()

    start = time.time()
    results = {}

    # Always run lint
    results["yaml_errors"] = lint_yaml()
    results["json_errors"] = lint_json()

    if not args.lint_only:
        results["schema_errors"] = check_schemas()
        results["tests"] = run_tests()
        results["verify"] = run_verify()
        results["sync_audit"] = run_sync_audit()

    results["elapsed_seconds"] = round(time.time() - start, 2)

    # Determine overall status
    problems = (
        len(results.get("yaml_errors", []))
        + len(results.get("json_errors", []))
        + len(results.get("schema_errors", []))
        + (1 if results.get("tests", {}).get("returncode", 0) != 0 else 0)
        + (1 if results.get("verify", {}).get("returncode", 0) != 0 else 0)
    )
    results["status"] = "HEALTHY" if problems == 0 else f"DEGRADED ({problems} issue(s))"

    if args.json_out:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'═' * 50}")
        print(f"  Aurora Workspace Health: {results['status']}")
        print(f"{'═' * 50}")

        if results["yaml_errors"]:
            print(f"\n  YAML errors: {len(results['yaml_errors'])}")
            for e in results["yaml_errors"]:
                print(f"    - {e['file']}: {e['error'][:80]}")
        else:
            print("\n  YAML catalog:  OK")

        if results["json_errors"]:
            print(f"  JSON errors: {len(results['json_errors'])}")
            for e in results["json_errors"]:
                print(f"    - {e['file']}: {e['error'][:80]}")
        else:
            print("  JSON catalog:  OK")

        if not args.lint_only:
            schema_errs = results.get("schema_errors", [])
            if schema_errs and any("error" in e for e in schema_errs):
                print(f"  Schema errors: {len([e for e in schema_errs if 'error' in e])}")
            else:
                print("  Schema check:  OK")

            t = results.get("tests", {})
            symbol = "OK" if t.get("returncode") == 0 else "FAIL"
            print(f"  Tests:         {symbol}  ({t.get('summary', '?')})")

            v = results.get("verify", {})
            symbol = "OK" if v.get("returncode") == 0 else "FAIL"
            findings = f"  ({v.get('finding_count', '?')} findings)" if v.get("finding_count") else ""
            print(f"  Verify:        {symbol}{findings}")

            sa = results.get("sync_audit", {})
            symbol = "OK" if sa.get("returncode") == 0 else "WARN"
            print(f"  Sync audit:    {symbol}")

        print(f"\n  Elapsed: {results['elapsed_seconds']}s")
        print(f"{'═' * 50}\n")

    # Write JSON report
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / "workspace_health_latest.json"
    report_path.write_text(json.dumps(results, indent=2) + "\n")

    sys.exit(0 if problems == 0 else 1)


if __name__ == "__main__":
    main()
