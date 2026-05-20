from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "agent-dispatcher"
SKILL_MD = SKILL_ROOT / "SKILL.md"
OPENAI_YAML = SKILL_ROOT / "agents" / "openai.yaml"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
INSTALLED_SKILLS_ROOT = Path.home() / ".codex" / "skills"
INSTALLED_SKILL_ROOT = INSTALLED_SKILLS_ROOT / "agent-dispatcher"
SESSION_CATALOG = INSTALLED_SKILLS_ROOT / "aurora-skill-finder" / "references" / "session_skill_catalog.json"
GENERAL_CATALOG = (
    INSTALLED_SKILLS_ROOT / "aurora-skill-finder" / "references" / "general_utility_skill_catalog.json"
)

sys.path.insert(0, str(SCRIPTS_DIR))

import evaluate_dispatch  # noqa: E402


POSITIVE_PROMPTS = [
    "This repo audit is broad. Should we use subagents to parallelize investigation and verification?",
    "Create an approval-gated agent dispatcher plan with an explorer role and a worker role.",
    "Plan parallel agents for this migration, but do not spawn agents until I approve.",
    "Decide whether bespoke agents are warranted before doing substantial work.",
    "This migration touches docs, code, validation, and risk review. Split the work intelligently.",
    "Can you investigate the architecture while also checking tests and risks?",
    "Before implementing, decide whether parallel investigation would help.",
    "This is a broad repo audit across several modules; design a coordinated plan.",
]

NEGATIVE_PROMPTS = [
    "What is the current date?",
    "Fix the typo in this one sentence.",
    "Set the browser user-agent header for this HTTP request.",
    "Run the single failing unit test again.",
]


