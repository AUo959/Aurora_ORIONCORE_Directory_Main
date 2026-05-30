# Ingest Contract

Use these checks during automatic ingestion of new Python code and logic.

## Adapter Contract

- Adapter classes should end with `Adapter`.
- Adapter classes should expose `async process_turn(self, input_data)`.
- Adapter classes should expose `get_performance_summary(self)`.
- Adapter modules should include fallback classes prefixed with `_Fallback` when external dependencies are optional.
- Adapter modules should use guarded optional imports (`try/except`) when importing non-required scientific engines.
- Adapter classes should set `self.mode` to expose runtime mode (`fallback`, `external`, etc.).

## Export Wiring Contract

- Package `__init__.py` should import public classes from each module.
- `__all__` should be deterministic and alphabetized.
- Avoid exporting private symbols (`_name`).
- Keep export updates deterministic to minimize merge conflicts.

## Strict Failure Rules

Treat these as hard failures when `--strict` is enabled:

- Python parse errors in module files.
- Adapter class missing async `process_turn`.

Treat these as warnings by default:

- Missing fallback class for adapter modules.
- Missing optional-import guard.
- Missing `self.mode` assignment.
- Missing `get_performance_summary`.
