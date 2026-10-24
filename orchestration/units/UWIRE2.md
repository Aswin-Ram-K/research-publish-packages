# UWIRE2 — promote the chosen release artifact and guard the wiring

**Status:** `done` · **Bound:** 20 tool calls (18 used) · **Handoff:** `orchestration/handoffs/UWIRE2.json`

**Purpose.** UWIRE1 wired `SAN_SRC_OVERRIDE` but left the build's default on the **original, least-processed**
sanitised tree, so the release was one unset variable away from shipping the wrong bytes with no warning.
UWIRE2 promoted `scratch/ubij3/tree-three-r2` to the default, kept the frozen tree reachable through a named
environment override, added a loud non-interactive wiring line, added a regression test, and re-checked the
"frozen input" claim.

## Write paths

`orchestration/units/UBUILD1.build.sh` · `strategy/BUILD_WIRING.md` · `tests/test_build_wiring.py` ·
`scratch/uwire2/**` · `orchestration/units/UWIRE2.md` · `orchestration/handoffs/UWIRE2.json`

Pre-edit script preserved at `scratch/uwire2/UBUILD1.build.sh.orig`, sha256
`df471955985d03a28b073319679b754e83385c6cc7b708bf865e55416f0d0ab5` (identical to the live script at backup).
Live script after edit: sha256 `45fe28e435f7d1d7ddd11bbf327d741a1bef2028b6edf11b9e27d8d732867ad3`, 1,066 lines
(was 1,036); `bash -n` syntax OK.

## 1. The default — before / after (verbatim)

Before (`:125`):

```bash
SAN_SRC="${SAN_SRC_OVERRIDE:-$SRC/repro/encoder-crossover-190-SANITISED}"
```

After (`:135`–`:154`):

```bash
PROMOTED_SAN_SRC="$SRC/scratch/ubij3/tree-three-r2"
FROZEN_SAN_SRC="$SRC/repro/encoder-crossover-190-SANITISED"
if   [ -n "${SAN_SRC_OVERRIDE:-}" ]; then SAN_SRC="$SAN_SRC_OVERRIDE"
elif [ "${SAN_SRC_FROZEN_OVERRIDE:-0}" = "1" ]; then SAN_SRC="$FROZEN_SAN_SRC"
else SAN_SRC="$PROMOTED_SAN_SRC"
fi
if [ "$SAN_SRC" = "$PROMOTED_SAN_SRC" ]; then _san_promoted=yes; else _san_promoted=no; fi
echo "SAN_SRC WIRING: tree=$SAN_SRC promoted_default=$_san_promoted"
if [ "$_san_promoted" = no ]; then
  echo "SAN_SRC WIRING: WARNING - NOT the promoted release artifact; the promoted default is"
  echo "                $PROMOTED_SAN_SRC"
  if [ "$SAN_SRC" = "$FROZEN_SAN_SRC" ]; then
    echo "SAN_SRC WIRING: WARNING - this is the FROZEN original sanitised tree (the pre-promotion"
    echo "                input; ~12.4x more residual project identifiers: 44,056 vs 3,317)."
  fi
fi
```

**Override names (deliberate).** `SAN_SRC_OVERRIDE` keeps its existing name and meaning as the generic
any-tree override (highest precedence) so UWIRE1's documented invocation still works. `SAN_SRC_FROZEN_OVERRIDE=1`
is the new, named route to the previously-default frozen tree, so the pre-promotion input stays reproducible
and discoverable. Both are read from the environment only, never guessed from disk, and neither prompts.

**`SAN_SRC`'s meaning preserved for every consumer.** Consumers: resolution+wiring line `:135`–`:147`; the
staged `fixture/harness/verify → code/` and `preregistration/results/second-labeller → eval/` copy
`:256`–`:262`; `SHIP_STAGED=( … )` `:180`; fail-closed missing-file check `:309`–`:315`; `NEVER_SHIP` `:339`;
licence plumbing `LIC_SRC` `:622` and the licence sha guard `3d364676…f900` `:631` (guard text unchanged);
positive-vocabulary gate `:818`–`:943`, rc `:1052`–`:1053`. **Nothing but which tree is read changed** — the
dictated fail-closed behaviour, ship list, never-ship list, licence plumbing and gate are byte-identical.

## 2. The warning

Every build prints exactly one machine-greppable line first (`:147`):
`SAN_SRC WIRING: tree=<abs path> promoted_default=<yes|no>` — and, when not the promoted default, a
`WARNING` naming the promoted default (plus a FROZEN-specific WARNING). Non-interactive; exit code unchanged;
emitted before the first destructive step, so it appears even in a build that stops immediately.

## 3. Regression test — `tests/test_build_wiring.py` (8 tests)

