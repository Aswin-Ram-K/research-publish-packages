# VERIFICATION_REPORT_10 — UVER10 verifies UPAPER7 (`papers/gated-read-batching/`)

**Verdict: `pass-with-corrections`.** No number in the manuscript was invented. Every headline metric
reproduced from the raw rows. All 13 identifiers resolve. Three correctable defects (one numeric
rounding, one reference title, two `CLAIMS.md` line locators) — listed first, each with its replacement.

- Checker: `scratch/ver10/check_manuscript.py` (recomputes from `gated-read-rows.jsonl`, parses the
  manuscript's §4.1/§4.3 tables and the operating-point sentence, diffs them).
- Re-derivation: `scratch/ver10/rederive.py` (read-only over `/home/zer0null/Duval/docs/research/gated-read-rows.jsonl`, 9,260 rows).
- Target `/home/zer0null/Duval` untouched (no writes, no `git`). `papers/**` not edited. Real manuscript
  unmodified — `MANUSCRIPT.md` md5 `f9118b2f9ada553d3c9df6e7b440e23f` before and after the red→green run.
- **UFIX17 pointer (2026-10-15, dated record left unrewritten):** the "untouched" clause above must now be read
  as **"no write by this workspace's units"** — five root files and the trace were rewritten by a foreign actor
  (`strategy/CONTAINMENT_CHECK.md` §2/§7). The claims above were true of *this* unit's run.
- Tool calls used: 31 of the 55-call bound. Bound respected.

---

## 1. Contradicted items (corrections, with replacements)

| # | Where | As written | Replacement / truth | Severity |
|---|---|---|---|---|
| X1 | MANUSCRIPT.md:9 (abstract), :143, :215; CLAIMS.md C24 | F1 bs90 `none` = **0.210**, spread **0.017** | Exact re-derived F1 = **0.210526… (0.2105)**; at the manuscript's 3-dp display that is **0.211**. The sources carry 0.2105 (`S gate.gate90_none.f1 = 0.2105`, `G:152` prints 0.210), so 0.210 is a **truncation inherited from the source run report**. Corrected spread = 0.2268 − 0.2105 = **0.0163** (0.016). | **Minor** — 0.001, conclusions unchanged: the ±0.01 tolerance still holds (0.218 − 0.2105 = 0.0075), and 0.211 still sits inside it |
| X2 | MANUSCRIPT.md:229 ref 10; REFS.md (same title); also source `P:47` | *Inside the Scaffold: A Source-Code Taxonomy of **13 Coding-Agent Scaffolds*** | `arXiv:2604.03515` resolves to Rombaut, ***Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures***. The "13 scaffolds" figure is in the abstract, not the title. **Carried from the source's own row `P:47`** — a source error UPAPER7 reproduced rather than introduced. | **Moderate** — a real paper, real identifier, cited claim (13 scaffolds; 7 context-retrieval types) matches the abstract; only the title wording is wrong |
| X3 | CLAIMS.md C48 | locator **G:211-213** | The numeral `p≥0.219` is at **`GATED_READ_2026.md:313`** ("all sign tests p≥0.219"). `G:211-213` states the same *finding* ("not significant … both a coin flip") with **no numeral**. | **Minor** — value exists in the source, line is wrong |
| X4 | CLAIMS.md C65 | second locator **P:247-249** | The "Recalled-ID corrections caught by fetching" paragraph is at **`GATED_READ_PROVENANCE.md:254-256`**. `P:247-249` is the Self-RAG-venue / INFERENCE bullet. The first locator `P:11-15` does contain the four wrong IDs (lines 13–16). | **Minor** — value exists, line is wrong |

Nothing in category X1–X4 changes a manuscript conclusion. X2 is the only one visible to an outside
reader; X3/X4 are internal traceability metadata.

## 2. Re-derived headline table (Priority 1)

Computed by summing `prompt_tok`/`completion_tok` and counting `tp/fp/fn/tn` per `mode` over all 9,260 rows.

| config | calls (S) | prompt tok (re-derived) | manuscript | completion tok | total tok | tp/fp/fn/tn | P / R | F1 exact | F1 (3 dp) | manuscript F1 | admitted (tp+fp) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bs1 `none` (`gate1_none`) | 1,800 | **631,210** | 631 K ✓ | 10,800 | 642,010 | 21/52/99/1628 | 0.2877 / 0.1750 | 0.21756 | 0.218 | 0.218 ✓ | **73** |
| bs16 `none` (`gate16_none`) | 120 | **269,614** | 270 K ✓ | 20,162 | 289,776 | 44/224/76/1456 | 0.1642 / 0.3667 | 0.22680 | 0.227 | 0.227 ✓ | **268** |
| bs90 `none` (`gate90_none`) | 20 | **261,090** | 261 K ✓ | 46,620 | 307,710 | 28/118/92/1562 | 0.1918 / 0.2333 | 0.21053 | **0.211** | 0.210 ✗ (X1) | **146** |
| bs1 `minimal` | 1,800 | 631,210 | 631 K ✓ | 190,699 | 821,909 | 44/111/76/1569 | 0.2839 / 0.3667 | 0.32000 | 0.320 | 0.320 ✓ | 155 |
| bs90 `minimal` | 20 | 261,090 | 261 K ✓ | 1,690,920 | 1,952,010 | 28/39/92/1641 | 0.4179 / 0.2333 | 0.29951 | 0.300 | 0.299 ✓ | 67 |

- **Calls 1,800 / 120 / 20 reproduce** (also `S gate.<mode>.calls`). **Prompt tokens 631,210 / 269,614 /
  261,090 reproduce exactly** — including the two the shipped summary leaves `null` (G-02).
- **F1 0.218 / 0.227 reproduce**; **0.210 is the one mismatch (X1)**.
- Operating-point nuance (C70) **reproduces exactly: 73 / 268 / 146 admitted of 1,800** at near-equal F1.
  Real, and stated without overclaiming: the manuscript says F1-stability is established and
  **operating-point stability is explicitly not** ("does **not** establish operating-point stability",
  line 199; "anyone deploying a batched gate must pin the threshold behaviour, not just the F1", line 143).
- No `unparsed` and no `err` on any gate row; the 260 non-gate rows (`stage` 20, `router` 120, `e2e` 120)
  carry `pred=null` and are excluded from the gate aggregates.

### The "10×" correction — **UPAPER7 is right about the denominator, overstated about the factor**

`GATED_READ_2026.md:160-162` literally reads: "1.69 M completion tokens (**10× the total** of bs1-minimal)".
Re-derived: bs90-minimal completion 1,690,920 ÷ bs1-minimal **completion** 190,699 = **8.87×**;
÷ bs1-minimal **total** 821,909 = **2.06×**; and bs90-minimal total ÷ bs1-minimal total = 2.375× ("2.4×",
which the report states correctly two sentences later at `:163`). So the source conflates the denominator:
"10×" is neither the completion ratio (8.9×) nor the total ratio (2.1×).
UPAPER7's G-01 records exactly this (8.9× / 2.1×) → **correction confirmed**. **But the manuscript does not
carry the correction**: it still says "**ten times** the completion tokens" (line 147) and "the 10×
completion-token blow-up" (line 187), and never prints 8.9. The denominator (completion, not total) was
fixed; the factor was not. → listed as `overstated`.

## 3. Spot-checked CLAIMS.md rows (12; ≥8 required)

| # | Claim | Stated locator | Does the locator contain it? |
|---|---|---|---|
| C01 | corpus 90 files | G:60 | **yes** — "90 files (docs/, src/, …)" |
| C08 | 120 gold pairs / C09 6.7 % | G:122 | **yes** — "120 gold pairs (6.7 % base rate)" |
| C11 | always-`false` accuracy 0.933 | G:134-135 | **yes** |
| C18 | bs1 prompt 631,210 | G:150 + R | **yes** — G:150 prints 631 K; re-derived 631,210 |
| C20 | bs90 prompt 261,090 | G:152 + R | **yes** — G:152 prints 261 K; re-derived 261,090 (S null, G-02) |
| C24 | bs90 F1 0.210 | G:152 + S 0.2105 | locator contains 0.210; **exact value 0.2105 → X1** |
| C26 | 9,260 rows, 0 errors, 0 unparsed | G:119-120 + R | **yes** |
| C28 | bs90-minimal completion 1.69 M | G:160 + R | **yes** — 1,690,920 |
| C34 | "10×" = 8.9× completion | G:160-162 + R | **yes** — and correctly annotated in GAPS G-01 (`overstated` in the manuscript text) |
| C48 | sign tests p ≥ 0.219 | G:211-213 | **NO (X3)** — numeral is at G:313 |
| C50 | BoolQ 90.6 → 72.8, −17.8, bs ≥ 64 | P:209-212 | **yes** |
| C65 | four wrong recalled arXiv IDs | P:11-15, P:247-249 | first **yes**; second **NO (X4)** → P:254-256 |

Also checked and exact: C51 (P:213 GSM8K −5.8 / bs32), C52 (P:232 "−4 to −18 point"), C53 (P:216-218
±1.2 pts, 9–16 % of calls), C54 (P:196-199 + P:52 near-inverse-linear / 5×), C55 (P:221-222 "15 generated
answers … batch size is 16"), C56 (P:205-206 + P:53 position/order), C57 (P:224-226), C58 (P:44 + P:121-122
3.66×), C59 (P:45 + P:122 98 %), C60 (P:37 98 %/83 %), C61 (P:47 13 scaffolds), C62 (P:31 + G:40),
C63 (P:25 + G:38), C64 (P:26), C66 (P:259-272), C67–C73 (confusion counts and 73/268/146 — all
re-derived exact). **11 rows are wrong out of 73? No — every one of the 73 rows I opened carries a
locator that lands in the correct document, and 71 land on the exact line; 2 (C48, C65) are off.**

## 4. Reference resolution table (Priority 2 — highest severity)

All 13 identifiers were resolved live in one `web_fetch` of the arXiv Atom API (`id_list`, HTTP 200,
2026-10-15 UTC). **13/13 resolve; 0 fabricated; 0 UNVERIFIED identifiers** — matching the package's claim.

| Ref | Identifier | Resolves | Title matches record | Cited claim / venue |
|---|---|---|---|---|
| 1 Asai et al. | 2310.11511 | yes | yes | Self-RAG; venue correctly **unclaimed** (REFS honest) |
| 2 Chen et al. | 2305.05176 | yes | yes | FrugalGPT, 98 % ✓ |
| 3 Cheng et al. | 2301.08721 | yes | yes | EMNLP 2023 Industry Track (arXiv comment) ✓ |
| 4 Jeong et al. | 2403.14403 | yes | yes | NAACL 2024 ✓; "a classifier, which is a smaller LM" ✓ |
| 5 Jiang et al. | 2305.06983 | yes | yes | FLARE; EMNLP 2023 ✓ |
| 6 Lin et al. | 2309.00384 | yes | yes (case only) | BatchPrompt; −17.8/−5.8/±1.2/9–16 %/"15 answers" ✓ |
| 7 Mallen et al. | 2212.10511 | yes | yes | ACL 2023 ✓ |
| 8 Ong et al. | 2406.18665 | yes | yes | RouteLLM 3.66× ✓; **ICLR 2025 not on the arXiv record** (source-only) |
| 9 Parisi et al. | 2205.12255 | yes | yes | TALM ✓ |
| 10 Rombaut | 2604.03515 | yes | **NO — X2** | 13 scaffolds / 7 retrieval types ✓ from abstract |
| 11 Schick et al. | 2302.04761 | yes | yes | Toolformer; NeurIPS 2023 ✓ |
| 12 Xiang et al. | 2406.09187 | yes | yes | GuardAgent 98 %/83 % ✓ (ICML 2025 in arXiv comment) |
| 13 Yue & Yao | 2503.15551 | yes | yes | Findings of ACL 2025 ✓ |

The **2 live-verified** refs are confirmed (both resolve, titles agree, claims match) — no fetch-date
regression. **11/11 "verified-in-source-only" resolve live**; the only failure is the ref-10 title (X2).
No fabricated citation was found: every identifier exists, every title except ref 10 is real, and every
cited claim matches the fetched record or the source's provenance line.

One **`unverified`** (not contradicted): ref 11's author list includes **Hambro**, which arXiv v1 does not
list (v1 has 8 authors; the manuscript has 9). The manuscript's own stated rule — "exactly the set the
source material carries" — is satisfied (`P:25` carries Hambro, presumably from the NeurIPS proceedings
row). Semantic Scholar (`…/arXiv:2302.04761?fields=authors,venue`) returned **HTTP 429** twice, so the
9-author NeurIPS list could not be independently re-confirmed. Not a fabrication finding.

