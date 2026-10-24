# UCORR1 — apply UP2's corrections and additions to `strategy/PAPER_CANDIDATES.md`

**Unit:** UCORR1 · **Date:** 2026-10-14 · **Status:** done
**Work order:** [`strategy/PAPER_CANDIDATES_SUPPLEMENT.md`](../../strategy/PAPER_CANDIDATES_SUPPLEMENT.md) (UP2, 305 lines) — read in full.
**Purpose (one):** apply UP2's corrections and additions so the inventory does not overstate what is novel,
**without deleting or weakening anything that is actually true**.

**Hard bound:** 45 tool calls. Used **30**.
**Write paths (touched nothing else):** `strategy/PAPER_CANDIDATES.md`, `orchestration/units/UCORR1.md`,
`orchestration/handoffs/UCORR1.json`.
**Target:** `/home/zer0null/Duval` — **read-only**. Every target command was `sed`/`grep`/`ls`; no write, no
state-changing `git`, no hook. Confirmed correction: the orchestrator had already verified V13.

## Result

`strategy/PAPER_CANDIDATES.md` 710 → **970 lines**. **7/7 corrections applied, 0 refused, 1 candidate added,
A1 narrowed, 0 existing ranks changed.**

1. **A1 narrowed (correction 1).** Thesis restated as *"no shipping agent runtime exposes a
   machine-checkable resume contract or a first-class unknown-effect state"*; new item 7 states the
   resume-contract **observation is prior-published** (arXiv:2608.03836 = V13, arXiv:2608.29381 = V14;
   `SOURCE_VERIFICATION.md:35–36`, `:46`, `:101–105`) while the **construction** is unoccupied. The
   contribution was restated, not deleted; citation to V13/2608.03836 kept.
2. **A1 substrate (correction 2).** Added the decision-log grounding: D-001/D-002 **as refined by D-023**
   (`:567`), plus D-042 (`:1216`), D-051 (`:1648`), D-009 (`:155`), D-039 (`:1123`) and **D-058 (`:1993`)** —
   the last recording the *measured* `ee2852ce…` vs `5d34ff6b…` `epoch`-hash defect. The log was cited 0
   times before.
3. **A2 (correction 3).** Added the externally verified gap statement — V24 Letta, model-agnostic with
   mid-conversation swaps and *"No measurement of behavioural continuity across a swap was found"*
   (`SOURCE_VERIFICATION.md:51`).
4. **§D (correction 4).** `"the corpus is fully accounted for. 30 documents."` → §D accounts for
   `docs/research/` only; the measured census is stated (38 root `docs/*.md` / 2,060,775 B, one cited;
   `DECISION_LOG`/`MISTAKES`/`EVALS.md`/`BUILD_PLAN`/`K0_BUILD_PATH`/`BACKLOG`/`EXPERIMENT_SM_PILOT` cited 0×;
   `source-material/` correctly excluded). The M1–M14 §D note is marked **superseded by NC1** and retained
   as the record of the decision it supersedes.
5. **SM pilot (correction 5).** Pre-registration and its **recorded VOID** against the authors' own 53.8 %
   headline now cited (`EXPERIMENT_SM_PILOT.md:251–263`, `:284–286`, `:289+`) in **A1 item 8 and B8/#8**.
6. **#9 (correction 6).** Added `BUILD_PLAN.md:123–186` ("RUN 36 STOPPED — a reproducible death"),
   **D-116 `:5685` / D-117 `:5771` / D-127 `:6432`**, and **D-098 `:4553` / D-099 `:4594`**.
7. **Method paragraph (correction 7).** The ledger was read and then unused; it is now named as the
   novelty-narrowing instrument (`PAPER_DERIVATION.md:35–37`) and cited in A1, A2 and new §F7.

