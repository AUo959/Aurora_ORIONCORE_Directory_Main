"""Tests for the production-client code path WITHOUT hitting the network.

Uses MockClient (drop-in test double) and a fake SDK to verify:
  - The pipeline accepts MockClient in place of HeuristicClient.
  - AnthropicClient parses well-formed JSON replies into ClaimType + Restatement.
  - AnthropicClient is defensive against malformed/empty replies and never
    raises into the pipeline (Principle 9: honest about the residual).
"""
from __future__ import annotations

from dataclasses import dataclass

from warrant_lens.anthropic_client import (
    AnthropicClient,
    MockClient,
    _parse_first_json_object,
)
from warrant_lens.config_loader import load_app_config, load_fit_table, load_taxonomy
from warrant_lens.llm_client import Restatement
from warrant_lens.pipeline import analyze, flagged_claims


# ---------- MockClient drop-in ----------

def test_pipeline_accepts_mock_client_instead_of_heuristic():
    """The pipeline depends only on the LLMClient protocol, never on the
    concrete HeuristicClient. Swapping a MockClient must not change pipeline
    behaviour structurally."""
    text = "Global emissions rose 42% last year."
    mock = MockClient(
        classify_responses={text: "specific_statistic"},
        restate_responses={text: Restatement(text=text, extensions=tuple())},
    )
    result = analyze(
        text,
        client=mock,
        taxonomy=load_taxonomy(),
        fit_table=load_fit_table(),
        app_config=load_app_config(),
    )
    flagged = flagged_claims(result.records)
    assert len(flagged) == 1
    assert flagged[0].attention_flag.reason_code == "NO_SOURCE"
    assert flagged[0].tool_restatement == text


# ---------- AnthropicClient response parsing ----------

@dataclass
class _Block:
    text: str


@dataclass
class _Response:
    content: list


class _FakeMessages:
    def __init__(self, replies: list[str]):
        self._replies = list(replies)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self._replies.pop(0) if self._replies else ""
        return _Response(content=[_Block(text=text)])


class _FakeSDK:
    def __init__(self, replies: list[str]):
        self.messages = _FakeMessages(replies)


def test_anthropic_client_parses_valid_classify_response():
    client = AnthropicClient(api_key="test-key")
    client._sdk_client = _FakeSDK(['{"claim_type": "specific_statistic"}'])
    assert client.classify_claim("Global emissions rose 42%.") == "specific_statistic"


def test_anthropic_client_parses_valid_restate_response():
    client = AnthropicClient(api_key="test-key")
    client._sdk_client = _FakeSDK([
        '{"restatement": "Emissions rose 42 percent.", "extensions": ["normalized number format"]}'
    ])
    r = client.restate_claim("Global emissions rose 42%.")
    assert r.text == "Emissions rose 42 percent."
    assert r.extensions == ("normalized number format",)


def test_anthropic_client_rejects_label_outside_closed_set():
    """Defensive: if the model returns a label we don't recognise, return
    unclassified rather than risk a silent miscategorisation."""
    client = AnthropicClient(api_key="test-key")
    client._sdk_client = _FakeSDK(['{"claim_type": "marketing_speak"}'])
    assert client.classify_claim("Tomorrow's leader, today.") == "unclassified"


def test_anthropic_client_handles_empty_response():
    """A non-JSON / empty reply must not crash the pipeline."""
    client = AnthropicClient(api_key="test-key")
    client._sdk_client = _FakeSDK([""])
    assert client.classify_claim("Some text.") == "unclassified"
    # restate returns the source text with a self-seam marker, never raises.
    r = client.restate_claim("Some text.")
    assert r.text == "Some text."
    assert any("no usable output" in e for e in r.extensions)


def test_anthropic_client_handles_prose_wrapped_json():
    """The system prompt tells the model to return only JSON; if it disobeys
    and wraps the JSON in prose, we still recover."""
    client = AnthropicClient(api_key="test-key")
    client._sdk_client = _FakeSDK([
        'Here is the classification you asked for: {"claim_type": "definition"} -- happy to refine.'
    ])
    assert client.classify_claim("A vector is an ordered tuple.") == "definition"


def test_anthropic_client_handles_sdk_exception_gracefully():
    """A transient SDK failure must NOT raise into the pipeline; trace records
    'unclassified' and the human can re-run."""
    class _BrokenSDK:
        class _Msgs:
            def create(self, **kwargs):
                raise RuntimeError("network down")
        messages = _Msgs()

    client = AnthropicClient(api_key="test-key")
    client._sdk_client = _BrokenSDK()
    assert client.classify_claim("anything") == "unclassified"
    r = client.restate_claim("anything")
    assert r.text == "anything"
    assert r.extensions  # has a self-seam marker explaining the failure


# ---------- helpers ----------

def test_parse_first_json_object_finds_embedded_json():
    assert _parse_first_json_object('blah {"a": 1} blah') == {"a": 1}
    assert _parse_first_json_object('{"a": 1, "b": 2}') == {"a": 1, "b": 2}
    assert _parse_first_json_object("no json here") is None
    assert _parse_first_json_object("") is None
