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

from mech_gov_001 import (  # noqa: E402
    ComplacencyModel,
    CultureModel,
    DiplomaticStabilityModel,
    FactionDecisionModel,
    InsurgencyResolutionModel,
    MediationModel,
    PopulationGrievanceModel,
    PowerDynamicsModel,
    SuccessionModel,
    TerritorialConsequenceModel,
    TreatyEnforcementModel,
    WarEconomyModel,
    PostWarRecoveryModel,
    WarWearinessModel,
)

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
def test_dsi_militarization_destabilizes():
    """MECH-SOC-003: a cohesive, prosperous polity has higher stability
    capacity than a militarized/corrupt one (DSI = (P+E+S)/(C+M))."""
    d = DiplomaticStabilityModel()
    cohesive = d.capacity_for(economic=0.8, cohesion=0.8, political_unity=0.8,
                              militarization=0.3, institutional_control=0.8)
    militarized = d.capacity_for(economic=0.4, cohesion=0.4, political_unity=0.4,
                                 militarization=0.9, institutional_control=0.4)
    assert cohesive > militarized + 0.15, (cohesive, militarized)
    assert 0.0 <= militarized <= cohesive <= 1.0


@pytest.mark.simulation
def test_dsi_grievance_erodes_cohesion():
    """Remembered grievance (MECH-SOC-001) lowers effective cohesion -> capacity."""
    d = DiplomaticStabilityModel()
    base = {"economic": 0.7, "cohesion": 0.7, "political_unity": 0.7,
            "militarization": 0.5, "institutional_control": 0.6}
    calm = d.capacity_for(grievance=0.0, **base)
    aggrieved = d.capacity_for(grievance=0.8, **base)
    assert aggrieved < calm


@pytest.mark.simulation
def test_war_weariness_builds_then_erodes_support():
    """MECH-SOC-002: a grinding war wearies — weariness grows with time and
    erosion rises with it; ending the war resets the clock."""
    w = WarWearinessModel()
    # Within the grace period, no weariness yet.
    assert w.weary("ins-1", active=True) == 0.0  # turn 1
    for _ in range(3):
        w.weary("ins-1", active=True)            # turns 2..4 (grace = 4)
    early = w.weary("ins-1", active=True)         # turn 5, just past grace
    for _ in range(25):
        late = w.weary("ins-1", active=True)
    assert late > early, (early, late)
    se_late, _, _ = w.erosion(late)
    se_early, _, _ = w.erosion(early)
    assert se_late > se_early >= 0.0
    # Resolving/ending the war resets the clock.
    assert w.weary("ins-1", active=False) == 0.0
    assert w.weary("ins-1", active=True) == 0.0


@pytest.mark.simulation
def test_post_war_recovery_lifts_and_never_degrades():
    """MECH-SOC-005: reconstruction lifts low values toward health and eases
    stress drivers down, but never degrades an already-healthy value."""
    r = PostWarRecoveryModel()
    # population/legitimacy/food: lift toward a higher target
    assert r.toward(0.10, r.POP_TARGET, r.POP_RECOVERY_RATE) > 0.10
    assert r.toward(0.90, 0.72, 0.06) == 0.90          # already healthy -> unchanged
    # housing/unemployment: ease down toward a lower target
    assert r.ease_down(0.80, r.HOUSING_TARGET, r.DRIVER_RECOVERY_RATE) < 0.80
    assert r.ease_down(0.10, r.HOUSING_TARGET, 0.05) == 0.10  # already low -> unchanged
    # repeated peacetime recovery converges toward the target
    v = 0.10
    for _ in range(80):
        v = r.toward(v, r.POP_TARGET, r.POP_RECOVERY_RATE)
    assert v > 0.65


