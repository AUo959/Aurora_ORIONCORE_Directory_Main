#!/usr/bin/env python3
"""
mech_gov_001.py — the Faction Decision Retrieval Model (MECH-GOV-001).

Realizes the L2 governance mechanic that was designed at the project's genesis
(the "Crisis & Compromise" RPG), formalized in the recovered L2 Mechanic
Registry, and never coded: factions choose actions by combining their *current
state* with *retrieved memory* of past betrayals, alliances, and negotiations,
plus the canon rules —

    "betrayal history raises the odds of future betrayal"
    "weakness increases the odds of negotiation"
        — canon/L2/mechanics/03_galactic_union_mechanics_and_models.md

Memory substrate ported (cleanly) from the recovered 2025 `memory_system.py`
(importance-weighted strength, exponential decay by half-life, reinforcement
on recall, recency+importance+relevance retrieval). One deliberate change: the
recovered code used wall-clock `time.time()`, which makes runs irreproducible.
This implementation uses a **logical turn clock**, so a seed + event log
yields a deterministic decision trace — required for simulation fidelity.

Companion mechanic MECH-DIP-001 (Diplomatic Trust Decay,
`T_new = T_old - lambda*B + delta*A`) is included as the trust-update rule the
decision model reads.

Usage (library):
    m = FactionDecisionModel(seed=808)
    m.record_event("Galactic Union", "betrayal", about="The Black Hand", importance=8)
    decision = m.decide(faction, toward="The Black Hand", action_space=[...])

CLI demo:
    python3 tools/mech_gov_001.py demo
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass, field
from typing import Optional

# Memory half-life is expressed in *turns* (logical clock), not seconds.
DEFAULT_HALF_LIFE_TURNS = 12.0
RECENCY_DECAY_PER_TURN = 0.08

# Canonical event kinds and their valence toward the subject faction.
HOSTILE_KINDS = {"betrayal", "attack", "broken_treaty", "sabotage"}
FRIENDLY_KINDS = {"alliance", "negotiation", "aid", "honored_treaty"}

DEFAULT_ACTIONS = ["ally", "negotiate", "verify", "hold", "escalate", "betray"]


@dataclass
class EpisodicMemory:
    """A single remembered event one faction holds about another."""
    kind: str
    about: str
    content: str
    importance: float          # 1..10
    created_turn: int
    half_life: float = DEFAULT_HALF_LIFE_TURNS
    strength: float = 1.0
    last_access_turn: int = 0

    def decay_to(self, turn: int) -> None:
        elapsed = max(0, turn - self.last_access_turn)
        if elapsed and self.strength > 0:
            lam = math.log(2) / self.half_life
            self.strength *= math.exp(-lam * elapsed)
            if self.strength < 1e-4:
                self.strength = 0.0
        self.last_access_turn = turn

    def reinforce(self, amount: float = 0.2) -> None:
        if self.strength < 1.0:
            self.strength += (1.0 - self.strength) * amount

    @property
    def valence(self) -> float:
        if self.kind in HOSTILE_KINDS:
            return -1.0
        if self.kind in FRIENDLY_KINDS:
            return 1.0
        return 0.0


class FactionMemoryStore:
    """Episodic memory for one faction (the recovered MemoryStore, logical-clock)."""

    def __init__(self) -> None:
        self.memories: list[EpisodicMemory] = []

    def add(self, mem: EpisodicMemory) -> None:
        self.memories.append(mem)

    def retrieve(self, about: str, turn: int, top_k: int = 8) -> list[EpisodicMemory]:
        scored: list[tuple[float, EpisodicMemory]] = []
        for m in self.memories:
            m.decay_to(turn)
            if m.strength <= 0 or m.about != about:
                continue
            recency = math.exp(-RECENCY_DECAY_PER_TURN * max(0, turn - m.created_turn))
            importance = m.importance / 10.0
            score = (recency + importance) * m.strength
            scored.append((score, m))
        scored.sort(key=lambda s: s[0], reverse=True)
        top = [m for _, m in scored[:top_k]]
        for m in top:
            m.reinforce(0.1)
            m.last_access_turn = turn
        return top


@dataclass
class Decision:
    faction: str
    toward: str
    action: str
    rationale: str
    scores: dict[str, float]
    retrieved: list[str] = field(default_factory=list)


class FactionDecisionModel:
    """MECH-GOV-001 + MECH-DIP-001.

    Holds per-faction episodic memory and trust scores, and selects actions by
    combining current state with retrieved history.
    """

    # MECH-DIP-001 trust decay coefficients (T_new = T_old - lambda*B + delta*A)
    BETRAYAL_LAMBDA = 0.25
    ALLIANCE_DELTA = 0.12

    def __init__(self, seed: int = 0, weak_military_threshold: float = 0.4) -> None:
        self.rng = random.Random(seed)
        self.turn = 0
        self.stores: dict[str, FactionMemoryStore] = {}
        self.trust: dict[tuple[str, str], float] = {}
        self.weak_threshold = weak_military_threshold

    def _store(self, faction: str) -> FactionMemoryStore:
        return self.stores.setdefault(faction, FactionMemoryStore())

    # --- event intake -------------------------------------------------------
    def record_event(self, faction: str, kind: str, about: str,
                     importance: float = 5.0, content: str = "") -> None:
        """The acting faction's memory of an event involving `about`."""
        self._store(faction).add(EpisodicMemory(
            kind=kind, about=about, content=content or f"{kind} involving {about}",
            importance=float(importance), created_turn=self.turn,
            last_access_turn=self.turn,
        ))
        # MECH-DIP-001: update the trust the faction holds toward `about`.
        key = (faction, about)
        t = self.trust.get(key, 0.5)
        if kind in HOSTILE_KINDS:
            t -= self.BETRAYAL_LAMBDA * (importance / 10.0)
        elif kind in FRIENDLY_KINDS:
            t += self.ALLIANCE_DELTA * (importance / 10.0)
        self.trust[key] = max(0.0, min(1.0, t))

    def trust_of(self, faction: str, toward: str) -> float:
        return self.trust.get((faction, toward), 0.5)

    # --- the decision -------------------------------------------------------
    def disposition(self, faction: str, toward: str) -> tuple[float, list[EpisodicMemory]]:
        """Return a hostility disposition in [-1, 1] (negative = hostile) and the
        memories that produced it. Combines current trust with retrieved history."""
        retrieved = self._store(faction).retrieve(toward, self.turn)
        memory_pull = sum(m.valence * m.strength * (m.importance / 10.0) for m in retrieved)
        # Normalize memory pull softly; trust contributes the current-state half.
        trust = self.trust_of(faction, toward)
        disposition = math.tanh(memory_pull) * 0.6 + (trust - 0.5) * 0.8
        return max(-1.0, min(1.0, disposition)), retrieved

    def decide(self, faction: dict, toward: str,
               action_space: Optional[list[str]] = None) -> Decision:
        """Select an action toward `toward`. `faction` is a dict-like with
        keys: name, military_strength (0..1). Memory + weakness + trust drive it."""
        actions = action_space or DEFAULT_ACTIONS
        name = faction["name"]
        mil = float(faction.get("military_strength", 0.5))
        disp, retrieved = self.disposition(name, toward)
        weak = mil < self.weak_threshold

        # Canon rules made concrete:
        #  - betrayal history (disp << 0) raises hostile actions (betray/escalate)
        #  - weakness raises negotiation/verification (de-escalation)
        scores: dict[str, float] = {}
        for a in actions:
            s = 0.0
            if a in ("betray", "escalate"):
                s += max(0.0, -disp) * 1.4           # hostile memory pushes here
                s += max(0.0, mil - 0.5) * 0.6        # strength emboldens
                if weak:
                    s -= 0.6                           # the weak rarely start fights
            elif a in ("negotiate", "verify"):
                s += 0.4                               # baseline diplomatic option
                if weak:
                    s += 0.9                           # weakness -> negotiation (canon)
                s += max(0.0, -disp) * 0.5            # distrust -> verify before acting
            elif a == "ally":
                s += max(0.0, disp) * 1.3             # friendly memory enables alliance
                s -= max(0.0, -disp) * 1.0            # betrayal memory blocks it
            elif a == "hold":
                s += 0.3 + (1.0 - abs(disp)) * 0.4    # ambiguity favors holding
            s += self.rng.random() * 0.05            # tiny deterministic tie-breaker
            scores[a] = round(s, 4)

        action = max(scores, key=scores.get)
        why = []
        if retrieved:
            hostile = sum(1 for m in retrieved if m.valence < 0)
            friendly = sum(1 for m in retrieved if m.valence > 0)
            why.append(f"recalled {len(retrieved)} memories ({hostile} hostile, {friendly} friendly)")
        why.append(f"disposition {disp:+.2f}, trust {self.trust_of(name, toward):.2f}")
        if weak:
            why.append("militarily weak -> favors negotiation")
        return Decision(faction=name, toward=toward, action=action,
                        rationale="; ".join(why), scores=scores,
                        retrieved=[f"{m.kind}:{m.about}@t{m.created_turn}(s{m.strength:.2f})" for m in retrieved])

    def tick(self, turns: int = 1) -> None:
        """Advance the logical clock; memory decay is lazy (on retrieval)."""
        self.turn += turns


