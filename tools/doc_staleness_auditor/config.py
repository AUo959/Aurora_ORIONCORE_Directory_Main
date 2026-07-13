"""Per-repo governance configuration.

``repos.yaml`` maps a repo name to how ``execute`` should land fixes. The
``governance_mode`` field selects the routing strategy so new repos/modes can be
added without touching code:

* ``standard_pr``            -> branch + commit + ``gh pr create`` (never merge)
* ``canon_promotion_queue``  -> Drift Containment Protocol: quarantine draft,
                                append to DRIFT_LOG.md and the promotion queue
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CONFIG = Path(__file__).with_name("repos.yaml")


@dataclass
class RepoConfig:
    name: str
    governance_mode: str = "standard_pr"
    default_branch: str = "main"
    drift_log_path: str = "DRIFT_LOG.md"
    promotion_queue_path: str = (
        "canon/L1/station/operational_library_v2_2/LOG__PROMOTION_QUEUE__v1.1.md"
    )
    quarantine_dir: str = "canon/_quarantine/drift"
    extra: dict[str, Any] = field(default_factory=dict)


def load_config(path: str | None = None) -> dict[str, RepoConfig]:
    cfg_path = Path(path) if path else _DEFAULT_CONFIG
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    repos: dict[str, RepoConfig] = {}
    for name, spec in (data.get("repos") or {}).items():
        spec = spec or {}
        known = {f for f in RepoConfig.__dataclass_fields__ if f != "extra"}
        repos[name] = RepoConfig(
            name=name,
            **{k: v for k, v in spec.items() if k in known and k != "name"},
            extra={k: v for k, v in spec.items() if k not in known},
        )
    return repos


def resolve_repo_config(
    name: str, path: str | None = None, default_mode: str = "standard_pr"
) -> RepoConfig:
    repos = load_config(path)
    if name in repos:
        return repos[name]
    # unknown repo -> conservative default
    return RepoConfig(name=name, governance_mode=default_mode)
