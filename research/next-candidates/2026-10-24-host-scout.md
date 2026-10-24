# Host-wide paper-readiness scout — 2026-10-24

**What this is.** The answer to the question the repo record did not ask: *across every project on this
machine, what is already paper-ready — or one small batch away?* `2026-10-24-sweep.md` scoped this
workspace's own experiments and papers; this is the outward-looking companion. It is an inventory of
evidence already on disk, not a result. No experiment, server, build or model request was made, and **no
number below was re-measured by the writer** — every figure is quoted from a scout report, which quoted it
from the file at the path given.

**Scope.** Four read-only units covered ~20 trees: `Duval`, `publish-present-compete`, `TRUTH`; `AND-1`
(`absent-loop`, `head2head-search-orch-battle`), `High-density verified agent execution fabric`,
`projects/gx10-local-agent-runtime`, MU-PHI; `deepseek-harness`, `dsh-plugins`, `agentnet`(+`-sandbox`),
`background agent`, `auto PR tool`, `pi-autonomous-test`, `maintenance`; `video ingestor`, `orbit-store`,
`locall stt`, `open web index`, `ece449-kit`, and `~/Documents`/`~/Desktop`/`~/Downloads` at depth 1–2.

**Method.** Listings first, then only the documents that could carry measurements (registers, findings,
eval logs, benchmark notes), then — where cheap — a re-parse of the raw row file instead of the prose.
HOST-SCOUT-1 re-read every headline number from `EXP#11-evidence/*.jsonl` and `EXP#46-evidence/sweep.jsonl`
with `python3 -c`; SCOUT-3 tallied `auto PR tool/data/proposals.json`; SCOUT-4 aggregated the video-ingestor
and orbit-store JSON/logs. This writer read the four unit reports, their four handoffs and this workspace's
sweep, and opened **no file in any target tree**.

**Honest limits.** (a) Bounds — SCOUT-1 used 25 calls / ~24 min against 40/20 (over on time, recorded);
SCOUT-2 22 calls; SCOUT-3 31/40; SCOUT-4 19/40: breadth over depth, and no unit read a full paper draft
because none exists. (b) This is not the whole host: `~/.config`, `/opt`, `/srv`, every dotfile and most of
`~/Desktop`'s 44 items were never opened. (c) Absence claims are predicate-limited — "no `.tex`" came from
`find` over four trees, and `~/Downloads` holds `.docx` proposals, so it is not "no manuscript". (d) Where
two scouts overlapped (orbit-store) they agree, but neither cross-checked the other. (e) Readiness is a
judgement about *what remains*, not about *what the result is worth*.

---

## 1. Verdict in one page

**No project on this machine is paper-ready in the strict sense.** Not one has a manuscript, an abstract,
a related-work section or a venue submission outside `/home/zer0null/reserach extarctor/papers/`, which
belongs to *this* workspace, not to the host. Every "publishable" label found on disk was a unit's or an
author's own label, and each one, when checked, meant *the artefact is finished* — not *the paper is written*.

What does exist is unusually good raw material. **13 candidates: 7 are substance-complete and need only
writing (0 requests), 6 need one small batch.** Two of the seven (D1, D2) are finished in the sense that
their intended outlet is a blog, not a venue.

- **Strongest external paper: Duval EXP#11** — a real effect with a never-revised control stratum and two
  zero-cost recounts standing between it and a draft. It is already this workspace's shortlist A4, where
  the same Bonferroni caveat is recorded.
- **Most complete experiment: `absent-loop`** — 6 arms × 4 corpora, full n, CIs, and an independent
  re-derivation at 122/122. It needs prose, tables and one figure.
- **Most citable artefact story: the High-density fabric** — an adversary pass that found two escapes, with
  the red→green fix already on disk.
- **Sharpest single number: orbit-store** — gates calibrated at idle pass 25/25 and fail 10/10 under load
  while every invariant stays green.

