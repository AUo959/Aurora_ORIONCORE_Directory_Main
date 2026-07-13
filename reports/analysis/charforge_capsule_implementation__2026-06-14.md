# CharForge Capsule Implementation - 2026-06-14

Status: implementation lane opened for Codex while Claude Code is unavailable.
Branch: `codex/charforge-capsule-implementation-2026-06-14`.
Worktree: `/private/tmp/charforge-capsules-20260614`.

## Scope

This pass moves the CharForge capsule idea from design toward implementation
without mutating CanonRec, CloudBank, or live simulation owner repos.

The implemented root surface is an adapter that treats CharForge capsules as
evidence and decision inputs:

- Reads `identity.json`, `traits.json`, `knowledge.jsonl`, `cns.yaml`,
  `state.bin`, `manifest.json`, and `BUILD_RECEIPT.json`.
- Verifies capsule manifest hashes.
- Decodes the 21-slot CharForge state vector.
- Produces `CharacterDecisionProfile` inputs for `CultureModel`.
- Produces `CapsuleEvidenceFact` records that preserve authority tier:
  `CANON`, `OPERATIONAL`, `STAGING`, or `PROPOSED`.

## Files

- `tools/character_capsule_adapter.py`
- `tests/test_character_capsule_adapter.py`

## Validation

Commands run:

```bash
PYTHONPYCACHEPREFIX=/tmp/aurora_pycache python3 -m pytest -q tests/test_character_capsule_adapter.py -p no:cacheprovider
PYTHONPYCACHEPREFIX=/tmp/aurora_pycache python3 -m pytest -q tests/test_mech_gov_001.py -p no:cacheprovider
PYTHONPYCACHEPREFIX=/tmp/aurora_pycache python3 -m py_compile tools/character_capsule_adapter.py tests/test_character_capsule_adapter.py
PYTHONPYCACHEPREFIX=/tmp/aurora_pycache python3 validate_v3.py
python3 tools/character_capsule_adapter.py summarize "<canonical workspace>/GUMAS_SIM_2.5/CanonRec/canon/L2/entities" --authority-tier CANON
```

Results:

- Character capsule adapter tests: 4 passed.
- MECH-GOV-001/CultureModel regression tests: 21 passed.
- Python compile check passed.
- GUMAS v3.0 Forge validator: 45/45 passed.
- CanonRec read-only smoke check: 29 L2 entity capsules discovered and all 29
  verified by manifest. No CanonRec files were written.

## Promotion Safety

No canon material was promoted. The adapter can mark verified `CANON` capsule
facts as established evidence, but `STAGING` capsules stay staging and are not
promotable. Tampered capsules load for inspection but emit `unverified` facts
with lower confidence.

## Next Edits

1. Wire `character_capsule_adapter.load_capsules()` into the phase-two
   `state_builder` once that builder lands.
2. Add a regression fixture based on a real CanonRec capsule after choosing the
   owner surface for test fixtures.
3. Add a GUMAS integration pass that reads capsule decision profiles and applies
   them to faction culture without requiring direct CanonRec mutation.
