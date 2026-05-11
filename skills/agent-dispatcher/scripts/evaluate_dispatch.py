#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTION_PATTERNS = {
    "investigation": (
        "audit",
        "scan",
        "map",
        "inventory",
        "investigate",
        "investigation",
        "inspect",
        "analyze",
        "analysis",
        "research",
        "triage",
        "find",
        "discover",
    ),
    "implementation": (
        "implement",
        "implementing",
        "implementation",
        "patch",
        "fix",
        "build",
        "refactor",
        "migration",
        "migrate",
        "edit",
        "change",
        "repair",
    ),
    "verification": (
        "test",
        "tests",
        "checking",
        "check",
        "verify",
        "verification",
        "validate",
        "validation",
        "regression",
        "smoke",
        "prove",
    ),
    "review": (
        "review",
        "risk",
        "risks",
        "security",
        "edge case",
        "architecture",
        "strategy",
        "tradeoff",
        "compare",
        "assess",
    ),
    "planning": (
        "plan",
        "design",
        "coordinate",
        "coordinated",
        "workflow",
        "split",
        "decide",
        "organize",
    ),
}

ARTIFACT_PATTERNS = {
    "repo": ("repo", "repository", "codebase", "workspace", "project"),
    "modules": ("module", "modules", "packages", "components", "subsystems"),
    "code": ("code", "implementation", "source", "scripts", "files"),
    "docs": ("docs", "documentation", "readme", "markdown", "spec"),
    "tests": ("tests", "test suite", "unit test", "regression", "smoke"),
    "architecture": ("architecture", "design", "dependency", "dependencies", "interfaces"),
    "validation": ("validation", "verify", "checks", "ci", "build"),
    "risk": ("risk", "risks", "security", "safety", "edge cases"),
    "archives": ("archive", "archives", "evidence", "corpus", "dataset"),
}

ROLE_BY_ACTION = {
    "investigation": "explorer",
    "implementation": "worker",
    "verification": "verifier",
    "review": "reviewer",
    "planning": "coordinator",
}

ROLE_OBJECTIVES = {
    "coordinator": "Keep the workflow coherent, preserve the critical path locally, and merge results into one dispatch recommendation.",
    "explorer": "Map evidence, boundaries, dependencies, and candidate workstreams without editing files.",
    "worker": "Implement or draft a bounded change in an explicitly owned write scope.",
    "verifier": "Run or design independent checks and report residual risk.",
    "reviewer": "Review architecture, risk, edge cases, or competing approaches before execution.",
}

ROLE_OUTPUTS = {
    "coordinator": "One merged plan with role boundaries, approval gate, and validation path.",
    "explorer": "Evidence map, affected surfaces, risks, and recommended next work units.",
    "worker": "Patch summary, changed paths, unresolved assumptions, and test notes.",
    "verifier": "Validation commands, pass/fail results, and residual risk.",
    "reviewer": "Findings, tradeoffs, and recommendation on whether to proceed.",
}

SIMPLE_PATTERNS = (
    "typo",
    "one sentence",
    "single sentence",
    "current date",
    "what time",
    "translate",
    "small fix",
    "quick fix",
    "single failing",
    "single failing test",
    "one file",
    "single file",
)

SENSITIVE_PATTERNS = (
    "password",
    "secret",
    "token",
    "credential",
    "private key",
    "delete",
    "destroy",
    "reset --hard",
    "force push",
    "publish",
    "deploy",
)

EXPLICIT_AGENT_PATTERNS = (
    "agent",
    "agents",
    "subagent",
    "subagents",
    "bespoke agent",
    "agent dispatcher",
    "agent council",
    "council",
    "swarm",
    "worker",
    "explorer",
)

WORKFLOW_EVALUATION_PATTERNS = (
    "decide whether",
    "would help",
    "if warranted",
    "split the work",
    "split work",
    "coordinate",
    "best way",
    "how should we approach",
)

AMBIGUOUS_BROAD_PATTERNS = (
    "make it better",
    "improve this",
    "handle this",
    "do everything",
    "fix everything",
    "sort this out",
)

