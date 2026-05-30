"""Production LLMClient backed by the Anthropic API.

ISOLATION INVARIANT (SPEC §11): the `anthropic` SDK is imported ONLY here.
classify and restate continue to depend on the LLMClient Protocol; this file
is the single seam where a model call enters the pipeline. Nothing else in
the package reaches the network.

Determinism notes:
  - temperature=0 by default so the same input yields the same classification.
  - The model is told the taxonomy verbatim and required to return EXACTLY one
    label from a closed set; unparseable replies fall back to "unclassified".
  - The restate prompt forbids the model from adding judgment / opinion;
    self-seam markers are emitted only when the model explicitly declares them.

Configuration:
  - API key: env ANTHROPIC_API_KEY (loaded lazily).
  - Model:   env WARRANT_LENS_MODEL or constructor arg (default below).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

from .llm_client import Restatement


DEFAULT_MODEL = "claude-sonnet-4-6"


# Closed-set of labels the API may return. Anything outside this set is
# treated as classifier failure (→ "unclassified") rather than risking a
# silent miscategorisation. Mirror of taxonomy.yaml keys.
_VALID_CLAIM_TYPES = (
    "specific_statistic",
    "named_citation",
    "temporal_fact",
    "causal_mechanism",
    "code_api_signature",
    "consequential_empirical",
    "definition",
    "opinion_normative",
    "hedge_uncertainty",
    "unclassified",
)


_CLASSIFY_SYSTEM = """You are the classification stage of Warrant Lens.

Your ONLY job: given a single sentence, output exactly one label from this set:
  - specific_statistic        (a numeric/percentage claim about the world)
  - named_citation            (an explicit reference to a source by name)
  - temporal_fact             (a claim about WHEN something occurred — a date fact)
  - causal_mechanism          (a claim that X causes/leads-to Y)
  - code_api_signature        (a claim about a programming API or signature)
  - consequential_empirical   (a substantive empirical claim about the world)
  - definition                (a definition of a term or concept)
  - opinion_normative         (a value judgment, "should", "wrong", "beautiful")
  - hedge_uncertainty         (a claim hedged with "may", "might", "I think")
  - unclassified              (none of the above, or unclear)

Output format: a single JSON object on one line:
  {"claim_type": "<label>"}

Do not output anything else. Do not assess truth. Do not pick more than one
label. If multiple apply, prefer the one with stronger evidentiary demand
(specific_statistic > named_citation > temporal_fact > causal_mechanism >
consequential_empirical). Hedges and opinions always win over their substantive
counterparts because they cannot be flagged.
"""


_RESTATE_SYSTEM = """You are the restatement stage of Warrant Lens.

Your job: produce a faithful paraphrase of the claim being tested. The
paraphrase will be shown to the human user adjacent to a structural flag and
the user can reject it — wrongness here voids the flag, not the claim.

Hard rules:
  1. Do not assess truth. Do not endorse or deny the claim.
  2. Do not add scope, qualifications, or causal structure the source did not
     contain. If you find yourself doing so, list it under "extensions".
  3. Do not flatten away qualifications the source DID contain (e.g.
     "approximately", "in the United States", "since 1990").
  4. Strip a leading epistemic hedge ("I think", "It seems") ONLY if you
     declare that strip under "extensions".
  5. Keep the same epistemic status — if the source asserts, the paraphrase
     asserts; if the source hedges, the paraphrase hedges.

Output format: a single JSON object on one line:
  {"restatement": "<paraphrase>", "extensions": ["<each self-seam>", ...]}

