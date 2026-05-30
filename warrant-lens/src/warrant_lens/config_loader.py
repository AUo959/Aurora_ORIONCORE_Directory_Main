"""Load and validate the three config artifacts.

Principle 6: these are the contestable mappings — inspectable, editable files.
Loader is intentionally tolerant (extra keys ignored) so the YAML can evolve
without breaking the code path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


@dataclass(frozen=True)
class Taxonomy:
    claim_types: dict[str, dict[str, Any]]

    def is_demanding(self, claim_type: str) -> bool:
        return bool(self.claim_types.get(claim_type, {}).get("evidentiary_demand", False))


@dataclass(frozen=True)
class FitTable:
    domains: dict[str, dict[str, dict[str, list[str]]]]
    settled_claim_markers: dict[str, dict[str, list[str]]]

    def lookup(self, domain: str, claim_type: str) -> Optional[dict[str, list[str]]]:
        """Return {"strong": [...], "weak": [...]} or None if domain is unknown."""
        dom = self.domains.get(domain)
        if dom is None:
            return None
        # Fall through to general_empirical for unmapped claim types.
        entry = dom.get(claim_type) or self.domains.get("general_empirical", {}).get(claim_type)
        return entry

    def domain_is_encoded(self, domain: str) -> bool:
        return domain in self.domains

    def consensus_bearing_classes(self, domain: str) -> list[str]:
        return list(
            self.settled_claim_markers.get(domain, {}).get("consensus_bearing_source_classes", [])
        )


@dataclass(frozen=True)
class DeliveryConfig:
    directness: str = "gentle"
    show_restatement: str = "always"
    invite_not_summon: bool = True


@dataclass(frozen=True)
class AppConfig:
    delivery: DeliveryConfig
    precision_bias: float
    logprob_enrichment: bool
    default_standard: str


def load_taxonomy(path: Path = CONFIG_DIR / "taxonomy.yaml") -> Taxonomy:
    data = yaml.safe_load(path.read_text())
    return Taxonomy(claim_types=data.get("claim_types", {}))


def load_fit_table(path: Path = CONFIG_DIR / "fit_table.yaml") -> FitTable:
    data = yaml.safe_load(path.read_text())
    return FitTable(
        domains=data.get("domains", {}),
        settled_claim_markers=data.get("settled_claim_markers", {}),
    )


def load_app_config(path: Path = CONFIG_DIR / "config.yaml") -> AppConfig:
    data = yaml.safe_load(path.read_text())
    delivery_data = data.get("delivery", {})
    return AppConfig(
        delivery=DeliveryConfig(
            directness=delivery_data.get("directness", "gentle"),
            show_restatement=delivery_data.get("show_restatement", "always"),
            invite_not_summon=bool(delivery_data.get("invite_not_summon", True)),
        ),
        precision_bias=float(data.get("precision_bias", 0.8)),
        logprob_enrichment=bool(data.get("optional_signals", {}).get("logprob_enrichment", False)),
        default_standard=str(data.get("standards", {}).get("default", "general_empirical_v1")),
    )
