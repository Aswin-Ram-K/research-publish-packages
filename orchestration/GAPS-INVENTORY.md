# GAPS-INVENTORY — what stands between this repository and its own stated goals

GAPS-CLASSIFY, 2026-10-25. Derived only from `papers/context-cache/GAPS.md`, `experiments/ptr-engine/RECORD.md`,
`papers/context-cache/FOLD-PROPOSAL.md` and the newest contradiction handoffs. No request sent. 48 gaps, sorted by
class; inside CLOSABLE-OFFLINE the order is what the closure unblocks.

| # | gap (one clause) | source (file:line or handoff key) | class | what closes it |
|---|---|---|---|---|
| 1 | Engine size frozen at the P0.1 count (9 modules, 1896+1222 lines) against a measured 10 modules / 3,653 + 2,248 lines | `RECORD.md:142`; `FOLD-PROPOSAL.md:33` | CLOSABLE-OFFLINE | `wc -l` over `ptr_engine/` and `tests/`, restated with its measurement date |
| 2 | "The engine's tests" is five branch counts (95/100/153/171/108) and no shippable tree | `RECORD.md:124` (C6); `FOLD-PROPOSAL.md:32` | CLOSABLE-OFFLINE | one `python3 -m pytest -q` on today's tree (190 passed / 0.22 s already run) and quote that tree only |
| 3 | `RESULTS.md` still prints the refuted 49,594 two lines from its own 32,401 correction, and `LAW.md` stands as written | `RECORD.md:118` (C3), `:120` (C4) | CLOSABLE-OFFLINE | apply the RECORD's C1/C3 text to `quality/RESULTS.md` and `miss-law/LAW.md` |
| 4 | `FIT-GAP.md` §2 states the 21-row composition wrongly and three units failed to fix it | `RECORD.md:128` (C8) | CLOSABLE-OFFLINE | rewrite §2 from the last 21 lines of `experiments/miss-law/rows.jsonl` |
| 5 | C8's bookkeeping reading is withdrawn, but its substance is re-derivable (outlier 0; 144 nonzero residuals all whole-grid multiples; 83 null rows `uncached == prompt`) | `RECORD.md:130`,`:138`; `C8-REDERIVE`,`C8-304` | CLOSABLE-OFFLINE | re-run the residual/grid predicate over the 774 rows and state the partition as a disjoint sum |
| 6 | G2 calls U4's 438 rows unsalvageable while post-U13 `u4_recon.py` already rebuilds both arms (44/44 head digests, bodies diverge from turn 12) | `GAPS.md:63-73`, `:52-61` | CLOSABLE-OFFLINE | run `cells/CX-V2/u4_recon.py`; replace G2's verdict with the distinct-arm re-derivation |
| 7 | The index leak proof hashes the in-row `index_text`, not a file, so it reads weaker than it is | `FOLD-PROPOSAL.md:28` | CLOSABLE-OFFLINE | hash `index_text` out of `quality/rows.jsonl`; re-print 458 B / 12 lines / `e81ba0…` |
| 8 | The 57.6x understatement exists only as one unit's server replay | `RECORD.md:118`; `FOLD-PROPOSAL.md:42` | CLOSABLE-OFFLINE | root cause is a code reading (`L = prompt_tokens + FRAMING`, `quality/runner.py:467`); recompute the corrected bill from the law |
| 9 | `r = 67.1x` is one corpus sitting *at* the crossover, and 78.3x at 383 B is a single-unit figure | `FOLD-PROPOSAL.md:26`,`:48` | CLOSABLE-OFFLINE | sweep body count and index format through the dependency-free renderer (`tools/rebuild_corpus.py`); print r as a curve |
| 10 | Padding predictions (`r >= 34`, `PAD_FOR_FREE_RESIDUE = 33`) rest on a stub calibrated at base P1 66 against measured 325/386/322 | `RECORD.md:122` (C5); `FOLD-PROPOSAL.md:46` | CLOSABLE-OFFLINE | recalibrate the stub against measured padded cells A/B/D and re-print or withdraw |
| 11 | Two bucket-(i) results (seven negative-control codes; `PTR_WARMPOOL_INSIDE_REPO` refusal) carry no claim | `FOLD-PROPOSAL.md:21-22` | CLOSABLE-OFFLINE | draft C80/C81 from `V-ENGINE-P0.json` checks 6/7 — a claim, not a measurement |
| 12 | PAPER-FINAL wrote the close and nobody adjudicated it, so the closing paragraph is the author's report | `GAPS.md:609-612` (G17) | CLOSABLE-OFFLINE | a fresh verifier unit re-derives the close offline; no request needed |
| 13 | G2's request count (454 claimed vs 451 on disk: 438 batch + 13 probe) is unresolved | `GAPS.md:63-70` | CLOSABLE-OFFLINE | card-to-row reconciliation; record 451 and mark the 3 smoke sends card-only |
| 14 | C1: no residue-0 **warm** `cached_tokens` exists, so 397/77/13 (factor 1–30.5) is undecided | `RECORD.md:114`; `APPLY-C1-VERDICT:next_unit_hint`; `RECON-C1` | NEEDS-LIVE | SGLang `:8012` `/chat/completions`, 3 reps, P1 = 384 (residue 0), L = 13, `cached_reported: true` — 3 requests, 1 cell |
| 15 | C2: the 8.5x penalty is one residue-0 pair; no residue-1 warm row inside controlled cell G6 | `RECORD.md:145` (C2 corrected); `C2-AMEND` | NEEDS-LIVE | vLLM `:8014`, cell G6 at P1 = 7393, 2 reps (joins 7392/7394) — 4 requests |
| 16 | C4: no quality arm completed (9 arm-A rep-0 rows, no `results-corrected.json`), so the arm has no bill and no refusal count | `RECORD.md:120` (C4); `CONTAINMENT-RULING:next_unit_hint` | NEEDS-LIVE | SGLang `:8012`, `runner_v2.py`, 12 rep cells x 4 turns ≈ 48 requests with per-turn `cached_tokens` stored |
| 17 | C5: no compact-UNPADDED cell (cell E) exists, so pad-vs-compact rests on a stub | `RECORD.md:122`; `C5-APPLY:next_unit_hint` | NEEDS-LIVE | SGLang `:8012`, cell E, 3 reps, P1_E and R_E recorded into `measure/rows.jsonl` |
| 18 | The harvested avalanche file is one vLLM profile; nothing on SGLang's B=64 law | `RECORD.md:132` (C9) | NEEDS-LIVE | SGLang `:8012` avalanche arms WINDOW 126 / CEIL 108 / RECOVER 63 / MINIMAL 36 / PP 30 requests |
| 19 | The 141/129 harvest split cannot separate residue from P1, so no residue→avalanche law exists | `RECORD.md:132`; `FOLD-PROPOSAL.md:45` | NEEDS-LIVE | vLLM `:8014`, fixed P1 with residue swept, 3 residues x 3 reps — 9 requests |
| 20 | The ledger's 387/387 is self-consistency (same file's `uncached_tokens`); a second instrument gave 12 exact / 9 off-by-k | `RECORD.md:74`; `FOLD-PROPOSAL.md:29`; `BILL-AUDIT:measure_sample` | NEEDS-LIVE | SGLang `:8012` `/generate` `meta_info.cached_tokens` over ~21–40 rows of the same regime |
| 21 | G3 remainder (i)-(iii): trigger never overran, post-boundary segments are 27–89 turns, no arm compacts to the baseline's window | `GAPS.md:103-119` | NEEDS-LIVE | SGLang `:8012`: overrun-trigger arm + 64k run >48 post-boundary turns + baseline-window arm, ≈150 requests |
| 22 | G3 remainder (iv): no limit-triggered cell on a second engine | `GAPS.md:115`,`:163-166` | NEEDS-LIVE | vLLM `:8014` at 64k, one limit-triggered compaction cell |
| 23 | G4: one band only (no vLLM 64k), one corpus seed (1729), one GPU | `GAPS.md:245-250` | NEEDS-LIVE | vLLM `:8014` 64k battery (4 arms x 71 turns = 284 rows) + a seed-2 corpus on `:8012` (160 requests) |
| 24 | G6: R's ~1,660-token per-turn re-prefill is described, not instrumented — no prefix-diff log, no radix dump | `GAPS.md:291-304` | NEEDS-LIVE | instrument per-turn prefix diffs, re-run U15 (3 arms x 40 turns, `:8012`) |
| 25 | G7: the append deviation's mamba-account has no pure-attention control | `GAPS.md:306-326` | NEEDS-LIVE | replay the 372-append pattern on the dense checkpoint's SGLang cell (DENSE-SGL; port in its cell config) |
| 26 | G8: latency is six lengths and TTFT only; 139 of a planned 200 requests | `GAPS.md:328-338` | NEEDS-LIVE | `:8012`, >=61 more requests, lengths above 31k, plus inter-token and end-to-end timing |
| 27 | G9: n = 5 per length, so the 64-grid boundary rule has no power | `GAPS.md:340-348` | NEEDS-LIVE | `:8012`, n=20 at 960 / 1,152 / 2,048 / 4,096 (~80 requests) + a chunk-insertion trace |
| 28 | G10: the accuracy comparison sits on a 91.6% identical-prompt floor | `GAPS.md:350-360` | NEEDS-LIVE | `:8012`, repeated sampling of the 190 U5 cases + a graded model-judged measure |
| 29 | G11: U15's cheaper arm has no correctness or retention record, and its summariser is a 750-char stub | `GAPS.md:362-387` | NEEDS-LIVE | `:8012`, graded correctness on U15 completions + one re-run with a real summariser |
| 30 | G12: corpora are synthetic and serial; the append arm assumes a cache that never evicts | `GAPS.md:389-405` | NEEDS-LIVE | replay the workspace's real trace on `:8012` with concurrent sessions and a small KV budget |
| 31 | G13: no per-row server build pin and no canary, so a server upgrade is invisible | `GAPS.md:407-416` | NEEDS-LIVE | `:8012`, U2's 44 repeats as a canary (44 requests) |
| 32 | G14: the hybrid arm (append to the limit, then compact) has never been run | `GAPS.md:418-433` | NEEDS-LIVE | U15 harness on `:8012`, hybrid arm x 3 reps, budget below the final window (≈120 requests) |
| 33 | G15: per-break spread and the 81/81 post-compaction window imbalance are unexplained | `GAPS.md:435-444` | NEEDS-LIVE | `:8012`, 2–3 further sessions x 44 turns + prefix-diff logging |
| 34 | G16(a): the HiCache hybrid rejection is unverified for build `0.0.0.dev1+g4ccff141d` | `GAPS.md:530-538` | NEEDS-LIVE | one startup attempt at `--hicache-ratio 2` on `:8012`, then one G5 replay arm |
| 35 | G16(b): one of five documented eviction policies was measured (`slru`, default parameter) | `GAPS.md:492-503` | NEEDS-LIVE | SGLang `:8012`, one `lfu` and one `tlru` arm on the M4/TUNED pressure protocol — 2 cells |
| 36 | G16(c): no vLLM offload tier was ever enabled (`kv_offloading_size="None"` in all four captures) | `GAPS.md:520-526` | NEEDS-LIVE | vLLM `:8014`, one arm at `--kv-offloading-size` >= the GPU KV size |
| 37 | G16(d): the chunked-prefix cell restated the live default, so its null tests nothing | `GAPS.md:546-551` | NEEDS-LIVE | `:8012`, one genuinely different chunked-prefix configuration |
| 38 | Downgrade note: S1/S2/TUNED have no in-cell G0, so their grid rests on a gate that predates their path | `GAPS.md:446-448` | NEEDS-LIVE | one in-cell G0 battery per cell (3 cells) on `:8012` |
| 39 | §8's universal 372/372 append deviation collides with §9e's grid-exact 322–386-token appends | `FOLD-PROPOSAL.md:74` | NEEDS-OPERATOR | operator decides scope vs second regime; **default: scope §8 to 931–12,393-token histories** |
| 40 | Nobody has ratified fold-with-limits or the drafted claim ids C75–C79 | `FOLD-PROPOSAL.md:7`,`:52` | NEEDS-OPERATOR | operator signs off §9e; **default: fold as drafted, five claims** |
| 41 | G17 froze collection; the G3/G4 remainders can only be answered by unfreezing it | `GAPS.md:574-592` | NEEDS-OPERATOR | operator reopens or keeps the freeze; **default: keep it, print G3/G4 as narrowed** |
| 42 | S1/S2/TUNED's grid attribution is downgraded, not retracted | `GAPS.md:446-448` | NEEDS-OPERATOR | operator chooses retract vs downgrade; **default: keep the downgrade note** |
| 43 | The brief's "no measured reason to change any of it" contradicts its own knob-by-knob scope | `GAPS.md:569-572` | NEEDS-OPERATOR | operator edits the sentence; **default: restrict it to the knobs turned** |
| 44 | G4's replication asks for a second endpoint/model, which is a spend decision, not a measurement | `GAPS.md:229-231` | NEEDS-OPERATOR | operator authorises the endpoint; **default: no new endpoint, print the limitation** |
| 45 | C8's 321 "rows of concern" partition cannot be reproduced; its unit record was rewritten to 13 lines and no predicate on disk yields 321 | `RECORD.md:138` | UNCLOSABLE | nothing — the classifying artefact was overwritten; only the record's sentence survives |
| 46 | QUALITY-ARM's standalone index artefact is gone (`/tmp` run roots deleted), so the 458 B hash is over in-row text | `FOLD-PROPOSAL.md:28`; `V-QUALITY-ARM.json` checks[2] | UNCLOSABLE | the bytes were never persisted outside `/tmp`; only the in-row `index_text` is restorable |
| 47 | The "17,552 raw prefix" figure has no field behind it in any row | `RECORD.md:99-101` | UNCLOSABLE | never collected — the only nearby field is `prompt_bytes` (458/9,570/18,630) |
| 48 | A per-turn vLLM TTFT multiple was inferred from a cold `prime` row against a warm `measure` row of a different length | `RECORD.md:145`; `FOLD-PROPOSAL.md:44` | UNCLOSABLE | the pair is a role mismatch by construction and the file has no cross-arm TTFT contrast |

