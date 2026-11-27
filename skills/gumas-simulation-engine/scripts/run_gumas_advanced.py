#!/usr/bin/env python3
"""Run the integrated GUMAS simulation engine for a workspace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run integrated GUMAS simulation")
    parser.add_argument("--workspace", default=".", help="Workspace root path")
    parser.add_argument("--turns", type=int, default=20, help="Number of turns to run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output JSON path (default: workspace/GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/advanced_skill_output.json)",
    )
    parser.add_argument(
        "--replay-artifacts", action="store_true",
        help="Export reproducible state and ledger files to an explicit path outside the workspace",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if args.replay_artifacts and (not args.output or Path(args.output).resolve().is_relative_to(workspace)):
        parser.error("--replay-artifacts requires --output outside the workspace")
    engine_dir = workspace / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS"
    if not engine_dir.is_dir():
        raise FileNotFoundError(f"Engine directory not found: {engine_dir}")

    sys.path.insert(0, str(engine_dir))

    engine_mode = "advanced"
    engine_class_name = "unknown"

    try:
        from engine import GUMASEngine  # default points to advanced in this repository
    except Exception as exc:
        raise RuntimeError(f"Failed to import engine entrypoint from {engine_dir}: {exc}") from exc

    engine = GUMASEngine(seed=args.seed)
    state = engine.init_scenario()
    results = engine.run(max(0, args.turns))

    engine_class_name = engine.__class__.__name__
    if engine_class_name.lower().find("advanced") == -1:
        engine_mode = "legacy"

    output_path = (
        Path(args.output).resolve()
        if args.output
        else engine_dir / "advanced_skill_output.json"
    )

    if hasattr(engine, "export_advanced_state"):
        options = {"replay_artifacts": True} if args.replay_artifacts else {}
        engine.export_advanced_state(
            str(output_path), include_base_history=False, include_advanced_history=False, **options,
        )
    elif args.replay_artifacts:
        parser.error("--replay-artifacts requires the advanced engine")
    else:
        engine.export_state(str(output_path), include_history=False)

    latest_summary = None
    latest_turn = state.turn
    if results:
        latest = results[-1]
        latest_turn = getattr(latest, "turn", latest_turn)
        latest_summary = getattr(latest, "summary", None)
        if callable(latest_summary):
            latest_summary = latest_summary()

    payload = {
        "workspace": str(workspace),
        "engine_dir": str(engine_dir),
        "engine_mode": engine_mode,
        "engine_class": engine_class_name,
        "scenario_id": getattr(state, "scenario_id", "unknown"),
        "turns_requested": max(0, args.turns),
        "turns_completed": latest_turn,
        "last_summary": latest_summary,
        "output_path": str(output_path),
        "output_exists": output_path.exists(),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
