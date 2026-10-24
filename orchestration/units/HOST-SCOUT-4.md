# HOST-SCOUT-4 — Read-only paper-readiness scout (five local projects + home dirs)

**Date:** 2026-10-23 · **Mode:** READ-ONLY, no execution, no servers, no builds, no git writes.
**Bound:** ≤40 tool calls / 20 min. **Used:** 19 calls, ~15 min. **Status:** done.

## Question

Which local work is already paper-ready, or one small batch from it — a complete experiment/analysis
with real numbers, ideally a write-up?

## Findings (measured vs planned)

### 1. `/home/zer0null/video ingestor` — ECE 443/518 lecture knowledge base — **ONE BATCH** (top candidate for completeness)

Measured, on disk (all produced 2026-10-12):
- `kb/meta/verification_report.json`: **19 checks passed / 0 failed**. 15 lectures, **173,732 transcript words**,
  **2,935 chunks** (transcript 1,464 / textbook 1,102 / slide 318 / practice 51), 2,935 embeddings,
  318 slides over 15 PDFs, 14 docs, **1,843 edges** (covers 1,827 + references 16).
  Segment coverage ≥95 % on every lecture; no internal gap >30 s; 0 null slide boundaries.
- Retrieval gold set (28 queries): **hit@5 = 28/28 = 100 %**, **27 at rank 1, 1 at rank 2**; textbook in top-3
  for **11/28 = 39.3 %**. (`tools/verify_kb.py` GOLD, threshold ≥80 %.)
- `kb/meta/slide_timeline_report.json`: **286/318 observed anchors = 89.94 %**, 32 interpolated (10.06 %),
  0 null boundaries; per-lecture topics + interpolated counts.
- `kb/meta/index_report.json` + `edges_report.json`: per-lecture chunk/edge breakdown, chapter→lecture map.
- Transcript provenance: 15/15 `kb/transcripts/lecNN.json`, **backend = faster-whisper**, 18,299 segments,
  total **18.24 h** (runbook: 18 h 14 min, 15 mp4 + official slide PDFs + Paar & Pelzl textbook 13 ch).
- Downstream artifacts exist: `studyapp/out/mock-midterm-{paper,key}.pdf`, `ece443-midterm-cheat-sheet.pdf`,
  `output/pdf/ece443-master-prep/*.pdf` (10 files).

Missing: no write-up (only `docs/KB-RUNBOOK.md`, an ops runbook); **no retrieval baseline/ablation**
(keyword-only vs dense vs hybrid is not separated); no WER against gold transcripts; n = 1 course.
Venue: workshop/demo or education-tools short paper. Risk: self-authored 28-query gold set, single course,
lecture-level metric only — reviewers will demand at least a BM25-only baseline.

### 2. `/home/zer0null/orbit-store` + `verify-repo*/agent/evals` — **ONE BATCH** (cleanest single publishable finding)

Measured logs, 2026-10-01, baseline commit `c087541` (`verify-repo/agent/evals/baseline.json`):
- `verify/evals-loop.log`: **25 runs, 4 evals each, 25/25 all-pass, EXIT=0** (idle). Evals: store-integrity,
  dedup-ratios, performance, contract-drift.
- Integrity: `multi_open=0`, `intervals.inverted=0`, `facts.valid_before_observed=0`, `identity.mismatches=0`
  (200 sampled); 243,504 facts, 301 (subject,relation) pairs, 9,581 collection runs, 233,895 legacy-identity rows.
- Dedup: inserted 6.46 / unchanged 22.94 / skipped 15.37 / superseded 6.46 / candidates 51.23 rows per run;
  `share.inserted=0.1261`, `share.unchanged=0.4472` (window: last 200 runs).
- Perf at idle: canonical **1.74 µs/op** (20k ops × 7 trials, spread 0.356), commit batch p50 **4.93 ms**
  (40 timed + 5 warmup, 50 facts each), commit fact p50 **0.0985 ms**, query page p50 **77.47 ms**.
- `verify/evals-load-loop.log`: **10 loaded runs** (16:45:52–16:46:18), **10/10 = 3 passed / 1 failed, EXIT=1** —
  only the performance eval fails, every metric beyond the ±50 % tolerance:
  canonical 1.60→2.71–2.87 µs/op (+69–78 %), commit batch 4.65→8.98–9.98 ms (+93–115 %),
  commit fact 0.0930→0.1797–0.1996 ms, query page 76.51→131.2–133.2 ms (+71–74 %).
  Invariant/dedup/contract evals stay green under the same load.
- Methodology finding, verbatim in `baseline.json` `reason`: a single cold trial measured JIT warmup
  **1.78–2.88 µs/op (60 % spread)**; median of 7 warm trials **1.39–1.43 (3 % spread)** — hence re-baseline.
