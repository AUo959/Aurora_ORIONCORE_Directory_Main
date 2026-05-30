"""Acceptance tests — one per row of SPEC §9.

These encode the principles. A v1 build is correct iff every test here passes.
T-CLIMATE and T-DELIVERY are tier-1: they protect the tool from becoming a
partisan or a sycophant.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from warrant_lens.config_loader import load_app_config, load_fit_table, load_taxonomy
from warrant_lens.emit_inline import render as render_inline
from warrant_lens.emit_trace import records_to_jsonable, trace_filename, write_trace
from warrant_lens.model import ClaimRecord
from warrant_lens.pipeline import analyze, flagged_claims
from warrant_lens.warrant import ClaimContext


# ---------- shared fixtures ----------

@pytest.fixture(scope="module")
def taxonomy():
    return load_taxonomy()


@pytest.fixture(scope="module")
def fit_table():
    return load_fit_table()


@pytest.fixture(scope="module")
def app_config():
    return load_app_config()


def _run(text, **kwargs):
    return analyze(text, **kwargs)


# ---------- T-FILTER ----------

def test_T_FILTER_opinion_definition_hedge_raise_zero_flags(taxonomy, fit_table, app_config):
    """Opinion + definition + hedge → no flags raised."""
    text = (
        "Capitalism is wrong. "
        "A vector is defined as an ordered tuple of numbers. "
        "It might rain tomorrow."
    )
    result = _run(text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config)
    assert all(not r.attention_flag.raised for r in result.records), [
        (r.claim_text, r.attention_flag.reason_code) for r in result.records
    ]


# ---------- T-DEMAND ----------

def test_T_DEMAND_bare_statistic_no_source_flags_NO_SOURCE(taxonomy, fit_table, app_config):
    """Bare specific statistic, no source → NO_SOURCE flag with handoff."""
    text = "Global emissions rose 42% last year."
    result = _run(text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config)
    flagged = flagged_claims(result.records)
    assert len(flagged) == 1
    r = flagged[0]
    assert r.attention_flag.reason_code == "NO_SOURCE"
    assert r.attention_flag.human_handoff
    assert r.attention_flag.human_handoff.strip()


# ---------- T-PAIR ----------

def test_T_PAIR_same_source_two_claim_types_verdict_differs(taxonomy, fit_table, app_config):
    """The same observed source class drives different verdicts depending on
    claim type. No standalone source-quality badge anywhere."""
    text = (
        "Global emissions rose 42% last year (per the Daily Polemicist). "
        "John Smith assumed office in 2017 (per the Daily Polemicist)."
    )
    ctxs = {
        0: ClaimContext(
            domain="general_empirical",
            observed_source_class="op_ed",
            source_text="Daily Polemicist",
            source_role="secondary",
            settled=True,
        ),
        1: ClaimContext(
            domain="general_empirical",
            observed_source_class="news_of_record",
            source_text="Daily Polemicist",
            source_role="secondary",
            settled=True,
        ),
    }
    result = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config, contexts=ctxs
    )
    flagged = flagged_claims(result.records)
    # First claim (statistic w/ op_ed) → category_mismatch; second (temporal
    # fact w/ news_of_record) → fit. Verdicts differ.
    verdicts = [r.warrant.fit.fit_verdict for r in result.records if r.warrant]
    assert "category_mismatch" in verdicts
    assert "fit" in verdicts
    # No standalone source-quality badge: ensure every flagged record carries
    # both the claim_type and the fit pair.
    payload = json.dumps(records_to_jsonable(result.records))
    assert "source_quality" not in payload  # never emitted standalone
    for r in result.records:
        if r.warrant is None:
            continue
        # the fit assessment ALWAYS sits next to the claim type
        assert r.claim_type
        assert r.warrant.fit is not None


# ---------- T-CLIMATE (tier-1) ----------

@pytest.mark.tier1
def test_T_CLIMATE_verdict_independent_of_argued_conclusion(
    taxonomy, fit_table, app_config
):
    """A settled-science claim cited to an advocacy blog AND a contrary
    skeptic claim cited to an advocacy blog must yield IDENTICAL
    category_mismatch flags. Discourse-level controversy must not appear
    anywhere in the output."""

    consensus_text = "The planet has warmed substantially since 1900 (per AdvocacyOrg blog)."
    skeptic_text = "The planet has not warmed substantially since 1900 (per AdvocacyOrg blog)."

    ctx = ClaimContext(
        domain="general_empirical",
        observed_source_class="advocacy_org_publication",
        source_text="AdvocacyOrg blog",
        source_role="secondary",
        settled=True,
    )

    r_consensus = _run(
        consensus_text, taxonomy=taxonomy, fit_table=fit_table,
        app_config=app_config, contexts={0: ctx},
    )
    r_skeptic = _run(
        skeptic_text, taxonomy=taxonomy, fit_table=fit_table,
        app_config=app_config, contexts={0: ctx},
    )

    f_c = flagged_claims(r_consensus.records)
    f_s = flagged_claims(r_skeptic.records)
    assert len(f_c) == 1 and len(f_s) == 1

    # Identical reason code + verdict.
    assert f_c[0].attention_flag.reason_code == "SOURCE_CATEGORY_MISMATCH"
    assert f_s[0].attention_flag.reason_code == "SOURCE_CATEGORY_MISMATCH"
    assert f_c[0].warrant.fit.fit_verdict == f_s[0].warrant.fit.fit_verdict == "category_mismatch"

    # No field carries discourse-controversy signal.
    payload_c = json.dumps(records_to_jsonable(r_consensus.records))
    payload_s = json.dumps(records_to_jsonable(r_skeptic.records))
    for forbidden in ("controversy", "controversial", "public_debate", "contested_publicly"):
        assert forbidden not in payload_c
        assert forbidden not in payload_s


# ---------- T-PRIMARY ----------

def test_T_PRIMARY_lone_primary_for_settled_claim_role_mismatch(
    taxonomy, fit_table, app_config
):
    """Lone primary study for a SETTLED body → role_mismatch (not fit).
    Proximity is not confirmation."""
    text = "Smoking causes lung cancer (Smith et al. 2003)."
    ctx = ClaimContext(
        domain="general_empirical",
        observed_source_class="peer_reviewed_primary_body",
        source_text="Smith et al. 2003",
        source_role="primary",
        settled=True,
    )
    result = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config, contexts={0: ctx}
    )
    flagged = flagged_claims(result.records)
    assert len(flagged) == 1
    assert flagged[0].warrant.fit.fit_verdict == "role_mismatch"
    assert flagged[0].attention_flag.reason_code == "SOURCE_ROLE_MISMATCH"


# ---------- T-CHAIN ----------

def test_T_CHAIN_secondary_not_traceable_to_primary_chain_broken(
    taxonomy, fit_table, app_config
):
    """Secondary claim with chain_intact=False → chain_broken."""
    text = "Mortality fell 30% over the decade (synthesis-org summary)."
    ctx = ClaimContext(
        domain="general_empirical",
        observed_source_class="synthesis_report",
        source_text="synthesis-org summary",
        source_role="secondary",
        chain_intact=False,
        settled=True,
    )
    result = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config, contexts={0: ctx}
    )
    flagged = flagged_claims(result.records)
    assert len(flagged) == 1
    assert flagged[0].warrant.fit.fit_verdict == "chain_broken"
    assert flagged[0].attention_flag.reason_code == "CHAIN_BROKEN"


# ---------- T-RESTATE ----------

def test_T_RESTATE_every_flag_has_nonempty_restatement(taxonomy, fit_table, app_config):
    """Every raised flag → non-empty tool_restatement, rendered before flag."""
    text = (
        "Global emissions rose 42% last year. "
        "Smoking causes lung cancer (Smith et al. 2003). "
        "Mortality fell 30% over the decade (synthesis-org summary)."
    )
    ctxs = {
        0: ClaimContext(domain="general_empirical"),  # NO_SOURCE for stat
        1: ClaimContext(
            domain="general_empirical",
            observed_source_class="peer_reviewed_primary_body",
            source_text="Smith et al. 2003",
            source_role="primary",
            settled=True,
        ),
        2: ClaimContext(
            domain="general_empirical",
            observed_source_class="synthesis_report",
            source_text="synthesis-org summary",
            source_role="secondary",
            chain_intact=False,
            settled=True,
        ),
    }
    result = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config, contexts=ctxs
    )
    flagged = flagged_claims(result.records)
    assert flagged, "expected some flags"
    for r in flagged:
        assert r.tool_restatement, f"flag without restatement: {r.claim_text}"

    # Render and confirm the restatement is present in the inline annotation
    # metadata BEFORE the flag (Principle 7: rendered adjacent to flag).
    annotated, annotations = render_inline(text, result.records, app_config.delivery)
    for a in annotations:
        assert a.metadata["tool_restatement"]


# ---------- T-FRONTIER ----------

def test_T_FRONTIER_unknown_consensus_defaults_to_frontier_handoff(
    taxonomy, fit_table, app_config
):
    """Claim with no encoded consensus (settled=None) → default frontier
    handoff. Tool does NOT assert settledness."""
    text = "Compound X induces apoptosis in liver cells (Doe 2024)."
    ctx = ClaimContext(
        domain="general_empirical",
        observed_source_class="peer_reviewed_primary_body",
        source_text="Doe 2024",
        source_role="primary",
        settled=None,  # unknown
    )
    result = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config, contexts={0: ctx}
    )
    flagged = flagged_claims(result.records)
    assert len(flagged) == 1
    r = flagged[0]
    assert r.attention_flag.reason_code == "FRONTIER_HANDOFF"
    assert "frontier" in (r.attention_flag.human_handoff or "").lower()


# ---------- T-DELIVERY (tier-1) ----------

@pytest.mark.tier1
def test_T_DELIVERY_directness_changes_phrasing_only(taxonomy, fit_table, app_config):
    """Same input at gentle and direct → IDENTICAL set of flagged claims;
    only phrasing differs."""
    text = "Global emissions rose 42% last year (per AdvocacyOrg blog)."
    ctx = ClaimContext(
        domain="general_empirical",
        observed_source_class="advocacy_org_publication",
        source_text="AdvocacyOrg blog",
        source_role="secondary",
        settled=True,
    )

    gentle_cfg = replace(app_config, delivery=replace(app_config.delivery, directness="gentle"))
    direct_cfg = replace(app_config, delivery=replace(app_config.delivery, directness="direct"))

    r_g = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=gentle_cfg, contexts={0: ctx}
    )
    r_d = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=direct_cfg, contexts={0: ctx}
    )

    # SUBSTANCE invariant: same flagged set, same reason codes, same verdicts.
    g_flags = [(r.claim_id, r.attention_flag.reason_code, r.warrant.fit.fit_verdict)
               for r in flagged_claims(r_g.records)]
    d_flags = [(r.claim_id, r.attention_flag.reason_code, r.warrant.fit.fit_verdict)
               for r in flagged_claims(r_d.records)]
    assert g_flags == d_flags

    # PHRASING differs in the inline headlines.
    _, g_ann = render_inline(text, r_g.records, gentle_cfg.delivery)
    _, d_ann = render_inline(text, r_d.records, direct_cfg.delivery)
    assert g_ann[0].headline != d_ann[0].headline


# ---------- T-BLINDSPOT ----------

def test_T_BLINDSPOT_clean_structure_carries_blind_spot_note(
    taxonomy, fit_table, app_config
):
    """A claim with a well-formed warrant that passes structural checks
    must still carry a blind_spot_note. The tool must NOT imply the claim is
    verified true."""
    text = "Global emissions rose 42% last year (IPCC 2023 synthesis)."
    ctx = ClaimContext(
        domain="general_empirical",
        observed_source_class="synthesis_report",
        source_text="IPCC 2023 synthesis",
        source_role="secondary",
        chain_intact=True,
        settled=True,
    )
    result = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config, contexts={0: ctx}
    )
    # Should pass structural checks (no flag) but still record the blind spot.
    rec = [r for r in result.records if r.makes_evidentiary_demand][0]
    assert not rec.attention_flag.raised
    assert rec.blind_spot_note
    assert "false" in rec.blind_spot_note.lower() or "warrant" in rec.blind_spot_note.lower()
    # And nothing in the record asserts verification / truth.
    payload = json.dumps(records_to_jsonable(result.records)).lower()
    assert "verified" not in payload
    assert "is true" not in payload


# ---------- T-CALIB ----------

def test_T_CALIB_jsonl_trace_supports_offline_precision_scoring(
    tmp_path, taxonomy, fit_table, app_config
):
    """The JSONL trace must be machine-readable and contain the fields
    needed to compute precision of 'worth attention' offline."""
    text = (
        "Capitalism is wrong. "                                    # filtered (opinion)
        "Global emissions rose 42% last year. "                    # NO_SOURCE
        "Global emissions rose 42% last year (IPCC 2023 synthesis)."  # fit
    )
    ctxs = {
        # idx 0 → no context (NO_SOURCE)
        1: ClaimContext(
            domain="general_empirical",
            observed_source_class="synthesis_report",
            source_text="IPCC 2023 synthesis",
            source_role="secondary",
            settled=True,
        ),
    }
    result = _run(
        text, taxonomy=taxonomy, fit_table=fit_table, app_config=app_config, contexts=ctxs
    )
    path = write_trace(result.records, tmp_path, topic="climate-demo")
    assert path.exists()
    # Filename convention.
    assert path.name.startswith("WARRANTLENS__TRACE__climate-demo__v1.0__")
    assert path.name.endswith(".jsonl")

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(result.records)
    for line in lines:
        rec = json.loads(line)
        # Fields required to compute precision-of-attention offline.
        assert "claim_id" in rec
        assert "claim_type" in rec
        assert "makes_evidentiary_demand" in rec
        assert "attention_flag" in rec
        assert "raised" in rec["attention_flag"]
        if rec["attention_flag"]["raised"]:
            assert rec["attention_flag"]["reason_code"]
            assert rec["attention_flag"]["human_handoff"]


def test_trace_filename_convention():
    """Sanity: filename follows WARRANTLENS__TRACE__[topic]__v1.0__YYYY-MM-DD.jsonl."""
    name = trace_filename("climate-2026")
    assert name.startswith("WARRANTLENS__TRACE__climate-2026__v1.0__")
    assert name.endswith(".jsonl")
