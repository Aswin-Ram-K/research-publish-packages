# REPRO.md — can a third party re-derive the numbers from the shipped tree?

Unit: `RELEASE-DATA` · Date: 2026-10-24 · Target: [`release/v0.1`](v0.1/) (945 manifest files, 61,143,643 bytes)
Supersedes the `REPRO-IN-RELEASE` verdict of the same date, which was measured against the pre-repair tree.
Interpreter: `/home/zer0null/reserach extarctor/.venv/bin/python` (Python 3.14.4), i.e. `../../.venv/bin/python`
from `release/v0.1`. `PYTHONDONTWRITEBYTECODE=1` throughout; the pytest runs add `-p no:cacheprovider` so that no
`.pytest_cache` is produced inside the artefact. The venv lives at the **workspace root**, not at `release/` and
not at `release/v0.1/` — `../.venv/bin/python` does not exist (deviation D4).

## Verdict

**YES for every number, with one named limitation.** From `cd release/v0.1`, all three numeric entry points
exit **0** and **69/69 claims re-derive from the shipped bytes alone** — no file needs to be supplied from
outside the package. The gap-closure ledger guard (`tests/test_gap_closure_ledger.py`) still exits **1**, with
`6 failed, 2 passed`; its failures are **unresolvable content refs**, not missing data — paths that a
publication tree structurally cannot contain (limitation L1). That guard is scoped to the working tree, so its
red state here is a property of the artefact, not a numerics finding.

Script paths: the runners live at **`papers/context-cache/`**, never at the tree root. Every command below is
run from `cd release/v0.1` and names the script as `papers/context-cache/<script>`; a root-level
`verify_package.py` does not exist and exits 2.

## Table — measured 2026-10-24 in `release/v0.1`

| # | Command (from `release/v0.1`) | Exit | Decisive output line | Result |
|---|---|---|---|---|
| 1 | `papers/context-cache/verify_package.py` | **0** | `verify_package: PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, 8 script-backed + 61 recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none` | **PASS** |
| 2 | `papers/context-cache/recompute.py all` | **0** | `COVERAGE GUARD PASS  69 claims documented, 67 runnable here + 2 script-backed`; also `GRID GUARD PASS  7/7 configs`, `64 claims checked, all match`, `claim ids are contiguous C01..C69 (no row lost above the maximum)` | **PASS** |
| 3 | `papers/context-cache/recompute_r2.py all` | **0** | `PASS  61/61 values match`, `38/38`, `48/48`, `75/75`, `85/85`, `70/70`, `50/50 values match` — 7 PASS lines (C63, C64, C65, C66, C67, C68, SYSOPT) | **PASS** |
| 4 | `-m pytest tests/test_gap_closure_ledger.py -q -p no:cacheprovider` | **1** | `6 failed, 2 passed in 0.07s` — first cause `AssertionError: unresolvable evidence refs:` → `G11: orchestration/VERDICTS.md:12 (file_line) does not resolve` | **FAIL (limitation L1)** |
| 5 | `-m pytest tests/test_g5_fanout_attribution.py -q -p no:cacheprovider` | **0** | `4 passed in 0.01s` | **PASS** |
| 6 | `-m pytest tests/test_paper_g3_bands.py -q -p no:cacheprovider` | **0** | `13 passed in 0.02s` | **PASS** |

The previous revision reached 2/3 numeric entry points only by pointing a copy at the live `state/` directory
from outside the tree. That workaround is no longer needed: these six rows are all runs **inside** the shipped
tree with nothing mounted or symlinked in.

## What the repair shipped (D1 and D2 are resolved)

Two files, and only two, were added — the minimum set that makes the claims re-derivable and makes the ledger
guard report its real state instead of crashing on a missing file. Both are in `MANIFEST.json`; both were
checked for internal host addresses and absolute home paths before being copied (**zero** occurrences of
`192.168.` and **zero** of `/home/zer0null`, so **0 replacements** were needed and the shipped bytes are the
live bytes).

| Path | Bytes | sha256 |
|---|---|---|
| `state/config/rows.jsonl` | 82,565 | `8154e32d2f98f0d653ed6a3f03af7b6ca5effefd6c03c74c392e6a8819fc00e0` |
| `state/gap-ledger.json` | 25,834 | `56f2722862904ed78115eab427513b7a5b66ac45893b69f47c915c3610aa0b8a` |

`state/config/rows.jsonl` is required by two call sites that resolve through the **release** root
(`ROOT = Path(__file__).resolve().parents[2]`, so `Path(__file__)` stays inside the copy):
`recompute.py:1640` `C63_R2_CELLS = {"R2-VLLM-CELL": ROOT / "state" / "config" / "rows.jsonl"}` and
`recompute_r2.py:557` `C65_R2_PATH = [ROOT / "state" / "config" / "rows.jsonl"]`. Without it both scripts died
at **claim 65 of 69**, leaving C65, C66, C67, C68 and SYSOPT unreachable — 5 of 69 claims. It parses as JSONL:
284 non-blank lines, all valid objects.

`state/gap-ledger.json` is what `tests/test_gap_closure_ledger.py:24` reads
(`LEDGER = ROOT / "state" / "gap-ledger.json"`). Without it that module failed 8/8 on `FileNotFoundError`; with
it the guard reaches the state it is meant to report, i.e. **2 pass and 6 fail on content refs**.

## L1 — the named limitation: the ledger guard cites what a release cannot contain

With both files in place, `tests/test_gap_closure_ledger.py` fails 6 of 8 on **9 unresolvable evidence refs**,
verbatim from the run:

