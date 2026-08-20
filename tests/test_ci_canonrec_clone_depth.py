"""CI must clone CanonRec deep enough to evaluate ACE manifest freshness.

The defect
----------
ACE capability manifests declare ``refresh_on_paths``: the files whose change
would actually alter a capability's behaviour. ``_refresh_paths_unchanged()``
decides staleness by running::

    git diff --name-only <pinned_sha>..<observed_head> -- <refresh_on_paths>

and it fails closed on purpose — an unreadable range returns False, so the
caller raises. That asymmetry is correct: freshness is a safety property and
uncertainty must not read as fresh.

But it interacts badly with ``actions/checkout``. Given a ``ref:``, checkout
defaults to ``fetch-depth: 1``. The pinned commit is then simply absent from the
clone, the diff errors, and *every* manifest whose pin trails the registry reads
as stale regardless of what changed. The rule cannot ever return "fresh" in CI.

On 2026-08-20 that meant 7 CanonRec commits — **none** of which touched either
declared refresh path — failed 5 tests across ``test_aurora_ace.py`` and
``test_aurora_ace_character_materialization.py``. Aurora CI had been red on main
for 10 consecutive runs. Locally the same suite passed, because a developer
clone has full history and the diff resolves. That divergence is what made it
survive: the failure was invisible everywhere anyone would have looked for it.

Why a test rather than a comment
--------------------------------
The failure mode is silent and inverted. A shallow clone does not announce
itself; it just makes a safety check unconditionally strict, which reads as the
check working. Someone trimming CI time would reasonably drop ``fetch-depth: 0``
and see tests still "correctly" failing on stale pins. Only a test that names
the coupling prevents that.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

CANONREC = "AUo959/CanonRec"

pytestmark = pytest.mark.skipif(
    not WORKFLOWS.is_dir(), reason="workflows directory not present"
)


def canonrec_checkout_steps() -> list[tuple[str, str, dict]]:
    """Every actions/checkout step in any workflow that provisions CanonRec."""
    found: list[tuple[str, str, dict]] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:  # pragma: no cover - a malformed workflow is its own bug
            continue
        if not isinstance(doc, dict):
            continue
        for job_name, job in (doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                using = str(step.get("uses") or "")
                params = step.get("with") or {}
                if not using.startswith("actions/checkout"):
                    continue
                if str(params.get("repository") or "") != CANONREC:
                    continue
                found.append((path.name, str(job_name), params))
    return found


def test_canonrec_is_provisioned_somewhere():
    """Guard the guard: if nothing matches, the assertions below are vacuous.

    This is the ``PASS`` on zero coverage failure the governance scanners were
    just fixed for. A test that silently checks nothing is worse than no test.
    """
    assert canonrec_checkout_steps(), (
        "No CanonRec checkout step found in any workflow. Either provisioning "
        "moved, or this test's matcher is stale — both need a look."
    )


def test_every_canonrec_checkout_has_full_history():
    """fetch-depth: 0, or refresh_on_paths cannot be evaluated at all."""
    shallow = [
        f"{workflow}:{job}"
        for workflow, job, params in canonrec_checkout_steps()
        if str(params.get("fetch-depth")) != "0"
    ]
    assert not shallow, (
        "CanonRec is cloned without full history in:\n  "
        + "\n  ".join(shallow)
        + "\n\nACE staleness is decided by diffing pinned_sha..observed_head over "
          "each manifest's refresh_on_paths. A shallow clone lacks the pinned "
          "commit, so that diff errors and _refresh_paths_unchanged() fails "
          "closed — making every trailing pin look stale no matter what changed. "
          "Set `fetch-depth: 0` on the checkout step."
    )


def test_pinned_ref_checkouts_are_the_case_that_needs_depth():
    """Documents *why* depth matters here: these steps check out a bare SHA.

    A branch-ref checkout would at least contain recent history. Pinning an
    explicit commit is what makes depth-1 lose the range endpoint.
    """
    for workflow, job, params in canonrec_checkout_steps():
        assert params.get("ref"), (
            f"{workflow}:{job} checks out CanonRec without a pinned ref; the "
            f"registry-pinned provisioning contract assumed by ACE freshness "
            f"no longer holds."
        )
