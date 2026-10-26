# FOLD-PROPOSAL — does the pointer engine belong in the manuscript?

FOLD-ENGINE, 2026-10-25. Sources read: `experiments/ptr-engine/RECORD.md` (140 lines), `ADOPTION.md` (39), `MANUSCRIPT.md` headings + abstract + §8, `GAPS.md` headings, `V-RECORD.json`, `RECON-ADJ-CLAIMS.md`, `RECON-C1.md`, and the rows named below (re-run in this unit). No request sent. Nothing but this file and the handoff written.

## Verdict

- **fold-with-limits — CHOSEN.** The arithmetic and capability results are re-derivable offline from named rows and survived an independent verifier; the cost claims did not (two refuted, one undecidable), so a §9e that prints r and the capability arms with its limits stated is defensible, and a §9e that prints any per-turn cost from this material is not.
- fold — rejected: it would print `397`, the 5.2x and the quality-arm bills, which the record itself withdraws; a publication asset cannot carry a number its own record refutes.
- do-not-fold — rejected: it would leave the paper's only measured alternative to compaction unnamed while §10a.3 cites pointer-structured context as related work.

## Buckets

### (i) publishable now — 8

- index 447 B, 12 lines, 37.25 B/line, zero-resolution prompt 472 B — `V-ENGINE-P0.json` 4 r recomputed (`checks[4]`); 447/12 arithmetic.
- index sha256 `e08700c9…9bd2`, identical across 2 processes and 2 warmpool roots — `V-ENGINE-P0.json` 3 determinism (`checks[3]`); `tests/test_determinism.py`.
- `L_app = n_payload + 12` in 387/387 rows, 0 violations — `experiments/miss-law/rows.jsonl`, re-run here.
- warm cells `cached = P1 − residue`, `uncached = residue + L`, cells A/B/D = 18/15/15 at residues 5/2/2, 13 billed in full in 9/9 warm rows — `experiments/ptr-engine/measure/rows.jsonl`; `RECON-C1.md` offset table.
- quality arm: A 3/3 and C 3/3 exact expected string, B 0/3 with 33 named `PTR_STORE_MISS` (11/rep), D 0/3 with 0 bodies resolved and a digest echoed off the index — `V-QUALITY-ARM.json` 2 discrimination (`checks[1]`).
- suite 190 passed in 0.22 s on today's tree — run here: `cd experiments/ptr-engine && python3 -m pytest -q`.
- seven distinct negative-control codes, one per control class — `V-ENGINE-P0.json` 6 seven negative (`checks[6]`); **drafted as C80, not ratified**.
- warmpool inside the repository refused `PTR_WARMPOOL_INSIDE_REPO`, directory not created — `V-ENGINE-P0.json` 7 warmpool isolation (`checks[7]`); **drafted as C81, not ratified**.

### (ii) publishable only with a stated limitation — 8

