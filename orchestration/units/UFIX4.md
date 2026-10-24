# UFIX4 — apply UVER3's corrections to `second-labeller-190`

**Unit:** UFIX4 (repair unit; not the author of the artifacts, not the verifier).
**Work order:** `strategy/VERIFICATION_REPORT_3.md` (UVER3, verdict `pass-with-corrections`).
**Target repo:** `/home/zer0null/Duval` — **read-only; never written** (only `read`/`grep`/`wc`/JSON parse
against it).
**Hard bound:** 35 tool calls. **Used: 28.**

## Write paths (declared, nothing else touched)

`experiments/second-labeller-190/{RUN.json,EVIDENCE.md,metrics.json,OWED_CORRECTIONS.md}`,
`strategy/PUBLICATION_STRATEGY.md` (line 46 only), `orchestration/units/UFIX4.md`,
`orchestration/handoffs/UFIX4.json`.

Never touched: `PREREGISTRATION.md` (frozen; sha256 `42bffdb0…` unchanged), `ROBUSTNESS.md`, `RUN2.json`,
`labelsB2.json` (UEXP2's files — none existed in the directory during this unit), `journal/`, `jobs/`,
`papers/`, any file in `/home/zer0null/Duval`. No new file created in the experiment directory except the
one required record, `OWED_CORRECTIONS.md`.

## Corrections applied (each re-confirmed before editing)

1. **Referent error (UVER3 C1) — `RUN.json`, `EVIDENCE.md`.** Re-confirmed: `FINDINGS_REGISTER.md:47`
   (read raw) measures `answerInOptionSet` over **model-emitted answers** in EXP#11
   (4,090 decider + 3,590 imajev rows as recorded there), whereas UEXP's 0/190 is a property of the
   **fixture's authored `correct` indices**. Different referents → not corroboration.
   - `RUN.json`: key **`corroboration` → `related_measurement`** (no consumer of the old key exists — only
     `RUN.json` itself carried it; checked workspace-wide), `finding` restated as a related but distinct
     check that is *consistent*, added `referent` and `register_quote_note` (which also points at owed
     item 1). Marked `[corrected by UFIX4 per UVER3 C1]`.
   - `EVIDENCE.md:258`: "This **corroborates**…" → "This is a **related but distinct check**, not
     corroboration…", and the closing paragraphs now name the two referents and say the results are
     consistent, not corroborating. Marked `[corrected by UFIX4 per UVER3 C1]`. **The 0/190 finding itself
     is untouched and not softened.**
2. **Bare κ (UVER3 C2) — `metrics.json`.** κ `0.9013584840356494` is unchanged; a `limitation` string was
   added **adjacent to the value** in both places the pooled κ appears (`passes["labelsB.json"]` and
   `routeB_primary`), plus a top-level `limitation` and a `_correction` note. The limitation states: the
   second labeller is a **model, not an independent human annotator**; κ is **NOT inter-annotator
   agreement**, must **never** be cited as such, and does **not** discharge `PAPER_CANDIDATES.md` §F.3's
   call for a second independent labeller (corpus records one absent, UCORR1). Pooled-kappa weakness
   (51/74 singletons, `pe=0.0396`) travels with it.
   - Consequence handled honestly: editing `metrics.json` breaks the literal "reproduces byte-for-byte"
     claim, so `RUN.json`'s `reproducibility` value now says the **unmodified scripts still regenerate the
     pre-correction bytes**, and the added keys are the only delta. Marked `[corrected by UFIX4 per UVER3]`.
     This is disclosure of my own edit, not a softening of UVER3's reproduced result.
3. **Mis-counted `id:` match (UVER3 overstated #3) — `EVIDENCE.md`.** Re-measured myself:
   `grep '^[[:space:]]*id:'` on the fixture = **191** matches, and the **first by line order is line 63**
   (`  id: string;` inside `export interface DecisionCase`), the only non-case match. "The 191st match" →
   "the one `id:` match that is not a case id — the **first** by line order, at line 63". The same wrong
   wording existed in `RUN.json`'s `corpus_documentation_detail`; corrected there too and marked, so the
   two artifacts cannot disagree. The substance of the owed correction is unaffected.
4. **Owed document correction (UVER3 item 8e) — `strategy/PUBLICATION_STRATEGY.md:46`.** "(190 cases + 1
   container id)" → "(190 case ids + the `DecisionCase` interface field declaration `id: string;` at line
   63 — the one `id:` match that is not a case id, and the first by line order; there is no container id)".
   Marked `[corrected by UFIX4 per UVER3]`. **Line 46 only**; line 404 (`S28`) repeats the count without
   the wrong attribution and was left alone, as UVER3 noted.
5. **`OWED_CORRECTIONS.md` created** — the five corrections owed to the **read-only** corpus, each with
   exact path:line, current text, correct value, evidence/unit, and my own re-verification. Not applied
   (target read-only).

## The five owed items — UFIX4 re-verified each before listing (0 refuted)

| # | Path:line | UFIX4 measurement |
|---|---|---|
| 1 | `Duval/docs/research/FINDINGS_REGISTER.md:47` — "3,590 imajev rows" | `imajev-rows.jsonl`: `wc -l` = **3690**, all 3,690 lines valid JSON, 0 unparsable, 6 rounds → **3,690 confirmed; 3,590 wrong** |
| 2 | fixture `:839–847` `capability.family-010` | label `correct: 0` = "model + context"; rationale says declared tools "still construct… tool grants" → **tension real** (flagged, not a mislabel) |
| 3 | fixture `:329–338` `worker.class-023` | question's "keeps the class and adds a fs.write grant" vs rationale's "no transition can widen a role in place" → **premise self-contradictory** |
| 4 | fixture `:773–782` `capability.family-004` | answer needs "a skill is not a grant unless the policy emits one", absent from the question → **gap real** |
| 5 | fixture `:1872–1881` `topology-018` | question's own facts (disjoint, no dependency, both required, class attached) satisfy `PARALLEL`, record says `SEQUENCE`; the Reducer rule is rationale-only → **gap + sharper point real** |

## What I did NOT weaken

UVER3's reproduced results stand untouched: sha256 `076164ac…4796` identical, parser 190 cases / 721
options, ESCALATE=28 unfitted, agreement 0.905263 / κ 0.9013584840356494 / 172 of 190 exact, all 7
stratified κ, and D-P1 real (`context.package-014` the one false hit; independent non-regex parser 0/190 —
the 0/190 result is **confirmed**, not softened). The two `not_reproduced` items (the 14:28:31 write
timestamp; the re-observability of `_before`) and the two `unverified` items (Route B blindness; the
stood-down second model) are **not** edited, because they are coverage limits, not author claims to fix.

## Evidence lines

- Marker sweep: `[corrected by UFIX4 per UVER3]` present at `RUN.json:100`, `RUN.json:104` (C1),
  `RUN.json:116`, `EVIDENCE.md:280`, `PUBLICATION_STRATEGY.md:46`; `metrics.json` carries 3 `limitation`
  strings + `_correction` (verified via `json.load`: κ unchanged at `0.9013584840356494`).
- `json.load` on `RUN.json` and `metrics.json` → both parse; `related_measurement` present,
  `corroboration` absent.
- `PREREGISTRATION.md` sha256 `42bffdb0f3f71ad6238fcd4bd3e1d4e608d67b25298c325e334d84e9f05adc0f`
  (unchanged; frozen).
- No write to `/home/zer0null/Duval`; `OWED_CORRECTIONS.md` records the 5 owed items (0 refuted).
