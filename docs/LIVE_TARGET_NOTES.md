# Live-target notes — `/home/zer0null/Duval` is under concurrent modification

Recorded by unit **U5.4** on **2026-10-08** (UTC), strictly read-only. This is a
measurement of the environment, not a statement about intent.

## The fact

`/home/zer0null/Duval`, the acceptance target, is being written to by a
**foreign actor**: the repository's own autonomous self-build loop
(`tools/selfbuild/loop.ts`, `tools/selfbuild/run.ts`). Nothing in this workspace
wrote to it, and no command below must be mistaken for permission to write.

| observation | value |
| --- | --- |
| HEAD at this unit's recon | `3982f26` |
| HEAD after this unit's live windows | `5cdc471a` |
| newest tracked-file mtime | `2026-10-08T11:04:38Z` (`traces/2026-09-28-duval-m0.jsonl`) |
| `.worktrees/run-*` directories | `1` (`run-1`; 29 non-recursive top-level entries) |
| files under `.worktrees/run-1/` | 441 — reported by the sibling unit that caught the foreign write; **this unit deliberately did not recurse** |
| tracked files | 440 (`git ls-files`); **0** of them under `.worktrees/` |
| untracked churn produced by the actor | `.ci-trunk.txt` (281253 bytes), `.lane-j-scratch/` (13 top-level entries) |
| working-tree churn present only on disk | `.ci-trunk.txt` exists at **no** commit |

### HEAD moves (reflog, read-only)

```
5cdc471 2026-10-08 06:04:38 -0500  pull -q --ff-only origin main: Fast-forward
b2bade3 2026-10-08 06:04:37 -0500  checkout: moving from lane/engine-revert to main
b2c5e43 2026-10-08 06:03:52 -0500  commit: chore(engine-revert): settle the trace record
3982f26 2026-10-08 06:03:15 -0500  commit: fix(selfbuild): revert the tree after a REFUSED candidate
b2bade3 2026-10-08 06:03:15 -0500  reset: moving to HEAD
b2bade3 2026-10-08 06:02:59 -0500  checkout: moving from main to lane/engine-revert
b2bade3 2026-10-08 06:01:38 -0500  pull -q --ff-only origin main: Fast-forward
b44e0e1 2026-10-08 06:01:38 -0500  checkout: moving from main to main
```

Nine reflog entries in about three minutes (`06:01:38` → `06:04:38 -0500`, i.e.
`11:01:38Z` → `11:04:38Z`), including branch checkouts and a `reset`. The moves
reported earlier this session (`6deaed0` → `b44e0e1` → `b2bade3`) are the same
activity; HEAD went on to `3982f26` and then `5cdc471a` while this unit ran.

## Consequence 1 — material must be commit-pinned

The copy path (`resextract.docket.copy.Copier`) reads the **working tree**. Bytes
copied after HEAD was recorded therefore need not correspond to that commit.
Measured live on the actor's own churn:

| path | working tree | pinned at HEAD `5cdc471a` | pinned at `3982f26` |
| --- | --- | --- | --- |
| `traces/2026-09-28-duval-m0.jsonl` | `431605e6` (866816 B) | `431605e6` (matches) | `ba6128bf` (864384 B) |
| `.ci-trunk.txt` | `590e007e` (281253 B) | `PathNotFoundAtCommit` | `PathNotFoundAtCommit` |

`3982f26` is the commit HEAD pointed at during this unit's recon, minutes before
the file assumed its current content. A docket that recorded `head_sha=3982f26`
and later copied the working tree holds bytes that commit never contained, and
nothing in the working-tree copy path would notice. `.ci-trunk.txt` shows the
other direction: the working tree contains content no commit describes at all,
so "verifiable at commit X" cannot cover it.

Fix: material is resolved through `resextract.docket.git_source.GitObjectSource`,
which reads the object store (`git cat-file blob <commit>:<path>`, identity from
`git ls-tree -z`) and **never falls back** to the working tree — a path absent at
that commit raises `PathNotFoundAtCommit` rather than silently reading a file.

Note (honest): `README.md`, pinned at the then-current HEAD `5cdc471a`, matched
the working tree exactly (`1f6bbdf6`, blob `2c34d208`, 19578 bytes) because the
file is clean between bursts. The hole is not visible on a clean file; it was
demonstrated on the actor's own changing file, above.

## Consequence 2 — an acceptance run must prove quiescence at run time

**Both live windows returned `quiescent`** — 5 s and 25 s: HEAD stable, 0 tracked
files touched, no new untracked entries, 440 tracked files watched. The burst had
ended at `11:04:38Z`, roughly three minutes before the windows ran.

So a quiescent observation is evidence about *one window*, never about the
target's safety in general. An acceptance run must call
`resextract.refresh.writer.assert_quiescent(target)` at the moment it measures,
and fail with `TargetBusyError` if the target moved; measuring a moving target is
available only by explicitly passing `allow_active=True`.

## Why graphify's ignore behaviour matters

`.worktrees/` holds hundreds of live files — 441 under `run-1` alone — belonging
to another actor's in-flight worktrees, and that count grows while the loop runs.
A previous unit verified that `.worktrees/` contributes **0** graph nodes, which
is why the graph is not swamped by churn that has nothing to do with the target's
intent. The same discipline is applied here: the writer detector's bounded walk
stat'ed exactly the 440 tracked files, saw **0** paths under `.worktrees/`, and
never entered the directory (one `scandir` of `.worktrees` counted `run*`
directories as an observation only).

## Confirmations (this unit wrote nothing)

- `git -C /home/zer0null/Duval rev-parse HEAD` was identical before and after
  every command (`5cdc471afb2a14934030d581a20f6a9bcffb727e`).
- `git status --porcelain` shows only the foreign actor's output —
  `?? .ci-trunk.txt`, `?? .lane-j-scratch/` — and was unchanged across the unit.
- The bounded walk's file count (440) equals `git ls-files` exactly, and
  `git ls-files` names 0 files under `.worktrees/`: no path under `.worktrees/`
  can have been read, because no such path was ever stat'ed or opened.
