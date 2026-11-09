# UNIT V-FIXTURE-V8 — audit the fixture the grid will actually run on

**Bound:** ≤20 tool calls, **0 network requests**. **Status:** done. **Verdict:** PASS.

## Why this unit exists

`FIXTURE-TREATMENTS` authored `tasks-v6/LR-01.v8.json` (22:02, 57,242 B) and `RUN-A*` now runs on v8,
not v7. `V-FIXTURE-V7` verified the *v7* twelve truths; nobody had audited v8. If the treatment work
had touched a checkpoint, the grid would grade against a ruler no audit had blessed.

## Objective

Five ordered checks, deriving from source **before** opening the fixture:

1. **Truth independence** — derive all 12 expected values from `resolve.py` / `errors.py` (AST), compare.
   Report agree/disagree/ambiguous per id with the source line quoted.
2. **v7 → v8 delta** — list every changed JSON path; anything under
   `wall_tokens*`, `lease_reopen_turns`, `treatments`, `expected_digests` is expected; any change to a
   checkpoint id, expected value, turn, `system_prompt`, or the answer contract is a **finding**.
3. **The 3 NONE ids stay unanswerable by construction** — show why, and that v8 still requires
   `ANSWER: NONE` where v7 did.
4. **Loadability** — all 12 ids load; none silently absent; CALL argument sets **exact, not subsets**;
   `\u003d` decodes to `=`.
5. **A mutant that must go red** — flip one truth in a `/tmp` copy and show the audit naming the id.

## Method

AST census of `ptr_engine/errors.py` and `ptr_engine/resolve.py` was run and recorded **before** the v8
`checkpoints[]` array was read. Each checkpoint was then re-derived by executing its own
`answer_spec.derive` rule (`constant_value`, `count_classes`, `call_inside_function`, `call_at_line`,
`no_attr_call_inside_function`) against source, and compared structurally — callee, kwarg name set,
non-elided values — never by string equality against the fixture.

## Results

- **1. Truths:** 12 agree / 0 disagree / 0 ambiguous. Kinds NUM 5 · CALL 4 · NONE 3.
- **2. Delta:** `checkpoints[]` byte-identical to v7; per-checkpoint field diffs **none**. 32 changed doc
  paths, all treatment-layer. **Critical paths changed: NONE.** Only extras: `fixture_version` label and a
  new `supersedes.*` self-description.
- **3. NONE:** all three decidable by construction (`resolve()` body has no `record_refusal`;
  `_refuse()` body has `record_refusal` only — no `resolved_count`, no `block`). Same 3 ids as v7, same
  `ANSWER: NONE` contract in both. Wrong answer exists one frame down (`_refuse` at `resolve.py:155`).
- **4. Loadability:** 12/12 ids, unique, all fields present; CALL kwarg sets exact 5/0/0/3; no literal
  `\u003d` in the file; `\u003d` decodes to `=`.
- **5. Mutants:** `64 → 65` on `cp.2.t12` → 11/1/0 EXIT=1 naming `cp.2.t12`; dropping `code` from
  `cp.11.t46` → EXIT=1; untouched v8 → 12/0/0 EXIT=0.

## Findings

- **F1** (carried) value elision is the false-pass surface: 3 of 8 substantive CALL values may be answered
  `...` and still pass; the elided `scope` on `cp.11.t46` is the discriminating value.
- **F2** (carried) CALL `expected` strings are in source order, not the contract's alphabetical order;
  `cp.11.t46` appends `, before re-raising`. Ungraded → documentation drift.
- **F3** (new) top-level `wall_tokens = 3838` is 10 tokens below v8's own first prompt (3848), by the
  fixture's own admission; it would fire at T2. The live wall is `wall_tokens_by_arm = 10616`.

## Write paths (exactly)

- `experiments/ptr-engine/measure/V-FIXTURE-V8.json`
- `docs/V-FIXTURE-V8.md`
- `orchestration/units/V-FIXTURE-V8.md`
- `orchestration/handoffs/V-FIXTURE-V8.json`
- `orchestration/journals/V-FIXTURE-V8.jsonl`

v7 and v8 were never edited; mutants lived in `/tmp` only. Offline: 0 requests.
