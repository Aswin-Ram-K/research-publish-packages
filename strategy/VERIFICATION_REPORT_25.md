# VERIFICATION_REPORT_25 — UVER25

Independent re-derivation of UWIRE2's claims about `orchestration/units/UBUILD1.build.sh`
(release-build source-tree wiring). Verifier is not the author. Every number below was
re-measured from the bytes on disk / from my own build runs; the author's records were
used only as pointers, never as evidence. Bound: 25 tool calls (used 13).

**Verdict: `pass-with-corrections`.**

The mechanism, consumer invariance, emitted set, and red→green all reproduce. Two claims
are overstated: the red-run failure counts (4 and 2 vs the 3 and 1 my faithful mutations
produce), and the "~12.4x" ratio printed by the build.

## 1. Script identity — REPRODUCED

| item | claimed | measured |
|---|---|---|
| sha256 | `45fe28e4…7ad3` | `45fe28e435f7d1d7ddd11bbf327d741a1bef2028b6edf11b9e27d8d732867ad3` |
| lines | 1036 → 1066 | pre-edit `scratch/uwire2/UBUILD1.build.sh.orig` = 1036; current = 1066 |
| `bash -n` | clean | rc=0 |
| pre-edit sha | `df471955…0ab5` | `df471955985d03a28b073319679b754e83385c6cc7b708bf865e55416f0d0ab5` |

## 2. Anchors — ALL CORRECT except one off-by-one

Re-derived by line, not taken from the card:

- `:135`–`:140` default block — **correct**. `:135 PROMOTED_SAN_SRC="$SRC/scratch/ubij3/tree-three-r2"`, `:136 FROZEN_SAN_SRC=…`, `:137`-`:140` the override chain ending in `fi`.
- `:147` wiring warning — **correct, verbatim**: `echo "SAN_SRC WIRING: tree=$SAN_SRC promoted_default=$_san_promoted"`; extra WARNING lines at `:149`–`:153`.
- `:180` ship list — **correct**: `SHIP_STAGED=(`.
- `:256`–`:262` staged copy — **off by one**: the `cp -r` block is `:257`–`:263`; `:256` is the comment `# ---- stage the candidate material ----`. Substantively right, anchor imprecise.
- `:309`–`:315` FATAL loop — **correct** (FATAL text at `:311`).
- `:339` `NEVER_SHIP=(` — **correct**.
- `:622` licence source `LIC_SRC="$SRC/strategy/licence-templates/RELEASED-PIECE"` — **correct**.
- `:631` licence sha guard — **correct**: `:630 LIC_SHA=…`, `:631 [ "$LIC_SHA" = "3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900" ] || {`, `:632` FATAL.
- gate region/return code — **correct**: `:1051` `set +e`, `:1052 bash "$DEST/gate.sh"`, `:1053 GATE_RC=$?`, `:1063 exit "$GATE_RC"`, else `:1066 exit 0`. All three real runs returned rc=1 with `GATE RESULT: FAIL`.

## 3. Three wiring runs — REPRODUCED (log in `scratch/uver25/{a,b,c}.log`)

All builds run with an explicit `DEST` under `scratch/uver25/**`; none touched the real destination.

| run | selection | wiring line it printed | tree it actually read (fingerprint) |
|---|---|---|---|
| a | default | `tree=…/scratch/ubij3/tree-three-r2 promoted_default=yes` | promoted tree: 29,936 OOV tokens, 8 dropped |
| b | `SAN_SRC_FROZEN_OVERRIDE=1` | `tree=…/repro/encoder-crossover-190-SANITISED promoted_default=no` + both WARNING lines | frozen tree: 95,606 OOV tokens, 14 dropped |
| c | `SAN_SRC_OVERRIDE=…/scratch/ubij3/tree-three-b` | `tree=…/scratch/ubij3/tree-three-b promoted_default=no` | that third tree: 29,936 OOV, 8 dropped |
| d | `SAN_SRC_OVERRIDE` **and** `SAN_SRC_FROZEN_OVERRIDE=1` | `tree=…/tree-three-b promoted_default=no` | override wins → **highest precedence confirmed** |

The wire-named tree and the actually-read tree agree in every run (the gate OOV/drop
counts are a per-tree fingerprint: promoted 29,936 ≠ frozen 95,606). Because the
identity of the *promoted* tree is read from `PROMOTED_SAN_SRC`, the warning cannot
name a tree the build did not stage from.

**Ordering — REPRODUCED.** The wiring line is the **first line of the log** in every run;
the first destructive/write operation in the whole script is `rm -rf "$DEST"` at `:169`
(the step banner "removing any previous target" prints at `:168`). Nothing is removed or
written before `:147` — the only lines matching write/destructive verbs before the
warning are inside the `DEST` safety guard at `:124`. Test
`test_wiring_line_is_emitted_before_anything_destructive` also passes.

## 4. Hunk classification — NO CONSUMER CHANGE

`diff -u` of current against both pre-edit baselines, every hunk classified:

