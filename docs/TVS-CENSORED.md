# TVS-CENSORED — the censored reading of tokens-to-verified-success

Companion to [`docs/TVS.md`](TVS.md) (the definition) and
[`docs/TVS-RESULTS.md`](TVS-RESULTS.md) / [`TVS.json`](../experiments/ptr-engine/measure/TVS.json) (the first
result). **Neither of those files is edited here.** This document adds the observation that the first result
threw away: for 20 of 23 run/arm pairs the run was *observed* to its horizon without a verified success, and
that is a measurement of non-success, not a missing figure.

Machine-readable: [`TVS-CENSORED.json`](../experiments/ptr-engine/measure/TVS-CENSORED.json), produced by
`python3 /tmp/tvc/tvs_censored.py` (regenerable; two runs are byte-identical). Offline: it reads row files, grade
files and `TVS.json` only, and issues **zero** inference requests.

---

## 1. The rule this document applies

`docs/TVS.md` already forbids substituting another metric, forbids `0`, and requires `null` + reason rather than
an invented number. That rule stands and is not relaxed here. What it does not yet say is *what the null is
worth*: "no verified success" over a run that was actually observed to turn 48 is a **right-censored
observation**, and it carries two facts a `null` throws away — how long the run was watched, and what watching
it cost.

So every pair gets exactly one of two states:

| state | carries | does not carry |
|---|---|---|
| `event` | `turn_of_success`, `tokens_to_success` (prompt+completion, cached share separate), `checkpoint_id` | — |
| `censored` | `turns_observed`, the tokens actually spent, the reason the last graded checkpoint in that run did not pass | **no tvs value of any kind** |

The horizon rule: **horizon = the last turn the row file for that arm actually reaches**; the declared budget is
48 turns. A shorter horizon is reported as a shorter horizon, with its recorded reason or explicitly as
unrecorded — it is never silently treated as 48.

**Not computed anywhere in this document:** a mean, median, CI, imputed value, success rate, or Kaplan–Meier
estimate over any set containing a censored pair. One arm has 3 events, one has 0, the rest have 0. There is no
rate to estimate and this document does not estimate one.

---

## 2. The censored observation table (all 23 pairs)

`tokens` for a censored row is the **whole observed run**, deduplicated by the shared rule in `docs/TVS.md`
(identical `arm/rep/turn/ts/prompt/completion/content_sha256` counted once). It is spending, not a tvs.
`last checkpoint` is the highest-turn cell the grid's `grade_v5` file graded for that arm.

