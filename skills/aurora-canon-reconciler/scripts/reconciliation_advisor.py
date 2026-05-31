#!/usr/bin/env python3
"""
Aurora Canon Reconciler — Reconciliation Advisor (v1.2)
Adapted from HDE++ (Heuristic Decision Engine PlusPlus) patterns.

Provides weighted multi-axis scoring for certainty tag recommendations,
confidence calculation, constraint propagation for layer/canon rules,
and explainable decision logging.

Design lineage: HDE++ → ReconciliationAdvisor
  - Weighted scoring engine → applied to entity readiness dimensions
  - Confidence delta calculation → applied to tag recommendation confidence
  - require/forbid constraint propagation → applied to layer and canon rules
  - Explainable decision log → applied to reconciliation audit trail

Usage:
    from reconciliation_advisor import ReconciliationAdvisor

    advisor = ReconciliationAdvisor()
    result = advisor.recommend_certainty(entity_profile, validation_report)
    # result = {
    #   "recommended_tag": "STAGING",
    #   "confidence": 0.78,
    #   "explanation": "...",
    #   "alternatives": [...],
    #   "constraints_applied": [...],
    #   "audit_entry": {...}
    # }
"""

import json
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Certainty Tag Profiles — the "models" in HDE++ terms
# ---------------------------------------------------------------------------
# Each tag has readiness requirements scored across multiple dimensions.
# Higher thresholds mean stricter requirements to earn that tag.

CERTAINTY_TAG_PROFILES: Dict[str, Dict[str, Any]] = {
    "CANON_PROMOTE": {
        "field_completeness": 1.0,    # All required fields must be present
        "conflict_freedom": 1.0,      # Zero unresolved conflicts with existing canon
        "provenance_strength": 0.8,   # Strong source attribution
        "schema_compliance": 1.0,     # Full schema compliance, no drift
        "layer_integrity": 1.0,       # No cross-layer contamination
        "review_status": 0.8,         # User has reviewed and approved
        "tags": ["promotion", "commit_ready"],
        "description": "Ready for Git commit. All checks passed, user approved.",
    },
    "STAGING": {
        "field_completeness": 0.8,
        "conflict_freedom": 0.7,
        "provenance_strength": 0.5,
        "schema_compliance": 0.8,
        "layer_integrity": 1.0,
        "review_status": 0.0,         # Doesn't require user review yet
        "tags": ["working", "revisable"],
        "description": "Usable for development. May be revised without retcon.",
    },
    "PLACED": {
        "field_completeness": 0.7,
        "conflict_freedom": 0.6,
        "provenance_strength": 0.4,
        "schema_compliance": 0.7,
        "layer_integrity": 1.0,
        "review_status": 0.0,
        "tags": ["map", "location_only"],
        "description": "Placed on L2 map. Revisable unless LOCKED_POSITION.",
    },
    "LOCKED_POSITION": {
        "field_completeness": 0.7,
        "conflict_freedom": 0.8,
        "provenance_strength": 0.6,
        "schema_compliance": 0.8,
        "layer_integrity": 1.0,
        "review_status": 0.3,
        "tags": ["map", "frozen_placement"],
        "description": "Map placement frozen. Attributes may still evolve.",
    },
    "UNCONFIRMED": {
        "field_completeness": 0.3,
        "conflict_freedom": 0.0,       # Conflicts are acceptable
        "provenance_strength": 0.2,
        "schema_compliance": 0.3,
        "layer_integrity": 0.5,        # Some cross-layer ambiguity tolerated
        "review_status": 0.0,
        "tags": ["draft", "unvalidated"],
        "description": "Mentioned but not validated. Needs work before staging.",
    },
    "LEGEND_CONTESTED": {
        "field_completeness": 0.4,      # Raised from 0.2 — legends should at least have basic identity fields
        "conflict_freedom": 0.0,
        "provenance_strength": 0.1,
        "schema_compliance": 0.2,
        "layer_integrity": 0.5,
        "review_status": 0.0,
        "tags": ["narrative", "in_universe_rumor"],
        "description": "In-universe rumor, myth, or disputed account.",
    },
    "APPROX": {
        "field_completeness": 0.5,
        "conflict_freedom": 0.3,
        "provenance_strength": 0.3,
        "schema_compliance": 0.5,
        "layer_integrity": 0.8,
        "review_status": 0.0,
        "tags": ["approximate", "partial_data"],
        "description": "Approximate data. Usable but not precise.",
    },
}

