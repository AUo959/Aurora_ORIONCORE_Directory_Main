# Restricted Recovery Candidate Pre-Triage Packet - 2026-06-07

Timestamp: 2026-06-07T15:35:36Z

Scope: root control-plane review packet only. This packet uses the current
tracked recovery-index artifact as review evidence and does not promote,
extract, publish, move, redact, or mutate any recovery candidate. Nested repos
were not edited.

## Source Artifacts

- Primary artifact:
  `reports/analysis/workspace_recovery_index_latest.json`
  - `generated_at`: `2026-05-31T21:04:06Z`
  - `status`: `READY`
  - `mode`: `read_only`
  - retained candidates: `100`
  - `secret_or_key_material` signal count: `36`
- Recovery index config:
  `catalog/recovery_index_manifest.json`
  - The restricted signal is broad and term-based. It fires on path terms
    `accesskey`, `credential`, `key`, `secret`, `token`, or content terms
    `api_key`, `credential`, `private key`, `secret`, `token`.
- Recovery object context:
  `catalog/recovery_objects_to_resolve.json`
  - `recovered-key-aurora-pdk-001` is still `open`, has a raw-material
    non-duplication policy, and says source material contains the full key.
- Secret-scan context:
  `.gitleaksignore`
  - Contains five fingerprint-only baselines for historical
    `catalog/session_state.json` AWS access-token findings.
  - These baselines do not prove credential safety and do not close the owner
    deactivation check.

## Redact-Safe Cross-Checks

No raw candidate contents or matched secret values were copied into this packet.
The checks below used candidate paths and hashes from the tracked recovery-index
artifact.

| Check | Result |
| --- | --- |
| Redacted strict `gitleaks dir` pass over all 36 candidates using default rules, no root allowlist, no `.gitleaksignore` | `0` findings |
| Redacted root-policy `gitleaks dir` pass over all 36 candidates using `.gitleaks.toml` and `.gitleaksignore` | `0` findings |
| Redacted high-risk pattern pass for PEM private key headers, AWS access key IDs, OpenAI/GitHub/Slack/Stripe/Google/SendGrid token prefixes, JWT-like blobs, and explicit secret assignments | `0` hits |
| Current dry-run `python3 tools/workspace_recovery_index.py --summary` | `READY`, findings `none`; not persisted |

The dry-run summary scanned `2381` files and retained `100 of 1017`
candidates. Its target-hint distribution differed slightly from the persisted
artifact (`aurora-cloudbank-symbolic-main`: `52`, `qgia-knowledge-spine-main`:
`12`) but this packet intentionally triages the tracked current artifact rather
than regenerating it.

## Triage Summary

### Likely Live Secret Exposure

Disposition: `none_found_in_retained_36`.

Evidence:

- All 36 restricted candidates have `restricted_material_possible: true` only
  because the recovery-index restricted signal is term-based.
- Redacted strict gitleaks, root-policy gitleaks, and high-risk pattern checks
  found `0` live-secret indicators across the 36 candidate files.

Recommended action:

- Do not trigger emergency credential rotation based on these 36 candidates
  alone.
- Keep the candidates restricted until manual review or promotion decisions are
  made.

Owner action:

- None for live exposure from these 36 candidates based on current evidence.

### Historical Fingerprint-Only Items

Disposition: `outside_candidate_set_but_still_owner_action_required`.

Evidence:

- `.gitleaksignore` contains five fingerprint-only baselines for historical
  `catalog/session_state.json` AWS access-token findings.
- `reports/analysis/root_secret_scan_rollout_receipt__2026-05-31.md` records
  that those were historical findings and that the baseline is not proof of
  deactivation.
- These fingerprints are not the same thing as the 36 recovery-index
  restricted candidates.

Recommended action:

- Keep the fingerprint-only baseline as historical scan hygiene unless the
  owner chooses destructive history remediation.
- Do not copy the root baseline into nested repos.

Owner action:

- Verify/deactivate the historical AWS IAM access key in the AWS console, or
  explicitly accept the fingerprint-only baseline plus no-history-rewrite
  posture.

### Recovered Key-Material References

Disposition: `restricted_review_required_not_live_service_secret_evidence`.

These are candidate files whose restricted signal appears connected to Aurora
recovery-key, activation, symbolic credential, or private-key language. The
redacted detector checks still found no live service secret pattern.

Recommended action:

- Do not quote, duplicate, or promote raw key material from these files.
- Keep each candidate `pending_review` and `not_promoted`.
- If any item is later considered valuable, compare against the canonical owner
  surface first and create a separate promotion receipt.

Owner action:

- Decide whether `recovered-key-aurora-pdk-001` remains an open restricted
  recovery object, needs stronger local access controls, or should be closed as
  non-operational narrative/security material.

