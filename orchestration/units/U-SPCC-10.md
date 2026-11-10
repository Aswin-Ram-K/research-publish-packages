# U-SPCC-10 — Provenance of the TX-AGG fixture pinned by rows-agg-fetch-mt36

**Status: DONE — classification UNVERIFIABLE.**

## Question
`experiments/ptr-engine/measure/rows-agg-fetch-mt36.jsonl` pins a `fixture_sha256`
that resolves to no file on disk. Is the fixture recoverable, deleted, or unverifiable?

## Answer
Unverifiable. The pinned content was overwritten in place at 2026-11-09T08:57:28Z,
after the last run that used it, and was never committed.

## Digest inventory
`wc -l` = 41 rows, one distinct digest on all 41:
`2b416d827c36ec958aa50e54db4ec5d52f72f061e7c39e9a417b5f0b2078370c`
- `fixture_path` = `/home/zer0null/research extractor/experiments/ptr-engine/longrun/tasks-v7/TX-AGG.v1.json`
- `fixture_id` = `TX-AGG.TX-AGG.v1`, `generation` = `gen-7`, `task_id` = `TX-AGG`
- `arm` = `bounded-context-fetch`, `model` = `occamy-1.0-NVFP4`, `engine` = `sglang`
- `run_id` = `longrun-2026-11-09T084217Z-bounded-context-fetch-r1`
- `claim` = `none`, `comparison_eligible` = `false` (all rows)

The digest is pinned by **278 rows total** in six files (54 mt50, 36 fetch-test,
10 fetch-r1, 100 masking-r1, 37 fetch-test2, 41 mt36) — not 400+.

## Candidates and comparison
| Path | sha256 | Verdict |
|---|---|---|
| `experiments/ptr-engine/longrun/tasks-v7/TX-AGG.v1.json` | `178042c254f7b732f57603985de35adf8e3722f80507219103c0f7b259e81b03` | **differs** — same ids (gen-7, TX-AGG.v1, N=100, wall_tokens 4312) but different content |
| whole workspace, 56,431 files hashed | — | **no byte match** for `2b416d82…` |
| reserialization sweep (schema /1,/2 × indent {None,1,2,3,4} × sort_keys × ensure_ascii × newline) | — | **no match** — not a formatting variant |
| `/` (maxdepth 6, `TX-AGG*.json`) | — | only the single repo path |

Content-level: all 26 rows embedding a `checkpoint` match on id/turn/question/source
but **disagree on `expected`** (0 of 26 agree): e.g. `cp.TX-AGG.g00.d2` row `20786`
vs disk `156145`; `g01.d2` `60786` vs `210513`; `g02.d2` `100786` vs `269767`. The
on-disk file is a re-generated TX-AGG with different ground truths.

## Git history
- Only commit touching the path: `9fadcc9` (2026-11-09 06:56:48 -0600) — already the
  post-rewrite bytes; every historical blob of the path hashes `178042c2…`.
- `git log --all --diff-filter=D --name-only -- '*agg*' '*mt36*' '*TX-AGG*'`: empty.
- `git status`/`git diff` for the path: clean.
- `ctime` = `mtime` = `2026-11-09 02:57:28 -0600` = `08:57:28Z` — a real in-place write.
- 20 manifests from 08:21:44Z to 08:49:43Z record `fixture.sha256 = 2b416d82…`, so the
  file genuinely had those bytes at run time; the rewrite came 8 min after the last one.

## Claim limits
May support: recorded per-row measurements, the run's existence with that fixture digest,
the answers emitted and their grading against each row's own recorded expected values.
May not support: reproducibility (prompt prefix unreconstructable), any substitution of the
current on-disk fixture's numbers, cross-arm comparability, or "absent = 0".

## Deliverable
`measure/FIXTURE-MAP-MT36.note` (provenance record; not a mapping claim — a mapping
would be false because no same-content document exists).
The test was **not** fixed; its red state stays the correct signal.
