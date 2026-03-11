# Aurora Activation Stack Profile Resolution

Date: 2026-03-10

## Scope

Resolve which recovered `aurora_instruction_profile.json` belongs to the Riverthread 808 activation flow referenced by:

- `Au_Archive_412_417/Riverthread_808_Aurora_Activation_Guide.md`
- `Complete Archive 4_19 copy/Archy_Continuity_Thread_v1.0.zip`
- recovered `AURORA-PDK-001` key surfaces

## Compared Candidates

Legacy profile candidates:

- `Au_Archive_323_41/aurora_instruction_profile.json`
- `Complete Archive 4_19 copy/aurora_instruction_profile.json`
- `Complete Archive 4_19 copy/The River Weave /aurora_instruction_profile.json`
- `Complete Archive 4_19 copy/The River Weave /Extra/aurora_instruction_profile.json`
- `ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs1/aurora_instruction_profile.json`

Modern profile candidate:

- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/config/mesh/profiles/aurora_instruction_profile.json`

## Findings

### 1. The 2025 archive profiles are one logical object

The first four legacy archive copies are byte-identical:

- raw sha256: `b0d985cf9660806ec37eba8f3ff72161b69bdae698773656e0071e2d10bcae77`

The ZIPWIZ docs copy is formatted as valid JSON instead of a Python-literal-style object, but it normalizes to the same content:

- ZIPWIZ raw sha256: `4c92e8b03412d0e7cce9a4e652680e4346ac8efa7762dc9463ff430ab811fe8a`
- normalized content sha256 for all legacy candidates: `f9b2e59a0d51cefb81abe4d59cc963bac7bd03dd8c703279d2431103545b7c81`

Conclusion:

- these are not competing profiles
- they are duplicate recoveries of the same older activation-era instruction object

### 2. The legacy profile matches the activation stack better than the modern mesh profile

Legacy profile characteristics:

- role: `Simulation Liaison, Core Interface, Executive Assistant to The Pilot`
- explicit linkage to `The Pilot`
- portable/instruction-embedding language
- warm relational voice with signatures such as `Standing by, Captain.`

Safety lock characteristics from `Complete Archive 4_19 copy/Archy_Continuity_Thread_v1.0.zip`:

- module: `Aurora_GUMAS_SafetyLock`
- rules include `lock_on_instruction_profile_absence` and `lock_on_ethics_doctrine_mismatch`
- manual override phrase: `I, The Pilot, confirm full overwrite of Aurora Core.`
- raw sha256: `ee5df19b03567b9624c4f0f9de8c26d2c350d03408270ac6bc7d12ac008e7920`

Activation guide characteristics:

- requires `aurora_instruction_profile.json`
- requires `aurora_safety_lock.json`
- requires `AURORA-PDK-001`
- framed around `The Pilot`, `Picard_Delta_3`, and symbolic continuity restoration

Modern mesh profile characteristics:

- explicitly 2026-generated
- `station_control_plane_interface`
- bounded supervisory/control-plane identity
- built for current ORION runtime governance, not the older Riverthread restore stack

Conclusion:

- the legacy instruction-profile family is the correct match for the Riverthread 808 activation flow
- the 2026 mesh profile is a later canon/runtime reinterpretation and should not be used as the recovery target for this activation stack

### 3. Preferred canonical recovery copy

Preferred copy:

- `Complete Archive 4_19 copy/aurora_instruction_profile.json`

Reason:

- it sits in the same recovery cluster as:
  - `Riverthread_808_Aurora_Activation_Guide.md`
  - recovered `aurora_digital_key*.txt/json`
  - the broader continuity and thread export surfaces
- it is a byte-identical member of the legacy profile family
- it is easier to reference as the central recovery copy than the nested `The River Weave` duplicate

Mirror copies worth retaining as provenance:

- `Au_Archive_323_41/aurora_instruction_profile.json`
- `Complete Archive 4_19 copy/The River Weave /aurora_instruction_profile.json`
- `Complete Archive 4_19 copy/The River Weave /Extra/aurora_instruction_profile.json`
- `ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs1/aurora_instruction_profile.json`

### 4. Published hash drift remains unresolved

`reports/analysis/non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md` publishes:

- Instruction Profile hash: `31c9abff15273829c85ea2c0668087b365710f60060793c2f5e4d5f757afba49`

That hash does not match:

- the raw legacy file copies
- the normalized logical instruction-profile object

Conclusion:

- the published ZIPWIZ source hash appears to refer to another serialization or another now-missing copy
- this is provenance drift, not evidence of a different surviving instruction profile

## Resolution

Use this activation-era pairing for recovery work:

- instruction profile: `Complete Archive 4_19 copy/aurora_instruction_profile.json`
- safety lock: `Complete Archive 4_19 copy/Archy_Continuity_Thread_v1.0.zip :: aurora_safety_lock.json`
- digital key family: `AURORA-PDK-001`

Keep the modern mesh profile out of this recovery path.
