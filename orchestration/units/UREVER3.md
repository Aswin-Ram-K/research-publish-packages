# UREVER3 — feasibility of candidate paper N3

**Unit role:** FEASIBILITY. Establish whether paper N3 (*independent-verification protocol + taxonomy of
defect classes it catches*) can be written from what is already on disk. Not drafting.

**Hard bound:** 20 tool calls. Increment-and-append so a death is still readable from disk.

## Declared write paths
- `strategy/PAPER_N3_FEASIBILITY.md`
- `orchestration/units/UREVER3.md`
- `orchestration/handoffs/UREVER3.json`
- `scratch/urever3/**`

## Claim under test
The workspace ran a disciplined independent-verification protocol: every unit's work re-checked by a unit
that did not write it; verdicts recorded; corrections dated and appended not overwritten. The defects
caught fall into recurring, nameable classes.

## Method
Measure the frozen records directly (unit cards, handoffs, VERDICTS.md, strategy/ reports). Do not trust
prose summaries. Every count carries the command that produced it. Separate MEASURED / INFERRED /
COULD NOT DETERMINE.

## Findings log (appended as measured)

### F1 — corpus counts (MEASURED)
Command:
```
cd "/home/zer0null/reserach extarctor" && ls orchestration/units/*.md | wc -l && ls orchestration/handoffs/*.json | wc -l
```
**RESULT: 415 unit cards (1,472,601 B) / 427 handoffs (3,317,592 B).**

### F2 — corpus (MEASURED)
- 415 `orchestration/units/*.md` = 1,472,601 B; +1 non-md `UBUILD1.build.sh`.
- 427 `orchestration/handoffs/*.json` = 3,317,592 B; **427/427 parse as JSON, 0 unparseable**.
- 60 `V*` handoffs; **97 verdict-shaped** (`overall` or `checks`), 330 unit-shaped → 37 verifiers are NOT `V*`.
- `orchestration/VERDICTS.md` 349,291 B / 3,309 lines / 53 `## V<n>` sections.
- 36 `strategy/VERIFICATION_REPORT*.md` = 493,439 B.
- Date range: handoffs 2026-10-08 05:52:04 → 2026-10-16 14:52:48; cards → 2026-10-16 17:07:37. 9 days.
- Release subset for all counts: **880 files / 5,632,923 B (~5.4 MiB)**; verdict counts alone need only the
  427 handoffs = 3,317,592 B.

### F3 — verdict fields (MEASURED) ⇒ the recomputable taxonomy
`contradicted` 49 entries / 23 files · `overstated` 178 / 73 · `not_reproduced` 169 / 62 · `unverified` 177 / 73
= **573 entries over 97 handoffs**. `overall`: 43 pass (33 `PASS` + 10 `pass`), 36 partial (18+18), 12
`pass-with-corrections`, 4 `FAIL` — **two spellings coexist**, a normalisation hazard.

### F4 — protocol NOT followed (MEASURED) — the counterexamples the paper must carry
1. Workspace git history = **5 commits, all 2026-10-08**; only 3 touch `VERDICTS.md`/handoffs. Everything
   2026-10-09→16 is **uncommitted** ⇒ append-vs-overwrite is **unverifiable for ~90% of the corpus**.
2. `AGENTS.md`'s own census (136 handoffs / 194 strings / 62 plain `status` / 0 mutating) does **not
   reproduce**: deep extraction gives **134 / 215 / 86 plain / 17 lock-free / 0 mutating**. 0-mutating holds;
   the 62 figure is an undercount.
3. `AGENTS.md`'s "43 `V*` handoffs (U8.18)" is now 60; the paper must date-stamp it.
4. One `.build.sh` sits under `orchestration/units/` (untracked) ⇒ "units are `.md`" is false as stated.

### F5 — defect classes re-derived (INFERRED from quoted fields, not from a recorded field)
- MC-1 stale live-path value — **≥3 instances** (real class). Anchor `UTRACE1.json` contradicted[0]/overstated[0]/not_reproduced[1].
- MC-2 closing message is a claim — **2 strong** (`UNEUTRAL4.json`: author 8,213/99-of-184 vs re-run 5,384/95-of-184, `[U3✗U4]`; `U6.13.json` census.note 12 vs 14).
- MC-3 line-count-neutral edit ⇒ citation/digest rot — **1 primary** (`UFIX15.json` `line_count_neutrality` + `build_script_sha256_after`, BS 1019 lines, sha changed). **Anecdote.**
- MC-4 superseded-build artifact — 2 (`30b75581…` from dead `rt/bij`; `UVER11.json` 218 vs 156).
- MC-5 build consumed the wrong input tree — `strategy/BUILD_INPUT_PIN.md` (59/46/13 describes the sanitised tree; build reads the 45-file `tree-three-r2`); `BUILD_PIN_CHANGE.md` promoted `urecut1`→`uneutral10`.
- MC-6 unreproducible frozen figure — 1 (the `AGENTS.md` census).

### F6 — VERDICT: (b) draftable after one named measurement, with scope reduction
Section 2 + the verdict-field table are draftable now from a 3.3 MiB releasable subset. A **taxonomy of
recurring mechanism classes is NOT supported** — only MC-1 (≥3) and MC-2 (2) clear the "not an anecdote" bar;
MC-3/4/5/6 have 1–2 instances each. Named measurement: a blind relabelling pass over the 97 verdict-shaped
handoffs assigning each of the 573 entries a mechanism label against a published rubric, then recount.
Strongest spine: **`contradicted`** (49 instances / 23 handoffs), anchored on `UNEUTRAL4.json` and `UTRACE1.json`.

### F7 — the honest sentence
Almost everything a reader would care about is **on trust**: the counts recompute, but no verdict's
*correctness*, no mechanism label, and not the append-only claim can be checked from any releasable subset.

Full report: [`strategy/PAPER_N3_FEASIBILITY.md`](../../strategy/PAPER_N3_FEASIBILITY.md).