- r = 30000/447 = 67.1x — limitation: **one corpus scope only** — 12 bodies totalling 30,000 B encoded into one 447 B / 12-line index, a corpus deliberately built to sit *at* the crossover where a reference plus a fetch first pays. r is an index-encoding consequence, not a constant, and no body-count or index-format sweep was run (body count and format held at 12 and the packed 12-line index; see Corrections 2026-10-26, option b), so 67.1x must not be read as a curve. The 78.3x compact-index figure at 383 B is a **single-unit** figure, not a second point on any curve, and is not in `V-RECORD`'s confirmed set (see iii).
- 33 `PTR_STORE_MISS` — limitation: a count of resolution codes, not the rows' `refused_total` field, which is 0 (`RECORD.md` C10).
- index leak proof sha `e81ba025…531d5`, 458 B, 12 index lines (`index_lines` 12; 13 newline-terminated lines counting the final newline), no `AUD-` or `lumen` anywhere in the text — limitation: **the 458-byte / 12-line artefact was never persisted outside `/tmp`** — the QUALITY-ARM run roots were deleted, so no copy exists to hash and gap #46 of `orchestration/GAPS-INVENTORY.md` is UNCLOSABLE. What the hash covers is therefore the in-row `index_text` inside `experiments/ptr-engine/quality/rows.jsonl` — 115 rows, 4 of which carry `index_text`, one distinct value — not a file on disk; because no `AUD-` or `lumen` appears at all, none appears outside `k01` either. Re-derived here 2026-10-26 (`V-QUALITY-ARM.json` 3 index (`checks[2]`)).
- ledger reconciliation 387/387 exact, `explained_fraction` 1.0 — limitation: it reuses the same file's `uncached_tokens`; the 379 null rows read `P1` as 0, and a second instrument gave 12 exact / 9 off-by-k (`BILL-AUDIT.json:measure_sample`). Self-consistency, not wire agreement.
- harvested avalanche file 378 rows, sha `8147d195…`, arms WINDOW 126 / CEIL 108 / RECOVER 63 (+36/30/15) — limitation: single vLLM profile, file-scope, harvested after its units failed to report; supports a cell table, not a residue law; `ADOPTION.md` forbids using it as evidence.
- vLLM warm cache, cell G6: at residue 0 the warm prefix re-bills the whole prefix (`cached_tokens 0`) and the first token takes 1.79 s against 0.211 s at residue 2 in the same cell, an 8.5x warm-to-warm penalty — limitation: one residue-0 pair only (`P1 7392` at residues 0/2, two reps each, `experiments/miss-law/vllm2/rows.jsonl`); no residue-1 warm row exists anywhere in that file, and its nine cells are CAL, CAL-T and G1–G7, so the file carries no TTFT comparison across arms. The previously quoted pair was mismatched — a cold `prime` row at `P1_target 6336` against a warm `measure` row at `P1 7450`, different role and different prompt length — so the multiple across it was arithmetic rather than a contrast, and it is withdrawn (`V-FOLD-RESIDUAL.json`).
- the engine's tests: one tree, `190 passed`, run here 2026-10-26 as `cd experiments/ptr-engine && python3 -m pytest -q` (0.24 s on this run against the 0.22 s measured earlier — the count is the point, the wall time is noise). The five branch counts 95 / 100 / 153 / 171 / 108 are retired: they were five trees, none of them shippable today, and 153 was absent from `V-RECORD`'s confirmed set (C6).
- engine size 10 modules / 3,653 lines in `ptr_engine/`, 13 test files / 2,248 test lines in `tests/`, `SPEC.md` 499 lines — measured here 2026-10-26 with `ls`/`wc -l` over `experiments/ptr-engine/ptr_engine/*.py` and `experiments/ptr-engine/tests/*.py`, superseding the P0.1 count (9 modules, 1,896 + 1,222 lines, SPEC 260) that `PTR-ENGINE-P0.1.json:evidence.commands[9]` stated in the present tense; agrees with `experiments/ptr-engine/RECORD.md:142`.

### (iii) must not be published as measured — 12

- the 5.2x overstatement of `397` — UNDECIDABLE (`RECON-C1.md`): the 9 warm rows fit one-block and grid-alignment models identically; cell C is null, so the factor is 1, 5.2 or 30.5 depending on an unmeasured field.
- `397` as a law of the endpoint — refuted: the identical append bills 15/18 at residues 2/5 (`RECON-C1.md`).
- bill telescopes as `Σ prompt_tokens + 12(R−1)` — refuted: stored 32,401 vs claimed 34,201, residual +17,193, and the three completions total 6 tokens (`V-QUALITY-ARM.json` 5 billed tokens (`checks[4]`)).
- `49,594` as a measured bill — it is the model's own bill (residue 1, avalanche true, `uncached` 34,190) (C10).
- quality-arm token figures 34,390 / 34,372 / 30,652 and the A-vs-C −2 gap — void as costs (`BILL-AUDIT.json:root_cause`; C3).
- 57.6x understatement — one unit's replay, not re-derived; keep the lesson, not the multiple.
- 26x avalanche insurance — inherited from a null-instrument row; not re-measured anywhere (`RECON-C1.md` §5).
- a per-turn vLLM TTFT multiple — the earlier pair (cold `prime` against warm `measure`, different prompt lengths) is withdrawn; what is measured is a warm-to-warm 8.5x at one residue-0 boundary in one cell (G6), which is a single-cell boundary effect, not a per-turn cost (`V-FOLD-RESIDUAL.json`).
- 141/129 avalanche split or any residue→avalanche law — residue is not separable from P1 (`RECORD.md` C9; `HARVEST.md`).
- padding predictions `r ≥ 34`, `PAD_FOR_FREE_RESIDUE = 33`, "compact unpadded wins by 12/cycle" — an uncalibrated stub (C5).
- "no measured padded cycle exists" — false: cells A/B/D are measured padded cycles at pads 60/58/50 (C5-ADJUDICATE).
- 78.3x compact index at 383 B — single-unit figure, not in `V-RECORD`'s confirmed set.

