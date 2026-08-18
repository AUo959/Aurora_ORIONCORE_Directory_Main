#!/usr/bin/env python3
"""Extract claims about canon entities from unstructured prose.

Why this exists
---------------
The early project lived almost entirely in prose — design conversations, chat
exports, session logs. Claims made there are canon material and must be salvaged
per the Canon Protocol. They cannot be reached by the tooling built for structured
records, and they are not reachable by looking for *new names* either.

That last point is the lesson this tool encodes. A 2026-08-09 sweep of
`deep_filtered_galactic_union_simulation_conversations` extracted proper nouns and
concluded the prose was "exhausted". It was not. Proper-noun extraction returns
fragments of names already in canon ("Judicator", "Velar", "Zylox"), profile-template
field labels ("Recent Actions", "Decision Style") and reputation metrics ("Fleet
Trust") — noise. The value in prose is **assertions about entities that already
exist**: "Zylox rose to the chancellorship via an alliance of the Trade Coalition,
AI Vanguard and economic technocrats". That sentence is how the Trade Coalition was
found at all, and it was found by accident.

So this tool extracts CLAIMS, not names: sentences that mention a canon entity and
make an assertion about it.

Matching discipline
-------------------
Entity matching is deliberately strict. Two loose-matching errors were made on
2026-08-09 and both would have corrupted canon silently:

  * a surname fallback gave the Elari Luminary *Aelindra Voss-Aurai* the profile of
    *Lyra Voss*, and matched *Lirian Vael-Torin* against *Vael Saros*;
  * a bare-word match on "diplomacy" attributed a discussion of memory allocation
    and embedding similarity to `org_office_of_strategic_diplomacy`.

Shared name fragments and common nouns are everywhere in this setting. A partial
match is not evidence of reference. Hence: word-boundary matches on full entity
names and aliases only, with a stoplist for entity names that are common nouns.

Output is a claim ledger for review. This tool does NOT write canon: claims are
evidence, and evidence goes through the reconciler's conflict scan before anything
is promoted.

Usage
-----
    python3 tools/prose_claim_extractor.py --source <file-or-dir> [--out claims.json]
    python3 tools/prose_claim_extractor.py --source X --entity org_galactic_union
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"

#: Entity names that are also ordinary words. Matching on these produces noise, so a
#: single-word form is only used when it is distinctive.
COMMON_NOUN_NAMES = {
    "diplomacy", "senate", "marshals", "sentinels", "union", "navy", "judiciary",
    "military", "cross", "prime", "core", "vanguard", "collective", "compact",
    "pact", "order", "orders", "clans", "nomads", "empire", "republic",
    # "human" is the hardest case and the reason this list exists.
    #
    # Matching the bare word gave species_human 562 claims in one corpus. The
    # case-sensitive rule below cut that to 57 — and a 2026-08-15 triage of those
    # 57 found only THREE in-world (5%). The rest were real-world news (Musk/DOGE,
    # the UN Human Rights Chief, the Universal Declaration, AP Human Geography)
    # and project engineering prose ("human-in-the-loop", "human interface",
    # "human resources"). Capitalisation cannot separate them: "Human Rights" and
    # "Human Services" are proper nouns in the real world, and title-case headings
    # capitalise everything.
    #
    # The three genuine claims were reconciled by hand on 2026-08-15 (Separatists
    # as "Human Dissidents", the Varlithian Paradox's origin, and the "right to
    # rule" reaction to AI ascendancy). Claims about humans must be reached by
    # DISTINCTIVE multi-word phrases, not by the species name.
    "human", "humans", "humanity",
}

#: A sentence only counts as a claim if it asserts something.
ASSERTIVE = re.compile(
    r"\b(is|was|are|were|has|had|commands?|commanded|leads?|led|founded|serves?|"
    r"served|controls?|controlled|governs?|governed|rules?|ruled|built|created|"
    r"destroyed|defeated|allied|opposes?|opposed|betrayed|negotiated|brokered|"
    r"oversees?|oversaw|holds?|held|operates?|operated|maintains?|maintained|"
    r"established|appoints?|appointed|approves?|approved|passes?|allocates?|"
    r"reports? to|answers? to|consists? of|comprises?)\b",
    re.I,
)

MIN_LEN, MAX_LEN = 40, 400


def load_entity_forms() -> dict[str, str]:
    """Map lowercased surface form -> entity_id, for canon L2 entities."""
    forms: dict[str, str] = {}
    if not CANON_L2.exists():
        return forms
    for path in CANON_L2.rglob("*.json"):
        if "/capsule/" in path.as_posix():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        eid = data.get("entity_id") or data.get("canonical_id")
        if not eid:
            continue
        candidates = set()
        name = data.get("name")
        if isinstance(name, str):
            candidates.add(name)
        for alias in data.get("aliases") or []:
            if isinstance(alias, str):
                candidates.add(alias)
        for form in candidates:
            form = form.strip()
            if len(form) < 5:
                continue
            if " " not in form and form.lower() in COMMON_NOUN_NAMES:
                continue
            forms.setdefault(form.lower(), eid)
    return forms


def iter_text(source: Path):
    """Yield (label, text) from a file or directory. Handles chat-export JSON."""
    paths = [source] if source.is_file() else sorted(
        p for p in source.rglob("*") if p.is_file()
    )
    for path in paths:
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                parts = []
                _collect_chat_parts(data, parts)
                if parts:
                    yield str(path), "\n\n".join(parts)
                    continue
                yield str(path), json.dumps(data)
            elif suffix in (".md", ".txt"):
                yield str(path), path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue


def _collect_chat_parts(node, out: list) -> None:
    """Pull message text out of a ChatGPT-style conversation export."""
    if isinstance(node, dict):
        message = node.get("message")
        if isinstance(message, dict):
            content = message.get("content") or {}
            for part in content.get("parts") or []:
                if isinstance(part, str) and part.strip():
                    out.append(part)
        for value in node.values():
            _collect_chat_parts(value, out)
    elif isinstance(node, list):
        for value in node:
            _collect_chat_parts(value, out)


def extract(text: str, forms: dict[str, str], source: str) -> dict[str, list]:
    """Collect claim sentences per entity.

    Single-word entity names are matched **case-sensitively** against the original
    sentence, so they only fire on proper-noun usage. Without this, `species_human`
    ("Human") matched the bare word "human" 562 times in one corpus and swept in
    AI-architecture discussion — "as the human-AI bridge, Aurora translates human
    commands…". A stoplist cannot keep up with that; requiring capitalisation is the
    general fix. Multi-word names stay case-insensitive: they are distinctive enough
    that casing varies harmlessly.
    """
    claims: dict[str, list] = collections.defaultdict(list)
    multiword = {f: re.compile(r"\b" + re.escape(f) + r"\b") for f in forms if " " in f}
    single = {
        f: re.compile(r"\b" + re.escape(f[:1].upper() + f[1:]) + r"\b")
        for f in forms if " " not in f
    }
    for raw in re.split(r"(?<=[.!?])\s+|\n+", text):
        sentence = " ".join(raw.split())
        if not (MIN_LEN < len(sentence) < MAX_LEN):
            continue
        if not ASSERTIVE.search(sentence):
            continue
        low = sentence.lower()
        hit = None
        for form, rx in multiword.items():
            if rx.search(low):
                hit = form
                break
        if hit is None:
            for form, rx in single.items():
                if rx.search(sentence):  # case-sensitive, original text
                    hit = form
                    break
        if hit is not None:
            claims[forms[hit]].append({"claim": sentence, "matched": hit,
                                       "source": source})
    return claims


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="File or directory of prose")
    ap.add_argument("--out", help="Write the claim ledger here (JSON)")
    ap.add_argument("--entity", help="Only report claims for this entity_id")
    ap.add_argument("--min-claims", type=int, default=1)
    args = ap.parse_args()

    forms = load_entity_forms()
    if not forms:
        print("prose-claim-extractor: no canon entities found — is CanonRec checked out?",
              file=sys.stderr)
        return 1

    merged: dict[str, list] = collections.defaultdict(list)
    for label, text in iter_text(Path(args.source)):
        for eid, items in extract(text, forms, label).items():
            merged[eid].extend(items)

    if args.entity:
        merged = {args.entity: merged.get(args.entity, [])}

    merged = {k: v for k, v in merged.items() if len(v) >= args.min_claims}
    total = sum(len(v) for v in merged.values())
    print(f"prose-claim-extractor: {len(forms)} entity surface forms | "
          f"{len(merged)} entities | {total} claims")
    for eid, items in sorted(merged.items(), key=lambda kv: -len(kv[1]))[:20]:
        print(f"  {eid:<38} {len(items):5d}")

    if args.out:
        Path(args.out).write_text(json.dumps(merged, indent=2), encoding="utf-8")
        print(f"\nclaim ledger -> {args.out}")
        print("NOTE: claims are EVIDENCE, not canon. Route them through "
              "aurora-canon-reconciler's conflict scan before promoting anything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
