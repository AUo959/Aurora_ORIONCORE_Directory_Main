from unittest import TestCase

import pytest

from tools import canon_ops_reconciliation as review


CHECK = TestCase()


class FixtureAdvisor:
    def __init__(self):
        """Stand in for the pinned advisor behind the staging-only runner."""
        self.forbidden = []

    def set_constraints(self, *, forbid):
        self.forbidden = forbid

    def recommend_certainty(self, profile, *, entity_name):
        return {
            "recommended_tag": "STAGING" if "promotion" in self.forbidden else "CANON_PROMOTE",
            "confidence": profile["readiness"],
            "confidence_kind": "HEURISTIC_GAP",
            "calibration_ref": "fixture-reference",
            "uncertainty_band": "HIGH",
            "explanation": entity_name,
            "audit_entry": {"timestamp": "ignored-runtime-time"},
        }


def test_advisor_disables_promotion_and_keeps_deterministic_fields():
    assess = review.advisor_runner(FixtureAdvisor, ["readiness"])
    result = assess({"readiness": 0.75}, "target")
    CHECK.assertEqual(result["recommended_tag"], "STAGING")
    CHECK.assertEqual(result["explanation"], "target")
    CHECK.assertEqual(result["canonrec_commit"], review.CONTRACT_COMMIT)
    CHECK.assertNotIn("audit_entry", result)
    CHECK.assertEqual(result, assess({"readiness": 0.75}, "target"))


def test_advisor_rejects_invalid_readiness_profiles():
    assess = review.advisor_runner(FixtureAdvisor, ["readiness"])
    for invalid in ({"readiness": 3}, {}, {"readiness": 0.9, "unrelated": 1}):
        with pytest.raises(review.AdvisoryError, match="entity_profile"):
            assess(invalid, "target")
