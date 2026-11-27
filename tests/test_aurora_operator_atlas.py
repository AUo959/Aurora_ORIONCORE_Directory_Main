"""Offline Aurora Operator Atlas invariants and source-label regression checks."""

from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "projects/aurora_operator_atlas/index.html"


class UIInventory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.panels = []
        self.controls = []
        self.links = []
        self.script_sources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and "panel" in attrs.get("class", "").split():
            self.panels.append(attrs.get("id"))
        if tag == "button":
            self.controls.append(attrs)
        if tag == "script":
            self.script_sources.append(attrs.get("src"))
        if tag == "a":
            self.links.append(attrs.get("href", ""))


def test_five_distinct_real_views():
    parser = UIInventory()
    parser.feed(PREVIEW.read_text(encoding="utf-8"))
    assert parser.panels == ["overview", "mission", "simulation", "canon", "integration"]
    assert len([c for c in parser.controls if c.get("data-view")]) == 5
    assert len([c for c in parser.controls if c.get("data-layer")]) == 3
    assert len([c for c in parser.controls if c.get("data-filter")]) == 3


def test_offline_no_unintended_network_or_runtime_execution():
    data = PREVIEW.read_text(encoding="utf-8")
    parser = UIInventory()
    parser.feed(data)
    assert all(src is None for src in parser.script_sources)
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket(", "EventSource(",
                      "sendBeacon(", "localStorage.", "sessionStorage.",
                      "eval(", "new Function(", "navigator.credentials"):
        assert forbidden not in data, forbidden
    assert all(url.startswith("https://github.com/AUo959/") for url in parser.links)


def test_report_provenance_and_demonstration_labels():
    data = PREVIEW.read_text(encoding="utf-8")
    for required in ("August 15, 2026", "Historical source snapshot",
                     "synthetic", "No GUMAS execution",
                     "not current telemetry", "read-only",
                     "Not connected", "Operator inbox"):
        assert required.lower() in data.lower()
    assert "private-recovery.json" not in data
    assert "restricted_recovery_candidates_metadata" not in data
    assert "AURORA_UI_READ_TOKEN_SHA256" not in data


def test_report_totals_and_github_links():
    data = PREVIEW.read_text(encoding="utf-8")
    assert "All · 12" in data and "P1 · 4" in data and "P2 · 8" in data
    assert "Issue #90" in data and "Issue #1610" in data
    assert "Issue #12" in data
    assert all(("pull/"+str(i)) in data for i in (97,98,99))


def test_no_implicit_permission_grant():
    data = PREVIEW.read_text(encoding="utf-8")
    assert "No automatic promotion" in data or "No simulated output" in data
    assert "without crossing authority boundaries" in data
