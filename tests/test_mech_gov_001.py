"""MECH-GOV-001 — Faction Decision Retrieval Model.

Locks in the two canon rules the mechanic was designed for
(canon/L2/mechanics/03_galactic_union_mechanics_and_models.md):
    "betrayal history raises the odds of future betrayal"
    "weakness increases the odds of negotiation"
plus the memory substrate's decay and the model's determinism.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from mech_gov_001 import FactionDecisionModel, PopulationGrievanceModel  # noqa: E402

STRONG = {"name": "Galactic Union", "military_strength": 0.7}
WEAK = {"name": "Vel-Surak Compact", "military_strength": 0.3}


@pytest.mark.simulation
def test_no_history_is_neutral():
    m = FactionDecisionModel(seed=808)
    d = m.decide(STRONG, "The Black Hand")
    assert d.action == "hold", d.scores
    assert abs(m.disposition("Galactic Union", "The Black Hand")[0]) < 0.05


@pytest.mark.simulation
def test_betrayal_history_hardens_a_strong_faction():
    """Canon: betrayal history raises the odds of future hostility."""
    m = FactionDecisionModel(seed=808)
    for _ in range(2):
        m.tick(2)
        m.record_event("Galactic Union", "betrayal", about="The Black Hand", importance=8)
    disp, retrieved = m.disposition("Galactic Union", "The Black Hand")
    assert disp < -0.4, f"disposition should be hostile, got {disp}"
    assert retrieved, "betrayal memories should be retrievable"
    assert m.decide(STRONG, "The Black Hand").action in ("escalate", "betray", "verify")


@pytest.mark.simulation
def test_weakness_favors_negotiation_under_the_same_threat():
    """Canon: weakness increases the odds of negotiation (de-escalation)."""
    m = FactionDecisionModel(seed=808)
    m.tick(2)
    m.record_event("Vel-Surak Compact", "betrayal", about="The Black Hand", importance=8)
    weak_action = m.decide(WEAK, "The Black Hand").action
    # Same hostile memory, strong faction:
    m.record_event("Galactic Union", "betrayal", about="The Black Hand", importance=8)
    strong_action = m.decide(STRONG, "The Black Hand").action
    assert weak_action in ("negotiate", "verify"), weak_action
    assert strong_action in ("escalate", "betray"), strong_action
    assert weak_action != strong_action


@pytest.mark.simulation
def test_alliance_memory_enables_alliance():
    m = FactionDecisionModel(seed=808)
    for _ in range(3):
        m.tick(1)
        m.record_event("Galactic Union", "alliance", about="Armada Nova Systems", importance=6)
    assert m.disposition("Galactic Union", "Armada Nova Systems")[0] > 0.3
    assert m.decide(STRONG, "Armada Nova Systems").action == "ally"


@pytest.mark.simulation
def test_memory_decays_over_time():
    m = FactionDecisionModel(seed=808)
    m.record_event("Galactic Union", "betrayal", about="The Black Hand", importance=8)
    fresh = abs(m.disposition("Galactic Union", "The Black Hand")[0])
    m.tick(60)  # many turns later
    faded = abs(m.disposition("Galactic Union", "The Black Hand")[0])
    assert faded < fresh, f"memory should decay: fresh {fresh}, faded {faded}"


@pytest.mark.simulation
def test_grievance_accumulates_and_relief_eases():
    """MECH-SOC-001: hardship/repression raise grievance; relief lowers it."""
    s = PopulationGrievanceModel(seed=808)
    assert s.grievance_pressure("Velkaris") == 0.0
    for _ in range(3):
        s.tick(1)
        s.record("Velkaris", "repression", importance=7)
        s.record("Velkaris", "hardship", importance=6)
    aggrieved = s.grievance_pressure("Velkaris")
    assert aggrieved > 0.3, aggrieved
    # Relief eases it.
    for _ in range(5):
        s.tick(1)
        s.record("Velkaris", "relief", importance=6)
        s.record("Velkaris", "prosperity", importance=6)
    assert s.grievance_pressure("Velkaris") < aggrieved


@pytest.mark.simulation
def test_grievance_persists_path_dependence():
    """Grievance decays slowly (half-life 30 turns) — a population that
    suffered carries it forward, the point of the social-memory model."""
    s = PopulationGrievanceModel(seed=1)
    for _ in range(4):
        s.record("Torix", "repression", importance=8)
        s.tick(1)
    early = s.grievance_pressure("Torix")
    s.tick(10)   # a decade of turns later, no new relief
    assert s.grievance_pressure("Torix") > 0.5 * early, "grievance should persist"


@pytest.mark.simulation
def test_determinism():
    """Same seed + event log -> identical decisions (the wall-clock fix)."""
    def run():
        m = FactionDecisionModel(seed=42)
        m.tick(1); m.record_event("A", "betrayal", about="B", importance=7)
        m.tick(3); m.record_event("A", "alliance", about="C", importance=5)
        return [m.decide({"name": "A", "military_strength": 0.6}, t).action for t in ("B", "C")]
    assert run() == run()
