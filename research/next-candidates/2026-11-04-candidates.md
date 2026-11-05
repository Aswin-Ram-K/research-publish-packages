# Paper candidates — sweep of 2026-10-24 → 2026-11-04

**What this is.** The candidate record for the question: *what is the next high-quality paper this workspace can
actually publish?* It follows the previous candidate sweep (`2026-10-24-sweep.md`, branch
`research/next-candidates-2026-10-24`) and covers only work produced **after** the last compile/publish:
`papers/context-cache/MANUSCRIPT.md` was last sealed 2026-10-24 21:39 and the three filed papers
(encoder-crossover-190, replay-record-not-decision, gated-read-batching) went out 2026-10-19.

**Branch policy.** This record lives on `research/paper-candidates-2026-11-04`, **not** on the session worktree
and **not** on `research/next-candidates-2026-10-24`. Keep the branch until the owner picks the work up from the
real repository. Do not prune it, do not squash it into the previous candidate branch, and do not rewrite its
history.

**Provenance.** Four briefs, each composed from primary evidence (`*.jsonl` rows, `analysis.json`, claim files)
by a separate read-only unit with an explicit instruction not to fabricate and to label anything unverified;
the session that owns this branch materialised them and is responsible for their content. Every number in them
carries a file path. Where the record disagrees with itself the brief states the disagreement instead of
picking a winner silently.

---

## What is genuinely new since the last compile

| Date | Finding | Where |
|---|---|---|
| 2026-10-26 | **The append-cost law**: `uncached = (P1 mod B) + L`, residual 0 in 186/186 rows; a residue-0/1 cliff that re-bills the prefix; vLLM's `+B` term | `experiments/miss-law/LAW.md` |
| 2026-10-26 | The fetch-count sign flip (+44.8 % → −95.6 %) is the **cold arm**, not block boundaries (≤3.7 % of the swing) | `LAW.md` §6 |
| 2026-10-28 | **The quality emitter cannot say yes** (`PATH-CANNOT-SAY-YES`): five-log truth table, four negatives indistinguishable from the positive, two mutually exclusive graders | `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md` |
| 2026-10-28 | **Four instrument defects in one live grid**; H1 `not_adjudicable_floor` at n_eff 26.14 < 60; p95 refused | `docs/GRID-2-FINAL.md`, `docs/GRID-GAP-DIAGNOSIS.md` |
| 2026-10-28 | Ledger reconciliation made delta-aware after a stale freeze refused every launch | `docs/LEDGER-RECONCILE.md` |
| 2026-11-03 | Consonance BRCV report + prospective protocol, both rechecked PASS at **0 live calls**; the comparative is `UNFUNDED` (7,560 vs 1,729) | `consonance-bounded-context-report.md`, `consonance-bounded-context-evaluation.md` |

## Ranking

| # | Brief | One-line thesis | New requests | Verdict |
|---|---|---|---|---|
| **1** | [`N1-residue-law.md`](N1-residue-law.md) | An append costs `(P1 mod B) + L`; at residue 0/1 the cache entry is gone; two tokens of padding defuse it | **0** | **Best new paper.** Closed-form law, exact fit, a discontinuity worth four orders of magnitude, a cheap intervention, and a refuted alternative explanation. Concession: the cliff's magnitude is instrument-dependent and its mechanism is unexplained. |
| 2 | [`N2-instrument-liveness.md`](N2-instrument-liveness.md) | An instrument must prove it can say yes and no before its nulls count | **0** | Strong, cheap, and self-contained; a methods/case-series paper, narrower audience, and it lives on the workspace's own failures. |
| 3 | [`N4-finish-flagship.md`](N4-finish-flagship.md) | The best paper is the drafted one: 1,892 uncited rows fold in for free | **0** (≈90 optional) | Not new research, but the precondition for submitting anything. Seven cells are uncited and two numbers are wrong. |
| 4 | [`N3-the-wall.md`](N3-the-wall.md) | The wall's cost is a window decision, not a boundary event | ~**920** | Real but expensive, and it rides on magnitude: S and F already fail to separate at 64k. Displaces the Round-2 subset. |

**Not paper-ready.** The Consonance BRCV program (report + protocol, both PASS) is a *prospective* design with
no measurement: the comparative is 7,560 requests against 1,729 remaining = 4.37× ⇒ `UNFUNDED`. Its funded
alternative is a 185-call instrument pilot. Nothing here should be written up as a result.

## The recommendation

Write **N1**, then **N4**. N1 is the only candidate that is simultaneously (a) a law rather than a
measurement, (b) reproducible to the digit offline, (c) actionable by a reader in a few lines of code, and
(d) not already inside the in-draft paper — the manuscript's §9 covers immediate-repeat misses and §9a covers
the per-stack grid, but neither states the append law, the vLLM `+B` term, or the two-token rule, and §8a
argues the *opposite* way about padding.

Two things must be settled in the paper's own text before submission, and both are named in the brief:
the **instrument-dependent magnitude** of the cliff (`RECORD.md` C1 reads 64 + L on a second instrument where
`LAW.md` reads the whole prefix), and the **scope collision** with the manuscript's `L − 64` recovery result,
which is a different request shape (immediate repeat vs one append). A paper that hides either one will be
caught in the first review round; a paper that states both is stronger than either source alone.

N4 is the second move because it costs nothing and unblocks a submission that has been sitting since 2026-10-24
with four datasets on disk that its own manuscript does not cite.
