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

# MECH-REB-004 reuses the engine's *own* de-escalation formula
# (SIM_ENGINE_OUTPUTS/formulas.py, "PR Section 5.2 Formula 1") so insurgency
# resolution and inter-faction conflict resolution share one rule. When the
# engine package isn't importable (e.g. standalone unit tests of this module),
# fall back to a faithful copy kept in sync with it.
try:  # pragma: no cover - exercised via the integration harness
    from formulas import calc_deescalation_probability as _DEESC
    from formulas import calc_treaty_breach_score as _BREACH
    from formulas import is_treaty_breach as _IS_BREACH
except Exception:  # noqa: BLE001 - any import failure -> local copies
    def _DEESC(  # type: ignore[misc]
        war_cost_a: float, war_cost_b: float, stalemate_index: float,
        internal_pressure_a: float, internal_pressure_b: float,
        mediation_available: bool, *, cost_weight: float = 0.3,
        stalemate_weight: float = 0.25, pressure_weight: float = 0.25,
        mediation_bonus: float = 0.2,
    ) -> float:
        """Faithful copy of `SIM_ENGINE_OUTPUTS/formulas.py`
        `calc_deescalation_probability` (PR Section 5.2 Formula 1). Kept in sync
        with the engine; used only when that module is off the import path."""
        avg_war_cost = (war_cost_a + war_cost_b) / 2.0
        avg_pressure = (internal_pressure_a + internal_pressure_b) / 2.0
        p = (cost_weight * avg_war_cost + stalemate_weight * stalemate_index
             + pressure_weight * avg_pressure
             + mediation_bonus * (1.0 if mediation_available else 0.0))
        if stalemate_index >= 1.0:
            p = max(p, 0.5)
        if war_cost_a > 0.9 and war_cost_b > 0.9:
            p = max(p, 0.6)
        return max(0.0, min(1.0, p))

    def _BREACH(  # type: ignore[misc]
        action_severity: float, is_direct_action: bool, treaty_ambiguity: float,
        faction_trust: float, *, ambiguity_tolerance: float = 0.2,
        trust_discount_multiplier: float = 0.1,
    ) -> float:
        """Faithful copy of `calc_treaty_breach_score` (PR §5.2 Formula 3)."""
        violation_weight = 1.0 if is_direct_action else 0.5
        return (action_severity * violation_weight
                - treaty_ambiguity * ambiguity_tolerance
                - faction_trust * (trust_discount_multiplier * faction_trust))

    def _IS_BREACH(breach_score: float, violation_threshold: float = 0.6) -> bool:
        """Faithful copy of `is_treaty_breach`."""
        return breach_score > violation_threshold

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