## Draft insertion

**DRAFT — not in `MANUSCRIPT.md`, not in `CLAIMS.md`.** Proposed placement: new §9e, after §9d and before §10. Proposed claim ids **C75–C81**: C75–C79 for the fold's five results, and C80/C81 drafted 2026-10-26 from `V-ENGINE-P0.json` checks 6/7 — **drafted, not ratified** — so bucket (i)'s eight items all carry a claim. C75–C81 collide with nothing: `grep -rnoE 'C7[5-9]|C8[01]' papers/*/CLAIMS.md` returns 0 hits across all four claim files. An earlier draft's C70–C74 would have collided — `papers/gated-read-batching/CLAIMS.md:121-124` already defines C70–C73.

## 9e. What a pointer index saves, at the corpus it was built for

The engine in `experiments/ptr-engine/` is not a cache policy, but it changes what the prompt carries, so its saving is measurable in this paper's units. It compiles a turn's material into a 12-line index over a content-addressed store and resolves a reference through one `fetch` call; the host never re-sends a body it already sent. At 12 bodies totalling 30,000 B the index is 447 B, 37.25 B per line, and a turn that resolves nothing carries 472 B instead of 30,000 B — r = 30000/447 = 67.1x (C75). The index is byte-identical across two Python processes and two warmpool roots, so the byte count is not one run's accident. r is not a constant of the technique: it moves with body count and index format, and this corpus sits at the crossover where a reference plus a fetch first pays, not at a flattering size.

The append is 12 framing tokens. Over the 387 rows of `experiments/miss-law/rows.jsonl` that carry both fields, `L_app = n_payload + 12` with 0 violations (C76). On the engine's own three warm cells the server's report is `cached = P1 − residue` and `uncached = residue + L`: cells A/B/D read 18/15/15 uncached at residues 5/2/2, the append (13 tokens) billed in full in all nine warm rows with no spread around the identity (C77). The one residue-0 cell in that set reports a null cache field and carries no claim here; what this endpoint bills when the prompt ends on a block boundary is not measured in this package, and we do not fill the gap by assumption.

Capability was pre-registered and kept apart from cost. With every body retained the model reached the one fact-bearing body in 3/3 repetitions, returning the exact expected string; with only the three newest retained it returned 0/3, and every missing body produced a named `PTR_STORE_MISS` resolution (11 per repetition, 33 in total) with no silent wrong answer; compaction of a non-fact body still finished 3/3; and an index-only control — same corpus, plan and question, no body ever resolved — scored 0/3 and answered with a digest echoed off the index, the control that makes the other three arms measurable (C78). The package's suite passes 190 tests in 0.22 s from `experiments/ptr-engine` (C79). Failure is named rather than thrown: the seven negative controls are seven distinct codes, one per control class (C80), and a warm pool pointed inside the repository is refused by name with no directory created (C81). Every figure in this section is re-derivable offline from the artefact named beside it; none is a per-turn cost, and we print none from the quality arm, whose cache field never reached its rows.

