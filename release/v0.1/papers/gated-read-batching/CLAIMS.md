# CLAIMS.md — every quantitative claim in `MANUSCRIPT.md`, with its source

**Purpose.** Enforce that no number in the manuscript was invented. Every row below is a quantitative or
factual claim made in `papers/gated-read-batching/MANUSCRIPT.md`, traced to a file and line in the source
material. **Rows marked `RE-DERIVED` were recomputed by the authors of this manuscript from the raw per-row data** rather than
read from a summary table; the command is given so the recomputation can be repeated.

**Source paths** are relative to the root of the read-only source material (an external checkout; name and location withheld):

| abbrev | path |
|---|---|
| **G** | `docs/research/GATED_READ_2026.md` (the run report, 340 lines) |
| **R** | `docs/research/gated-read-rows.jsonl` (9,260 per-decision rows; **2,267,742 bytes, 9,260 lines, md5 `3aad1ae29e472ef9f5f54e179510faf5`** — byte-identical across the pinned engine-a tree, the base-repo copy and the live target copy; recorded by UFIXGR7, 2026-10-15). **Dated note (2026-10-19):** the copy *shipped* in paper #7's release package differs from that source measurement in exactly four R5 `answer` values, replaced at equal length by a neutral identifier (`2026-09-28-trace-m0`); 2,267,742 bytes and 9,260 lines are unchanged, and the shipped digest is md5 `93acbf2e5399e9bc42ac7e84a6b5848e` / sha256 `b063fbae534a8e5f6649e6b36a21f12b2c40f95c8b0a36b290ad1adf650de809`. **Dated note (2026-10-19, pass 2):** a case-insensitive sweep found two more rows (`mode=e2e`, `task=T17`) whose `answer` carried the target project's name in uppercase as a 21-character sentinel; they are replaced at equal length by `HOSTED_LAYER_CHECK_OK`. 2,267,742 bytes and 9,260 lines are unchanged; the shipped digest is now md5 `bc2b2a5a36f331a621437cdf328d0d77` / sha256 `e877d05eb3a06069b7cc35b4ffb5fc06e150b6a3b79efd4a9d7f4a3939da47cb`. **Dated note (2026-10-19, pass 3):** the shipped bytes differ from the pinned source measurement in six R5 `answer` values across passes 1-2 **and** in one prose word in `results/GATED_READ_2026.md` (the target project's own name, replaced at equal length by the neutral token `Corpusfile`). 2,267,742 bytes and 9,260 lines are unchanged; the shipped digest is now md5 `20727b5c6bed2db935c14bf2e076340f` / sha256 `184ab747e87f7d127005ce08316dcde640ae93e5278bb1bd57bf353e23d9c44f`. Gap G-23 is closed by this pass. |
| **S** | `docs/research/gated-read-summary.json` (aggregates the harness wrote) |
| **P** | `docs/research/GATED_READ_PROVENANCE.md` (literature provenance + fetched URLs) |

**Recomputation command** (used for every `RE-DERIVED` row) reads `R`, sums `ptok`/`ctok` and counts
`tp`/`fp`/`fn` per `mode`:

```
python3 -c "import json,collections; pt=collections.defaultdict(int); ... for line in open('gated-read-rows.jsonl'): r=json.loads(line) ..."
```

---

