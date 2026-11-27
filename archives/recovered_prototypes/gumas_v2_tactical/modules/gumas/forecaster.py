#!/usr/bin/env python3
"""
GUMAS L2 Enhanced Monte Carlo Forecaster v2.0
Anchor: GUMAS-FORECASTER-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
Version: 2.0.0

Enhanced forecasting system using Monte Carlo ensemble methods
with intervention modeling, statistical analysis, and risk assessment.
"""

import copy
import json
import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from modules.gumas.models import ConflictPhase, EventType, GUMASState, SimulationEvent
from modules.gumas.formulas import _clamp


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class Intervention:
    """Represents an intervention scenario to inject into forecast runs."""
    name: str
    event: SimulationEvent
    description: str = ""


@dataclass
class FactionTrajectory:
    """Aggregated trajectory metrics for a single faction across all runs."""
    faction_id: str
    military_mean: List[float] = field(default_factory=list)
    military_std: List[float] = field(default_factory=list)
    economic_mean: List[float] = field(default_factory=list)
    economic_std: List[float] = field(default_factory=list)
    trust_mean: Dict[str, List[float]] = field(default_factory=dict)
    legitimacy_mean: List[float] = field(default_factory=list)


@dataclass
class RiskEvent:
    """High-probability negative event detected across simulation runs."""
    description: str
    probability: float
    avg_severity: float
    affected_factions: List[str] = field(default_factory=list)


@dataclass
class SingleRunResult:
    """Result from a single simulation run."""
    seed: int
    trajectory: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    final_state: Dict[str, Any] = field(default_factory=dict)
    events_log: List[Dict[str, Any]] = field(default_factory=list)
    conflict_phases: Dict[str, str] = field(default_factory=dict)


@dataclass
class ForecastResult:
    """Aggregated forecast results from multiple simulation runs."""
    horizon: int
    n_runs: int
    conflict_probabilities: Dict[str, Dict[str, float]] = field(default_factory=dict)
    faction_trajectories: Dict[str, FactionTrajectory] = field(default_factory=dict)
    risk_events: List[RiskEvent] = field(default_factory=list)
    stability_index: float = 0.0
    summary: str = ""


@dataclass
class ComparisonResult:
    """Results comparing multiple intervention scenarios."""
    baseline: ForecastResult
    interventions: Dict[str, ForecastResult] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# Main Forecaster Class
# ============================================================================


