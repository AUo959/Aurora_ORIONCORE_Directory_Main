"""Regression tests for v1.1 fixes — each one was a real dogfood finding.

If these regress, the heuristic has lost ground on real-world prose. Keep
them next to the spec acceptance tests; they're equally load-bearing now.
"""
from __future__ import annotations

import pytest

from warrant_lens.config_loader import load_app_config, load_fit_table, load_taxonomy
from warrant_lens.llm_client import HeuristicClient
from warrant_lens.pipeline import analyze, flagged_claims
from warrant_lens.warrant import ClaimContext, extract_inline_source


@pytest.fixture(scope="module")
def client():
    return HeuristicClient()


# ---------- Issue 1: broaden empirical-hint regex ----------

@pytest.mark.parametrize("text", [
    "Data center electricity consumption is rising.",
    "Inference is now the larger share of total AI carbon cost.",
    "Mortality declined steadily across the period.",
    "GDP growth is slowing across the OECD.",
    "Workload demand jumped by a factor of three.",
])
def test_v11_broader_empirical_vocab_now_classified(text, client):
    """Real-world empirical claims that v1.0 returned 'unclassified' for."""
    label = client.classify_claim(text)
    assert label != "unclassified", f"{text!r} should classify as empirical-something"
    assert label in {"consequential_empirical", "specific_statistic", "temporal_fact"}


# ---------- Issue 2: source extractor accepts articles ----------

def test_v11_source_extractor_handles_the_article():
    """'According to the IEA' must be detected. v1.0 missed it because the
    regex required a capital after the trigger word, blocking 'the'."""
    text = "According to the IEA, data center demand could reach 945 TWh by 2030."
    src, locatable = extract_inline_source(text)
    assert src is not None
    assert "IEA" in src
    assert locatable is True


def test_v11_source_extractor_handles_per_the():
    text = "Per the official press release, the initial $100B is being deployed."
    src, locatable = extract_inline_source(text)
    assert src is not None
    assert locatable is True


# ---------- Issue 3: code-api regex no longer over-triggers on citation parens ----------

def test_v11_citation_paren_does_not_become_code_api(client):
    """v1.0 classified this as code_api_signature because 'vehicles (Brown...'
    matched the loose function-call regex."""
    text = (
        "In 2018, researchers at MIT demonstrated that adversarial patches "
        "could fool object detectors used in autonomous vehicles (Brown et al., 2017)."
    )
    label = client.classify_claim(text)
    assert label != "code_api_signature"


def test_v11_real_code_api_still_classifies_as_code_api(client):
    """Tightening must not break the legitimate case."""
    text = (
        "openai.chat.completions.create(model='gpt-4', messages=[...]) returns "
        "a ChatCompletion object."
    )
    assert client.classify_claim(text) == "code_api_signature"


# ---------- Issue 4: FRONTIER_HANDOFF gated to empirical-ish claim types ----------

def test_v11_code_api_claim_does_not_get_frontier_handoff():
    """A code-api signature has docs-vs-not, NOT settled-vs-frontier.
    Firing FRONTIER_HANDOFF on it is nonsense."""
    text = "The function openai.chat.completions.create(model=...) returns a ChatCompletion."
    result = analyze(
        text,
        taxonomy=load_taxonomy(),
        fit_table=load_fit_table(),
        app_config=load_app_config(),
        # settled deliberately left None — would have triggered frontier in v1.0
        contexts={0: ClaimContext(
            domain="general_empirical",
            observed_source_class="official_docs",
            source_text="OpenAI Python SDK docs",
            source_role="primary",
            settled=None,
        )},
    )
    for r in flagged_claims(result.records):
        assert r.attention_flag.reason_code != "FRONTIER_HANDOFF", (
            "code_api_signature must not receive a frontier handoff"
        )


def test_v11_empirical_claim_still_gets_frontier_handoff():
    """The gate must NOT block frontier handoffs on the claim types where
    they're meaningful — otherwise T-FRONTIER would silently break."""
    text = "Compound X causes apoptosis in liver cells (Doe 2024)."
    result = analyze(
        text,
        taxonomy=load_taxonomy(),
        fit_table=load_fit_table(),
        app_config=load_app_config(),
        contexts={0: ClaimContext(
            domain="general_empirical",
            observed_source_class="peer_reviewed_primary_body",
            source_text="Doe 2024",
            source_role="primary",
            settled=None,
        )},
    )
    flagged = flagged_claims(result.records)
    assert flagged
    assert flagged[0].attention_flag.reason_code == "FRONTIER_HANDOFF"


# ---------- Issue 5: empirical+number wins over bare year ----------

def test_v11_statistic_with_year_classifies_as_statistic_not_temporal(client):
    """'emitted 552 metric tons in 2024' is a statistic, not a date fact."""
    text = "Training a single large language model in 2024 emitted roughly 552 metric tons of CO2."
    label = client.classify_claim(text)
    assert label == "specific_statistic"


# ---------- Bonus: causal regex now recognises scientific vocabulary ----------

@pytest.mark.parametrize("text,expected", [
    ("Compound X induces apoptosis in liver cells.", "causal_mechanism"),
    ("Statin Y inhibits HMG-CoA reductase.", "causal_mechanism"),
    ("Drug Z suppresses inflammation via the IL-6 pathway.", "causal_mechanism"),
    ("Receptor A activates the downstream kinase.", "causal_mechanism"),
])
def test_v11_scientific_causal_vocab_now_recognised(text, expected, client):
    assert client.classify_claim(text) == expected
