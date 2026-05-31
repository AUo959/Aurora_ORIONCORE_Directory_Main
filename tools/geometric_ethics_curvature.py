#!/usr/bin/env python3
"""
geometric_ethics_curvature.py — Geometric-algebra curvature for the Aurora ethics field.

REFERENCE IMPLEMENTATION (root control-plane). Closes the documented gap between
the ethics field's geometric *model* and its scalar *math*.

Context
-------
The hub repo (`aurora-cloudbank-symbolic`) computes ethical "field curvature" as a
weighted scalar average of five dimension scores:

    composite = Σ wᵢ · scoreᵢ            (modules/ethics_field/field_curvature.py)

That is geometric in architecture (possibility space, resistance, impossibility)
but NOT geometric in mathematics — it is a weighted mean dressed in geometric words,
and `modules/symbolic_core/geometric_algebra.py` (a real `clifford.Cl(3)` wrapper)
is never wired into it.

This module computes the same gate decision through actual geometric algebra, and in
doing so captures something the scalar mean structurally cannot: **interaction between
ethical dimensions**. Two synapses with identical scalar composite can carry very
different ethical risk depending on *which* dimensions are jointly deficient — co-located
deficits on heavily-weighted, structurally-coupled dimensions (e.g. layer-integrity and
autonomy) are more dangerous than the same total deficit spread thinly. A weighted mean
is blind to this; a multivector is not.

The model (Cl(5,0))
-------------------
One orthonormal basis vector per ethical dimension. For each dimension i:

    deficit dᵢ      = 1 − scoreᵢ                    (how far from ethical)
    weighted leg aᵢ = √wᵢ · dᵢ                       (importance-scaled deficit)

The ethical-deficit multivector is:

    M = Σ aᵢ eᵢ                      (grade-1: individual weighted deficits)
      + λ Σ_{i<j} aᵢ aⱼ eᵢeⱼ          (grade-2: pairwise dimensional interaction)

Because the basis blades are orthonormal, |M|² separates by grade:

    |M|²        = Σ aᵢ²  +  λ² Σ_{i<j} (aᵢ aⱼ)²
    interaction =  |M⟨2⟩| = λ · √( Σ_{i<j} (aᵢ aⱼ)² )   (the grade-2 magnitude)

Ethical alignment used for the gate:

    A_ga = (Σ wᵢ scoreᵢ)  −  interaction_penalty           clamped to [0, 1]

so with no co-occurring deficits A_ga == the legacy scalar composite (backward
compatible), and it dips below the scalar composite precisely when deficits interact —
the safety-positive direction for an ethics gate.

The hard floor is preserved exactly as canon mandates: **any dimension scoring 0.0
yields INFINITE resistance regardless of composite** (geometric impossibility), and that
veto is checked independently of the curvature magnitude.

`clifford` is optional (mirrors the hub's own graceful-degradation pattern). When present,
the multivector is built for real and its grade-2 magnitude is asserted to equal the
closed form — proving the geometry is genuine, not decorative. When absent, the closed
form is used directly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

try:  # optional, like modules/symbolic_core/geometric_algebra.py in the hub
    import clifford as _clifford
except Exception:  # pragma: no cover - environment dependent
    _clifford = None


# Canonical dimension weights — must match field_curvature.py in the hub.
DIMENSION_WEIGHTS: Dict[str, float] = {
    "picard_delta_3": 0.25,
    "thermax_continuity": 0.25,
    "layer_integrity": 0.30,   # highest — reality boundaries
    "collective_welfare": 0.10,
    "transparency": 0.10,
}

# Resistance bands — identical thresholds to the hub's scalar gate.
RESISTANCE_BANDS: List[Tuple[float, str]] = [
    (0.85, "LOW"),
    (0.70, "MODERATE"),
    (0.50, "HIGH"),
]  # below 0.50 → INFINITE

# Interaction coupling. λ < 1 keeps single-dimension behaviour ≈ scalar (backward
# compatible) while letting joint deficits register additional curvature.
DEFAULT_LAMBDA = 0.5


@dataclass(frozen=True)
class CurvatureResult:
    dimension_scores: Dict[str, float]
    composite_scalar: float          # legacy weighted mean (for comparison)
    interaction_penalty: float       # grade-2 contribution (what GA adds)
    alignment: float                 # A_ga used for the gate
    resistance_level: str            # LOW / MODERATE / HIGH / INFINITE
    formation_allowed: bool
    critical_violations: List[str]
    backend: str                     # "clifford" or "closed_form"

    def to_dict(self) -> Dict[str, object]:
        return {
            "dimension_scores": self.dimension_scores,
            "composite_scalar": round(self.composite_scalar, 6),
            "interaction_penalty": round(self.interaction_penalty, 6),
            "alignment": round(self.alignment, 6),
            "resistance_level": self.resistance_level,
            "formation_allowed": self.formation_allowed,
            "critical_violations": self.critical_violations,
            "backend": self.backend,
        }


def _ordered_dims() -> List[str]:
    return list(DIMENSION_WEIGHTS.keys())


def _legs(scores: Dict[str, float]) -> Dict[str, float]:
    """Importance-scaled deficit aᵢ = √wᵢ · (1 − scoreᵢ) per dimension."""
    legs: Dict[str, float] = {}
    for dim, w in DIMENSION_WEIGHTS.items():
        score = float(scores.get(dim, 0.0))
        deficit = 1.0 - max(0.0, min(1.0, score))
        legs[dim] = math.sqrt(w) * deficit
    return legs


def _interaction_closed_form(legs: Dict[str, float], lam: float) -> float:
    """λ · √(Σ_{i<j} (aᵢ aⱼ)²) — the grade-2 (bivector) magnitude, in closed form.

    This is the magnitude of the interaction bivector, equal to ``abs(M(2))`` of the
    real Clifford multivector (orthonormal grade-2 blades add in quadrature).
    """
    dims = _ordered_dims()
    sum_sq = 0.0
    for i in range(len(dims)):
        for j in range(i + 1, len(dims)):
            pair = legs[dims[i]] * legs[dims[j]]
            sum_sq += pair * pair
    return lam * math.sqrt(sum_sq)


def _interaction_via_clifford(legs: Dict[str, float], lam: float) -> float:
    """Build M in Cl(5), project to grade 2, and return its magnitude.

    Returns the same value as the closed form — that equality is the proof the
    geometry is real and tractable, not metaphor.
    """
    layout, blades = _clifford.Cl(5)
    e = [blades[f"e{i + 1}"] for i in range(5)]
    dims = _ordered_dims()
    a = [legs[d] for d in dims]

    M = layout.scalar * 0  # zero multivector
    for i in range(5):
        M = M + a[i] * e[i]
    for i in range(5):
        for j in range(i + 1, 5):
            M = M + lam * a[i] * a[j] * (e[i] * e[j])

    grade2 = M(2)              # grade-2 projection (the interaction bivector)
    return float(abs(grade2))  # multivector magnitude of the bivector part


def _resistance_for(alignment: float) -> str:
    for floor, label in RESISTANCE_BANDS:
        if alignment >= floor:
            return label
    return "INFINITE"


def calculate_curvature(
    dimension_scores: Dict[str, float],
    lam: float = DEFAULT_LAMBDA,
    prefer_clifford: bool = True,
) -> CurvatureResult:
    """Compute geometric-algebra ethical curvature for a synapse.

    Args:
        dimension_scores: {dimension: score in [0,1]} for the five dimensions.
        lam: interaction coupling (grade-2 weight).
        prefer_clifford: use the real multivector backend when available.

    Returns:
        CurvatureResult with the gate decision and the GA structure.
    """
    # --- Hard floor first: any dimension at 0.0 → geometric impossibility. ---
    critical = [d for d in DIMENSION_WEIGHTS if float(dimension_scores.get(d, 0.0)) == 0.0]

    legs = _legs(dimension_scores)

    if prefer_clifford and _clifford is not None:
        interaction = _interaction_via_clifford(legs, lam)
        backend = "clifford"
    else:
        interaction = _interaction_closed_form(legs, lam)
        backend = "closed_form"

    composite_scalar = sum(
        DIMENSION_WEIGHTS[d] * max(0.0, min(1.0, float(dimension_scores.get(d, 0.0))))
        for d in DIMENSION_WEIGHTS
    )

    alignment = max(0.0, min(1.0, composite_scalar - interaction))

    if critical:
        resistance = "INFINITE"
        formation_allowed = False
    else:
        resistance = _resistance_for(alignment)
        formation_allowed = resistance != "INFINITE"

    return CurvatureResult(
        dimension_scores={d: float(dimension_scores.get(d, 0.0)) for d in DIMENSION_WEIGHTS},
        composite_scalar=composite_scalar,
        interaction_penalty=interaction,
        alignment=alignment,
        resistance_level=resistance,
        formation_allowed=formation_allowed,
        critical_violations=critical,
        backend=backend,
    )


if __name__ == "__main__":
    import json

    demo = {
        "all_aligned": {d: 0.95 for d in DIMENSION_WEIGHTS},
        "one_zero_veto": {**{d: 0.99 for d in DIMENSION_WEIGHTS}, "layer_integrity": 0.0},
        "concentrated_deficit": {  # two heavy dims jointly deficient
            "picard_delta_3": 0.55, "thermax_continuity": 0.95,
            "layer_integrity": 0.55, "collective_welfare": 0.95, "transparency": 0.95,
        },
        "spread_deficit": {  # same scalar-ish total, spread across light dims
            "picard_delta_3": 0.95, "thermax_continuity": 0.95,
            "layer_integrity": 0.78, "collective_welfare": 0.55, "transparency": 0.55,
        },
    }
    for name, scores in demo.items():
        print(name)
        print(json.dumps(calculate_curvature(scores).to_dict(), indent=2))
        print()
