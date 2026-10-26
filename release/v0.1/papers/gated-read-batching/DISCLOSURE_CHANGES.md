# DISCLOSURE_CHANGES.md — UFIX11 correction pass on `papers/gated-read-batching/`

**Unit:** UFIX11 · **Basis:** `strategy/VERIFICATION_REPORT_10.md` (UVER10, `pass-with-corrections`).

**This file did not exist before UFIX11** (`find` over the workspace returned only `papers/encoder-crossover-190/DISCLOSURE_CHANGES.md`), so nothing was overwritten. Every edit is line-local — no line was added or removed — so each cited line number is the same before and after.

**Target `<workspace>` was read only** (4 reads/fetches of source lines and 1 of the source docs); no write, no `git`.

---

## Summary of the four corrections

| correction | status | files / lines | confirmed against the source myself |
|---|---|---|---|
| 1. bs90 `none` F1 0.210 → 0.211; F1 spread 0.017 → 0.016 | **applied** | `MANUSCRIPT.md` 9, 135, 137, 158, 174, 197, 215 (+ derived 30); `CLAIMS.md` C24, C25, C38; `GAPS.md:62` | **yes** — `S gate.gate90_none.f1 = 0.2105` (cited at `CLAIMS.md:58`), exact 0.210526 → 0.211; spread 0.2268 − 0.2105 = 0.0163 → 0.016 |
| 2. Reference 10 title wrong | **applied** | `MANUSCRIPT.md:234`; `REFS.md:50` | **yes** — fetched `https://arxiv.org/abs/2604.03515` myself (HTTP 200): *Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures*, Benjamin Rombaut |
| 3. two `CLAIMS.md` locators wrong; 73/73 overstated | **applied** | `CLAIMS.md` C48, C65, Coverage:131; `MANUSCRIPT.md:127`; `GAPS.md:98` | **yes** — both source lines opened myself (see below); UVER10's replacements are correct |
| 4. "10×"/"ten times" prose never corrected | **applied** | `MANUSCRIPT.md:147, 187`; `CLAIMS.md` C34; `GAPS.md:16` | **yes** — 1,690,920 / 190,699 = **8.867** (8.9×); 1,690,920 / 821,909 = **2.057** (2.1×); total/total 1,952,010 / 821,909 = 2.375× |

**Extra item, resolved (no change):** the `unverified` Toolformer 9th author *Hambro*. arXiv v1 (`arxiv.org/abs/2302.04761`) lists **8** authors with no Hambro; but the **NeurIPS 2023 proceedings page** (`papers.nips.cc/.../d842425e4bf79ba039352da0f658a906-Abstract-Conference.html`, fetched myself, HTTP 200) lists **9**: Schick, Dwivedi-Yu, Dessi, Raileanu, Lomeli, **Eric Hambro**, Zettlemoyer, Cancedda, Scialom. The manuscript cites "NeurIPS 2023; arXiv:2302.04761" and its stated rule is "exactly the set the source material carries" (`P:25` carries Hambro), so the citation is **correct as written and was left unchanged** — `toolformer_hambro_resolved = yes`. The 8-vs-9 discrepancy is arXiv-v1-vs-proceedings, not a fabrication.

---

## Correction 1 — bs90 `none` F1 was truncated (0.210 → 0.211) and the spread was 0.016, not 0.017

Occurrences of **0.210** found (`grep -nE '0\.210'`): `MANUSCRIPT.md:9` (abstract), `:135` (§4.1 table), `:137` (§4.1 prose), `:158` (§4.3 table), `:174` (§4.4 summary table), `:215` (§7), plus `CLAIMS.md:58` (C24), `:77` (C38) and `GAPS.md:62` (G-08) — **all nine updated**. Occurrences of the spread **0.017**: `MANUSCRIPT.md:9, :137, :197` and `CLAIMS.md:59` (C25) — **all four updated to 0.016**.

**`MANUSCRIPT.md:9`** — C1 abstract: 0.210→0.211, spread 0.017→0.016

```text
BEFORE: We measure a **binary file-read gate**: a small decision model that answers `{"relevant": true|false}` for a proposed read of file *f* for task *t* with stated purpose *p*, conditioned only on the question, the purpose, the file path, a short header and a structure outline — never on the file body. On 1,800 (task, file) pairs drawn from a 90-file corpus and 20 tasks, we test whether those per-read decisions can be batched. Batching 16 or 90 decisions into a single request at `reasoning_effort=none` reduces the number of decision calls from 1,800 to 120 and 20 (15× and 90×) and prompt tokens from 631 K to 270 K and 261 K (2.3× and 2.4×) while F1 moves from 0.218 to 0.227 and 0.210 — a spread of 0.017, within ±0.01 of the single-decision baseline. On this task, corpus and decision model, batching binary gate decisions at `effort=none` did not measurably degrade decision quality. This is a narrower claim than "batching is free": published batch-prompting losses on question answering and natural-language inference are large (−4 to −18 points; e.g. BoolQ 90.6 % → 72.8 %, −17.8, at batch size ≥ 64 without repair), and the present result is a measured exception on one task shape, not a refutation.
AFTER:  We measure a **binary file-read gate**: a small decision model that answers `{"relevant": true|false}` for a proposed read of file *f* for task *t* with stated purpose *p*, conditioned only on the question, the purpose, the file path, a short header and a structure outline — never on the file body. On 1,800 (task, file) pairs drawn from a 90-file corpus and 20 tasks, we test whether those per-read decisions can be batched. Batching 16 or 90 decisions into a single request at `reasoning_effort=none` reduces the number of decision calls from 1,800 to 120 and 20 (15× and 90×) and prompt tokens from 631 K to 270 K and 261 K (2.3× and 2.4×) while F1 moves from 0.218 to 0.227 and 0.211 — a spread of 0.016, within ±0.01 of the single-decision baseline. On this task, corpus and decision model, batching binary gate decisions at `effort=none` did not measurably degrade decision quality. This is a narrower claim than "batching is free": published batch-prompting losses on question answering and natural-language inference are large (−4 to −18 points; e.g. BoolQ 90.6 % → 72.8 %, −17.8, at batch size ≥ 64 without repair), and the present result is a measured exception on one task shape, not a refutation.
```

**`MANUSCRIPT.md:30`** — C1 derived knock-on: 0.218−0.211=0.007

