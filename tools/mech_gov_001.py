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

# MECH-SOC-001 population grievance kinds: hardship/repression accumulate
# grievance; relief/autonomy ease it. Slow decay -> grievances persist.
GRIEVANCE_KINDS = {"repression", "hardship", "broken_promise", "war_loss"}
RELIEF_KINDS = {"relief", "autonomy", "prosperity", "reform"}
GRIEVANCE_HALF_LIFE_TURNS = 30.0

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
        if self.kind in HOSTILE_KINDS or self.kind in GRIEVANCE_KINDS:
            return -1.0
        if self.kind in FRIENDLY_KINDS or self.kind in RELIEF_KINDS:
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


class PopulationGrievanceModel:
    """MECH-SOC-001 — Population Grievance Memory (social dynamics).

    A polity's population remembers hardship, repression, and broken promises
    (grievance), and relief, autonomy, and prosperity (easing), with *slow*
    decay so the memory persists long after the immediate cause. Accumulated
    net grievance is the social-pressure term the canon frames as eroding
    stability (`P_stability = E + T - C`; DSI fracture under pressure) and
    raising insurgency onset. Makes instability path-dependent: a population
    that suffered carries it forward.
    """

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)
        self.turn = 0
        self.stores: dict[str, FactionMemoryStore] = {}

    def _store(self, faction: str) -> FactionMemoryStore:
        return self.stores.setdefault(faction, FactionMemoryStore())

    def record(self, faction: str, kind: str, importance: float = 5.0, content: str = "") -> None:
        self._store(faction).add(EpisodicMemory(
            kind=kind, about="__population__", content=content or kind,
            importance=float(importance), created_turn=self.turn,
            last_access_turn=self.turn, half_life=GRIEVANCE_HALF_LIFE_TURNS,
        ))

    def grievance_pressure(self, faction: str) -> float:
        """Net remembered grievance in [0, 1] (0 = content, 1 = seething)."""
        store = self.stores.get(faction)
        if not store:
            return 0.0
        net = 0.0
        for m in store.memories:
            m.decay_to(self.turn)
            if m.strength <= 0:
                continue
            # grievance pulls up, relief pulls down
            net += -m.valence * m.strength * (m.importance / 10.0)
        # squash to [0, 1]; only positive net grievance raises pressure
        return max(0.0, min(1.0, math.tanh(max(0.0, net) * 0.5)))

    def tick(self, turns: int = 1) -> None:
        self.turn += turns


class DiplomaticStabilityModel:
    """MECH-SOC-003 — Diplomatic Stability Index (the non-war progression gate).

    `DSI = (P + E + S) / (C + M)` — a faction absorbs crises *without war* when
    political unity (P), economic prosperity (E), and social cohesion (S)
    outweigh corruption (C) and militarization (M). Militarization is a
    destabilizing term: a galaxy built on fleets and operations is mechanically
    biased toward instability, which is exactly the seed-42 failure. Realizes
    `canon/L2/social_dynamics/non_war_progression_mechanics.md`.

    The derived **stability capacity** in [0,1] gates rebellion onset: high
    capacity lifts governance legitimacy (fewer insurgencies begin); low
    capacity (militarized/corrupt/poor) erodes it. This is the missing third
    faction disposition — prosperous-and-cohesive → de-escalate — alongside
    MECH-GOV-001's betrayed→wary and weak→negotiate.
    """

    DEN_FLOOR = 0.25  # keeps DSI finite when corruption+militarization ~ 0

    def dsi(self, political_unity: float, economic: float, cohesion: float,
            corruption: float, militarization: float) -> float:
        num = max(0.0, political_unity) + max(0.0, economic) + max(0.0, cohesion)
        den = max(0.0, corruption) + max(0.0, militarization) + self.DEN_FLOOR
        return num / den

    def stability_capacity(self, dsi_value: float) -> float:
        """Squash DSI to [0,1]: ~0.3 (militarized/poor) .. ~0.75 (cohesive)."""
        return max(0.0, min(1.0, math.tanh(dsi_value * 0.5)))

    def capacity_for(self, *, economic: float, cohesion: float, political_unity: float,
                     militarization: float, institutional_control: float,
                     grievance: float = 0.0) -> float:
        """Convenience: corruption derived from weak institutional control;
        cohesion eroded by remembered grievance (MECH-SOC-001 tie-in)."""
        corruption = max(0.0, 1.0 - institutional_control)
        cohesion_eff = max(0.0, cohesion - grievance * 0.5)
        return self.stability_capacity(
            self.dsi(political_unity, economic, cohesion_eff, corruption, militarization))