| claim | artefact | command |
|---|---|---|
| C75 | `orchestration/handoffs/V-ENGINE-P0.json` 3 determinism (`checks[3]`), 4 r recomputed (`checks[4]`) | `cd experiments/ptr-engine && python3 -m pytest -q tests/test_determinism.py && python3 -c "print(30000/447, 447/12)"` |
| C76 | `experiments/miss-law/rows.jsonl` | `python3 -c "import json;R=[json.loads(l) for l in open('experiments/miss-law/rows.jsonl')];H=[x for x in R if 'n_payload' in x and 'L_app' in x];print(len(H), sum(x['L_app']!=x['n_payload']+12 for x in H))"` |
| C77 | `experiments/ptr-engine/measure/rows.jsonl` | `python3 -c "import json;W=[x for x in map(json.loads,open('experiments/ptr-engine/measure/rows.jsonl')) if x.get('cached_tokens') is not None];print([(x['cell'],x['residue'],x['cached_tokens'],x['uncached_tokens'],x['L']) for x in W])"` |
| C78 | `experiments/ptr-engine/quality/rows.jsonl`; re-derivation in `orchestration/handoffs/V-QUALITY-ARM.json` 2 discrimination (`checks[1]`) | the arm's own rows: A 3/3, B 0/3, C 3/3, D 0/3; D `resolved_total [0,0,0]`, `withheld_total [5,5,5]` |
| C79 | `experiments/ptr-engine/tests/` | `cd experiments/ptr-engine && python3 -m pytest -q` → `190 passed` |
| C80 | `experiments/ptr-engine/tests/test_negative_controls.py:104-114`; `V-ENGINE-P0.json` 6 seven negative (`checks[6]`) | `cd experiments/ptr-engine && python3 -m pytest -q tests/test_negative_controls.py` → one control per class, codes `PTR_SYNTAX` / `PTR_UNKNOWN_KIND` / `PTR_UNKNOWN_ID` / `PTR_SCOPE_UNGRANTED` / `PTR_PROJECTION_UNENUMERATED` / `PTR_POINTER_INVALID` / `PTR_BUDGET_EXCEEDED`, 7/7 distinct, each asserted `isinstance(PtrError)` and `str.startswith(code)` |
| C81 | `V-ENGINE-P0.json` 7 warmpool isolation (`checks[7]`) | run both ways: the repo root, `experiments/ptr-engine`, and `PTR_WARMPOOL_ROOT=<repo>/cache-warmpool` each refuse `PTR_WARMPOOL_INSIDE_REPO` with the directory **not created**; a `/tmp` root is accepted and created, `default_root()` → `~/.cache/ptr-engine/warmpool` |

**Limits that travel with it:** one engine (SGLang, B = 64), one model, one corpus of 12 bodies over 4 turns, one seed; the corpus was built to sit at the crossover, so r does not transfer to another body count or index format.

## What it costs

Folding buys an external reader the thing the paper now lacks: a measured alternative to compaction whose saving is arithmetic at a stated corpus and whose failure mode is a named refusal rather than a silent loss, plus the control that proves an index alone is not an answer. It costs the paper its clean scope, and a reviewer will collect on it in the first round: a warm cache reading at residue 0 (cell C is null, so `397` is evidence in neither direction), a residue-1 cell on SGLang (only vLLM has one), a compact **unpadded** index cell at a recorded P1 and residue (cell E, never run), a per-turn `cached_tokens` in the quality arm's rows (read at `quality/runner.py:585-596`, never stored — which is why no token figure from that arm is a cost), and a corpus build a reader can run — `experiments/ptr-engine/tools/rebuild_corpus.py`, written and verified 2026-10-25 19:00, prints BODIES 12 / BODY_BYTES 30000 / INDEX_BYTES 447 / INDEX_LINES 12 / BYTES_PER_LINE 37.25 / ZERO_RESOLUTION_PROMPT 472 / the index sha256, and two runs from different roots were byte-identical, so the reproducibility demand is satisfied. It also exposes a seam on the page: §8's 372/372 append deviation is measured on 931–12,393-token histories, while these 322–386-token appends follow the grid exactly, so §9e must be read as a second regime or §8's universal wording has to be scoped — an edit an operator, not this unit, must approve.

## What would have to be measured first

