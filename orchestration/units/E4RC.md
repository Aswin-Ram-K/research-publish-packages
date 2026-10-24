# Unit E4RC — `e4r-record-correction`

**Status:** running (started 2026-10-21). **Purpose (one only):** apply verifier **VE4R**'s corrections to
the **E4R** record. VE4R's verdict is **pass** — every number re-derived; the defects are internal wording
contradictions and one mislabelled key set. **Record repair only: 0 live requests, no `.occamy.lock`, no
re-measurement, no `git`.**

**Hard bound:** <=8 tool calls, <=8 min. **Write paths (only):**
`orchestration/units/E4RC.md`, `orchestration/handoffs/E4RC.json`, `orchestration/units/E4R.md`,
`orchestration/handoffs/E4R.json`. No `cells/E4R/*`, no `src/`, no `tests/`, no `VERDICTS.md`.

**Inputs (read-only):** `orchestration/handoffs/{VE4R,E4R}.json`, `orchestration/units/{VE4R,E4R}.md`;
rows `experiments/context-cache/cells/E4R/e4r_rows.jsonl` (sha `05a59f28...e09a7`, not re-read here).

**Method:** additive only — every replaced string is preserved under `superseded_text`, and each repair is
listed as a `verifier_corrections` entry (claim / as_written / corrected_to / verifier / applied). Both
records rewritten temp -> parse -> keys -> `mv`, so a failed assertion leaves the originals untouched.

## Corrections to apply (VE4R, verdict pass)

| # | where | defect | repair |
|---|---|---|---|
| 1 | `E4R.md:53` vs `E4R.md:37` + `E4R.json one_repeat_lag_persists` | same label "one-repeat lag" carries opposite verdicts: refuted at `:53`, CONFIRMED at `:37`/JSON | persistence is the supported reading: "the one-repeat (transient) lag is refuted; the persistence reading is confirmed" |
| 2 | `E4R.json rep3_licensed_sentence` | "permanent one-block tax on every later repeat measured (repeats 1-3)" reads as a tax on repeats 1-3 | bound to **persistent through repeat 3 (repeats 2-3 of 3 measured)**; rep-1's tax is `L`, not 64; `(repeats 1-3)` is the window. `E4R.md:57-58` already correct |
| 3 | `E4R.json ttft_ms_medians`, `E4R.md:61-62` | `*_miss` keys (231.4/278.9) are the **rep-1** medians, not cold (232.5/279.3) | rename to `*_rep1`, add cold keys, record rep-2 116.9/117.6 and rep-3 116.7/117.3 |
| 4 | `E4R.md:52` CP95 | label check | confirmed Clopper-Pearson `0.025**(1/40)` = 0.9119, **not** Wilson 0.9124; `CP` label correct, named explicitly in the JSON |

## Numbers that must not move
180/180 requests, cold 46/46 `cached==0`, rep-3 40/40 at `L-64`, 0/40 at `L`, block tax 64 40/40,
`rep3 == rep2` 40/40, rows sha256 `05a59f28d169947fd959842ef482e07ec95fb2a96ac8405151e4aaf1920e09a7`.

## Result

**done** — four word-level corrections applied, no number moved. 2026-10-21T16:17:30-0500.

| # | applied to | before -> after | proof |
|---|---|---|---|
| 1 | `E4R.md:70` (was `:53`), `:54` row, JSON `predictions` | "One-repeat lag is refuted; transient recovery is refuted." -> "The one-repeat (transient) lag is refuted; the persistence reading is confirmed"; row relabelled `persistence (was labelled "one-repeat lag")`; JSON prediction names persistence CONFIRMED / recovery REFUTED | both readings now one sentence, opposite verdicts removed |
| 2 | JSON `rep3_licensed_sentence`; `E4R.md:74-76`, `:84-86` | "permanent ... (repeats 1-3)" -> "persistent through repeat 3 (repeats 2-3 of 3 measured); rep-1's tax is `L`; `(repeats 1-3)` = window, not tax range" | JSON now matches `E4R.md:57-58`, which VE4R found already correct |
| 3 | JSON `ttft_ms_medians`; `E4R.md:80-84` | `1024_miss`/`1088_miss` 231.442/278.87 -> `1024_rep1`/`1088_rep1`, plus `1024_cold` 232.524 / `1088_cold` 279.3 and a `ttft_ms_key_labels` note; rep-2 116.947/117.6 and rep-3 116.669/117.347 recorded | `miss` no longer readable as cold |
| 4 | JSON `rep3_counts.eq_ceiling_u10_64floor`; `E4R.md:69` | "CP95 [0.9119,1.0]" -> "... (exact Clopper-Pearson 0.025**(1/40) = 0.9119; Wilson would be 0.9124)" | card already said `CP`; interval now named |

**Numbers unchanged (re-read from the edited JSON, not retyped):** requests 180/180, cold `cached == 0`
46/46, rep-3 **40/40** at `L-64`, **0/40** at `L`, block tax 64 **40/40**, `rep3 == rep2` **40/40**.
`e4r_rows.jsonl` sha256 `05a59f28d169947fd959842ef482e07ec95fb2a96ac8405151e4aaf1920e09a7` — byte-identical,
never opened for write. `E4R.json` re-parsed after rewrite: valid JSON, 7/7 contracted keys present.

**Originals preserved:** `superseded_text` in `orchestration/handoffs/E4R.json` holds every replaced string
(licensed sentence, `*_miss` medians, prediction, `next_unit_hint`, `eq_ceiling`, and the four md fragments),
and `verifier_corrections` holds the four claim / as_written / corrected_to / verifier / applied entries.
