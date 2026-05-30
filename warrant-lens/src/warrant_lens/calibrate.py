"""Calibration harness — SPEC §8.2 / §9 T-CALIB made real.

Replays a JSONL trace, accepts human labels of "worth attention y/n/unsure",
computes precision and (best-effort) recall, and emits both a labelled JSONL
and a markdown summary.

Precision (the primary metric):
    P = |flagged AND worth_attention=yes| / |flagged AND worth_attention in {yes,no}|
    "unsure" is excluded from the denominator so the user is not penalised
    for declining to render a verdict.

Recall (best effort — requires labelling unflagged claims too):
    R = |flagged AND yes| / |all worth_attention=yes|
    Only meaningful if the user also labelled the silent claims; otherwise
    reported as null.

Two modes:
  - interactive: prompt-by-prompt at the terminal, in span order. Skippable.
  - file: read labels from a CSV (claim_id,worth_attention[,notes]).

Both write the canonical labelled-trace file with the same archival convention
plus a `.labels` suffix, e.g.
    WARRANTLENS__TRACE__topic__v1.0__YYYY-MM-DD.labels.jsonl
"""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Optional, TextIO


VALID_LABELS = {"yes", "no", "unsure"}


@dataclass
class LabelledRecord:
    raw: dict
    worth_attention: Optional[str]  # None means not labelled
    notes: str = ""

    @property
    def claim_id(self) -> str:
        return self.raw["claim_id"]

    @property
    def flagged(self) -> bool:
        return bool(self.raw.get("attention_flag", {}).get("raised", False))

    @property
    def claim_text(self) -> str:
        return self.raw.get("claim_text", "")

    @property
    def reason_code(self) -> Optional[str]:
        return self.raw.get("attention_flag", {}).get("reason_code")


@dataclass
class CalibrationReport:
    n_total: int
    n_flagged: int
    n_silent: int
    n_labelled_flagged: int
    n_labelled_silent: int
    precision: Optional[float]
    """None when no flagged claims have yes/no labels."""

    recall: Optional[float]
    """None unless silent claims were also labelled."""

    confusion: dict[str, int] = field(default_factory=dict)
    """Counts keyed by 'flagged_yes', 'flagged_no', 'flagged_unsure',
    'silent_yes', 'silent_no', 'silent_unsure'."""

    def to_markdown(self, source_trace: Optional[Path] = None) -> str:
        lines: list[str] = []
        lines.append("# Warrant Lens — Calibration Report")
        lines.append("")
        if source_trace:
            lines.append(f"**Trace:** `{source_trace}`")
        lines.append(f"**Date:** {date.today().isoformat()}")
        lines.append("")
        lines.append("## Counts")
        lines.append("")
        lines.append(f"- Total records: {self.n_total}")
        lines.append(f"- Flagged: {self.n_flagged}")
        lines.append(f"- Silent (filtered): {self.n_silent}")
        lines.append(f"- Labelled flagged: {self.n_labelled_flagged}")
        lines.append(f"- Labelled silent: {self.n_labelled_silent}")
        lines.append("")
        lines.append("## Precision / Recall")
        lines.append("")
        if self.precision is None:
            lines.append("- Precision: _not computable — no labelled flagged claims_")
        else:
            lines.append(f"- Precision (flagged-and-worth-attention / flagged-labelled-yes-or-no): **{self.precision:.3f}**")
        if self.recall is None:
            lines.append("- Recall: _not computable — silent claims were not labelled_")
        else:
            lines.append(f"- Recall (estimated): **{self.recall:.3f}**")
        lines.append("")
        lines.append("## Confusion matrix")
        lines.append("")
        lines.append("| | yes | no | unsure |")
        lines.append("|---|---:|---:|---:|")
        lines.append(
            "| flagged | {} | {} | {} |".format(
                self.confusion.get("flagged_yes", 0),
                self.confusion.get("flagged_no", 0),
                self.confusion.get("flagged_unsure", 0),
            )
        )
        lines.append(
            "| silent  | {} | {} | {} |".format(
                self.confusion.get("silent_yes", 0),
                self.confusion.get("silent_no", 0),
                self.confusion.get("silent_unsure", 0),
            )
        )
        lines.append("")
        lines.append(
            "_Reminder: this tool measures whether flagged claims are "
            "worth a human's attention. It does NOT measure whether claims "
            "are true. Truth verification is explicitly out of scope (Principle 2)._"
        )
        lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace I/O
# ---------------------------------------------------------------------------

