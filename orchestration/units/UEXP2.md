# UEXP2 — second-labeller-190, second-model robustness pass

**One purpose:** re-run UEXP's pre-registered blind Route B labelling over the 190-case fixture
with a **different model** as the blind reader, and report whether κ = 0.901 replicates,
collapses, or exceeds — with the disagreement structure compared to UEXP's.

**Target:** `/home/zer0null/Duval` — READ ONLY (HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`
unchanged before/after; 8 in-window target files, all under `.git/objects/`, mtime 14:38:30 CDT
= before UEXP2's first command, attributed to the unrelated concurrent session).
**Sandbox:** `experiments/second-labeller-190/` (extended, nothing wiped).
**Hard bound:** ≤50 tool calls (used ≈27; not exceeded).

## Method (identical protocol, one changed variable)

- Reused UEXP's `blinded_cases.json` and frozen `PREREGISTRATION.md`; blinding NOT re-derived.
- Blind reader: fresh-context subagent on `keyring/mimo-v2.6-flash`, pre-registered Route B
  prompt verbatim except output path `labelsB.json` → `labelsB2.json` (protects UEXP's frozen
  record). First attempt failed (subagent token limit, no file written); retry succeeded with one
  operational line added (write JSON via shell, don't print). Both deviations recorded.
- UEXP2 itself did NOT label: it had to read `EVIDENCE.md` (disagreement catalogue) per this
  card, so blindness was preserved by delegation, exactly as UEXP designed.
- `labelsB.json` records no model id; distinctness rests on UEXP's own note calling the stood-down
  labelsB2 pass "distinct-model (mimo-v2.6-flash)". Ambiguity recorded, not silently resolved.

## Result (full detail: ROBUSTNESS.md, RUN2.json, metrics2.json, disagreementsB2.jsonl)

| Comparison | agreement | κ |
|---|---|---|
| B2 (mimo-v2.6-flash) vs fixture | 0.8632 | 0.8577 |
| UEXP vs fixture (recomputed sanity check: matches RUN.json) | 0.9053 | 0.9014 |
| **B2 vs UEXP (model-to-model, new quantity)** | **0.9158** | **0.9125** |

**Verdict: PARTIAL replication.** Same weak dimensions for both readers (`memory.admission`
κ_B2 = 0.563 weakest, `acquisition` second); 14-case contested core replicates (all four
`acquisition` traps, `topology-018`, `capability.family-004/009`, …); B2-only tail of 12
scattered items is reader-specific noise, not new defects. **UEXP's systematic finding
replicated 4/4**: both blind readers say `DROP` (record: `EPHEMERAL`) on never-re-read
step-scoped scratch (`memory.admission-001/009/021/027`) → **real systematic ambiguity at the
tier boundary, the fixture's top repair item.** Arity test: accuracy tracks option arity for
*both* readers (B2 0.970→0.722, UEXP 1.000→0.815 from 2- to 5-option cases), confounded with
kind and not consistent with pure option-wording exploitation — but it weakens any blanket
"labels are sound" for the high-arity closed-roster kinds.

## ⚠ Limitation (in-band, travels with every number)

**A model is not an independent human annotator.** κ = 0.9125 between two models is **not**
inter-annotator agreement and must never be cited as such. This bounds *machine* reproducibility
for exactly two models on one fixture; it does not discharge `PAPER_CANDIDATES.md` §F.3 — only a
second independent **human** labeller does that.

## Declared write paths (all respected)

`experiments/second-labeller-190/` (new files only: `labelsB2.json`, `compare2.py`,
`metrics2.json`, `disagreementsB2.jsonl`, `ROBUSTNESS.md`, `RUN2.json`),
`orchestration/units/UEXP2.md`, `orchestration/handoffs/UEXP2.json`. No writes to the target,
`journal/`, `strategy/`, `jobs/`, or UEXP's artifacts. `compare.py` deliberately NOT re-run
(it would overwrite UEXP's `metrics.json`/`disagreements.jsonl`).
