# VERIFICATION_REPORT_30 — UVER30 (independent verifier) vs UGATE3

Author != verifier. Every number below was re-derived with my own commands into
`scratch/uver30/**`. Verdict words: contradicted | overstated | not_reproduced | unverified.

## Headline
**partial.** Claims 2, 4, 5, 6, 7 reproduce. **Claim 1 is contradicted** (the build
script on disk did NOT produce UGATE3's artifact) and **claim 3 is not_reproduced
from the current script** (I get **1,398**, not 1,410).

## C1 — "build heredoc already scoped (UGATE2); UBUILD1.build.sh NOT modified" — CONTRADICTED
- Current digest agrees: `sha256sum orchestration/units/UBUILD1.build.sh` =
  `bbf5a52cb1983a0a0f3b6adf8aeaa1ab87e0dc3eabc97c21563e5e6b0512c372` (matches the
  truncated `bbf5a52cb198…`). `:134` is `PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"`
  — **intact, confirmed**.
- But the "not modified" half is **contradicted**:
  - mtime `orchestration/units/UBUILD1.build.sh` = **2026-10-16 01:15:52**, which is
    *after* `scratch/ugate3/build1.log` (01:14:04) and *before* `UGATE3.json`
    (01:16:18). The file was written after the build that it is claimed to have produced.
  - The `gate.sh` heredoc is quote-delimited and deterministic. Current script →
    `gate.sh` sha256 `cccacbe903332c72479ca4aabc9533107909c7efb985ef1f033215f051594992`;
    UGATE3's artifact → `7df3ed72d20fb7d0e5bc5bdd59bd077a7ff33f3077f2d770f58537bee069b163`.
    Two rejects from one deterministic heredoc is impossible: the on-disk script is
    **not** what produced `scratch/ugate3/dest`.
  - The current heredoc does **not** carry the "UGATE2: SCOPED revision" header label,
    nor `FAIL_LIMIT = 10 ** 9` / `UNCAPPED` / `DATA_EXT`, that UGATE3's gate.sh carries
    (`grep` returns ABSENT). Commit sha of the built tree also differs
    (mine `b1ff2b7` vs theirs `2b0f30a`), consistent with a different authored `gate.sh`.
- Named location: `orchestration/units/UGATE3.md:40` ("`UBUILD1.build.sh` NOT modified")
  vs the file mtime and the output digests above.

## C2 — staged/emitted/vocab/anchor figures — VERIFIED (my own build)
`DEST="$PWD/scratch/uver30/dest/research-publish-packages" bash orchestration/units/UBUILD1.build.sh`
(rc 1) logged: `staged 29 file(s): 29 kept, 0 dropped`; `never-ship list enforced: 15
names checked absent`; `vocabulary/english.txt: 74959 words`; `vocabulary/data.txt:
501 declared data-file key(s) from 32 parsed document(s)`; `anchor 907fa39 present in
4 file(s)`; `repo total: 39 files`. Independent `find … -path '*/.git' -prune -o -type f`
= **39** files (same as UGATE3's tree). Never-ship names absent (`uvbuild`,
`pyproject.toml`, `.pypirc` = 0 each).

## C3 — "gate count fell 1,689 → 1,410, all listed, 0 under vocabulary/" — NOT_REPRODUCED
- My rerun of the **current** script: `flagged tokens: 1398`, `offender lines printed:
  1398` (means "1,398 *genuine* residual tokens" — exactly the figure UGATE2.md:64 records),
  `GATE RESULT: FAIL -- 1398`. Line 52 of my log says "the list is complete"; UGATE3's says
  "the listing is uncapped". Whole-log diff = 29 lines, and the delta is purely the 12
  self-referencing tokens that exist only in UGATE3's `gate.sh` (`gate.sh:4 UGATE2`,
  `gate.sh:4 UBUILD1`, `:17 enum/label`, `:22 UNCAPPED`, `:53 DATA_EXT`, `:102 fam`,
  `:102 abr`, `:104 A-Za-z`, `:105 NKFS`, `:138/:145 uncapped`, `:153 DATA_EXT`). 1398+12 = 1410.
- 1,410 **is** reproducible from UGATE3's frozen artifact: re-running
  `scratch/ugate3/dest/research-publish-packages/gate.sh` myself gives
  `flagged tokens: 1410`, `offender lines listed: 1410`, and **0** offenders matching
  `^vocabulary/`. So "all listed / uncapped / 0 under vocabulary/" is verified **for that
  artifact**, not for the shipped script.
