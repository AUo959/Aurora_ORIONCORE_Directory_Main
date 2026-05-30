"""Stage [6c] EMIT HTML inline-annotation viewer.

A SECOND rendering of the SAME ClaimRecord[] (per SPEC §8: build once, render
twice — this is render-thrice now). The HTML view exists because the text-
marker syntax in emit_inline.py is fine for terminals and pipelines but not
for human review at scale.

Rendering rules (mirror §8.1):
  - Subtle highlight on flagged spans only. Unflagged text is unmarked.
  - Hover reveals: tool_restatement, reason in plain language, human_handoff,
    standard_invoked, blind_spot_note, tool_extensions (self-seams).
  - Directness toggle (gentle/direct) drives PHRASING only, not which spans
    are highlighted (Principle 3, enforced upstream by emit_inline).
  - No JavaScript dependencies. No CDN. Self-contained file. The viewer must
    not call out to the network — Principle 2 echo (the artefact carries the
    same no-truth-verification discipline).
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .config_loader import DeliveryConfig
from .emit_inline import _REASON_PHRASES
from .model import ClaimRecord


_CSS = """
:root {
  --bg: #fafaf7;
  --fg: #1c1c1a;
  --muted: #6b6b67;
  --rule: #e4e3dd;
  --flag-bg: #fff4d9;
  --flag-border: #d2a200;
  --frontier-bg: #eef3fc;
  --frontier-border: #5c7bd9;
  --chrome-bg: #ffffff;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", system-ui, sans-serif;
  background: var(--bg);
  color: var(--fg);
  line-height: 1.55;
}
.wl-page {
  max-width: 820px;
  margin: 2.5rem auto;
  padding: 0 1.5rem 4rem;
}
.wl-header {
  border-bottom: 1px solid var(--rule);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
.wl-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.25rem;
  letter-spacing: -0.01em;
}
.wl-sub {
  color: var(--muted);
  font-size: 0.85rem;
  margin: 0;
}
.wl-text {
  font-size: 1.0625rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.wl-flag {
  background: var(--flag-bg);
  border-bottom: 2px solid var(--flag-border);
  padding: 0 0.1em;
  cursor: help;
  position: relative;
}
.wl-flag[data-reason="FRONTIER_HANDOFF"] {
  background: var(--frontier-bg);
  border-bottom-color: var(--frontier-border);
}
.wl-flag .wl-popover {
  position: absolute;
  left: 0;
  top: calc(100% + 4px);
  z-index: 10;
  width: 28rem;
  max-width: 90vw;
  background: var(--chrome-bg);
  border: 1px solid var(--rule);
  border-radius: 6px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.08);
  padding: 0.85rem 1rem;
  font-size: 0.875rem;
  color: var(--fg);
  display: none;
  white-space: normal;
  line-height: 1.45;
}
.wl-flag:hover .wl-popover,
.wl-flag:focus-within .wl-popover {
  display: block;
}
.wl-popover h4 {
  margin: 0 0 0.35rem;
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 600;
}
.wl-popover p {
  margin: 0 0 0.6rem;
}
.wl-popover .wl-restate {
  font-style: italic;
}
.wl-popover .wl-handoff {
  color: var(--fg);
}
.wl-popover .wl-meta {
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px solid var(--rule);
  font-size: 0.75rem;
  color: var(--muted);
}
.wl-popover .wl-seam {
  margin: 0.35rem 0 0;
  padding: 0.4rem 0.55rem;
  background: #fffaeb;
  border-left: 2px solid #d2a200;
  font-size: 0.78rem;
}
.wl-summary {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--rule);
  font-size: 0.85rem;
  color: var(--muted);
}
.wl-summary table {
  border-collapse: collapse;
  width: 100%;
  margin-top: 0.4rem;
  font-variant-numeric: tabular-nums;
}
.wl-summary th, .wl-summary td {
  text-align: left;
  padding: 0.25rem 0.6rem 0.25rem 0;
  border-bottom: 1px solid var(--rule);
}
.wl-footer {
  margin-top: 2.5rem;
  font-size: 0.75rem;
  color: var(--muted);
  border-top: 1px solid var(--rule);
  padding-top: 0.85rem;
}
"""


@dataclass(frozen=True)
class HtmlRenderResult:
    html: str
    n_flagged: int
    n_silent: int


def render_html(
    text: str,
    records: Iterable[ClaimRecord],
    delivery: DeliveryConfig,
    *,
    title: str = "Warrant Lens — analysis",
    standard_invoked: str = "general_empirical_v1",
) -> HtmlRenderResult:
    """Build a self-contained HTML page rendering the input text with
    flagged-span highlights and hover cards. Returns the HTML string plus
    counts for the summary footer."""
    directness = delivery.directness if delivery.directness in {"gentle", "direct"} else "gentle"
    record_list = list(records)
    flagged = sorted(
        [r for r in record_list if r.attention_flag.raised],
        key=lambda r: r.span.start,
    )
    silent = [r for r in record_list if not r.attention_flag.raised]

    body = _build_annotated_body(text, flagged, directness)

    summary_rows = _summary_rows(record_list)

    page = _HTML_SHELL.format(
        css=_CSS,
        title=html.escape(title),
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        standard=html.escape(standard_invoked),
        n_flagged=len(flagged),
        n_silent=len(silent),
        body=body,
        summary_rows=summary_rows,
        directness=html.escape(directness),
    )
    return HtmlRenderResult(html=page, n_flagged=len(flagged), n_silent=len(silent))


def _build_annotated_body(text: str, flagged_records: list[ClaimRecord], directness: str) -> str:
    """Walk the source text, wrap flagged spans in <span class="wl-flag"> with
    popover content, and HTML-escape everything else."""
    parts: list[str] = []
    cursor = 0
    for r in flagged_records:
        if r.span.start < cursor:
            # Overlapping spans should not happen given segmentation, but
            # guard anyway: skip the second one rather than corrupt the doc.
            continue
        # Unflagged text up to this span.
        parts.append(html.escape(text[cursor : r.span.start]))
        # Flagged span.
        parts.append(_flag_html(text[r.span.start : r.span.end], r, directness))
        cursor = r.span.end
    parts.append(html.escape(text[cursor:]))
    return "".join(parts)


def _flag_html(span_text: str, r: ClaimRecord, directness: str) -> str:
    rc = r.attention_flag.reason_code or "SOURCE_CATEGORY_MISMATCH"
    headline = _REASON_PHRASES.get(rc, {}).get(directness, rc)

    restatement = r.tool_restatement or "(restatement omitted — non-demanding claim)"
    handoff = r.attention_flag.human_handoff or ""

    seam_block = ""
    if r.tool_extensions:
        items = "".join(
            f"<li>{html.escape(e)}</li>" for e in r.tool_extensions
        )
        seam_block = (
            f'<div class="wl-seam"><h4>Self-seam (tool extensions)</h4>'
            f'<ul style="margin:0.2rem 0 0 1rem;padding:0;">{items}</ul></div>'
        )

    popover = (
        '<span class="wl-popover" role="tooltip">'
        f'<h4>Flag · {html.escape(headline)}</h4>'
        f'<h4>Claim I am testing</h4>'
        f'<p class="wl-restate">{html.escape(restatement)}</p>'
        f'<h4>Handoff</h4>'
        f'<p class="wl-handoff">{html.escape(handoff)}</p>'
        f'{seam_block}'
        '<div class="wl-meta">'
        f'<div>reason_code: {html.escape(rc)}</div>'
        f'<div>claim_type: {html.escape(r.claim_type)}</div>'
        f'<div>standard: {html.escape(r.standard_invoked)}</div>'
        f'<div>blind-spot: {html.escape(r.blind_spot_note)}</div>'
        '</div>'
        '</span>'
    )

    return (
        f'<span class="wl-flag" data-reason="{html.escape(rc)}" tabindex="0">'
        f'{html.escape(span_text)}{popover}</span>'
    )


def _summary_rows(records: list[ClaimRecord]) -> str:
    """Count flagged records by reason_code, render as table rows."""
    counts: dict[str, int] = {}
    for r in records:
        if not r.attention_flag.raised:
            continue
        code = r.attention_flag.reason_code or "UNCATEGORISED"
        counts[code] = counts.get(code, 0) + 1
    if not counts:
        return '<tr><td colspan="2"><em>No flags raised — input is clean by structural checks.</em></td></tr>'
    rows = []
    for code, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        rows.append(f"<tr><td>{html.escape(code)}</td><td>{n}</td></tr>")
    return "\n".join(rows)


_HTML_SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="warrant-lens">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="wl-page">
  <header class="wl-header">
    <h1 class="wl-title">{title}</h1>
    <p class="wl-sub">{date} · standard: {standard} · delivery: {directness} · {n_flagged} flag(s), {n_silent} silent claim(s)</p>
  </header>
  <article class="wl-text">{body}</article>
  <section class="wl-summary">
    <strong>Flag summary</strong>
    <table>
      <thead><tr><th>reason_code</th><th>count</th></tr></thead>
      <tbody>{summary_rows}</tbody>
    </table>
  </section>
  <footer class="wl-footer">
    <p><strong>Reminder.</strong> Warrant Lens checks the structural quality of claim warrants. It does <em>not</em> assert truth. Every record carries a blind-spot note — a structurally well-formed warrant can still be false. Credibility of any specific named source is yours to judge.</p>
  </footer>
</div>
</body>
</html>
"""
