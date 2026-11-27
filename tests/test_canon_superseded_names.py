"""Conflict scans must read rename rulings, not just compare entity records.

The gap
-------
A conflict scan compares a candidate against existing ENTITY RECORDS. It never
reads the rulings that declare a name superseded, so a *rename* passes cleanly
while a duplicate string is caught.

On 2026-07-20 canon ruled ``"Galactic Security Bureau" -> canonical Union
Intelligence Bureau``. On 2026-07-21 ``char_sarina_vael`` was promoted as
"Director of the Galactic Security Bureau (GSB)" with a conflict scan recording
"zero name/office collisions". Both statements were true as written — no other
record used that string. The scan simply had not read the ruling issued the day
before, which is why that record's notes say "No GSB org record exists yet".

The precision that matters
--------------------------
A superseded name in an IDENTITY field is a finding; the same string in an
alias or a documented conflict block is CORRECT — that is canon recording its
own drift. ``char_zylox_rhaegos`` keeps "Zylox Verrin" among its aliases quite
deliberately, and a naive substring check would flag exactly the record that did
the right thing. These tests pin both directions, because a checker that punishes
good bookkeeping will be turned off.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"

pytestmark = pytest.mark.skipif(
    not CANON_L2.is_dir(), reason="CanonRec not checked out"
)


@pytest.fixture(scope="module")
def rulings():
    from canon_superseded_names import load_rulings
    return load_rulings()


# --- the index ------------------------------------------------------------

def test_known_rulings_are_indexed(rulings):
    """Both rulings in canon must be found."""
    pairs = {(r["superseded"], r["canonical"]) for r in rulings}
    assert ("Galactic Security Bureau", "Union Intelligence Bureau") in pairs
    assert ("Zylox Verrin", "Zylox Rhaegos") in pairs


def test_declarations_spanning_a_line_break_yield_clean_names(rulings):
    """Canon markdown wraps these declarations mid-sentence.

    Both real rulings straddle a hard line break. The failure this guards is
    subtler than "finds nothing": the pattern DOES match wrapped text, because
    `[^*]` matches newlines — it just captures 'Zylox\nRhaegos'. A canonical name
    carrying an embedded newline compares equal to nothing and would silently
    never match a record, so the checker would report zero findings and look
    healthy.

    Hence the parser normalises whitespace before matching, and this pins the
    property that actually matters: the captured names are clean.
    """
    from canon_superseded_names import RENAME
    wrapped = (
        'Superseded-draft notes (not canon): early surname "Zylox Verrin" → canonical **Zylox\n'
        'Rhaegos**; early agency name "Galactic Security Bureau" → canonical **Union Intelligence\n'
        'Bureau**.\n'
    )
    raw = [m.group(3) for m in RENAME.finditer(wrapped)]
    assert any("\n" in name for name in raw), "fixture no longer spans a break"

    clean = [m.group(3) for m in RENAME.finditer(" ".join(wrapped.split()))]
    assert clean == ["Zylox Rhaegos", "Union Intelligence Bureau"]
    assert all("\n" not in name for name in clean)

    # and the indexed rulings are clean for the same reason
    assert all("\n" not in r["canonical"] and "\n" not in r["superseded"] for r in rulings)


# --- the check ------------------------------------------------------------

def test_identity_field_use_is_a_violation():
    """The case that motivated this: a role asserting a superseded agency."""
    from canon_superseded_names import find_violations
    hits = {(v["entity_id"], v["field"]) for v in find_violations()}
    assert ("char_sarina_vael", "role") in hits


def test_aliases_preserving_a_superseded_name_are_not_violations():
    """char_zylox_rhaegos keeps "Zylox Verrin" as an alias, correctly.

    This is the false positive a naive substring check produces, and it would
    land on the record that documented its own rename properly.
    """
    from canon_superseded_names import find_violations, find_annotations
    assert "char_zylox_rhaegos" not in {v["entity_id"] for v in find_violations()}
    assert "char_zylox_rhaegos" in {a["entity_id"] for a in find_annotations()}


def test_documented_conflict_blocks_are_not_violations():
    """A record may discuss a superseded name at length without asserting it.

    char_sarina_vael carries an agency_name_conflict block that names both forms.
    Only its `role` should count — otherwise recording the conflict would itself
    become a second finding.
    """
    from canon_superseded_names import find_violations
    fields = {v["field"] for v in find_violations() if v["entity_id"] == "char_sarina_vael"}
    assert fields == {"role"}


def test_violations_carry_their_authority():
    """A finding must cite the ruling, or it cannot be acted on."""
    from canon_superseded_names import find_violations
    for v in find_violations():
        assert v["authority"].endswith(".md")
        assert v["canonical"] and v["superseded"]


def test_no_rulings_means_no_findings(tmp_path):
    """Fail quiet, not loud, when there is nothing to check against."""
    from canon_superseded_names import find_violations
    assert find_violations(canon=tmp_path) == []
