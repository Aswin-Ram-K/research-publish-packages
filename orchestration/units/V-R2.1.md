# V-R2.1 — verifier verdict on rule R2.1

**overall: partial** — all five checks hold (including my own red case and my own
tokenizer); one sentence inside the frozen normative body is false and needs a named fix.

Offline unit: 0 network requests, 0 live model calls, 0 re-grades. No artifact edited.

## 1. The guard is real, and it can go red

| check | command | literal result |
|---|---|---|
| tests green | `python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py` | exit **0**, `Ran 15 tests in 0.014s` / `OK` |
| tests red | real suite against `/tmp/vr21/anchor_classify.py`, matcher degraded to substring containment (`if key not in tok.string.lower():`) | exit **1**, `FAILED (failures=2)` — `RedTest.test_record_is_not_satisfied_by_recording` and `DivergenceTest.test_budget_is_prose_in_both_divergence_families` |

The degradation was made in the copy only (`/tmp/vr21`), confirmed by `diff`; the single
extra line in the copy pins `ROOT` to the workspace because the copy lives outside it.

## 2. Probe corpus — exit 0, six verdicts as claimed

`python3 experiments/ptr-engine/tools/anchor_probes.py` → exit **0**, `RESULT: PASS`,
`A=ACCEPT B=REJECT C-minimal=ACCEPT C-global=REJECT E=ACCEPT F=ACCEPT`.

The two that could have been embarrassing:

- **C-minimal = ACCEPT, labelled ACCEPT.** The R2 round's claim that this edit was
  rejected does not reproduce. `scope` survives in `scope_name` (`['scope','name']`).
- **E = ACCEPT, `metric: mention-only`, `semantic: false`**, described in the rule body
  (g) as a *known, accepted limitation*. It is reported nowhere as a semantic failure
  and nowhere as a semantic pass.

## 3. Digest — it attests the text, not the clock

Recomputed `rule_digest` = `b1654830…eb9ad57`, equal to the recorded value. The hashed
region is the 60 lines strictly between the markers at `:45` and `:106` — the whole
normative rule, read by a third party as the rule. `ANCHOR-PREREG.md` has no rule-body
digest at all, so **R2's freeze was unverifiable and R2.1's is attested**. The stated
instant `2026-10-26T13:46:53Z` is 34 s *before* the doc's mtime; body↔digest equality
proves the body on disk is the hashed text, but the instant itself is author-claimed.

## 4. The two divergence cases, my own tokenizer

Independent `tokenize` (Python 3.14.4): `resolve.py:143` `spent` sits in
`FSTRING_MIDDLE (143,143)`; `resolve.py:47` `budget` sits in `STRING (44,50)`. Both
prose; both PROSE-CONNECTOR in my run; R2.1 agrees.

## 5. Census and the demotion question

My own census reproduces 11/11 (8 CODE-SYMBOL, 2 NUMBER, 1 PROSE-CONNECTOR).
R2 whole-file vs R2.1 range-scoped, cell by cell: **0 cells demoted**. All 8 keep an
in-range NAME part; only `ledger` (:33→:66) and `scope` (:43→:66) change their evidence
line, which §1.1 discloses. The demotion mechanism is real but unexercised by these 11
cells — a *narrower* future citation would demote and would silently require fewer tokens.

## The named fix (why `partial`, not `pass`)

`ANCHOR-PREREG-V2.md:59-60`, inside the frozen body, is false under its own rule:
"`PtrBudgetExceededError` carries `ptr` and `exceeded` and `error` but **not** `budget`."
The classifier splits NAME tokens on `_` only, so the token is one part,
`ptrbudgetexceedederror`, and carries none of the four; and any camel reading that yields
ptr/exceeded/error also yields budget. Doc `:117` already contradicts it. Replacement:
"`PtrBudgetExceededError` is a single part, `ptrbudgetexceedederror`, because the token
has no underscore: it carries neither `ptr`, `exceeded`, `error` nor `budget`."

No census cell depends on it (camel splitting moves 0/11) — a text defect, not a metric
defect. Secondary: (a) says "underscore-separated parts" for *every* token, but the
prose path splits on any non-alphanumeric (that is how `raising` in `re-raising` is
found); class unaffected, evidence line affected.
