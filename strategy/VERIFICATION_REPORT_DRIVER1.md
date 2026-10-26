# VERIFICATION REPORT — release build driver (UBUILD1 / UBUILD1.build.sh)

Verifier: UVERDRIVER1 (independent; not the author). Bound: 20 tool calls.
Driver under test: `orchestration/units/UBUILD1.build.sh`
sha256 `26993bcc6ca78d0dc790c14bba25b43d32dbec9041675e212b239344ca86abfd` (1126 lines).
Pre-refactor baseline used for comparison (found on disk):
`scratch/ubuildall1/orig/UBUILD1.build.sh`, 969 lines, sha256 `f44c71e96c70bef335d53594761460afd6d0546b0fd3d0a282b962e0de34096d`.
All builds ran under `scratch/uverdriver1/**`; no real release destination touched; no git run against `/home/zer0null/Duval`.

## Verdict

**overall: pass.** Every claim reproduced by independent measurement. No contradiction, no
overstatement. One genuine design blind spot in the new check is reported (not fixed), and two
minor non-claims observations are noted.

## 1. Ship-list/tree equality check — REPRODUCED

- Located at `orchestration/units/UBUILD1.build.sh:359-409` (`SHIPLIST_TREE_CHECK_PY`), between the
  clean step (`:351-357`, `rm -rf "$PKG"`) and staging (`:472-473`, `cp -r "$SAN_SRC/." "$PKG/"`).
  Placement therefore precedes staging: claimed, confirmed from the script and from logs.
- Derived from the manifest, not a new literal: the heredoc reads `man["promoted_san_src"]`
  (`:382`) and `man["ship_staged"]` (`:397`); the only list literals in the file are the
  default-package blocks, which predate this change. `SHIPLIST_TREE_CHECK_PY` occurs 0 times in the
  pre-refactor baseline. Not overstated.
- Red case, reproduced twice, independently:
  - manifest perturbation of the default slug (added `results/STALE-ENTRY.json` to `ship_staged`):
    `RED_RC=2`; `FATAL: SHIP-LIST/TREE MISMATCH for package 'gated-read-batching'`;
    `listed but not on disk: ['results/STALE-ENTRY.json']`; `on disk but not listed: []`;
    0 files anywhere under the DEST.
  - same perturbation under a non-default slug (`perturbed-pkg`, one manifest copy, real tree):
    `REDND_RC=2`; `FATAL: SHIP-LIST/TREE MISMATCH for package 'perturbed-pkg'`;
    `listed but not on disk: ['results/STALE-ENTRY.json']`; 0 files under DEST. This proves the check
    runs for non-default packages (the pre-existing default-only tripwire cannot be what fired).
  - opposite direction (tree has an extra file the manifest does not list; tree copy + absolute
    `promoted_san_src`): `REDTREE_RC=2`; `on disk but not listed: ['results/STALE-ENTRY.json']`;
    0 files under DEST.
- Green case, reproduced literally:
  `ship-list/tree check: 29 declared file(s) == 29 present in /home/zer0null/reserach extarctor/scratch/uneutral10/package`
  then the build reaches the gate: `GATE RESULT: FAIL -- 1026 out-of-vocabulary token(s).`,
  `BUILD COMPLETE — the exclusion gate FAILED (exit 1).`, `GREEN_RC=1` (unchanged). 29 files staged.

### Placement reason — assessed independently, reason is real

`tests/test_build_wiring.py:105-110` builds a fake SRC with the promoted tree created **empty**, and
`:200` asserts `log.index("SAN_SRC WIRING:") < log.index("removing any previous target")`. Under the
empty fake tree the check computes 0 present vs 29 listed and fails closed, so if it preceded the
clean step the phrase "removing any previous target" would never be printed and that assertion would
raise `ValueError`. I moved the 2205-byte block to before the clean step on a copy and ran it with
`SRC` = the empty fake tree: log is `SAN_SRC WIRING` (line 1) then `FATAL: SHIP-LIST/TREE MISMATCH`
(line 8) and **no** "removing any previous target"; exit 2. Current order produces it (green log
line 7). The stated reason is the actual reason.

## 2. Archive README index and per-package clean — REPRODUCED

- `README_INDEX_PY` (`:572-610`) reads every `*.toml` in the manifest dir, keeps those whose
  `name` directory exists under `$DEST/packages/`, takes `index_row`, sorts by slug, and writes
  `$DEST/README.md`. No `readme_head`/`readme_tail` reference remains anywhere in the driver
  (grep: 0); the prior manifest `scratch/ubuildall1/gated-read-batching.toml.bak:54-55` did carry
  them. Drop reproduced.
- Clean step: baseline had `rm -rf "$DEST"` (baseline line 168); new driver has `rm -rf "$PKG"`
  (`:356`). Change reproduced.
- Two-package accumulation, built in the order gated-read-batching then encoder-crossover-190 into
  one scratch DEST. Final `README.md` rows, exact order:
  1. `| [encoder-crossover-190](packages/encoder-crossover-190/) | Encoder-crossover-190 data + verification package (same payload, paper #3 path) |`
  2. `| [exp12-encoder-crossover](packages/exp12-encoder-crossover/) | Encoder-crossover-190 data + verification package |`
  Order is slug order, not build order (`encoder-…` < `gated-…`). The first package's row is
  byte-identical in the final README (`True`), its 29-file tree is byte-identical (`diff -rq` clean),
  and the build reported `README.md index: 2 package row(s)`. Reproduced.

## 3. Evidence commands — REPRODUCED

