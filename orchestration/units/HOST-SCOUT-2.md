# HOST-SCOUT-2 — paper-readiness scout over four host projects (read-only)

**Status:** done · **Date:** 2026-10-23 · **Mode:** read-only reconnaissance, no execution, no git writes, no model requests.
**Hard bound:** ≤40 tool calls / 20 min. **Used:** 22 read-side calls + 2 writes + 1 message. Under bound.
**Write paths:** `orchestration/units/HOST-SCOUT-2.md`, `orchestration/handoffs/HOST-SCOUT-2.json` (only).
**Question:** which project already holds a COMPLETE experiment/analysis with real numbers and a write-up — not an idea, not a plan?

---

## 0. Verdict

| # | Project | Candidate | State | Requests to finish |
|---|---|---|---|---|
| 1 | `AND-1/EXPERIMENTS/absent-loop` | **Gap-loop ablation, 6 arms × 4 corpora** | **complete + independently re-derived** | **0 — writing only** |
| 2 | `High-density verified agent execution fabric` | **Offline-verifiable denial bundle + adversarial pass** | measured claims + red→green adversary fix; no paper-shaped artefact | 0 for a short/workshop note; ≥1 run batch (T4 witness / microVM) for a full systems paper |
| 3 | `AND-1/EXPERIMENTS/head2head-search-orch-battle` | Instrument-critique of search orchestration | complete, **self-declared design flaw** (4/15 pairs like-for-like) | 0, but weak |
| 4 | `projects/gx10-local-agent-runtime` | — | **engineering only; no measured output stored** | needs runs (and model requests — out of scope here) |
| 5 | `memory and knowledge research -  MU-PHI\` | — | **explicitly shape-only, no experiment executed** | needs a real experiment; FES is DRAFT + DORMANT |

**Nothing on this host is "already paper-ready" in the strict sense — no project has a paper draft (no `.tex`, no `.bib`, no abstract/intro/related-work/venue section anywhere in the four trees).** One candidate (`absent-loop`) is paper-ready in substance and needs only prose: every number already has a CI, an independent reproduction and a defect register.

---

## 1. `AND-1/EXPERIMENTS/absent-loop` — BEST CANDIDATE (one writing batch, 0 requests)

**Paths (exact):**
- `/home/zer0null/AND-1/EXPERIMENTS/absent-loop/FINDINGS.md` (747 lines, 8 sections, restructured for a cold reader)
- `/home/zer0null/AND-1/EXPERIMENTS/absent-loop/state/u5/audit.md` + `state/u5/audit.py` (independent audit)
- `/home/zer0null/AND-1/EXPERIMENTS/absent-loop/state/u3/REPORT.md`, `state/u4/REPORT.md`, `state/u2/REPORT.md`
- `/home/zer0null/AND-1/EXPERIMENTS/absent-loop/runner/` (`loop.py`, `meta.py`), `state/u3/run_all.sh`
- `/home/zer0null/AND-1/EXPERIMENTS/EXPERIMENTS-TRACKER.md` (owner-side dashboard, `absent-loop` marked COMPLETE)

**Question measured.** Does a gap/absence-tracking retrieval loop beat the same method with the loop OFF, and does narrowing the query each round help or hurt evidence recall? The mechanism is **already published** (FAIR-RAG, arXiv:2510.22344 — verbatim-matched in the prior-art check), so this is framed as an evaluation, not an invention.

**Already established (numbers, all with paired percentile bootstrap, B=2000, seed 20261004; audit re-seeded 424242):**
- Substrate: `hotpotqa-distractor-dev` **n=7,405**, gold min=mean=max=2, **0 excluded**; plus scifact 1,109 / nfcorpus 3,237 / fiqa 6,648 — **full n everywhere, no subsampling**. One shared BM25 (k1=1.2, b=0.75); arms differ only in query construction.
- **Loop** (#3 loop ON vs #6 loop OFF, primary, n=7,405): recall/run **0.81411 vs 0.76887, Δ +0.04524 [+0.04186, +0.04862], CI excludes 0**; recall/call **−0.26946 [−0.27583, −0.26297], excludes 0 the other way**; 664 gained / 6,741 tied / **0 lost**; **93.6 % of the gain is the second call** (marginals +0.04234 / +0.00283 / +0.00007); 4/4 corpora, signs identical.
- **Narrowing** (#3 vs #5): recall/run **−0.00459 [−0.00716, −0.00216] excludes 0 — narrow LOSES**; gold precision **−0.01655 [−0.01723, −0.01590]**, down 4/4 corpora. The documented "narrowing raises precision, costs recall" trade is **falsified**.
- **Drift refuted, collapse found:** method-A vocabulary retention **exactly 1.0** across 17,107 narrow+broad transitions; risk is repetition (narrow 0.629→0.249→0.107).
- **STOP ≠ FINISH:** sufficiency fired 5,331× → gold-complete only **63.3 %**, **premature 36.7 % of fires** (26.4 % of runs), 67 fires held 0 gold.
- **Arm 4 META:** 1st of 6 on all four corpora; vs oracle regret **+0.04571 [+0.04213, +0.04916]**, captures **94.81 %** of oracle, regret 0 on 89.3 % of questions; vs best fixed **+0.01688 [+0.01290, +0.02080]**; tie-inclusive routing accuracy **94.64 %** with **75.2 % moot turns** disclosed; precision 0.10956.
- **Verification:** **122/122 checks REPRODUCED, 0 DIFFERS, 0 COULD NOT CHECK** by U5 with its own reader and seed; worst CI-endpoint gap **0.00096**; **determinism measured = 0 variance** (pure-code chooser, all jsonl byte-identical on re-run).
- **Defect register present:** 14 U2 failure modes, 8 U3 self-caught defects, 6 U4, U5's own self-caught defect, plus a §5 "cannot claim" list. That is unusual honesty for a paper draft and is directly reusable as a Limitations section.

**Missing (writing, not computing):** abstract, intro, related work section (prior-art citations exist but are scattered in §1 and the tracker's `2026-10-02` framing-verified note), a camera-ready results table set, venue choice, figures. No re-run needed; `python3 state/u5/audit.py` regenerates the audit.

**Readiness:** **one batch** (prose + tables + one figure). **Requests: 0.**
**Venue fit:** empirical IR / RAG-evaluation workshop (e.g. a RAG or IR-evaluation workshop at ACL/EMNLP; arXiv preprint credible given the audit trail). Not a top-tier full paper: single BM25, gold-passage recall only, deterministic (non-LLM) chooser.
**Risk:** (a) novelty is low by design — it evaluates a published mechanism; (b) the loop's gain is small and lives almost entirely in call 2; (c) **U4's own disclosure**: a deterministic chooser is a *weak analogue* of an LLM router, and U4's rules were designed with U3's aggregates in hand; (d) fiqa reverses the loop's sign (naive beats loop arm, −0.01625 [−0.02196, −0.01067]). Any paper must lead with (c) and (d) or a reviewer will find them.

---

## 2. `High-density verified agent execution fabric` — STRONG MATERIAL, NO PAPER SHAPE

**Paths (exact):** `/home/zer0null/High-density verified agent execution fabric/docs/CLAIMS.md` (claim register, 9 rows), `docs/board/CLAIMS-PROVE.md` (352 lines, per-claim evidence), `docs/research/EXP#1-T1-negative-evidence.md` (§9 Result), `EXP#2`…`EXP#6`, `docs/EVAL.md` (199 lines, runnable), `docs/board/ADVERSARY-1.md` (56 lines), `docs/board/FIX-ADV.md`, `docs/PROGRAMME_LOG.md` (2,359 lines), `justfile`, `mutants.out/`.

