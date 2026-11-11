# Journal index — 2026-09-28 … 2026-11-10

Two eras. The **Consonance/Duval era** below (15 notes, 2026-09-28 … 2026-10-13) is indexed by Duval
commit count and anchor commit. The **campaign era** (2026-10-26 → present, second table) is indexed by
the unit/handoff that owns each note, because this repo's own history is uncommitted and the anchors
that matter are handoffs, not commits. 2026-10-03 has no note: **no work recorded (0 commits)**.
Commit counts are
author-date counts over all refs (`git -C /home/zer0null/Duval log --all`); the anchor is the commit
carrying that day's headline claim. Corrected by unit UJC1.

| Date | Headline | Commits | Anchor |
|---|---|---|---|
| [2026-09-28](2026-09-28.md) | DUVAL M0 exists; eval, prevention, trace and sandbox layers land on the state primitive | 19 | `dae60e0` |
| [2026-09-29](2026-09-29.md) | Design of record converges on Consonance; first two real measurements land (9,260 gated-read rows; ladder priced) | 17 | `cc96222` |
| [2026-09-30](2026-09-30.md) | Two live pilots scored honestly: 3-model engine 280 runs; single-agent state machine DR1 not supported | 11 | `98d432e` |
| [2026-10-01](2026-10-01.md) | Biggest day in the window: eight preregistered experiments emerged, the paper completed, gated-read at horizon sweep | 140 | `14cc11e` |
| [2026-10-02](2026-10-02.md) | EXP#10 closed on its own falsifier; the session written into one document; ornith thinking OFF proven live | 12 | `7af0f7a` |
| 2026-10-03 | **no work recorded (0 commits)** | 0 | — |
| [2026-10-04](2026-10-04.md) | EXP#11 and EXP#12 closed; four identity hazards resolved; P0 constitution pinned; teardown falsifier fired live | 148 | `fb74fbd` |
| [2026-10-05](2026-10-05.md) | EXP#13 and EXP#14 both EMERGE; verifier-found tracker/gate defects fixed by name; Actions removed | 143 | `9b3ca96` |
| [2026-10-06](2026-10-06.md) | K0 redirection lands with its Phase 1 plan; external review of the Consonance monograph written | 6 | `99d8ca6` |
| [2026-10-07](2026-10-07.md) | EXP#16 answers T6 as a plan-time hybrid; K0 Phase 1 primitives land; 16 invariants become code | 39 | `514ff58` |
| [2026-10-08](2026-10-08.md) | Self-build engine built and its first pre-registered cycle fails honestly: no candidate, seam unsatisfiable | 45 | `a117ecd` |
| [2026-10-09](2026-10-09.md) | Tier-2 model survey lands and corrects a claim of our own; search router removed; kernel gets its seed | 28 | `1aa1431` |
| [2026-10-10](2026-10-10.md) | Tier 2 locked to Qwen3.5-9B/FP8; first kernel run read as the most important negative result produced | 46 | `50cf9ad` |
| [2026-10-11](2026-10-11.md) | Judge boundary closed in the goal seed; trace overclaim corrected in every site; project PAUSED | 39 | `e0b786a` |
| [2026-10-12](2026-10-12.md) | Minimal State-driven kernel planned and built by six workstreams after Gate 0 RED → GREEN | 127 | `db1554c` |
| [2026-10-13](2026-10-13.md) | Pilot evaluator assembled; "authenticity gate" measured caller-controlled; EXP#22 closes EMERGE with no satisfying source | 94 | `65bc07a` |

## Campaign era — the ptr-engine measurement campaign