| # | grid (rows file) | arm | state | turns observed | tokens | last checkpoint | verdict / reason |
|---|---|---|---|---|---|---|---|
| 1 | `rows-longrun-2026-10-26-fix` | transcript-grow | censored | 12 | 434 290 | `cp.2.t46` | fail / `turn_missing` |
| 2 | `rows-longrun-2026-10-26-fix` | transcript-compact | censored | 3 | 64 519 | `cp.2.t46` | fail / `turn_missing` |
| 3 | `rows-longrun-2026-10-26-fix` | pointer-stable | censored | 3 | 9 705 | `cp.2.t46` | fail / `turn_missing` |
| 4 | `rows-longrun-2026-10-26-fix` | lease-reopen | censored | 3 | 7 394 | `cp.2.t46` | fail / `turn_missing` |
| 5 | `rows-longrun-2026-10-26-policy` | transcript-grow | censored | 28 | 1 385 522 | `cp.2.t46` | fail / `turn_missing` |
| 6 | `rows-longrun-2026-10-26-policy` | transcript-compact | censored | 3 | 21 360 | `cp.2.t46` | fail / `turn_missing` |
| 7 | `rows-longrun-2026-10-26-policy` | pointer-stable | censored | 3 | 16 146 | `cp.2.t46` | fail / `turn_missing` |
| 8 | `rows-longrun-2026-10-26-policy` | lease-reopen | censored | 3 | 19 635 | `cp.2.t46` | fail / `turn_missing` |
| 9 | `rows-longrun-2026-10-26` | transcript-grow | censored | 48 | 139 174 | `cp.2.t46` | undecidable / `no_answer_line` |
| 10 | `rows-longrun-2026-10-26` | transcript-compact | censored | 48 | 210 813 | `cp.2.t46` | undecidable / `prose_only` |
| 11 | `rows-longrun-2026-10-26` | pointer-stable | censored | 48 | 95 325 | `cp.2.t46` | undecidable / `no_answer_line` |
| 12 | `rows-longrun-2026-10-26` | lease-reopen | censored | 48 | 14 379 | `cp.2.t46` | undecidable / `prose_only` |
| 13 | `rows-longrun-c-2026-10-26` | transcript-grow | censored | 48 | 931 564 | `cp.2.t46` | undecidable / `prose_only` |
| 14 | `rows-longrun-c-2026-10-26` | transcript-compact | censored | 48 | 187 421 | `cp.2.t46` | undecidable / `prose_only` |
| 15 | `rows-longrun-c-2026-10-26` | pointer-stable | censored | 48 | 113 404 | `cp.2.t46` | undecidable / `prose_only` |
| 16 | `rows-longrun-c-2026-10-26` | lease-reopen | censored | 48 | 86 287 | `cp.2.t46` | undecidable / `prose_only` |
| 17 | `rows-longrun-v3-2026-10-26` | transcript-grow | censored | 48 | 172 124 | `cp.2.t46` | undecidable / `unparseable` |
| 18 | `rows-longrun-v3-2026-10-26` | pointer-stable | censored | 48 | 114 289 | `cp.2.t46` | undecidable / `unparseable` |
| 19 | `rows-longrun-v4-2026-10-26` | transcript-grow | censored | 48 | 261 698 | `cp.2.t46` | undecidable / `unparseable` |
| 20 | `rows-longrun-v4-2026-10-26` | pointer-stable | **event** | 12 | **48 347** | `cp.0.t12` | **pass / `num_equal`** |
| 21 | `rows-longrun-v4-tools-2026-10-26` | pointer-stable | **event** | 12 | **50 847** | `cp.0.t12` | **pass / `num_equal`** |
| 22 | `rows-longrun-v5-tools` | pointer-stable | censored | 48 | 382 810 | `cp.2.t46` | undecidable / `prose_only` |
| 23 | `rows-longrun-v6-tools` | pointer-stable | **event** | 12 | **111 994** | `cp.0.t12` | **pass / `num_equal`** (pre-T3 grader) |

Why the last checkpoint did not pass, by reason — the whole censored set, 20 pairs:

| reason | pairs | what it is |
|---|---|---|
| `turn_missing` | 8 | the checkpoint's turn was **never reached**: rows stop at 3, 12 or 28 turns. The verdict is a consequence of the short horizon, not of a wrong answer. |
| `prose_only` | 7 | the run answered in prose; the forced one-line `ANSWER:` contract was not met, so there is nothing to grade. |
| `no_answer_line` | 2 | no answer slot at all in the graded turn. |
| `unparseable` | 3 | an answer-shaped line existed but did not parse under ANSWER-CONTRACT v1. |

`cp.2.t46` is the last checkpoint every grid emits; for the 8 short-horizon pairs the fail is the instrument
correctly reporting that the turn never happened.

---

## 3. Per-arm censoring statement (not an average)

| arm | n_pairs | n_event | n_censored | events listed individually | censored horizons |
|---|---|---|---|---|---|
| `pointer-stable` | 9 | **3** | 6 | v4 t12 = 48 347 · v4-tools t12 = 50 847 · v6-tools t12 = 111 994 (all `cp.0.t12`) | 3, 3, 48, 48, 48, 48 |
| `transcript-grow` | 6 | 0 | 6 | none | 12, 28, 48, 48, 48, 48 |
| `transcript-compact` | 4 | 0 | 4 | none | 3, 3, 48, 48 |
| `lease-reopen` | 4 | 0 | 4 | none | 3, 3, 48, 48 |
| **all** | **23** | **3** | **20** | | |

Read this as a censoring statement, not a ranking:

- **`pointer-stable` is the only arm with any event: 3 of its 9 pairs, all at the first checkpoint (turn 12).**
  That is not a success rate of 3/9 — the six censored pairs include two that were observed for only 3 turns, so
  their non-success is not comparable on the time axis to a 48-turn non-success. The 3/9 arithmetic is reported
  only so a reader can see what was measured; it is not an estimate of anything.
