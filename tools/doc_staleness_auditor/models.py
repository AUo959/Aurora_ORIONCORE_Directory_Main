"""Core dataclasses for the doc staleness auditor.

A ``Claim`` is a checkable assertion extracted from a doc. A ``Finding`` is the
result of verifying one claim against directly observed ground truth. ``Evidence``
names the exact primary source that was inspected so a human can independently
re-check the verdict.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ClaimType(str, Enum):
    PATH = "path"          # a referenced file/dir path
    SYMBOL = "symbol"      # a function/class/route/symbol name
    NUMERIC = "numeric"    # a count claim ("49 docs", "3 backends")
    VERSION = "version"    # a version string ("v2.2", "2.1.0")


class Status(str, Enum):
    CONFIRMED = "CONFIRMED"
    STALE = "STALE"
    UNVERIFIABLE = "UNVERIFIABLE_BY_AUTOMATION"


# The only verification methods that may yield a CONFIRMED verdict. Each names a
# *primary* evidence source. Doc-to-doc corroboration and bare filename-existence
# are deliberately absent -- see README "Evidence policy".
PRIMARY_METHODS = {
    "git_tree_lookup",        # actual `git ls-tree` state at HEAD
    "source_content_read",    # actual file content read + regex/substring matched
    "python_ast_parse",       # actual Python source parsed via ast
    "config_file_read",       # actual VERSION/package.json/pyproject.toml value read
    "recomputed_count",       # count recomputed from real tree/content by a stated rule
}


@dataclass
class Claim:
    """A single verifiable assertion lifted out of a markdown doc."""

    id: str
    type: ClaimType
    doc_path: str            # md file the claim came from (repo-relative)
    doc_line: int            # 1-based line number in that doc
    raw_text: str            # the surrounding text the claim was read from
    value: str               # the extracted checkable value (path, symbol, number, version)
    context: dict[str, Any] = field(default_factory=dict)  # hints for the verifier

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["type"] = self.type.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Claim":
        return cls(
            id=d["id"],
            type=ClaimType(d["type"]),
            doc_path=d["doc_path"],
            doc_line=d["doc_line"],
            raw_text=d["raw_text"],
            value=d["value"],
            context=d.get("context", {}),
        )


@dataclass
class Evidence:
    """The exact primary source inspected to reach a verdict.

    ``method`` must be one of :data:`PRIMARY_METHODS` for a CONFIRMED/STALE verdict.
    ``files`` lists repo-relative paths actually read; ``lines`` gives 1-based
    ranges within them; ``sha`` records the git HEAD the tree/content was read at.
    """

    method: str
    detail: str
    files: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    sha: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class Finding:
    claim: Claim
    status: Status
    observed: str | None            # what ground truth actually showed
    evidence: Evidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "status": self.status.value,
            "observed": self.observed,
            "evidence": self.evidence.to_dict(),
        }