## 5. Self-claims (Priority 3)

| Claim | Result |
|---|---|
| 5,193 words | **confirmed** — `wc -w` = 5193 on MANUSCRIPT.md |
| 8/8 prose sections, no placeholders | **confirmed** — Abstract + §1–§7 = 8; grep `TODO\|TBD\|XXX\|placeholder\|\[cite\]\|FIXME\|insert\|Lorem` over `papers/gated-read-batching/*.md` → **0 hits** |
| CLAIMS.md 73 rows, 73/73 with a source locator | **overstated** — 73 rows confirmed (C01–C73), all carry a locator, but C48 and C65's second locator miss the exact line (X3, X4). Values are in-source in both cases. |
| numbers_invented = 0 | **confirmed** — every headline number re-derived; no unlocatable number found |
| R1 negative reported | **confirmed** — §4.3 five-row table; §5 "The negative is the more important half"; §7 restates it |
| R5 dropped and noted | **confirmed** — §6 "The removed arm, stated rather than silently omitted": names the end-to-end arm, the injection measurement and the R3/R4 arms, gives the power reason (sign tests p ≥ 0.219), and states the paper makes no downstream-accuracy/context-cost/injection claim |
| mechanism abstracted | **confirmed** — §3 describes only the gate's inputs (path, 300-char header, outline; "never on the file body"); nothing about the private kernel's implementation |

