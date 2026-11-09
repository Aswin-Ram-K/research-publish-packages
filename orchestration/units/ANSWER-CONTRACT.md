# UNIT `ANSWER-CONTRACT` — checkpoint answers made machine-decidable

Status: **done** (offline; zero inference requests). Wave: Part B of three cards on the shared
row seam (v1). Scope: fixture v5 + runner support + `grade_v5` + red→green guards.

## Why (evidence the card started from)
`docs/HARNESS-MAP.md` §3 ranks this the highest-value change: 13 of 40 card rounds and 386 live
requests bought answers no judge could read; marker compliance 82 % tools-off → 18 % tools-on;
grade_v3 FN 30.8 %/FP 45.5 %, grade_v4 26.9 %/50.0 % (`measure/GRADER-FITNESS.md`).
`docs/EXTERNAL-EVAL-PRACTICE.md`: established suites grade an **effect**, never prose tokens.

## What was built

### 1. Fixture v5 — `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json`
Derived from `tasks-v4/runtime-v4/LR-01.v4.json` (sha256 recorded in `derived_from`). Same 48
turns, same three checkpoints, **same questions and same expected strings** (asserted programmatically
against `tasks-v4/LR-01.v4.json`). Added:
- `system_prompt`: the v4 tail (“End every answer with a final line: ANSWER: …”) replaced by the
  **ANSWER CONTRACT block, verbatim**: the four forms, alphabetical kwargs, the citation rule with a
  deliberate non-truth example (`ANSWER: 6 (scope.py:3)`), the named turns **T12, T24, T46**, and
  “on those turns the tools are unavailable”. Leak-checked: no `64` and no `31` in `system_prompt`
  or in any `turns[].question`.
- `checkpoint_turns: [12, 24, 46]`, `answer_contract` (schema `consonance.answer-contract/1`).
- `checkpoints[].id` + `checkpoints[].answer_spec` (kind + AST `derive`), and `sources` (paths +
  sha256) so the truth can be re-derived offline by a later cell with no model.

### 2. Runner — `experiments/ptr-engine/longrun/run_longrun.py`
Additive only; every existing flag still works and `--dry-run` stays offline (48 would-send turns,
0 requests, previews under `/tmp/longrun-previews/`).
- `checkpoint_turns(fixture)` reads `checkpoint_turns`, falls back to `checkpoints[].turn` (so v2–v4
  fixtures are recognised unchanged).
- `checkpoint_prompt(fixture, t, prompt)` injects the checkpoint **question** (only when absent) plus
  `CHECKPOINT_CONTRACT_LINE` (tools-disabled banner + the four forms). Question only — never a value.
- On a checkpoint turn **tools are disabled**: the `fetch_rounds` block and its row keys are skipped,
  so no `<tool_call>` is executed and no follow-up request is bought.
- `checkpoint_answer_fields(resp)` parses the reply with `grade_v5.parse_answer_contract` (imported,
  not re-implemented) and `make_row` writes `answer_turn`/`answer_kind`/`answer_value`/`answer_raw`/
  `answer_parse_error` on **every** row (null/false off a checkpoint turn). Failed requests get
  `answer_turn=true, answer_parse_error="no_response"`.
- One extra stdout line per checkpoint turn: `answer_contract kind=… value=… error=…`.

### 3. Grader — `experiments/ptr-engine/longrun/grade_v5.py`
- `parse_answer_contract(text)` is the single parser (runner imports it). Accepts `NUM`, `CALL`,
  `NONE`, `TEXT`, and a **bare leading numeral** (`ANSWER: 64 (resolve.py:39)` → `64`); citations are
  dropped by importing `det_verify.asserted_number` / `citation_spans` (card: no weaker second rule).
  Prose before/after the single ANSWER line is tolerated but never read; ≥2 ANSWER lines, empty body,
  or a non-contract body → `answer_kind=null` + `answer_parse_error`.
- `derive_truth(fixture)` derives every expected value from the source tree by AST
  (`dv.constant_value`, `dv.count_classes`, `dv.call_inside_function`); the fixture's human
  `expected` strings are documentation, cross-checked — a divergence **aborts** with
  `fixture_truth_mismatch` instead of grading stale prose.
- Decisions: `NUM` integer equality; `CALL` exact callee + exact kwarg **name set** + exact value
  text; `NONE` only passes where the source has no such call; `TEXT` verdict `text`, reported
  separately, never a pass. Kwarg **order is not graded** (formatting rule) — reported as
  `kwargs_as_written`. Declared elisions (`scope=...` in cp3) accept `...`/`…` or the AST text.
