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
        "GUMAS mutation authorization",
        "gumas_mutation_auth_status",
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
        "run_mode",
        "execution_scope",
        "live_runtime_execution",
        "simulation_status",
        "runtime_handler_verified",
        "gumas_mutation_auth_required",
        "gumas_mutation_auth_status",
        "gumas_mutation_auth_refs",
        "execution_status",
        "target_repo",
        "recommended_next_action",
    }.issubset(required)
    assert "mesh_router" in schema["properties"]["grammar_family"]["enum"]
    assert "blocked_pending_verification" in schema["properties"]["execution_status"]["enum"]
    assert "run_mode" in schema["properties"]
    assert "execution_scope" in schema["properties"]
    assert "live_runtime_execution" in schema["properties"]
    assert "simulation_status" in schema["properties"]
    assert "gumas_mutation_auth_required" in schema["properties"]
    assert "gumas_mutation_auth_status" in schema["properties"]
    assert "gumas_mutation_auth_refs" in schema["properties"]
    assert "required_not_verified" in schema["properties"]["gumas_mutation_auth_status"]["enum"]


def test_audit_handoff_schema_wraps_command_intent_without_replacing_it() -> None:
    schema = json.loads(read_text(SKILL_ROOT / "references" / "audit-handoff-record.schema.json"))

    assert schema["title"] == "Aurora Audit Handoff Record"
    required = set(schema["required"])
    assert {
        "handoff_id",
        "source_epistemic_status",
        "command_intent",
        "execution_boundary",
        "no_mutation_attestation",
    }.issubset(required)
    assert "runtime_verified" in schema["properties"]["source_epistemic_status"]["enum"]
    execution_required = set(schema["properties"]["execution_boundary"]["required"])
    assert "live_execution_claim" in execution_required
    assert "gumas_mutation_auth_required" in execution_required
    assert "gumas_mutation_auth_status" in execution_required


def test_github_templates_include_envelope_and_execution_boundary() -> None:
    pr_template = read_text(REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE" / "aurora-command-grammar.md")
    issue_template = read_text(REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "aurora-command-grammar.md")

    for text in (pr_template, issue_template):
        assert '"schema_version": "1.1.0"' in text
        assert '"runtime_handler_verified": false' in text
        assert '"gumas_mutation_auth_status": "not_applicable"' in text
        assert "Grammar interpretation is separated from runtime execution" in text or (
            "grammar-valid text as execution approval" in text
        )