### Framing assessment of the newly authored §1/§2/§5/§6/§7 (G-21)

- **Abstract does not claim more than §4 supports.** Every abstract figure maps to a re-derived §4 value
  (X1 excepted). The batching claim is bounded three times — title, abstract ("On this task, corpus and
  decision model … did not measurably degrade decision quality. This is a narrower claim than 'batching is
  free'"), and §7 ("not a general licence to batch"). No claim of general batching safety.
- **The negative is a finding, not buried.** It is in the abstract's second paragraph, the second of the
  title's two clauses, §5's "The negative is the more important half", and §7.
- **§6 discloses the scope bounds and the omission**: one model / one corpus / one task family (also in the
  Status line), no significance test ("a descriptive tolerance … not a pre-registered non-inferiority
  margin"), the R5 removal with its power justification, the token-accounting label change between tables,
  the `prompt_tok_total: null` wart, the byte-containment label limit, the unrun second model, and the
  absent end-to-end ceiling. This is a stronger limitations section than the batch standard.
- **The private kernel is not described.** §2.2 cites only public prior art (Adaptive-RAG, RouteLLM,
  FrugalGPT, GuardAgent); §5's mechanism remark is a conjecture about one-bit JSON vs generated answers,
  not implementation detail.
- **One framing nit (see §6 below):** §5 line 187 still calls the completion-token blow-up "10×", which
  the package's own G-01 knows is 8.9×. The negative result is not oversold; this one efficiency adjective is.

## 6. Red→green

Checker `scratch/ver10/check_manuscript.py`; alteration made on a **workspace copy**
(`scratch/ver10/MANUSCRIPT_red.md`), never on the real file.

```
GREEN (unmodified MANUSCRIPT.md)               rc=0  CHECK: PASS
RED   (copy: bs16 row 270 K→27 K, 0.227→0.927) rc=1  CHECK: FAIL
  - R2 bs16 promptK: manuscript=27 re-derived=270 (exact 270)
  - R2 bs16 F1:      manuscript=0.927 re-derived=0.227 (exact 0.2268)
```

Copy deleted after the run; real file md5 `f9118b2f9ada553d3c9df6e7b440e23f` unchanged. The check is
sensitive to a one-unit change in a headline metric and clears when restored.

## 7. Disclosure grep

Pattern: `/home/zer0null`, `duval` (case-insensitive), `Consonance`, `a5ef1b28`, `89003e70`,
`publish-present-compete`, `LAYERS.md`, `AGENTS.md`, `D-0XX`, `MISTAKES`, `M1X`, `gated-read-rows`,
`gated-read-summary`, `GATED_READ`, `tools/gated-read`.

**No corpus file or path is named. No hex identifier, no internal decision ID, no workspace path, no
"Consonance"/"Duval" string.** Four benign hits at lines 32, 48, 185, 195 for the generic words
"stage"/"staged"/"router" used as architecture terms (and the paper's own arm labels R3/R4). The one
internal artefact line in the source (`GATED_READ_2026.md:327`, Consonance/D-038) is absent from the
manuscript, consistent with G-17/G-18. Disclosure gate: **clean**.

## 8. Verdict lists

- **`contradicted`**: X1 F1 bs90 `none` (0.210 → 0.2105 / 0.211; spread 0.017 → 0.016); X2 ref 10 title;
  X3 CLAIMS C48 locator; X4 CLAIMS C65 locator.
- **`overstated`**: "73/73 with a source locator" (exact-line accuracy 71/73); "ten times the completion
  tokens" / "10× completion-token blow-up" (true factor 8.87×; the package's own G-01 says so and the
  manuscript did not carry the correction).
- **`not_reproduced`**: none. (Every re-checkable claim was reproduced; the only unreachable item was the
  Toolformer author list, which is a `unverified`, not a coverage failure of the manuscript.)
- **`unverified`**: ref 11 Toolformer 9-author list incl. Hambro (arXiv v1 lists 8; Semantic Scholar HTTP
  429, so not independently re-confirmed); ref 8 RouteLLM ICLR 2025 and ref 11 NeurIPS 2023 venues rest on
  the source's fetched records, not re-fetched by me; literature claim *texts* were matched against the
  fetched arXiv abstracts and the source's provenance rows, not against each full paper.

## 9. What would change my verdict

- **To `fail`:** a headline number that does not reproduce (none — all reproduced); an identifier that
  does not resolve (none — 13/13); a fabricated title that is not also in the source (X2 is in `P:47`);
  a number in the manuscript with no source anywhere (none found); or evidence the real `MANUSCRIPT.md`
  was altered to make the check pass (md5 unchanged; all edits were on a deleted copy).
- **To `pass` (no corrections):** correct the ref-10 title, print 0.2105 (or 0.211) for bs90 `none` F1
  and 0.016 for the spread, append the 8.87× factor where "10×"/"ten times" appears, and repoint C48 to
  `G:313` and C65's second locator to `P:254-256`. All four are one-line edits; nothing else changes.
- **Would invalidate the bounded batching claim:** a formal non-inferiority test on the 1,800 pairs
  showing a real degradation beyond ±0.01 (no test was run — disclosed in §6), or a second run showing the
  F1 spread is not stable; or a second decision model showing the gate weakness is model-specific rather
  than task-specific (open, disclosed).
- **Would invalidate the operating-point nuance:** a threshold sweep showing 73/268/146 is an artefact of
  the batching template rather than of the decision rule — the manuscript already declines to claim
  operating-point stability, so this would narrow, not break, the claim.