**Added — `NC1` · *Detectors that cannot fail* (rank 6½, between #6 and #7)** with the same field set
(working title, thesis, contribution type, evidence base, closeness, what is missing, venue class, risk).
Evidence: `MISTAKES.md:1–31`, `:386–388` (19 classes, 12/3/4, count enforced by `evals/prevention.ts` —
`ID = "prevention.detector-coverage"`), `:417`, `:522–575`, `:576–605` (13 mutations → 8 survived green at
33/33; 20 mutations → 17 RED / 3 inert; 41/41 dormant guard), `DECISION_LOG.md:4368` D-096
(`18 assertions, 0 failure(s)` at `:4382`, tautology via `get()` by reference, 7 of 9 shapes missed),
`EVALS.md:49/130/240/396`, `EXPERIMENT_SM_PILOT.md:251–263/:284–286`, `evidence/gates-2026-10-11/RUN.md:1–5`,
`WORKSTREAM_RECOVERY_PLAN.md:28–37`. It **supersedes the §D M1–M14 note**; the missing M1–M14 cross-walk is
named (M11/M12 have no class; 15 of 19 classes have no M-id). Ranking table row **6½**, publishable-now list
8 → **9**.

**Negative result recorded (correction set item 5 of the card):** no second labeller, no external benchmark
and no independent corpus exists anywhere outside `docs/research/`; the external-validity caveat on every
strong candidate is **unchanged** (stated in the errata header and §F2).

**Append-only discipline.** A dated **ERRATA HEADER** at the top lists what was corrected, by which unit
(UCORR1, applying UP2), on what evidence, and that the original claims were re-verified before being
narrowed. Corrections are inline and dated; nothing was silently rewritten.

## Deviations / notes for the verifier

- **Correction 5's line anchor.** UP2 anchored it at *"#6, `:295–336`"*, but **B6 cites no SM-pilot file**
  (it cites EXP#13/#14/#16). `SM_PILOT_RESULTS.md` is cited at `:393` in **B8/#8**, and the pre-registration
  lives in the same pilot. The **substance was verified against `EXPERIMENT_SM_PILOT.md` and applied at A1
  and B8**; the discrepancy is recorded inline at the B8 bullet and in the errata header. Not counted as a
  refusal — the correction's content is true and applied.
- **Ranks.** NC1 uses a half-rank (6½) so that **no existing rank is renumbered** and every §E
  cross-reference stays valid. Per-candidate *"Rank N of 14"* labels are retained as historical; the errata
  header says so.
- **Left untouched (re-verified true):** A1's *"nothing was promoted into `src/`"* gap; A2's 244/244 zero
  control and 41.8 %/32.2 %; §F1; §F6. **EXP#11 / EXP#12 / EXP#7 statistics are unmodified** (spot-checked
  after editing: 4,090 / 3,590 / p = 0.0156 / 4.167e−09 / 244/244 / 0.3474 / 0.6684 all still present).

## Evidence commands (all read-only against the target)

```
sed -n '33,52p;99,106p' docs/consolidation/SOURCE_VERIFICATION.md
for n in 8 28 155 567 1123 1216 1648 1993 4368 4553 4594 5685 5771 6432; do sed -n "${n}p" docs/DECISION_LOG.md; done
sed -n '384,390p;415,419p;524,530p;531,575p;576,605p' docs/MISTAKES.md
sed -n '123p;180p' docs/BUILD_PLAN.md ; sed -n '251,263p;284,292p' docs/EXPERIMENT_SM_PILOT.md
sed -n '49p;130p;240p;396p' docs/EVALS.md ; sed -n '1,5p' docs/evidence/gates-2026-10-11/RUN.md
sed -n '28,37p' guidance/recovery/WORKSTREAM_RECOVERY_PLAN.md
ls -l evals/prevention.ts ; grep -n 'detector-coverage' evals/prevention.ts
sed -n '85,95p' docs/research/PAPER_DERIVATION.md
grep -c '<path>' strategy/PAPER_CANDIDATES.md   # citation census
wc -l strategy/PAPER_CANDIDATES.md              # 710 -> 970
```

## Next

A verifier that is not this unit should re-check: (a) that A1's thesis no longer overstates while its
contribution survives; (b) that every new citation resolves to the quoted text at the quoted line; (c) that
the EXP#7/EXP#11/EXP#12 numbers are unchanged; (d) red→green on one guard of the census claim (removing the
new §D census sentence must not break anything else, and the census must fail if `MISTAKES.md` is claimed
cited).
