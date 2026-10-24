# UPAPER9 — Final alignment pass: paper ↔ neutralised release identifiers

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a · **Status: DONE** · **Tool calls used: 10 / 20**

## Purpose
Align `papers/encoder-crossover-190/**` with the twice-verified neutralised release tree
`scratch/uneutral10/package/` after neutralisation moved two printed numbers.

## FINAL numbers
- route A κ `0.3252` → **`0.3249`** (exact `0.3248813212427869`)
- route A agreement `0.3421` → **unchanged** (exact `0.34210526315789475`)
- A/B mutual agreement `0.3526` → **`0.3684`** (exact `0.3684210526315789`)
- `disagreements_where_routeA_backs_record` `5` → **`4`**
- unchanged: route B κ `0.9013584840356494`, route B agreement `0.9052631578947369`, fixture digest `c7696edc…c9a55`

## Site classification (LIVE = corrected in place; FROZEN = byte-intact + dated `Note 2026-10-16:`)

### LIVE
| Site | Why LIVE | Change |
|---|---|---|
| `CLAIMS.md:108` | present-tense claims table; value asserts current `.routeA.kappa` | `0.3252`→`0.3249`; exact `0.32520740993294694`→`0.3248813212427869` |
| `CLAIMS.md:109` | same table | `0.3526`→`0.3684` |
| `CLAIMS.md:110` | same table (**missed by UNEUTRAL10**) | `5`→`4` (both occurrences) |
| `GAPS.md:19` | current values table | `0.3252`→`0.3249` |
| `MANUSCRIPT.md:381` | §3.4 current result caveat | κ `0.3252`→`0.3249` |
| `MANUSCRIPT.md:633` | §6.2 current caveat | `0.3526`→`0.3684`; κ `0.3252`→`0.3249` |
| `MANUSCRIPT.md:634` | same sentence | `5`→`4` of 18 |
| `MANUSCRIPT.md:852-855` | **missed by UNEUTRAL10**; LIVE and newly FALSE (said the four external entries were still missing title/author, but UBIB1 completed them) | ported UBIB1's completed-bibliography wording |
| `submission/main.tex:195` | generated from `MANUSCRIPT.md:381` | via regeneration |
| `submission/main.tex:335` | generated from `MANUSCRIPT.md:633-634` | via regeneration |

### FROZEN (original bytes kept; dated note appended)
`EVIDENCE_NOTES.md:279`, `:280`, and `:281` (**missed by UNEUTRAL10**) — verbatim past-run output block;
`LIMITATIONS_UPDATE.md:245` — "Explicitly NOT changed" ledger; `VERIFIER_CORRECTIONS.md:139` — verifier's
occurrence recount at the time; `DISCLOSURE_CHANGES.md:143` — disclosure change-log of a past pass.

### Sweep results
All `0.3474` / `0.3473684210526316` hits are **arm accuracies** (modernbert/deberta tie, H4 monotone ordering,
F1 narrative), not the A/B figure → **unchanged**. `0.3526` was the only A/B figure. `0.3421` unchanged by design.

## New limitations sentence (placed `MANUSCRIPT.md:635-638`, §6.2 under §6 Limitations, in the bullet that
already carries the route A caveat)

> Route A is a **tokeniser-overlap rule** rather than a model, so its κ moves by a few thousandths with how the
> fixture's text is spelled and cased — the measured range across our neutralisation rounds was 0.319886… to
> 0.324881… — an order of magnitude smaller than its ≈0.33 separation from the decider, so no conclusion rests
> on the exact value.

## main.tex regeneration (never hand-edited for numbers)
`python3 scratch/uprep1/md2tex.py` → 79814 bytes. **Final diff vs `scratch/upaper9/main.tex.before` = lines 195
and 335 only.** 0 non-ASCII bytes; 12 `\bibitem`s (all keys present); λ agreement `0.3421` intact.

### UBIB1 survival — converter WOULD drop/reformat, so I did not ship it
- `main.tex:428` was a **main.tex-only hand-patch** absent from `MANUSCRIPT.md:852-855`; regeneration reverted it.
  Fixed durably by porting the wording into its true source, then restoring `:428` verbatim.
- `:431-434` regenerate from `REFERENCES.bib` and gain UBIB1's own `howpublished` provenance — author/title survive.
- `:435` `source_decider_stack_2026`: converter drops "unpublished internal corpus document (no attributable
  author)" and appends the wrong `[Author and/or title not recorded …]` placeholder. **Restored `:428` + `:431-435`
  verbatim** (prose, not numbers) so no regression ships.
- Follow-up: align `REFERENCES.bib`/`md2tex` for the authorless internal entry.

## benayas2024comparative — DO NOT MERGE (not unambiguous)
Complete at `REFERENCES_ADDITIONS.bib:109-145`; `REFS_VERIFIED.md:22` says **FOUND**, but `UNSOURCED_RETAINED.md:12`
and `REFERENCES.bib:21-23` say **NOT FOUND/dropped**, and `submission/BUILD_NOTES.md:54-55` records the deliberate
exclusion. The do-not-cite list forbids the 94.27/70.87 numbers. Two units contradict; merging forces argument edits
at `MANUSCRIPT.md:182-190`/`677-679` → sourcing decision for a dedicated unit. **No merge; `main.tex:428`'s
125M-RoBERTa clause left deliberately stale.**

## Constraints honoured
No number other than the four moved. `/home/zer0null/Duval` untouched. No `scratch/uneutral*/` or
`research-publish-packages` writes. `submission/ABSTRACT_METADATA.txt` untouched.
