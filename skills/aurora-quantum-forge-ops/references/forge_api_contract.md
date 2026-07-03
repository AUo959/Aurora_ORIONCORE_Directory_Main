# Forge API Contract

## Authoritative Root

`/Users/travisstreets/dev/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19`

Required files:

- `validate_v3.py`
- `engine_v3_patch.py`
- `charforge.py`

## Validation

Run:

```bash
python3 validate_v3.py
```

Expected baseline:

- `GUMAS v3.0 Validation: 45/45 tests passed`

## Engine API

From `engine_v3_patch.py`:

- `GUMASEngineV3(seed: int = 42, ethics_callback=None)`
- `init_scenario(state=None)`
- `full_step() -> (base_result, TickResultV3)`
- `run_v3(n_turns: int = 10)`
- `export_v3_state(path: str)`

## Capsule API

From `charforge.py`:

- `generate_all_capsules(world_state, output_dir, overwrite=False) -> Dict[str, Path]`
- `verify_capsule(bundle_path) -> bool`
- `capsule_summary(bundle_path) -> Dict[str, Any]`

Generated bundle shape:

- `<bundle>/capsule/identity.json`
- `<bundle>/capsule/traits.json`
- `<bundle>/capsule/knowledge.jsonl`
- `<bundle>/capsule/cns.yaml`
- `<bundle>/capsule/state.bin`
- `<bundle>/capsule/runtime.py`
- `<bundle>/capsule/manifest.json`
- `<bundle>/bundle.manifest.json`
- `<bundle>/BUILD_RECEIPT.json`
