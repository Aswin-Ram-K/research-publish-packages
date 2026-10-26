# CLAIM-HEALTH.md — the 20 suspect-cell claims, judged

**Verdict: 20 claims reviewed — SAFE 7 / REMEASURED 0 / BLOCKED 13.**
No number in `CLAIMS.md` is changed here; this file states only whether each cell is safe to publish.
Source of the class: `orchestration/handoffs/CACHED-AUDIT2.json` (27 cells, 96 cell-arm entries,
`clean 12 / suspect 13 / corrupt 2`, detector calibrated red→green, 0 live requests). Read offline:
`tools/audit/cached_dedupe.py` + `state/logs/cached-dedupe-audit.json`, no endpoint contacted, no model lock.

## The 20 rows

| id | value | cell | audit class | outcome | evidence |
|---|---|---|---|---|---|
| C06 | B/A_cf 5.3922 (A 2,856 unc); measured 3.3133 (superseded as an effect size); G5 ref 6.744 | U4b-rows, G5-rows | U4b clean (0 fires); G5 suspect (C 2/64) | SAFE | 5.3922 is the U4b counterfactual; U4b A/B/C 0/8 fires each, so the 3.3133-and-above relation cannot move. G5 contributes only the A/B arms (0/64) |
| C17 | R: prompt 194,788 / cached 143,616 / unc 51,172 / hit .7373 / 40 rows | U15-rows | suspect (a) U15 R 7/40 fires (rate .1842) | BLOCKED | 7 fired turns on R, excess 902-948 each (~6,325 total): both cached 143,616 and unc 51,172 rest on those rows; hit .7373 is a function of them |
| C18 | F: 198,376 / 151,296 / 47,080 / .7627 / 40 | U15-rows | suspect (a) U15 F 2/40 fires | BLOCKED | 2 fired turns (33, 34; excess 842 + 1,270 = 2,112) sit in F's totals |
| C19 | A: 412,177 / 382,080 / 30,097 / .9270 / 40 | U15-rows | suspect (a) U15 A 1/40 fires | BLOCKED | A carries 1 fired turn at rate .0256; cached 382,080 is therefore not exact |
| C20 | C: 403,259 / 372,736 / 30,523 / .9243 / 40 | U15-rows | suspect (a) U15 C 2/40 fires | BLOCKED | C carries 2 fired turns (rate .0513) feeding its hit fraction |
| C21 | A/R 1.7002359; R/F 1.0869159; F/A 1.5642755; gap 8.69 % | U15-rows | suspect (a) U15 R 7 / F 2 / A 1 of 40 | BLOCKED | every operand of both ratios is an arm with fired rows; direction is conservative (R inflated) but the figure itself is not derivable from clean rows |
| C22 | net break 1,620 / excess 20,649 = .078454; steady 19,029 = .921546 | U15-rows | suspect (a) U15 R 7/40, F 2/40 | BLOCKED | excess is the R-minus-A uncached difference; the R arm's fired rows move it |
| C23 | R 1,659.9375 on 5,811.9375; C 754.9375 on 12,838.9375; A 722.9375 on 13,146.9375; F 1,678.9375 on 5,942.9375 | U15-rows | suspect (a) U15 all four arms fire | BLOCKED | the uncached numerators are (prompt - cached) means over turns 19-34, all four arms carry fires |
| C24 | counterfactual R 32,143; R/cf-A 1.0679802 | U15-rows | suspect (a) U15 R 7/40 | BLOCKED | counterfactual R is built from R's own fired rows |
| C25 | first 1,186; last 19,583; growth 18,397 (16.5118x); prompt 412,177 vs 403,259 (+8,918); R last 4,134 | U15-rows | suspect (a) U15 A 1 / C 2 / R 7 of 40 | SAFE | all five values are prompt_tokens aggregates; the flagged defect is cached_tokens credit and never rewrites prompt_tokens (checked: A 382,080+30,097=412,177) |
| C26 | R breaks [18, 35]; F breaks [18, 35]; A []; C [] | U15-rows | suspect (a) U15 R 7 / F 2 of 40 | SAFE | a break is a prompt_tokens shrink between turns; it is a turn index, not a token sum, so no cached_tokens fire can create or erase one |
| C44 | E/F 1.0384615; mean gross E 1,728.0 / F 1,664.0; 2/6 within 10 %; flag False | G1-rows, G1-analysis | suspect (a) G1 F 13/132 fires (rate .1032) | BLOCKED | gross per-break cost is uncached mass on F; 13 of F's 132 rows are fired, so both the means and the 2/6 count were computed over flagged credit |
| C45 | 1,800 rows, 900 + 900, 1,800 status 200, sha256 ea5728760… | WIN-SGL-rows | suspect (a) A 6 / R 5 / C 4 / H 4 of 444 | SAFE | row count, per-config count, status and file digest are properties of the file, not of cached_tokens values |
| C46 | S1 hit .974202, 740.4/turn (32k 729.2, 64k 746.01), gcd 64, odd64 351; S2 hit .973778, 752.6 (745.2/756.28), gcd 128, odd64 0 | WIN-SGL-rows | suspect (a) A 6 / R 5 / C 4 / H 4 of 444 | BLOCKED | hit and uncached-per-turn are direct functions of cached_tokens (fires at .0091-.0136 per arm); only the gcd/odd64 grid column is prompt-geometry and would survive a re-run |
| C47 | 888 rows OK; hit .974242; 739.2/turn (725.74, 746.01); steady 880; gcd 64; odd64 351; sha d6313f72… | G3-rows | suspect (a) A 8 / C 7 / H 7 / R 7 of 222 | BLOCKED | hit .974242 and 739.2 rest on cached_tokens (7-8 fired rows per arm); row count, sha and the grid are clean but the claim's headline numbers are not |
| C48 | 692 rows; V1 358 / V2 312 / V3 22; 692 status 200; sha256 a606ca06… | WIN-VLLM-rows | suspect (a) A/C/H/R each 14/142 fires (rate .1061) | SAFE | counts, per-config split, status and digest are file properties; no cached_tokens value enters them |
| C49 | V1 gcd 1088, exact 10/70, 19 distinct L; V2 gcd 1056, 10/26, 11; V3 2096, 15/20, 5 | WIN-VLLM-rows | suspect (a) 14/142 per arm | SAFE | gcd, exact-match count and distinct-L count are computed over prompt lengths L only, not over cached_tokens |
| C50 | V1 hit .869037, 2,230.8/turn (n=284); V2 hit .868144, 2,246.0/turn | WIN-VLLM-rows | suspect (a) 14/142 per arm (rate .1061) | BLOCKED | 14 of every arm's 142 rows fire — after U15 R the highest fire rate touching a claim — and both headline numbers are cached_tokens functions |
| C51 | S0 32k unc 725.74 / hit .974242 vs V1 2,230.8 / .869037; ratio 3.074x | G3-rows, WIN-VLLM-rows | suspect (a) both cells: G3 7-8/222, WIN-VLLM 14/142 | BLOCKED | composite of C47 and C50: both operands are flagged, so the 3.074x inherits both exposures |
| C53 | B/A 6.744331504 [4.04542649, 9.44323652]; C/A 1.105174403; A 123,240/102,912/20,328; B 123,256/0/123,256 | G5-rows | suspect (a) G5 C 2/64 fires; A and B 0/64 | SAFE | the headline B/A interval is computed from A and B, both 0/64 fires (0 fires over 64 rows each); only the secondary C/A touches the 2 fired C-arm rows |

