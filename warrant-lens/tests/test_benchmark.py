"""Tests for the benchmark module.

Uses MockClient pairs so the machinery is verified deterministically without
hitting the network. Covers: agreement counting, disagreement enumeration,
file outputs, and the symmetric self-benchmark (a client compared to itself
must show 100% agreement).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from warrant_lens.anthropic_client import MockClient
from warrant_lens.benchmark import run_benchmark, write_benchmark
from warrant_lens.llm_client import HeuristicClient, Restatement


CORPUS = (
    "Global emissions rose 42% last year. "
    "A vector is defined as an ordered tuple of numbers. "
    "Smoking causes lung cancer (Smith et al. 2003)."
)


def test_benchmark_self_compare_is_total_agreement():
    """A client benchmarked against itself must agree on every claim."""
    h = HeuristicClient()
    report = run_benchmark(
        CORPUS, client_a=h, client_b=h,
        client_a_name="heuristic", client_b_name="heuristic-clone",
    )
    assert report.n_type_agree == report.n_claims
    assert report.n_flag_agree == report.n_claims
    assert report.type_disagreements == []
    assert report.flag_disagreements == []
    assert report.type_agreement_rate == 1.0
    assert report.flag_agreement_rate == 1.0


def test_benchmark_finds_classification_disagreements():
    """Construct two MockClients that classify the same text differently and
    confirm the report surfaces the disagreement."""
    text = "Global emissions rose 42% last year."
    client_a = MockClient(
        classify_responses={text: "specific_statistic"},
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    client_b = MockClient(
        classify_responses={text: "consequential_empirical"},
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    report = run_benchmark(
        text, client_a=client_a, client_b=client_b,
        client_a_name="mock_a", client_b_name="mock_b",
    )
    assert report.n_claims == 1
    assert report.n_type_agree == 0
    assert len(report.type_disagreements) == 1
    d = report.type_disagreements[0]
    assert d.a_type == "specific_statistic"
    assert d.b_type == "consequential_empirical"


def test_benchmark_finds_flag_disagreements():
    """One client classifies as definition (silent), the other as
    consequential_empirical (gets flagged). Flag disagreement is captured."""
    text = "Global emissions rose 42% last year."
    client_a = MockClient(
        classify_responses={text: "definition"},  # silent
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    client_b = MockClient(
        classify_responses={text: "specific_statistic"},  # demanding → flagged
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    report = run_benchmark(text, client_a=client_a, client_b=client_b)
    assert report.n_flag_agree == 0
    assert len(report.flag_disagreements) == 1
    d = report.flag_disagreements[0]
    assert d.a_flagged is False
    assert d.b_flagged is True


def test_benchmark_writes_json_and_markdown(tmp_path):
    h = HeuristicClient()
    report = run_benchmark(CORPUS, client_a=h, client_b=h)
    json_path, md_path = write_benchmark(
        report, tmp_path, topic="self-test"
    )
    assert json_path.exists()
    assert md_path.exists()
    # Filename convention check.
    assert "WARRANTLENS__BENCHMARK__self-test__v1.0__" in json_path.name
    assert json_path.name.endswith(".json")
    assert md_path.name.endswith(".md")
    # JSON is round-trippable.
    data = json.loads(json_path.read_text())
    assert data["n_claims"] == report.n_claims
    assert data["type_agreement_rate"] == report.type_agreement_rate
    # Markdown carries the headline numbers.
    md = md_path.read_text()
    assert "Headline numbers" in md
    assert "Claim-type agreement" in md
    assert "does NOT measure truth" in md  # Principle 2 reminder


def test_benchmark_counts_unclassified_per_client():
    """The unclassified-count is a critical signal for whether the LLM
    closes the recall gap. Make sure it's reported per client."""
    text = "Carbon offsets are widely used by hyperscalers."
    client_a = MockClient(
        classify_responses={},  # default_class is "unclassified"
        restate_responses={},
    )
    client_b = MockClient(
        classify_responses={text: "consequential_empirical"},
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    report = run_benchmark(text, client_a=client_a, client_b=client_b)
    assert report.a_unclassified == 1
    assert report.b_unclassified == 0


def test_benchmark_markdown_lists_disagreements_with_snippet():
    """Disagreement tables in the markdown must show the actual claim text
    so a reader can spot-check who's right."""
    text = "Smoking causes lung cancer (Smith et al. 2003)."
    client_a = MockClient(
        classify_responses={text: "causal_mechanism"},
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    client_b = MockClient(
        classify_responses={text: "named_citation"},
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    report = run_benchmark(text, client_a=client_a, client_b=client_b)
    from warrant_lens.benchmark import _render_markdown
    md = _render_markdown(report)
    assert "causal_mechanism" in md
    assert "named_citation" in md
    assert "Smoking causes lung cancer" in md