**If one person writes:** EXP#11 → absent-loop → the High-density short note. **If one compute batch is
funded:** the video-ingestor BM25 baseline, or the orbit-store load spec. **Do not start** the
execution-required items (Orbit post-fix re-measurement, EXP#46 SGLang arms) without approval.

---

## 2. Tier 0 — write now, 0 compute

Ranks are paper value (1–5) × readiness; a tier is about *what remains*, not about value.

### H0 · rank 1 — Duval EXP#11: option-set revision / self-refinement degradation

**Root** `/home/zer0null/Duval`. **Paths:** `docs/research/experiments/EXP#11-per-model-option-revision.md`;
`docs/research/SELF_REFINEMENT_DEGRADATION_2026.md` (50 KB); `docs/research/EXTERNAL_EVIDENCE_2026-10-07.md`;
F-EXP11-01…17 at `docs/research/FINDINGS_REGISTER.md:30-70`; raw
`docs/research/EXP#11-evidence/{decider,imajev}-dashboard.jsonl`, `decider-rows.jsonl`.
**Established (re-parsed from rows):** revised stratum **0.665 → 0.630 over 7 rounds**; imajev-4b
**0.645 → 0.580 over 6** (−6.5 pts, trough 0.570 at r4); never-revised control **0.6700 in all 13 dashboard
rows**; AUROC **0.708–0.715** vs published 0.522–0.605; paired **7/7 discordant, p = 0.0156**; option sets
grew 2 → 8; `ANSWER ∉ option set` **0.00 %** every round; 4,090 + 3,690 rows. **Three discrepancies, all
zero-cost:** 13 control measurements not 12; **3,690** imajev rows not 3,590; **−6.5 over six rounds** not
−7.5 (`SELF_REFINEMENT_DEGRADATION_2026.md` §1 still prints −7.50).
**Missing:** the manuscript (abstract, intro, related work, tables), a claims ledger, the two recounts, and
F-EXP11-12's headroom figure, which must be recomputed from `live2-decider/rows.jsonl`. **Venue:** TMLR or
a self-refinement/evaluation workshop — the contribution is the control stratum and the 2→8 range, not
"self-refinement hurts" (Huang et al. 2024 is cited as public). **Risk:** small effect, n = 2 models / one
4B class; the honest core is a correction story; p = 0.0156 does **not** survive Bonferroni 0.0125, so it is
written as descriptive only. **Requests 0.**

### H1 · rank 2 — AND-1 `absent-loop`: gap-loop ablation, 6 arms × 4 corpora

**Root** `/home/zer0null/AND-1`. **Paths:** `EXPERIMENTS/absent-loop/FINDINGS.md` (747 lines, 8 sections);
`state/u5/audit.md` + `audit.py`; `state/u{2,3,4}/REPORT.md`; `runner/{loop.py,meta.py}`;
`EXPERIMENTS/EXPERIMENTS-TRACKER.md`.
**Established:** hotpotqa-distractor-dev **n = 7,405** (gold 2, 0 excluded) plus scifact 1,109 / nfcorpus
3,237 / fiqa 6,648 — full n everywhere. Loop ON vs OFF: recall/run **0.81411 vs 0.76887, Δ +0.04524
[+0.04186, +0.04862]**; recall/call **−0.26946**; 664 gained / 6,741 tied / 0 lost; **93.6 % of the gain is
call 2** (marginals +0.04234 / +0.00283 / +0.00007). Narrowing **loses**: **−0.00459 [−0.00716, −0.00216]**,
gold precision −0.01655, down 4/4 corpora. Sufficiency fired 5,331×, gold-complete only **63.3 %**, **36.7 %
premature**. Arm-4 META is 1st of 6 on 4/4 corpora (94.81 % of oracle). **Verification: 122/122 reproduced,
0 differs, 0 could not check** (U5, own reader, seed 424242); worst CI-endpoint gap 0.00096; 29 recorded
defects plus a §5 "cannot claim" list reusable as Limitations.
**Missing:** abstract, intro, related work, a camera-ready table set, one figure, venue. **Venue:** IR /
RAG-evaluation workshop or arXiv. **Risk:** novelty low by design (FAIR-RAG, arXiv:2510.22344); the gain is
small and lives in call 2; the deterministic chooser is a weak router analogue whose rules were designed
with U3's aggregates in hand; **fiqa reverses sign** (−0.01625). Lead with both. **Requests 0.**

### H2 · rank 3 — High-density fabric: denial bundle + adversary pass

**Root** `/home/zer0null/High-density verified agent execution fabric`. **Paths:** `docs/CLAIMS.md` (9 rows;
wording rules §3); `docs/board/CLAIMS-PROVE.md`; `docs/research/EXP#1-T1-negative-evidence.md` §9 and
`EXP#2`…`EXP#6`; `docs/{EVAL,PROGRAMME_LOG}.md`; `docs/board/{ADVERSARY-1,FIX-ADV}.md`; `mutants.out/`.
**Established: C1–C5 and C9 proven** — kernel denials journal errnos 2 / 2 / 30 / 101; bundle from the
journal alone = 4 records / 4 denials; byte flip at offset 42 → `FAIL(tamper:hash-mismatch)`; **cold
principal verifies from three files with zero network syscalls** (`--bundle --pubkey --task` → `OK` exit 0);
drop-in to the Duval sandbox **41 PASSED · 0 FAILED · 0 SKIPPED**; `entry_count=6 wall_ms=12 verified=True`.
**Health: 397 tests passed, 0 skipped; 24 adversary probes → 2 escapes** (truncated-journal re-seal;
attacker-chosen task), both closed with 8 new tests, **red→green on disk**; mutation 9 caught / 0 missed over
a 10-mutant set on one module — a narrow instrument, not a repo-wide score.
**Missing:** no paper shape; **C6/C7/C8 unproven or deferred** — no microVM second mechanism, no third-party
witness, and **C7 is a real gap**: the bundle projects only `op=="deny"` while MCP refusals journal as
`mcp.tool.refused`, so a live bundle shows `denials` length 0. **Venue:** systems/security workshop or
artefact-evaluation venue. **Risk:** the two escapes *are* the finding; `docs/CLAIMS.md` forbids
"tamper-proof" / "deterministic replay" / "AI Act compliant" and `scripts/claims-lint` gates in-tree text.
**Requests 0** for a short note; ≥1 run batch for a full paper.

### H3 · rank 4 — deepseek-harness: performance-gate corpus + four post-mortems

**Root** `/home/zer0null/deepseek-harness`. **Paths:** `benchmarks/session-corpus/README.md`;
`benchmarks/agent-continuation/README.md`;
`.agents/notes/implemented/testing/2026-09-28-session-corpus-performance.md:54-66`;
`docs/postmortem/0001…0004*.md`; `docs/subsystems/` (60+ docs).
**Established:** list 3,000 sessions boot **2,317.8 / 2,204.5 ms**, first 3,228.7 / 2,633.6, repeat 2,636.4 /
2,235.1 (EPYC 7763 / 9V74); content search 1,000 sessions first **144,359 / 135,065 ms**, repeat 3,426.3 /
2,704; fork p99 **1,066.2 ms**, longest 19,162.1 / 20,326.7; peak RSS 742.7 / 1,197.8 / 745.1 MB; M5 Pro list
10,000 **3.2–5.4 s at 1.9 GB RSS**; budgets = higher median × 1.25. Four resolved post-mortems, each with a
named root cause, an event-log-numbered timeline and the guardrail that closed it.
**Missing:** the paper — no consolidated table, no before/after baseline for any optimisation, **no
agent-level evaluation** (only harness latency/memory), no related work. **Venue:** ICSE/FSE industry or
experience track, HotOS/HotInfra workshop; best framing today is *"performance regression gates for a
multi-package agent harness"*, post-mortems as reliability companion. **Risk:** reviewers will ask for the
agent-level evaluation; the numbers come from the project's own CI. `BENCHMARK.md` is 3 lines of setup, not
a results document. **Requests 0.**

### H4 · rank 5 — orbit-store: the idle-vs-loaded verification gate

**Root** `/home/zer0null/orbit-store`. **Paths:** `verify/evals-loop.log`; `verify/evals-load-loop.log`;
`verify-repo/agent/evals/baseline.json` (commit `c087541`); `verify/*-probe.mjs`.
**Established:** idle **25 runs × 4 evals, 25/25 all-pass, EXIT=0**; loaded **10 runs, 10/10 "3 passed /
1 failed", EXIT=1** — **only the performance gate fails**: canonical 1.60 → 2.71–2.87 µs/op (+69–78 %),
commit batch 4.65 → 8.98–9.98 ms (+93–115 %), commit fact 0.0930 → 0.1797–0.1996, query page 76.51 →
131.2–133.2 ms (+71–74 %), **every metric beyond ±50 % tolerance**, while integrity, dedup and contract gates
stay green. Corpus 243,504 facts / 9,581 runs / 301 pairs, all invariant counters 0. Methodology: a single
cold trial read 1.78–2.88 µs/op (**60 % spread**) vs 1.39–1.43 over 7 warm (**3 %**).
**Missing:** the write-up; **the load generator and its parameters are not recorded anywhere**; no hardware
spec; no comparison store; no commit pin (drift since 2026-10-01). **Venue:** SE/systems short paper or
verification-gate workshop. **Risk:** "loaded" is undefined until the generator is recorded; 25 idle runs
are a tight loop, not 25 trials; the store is live (`events.jsonl` 46 MB, `orbit.db` 562 MB) so cite the
frozen logs only. **Requests 0.**

### H5 · rank 12 — publish-present-compete D1: Node zstd multiframe record loss

**Root** `/home/zer0null/publish-present-compete`. **Paths:** `publish/drafts/D1-node-zstd-multiframe.md`;
`publish/repro/{zstd-multiframe,corpus-census}.mjs`; `publish/corpus-census-2026-10-07.json` (INTERNAL —
carries an absolute home path in `root`).
**Established:** 4,986 logs / 4,982 session dirs, 3,086,067,541 bytes, 6,715,736 frames,
`records_first_frame_only` 4,985, **`silently_lost_records` 11,757,139**, **`silent_loss_pct` 99.96**.
Version matrix on released binaries: Node **v22.23.3 and v24.21.0** return `"ONE"` from a 3-frame stream;
**v26.10.0** returns `"ONETWOTHREE"`; fixed on `main`, **not backported** — so the draft is a comment on an
existing issue, not a new report. **Missing:** strip `root`; ship both artefacts together. **Venue:**
engineering blog / upstream issue; **not a research venue** (n = 1 machine, one corpus, upstream's bug).
**Risk:** the 99.96 % figure is only credible *with* the version matrix. **Requests 0.**

### H6 · rank 13 — publish-present-compete D2: failure autopsy

**Path:** `publish/drafts/D2-failure-autopsy.md` — *"The Decompressor Was Innocent: Five Claims One
Instrument Falsified"*. **Established:** five of the project's own claims falsified by its own measurement
passes — 0 % coverage, "285 distinct sessions", "1 distinct catalog value", and **1.08 GB RSS after 54,385
frames**, measured false on Node v22.22.1 with forced GC; the residue is four assertions against real data.
**Venue:** engineering blog / technical report, **not a venue paper**. **Risk:** one project, one machine, a
few weeks — the draft says so itself. **Requests 0.**

---

## 3. Tier 1 — one small batch each

### H7 · rank 6 — video ingestor: ECE 443/518 lecture knowledge base

**Root** `/home/zer0null/video ingestor`. **Paths:** `kb/meta/{verification_report,slide_timeline_report,
index_report,edges_report}.json`; `kb/transcripts/lecNN.json`; `tools/verify_kb.py`; `docs/KB-RUNBOOK.md`.
**Established: 19 checks passed / 0 failed**; 15 lectures, 173,732 transcript words, **2,935 chunks** (1,464
transcript / 1,102 textbook / 318 slide / 51 practice), 318 slides over 15 PDFs, 1,843 edges; coverage ≥95 %
every lecture. Gold set **hit@5 = 28/28 = 100 %** (27 at rank 1, 1 at rank 2). Slide timeline **286/318
observed = 89.94 %** (32 interpolated), 0 nulls. ASR 15/15 faster-whisper, 18,299 segments, **18.24 h**.
**Missing:** the write-up (only an ops runbook); **a retrieval baseline** — a BM25-only run is the minimum;
no WER; n = 1 course. **Venue:** education-tools workshop / demo. **Risk:** self-authored 28-query
lecture-level gold set, one course. **Requests 1** (small local batch).

### H8 · rank 7 — Orbit: identity duplication in the fact store

**Root** `/home/zer0null/background agent`. **Paths:** `research/identity-duplication.md`; `docs/EVALS.md`;
`docs/SESSION-FINDINGS.md`; `research/{storage-audit,stream-redundancy}.md`.
**Established: 230,395 rows; 100 duplicate pairs = 131,500 rows = 57.1 % of the table**, every pair
`relation_kind='stream'`, `k2:K2-806C/job:*` (25 jobs × 4 relations), 1,315 rows/pair,
`COUNT(DISTINCT observed_at) = 1`. The design claim "differ only in `provenance.fetchedAt`" is **false**:
dropping `fetchedAt` alone dedups nothing; dropping it plus `epoch` collapses 13,150 → 10 rows. `epoch`
equals `run.id` for **99.7 %** of rows — sequencing leaking into a content hash.
**Missing:** the **post-fix re-measurement** — no "after" number exists, and that number is the whole
experiment; plus a second adapter family and a bitemporal baseline. **Venue:** short paper / workshop on
agent memory. **Risk:** n = 1 store; obvious-in-hindsight field bug. **Requests 1 — execution:** the user
forbade execution for this record, so this batch is **queued, not started**.

### H9 · rank 10 — auto PR tool: human-gated contribution funnel

**Root** `/home/zer0null/auto PR tool`. **Paths:** `README.md` (two gates, strong ≥0.30 / candidate ≥0.20);
`data/proposals.json` (109,709 bytes); `.prtool/SESSION-CLOSEOUT-2026-{09-23,10-05}.md`; `.prtool/pr663/`.
**Established: 38 proposals** — submitted 3, awaiting-gate2 2, gate1-rejected 20, awaiting-gate1 12, failed
1; tiers strong 14 / candidate 24; gate-1 acceptance **5 of 25 decided = 20 %**. Real outcomes:
`OpenHands/extensions#663` open (head `cf235dd`), triage issue `#733` filed.
**Missing:** ground truth, a baseline matcher, an instrumented log; the 12 awaiting-gate1 must be excluded
(n = 25). **Venue:** workshop on human-in-the-loop automation / OSS tooling. **Risk:** small n, one repo
graph, author-measured outcomes; the batch is *design* more than measurement. **Requests 1.**

### H10 · rank 8 — Duval EXP#46: serving-config Pareto / MTP speculation

**Paths (root `Duval`):** `docs/research/experiments/EXP#46-serving-config-pareto.md`;
`docs/research/EXP#46-evidence/{sweep.jsonl,analysis.json,RUN_LOG,prefix-cache-probe.json}`; register §EXP#46.
**Established:** 16 rows = 4 arms × c ∈ {1,2,4,8}; MTP-on vs speculation-off 32.67/62.82/117.45/148.05 vs
22.16/45.28/85.12/108.49 tok/s = **1.474 / 1.387 / 1.380 / 1.365×**; `--max-num-seqs` 8 vs 4 at c = 8 is
**1.738×** (148.16 vs 85.27); 6/16 rows `deterministic=False`, all speculation-off.
**Missing:** the file itself says `resolution: "VOID"`, `pareto_claims: []`, `incomplete_comparisons: 16`;
**12 SGLang points never ran** (Launcher `DockerCmd` TypeError), the c = 4 four-vs-six cell was never
measured, and the prefix-cache gauge was never shown able to report a non-zero hit. **Venue:** serving
workshop or engineering report. **Risk:** one engine, model, quantisation, greedy 64-token workload and GB10
box — width equals ceiling. **Requests 1 (execution), not started.**

### H11 · rank 9 — Duval EXP#45: selective-risk reformulation

**Paths:** `docs/research/experiments/EXP#45-selective-risk-reformulation.md`;
`docs/research/EXP#45-evidence/{REPORT.md,analysis.json,rows.jsonl}`.
**Established:** `pooled.raw_accuracy` **0.6316**; at the 97.5 % per-decision target the cross-fitted
isotonic gate covers **0.0158** (handled 1.000) and the raw-confidence gate **0.0**; learned gate 0.6684
(escalation 0.9842) vs fixed rule t = 0.75 0.6789; `per_kind` 7 types; MDE split at n = 22–30.
**Missing:** the **aggregate-tolerance arm** — the claim worth making (11.5–16 % handled under 97.5 %
per-decision vs **41–49 %** at an aggregate tolerance, quoted from `docs/DECIDER_TIER.md` and **not
re-derived**) is uncomputed. **Venue:** short note / workshop. **Risk:** power analysis + negative result;
low excitement. **Requests 1.**

### H12 · rank 11 — Duval `PAPER_DERIVATION.md`: the 8-experiment programme paper

**Path:** `docs/research/PAPER_DERIVATION.md` (46 KB) — Abstract through §8 Reproducing; eight experiments
complete. **Missing:** no package in `papers/`; stale (2026-10-04) against the register (2026-10-19); the
EXP#7 overlap belongs to `papers/replay-record-not-decision`. **Venue:** umbrella paper — but its results
are individually published, so the split is the work. **Risk:** broad, and may exceed one batch (0 compute).
**Requests 1.**

---

## 4. Not candidates

- **`projects/gx10-local-agent-runtime`** — coherent topology (LiteLLM :8000, llama.cpp :8080, vLLM :8002,
  MTP depth 3 "validated GB10 profile") but **no stored benchmark output**; "validated" has no number.
- **`open web index`** — design only: docs 010–150, ~20 modules, 8 tests, no `.db`/`.jsonl`/`data/`, no
  corpus statistics. Nothing to make a dataset paper from.
- **`agentnet` + `agentnet-sandbox`** — a working A2A mesh (1,205 lines, 8 tests) and a **demo**: empty
  `inboxes/`, no latency, delivery or reconnect numbers.
- **`dsh-plugins`** — one OpenUI renderer plugin; no data, no experiment. **`ece449-kit`** — course
  submission plumbing; no evaluation. **`pi-autonomous-test`** — README is `// test project`; a scratchpad.
- **MU-PHI** — shape-only by its own README: "There is no store and no LLM"; "Every experiment run so far is
  a *shape* verification"; FES DRAFT, system DORMANT (`egress-ungranted`).
- **TRUTH** — operational, not research: 82-outlet guide, 2,270 contact rows, 948 journal records, and
  **zero** response/reply-rate documents. The outlet guide is a living dataset at best.
- **`maintenance/fleet-hygiene`** — 4 dated snapshots (2026-10-22: 55 repos, 24 dirty, 1,755 dirty files);
  a supporting figure for the harness paper.
- **`locall stt`** — latency only (34 ms / 11 s = 319×; 135 ms / 33 s; 513 ms batch); **every WER in the tree
  is literature**, headline rests on n = 2 clips. Needs a labelled accuracy set — more than one batch.
  (SCOUT-4 ranked it one-batch; this record holds it out.)
- **`head2head-search-orch-battle`** — only **4 of 15 pairs** like-for-like, and s2/s3 are frozen, so it
  cannot be repaired: an instrument-critique note at best.

---

## 5. Cross-project comparison

`value` is value **as a venue submission** (1–5), not artefact quality; `ready` is what remains.

| Rank | ID | Candidate | Project | Value | Ready | Requests |
|---|---|---|---|---|---|---|
| 1 | H0 | EXP#11 option-set revision | Duval | 4 | now | 0 |
| 2 | H1 | absent-loop gap-loop ablation | AND-1 | 4 | now | 0 |
| 3 | H2 | Denial bundle + adversary pass | High-density fabric | 4 | now | 0 |
| 4 | H3 | Perf gates + 4 post-mortems | deepseek-harness | 3 | now | 0 |
| 5 | H4 | Idle-vs-loaded verification gate | orbit-store | 3 | now | 0 |
| 6 | H7 | Lecture KB (19/19 checks) | video ingestor | 3 | 1 batch | 1 |
| 7 | H8 | Identity duplication 57.1 % | background agent | 3 | 1 batch | 1 (exec) |
| 8 | H10 | Serving-config Pareto (VOID) | Duval | 3 | 1 batch | 1 (exec) |
| 9 | H11 | Selective risk @ 97.5 % | Duval | 2 | 1 batch | 1 |
| 10 | H9 | Human-gated PR funnel | auto PR tool | 2 | 1 batch | 1 |
| 11 | H12 | 8-experiment working paper | Duval | 2 | 1 batch | 1 |
| 12 | H5 | zstd silent record loss | publish-present-compete | 1 | now | 0 |
| 13 | H6 | Failure autopsy | publish-present-compete | 1 | now | 0 |

D1 and D2 score 1 **as papers** because their outlet is a blog; their readiness is perfect and their artefact
value is high — a different axis.

**Relationship to the repo record.** This list does not displace `2026-10-24-sweep.md`. For *this workspace's
own papers*, the repo record still outranks it: **P0** (reconcile E1 vs C44, fold E2/E3/E4/E4R, fix the
1.700× horizon sentence; 0 requests) is the precondition for submitting the flagship, and **R2-VLLM "zero
hits"** (418 rows; 0/64 battery vs 27/27 probe; `cached_tokens` has at least four meanings) is the cheapest
novel paper here. The one deliberate overlap: **EXP#11 is the strongest external candidate and coincides with
shortlist A4**, where the same Bonferroni caveat already sits as a trap. Everything else on the host list is
a different portfolio, not a competitor to P0/P2.

---

## 6. Recommendation

1. **Writing capacity only:** **EXP#11 first** — 0 requests, a control stratum, two bookkeeping fixes to a
   draft. Then **absent-loop** (already audit-complete), then the **High-density short note**.
2. **One compute batch:** **video-ingestor BM25 baseline** (cheapest, local, turns a 28/28 demo into a
   comparison) or the **orbit-store load spec** (0 compute; the paper is otherwise done).
3. **One approved execution batch:** **Orbit post-fix re-measurement** first — one number turns a case study
   into a result.
4. **Do not start** the Orbit post-fix run or the EXP#46 SGLang arms without explicit approval: both are
   execution, forbidden for this record. EXP#45's aggregate arm and the auto-PR labelling are cheap but also
   not started.
5. **Do not card** gx10, open web index, agentnet, MU-PHI, locall stt or head2head.

## 7. Traps / unverified

- **Scope labels are not evidence.** "PUBLISHABLE", "COMPLETE", "validated" are self-labels; each checked one
  meant the *artefact* is finished. `deepseek-harness/BENCHMARK.md` is 3 lines of setup, and
  `research/b2-evidence.txt` / `runs/m4-b3*.txt` are agent transcripts, not results — do not cite them.
- **The 4/15 head2head flaw** cannot be repaired in place (s2/s3 frozen). Any write-up leads with it.
- **122/122 vs "0 differs".** The audit reproduced 122/122 with 0 differs, but it is the **same project's**
  U5 unit with its own reader and a re-seeded bootstrap — not third-party replication. Say "independently
  re-derived inside the project", never "externally reproduced".
- **The "zero .tex" claim** is a `find` negative over four trees; `~/Downloads` holds `.docx` proposals and
  one redacted arXiv-style PDF withheld by the secret guard. No `.tex` ≠ no manuscript.
- **Unread by the scouts (unverified here):** Duval `EXP#16` and `EXP#10` (titles only) and the high-entropy
  2×2 decomposition doc; `publish-present-compete/discussion*.md` (149 KB); TRUTH `mailsweep/state/sweep.db`
  (never queried); `GX10_COMPANION_SURFACE` and `TIER2_SERVING_EVIDENCE` (heads only); orbit-store's owning
  source repo (assumed to be the High-density fabric, **not** confirmed); the redacted Downloads PDF.
- **Nothing re-measured.** No unit and no writer ran an experiment, build, server or model request; the only
  executions were read-only `python3 -c` / `node -e` parses over files already on disk. A stale source number
  propagates unchanged — which is exactly why the EXP#11 recounts exist.

## 8. Provenance

Units: `orchestration/units/HOST-SCOUT-1.md` (Duval, publish-present-compete, TRUTH), `HOST-SCOUT-2.md`
(AND-1, High-density fabric, gx10, MU-PHI), `HOST-SCOUT-3.md` (deepseek-harness, dsh-plugins, agentnet,
background agent, auto PR tool, maintenance), `HOST-SCOUT-4.md` (video ingestor, orbit-store, locall stt,
open web index, ece449-kit, home dirs). Handoffs: `orchestration/handoffs/HOST-SCOUT-{1,2,3,4}.json`.
Cross-reference: `research/next-candidates/2026-10-24-sweep.md`. Writer: read-only, no target file opened,
**no number re-measured**.

*Read-only scout record, 2026-10-24. No model request, no server, no build, no write outside this workspace,
no git command against any target.*
