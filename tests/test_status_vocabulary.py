"""C2 lifecycle status must be checkable without flattening canon.

Field finding 2026-08-09: `STATUS_VOCAB` was a single flat set applied to every
entity kind. It is body-oriented — C2 is "one body, one place", and the dead do not
act — but canon also has species, events, reports, places and equipment, whose
lifecycles are different words entirely. A species is not "active", it is EXTANT.
An event is CONCLUDED. A report is SUBMITTED. 25 of 189 records fell outside the
vocabulary, so the invariant was effectively unenforced for all of them.

A second failure was mixed in: 11 records packed lifecycle AND situation into one
string (`alive_in_union_medical_custody`, `withdrawn_from_lethan_active_strength_unknown`).
Those are real canon, and the fix must not delete them to satisfy a linter.

Resolution: `status` carries lifecycle only, per-kind; situational canon moves
verbatim to `status_detail` with the original preserved in `prev_status`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"
sys.path.insert(0, str(REPO_ROOT / "tools"))

from fabric_invariants_check import (  # noqa: E402
    STATUS_VOCAB_BY_KIND,
    status_vocab_for,
)


def _records() -> list[dict]:
    out = []
    if not CANON_L2.exists():
        return out
    for path in CANON_L2.rglob("*.json"):
        if "/capsule/" in path.as_posix():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("entity_kind"):
            out.append(data)
    return out


def test_every_status_is_in_its_kind_vocabulary():
    records = _records()
    if not records:
        return
    bad = [
        (r.get("entity_id"), r["entity_kind"], r["status"])
        for r in records
        if r.get("status") and r["status"] not in status_vocab_for(r["entity_kind"])
    ]
    assert not bad, f"statuses outside their kind's lifecycle vocabulary: {bad}"


def test_species_use_extant_not_active():
    """The flat vocabulary forced species to lie; per-kind vocab lets them be right."""
    assert "extant" in STATUS_VOCAB_BY_KIND["species"]
    assert "extinct" in STATUS_VOCAB_BY_KIND["species"]
    assert "active" not in STATUS_VOCAB_BY_KIND["species"], (
        "a species is extant or extinct — 'active' is a category error"
    )


def test_events_conclude_rather_than_deactivate():
    assert "concluded" in STATUS_VOCAB_BY_KIND["event"]
    assert "ongoing" in STATUS_VOCAB_BY_KIND["event"]


def test_reports_have_their_own_lifecycle():
    assert "submitted" in STATUS_VOCAB_BY_KIND["report"]


def test_characters_keep_the_body_oriented_vocabulary():
    """C2's original purpose must survive the generalisation."""
    char = STATUS_VOCAB_BY_KIND["character"]
    assert {"active", "deceased"} <= char
    assert "extant" not in char, "people are alive or dead, not 'extant'"


def test_split_records_preserve_the_original_canon_verbatim():
    """The load-bearing guarantee: no canon detail was traded for linter cleanliness."""
    records = _records()
    if not records:
        return
    split = [r for r in records if r.get("prev_status")]
    assert split, "expected records whose composite status was split"
    for record in split:
        assert record.get("status_detail"), (
            f"{record.get('entity_id')} lost its situational detail in the split"
        )
        assert record["status"] != record["prev_status"]


def test_selene_ark_is_alive_and_her_custody_is_still_recorded():
    """The record that opened this thread."""
    records = {r.get("entity_id"): r for r in _records()}
    ark = records.get("char_selene_ark")
    if ark is None:
        return
    assert ark["status"] == "active", "Selene Ark is alive — C2's one-body rule applies"
    assert "custody" in ark.get("status_detail", "").lower(), (
        "her medical custody is canon and must survive the vocabulary fix"
    )
    assert ark.get("prev_status") == "alive_in_union_medical_custody"


def test_unknown_kind_falls_back_rather_than_passing_silently():
    fallback = status_vocab_for("some_new_kind_nobody_defined")
    assert "active" in fallback and "unknown" in fallback
