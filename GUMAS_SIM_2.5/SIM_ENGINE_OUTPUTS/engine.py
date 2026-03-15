#!/usr/bin/env python3
"""
GUMAS Engine Entrypoint (Default: Advanced)
===========================================

Default export now points to the synthesized advanced engine.
Legacy engine remains available via LegacyGUMASEngine.
"""

from __future__ import annotations

from engine_advanced import AdvancedTickResult, GUMASAdvancedEngine
from engine_base import GUMASEngine as LegacyGUMASEngine

# Backward-compatible symbol: importing GUMASEngine now gets advanced behavior.
GUMASEngine = GUMASAdvancedEngine

__all__ = [
    "GUMASEngine",
    "GUMASAdvancedEngine",
    "LegacyGUMASEngine",
    "AdvancedTickResult",
]


def main() -> None:
    engine = GUMASAdvancedEngine(seed=42)
    state = engine.init_scenario()
    print(
        f"GUMAS advanced entrypoint | scenario={state.scenario_id} "
        f"factions={len(state.factions)}"
    )
    for res in engine.run(5):
        print(res.summary)


if __name__ == "__main__":
    main()