| Candidate ref | Path | SHA256 prefix | Evidence | Recommended disposition |
| --- | --- | --- | --- | --- |
| `candidates[0]` | `intake/Aurora_CloudBank_Review_R1_R10.md` | `0ce6bafd0569` | PDK command-code term; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; manual recovery review only |
| `candidates[1]` | `intake/text_conversation_PDK001.txt` | `62b1be683589` | PDK object/digital-key terms; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; tie to `recovered-key-aurora-pdk-001` decision |
| `candidates[3]` | `intake/aurora_scaffold_nexus_meta_narrative.md` | `5db6eb65185e` | PDK command-code terms; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; no canon promotion |
| `candidates[4]` | `intake/TOBIAS_QIN_CHARACTER_PROFILE.md` | `a97b1f18cd23` | PDK command-code and credential terms; strict/root gitleaks `0`; high-risk patterns `0` | Likely narrative/recovery language; keep restricted |
| `candidates[12]` | `_staging/apple_notes_recovery__2026-03-16/L1/ord_drone_fleet_v1.0.py` | `affb09adea88` | PDK command-code plus generic secret/token terms; strict/root gitleaks `0`; high-risk patterns `0` | Review before any code extraction; no secret emergency |
| `candidates[19]` | `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/Please provide a comprehensive report outlining th 1.md` | `892cfd069ed0` | Duplicate SHA family; PDK object/digital-key terms; strict/root gitleaks `0`; high-risk patterns `0` | Treat as historical duplicate; do not duplicate key material |
| `candidates[20]` | `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/Please provide a comprehensive report outlining th.md` | `892cfd069ed0` | Same SHA as `candidates[19]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[21]` | `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs1/Please provide a comprehensive report outlining th.md` | `892cfd069ed0` | Same SHA as `candidates[19]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[28]` | `intake/text_16.txt` | `8f9329969018` | PDK command-code and private-key language; strict/root gitleaks `0`; high-risk patterns `0` | Highest manual-review priority in this group; keep restricted |
| `candidates[30]` | `intake/text_Opal2_Core.txt` | `e53e681dcb77` | PDK command-code term; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; no live-secret evidence |
| `candidates[32]` | `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/relay_handshake.py` | `e55b81ede35e` | PDK command-code terms; strict/root gitleaks `0`; high-risk patterns `0` | Review as historical bridge code before extraction |
| `candidates[37]` | `_staging/orion_ord_review_fix/zipwiz_fixed.md` | `4d969de0a990` | PDK command-code plus secret/token terms; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; no promotion |
| `candidates[57]` | `intake/text_CN_v4.txt` | `a4da266ce231` | PDK command-code and token terms; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; term-only secret signal |
| `candidates[58]` | `intake/text_CN_v5.txt` | `bae5c5cf7575` | PDK command-code and token terms; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; term-only secret signal |
| `candidates[59]` | `intake/text_CN_v6.txt` | `20a96a39ce51` | PDK command-code and token terms; strict/root gitleaks `0`; high-risk patterns `0` | Keep restricted; term-only secret signal |
| `candidates[79]` | `intake/text_44.txt` | `884ebf9a21f7` | PDK command-code and token terms; strict/root gitleaks `0`; high-risk patterns `0` | `review-required`; keep restricted |
| `candidates[89]` | `.gitleaks.toml` | `210ec053f1d1` | Policy file mentions PDK allowlist context; strict/root gitleaks `0`; high-risk patterns `0` | Policy false positive; keep as managed root policy |

### Obvious False Positives

Disposition: `term_only_restricted_signal`.

These candidates match generic `token`, `credential`, `secret`, or `api_key`
language, or are duplicate historical archive/index files. Redacted detector
checks found no live-secret patterns.

Recommended action:

- No credential rotation or emergency remediation.
- Leave candidates as recovery evidence only.
- If future scanners flag any one of these, triage that scanner finding by
  fingerprint and rule ID before adding an allowlist entry.

Owner action:

- None unless the owner wants to lower recovery-index noise by tuning the
  restricted signal or adding a separate `restricted_false_positive_reason`
  metadata field in a future tooling change.

