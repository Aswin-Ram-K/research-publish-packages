# UNIT CELL-ONE-COMMAND — collapse the cell lifecycle into one command

**Status:** done · **Bound:** ≤34 tool calls, zero inference requests · **Mode:** offline only

## Why

Measured in [`docs/HARNESS-MAP.md`](../../docs/HARNESS-MAP.md): question → one trustworthy graded
cell has cost **40 card rounds and 863 live requests** (7h52m), **31 rounds spending zero requests**
on process. The waste was a hand-run chain (dry-run → run → grade → re-grade → analyse, one round
each) plus checks that were done late or not at all:

| Waste | Cost | Now refused by |
|---|---|---|
| fixture with no `system_prompt` | 386 requests unreadable | stage 1 preflight (exit 2) |
| harness edited mid-cell | 12 requests re-run | stage 2 harness freeze (exit 2) |
| cell started with no budget arithmetic | — | stage 3 budget (exit 3) |
| bare p95 with no `n`, no CI | unquotable output | stage 6 analyse (a refusal, never a bare number) |

## The command

```bash
python3 experiments/ptr-engine/longrun/cell.py \
    --arm <arm> --fixture <path> --turns 48 --reps 1 --budget <requests> \
    [--endpoint <url>] [--expect-harness <sha>]

# zero-request exercise of the whole conductor (CI):
python3 experiments/ptr-engine/longrun/cell.py --arm <arm> --fixture <path> \
    --offline <rows.jsonl> [--out-dir <dir>]
```

## Stages and their exit codes

| # | Stage | Does | Exit |
|---|---|---|---|
| 1 | preflight | fixture parses; `system_prompt` non-empty; every checkpoint has `question`, `turn`, truth (`truth`/`expected`) and an `answer_spec` whose truth is **derived from the source tree by AST** via `grade_v5.derive_truth` (one checkpoint at a time, so the refusal names it); every answer-contract form appears in the system prompt; the arm is one the runner declares | **2** |
| 2 | harness freeze | sha256 of `run_longrun.py`, `client.py`, `grade_v5.py`, `analyze_stats.py`, `tools/det_verify.py`, and the fixture → per-file digests + one combined `harness_sha256`; `--expect-harness` mismatch refuses | **2** |
| 3 | budget | the **runner's own** `--dry-run`; `would_send_total` + 10 % headroom must fit `--budget`; prints would_send_total, budget, required, and the project's 4,320-quota remainder (best-effort: cap minus rows on disk; the runner reports no quota) | **3** |
| 4 | run | `run_longrun.py` unchanged, output streamed through, rows at `measure/rows-cell-<arm>-<stamp>.jsonl` | **4** |
| 5 | grade | `grade_v5.py` on those rows → per-cell verdicts | **5** |
| 6 | analyse | `analyze_stats.py`; per arm `n`, dropped-null, `p50`, `p95` **with interval**, accuracy `passed/decidable` **with Wilson**, each pair's McNemar **or its refusal**; anything unavailable is printed as a REFUSAL, never replaced by a number | **6** (a refusal is exit 0) |
| 7 | record | `measure/cell-<arm>-<stamp>.json` + `.md` beside it (stage lines, harness digest, requests used, grade + analysis verbatim); optional unit handoff | **7** |

`--offline <rows.jsonl>` skips stages 3–4 and runs 5–7 against an existing row file: **zero requests**.

## Tests — `experiments/ptr-engine/longrun/tests/test_cell.py` (offline only)

7 tests, all passing: (a) `--offline` produces JSON + markdown, exit 0, markdown carries an interval
and an `n`; (b) fixture without `system_prompt` → exit 2 naming `system_prompt`; (c) underivable
checkpoint truth → exit 2 naming the checkpoint; (d) `--budget` under `would_send_total` → exit 3 with
a fake runner proving it was never invoked past `--dry-run` and no row file was created; (e) wrong
`--expect-harness` → exit 2; (f) an analysis that must refuse (n=6) prints `REFUSED at n=` and the cell
still exits 0 with the refusal recorded; plus **red→green**: six string mutations of `cell.py`, one per
guard, each asserted to make exactly its own check fail.

```
Ran 7 tests in 0.58s — OK
```

## The one seam

`grade_v5.py` has no `--json` output flag (only `--out`) and prints its verdicts as text. Rather than
edit the sibling, `cell.py` invokes it as a CLI, captures stdout verbatim for the record, and parses the
one-line-per-arm verdict summary itself — a thin adapter inside `cell.py`. `analyze_stats.py` **does**
have `--json`, so the analysis stage reads its machine document and only falls back to text scanning for
the Wilson-interval line.

## Refusals proven offline

```
cell: 1/7 preflight ok checkpoints=3 turns=[12, 24, 46] kinds=['NUM', 'NUM', 'CALL']
cell: 2/7 harness ok harness_sha256=53fb8112f0912b7744d14b448d13ef8ff1ae6bf0032f5e57cf94c981074d8d5e files=6
cell: budget REFUSED(3) would_send_total=48 +10% headroom = 53 exceeds --budget 1
```

`would_send_total` for a 48-turn v5 cell: **48** (one arm, reps=1; N=48, digest_requests=0) — **192**
for all four arms, so 212 with the 10 % headroom against the 4,320-project quota.

## Next unit hint

Run one live cell through `cell.py` with `--expect-harness` pinned to the digest above; nothing else in
the chain should need a human step.