## A. Fixture and task definition

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C01 | Corpus size | 90 files | **G:60** | "the corpus: 90 files (docs/, src/, tests/, evals/, examples/, tools/, scripts/ + 4 roots)" |
| C02 | Corpus size on disk | **not reproducible** — measured **2,426,190 B (2.426 MB)** in the pinned snapshot tree / **2,886,664 B (2.753 MB)** live; the recorded **"1.83 MB"** is withdrawn (kept visible for the record) | **G:61** (prose only; no byte record anywhere) | **RE-DERIVED 2026-10-15 by UFIXGR7**: `tasks.json` lists 90 paths with **no size fields**; `os.path.getsize` over those 90 paths gives the two measured totals; no byte record exists for the run date. See GAPS.md G-25. |
| C03 | Number of tasks | 20 | **G:62** | "20 questions with mechanically verified answers" |
| C04 | Answers per task | 1–13 files | **G:62-63** | "every answer hits 1–13 files; zero-miss enforced at fixture build" |
| C05 | Gold label definition | `gold(t,f)` iff *f*'s bytes contain *t*'s answer; recomputed from bytes every run | **G:64-65** | |
| C06 | Evaluation set size | 1,800 (task, file) pairs per configuration | **G:121-122** | "1,800 (task, file) pairs per gate configuration" |
| C07 | Evaluation set is exhaustive | 20 × 90 = 1,800 | arithmetic on **G:60,62** | every task paired with every file |
| C08 | Gold pairs | 120 | **G:122** | "120 gold pairs (6.7 % base rate)" |
| C09 | Gold base rate | 6.7 % | **G:122**; check: 120/1800 = 0.0667 | |
| C10 | Gate input | path + 300-char header + structure outline | **G:66-67** | "The gate never sees file bodies" |
| C11 | Always-`false` accuracy at this base rate | 0.933 | **G:134-135** | "an always-`false` gate scores 0.933" |
| C12 | Decision model | `deepseek-v4-flash`, `reasoning_effort` as labelled | **G:109**; S `models.decision` | |
| C13 | Run control | temperature 0, JSON mode, 8-way concurrency, resumable rows de-duped by `(mode, task, tag)` | **G:110-111** | |
| C14 | Unparsed handling | `pred=null`, counted in `unparsed`, never coerced | **G:112-113** | |

## B. R2 — the batching result (positive)

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C15 | Calls, bs1 `none` | 1,800 | **G:150** | |
| C16 | Calls, bs16 `none` | 120 (15× fewer) | **G:151** | 1800/120 = 15 |
| C17 | Calls, bs90 `none` | 20 (90× fewer) | **G:152** | 1800/20 = 90 |
| C18 | Prompt tokens, bs1 `none` | 631 K | **G:150** | RE-DERIVED: **R** sum `ptok` for `gate1_none` = **631,210** |
| C19 | Prompt tokens, bs16 `none` | 270 K (2.3× fewer) | **G:151** | RE-DERIVED: **R** sum `ptok` for `gate16_none` = **269,614**; S has `prompt_tok_total: null` here — see GAPS.md G-02 |
| C20 | Prompt tokens, bs90 `none` | 261 K (2.4× fewer) | **G:152** | RE-DERIVED: **R** sum `ptok` for `gate90_none` = **261,090**; S has `null` here |
| C21 | Prompt-token reduction ratios | 2.3× and 2.4× | check: 631,210/269,614 = 2.341; 631,210/261,090 = 2.418 | matches **G:154** ">2×" |
| C22 | F1, bs1 `none` | 0.218 | **G:150**; S `gate.gate1_none.f1 = 0.2176` | |
| C23 | F1, bs16 `none` | 0.227 | **G:151**; S `gate.gate16_none.f1 = 0.2268` | |
| C24 | F1, bs90 `none` | 0.211 | **G:152**; S `gate.gate90_none.f1 = 0.2105` | exact 0.210526; the manuscript's 0.210 was a truncation and now prints 0.211 |
| C25 | F1 spread across the three `effort=none` configurations | 0.016 (0.2268 − 0.2105 = 0.0163), within ±0.01 of baseline | derived from **G:150-152**; tolerance asserted at **G:154** ("F1 within ±0.01 of bs1") | |
| C26 | Gate rows and errors | 9,260 rows, 0 call errors, 0 unparsed | **G:119-120**; RE-DERIVED from **R**: mode counts `gate1_none/b16/b90/g90min/b1min = 1800` each, `stage=20`, `router=120`, `e2e=120` → 9,260; `err` null on all gate rows | |
| C27 | Gate rows examined for the batching claim | 9,000 | 5 configurations × 1,800 (**R**) | |
| C28 | bs90 `minimal` completion tokens | 1.69 M | **G:160**; RE-DERIVED **R** sum `ctok` for `gate90_minimal` = **1,690,920** | |
| C29 | bs90 `minimal` total tokens | 1.952 M | **G:132**; RE-DERIVED 261,090 + 1,690,920 = **1,952,010** | |
| C30 | bs90 `minimal` tokens/decision | 1,084 | **G:132**; check 1,952,010/1,800 = 1,084.5 | |
| C31 | bs1 `minimal` tokens/decision | 457 | **G:129**; RE-DERIVED (631,210 + 190,699)/1,800 = 456.6 | |
| C32 | Per-decision cost ratio bs90-min vs bs1-min | 2.4× | **G:160-163** ("2.4× more expensive"); check 1,084.5/456.6 = 2.375 | |
| C33 | F1 bs90 `minimal` vs bs1 `minimal` | 0.299 vs 0.320 | **G:132** and **G:129**; S `gate90_minimal.f1 = 0.2995` | |
| C34 | "8.9× the completion tokens of bs1-minimal" | 1,690,920 / 190,699 = 8.87× | **G:160-162**; RE-DERIVED from **R** | report says "10× the total of bs1-minimal" but the ratio is against bs1-minimal *completion* tokens (190,699), not its total (821,909); the manuscript now prints 8.9×; see GAPS.md G-01 |