NON_DISPATCH_COLLISION_PATTERNS = (
    "user-agent",
    "http request",
    "request header",
    "browser header",
)

PARALLEL_MARKERS = ("while", "while also", "parallel", "simultaneously", "at the same time", "split")
DEPENDENCY_MARKERS = ("before", "after", "then", "once", "afterwards")


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    source_text: str
    action: str
    artifact: str
    role_hint: str
    write_scope: str
    parallel_safe: bool
    rationale: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_term(text: str, term: str) -> bool:
    term = term.strip().lower()
    if not term:
        return False
    if " " in term or "-" in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def hits_for(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if contains_term(text, term)]


def split_clauses(text: str) -> list[str]:
    normalized = normalize(text)
    raw_parts = re.split(
        r"(?:[.;?]+|\bwhile also\b|\bwhile\b|\band then\b|\bthen\b|\bplus\b|\bin addition\b)",
        normalized,
    )
    clauses = [part.strip(" ,") for part in raw_parts if part.strip(" ,")]
    return clauses or ([normalized] if normalized else [])


def categories_for(text: str, patterns: dict[str, tuple[str, ...]]) -> list[str]:
    return [category for category, terms in patterns.items() if any(contains_term(text, term) for term in terms)]


def infer_action_for_artifact(artifact: str, actions: list[str]) -> str:
    if artifact in {"tests", "validation"}:
        return "verification"
    if artifact in {"risk", "architecture"}:
        return "review"
    if artifact in {"repo", "modules", "archives"} and "implementation" not in actions:
        return "investigation"
    if artifact in {"code", "docs"} and "implementation" in actions:
        return "implementation"
    if actions:
        return actions[0]
    return "investigation"


def write_scope_for(action: str, artifact: str) -> str:
    if action == "implementation":
        return "write_possible"
    return "read_only"


def synthesize_work_units(request: str) -> list[WorkUnit]:
    units: list[WorkUnit] = []
    for clause in split_clauses(request):
        actions = categories_for(clause, ACTION_PATTERNS)
        artifacts = categories_for(clause, ARTIFACT_PATTERNS)
        if not actions and not artifacts:
            continue

        if artifacts:
            for artifact in artifacts:
                action = infer_action_for_artifact(artifact, actions)
                role = ROLE_BY_ACTION[action]
                scope = write_scope_for(action, artifact)
                units.append(
                    WorkUnit(
                        unit_id=f"unit-{len(units) + 1}",
                        source_text=clause,
                        action=action,
                        artifact=artifact,
                        role_hint=role,
                        write_scope=scope,
                        parallel_safe=scope == "read_only",
                        rationale=f"{artifact} lane maps to {action}.",
                    )
                )
        else:
            for action in actions:
                role = ROLE_BY_ACTION[action]
                units.append(
                    WorkUnit(
                        unit_id=f"unit-{len(units) + 1}",
                        source_text=clause,
                        action=action,
                        artifact="unspecified",
                        role_hint=role,
                        write_scope="read_only" if action != "implementation" else "write_possible",
                        parallel_safe=action != "implementation",
                        rationale=f"{action} work is explicit but artifact scope is unspecified.",
                    )
                )

    return units


def summarize_request(request: str, units: list[WorkUnit]) -> dict[str, Any]:
    normalized = normalize(request)
    deliverable = split_clauses(request)[0] if request.strip() else ""
    return {
        "original": request,
        "normalized": normalized,
        "detected_goal": deliverable,
        "work_unit_count": len(units),
    }


def extract_dependencies(text: str, units: list[WorkUnit]) -> tuple[list[dict[str, str]], list[str]]:
    normalized = normalize(text)
    dependencies: list[dict[str, str]] = []
    critical_path: list[str] = []

    actions = {unit.action for unit in units}
    if "before" in hits_for(normalized, DEPENDENCY_MARKERS) and {"investigation", "implementation"} <= actions:
        dependencies.append(
            {
                "type": "sequential",
                "reason": "The request asks to decide or investigate before implementing.",
                "source": "investigation",
                "target": "implementation",
            }
        )
        critical_path = ["investigation", "implementation"]
    elif any(contains_term(normalized, marker) for marker in ("then", "after", "once", "afterwards")):
        ordered_actions = []
        for unit in units:
            if unit.action not in ordered_actions:
                ordered_actions.append(unit.action)
        if len(ordered_actions) >= 2:
            dependencies.append(
                {
                    "type": "sequential",
                    "reason": "The request includes sequential timing language.",
                    "source": ordered_actions[0],
                    "target": ordered_actions[-1],
                }
            )
            critical_path = ordered_actions

    return dependencies, critical_path


