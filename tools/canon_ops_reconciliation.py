"""Re-evaluate pinned CanonRec readiness profiles without permitting promotion."""

from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from jsonschema import Draft202012Validator

if __package__:
    from .canon_ops_query import CONTRACT_COMMIT, CanonRec
else:
    from canon_ops_query import CONTRACT_COMMIT, CanonRec


ADVISOR_FILE = "aurora-canon-reconciler/scripts/reconciliation_advisor.py"
Advisory = Callable[[dict, str], dict]


class AdvisoryError(ValueError):
    """The pinned reviewer cannot assess the supplied reconciliation evidence."""


def _profile_validator(dimensions: list[str]) -> Draft202012Validator:
    metric = {"type": "number", "minimum": 0, "maximum": 1}
    return Draft202012Validator({
        "type": "object",
        "required": dimensions,
        "properties": {dimension: metric for dimension in dimensions},
        "additionalProperties": False,
    })


def advisor_runner(advisor_class, dimensions: list[str]) -> Advisory:
    """Construct the staging-only invocation and stable output projection."""
    validator = _profile_validator(dimensions)

    def assess(profile: dict, entity_name: str) -> dict:
        error = next(validator.iter_errors(profile), None)
        if error:
            raise AdvisoryError(f"/gate_receipts/final_reconciliation/entity_profile: {error.message}")
        advisor = advisor_class()
        advisor.set_constraints(forbid=["promotion", "map"])
        output = advisor.recommend_certainty(profile, entity_name=entity_name)
        if output["recommended_tag"] in {"CANON", "CANON_PROMOTE"}:
            raise AdvisoryError("CanonRec returned a promotion recommendation in staging mode")
        evidence = {
            name: output[name] for name in (
                "recommended_tag", "confidence", "confidence_kind", "calibration_ref",
                "uncertainty_band", "explanation",
            )
        }
        return {"canonrec_commit": CONTRACT_COMMIT, "advisor_path": ADVISOR_FILE, **evidence}

    return assess


def pinned_advisor(repo: CanonRec) -> Advisory:
    """Load the advisor from the verified CanonRec contract commit."""
    with TemporaryDirectory(prefix="canon-ops-advisor-") as directory:
        script = Path(directory) / "reconciliation_advisor.py"
        script.write_bytes(repo.blob(f"{CONTRACT_COMMIT}:{ADVISOR_FILE}"))
        # Run only the project code at the fixed, reviewed Git object.
        module = runpy.run_path(str(script))
    return advisor_runner(module["ReconciliationAdvisor"], list(module["DEFAULT_WEIGHTS"]))


def assess_gate(request: dict, gate: dict, advisor: Advisory | None) -> dict | None:
    """Use only readiness profiles carried by an already verified gate."""
    if "entity_profile" not in gate:
        return None
    if advisor is None:
        raise AdvisoryError("A pinned advisor is required to reassess this receipt")
    target_description = ", ".join(target["record_id"] for target in request["targets"])
    return advisor(gate["entity_profile"], target_description)