def load_trace(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def labelled_filename(trace_path: Path) -> Path:
    """Replace .jsonl with .labels.jsonl, preserving the archival convention."""
    stem = trace_path.name
    if stem.endswith(".jsonl"):
        return trace_path.with_name(stem[:-len(".jsonl")] + ".labels.jsonl")
    return trace_path.with_suffix(".labels.jsonl")


def report_filename(trace_path: Path) -> Path:
    stem = trace_path.name
    if stem.endswith(".jsonl"):
        return trace_path.with_name(stem[:-len(".jsonl")] + ".calibration.md")
    return trace_path.with_suffix(".calibration.md")


def write_labelled_trace(path: Path, labelled: Iterable[LabelledRecord]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for lr in labelled:
            payload = dict(lr.raw)
            payload["calibration"] = {
                "worth_attention": lr.worth_attention,
                "notes": lr.notes,
            }
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Labelling sources
# ---------------------------------------------------------------------------

def label_from_csv(records: list[dict], csv_path: Path) -> list[LabelledRecord]:
    """CSV columns: claim_id, worth_attention (yes|no|unsure), notes (optional).
    Unknown claim_ids are silently ignored; unlabelled records remain unlabelled.
    """
    by_id: dict[str, dict] = {}
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("claim_id", "").strip()
            if not cid:
                continue
            wa = (row.get("worth_attention") or "").strip().lower()
            if wa not in VALID_LABELS:
                wa = ""
            by_id[cid] = {
                "worth_attention": wa or None,
                "notes": (row.get("notes") or "").strip(),
            }
    out: list[LabelledRecord] = []
    for r in records:
        entry = by_id.get(r["claim_id"], {})
        out.append(
            LabelledRecord(
                raw=r,
                worth_attention=entry.get("worth_attention"),
                notes=entry.get("notes", ""),
            )
        )
    return out


def label_interactive(
    records: list[dict],
    *,
    flagged_only: bool = True,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> list[LabelledRecord]:
    """Prompt at the terminal for each record. Returns labelled list.

    flagged_only=True (default): only ask about flagged records — this is what
    precision needs. Set False to label silent records too for recall.
    """
    out: list[LabelledRecord] = []
    for r in records:
        flagged = bool(r.get("attention_flag", {}).get("raised", False))
        if flagged_only and not flagged:
            out.append(LabelledRecord(raw=r, worth_attention=None))
            continue
        stdout.write("\n---\n")
        stdout.write(f"claim_id: {r['claim_id']}\n")
        stdout.write(f"claim:    {r.get('claim_text', '')}\n")
        if flagged:
            ah = r.get("attention_flag", {})
            stdout.write(f"flagged:  YES ({ah.get('reason_code')})\n")
            stdout.write(f"handoff:  {ah.get('human_handoff')}\n")
        else:
            stdout.write("flagged:  no (silent — filtered)\n")
        stdout.write("Worth a human's attention? [y]es / [n]o / [u]nsure / [s]kip: ")
        stdout.flush()
        ans = (stdin.readline() or "").strip().lower()
        mapping = {"y": "yes", "n": "no", "u": "unsure"}
        worth = mapping.get(ans[:1] if ans else "s")  # 's' → None
        notes = ""
        if worth in {"yes", "no"}:
            stdout.write("notes (optional, blank to skip): ")
            stdout.flush()
            notes = (stdin.readline() or "").strip()
        out.append(LabelledRecord(raw=r, worth_attention=worth, notes=notes))
    return out


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_report(labelled: list[LabelledRecord]) -> CalibrationReport:
    confusion: dict[str, int] = {}

    def bump(key: str) -> None:
        confusion[key] = confusion.get(key, 0) + 1

    n_total = len(labelled)
    n_flagged = sum(1 for lr in labelled if lr.flagged)
    n_silent = n_total - n_flagged
    n_lf = 0
    n_ls = 0

    flagged_yes = 0
    flagged_no = 0
    silent_yes = 0
    silent_no = 0

    for lr in labelled:
        wa = lr.worth_attention
        if wa not in VALID_LABELS:
            continue
        bucket = ("flagged" if lr.flagged else "silent") + "_" + wa
        bump(bucket)
        if lr.flagged:
            n_lf += 1
            if wa == "yes":
                flagged_yes += 1
            elif wa == "no":
                flagged_no += 1
        else:
            n_ls += 1
            if wa == "yes":
                silent_yes += 1
            elif wa == "no":
                silent_no += 1

    denom_p = flagged_yes + flagged_no
    precision = (flagged_yes / denom_p) if denom_p > 0 else None

    # Recall only computable if at least one silent claim was labelled
    # (otherwise the denominator is just flagged_yes and recall == 1.0 by
    # construction — meaningless).
    if n_ls > 0:
        all_yes = flagged_yes + silent_yes
        recall = (flagged_yes / all_yes) if all_yes > 0 else None
    else:
        recall = None

    return CalibrationReport(
        n_total=n_total,
        n_flagged=n_flagged,
        n_silent=n_silent,
        n_labelled_flagged=n_lf,
        n_labelled_silent=n_ls,
        precision=precision,
        recall=recall,
        confusion=confusion,
    )


# ---------------------------------------------------------------------------
# End-to-end orchestration helper
# ---------------------------------------------------------------------------

def run_calibration(
    trace_path: Path,
    *,
    labels_csv: Optional[Path] = None,
    interactive: bool = False,
    label_silent: bool = False,
    out_dir: Optional[Path] = None,
) -> tuple[Path, Path, CalibrationReport]:
    """Return (labelled_jsonl_path, report_md_path, report).

    Exactly one of labels_csv / interactive must be provided.
    """
    if not labels_csv and not interactive:
        raise ValueError("Provide labels_csv or set interactive=True.")
    if labels_csv and interactive:
        raise ValueError("Provide only one of labels_csv / interactive.")

    records = load_trace(trace_path)
    if interactive:
        labelled = label_interactive(records, flagged_only=not label_silent)
    else:
        labelled = label_from_csv(records, labels_csv)  # type: ignore[arg-type]

    report = compute_report(labelled)

    target_dir = out_dir or trace_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    lab_path = target_dir / labelled_filename(trace_path).name
    rep_path = target_dir / report_filename(trace_path).name

    write_labelled_trace(lab_path, labelled)
    rep_path.write_text(report.to_markdown(source_trace=trace_path), encoding="utf-8")
    return lab_path, rep_path, report
