# VERDICT-SCOPE — the row must say which bytes it judged

Owner tool: [`experiments/ptr-engine/tools/verdict_scope.py`](../experiments/ptr-engine/tools/verdict_scope.py)
Ritual section: [`orchestration/VERDICT-RITUAL.md`](../orchestration/VERDICT-RITUAL.md) §8 "Scope: which bytes the row judged"
Machinery reused (not forked): [`experiments/ptr-engine/tools/tree_freeze.py`](../experiments/ptr-engine/tools/tree_freeze.py)

## The defect

A verdict row is `{command, exit, sha}`. That answers *what ran* and *how it ended*, and it is
silent about **which files the command read**. Three rows settled this batch close that gap:

| instance | what the row recorded | what had actually happened |
|---|---|---|
| `SEAM-TEST-RED` | `FAIL exit-1` | acceptance ran the longrun suite; `tests/test_cap_gate.py:205` reddened at `11:33:19 → 11:33:43` because **another card** was editing `cell.py`. Its own seam tests were 5/5 |
| `GRID-PARAMS-DIGEST-SUPERSEDE` | `FAIL exit-1` | `launch_contract_diff --check` passed at `19:27`; `grade_v5.py` moved at `14:44`; the same command afterwards exits 1. The work was correct when it ran |
| `tests/test_cap_gate.py:205` | three `FAIL`s | the assertion itself was stale — the assertion, not the code, was wrong |

None of these can be re-judged from the row: the tree that produced it no longer exists, and the
`sha` field cannot stand in for it. In this workspace the load-bearing files (`cell.py`,
`tree_freeze.py`, this tool) are **untracked**, so `sha f17663d1` is a statement about a commit
that does not contain them.

## Two verbs

### `run` — freeze before, run, freeze after, emit one paste-ready row

```sh
python3 experiments/ptr-engine/tools/verdict_scope.py run \
  --record /tmp/rec.json \
  --paths experiments/ptr-engine/tools/verdict_scope.py \
          experiments/ptr-engine/tests/test_verdict_scope.py \
  -- python3 -m pytest -q experiments/ptr-engine/tests/test_verdict_scope.py
```

It prints one JSON payload line and one human line:

```json
{"command":"python3 -m pytest -q experiments/ptr-engine/tests/test_verdict_scope.py",
 "argv":["python3","-m","pytest","-q","experiments/ptr-engine/tests/test_verdict_scope.py"],
 "exitCode":0,
 "sha":"f17663d1fed0162a7dc3c5a0a58d372c710974c3",
 "head_is_meaningful":false,
 "head_is_meaningful_because":"untracked at HEAD: ... -- the sha names a commit that does not contain these bytes",
 "scope":{"paths":[{"path":"experiments/ptr-engine/tools/verdict_scope.py",
                    "sha_before":"3d9e7b4b…","sha_after":"3d9e7b4b…","moved":false}],
          "moved":[],"exit":0,
          "command":"python3 -m pytest -q experiments/ptr-engine/tests/test_verdict_scope.py",
          "verdict":"clean"}}
```

* `command` is `shlex.join(argv)` — the **exact argv** re-quoted for the row, never a shell
  program (no pipes, no redirects, no `&&`). `argv` carries the tokens unquoted so a reader never
  re-parses.
* `exitCode` is the **command's measured exit**, never the wrapper's 13.
* `sha` is the repo HEAD sampled read-only at wrap start; `head_is_meaningful` says whether that
  commit contains the named bytes.
* `scope.paths` carries `sha_before` / `sha_after` per named path and `moved`; `scope.moved` lists
  what moved; `scope.exit` is the exit judged; `scope.verdict` is `clean` or `tree-moved`.

### `check` — re-judge a row against present bytes

```sh
python3 experiments/ptr-engine/tools/verdict_scope.py check --row /tmp/rec.json
python3 experiments/ptr-engine/tools/verdict_scope.py check --row '{"command":"…","exitCode":0,"sha":"…"}'
```

| classification | meaning | exit |
|---|---|---|
| `same` | present bytes are the bytes the row judged | 0 |
| `moved_since` | the tree moved **after** the row — information, not a verdict | 0 |
| `path_missing` | a path the row named is gone: the row cannot be re-judged | **1** |
| `undatable` | the row carries no `scope` block (written before this tool) | 0 |

## Exit codes

| code | meaning |
|---|---|
| 0 | clean; command exited 0 |
| N | clean; command exited N (its own code, never converted) |
| 2 | refused: no paths, a phantom path, a bad option — the command never ran |
| **13** | `exit_codes.EXIT_TREE_MOVED` — **the tree moved**, not "the work failed" |

13 is imported from `longrun/exit_codes.py` through `tree_freeze` (`EXTERNAL_CODES`), never
re-typed. A `tree-moved` run is **UNSTAMPED**: re-run against the settled tree, do not re-read
the result as a verdict. `failed_and_moved` keeps the command's failure exit but its row is
unstamped too.

## Reuse, and the finding that made it exact

`tree_freeze.py` already freezes `{sha256, size, mtime_ns}`, classifies
`same`/`moved`/`deleted`, reports `created` files inside declared roots, owns the four verdicts
and exit 13, and samples HEAD with `git --no-optional-locks` (no index write, no network). This
tool **imports** it: `run` is `tree_freeze.wrap(...)` plus a `scope` block read back out of the
record; `check` uses `tree_freeze.sha256_of`.

Finding recorded rather than forked: the wrap record carries `moved_detail` only for the paths
that **moved**, so an unmoved path's `sha_after` is its own `sha_before` — exact, because a path
absent from `moved_detail` was classified `same` by the same read that produced the digest.

## Acceptance

```sh
python3 -m pytest -q experiments/ptr-engine/tests/test_verdict_scope.py     # 11 passed
```

Cases: clean → `moved: []` / `clean` / 0 · edit mid-run → 13 with both shas · deleted path →
`check` 1 `path_missing` · no scope → `undatable` 0 · untracked path → `head_is_meaningful:
false` · unchanged tree → `same` 0 · drift after the row → `moved_since` 0 · nonzero command →
payload keeps its exit · empty path set → 2 before the command · phantom path → 2, no row.

## The rule

**A row without a scope block is `undatable`; an untracked load-bearing path makes
`head_is_meaningful: false`.**