@pytest.mark.simulation
def test_complacency_builds_in_peace_and_purges_in_war():
    """MECH-SOC-006: long peace breeds complacency (a destabilizer that lets
    unrest recur); serious conflict purges it — the limit-cycle engine that
    keeps the galaxy from freezing into permanent peace."""
    c = ComplacencyModel()
    # Within the grace period a fresh order stays clean.
    for _ in range(c.GRACE_TURNS):
        assert c.update("Velkaris", at_serious_war=False) == 0.0
    early = c.update("Velkaris", at_serious_war=False)   # just past grace
    for _ in range(40):
        late = c.update("Velkaris", at_serious_war=False)
    assert late > early > 0.0, (early, late)
    assert late <= c.PEAK                                  # capped, never runaway
    # Its destabilizing drags scale with the accrued complacency.
    assert c.legitimacy_drag(late) > c.legitimacy_drag(early) >= 0.0
    assert c.stress_pressure(late) > 0.0
    assert c.insurgent_fuel(late) > 0.0
    # Serious conflict resets the peace clock — upheaval renews the order.
    assert c.update("Velkaris", at_serious_war=True) == 0.0
    assert c.update("Velkaris", at_serious_war=False) == 0.0   # grace restarts


@pytest.mark.simulation
def test_insurgency_resolution_is_earned_and_settles():
    """MECH-REB-004: a grinding, costly, stalemated insurgency whose host has
    domestic pressure to end it de-escalates more readily than a fresh, popular
    one; mediation helps; and repeated settlement progress reaches RESOLVED."""
    r = InsurgencyResolutionModel(seed=1)
    # A fresh, popular, low-cost insurgency: low de-escalation pull.
    fresh = r.deescalation_p(
        host_war_pressure=0.1, insurgent_strength=0.6, repression_level=0.2,
        turns_active=2, host_grievance=0.3, popular_support=0.8,
        diplomacy_openness=0.5, mediation_available=False)
    # A grinding, costly, stalemated, unpopular insurgency under domestic pressure.
    ripe = r.deescalation_p(
        host_war_pressure=0.8, insurgent_strength=0.3, repression_level=0.6,
        turns_active=40, host_grievance=0.8, popular_support=0.2,
        diplomacy_openness=0.7, mediation_available=False)
    assert ripe > fresh, (fresh, ripe)
    # Mediation (a diplomatic overture) raises the chance further (DIP-002 hook).
    mediated = r.deescalation_p(
        host_war_pressure=0.8, insurgent_strength=0.3, repression_level=0.6,
        turns_active=40, host_grievance=0.8, popular_support=0.2,
        diplomacy_openness=0.7, mediation_available=True)
    assert mediated > ripe
    # Settlement is reached only after accumulated progress, then it's terminal.
    settled = any(r.advance("ins-1", 1.0) for _ in range(5))
    assert settled
    r.forget("ins-1")
    assert "ins-1" not in r.progress


@pytest.mark.simulation
def test_mediation_needs_a_mutually_trusted_peaceful_broker():
    """MECH-DIP-002: a credible mediator is mutually trusted (>= floor) and not
    itself fighting a serious war. A well-connected host gets a broker; an
    isolated/distrusted one does not (it must grind to exhaustion)."""
    m = MediationModel()
    trust = {
        "union":   {"compact": 0.7, "warlord": 0.2, "fringe": 0.4},
        "compact": {"union": 0.7, "warlord": 0.2, "fringe": 0.4},  # mutual w/ union
        "warlord": {"union": 0.2, "compact": 0.2, "fringe": 0.2},  # distrusted by all
        "fringe":  {"union": 0.4, "compact": 0.4, "warlord": 0.2},  # below floor
    }
    # Union and Compact mutually trust each other -> each can broker for the other.
    assert m.find_mediator("union", trust, busy=set()) == "compact"
    # The warlord is distrusted by everyone -> no credible broker.
    assert m.find_mediator("warlord", trust, busy=set()) is None
    # Fringe's only above-floor partner is... none at >=0.58 -> no broker.
    assert m.find_mediator("fringe", trust, busy=set()) is None
    # A faction fighting its own serious war can't broker (excluded via busy).
    assert m.find_mediator("union", trust, busy={"compact"}) is None


