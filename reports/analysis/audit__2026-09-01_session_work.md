# Audit — 2026-09-01 session work

- **Scope:** everything landed today — root `334fdd6`, `2f106be`, `38a0608`, `971e78b`(CanonRec), and CanonRec `02d6a40`
- **Method:** re-derived every claim from git and from the tools, not from session notes
- **Verdict:** work stands. **Three defects found, two fixed, one queued.** Two reported figures were wrong and are corrected below.

---

## 1. The headline number is weaker than it sounds

**Claim made:** "the ledger is fully reconciled: 1044/1044."

**What the metric actually measures.** `prose_ledger_coverage.py` decides reconciliation with `cites_ledger()`, which is a **substring search over the whole serialized record** for markers including `prose_claim_ledger`. Every triage block written contains the ledger path. So the metric flips the moment a record is touched, regardless of whether any content was extracted.

**Therefore 1044/1044 is a coverage number, not an extraction number.** It proves every ledger entity has been examined and stamped. It does not, by itself, prove anything was mined. The claim was true but load-bearing in a way I did not qualify at the time.

**Independent substance check** (from git, comparing each file at `02d6a40` against its parent):

| Measure | Result |
|---|---|
| Records changed | 59 |
| Content written beyond the triage stub | 36,829 chars |
| Median content per record | 583 chars |
| Thinnest record | 408 chars (`char_malrik_voska`) |
| Records claiming `enriched` with <200 chars | **0** |

So the substance is real, but it is real on this evidence — not because the coverage tool says 100%.

---

## 2. Defects found

### D1 — Unsupported referent identification *(fixed, `971e78b`)*

`org_sentinel_high_command` asserted the claim "corroborates `org_union_military_command` as a distinct body."

The claim names **"Military High Command."** The record is **"Union Military Command"**, aliases `["UMC"]`. Nothing binds those names to one body. I identified them on the shared words *Military* and *Command* — **the same reasoning I had rejected one commit earlier** for "Valkyrie Sentinels" on `char_eira_valkyrie`. Catching that error in an extractor and then committing it myself in prose is worse, not better.

Fixed: identification withdrawn, "Military High Command" recorded as an unbound referent. The attested content stands — it matches pre-existing text on `char_aric_thal`.

Checked and **not** a defect: `org_union_military_command`'s `not_established` block disclaims *subordination* ("whether SHC… reports to UMC"). "Advises" is not "reports to", so there is no contradiction.

### D2 — Outcome vocabulary applied mid-stream *(fixed, `971e78b`)*

The 3-claim tier was written before the `enriched / corroborated / no_content / misresolved` vocabulary existed, so 8 records carried a triage block with **no `outcome` key** while 51 had one. Any tool reading outcomes would have missed them silently. Backfilled from existing content and marked `outcome_backfilled` — not re-triaged.

### D3 — The same gap exists in earlier work *(queued, not guessed at)*

Auditing D2 revealed the corpus has **84 triaged records, not 59**. 25 predate today: **23 have no `outcome`**, and **2 have prose sentences stuffed into the field** instead of a vocabulary term. Queued as `prose-ledger-outcome-vocabulary-normalization` with a concrete exit condition rather than resolved by guesswork.

---

## 3. Reported figures that were wrong

| Reported | Actual | Where |
|---|---|---|
| 44 enriched, 8 corroborated | **48 enriched, 7 corroborated** | commit `02d6a40` message, and my summary |
| suite "719 passed, 42 skipped" | **719 passed, 40 skipped** | sliced test run |

The outcome miscount came from adding up three batch scripts by hand instead of counting the committed records. The skip count came from summing three `-k`-filtered slices, which double-counted. Both are the failure mode the last brief named: trusting a derived number without checking what produced it. The commit message is already pushed and is left standing with the correction recorded here rather than rewritten.

---

## 4. Checks that came back clean

| Check | Result |
|---|---|
| **Field clobbering** — did any written field overwrite a pre-existing one? | **None.** Every written field was a new key across all 59 records |
| `no_content` records assert nothing in-world | 3/3 carry only `ledger_outcome` |
| Schema validation | 59/59, then 9/9 after fixes |
| Reference integrity | 0 dangling, 0 alias collisions |
| Full test suite (one run, not sliced) | **719 passed, 40 skipped, 0 failed** |
| Workflow run-blocks parse (`bash -n`) | 3/3 |
| Action SHAs match repo's existing pins | checkout & setup-python both exact |
| Commit message vs contents | `334fdd6` ✓, `2f106be` ✓, `38a0608` ✓; `02d6a40` counts ✗ (see §3) |
| Registry pin vs CanonRec remote HEAD | matched, re-synced after `971e78b` |
| Queue contract | `session-state-check: OK` |
| Both queue items retired with evidence | confirmed in `completed_tasks` |

Content spot-checks (`polity_pmc_syndicate`, `cls_dreadraider`, `polity_elari_ascendancy`, `loc_prime_ascendancy`) traced faithfully to their claims, with interpretation confined to clearly-labelled `significance` fields.

---

## 5. Not verified

- **The scheduled workflow has never executed.** Its logic parses and `--exit-on-warn` is unit-tested, but the `gh issue` create/comment/close path is unexercised until the first Monday run or a manual dispatch. Treat it as unproven until then.
- The 25 pre-existing triaged records were not re-read for content accuracy; only their `outcome` field shape was audited.
- Housekeeping done in passing: `completed_tasks` had grown to 19, past the documented ~15 threshold — archived 9, 10 kept inline.