Follows the workspace's pytest convention (`tests/`, `resextract` conftest, `.venv/bin/python -m pytest`).
Fails if the default is silently changed away from the chosen artifact, if `SAN_SRC_FROZEN_OVERRIDE=1` or
`SAN_SRC_OVERRIDE=<path>` stops being honoured, if the default stops being a literal (a disk guess), if the
wiring line stops being emitted first, or if `strategy/BUILD_WIRING.md` stops documenting it. `UWIRE2_BUILD_SCRIPT`
points it at a throwaway copy (that is how the reds were made).

**Green (final, real script + real doc):** `8 passed in 0.04s`
**Red 1 — `red1-frozen-default.sh`, `PROMOTED_SAN_SRC` reverted to the frozen literal:**
`4 failed, 4 passed`; wiring failures = `test_default_is_the_chosen_release_artifact`,
`test_frozen_override_still_selects_the_frozen_tree`, `test_default_is_a_literal_never_guessed_from_disk`
(the 4th, the doc guard, was independently red at that moment and is green in the final run).
**Red 2 — `red2-ignored-override.sh`, frozen branch forced false:** `2 failed, 6 passed`; wiring failure =
`test_frozen_override_still_selects_the_frozen_tree`.
**Red 0 — the real pre-UWIRE1 script (`scratch/uwire2/red/red0-prewire.sh`):** `6 failed, 2 passed`.

## 4. Re-run of both paths after the edit

| | promoted default (no overrides) | frozen (`SAN_SRC_FROZEN_OVERRIDE=1`) |
|---|---|---|
| wiring line | `tree=…/scratch/ubij3/tree-three-r2 promoted_default=yes` | `tree=…/repro/encoder-crossover-190-SANITISED promoted_default=no` + `WARNING` |
| staged | `staged 60 file(s): 52 kept, 8 dropped` | `staged 66 file(s): 52 kept, 14 dropped` |
| ship list | `52 staged file(s) present` | `52 staged file(s) present` |
| never-ship | `17 names checked absent` | `17 names checked absent` |
| gate verdict | `GATE RESULT: FAIL -- 29936 out-of-vocabulary token(s).` | `GATE RESULT: FAIL -- 95606 out-of-vocabulary token(s).` |
| exit code | 1 (the gate) | 1 (the gate) |
| emitted | **64 files** | **64 files** |

The emitted file set is **identical** (64 paths, `diff` clean). The promoted run reproduces UWIRE1's opt-in
numbers exactly (29,936 and 60→52/8), which is the proof that the promotion changed *which tree is read* and
nothing else.

## 5. The "frozen input" finding (next-hint 3)

`repro/encoder-crossover-190-SANITISED` is **not frozen**, and the card's 58-file figure is stale.

- **59 files = 46 staged** (`fixture/ harness/ verify/ preregistration/ results/ second-labeller/`) **+ 13
  non-staged**. `REDACT3_REPORT.md` (mtime **2026-10-15 21:04:58**) is top-level and **never staged**, so it
  cannot change a byte of the package.
- **Staged bytes re-hashed against `INTEGRITY.md`** (mtime 19:02:10): **38 of the 46 staged files have a
  recorded sha256 and all 38 MATCH; 0 mismatch.** The 8 `verify/*` files have **no** `INTEGRITY.md` row; the
  newest staged mtime is `verify/scrub-uscrub1.py` at **18:30:14**, before both `INTEGRITY.md` and the
  artifact's derivation (dir mtime 21:21, `MANIFEST.json` 21:39).
- **Identity of the input tree cannot be pinned retroactively:** `scratch/ubij3/tree-three-r2/MANIFEST.json`
  pins only `instrument_sha256` and `exp11_corpus_sha256` — **no digest of the tree it was derived from**.
  What the evidence *does* support: no staged byte can have changed since derivation. The tree as a whole,
  including its mutable top level, is **not frozen and must not be called frozen**.
- Recorded staged-subtree digest (sha256 of sorted `<sha256>  <path>` lines over the 46 staged files):
  `0b79908422a3f79785ee5ec4640498e302a913bfb3bd97007d86b4f6717a25a5`. Per-file digests of the 8 `verify/*`
  files are in the handoff. Nothing under `repro/` was written.

## 6. Containment

The real destination `/home/zer0null/research-publish-packages` was never used as `DEST` (every run built into
`scratch/uwire2/run-promoted|run-frozen/research-publish-packages`); `0 files newer than 2026-10-15 21:45`
under it. `repro/**` read-only. No git command was run against `/home/zer0null/Duval`.

## 7. Blocker and next hint

**Blocker:** none for this unit. **Next:** (1) the gate still FAILS on both paths — the release cannot pass
its own gate until the positive-vocabulary question is settled; that, not the wiring, is the publish blocker.
(2) If the frozen input must be genuinely reproducible, pin it (staged aggregate digest above) or point
`SAN_SRC_FROZEN_OVERRIDE` at an immutable copy. (3) Any future promotion must edit the `PROMOTED_SAN_SRC`
literal deliberately — the new test fails on a silent change and on a broken override.