## Bottom line

**Counts: CLOSABLE-OFFLINE 13 · NEEDS-LIVE 25 · NEEDS-OPERATOR 6 · UNCLOSABLE 4 = 48.** Nothing is unclassified.
The three gaps that most block publication: **#1–#4** (the package contradicts its own files on size, suite count and
the bill — a reviewer collects these in round one), **#14/#15/#17** (the three missing live cells that would move
§9e from "with limitation" to "publishable now"), and **#21/#23** (the G3/G4 remainders — the only places the
headline advice still lacks a measured bound at the limit).

Shortest path to a publishable paper:
1. **CLOSABLE-OFFLINE** — apply what is already on disk: engine size and one suite tree (#1, #2), the C1/C3 text to `RESULTS.md`/`LAW.md` (#3), `FIT-GAP.md` §2 (#4), the in-row index hash (#7).
2. **CLOSABLE-OFFLINE** — one re-derivation pass: C8's disjoint partition (#5), `u4_recon.py` for G2 (#6), the r sweep and the recalibrated stub (#9, #10), and the owed verifier of PAPER-FINAL (#12).
3. **NEEDS-LIVE** — one `:8012` batch of ≈6–12 requests: residue-0 warm cell at `P1 = 384` (#14), an SGLang residue-1 cell (C1's residue-1 half), cell E compact-unpadded (#17). Closes C1, C5 and the SGLang avalanche instrument.
4. **NEEDS-LIVE** — one `:8014` cell: G6 residue-1 warm row at `P1 = 7393`, 2 reps (#15), so the 8.5x rests on two residues.
5. **NEEDS-OPERATOR** — ratify fold-with-limits and C75–C79 (#40) and scope §8's 372/372 sentence (#39): these two decisions, not measurements, are what let §9e enter `MANUSCRIPT.md`.
6. **NEEDS-OPERATOR** — keep the G17 freeze and print G3/G4 as narrowed (#41, #21, #23); reopening buys a bound the paper does not need now. Everything else prints as a stated limitation, which is already its status.
