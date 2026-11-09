# V-FIXTURE-V8 — audit of the fixture RUN-A* actually grades on

**Subject:** `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` — 57,242 B,
sha256 `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`
**Against:** `LR-01.v7.json` — sha256
`42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392` (passed `V-FIXTURE-V7` 12/12)
**Verdict:** **PASS** — 12 agree / 0 disagree / 0 ambiguous

Source pin (unchanged since v7, and equal to v8 `sources[]`):

| file | sha256 |
|---|---|
| `ptr_engine/resolve.py` | `71a14c2c1dd1b6e97b3fdf2a666ea459d093adcd0f813676cf787271a48da563` |
| `ptr_engine/errors.py` | `402dc9589d8e8fd5de82ed6c8f3364390e105bf8285eb7c326b799f8200fdba0` |
| `ptr_engine/ledger.py` | `4c40f11b29cbda9dfdc752f7d47549cf083349cfa8a583c96437a8133e00967e` |

The derivation was computed from source **before** the v8 `checkpoints[]` array was opened, then each
checkpoint's own `answer_spec.derive` rule was re-executed against source and compared to `expected[]`.

## 1. Truth independence — 12/12 agree

| id | kind | turn | ours (from source) | fixture | verdict |
|---|---|---|---|---|---|
| `cp.0.t06` | CALL | 6 | `ledger.record_resolution(scope=scope.name,serialized_ref=presented,bytes_appended=len(presented.encode("utf-8")),block_size=scope.block(),entry_text=entry.text,)` | same, 2 values elided | agree |
| `cp.1.t08` | CALL | 8 | `scope.block()` | `scope.block()` | agree |
| `cp.2.t12` | NUM | 12 | `64` | `64` | agree |
| `cp.3.t14` | NONE | 14 | `NONE` | `NONE` | agree |
| `cp.4.t18` | NUM | 18 | `6` | `6` | agree |
| `cp.5.t20` | NONE | 20 | `NONE` | `NONE` | agree |
| `cp.6.t24` | NUM | 24 | `31` | `31` | agree |
| `cp.7.t26` | NUM | 26 | `5` | `5` | agree |
| `cp.8.t32` | NUM | 32 | `2` | `2` | agree |
| `cp.9.t36` | CALL | 36 | `ledger.resolved_count()` | `ledger.resolved_count()` | agree |
| `cp.10.t42` | NONE | 42 | `NONE` | `NONE` | agree |
| `cp.11.t46` | CALL | 46 | `ledger.record_refusal(scope=scope_name,serialized_ref=text,code=error.code)` | same, `scope` elided, `, before re-raising` | agree |

Source lines quoted:

- `resolve.py:39` — `DEFAULT_MAX_REFS = 64`
- `resolve.py:69` — `ledger.record_refusal(scope=scope_name,serialized_ref=text,code=error.code)` (inside `_refuse`)
- `resolve.py:141` — `ledger.resolved_count()` (first of three sites, all 0-arg)
- `resolve.py:159` — `ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=len(...), block_size=scope.block(), entry_text=entry.text)`
- `resolve.py:163` — `scope.block()`
- `errors.py` top-level `ClassDef` census — 31 total; `^PtrLedger\w*$` = 6; `^PtrLaw\w*$` = 5; `^PtrUnknown\w*$` = 2

Kinds NUM 5 · CALL 4 · NONE 3 confirm the card's stated shape.

## 2. The v7 → v8 delta is only the treatment layer

`checkpoints[]` is **byte-identical** to v7's (canonical-JSON equal), and per-checkpoint field diffs are
**none** — same ids, same `expected`, same `turn`, same `answer_spec`, same `source`, same `legacy_id`.
`N`, `turns`, `items`, `checkpoint_turns`, `system_prompt`, `answer_contract`, `answer_budget`, `sources`
and `acceptance` are all unchanged.

32 changed document paths, every one under the treatment layer:

- `wall_tokens` `65536 → 3838`
- `wall_tokens_by_arm` (added): all four arms `= 10616`
- `wall_tokens_basis.*` (added): arithmetic, per-arm rule, why-not-65536, the v5-era note, and six
  measured `tok/turn` slopes
- `lease_reopen_turns` (added): `[23, 40]`
- `treatments.*` (added): schema `consonance.longrun-treatments/1`, `horizon_turns 48`,
  `answer_padding_tokens_max 540`, four predicates, `verbosity_caveat`
- `expected_digests`: the integer literal `2` replaced by a derived-rule string