```text
BEFORE: - A **measured batching result** for binary gate decisions: 1,800 → 20 calls (90×) and 631 K → 261 K prompt tokens (2.4×) at a 0.008 F1 change relative to the single-decision baseline, at `effort=none` (Section 4.1).
AFTER:  - A **measured batching result** for binary gate decisions: 1,800 → 20 calls (90×) and 631 K → 261 K prompt tokens (2.4×) at a 0.007 F1 change relative to the single-decision baseline, at `effort=none` (Section 4.1).
```

**`MANUSCRIPT.md:135`** — C1 §4.1 table

```text
BEFORE: | bs90, `none` | 20 (**90× fewer**) | 261 K (2.4× fewer) | 0.210 |
AFTER:  | bs90, `none` | 20 (**90× fewer**) | 261 K (2.4× fewer) | 0.211 |
```

**`MANUSCRIPT.md:137`** — C1 §4.1 prose + spread

```text
BEFORE: At `reasoning_effort=none`, batching 16 or 90 binary JSON decisions into one request loses **nothing measurable** on this task: F1 is 0.218, 0.227 and 0.210, a total spread of 0.017 and within ±0.01 of the single-decision baseline. Meanwhile the call count falls 15× and then 90×, and prompt tokens fall 2.3× and 2.4×. Re-derived from the raw rows, the prompt-token totals are 631,210 / 269,614 / 261,090, matching the rounded 631 K / 270 K / 261 K; all five gate configurations report zero errors and zero unparsed decisions across 9,000 gate rows.
AFTER:  At `reasoning_effort=none`, batching 16 or 90 binary JSON decisions into one request loses **nothing measurable** on this task: F1 is 0.218, 0.227 and 0.211, a total spread of 0.016 and within ±0.01 of the single-decision baseline. Meanwhile the call count falls 15× and then 90×, and prompt tokens fall 2.3× and 2.4×. Re-derived from the raw rows, the prompt-token totals are 631,210 / 269,614 / 261,090, matching the rounded 631 K / 270 K / 261 K; all five gate configurations report zero errors and zero unparsed decisions across 9,000 gate rows.
```

**`MANUSCRIPT.md:158`** — C1 §4.3 table

```text
BEFORE: | bs90, `none` | 0.192 | 0.233 | **0.210** | 0.883 | 20 | 308 K | 171 |
AFTER:  | bs90, `none` | 0.192 | 0.233 | **0.211** | 0.883 | 20 | 308 K | 171 |
```

**`MANUSCRIPT.md:174`** — C1 §4.4 summary table

```text
BEFORE: | **R2** | does batching 16–90 binary gate decisions at `effort=none` degrade them? | no measurable degradation on this task (F1 0.218 → 0.227 → 0.210; calls 1,800 → 120 → 20; prompt tokens 631 K → 270 K → 261 K) | single model, single corpus, 1,800 pairs/configuration, 0 errors |
AFTER:  | **R2** | does batching 16–90 binary gate decisions at `effort=none` degrade them? | no measurable degradation on this task (F1 0.218 → 0.227 → 0.211; calls 1,800 → 120 → 20; prompt tokens 631 K → 270 K → 261 K) | single model, single corpus, 1,800 pairs/configuration, 0 errors |
```

**`MANUSCRIPT.md:197`** — C1 §6 spread

```text
BEFORE: **No significance test on the batching delta.** "Within ±0.01" is a descriptive tolerance chosen before writing, not a pre-registered non-inferiority margin, and no null hypothesis is tested against the F1 differences. With 1,800 pairs the per-point sampling error is not negligible; the honest statement is that the observed F1 spread (0.017 across the three `effort=none` configurations) is small relative to anything the literature calls a batching loss, and that a formal non-inferiority test was not run.
AFTER:  **No significance test on the batching delta.** "Within ±0.01" is a descriptive tolerance chosen before writing, not a pre-registered non-inferiority margin, and no null hypothesis is tested against the F1 differences. With 1,800 pairs the per-point sampling error is not negligible; the honest statement is that the observed F1 spread (0.016 across the three `effort=none` configurations) is small relative to anything the literature calls a batching loss, and that a formal non-inferiority test was not run.
```

**`MANUSCRIPT.md:215`** — C1 §7 conclusion

```text
BEFORE: Batching binary read-gate decisions 16- and 90-way at `reasoning_effort=none` did not measurably degrade them on this fixture: F1 moved from 0.218 to 0.227 and 0.210 while calls fell from 1,800 to 120 and 20 and prompt tokens fell from 631 K to 270 K and 261 K, with zero unparsed decisions and zero call errors. As a statement about batching, this is deliberately narrow — a measured exception to the −4 to −18 point losses reported for batched QA/NLI prompting, on one task shape, one corpus and one decision model; not a general licence to batch.
AFTER:  Batching binary read-gate decisions 16- and 90-way at `reasoning_effort=none` did not measurably degrade them on this fixture: F1 moved from 0.218 to 0.227 and 0.211 while calls fell from 1,800 to 120 and 20 and prompt tokens fell from 631 K to 270 K and 261 K, with zero unparsed decisions and zero call errors. As a statement about batching, this is deliberately narrow — a measured exception to the −4 to −18 point losses reported for batched QA/NLI prompting, on one task shape, one corpus and one decision model; not a general licence to batch.
```

**`CLAIMS.md:58`** — C1 C24

```text
BEFORE: | C24 | F1, bs90 `none` | 0.210 | **G:152**; S `gate.gate90_none.f1 = 0.2105` | |
AFTER:  | C24 | F1, bs90 `none` | 0.211 | **G:152**; S `gate.gate90_none.f1 = 0.2105` | exact 0.210526; the manuscript's 0.210 was a truncation and now prints 0.211 |
```

**`CLAIMS.md:59`** — C1 C25

```text
BEFORE: | C25 | F1 spread across the three `effort=none` configurations | 0.017, within ±0.01 of baseline | derived from **G:150-152**; tolerance asserted at **G:154** ("F1 within ±0.01 of bs1") | |
AFTER:  | C25 | F1 spread across the three `effort=none` configurations | 0.016 (0.2268 − 0.2105 = 0.0163), within ±0.01 of baseline | derived from **G:150-152**; tolerance asserted at **G:154** ("F1 within ±0.01 of bs1") | |
```

