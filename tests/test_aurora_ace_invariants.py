"""The ACE core invariants (spec §4) must hold in code, not only in prose.

Why this file is separate from test_aurora_ace.py
-------------------------------------------------
The existing suite proves the engine is *deterministic and replayable* — same
inputs, same digests. That is necessary and it is not the same thing as proving
the engine is *correct about canon*. These tests assert the normative invariants
the spec declares with MUST, because those invariants are the reason ACE exists:

  §4.1 completion      — every valid inquiry ends in a determination or a precise
                         TRUE_CONFLICT; operational failure is reported as
                         EXECUTION_BLOCKED, never disguised as uncertainty.
  §4.2 no-parking      — "no prior record exists" and its siblings MUST NOT
                         produce a final STAGING / UNKNOWN / owner-decision.
  §4.3 specialist-first— every returned field MUST identify its producer.
  §4.5 canon-at-commit — GENERATED_CANON requires a real commit; and lacking
                         materialization authority MUST NOT downgrade content
                         to STAGING.

§4.2 is the one that matters most to this project. The failure it forbids —
parking a routine decision on the owner — is a documented, repeated failure mode
here, and until now nothing but discipline prevented it. A sentence in a spec is
not an enforcement mechanism.

Note the deliberate asymmetry in `test_determination_vocabulary_is_not_exceeded`
and `test_reachable_determination_states_are_recorded`: the first forbids the
code from inventing states the spec does not define, the second records how many
of the spec's states the engine can currently reach. v0.1 reaches exactly one.
That is a real limitation, tracked with a number rather than left implicit.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import build_capability_index, compile_character_query  # noqa: E402
from ace.engine import resolve_character_query  # noqa: E402

SPEC = REPO_ROOT / "docs" / "AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md"

#: Values that mean "somebody else decides later". §4.2 forbids these as FINAL
#: states. They remain legal inside an execution transaction.
PARKING_SENTINELS = {
    "STAGING", "UNKNOWN", "TBD", "TODO", "PENDING", "PENDING_OWNER",
    "OWNER_DECISION", "AWAITING_OWNER", "DEFERRED", "UNRESOLVED", "NEEDS_OWNER",
}

LIVE = os.environ.get("AURORA_ACE_LIVE_TESTS") == "1"
live_only = pytest.mark.skipif(
    not LIVE, reason="set AURORA_ACE_LIVE_TESTS=1 to run the live vertical slice"
)


def character_context() -> dict[str, object]:
    """A context whose subject has NO prior record — the §4.2 trigger case."""
    return {
        "role": "logistics_officer",
        "faction_id": "org_galactic_union",
        "faction_name": "Galactic Union",
        "location_type": "judicator_class_vessel",
        "observed_behavior": ["coordinated emergency supply allocation"],
        "contextual_refs": ["scenario.ace.invariants.001"],
    }


@pytest.fixture(scope="module")
def determination(tmp_path_factory) -> dict:
    if not LIVE:
        pytest.skip("live resolve required")
    query = compile_character_query(
        "What is this character's name and background?",
        character_context(),
        seed=808,
    )
    out = tmp_path_factory.mktemp("ace-invariants") / "run"
    return resolve_character_query(query, out)


def spec_determination_vocabulary() -> set[str]:
    """Read the determination vocabulary out of the spec, not a copy of it."""
    if not SPEC.is_file():
        pytest.skip("ACE spec not present")
    body = SPEC.read_text(encoding="utf-8")
    section = body.split("## 7. Determination vocabulary", 1)
    if len(section) < 2:
        pytest.fail("Spec §7 'Determination vocabulary' not found — has it moved?")
    return set(re.findall(r"^### `([A-Z_]+)`", section[1], re.MULTILINE))


# --- §4.1 completion ------------------------------------------------------

def test_determination_vocabulary_is_defined_in_the_spec():
    """The vocabulary must be discoverable from the spec, since tests read it."""
    vocab = spec_determination_vocabulary()
    assert {"RETRIEVED_CANON", "DERIVED_CANON", "GENERATED_CANON",
            "CANON_REVISION", "TRUE_CONFLICT", "EXECUTION_BLOCKED"} <= vocab


@live_only
def test_determination_vocabulary_is_not_exceeded(determination):
    """§4.1 — the engine MUST NOT invent a terminal state the spec does not define."""
    assert determination["status"] in spec_determination_vocabulary(), (
        f"status {determination['status']!r} is not in the spec's determination "
        f"vocabulary. A new terminal state needs a spec change, not just code."
    )


@live_only
def test_execution_blocked_is_operational_not_epistemic(determination):
    """§4.1 — EXECUTION_BLOCKED reports an OPERATIONAL failure.

    It must never be a polite way of saying "we weren't sure". If the engine
    blocks, it owes a concrete blocker with a recovery action.
    """
    if determination["status"] != "EXECUTION_BLOCKED":
        pytest.skip("run did not block")
    blockers = determination.get("blockers") or []
    assert blockers, "EXECUTION_BLOCKED with no blocker is indistinguishable from parking."
    for blocker in blockers:
        assert blocker.get("kind"), f"blocker lacks a kind: {blocker}"
        assert blocker.get("reason"), f"blocker lacks a reason: {blocker}"
        assert blocker.get("recovery_action"), (
            f"blocker {blocker.get('blocker_id')!r} has no recovery_action — a block "
            f"the caller cannot act on is a dead end, which §4.1 forbids."
        )


# --- §4.2 no-parking ------------------------------------------------------

@live_only
def test_absent_prior_record_does_not_park(determination):
    """§4.2 — 'no prior record exists' MUST NOT yield a parked final state.

    This is the invariant the whole engine is built around: absence of a record
    is an instruction to complete the world, not a reason to stop.
    """
    assert determination["answer"]["no_prior_record"] is True, (
        "fixture no longer exercises the unobserved-subject path"
    )
    assert determination["status"] not in PARKING_SENTINELS, (
        f"status {determination['status']!r} parks a subject that merely had no "
        f"prior record — exactly what §4.2 forbids."
    )


@live_only
def test_no_field_value_is_a_parking_sentinel(determination):
    """§4.2 — a completed answer must not smuggle parking into its field values."""
    parked = []
    for field in determination["answer"]["fields"]:
        value = field.get("value")
        if isinstance(value, str) and value.strip().upper() in PARKING_SENTINELS:
            parked.append(f"{field['field_path']} = {value!r}")
    assert not parked, (
        "Fields parked rather than determined:\n  " + "\n  ".join(parked)
    )


@live_only
def test_no_coverage_requirement_defers_to_the_owner(determination):
    """§4.2/§4.4 — the owner is not the routine value generator.

    A coverage requirement resolved by "ask the owner" is the failure mode in
    prose form; it must not appear in a completed answer contract.
    """
    contract = determination["answer_contract"]
    offenders = []
    for requirement in contract.get("coverage") or []:
        status = str(requirement.get("status", "")).upper()
        reason = str(requirement.get("reason", "")).lower()
        if status in PARKING_SENTINELS:
            offenders.append(f"{requirement['requirement_id']}: status={status}")
        elif re.search(r"\bowner (?:must|should|to) (?:decide|choose|select|provide)",
                       reason):
            offenders.append(f"{requirement['requirement_id']}: reason defers to owner")
    assert not offenders, (
        "Coverage requirements deferring to the owner:\n  " + "\n  ".join(offenders)
    )


# --- §4.3 specialist-first ------------------------------------------------

@live_only
def test_every_field_identifies_its_producer(determination):
    """§4.3 — 'Every returned field MUST identify its producer.'"""
    unattributed = [
        field["field_path"]
        for field in determination["answer"]["fields"]
        if not field.get("producer_refs") or not field.get("origin")
    ]
    assert not unattributed, (
        "Fields with no producer or origin: " + ", ".join(unattributed)
    )


@live_only
def test_declared_producers_exist_in_the_capability_index(determination):
    """A field may not credit a capability the engine does not actually register.

    Catches drift between what the answer claims produced a value and what the
    capability index knows about — the sort of gap that makes provenance
    decorative rather than checkable.
    """
    index = build_capability_index()
    known = {
        entry["capability_id"]
        for entry in index.get("capabilities", index.get("active", []))
        if isinstance(entry, dict) and entry.get("capability_id")
    } or set(index.get("active", []))
    unknown = set()
    for field in determination["answer"]["fields"]:
        for producer in field.get("producer_refs") or []:
            if producer.startswith("ace.capability.") and producer not in known:
                unknown.add(producer)
    assert not unknown, (
        f"Fields credit capabilities absent from the index: {sorted(unknown)}"
    )


# --- §4.5 canon-at-commit -------------------------------------------------

@live_only
def test_generated_canon_requires_a_real_commit(determination):
    """§4.5 — MUST NOT claim GENERATED_CANON/CANON_REVISION without a commit."""
    materialization = determination.get("materialization") or {}
    if determination["status"] in {"GENERATED_CANON", "CANON_REVISION"}:
        commit = materialization.get("commit_sha")
        assert commit and re.fullmatch(r"[0-9a-f]{7,40}", str(commit)), (
            f"status {determination['status']} without an authoritative commit_sha "
            f"({commit!r}) — canon is made at commit, not at generation."
        )


@live_only
def test_missing_authority_blocks_without_downgrading(determination):
    """§4.5 — lacking materialization authority MUST NOT downgrade to STAGING.

    The engine must hand back a COMPLETE, VALIDATED, commit-ready packet and say
    "I could not persist this", rather than quietly demoting good content because
    a persistence gate has not run. This is the invariant that keeps a permissions
    boundary from silently becoming an epistemic one.
    """
    materialization = determination.get("materialization") or {}
    if materialization.get("commit_sha"):
        pytest.skip("this run had materialization authority")
    assert determination["status"] == "EXECUTION_BLOCKED"
    assert materialization.get("status") == "commit_ready", (
        f"materialization status {materialization.get('status')!r} — an unpersisted "
        f"packet must still be commit_ready, not parked."
    )
    assert determination["answer_contract"]["overall_status"] == "complete", (
        "answer contract was downgraded because persistence had not run"
    )
    assert determination["validation"]["overall_status"] == "pass", (
        "validation was downgraded because persistence had not run"
    )
    assert materialization.get("target_repository"), "no declared target repository"
    assert materialization.get("target_paths"), "no declared target paths"


# --- known-limitation ledger ----------------------------------------------

@live_only
def test_reachable_determination_states_are_recorded():
    """Records how much of the spec's vocabulary the engine can actually reach.

    Not a pass/fail on quality — a tracked number, the same device used for
    location-subtype drift. v0.1 reaches exactly ONE of six terminal states
    (EXECUTION_BLOCKED), because materialization is unimplemented. The engine
    therefore cannot yet satisfy §4.1 in the affirmative: it never returns a
    canonical determination.

    When v0.2 lands materialization this test SHOULD fail, and the fix is to
    raise the count deliberately — which forces someone to notice that ACE
    started making canon.
    """
    source = (REPO_ROOT / "tools" / "ace").rglob("*.py")
    emitted = set()
    for path in source:
        body = path.read_text(encoding="utf-8")
        for term in spec_determination_vocabulary():
            if re.search(rf'["\']{term}["\']', body):
                emitted.add(term)
    assert emitted == {"EXECUTION_BLOCKED"}, (
        f"Reachable determination states changed to {sorted(emitted)}. If "
        f"materialization has landed, update this expectation deliberately and "
        f"note it in the spec's implementation status."
    )
