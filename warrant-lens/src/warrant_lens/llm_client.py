"""LLMClient protocol + deterministic HeuristicClient stub.

SPEC §11 requirement: classify and restate MAY call an LLM internally. If
they do, that call is the ONLY model dependency and must be swappable/mockable
for tests. v1 ships HeuristicClient — pure rules, no network — and defines
the protocol for swap-in production clients.

The protocol is intentionally minimal: classify returns a claim_type label,
restate returns a paraphrase plus self-seam markers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Restatement:
    text: str
    extensions: tuple[str, ...]
    """Self-seam markers (Principle 7): where the restatement adds structure
    the source text did not supply. Empty when the restatement is pure paraphrase."""


class LLMClient(Protocol):
    def classify_claim(self, text: str) -> str:
        """Return a claim_type from taxonomy.yaml."""
        ...

    def restate_claim(self, text: str) -> Restatement:
        """Return the tool's restatement of the claim being tested (Principle 7)."""
        ...


# ---------------------------------------------------------------------------
# HeuristicClient — deterministic stub for v1 tests. Recognises the patterns
# the acceptance tests in §9 actually require. Production swaps this for a
# real client implementing the same protocol.
# ---------------------------------------------------------------------------

_PCT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")
_NUMERIC_RE = re.compile(r"\b\d{2,}\b")
_YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2}|21\d{2})\b")
_DATE_PHRASE_RE = re.compile(
    r"\b(in|on|by|since|before|after)\s+(?:the\s+)?(?:year\s+)?\d{3,4}\b",
    re.IGNORECASE,
)
_HEDGE_RE = re.compile(
    r"\b(might|may|perhaps|possibly|likely|seems|appears|i think|in my view|i believe)\b",
    re.IGNORECASE,
)
_OPINION_RE = re.compile(
    r"\b(should|ought to|must (?:be|do)|is (?:wrong|right|beautiful|ugly|evil|good|bad))\b",
    re.IGNORECASE,
)
_DEFINITION_RE = re.compile(
    r"\bis\s+(?:defined\s+as|the\s+study\s+of|a\s+(?:term|word|concept)\s+for)\b",
    re.IGNORECASE,
)
_CAUSAL_RE = re.compile(
    r"\b("
    r"causes?|leads? to|results? in|is caused by|because|due to|"
    # Scientific / mechanism vocabulary
    r"induces?|triggers?|drives?|produces?|generates?|inhibits?|suppresses?|"
    r"activates?|prevents?|reduces?|raises?|amplifies?|attenuates?|mediates?"
    r")\b",
    re.IGNORECASE,
)
_CODE_API_RE = re.compile(
    # Identifier IMMEDIATELY followed by '(' — real code rarely has whitespace
    # before the open paren. Or a method call (.name(). Or backticked code.
    r"(?:"
    r"\b[a-z_][a-z0-9_]*\([^)]*\)"          # foo(...)
    r"|\.[a-z_][a-z0-9_]*\("                 # .method(
    r"|\b[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*" # module.method
    r"|`[^`]+`"                              # `inline code`
    r")",
    re.IGNORECASE,
)
_CITATION_HINT_RE = re.compile(
    r"(?:"
    # Parenthetical: (Brown et al., 2017), (Smith, 2003), (Brown and Smith 2003)
    r"\(\s*[A-Z][A-Za-z'\-]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][A-Za-z'\-]+))?\s*,?\s*\d{4}\s*\)"
    # Author-year free: see Brown 2017, per Smith et al. 2003
    r"|\b(?:see|cf\.|per)\s+[A-Z][A-Za-z'\-]+(?:\s+et\s+al\.?)?\s+\d{4}\b"
    # DOI / arXiv / publisher prefix
    r"|\b(?:doi:|arxiv:)\s*\S+"
    r")",
)
_EMPIRICAL_HINT_RE = re.compile(
    r"\b("
    # nouns (real-world quantities and metrics)
    r"deaths?|cases|emissions?|mortality|incidence|prevalence|rate|rates|temperature|"
    r"warming|GDP|growth|unemployment|consumption|demand|share|cost|costs|"
    r"production|output|revenue|spending|deployment|workload|workloads|"
    # past-tense empirical verbs
    r"warmed|cooled|rose|fell|grew|declined|increased|decreased|dropped|jumped|"
    r"emitted|reached|absorbed|deployed|consumed|reduced|raised|lowered|"
    # progressive forms — "consumption is rising", "share is growing"
    r"rising|falling|growing|shrinking|declining|increasing|decreasing"
    r")\b",
    re.IGNORECASE,
)


class HeuristicClient:
    """Deterministic rule-based classifier + restater. No network.

    Order of checks matters: hedges and opinions short-circuit before numeric
    rules so that "I think 50% is fair" classifies as opinion, not statistic.
    """

    # ---- classification ----

    def classify_claim(self, text: str) -> str:
        t = text.strip()
        if not t:
            return "unclassified"

        if _HEDGE_RE.search(t):
            return "hedge_uncertainty"
        if _OPINION_RE.search(t):
            return "opinion_normative"
        if _DEFINITION_RE.search(t):
            return "definition"

        # Code-api is now strict (requires no whitespace before '('), so it
        # no longer over-triggers on "(Author, YYYY)" citation parens
        # (v1.1 fix — dogfood issue 3, fixed by tightening _CODE_API_RE).
        if _CODE_API_RE.search(t) and not _PCT_RE.search(t):
            return "code_api_signature"

        # Empirical content + a number beats pure temporal_fact. A claim like
        # "emitted 552 metric tons in 2024" is a statistic, not a date fact
        # (v1.1 fix — dogfood issue 5).
        if _PCT_RE.search(t) or (_NUMERIC_RE.search(t) and _EMPIRICAL_HINT_RE.search(t)):
            return "specific_statistic"

        # Causal claims win over temporal_fact and named_citation. A claim
        # "X causes Y (Doe 2024)" is a causal claim with a citation, not a
        # meta-claim about a citation.
        if _CAUSAL_RE.search(t):
            return "causal_mechanism"

        # Empirical content (any form) beats pure temporal — keeps "the
        # planet warmed since 1900" out of temporal_fact (v1.1 fix — issue 1).
        if _EMPIRICAL_HINT_RE.search(t):
            return "consequential_empirical"

        if _DATE_PHRASE_RE.search(t) or _YEAR_RE.search(t):
            return "temporal_fact"

        # Named-citation is now a FALLBACK: it fires only when a citation
        # pattern is present and nothing more substantive matched. A citation
        # is a source marker, not a claim type (v1.1 fix — see test commit).
        if _CITATION_HINT_RE.search(t):
            return "named_citation"

        return "unclassified"

    # ---- restatement (Principle 7) ----

    def restate_claim(self, text: str) -> Restatement:
        """Heuristic paraphrase: strip a leading "I think / it seems" hedge,
        normalize whitespace, and flag the strip as a self-seam if it changed
        the claim's epistemic status. The restatement is shown to the user
        and is rejectable — wrongness here voids the flag, not the tool."""
        t = text.strip()

        extensions: list[str] = []
        stripped = re.sub(
            r"^(?:I think|I believe|In my view|It seems that|It appears that)\s*,?\s*",
            "",
            t,
            flags=re.IGNORECASE,
        )
        if stripped != t:
            extensions.append(
                "Removed a leading epistemic hedge from the source text; "
                "tool is testing the assertion as stated without the hedge."
            )

        # Collapse internal whitespace for readability without altering meaning.
        normalized = re.sub(r"\s+", " ", stripped)
        if not normalized:
            normalized = t

        return Restatement(text=normalized, extensions=tuple(extensions))
