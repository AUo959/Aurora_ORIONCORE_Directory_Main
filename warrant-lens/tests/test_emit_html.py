"""Tests for the HTML inline-annotation viewer.

Confirms (a) flagged spans get wrapped, unflagged text does not; (b) hover
metadata is present and properly HTML-escaped; (c) no external resources
are referenced (Principle 2 echo — viewer must not call the network);
(d) directness affects PHRASING only (Principle 3).
"""
from __future__ import annotations

import re
from dataclasses import replace

from warrant_lens.config_loader import load_app_config, load_fit_table, load_taxonomy
from warrant_lens.emit_html import render_html
from warrant_lens.pipeline import analyze
from warrant_lens.warrant import ClaimContext


def _result(text: str, ctxs=None):
    return analyze(
        text,
        taxonomy=load_taxonomy(),
        fit_table=load_fit_table(),
        app_config=load_app_config(),
        contexts=ctxs or {},
    )


def test_html_wraps_flagged_spans_only():
    text = (
        "Capitalism is wrong. "                                # silent
        "Global emissions rose 42% last year."                 # NO_SOURCE
    )
    result = _result(text)
    app = load_app_config()
    out = render_html(text, result.records, app.delivery)
    # Both texts appear in the body.
    assert "Capitalism is wrong." in out.html
    assert "Global emissions rose 42% last year." in out.html
    # The flagged span is wrapped in wl-flag.
    flagged_wrap = re.search(
        r'<span class="wl-flag"[^>]*>Global emissions rose 42% last year\.',
        out.html,
    )
    assert flagged_wrap, "flagged span must be wrapped in wl-flag"
    # The unflagged opinion is NOT wrapped in wl-flag — it appears as plain
    # text without a wl-flag wrapper immediately preceding it.
    unflagged_wrap = re.search(
        r'<span class="wl-flag"[^>]*>Capitalism is wrong\.',
        out.html,
    )
    assert unflagged_wrap is None, "unflagged opinion must not be wrapped"


def test_html_includes_hover_metadata():
    text = "Global emissions rose 42% last year."
    result = _result(text)
    app = load_app_config()
    out = render_html(text, result.records, app.delivery)
    # All five required metadata pieces must appear in the hover popover.
    assert "Claim I am testing" in out.html
    assert "Handoff" in out.html
    assert "reason_code" in out.html
    assert "standard" in out.html
    assert "blind-spot" in out.html


def test_html_has_no_external_resources():
    """Principle 2 echo: the viewer must not call the network. No <script>,
    no <link>, no http(s):// references."""
    text = "Global emissions rose 42% last year."
    result = _result(text)
    out = render_html(text, result.records, load_app_config().delivery)
    assert "<script" not in out.html.lower()
    assert "<link" not in out.html.lower()
    # No remote URLs anywhere in the body.
    assert not re.search(r"https?://", out.html)


def test_html_escapes_dangerous_content():
    """HTML escaping must not be bypassable via injected source text."""
    text = "<img onerror=alert(1) src=x> rose 42% last year."
    result = _result(text)
    out = render_html(text, result.records, load_app_config().delivery)
    assert "<img onerror" not in out.html
    assert "&lt;img onerror" in out.html


def test_html_directness_changes_phrasing_only():
    """Same input, different directness → same flagged spans, different
    headline text. Mirrors test_T_DELIVERY at the HTML layer."""
    text = "Global emissions rose 42% last year (per AdvocacyOrg blog)."
    ctx = ClaimContext(
        domain="general_empirical",
        observed_source_class="advocacy_org_publication",
        source_text="AdvocacyOrg blog",
        source_role="secondary",
        settled=True,
    )
    result = _result(text, ctxs={0: ctx})
    app = load_app_config()

    gentle = render_html(text, result.records, replace(app.delivery, directness="gentle"))
    direct = render_html(text, result.records, replace(app.delivery, directness="direct"))

    # Same flagged count, same DOM structure for wl-flag count.
    assert gentle.html.count('class="wl-flag"') == direct.html.count('class="wl-flag"')
    # Different headlines in the popover.
    assert "typically weak" in gentle.html
    assert "mismatched" in direct.html


def test_html_summary_table_lists_reason_codes():
    """The footer summary counts flags per reason_code."""
    text = (
        "Global emissions rose 42% last year. "                       # NO_SOURCE
        "Smoking causes lung cancer (Smith et al. 2003)."             # role_mismatch (settled)
    )
    ctxs = {
        1: ClaimContext(
            domain="general_empirical",
            observed_source_class="peer_reviewed_primary_body",
            source_text="Smith et al. 2003",
            source_role="primary",
            settled=True,
        ),
    }
    result = _result(text, ctxs=ctxs)
    out = render_html(text, result.records, load_app_config().delivery)
    assert "NO_SOURCE" in out.html
    assert "SOURCE_ROLE_MISMATCH" in out.html
