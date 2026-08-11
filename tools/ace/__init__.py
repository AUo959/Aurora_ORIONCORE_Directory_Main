"""Aurora Canon Engine (ACE) root-control-plane package."""

from .core import ACEError, ENGINE_VERSION, build_capability_index, compile_character_query
from .engine import resolve_character_query
from .invocation import (
    INVOCATION_MODES,
    INVOCATION_SCHEMA_VERSION,
    build_invocation_envelope,
    compile_character_invocation,
    resolve_invocation,
    validate_invocation_envelope,
)

__all__ = [
    "ACEError",
    "ENGINE_VERSION",
    "INVOCATION_MODES",
    "INVOCATION_SCHEMA_VERSION",
    "build_capability_index",
    "build_invocation_envelope",
    "compile_character_invocation",
    "compile_character_query",
    "resolve_character_query",
    "resolve_invocation",
    "validate_invocation_envelope",
]