def build_workflow_graph(request: str, units: list[WorkUnit]) -> dict[str, Any]:
    normalized = normalize(request)
    dependencies, critical_path = extract_dependencies(request, units)
    action_categories = sorted({unit.action for unit in units})
    artifact_lanes = sorted({unit.artifact for unit in units if unit.artifact != "unspecified"})
    parallel_markers = hits_for(normalized, PARALLEL_MARKERS)
    dependency_markers = hits_for(normalized, DEPENDENCY_MARKERS)
    critical_actions = set(critical_path)
    parallel_units: list[str] = []
    for unit in units:
        if critical_actions and unit.action in critical_actions:
            continue
        if len(artifact_lanes) >= 3 and unit.artifact in artifact_lanes:
            parallel_units.append(unit.unit_id)
            continue
        if unit.parallel_safe and parallel_markers:
            parallel_units.append(unit.unit_id)
            continue
        if unit.parallel_safe and not dependencies and len(units) > 1:
            parallel_units.append(unit.unit_id)

    return {
        "work_units": [
            {
                "id": unit.unit_id,
                "text": unit.source_text,
                "action": unit.action,
                "artifact": unit.artifact,
                "role_hint": unit.role_hint,
                "write_scope": unit.write_scope,
                "parallel_safe": unit.parallel_safe,
                "rationale": unit.rationale,
            }
            for unit in units
        ],
        "action_categories": action_categories,
        "artifact_lanes": artifact_lanes,
        "parallel_lanes": parallel_units,
        "parallel_lane_count": len(set(parallel_units)),
        "dependencies": dependencies,
        "dependency_markers": dependency_markers,
        "parallel_markers": parallel_markers,
        "critical_path": critical_path,
    }


