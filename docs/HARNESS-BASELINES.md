# Harness baselines — attributing a change before it happens

**Status:** armed 2026-10-26. Baseline `state/harness-baselines/20261026T190209Z/`
(10 files), `MANIFEST.json` sha256 `37e50181f225878cc9fcdff9f4fc242346285f456f3fcdf80d461e493d20838a`.
Guard: [`experiments/ptr-engine/tools/harness_baseline.py`](../experiments/ptr-engine/tools/harness_baseline.py),
test: [`tests/test_harness_baseline.py`](../tests/test_harness_baseline.py).

## Why this exists

`cell.py` is **untracked by git**. On 2026-10-26 it was written at **18:54:16Z**
(sha `e24e867b…` → `c29a9fb3…`). No settled card claims that hunk, and no copy of
the pre-edit bytes exists anywhere in the tree (HARNESS-REPIN scanned 2,406 `.py`
files across `manifests/`, `manifests/archive/`, `scratch/`, `audit/`, `state/logs/`
for `e24e867b`: zero matches). **That change is therefore permanently
unattributable — not "not yet found", but unrecoverable.** This document does not
attempt to guess what it was, and nobody should.

The lesson is mechanism, not culprit. A file that git does not version, edited by
concurrent cards, cannot be attributed *after* the edit. It can only be attributed
*before* it, by holding the pre-edit bytes.

## What a baseline is

A byte-for-byte copy of every file whose contents can change what a cell measures,
plus the untracked/orchestration-adjacent files around them, taken at one instant,
with a manifest of shas. Two independent things are recorded:

1. `harness_sha256_of_HARNESS_FILES` — the same digest `cell.py:332-346` refuses a
   cell on (`--expect-harness`), computed over the five `HARNESS_FILES`
   (`run_longrun.py`, `client.py`, `grade_v5.py`, `analyze_stats.py`,
   `tools/det_verify.py`). The fixture is excluded: it is added per invocation.
2. Per-file `{path, sha256, size, mtime_ns}` for those five **plus** `cell.py`,
   `run_a_star.py`, `spawn_record.py`, `exit_codes.py`, `tree_freeze.py`.

## The rule

> **A card that edits a harness file writes a baseline first and names it in its
> handoff.**

- "Writes a baseline first" means `snapshot` runs and exits 0 **before** the first
  byte of the edit, so the pre-edit sha is on disk.
- "Names it in its handoff" means the handoff's `artifacts` (or evidence) carries
  the baseline directory, e.g. `state/harness-baselines/20261026T190209Z`, and the
  post-edit sha. Then `verify <baseline-dir>` reports exactly which files moved.
- A card that edits a harness file without a baseline is the failure this exists
  to prevent; say so in the handoff rather than reconstructing a story afterwards.

## Commands

```bash
# take a baseline (UTC timestamp directory name by default)
python3 experiments/ptr-engine/tools/harness_baseline.py snapshot

# prove the bytes you are about to change have not moved since the baseline
python3 experiments/ptr-engine/tools/harness_baseline.py verify state/harness-baselines/20261026T190209Z
```

`snapshot` copies to `state/harness-baselines/<label>/<repo-relative path>`, re-hashes
each copy and **refuses (exit 1) if a copied byte differs from its source**. It
never writes to a source file. `verify` prints one line per file —
`same` / `moved` / `deleted` / `added` — prints the baseline sha and the current sha
on any difference, and exits 1 if anything differs. `verify` compares sha only:
an mtime-only touch reports `same` (the bytes did not move), which is intended.

## How to diff two baselines

```bash
A=state/harness-baselines/<earlier>; B=state/harness-baselines/<later>
# byte diff per file
diff -u "$A/experiments/ptr-engine/longrun/cell.py" "$B/experiments/ptr-engine/longrun/cell.py" | head -100
# or wholesale
diff -ru "$A" "$B" --exclude=MANIFEST.json
# sha table (path, earlier, later)
python3 - "$A" "$B" <<'PY'
import json,sys
a={f["path"]:f["sha256"] for f in json.load(open(sys.argv[1]+"/MANIFEST.json"))["files"]}
b={f["path"]:f["sha256"] for f in json.load(open(sys.argv[2]+"/MANIFEST.json"))["files"]}
for p in sorted(set(a)|set(b)):
    print("%-55s %s -> %s %s" % (p, a.get(p,"MISSING")[:8], b.get(p,"MISSING")[:8],
                                 "" if a.get(p)==b.get(p) else "CHANGED"))
PY
```

## The baseline taken when this was armed

| path | sha256 (first 8) | size |
|---|---|---|
| experiments/ptr-engine/longrun/run_longrun.py | `0d581d1f` | 154535 |
| experiments/ptr-engine/longrun/client.py | `5aa23bb5` | 41593 |
| experiments/ptr-engine/longrun/grade_v5.py | `056eb605` | 44739 |
| experiments/ptr-engine/longrun/analyze_stats.py | `800c8f6c` | 82694 |
| experiments/ptr-engine/tools/det_verify.py | `12ccc74e` | 46515 |
| experiments/ptr-engine/longrun/cell.py | `c29a9fb3` | 112724 |
| experiments/ptr-engine/tools/run_a_star.py | `2c60504a` | 18200 |
| experiments/ptr-engine/longrun/spawn_record.py | `eba15471` | 44084 |
| experiments/ptr-engine/longrun/exit_codes.py | `a57017e1` | 14598 |
| experiments/ptr-engine/tools/tree_freeze.py | `e63e4f7f` | 26998 |

`harness_sha256_of_HARNESS_FILES` = `12616ff35b2941f622c3da67016874c4bae53e735596e08e87361348b62f355d`
(not the pinned `1f7c6791…` of HARNESS-REPIN: that pin covers five files **plus**
the fixture, and the fixture is not a fixed path — the two numbers are not
comparable and neither supersedes the other).

## What is already lost

`cell.py`'s 18:54:16Z edit (`e24e867b` → `c29a9fb3`) has **no prior baseline**,
because this mechanism did not exist before it. It stays unattributable. The next
edit to `cell.py` has a baseline behind it and will be diffable byte-for-byte
against `c29a9fb3`.