| Date | Headline | Owner anchor |
|---|---|---|
| [2026-10-26](2026-10-26.md) | CANARY-ERA-B-4 stopped at gate 2 on the launcher's ledger refusal — zero requests sent | `orchestration/handoffs/CANARY-ERA-B-4.json` |
| [2026-10-27](2026-10-27.md) | 16-cell gen-6 grid run; verdict `not_adjudicable_floor`; ledger 2,591/4,320 after the batch | `orchestration/handoffs/GRID-RUN-2.json`, `GRID-2-FINAL.json` |
| [2026-10-28](2026-10-28.md) | Session reorientation: agent contract rewritten, state page + doc index + doc guard added; ledger rebuilt to 2,591/1,729 | this note |
| [2026-11-03](2026-11-03.md) | Consonance bounded-context research filed: report + prospective protocol, both PASS after repair (E2 ≤120 → 123 descriptive; comparative 6,300 → 7,560 = 4.37× ⇒ UNFUNDED); 0 live calls, no build | `orchestration/handoffs/V-CONSONANCE-BC-REPORT-RECHECK.json`, `V-CONSONANCE-BC-EVAL-RECHECK.json` |
| [2026-11-04](2026-11-04.md) | Paper-candidate sweep of everything since the 2026-10-24 compile: four one-page briefs, N1 (append-cost residue law) recommended, six numbers corrected by independent re-check; recorded on branch `research/paper-candidates-2026-11-04`, 0 requests | `orchestration/handoffs/PAPER-CANDIDATES-2026-11-04.json` |
| [2026-11-06](2026-11-06.md) | Research seed package: evidence warrants **two** papers (append-cost law flagship + instrument-validity methods), with kill criteria and a staged roadmap; corrections folded (5,403 uncited rows not 1,892; 69 claims not 63); 0 requests | `experiments/ptr-engine/research-seed-concepts/README.md` |
| [2026-11-10](2026-11-10.md) | Serving/context programme executed: preservation landed (research branch only — `origin/main` never moved) and the leaked-tree `origin/main` merge reverted; findings ledger checked; layer compiler built **and wired** as the `spcc` arm; launch script + no-fork decision; memory allowance as a supervisor chain (`VERIFIED` last resort); E1–E6 pre-registered; suite 86 failed → 5 failed of 806 passed, and the masking claim corrected to 12/48 + 8/48 (all d=2, 0/36 beyond), and the live billing **plumbing** proof run (100 turns, cached/prompt 0.917821) with accuracy on that arm unproven | `orchestration/handoffs/U-SPCC-0.json` … `U-SPCC-9C.json`, `U-SPCC-CLOSE.json` |
| [2026-11-11](2026-11-11.md) | Crash recovery: the frontier was intact (`de048d6`, pushed, clean tree, no stray process, released lock) and nothing in code was lost — the crash cost the close-out of `U-SPCC-69`…`U-SPCC-73`, now journaled; corpus re-measured at **103 files / 10,167 rows** so the ledger headroom is **1,927** not 4,125 and the Consonance comparative is 3.923×; `REQUEST-LEDGER.json` is stale and cannot be rebuilt while the 4,320 default cap refuses the write (exit 4); `test_verdict_ritual` green, `test_journal_lint` red at 360 new misses, `test_request_ledger` red at 5,847 over. **Then** the compaction/cache design: measured that a fold's re-prefill is **0.05 %** of prompt units and its drop saving is **6.38 % → 0.88 %** as L0 grows, that `billed_of` prices a cached token at **zero** so a pin costs 0 units here and 480 at 0.1× against a re-fetch's ~1,627, and wrote `docs/COMPACTION-CACHE-DESIGN.md` + E7's pre-registration (4 arms, 1,000 requests, gated on the cap decision); prior art then folded in and **confirmed** the design (CONPACT 17 % constraint retention / 30-of-100 forbidden deletes; Missing Boundary 0 % vs 87 % loss of control; codex#25792 97 %→42 %) and added four pin rules (cap-and-refuse, turn stamp, supersede, sanitise); 0 requests | `orchestration/handoffs/U-SPCC-73.json`, `docs/STATE.md` §6, `docs/COMPACTION-CACHE-DESIGN.md`, `experiments/ptr-engine/research-seed-concepts/PREREG-COMPACTION.md` |