- residue-0 warm `cached_tokens` on `:8012` at P1 = 384, L = 13 — decides `397` vs `77` vs `13`, i.e. closes C1 instead of citing the boundary of it.
- one residue-1 cell on SGLang (asserted at `RECORD.md:114`, present in no row).
- cell E: the compact index **unpadded**, with P1_E and residue recorded, in `experiments/ptr-engine/measure/rows.jsonl`.
- per-turn `usage.prompt_tokens_details.cached_tokens` stored in `quality/rows.jsonl`, and `refused_total` populated — without both, the quality arm has no bill and no refusal count of its own.
- ~~a 12-body corpus build script printing 30000 / 447 / 472 so r is a command, not a handoff~~ — satisfied 2026-10-25 by `experiments/ptr-engine/tools/rebuild_corpus.py` (see Corrections).
- mamba / hybrid-state settings on `:8012` — reported by no input handoff (`ADOPTION.md`), so the append deviation stays unexplained.

## Corrections (2026-10-26)

Source: independent verifier handoff `orchestration/handoffs/V-FOLD.json` (verdict `fail`); values-only repair, no re-analysis.

- Suite count: the stale three-instance figure replaced with `190 passed in 0.22 s`, re-measured here with `cd experiments/ptr-engine && python3 -m pytest -q` (lines 20, 32, 60, 68).
- Claim identifiers: the five drafted claims renumbered to C75–C79 in drafted order, C75 being the next free identifier across the paper set (lines 52-68).
- `checks[...]` citations re-pointed at the array element whose text begins with the cited label, in both `V-ENGINE-P0.json` and `V-QUALITY-ARM.json`; each now reads `<label> (checks[i])` (lines 15, 16, 19, 21, 22, 28, 39, 64, 67).
- Corpus build: the claim that no runnable 12-body build exists is withdrawn — `experiments/ptr-engine/tools/rebuild_corpus.py` (verified 2026-10-25 19:00) prints the corpus figures and the index sha256, byte-identical across two roots, so reproducibility is satisfied (lines 74, 82).
- Bucket (i) items 7 and 8 (seven negative-control codes; `PTR_WARMPOOL_INSIDE_REPO` warmpool refusal) marked `no claim drafted — needs a claim, not a fold`; no sixth claim invented (lines 21-22).
- TTFT pair: the mismatched cold-`prime` / warm-`measure` pair withdrawn and replaced by the controlled residue-0 against residue-2 measurement in cell G6, an 8.5x warm-to-warm boundary penalty; values only, no claim id attached, per `orchestration/handoffs/V-FOLD-RESIDUAL.json` (lines 31, 44).
- 2026-10-26 (FOLD-FIX-3, from V-FOLD-2): bucket (i) publishable-now count corrected 9 -> 8 to match its eight bullets; claim-id justification restated from the measured `grep` (C75-C79 free in all four claim files; C70-C73 collided with `papers/gated-read-batching/CLAIMS.md:121-124`, C74 free); suite wall time corrected 0.27 s -> 0.22 s (measured).
- 2026-10-26 (FOLD-CONSISTENCY, gaps #1/#2/#7/#9/#11 of `orchestration/GAPS-INVENTORY.md`): engine size re-measured to **10 modules / 3,653 engine lines, 13 test files / 2,248 test lines, SPEC 499** (was 9 / 1,896 + 1,222 / 260) (#1); the five branch suite counts replaced by the one measured tree, `190 passed` (#2); the leak-proof line now states that the 458 B / 12-line artefact was **never persisted outside `/tmp`** (gap #46, UNCLOSABLE) and that the hash `e81ba025…531d5` is over `index_text` in `quality/rows.jsonl` — 115 rows, 4 carrying one distinct `index_text`, no `AUD-`/`lumen` anywhere — re-derived here (#7; the 48-row figure quoted for this file does not reproduce against today's 115-row artefact); `r = 67.1x` marked as one corpus scope and 78.3x marked single-unit, with a body-count sweep not run and why (#9, option b); bucket (i)'s two claimless items drafted as **C80** and **C81**, drafted-not-ratified, `grep -rnoE 'C7[5-9]|C8[01]' papers/*/CLAIMS.md` returning 0 hits (#11).

The classification — 8 publishable now / 8 publishable with a stated limitation / 12 not publishable as measured — is unchanged in substance; only bucket (i)'s count label was corrected to 8 to match its eight bullets.