def reasoning_factors(request: str, graph: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize(request)
    simple_hits = hits_for(normalized, SIMPLE_PATTERNS)
    sensitive_hits = hits_for(normalized, SENSITIVE_PATTERNS)
    explicit_agent_hits = hits_for(normalized, EXPLICIT_AGENT_PATTERNS)
    workflow_evaluation_hits = hits_for(normalized, WORKFLOW_EVALUATION_PATTERNS)
    ambiguous_hits = hits_for(normalized, AMBIGUOUS_BROAD_PATTERNS)
    collision_hits = hits_for(normalized, NON_DISPATCH_COLLISION_PATTERNS)

    action_count = len(graph["action_categories"])
    artifact_count = len(graph["artifact_lanes"])
    parallel_count = int(graph["parallel_lane_count"])
    independent_lane_count = max(parallel_count, artifact_count, action_count)
    material_criteria = material_dispatch_criteria(normalized, graph)

    return {
        "explicit_agent_request": bool(explicit_agent_hits),
        "workflow_evaluation_request": bool(workflow_evaluation_hits),
        "simple_local_task": bool(simple_hits),
        "sensitive_or_destructive": bool(sensitive_hits),
        "non_dispatch_collision": bool(collision_hits),
        "ambiguous_scope": bool(ambiguous_hits) or (not graph["work_units"] and len(normalized.split()) > 3),
        "action_category_count": action_count,
        "artifact_lane_count": artifact_count,
        "parallel_lane_count": parallel_count,
        "independent_lane_count": independent_lane_count,
        "material_dispatch_criteria": material_criteria,
        "material_dispatch_score": len(material_criteria),
        "material_dispatch_justified": len(material_criteria) >= 2,
        "has_dependencies": bool(graph["dependencies"]),
        "signals": {
            "simple_hits": simple_hits,
            "sensitive_hits": sensitive_hits,
            "explicit_agent_hits": explicit_agent_hits,
            "workflow_evaluation_hits": workflow_evaluation_hits,
            "ambiguous_hits": ambiguous_hits,
            "collision_hits": collision_hits,
        },
    }


def material_dispatch_criteria(normalized: str, graph: dict[str, Any]) -> list[str]:
    units = graph["work_units"]
    action_count = len(graph["action_categories"])
    artifact_count = len(graph["artifact_lanes"])
    parallel_count = int(graph["parallel_lane_count"])
    read_only_units = [unit for unit in units if unit["write_scope"] == "read_only"]
    write_units = [unit for unit in units if unit["write_scope"] == "write_possible"]
    read_only_roles = {unit["role_hint"] for unit in read_only_units}
    write_artifacts = {
        unit["artifact"]
        for unit in write_units
        if unit["artifact"] not in {"repo", "unspecified"}
    }

    criteria: list[str] = []
    if parallel_count >= 2:
        criteria.append("separable_parallel_streams")
    if parallel_count >= 1 and graph["dependencies"] and action_count >= 3:
        criteria.append("nonblocking_sidecar_available")
    if artifact_count >= 3 and action_count >= 2:
        criteria.append("broad_multi_surface_work")
    if len(read_only_units) >= 2 and len(read_only_roles) >= 2:
        criteria.append("independent_review_or_verification")
    if len(write_artifacts) >= 2:
        criteria.append("distinct_write_scopes")
    if graph["parallel_markers"] and action_count >= 3:
        criteria.append("explicit_parallel_workflow")
    if (
        any(contains_term(normalized, marker) for marker in ("many", "several", "across", "independent"))
        and len(read_only_units) >= 2
        and (parallel_count >= 1 or artifact_count >= 2)
    ):
        criteria.append("many_independent_search_lanes")

    return list(dict.fromkeys(criteria))


def synthesize_roles(graph: dict[str, Any], pattern: str) -> list[dict[str, Any]]:
    roles: list[str] = []
    for unit in graph["work_units"]:
        role = unit["role_hint"]
        if role not in roles:
            roles.append(role)

    if pattern in {"agent_council", "search_swarm"} and "coordinator" not in roles:
        roles.insert(0, "coordinator")
    if pattern == "parallel_sidecar" and "coordinator" in roles and len(roles) > 2:
        roles.remove("coordinator")

    roles = roles[:4]
    return [
        {
            "role": role,
            "objective": ROLE_OBJECTIVES[role],
            "work_units": [
                unit["id"]
                for unit in graph["work_units"]
                if unit["role_hint"] == role or role == "coordinator"
            ],
            "scope": "read_only" if role in {"explorer", "reviewer", "verifier"} else "owned_write_scope_required",
            "output_contract": ROLE_OUTPUTS[role],
        }
        for role in roles
    ]


def decide_dispatch(request: str, graph: dict[str, Any], factors: dict[str, Any]) -> tuple[str, str]:
    normalized = normalize(request)
    explicit_swarm = contains_term(normalized, "swarm")
    explicit_council = contains_term(normalized, "council") or contains_term(normalized, "agent council")

    if factors["simple_local_task"] and not factors["explicit_agent_request"]:
        return "silent_local", "local_linear"
    if factors["non_dispatch_collision"]:
        return "silent_local", "local_linear"
    if factors["sensitive_or_destructive"]:
        return "explain_no_dispatch", "guarded_local"
    if factors["ambiguous_scope"]:
        return "explain_no_dispatch", "clarify_then_decide"
    if factors["simple_local_task"] and factors["explicit_agent_request"]:
        return "explain_no_dispatch", "local_linear"
    if not factors["material_dispatch_justified"]:
        if factors["explicit_agent_request"] or factors["workflow_evaluation_request"]:
            return "explain_no_dispatch", "insufficient_parallelism"
        return "silent_local", "local_linear"
    if explicit_swarm or factors["parallel_lane_count"] >= 6:
        return "propose_swarm", "search_swarm"
    read_only_count = sum(
        1 for unit in graph["work_units"] if unit["write_scope"] == "read_only"
    )
    independent_council_shape = (
        factors["parallel_lane_count"] >= 3
        or factors["artifact_lane_count"] >= 4
        or (read_only_count >= 3 and not factors["has_dependencies"])
    )
    if explicit_council or (
        independent_council_shape and factors["action_category_count"] >= 2
    ):
        return "propose_council", "agent_council"
    if (
        factors["explicit_agent_request"]
        or factors["workflow_evaluation_request"]
        or factors["parallel_lane_count"] >= 2
        or (factors["artifact_lane_count"] >= 2 and factors["action_category_count"] >= 2)
    ):
        return "propose_dispatch", "parallel_sidecar"
    return "silent_local", "local_linear"


def local_critical_path(graph: dict[str, Any], pattern: str) -> list[str]:
    if graph["critical_path"]:
        return graph["critical_path"]
    if pattern == "local_linear":
        return [unit["action"] for unit in graph["work_units"][:1]]
    if graph["dependencies"]:
        return [graph["dependencies"][0]["source"], graph["dependencies"][0]["target"]]
    if graph["work_units"]:
        return [graph["work_units"][0]["action"]]
    return []


def compose_tutorial(
    verdict: str,
    pattern: str,
    graph: dict[str, Any],
    factors: dict[str, Any],
    roles: list[dict[str, Any]],
) -> str:
    if verdict == "silent_local":
        return ""
    if pattern == "clarify_then_decide":
        return "I need one concrete target or deliverable before deciding whether delegation would help."
    if pattern == "guarded_local":
        return "This includes destructive, publishing, or credentialed work; keep it under direct control unless that exact delegation is approved."
    if pattern == "local_linear":
        return "No agents here; this is single-step and linear, so dispatch would add coordination cost without improving the outcome."
    if pattern == "insufficient_parallelism":
        return "No agents here; the request does not show enough independent parallel work to justify bespoke dispatch."

    lane_count = factors["independent_lane_count"]
    role_names = ", ".join(role["role"] for role in roles) or "specialist"
    if pattern == "search_swarm":
        return (
            f"A swarm is warranted because there are about {lane_count} independent search or evidence lanes "
            "that can run without shared write scope. I would keep synthesis local and require approval before launch."
        )
    if pattern == "agent_council":
        return (
            f"A council is warranted because the request separates architecture, implementation, validation, or risk "
            f"into {lane_count} lanes. Suggested roles: {role_names}. I would keep the critical path local and ask before starting them."
        )
    return (
        f"Agents help here because the request separates into {lane_count} work lanes. Suggested roles: {role_names}. "
        "I would keep the blocking next step local and ask before starting any agent."
    )


def evaluate_request(request: str) -> dict[str, Any]:
    units = synthesize_work_units(request)
    request_summary = summarize_request(request, units)
    workflow_graph = build_workflow_graph(request, units)
    factors = reasoning_factors(request, workflow_graph)
    verdict, pattern = decide_dispatch(request, workflow_graph, factors)
    roles = synthesize_roles(workflow_graph, pattern) if verdict.startswith("propose") else []
    critical_path = local_critical_path(workflow_graph, pattern)
    explanation = compose_tutorial(verdict, pattern, workflow_graph, factors, roles)

    return {
        "request_summary": request_summary,
        "workflow_graph": workflow_graph,
        "dispatch_verdict": verdict,
        "reasoning_factors": factors,
        "recommended_pattern": pattern,
        "agent_roles": roles,
        "local_critical_path": critical_path,
        "approval_gate": verdict.startswith("propose"),
        "user_facing_explanation": explanation,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate whether a request warrants agent dispatch.")
    parser.add_argument("request", nargs="*", help="Natural language request to evaluate.")
    parser.add_argument("--request-file", help="Read the request text from a file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.request_file:
        request = Path(args.request_file).read_text(encoding="utf-8")
    else:
        request = " ".join(args.request).strip()
    if not request:
        print("Request text is required.", file=sys.stderr)
        return 2

    report = evaluate_request(request)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
