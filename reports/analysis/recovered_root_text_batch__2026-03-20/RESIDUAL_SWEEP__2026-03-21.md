# Residual Sweep

This pass rechecked the unrecovered remainder after Placement Wave 1, with
special attention to lower-band artifacts that still looked structurally like
code, manifests, continuity outputs, or worldbuilding capsules.

## Result

- New code miss found and routed:
  - `text_symbiosis_graft.txt` -> `tools/prototypes/python/recovered/symbiosis_threadcore_injection.py`
- Additional false-negative promotions confirmed:
  - `text_42.txt` -> elevate to `P2`
  - `text_GitChain.txt` -> elevate to `P3`
  - `text_GitBridge.txt` -> elevate to `P3`
  - `text_46.txt` -> elevate to `P3`
  - `text_45.txt` -> elevate to `P3`
  - `text_Loom.txt` -> elevate to `P3`
  - `text_GitBridge_Capsule.txt` -> elevate to `P3`
  - `text_103.txt` -> elevate to `P3`
  - `text_vector_chain_transfer.txt` -> elevate to `P3`
  - `text_deploy_a1.txt` -> elevate to `P3`

## Why These Moved

- `text_symbiosis_graft.txt` is executable Python patch logic with concrete file
  mutations and runtime anchor binding, so it should not live in prompt residue.
- `text_42.txt` is a structured ecosystem graft capsule with named modules and
  continuity bindings, which makes it canon/worldbuilding follow-up rather than
  discardable residue.
- The promoted `P3` files are all structured continuity, deploy, registration,
  or transfer capsules with manifest-like fields that are useful for ops history
  and future routing.

## Remaining Queue After This Sweep

- `P0`: `14`
- `P1`: `0`
- `P2`: `18`
- `P3`: `75`

## Notes

- Root originals remain untouched.
- The recovered `symbiosis_threadcore_injection.py` file was syntax-checked with
  `py_compile`.
- No additional unplaced executable-code artifacts were found in the lower-band
  residual sweep after routing `text_symbiosis_graft.txt`.