# --------------------------------------------------------------------------- demo
def _demo() -> int:
    """Show MECH-GOV-001 changing a faction's behavior as memory accrues —
    the de-escalation the seed-42 runaway-conflict run lacked."""
    m = FactionDecisionModel(seed=808)
    union = {"name": "Galactic Union", "military_strength": 0.7}
    weak = {"name": "Vel-Surak Compact", "military_strength": 0.3}

    print("== MECH-GOV-001 demo ==")
    print("\nT0 — no history:")
    print("  Union -> Black Hand:", m.decide(union, "The Black Hand").action,
          "|", m.decide(union, "The Black Hand").rationale)

    # The Black Hand betrays the Union twice; memory should harden it.
    for _ in range(2):
        m.tick(2)
        m.record_event("Galactic Union", "betrayal", about="The Black Hand", importance=8)
    d = m.decide(union, "The Black Hand")
    print("\nAfter two betrayals (memory-driven):")
    print("  Union -> Black Hand:", d.action, "|", d.rationale)

    # A weak faction under the same hostility negotiates instead (canon rule).
    m.record_event("Vel-Surak Compact", "betrayal", about="The Black Hand", importance=8)
    dw = m.decide(weak, "The Black Hand")
    print("\nWeak faction, same betrayal:")
    print("  Vel-Surak -> Black Hand:", dw.action, "|", dw.rationale)

    # Alliances build the other way.
    for _ in range(3):
        m.tick(1)
        m.record_event("Galactic Union", "alliance", about="Armada Nova Systems", importance=6)
    da = m.decide(union, "Armada Nova Systems")
    print("\nAfter three alliance acts:")
    print("  Union -> Armada Nova:", da.action, "|", da.rationale)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", nargs="?", choices=["demo"], default="demo")
    p.parse_args()
    return _demo()


if __name__ == "__main__":
    raise SystemExit(main())