**Already established (numbers):**
- **C1 PROVEN:** `cargo test -p fabric-core --test parity` → `8 passed; 0 failed`, live conformance run keeps grant parity per request; sibling binaries 28/28.
- **C2 PROVEN (kernel-mediated denials):** live probe journals errnos `open $HOME/…canary`→**2**, `list $HOME`→**2**, `open /usr/…canary`→**30**, `connect 203.0.113.1:80`→**101**; bundle assembled from journal alone = **4 records / 4 denials**; one byte flipped at offset 42 → `FAIL(tamper:hash-mismatch)`.
- **C3 PROVEN + narrowing recorded:** cold principal verifies from a directory of **three files**, `fabric-verify --bundle ./bundle.json --pubkey ./fabric.pub --task t6-conformance` → `OK` exit 0; `strace` shows it opens **only** those two files and makes **zero network syscalls** — but no network namespace was achieved and it was the same host (`D-020`).
- **C4 PROVEN:** two live leases → `read.tools` **4**, `write.tools` **7**, symmetric difference **3**, `stale_requests` **0**, refusal `class="unauthorized" kind=policy errno=None`, `journal_refusal_count` **1**.
- **C5 PROVEN:** drop-in to Duval sandbox → **41 PASSED · 0 FAILED · 0 SKIPPED**, changed-path set exactly `{src/fabric-backend.ts, src/sandbox.ts}`.
- **C9 PROVEN:** `entry_count=6 wall_ms=12 cpu_ms=7 verified=True`; report byte-identical from `/tmp` with no journal present.
- **Adversarial pass:** **24 probes, 2 escapes** (A1 truncated-journal re-seal; A7 re-seal under an attacker-chosen task) → `FIX-ADV` closed both (root-witness row; `--task` required), 8 new tests, re-measured `OK` under the right task / `FAIL(tamper:hash-mismatch)` under another. Red→green is already on disk.
- **Health:** `397 tests run: 397 passed, 0 skipped` (PROGRAMME_LOG tail); mutation run `mutants.out/` = **9 caught, 0 missed, 0 timeout, 0 unviable** (cargo-mutants 27.1.0, 2026-10-23) — but the mutant set is only `crates/fabric-run/src/main.rs` `KernelSyscalls` (`real_uid`, `real_gid`, `set_dumpable`, `unshare_newuser`, `write_file`, `set_no_new_privs`), so it is a narrow instrument, **not** a repo-wide mutation score.