class InsurgencyResolutionModel:
    """MECH-REB-004 — Insurgency Resolution / Mediated Settlement.

    The inter-faction conflict layer has always carried a full de-escalation
    ladder ending in RESOLUTION (`calc_deescalation_probability`, ported here from
    the engine's `formulas.py`), but the insurgency layer only ever had military
    suppression — a civil war could be *crushed* (SUPPRESSED) but never *ended*.
    Suppression leaves the grievance intact, so the same handful of insurgencies
    reopened indefinitely and war was the only off-ramp (Observatory roundtable,
    2026-06-14). `InsurgencyPhase.RESOLVED` was declared in canon yet never
    assigned.

    This grafts the proven model onto insurgencies: a grinding, costly,
    stalemated insurgency whose host population has pressure to end it can reach a
    negotiated **settlement**. Settlement RETIRES the movement (the realization of
    RESOLVED, since the engine has no terminal/removal path of its own) and SPENDS
    the grievance that drove it — easing demographic stress and restoring a little
    legitimacy (a *peaceful* renewal path, distinct from the war-purge). Because
    the cause is addressed, the conflict cast can rotate instead of reopening.

    `mediation_available` (set by a diplomatic overture, MECH-DIP-002) adds the
    formula's mediation bonus — diplomacy becomes a faster, grievance-cheaper
    off-ramp than grinding to mutual exhaustion.

    Deliberately *self-limiting*: de-escalation probability only rises as war
    cost, stalemate, and domestic pressure accumulate, so fresh or popular
    insurgencies don't settle — which keeps conflict real and avoids re-creating
    the permanent-peace fixed point. Calibrated, not tuned to a target.
    """

    GRACE_TURNS = 6            # a fresh insurgency can't be settled instantly
    SETTLE_STEP = 0.34         # settlement progress per successful roll (~3 rungs)
    STALEMATE_TURNS = 30.0     # turns_active at which stalemate_index saturates
    OPENNESS_WEIGHT = 0.10     # leader diplomacy_openness sways the effective roll
    LEGIT_RESTORE = 0.04       # a settled peace restores some legitimacy (D6)
    STRESS_RELIEF = 0.06       # settlement eases the host's demographic stress
    GRIEVANCE_RELIEF = 0.20    # ... and the lingering grievance drivers

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)
        self.progress: dict[str, float] = {}   # insurgency_id -> settlement [0,1]

    def deescalation_p(
        self, *, host_war_pressure: float, insurgent_strength: float,
        repression_level: float, turns_active: int, host_grievance: float,
        popular_support: float, diplomacy_openness: float,
        mediation_available: bool,
    ) -> float:
        """De-escalation probability for one insurgency, via the engine's own
        `calc_deescalation_probability`, with the insurgency's fields mapped onto
        the inter-faction conflict inputs."""
        war_cost_state = min(1.0, max(0.0, host_war_pressure))
        # the insurgents' own cost: how ground-down they are
        war_cost_rebels = min(1.0, max(repression_level, 1.0 - insurgent_strength))
        stalemate = min(1.0, turns_active / self.STALEMATE_TURNS)
        internal_state = min(1.0, max(0.0, host_grievance))      # population wants it ended
        internal_rebels = min(1.0, max(0.0, 1.0 - popular_support))  # rebels losing the public
        p = _DEESC(
            war_cost_state, war_cost_rebels, stalemate,
            internal_state, internal_rebels, mediation_available,
        )
        p += (diplomacy_openness - 0.5) * self.OPENNESS_WEIGHT
        return max(0.0, min(1.0, p))

    def advance(self, insurgency_id: str, p: float) -> bool:
        """Roll de-escalation; accumulate settlement progress; return True the
        turn a full settlement is reached."""
        if self._rng.random() < p:
            prog = self.progress.get(insurgency_id, 0.0) + self.SETTLE_STEP
            self.progress[insurgency_id] = prog
            if prog >= 1.0:
                return True
        return False

    def forget(self, insurgency_id: str) -> None:
        self.progress.pop(insurgency_id, None)


class MediationModel:
    """MECH-DIP-002 — Mediated Settlement.

    Diplomacy as a *real* off-ramp, not just exhaustion. When a host faction
    fighting an insurgency has a credible third-party mediator — a peaceful
    neighbour it **mutually trusts** — that broker opens a negotiated path. It
    sets `mediation_available` on the host's insurgencies, which feeds the
    de-escalation formula's mediation bonus (MECH-REB-004), so the civil war can
    end **faster and at lower accumulated cost/grievance** than grinding to
    mutual exhaustion. An isolated or widely distrusted regime has no such
    shortcut and must grind on — which is exactly the canon dynamic (a
    well-connected polity settles; a pariah bleeds).

    Emergent, not scripted: the broker is found in the live trust network that
    MECH-GOV-001 / MECH-DIP-001 already maintain (`faction.trust_scores`). A
    faction fighting its *own* serious war cannot broker peace and is excluded.
    """

    # Mutual trust required to be a *credible* broker. Calibrated so brokering is
    # meaningful but not universal: at 0.58 (notably above the ~0.5 average) about
    # half of settlements are mediated and half grind to exhaustion, and the share
    # varies by seed with the trust network — the well-connected get a faster,
    # cheaper peace; isolated regimes bleed. Lower makes brokers ubiquitous
    # (diplomacy stops discriminating); higher makes them vanish.
    TRUST_FLOOR = 0.58   # mutual trust required to be a credible broker

    def find_mediator(self, host, trust_by_faction, busy):
        """Return the best credible mediator id for `host`, or None.

        `trust_by_faction`: {fid: {other_fid: trust}}; `busy`: set of faction ids
        too embroiled in their own serious war to broker. A mediator must be
        *mutually* trusted with the host at or above TRUST_FLOOR."""
        host_trust = trust_by_faction.get(host, {}) or {}
        best, best_mutual = None, self.TRUST_FLOOR
        for m, m_trust in trust_by_faction.items():
            if m == host or m in busy:
                continue
            mutual = min(float(host_trust.get(m, 0.0)),
                         float((m_trust or {}).get(host, 0.0)))
            if mutual >= best_mutual:
                best, best_mutual = m, mutual
        return best