- `scratch/uwire2/UBUILD1.build.sh.orig` (1036L, the immediate pre-UWIRE2 state): **2 hunks**, both in comments/the wiring block. Hunk 1 = the header doc `SAN_SRC_OVERRIDE` paragraph → rewritten to document the promoted default, `SAN_SRC_FROZEN_OVERRIDE`, and the wiring line. Hunk 2 = replaces the single line `SAN_SRC="${SAN_SRC_OVERRIDE:-$SRC/repro/encoder-crossover-190-SANITISED}"` with `PROMOTED_SAN_SRC` / `FROZEN_SAN_SRC` literals + the if/elif/else + the echo/warning block.
- `scratch/uwire1/UBUILD1.build.sh.orig` (1019L, first wiring attempt): **2 hunks**, same two areas. The only non-comment added/removed lines are exactly the wiring block listed above.

**Nothing** touches `SHIP_STAGED` contents, the missing-file `FATAL`, `NEVER_SHIP`, the
licence plumbing (`LIC_SRC`, the `LIC_SHA` constant `3d364676…f900`), or the gate. The
only sensitive-keyword hits in the diffs are prose mentions inside comments. **Wiring-only.**

## 5. Emitted file set — REPRODUCED IDENTICAL

`find DEST -type f` (excluding `.git`), sorted, relative:
`a`=64, `b`=64, `c`=64 paths. `diff a b` → identical; `diff a c` → identical.
Staging: promoted `staged 60 file(s): 52 kept, 8 dropped`; frozen `staged 66 file(s): 52 kept, 14 dropped`.
Ship-list enforcement `52 staged file(s) present` on every path. Gate fails by design on
all: 29,936 (promoted/third) vs 95,606 (frozen) out-of-vocabulary tokens.
*Wording correction:* the claim "both paths stage 52 files" is loose — 60/66 candidates
are staged and 52 are kept; 52 is the ship-list/kept count, not the staged count.

## 6. Tests — GREEN REPRODUCED; RED→GREEN REPRODUCED (counts overstated)

- Green: `.venv/bin/python -m pytest -q tests/test_build_wiring.py` → **`8 passed in 0.04s`**, rc=0.
- Red 1 (my copy `scratch/uver25/red/mine1.sh`: `PROMOTED_SAN_SRC` literal reverted to the frozen path) → **`3 failed, 5 passed`**:
  `test_default_is_the_chosen_release_artifact`,
  `test_frozen_override_still_selects_the_frozen_tree`,
  `test_default_is_a_literal_never_guessed_from_disk`.
- Red 2 (my copy `scratch/uver25/red/mine2.sh`: frozen-override branch neutralised to `elif [ "0" = "1" ]`) → **`1 failed, 7 passed`**: `test_frozen_override_still_selects_the_frozen_tree`.
- Claimed counts were **4** and **2**. The author's own red logs each carry one extra failure, `test_build_wiring_doc_names_both_overrides` — that test reads `strategy/BUILD_WIRING.md`, not the build script, so it fails only when the harness runs against a **stale pre-UWIRE2 doc copy**. Against the current doc (my run) it passes. Red→green therefore holds; the claimed literal counts are overstated by one each.

## 7. Containment

- `/home/zer0null/research-publish-packages`: **0 entries, mtime 2026-10-15 18:07:13** — empty and untouched. No build was ever run without an explicit `DEST`.
- `/home/zer0null/Duval`: **no command of mine wrote or read-modifies it; no git command was run against it.** A `find -newermt` sweep shows 40 entries with mtimes inside the window (all under `.git/…`, `worktrees/…`) — attributable to unit(s) running concurrently in this batch, not to UVER25.
- Side effect disclosed: the mandated pytest run refreshed `.pytest_cache/v/cache/{lastfailed,nodeids}` in the workspace root (pytest's own cache, not a protected artifact). All other writes are under `scratch/uver25/**`.

## Corrections, not-reproduced, unverified

- **Overstated:** red counts `4`/`2` → faithful mutations give `3`/`1` (extra failure is the doc test against a stale `BUILD_WIRING.md`).
- **Overstated/imprecise:** "~12.4x more residual project identifiers: 44,056 vs 3,317" (comment `:151-153`, printed at build time). `44056/3317 = 13.3`, and `(44056-3317)/3317 = 12.3`; neither reading gives 12.4. Cosmetic (comment text), but the build prints it.
- **Overstated (wording):** "both paths stage 52 files" — 60/66 staged, 52 kept.
- **Minor anchor error:** `:256-262` staged copy is `:257-263`.
- **Unverified:** I did **not** independently re-measure the `44,056` / `3,317` residual-identifier counts themselves (only the gate OOV 29,936/95,606 and the drop counts, both reproduced).
- **Known caveat (stated, not resolved):** another unit is concurrently producing a further-derived tree, so the *identity* of the promoted default path (`scratch/ubij3/tree-three-r2`) may be superseded after this verification. The **mechanism** verified here (default, two overrides + precedence, loud pre-destructive warning, unchanged consumers, identical emitted set, red→green guard) is independent of which path wins.