| Candidate ref | Path | SHA256 prefix | Evidence | Recommended disposition |
| --- | --- | --- | --- | --- |
| `candidates[5]` | `_staging/orion_ord_review_fix/package/tests/test_ord_policy_engine.py` | `668c0487f5e4` | Test file; `api_key`/`token` terms; strict/root gitleaks `0`; high-risk patterns `0` | Obvious fixture/test false positive |
| `candidates[6]` | `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/QuantumSymbolic_Index.txt` | `7928a9ab7122` | Duplicate SHA family; credential/secret/token terms; strict/root gitleaks `0`; high-risk patterns `0` | Historical index false positive |
| `candidates[7]` | `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs1/QuantumSymbolic_Index.txt` | `7928a9ab7122` | Same SHA as `candidates[6]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[10]` | `intake/text_25.txt` | `9e9284953f07` | Single token term; strict/root gitleaks `0`; high-risk patterns `0` | Term-only false positive |
| `candidates[16]` | `SPEC__WARRANT_LENS__v1.md` | `cc8d36dbe8d3` | Spec document; token terms; strict/root gitleaks `0`; high-risk patterns `0` | Spec-language false positive |
| `candidates[18]` | `AGENTS.md` | `bda97261bf37` | Agent reference mentions secret scanning; strict/root gitleaks `0`; high-risk patterns `0` | Root-doc false positive |
| `candidates[22]` | `intake/threadcore_symbiosis_delta_manifest.md` | `830751e3f4e7` | Token term; strict/root gitleaks `0`; high-risk patterns `0` | Term-only false positive |
| `candidates[26]` | `_staging/orion_ord_review_fix/package/staging/legacy_pack/SOURCE__Recovered__ORD_DroneDispatch__v0.1__2026-03-10.py` | `1b9b9f8d6316` | Generic `api_key`/credential/secret/token terms; strict/root gitleaks `0`; high-risk patterns `0` | Review code value separately; no secret finding |
| `candidates[40]` | `archives/unzipped/Complete Archive 4_19 copy/COMMANDCORE_FULL_INDEX_v1.json` | `f6d89ce079da` | Token terms in historical index JSON; strict/root gitleaks `0`; high-risk patterns `0` | Historical index false positive |
| `candidates[55]` | `_staging/apple_notes_recovery__2026-03-16/L2/MULTILINGUAL_BEAMFORMING_ARRAY_SEED.md` | `91703ee9e575` | Credential/token terms; strict/root gitleaks `0`; high-risk patterns `0` | Concept-language false positive |
| `candidates[70]` | `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/Au_Archive_62_619/54726075.md` | `041dee63fc75` | Token terms; strict/root gitleaks `0`; high-risk patterns `0` | Historical narrative false positive |
| `candidates[92]` | `archives/unzipped/Complete Archive 4_19 copy/formatted_galactic_union_memory_index (1).json` | `9d88c01c13ef` | Duplicate SHA family; token terms; strict/root gitleaks `0`; high-risk patterns `0` | Historical duplicate false positive |
| `candidates[93]` | `archives/unzipped/Complete Archive 4_19 copy/formatted_galactic_union_memory_index 2 (1).json` | `9d88c01c13ef` | Same SHA as `candidates[92]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[94]` | `archives/unzipped/Complete Archive 4_19 copy/formatted_galactic_union_memory_index 2.json` | `9d88c01c13ef` | Same SHA as `candidates[92]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[95]` | `archives/unzipped/Complete Archive 4_19 copy/formatted_galactic_union_memory_index.json` | `9d88c01c13ef` | Same SHA as `candidates[92]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[96]` | `archives/unzipped/Complete Archive 4_19 copy/merged_galactic_union_memory_index (1).json` | `c534bdc1dd3d` | Duplicate SHA family; token terms; strict/root gitleaks `0`; high-risk patterns `0` | Historical duplicate false positive |
| `candidates[97]` | `archives/unzipped/Complete Archive 4_19 copy/merged_galactic_union_memory_index 2 (1).json` | `c534bdc1dd3d` | Same SHA as `candidates[96]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[98]` | `archives/unzipped/Complete Archive 4_19 copy/merged_galactic_union_memory_index 2.json` | `c534bdc1dd3d` | Same SHA as `candidates[96]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |
| `candidates[99]` | `archives/unzipped/Complete Archive 4_19 copy/merged_galactic_union_memory_index.json` | `c534bdc1dd3d` | Same SHA as `candidates[96]`; strict/root gitleaks `0`; high-risk patterns `0` | Same disposition as duplicate family |

## Decision Notes

- `restricted_material_possible` is a handling flag, not proof of a credential
  leak.
- Candidate paths and SHA256 prefixes are safe evidence references; source
  lines and matched values were intentionally omitted.
- The retained 36 should remain recovery candidates only:
  `pending_review` and `not_promoted`.
- The only owner-facing security action still carried forward is the historical
  AWS IAM access-key verification/deactivation from the root secret-scan
  baseline. That item is not newly discovered by this packet.

## Recommended Next Steps

1. Owner verifies/deactivates the historical AWS IAM key or accepts the
   fingerprint-only historical baseline posture.
2. If the recovery-index restricted signal is too noisy, add a future tooling
   enhancement that records redacted per-candidate restricted-term reasons and
   false-positive dispositions without source excerpts.
3. If any recovered key-material candidate is considered for extraction, run a
   separate canon-promotion review against the named owner surface and leave a
   promotion receipt. Do not infer promotion from this packet.