- Per cell: `verdict`, `reason`, `asserted`, `expected`, `derivation` (`file:line` + AST node text),
  plus `answer_raw`, `answer_kind`, `answer_parse_error`.

### 4. Guards
- `experiments/ptr-engine/longrun/tests/test_answer_contract.py` — 26 assertions (11 accept, 13 reject, 2 citation-rule).
- `experiments/ptr-engine/longrun/tests/test_grade_v5.py` — 16 cases (truth derivation, all-pass, citation numeral, wrong numeral,
  wrong callee, extra kwarg, missing kwarg, wrong value, wrong ORDER → pass, `NONE` vs existing call,
  `NONE` vs a number, prose → `answer_not_contract`, `TEXT` never a pass, kind mismatch, runner-parsed
  fields, missing turn).
- Red→green: contract **26/26 green, exit 0** / `--red` **26/26 fail, exit 1**; grade_v5
  **16/16 green, exit 0** / `--red` (CALL/NONE stubbed to pass) **8/16 fail, exit 1**.

## Evidence (offline, zero requests)
- `python3 experiments/ptr-engine/longrun/tests/test_answer_contract.py` → rc 0, `26/26 assertions passed`; `--red` → rc 1.
- `python3 experiments/ptr-engine/longrun/tests/test_grade_v5.py` → rc 0, `16/16 guard cases passed`; `--red` → rc 1, `8/16` fail.
- Fake-model `run_cell` (in-process `send_chat` stub, 12 fixture replies, `--tools read_file`): T12
  row `answer_turn=True kind=NUM value=64 raw='ANSWER: NUM 64' err=None tool_calls=None`; a
  checkpoint reply containing a `<tool_call>` produced **0** follow-up requests (12 requests total);
  T12 prompt carries `TOOLS ARE DISABLED`.
- Dry-run: v5 → `would_send_total=48`; legacy v4 fixture → `would_send_total=48` (back-compat).
- `grade_v5.py --rows … --fixture LR-01.v5.json --out …` → cells for T12/T24 pass
  (`num_equal`), derivations `resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 64` and
  `errors.py:15-247 ast.ClassDef count(^Ptr\w*$) = 31`; CALL cell derivation
  `resolve.py:69 ast.Call inside _refuse`.
- Token cost (cl100k, offline): contract lines 6 + 6 + 20 = **32 tok** vs representative prose
  22 + 18 + 23 = **63 tok** → **Δ31 tok/checkpoint-batch (~49 %)**; the CALL line is 20 tok, the same
  as v4's documented cp3 prose string. Over the 40 checkpoint rounds the map counted: 1280 vs 2520 tok.

## Corrections to the card's premise (recorded, not silently absorbed)
- The card says `tasks-*/…/LR-01*.json` has **no** `system_prompt` key. True for the **score**
  fixture `tasks-v4/LR-01.v4.json` (`consonance.fixture/1`), **false** for the longrun fixture
  `tasks-v4/runtime-v4/LR-01.v4.json` (`consonance.longrun-fixture/1`), which already carries one —
  including an ambiguous `ANSWER: <value or NOT-AN-ANSWER>` instruction. v5 replaces that tail with
  the contract; it does not invent a first system prompt.
- The contract's citation rule lives in `experiments/ptr-engine/tools/det_verify.py` (not
  `longrun/det_verify.py`, which does not exist).

## Assumptions (automated session, no human)
1. Prose around the single ANSWER line is tolerated (recorded as unread) rather than failing: the
   measured compliance failure is a formatting problem, and the line is the only evidence read.
2. `NONE` needs a derivable absence to pass; with all three v5 checkpoints derivable, `NONE` always
   fails here (`none_but_call_exists` / `none_contradicted_by_source`).
3. Declared elision (`scope=...`) accepts `...`/`…` or the exact AST value text — recorded per cell
   as `elided_kwargs`.
4. The score-fixture counterpart (`tasks-v5/LR-01.v5.json`) was **not** written: outside this card's
   declared write paths.

## Not done / next hint
- No live arm was run (card: zero requests). A later cell runs the v5 fixture on the tools-on arm and
  grades with `grade_v5.py --rows … --fixture …/LR-01.v5.json --out …`.
- If a v5 score fixture is wanted, adapt `tasks-v5/LR-01.v5.json` from `tasks-v4/LR-01.v4.json` and
  point `sources` at the same pinned files.
