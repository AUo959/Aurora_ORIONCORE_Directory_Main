"""Lift verifiable claims out of markdown text.

Extraction is deliberately conservative: we only emit a claim when the text
gives us something a ground-truth verifier can actually check. Noise (URLs,
shield badges, anchor links) is filtered here so the ledger stays checkable.
"""

from __future__ import annotations

import re

from .models import Claim, ClaimType

# A repo-relative-looking path inside inline code: has a slash or a file extension,
# no scheme, no spaces. e.g. `tools/foo.py`, `docs/X.md`, `pyproject.toml`
_PATH_RE = re.compile(r"`([A-Za-z0-9_.\-/]+(?:/[A-Za-z0-9_.\-/]+|\.[A-Za-z0-9]{1,6}))`")
# Fenced-code lines and headings we skip for path noise.
_URLISH = re.compile(r"^[a-z]+://|badge|shields\.io|@|^#")

# function/method call in inline code: `name(` optionally `mod.name(`
_FUNC_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)\(\)?`")
# explicit "function/class `name`" phrasing, optionally "... in `file`"
_SYMBOL_PHRASE_RE = re.compile(
    r"(?:function|method|class|def|route|endpoint)\s+`([A-Za-z_][A-Za-z0-9_.]*)`"
    r"(?:\s+(?:in|at|from)\s+`([A-Za-z0-9_.\-/]+)`)?",
    re.IGNORECASE,
)

# "<N> <noun>" count claims, noun captured as the counting subject.
_COUNT_RE = re.compile(
    r"\b(\d{1,6})\s+([A-Za-z][A-Za-z_\-]{2,30})\b"
)
_COUNT_NOUNS = {
    "docs", "documents", "files", "tests", "modules", "scripts", "tools",
    "workflows", "specs", "commands", "endpoints", "routes", "entries",
}

# version strings: v2.2, 2.1.0, version 2.2.5
_VERSION_RE = re.compile(
    r"(?<![\w.])(?:v(?:ersion)?\.?\s*)?(\d+\.\d+(?:\.\d+)?)(?![\w.])",
    re.IGNORECASE,
)
_VERSION_CONTEXT = re.compile(r"\bv(?:ersion)?\b|\brelease\b", re.IGNORECASE)


def _skip_line(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("![") or "shields.io" in stripped


def _path_hits(line: str):
    for m in _PATH_RE.finditer(line):
        token = m.group(1)
        if _URLISH.search(token) or token.count(".") > 6:
            continue
        # a slash-free token is only a file if it has a lowercase-ish extension;
        # skip dotted identifiers like `ORION.ROLE.PILOT`.
        if "/" not in token and not re.search(r"\.[a-z][a-z0-9]{0,5}$", token):
            continue
        yield ("path", ClaimType.PATH, token, {})


def _symbol_hits(line: str):
    for m in _SYMBOL_PHRASE_RE.finditer(line):
        name, file_hint = m.group(1), m.group(2)
        yield ("sym", ClaimType.SYMBOL, name,
               {"file_hint": file_hint} if file_hint else {})
    for m in _FUNC_RE.finditer(line):
        name = m.group(1)
        if "." in name and "/" in name:
            continue
        yield ("sym", ClaimType.SYMBOL, name, {"callable": True})


def _count_version_hits(line: str):
    for m in _COUNT_RE.finditer(line):
        n, noun = m.group(1), m.group(2).lower()
        if noun in _COUNT_NOUNS:
            yield ("num", ClaimType.NUMERIC, n, {"noun": noun})
    if _VERSION_CONTEXT.search(line):
        for m in _VERSION_RE.finditer(line):
            yield ("ver", ClaimType.VERSION, m.group(1), {})


def _iter_line_hits(line: str):
    """Yield (kind, value, context) for every checkable token on one line."""
    yield from _path_hits(line)
    yield from _symbol_hits(line)
    yield from _count_version_hits(line)


def extract_claims(doc_path: str, text: str) -> list[Claim]:
    claims: list[Claim] = []
    in_fence = False
    seq = 0

    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or _skip_line(line):
            continue
        for kind, ctype, value, context in _iter_line_hits(line):
            seq += 1
            claims.append(Claim(
                id=f"{doc_path}::{kind}{seq}", type=ctype, doc_path=doc_path,
                doc_line=lineno, raw_text=line.strip(), value=value,
                context=context,
            ))

    return _dedupe(claims)


def _dedupe(claims: list[Claim]) -> list[Claim]:
    seen: set[tuple] = set()
    out: list[Claim] = []
    for c in claims:
        key = (c.type, c.doc_path, c.doc_line, c.value)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out