- The "old = 1,689" leg is **unverified and inconsistent**: `strategy/GATE_VOCABULARY_ANALYSIS.md:376`
  states "the **old shipped gate measures 1,740** (the card's 1,689 was an earlier revision of …)",
  and `orchestration/units/UGATE2.md:53` records old = 1,740 (capped at 400). No pre-patch
  artifact was available to re-derive 1,689. The 117-phantom mechanism is corroborated: I read
  the broken guard at `scratch/ugate1/gate_scoped.sh:121`
  (`if rel.split(os.sep)[0] == VOCAB_DIR or os.path.dirname(rel) == VOCAB_DIR:` with an
  absolute `VOCAB_DIR` vs a relative `rel`), and `strategy/GATE_VOCABULARY_ANALYSIS.md:135`
  records the 117; I did not independently re-count 117.

## C4 — offender classes — VERIFIED
Re-derived from the gate's own `.tsv` (1,410 data rows): released-schema-key 80 occ / 38
distinct; third-party-incidental 1,054 / 296; genuinely-mechanism 276 / 11; encoding
artefacts 0. Sum = 1,410 occ; **global distinct = 321** (38+296+11 = 345 because 24 tokens
are class-overlapping) — so the handoff's "1410/321" is correct. Spot-opened:
`results/eval-setfit-mpnet.json:540` = `"code-inspector (detached, fs.read)",`;
`results/eval-modernbert-base.json:864` = `"F54": "relist every ancestor",`.

## C5 — the 11 mechanism tokens are inside the released stimulus — VERIFIED
My own walk of the emitted tree (not the claim): all 11 occur **only** under
`packages/exp12-encoder-crossover/{fixture,results,second-labeller}` (12 files max).
Occurrence counts re-derived from the gate output match the handoff exactly and sum to 276
(`fs.read` 116, `fs.write` 104, `fs.write.` 8, `expiresAtEpoch` 12, `reasonerCalls` 8,
`MutationProposal` 8, `role.canRequestEscalation` 5, `ToolCallIR` 5, `ToolCallIR.` 4,
`canRequestEscalation` 4, `policyHash` 2). Opened in place: `fixture/fixture-190.json:531`
("the policyHash provenance"), `fixture/reflex-decisions.ts:791` (ToolCallIR inside a
stimulus question), `second-labeller/cases.json:479` (expiresAtEpoch inside a question).
Scope note: confinement was checked within the emitted package, not the whole workspace.

## C6 — RED→GREEN — VERIFIED (on my own copy)
`cp -a` of the artifact; append `grantPolicy` to `results/REPORT.md` →
`results/REPORT.md:305: grantPolicy  [identifier-shaped, not a declared public identifier]`,
`flagged tokens: 1411`. Remove it → `flagged tokens: 1410`. `diff -r` redtest vs artifact:
only `REPORT.md:304d303 <` — a blank line **my own** `sed` restore left, not theirs.

## C7 — FAIL-CLOSED — VERIFIED
`: > vocabulary/english.txt` on my own copy → gate **rc 2** with
`FATAL: vocabulary file has no declared terms: …/scratch/uver30/failclosed/vocabulary/english.txt`.
Build propagation read at `orchestration/units/UBUILD1.build.sh:951-967`: `exit "$GATE_RC"`
on non-zero, so it never reaches `BUILD COMPLETE — the exclusion gate PASSED`; my full build
run returned rc 1 on a failing gate.

## Method-not-vacuous control — PASSES
Injected **both** `policyHash` and `banana` into `README.md` of a copy: gate flagged
`README.md:33: policyHash  [identifier-shaped…]` and count rose 1410 → 1411, while the
ordinary English word `banana` (line 34) was **not** flagged. The discriminator fires on a
mechanism token and stays silent on a normal word.

## Files relied on
`orchestration/units/UBUILD1.build.sh` (:134, :951-967), `scratch/ugate3/build1.log`,
`scratch/ugate3/dest/…/gate.sh`, `scratch/ugate3/offenders_classified.tsv`,
`strategy/GATE_VOCABULARY_ANALYSIS.md` (:135, :376), `orchestration/units/UGATE2.md` (:53,:64),
`orchestration/units/UGATE3.md` (:40,:43), `scratch/ugate1/gate_scoped.sh` (:121).
