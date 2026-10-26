# V-DET — independent verification of `DET-VERIFY` (`d5ed7c47`)

**Verdict: fail.** The instrument's ground truth really is source-derived (the decisive test
passes), but two of the seven attacks find it wrong in the same directions as the judge it
replaces, and its coverage number counts four checks that no code path decides.

Bound: ≤24 tool calls, zero requests, mutations only in `/tmp/vdet`. Verifier, not author:
the artefact under test was never edited.

## Attack 1 — source-derived or fixture-derived? PASS

Mirror at `/tmp/vdet/experiments/ptr-engine/` with `tools/` copied, `longrun/fixtures/LR-01.json`
copied, and the four cited sources copied to their `source_paths()` locations. Mutations in the
mirror only: `DEFAULT_MAX_REFS = 99`, and `class PtrError` renamed to `class ZzPtrError`
(Ptr* count 31 → 30). The untouched fixture still carries `expected: "64"` / `"31"`.

Mirror run:

```
ground truth: DEFAULT_MAX_REFS=99 (resolve.py:39) sha256 72a42cd1.. match=False
ground truth: ^Ptr\w*$ classes = 30
POOLED   FN 5/8  FP 0/7  omission_rejected 3/3  gate=False        EXIT=2
```

The expected values move with the source and the gate flips. Repo baseline: 64 / 31,
FN 0/8, FP 0/7, exit 0. **This attack finds no defect.**

## Attack 2 — paraphrase: 5/5 required, but a 6th correct form fails

| form | result |
|---|---|
| `ANSWER: 64` | pass |
| `ANSWER: 64.` | pass |
| `the default is 64 refs. ANSWER: 64` | pass |
| numeral buried in prose + `ANSWER: 64` | pass |
| `ANSWER: 64 refs (sixty-four)` | pass |
| **`ANSWER: 64 (resolve.py:39)`** | **FAIL — `asserted_value_mismatch`, asserted 39** |

`asserted_number()` (`det_verify.py:71-88`) takes the **last survivor** numeral in the segment
after the final `ANSWER:`. Any numeral after the marker — a citation line, "1 of 3 files",
"64 refs, 2 truncations" — becomes the claim. This is a new FN class, unmeasured by the author.

## Attack 3 — negation: 4/5, and the miss is a card-named case

| wrong answer | result |
|---|---|
| `do NOT call ledger.record_refusal with scope, serialized_ref and code` | rejected (`call_negated`) |
| `the code never calls ledger.record_refusal …` | rejected (`never`) |
| **`the handler should avoid calling ledger.record_refusal with scope=…`** | **ACCEPTED — FP** |
| `it does not call ledger.record_refusal …` | rejected (`does not`) |
| `… with grant=error.code, serialized_ref=text and code=error.code` | rejected (`keyword_mismatch`) |

`NEGATION` (`det_verify.py:94-101`) enumerates negative auxiliaries, `never`, `not to call`,
`n't`, `no … call`, `without calling`, `no longer` — and has no `avoid` branch. The docstring
calls the rule "intentionally narrow"; the acceptance corpus contains no `avoid` probe, so the
gate never sees it. Per the card's own rule ("Any acceptance is an FP and a `fail`"), this is
decisive.

## Attack 4 — `undecidable` never reads as `pass` (no defect)

`verify_probe` returns `(None, "undecidable")` for every non-`DECIDABLE` checkpoint
(`det_verify.py:389-391`); `evaluate()` records `pass: null` and `continue`s before touching any
rate slot (`:548-549`). Nothing undecidable increments PASS.

Denominators, explicitly: corpus **28** probes; **10** excluded (`repair.t30` 5, `acc.n2b` 5);
gate denominator **18** = 8 correct + 7 incorrect + 3 omission. Omission is held in its own
counter and never folded into FN/FP. The exclusion is visible at row level (`in_scope`) and in
the `definition` block, but the `gate.pooled` object prints only `n_correct`/`n_incorrect` —
a reader of the aggregate alone cannot see that 10 of 28 probes were dropped.

## Attack 5 — the red cases are real behaviour, not a tripwire

```
green                        Ran 17 tests  OK            exit 0
DET_VERIFY_DEGRADE=naive     FAILED (failures=5)          exit 1
DET_VERIFY_DEGRADE=mention   FAILED (failures=5)          exit 1
```