# Scoring dimensions and their default weights
DEFAULT_WEIGHTS: Dict[str, float] = {
    "field_completeness": 2.0,     # Most important — can't promote incomplete entities
    "conflict_freedom": 2.0,       # Equal importance — conflicts are blockers
    "provenance_strength": 1.0,    # Important but secondary
    "schema_compliance": 1.5,      # Structural integrity matters
    "layer_integrity": 3.0,        # Critical — cross-layer errors are the worst class
    "review_status": 1.0,          # Matters for promotion, less for staging
}


# ---------------------------------------------------------------------------
# Entity Profile Builder — converts validation results to scorable profile
# ---------------------------------------------------------------------------

def build_entity_profile(
    data: dict,
    validation_findings: list[dict],
    layer: str,
    entity_type: str,
    required_fields_total: Optional[int] = None,
    has_conflicts: bool = False,
    conflict_count: int = 0,
    user_reviewed: bool = False,
    origin_is_simulation: bool = False,
) -> Dict[str, float]:
    """
    Convert raw entity data + validation findings into a normalized
    readiness profile (0.0 to 1.0 per dimension) that the advisor can score.
    """
    blocks = [f for f in validation_findings if f.get("severity") == "BLOCK"]
    warns = [f for f in validation_findings if f.get("severity") == "WARN"]

    # Field completeness: 1.0 if no missing-field blocks, scaled down per block
    field_blocks = [f for f in blocks if f.get("code", "").startswith("MISSING")]
    total_fields = max(int(required_fields_total) if required_fields_total else len(data), 1)
    field_completeness = max(0.0, 1.0 - (len(field_blocks) / total_fields))

    # Conflict freedom: 1.0 if no conflicts, 0.0 if many
    if conflict_count == 0 and not has_conflicts:
        conflict_freedom = 1.0
    else:
        conflict_freedom = max(0.0, 1.0 - (conflict_count * 0.25))

    # Provenance strength: based on origin file quality
    origin = data.get("origin_file", "") or ""
    doc_sources = data.get("doc_sources", [])
    if isinstance(doc_sources, list) and len(doc_sources) >= 2:
        provenance = 0.8  # Multiple sources = strong
    elif doc_sources or origin:
        provenance = 0.5  # Single source = moderate
    else:
        provenance = 0.1  # No source = weak
    if origin_is_simulation:
        provenance *= 0.6  # Simulation origin reduces confidence (Tertiary Canon)

    # Schema compliance: based on validation warnings
    schema_warns = [f for f in warns if f.get("code", "") in (
        "DEPRECATED_FIELD", "INVALID_LOCATION_SUBTYPE", "INVALID_POLITY_SUBTYPE",
        "INVALID_DOMAIN_SUBTYPE", "NONSTANDARD_CHARACTER_ID", "ZYPHARI_ID_PREFIX",
        "UNKNOWN_CLEARANCE_LEVEL"
    )]
    schema_compliance = max(0.0, 1.0 - (len(schema_warns) * 0.15))
    if blocks:
        # Any BLOCK-level issue tanks schema compliance
        schema_compliance = min(schema_compliance, 0.3)

    # Layer integrity: check for cross-layer signals
    cross_layer = [f for f in warns if f.get("code") == "CROSS_LAYER_CONTAMINATION"]
    possible_l2 = [f for f in validation_findings
                   if f.get("code") == "POSSIBLE_L2_REFERENCE"]
    if cross_layer:
        layer_integrity = 0.1  # High-confidence cross-layer issue
    elif possible_l2:
        layer_integrity = 0.6  # Possible but not confirmed
    else:
        layer_integrity = 1.0

    # Review status
    review_status = 1.0 if user_reviewed else 0.0

    return {
        "field_completeness": round(field_completeness, 3),
        "conflict_freedom": round(conflict_freedom, 3),
        "provenance_strength": round(provenance, 3),
        "schema_compliance": round(schema_compliance, 3),
        "layer_integrity": round(layer_integrity, 3),
        "review_status": round(review_status, 3),
    }


