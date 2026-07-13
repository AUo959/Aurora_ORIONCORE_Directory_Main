# doc-staleness-auditor

An on-demand CLI that scans Markdown docs across Aurora-ecosystem repos, checks
every machine-verifiable claim against **directly observed ground truth**, and
drafts evidence-backed fixes — routed either into a normal PR or, for
CanonRec-style repos, into the Drift Containment Protocol.

## Evidence policy (the whole point of this tool)

A claim is marked **`CONFIRMED`** *only* when it was checked against a **primary
evidence source**:

| method | primary source |
|---|---|
| `git_tree_lookup` | the actual `git ls-tree` state at HEAD |
| `source_content_read` | actual file content, read and matched (not "file exists") |
| `python_ast_parse` | actual Python source parsed with `ast` |
| `config_file_read` | actual `VERSION` / `package.json` / `pyproject.toml` / `.python-version` / `runtime.txt` value |
| `recomputed_count` | a count recomputed from the real tree using a stated rule |

A claim is **never** confirmed because:

* **another doc says the same thing** — doc-to-doc corroboration is not evidence
  (see `test_doc_to_doc_is_not_evidence`); or
* **a file merely exists** at a referenced path — existence ≠ content correctness.
  Symbol/version/count claims must be read out of real content, not inferred
  from a path stat.

Every finding carries an `evidence` object naming the exact **file(s), line
range(s), and git sha** inspected, so a human can independently re-check the
verdict. A claim with no machine-checkable ground truth (e.g. a narrative
architecture assertion) is labeled **`UNVERIFIABLE_BY_AUTOMATION`** — never
silently passed as confirmed.

## Claim types extracted

* **path** — referenced file/dir paths (`` `tools/foo.py` ``)
* **symbol** — function/class/route names (`` `parse_config` ``, `function X in Y`)
* **numeric** — counts (`49 docs`, `12 tests`), scoped to a directory
* **version** — version strings (`v2.2`, `2.1.0`, `Python 3.11`)

## Commands

```bash
# run from the repo that contains this tool; or set PYTHONPATH=tools
cd tools

# 1. extract a claims ledger from every .md file
python3 -m doc_staleness_auditor scan --repo /path/to/target --out claims.json

# 2. verify each claim against ground truth at the target's HEAD
python3 -m doc_staleness_auditor verify --claims claims.json --repo /path/to/target \
    --out findings.json --md findings.md

# 3. draft diff-style fixes for STALE findings (evidence cited inline)
python3 -m doc_staleness_auditor plan --findings findings.json --out plan.json

# 4. apply fixes, routed by per-repo governance mode (dry-run unless --apply)
python3 -m doc_staleness_auditor execute --findings findings.json \
    --repo <repo-name-in-repos.yaml> --repo-root /path/to/target [--apply]
```

`--backend {auto,git,fs}` selects how the target is read. `git` reads content via
`git show HEAD:<path>` and lists files via `git ls-tree` (works in a shallow /
sparse worktree where files are not on disk); `fs` reads a materialised working
tree; `auto` picks `git` for sparse checkouts, else `fs`.

## Per-repo governance (`repos.yaml`)

`execute` routing is data-driven so new repos/modes need no code change:

```yaml
repos:
  aurora-cloudbank-symbolic:
    governance_mode: standard_pr        # branch + commit + gh pr create (never merge)
  CanonRec:
    governance_mode: canon_promotion_queue   # Drift Containment Protocol, never a canon PR
    drift_log_path: DRIFT_LOG.md
    promotion_queue_path: canon/L1/station/operational_library_v2_2/LOG__PROMOTION_QUEUE__v1.1.md
    quarantine_dir: canon/_quarantine/drift
```

* **`standard_pr`** — writes the drafted edits, opens a branch + PR whose body is
  a table of `{claim, doc-claimed value, observed value, evidence path/line@sha,
  verification method}`. Never merges.
