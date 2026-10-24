# VM1 — independent verification of batch 1 (M1-R + M1-M)

**Status:** done. **Verdict: PARTIAL** — every headline measurement in both units reproduces exactly,
but one stated invariant does not (M1-M's "every base prompt is cold": 9/33), one denominator is
overstated (M1-R's U9 "139 rows, 0 violations" is 65 non-zero rows), and the "954" global count is a
snapshot, not a live number (today 1044). No re-run is needed.

This unit authored nothing it checks. Bound: **40 work tool calls, one attempt** (used 28). Write paths:
`orchestration/units/VM1.md`, `orchestration/handoffs/VM1.json`, `orchestration/VERDICTS.md` (append +
one table row), `scratch/vm1/**`. No live chat POST, no lock, no write under `experiments/`.

## Inputs read (in order)

`orchestration/units/M1-R.md` + `handoffs/M1-R.json`; `units/M1-M.md` + `handoffs/M1-M.json`;
`handoffs/CX-V3.json` (verdict shape) and `handoffs/CX-V2.json` (phase-1 re-derivation, overall fail);
`experiments/context-cache/README.md` (batch contract). The dead `scratch/vM1/*.py` scripts were not
executed; own scripts live in `scratch/vm1/`.

## Checks (each re-derived from the row files)

| # | Check | Result |
| --- | --- | --- |
| 1 | M1-M invariants (`rows.jsonl`) | 99 rows; `cached%64==0` **99/99**; `cached<=prompt` **99/99**; **base cold 9/33** (expected 33/33); 9 salts = one per (series,rep), 0/33 cells with >1 salt |
| 2 | M1-M control | 3/3 `cached=10432` at L 10,446/10,445/10,444 (`=64*floor(L/64)`); 0/3 `cached==prompt`; base==repeat sha256 3/3 |
| 3 | M1-M edited vs prefix join | 30 edited / 30 prefix; **22 floor64, 8 floor64−64, 0 equal to position, 0 zero**; anchors 8581→8512, 5201→5184, 5190→5120, 514→448 all exact |
| 4 | M1-M truncation | first send **8,192 on 3/3** (L 8,625/8,623/8,623); repeats 8,576 (L 8,623) and 10,368 (L 10,394); `analysis.json` matches the card table |
| 5 | M1-R U2 grid | 44/44 `cached==64*floor(L/64)`; 44/44 `uncached==L%64`; 0 rows at L%64==0 (cannot discriminate the two floor laws) |
| 6 | M1-R U9 | 65 rows with `cached>0`: **65/65** agree with `64*((L-1)//64)`; 3 disagree with `64*floor(L/64)` at L=1024 (960); 74 rows are zero-cache misses; L=1024 rep1 0 → rep2 960 |
| 7 | M1-R "954" | recipe: `rglob(**/*.jsonl)`, `cached_tokens` else `cached`, non-zero. Today **1044**, 0 non-multiples; 954 = 1044 − M1-M rows 84 − diag 6 (the 00:17 snapshot). 44 of the 954 hang on the `cached` alias (alias-free: 910 then / 1000 today) |
| 8 | M1-R cited rows | U15 `:18` R 0/1,928; `:98` A 8,448/9,263; hit rates 0.9270/0.9243/0.7627/0.7373 (A/C/F/R); U10 `:3-4` rep1 0, rep2 960 |
| 9 | M1-R live config | 2 GETs (no POST): **17/17 keys match**; `/metrics` `cache_type="UnifiedRadixCache"`; `cache_hit_rate` now 0.9975 vs 0.9748 in the author's 00:18 capture (counter drift) |
| 10 | M1-R docs | SGLang `llms-full.txt`: 0/0/0 for `non-prefix`/`CacheBlend`/`match_prefix` on today's 5,578,727-char fetch (card's 5,518,111 chars / `671770ab…` is a stale capture); vLLM "resume only at a block boundary" verbatim |
| 11 | Red→green | pristine 99/99 + 44/44 PASS; in-memory +1 and +64 → 98/99 and 43/44 RED |

## What does not reproduce

**M1-M: "fresh salt per rep → every base prompt is cold."** 9/33 kind=base rows are cold; 24/33 are
warm repeats of the byte-identical base at `cached=10432`. The 9 salts are one per (series,rep) pass, so
only the first base of each pass is cold; each of the 5 item cells per pass re-sends the same base. The
headline numbers are unaffected (the probes deliberately run on a warm base).

## Corrections (sentence-level; no re-measurement needed)

1. **954** → "954 non-zero cached counts across the 00:17 file set (0 non-multiples); re-taken today the
   same recipe gives **1044**, still 0 non-multiples (M1-M's rows arrived after the scan)." It accepts
   both `cached_tokens` and `cached`; the 954 includes 44 U2 rows that only carry `cached`.
2. **U9** → "139 rows carry a cached count; of the **65** with a non-zero count, 0 violate
   `64*((L-1)//64)`; the other 74 are zero-cache misses."
3. **M1-M** → "fresh salt per (series,rep) pass; the 9 pass-opening bases are cold, the 24 later base
   sends are warm."
4. **SGLang doc digest** is a dated capture; the negative claim holds on today's bytes
   (`sha256 d95e5e1e…`, 5,578,727 chars).

## Not verified (carried as gaps)

- The `PREFIX | INSERT | SUFFIX` 384-token test still has no artifact on disk (M1-R already flags it);
  the 0/813 probe is an in-hand prior; M1-S (the mid-prompt probe) remains unrun.
- arXiv / LMCache quotes were not re-fetched (only the two decisive doc checks were).
- M1-M's flock/serial-execution claim is not re-derivable offline (no lock log); `request_index` is
  contiguous 1..99 and the 99 timestamps span 63.6 s, consistent with serial execution.
- "30 of 40 layers linear" remains the operator's premise (M1-R flags it).

## Reproduce

```bash
.venv/bin/python scratch/vm1/checks.py    # M1-M invariants, control, edit join, truncation
.venv/bin/python scratch/vm1/checks3.py   # U2 / U9 / U10
.venv/bin/python scratch/vm1/checks4.py   # U15 + the global cached-count scan (recipe + sha256)
.venv/bin/python scratch/vm1/guard.py green ; .venv/bin/python scratch/vm1/guard.py red
```
