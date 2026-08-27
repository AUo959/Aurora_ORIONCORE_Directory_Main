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

#: Repositories that back a capability with ``current_head_required: true``.
#: Only these need full history — their manifests are the ones whose freshness
#: is decided by a git range. Keep this list derived from the manifests rather
#: than guessed: a capability flipping to current_head_required silently adds a
#: repository here, and test_backing_repositories_are_covered() catches that.
PINNED_REPOS = {
    "AUo959/CanonRec": "CanonRec",
    "AUo959/aurora-cloudbank-symbolic": "aurora-cloudbank-symbolic-main",
}

CANONREC = "AUo959/CanonRec"

pytestmark = pytest.mark.skipif(
    not WORKFLOWS.is_dir(), reason="workflows directory not present"
)


def backing_repositories_needing_head() -> set[str]:
    """Repositories named by manifests with current_head_required: true.

    Read from the manifests so the list cannot drift silently.
    """
    import json

    # Read EVERY manifest file, not just specialists.jsonl. The first version of
    # this helper read only specialists.jsonl and so never saw
    # ace.capability.gumas.naming.resolve, which lives in core.jsonl and is the
    # CloudBank-backed capability this test most needed to cover — it passed by
    # checking nothing, which is the failure this module's docstring warns about.
    manifest_dir = REPO_ROOT / "catalog" / "ace" / "capability_manifests"
    manifest_files = sorted(manifest_dir.glob("*.jsonl"))
    if not manifest_files:
        pytest.skip("capability manifests not present")
    repos: set[str] = set()
    for path in manifest_files:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            manifest = record.get("manifest", record)
            if (manifest.get("freshness") or {}).get("current_head_required"):
                repos.add(str((manifest.get("tool") or {}).get("repository") or ""))
    return {r for r in repos if r and r != "root"}


def test_backing_repositories_are_covered():
    """Every current_head_required repository must appear in PINNED_REPOS.

    If a capability starts requiring current head for a repository CI clones
    shallowly, the freshness rule breaks for it exactly the way it broke for
    CanonRec — silently, and only in CI.
    """
    covered = set(PINNED_REPOS.values())
    missing = backing_repositories_needing_head() - covered
    assert not missing, (
        f"capability manifests require current head for {sorted(missing)}, which "
        f"PINNED_REPOS does not cover. Add the repository and ensure its CI "
        f"checkout sets fetch-depth: 0."
    )


def canonrec_checkout_steps() -> list[tuple[str, str, dict]]:
    """Every actions/checkout step provisioning a current-head-backed repo.

    Covers both CanonRec and CloudBank: the depth requirement follows from
    current_head_required, not from which repository it happens to be.
    """
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
                if str(params.get("repository") or "") not in PINNED_REPOS:
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