@pytest.mark.simulation
def test_treaty_binds_then_breaks_under_backsliding():
    """MECH-DIP-003: a peace accord holds while conditions stay near the floor it
    set, survives a grace window, breaks under heavy backsliding, and repeated
    breaches compound (a later accord breaks under lighter strain)."""
    t = TreatyEnforcementModel(seed=1)
    t.register("velkaris", mediator="union", base_grievance=0.30)
    # Within grace: no breach even under strain.
    assert t.check("velkaris", current_grievance=0.55, trust_with_mediator=0.5) is None
    # Past grace, conditions near the floor -> holds.
    for _ in range(t.GRACE):
        t.check("velkaris", current_grievance=0.31, trust_with_mediator=0.5)
    assert "velkaris" in t.accords
    # A heavy backslide breaks it; the broker is named in the broken accord.
    t.register("velkaris", mediator="union", base_grievance=0.30)
    for _ in range(t.GRACE):
        t.check("velkaris", 0.30, 0.5)
    broken = None
    for _ in range(5):
        broken = t.check("velkaris", current_grievance=0.55, trust_with_mediator=0.5)
        if broken:
            break
    assert broken is not None and broken["mediator"] == "union"
    assert t.breaches["velkaris"] >= 1
    assert "velkaris" not in t.accords  # retired on breach


@pytest.mark.simulation
def test_culture_weights_decisions_by_dominant_bias():
    """MECH-GOV-002: a leader's dominant_bias colours the settle-or-grind
    decision. A zero-sum clan or sunk-cost attritionist resists a negotiated end
    (negative settlement lean); a hyper-rational or survivalist order takes it
    (positive). Accepts the engine's BiasType.X form and the traits.json
    '..._thinking'/'..._bias' text forms alike. Unknown bias is neutral."""
    c = CultureModel()
    assert c.settlement_lean("BiasType.ZERO_SUM") < 0
    assert c.settlement_lean("zero_sum_thinking") < 0
    assert c.settlement_lean("sunk_cost_fallacy") < 0
    assert c.settlement_lean("BiasType.HYPER_RATIONALISM") > 0
    assert c.settlement_lean("survivorship_bias") > 0
    # the rational order settles more readily than the zero-sum clan
    assert c.settlement_lean("hyper_rational") > c.settlement_lean("zero_sum")
    # belligerent cultures escalate more than rational ones
    assert c.escalation_lean("zero_sum") > c.escalation_lean("hyper_rational")
    # unknown / missing bias is culturally neutral
    assert c.settlement_lean(None) == 0.0
    assert c.escalation_lean("some_unmodelled_bias") == 0.0


@pytest.mark.simulation
def test_succession_falls_on_lost_grip_coup_vs_election():
    """MECH-GOV-003: a healthy leader keeps power; a scandal-ridden, illegitimate
    one falls after the honeymoon. A militarized polity falls by coup, an economic
    one by election, and the successor arrives with a fresh mandate, cleared
    scandals, and a shifted culture."""
    s = SuccessionModel(seed=3)
    # grip drops as legitimacy falls and scandals pile up
    assert s.grip(0.7, 0, 0.0) > s.grip(0.3, 100, 0.3)
    # A strong, clean leader survives indefinitely.
    strong = [s.step("union", legitimacy=0.7, scandals=0, war_pressure=0.0, militarized=False)
              for _ in range(60)]
    assert all(r is None for r in strong)
    # A failing militarized regime eventually falls — by coup, hard-line successor.
    fell = None
    for _ in range(80):
        fell = s.step("warlord", legitimacy=0.15, scandals=110, war_pressure=0.4, militarized=True)
        if fell:
            break
    assert fell is not None and fell["kind"] == "coup"
    assert fell["new_bias"] in s.COUP_BIASES
    assert fell["legit"] == s.COUP_LEGIT and fell["stress"] > 0
    # A failing economic regime falls by election, pragmatic successor, no stress shock.
    elected = None
    for _ in range(80):
        elected = s.step("compact", legitimacy=0.12, scandals=120, war_pressure=0.2, militarized=False)
        if elected:
            break
    assert elected is not None and elected["kind"] == "election"
    assert elected["new_bias"] in s.ELECTION_BIASES and elected["stress"] == 0.0
    # structural character is locked at first sight (a transient flip is ignored)
    assert s.character["warlord"] is True and s.character["compact"] is False