**Critical paths changed: NONE.** The only diffs outside the allow-list are `fixture_version`
(`v7-answer-forms → v8-treatments-reachable`) and the added `supersedes.*` self-description — version
metadata, not a graded surface, and `supersedes.sha256` correctly names v7's `42b4df00…`.

So the grid grades the **same ruler** `ATTACK-GRADE-V5-2` and `V-FIXTURE-V7` passed; only the treatment
knobs RUN-A* varies moved.

## 3. The 3 NONE ids stay unanswerable by construction

Each NONE question names a **caller** and a callee that caller's body provably never invokes:

- `cp.3.t14` "Does `resolve()` itself call `ledger.record_refusal()`?" — `resolve()`'s body calls
  `{block, encode, enumerated, get, record_resolution, resolved_count}`. No `record_refusal`.
- `cp.5.t20` "Does `_refuse()` call `ledger.resolved_count()`?" — `_refuse()`'s body calls
  `{record_refusal}` only.
- `cp.10.t42` "Does `_refuse()` call `scope.block()`?" — same body, no `block`.

The plausible wrong answer is one frame down: `resolve()` reaches `record_refusal` indirectly via
`_refuse` at `resolve.py:155`. That is why these are discrimination tests, not freebies — though as
`PARM-1-ERRATA E1` records, 3 of 12 (25%) of the H3 denominator is still collectible by any constant-NONE arm.

`ANSWER: NONE` appears in the answer contract of **both** v7 and v8, and the same three ids carry it.

## 4. Loadability

All 12 ids load through the same `checkpoints[]` path the grader walks: 12 loaded, 12 unique, none absent,
every id carrying `id`, `question`, `expected`, `answer_form`, `answer_spec`, `source`. Turns are
`6, 8, 12, 14, 18, 20, 24, 26, 32, 36, 42, 46`.

CALL argument sets are **exact, not subsets**, against the source call sites:

| id | callee | source | fixture | names |
|---|---|---|---|---|
| `cp.0.t06` | `ledger.record_resolution` | 5 | 5 | scope, serialized_ref, bytes_appended, block_size, entry_text |
| `cp.1.t08` | `scope.block` | 0 | 0 | — |
| `cp.9.t36` | `ledger.resolved_count` | 0 | 0 | — |
| `cp.11.t46` | `ledger.record_refusal` | 3 | 3 | scope, serialized_ref, code |

No literal `\u003d` escape exists in the raw file, and `"\u003d"` decodes to `=`, so decoding cannot alter
a kwarg comparison.

## 5. The mutant goes red

| case | mutation | result |
|---|---|---|
| A | `/tmp/LR-01.v8.mut64.json`: `cp.2.t12` expected `64 → 65` | `{"agree": 11, "disagree": 1, "ambiguous": 0}`, EXIT=1 — `[disagree] cp.2.t12 [ours='64' fixture=65]` |
| B | `/tmp/LR-01.v8.mutkw.json`: drop `code=error.code` from `cp.11.t46` | EXIT=1 — `[disagree] cp.11.t46 [ours='ledger.record_refusal(scope=scope_name,serialized_ref=text,code=error.code)' fixture='ledger.record_refusal(scope=..., serialized_ref=text), before re-raising']` |
| green | untouched v8 | `{"agree": 12, "disagree": 0, "ambiguous": 0}`, EXIT=0 |

The audit bites, and it names the id.

## Findings

- **F1 (carried from v7, still true):** the false-pass surface is *value elision*, not name subsetting.
  `cp.0.t06` elides 2/5 values, `cp.11.t46` elides 1/3 — and the elided `scope` is exactly the value that
  would distinguish `scope=scope_name` from `scope=scope.name`. An arm naming callee + kwarg names and
  writing `...` for values passes those ids.
- **F2 (carried):** both CALL `expected` strings are in source order, not the contract's alphabetical
  order, and `cp.11.t46` appends `, before re-raising`; order and suffix are ungraded, so documentation drift.
- **F3 (new, v8-specific):** `wall_tokens = 3838` is admitted in `wall_tokens_basis.transcript-compact_v5_era`
  to sit 10 tokens **below** v8's own first prompt (3848), so on v8 it fires at T2 and compacts a transcript
  that never fit. The live grading wall is `wall_tokens_by_arm = 10616` for all four arms; F3 only bites a
  runner that reads the top-level field instead of the per-arm map.

## Can 800 requests be graded against v8's twelve truths?

**Yes.** All 12 truths reproduce from unchanged source, the checkpoint layer is byte-identical to the v7
layer that already passed independent audit, and the only delta is the treatment layer RUN-A* varies by
design.

*Offline audit: 0 network requests. v7 and v8 were never modified; mutants lived in `/tmp` copies only.*
