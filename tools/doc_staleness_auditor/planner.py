"""Draft evidence-backed fixes for STALE findings.

For each STALE finding we produce a concrete edit: the doc, the line, the exact
old text, the proposed new text (with the observed ground-truth value swapped in
for the doc-claimed value), and the evidence cited inline as a trailing comment
so a reviewer never has to trust the tool -- only re-check the cited source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .models import ClaimType, Finding, Status


@dataclass
class PlannedEdit:
    doc_path: str
    line: int
    old_text: str
    new_text: str
    rationale: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_path": self.doc_path, "line": self.line,
            "old_text": self.old_text, "new_text": self.new_text,
            "rationale": self.rationale, "evidence": self.evidence,
        }

    def diff(self) -> str:
        return (
            f"--- {self.doc_path}:{self.line}\n"
            f"- {self.old_text}\n"
            f"+ {self.new_text}\n"
            f"# evidence: {self.rationale}"
        )


def plan_fixes(findings: list[Finding]) -> list[PlannedEdit]:
    edits: list[PlannedEdit] = []
    for f in findings:
        if f.status is not Status.STALE:
            continue
        edit = _draft_edit(f)
        if edit is not None:
            edits.append(edit)
    return edits


def _draft_edit(f: Finding) -> PlannedEdit | None:
    claim = f.claim
    old = claim.raw_text
    ev = f.evidence
    cite = _cite(ev)

    if claim.type is ClaimType.PATH:
        # Broken path reference: we cannot invent the correct path, so we flag it
        # in place for a human, citing that the tree has no such entry.
        new = f"{old}  <!-- STALE: path not found at HEAD; {cite} -->"
        rationale = f"referenced path '{claim.value}' absent from git tree; {cite}"
        return PlannedEdit(claim.doc_path, claim.doc_line, old, new, rationale, ev.to_dict())

    if claim.type is ClaimType.SYMBOL:
        new = f"{old}  <!-- STALE: symbol '{claim.value}' not found in cited source; {cite} -->"
        rationale = f"symbol '{claim.value}' not defined in ground-truth source; {cite}"
        return PlannedEdit(claim.doc_path, claim.doc_line, old, new, rationale, ev.to_dict())

    if claim.type in (ClaimType.NUMERIC, ClaimType.VERSION) and f.observed:
        observed = _bare_value(f.observed)
        new = _substitute(old, claim.value, observed)
        if new == old:
            new = f"{old}  <!-- STALE: doc says {claim.value}, observed {observed}; {cite} -->"
        else:
            new = f"{new}  <!-- fixed {claim.value} -> {observed}; {cite} -->"
        rationale = f"doc-claimed '{claim.value}' vs observed '{observed}'; {cite}"
        return PlannedEdit(claim.doc_path, claim.doc_line, old, new, rationale, ev.to_dict())

    return None


def _substitute(text: str, old_val: str, new_val: str) -> str:
    return re.sub(rf"(?<![\w.]){re.escape(old_val)}(?![\w.])", new_val, text, count=1)


def _bare_value(observed: str) -> str:
    # observed may be like "2.1.0" or "3.11 (per pyproject...)" or "VERSION=2.1.0"
    m = re.search(r"\d+\.\d+(?:\.\d+)?|\d+", observed)
    return m.group(0) if m else observed


def _cite(ev) -> str:
    loc = ", ".join(
        f"{fpath}:{ln}" for fpath, ln in zip(ev.files, ev.lines, strict=False)
    ) or ", ".join(ev.files)
    sha = f"@{ev.sha[:12]}" if ev.sha else ""
    return f"[{ev.method}] {ev.detail} ({loc}{sha})".strip()
