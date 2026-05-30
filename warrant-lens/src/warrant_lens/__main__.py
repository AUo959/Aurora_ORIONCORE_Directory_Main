"""CLI entrypoint: `warrant-lens analyze <path> [--trace-dir DIR] [--topic NAME]`.

Emits the inline-annotated text to stdout and writes the JSONL trace to disk.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .benchmark import run_benchmark, write_benchmark
from .calibrate import run_calibration
from .config_loader import load_app_config, load_fit_table, load_taxonomy
from .emit_html import render_html
from .emit_inline import render as render_inline
from .emit_trace import write_trace
from .llm_client import HeuristicClient, LLMClient
from .pipeline import analyze


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="warrant-lens")
    sub = parser.add_subparsers(dest="cmd", required=True)

    analyze_p = sub.add_parser("analyze", help="Run the pipeline on a text file.")
    analyze_p.add_argument("path", type=Path, help="Input text file.")
    analyze_p.add_argument(
        "--trace-dir",
        type=Path,
        default=Path("traces"),
        help="Directory to write the JSONL trace into.",
    )
    analyze_p.add_argument(
        "--topic", default="untopiced", help="Topic slug for the trace filename."
    )
    analyze_p.add_argument(
        "--directness",
        choices=("gentle", "direct"),
        default=None,
        help="Override delivery.directness for this run (phrasing only).",
    )
    analyze_p.add_argument(
        "--client",
        choices=("heuristic", "anthropic"),
        default="heuristic",
        help="Which LLMClient to use for classify/restate. 'anthropic' requires "
        "ANTHROPIC_API_KEY and `pip install warrant-lens[anthropic]`.",
    )
    analyze_p.add_argument(
        "--html",
        type=Path,
        default=None,
        help="Write a self-contained HTML inline-annotation viewer to this path.",
    )

    bench_p = sub.add_parser(
        "benchmark",
        help="Compare two LLMClients on the same corpus. Writes a markdown "
        "report and a machine-readable JSON diff.",
    )
    bench_p.add_argument("path", type=Path, help="Input text file.")
    bench_p.add_argument(
        "--a", choices=("heuristic", "anthropic"), default="heuristic",
        help="Client A (left column).",
    )
    bench_p.add_argument(
        "--b", choices=("heuristic", "anthropic"), default="anthropic",
        help="Client B (right column).",
    )
    bench_p.add_argument(
        "--topic", default="benchmark",
        help="Topic slug for the report filename.",
    )
    bench_p.add_argument(
        "--out-dir", type=Path, default=Path("traces"),
        help="Directory to write the benchmark report into.",
    )

    calib_p = sub.add_parser(
        "calibrate",
        help="Score a JSONL trace against human attention labels. "
        "Computes precision (and best-effort recall).",
    )
    calib_p.add_argument("trace", type=Path, help="JSONL trace file.")
    calib_p.add_argument(
        "--labels",
        type=Path,
        default=None,
        help="CSV with columns: claim_id, worth_attention (yes|no|unsure), notes.",
    )
    calib_p.add_argument(
        "--interactive", action="store_true",
        help="Label at the terminal instead of from CSV.",
    )
    calib_p.add_argument(
        "--label-silent", action="store_true",
        help="(interactive only) Also label unflagged claims; required for recall.",
    )
    calib_p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Where to write the labelled trace + report. Defaults to alongside the trace.",
    )

    args = parser.parse_args(argv)

    if args.cmd == "calibrate":
        return _cmd_calibrate(args)
    if args.cmd == "benchmark":
        return _cmd_benchmark(args)
    if args.cmd != "analyze":
        parser.error("unknown command")
        return 2

    text = args.path.read_text(encoding="utf-8")

    taxonomy = load_taxonomy()
    fit_table = load_fit_table()
    app_config = load_app_config()

    if args.directness:
        # Build a delivery override without mutating disk config.
        from dataclasses import replace

        app_config = replace(
            app_config, delivery=replace(app_config.delivery, directness=args.directness)
        )

    client: LLMClient
    if args.client == "anthropic":
        from .anthropic_client import AnthropicClient
        client = AnthropicClient()
    else:
        client = HeuristicClient()

    result = analyze(
        text,
        taxonomy=taxonomy,
        fit_table=fit_table,
        app_config=app_config,
        client=client,
    )

    annotated, _ = render_inline(text, result.records, app_config.delivery)
    sys.stdout.write(annotated)
    if not annotated.endswith("\n"):
        sys.stdout.write("\n")

    trace_path = write_trace(result.records, args.trace_dir, args.topic)
    sys.stderr.write(f"[warrant-lens] trace written: {trace_path}\n")

    if args.html:
        html_out = render_html(
            text,
            result.records,
            app_config.delivery,
            title=f"Warrant Lens — {args.topic}",
            standard_invoked=result.standard_invoked,
        )
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(html_out.html, encoding="utf-8")
        sys.stderr.write(f"[warrant-lens] html viewer:   {args.html}\n")

    return 0


def _cmd_benchmark(args) -> int:
    def _make_client(name: str) -> LLMClient:
        if name == "anthropic":
            from .anthropic_client import AnthropicClient
            return AnthropicClient()
        return HeuristicClient()

    text = args.path.read_text(encoding="utf-8")
    client_a = _make_client(args.a)
    client_b = _make_client(args.b)
    report = run_benchmark(
        text,
        client_a=client_a, client_b=client_b,
        client_a_name=args.a, client_b_name=args.b,
    )
    json_path, md_path = write_benchmark(report, args.out_dir, topic=args.topic)
    sys.stderr.write(f"[warrant-lens] benchmark json: {json_path}\n")
    sys.stderr.write(f"[warrant-lens] benchmark md:   {md_path}\n")
    sys.stderr.write(
        f"[warrant-lens] type-agreement: {report.n_type_agree}/{report.n_claims}"
        f" ({report.type_agreement_rate:.1%})\n"
    )
    sys.stderr.write(
        f"[warrant-lens] flag-agreement: {report.n_flag_agree}/{report.n_claims}"
        f" ({report.flag_agreement_rate:.1%})\n"
    )
    return 0


def _cmd_calibrate(args) -> int:
    if not args.labels and not args.interactive:
        sys.stderr.write(
            "error: provide --labels CSV or pass --interactive\n"
        )
        return 2
    if args.labels and args.interactive:
        sys.stderr.write(
            "error: --labels and --interactive are mutually exclusive\n"
        )
        return 2

    lab_path, rep_path, report = run_calibration(
        args.trace,
        labels_csv=args.labels,
        interactive=args.interactive,
        label_silent=args.label_silent,
        out_dir=args.out_dir,
    )
    sys.stderr.write(f"[warrant-lens] labelled trace: {lab_path}\n")
    sys.stderr.write(f"[warrant-lens] report:         {rep_path}\n")
    if report.precision is not None:
        sys.stderr.write(f"[warrant-lens] precision:      {report.precision:.3f}\n")
    if report.recall is not None:
        sys.stderr.write(f"[warrant-lens] recall:         {report.recall:.3f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
