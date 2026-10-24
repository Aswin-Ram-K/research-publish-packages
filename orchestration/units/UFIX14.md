# UFIX14 — update stale licence pins/text in UBUILD1.build.sh  (DONE)

PURPOSE: ULICENCE5 changed `strategy/licence-templates/RELEASED-PIECE/LICENSE` (151 lines /
5,851 B / sha256 3d364676…f900, was 150 / 5,662 / 25aa637b…cfe), leaving the build's pinned
digest stale so the build failed closed by design. Update the pins and the now-false placeholder
text only; keep the guard fail-closed.

WRITE PATHS: `orchestration/units/UBUILD1.build.sh`, `scratch/ufix14/**`, this card,
`orchestration/handoffs/UFIX14.json`. Nothing else touched.

EDITS (7 literal replacements; line count unchanged 1,019 → 1,019, so all citations stay valid):
1. :584 expected digest `25aa637b…cfe` → `3d364676…f900` (guard kept fail-closed).
2. :585 drift message shorthand `25aa637b…cfe` → `3d364676…f900`.
3. :586 comment byte count `bytes 1-5662` → `bytes 1-5851` (the comment named bytes, not a line
   range; the now-superseded 10–140 body anchor appears nowhere in the script).
4. :409-411 root-README placeholder instruction → resolved text (notice = "Required Notice:
   Copyright 2026 Aswin-Ram-K"; contact = repo issue tracker URL; no email invented).
5. :610 emitted `paper/LICENSE` `Required Notice: Copyright <YEAR> <COPYRIGHT HOLDER>` → `…2026 Aswin-Ram-K`.
6. :629-630 same file's attribution sentence → `…Copyright 2026\nAswin-Ram-K".` (2 lines kept).
7. :988 commit message placeholder clause → `…1.0.0, required notice: Copyright 2026 Aswin-Ram-K.`

VERIFICATION (scratch only, DEST=scratch/ufix14/research-publish-packages):
- green: guard passes; build completes and stops at the exclusion gate — exit 1,
  `flagged tokens: 95606`, `GATE RESULT: FAIL -- 95606 out-of-vocabulary token(s).`
- emitted `LICENSE`: 162 lines / 6,408 B / sha256 58ab7d1e… — exactly ULICENCE5's prediction.
- emitted `packages/exp12-encoder-crossover/paper/LICENSE`: 29 lines / 1,300 B / df2f4fc3….
- placeholder scan of the emitted tree (excluding .git): zero hits.
- red→green: scratch copies with the pin reverted to 25aa637b…cfe exit 1 on
  `FATAL: LICENSE template drift: sha256 is 3d364676…, expected 25aa637b…cfe` before the gate.

BOUND: used 13 of ≤15 tool calls. No blockers.