extensions is an empty array when the paraphrase is purely a paraphrase.
"""


@dataclass
class AnthropicClient:
    """Production LLMClient. Implements the LLMClient Protocol implicitly via
    duck typing — no inheritance needed since Protocol is structural."""

    model: str = ""
    api_key: Optional[str] = None
    max_tokens_classify: int = 64
    max_tokens_restate: int = 512
    temperature: float = 0.0
    _sdk_client: object = None  # lazy

    def __post_init__(self) -> None:
        if not self.model:
            self.model = os.environ.get("WARRANT_LENS_MODEL", DEFAULT_MODEL)
        if not self.api_key:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")

    # ---- LLMClient Protocol ----

    def classify_claim(self, text: str) -> str:
        if not text.strip():
            return "unclassified"
        client = self._client()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens_classify,
                temperature=self.temperature,
                system=_CLASSIFY_SYSTEM,
                messages=[{"role": "user", "content": text.strip()}],
            )
            payload = _extract_text(response)
            obj = _parse_first_json_object(payload)
            label = (obj or {}).get("claim_type", "")
            if label in _VALID_CLAIM_TYPES:
                return label
            return "unclassified"
        except Exception:
            # Defensive: a transient SDK / network failure must NOT crash the
            # pipeline. The trace will record "unclassified" and the human
            # can re-run. Principle 9: honest about the residual.
            return "unclassified"

    def restate_claim(self, text: str) -> Restatement:
        if not text.strip():
            return Restatement(text="", extensions=tuple())
        client = self._client()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens_restate,
                temperature=self.temperature,
                system=_RESTATE_SYSTEM,
                messages=[{"role": "user", "content": text.strip()}],
            )
            payload = _extract_text(response)
            obj = _parse_first_json_object(payload) or {}
            restatement = str(obj.get("restatement", "")).strip()
            raw_ext = obj.get("extensions", [])
            extensions = tuple(str(x) for x in raw_ext if isinstance(x, str))
            if not restatement:
                # Failure mode: pass through the original text rather than
                # invent a restatement. Marks the no-op as a self-seam so the
                # human knows the tool did not actually restate.
                return Restatement(
                    text=text.strip(),
                    extensions=("restatement model returned no usable output; "
                                "showing source text unchanged",),
                )
            return Restatement(text=restatement, extensions=extensions)
        except Exception:
            return Restatement(
                text=text.strip(),
                extensions=("restatement model call failed; "
                            "showing source text unchanged",),
            )

    # ---- internals ----

    def _client(self):
        if self._sdk_client is not None:
            return self._sdk_client
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "AnthropicClient requires the 'anthropic' package. "
                "Install with: pip install anthropic"
            ) from e
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it or pass api_key=..."
            )
        self._sdk_client = anthropic.Anthropic(api_key=self.api_key)
        return self._sdk_client


# ---- helpers ----

_JSON_OBJ_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _extract_text(response) -> str:
    """Pull text out of the SDK response shape, defensively."""
    # anthropic SDK: response.content is a list of blocks; .text on the first
    # text block. Be defensive in case the shape evolves.
    try:
        for block in getattr(response, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                return text
    except Exception:
        pass
    return ""


def _parse_first_json_object(s: str) -> Optional[dict]:
    """Find and parse the first {...} object in the string. Tolerates the
    model wrapping its output in prose despite system-prompt orders."""
    if not s:
        return None
    # Fast path: the whole string is valid JSON.
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # Fallback: scan for the first balanced-ish object substring.
    for m in _JSON_OBJ_RE.finditer(s):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# MockClient — drop-in test double for the production client. Lets tests
# exercise the AnthropicClient code path without hitting the network.
# ---------------------------------------------------------------------------

@dataclass
class MockClient:
    """Test double. Returns whatever you script."""
    classify_responses: dict[str, str]
    restate_responses: dict[str, Restatement]
    default_class: str = "unclassified"
    default_restatement: str = ""

    def classify_claim(self, text: str) -> str:
        return self.classify_responses.get(text.strip(), self.default_class)

    def restate_claim(self, text: str) -> Restatement:
        return self.restate_responses.get(
            text.strip(),
            Restatement(text=self.default_restatement or text.strip(), extensions=tuple()),
        )