class ComplacencyModel:
    """MECH-SOC-006 — Complacency Cycle (the seeds of the next conflict).

    A galaxy whose every stabilizer ratchets up monotonically collapses to a
    permanent-peace fixed point — as degenerate as permanent war. Real polities
    don't stay healthy forever: long peace breeds **corruption and complacency**,
    which the canon names as a *destabilizer* ("if C or M are too high … it
    increases instability" — non_war_progression). So a faction unchallenged for
    many turns accrues complacency that raises its effective corruption in the
    DSI, lowering its stability capacity until unrest becomes possible again.
    Conflict (serious war) **purges** it — upheaval renews the order. The result
    is a *limit cycle*: peace → complacency → conflict → renewal → peace.
    """

    # Calibrated for a *limit cycle*, not a ratchet: conflict waxes and wanes.
    # Stronger values pump constant war; weaker ones let peace flatline. These
    # produce conflict waves with stability oscillating ~0.48-0.59.
    BUILD_RATE = 0.012        # complacency accrued per peaceful turn
    PEAK = 0.55               # ceiling on accrued complacency
    GRACE_TURNS = 8           # a fresh, post-conflict order is briefly clean

    def __init__(self) -> None:
        self.peace_streak: dict[str, int] = {}

    LEGIT_EROSION = 0.04      # how hard complacency drags governance legitimacy

    def update(self, faction: str, at_serious_war: bool) -> float:
        """Advance the peace clock (or reset it on serious war); return the
        current complacency level in [0, PEAK]."""
        if at_serious_war:
            self.peace_streak[faction] = 0
            return 0.0
        t = self.peace_streak.get(faction, 0) + 1
        self.peace_streak[faction] = t
        return max(0.0, min(self.PEAK, (t - self.GRACE_TURNS) * self.BUILD_RATE))

    STRESS_PRESSURE = 0.015   # corrupt mismanagement worsens living conditions

    def legitimacy_drag(self, complacency: float) -> float:
        """Corruption erodes public legitimacy — the downward pressure that
        long peace needs so unrest can recur."""
        return complacency * self.LEGIT_EROSION

    INSURGENT_FUEL = 0.012    # corruption breeds strong resentment in rebels

    def stress_pressure(self, complacency: float) -> float:
        """A complacent, corrupt order mismanages — housing/conditions worsen,
        which (with eroded legitimacy) re-ignites unrest (onset). Must out-push
        peacetime recovery, or the cycle never turns."""
        return complacency * self.STRESS_PRESSURE

    def insurgent_fuel(self, complacency: float) -> float:
        """A corrupt order breeds *strong* resentment: rebellions against a
        complacent regime gain popular support and grievance, so they mature
        into civil wars rather than fizzling. This is the maturation lever the
        onset levers alone can't supply — without it, post-conflict societies
        spawn only weak unrest that never escalates."""
        return complacency * self.INSURGENT_FUEL


class PostWarRecoveryModel:
    """MECH-SOC-005 — Post-War Reconstruction.

    The stability index is `0.35·population + 0.30·legitimacy + 0.25·trust +
    0.10·peace`. The seed-42 lessons found population stability floored at ~0.09
    (§1.5) and legitimacy the weakest contributor (§1.6) — because the engine
    only ever *drags these down* under war and never restores them. With
    conflict now resolvable (MECH-SOC-002), a faction at peace must be able to
    *heal*: population stability and governance legitimacy rebuild over time,
    and the demographic stress drivers (housing, unemployment, food) ease toward
    healthy baselines. Recovery is gated on peace — an active insurgency halts
    reconstruction — so it rewards ending wars rather than papering over them.
    """

    POP_TARGET = 0.72
    POP_RECOVERY_RATE = 0.06
    LEGIT_TARGET = 0.65
    LEGIT_RECOVERY_RATE = 0.04
    HOUSING_TARGET = 0.25
    UNEMPLOY_TARGET = 0.12
    FOOD_TARGET = 0.80
    DRIVER_RECOVERY_RATE = 0.05

    @staticmethod
    def toward(current: float, target: float, rate: float) -> float:
        """Lift `current` a fraction `rate` toward a higher target (population,
        legitimacy, food security). Recovery never degrades a healthy value."""
        if current < target:
            return current + (target - current) * rate
        return current

    @staticmethod
    def ease_down(current: float, target: float, rate: float) -> float:
        """Relax `current` a fraction `rate` down toward a lower target
        (housing pressure, unemployment)."""
        if current > target:
            return current - (current - target) * rate
        return current


class WarWearinessModel:
    """MECH-SOC-002 — Insurgency Resolution / War-Weariness (the exit edge).

    The seed-42 civil war is a one-way door: `InsurgencyPhase.RESOLVED` is never
    assigned and the engine's only exit (the SUPPRESSED gate, strength < 0.05)
    is unreachable because insurgent strength pins at 1.0. This makes that exit
    *reachable* without fighting the engine: a population at war wearies, and
    its support for the insurgency erodes the longer the war grinds on. Falling
    popular support is the engine's own primary driver of insurgent strength —
    so eroding it lets the engine's dynamics drain strength → territory shrinks
    → SUPPRESSED, the natural resolution the attractor never had.

    Grounded in lessons §1.2 ("resource-exhaustion mechanic that forces
    insurgency phases to decay") and the social canon's de-escalation paths.
    """

    GRACE_TURNS = 4            # early war has fresh fervor; weariness builds after
    SUPPORT_EROSION = 0.012    # per war-turn beyond grace, scaled by weariness
    STRENGTH_ATTRITION = 0.010  # direct attrition once deeply weary
    TERRITORY_ATTRITION = 0.015  # weary insurgents cede ground -> reach SUPPRESSED

    def __init__(self) -> None:
        self.turns_in_war: dict[str, int] = {}

    def weary(self, insurgency_id: str, active: bool) -> float:
        """Advance/reset the war clock; return a weariness factor in [0,1]."""
        if not active:
            self.turns_in_war.pop(insurgency_id, None)
            return 0.0
        t = self.turns_in_war.get(insurgency_id, 0) + 1
        self.turns_in_war[insurgency_id] = t
        return max(0.0, min(1.0, (t - self.GRACE_TURNS) / 30.0))

    def erosion(self, weariness: float) -> tuple[float, float, float]:
        """Return (support_erosion, strength_attrition, territory_attrition).

        Territory attrition matters for resolution: an insurgency only reaches
        the engine's SUPPRESSED gate at territory < 0.01, so a weary movement
        must cede ground, not just lose strength. This clears the lingering
        minor-insurgency swarm that chronically drags population stability."""
        return (self.SUPPORT_EROSION * weariness,
                self.STRENGTH_ATTRITION * max(0.0, weariness - 0.5) * 2.0,
                self.TERRITORY_ATTRITION * weariness)


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