**`CLAIMS.md:77`** — C1 C38

```text
BEFORE: | C38 | Row bs90 `none`: 0.192 / 0.233 / 0.210 / 0.883 / 20 / 308 K / 171 | as stated | **G:131** | RE-DERIVED: P=0.1918, R=0.2333, F1=0.2105, total 307,710 |
AFTER:  | C38 | Row bs90 `none`: 0.192 / 0.233 / 0.211 / 0.883 / 20 / 308 K / 171 | as stated | **G:131** | RE-DERIVED: P=0.1918, R=0.2333, F1=0.2105, total 307,710 |
```

**`GAPS.md:62`** — C1 G-08 sync

```text
BEFORE: at nearly equal F1 (0.218 / 0.227 / 0.210). The manuscript reports this (Section 4.1) but cannot say which
AFTER:  at nearly equal F1 (0.218 / 0.227 / 0.211). The manuscript reports this (Section 4.1) but cannot say which
```

**Confirmations I ran myself (not taken from UVER10)** — the first five are the correction-1/2 source facts, the rest are the correction-3 locator checks:

- `G:313 contains 'p≥0.219'`: **YES**
- `G:211-213 contains NO '0.219'`: **YES**
- `G:211-213 states 'not significant'/'coin flip'`: **YES**
- `P:254-256 contains 'Recalled-ID corrections'`: **YES**
- `P:247-249 is the Self-RAG venue + [INFERENCE] bullets, with no Recalled-ID paragraph`: **YES** (the Self-RAG venue bullet opens at `P:246` and runs into `:247`; `P:248-249` is the `[INFERENCE]` bullet; `Recalled-ID corrections` appears only at `P:254`)
- `P:11-16 carries all four originally-wrong IDs`: **YES**
- `S gate.gate90_none.f1` (= 0.2105) is the exact value cited by the package itself at `CLAIMS.md:58`; `GATED_READ_2026.md:152` prints the truncated 0.210.

- Derived arithmetic: `0.21756 − 0.21053 = 0.00703` → the contribution bullet's F1 change is **0.007**, not 0.008 (the 0.008 was computed from the un-truncated 0.210 and becomes stale once 0.211 is printed). This is a knock-on of correction 1, not a fifth correction; flagged here for the reviewer.


## Correction 2 — Reference 10's title

Cited as *"Inside the Scaffold: A Source-Code Taxonomy of 13 Coding-Agent Scaffolds"*; the record is *"…Taxonomy of Coding Agent Architectures"*. "13 scaffolds" is in the abstract, not the title.

**`MANUSCRIPT.md:234`** — C2 ref 10 title

```text
BEFORE: 10. Rombaut (2026). *Inside the Scaffold: A Source-Code Taxonomy of 13 Coding-Agent Scaffolds.* arXiv:2604.03515.
AFTER:  10. Rombaut (2026). *Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures.* arXiv:2604.03515.
```

**`REFS.md:50`** — C2 B9 title

```text
BEFORE: | B9 | Rombaut — *Inside the Scaffold: A Source-Code Taxonomy of 13 Coding-Agent Scaffolds* | arXiv:2604.03515 | **P:47**, URL `arxiv.org/abs+html/2604.03515` at **P:269** | VERIFIED-in-source |
AFTER:  | B9 | Rombaut — *Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures* | arXiv:2604.03515 | **P:47**, URL `arxiv.org/abs+html/2604.03515` at **P:269** | VERIFIED-in-source |
```

**Confirmed myself:** `web_fetch https://arxiv.org/abs/2604.03515` → HTTP 200, "Title:Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures", author Benjamin Rombaut. The cited claim (13 open-source scaffolds; seven context-compaction strategies) is in that abstract, so only the title wording was wrong.

**The wrong title is carried by the source, not invented here.** Occurrences of the string in the read-only target:

- `GATED_READ_PROVENANCE.md:47` — | **Inside the Scaffold** — Rombaut (P: arXiv 2604.03515) | 2026 | Source-code taxonomy of **13 coding-agent scaffolds**; §4.2.4 gives 7 context-retrieval strategy types: keyword/regex (SWE-agent, OpenHands, Codex CLI, Gemini CLI, Cline, mini-swe-agent, DARS-Agent, OpenCode), repo map (Aider), AST search (AutoCodeRover…), knowledge graph (Prometheus), embeddings (Moatless — "the only agent with embedding-based retrieval as an LLM-callable tool"), hierarchical localization (Agentless), fault localization | **The strongest evidence for the gap:** file relevance is decided by search/rank/retrieval machinery or by free LLM tool choice — no per-read binary classifier anywhere in the 13 |

