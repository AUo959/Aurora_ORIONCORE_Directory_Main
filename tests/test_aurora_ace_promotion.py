"""Review handoff tests; E2E reuses an existing world without changing it."""

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ace.core import ACEError, CANONREC_REL  # noqa: E402
from ace.promotion import (  # noqa: E402
    _assert_packet_integrity,
    _clone,
    _separate_output,
    prepare,
    verify,
)  # noqa: E402
from ace.sandbox import World, git  # noqa: E402
from aurora_ace_sandbox import provision  # noqa: E402


def test_protected_and_existing_destinations(tmp_path):
    protected = tmp_path / "source"
    protected.mkdir()
    for output in (protected, protected / "review", tmp_path):
        with pytest.raises(ACEError):
            _separate_output(output, [protected])
    link = tmp_path / "link"
    link.symlink_to(protected, target_is_directory=True)
    with pytest.raises(ACEError):
        _separate_output(link / "review", [protected])


@pytest.fixture(scope="module")
def review(tmp_path_factory):
    if os.environ.get("ACE_PROMOTION_E2E") != "1":
        pytest.skip("Set ACE_PROMOTION_E2E=1 with a persistent sandbox creation")
    temp = tmp_path_factory.mktemp("promotion")
    canonical = Path(os.environ.get("ACE_SANDBOX_REPOSITORIES_ROOT", str(ROOT)))
    world = temp / "world"
    provision(world, ROOT, canonical, Path(sys.executable))
    request = "promotion-test-create"
    World(world).character(
        "Create a new L2 expedition archivist.",
        {
            "role": "expedition_archivist",
            "faction_id": "galactic_union",
            "location_type": "archive_outpost",
        },
        request,
        "create",
    )
    target_root = temp / "target"
    source = canonical / CANONREC_REL
    _clone(source, target_root / CANONREC_REL, git(source, "rev-parse", "HEAD"))
    output = temp / "review"
    result = prepare(world, request, target_root, output, root=ROOT)
    assert result["status"] == "review_ready", result["blockers"]
    return world, request, target_root, output, result


def test_native_patch_and_recorded_background(review, tmp_path):
    _, _, target_root, output, result = review
    assert verify(output)["artifacts_verified"]
    clone = tmp_path / "apply"
    _clone(target_root / CANONREC_REL, clone, result["target_baseline"])
    git(clone, "apply", "--check", str(output / "proposal.patch"))
    git(clone, "apply", str(output / "proposal.patch"))
    final = json.loads(
        (output / "packet/materialized_determination_receipt.json").read_text()
    )
    original = json.loads(
        (output / "source_materialized_determination.json").read_text()
    )
    before = {f["field_path"]: f["value"] for f in original["answer"]["fields"]}
    after = {f["field_path"]: f["value"] for f in final["answer"]["fields"]}
    assert before == after
    for path in final["materialization"]["target_paths"]:
        assert (clone / path).read_bytes() == (
            output / "rehearsal" / CANONREC_REL / path
        ).read_bytes()
    assert result["sources_unchanged"]
    assert not result["publication_performed"]


def test_duplicate_output_refused(review):
    world, request, target_root, output, _ = review
    with pytest.raises(ACEError, match="new directory"):
        prepare(world, request, target_root, output, root=ROOT)


def test_tampered_packet_refused(review, tmp_path):
    _, _, _, output, result = review
    packet = tmp_path / "packet"
    shutil.copytree(output / "packet", packet)
    original = json.loads((packet / "determination_receipt.json").read_text())
    candidate = packet / "candidate" / f"{result['entity_id']}.json"
    candidate.write_text(candidate.read_text().replace("Jorenon", "Altered"))
    with pytest.raises(ACEError, match="artifact changed"):
        _assert_packet_integrity(packet, result["entity_id"], original)


def test_tampered_review_refused(review, tmp_path):
    _, _, _, output, _ = review
    copied = tmp_path / "review"
    shutil.copytree(
        output, copied, ignore=shutil.ignore_patterns("rehearsal", "python-cache")
    )
    (copied / "proposal.patch").write_bytes(b"altered")
    with pytest.raises(ACEError, match="artifact changed"):
        verify(copied)


def test_advanced_target_and_identity_collision_block(review, tmp_path):
    world, request, target_root, output, result = review
    target = tmp_path / "target" / CANONREC_REL
    _clone(target_root / CANONREC_REL, target, result["target_baseline"])
    git(target, "apply", str(output / "proposal.patch"))
    git(target, "add", "canon/L2/entities")
    git(
        target,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@aurora.local",
        "commit",
        "-m",
        "Existing character",
    )
    blocked = prepare(
        world, request, tmp_path / "target", tmp_path / "blocked", root=ROOT
    )
    assert blocked["status"] == "blocked"
    assert blocked["checks"]["identity_discovery"]["direct_candidates"]
    assert any("baseline" in b for b in blocked["blockers"])
    assert "rehearsal_commit" not in blocked
    assert not (tmp_path / "blocked/proposal.patch").exists()


def test_dirty_target_refused(review, tmp_path):
    world, request, target_root, _, result = review
    target = tmp_path / "target" / CANONREC_REL
    _clone(target_root / CANONREC_REL, target, result["target_baseline"])
    (target / "unexpected.txt").write_text("uncommitted")
    with pytest.raises(ACEError, match="must be clean"):
        prepare(world, request, tmp_path / "target", tmp_path / "blocked", root=ROOT)


def test_review_verification_refuses_stale_target(review, tmp_path):
    _, _, target_root, output, result = review
    target = tmp_path / "target" / CANONREC_REL
    _clone(target_root / CANONREC_REL, target, result["target_baseline"])
    copied = tmp_path / "review"
    shutil.copytree(
        output, copied, ignore=shutil.ignore_patterns("rehearsal", "python-cache")
    )
    data = json.loads((copied / "promotion_review.json").read_text())
    data["target_root"] = str(tmp_path / "target")
    (copied / "promotion_review.json").write_text(json.dumps(data))
    assert verify(copied)["target_baseline_current"]
    git(
        target,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@aurora.local",
        "commit",
        "--allow-empty",
        "-m",
        "Advance target",
    )
    with pytest.raises(ACEError, match="Target CanonRec changed"):
        verify(copied)