- **No other arm has an event**, at 48 turns or at any shorter horizon: 0 events over 14 pairs.
- **A Kaplan–Meier curve, a hazard ratio, or a median time-to-success is not justified here.** One arm has
  3 events (all at the same turn, so there is no time variation at all inside its event set), three arms have 0.
  Any rate or survival estimate from `1 event → non-parametric survival estimate` requires an event count of at
  least a handful spread over distinct times; this corpus delivers 1 distinct event time and 0 for three arms.
  Nothing in this document is a survival curve.

---

## 4. Wasted-work decomposition — the 3 event pairs

"Tokens to verified success" splits into tokens spent *before* the successful checkpoint's turn, tokens spent
*on* it, and (for the tool grids) how many of the window's sends were tool round-trips. Follow-up sends after
the success are shown separately — they are not part of the tvs, but they are what the run went on to spend.

| pair | tvs | before turn 12 (turns 1–11) | on turn 12 | sends in window | of which tool round-trips | after success | after share of whole run |
|---|---|---|---|---|---|---|---|
| `rows-longrun-v4-2026-10-26` / pointer-stable | **48 347** | 44 213 | 4 134 | 12 (11 + 1) | 0 | 184 695 over 36 sends | 79.3 % of 233 042 |
| `rows-longrun-v4-tools-2026-10-26` / pointer-stable | **50 847** | 46 471 | 4 376 | 12 (11 + 1) | **10** | 174 333 over 39 sends | 77.4 % of 225 180 |
| `rows-longrun-v6-tools` / pointer-stable | **111 994** | 107 477 | 4 517 | 20 (19 + 1) | **16** | 195 386 over 41 sends | 63.6 % of 307 380 |

### Worked example — `rows-longrun-v4-tools-2026-10-26` / pointer-stable, tvs = 50 847

- **Before the success turn:** 46 471 tokens over turns 1–11, 11 sends — **91.4 %** of the tvs.
- **On the success turn (12):** 4 376 tokens, 1 send — **8.6 %** of the tvs, of which 0 tool round-trips.
- **Tool round-trips inside the window:** 10 of the 12 counted sends are `kind: tool-followup` fetch
  round-trips. They are the reason this cell costs **2 500 more** than the no-tools twin
  (`rows-longrun-v4-2026-10-26`, 48 347): same 12 turns, same checkpoint, same pass, 10 extra billed sends.
- **After the success:** the run kept going for 39 more sends and **174 333 tokens** — 77.4 % of its whole run
  spend came *after* the number the metric reports. The tvs is therefore not "what the run cost"; it is what the
  run had spent when the first checkpoint passed.
- Cached share (diagnostic only, never in place of the number): 0.8807.

The one mechanism that is readable from this decomposition, stated without extrapolation: **the tool-follow-up
sends are inside the window because they bill, and they are the difference between the no-tools and tools
pointer-stable cells at the same turn of the same checkpoint.** The v6-tools value (111 994) is not a like-for-like
third replicate: it is graded under the pre-T3 grader (§6) and its window carries 20 counted sends, 16 of them
tool round-trips.

---

## 5. The censoring horizon: 8 pairs stop short of 48 turns

Eight pairs are censored at a horizon **shorter than 48 turns**: four in `rows-longrun-2026-10-26-fix` (12, 3, 3, 3)
and four in `rows-longrun-2026-10-26-policy` (28, 3, 3, 3). Each carries a **grid-level** recorded reason:

- `docs/FAILED-TRIAGE.md:172` (RUN-INSTRUMENT-FIX) — *"rows exist (903 KB) but the proof is 12/48 turns, so the
  instrument fix stays unproven"*.
- `docs/FAILED-TRIAGE.md:171` (RUN-REASONING-POLICY) — *"rows 1-12 are real and row-backed; turns 13-48 were
  never sent"*.

**Answer to the question the card asks:** *no pair is censored at a short horizon with no reason recorded at all*
— `counts.short_horizons_without_a_recorded_reason` is `[]`. But the record is **grid-level, and it only names
the last turn**, not a per-arm cause:

- it explains `fix/transcript-grow` (12) and `policy/transcript-grow` (28 — whose last row is
  `finish_reason: length` at the 16 384 cap with `failed_turn: true`, so truncation is visible in the rows);
- it does **not** name a cause for the six arms whose last row is turn 3: their final row is
  `finish_reason: stop`, `failed_turn: false`, `error: null`, `http_status: null`. A clean completion at turn 3
  followed by 45 turns that were never sent is an unexplained stop at the **arm** level, and it is recorded here
  as such rather than imputed as "hit the budget" or "ended early by design".

That is why a short-horizon censored row is not interchangeable with a 48-turn one: two of the three censored
`pointer-stable` pairs (fix, policy) were watched for 3 turns, and their non-success says nothing about what
would have happened at turn 12. No comparison of censored pairs across horizons is made in this document.

---

## 6. Which grader each grade file recorded — era and stamp, per row

The card requires reading what each grade file actually recorded, and marking `grader_unstamped` where nothing is
recorded. It is worse than expected and is stated plainly:

- **All 9 declared-grid grade files that `measure/TVS.json`'s own selection uses record no `grader_sha256`**
  (`measure/cell-longrun-{base,fix,policy,c,v3,v4,v4-tools,v5-tools}-20261026T1556Z.grade-v5.json` and
  `measure/cell-pointer-stable-20261026T145722Z.grade-v5.json`). `tokens_to_verified.py`'s `cell_grade_files()`
  globs exactly `measure/cell-*.grade-v5.json`, so **every one of the 23 rows is `grader_unstamped`** in
  `TVS-CENSORED.json → cells[].grader_state`.
- **Stamped twins exist beside them:** `measure/regrade/<grid>.grade-v5.json`, 9 files, each recording
  `grader_sha256 = 6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`. Per-pair checkpoint
  verdicts were diffed against those twins: **22 of 23 pairs are identical, 1 is not.**
- **The one difference is `rows-longrun-v6-tools`**, whose picked grade file was generated at
  **14:57:22Z — before the T3 boundary (15:56:00Z)** — and is therefore **pre-T3**, not current. Its twin
  (16:00:00Z) differs on two checkpoints:

  | checkpoint | picked file (pre-T3) | stamped twin (current) |
  |---|---|---|
  | `cp.1.t24` | `fail` / `answer_not_contract` | `undecidable` / `prose_only` |
  | `cp.2.t46` | `fail` / `answer_not_contract` | `undecidable` / `unparseable` |

  **`cp.0.t12` is `pass` in both files**, so the v6 event (111 994, turn 12) survives the era change; what does
  not survive is any statement about that pair's later checkpoints. This document therefore never pools v6 with
  the other two events and never quotes its `cp.1`/`cp.2` verdicts as current-era facts.

`repair.t30` is absent from all 23 rows: it is not among the 12 declared checkpoint turns (`PARM-1-ERRATA`), and
`grade_v5` emits no cell for it. It is not in this denominator, and no censored row is created for it.

---

## 7. Proposed definition clause — **needs the owner of `docs/TVS.md` to adopt it**

This unit does not edit `docs/TVS.md`. The clause below is proposed, with the exact place it would go (§3 of
`docs/TVS.md`, beside the "No success" bullet), and it is the only text here that is not already a measured fact:

> **Censoring.** TVS is a right-censored time-to-event observation. A run/arm pair is an **event** when its first
> `grade_v5` `pass` checkpoint occurs within the run's turn budget (48); it is **censored** when the run reaches
> its horizon without one. A censored pair has **no TVS value**: it reports `turns_observed` and the tokens
> actually spent, and it is a measured non-event, not a missing datum. No mean, median, confidence interval,
> imputed value or `0` is computed over any set containing a censored pair, and no success-rate or survival
> estimate is quoted where the event count is too small to support one.

Until it is adopted, the rule above is local to this document and `TVS-CENSORED.json`; `docs/TVS.md` and
`measure/TVS.json` are unchanged.

---

## 8. What this does and does not buy the brief

**The one quotable sentence (verbatim, quotable as-is):**

> **Three of 23 run/arm pairs reached a verified success within 48 turns; all 3 are the pointer-stable arm at
> `cp.0.t12` (turn 12); the other 20 are censored at their horizon, which is a measurement of non-success, not a
> missing figure.**