**Missing for a paper:** no abstract/intro/related-work/venue section anywhere; **C6, C7, C8 are UNPROVEN or deferred** — no microVM second mechanism (`P4` not run), no third-party evidence suite (`agentci` T4 deferred under D-43), and **C7 is a real gap** (`DEF-C1`: bundle projects only `op=="deny"`, MCP refusals are journaled as `mcp.tool.refused`, so `denials` length **0** in a live bundle). `docs/EVAL.md` itself says "Not certified by a third party… Not a microVM… Not finished".

**Readiness:** **one batch** for a short/workshop paper on the denial-bearing, offline-verifiable record (artefact + adversary + red→green is a complete story); **more than one batch** for a full systems paper, which reviewers will want to see with an external witness and a second mechanism.
**Venue fit:** systems/security workshop or artefact-evaluation venue; the adversary-then-fix narrative is the most citable part. Claims register forbids "tamper-proof"/"deterministic replay"/"AI Act compliant" — the paper must use the permitted wording verbatim (`docs/CLAIMS.md` §3).
**Risk:** the two escapes are the finding, not a footnote — a paper that reports only the 22 non-escapes would be the exact overclaim `docs/CLAIMS.md` exists to prevent. Also `scripts/claims-lint` (D11) gates commits, so any paper text placed in-tree must pass it.

---

## 3. `AND-1/EXPERIMENTS/head2head-search-orch-battle` — complete, but its own verdict is weak

