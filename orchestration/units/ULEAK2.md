# Unit ULEAK2 — paper #2 deposit archive: leak sweep, licence fix, re-prove

**Bound**: 25 tool calls. **Used: 18.** **Status: partial** (remainder named below).
**Write paths used**: `papers/replay-record-not-decision/released/**`, `scratch/uleak2/**`,
`orchestration/units/ULEAK2.md`, `orchestration/handoffs/ULEAK2.json`.
No git command was run against any target; no target was read for this unit.

## JOB 1 — classification of the 28 reported sites (before any edit)

The 28 reported lines are **not 28 independent edits**. By class:
**10 unit-id-only** (MANIFEST 3,50,86 / README 10,39,81,96,97,117,118), **13 workspace-path-only**
(MANIFEST 23,32,41 / README 49,50,54,93,94,95,102,103,114,120), **3 unit-id + tool path**
(MANIFEST 5 / README 6,98), **1 path + absolute target path** (README 91), **1 unit-id + tool path +
internal state path** (MANIFEST 9) = 28.

| class | what the string IS | verdict |
|---|---|---|
| A unit ids `UPKG2B/UPKG2C` | internal orchestration bookkeeping; names no artefact a reader has | internal material — rewritten/removed |
| B workspace build/state paths | `scratch/…`, `tools/package/…`, `state/refresh-verify/…` — authoring layout | internal material — rewritten |
| B1 tool paths a reader **needs to run something** | **none.** Every tool named (`regen_manifest.py`, `census.py`, `neutralise.py`, `cut_ladder.py`, `reproduce-join.py`) is author-side and does **not** ship; the only runnable command in the package is `python3 verify/recompute-claims.py`, whose path ships and was **kept** | no reader command dropped; each non-shipping tool now says "author-side; not distributed" |
| C absolute path | `README:91 /home/zer0null/Duval/.worktrees/*/docs/research/` | **removed** |
| D target-repo name `duval` (my own grep; **not** in the verifier's 28) | `MANIFEST:68,77`, `README:91,92` | internal material — rewritten |
| E provenance references | the sources table + `source`/`source_sha256` fields | **kept as provenance**, rewritten to author-side descriptions; every digest preserved |
| F cross-paper refs | "paper #3" kept (the companion release must be named); `papers/encoder-crossover-190/` removed | path internal — removed |
| G deep project paths naming withheld material | `README:78 evals/fixtures/reflex-decisions.ts`, `README:82 docs/research/experiments/EXP#7-replay-divergence.md` | de-pathed to descriptions; size + sha256 kept |
| H **not** a leak (kept, with reason) | `harness/`, `data/`, `verify/`, model names, `Required Notice`, the GitHub issue-tracker URL (the sanctioned contact route), the DOI; and the 8 bare `MANUSCRIPT.md` citations in the shipped checker (document name, no directory — they anchor each check to the paper's own sections) | kept |

**Extra defect the verifier did not report (a number, not a leak):** `README.md:18` stated
**13,953 B** for `verify/recompute-claims.py`; the shipped file is **13,945 B**. Corrected (now 13,936
after de-pathing its one internal path).

## JOB 2 — what was fixed, and the licence decision

* `MANIFEST.json` — **not hand-edited**: the feeder is the package source manifest
  `scratch/upkg2c/package/MANIFEST.json` (proved: `regen_manifest.py` does `body = dict(old)` and never
  writes `purpose`/`generated_by`/`amended_by`/`source*`). Feeder fields rewritten, then the manifest
  regenerated with `python3 tools/package/regen_manifest.py --no-note --generated-utc 2026-10-19T06:22:36Z`.
* `README.md` — 15 substitutions: unit ids, workspace paths, absolute path and target name replaced by
  reader-facing wording; every number and digest preserved; no command removed.
* `README_DEPOSIT.md`, `CITATION.cff` — one internal path each (`papers/encoder-crossover-190/`).
* `verify/recompute-claims.py` — one internal path in the docstring (line 4). Code untouched.
* **LICENCE DECISION: restore the template.** The `LICENSE:152-163` Scope section is inherited from
  paper #3's tree and governs `harness/`, `results/`, `fixture/`, `second-labeller/` — **none exist in
  this package**, which ships `data/` and `verify/`. Rewriting it would have left a bespoke licence text
  needing its own review; the reviewed, shared artefact is
  `strategy/licence-templates/RELEASED-PIECE/LICENSE`. Restoring it (a) removes the false statement,
  (b) makes `LICENSE` byte-identical to the template, (c) leaves what is withheld already stated in
  `README.md` + `README_DEPOSIT.md`. The PolyForm body is untouched: **4,563 B, offset 115, sha256
  `ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`** in both template and old file.
  New `LICENSE` = 5,851 B, sha256 `3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900`.
* **Disagreement with the verifier:** the `CONTRIBUTING.md` divergence is **not** a defect. The template
  literally opens `> **DRAFT — template for the author to place.** See ../PLACEMENT.md`, and
  `strategy/licence-templates/PLACEMENT.md` says that draft goes to each released piece as
  `CONTRIBUTING.md`; the packaged file *is* that placed, filled version. Byte-identity to a DRAFT
  placeholder would be the wrong test. Left unchanged, reported here.

## JOB 3 — my own greps (reported whether or not fixed)

Patterns run over payload + archive + extras: unit ids, `scratch/`, `tools/package`, `/home/`,
`orchestration/`, `strategy/`, `duval|Duval`, `uneutral`, `upkg`, `engine-a`, `papers/`,
`reserach|resextract`, `.worktrees`, `reflex-decisions|docs/research|evals/fixtures`, `MANUSCRIPT`.
* **0** hits for `orchestration/`, `strategy/`, `/home/`, `duval|Duval`, `reserach|resextract` in the old
  tree except the 3 `duval` + 1 `/home/` lines the verifier had already listed (plus `MANIFEST:68,77`,
  which the verifier had **not**).
* **Not in the verifier's 28, now fixed**: `MANIFEST:68,77` (target name + state path),
  `CITATION.cff:36`, `README_DEPOSIT.md:103`, `README:7,38,78,82`, `verify/recompute-claims.py:4`.
* **Not fixed, reported**: `papers/replay-record-not-decision/submission/BUILD_NOTES.md` and
  `METADATA.md` carry the same class (`scratch/upayload2`, `scratch/ufixtex1`, `scratch/utex1/bin/tectonic`,
  `tools/package/md2tex.py`, `.../engine-a/…`). They are submission-side authoring notes, **not** the
  deposit archive; they are outside this card's defect and outside a safe edit here.
* **Frozen data untouched**: both `data/*.jsonl` byte-identical, shas `c5ec44a7…` / `6af0e0d8…` unchanged.
* Also unexamined: `papers/replay-record-not-decision/submission/replay-record-not-decision.tar.gz` and
  `preprints/*.zip` — **not verified** (would need an unzip pass).

## JOB 4 — rebuild and re-prove (all on the installed artifact)

| check | result |
|---|---|
| `check_manifest.py` payload (`scratch/uleak2/package`) | `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0` / `VERDICT PASS` / exit 0 |
| `check_manifest.py` clean extraction | same five zeros / `VERDICT PASS` / exit 0 |
| `check_manifest.py` installed tree | same five zeros / `VERDICT PASS` / exit 0 |
| `verify/recompute-claims.py` in extraction **and** installed tree | exit 0 / `CHECKS: 30/30 passed` / `VERDICT PASS` |
| leak greps, installed tree | **0** lines (was 40 distinct leaked lines by my union pattern) |
| build determinism | `cmp build1 build2` exit 0 |
| **DIGEST CHANGED** | 107,474 → **107,641 B**; sha256 `7703fe83…` → **`b5dbe854a97e261546289f773e3c0745f45f5cc9a2457b3b9b3a4a9de7168ce2`**; md5 `16e2b2bf…` → **`a279e399382792952205b0738f958e38`** |

## Remainder (why status = partial)

1. **Canonical source not updated.** `scratch/upkg2c/package/` is the tree the shipped archive used to be
   built from; it is **outside this unit's declared write paths**, so the patch lives in the private copy
   `scratch/uleak2/package/`. A future rebuild from the canonical path would reintroduce every leak.
2. Submission-side notes (JOB 3) still carry the class; the two archives under `submission/`/`preprints/`
   are unexamined.