What the censored view adds over "3 values and 20 blanks":

- the 20 censored pairs are **not homogeneous**: 8 were watched for fewer than 48 turns, 12 for the full 48;
- their failure modes differ and are now named: turn never reached (8), prose instead of the answer contract (7),
  no answer line (2), unparseable (3);
- their **cost is now on the record**: the 20 censored runs together spent **4 667 859 tokens** without a verified
  success. That is a spending total, not a tvs and not an average — it is the sum of whole observed runs
  (1 385 522 of it in one policy run). Of that total, **1 958 571** was spent by the 8 short-horizon pairs and
  **2 709 288** by the 12 pairs watched for the full 48 turns.

What it does **not** buy, and what the next unit would have to produce: any statement about *when* non-success
became certain, and any rate. With 1 distinct event time and 0 events in three arms, the honest output is this
table, not a curve. The cheapest real movement is still the one `docs/TVS.md` §6 names — grade the grids that
were already run — but even fully graded, 3 events at one turn cannot support an estimate; the corpus needs
events at *different* turns for that, which is a run-budget question, not a grader question.

---

## 9. Reproduce

```
# the generator is kept verbatim in orchestration/units/TVS-CENSORED.md (between #SCRIPT-BEGIN/#SCRIPT-END),
# so the verdict command can re-derive this JSON in a fresh scratch copy with no /tmp state assumed:
python3 -c "import re,pathlib
txt=pathlib.Path('orchestration/units/TVS-CENSORED.md').read_text()
m=re.search(r'#SCRIPT-BEGIN\n(.*?)#SCRIPT-END',txt,re.S)
pathlib.Path('/tmp/tvs_censored.py').write_text(m.group(1))
print('extracted',len(m.group(1)),'bytes')"; python3 /tmp/tvs_censored.py --out /tmp/tvs_cens_run1.json; python3 /tmp/tvs_censored.py --out /tmp/tvs_cens_run2.json; diff -u /tmp/tvs_cens_run1.json /tmp/tvs_cens_run2.json; diff -u /tmp/tvs_cens_run1.json experiments/ptr-engine/measure/TVS-CENSORED.json; echo DETERMINISTIC-OK
# exit 0 + "DETERMINISTIC-OK" = two independent runs are byte-identical and equal the shipped file
```

This is the exact line recorded in the verdict row (PASS, exit 0); the segments each start with an allow-listed
runner because `checkVerdictCommand` splits on `;`, `&` and `|` even inside quotes.

Integrity checks performed by the generator: the recomputed per-pair `prompt+completion` over distinct requests
equals `measure/TVS.json → cells[].whole_run_total` for all 23 pairs (**0 mismatches**); every pair's checkpoint
verdicts were diffed against its stamped twin (22 identical, 1 pre-T3 difference, §6).

## 10. Assumptions (every judgement call in this file)

| # | call | why |
|---|---|---|
| A1 | The pair space is exactly `measure/TVS.json` `cells[]` (23). No pair added, dropped or re-graded. | The card's subject is that denominator; re-grading was the previous unit's scope. |
| A2 | The grade file used per pair is the one `measure/TVS.json`'s own selection picked — not the stamped twin. | So this table cannot disagree with the produced TVS values; the twin is used only as a corroboration check. |
| A3 | `turns_observed` is measured from the rows (max turn present), not from the declared budget. | A run that stopped early must be censored at the turn it reached; calling it 48 would invent observation. |
| A4 | Tokens on a censored row are the whole observed, deduplicated run. | They are spending. They are never labelled tvs and never summed with one. |
| A5 | A `turn_missing` fail at a checkpoint beyond the horizon is reported as such, not as a wrong answer. | The instrument is right; the run was short. Distinguishing the two is the point of the horizon column. |
| A6 | All 23 rows are marked `grader_unstamped` because the grade files record no grader sha. | That is what those files record; the card's rule is per-row honesty, not a best guess. |
| A7 | The v6-tools pair is kept in the table but flagged pre-T3 and never pooled. | Its `cp.0` pass is era-stable; its later checkpoints are not, so only the era-stable fact is used. |