* **`canon_promotion_queue`** — never edits canon content and never opens a PR
  against it. Instead it quarantines the proposed change as a draft under
  `quarantine_dir/`, appends a `## Drift Entry — <date>` block to `DRIFT_LOG.md`
  (matching CanonRec's existing entry format), and appends a proposal bullet to
  the promotion queue for canon-owner review.

## Worked examples (real pilot output, not mocked)

Run against the two pilot repos at their real HEADs. Full run summarised in
`/home/user/workspace/doc_staleness_auditor_pilot_results.md`.

### CONFIRMED — Python symbol via AST

> `Aurora_ORIONCORE_Directory_Main/CLAUDE.md:56` references the session-state
> `load()`/`save()` API.

```
claim   : symbol `load`   (CLAUDE.md:56)
status  : CONFIRMED
evidence: [python_ast_parse] symbol 'load' defined in real source
          tools/session_state_io.py:76 @ b3244113ad77
```
The verifier parsed `tools/session_state_io.py` with `ast` and found the actual
`def load` at line 76 — not merely that the file exists.

### CONFIRMED — version against a config file

```
claim   : version `2.1.0`   (aurora-cloudbank-symbolic tools/command_chain/COMPREHENSIVE_SYNC_321.md:284)
status  : CONFIRMED
evidence: [config_file_read] read first line of VERSION at HEAD -> '2.1.0' @ 5dd18d364070
```

### STALE — CHANGELOG headline vs VERSION

```
claim   : version `2.2.5`   (aurora-cloudbank-symbolic CHANGELOG.md:14)
status  : STALE
observed : VERSION=2.1.0
evidence: [config_file_read] CHANGELOG latest release '2.2.5' vs first line of
          VERSION -> '2.1.0'  (VERSION, CHANGELOG.md @ 5dd18d364070)
```
The changelog's top released heading is `2.2.5`, but the repo's `VERSION` file
still reads `2.1.0`.

### STALE — documented Python floor vs pinned runtime

```
claim   : version `3.11`   (aurora-cloudbank-symbolic .github/copilot-instructions.md:270)
status  : STALE
observed : 3.12 (per runtime.txt)
evidence: [config_file_read] python floor '3.11' vs runtime.txt -> '3.12'
```
The doc says "Target Python 3.11+"; `runtime.txt` pins `python-3.12.0`.

### STALE — broken intra-repo path reference

```
claim   : path `docs/philosophy/PHILOSOPHY.md`
          (Aurora_ORIONCORE_Directory_Main docs/AURORA__CHARTER__MORAL_ARCHITECTURE__v1.0__2026-06-11.md:470)
status  : STALE
observed : <not found>
evidence: [git_tree_lookup] no tracked path 'docs/philosophy/PHILOSOPHY.md' in
          git tree at HEAD; first segment 'docs' is a real top-level dir so this
          is a broken intra-repo reference @ b3244113ad77
```
The Charter links a `docs/philosophy/` set that does not exist in the tree.

### UNVERIFIABLE_BY_AUTOMATION — narrative claim

Prose such as "Our architecture is fundamentally emergent" yields no checkable
claim and is never extracted; a version like a spec doc's own `v1.0` frontmatter
that cannot be bound to a version artifact is returned `UNVERIFIABLE`, not
confirmed.

## Design notes

* **STALE is conservative.** A path is only STALE when it is a *structural*
  intra-repo reference (has a directory whose first segment is a real top-level
  dir) that does not resolve. Bare filenames, out-of-tree/absolute paths, and
  unknown roots are `UNVERIFIABLE` — the tree alone cannot prove the doc wrong.
* **Historical docs are skipped for counts/versions.** Dated reports, handoffs,
  archives, and session logs record values true at authoring time; recomputing
  them against current HEAD would mislabel them.
* **No network for verification.** All ground truth is read from the local
  target repo at HEAD; only `execute --apply` in `standard_pr` mode shells out to
  `git`/`gh`.

## Tests

```bash
python3 -m pytest tools/doc_staleness_auditor/tests -q
```
The suite builds a real throwaway git repo and asserts the evidence policy
end-to-end (CONFIRMED only via primary methods, doc-to-doc is not evidence,
narrative is never confirmed, governance artifacts match the drift-log format).