**The source document was NOT edited** (it is outside UFIX11's write paths and is a record). The wrong title therefore **still stands in the source**; it is corrected only in this package.

Note: the unit card named `GATED_READ_2026.md:47`; the actual carrier is `GATED_READ_PROVENANCE.md:47` (the row `P:47` that `CLAIMS.md` C61 and `REFS.md` B9 both cite). The card's file name appears to be a slip; no edit was made to either source file.


## Correction 3 — two wrong `CLAIMS.md` locators, and the 73/73 claim

I opened both replacement locations **and** both original locations myself before editing:

- `G:313 contains 'p≥0.219'`: **YES**
- `G:211-213 contains NO '0.219'`: **YES**
- `G:211-213 states 'not significant'/'coin flip'`: **YES**
- `P:254-256 contains 'Recalled-ID corrections'`: **YES**
- `P:247-249 is the Self-RAG venue + [INFERENCE] bullets, with no Recalled-ID paragraph`: **YES** (the Self-RAG venue bullet opens at `P:246` and runs into `:247`; `P:248-249` is the `[INFERENCE]` bullet; `Recalled-ID corrections` appears only at `P:254`)
- `P:11-16 carries all four originally-wrong IDs`: **YES**
- The four wrong IDs are stated at `P:12`, `P:13`, `P:14` and `P:51` (so the `P:11-15` locator does contain three of them; the remaining occurrences at `P:254`, `P:255` and `P:272` are the correction log itself), and the second C65 locator `P:247-249` does not contain them - hence the repoint to `P:254-256`.

UVER10's replacements are **correct**; nothing needed to be sent back as an error in the replacement itself.

**`MANUSCRIPT.md:127`** — C3 soften 73/73 in the manuscript

```text
BEFORE: All figures below come from the 2026-09-30 run. Every quantitative statement is traced to a source file and line in `CLAIMS.md`; where a figure could only be re-derived from the raw rows rather than read from the summary, that is stated.
AFTER:  All figures below come from the 2026-09-30 run. Every quantitative statement is traced to a source file and line in `CLAIMS.md` (exact-line accuracy 71/73; two locators — C48 and C65's second — were repointed to the exact line in a correction pass); where a figure could only be re-derived from the raw rows rather than read from the summary, that is stated.
```

**`CLAIMS.md:87`** — C3 C48 locator

```text
BEFORE: | C48 | Sign tests for the dropped end-to-end arms | p ≥ 0.219 | **G:211-213** | used only to justify the Section 6 drop |
AFTER:  | C48 | Sign tests for the dropped end-to-end arms | p ≥ 0.219 | **G:313** | used only to justify the Section 6 drop |
```

**`CLAIMS.md:109`** — C3 C65 second locator

```text
BEFORE: | C65 | Reference-ID corrections caught by fetching | four wrong recalled arXiv IDs | **P:11-15**, **P:247-249** | evidence the source's citations were fetched, not recalled |
AFTER:  | C65 | Reference-ID corrections caught by fetching | four wrong recalled arXiv IDs | **P:11-15**, **P:254-256** | evidence the source's citations were fetched, not recalled |
```

**`CLAIMS.md:131`** — C3 soften coverage claim

```text
BEFORE: - Rows with an explicit `file:line` source: **all** (73/73). Where the source is a JSON file, the row cites
AFTER:  - Rows with an explicit `file:line` source: **all 73**; **exact-line accuracy 71/73** (C48 and C65's second locator originally missed the line and are corrected in this revision). Where the source is a JSON file, the row cites
```

**`GAPS.md:98`** — C3 G-13 locator sync

```text
BEFORE:    records sign tests at p ≥ 0.219, i.e. coin flips (`GATED_READ_2026.md:211-213`).
AFTER:     records sign tests at p ≥ 0.219, i.e. coin flips (`GATED_READ_2026.md:313`).
```

**Softening of the blanket claim.** `CLAIMS.md` Coverage said "Rows with an explicit `file:line` source: **all** (73/73)"; the true exact-line accuracy is **71/73** (C48 and C65's second locator were off). The manuscript repeats the substance at `MANUSCRIPT.md:127` ("Every quantitative statement is traced to a source file and line in `CLAIMS.md`") and that line is softened to state 71/73. `GAPS.md:98` carried the same wrong `G:211-213` pointer and is repointed to `G:313` so the package has no known-wrong locator left.


## Correction 4 — the "10×" factor in the prose

The true factors: `1,690,920 / 190,699 = 8.867` → **8.9×** the bs1-minimal **completion** tokens; `1,690,920 / 821,909 = 2.057` → **2.1×** bs1-minimal **total**; and bs90-minimal total ÷ bs1-minimal total = `1,952,010 / 821,909 = 2.375` → **2.4×** (already stated correctly in the source at `:163` and in `CLAIMS.md` C32). The source sentence conflated the denominators; the prose now prints **8.9×**.

**`MANUSCRIPT.md:147`** — C4 prose factor

```text
BEFORE: The batching result is specific to `effort=none`, and the same table shows why that qualifier is not cosmetic. The `bs90 × minimal` configuration consumes **1.69 M completion tokens** — ten times the completion tokens of the `bs1 × minimal` configuration — because the model reasons over all 90 files in each call. Its total is **1.952 M tokens**, or **1,084 tokens per decision**, against **457 per decision** for `bs1 × minimal`: batching multiplies thinking cost, it does not amortise it, when extended reasoning is switched on. And it does so while scoring *lower*: F1 0.299 at bs90/minimal versus 0.320 at bs1/minimal.
AFTER:  The batching result is specific to `effort=none`, and the same table shows why that qualifier is not cosmetic. The `bs90 × minimal` configuration consumes **1.69 M completion tokens** — 8.9× the completion tokens of the `bs1 × minimal` configuration — because the model reasons over all 90 files in each call. Its total is **1.952 M tokens**, or **1,084 tokens per decision**, against **457 per decision** for `bs1 × minimal`: batching multiplies thinking cost, it does not amortise it, when extended reasoning is switched on. And it does so while scoring *lower*: F1 0.299 at bs90/minimal versus 0.320 at bs1/minimal.
```

**`MANUSCRIPT.md:187`** — C4 §5 prose factor

```text
BEFORE: **Effort is a design variable, not a knob.** The recall doubling from `none` to `minimal` — and the 10× completion-token blow-up when those extra tokens are spent over 90 files per call — together say that `reasoning_effort` changes what classifier you have, not merely what it costs. Any comparison across configurations must pin effort, as this run does.
AFTER:  **Effort is a design variable, not a knob.** The recall doubling from `none` to `minimal` — and the 8.9× completion-token blow-up when those extra tokens are spent over 90 files per call — together say that `reasoning_effort` changes what classifier you have, not merely what it costs. Any comparison across configurations must pin effort, as this run does.
```

**`CLAIMS.md:68`** — C4 C34 quote/value sync

```text
BEFORE: | C34 | "10× the completion tokens of bs1-minimal" | 1,690,920 / 190,699 = 8.9× ≈ 10× | **G:160-162**; RE-DERIVED from **R** | report says "10× the total of bs1-minimal" but the ratio is against bs1-minimal *completion* tokens (190,699), not its total (821,909); see GAPS.md G-01 |
AFTER:  | C34 | "8.9× the completion tokens of bs1-minimal" | 1,690,920 / 190,699 = 8.87× | **G:160-162**; RE-DERIVED from **R** | report says "10× the total of bs1-minimal" but the ratio is against bs1-minimal *completion* tokens (190,699), not its total (821,909); the manuscript now prints 8.9×; see GAPS.md G-01 |
```

**`GAPS.md:16`** — C4 G-01 sync

```text
BEFORE: therefore says "ten times the completion tokens" and carries the recomputed ratio here rather than repeating
AFTER:  therefore says "8.9× the completion tokens" (corrected from "ten times" in the UFIX11 correction pass) and carries the recomputed ratio here rather than repeating
```


## Files, md5 before/after, word count

| file | md5 before | md5 after | changed |
|---|---|---|---|
| `MANUSCRIPT.md` | `f9118b2f9ada553d3c9df6e7b440e23f` | `137d83c9c803c8d9a0aa99025927f063` | yes |
| `CLAIMS.md` | `62ae942361d52f1c53ef17d6728aa4d7` | `374e5ce4e1fecd9b50db06e4343fd767` | yes |
| `REFS.md` | `970055a163a7e165428d3651c7b7a560` | `7a3ac71b321a95c12837174e4be45452` | yes |
| `GAPS.md` | `171ee4471650e2372e66560cbe0d74b7` | `0862ae005158bce2806a5c621d9d4fff` | yes |

- `MANUSCRIPT.md` md5 before `f9118b2f9ada553d3c9df6e7b440e23f` (matches the value in the unit card and in `VERIFICATION_REPORT_10.md` §6) → after `137d83c9c803c8d9a0aa99025927f063`.
- **Word count (`wc -w`): `MANUSCRIPT.md` 5193 before → 5213 after.** UVER10 measured 5,193 (reproduced before editing).

## Disclosure grep (re-run on the edited files, before and after)

Patterns: `<workspace>`, `duval` (case-insensitive), the target project's own name, `a5ef1b28`, `89003e70`, `publish-present-compete`, `\b[0-9a-f]{8,}\b` (hex ID).

| file | hits before | hits after |
|---|---|---|
| `MANUSCRIPT.md` | 0 | 0 |
| `CLAIMS.md` | 2 | 2 |
| `REFS.md` | 2 | 2 |
| `GAPS.md` | 0 | 0 |

**No edit introduced a disclosure string** (hit counts are identical before and after on every file): true.

- `CLAIMS.md` pre-existing hits, unchanged by this pass: ['<workspace>', 'duval']
  - `CLAIMS.md:8` [<workspace>] — **Source paths** are relative to the read-only target root `<workspace>`:
  - `CLAIMS.md:8` [duval] — **Source paths** are relative to the read-only target root `<workspace>`:
- `REFS.md` pre-existing hits, unchanged by this pass: ['<workspace>', 'duval']
  - `REFS.md:12` [<workspace>] — read-only target root `<workspace>`, in particular its §1 master table (`P:23-56`), its §4 batching
  - `REFS.md:12` [duval] — read-only target root `<workspace>`, in particular its §1 master table (`P:23-56`), its §4 batching

---

## Pass 2 (UFIX11 follow-up) — package-wide disclosure sweep and neutralisation

**Scope.** The WHOLE directory `papers/gated-read-batching/`, not only the four files edited in pass 1. Files
present: `CLAIMS.md`, `GAPS.md`, `MANUSCRIPT.md`, `REFS.md`, `DISCLOSURE_CHANGES.md`. The follow-up named
`CHECKLIST.md`, `OPEN_QUESTIONS.md`, `REFERENCES.bib` and `README*` — none of those exist in this package.

**Patterns.** `<workspace>`, `/home/`, `/Users/`, `/mnt/`, `/opt/`, `duval` (case-insensitive) and the target project's own name (case-insensitive),
`a5ef1b28`, `89003e70`, `publish-present-compete`, `Aswin-Ram-K`, `github.com/Aswin`, `UVER`, `UPAPER`, `UFIX`,
`StateClass`, `grantPolicy`, `expanded[`, `admit(`, and any hex run `[0-9a-f]{8,}`.

### Sweep table — hits per file, before → after

| file | before | after | where | outcome |
|---|---|---|---|---|
| `MANUSCRIPT.md` | 0 | 0 | — | clean |
| `CLAIMS.md` | 3 | **0** | 1 line (3 patterns on `CLAIMS.md:8`) | neutralised |
| `REFS.md` | 4 | **0** | 1 line (3 patterns on `REFS.md:12`) + `UPAPER7` at `REFS.md:17` | neutralised |
| `GAPS.md` | 1 | **0** | `UFIX11` at `GAPS.md:16` | neutralised |
| `DISCLOSURE_CHANGES.md` | 52 | 52 (pre-append) | this change log | **flagged, not scrubbed** (see below) |
| **total** | **60** | **52** (all remaining in this log) | | |

Zero hits anywhere for: the target project's own name (both cases), `a5ef1b28`, `89003e70`, `publish-present-compete`,
`Aswin-Ram-K`, `github.com/Aswin`, `StateClass`, `grantPolicy`, `expanded[`, `admit(`, `/Users/`, `/mnt/`, `/opt/`.
No absolute path of any kind is left outside this log.

### Fixed — verbatim before/after

**`CLAIMS.md:8`**

```text
BEFORE: **Source paths** are relative to the read-only target root `<workspace>`:
AFTER:  **Source paths** are relative to the root of the read-only source material (an external checkout; name and location withheld):
```

**`REFS.md:12`**

```text
BEFORE: read-only target root `<workspace>`, in particular its §1 master table (`P:23-56`), its §4 batching
AFTER:  read-only source material (an external checkout; name and location withheld), in particular its §1 master table (`P:23-56`), its §4 batching
```

**`REFS.md:17`**

```text
BEFORE: ## Tier A — re-verified by unit UPAPER7 in this session (2 refs)
AFTER:  ## Tier A — re-verified for this manuscript in this session (2 refs)
```

**`GAPS.md:16`**

```text
BEFORE: therefore says "8.9× the completion tokens" (corrected from "ten times" in the UFIX11 correction pass) and carries the recomputed ratio here rather than repeating
AFTER:  therefore says "8.9× the completion tokens" (corrected from "ten times" in a later correction pass) and carries the recomputed ratio here rather than repeating
```

### Flagged, NOT fixed (ambiguity for the reviewer rather than a guess)

1. **`DISCLOSURE_CHANGES.md` (this file) — 52 hits, left intact.** It carries `UFIX11`, `UVER10`,
   `strategy/VERIFICATION_REPORT_10.md`, five md5 hex digests and the target root path. Every one of those is the
   audit trail this deliverable exists to carry (the unit card requires verbatim before/after, md5s and the
   source of each correction), so scrubbing it would destroy reviewability rather than protect anything.
   **Recommendation:** exclude `DISCLOSURE_CHANGES.md` from any shipped subset, the way
   `repro/encoder-crossover-190-SANITISED/EXCLUDED.md` excludes internal artifacts — do not scrub it.
2. **Generic process nouns, not named identifiers** — `CLAIMS.md:5` ("recomputed by this unit"),
   `REFS.md:4` ("re-verified by this unit in this session"), `REFS.md:11` ("Source of all non-unit
   verification"). These say "unit" without naming one, and the word is doing real work (it separates
   the author's own checks from the source's). Not changed. If the reviewer wants them gone, the proposed
   wording is "by the authors of this manuscript" / "independent of the source material" — a meaning
   choice, not a redaction, hence flagged rather than guessed.
3. **Source-document filenames** (`GATED_READ_2026.md`, `GATED_READ_PROVENANCE.md`, `gated-read-rows.jsonl`,
   `gated-read-summary.json`) are named throughout `CLAIMS.md`/`REFS.md`/`GAPS.md` as the provenance
   abbreviations **G/P/R/S**. They are not workspace paths and are not in the pattern set, but they ARE the
   citation targets — deleting them breaks every locator in the package. Flagged for the reviewer in case the
   shipped subset must not name the internal source documents; that is a traceability redesign, out of scope here.

**Neutralisation convention** follows the one already recorded in `repro/encoder-crossover-190-SANITISED/SCRUB_REPORT.md`
(rule R9 / the `AVAILABILITY.md` precedent): keep the provenance fact, withhold the name —
"an external checkout; name and location withheld".

### After this pass

- `wc -w MANUSCRIPT.md` = **5213** (unchanged from pass 1: this pass touched no manuscript prose).
- md5 after: `MANUSCRIPT.md` `137d83c9c803c8d9a0aa99025927f063`, `CLAIMS.md` `2392ccafd6f32a4c7039a373fdeb1a3b`, `REFS.md` `917a31f43f0e30e7d268cc94ca147916`, `GAPS.md` `8e38d394a149685c0680215bd6079876`.
- Re-sweep after editing: every pattern above is 0-hit in the four traceability/manuscript files; the only
  remaining hits in the directory are the 52 (now more) in this log.

---

## Pass 3 (UFIX11 follow-up) — internal process nouns removed

The three flagged (b) wording fixes, plus the one same-class occurrence on the same page (`REFS.md:9`) that
would otherwise have contradicted them. Truth was checked for each before the edit: every sentence stays
true after the change and none of them needed a unit name.

**Constraint honoured:** the `G/P/R/S` source-document filenames were NOT touched (they are the citation
targets, and their shipment is UCURATE1's call), and nothing inside this log was edited except this appended
section.

### Fixed — verbatim before/after

**`CLAIMS.md:5`**

```text
BEFORE: material. **Rows marked `RE-DERIVED` were recomputed by this unit from the raw per-row data** rather than
AFTER:  material. **Rows marked `RE-DERIVED` were recomputed by the authors of this manuscript from the raw per-row data** rather than
```

**`REFS.md:4`**

```text
BEFORE: is either (a) re-verified by this unit in this session, (b) verified by *direct fetch* in the source material
AFTER:  is either (a) re-verified by the authors of this manuscript during preparation, (b) verified by *direct fetch* in the source material
```

**`REFS.md:9`**

```text
BEFORE: **Verification date for this unit's own checks:** 2026-10-15 (UTC).
AFTER:  **Verification date for the authors' own checks:** 2026-10-15 (UTC).
```

**`REFS.md:11`**

```text
BEFORE: **Source of all non-unit verification:** `docs/research/GATED_READ_PROVENANCE.md` (abbreviated **P**) in the
AFTER:  **Source of the verification not performed by the authors:** `docs/research/GATED_READ_PROVENANCE.md` (abbreviated **P**) in the
```

### Note on the third replacement

The pass-3 instruction proposed "Source of all non-unit verification" -> "independent of the source material".
That phrase would **invert this line's meaning**: the line names where the verification the authors did *not*
perform themselves comes from (the source document **P**). "Independent of the source material" describes the
authors' own checks — the opposite set. Replaced instead with the meaning-preserving "Source of the verification
not performed by the authors:".

### After this pass

- The same 20-pattern sweep as pass 2: **0 hits** in `MANUSCRIPT.md`, `CLAIMS.md`, `REFS.md`, `GAPS.md` before and
  after this pass (the three edits removed process nouns, not pattern hits); the only hits in the directory remain
  the ones inside this log, which is excluded from the package by UCURATE1's decision.
- Residual occurrences of the bare word "unit"/"units" in the four shipped files after this pass: **13**.
- md5: `CLAIMS.md` `926111ad608180625613d45d177036c4`, `REFS.md` `027dce391c6d0db86951b0dbe165e7c5`, `GAPS.md` `8e38d394a149685c0680215bd6079876`, `MANUSCRIPT.md` `137d83c9c803c8d9a0aa99025927f063` (unchanged), this log `pending append`.
- `wc -w MANUSCRIPT.md` = **5213** (unchanged — pass 3 touched no manuscript prose).

---

## Pass 3b — the same class of noun, in the remaining files

Pass 3 fixed the three requested lines and reported 13 residual occurrences of the bare word "unit". Seven of
those were the same internal-actor reference and are fixed here; the earlier "13" is superseded by the residual
list below. Nothing outside `papers/gated-read-batching/**` was touched. (The first attempt at this section
crashed after writing the edits but before appending this log; the seven edits are confirmed present above and
their verbatim before/after is reconstructed from the same lines, which is why they are exact.)

### Fixed — verbatim before/after

**`CLAIMS.md`**

```text
BEFORE: - Rows independently recomputed by this unit from the raw rows **R**: C18–C20, C26–C29, C31, C34–C39, C67–C73.
AFTER:  - Rows independently recomputed by the authors from the raw rows **R**: C18–C20, C26–C29, C31, C34–C39, C67–C73.
```

**`GAPS.md`**

```text
BEFORE: (`tag`/`file` → `f001…f0NN` with a withheld key) before release. This unit did not perform that rename — it
AFTER:  (`tag`/`file` → `f001…f0NN` with a withheld key) before release. The authors did not perform that rename — it
```

**`GAPS.md`**

```text
BEFORE: ## 6. Gaps this unit hit in its own production process
AFTER:  ## 6. Gaps the authors hit in producing this package
```

**`GAPS.md`**

```text
BEFORE: | G-21 | `papers/gated-read-batching/` was created by this unit; there was no prior manuscript to review, only the run report. | Sections 1, 2, 5, 6 and 7 are newly authored reasoning, not edited source text. They contain no new numbers, but their framing is this unit's, and a verifier should test the framing separately from the numbers. |
AFTER:  | G-21 | `papers/gated-read-batching/` was created by the authors; there was no prior manuscript to review, only the run report. | Sections 1, 2, 5, 6 and 7 are newly authored reasoning, not edited source text. They contain no new numbers, but their framing is this unit's, and a verifier should test the framing separately from the numbers. |
```

**`REFS.md`**

```text
BEFORE: these identifiers came from records rather than recall. This unit did **not** re-fetch them.
AFTER:  these identifiers came from records rather than recall. The authors did **not** re-fetch them.
```

**`REFS.md`**

```text
BEFORE: recorded and which caught four recalled-ID errors. This unit did not independently re-fetch them, and a
AFTER:  recorded and which caught four recalled-ID errors. The authors did not independently re-fetch them, and a
```

**`REFS.md`**

```text
BEFORE: | Re-verified by this unit in this session (Tier A) | **2** |
AFTER:  | Re-verified for this manuscript in this session (Tier A) | **2** |
```

### Residual "unit" after pass 3b — all legitimate or ambiguous, deliberately left

- `GAPS.md:11` — ### G-01 · The "10×" completion-token sentence in the source is unit-sloppy
- `GAPS.md:179` — | G-21 | `papers/gated-read-batching/` was created by the authors; there was no prior manuscript to review, only the run report. | Sections 
- `GAPS.md:182` — | G-24 | The handoff's `sections_complete` is counted against the eight prose units (Abstract + §1–§7). | Title, references and back matter 
- `MANUSCRIPT.md:44` — These are the direct ancestors of a binary relevance verdict. The difference here is the **unit of decision**: a passage against a query, or
- `MANUSCRIPT.md:50` — The pattern — small model, binary-ish verdict, in front of a bigger one — is therefore shipped and measured. What is absent is the *file-rea
- `MANUSCRIPT.md:201` — **Token accounting between two tables.** The R1 table reports *total* tokens (642 K for bs1/`none`) while the R2 table reports *prompt* toke

- `GAPS.md:11` ("the sentence in the source is unit-sloppy") is **ambiguous**: "unit" there may name the
  producing unit inside the source project rather than this manuscript's authors. Left for the reviewer rather
  than guessed; if it is ours, the wording is "is imprecise in the source".
- `GAPS.md:182` ("eight prose units"), `MANUSCRIPT.md:44` ("the **unit of decision**"), `MANUSCRIPT.md:50`
  and `MANUSCRIPT.md:201` are ordinary English/technical uses, not internal-process references.

`CLAIMS.md:136` now reads "Rows independently recomputed by the authors from the raw rows **R**" — true without
a unit name: the recomputation is the manuscript authors' own work.

### After pass 3b

- 20-pattern sweep over the four shipped files: **0 hits** (`MANUSCRIPT.md` 0, `CLAIMS.md` 0, `REFS.md` 0, `GAPS.md` 0).
- md5: `MANUSCRIPT.md` `137d83c9c803c8d9a0aa99025927f063` (unchanged throughout), `CLAIMS.md` `83df6bfe1bfbc5f11330baff17e5ab4f`, `REFS.md` `ba413fc3b97abed8421471cf655ae18a`, `GAPS.md` `a9711547072768ce9b93f26c51dd5afc`.
- Untouched by instruction: the `G/P/R/S` source-document filenames and this log's existing content.

---

## Pass 3c — the last same-class occurrence

The pass-3b residual list showed `GAPS.md:179` still carrying a second occurrence of the same noun; it is fixed
here and the residual count drops to **5**, all of them legitimate or ambiguous (listed in pass 3b).

```text
BEFORE: | G-21 | `papers/gated-read-batching/` was created by the authors; there was no prior manuscript to review, only the run report. | Sections 1, 2, 5, 6 and 7 are newly authored reasoning, not edited source text. They contain no new numbers, but their framing is this unit's, and a verifier should test the framing separately from the numbers. |
AFTER:  | G-21 | `papers/gated-read-batching/` was created by the authors; there was no prior manuscript to review, only the run report. | Sections 1, 2, 5, 6 and 7 are newly authored reasoning, not edited source text. They contain no new numbers, but their framing is the authors', and a verifier should test the framing separately from the numbers. |
```

- `GAPS.md` md5 `71e4678472e30a120f0df5b1b5cf8cef`.

## Pass 4 (2026-10-19) — target project name neutralised in four R5 `answer` values

The staging package (`scratch/upkg7b/package`) and the deposit metadata the recipe stages were brought
to the same clean state as the release payload, and the four end-to-end `answer` values that named the
target project were replaced at **equal length** so no published count moves.

### Neutralisation

| file | before | after |
|---|---|---|
| `data/gated-read-rows.jsonl` lines 9195, 9196, 9198, 9200 | `answer": "2026-09-28-<target>-m0"` (the target project's name, spelled out in the row itself) | `answer": "2026-09-28-trace-m0"` |

19 characters to 19 characters. `data/gated-read-rows.jsonl` is still **2,267,742 bytes, 9,260 lines**.

### Digests that legitimately moved

| site | superseded | now |
|---|---|---|
| `data/gated-read-rows.jsonl` sha256 | `5732766d67d533a2b2e2ddce50d04bcb34a2480f70e1087fdee5754cacc35223` | `b063fbae534a8e5f6649e6b36a21f12b2c40f95c8b0a36b290ad1adf650de809` |
| `data/gated-read-rows.jsonl` md5 | `3aad1ae29e472ef9f5f54e179510faf5` | `93acbf2e5399e9bc42ac7e84a6b5848e` |

Updated at `verify/recompute-claims.py` (`ROWS_SHA256`), `README.md` (digest table, byte-identity
prose and re-measure sentence, superseded values kept in a dated note), `CLAIMS.md` (claim R, dated
note), and the input pins in `scratch/upkginstall7/build_archive.sh`. `MANIFEST.json` was regenerated
with `tools/package/regen_manifest.py`, never hand-edited. No other published number was touched.

## Pass 5 (2026-10-19) — the uppercase same-name leak pass 4 missed, plus three document defects

Pass 4's sweep was case-sensitive and searched the lowercase form and the trace id; it therefore missed
**two rows carrying the target project's name in uppercase**. They are fixed here by an **equal-length**
(21-character) neutral replacement, and the three document defects a verifier found in the same archive
are corrected.

### Neutralisation

| file | before | after |
|---|---|---|
| `data/gated-read-rows.jsonl` lines 9235, 9239 | `answer": "<TARGET>_HOSTED_LAYER_OK"` (the target project's name, uppercase; `mode=e2e`, `task=T17`, arms `selfselect` and `stage`) | `answer": "HOSTED_LAYER_CHECK_OK"` |

21 characters to 21 characters. `data/gated-read-rows.jsonl` is still **2,267,742 bytes, 9,260 lines**.
The replacement names what the value is (the task's expected sentinel; the row's own `paths` already
name `tests/hosted-layer.ts`) and carries no project provenance.

### Document defects corrected

| defect | fix |
|---|---|
| package `README.md` PROVENANCE row stated `31,679` / `ba9f78dd…` / `0aca7cdb…` against a shipped `31,562` / `ae14de17…` / `cfc81ef6…` | row corrected to the measured values; the superseded values kept as a dated note |
| the two "What ships" tables (`README.md`, `README_DEPOSIT.md`) listed 10 of the 12 shipped files | both now list all 12 (`CITATION.cff`, `README_DEPOSIT.md` marked as deposit metadata added by the recipe, not package content) |
| the change record quoted only the **compressed** archive delta | the raw delta is stated alongside it: the 2026-10-19 pass-4 archive grew `125,847 → 126,639 B` (**+792 B compressed**), from raw additions `README.md +1,188 B`, `verify/recompute-claims.py +239 B`, `MANIFEST.json +1 B` = **+1,428 B raw** (`orchestration/units/VPKGFINAL7.md`) |

### Digests that legitimately moved again

| site | superseded (pass 1) | now |
|---|---|---|
| `data/gated-read-rows.jsonl` sha256 | `b063fbae534a8e5f6649e6b36a21f12b2c40f95c8b0a36b290ad1adf650de809` | `e877d05eb3a06069b7cc35b4ffb5fc06e150b6a3b79efd4a9d7f4a3939da47cb` |
| `data/gated-read-rows.jsonl` md5 | `93acbf2e5399e9bc42ac7e84a6b5848e` | `bc2b2a5a36f331a621437cdf328d0d77` |

Updated at `verify/recompute-claims.py` (`ROWS_SHA256`), `README.md` (digest table, dated notes),
`CLAIMS.md` (claim R, pass-2 dated note), the `README_DEPOSIT.md` file table, and the input pins in
`scratch/upkginstall7/build_archive.sh`. `MANIFEST.json` was regenerated with
`tools/package/regen_manifest.py`, never hand-edited. The checker never reads the `answer` field, so no
published number moved. Case-insensitive sweep of package + archive extraction + paper for `duval` in
every case form, the trace id, the host name and internal unit ids (`\bU[A-Z]{2,}[0-9][A-Z0-9]*\b`,
case-insensitive) reports **zero** hits after the fix.

## Pass 6 (2026-10-19, unit ULEAK7D) — the project's own name in the records, applied

Passes 1-2 neutralised the trace identifier and one uppercase sentinel in `answer`. This pass removes the
last trace of the parent project's name from the shipped bytes: **437 occurrences on 225 lines** in the
release payload — 436 in `data/gated-read-rows.jsonl` (`tag` 206, `file` 206, `staged[]` 3, `hit[]` 1,
`paths[]` 17) and 1 in prose at `results/GATED_READ_2026.md:327`.

The replacement is the **equal-length** ten-character token `CORPUSFILE` (`Corpusfile` in the prose
sentence, matching its case). The literal name is deliberately **not reproduced** in this change log: the
three sweep-pattern lists above previously spelled it out, which re-introduced the string they were
supposed to police, and they now describe it instead. Nothing else in the log was rewritten.

| file | before | after | effect |
|---|---|---|---|
| `data/gated-read-rows.jsonl` | the project's name, 436x, inside `tag`/`file`/`staged[]`/`hit[]`/`paths[]` (corpus paths `<NAME>.md`, `docs/<NAME>_PLAN.md`) | `CORPUSFILE.md`, `docs/CORPUSFILE_PLAN.md` | 2,267,742 B / 9,260 lines unchanged |
| `results/GATED_READ_2026.md:327` | "into a <NAME> artefact" (title case) | "into a Corpusfile artefact" | 23,591 B / 340 lines unchanged |

### Digests that moved

| site | superseded (pass 2) | now |
|---|---|---|
| `data/gated-read-rows.jsonl` md5 | `bc2b2a5a36f331a621437cdf328d0d77` | `20727b5c6bed2db935c14bf2e076340f` |
| `data/gated-read-rows.jsonl` sha256 | `e877d05eb3a06069b7cc35b4ffb5fc06e150b6a3b79efd4a9d7f4a3939da47cb` | `184ab747e87f7d127005ce08316dcde640ae93e5278bb1bd57bf353e23d9c44f` |
| `results/GATED_READ_2026.md` md5 | `fe1b900525c63ad0c1ee546d23370c6e` | `2df66834d3a54bee28da9b78d63855cb` |
| `results/GATED_READ_2026.md` sha256 | `17ac3c4eeeb6ac47188fe74424aebf3fff382ba7c6bf5e186a550565cbc9b431` | `c5a054030905944ca5e79ea27ed1310d9fb0ee91a0ba03559a077a87b2e1246d` |

Updated at `verify/recompute-claims.py` (`ROWS_SHA256`), the package `README.md` (digest table,
provenance paragraph, pass-3 dated note), `CLAIMS.md` (claim R), `GAPS.md` (G-23, closed),
`README_DEPOSIT.md` (bounded-difference disclosure), and the input pins in
`scratch/upkginstall7/build_archive.sh`. `MANIFEST.json` was regenerated with
`tools/package/regen_manifest.py`, never hand-edited. No published number moved — the checker never
reads `answer`, the prose word is not read by anything, and `verify/recompute-claims.py` reports
49/49 `VERDICT PASS` on the rebuilt archive.