## C. R1 — the gate negative result

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C35 | Full R1 table row bs1 `none`: P/R/F1/acc/calls/total tok/tok-per-decision | 0.288 / 0.175 / 0.218 / 0.916 / 1,800 / 642 K / 357 | **G:128** | RE-DERIVED from **R**: P=0.2877, R=0.1750, F1=0.2176; total 631,210+10,800 = 642,010 |
| C36 | Row bs1 `minimal`: 0.284 / 0.367 / 0.320 / 0.896 / 1,800 / 822 K / 457 | as stated | **G:129** | RE-DERIVED: P=0.2839, R=0.3667, F1=0.3200, total 821,909 |
| C37 | Row bs16 `none`: 0.164 / 0.367 / 0.227 / 0.833 / 120 / 290 K / 161 | as stated | **G:130** | RE-DERIVED: P=0.1642, R=0.3667, F1=0.2268, total 289,776 |
| C38 | Row bs90 `none`: 0.192 / 0.233 / 0.211 / 0.883 / 20 / 308 K / 171 | as stated | **G:131** | RE-DERIVED: P=0.1918, R=0.2333, F1=0.2105, total 307,710 |
| C39 | Row bs90 `minimal`: 0.418 / 0.233 / 0.299 / 0.927 / 20 / 1,952 K / 1,084 | as stated | **G:132** | RE-DERIVED: P=0.4179, R=0.2333, F1=0.2995 |
| C40 | Best F1 anywhere | 0.320 | **G:129**, **G:141-142** ("the best F1 is 0.320"); S `gate1_minimal.f1 = 0.32` | |
| C41 | Best precision and its recall | precision 0.418 at recall 0.233 | **G:132**, **G:141-143** | |
| C42 | "drops 3 of 4 gold files" | 1 − 0.233 = 0.767 | **G:142-143** ("silently drops 3 of 4 gold files") | |
| C43 | Effort doubles recall | 0.175 → 0.367 | **G:137**, **G:128-129** | |
| C44 | Effort cost | ~30 % more tokens (642 K → 822 K) | **G:137**; check 821,909/642,010 = 1.280 | |
| C45 | Smoke test: `none` said `false` for a gold file where `minimal` said `true` | one instance, `docs/LAYERS.md` for T01 | **G:138-140** | the file name is corpus metadata; the manuscript cites the observed behaviour, not the path |
| C46 | Preview-depth diagnosis | 500-char header rejected gold files whose answer sat at line 153 | **G:264-266** | |
| C47 | Reasoner-model note | `reasoning_effort=none` is a different classifier, not a cheaper one | **G:267-268** | |
| C48 | Sign tests for the dropped end-to-end arms | p ≥ 0.219 | **G:313** | used only to justify the Section 6 drop |
| C49 | Out-of-scope arms of the same run (R3, R4) | staged shortlist 17/20; router chose `grep` **120/120 row-backed** plus **87 in-end-to-end decisions that have no per-decision rows** (the 120 `e2e` rows carry no `method` field), so the bare **"207/207"** is **derived, not fully recorded** | **G:165-170**, **G:172-175**; S `stage.recall_at_5 = 0.2917`, `tasks_with_any_gold = 17`, `router.method_dist = {grep: 120}` | cited only as "measured but out of scope". **Qualification added 2026-10-15 by UFIXGR7** from the raw-record re-verification. |

