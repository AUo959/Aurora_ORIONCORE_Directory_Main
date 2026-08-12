"""Aurora Canon Engine (ACE) root-control-plane package."""

from .core import ACEError, ENGINE_VERSION, compile_character_query
from .capability_discovery import (
    CAPABILITY_MANIFEST_DIR,
    build_capability_index,
    load_capability_manifests,
    manifest_semantic_sha256,
    select_invocation_capability,
    validate_capability_manifest,
)
from .character_retrieval import (
    CHARACTER_RETRIEVAL_VERSION,
    build_character_index,
    discover_character_candidates,
    resolve_existing_character_query,
)
from .canon_resolution import (
    ALLOWED_DERIVATION_RULES,
    CANON_RESOLUTION_VERSION,
    compile_canon_query,
    resolve_canon_query,
)
from .engine import resolve_character_query
from .facility import compile_facility_query, resolve_facility_query, validate_coherence_seam
from .invocation import (
    INVOCATION_MODES,
    INVOCATION_SCHEMA_VERSION,
    RUNTIME_BINDING_IDS,
    build_invocation_envelope,
    compile_character_invocation,
    compile_canon_invocation,
    compile_facility_invocation,
    compile_facility_invocation_from_seam,
    resolve_invocation,
    validate_invocation_envelope,
)
from .ledger import DEFAULT_LEDGER_REL, LEDGER_VERSION, append_determination, query_ledger
from .materialize import AUTHORITY_MODES, MATERIALIZER_VERSION, materialize_facility_packet
from .character_materialize import (
    CHARACTER_MATERIALIZER_VERSION,
    materialize_character_packet,
    materialize_packet,
)

__all__ = [
    "ACEError",
    "ALLOWED_DERIVATION_RULES",
    "AUTHORITY_MODES",
    "CANON_RESOLUTION_VERSION",
    "CAPABILITY_MANIFEST_DIR",
    "CHARACTER_MATERIALIZER_VERSION",
    "CHARACTER_RETRIEVAL_VERSION",
    "DEFAULT_LEDGER_REL",
    "ENGINE_VERSION",
    "INVOCATION_MODES",
    "INVOCATION_SCHEMA_VERSION",
    "LEDGER_VERSION",
    "MATERIALIZER_VERSION",
    "RUNTIME_BINDING_IDS",
    "append_determination",
    "build_capability_index",
    "build_character_index",
    "build_invocation_envelope",
    "compile_character_invocation",
    "compile_canon_invocation",
    "compile_canon_query",
    "discover_character_candidates",
    "compile_character_query",
    "compile_facility_invocation",
    "compile_facility_invocation_from_seam",
    "compile_facility_query",
    "load_capability_manifests",
    "manifest_semantic_sha256",
    "materialize_character_packet",
    "materialize_facility_packet",
    "materialize_packet",
    "query_ledger",
    "resolve_canon_query",
    "resolve_existing_character_query",
    "resolve_character_query",
    "resolve_facility_query",
    "resolve_invocation",
    "select_invocation_capability",
    "validate_capability_manifest",
    "validate_coherence_seam",
    "validate_invocation_envelope",
]