- Probes: `verify/{callback-attack,store-margin-probe,whoop-binding-probe,runtime-started-probe}.mjs`.

Missing: no write-up; **the applied load is not recorded in the log** (no generator, no parameters);
hardware spec absent; no comparison store (SQLite/EventStoreDB). Store is live (`events.jsonl` 46 MB written
23:01 today, `orbit.db` 562 MB) → any claim must cite the frozen logs, not live paths.
Venue: systems/SE short paper or workshop on verification gates. Risk: commit drift since 10-01; "loaded" is
undefined until someone records the generator; 25 idle runs look like a tight automated loop, not 25 trials.

### 3. `/home/zer0null/locall stt` ("voiceflow") — **ONE BATCH, but needs accuracy**

Measured on this machine (`README.md` §"Measured on this machine"; `docs/STACK-DECISION.md:40-46,83-84`):
11 s speech → **34 ms** (319× real time); 33 s → **135 ms** (245×); LAN round trip **442 ms cold / 158 ms warm**;
LLM polish (Ornith 35B, thinking off) **355 ms**; full batch **513 ms** excluding endpointing;
thinking on burned 135–206 reasoning tokens → 1600–3200 ms vs **224 ms** off.
Fixtures exist: `test/fixtures/{jfk,long33s,AB,BA,AA,conv,conv_long,bt_*}.wav`, `test/voices/v0..v2.wav`.
Missing: **no local WER/accuracy measurement at all** — every WER in the reports is literature
(e.g. LS-clean 1.93 %). Only n = 2 clips for the headline latency. Venue: demo/technical report at best.

### 4. `/home/zer0null/open web index` — **MORE THAN ONE BATCH (design only)**

Docs 010–150 + `spec/shard-format-v0.3.md` + `muninn/` (~20 modules) + 8 test files + 33 KB CHANGELOG.
No `.db`, no `.jsonl`, no `data/` dir; no measured corpus statistics anywhere (only a threshold line,
"applied at ≥50 records"). Nothing to make a dataset paper from.

### 5. `/home/zer0null/ece449-kit` — **NOTHING**

`kit.sh` (push gate runs `grade_p1.py` before pushing to Dasan), `run_grade.py` (fork start method),
`my449/` = ECE 449 project code (`prj01/05/06.py`, `src/libeasynn.cpp`, `easynn_test`), local `grade_p*.py`.
Course submission plumbing; no evaluation, no numbers, no manuscript.

### 6. `/home/zer0null/{Documents,Desktop,Downloads}` depth 1–2 — **NO MANUSCRIPT**

Documents: no .md/.tex/.pdf at depth 2. Desktop: 44 items, mainly course assignment PDFs (ECE 443/485/449),
engineering design docs (`LONG RUNNING AGENT/00-HARNESS-DESIGN.md` 168 KB, `model deploy/*`), and
`personal site build/` playbooks. Downloads: course PDFs, textbook, docx proposals, one redacted
arXiv-style PDF (844 KB, name withheld by the secret guard).
Zero `.tex` files. The closest "research" docs are secondary literature with explicit marks
(`Desktop/personal site build/research-topic-4-6-pixel-budget-frame-pacing.md`: "[MEASURED] = someone
benchmarked it"; `model deploy/AGENTIC_SERVING_EVIDENCE_2026-10-05.md`: "Evidence-only web research …
**VERIFIED** = stated in a primary source"). Neither contains the user's own experiment.
Adjacent, out of scope but noted: `Desktop/model deploy/GB10_1B-9B_ORCHESTRATOR_SERVING_MAP_2026-10-06.md`
and `benchmarks`-looking `tb_README.md` — research compilations, not measurements.

## Verdict

Nothing on this machine is paper-ready as-is: **no draft/manuscript exists for any measured experiment.**
Two projects are one small batch away, and both already hold real numbers:

| Rank | Candidate | Already established | Gap | Readiness | Venue |
|---|---|---|---|---|---|
| 1 | video ingestor KB | 19/19 checks, 28/28 hit@5, 89.94 % observed anchors, 2,935 chunks | write-up + BM25 baseline + provenance note | one batch | education-tools workshop / demo |
| 2 | orbit-store evals | 25/25 idle pass vs 10/10 loaded fail, +69–115 % perf drift, invariant gates green | write-up + load spec + pin commit | one batch | SE/systems short paper |
| 3 | locall stt | 34 ms/11 s (319×), 135 ms/33 s, 513 ms budget | WER on a labelled set, N trials | one batch | demo track |
| — | open web index | nothing measured | crawl + statistics | more | — |
| — | ece449-kit | none | — | not a candidate | — |

Best single bet if only one batch is funded: **video ingestor** (completeness, 19 checks) — but the
**orbit-store** result has the sharper claim (perf gates calibrated at idle fail systematically under load
while invariants hold) and needs no new measurement, only documentation.
