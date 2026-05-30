#!/usr/bin/env python3
"""Run Quantum Forge operations and emit Markdown + JSON reports."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


REQUIRED_FORGE_FILES = ("validate_v3.py", "engine_v3_patch.py", "charforge.py")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run GUMAS Quantum Forge validation, engine execution, and capsule operations."
    )
    parser.add_argument("--forge-root", required=True, help="Path to FORGE__GUMAS_v3.0 root")
    parser.add_argument("--out-dir", help="Output directory (default: <forge-root>/workflow_output/quantum_forge_ops)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic engine seed (default: 42)")
    parser.add_argument("--turns", type=int, default=10, help="Number of engine turns to execute (default: 10)")
    parser.add_argument(
        "--run-validation",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run validate_v3.py before engine execution (default: true)",
    )
    parser.add_argument(
        "--generate-capsules",
        action="store_true",
        help="Generate ORION capsule bundles after engine run",
    )
    parser.add_argument("--capsule-out", help="Capsule output directory (default: <out-dir>/capsules)")
    parser.add_argument(
        "--verify-capsules",
        action="store_true",
        help="Verify generated capsules using verify_capsule",
    )
    parser.add_argument("--qforge-manifest", help="Optional QUANTUM_FORGE_Manifest.json path")
    parser.add_argument("--vector-injections", help="Optional Symbolic_Vector_Injections.json path")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if high-severity risks are detected")
    parser.add_argument(
        "--emit-run-manifest",
        action="store_true",
        help="Emit run_manifest.json with artifact locations and execution metadata",
    )
    return parser.parse_args(argv)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def resolve_path(path_value: str) -> Path:
    return Path(path_value).expanduser().resolve()


def validate_forge_root(forge_root: Path) -> None:
    if not forge_root.exists() or not forge_root.is_dir():
        raise FileNotFoundError(f"forge root not found: {forge_root}")

    missing = [name for name in REQUIRED_FORGE_FILES if not (forge_root / name).exists()]
    if missing:
        raise FileNotFoundError(
            "forge root missing required files: " + ", ".join(missing)
        )


def parse_validation_summary(output: str) -> Tuple[Optional[int], Optional[int]]:
    matches = re.findall(r"(\d+)\s*/\s*(\d+)\s*tests\s*passed", output, flags=re.IGNORECASE)
    if not matches:
        return None, None
    passed, total = matches[-1]
    return int(passed), int(total)


def run_validation(forge_root: Path) -> Dict[str, Any]:
    cmd = [sys.executable, str(forge_root / "validate_v3.py")]
    proc = subprocess.run(cmd, cwd=str(forge_root), capture_output=True, text=True, check=False)
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    passed, total = parse_validation_summary(combined)

    return {
        "ran": True,
        "command": cmd,
        "exit_code": proc.returncode,
        "tests_passed": passed,
        "tests_total": total,
        "passed": proc.returncode == 0 and passed is not None and total is not None and passed == total,
        "summary_line_detected": passed is not None,
        "stdout_tail": "\n".join((proc.stdout or "").splitlines()[-20:]),
        "stderr_tail": "\n".join((proc.stderr or "").splitlines()[-20:]),
    }


def import_forge_modules(forge_root: Path):
    path_str = str(forge_root)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

    engine_mod = importlib.import_module("engine_v3_patch")
    charforge_mod = importlib.import_module("charforge")
    return engine_mod, charforge_mod


def run_engine(engine_mod, seed: int, turns: int) -> Dict[str, Any]:
    engine_cls = getattr(engine_mod, "GUMASEngineV3")
    engine = engine_cls(seed=seed)
    engine.init_scenario()

    per_turn: List[Dict[str, Any]] = []
    event_breakdown: Dict[str, int] = {}
    total_events = 0

    for _ in range(turns):
        _, v3_result = engine.full_step()
        turn_events = list(getattr(v3_result, "v3_events", []))
        turn_event_count = len(turn_events)
        total_events += turn_event_count

        for event in turn_events:
            etype = str(event.get("type", "UNKNOWN"))
            event_breakdown[etype] = event_breakdown.get(etype, 0) + 1

        per_turn.append(
            {
                "turn": int(getattr(v3_result, "turn", 0)),
                "event_count": turn_event_count,
                "new_insurgencies": int(getattr(v3_result, "new_insurgencies", 0)),
                "civil_wars_started": int(getattr(v3_result, "civil_wars_started", 0)),
                "tech_breakthroughs": int(getattr(v3_result, "tech_breakthroughs", 0)),
                "migrations": int(getattr(v3_result, "migrations", 0)),
                "fragmentation_events": int(getattr(v3_result, "fragmentation_events", 0)),
                "negotiations_concluded": int(getattr(v3_result, "negotiations_concluded", 0)),
                "intelligence_ops": int(getattr(v3_result, "intelligence_ops", 0)),
            }
        )

    state = getattr(engine, "_state", None)
    factions = getattr(state, "factions", {}) if state is not None else {}
    leaders = getattr(state, "leaders", {}) if state is not None else {}

    return {
        "engine": engine,
        "state": state,
        "engine_metrics": {
            "seed": seed,
            "turns_requested": turns,
            "turns_executed": len(per_turn),
            "total_v3_events": total_events,
            "faction_count": len(factions),
            "leader_count": len(leaders),
            "per_turn": per_turn,
        },
        "event_breakdown": dict(sorted(event_breakdown.items(), key=lambda item: item[0])),
    }


def export_v3_state(engine_obj: Any, out_path: Path) -> None:
    engine_obj.export_v3_state(str(out_path))


def generate_and_verify_capsules(
    charforge_mod,
    state: Any,
    capsule_out: Path,
    verify_capsules: bool,
) -> Dict[str, Any]:
    capsule_out.mkdir(parents=True, exist_ok=True)
    generated = charforge_mod.generate_all_capsules(state, capsule_out, overwrite=True)

    bundle_paths = {leader_id: str(path) for leader_id, path in sorted(generated.items(), key=lambda x: x[0])}
    metrics: Dict[str, Any] = {
        "generated": True,
        "capsule_out": str(capsule_out),
        "generated_count": len(bundle_paths),
        "bundle_paths": bundle_paths,
    }

    verification_report = None
    if verify_capsules:
        failures: List[Dict[str, str]] = []
        verified_count = 0

        for leader_id, bundle in sorted(generated.items(), key=lambda x: x[0]):
            ok = bool(charforge_mod.verify_capsule(bundle))
            if ok:
                verified_count += 1
            else:
                failures.append({"leader_id": leader_id, "bundle_path": str(bundle)})

        verification_report = {
            "total": len(generated),
            "verified": verified_count,
            "failed": len(failures),
            "failures": failures,
            "pass_rate": (verified_count / len(generated)) if generated else 0.0,
        }

        metrics.update(
            {
                "verification_requested": True,
                "verified_count": verified_count,
                "failed_count": len(failures),
                "verification_pass_rate": verification_report["pass_rate"],
            }
        )

    else:
        metrics["verification_requested"] = False

    return {"capsule_metrics": metrics, "verification_report": verification_report}


def verify_existing_capsules(charforge_mod, capsule_out: Path) -> Dict[str, Any]:
    bundles = sorted(
        p for p in capsule_out.iterdir() if p.is_dir() and (p / "capsule").is_dir()
    )
    failures: List[Dict[str, str]] = []
    verified_count = 0

    for bundle in bundles:
        ok = bool(charforge_mod.verify_capsule(bundle))
        if ok:
            verified_count += 1
        else:
            failures.append({"bundle_path": str(bundle)})

    report = {
        "total": len(bundles),
        "verified": verified_count,
        "failed": len(failures),
        "failures": failures,
        "pass_rate": (verified_count / len(bundles)) if bundles else 0.0,
    }
    return report


def load_optional_json(path_value: Optional[str]) -> Tuple[Optional[Path], Optional[Any], Optional[str]]:
    if not path_value:
        return None, None, None

    path = resolve_path(path_value)
    if not path.exists():
        return path, None, f"optional file not found: {path}"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return path, data, None
    except Exception as exc:
        return path, None, f"failed to parse JSON {path}: {exc}"


def build_payload_context(
    qforge_manifest_path: Optional[str],
    vector_injections_path: Optional[str],
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    payload_context: Dict[str, Any] = {
        "qforge_manifest": None,
        "vector_injections": None,
    }
    risks: List[Dict[str, str]] = []

    manifest_path, manifest_data, manifest_error = load_optional_json(qforge_manifest_path)
    if manifest_path is not None:
        if manifest_error:
            risks.append(
                {
                    "code": "payload_manifest_unreadable",
                    "severity": "medium",
                    "message": manifest_error,
                }
            )
        elif isinstance(manifest_data, dict):
            payload_context["qforge_manifest"] = {
                "path": str(manifest_path),
                "module_id": manifest_data.get("module_id"),
                "engine": manifest_data.get("engine"),
                "status": manifest_data.get("status"),
                "ethics_protocol": manifest_data.get("ethics_protocol"),
                "binding_layer": manifest_data.get("binding_layer"),
                "capabilities_count": len(manifest_data.get("capabilities", []))
                if isinstance(manifest_data.get("capabilities"), list)
                else 0,
            }
        else:
            risks.append(
                {
                    "code": "payload_manifest_wrong_type",
                    "severity": "medium",
                    "message": f"expected object in manifest JSON: {manifest_path}",
                }
            )

    vectors_path, vectors_data, vectors_error = load_optional_json(vector_injections_path)
    if vectors_path is not None:
        if vectors_error:
            risks.append(
                {
                    "code": "vector_injections_unreadable",
                    "severity": "medium",
                    "message": vectors_error,
                }
            )
        elif isinstance(vectors_data, list):
            tag_counts: Dict[str, int] = {}
            ids: List[str] = []
            for item in vectors_data:
                if isinstance(item, dict):
                    tag = str(item.get("tag", ""))
                    vec_id = str(item.get("id", ""))
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    if vec_id:
                        ids.append(vec_id)

            payload_context["vector_injections"] = {
                "path": str(vectors_path),
                "count": len(vectors_data),
                "ids": sorted(ids),
                "tag_distribution": dict(sorted(tag_counts.items(), key=lambda item: item[0])),
            }
        else:
            risks.append(
                {
                    "code": "vector_injections_wrong_type",
                    "severity": "medium",
                    "message": f"expected list in vector injections JSON: {vectors_path}",
                }
            )

    return payload_context, risks


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def format_risk_lines(risks: List[Dict[str, str]]) -> str:
    if not risks:
        return "- None"
    lines = []
    for risk in risks:
        lines.append(f"- [{risk['severity'].upper()}] {risk['code']}: {risk['message']}")
    return "\n".join(lines)


def write_markdown(
    path: Path,
    report_json: Dict[str, Any],
) -> None:
    summary = report_json["run_summary"]
    validation = report_json["validation_status"]
    engine_metrics = report_json["engine_metrics"]
    capsule_metrics = report_json["capsule_metrics"]
    payload_context = report_json["payload_context"]
    artifacts = report_json["artifacts"]
    risks = report_json["risk_flags"]

    lines = [
        "# Quantum Forge Operations Report",
        "",
        "## Execution Snapshot",
        f"- Status: `{summary['status']}`",
        f"- Forge root: `{report_json['analysis_scope']['forge_root']}`",
        f"- Seed: `{engine_metrics['seed']}`",
        f"- Turns executed: `{engine_metrics['turns_executed']}`",
        f"- Total v3 events: `{engine_metrics['total_v3_events']}`",
        f"- Generated at (UTC): `{summary['generated_at_utc']}`",
        "",
        "## Validation Status",
        f"- Ran: `{validation['ran']}`",
        f"- Exit code: `{validation['exit_code']}`",
        f"- Tests passed/total: `{validation.get('tests_passed')}`/`{validation.get('tests_total')}`",
        f"- Full pass: `{validation['passed']}`",
        "",
        "## Engine Signals",
        f"- Factions: `{engine_metrics['faction_count']}`",
        f"- Leaders: `{engine_metrics['leader_count']}`",
        "- Event breakdown:",
    ]

    event_breakdown = report_json.get("event_breakdown", {})
    if event_breakdown:
        for event_name, count in sorted(event_breakdown.items(), key=lambda item: item[0]):
            lines.append(f"  - `{event_name}`: `{count}`")
    else:
        lines.append("  - None")

    lines.extend(
        [
            "",
            "## Capsule Operations",
            f"- Generated: `{capsule_metrics.get('generated', False)}`",
            f"- Capsule output: `{capsule_metrics.get('capsule_out')}`",
            f"- Bundle count: `{capsule_metrics.get('generated_count', 0)}`",
            f"- Verification requested: `{capsule_metrics.get('verification_requested', False)}`",
            f"- Verified count: `{capsule_metrics.get('verified_count', 0)}`",
            f"- Failed count: `{capsule_metrics.get('failed_count', 0)}`",
            "",
            "## Payload Context",
        ]
    )

    manifest = payload_context.get("qforge_manifest")
    vectors = payload_context.get("vector_injections")
    if manifest:
        lines.extend(
            [
                f"- Manifest module_id: `{manifest.get('module_id')}`",
                f"- Manifest engine: `{manifest.get('engine')}`",
                f"- Manifest status: `{manifest.get('status')}`",
                f"- Manifest ethics protocol: `{manifest.get('ethics_protocol')}`",
            ]
        )
    else:
        lines.append("- Manifest context: not provided")

    if vectors:
        lines.extend(
            [
                f"- Vector injection count: `{vectors.get('count')}`",
                f"- Vector IDs: `{', '.join(vectors.get('ids', []))}`",
            ]
        )
    else:
        lines.append("- Vector injection context: not provided")

    lines.extend(
        [
            "",
            "## Risk Flags",
            format_risk_lines(risks),
            "",
            "## Artifact Index",
            f"- JSON report: `{artifacts['json_report']}`",
            f"- Markdown report: `{artifacts['markdown_report']}`",
            f"- V3 state snapshot: `{artifacts['v3_state_snapshot']}`",
        ]
    )

    if artifacts.get("capsule_verification"):
        lines.append(f"- Capsule verification: `{artifacts['capsule_verification']}`")
    if artifacts.get("run_manifest"):
        lines.append(f"- Run manifest: `{artifacts['run_manifest']}`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    if args.turns < 1:
        print("[qforge-ops] --turns must be >= 1", file=sys.stderr)
        return 2

    try:
        forge_root = resolve_path(args.forge_root)
        validate_forge_root(forge_root)
    except Exception as exc:
        print(f"[qforge-ops] ERROR: {exc}", file=sys.stderr)
        return 2

    out_dir = resolve_path(args.out_dir) if args.out_dir else forge_root / "workflow_output" / "quantum_forge_ops"
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "quantum_forge_run_report.md"
    json_path = out_dir / "quantum_forge_run_report.json"
    state_path = out_dir / "v3_state_snapshot.json"
    capsule_verification_path = out_dir / "capsule_verification.json"
    run_manifest_path = out_dir / "run_manifest.json"

    risks: List[Dict[str, str]] = []

    validation_status = {
        "ran": False,
        "exit_code": None,
        "tests_passed": None,
        "tests_total": None,
        "passed": None,
    }

    if args.run_validation:
        validation_status = run_validation(forge_root)
        if not validation_status.get("summary_line_detected"):
            risks.append(
                {
                    "code": "validation_summary_missing",
                    "severity": "medium",
                    "message": "Could not parse tests passed summary from validate_v3.py output.",
                }
            )
        if not validation_status.get("passed", False):
            risks.append(
                {
                    "code": "validation_failed",
                    "severity": "high",
                    "message": "validate_v3.py did not report a full passing validation run.",
                }
            )

    try:
        engine_mod, charforge_mod = import_forge_modules(forge_root)
        engine_run = run_engine(engine_mod, seed=args.seed, turns=args.turns)
    except Exception as exc:
        print(f"[qforge-ops] ERROR: engine execution failed: {exc}", file=sys.stderr)
        return 1

    engine = engine_run["engine"]
    state = engine_run["state"]
    engine_metrics = engine_run["engine_metrics"]
    event_breakdown = engine_run["event_breakdown"]

    try:
        export_v3_state(engine, state_path)
    except Exception as exc:
        risks.append(
            {
                "code": "v3_state_export_failed",
                "severity": "high",
                "message": f"Failed to export v3 state snapshot: {exc}",
            }
        )

    capsule_metrics: Dict[str, Any] = {
        "generated": False,
        "capsule_out": None,
        "generated_count": 0,
        "verification_requested": bool(args.verify_capsules),
        "verified_count": 0,
        "failed_count": 0,
    }

    if args.generate_capsules:
        capsule_out = resolve_path(args.capsule_out) if args.capsule_out else (out_dir / "capsules")
        try:
            capsule_result = generate_and_verify_capsules(
                charforge_mod=charforge_mod,
                state=state,
                capsule_out=capsule_out,
                verify_capsules=args.verify_capsules,
            )
            capsule_metrics = capsule_result["capsule_metrics"]
            verification_report = capsule_result["verification_report"]

            if verification_report is not None:
                write_json(capsule_verification_path, verification_report)
                if verification_report["failed"] > 0:
                    risks.append(
                        {
                            "code": "capsule_verification_failed",
                            "severity": "high",
                            "message": f"{verification_report['failed']} generated capsules failed verification.",
                        }
                    )
            elif args.verify_capsules:
                risks.append(
                    {
                        "code": "capsule_verification_missing",
                        "severity": "medium",
                        "message": "Verification was requested but no verification report was produced.",
                    }
                )

            if int(capsule_metrics.get("generated_count", 0)) == 0:
                risks.append(
                    {
                        "code": "capsules_not_generated",
                        "severity": "high",
                        "message": "Capsule generation requested but zero bundles were generated.",
                    }
                )

        except Exception as exc:
            risks.append(
                {
                    "code": "capsule_generation_error",
                    "severity": "high",
                    "message": f"Capsule generation failed: {exc}",
                }
            )

    elif args.verify_capsules:
        capsule_out = resolve_path(args.capsule_out) if args.capsule_out else (out_dir / "capsules")
        if not capsule_out.exists() or not capsule_out.is_dir():
            risks.append(
                {
                    "code": "capsule_dir_missing",
                    "severity": "medium",
                    "message": f"Capsule directory not found for verification: {capsule_out}",
                }
            )
        else:
            verification_report = verify_existing_capsules(charforge_mod, capsule_out)
            write_json(capsule_verification_path, verification_report)
            capsule_metrics.update(
                {
                    "generated": False,
                    "capsule_out": str(capsule_out),
                    "generated_count": int(verification_report["total"]),
                    "verification_requested": True,
                    "verified_count": int(verification_report["verified"]),
                    "failed_count": int(verification_report["failed"]),
                    "verification_pass_rate": float(verification_report["pass_rate"]),
                }
            )
            if verification_report["failed"] > 0:
                risks.append(
                    {
                        "code": "capsule_verification_failed",
                        "severity": "high",
                        "message": f"{verification_report['failed']} existing capsules failed verification.",
                    }
                )

    payload_context, payload_risks = build_payload_context(
        qforge_manifest_path=args.qforge_manifest,
        vector_injections_path=args.vector_injections,
    )
    risks.extend(payload_risks)

    status = "ok" if not any(risk["severity"] == "high" for risk in risks) else "attention_required"

    artifacts = {
        "json_report": str(json_path),
        "markdown_report": str(md_path),
        "v3_state_snapshot": str(state_path),
        "capsule_verification": str(capsule_verification_path)
        if args.generate_capsules and args.verify_capsules and capsule_verification_path.exists()
        else None,
        "run_manifest": str(run_manifest_path) if args.emit_run_manifest else None,
    }

    report_json: Dict[str, Any] = {
        "run_summary": {
            "status": status,
            "generated_at_utc": utc_now(),
            "strict_mode": bool(args.strict),
        },
        "validation_status": validation_status,
        "engine_metrics": engine_metrics,
        "event_breakdown": event_breakdown,
        "capsule_metrics": capsule_metrics,
        "payload_context": payload_context,
        "risk_flags": risks,
        "artifacts": artifacts,
        "analysis_scope": {
            "forge_root": str(forge_root),
            "out_dir": str(out_dir),
            "qforge_manifest": str(resolve_path(args.qforge_manifest)) if args.qforge_manifest else None,
            "vector_injections": str(resolve_path(args.vector_injections)) if args.vector_injections else None,
            "seed": args.seed,
            "turns": args.turns,
            "run_validation": bool(args.run_validation),
            "generate_capsules": bool(args.generate_capsules),
            "verify_capsules": bool(args.verify_capsules),
        },
    }

    write_json(json_path, report_json)
    write_markdown(md_path, report_json)

    if args.emit_run_manifest:
        run_manifest = {
            "generated_at_utc": utc_now(),
            "tool": "build_qforge_ops_report.py",
            "forge_root": str(forge_root),
            "outputs": {k: v for k, v in artifacts.items() if v},
            "status": status,
        }
        write_json(run_manifest_path, run_manifest)

    print(f"[qforge-ops] forge root: {forge_root}")
    print(f"[qforge-ops] output dir: {out_dir}")
    print(f"[qforge-ops] turns executed: {engine_metrics['turns_executed']}")
    print(f"[qforge-ops] total v3 events: {engine_metrics['total_v3_events']}")
    print(f"[qforge-ops] risk flags: {len(risks)}")
    print(f"[qforge-ops] markdown: {md_path}")
    print(f"[qforge-ops] json: {json_path}")

    if args.strict and any(risk["severity"] == "high" for risk in risks):
        print("[qforge-ops] strict mode failed due to high-severity risks.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
