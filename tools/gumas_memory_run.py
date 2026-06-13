#!/usr/bin/env python3
"""
gumas_memory_run.py — wire MECH-GOV-001 into the live GUMAS engine.

Closes the design->code->engine loop: runs the GUMASAdvancedEngine turn by
turn, harvests each turn's faction events (treaty breaches = betrayals,
conflicts = attacks, ratified treaties = alliances) into MECH-GOV-001 episodic
memory, computes each faction's memory-driven disposition toward the others,
and writes it back into the engine's `trust_scores` — which the base engine
already consults for treaty-breach and mediation evaluation. So memory enriches
the engine's existing trust signal rather than rewriting its internals.

Emergence principle: nothing here scripts outcomes. Factions simply *remember
and adapt*; whatever de-escalation or hardening emerges is the engine's, kept
coherent by being driven only by events that actually happened.

Usage:
    python3 tools/gumas_memory_run.py --turns 50 --seed 42      # A/B compare
    python3 tools/gumas_memory_run.py --turns 50 --seed 42 --out-json /tmp/x.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS"
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from mech_gov_001 import FactionDecisionModel  # noqa: E402

# Blend weight: how strongly memory disposition pulls the engine's trust score.
MEMORY_PULL = 0.30


def _harvest(mech: FactionDecisionModel, state, prev_breach: dict, seen_conflicts: set,
             seen_treaties: set) -> dict:
    """Record this turn's faction events into episodic memory. Returns counts."""
    counts = {"betrayals": 0, "attacks": 0, "alliances": 0}

    for tid, tr in state.treaties.items():
        total_breaches = sum(tr.breach_count.values()) if tr.breach_count else 0
        if total_breaches > prev_breach.get(tid, 0):
            violators = [f for f, c in (tr.breach_count or {}).items() if c > 0]
            for v in violators:
                for p in tr.parties:
                    if p != v:
                        mech.record_event(p, "broken_treaty", about=v, importance=7.0)
                        counts["betrayals"] += 1
            prev_breach[tid] = total_breaches
        elif getattr(tr, "is_active", False) and total_breaches == 0 and tid not in seen_treaties:
            seen_treaties.add(tid)
            prev_breach[tid] = 0
            for p in tr.parties:
                for o in tr.parties:
                    if p != o:
                        mech.record_event(p, "alliance", about=o, importance=5.0)
                        counts["alliances"] += 1

    for cid, cf in state.conflicts.items():
        if cid not in seen_conflicts:
            seen_conflicts.add(cid)
            for p in cf.parties:
                for o in cf.parties:
                    if p != o:
                        mech.record_event(p, "attack", about=o, importance=6.0)
                        counts["attacks"] += 1
    return counts


def _writeback(mech: FactionDecisionModel, state) -> int:
    """Blend each faction's memory disposition into its engine trust_scores.

    Realizes both canon rules in the engine's trust signal:
      - memory disposition (betrayal hardens, alliance softens) sets the base;
      - a militarily weak faction is nudged toward cooperation ("weakness
        increases the odds of negotiation") so it seeks deals rather than war.
    """
    updated = 0
    for fid, fac in state.factions.items():
        store = mech.stores.get(fid)
        if not store:
            continue
        mil = float(getattr(fac, "military_strength", 0.5))
        weak = mil < mech.weak_threshold
        subjects = {m.about for m in store.memories}
        for other in subjects:
            if other not in state.factions or other == fid:
                continue
            disp, _ = mech.disposition(fid, other)
            target = 0.5 + disp * 0.5  # disposition [-1,1] -> trust [0,1]
            if weak:
                # the weak negotiate: pull trust up toward cooperation
                target = target + (1.0 - target) * (mech.weak_threshold - mil)
            cur = fac.trust_scores.get(other, 0.5)
            fac.trust_scores[other] = round((1 - MEMORY_PULL) * cur + MEMORY_PULL * target, 4)
            updated += 1
    return updated


def run(seed: int, turns: int, memory_on: bool) -> dict:
    from engine_advanced import GUMASAdvancedEngine

    engine = GUMASAdvancedEngine(seed=seed)
    engine.init_scenario()
    mech = FactionDecisionModel(seed=seed) if memory_on else None
    prev_breach: dict = {}
    seen_conflicts: set = set()
    seen_treaties: set = set()
    traj: list[dict] = []
    harvest_total = {"betrayals": 0, "attacks": 0, "alliances": 0}

    for t in range(turns):
        res = engine.step()
        d = res.to_dict()
        state = engine.get_state()
        if memory_on:
            mech.tick(1)
            c = _harvest(mech, state, prev_breach, seen_conflicts, seen_treaties)
            for k in harvest_total:
                harvest_total[k] += c[k]
            _writeback(mech, state)
        traj.append({
            "turn": d["turn"],
            "stability": d["stability_index"],
            "risk": d["risk_index"],
            "conflicts": len(state.conflicts),
        })

    final = traj[-1]
    return {
        "memory_on": memory_on, "seed": seed, "turns": turns,
        "final_stability": final["stability"], "final_risk": final["risk"],
        "final_conflicts": final["conflicts"],
        "mean_risk": round(sum(p["risk"] for p in traj) / len(traj), 4),
        "peak_conflicts": max(p["conflicts"] for p in traj),
        "harvested": harvest_total,
        "trajectory": traj,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--turns", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-json", default=None)
    args = p.parse_args()

    print(f"GUMAS x MECH-GOV-001 — seed {args.seed}, {args.turns} turns (A/B)")
    baseline = run(args.seed, args.turns, memory_on=False)
    memory = run(args.seed, args.turns, memory_on=True)

    def line(label, r):
        print(f"  {label:8} | final stability {r['final_stability']:.3f} | "
              f"final risk {r['final_risk']:.3f} | mean risk {r['mean_risk']:.3f} | "
              f"final conflicts {r['final_conflicts']} | peak {r['peak_conflicts']}")
    print("\nResults:")
    line("baseline", baseline)
    line("memory", memory)
    h = memory["harvested"]
    print(f"\n  memory harvested: {h['betrayals']} betrayals, {h['attacks']} attacks, "
          f"{h['alliances']} alliances -> faction episodic memory")
    ds = memory["final_stability"] - baseline["final_stability"]
    dr = memory["final_risk"] - baseline["final_risk"]
    print(f"  delta (memory - baseline): stability {ds:+.3f}, risk {dr:+.3f}, "
          f"conflicts {memory['final_conflicts'] - baseline['final_conflicts']:+d}")

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(
            {"baseline": baseline, "memory": memory}, indent=2) + "\n")
        print(f"\n  wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