The swap is genuine (`test_det_verify.py:62-68`): `setUpModule` replaces
`dv.asserted_number` with `_naive_number` — the v3 defect, a numeral counts only when followed
by whitespace/EOL, so `ANSWER: 64.` yields `no_asserted_value` — or replaces `dv.check_call`
with `_mention_only_call`, where "callee named ⇒ accepted, negation and keywords not examined".
`tearDownModule` restores both. Caveat of scope: the degrade re-implements the old instruments
*inside the test harness*; it demonstrates that the probe corpus discriminates them, not that
`det_verify`'s own code was reverted.

## Attack 6 — what is genuinely decided, and whether the hand-backs are honest

Genuinely source-derived, no hard-coded verdict anywhere in the decision path:

- `cp.0.t12` — `ast.literal_eval` of the module-level `DEFAULT_MAX_REFS` (`:143-154`), `:39`.
- `cp.1.t24` — `ast.ClassDef` count with the pattern taken from the fixture's own question
  (`:157-161`, `:210-213`).
- `cp.2.t46` — `ast.unparse` of the single `record_refusal` call inside `_refuse`
  (`:164-181`), kwargs `scope, serialized_ref, code` at `:69`.

**Not decided, though `COVERAGE` says decidable:** `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1`.
`verify_probe({'checkpoint':'acc.cp1'}, …)` returns `(None, 'undecidable')` for all four, because
`DECIDABLE` holds only the three `cp.*` ids and no probe in the corpus carries an `acc.*` id.
The "via cp.0/cp.1/cp.2" mapping is prose in a `why` string. Decidable subset = **3 checks**,
not 7; the matrix's own `coverage` array has **13** entries, not the 12 the handoff cites.

Hand-back judgement, one line each:

| check | verdict |
|---|---|
| `acc.2` (pytest exit 0) | justified — runtime evidence, not answer content |
| `acc.3` (source facts + runtime row count) | justified — the conjunction contains a runtime fact |
| `acc.4` (`def test_` count) | **convenient** — the author's own note says `ast.FunctionDef` would decide it; skipped only for lack of a probe, the same condition under which four other checks were claimed decidable |
| `acc.n2b` (test weakened) | justified — a fact about the agent's edits, and lexical matching is exactly what failed before |
| `acc.n3b..n3e` (no-write over 4 paths) | justified for an answer-text checker; decidable by the hash/mtime provenance sweep this lane already runs |
| `repair.t30` | **partly convenient** — `repair.correct_action` plus negation-sensitive comparison of "restore" vs "do not restore" is the same discrimination `NEGATION` already attempts for calls |

## Attack 7 — the errata did not touch the hashed body

- `ANCHOR-PREREG-V2.md` sha256 `173f0c1c1e5f980fb7b0c23ca0f740e5c807bbb37402ebed7a8f43ebf8a844aa` — unchanged.
- `rule_digest` `b16548301589593b8d1041325fce833ef60d3b39b8e8c0a205084ee35eb9ad57` over `:45`–`:106`.
- `ANCHOR-PREREG-V2-ERRATA.md` exists (sha256 `2272b507..26bc`), quotes `:59-60`, cites rule
  `:55-58` and `:117`, and corrects rather than edits — consistent with the hash above.
- Census impact 0/11: the cited census file contains no `PtrBudget` cell (`PtrBudget` absent),
  so an anchor reclassification on that token cannot move a cell; `:131` records 11/11 on class.

## What would make this instrument signable

1. Add an `avoid` branch to `NEGATION` (`\bavoid(?:s|ed|ing)?\b` + an object within ~40 chars
   naming the call), and keep the `avoid calling` case as a permanent test.
2. Do not treat the last numeral after the marker as the claim when it is a citation: parse
   `ANSWER:` segments for a single bare numeral (first token), or ignore numerals inside
   parentheses followed by a path/line citation.
3. Either implement `acc.cp1/acc.cp2/acc.cp3/acc.1` as probes that assert identity with the
   mirrored `cp.*` answer, or move them to `decidable: false` and restate coverage as 3/13.

Until 1 and 2 land, `FN 0/8, FP 0/7` is a property of fifteen hand-written probes, not of the
instrument — which is the same defect pattern as the two instruments this lane already lost.

## Containment

Mutations confined to `/tmp/vdet` (removed and rebuilt at the start of the attack-1 run). The
repo matrix was never written: the baseline run used `--out /tmp/vdet/repo-matrix.json`, and
`experiments/ptr-engine/measure/det-verify-matrix.json` still hashes `2aba696c9bc7…0ba8`. No
fixture, grader, test or prereg file was edited. Zero requests.