class GUMASForecaster:
    """
    Enhanced Monte Carlo forecaster for GUMAS engine.

    Runs multiple independent simulation trajectories with perturbed initial
    conditions, aggregating results to provide probabilistic forecasts,
    risk assessment, and intervention impact analysis.
    """

    def __init__(
        self,
        engine_factory: Callable[[], Any],
        base_state: GUMASState,
        seed: int = 42,
    ):
        """
        Initialize forecaster with engine factory and base state.

        Args:
            engine_factory: Callable that returns new GUMASEngine instance
            base_state: Initial GUMASState for all forecasts
            seed: RNG seed for reproducibility
        """
        self.engine_factory = engine_factory
        self.base_state = base_state
        self.seed = seed

    def forecast(
        self,
        horizon: int = 20,
        n_runs: int = 10,
        uncertainty: float = 0.1,
    ) -> ForecastResult:
        """
        Run n_runs independent simulations for horizon turns.

        Each run starts with slightly perturbed initial conditions
        (trust scores, economic/military values perturbed by ±uncertainty).

        Args:
            horizon: Number of simulation turns per run
            n_runs: Number of independent simulation runs
            uncertainty: Perturbation magnitude (0.0 to 1.0)

        Returns:
            ForecastResult with aggregated metrics and analysis
        """
        rng = random.Random(self.seed)
        runs: List[SingleRunResult] = []

        for i in range(n_runs):
            run_seed = self.seed + i
            perturbed_state = self._perturb_state(self.base_state, rng, uncertainty)
            result = self._run_single(perturbed_state, horizon, intervention=None)
            result.seed = run_seed
            runs.append(result)

        return self._aggregate_runs(runs)

    def forecast_with_intervention(
        self,
        intervention: Intervention,
        horizon: int = 20,
        n_runs: int = 10,
        uncertainty: float = 0.1,
    ) -> ForecastResult:
        """
        Run forecast with intervention event injected at turn 0.

        Args:
            intervention: Intervention scenario to inject
            horizon: Number of simulation turns per run
            n_runs: Number of independent simulation runs
            uncertainty: Perturbation magnitude

        Returns:
            ForecastResult reflecting intervention impact
        """
        rng = random.Random(self.seed)
        runs: List[SingleRunResult] = []

        for i in range(n_runs):
            run_seed = self.seed + i
            perturbed_state = self._perturb_state(self.base_state, rng, uncertainty)
            result = self._run_single(perturbed_state, horizon, intervention=intervention)
            result.seed = run_seed
            runs.append(result)

        return self._aggregate_runs(runs)

    def compare_interventions(
        self,
        interventions: List[Intervention],
        horizon: int = 20,
        n_runs: int = 10,
    ) -> ComparisonResult:
        """
        Compare forecast outcomes across baseline and multiple interventions.

        Args:
            interventions: List of Intervention scenarios to compare
            horizon: Number of simulation turns per run
            n_runs: Number of independent simulation runs per scenario

        Returns:
            ComparisonResult with baseline, all interventions, and recommendations
        """
        # Run baseline
        baseline = self.forecast(horizon=horizon, n_runs=n_runs, uncertainty=0.1)

        # Run each intervention
        intervention_results: Dict[str, ForecastResult] = {}
        for intervention in interventions:
            result = self.forecast_with_intervention(
                intervention, horizon=horizon, n_runs=n_runs, uncertainty=0.1
            )
            intervention_results[intervention.name] = result

        # Generate recommendations
        recommendations = self._generate_recommendations(
            baseline, intervention_results
        )

        return ComparisonResult(
            baseline=baseline,
            interventions=intervention_results,
            recommendations=recommendations,
        )

    # ========================================================================
    # Private Methods
    # ========================================================================

    def _perturb_state(
        self, state: GUMASState, rng: random.Random, uncertainty: float
    ) -> GUMASState:
        """
        Create deep copy of state with randomized perturbations.

        Perturbs:
        - trust_scores: ±uncertainty for each bilateral pair
        - military_strength: ±uncertainty * 0.5
        - economic_strength: ±uncertainty * 0.5
        - population_stability: ±uncertainty * 0.3
        - leader bias_intensity: ±uncertainty * 0.2

        All values clamped to valid ranges [0.0, 1.0].
        """
        perturbed = copy.deepcopy(state)

        # Perturb faction attributes
        for faction_id in perturbed.factions:
            faction = perturbed.factions[faction_id]

            # Military strength: ±uncertainty * 0.5
            delta_military = rng.uniform(-uncertainty * 0.5, uncertainty * 0.5)
            faction.military_strength = _clamp(
                faction.military_strength + delta_military, 0.0, 1.0
            )

            # Economic strength: ±uncertainty * 0.5
            delta_econ = rng.uniform(-uncertainty * 0.5, uncertainty * 0.5)
            faction.economic_strength = _clamp(
                faction.economic_strength + delta_econ, 0.0, 1.0
            )

            # Population stability: ±uncertainty * 0.3
            delta_pop = rng.uniform(-uncertainty * 0.3, uncertainty * 0.3)
            faction.population_stability = _clamp(
                faction.population_stability + delta_pop, 0.0, 1.0
            )

            # Leader bias intensity: ±uncertainty * 0.2
            if faction.leader:
                delta_bias = rng.uniform(-uncertainty * 0.2, uncertainty * 0.2)
                faction.leader.bias_intensity = _clamp(
                    faction.leader.bias_intensity + delta_bias, 0.0, 1.0
                )

        # Perturb trust scores
        for (f1, f2), score in list(perturbed.trust_scores.items()):
            delta_trust = rng.uniform(-uncertainty, uncertainty)
            perturbed.trust_scores[(f1, f2)] = _clamp(score + delta_trust, 0.0, 1.0)

        return perturbed

    def _run_single(
        self,
        state: GUMASState,
        horizon: int,
        intervention: Optional[Intervention] = None,
    ) -> SingleRunResult:
        """
        Execute a single simulation run for horizon turns.

        Optionally injects intervention event at turn 0.
        Collects trajectory data and events log.

        Args:
            state: Starting GUMASState (already perturbed)
            horizon: Number of turns to simulate
            intervention: Optional intervention to inject at turn 0

        Returns:
            SingleRunResult with trajectory and events
        """
        engine = self.engine_factory()
        engine.state = copy.deepcopy(state)

        trajectory: Dict[str, List[Dict[str, Any]]] = {
            faction_id: [] for faction_id in state.factions
        }
        events_log: List[Dict[str, Any]] = []
        conflict_phases: Dict[str, str] = {}

        # Inject intervention if provided
        if intervention:
            engine.state.events.append(intervention.event)
            events_log.append({
                "turn": 0,
                "type": "intervention",
                "name": intervention.name,
            })

        # Simulate horizon turns
        for turn in range(horizon):
            # Record snapshot before tick
            for faction_id, faction in engine.state.factions.items():
                trajectory[faction_id].append({
                    "military": faction.military_strength,
                    "economic": faction.economic_strength,
                    "legitimacy": faction.legitimacy,
                    "population_stability": faction.population_stability,
                })

            # Execute one turn
            try:
                result = engine.tick()
                if isinstance(result, dict) and "events" in result:
                    for event in result["events"]:
                        events_log.append({"turn": turn, "event": event})
            except Exception:
                # Handle engine errors gracefully
                pass

        # Capture final conflict phases
        for conflict_id, conflict in engine.state.conflicts.items():
            conflict_phases[conflict_id] = conflict.phase.name

        return SingleRunResult(
            seed=0,
            trajectory=trajectory,
            final_state=self._serialize_state(engine.state),
            events_log=events_log,
            conflict_phases=conflict_phases,
        )

    def _aggregate_runs(self, runs: List[SingleRunResult]) -> ForecastResult:
        """
        Aggregate results across all runs.

        Computes:
        - Mean/std of key metrics per faction per turn
        - Conflict phase probabilities at end of horizon
        - Risk events (high-probability negative outcomes)
        - Overall stability index
        - Human-readable summary
        """
        if not runs:
            return ForecastResult(horizon=0, n_runs=0)

        horizon = max(len(run.trajectory.get(fid, [])) for run in runs
                     for fid in run.trajectory.keys()) if runs[0].trajectory else 0

        # Aggregate faction trajectories
        faction_trajectories: Dict[str, FactionTrajectory] = {}
        factions_seen = set()
        for run in runs:
            for faction_id in run.trajectory.keys():
                factions_seen.add(faction_id)

        for faction_id in factions_seen:
            military_series = []
            economic_series = []
            legitimacy_series = []

            for turn in range(horizon):
                military_vals = []
                economic_vals = []
                legitimacy_vals = []

                for run in runs:
                    if faction_id in run.trajectory and turn < len(run.trajectory[faction_id]):
                        snap = run.trajectory[faction_id][turn]
                        military_vals.append(snap.get("military", 0.0))
                        economic_vals.append(snap.get("economic", 0.0))
                        legitimacy_vals.append(snap.get("legitimacy", 0.0))

                if military_vals:
                    military_series.append(statistics.mean(military_vals))
                    economic_series.append(statistics.mean(economic_vals))
                    legitimacy_series.append(statistics.mean(legitimacy_vals))

            faction_trajectories[faction_id] = FactionTrajectory(
                faction_id=faction_id,
                military_mean=military_series,
                military_std=[
                    self._safe_stdev([
                        run.trajectory[faction_id][t].get("military", 0.0)
                        for run in runs
                        if faction_id in run.trajectory and t < len(run.trajectory[faction_id])
                    ])
                    for t in range(horizon)
                ],
                economic_mean=economic_series,
                economic_std=[
                    self._safe_stdev([
                        run.trajectory[faction_id][t].get("economic", 0.0)
                        for run in runs
                        if faction_id in run.trajectory and t < len(run.trajectory[faction_id])
                    ])
                    for t in range(horizon)
                ],
                legitimacy_mean=legitimacy_series,
            )

        # Conflict phase probabilities
        conflict_phases_by_run: Dict[str, List[str]] = {}
        for run in runs:
            for conflict_id, phase in run.conflict_phases.items():
                if conflict_id not in conflict_phases_by_run:
                    conflict_phases_by_run[conflict_id] = []
                conflict_phases_by_run[conflict_id].append(phase)

        conflict_probabilities: Dict[str, Dict[str, float]] = {}
        for conflict_id, phases in conflict_phases_by_run.items():
            phase_counts: Dict[str, int] = {}
            for phase in phases:
                phase_counts[phase] = phase_counts.get(phase, 0) + 1
            conflict_probabilities[conflict_id] = {
                phase: count / len(phases) for phase, count in phase_counts.items()
            }

        # Risk events detection
        risk_events = self._detect_risk_events(runs)

        # Stability index
        stability_index = self._calc_stability_index(runs)

        # Generate summary
        summary = self._generate_summary(
            len(runs), horizon, stability_index, len(risk_events)
        )

        return ForecastResult(
            horizon=horizon,
            n_runs=len(runs),
            conflict_probabilities=conflict_probabilities,
            faction_trajectories=faction_trajectories,
            risk_events=risk_events,
            stability_index=stability_index,
            summary=summary,
        )

    def _calc_stability_index(self, runs: List[SingleRunResult]) -> float:
        """
        Calculate overall galaxy stability score (0=chaos, 1=peace).

        Stability = 1.0 - (avg_active_conflicts / max_possible_conflicts)
        weighted by conflict severity.
        """
        if not runs:
            return 1.0

        total_stability = 0.0
        for run in runs:
            active_count = sum(
                1 for phase in run.conflict_phases.values()
                if phase not in ("RESOLVED", "DORMANT")
            )
            run_stability = 1.0 - (active_count * 0.1)  # Each conflict reduces by 0.1
            total_stability += max(0.0, min(1.0, run_stability))

        return total_stability / len(runs)

    def _detect_risk_events(self, runs: List[SingleRunResult]) -> List[RiskEvent]:
        """Identify high-probability negative events across runs."""
        risk_events: List[RiskEvent] = []

        # Track occurrences of negative outcomes
        negative_pattern_count: Dict[str, int] = {}

        for run in runs:
            # Check for escalation patterns
            for conflict_id, phase in run.conflict_phases.items():
                if phase in ("ESCALATION", "CRISIS"):
                    key = f"conflict_escalation_{conflict_id}"
                    negative_pattern_count[key] = negative_pattern_count.get(key, 0) + 1

        # Convert counts to risk events
        for pattern_key, count in negative_pattern_count.items():
            probability = count / len(runs)
            if probability >= 0.3:  # 30% threshold
                risk_events.append(RiskEvent(
                    description=f"High probability {pattern_key.replace('_', ' ')}",
                    probability=probability,
                    avg_severity=probability * 0.8,
                    affected_factions=[],
                ))

        return risk_events

    def _generate_recommendations(
        self,
        baseline: ForecastResult,
        interventions: Dict[str, ForecastResult],
    ) -> List[str]:
        """Generate ranked recommendations based on intervention impacts."""
        recommendations: List[str] = []

        # Rank interventions by stability improvement
        ranked = sorted(
            interventions.items(),
            key=lambda x: x[1].stability_index - baseline.stability_index,
            reverse=True,
        )

        for name, result in ranked[:3]:  # Top 3
            improvement = (result.stability_index - baseline.stability_index) * 100
            if improvement > 0:
                recommendations.append(
                    f"Implement '{name}': Expected stability +{improvement:.1f}%"
                )

        if not recommendations:
            recommendations.append("Current baseline trajectory appears stable.")

        return recommendations

    def _generate_summary(
        self, n_runs: int, horizon: int, stability: float, risk_count: int
    ) -> str:
        """Generate human-readable summary of forecast."""
        stability_desc = (
            "highly stable"
            if stability > 0.8
            else "stable" if stability > 0.6 else "unstable"
        )

        risk_desc = (
            "no significant"
            if risk_count == 0
            else f"{risk_count} identified"
        )

        return (
            f"Monte Carlo forecast across {n_runs} runs over {horizon} turns "
            f"indicates a {stability_desc} outlook (stability: {stability:.2f}). "
            f"{risk_desc} risk events detected. "
            f"Recommend continuous monitoring and intervention assessment."
        )

    @staticmethod
    def _serialize_state(state: GUMASState) -> Dict[str, Any]:
        """Serialize GUMASState to JSON-compatible dictionary."""
        return {
            "turn": state.turn,
            "factions": {
                fid: {
                    "military": f.military_strength,
                    "economic": f.economic_strength,
                    "legitimacy": f.legitimacy,
                }
                for fid, f in state.factions.items()
            },
            "conflicts": {
                cid: c.phase.name for cid, c in state.conflicts.items()
            },
        }

    @staticmethod
    def _safe_stdev(values: List[float]) -> float:
        """Compute standard deviation, handling edge cases."""
        if len(values) < 2:
            return 0.0
        try:
            return statistics.stdev(values)
        except (ValueError, statistics.StatisticsError):
            return 0.0