# ---------------------------------------------------------------------------
# Reconciliation Advisor — the HDE++ engine retargeted for canon decisions
# ---------------------------------------------------------------------------

class ReconciliationAdvisor:
    """
    Weighted scoring engine for certainty tag recommendations.

    Design adapted from HDE++ (Heuristic Decision Engine PlusPlus):
    - Scores entity readiness across multiple dimensions
    - Calculates confidence based on gap between best and second-best tag
    - Supports require/forbid constraints for layer and canon rules
    - Produces explainable audit logs for every recommendation
    """

    def __init__(
        self,
        tag_profiles: Optional[Dict[str, Dict[str, Any]]] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.tag_profiles = tag_profiles or CERTAINTY_TAG_PROFILES
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self.constraints: Dict[str, Set[str]] = {"require": set(), "forbid": set()}
        self.custom_rules: List[Callable] = []
        self.audit_log: List[Dict[str, Any]] = []

    def set_constraints(self, require: Optional[list] = None, forbid: Optional[list] = None):
        """Set tag-level constraints. E.g., require=['map'] for location entities."""
        if require is not None:
            self.constraints["require"] = set(require)
        if forbid is not None:
            self.constraints["forbid"] = set(forbid)

    def add_rule(self, rule_fn: Callable):
        """Add a custom scoring rule. Signature: fn(tag_name, score, profile, entity_profile) -> score"""
        self.custom_rules.append(rule_fn)

    def score_tags(self, entity_profile: Dict[str, float]) -> Dict[str, float]:
        """
        Score every certainty tag against the entity's readiness profile.

        Scoring uses a "highest bar cleared" approach: for each tag, we check
        whether the entity meets ALL thresholds. Tags where the entity falls
        short on any dimension get penalized heavily. Among tags the entity
        qualifies for, higher-bar tags score better (we prefer the most
        demanding tag the entity can satisfy — promoting to the highest
        appropriate certainty level).
        """
        scores = {}
        for tag_name, tag_reqs in self.tag_profiles.items():
            # Constraint filtering (HDE++ pattern)
            tag_tags = set(tag_reqs.get("tags", []))
            if self.constraints["require"] and not self.constraints["require"].issubset(tag_tags):
                scores[tag_name] = -float("inf")
                continue
            if self.constraints["forbid"] and self.constraints["forbid"].intersection(tag_tags):
                scores[tag_name] = -float("inf")
                continue

            # Phase 1: Check qualification — does the entity meet all thresholds?
            deficits = []
            threshold_sum = 0.0
            for dim, _weight in self.weights.items():
                entity_val = entity_profile.get(dim, 0.0)
                threshold = tag_reqs.get(dim, 0.0)
                threshold_sum += threshold * weight
                delta = entity_val - threshold
                if delta < -0.05:  # Tolerance band for minor shortfalls
                    deficits.append((dim, delta, weight))

            # Phase 2: Score
            if not deficits:
                # Entity qualifies for this tag. Score = tag's threshold sum
                # (higher-bar tags get higher scores, so CANON_PROMOTE > STAGING > UNCONFIRMED)
                s = threshold_sum
            else:
                # Entity doesn't qualify. Score = threshold sum minus weighted penalty.
                penalty = sum(abs(d) * w * 3.0 for _, d, w in deficits)
                s = threshold_sum - penalty

            # Apply custom rules
            for rule in self.custom_rules:
                s = rule(tag_name, s, tag_reqs, entity_profile)

            scores[tag_name] = round(s, 4)

        return scores

    def recommend_certainty(
        self,
        entity_profile: Dict[str, float],
        entity_name: str = "<unnamed>",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Recommend a certainty tag for an entity based on its readiness profile.

        Returns a structured recommendation with confidence score, explanation,
        alternatives, and a full audit entry.
        """
        scores = self.score_tags(entity_profile)
        ranked = sorted(scores.items(), key=lambda x: -x[1])

        # Filter out excluded tags
        valid = [(tag, score) for tag, score in ranked if score > -float("inf")]

        if not valid:
            result = self._build_result(
                entity_name, None, 0.0, entity_profile, scores, ranked,
                "No certainty tag meets all constraints.", context
            )
            return result

        best_tag, best_score = valid[0]
        confidence = self._calculate_confidence(valid)
        explanation = self._build_explanation(entity_name, best_tag, best_score,
                                              entity_profile, valid, context)

        result = self._build_result(
            entity_name, best_tag, confidence, entity_profile, scores,
            ranked, explanation, context
        )
        self.audit_log.append(result["audit_entry"])
        return result

    def _calculate_confidence(self, valid_ranked: List[tuple]) -> float:
        """
        Confidence = normalized gap between #1 and #2.

        Adapted from HDE++._calculate_confidence. The wider the gap between
        the best tag and the next-best, the more confident we are.
        """
        if len(valid_ranked) < 2:
            return 0.5  # Only one option — moderate confidence by default
        best_score = valid_ranked[0][1]
        second_score = valid_ranked[1][1]
        if best_score <= 0:
            return 0.1  # Even the best is a poor fit
        delta = best_score - second_score
        confidence = min(1.0, max(0.05, delta / (abs(best_score) + 1e-6)))
        return round(confidence, 2)

    def _build_explanation(
        self,
        entity_name: str,
        best_tag: str,
        best_score: float,
        entity_profile: Dict[str, float],
        valid_ranked: list,
        context: Optional[dict],
    ) -> str:
        """Generate human-readable explanation for the recommendation."""
        parts = [f"Recommending '{best_tag}' for '{entity_name}' (score: {best_score:.2f})."]

        # Explain dimension contributions
        tag_reqs = self.tag_profiles[best_tag]
        strengths = []
        gaps = []
        for dim, _weight in self.weights.items():
            entity_val = entity_profile.get(dim, 0.0)
            threshold = tag_reqs.get(dim, 0.0)
            delta = entity_val - threshold
            if delta >= 0.1:
                strengths.append(f"{dim} ({entity_val:.2f} ≥ {threshold:.2f})")
            elif delta < -0.05:
                gaps.append(f"{dim} ({entity_val:.2f} < {threshold:.2f})")

        if strengths:
            parts.append(f"Strengths: {', '.join(strengths)}.")
        if gaps:
            parts.append(f"Gaps: {', '.join(gaps)}.")

        # Note alternatives
        if len(valid_ranked) > 1:
            alt_tag, alt_score = valid_ranked[1]
            delta = best_score - alt_score
            if delta < 1.0:
                parts.append(
                    f"Close alternative: '{alt_tag}' (score: {alt_score:.2f}, "
                    f"Δ={delta:.2f}). Consider reviewing if the gap is narrow."
                )

        # Constraint notes
        if self.constraints["require"]:
            parts.append(f"Required tags: {sorted(self.constraints['require'])}.")
        if self.constraints["forbid"]:
            parts.append(f"Excluded tags: {sorted(self.constraints['forbid'])}.")

        return " ".join(parts)

    def _build_result(
        self,
        entity_name: str,
        tag: Optional[str],
        confidence: float,
        entity_profile: Dict[str, float],
        scores: Dict[str, float],
        ranked: list,
        explanation: str,
        context: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Build the full recommendation result with audit entry."""
        # Top 3 alternatives (excluding -inf)
        alternatives = [
            {"tag": t, "score": round(s, 4)}
            for t, s in ranked[1:4]
            if s > -float("inf")
        ]

        audit_entry = {
            "timestamp": (context.get("timestamp") if isinstance(context, dict) and context.get("timestamp") else datetime.now(timezone.utc).isoformat()),
            "timestamp_source": (context.get("timestamp_source") if isinstance(context, dict) and context.get("timestamp_source") else "WALL_CLOCK_UTC"),
            "entity_name": entity_name,
            "recommended_tag": tag,
            "confidence": confidence,
            "confidence_kind": "HEURISTIC_GAP",
            "calibration_ref": "HDE_GAP_HEURISTIC_V1",
            "uncertainty_band": ("LOW" if confidence >= 0.75 else ("MED" if confidence >= 0.5 else "HIGH")),
            "entity_profile": entity_profile,
            "all_scores": {k: round(v, 4) for k, v in scores.items() if v > -float("inf")},
            "constraints": {
                "require": sorted(self.constraints["require"]),
                "forbid": sorted(self.constraints["forbid"]),
            },
            "context": context,
        }

        return {
            "recommended_tag": tag,
            "confidence": confidence,
            "confidence_kind": "HEURISTIC_GAP",
            "calibration_ref": "HDE_GAP_HEURISTIC_V1",
            "uncertainty_band": ("LOW" if confidence >= 0.75 else ("MED" if confidence >= 0.5 else "HIGH")),
            "explanation": explanation,
            "alternatives": alternatives,
            "constraints_applied": {
                "require": sorted(self.constraints["require"]),
                "forbid": sorted(self.constraints["forbid"]),
            },
            "audit_entry": audit_entry,
        }

    def get_audit_log(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Return last N audit entries."""
        return self.audit_log[-last_n:]


# ---------------------------------------------------------------------------
# Convenience: standalone recommendation from validation findings
# ---------------------------------------------------------------------------

def recommend_from_validation(
    data: dict,
    validation_findings: list[dict],
    layer: str,
    entity_type: str,
    entity_name: str = "<unnamed>",
    required_fields_total: Optional[int] = None,
    has_conflicts: bool = False,
    conflict_count: int = 0,
    user_reviewed: bool = False,
    origin_is_simulation: bool = False,
) -> Dict[str, Any]:
    """
    One-shot convenience function: takes entity data + validation findings,
    returns a certainty tag recommendation with confidence and explanation.
    """
    profile = build_entity_profile(
        data, validation_findings, layer, entity_type,
        required_fields_total=required_fields_total,
        has_conflicts=has_conflicts,
        conflict_count=conflict_count,
        user_reviewed=user_reviewed,
        origin_is_simulation=origin_is_simulation,
    )

    advisor = ReconciliationAdvisor()

    # Apply layer-appropriate constraints
    if entity_type in ("location",) and layer == "L2":
        advisor.set_constraints(require=["map"])
    if entity_type in ("polity", "species", "character", "ship", "mechanic"):
        advisor.set_constraints(forbid=["map"])  # Non-location entities shouldn't get map tags

    return advisor.recommend_certainty(profile, entity_name=entity_name)


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Reconciliation Advisor — certainty tag recommendation engine"
    )
    parser.add_argument("--profile", type=str, required=True,
                        help="JSON entity readiness profile (as string)")
    parser.add_argument("--name", type=str, default="<unnamed>",
                        help="Entity name for reporting")
    args = parser.parse_args()

    profile = json.loads(args.profile)
    advisor = ReconciliationAdvisor()
    result = advisor.recommend_certainty(profile, entity_name=args.name)
    print(json.dumps(result, indent=2, default=str))