## D. Related-work numbers (each double-sourced)

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C50 | BoolQ batched prompt loss | 90.6 % → 72.8 % = −17.8 points at batch size ≥ 64, one round | **P:209-212** | quote and numbers |
| C51 | GSM8K batched prompt loss | 94.9 % → 89.1 % = −5.8 points at batch size 32 | **P:213** | |
| C52 | Range of naive-batching accuracy cost | −4 to −18 points | **P:232** | "−4 to −18 point accuracy cost under naive batching" |
| C53 | Post-repair batching tolerance | within ≈±1.2 points, 9–16 % of LLM calls | **P:216-218** | |
| C54 | Batch Prompting cost case | near-inverse-linear; up to 5× with six samples per batch | **P:196-199**, **P:52** | |
| C55 | BatchPrompt silent-missing failure mode | "15 generated answers when input batch size is 16" | **P:221-222** | |
| C56 | BatchPrompt position sensitivity | performance correlated with positions and order of batched data | **P:205-206**, **P:53** | |
| C57 | Batch coupling | cross-talk risk, not size alone | **P:224-226** | |
| C58 | RouteLLM cost saving | up to 3.66×, threshold-swept | **P:44**, **P:121-122** | |
| C59 | FrugalGPT headline | 98 % cost reduction (or +4 % accuracy at same cost) | **P:45**, **P:122** | |
| C60 | GuardAgent reported accuracies | 98 % and 83 % on two agent benchmarks | **P:37** | |
| C61 | Scaffold taxonomy size | 13 coding-agent scaffolds; 7 context-retrieval strategy types; no per-read binary classifier | **P:47** | |
| C62 | Adaptive-RAG structural precedent | "a classifier, which is a smaller LM" | **P:31**, **P:40 of G** | G:40 = report table row |
| C63 | Toolformer self-supervised call-worth filter | kept iff it reduces next-token loss; cost is not in the decision | **P:25**, **G:38** | |
| C64 | TALM antecedent | arXiv 2205.12255, bootstraps the same objective | **P:26** | |
| C65 | Reference-ID corrections caught by fetching | four wrong recalled arXiv IDs | **P:11-15**, **P:254-256** | evidence the source's citations were fetched, not recalled |
| C66 | URLs actually fetched in the source | a listed set of arXiv/ACL/papers.nips URLs | **P:259-272** | |

---

## E. Operating point under batching (the confusion counts behind the F1 column)

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C67 | Confusion counts, bs1 `none` | tp 21, fp 52, fn 99, tn 1,628 | S `gate.gate1_none.tp/fp/fn/tn`; RE-DERIVED from **R** | |
| C68 | Confusion counts, bs16 `none` | tp 44, fp 224, fn 76, tn 1,456 | S `gate.gate16_none.*`; RE-DERIVED from **R** | |
| C69 | Confusion counts, bs90 `none` | tp 28, fp 118, fn 92, tn 1,562 | S `gate.gate90_none.*`; RE-DERIVED from **R** | |
| C70 | Pairs *admitted* (tp + fp) at bs1 / bs16 / bs90, `none` | 73 / 268 / 146 out of 1,800 | derived from C67–C69 | the operating-point change that F1 hides |
| C71 | Precision and recall move oppositely, bs1 → bs16 `none` | precision 0.288 → 0.164; recall 0.175 → 0.367 | **G:128**, **G:130** | |
| C72 | Confusion counts, bs1 `minimal` | tp 44, fp 111, fn 76 | S `gate.gate1_minimal.*`; RE-DERIVED | |
| C73 | Confusion counts, bs90 `minimal` | tp 28, fp 39, fn 92 | S `gate.gate90_minimal.*`; RE-DERIVED | |

---

## Coverage

- Quantitative claims enumerated: **73 rows** (C01–C73).
- Rows with an explicit `file:line` source: **all 73**; **exact-line accuracy 71/73** (C48 and C65's second locator originally missed the line and are corrected in this revision). Where the source is a JSON file, the row cites
  the exact JSON key path (`S gate.<mode>.<field>`) rather than a line number, because a line number in a
  serialized JSON object is not a stable locator.
- Rows sourced from the run report **G** or its summary **S**: C01–C49, C67–C73.
- Rows sourced from literature provenance **P**: C50–C66.
- Rows independently recomputed by the authors from the raw rows **R**: C18–C20, C26–C29, C31, C34–C39, C67–C73.
- Values that appear in the manuscript but could **not** be traced are listed in `GAPS.md` instead and are
  claimed nowhere.