@pytest.mark.simulation
def test_power_stance_splits_balance_vs_bandwagon_by_culture():
    """MECH-POW-001: a faction's stance toward a rising hegemon is decided by its
    culture — proud/defensive cultures balance against the strong, pragmatic/
    survivalist ones bandwagon with it. Power is weighted military+economic+tech."""
    p = PowerDynamicsModel()
    # power rises with all three components
    assert p.power(0.9, 0.9, 1.0) > p.power(0.2, 0.2, 0.2)
    assert p.stance("BiasType.ZERO_SUM") == "balance"
    assert p.stance("fear_based") == "balance"
    assert p.stance("BiasType.SURVIVORSHIP") == "bandwagon"
    assert p.stance("status_quo") == "bandwagon"
    assert p.stance("hyper_rationalism") == "bandwagon"
    # an unmodelled culture takes no stance
    assert p.stance("some_unmodelled_bias") == "neutral"
    assert p.stance(None) == "neutral"


@pytest.mark.simulation
def test_territorial_loss_is_permanent_and_caps_the_economy():
    """MECH-TER-001: a faction's mature wars permanently scar its territory, which
    lowers its economic ceiling; peace reclaims only contested ground, never the
    seceded core; and loss is bounded so a faction keeps its core."""
    t = TerritorialConsequenceModel()
    assert t.held_territory("velkaris") == 1.0 and t.economic_ceiling("velkaris") == 1.0
    for _ in range(20):
        t.scar("velkaris", insurgent_territory=0.6)
    assert t.total_loss("velkaris") > 0.05
    assert t.economic_ceiling("velkaris") < 1.0
    assert t.held_territory("velkaris") < 1.0
    # bounded — a faction always keeps its core
    for _ in range(2000):
        t.scar("velkaris", insurgent_territory=1.0)
    assert t.total_loss("velkaris") <= t.LOSS_CAP + 1e-9
    # the seceded core is permanent: peace reclaims contested ground, never it
    war_torn = "torix"
    for _ in range(10):
        t.scar(war_torn, insurgent_territory=0.5)
    seceded_floor = t.seceded[war_torn]
    assert seceded_floor > 0.0
    for _ in range(1000):
        t.reclaim(war_torn)
    assert t.contested.get(war_torn, 0.0) == 0.0           # all contested reclaimed
    assert abs(t.total_loss(war_torn) - seceded_floor) < 1e-9   # only the core loss remains
    assert t.total_loss(war_torn) > 0.0                    # and it is permanent


@pytest.mark.simulation
def test_war_economy_busts_and_booms_and_feeds_back():
    """MECH-ECO-001: war scarcity suppresses output; peace drives a recovery boom
    toward the ceiling; and a depressed economy deepens demographic stress while a
    booming one eases it (the economy → unrest feedback)."""
    e = WarEconomyModel()
    # war suppresses output; peace rebuilds it toward the (capped) ceiling
    assert e.flux(0.6, 0.9, at_war=True) < 0.6
    assert e.flux(0.6, 0.9, at_war=False) > 0.6
    # recovery cannot exceed the territory-capped ceiling
    assert e.flux(0.89, 0.9, at_war=False) <= 0.9
    # health is output relative to potential
    assert e.health(0.45, 0.9) == 0.5
    # a depressed economy raises stress; a booming one eases it; healthy is neutral
    assert e.stress_delta(0.3) > 0
    assert e.stress_delta(0.95) < 0
    assert e.stress_delta(0.75) == 0.0


@pytest.mark.simulation
def test_determinism():
    """Same seed + event log -> identical decisions (the wall-clock fix)."""
    def run():
        m = FactionDecisionModel(seed=42)
        m.tick(1); m.record_event("A", "betrayal", about="B", importance=7)
        m.tick(3); m.record_event("A", "alliance", about="C", importance=5)
        return [m.decide({"name": "A", "military_strength": 0.6}, t).action for t in ("B", "C")]
    assert run() == run()
