from __future__ import annotations

from pathlib import Path


def replace(path_str: str, old: str, new: str) -> None:
    path = Path(path_str)
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"needle not found in {path}: {old[:120]!r}")
    if text.count(old) != 1:
        raise SystemExit(f"needle not unique in {path}: count={text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


# Register retrieval and relation-enrichment specialists before generation tools.
replace(
    "tools/ace/core.py",
    '''        {
            "capability_id": "ace.capability.canonrec.project.name_reservations",''',
    '''        {
            "capability_id": "ace.capability.canonrec.retrieve.character",
            "name": "ACE CanonRec existing-character retriever",
            "repository": "root",
            "path": "tools/ace/character_retrieval.py",
            "operations": ["build_character_index", "retrieve_existing_character"],
            "mutation_model": "read_only",
            "status": "active",
        },
        {
            "capability_id": "ace.capability.canonrec.enrich.character_relations",
            "name": "ACE committed character relation evidence enricher",
            "repository": "root",
            "path": "tools/ace/character_retrieval.py",
            "operations": ["match_role", "match_faction", "match_location", "disambiguate_referent"],
            "mutation_model": "read_only",
            "status": "active",
        },
        {
            "capability_id": "ace.capability.canonrec.project.name_reservations",''',
)

# Make the existing compile_character_query do retrieval preflight before any
# role/faction/location requirement or ID/name generation.
replace(
    "tools/ace/core.py",
    '''    if mode not in {"plan_only", "commit_ready"}:
        raise ACEError("ACE MVP supports plan_only and commit_ready modes", code="input_validation_failed")
    for field in ("role", "faction_id", "location_type"):
        if not isinstance(context.get(field), str) or not str(context[field]).strip():
            raise ACEError(f"character context requires non-empty {field}", code="input_validation_failed")
    observed = context.get("observed_behavior", [])
    if not isinstance(observed, list) or any(not isinstance(item, str) for item in observed):
        raise ACEError("observed_behavior must be an array of strings", code="input_validation_failed")

    baselines = repository_baselines(root)
''',
    '''    if mode not in {"plan_only", "commit_ready"}:
        raise ACEError("ACE MVP supports plan_only and commit_ready modes", code="input_validation_failed")
    observed = context.get("observed_behavior", [])
    if not isinstance(observed, list) or any(not isinstance(item, str) for item in observed):
        raise ACEError("observed_behavior must be an array of strings", code="input_validation_failed")

    # Retrieval is constitutive precedence, not an optional optimization. An
    # existing canonical referent must be resolved (or explicitly blocked as
    # ambiguous) before identity allocation, NameService, or CharForge can run.
    from .character_retrieval import compile_existing_character_query_if_applicable

    retrieval_query = compile_existing_character_query_if_applicable(
        question,
        context,
        seed=seed,
        mode=mode,
        requester_kind=requester_kind,
        requester_id=requester_id,
        session_ref=session_ref,
        root=root,
    )
    if retrieval_query is not None:
        return retrieval_query

    for field in ("role", "faction_id", "location_type"):
        if not isinstance(context.get(field), str) or not str(context[field]).strip():
            raise ACEError(f"character context requires non-empty {field}", code="input_validation_failed")

    baselines = repository_baselines(root)
''',
)

# Route retrieve-character through the same invocation facade, leaving complete
# character queries on the existing generator engine.
replace(
    "tools/ace/invocation.py",
    '''from .engine import resolve_character_query
from .canon_resolution import compile_canon_query, resolve_canon_query
''',
    '''from .engine import resolve_character_query
from .character_retrieval import resolve_existing_character_query
from .canon_resolution import compile_canon_query, resolve_canon_query
''',
)
replace(
    "tools/ace/invocation.py",
    '''    if entity_type == "character":
        if root is None:
            determination = resolve_character_query(query, output_dir)
        else:
            determination = resolve_character_query(query, output_dir, root=root)
''',
    '''    if entity_type == "character":
        resolver = resolve_existing_character_query if query.get("query_kind") == "retrieve" else resolve_character_query
        if root is None:
            determination = resolver(query, output_dir)
        else:
            determination = resolver(query, output_dir, root=root)
''',
)

# Public package exports.
replace(
    "tools/ace/__init__.py",
    '''from .canon_resolution import (
''',
    '''from .character_retrieval import (
    CHARACTER_RETRIEVAL_VERSION,
    build_character_index,
    discover_character_candidates,
    resolve_existing_character_query,
)
from .canon_resolution import (
''',
)
replace(
    "tools/ace/__init__.py",
    '''    "CANON_RESOLUTION_VERSION",
''',
    '''    "CANON_RESOLUTION_VERSION",
    "CHARACTER_RETRIEVAL_VERSION",
''',
)
replace(
    "tools/ace/__init__.py",
    '''    "build_capability_index",
''',
    '''    "build_capability_index",
    "build_character_index",
''',
)
replace(
    "tools/ace/__init__.py",
    '''    "compile_canon_query",
''',
    '''    "compile_canon_query",
    "discover_character_candidates",
''',
)
replace(
    "tools/ace/__init__.py",
    '''    "resolve_canon_query",
''',
    '''    "resolve_canon_query",
    "resolve_existing_character_query",
''',
)

# CLI capability plan must reflect retrieval instead of generator requirements.
replace(
    "tools/aurora_ace.py",
    '''    if entity_type == "character":
        required |= {
            "ace.capability.canonrec.project.name_reservations",
            "ace.capability.gumas.state.build_character",
            "ace.capability.canonrec.validate.entity",
            "ace.capability.canonrec.validate.naming_receipt",
        }
''',
    '''    if entity_type == "character":
        if query.get("query_kind") == "retrieve":
            required |= {
                "ace.capability.canonrec.retrieve.character",
                "ace.capability.canonrec.enrich.character_relations",
            }
        else:
            required |= {
                "ace.capability.canonrec.project.name_reservations",
                "ace.capability.gumas.state.build_character",
                "ace.capability.canonrec.validate.entity",
                "ace.capability.canonrec.validate.naming_receipt",
            }
''',
)
