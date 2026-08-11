"""Aurora Canon Engine (ACE) root-control-plane package."""

from .core import ACEError, ENGINE_VERSION, build_capability_index, compile_character_query
from .engine import resolve_character_query

__all__ = [
    "ACEError",
    "ENGINE_VERSION",
    "build_capability_index",
    "compile_character_query",
    "resolve_character_query",
]
