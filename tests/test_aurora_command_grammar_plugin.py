from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "aurora-command-grammar"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "aurora-command-grammar"
MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_plugin_manifest_and_marketplace_are_registered() -> None:
    manifest = json.loads(read_text(PLUGIN_ROOT / ".codex-plugin" / "plugin.json"))
    marketplace = json.loads(read_text(MARKETPLACE))

    assert manifest["name"] == "aurora-command-grammar"
    assert manifest["skills"] == "./skills/"
    assert manifest["interface"]["displayName"] == "Aurora Command Grammar"
    assert "Create a command intent envelope." in manifest["interface"]["defaultPrompt"]

    entries = [entry for entry in marketplace["plugins"] if entry["name"] == "aurora-command-grammar"]
    assert entries == [
        {
            "name": "aurora-command-grammar",
            "source": {
                "source": "local",
                "path": "./plugins/aurora-command-grammar",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Coding",
        }
    ]


def test_skill_declares_user_agent_and_background_contracts() -> None:
    text = read_text(SKILL_ROOT / "SKILL.md")

    for phrase in (
        "Users who need a clear parse",
        "Agents that need a shared command-language protocol",
        "Background workflows that need durable command intent records",
        "grammar-valid command text is not execution approval",
        "command intent envelope",
        "runtime_handler_verified",
    ):
        assert phrase in text


def test_background_schema_has_required_cross_thread_fields() -> None:
    schema = json.loads(read_text(SKILL_ROOT / "references" / "command-intent-envelope.schema.json"))

    assert schema["title"] == "Aurora Command Intent Envelope"
    required = set(schema["required"])
    assert {
        "raw_text",
        "intent_type",
        "grammar_family",
        "validation_status",
        "runtime_handler_verified",
        "execution_status",
        "target_repo",
        "recommended_next_action",
    }.issubset(required)
    assert "mesh_router" in schema["properties"]["grammar_family"]["enum"]
    assert "blocked_pending_verification" in schema["properties"]["execution_status"]["enum"]


def test_github_templates_include_envelope_and_execution_boundary() -> None:
    pr_template = read_text(REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE" / "aurora-command-grammar.md")
    issue_template = read_text(REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "aurora-command-grammar.md")

    for text in (pr_template, issue_template):
        assert '"schema_version": "1.0.0"' in text
        assert '"runtime_handler_verified": false' in text
        assert "Grammar interpretation is separated from runtime execution" in text or (
            "grammar-valid text as execution approval" in text
        )