`PYTHONPATH=src python3 -m pytest tests/test_package_build.py tests/test_build_wiring.py -q`
→ `30 passed in 1.58s`, exit 0. The four tests new to this change (identified from
`tests/test_package_build.py`) are:
`test_the_driver_checks_the_ship_list_against_the_pinned_tree` (:298),
`test_ship_list_check_fails_closed_on_a_perturbed_manifest_copy` (:339),
`test_ship_list_check_passes_green_on_an_unperturbed_manifest_copy` (:356),
`test_root_readme_index_accumulates_two_packages` (:366).
They are not brittle in the ways that matter: the red test uses a **non-default slug** (`perturbed-pkg`),
so it is not confounded by the default-only tripwire; the README test asserts the second row index is
strictly less than the first (deterministic slug order), not a fixed string. The **"26 before"**
pre-change count could not be verified in this session (no git history for the driver; nothing
recorded it), so only the +4 and the 30-total are measured.

## 4. Guards — PRESENT and fail-closed

- Licence sha256 guard: `:647-655`. Default-slug manifest disagreement → exit 2; template drift
  (`sha256sum "$DEST/LICENSE"` vs expected) → exit 1. Exercised live in every green run.
- Fail-closed exclusion gate: `gate.sh` (heredoc `:818-995`) exits 2 on an unreadable/empty
  vocabulary file and 1 on out-of-vocabulary tokens; the driver captures `GATE_RC` and ends with
  `exit "$GATE_RC"` (`:1111-1123`). Observed live: `GATE RESULT: FAIL …`, exit 1 propagated.
- Never-ship absence checks: `:553-561`, exit 1 on any present name; green log shows
  `never-ship list enforced: 15 names checked absent`.
- No package digest pinned: only the licence hash appears in the driver (hex grep; the sole
  64-hex literal is the licence sha, `:647`), and `tests/test_package_build.py:178`
  (`test_no_package_digest_is_pinned_anywhere`) passes.
- `PROMOTED_SAN_SRC` pin line untouched: new `:302` is byte-identical to baseline
  `scratch/ubuildall1/orig/UBUILD1.build.sh:134`:
  `PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"`.

## 5. Red→green control — NON-VACUOUS

Same inputs, fix present vs fix reverted (the 1523-byte `SHIPLIST_TREE_CHECK_PY` block deleted from a
copy of the driver; the rest untouched):

| control | input | fixed driver | reverted driver |
|---|---|---|---|
| A | pinned tree has extra `results/STALE-ENTRY.json`, manifest lists 29 | exit 2, `on disk but not listed: ['results/STALE-ENTRY.json']`, 0 files under DEST | exit 1, `DROP results/STALE-ENTRY.json`, `staged 30 file(s): 29 kept, 1 dropped`, build proceeds to the gate (109 files under DEST) |
| B | non-default manifest lists `results/STALE-ENTRY.json`; file absent | exit 2, mismatch, 0 files under DEST | exit 1, `staging`, `staged 29 file(s): 29 kept, 0 dropped`, then `FATAL: ship-list names a file the package does not have: results/STALE-ENTRY.json` (29 files staged) |

Non-vacuous: reverting changes both the exit code and the staging outcome. Control A additionally
shows the fix's distinctive value — without it an on-disk-but-unlisted file is silently dropped
rather than detected; control B shows the pre-existing missing-file check still covers the other
direction, but only *after* staging and with a different error.

## 6. Check-the-check: blind spots (reported, not fixed)

- **Strict equality conflates "the pinned tree" with "the ship list".** A packed tree that
  legitimately contains non-shipped files cannot be expressed: the check would FATAL on
  `on disk but not listed` for files the manifest deliberately excludes. Both current manifests point
  `promoted_san_src` at `scratch/uneutral10/package`, which is already exactly the 29 shipped files,
  so equality holds today. But the manifests' own `never_ship` lists (e.g. `EXCLUDED.md`,
  `INTEGRITY.md`, `REDACT3_REPORT.md`, the `code/verify/*` process outputs) describe exactly such
  legitimate drops; pointing any package at `repro/encoder-crossover-190-SANITISED` (which contains
  them) would make the build unable to ship its declared subset. Demonstrated with the 30-file tree
  copy (red-tree above). This is a real limitation of the check, not an error in the claim.
- `.git` exclusion (`:391`) prunes any **directory** named `.git` at any depth; files named `.git`
  would still be listed. The promoted tree contains none, and a nested `.git` copied by `cp -r` would
  be removed by the prune step anyway, so this is a signal gap, not a ship leak.
- `os.path.isfile` follows symlinks while the later prune uses `find -type f` (which does not), so a
  symlink-to-file would count as "present" for the check but not as a staged file. No symlinks in the
  current tree; theoretical.
- Empty directories are ignored by the check; they are deleted later by
  `find "$PKG" -mindepth 1 -type d -empty -delete`. Consistent.

## 7. Non-claims observations

- `orchestration/packages/{gated-read-batching,encoder-crossover-190}/readme-head.md` and
  `readme-tail.md` remain on disk though nothing reads them (dead fragments from the pre-index
  schema). Harmless, but stale.
- A setup artifact only: an early reverted-driver run of mine (`revB`, default slug) failed at the
  manifest loader for a missing vocabulary fragment in my own scratch copy, not because of the driver;
  it is not evidence about any claim.

## Separated summary

- **Measured:** red/green/two-package builds, exit codes, literal log lines, staged file counts,
  pytest 30 passed, sha256s, baseline line comparison, reverted-driver controls, moved-block placement
  experiment.
- **Inferred:** the placement reason is real because `tests/test_build_wiring.py:200` requires the
  clean step's log line under an empty fake tree (empirically demonstrated, not merely read).
- **Could not determine:** the pre-change test count of 26 (no baseline count recorded);
  whether the driver beyond the pin line is byte-identical to any prior revision (no git history for
  it; only the pin line and the two changed blocks were compared).
