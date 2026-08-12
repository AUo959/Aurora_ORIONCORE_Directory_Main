"""Aurora Canon Engine (ACE) root-control-plane package."""

from .core import ACEError, ENGINE_VERSION, build_capability_index, compile_character_query
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

__all__ = [
    "ACEError",
    "ALLOWED_DERIVATION_RULES",
    "AUTHORITY_MODES",
    "CANON_RESOLUTION_VERSION",
    "DEFAULT_LEDGER_REL",
    "ENGINE_VERSION",
    "INVOCATION_MODES",
    "INVOCATION_SCHEMA_VERSION",
    "LEDGER_VERSION",
    "MATERIALIZER_VERSION",
    "append_determination",
    "build_capability_index",
    "build_invocation_envelope",
    "compile_character_invocation",
    "compile_canon_invocation",
    "compile_canon_query",
    "compile_character_query",
    "compile_facility_invocation",
    "compile_facility_invocation_from_seam",
    "compile_facility_query",
    "materialize_facility_packet",
    "query_ledger",
    "resolve_canon_query",
    "resolve_character_query",
    "resolve_facility_query",
    "resolve_invocation",
    "validate_coherence_seam",
    "validate_invocation_envelope",
]