class TreatyEnforcementModel:
    """MECH-DIP-003 — Treaty Enforcement & Consequence.

    A settled peace (MECH-REB-004/DIP-002) is not a free, permanent win — it
    **binds**, and it can **break**. Each settlement registers a peace *accord*
    (one per host) against the floor it established. Every turn the accord is
    tested for breach with the engine's own `calc_treaty_breach_score` /
    `is_treaty_breach`: as the host's conditions **backslide** above that floor
    (the complacency cycle rebuilding stress during peace), the accord is
    strained, and a heavy backslide breaks it. Repeated breaches compound: an
    oath-breaker's later accords break under lighter strain.

    When an accord breaks: grievance **resurges** (renewed conflict — the betrayed
    peace) and, if a broker guaranteed it, the trust between host and mediator
    **collapses**, burning the broker's credibility so future peace is harder to
    broker. This gives the diplomacy off-ramp real *stakes* — a brokered peace is
    faster and cheaper (DIP-002) but not automatically more lasting; a settlement
    among rivals can still fail, and when a *mediated* one fails it costs the
    broker. Couples the complacency cycle to the slow breakdown of peace.
    """

    GRACE = 4                      # an accord is safe just after signing
    AMBIGUITY = 0.15               # how much benefit-of-the-doubt an accord gets
    VIOLATION_THRESHOLD = 0.6      # engine default
    BACKSLIDE_WEIGHT = 5.0         # renewed stress -> strain (calibrated to the
                                   # measured backslide range: breach at ~0.13+,
                                   # the heaviest-backsliding ~20% of accord-turns)
    REPEAT_BREACH_WEIGHT = 0.08    # an oath-breaker's later accords break easier
    TRUST_BURN = 0.12              # broken brokered peace burns host<->mediator trust

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)
        self.accords: dict[str, dict] = {}    # host_id -> accord
        self.breaches: dict[str, int] = {}    # host_id -> cumulative breaches

    def register(self, host: str, mediator, base_grievance: float) -> None:
        """Record a peace accord for `host` (replacing any prior one)."""
        self.accords[host] = {"mediator": mediator,
                              "base": float(base_grievance), "age": 0}

    def check(self, host: str, current_grievance: float, trust_with_mediator: float):
        """Advance and test the host's accord. Returns the broken accord dict
        (with 'mediator') on breach, else None. A host that lets conditions
        collapse back into unrest has directly failed the accord (direct action)."""
        a = self.accords.get(host)
        if a is None:
            return None
        a["age"] += 1
        if a["age"] < self.GRACE:
            return None
        backslide = max(0.0, float(current_grievance) - a["base"])
        severity = min(1.0, backslide * self.BACKSLIDE_WEIGHT
                       + self.breaches.get(host, 0) * self.REPEAT_BREACH_WEIGHT)
        score = _BREACH(severity, True, self.AMBIGUITY, float(trust_with_mediator))
        if _IS_BREACH(score, self.VIOLATION_THRESHOLD):
            self.breaches[host] = self.breaches.get(host, 0) + 1
            del self.accords[host]
            return a
        return None

    def forget(self, host: str) -> None:
        self.accords.pop(host, None)


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