## Why `suspect` — and which flavour

All 20 claims sit on cells classed `suspect` for reason **(a), the flagged `cached_tokens` pattern** —
a one-quantum gap inflation that snaps back within 3 credit rows (the detector's only signature).
None is suspect for a non-cached_tokens reason: no cell here has a missing arm, an unparseable row or a
grid anomaly. Per-arm fire counts for the six cells involved: U15 R 7/40, F 2/40, C 2/40, A 1/40 ·
G1 F 13/132, E 1/132 · G3 A 8/222, C 7/222, H 7/222, R 7/222 · WIN-SGL A 6/444, R 5/444, C 4/444,
H 4/444 · WIN-VLLM A/C/H/R 14/142 · G5 C 2/64 (A, B clean) · U4b 0/8 on all three arms.

## REMEASURED — pairs printed side by side

**None of the 20 converts.** No claim in this set cites a cell that now has a clean replacement measuring
the same setup, so nothing is promoted to `verified-twice` by this review. Two same-setup pairs exist and
both fail to launder the class, printed here because they are the only candidates:

| pair | suspect / old value | clean / new value | agreement | why it does not convert |
|---|---|---|---|---|
| U15 R vs E2 R (same 40-turn R arm) | U15 R unc/turn 1,279.3, hit 0.7373 (**suspect**, R 7/40) | E2 R unc/turn 1,278.3, hit 0.737445 (**suspect**, 13/51 fires overall) | 0.08 % on unc/turn, 0.0002 on hit | E2 is itself suspect — two suspect copies agreeing is not a clean second measurement |
| PROMPT-O2-EXTRA vs R2-P1-O2 (both 355 rows, SGLang O2) | 600.17 R / 528.89 A (repaired in place by R2-P1-O2C) | 599.12 R / 529.48 A (0 fires, class clean) | 0.18 % on R, 0.11 % on A | **no claim cites PROMPT-O2-EXTRA** (the cell has no CLAIMS.md abbrev), so there is nothing for it to convert |

G5 is the near-miss worth naming: C53's headline B/A interval rests on arms A and B, which are 0/64 fires
in a cell whose C arm has 2 fires — that is why C53 is SAFE while C51 (both operands flagged) is not.

## BLOCKED — for a live re-run, numbers untouched

Each needs a fresh cell of the same setup measured on the calibrated path; none can be repaired offline
from the existing rows, because the defect is in the cached_tokens credit those rows record.

| claim(s) | why blocked | card that would fix it |
|---|---|---|
| C17, C18, C19, C20, C21, C22, C23, C24 | U15 arms R/F/A/C all carry fired turns; every total, ratio and share is a cached_tokens function | `REMEASURE-U15` — re-run U15 exactly (arms R, F, A, C × 40 turns, same prompts) |
| C44 | G1 F arm 13/132 fired; gross per-break cost and the 2/6-within-10 % count were computed over them | `REMEASURE-G1-BREAK` — re-run G1 (arms E, F × 132 rows, 6 break events) |
| C46 | WIN-SGL hit and uncached/turn; 4-6 fired rows per arm | `REMEASURE-WIN-SGL` — re-run WIN-SGL (S1 page 64, S2 page 128, 900 each) |
| C47 | G3 S0 hit .974242 and 739.2/turn; 7-8 fired rows per arm | `REMEASURE-G3-S0` — re-run G3 S0 (page_size 1, 888 rows) |
| C50 | WIN-VLLM V1/V2 hit and uncached/turn; 14/142 fires per arm | `REMEASURE-WIN-VLLM-V1` — re-run WIN-VLLM V1 and V2 |
| C51 | composite of C47 and C50 | needs **both** `REMEASURE-G3-S0` and `REMEASURE-WIN-VLLM-V1` |

All six cards are live-measurement cards: GX10, `.occamy.lock` held for the batch, no number edited until
the fresh cell's own audit is clean. Until then the affected figures stay published-as-measured but
carry this BLOCKED flag — the direction is conservative on U15 R (R's uncached is inflated, so A/R ≥
1.700), which is not a licence to republish them.

## What this review did not do

- No live request, no endpoint, no model lock, no GX10 contact (0 network calls in this unit).
- No edit to `CLAIMS.md`, `MANUSCRIPT.md`, `EVIDENCE.md`, `RUN.json`, `recompute.py` or any test.
- Classes are taken as given from `CACHED-AUDIT2.json`; the audit log on disk predates the R2-P1-O2
  repair (the cell now holds 355 clean rows), which is recorded in the assumptions rather than re-derived.