**Paths:** `/home/zer0null/AND-1/EXPERIMENTS/head2head-search-orch-battle/FINDINGS.md`, `FINDINGS-STAGE1-{GATE,MATERIAL,INSTRUMENT,RESULTS,SCORER,DEFECTS,WAVE}.md`, `state/material-review/qualitative.md`.
**Established:** gate **36/36 PASSED** (34 scored, 2 discarded, 12 condition rows); best quality/cost **NAIVE 0.714** > F/BLIND 0.577 > A/LEDGER 0.545; worst **E/LEDGER 0.185**; the control (one search) scored recall@8 **1.00**; `EA1_A_LEDGER` 7,152 tok density 0.912 vs `EA1_D_BLIND` 25,443 tok density 0.000; the headline **4 of 15 pairs like-for-like**.
**Missing:** the design flaw is large (only 4/15 like-for-like) and s2/s3 are frozen, so it cannot be repaired — it is an **instrument-critique note**, not a results paper.
**Readiness:** one batch, 0 requests. **Venue fit:** short methodological note. **Risk:** low impact; already superseded in the tracker by `absent-loop`.

---

## 4. `projects/gx10-local-agent-runtime` — engineering only, nothing measured stored

**Paths:** `/home/zer0null/projects/gx10-local-agent-runtime/README.md` (17 lines), `IMPLEMENTATION.md` (85), `FLASHNEXT_DEPLOYMENT.md` (83), `deploy/` (11 systemd units + `benchmark-ornith15-dflash2.py`, `qualify-flashnext.mjs`, `qwen38-mtp-sweep.mjs`, `test-effort-adapter.mjs`, LiteLLM configs), `vendor/qwen3.8-Flash-DGX/docs/`.
**Established:** a coherent deployment topology (LiteLLM at `192.168.2.168:8000/v1`, llama.cpp :8080, vLLM :8002 loopback-only, keyless LAN, MTP depth 3 "validated GB10 profile") and a capability contract table.
**Missing:** **no stored benchmark output** — a repo-wide find for `*.json|*.jsonl|*.csv` returns only vendor docs; every measurement is a *script* (`qualify-flashnext.mjs`, `qwen38-mtp-sweep.mjs`) with no result artefact committed, and the README/IMPLEMENTATION are architecture prose. "Validated" appears with no number attached anywhere I read.
**Readiness:** **not paper-ready**; needs runs (which require model/server requests — outside this scout's rules). **Venue fit:** an experience/deployment report at best. **Risk:** "validated" is currently an unsupported adjective — that is exactly the defect mode the other two projects have registries to prevent.

---

## 5. `memory and knowledge research -  MU-PHI\` — shape-only by its own README

**Paths:** `/home/zer0null/memory and knowledge research -  MU-PHI\/README.md` (86 lines), `AGENTS.md` (462), `docs/70-search/00-synthesis.md` (FES rev 9), `docs/70-search/evidence/verify-*.md` (12 files), `prototypes/{phase0-recall,phase1-gates,phase2-commit,fes-engine}`, `reference/benchmarks.md`.
**What the repo says about itself (verbatim, README):** prototypes are "sandbox-grade… neither promoted nor production"; "**There is no store and no LLM** anywhere in this repository"; "**Every experiment run so far is a *shape* verification** — a mechanical check that a return conforms to its declared type. **Nothing here proves retrieval quality.**"
**Checked:** the `verify-*` files in `docs/70-search/evidence/` are **document-review verdicts on spec text** (pinned blob hashes, md5/sha256, HELD verdicts), not retrieval metrics; `docs/70-search/00-synthesis.md` is **DRAFT**, "no file in this workstream is frozen", and the system is **DORMANT** — standing state `egress-ungranted`, nothing executes until an operator mints an `EgressClass.ExternalSearch` grant.
**Readiness:** **not paper-ready**; needs a designed experiment plus a run. **Venue fit:** none yet (design corpus). **Risk:** a paper built from this tree today would report document audits as if they were results; the README is explicit that nothing here proves quality.

---

## 6. What was NOT done (scope discipline)

No builds, no tests, no servers, no model requests, no git writes, no file in any target tree read-modified; `git` was not invoked at all against `/home/zer0null/Duval`. Every number above is quoted from a file on disk at the path given, not re-measured.
