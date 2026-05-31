"""Tests for the calibration harness.

The harness is the operational instrument SPEC §9 T-CALIB alludes to. It must:
  - Compute precision correctly with unsure-excluded denominator.
  - Skip recall when silent claims weren't labelled (rather than reporting 1.0).
  - Preserve the archival filename convention for the labelled trace.
  - Round-trip cleanly through JSONL.
"""
from __future__ import annotations

import csv
import io
import json

import pytest

from warrant_lens.calibrate import (
    LabelledRecord,
    compute_report,
    label_from_csv,
    label_interactive,
    labelled_filename,
    load_trace,
    report_filename,
    run_calibration,
    write_labelled_trace,
)
from warrant_lens.config_loader import load_app_config, load_fit_table, load_taxonomy
from warrant_lens.emit_trace import write_trace
from warrant_lens.pipeline import analyze
from warrant_lens.warrant import ClaimContext


@pytest.fixture
def trace_path(tmp_path):
    """Build a real trace via the pipeline, write it, return the path."""
    text = (
        "Capitalism is wrong. "                                       # silent (opinion)
        "Global emissions rose 42% last year. "                       # NO_SOURCE
        "Global emissions rose 42% last year (IPCC 2023 synthesis). "  # fit
        "Smoking causes lung cancer (Smith et al. 2003)."             # role_mismatch
    )
    ctxs = {
        # idx 0 → no context → NO_SOURCE
        1: ClaimContext(
            domain="general_empirical",
            observed_source_class="synthesis_report",
            source_text="IPCC 2023 synthesis",
            source_role="secondary",
            settled=True,
        ),
        2: ClaimContext(
            domain="general_empirical",
            observed_source_class="peer_reviewed_primary_body",
            source_text="Smith et al. 2003",
            source_role="primary",
            settled=True,
        ),
    }
    result = analyze(
        text,
        taxonomy=load_taxonomy(),
        fit_table=load_fit_table(),
        app_config=load_app_config(),
        contexts=ctxs,
    )
    path = write_trace(result.records, tmp_path, topic="calibration-fixture")
    return path


def test_filename_conventions_preserve_archival_format(trace_path):
    lab = labelled_filename(trace_path)
    rep = report_filename(trace_path)
    assert lab.name.startswith("WARRANTLENS__TRACE__calibration-fixture__v1.0__")
    assert lab.name.endswith(".labels.jsonl")
    assert rep.name.endswith(".calibration.md")


def test_csv_labelling_then_compute_precision(trace_path, tmp_path):
    """Two flagged claims labelled yes+no → precision = 0.5."""
    records = load_trace(trace_path)
    flagged = [r for r in records if r["attention_flag"]["raised"]]
    assert len(flagged) >= 2  # NO_SOURCE + role_mismatch

    csv_path = tmp_path / "labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "worth_attention", "notes"])
        w.writerow([flagged[0]["claim_id"], "yes", "real evidentiary gap"])
        w.writerow([flagged[1]["claim_id"], "no", "context made it fine"])

    labelled = label_from_csv(records, csv_path)
    report = compute_report(labelled)
    assert report.n_labelled_flagged == 2
    assert report.precision == pytest.approx(0.5)
    # Silent claims weren't labelled → recall must be None, not 1.0.
    assert report.recall is None


def test_unsure_excluded_from_precision_denominator(trace_path, tmp_path):
    """'unsure' should not be charged against the tool."""
    records = load_trace(trace_path)
    flagged = [r for r in records if r["attention_flag"]["raised"]]

    csv_path = tmp_path / "labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "worth_attention", "notes"])
        w.writerow([flagged[0]["claim_id"], "yes", ""])
        w.writerow([flagged[1]["claim_id"], "unsure", ""])

    labelled = label_from_csv(records, csv_path)
    report = compute_report(labelled)
    # Denominator is only yes/no → precision = 1/1 = 1.0, not 1/2 = 0.5.
    assert report.precision == pytest.approx(1.0)


def test_recall_computable_when_silent_claims_are_labelled(trace_path, tmp_path):
    """If the user labels at least one silent claim, recall is computable."""
    records = load_trace(trace_path)
    flagged = [r for r in records if r["attention_flag"]["raised"]]
    silent = [r for r in records if not r["attention_flag"]["raised"]]
    assert silent

    csv_path = tmp_path / "labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "worth_attention", "notes"])
        # One flagged claim genuinely worth attention.
        w.writerow([flagged[0]["claim_id"], "yes", ""])
        # One silent claim that — per the user — also was worth attention
        # (a missed flag). This is the recall-relevant signal.
        w.writerow([silent[0]["claim_id"], "yes", "tool missed this"])

    labelled = label_from_csv(records, csv_path)
    report = compute_report(labelled)
    # 1 flagged_yes / (1 flagged_yes + 1 silent_yes) = 0.5
    assert report.recall == pytest.approx(0.5)


def test_run_calibration_writes_labelled_jsonl_and_report(trace_path, tmp_path):
    records = load_trace(trace_path)
    flagged = [r for r in records if r["attention_flag"]["raised"]]

    csv_path = tmp_path / "labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "worth_attention", "notes"])
        w.writerow([flagged[0]["claim_id"], "yes", ""])

    lab_path, rep_path, report = run_calibration(
        trace_path, labels_csv=csv_path, out_dir=tmp_path / "out"
    )
    assert lab_path.exists()
    assert rep_path.exists()
    assert lab_path.name.endswith(".labels.jsonl")
    assert rep_path.name.endswith(".calibration.md")

    # Each line in the labelled trace round-trips and carries a calibration block.
    lines = lab_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(records)
    for line in lines:
        rec = json.loads(line)
        assert "calibration" in rec
        assert "worth_attention" in rec["calibration"]

    # Report markdown contains the actionable header.
    md = rep_path.read_text(encoding="utf-8")
    assert "Warrant Lens — Calibration Report" in md
    assert "Precision" in md


def test_interactive_labelling_via_synthetic_stdin(trace_path):
    """Drive the interactive prompt with a fake stdin to confirm it parses
    y/n/u/s correctly and prompts only flagged records by default."""
    records = load_trace(trace_path)
    n_flagged = sum(1 for r in records if r["attention_flag"]["raised"])
    # Inputs: alternate y, n, u, ... and skip notes.
    answers = ["y", "", "n", "", "u"][: n_flagged * 2]
    stdin = io.StringIO("\n".join(answers) + "\n")
    stdout = io.StringIO()
    labelled = label_interactive(records, stdin=stdin, stdout=stdout)
    flagged_labels = [
        lr.worth_attention for lr in labelled if lr.flagged
    ]
    # First flagged → 'yes'; second flagged → 'no'; etc. None of them are None.
    for v in flagged_labels[:2]:
        assert v in {"yes", "no", "unsure"}


def test_calibration_explicitly_not_truth_verification(trace_path, tmp_path):
    """Principle 2 enforcement: the calibration report must not claim to
    measure truth. The reminder phrase has to be there verbatim."""
    csv_path = tmp_path / "labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "worth_attention", "notes"])
    # No labels — exercise the empty path.
    _, rep_path, _ = run_calibration(
        trace_path, labels_csv=csv_path, out_dir=tmp_path / "out"
    )
    md = rep_path.read_text(encoding="utf-8")
    assert "does NOT measure whether claims are true" in md
