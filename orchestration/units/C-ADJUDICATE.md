# C-ADJUDICATE — adjudication of C1, C2, C3, C10

Adjudicated from the cited handoffs AND the artefacts they name. Rule applied: believe the artefact.
All counts below were recomputed by this unit; a handoff's prose was used only to locate the field.
Read-only; `RECORD.md` was NOT edited. Zero live requests. Bound 14 tool calls, used 13.

## C1 — SGLang avalanche magnitude

**Verdict: CLOSED** (evidence closes it; see C4 for why `RECORD.md` still can't be written yet).

Sentence: *C1 CLOSED: SGLang's residue-0 avalanche is one block, not the prefix — `/generate` `meta_info.cached_tokens` = 0 cold / 384 warm on a 423-token prompt (`experiments/ptr-engine/audit/raw_meta.json:cold,warm`), and the `parity_ok` arithmetic the engine stores is 64+L.*

Anchors:
- BILL-AUDIT DISCONFIRMED 2026-10-25: `experiments/ptr-engine/quality/runner.py:585-596` already reads `usage.prompt_tokens_details.cached_tokens` and stores `cached_reported`; this unit recomputed **48/48 request rows with `cached_tokens=None`, `cached_reported` absent entirely** — one `null`-reporting endpoint, not two instruments. So "0 is a reported zero, NOT a null" has no supporting artefact in `quality/rows.jsonl`.
- `experiments/ptr-engine/measure/rows.jsonl`: **12/12 measure rows `cached_reported: false`** — `run_cells.py:109` posts to `/chat/completions`, not `/generate`; its `cached=None` is an unreported field.
- `experiments/ptr-engine/audit/raw_meta.json` is real but a different endpoint: `cached_tokens: 0` cold, `384` warm, `details {device: 384, host: 0}`, prompt 423. It measures residue 423 mod 64 = 39, **not residue 0**, so it is no basis for "64 + L".
- Salvage: `experiments/ptr-engine/measure/rows.jsonl` cell C carries `law_uncached_measured_L = 397` — the engine's own field names 397 as *its law's* value. ENGINE-R1's 397 stands as the engine's law, not as an observed avalanche.

## C2 — vLLM avalanche magnitude

**Verdict: OPEN.**

Sentence: *C2 OPEN: vLLM's residue-{0,1} re-bill is real (`cached_tokens=0`, unc = whole prompt, TTFT 1.59 s vs 0.216 s at residue 2) but is a COLD-cache figure — no row shows a warm prefix re-billed.*

Anchors (recomputed from `experiments/miss-law/vllm2/rows.jsonl`, 133 rows):
- At P1 6336/7392/8448 (residue 0) and 6337/7393/8449 (residue 1): `cached_tokens=0`, `uncached_from_cached` = the whole prompt (6336…8449), all reps — real.
- BUT the identical figure appears at residue 2 (6338, 7394) and in the `P1<B` cold rows; TTFT ~1.58-2.47 s matches the *cold* calibration. `REPORT.md:183` states its own counterfactual as `cached = 5280, unc 2125` — i.e. **warm**, uncached 2125 ≠ P1. The arithmetic `unc = P1 + L` mixed row values from a different regime.
- The cited "8.5× TTFT jump" (`REPORT.md:176`, 7407 vs 7405) does not sit on this instrument: recomputed minimal TTFT ratio is 0.216 s → 1.59 s ≈ **7.4×**, and TTFT rises monotonically with prompt length for colder rows at the *same* residue (6336: 1.585; 7392: 2.019; 8448: 2.462 s) — length, not residue.
- `experiments/ptr-engine/ptr_engine/ledger.py:371-380` still flags vLLM `avalanche_measured=False`; the warm residue-{0,1} probe that would close it does not exist in the 133 rows.

## C3 — QUALITY-ARM's billed-token column is not a bill

**Verdict: CLOSED** (and worse than `RECORD.md` says).

Sentence: *C3 CLOSED and worse: 34,390/30,652 and 32,550/49,594 were already superseded before the run — `RESULTS.md:181`, `:248` carry 32,401 — and `RESULTS.md:181` still prints the refuted 49,594 two lines from its own correction.*

Anchors:
- `RECORD.md:118` quotes A 34,390/**34,372**/30,652 and C 32,550/34,374/49,594, but `experiments/ptr-engine/quality/RESULTS.md:181` records C rep2's raw prefix as **32,401** and `:248` calls 34,201 → 32,401 "the one numeric edit". The eight numbers in `RECORD.md:118` are the pre-correction copy; `QC-REPAIR2` edited `RESULTS.md`, **not** the handoff and **not** the rows (`quality/rows.jsonl` still holds `billed_tokens 49594`, `billed_tokens_measured 49594`).
- Root cause confirmed in-file: `quality/runner.py:495` `L = prompt_tokens + FRAMING`; the pre-repair array shift is documented at `quality/runner.py:721-730`.
- Law defect stands independently of the alignment defect: **48/48 request rows disagree** between `templated_prompt_tokens % 64` and the measured `prompt_tokens % 64` (recomputed).
- Consequence as `RECORD.md` states: no QUALITY-ARM token figure is a cost. Task success and refusals untouched (see C10).

## C10 — RESULTS.md claims a telescoping bill; +17,193 residual

**Verdict: CLOSED** (the author loses on all three counts, on its own artefact).

Sentence: *C10 CLOSED, verifier upheld: `quality/rows.jsonl` C rep2 `per_turn` reads residue 1, avalanche true, uncached 34,190 — the 49,594 bill — while C rep2's request rows carry residues 55/13/47.*

Anchors (all recomputed by this unit):
- `rep` row C rep2: `billed_tokens 49594`, `per_turn` = [{turn 2, P1 4471, residue 55}, {turn 3, P1 8589, residue 13}, **{turn 4, P1 17089, residue 1, `avalanche: true`, `uncached: 34190`}**] — the author's own field contradicts `RESULTS.md:150`'s "0 avalanches".
- **`per_turn` holds 3 entries, not 4** (turn 1 missing) — same array defect as C3; the request rows hold the other residues, so the two arrays are not comparable as written.
- **C rep2 has minus 12 net refusals, not 17,193**: recomputed `refused_total = 0` in all 12 `rep` rows (`REFUSED_COUNT` `PTR_STORE_MISS` 33 = `resolutions`-list occurrences, not turn-billed refusals). A whole turn was billed the avalanche model while unresolved/refused; the residual is a modelling gap plus what looks like one unstored turn.
- `RESULTS.md:174-175` (34,201 and "completions total 6") is superseded in the author's own file by `:181`/`:248`; the arithmetic 49,594 − 32,401 = **17,193** is still exactly right.
- The named missing field is real and unmeasured: **48/48 request rows `cached_tokens=None`** (no `cached_reported` key at all), so the bill cannot be measured from this run.

## What a single RECORD.md pass should change

1. **Line 114 (C1).** Replace the paragraph's verdict with the CLOSED sentence above. Delete the claim that ENGINE-R1's 397 is a "5.2× overstatement" — 397 is the engine's own law value (`measure/rows.jsonl:law_uncached_measured_L`); replace with: `cached_tokens` is unreported by `/chat/completions` in 12/12 measure rows and `quality/rows.jsonl` holds `cached_tokens=None` in 48/48, so no second instrument exists in the record.
2. **Line 116 (C2).** Change the opening to **OPEN** and replace the paragraph with the OPEN sentence above; delete "8.5× TTFT jump" and "recovery at residue 2".
3. **Line 118 (C3).** Keep the verdict CLOSED; correct the eight quoted figures to `RESULTS.md:181`'s values and add that `QUALITY-ARM.json:evidence.billed_tokens` and `quality/rows.jsonl` still hold 34,390/30,652 and 32,550/49,594 — the correction exists only in `RESULTS.md`.
4. **Line 120 (C4).** Unchanged: C4 stays OPEN, and C1/C3's corrections are still unapplied (`quality/runner.py` is repaired on disk but no arm re-ran; `LAW.md` and `RESULTS.md` stand as written).
5. **Line 134 (C10).** Keep CLOSED/verifier-upheld; add that the `rep` row carries **3** `per_turn` entries (turn 1 absent) and `refused_total = 0` — `PTR_STORE_MISS` 33 is not a refusal count.
