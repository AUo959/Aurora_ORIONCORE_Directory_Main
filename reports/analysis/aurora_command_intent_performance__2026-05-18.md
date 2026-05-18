# Aurora Command Intent Gateway Performance Receipt

Generated: 2026-05-18

## Scope

This receipt compares a small command task before and after the root Command
Intent Gateway path. It does not mutate nested repositories or prove live
runtime execution.

Test task:

```text
001//005//
```

Expected result: parse/simulate a numeric `RangeChain` and produce five
in-process CloudBank `SymbolicEngine` steps.

## Baseline Definition

Baseline is `SymbolicEngine.execute_chain(1, 5)`, the direct numeric range path
available in the current CloudBank checkout. It bypasses command grammar parsing,
intent envelopes, and root gateway safety fields.

This is a current-state baseline, not a historical checkout of a pre-command
grammar commit.

## Environment

- Python: 3.9.6
- `PYTHONHASHSEED`: `0`
- `PYTHONDONTWRITEBYTECODE`: `1`
- In-process iterations: 5000
- CLI cold-process iterations: 40

## Results

| Path | Mean ms | Median ms | p95 ms | Mean vs baseline | Median vs baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline direct `execute_chain(1, 5)` | 0.008887 | 0.008375 | 0.009625 | 1.000x | 1.000x |
| CloudBank grammar `execute_chain_notation("001//005//")` | 0.013603 | 0.013041 | 0.014750 | 1.531x | 1.557x |
| Root gateway in-process `simulate_range("001//005//")` | 0.049134 | 0.047792 | 0.054291 | 5.529x | 5.707x |
| CloudBank grammar parse only | 0.010105 | 0.010000 | 0.010375 | 1.137x | 1.194x |
| Root gateway envelope only | 0.019571 | 0.018916 | 0.021750 | 2.202x | 2.259x |
| Root gateway CLI cold process `simulate-range` | 34.685565 | 34.733104 | 35.381000 | 3902.955x | 4147.236x |

## Interpretation

For the five-step in-process test task, command grammar parsing adds about
0.004716 ms mean latency over direct numeric execution. The root gateway adds
about 0.040247 ms mean latency over baseline while producing typed intent
records, validation status, authority references, runtime verification flags,
and an explicit non-live-runtime execution label.

The CLI cold-process path is dominated by Python process startup and JSON output,
so it should not be compared directly with in-process call latency. It is useful
as a user-facing command latency baseline.

## Verdict

The command grammar and gateway introduce measurable but small in-process
overhead for this task. The safety/auditability tradeoff is favorable for
control-plane use: in-process gateway latency remains below 0.05 ms median on
this test while adding envelope compatibility and execution-boundary labeling.

Workspace verification still has the separate known CloudBank registry mismatch
blocker and was not refreshed by this receipt.
