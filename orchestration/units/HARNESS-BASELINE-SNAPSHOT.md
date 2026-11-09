# UNIT HARNESS-BASELINE-SNAPSHOT

**Purpose (one).** Make future harness changes attributable *before* the edit, by
holding byte baselines of every harness file — because `cell.py` is untracked by
git and its 18:54:16Z change is already permanently unattributable.

**Mode.** Offline. Zero requests, no network, no `ask_user_question`. Reads and
copies only; no harness file, row file, grade document or published number edited.
No state-changing git verb (read-only `git --no-optional-locks` only).
**Bound:** 18 tool calls. **Consumed:** see handoff.

## Tasks and outcome

1. **Snapshot** — `state/harness-baselines/20261026T190209Z/`, 10 files under their
   repo-relative paths, `MANIFEST.json` (sha256 `37e50181…`) with
   `{path, sha256, size, mtime_ns, taken_at, harness_sha256_of_HARNESS_FILES}`.
   Every copy re-hashed after copy and equal to its source. Source bytes untouched.
2. **`docs/HARNESS-BASELINES.md`** — what a baseline is for; the rule *"a card that
   edits a harness file writes a baseline first and names it in its handoff"*; how to
   diff two baselines (`diff -u`, sha table); and the plain statement that this
   exists because `cell.py` is untracked and one change is already unattributable.
3. **Retro-diff** — `run_longrun.py` (tracked): `git --no-optional-locks diff --stat
   f17663d1 -- …/run_longrun.py` → 1 file changed, **1295 insertions, 224 deletions**.
   `cell.py`: **no baseline exists prior to 18:54:16Z**, so the change is permanently
   unattributable; its content is not guessed.
4. **Guard** — `experiments/ptr-engine/tools/harness_baseline.py` (`snapshot`,
   `verify <baseline-dir>`), `tests/test_harness_baseline.py` proves green then red.
5. **Nothing else edited.**

## Artifacts

- `state/harness-baselines/20261026T190209Z/**`
- `docs/HARNESS-BASELINES.md`
- `experiments/ptr-engine/tools/harness_baseline.py`
- `tests/test_harness_baseline.py`
- `orchestration/units/HARNESS-BASELINE-SNAPSHOT.md`
- `orchestration/handoffs/HARNESS-BASELINE-SNAPSHOT.json`
- `orchestration/journals/HARNESS-BASELINE-SNAPSHOT.jsonl`

## Evidence

- snapshot: 10 files copied, all `sha256(copy) == sha256(source)`; manifest sha
  `37e50181f225878cc9fcdff9f4fc242346285f456f3fcdf80d461e493d20838a`;
  `harness_sha256_of_HARNESS_FILES = 12616ff35b2941f622c3da67016874c4bae53e735596e08e87361348b62f355d`
- green: `verify` → 10× `same`, `0 differing file(s)`, exit 0.
- red: scratch copy in `/tmp/hb-red/repo`, one appended line to its `cell.py` →
  `moved … c29a9fb3… -> dce7550c…`, `1 differing file(s)`, exit 1.
- `PYTHONPATH=src python3 -m pytest tests/test_harness_baseline.py -q` → 1 passed.

## Assumptions (recorded, per automated-session rule)

- The unit names eight files; `cell.py`'s own `HARNESS_FILES` names five different
  ones (`run_longrun.py`, `client.py`, `grade_v5.py`, `analyze_stats.py`,
  `tools/det_verify.py`). The baseline snapshots the **union (10 files)**, since the
  declared `HARNESS_FILES` digest is what a cell refuses on and cannot be omitted.
- The fixture is a per-invocation input with no fixed path (`cell.py:135`), so it is
  excluded from `harness_sha256_of_HARNESS_FILES`; that number is therefore not
  comparable to the HARNESS-REPIN pin `1f7c6791…`.
- The red test tampers with a *copy* under `/tmp` (append + touch), never a workspace
  source file, because the unit forbids editing a harness file.