```
G11: `orchestration/VERDICTS.md:12` (file_line) does not resolve
G16: `state/config/live-server-config.json` (path) does not resolve
G16: `scratch/cache-audit/docs/pin_sgl_hicache_design.mdx` (path) does not resolve
G16: `scratch/cache-audit/docs/pin_sgl_radix_eviction_policy.mdx` (path) does not resolve
G16: `scratch/cache-audit/docs/pin_vllm_cache.py` (path) does not resolve
G16: `scratch/cache-audit/docs/pin_vllm_argutils.py` (path) does not resolve
G16: `scratch/cache-audit/docs/pin_sgl_session_radix_cache.mdx` (path) does not resolve
G16: `CACHE-AUDIT` (handoff) does not resolve
G17: `PAPER-FINAL` (handoff) does not resolve
G17: `state/sys-opt-verdict.json` (path) does not resolve
```

These are unfixable **in a release, by design**, and shipping the missing trees to green the guard would be
wrong: `orchestration/` and `scratch/` are workspace provenance (verdict logs, pinned third-party source copies,
unit handoffs) that has never been part of a publication. Two further refs are excluded on the same grounds as
the other 167 redacted files rather than on provenance: `state/config/live-server-config.json` (61,336 bytes) is
a serving-host configuration that carries two internal `192.168.*` addresses, and `state/sys-opt-verdict.json` is
a workspace verdict document, not a numeric source. The remaining six are `scratch/cache-audit/docs/pin_*`
(pinned upstream source copies, five of them) and the two handoffs.

Because the ledger's own statuses re-derive as `unverifiable` when their refs do not resolve, the four
status-recomputation tests fail as a consequence of the same cause. This is recorded as a **limitation, not a
pass**: the guard is a working-tree invariant, green where the files it cites exist (`8 passed` in the live
tree) and red in any faithful artefact. It is **not** evidence either way about the 69 claims, which re-derive
in full in the shipped tree (table rows 1–3).

## Remaining deviations

- **D4 — the venv path.** From `release/v0.1` the interpreter is `../../.venv/bin/python`. `release/.venv` and
  `release/v0.1/.venv` do not exist. Every run above used the correct relative path.
- **D5 — `verify_package.py` is not self-contained outside a sibling paper directory.** Copied alone into a
  scratch layout it reports `verify_package: FAIL — missing papers/context-cache/CLAIMS.md`. Inside the release
  tree (or a faithful copy) that file is present and it passes. Noted so a stripped directory is not mistaken
  for a numeric failure.
- **D6 — not a defect, recorded because it looks like one.** `recompute_r2.py` prints bare
  `PASS 61/61 values match` lines with no claim id, so the C63→61/61 … SYSOPT→50/50 mapping was confirmed by
  running each claim individually, not by assuming the print order.
- **D7 — the claimed path defect in this document did not reproduce.** The brief for this unit stated that
  `release/REPRO.md` documented root-level commands such as `release/v0.1/verify_package.py`. A search of the
  whole of `release/` (`grep -rnE 'python +verify_package\.py|python +recompute(_r2)?\.py|release/v0\.1/verify_package' release/`)
  returns no such line: the previous revision of this file already used `papers/context-cache/…`. What *was*
  wrong is corrected here — the verdict (it read `NO as shipped`), the file and byte counts in the header, the
  `$OLDPWD/.venv/bin/python` line in the reproduce block (that path does not exist), and the two deviations
  D1/D2 that this unit fixed.

## Hygiene

`PYTHONDONTWRITEBYTECODE=1` was set for every invocation and pytest ran with `-p no:cacheprovider`;
`find release/v0.1 -name __pycache__ -o -name .pytest_cache` returns nothing. One `.pytest_cache/` created by an
earlier unfiltered run was deleted before `MANIFEST.json` was regenerated, so it is not listed and not shipped.

## Reproduce this report

```
export PYTHONDONTWRITEBYTECODE=1
cd release/v0.1
PY=../../.venv/bin/python

$PY papers/context-cache/verify_package.py                               # exit 0, PASS
$PY papers/context-cache/recompute.py all                                # exit 0, COVERAGE GUARD PASS
$PY papers/context-cache/recompute_r2.py all                             # exit 0, 7x PASS n/n
$PY -m pytest tests/test_gap_closure_ledger.py -q -p no:cacheprovider    # exit 1, 6 failed 2 passed (L1)
$PY -m pytest tests/test_g5_fanout_attribution.py -q -p no:cacheprovider # exit 0, 4 passed
$PY -m pytest tests/test_paper_g3_bands.py -q -p no:cacheprovider        # exit 0, 13 passed
```

Sanitisation, run against the whole shipped tree:

```
grep -rE '192\.168\.' release/v0.1 | wc -l        # 0
grep -rE '/home/zer0null' release/v0.1 | wc -l    # 0
```

Manifest, recomputed from disk and self-verified:

```
entries=945  files_on_disk=946  entries == files-1 -> True  (MANIFEST.json never lists itself)
sha256 mismatches over 945 entries: 0
```

## Self-sufficiency

**Self-sufficient for every number.** All 69 claims in `CLAIMS.md` re-derive, `verify_package.py` maps them 1:1,
and the two R2 runners' 7 value sets match, using nothing outside `release/v0.1`.

**Not self-sufficient for workspace provenance.** The gap-closure ledger cites 9 files that exist only in the
working tree (`orchestration/`, `scratch/`, two serving-side `state/` documents); those are deliberately absent
and their guard is expected to be red here (L1).