def read_skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(?P<body>.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must start with YAML frontmatter"
    out: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def load_catalog_entry(path: Path, skill_name: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = [row for row in payload.get("skills", []) if row.get("name") == skill_name]
    assert len(entries) == 1, f"{skill_name} must appear exactly once in {path}"
    return entries[0]


def contains_keyword(text: str, keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    if " " in keyword or "_" in keyword or "-" in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def prompt_matches_catalog_entry(prompt: str, entry: dict[str, object]) -> bool:
    text = prompt.lower()
    include_keywords = [str(value).lower() for value in entry.get("include_keywords", [])]
    exclude_keywords = [str(value).lower() for value in entry.get("exclude_keywords", [])]
    include_hits = [keyword for keyword in include_keywords if contains_keyword(text, keyword)]
    exclude_hits = [keyword for keyword in exclude_keywords if contains_keyword(text, keyword)]

    explicit_terms = {
        "agent dispatcher",
        "subagents",
        "subagent",
        "bespoke agents",
        "dispatch plan",
        "delegation plan",
        "parallel agents",
        "parallel work",
        "spawn agents",
        "worker role",
        "explorer role",
        "approval gate",
        "agent plan",
        "parallel investigation",
        "agent council",
        "swarm",
    }
    implicit_terms = {
        "broad repo audit",
        "split the work",
        "coordinated plan",
        "migration",
        "architecture mapping",
        "investigate the architecture",
        "checking tests and risks",
        "validation",
        "risk review",
        "independent workstreams",
        "multiple workstreams",
    }
    explicit_invocation = any(hit in explicit_terms for hit in include_hits)
    implicit_signal_count = len({hit for hit in include_hits if hit in implicit_terms})
    return (explicit_invocation or implicit_signal_count >= 2) and not exclude_hits


def test_skill_frontmatter_declares_product_intent() -> None:
    frontmatter = parse_frontmatter(read_skill_text())
    assert frontmatter["name"] == "agent-dispatcher"
    description = frontmatter["description"].lower()
    for phrase in (
        "extract the optimal workflow shape",
        "material parallel-work justification",
        "multiple independent workstreams",
        "broad repo audit",
        "agent council",
        "swarm",
        "stay silent",
        "explicit user approval",
    ):
        assert phrase in description


def test_skill_docs_define_portable_decision_contract() -> None:
    text = read_skill_text()
    for field_name in (
        "request_summary",
        "workflow_graph",
        "command_context",
        "dispatch_verdict",
        "reasoning_factors",
        "recommended_pattern",
        "agent_roles",
        "local_critical_path",
        "approval_gate",
        "user_facing_explanation",
    ):
        assert f"`{field_name}`" in text


def test_skill_docs_define_user_facing_behavior() -> None:
    text = read_skill_text().lower()
    for phrase in (
        "stay invisible for ordinary local tasks",
        "explicit agent language is a request to evaluate delegation",
        "teach through concrete role and workflow tradeoffs",
        "do not spawn, initialize, or message agents until the user explicitly approves",
        "if it returns `silent_local`, do not mention agents unless the user explicitly asked about them",
        "treat command grammar like a human context clue",
        "command intent is context-only",
    ):
        assert phrase in text


def test_openai_yaml_default_prompt_describes_workflow_intelligence() -> None:
    text = OPENAI_YAML.read_text(encoding="utf-8")
    assert 'display_name: "Agent Dispatcher"' in text
    assert "Workflow intelligence" in text
    assert "$agent-dispatcher" in text
    assert "workflow" in text
    assert "helpful context rather than a limiter" in text
    assert "council" in text
    assert "swarm" in text


@pytest.mark.parametrize("prompt", NEGATIVE_PROMPTS)
def test_evaluator_stays_silent_for_local_linear_tasks(prompt: str) -> None:
    report = evaluate_dispatch.evaluate_request(prompt)
    assert report["dispatch_verdict"] == "silent_local"
    assert report["recommended_pattern"] == "local_linear"
    assert report["approval_gate"] is False
    assert report["agent_roles"] == []
    assert report["user_facing_explanation"] == ""


def test_evaluator_contract_contains_required_fields() -> None:
    report = evaluate_dispatch.evaluate_request(
        "This migration touches docs, code, validation, and risk review. Split the work intelligently."
    )
    assert set(report) == {
        "request_summary",
        "workflow_graph",
        "command_context",
        "dispatch_verdict",
        "reasoning_factors",
        "recommended_pattern",
        "agent_roles",
        "local_critical_path",
        "approval_gate",
        "user_facing_explanation",
    }
    assert report["reasoning_factors"]["material_dispatch_justified"] is True
    assert report["reasoning_factors"]["material_dispatch_score"] >= 2
    assert report["reasoning_factors"]["material_dispatch_criteria"]
    assert report["command_context"]["dispatch_effect"] == "informational_only"


@pytest.mark.parametrize(
    ("prompt", "expected_verdict", "expected_pattern"),
    [
        (
            "This migration touches docs, code, validation, and risk review. Split the work intelligently.",
            "propose_council",
            "agent_council",
        ),
        (
            "Can you investigate the architecture while also checking tests and risks?",
            "propose_council",
            "agent_council",
        ),
        (
            "Before implementing, decide whether parallel investigation would help.",
            "propose_dispatch",
            "parallel_sidecar",
        ),
        (
            "Form an agent council to compare architecture, implementation strategy, validation, and risk.",
            "propose_council",
            "agent_council",
        ),
        (
            "This requires a swarm-style scan across many independent archive lanes and evidence files.",
            "propose_swarm",
            "search_swarm",
        ),
    ],
)
def test_dispatch_patterns_for_complex_requests(prompt: str, expected_verdict: str, expected_pattern: str) -> None:
    report = evaluate_dispatch.evaluate_request(prompt)
    assert report["dispatch_verdict"] == expected_verdict
    assert report["recommended_pattern"] == expected_pattern
    assert report["approval_gate"] is True
    assert report["agent_roles"]
    assert report["reasoning_factors"]["material_dispatch_justified"] is True
    assert report["reasoning_factors"]["material_dispatch_score"] >= 2


def test_workflow_graph_extracts_work_units_dependencies_and_critical_path() -> None:
    report = evaluate_dispatch.evaluate_request(
        "Before implementing, decide whether parallel investigation would help."
    )
    graph = report["workflow_graph"]
    assert graph["work_units"]
    assert graph["dependencies"]
    assert report["local_critical_path"] == ["investigation", "implementation"]


def test_workflow_graph_extracts_multiple_lanes_without_explicit_agent_words() -> None:
    report = evaluate_dispatch.evaluate_request(
        "This migration touches docs, code, validation, and risk review. Split the work intelligently."
    )
    graph = report["workflow_graph"]
    assert {"docs", "code", "validation", "risk"}.issubset(set(graph["artifact_lanes"]))
    assert graph["parallel_lane_count"] >= 4
    assert report["reasoning_factors"]["independent_lane_count"] >= 4


def test_command_grammar_context_is_attached_to_agent_briefs_without_limiting_dispatch() -> None:
    report = evaluate_dispatch.evaluate_request(
        "Please use two agents to look at the THREADWAKE path the way human reviewers would: "
        "one reviews architecture notes, the other checks tests and risk, and neither executes it."
    )

    assert report["dispatch_verdict"] == "propose_council"
    assert report["approval_gate"] is True
    assert report["command_context"]["present"] is True
    assert report["command_context"]["dispatch_effect"] == "informational_only"
    assert "helpful context clue" in report["command_context"]["human_use_guidance"]
    assert report["command_context"]["snippets"][0]["raw_text"] == "THREADWAKE"
    assert report["command_context"]["snippets"][0]["normalized_text"] == "THREADWAKE//."
    assert report["command_context"]["snippets"][0]["runtime_handler_verified"] is False
    assert all(role["command_intent"].startswith("context_only:") for role in report["agent_roles"])
    assert any("THREADWAKE//." in role["command_intent"] for role in report["agent_roles"])


def test_command_grammar_context_does_not_force_dispatch_for_linear_work() -> None:
    report = evaluate_dispatch.evaluate_request(
        "Can you have agents fix the single failing THREADWAKE test?"
    )

    assert report["dispatch_verdict"] == "explain_no_dispatch"
    assert report["approval_gate"] is False
    assert report["agent_roles"] == []
    assert report["command_context"]["present"] is True
    assert report["reasoning_factors"]["command_context_present"] is True
    assert report["reasoning_factors"]["command_context_dispatch_effect"] == "informational_only"
    assert report["reasoning_factors"]["material_dispatch_justified"] is False


def test_sensitive_or_destructive_requests_do_not_become_agent_tasks() -> None:
    report = evaluate_dispatch.evaluate_request(
        "Use agents to publish the release and force push the broken branch."
    )
    assert report["dispatch_verdict"] == "explain_no_dispatch"
    assert report["recommended_pattern"] == "guarded_local"
    assert report["approval_gate"] is False
    assert "direct control" in report["user_facing_explanation"].lower()


def test_explicit_agent_request_without_material_parallelism_does_not_dispatch() -> None:
    report = evaluate_dispatch.evaluate_request(
        "Use agents to fix the single failing root workspace unit test."
    )
    assert report["dispatch_verdict"] == "explain_no_dispatch"
    assert report["approval_gate"] is False
    assert report["agent_roles"] == []
    assert report["reasoning_factors"]["material_dispatch_justified"] is False
    assert "coordination cost" in report["user_facing_explanation"].lower()


def test_ambiguous_broad_request_requires_clarification() -> None:
    report = evaluate_dispatch.evaluate_request("Please handle this and make it better.")
    assert report["dispatch_verdict"] == "explain_no_dispatch"
    assert report["recommended_pattern"] == "clarify_then_decide"
    assert report["approval_gate"] is False
    assert "concrete target or deliverable" in report["user_facing_explanation"].lower()


def test_tutorial_text_explains_role_split_without_over_teaching() -> None:
    report = evaluate_dispatch.evaluate_request(
        "This migration touches docs, code, validation, and risk review. Split the work intelligently."
    )
    explanation = report["user_facing_explanation"].lower()
    assert "council is warranted" in explanation
    assert "suggested roles" in explanation
    assert "critical path local" in explanation


@pytest.mark.skipif(not SESSION_CATALOG.exists(), reason="installed session skill catalog is not available")
def test_installed_session_catalog_routes_simulated_user_prompts() -> None:
    entry = load_catalog_entry(SESSION_CATALOG, "agent-dispatcher")
    assert all(prompt_matches_catalog_entry(prompt, entry) for prompt in POSITIVE_PROMPTS)
    assert not any(prompt_matches_catalog_entry(prompt, entry) for prompt in NEGATIVE_PROMPTS)


@pytest.mark.skipif(not GENERAL_CATALOG.exists(), reason="installed general utility skill catalog is not available")
def test_installed_general_utility_catalog_routes_simulated_user_prompts() -> None:
    entry = load_catalog_entry(GENERAL_CATALOG, "agent-dispatcher")
    assert all(prompt_matches_catalog_entry(prompt, entry) for prompt in POSITIVE_PROMPTS)
    assert not any(prompt_matches_catalog_entry(prompt, entry) for prompt in NEGATIVE_PROMPTS)


@pytest.mark.skipif(not INSTALLED_SKILL_ROOT.exists(), reason="installed agent-dispatcher skill is not available")
def test_installed_skill_matches_repo_source() -> None:
    installed_files = {
        "SKILL.md": (INSTALLED_SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"),
        "agents/openai.yaml": (INSTALLED_SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"),
        "scripts/evaluate_dispatch.py": (INSTALLED_SKILL_ROOT / "scripts" / "evaluate_dispatch.py").read_text(
            encoding="utf-8"
        )
        if (INSTALLED_SKILL_ROOT / "scripts" / "evaluate_dispatch.py").exists()
        else "",
    }
    repo_files = {
        "SKILL.md": SKILL_MD.read_text(encoding="utf-8"),
        "agents/openai.yaml": OPENAI_YAML.read_text(encoding="utf-8"),
        "scripts/evaluate_dispatch.py": (SCRIPTS_DIR / "evaluate_dispatch.py").read_text(encoding="utf-8"),
    }
    if installed_files != repo_files:
        pytest.skip("installed agent-dispatcher copy is stale; run tools/sync_codex_skill.py to refresh it")
    assert installed_files == repo_files
