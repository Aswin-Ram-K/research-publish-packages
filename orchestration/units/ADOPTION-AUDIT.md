# ADOPTION-AUDIT — is `experiments/ptr-engine/ADOPTION.md` safe to act on?

**Verdict:** `partial` — 27 items; **19 CONFIRMED · 6 OVERSTATED · 1 STALE · 1 WRONG**. Bound 16, used 13. Nothing audited was edited and nothing was repaired.
**Method:** every distinct claim/recommendation in the 39-line page numbered and re-derived from rows — `RECORD.md`, `CLAIMS.md`, `miss-law/{LAW.md,rows.jsonl}`, `measure/rows.jsonl`, `quality/{RESULTS.md,PREREG.json,rows.jsonl}`, `audit/rows.jsonl`, and the P0/V-QUALITY/BILL-AUDIT handoffs. Prose was not accepted.

| # | operative clause | class |
|---|---|---|
| 1–5 | r 67.1x (30000/447); 78.3x compact (30000/383); A 3/3 · B 0/3 · C 3/3; retention is capability not cost; law bill 57.6x low (123 vs 7,087) | CONFIRMED, all re-derived |
| 8,9 | `:8012` occamy-1.0 SGLang `page_size=1` `enable_cache_report` 131072; B=64 / 1056 | CONFIRMED (`LAW.md` §1) |
| 11–14 | 12 lines / 447 B / 37.25 B per line / same sha256 across processes+roots; py3.11+; warmpool outside repo; `L = n_payload+12` (387/387) | CONFIRMED |
| 16 | vLLM whole-prefix re-bill, 8.5x TTFT | CONFIRMED — cell G6, 8.49x/8.48x warm-vs-warm |
| 18,19 | `PTR_REVISION_MISMATCH` deliberate; index-only arm echoes a digest, 0/3 | CONFIRMED (`756741be` x3) |
| 21–24 | don't bill from `Σ prompt_tokens`+law; `cached=null` is not 0; 387/387 is not wire proof; don't call a cap's saving a win; don't cite the 34.4 k quality figures | CONFIRMED (+17,193; no `cached_tokens` key in 115 rows) |
| 26 | name the branch when quoting a test count (95/100/108/153/171) | CONFIRMED |
| 6 | "Read `meta_info.cached_tokens` per turn" | OVERSTATED — `/generate`-only field; the engine posted `/chat/completions` |
| 7 | "`prompt_tokens_details` null where something was cached" | OVERSTATED — true only at residue {0,1}; warm chat returns 384 |
| 10 | mamba "reported by no input handoff … table carries no such field" | OVERSTATED — `EVIDENCE.md:16` has `max_mamba_cache_size 64` |
| 15 | SGLang residue 0 re-bills "one block (64 + L)" | OVERSTATED — C1 UNDECIDABLE; measure cell C says 397 |
| 17 | "One client … overstated an append 5.2x" | STALE — 5.2x WITHDRAWN in RECORD §5 C1 |
| 20 | "no measured padded cycle exists at all" | **WRONG** — nine measured, pads 60/58/50 cells B/C/D |
| 25 | 378 avalanche rows unusable, "never consumed by a unit" | OVERSTATED — C9: measurements; `HARVEST.md` used 270 |
| 27 | "Everything here is derivable from RECORD.md" | OVERSTATED — items 15/17 take one C1 layer, and `LAW.md:§1` is not a resolvable citation |

**Unsafe to act on** — #15 budgets one block where the prefix may re-bill (add: budget the whole prefix until a residue-0 warm row exists); #20 removes the only measured non-avalanche shape on a false premise (add: withdrawn, nine padded requests measured); #6+#7+#17 bill against a field null off `/generate` and generalise a withdrawn 5.2x.
**Defect in the record itself** — the "33 (11/rep)" refusals are 9/14/13 in `quality/rows.jsonl`, and every rep row says `refused_total: 0`, so 33 counts `outcome == refused_by_model`, not a ledger field.
**Blocker:** none. **Gaps left open offline:** no residue-0 warm reading on `:8012` (C1); no compact-unpadded cell E (C5); C4 still open — the `runner.py` repair aborted, 0 of 4 arms completed.
