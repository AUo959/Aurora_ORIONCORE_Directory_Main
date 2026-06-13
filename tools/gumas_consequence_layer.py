#!/usr/bin/env python3
"""
gumas_consequence_layer.py — make the inert instability signals consequential.

The seed-42 lessons flagged several mechanics that fire every turn but connect
to nothing — "diagnostic signals with no mechanical consequence":

  §2.1 INTELLIGENCE_COMPROMISE — most consistent signal in the run; never
       resolved, no counter-intelligence response, no consequence.
  §2.4 MASS_CONSCRIPTION — surged late; faction capabilities unchanged.
  §2.2 civil-war onset — no dampener; embattled factions destabilize further.
  §2.3 STATE_FRAGMENTATION — fires at 3/turn; produces no split or weakening.

This gives each a natural downstream effect, derived from faction/insurgency
state (no per-event parsing), so the dominant-but-inert signals become real:

  - **Counter-intel response** — a faction under intelligence pressure invests
    in counter-intelligence, raising `counter_intel_strength` and making
    compromise self-limiting (resolvable, not infinite noise). Bounded economic
    cost from residual vulnerability.
  - **Conscription → capacity** — a faction fighting active insurgencies
    mobilizes, raising military strength toward suppression capability.
  - **Onset dampener** — an already-embattled faction earns governance focus
    (legitimacy bonus) that makes *new* civil wars harder to ignite.
  - **Fragmentation consequence** — a faction bleeding territory to a large
    insurgency loses economic capacity (the split that never split).

Pure/tunable; wired via tools/gumas_memory_run.py and A/B'd. Realism first;
stability effects reported as measured, not forced.
"""

from __future__ import annotations


class ConsequenceLayer:
    # Conscription: modest emergency mobilization. Kept low — overwhelming
    # repression erases conflict entirely, which is neither realistic nor the
    # goal; the two-sided MECH-SOC-002/003 already manages onset/resolution, so
    # conscription is a realism touch (capacity under duress), not a war-ender.
    CONSCRIPTION_TARGET = 0.62
    CONSCRIPTION_RATE = 0.03
    # Onset dampener: off by default — redundant with the DSI gate + war-
    # weariness, and stacking it erases conflict. Retained as a tunable.
    ONSET_DAMPEN_PER_WAR = 0.0
    ONSET_DAMPEN_CAP = 0.05
    # Counter-intel: investment rate + ceiling are kept GENTLE on purpose.
    # `counter_intel_strength` is a shared lever — it also feeds the rebellion
    # onset `ci_suppression` term — so an aggressive build-up crushes rebellion
    # entirely (over-suppression, which trades against both realism and the
    # conflict-relief stability metric). A modest rise makes *compromise* more
    # self-limiting without flattening the galaxy's conflict dynamics.
    CI_INVESTMENT_RATE = 0.012
    CI_CEILING = 0.50
    INTEL_ECON_COST = 0.004
    # Fragmentation: economic capacity lost per turn while a large insurgency
    # holds territory above the fragmentation threshold.
    FRAG_TERRITORY_THRESHOLD = 0.5
    FRAG_ECON_DRAG = 0.004

    # ---- conscription -----------------------------------------------------
    def conscription_target(self, military_strength: float, active_wars: int) -> float:
        if active_wars <= 0:
            return military_strength
        return (military_strength
                + (self.CONSCRIPTION_TARGET - military_strength) * self.CONSCRIPTION_RATE
                if military_strength < self.CONSCRIPTION_TARGET else military_strength)

    # ---- onset dampener ---------------------------------------------------
    def onset_dampen_bonus(self, active_wars: int) -> float:
        return min(self.ONSET_DAMPEN_CAP, self.ONSET_DAMPEN_PER_WAR * max(0, active_wars))

    # ---- counter-intel response surface -----------------------------------
    def ci_investment(self, counter_intel_strength: float, intel_pressure: float) -> float:
        """Raise CI toward the ceiling, faster when intel pressure is high."""
        if counter_intel_strength >= self.CI_CEILING:
            return counter_intel_strength
        gap = self.CI_CEILING - counter_intel_strength
        return counter_intel_strength + gap * self.CI_INVESTMENT_RATE * min(1.0, 0.3 + intel_pressure)

    def intel_econ_cost(self, counter_intel_strength: float, intel_pressure: float) -> float:
        """Episodic, self-limiting economic drag: only bites when there is real
        compromise pressure, and shrinks as counter-intelligence adapts."""
        return self.INTEL_ECON_COST * max(0.0, 1.0 - counter_intel_strength) * max(0.0, intel_pressure)

    # ---- fragmentation consequence ----------------------------------------
    def fragmentation_drag(self, territory_controlled: float) -> float:
        return self.FRAG_ECON_DRAG if territory_controlled >= self.FRAG_TERRITORY_THRESHOLD else 0.0
