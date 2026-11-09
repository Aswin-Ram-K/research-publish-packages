# PROSE-VALUE-METRIC — the quality number a reader would have assumed

**Status: measured, errata UNAPPLIED.** `PARM-1` is frozen; this document drafts the errata an
operator would need to adopt a second quality column. Nothing here is applied, and no threshold
changes anywhere.

Second metric only. `checkpoint_accuracy` is **not** recomputed, not corrected and not overwritten
in any grade document: this document adds a column beside it and reports how far apart the two
readings are.

- Tool: `experiments/ptr-engine/tools/asserted_value.py` (read-only over rows and grade documents)
- Test: `experiments/ptr-engine/longrun/tests/test_asserted_value.py` — 13 tests; **red→green**: with
  `asserted_value()` neutered to `return None` the suite is `6 failed, 7 passed`; restored,
  `13 passed`.
- Measure: `experiments/ptr-engine/measure/PROSE-VALUE-METRIC.json`
- `live_requests: 0`, `network: false`, no grid re-run.

---

## 1. Why the frozen number is not what a reader assumes

`grade_v5` reads one channel: the `^ANSWER:` contract line. A turn that states the answer in prose
is filed `prose_only` → `never_answered`, and `never_answered` is scored as *no answer*. So wherever
the model wrote prose instead of the marker, `checkpoint_accuracy` is a **format-compliance**
number being read as an **answer-correctness** number.

`NEVER-ANSWERED-ROOT` sized that gap on the 63 `never_answered` cells: 5 of them state a value
(4 wrong, 1 right), and 0 of 63 ever contain the true `64`. This unit turns that finding into a
column that can be compared against the frozen verdict per cell.

## 2. The extractor — forms accepted

`asserted_value(text) -> (value, form, span) | None`. Contract line first, then prose in document
order. `span` always indexes the **original** text, so every accepted value can be quoted verbatim.

| form | reads | example |
|---|---|---|
| `answer_num` | the frozen grader's own channel | `ANSWER: NUM 64` |
| `answer_call` | the frozen grader's own channel | `ANSWER: CALL ledger.record_refusal(...)` |
| `answer_bare` | marker, no tag | `ANSWER: 64` |
| `is` | copula, emphasis-tolerant (`**1**`, `` `64` ``) | `the budget is 64` |
| `equals` | `=` / `equals` / `equal to` | `max_refs = 64` |
| `default_of` | `default of/to/is` | `the default of 64` |
| `leading_line` | first non-blank line is a bare numeral | `7\n\nEvidence: …` |
| `leading_bare` | the whole turn is a numeral | `2000` |
| `trailing_bare` | bare integer ending a sentence | `… total: 64` |
| `backtick` | integer in backticks, in an asserting sentence | `` the budget `64` `` |
| `calls` | prose names a **qualified** callee | `_refuse calls ledger.record_refusal` |
| `prose_call` | the whole turn is one call expression | `ledger.record_refusal(scope=…)` |

## 3. Rejection rules, one line each (each one is a `grade_v4` failure)

- **R1 code citation** — a numeral inside `resolve.py:39`, `#L39`, `L39`, `lines 15-142` is a
  location, never an answer (`grade_v4` read `#L39` as the answer 39).
- **R2 range endpoint** — a numeral adjacent to `-`, an en/em dash, `to`, `through` or `until` is one
  end of a span (`15–142`, `L15–L142`).
- **R3 unit suffix** — a numeral followed by `B`/`bytes`/`KiB`/`tokens`/`chars`/`ms`/`%` is a
  measurement (`1680 B`, `4096 tokens`); the numeral and its unit are masked together.
- **R4 identifier glue** — a numeral touching `[A-Za-z_.@]` belongs to a version, hash, path or
  identifier (`v5`, `p95`, `resolve.py`).
- **R5 count-of-other** — the low-precedence forms (`backtick`, `trailing_bare`) are accepted only
  when the sentence also carries a value cue (`is`/`=`/`equals`/`default`/`:`); without one,
  `passes four arguments` and `seven distinct Ptr* error classes` are counts of other things.
- **R6 non-prose zone** — anything inside `<tool_call>…</tool_call>`, a fenced code block, or a
  `@knowledge:…@N` pointer handle is markup or retrieved code, not the model's assertion
  (`grade_v4` read `64` out of a pasted `resolve()` body). Masked with spaces, offsets preserved.
- **R7 non-integer prose** — prose forms accept integers only; `0.9` PPL and `2.1` are scores.
  Contract lines are exempt because the frozen grader itself accepted them.
- **R8 unqualified call** — the `calls` form needs a qualified name (`obj.method`); a bare
  identifier is a tool or a local (`read_file`), and "I'll call read_file" is a plan, not an answer.

Two performance notes, recorded because they are properties of the corpus: the `policy ·
transcript-grow` turns are 85,100 chars of `<tool_call>open` every ~25 chars, so the tool-call mask
is a **linear scanner**, not a non-greedy DOTALL regex (that rescanned to EOF at every open, O(n²),
and did not finish in 60 s); and masking a unit suffix with a **leading** `\s*` is O(n²) on the
mostly-spaces zone those turns become — the numeral and its unit are masked in one anchored pass.

## 4. The population — both denominators, stated

Rule: the `grade_v5` documents written at/after `2026-10-26T15:56Z` over `rows-longrun-*.jsonl`
grids — the same 66-cell population `QUALITY-REASON-MIX` used.

**66 cells** from **8 documents**; **2 frozen passes**; **64 frozen non-passes**, of which **63**
are the `never_answered` set `NEVER-ANSWERED-ROOT` quotes (the 64th is the one
`answered_right_but_rejected_by_contract` cell, which asserts no value).

The card's "63 frozen non-passes" is the `never_answered` subset; the true non-pass denominator is
**64**. Every rate below carries both numbers.

| grid (`rows_file`) | cells | frozen pass | widened match | widened mismatch | no value |
|---|---|---|---|---|---|
| `rows-longrun-2026-10-26.jsonl` (base) | 12 | 0 | 0 | 1 | 11 |
| `rows-longrun-c-2026-10-26.jsonl` (c) | 12 | 0 | 2 | 3 | 7 |
| `rows-longrun-2026-10-26-fix.jsonl` (fix) | 12 | 0 | 0 | 0 | 12 |
| `rows-longrun-2026-10-26-policy.jsonl` (policy) | 12 | 0 | 0 | 0 | 12 |
| `rows-longrun-v3-2026-10-26.jsonl` (v3) | 6 | 0 | 0 | 0 | 6 |
| `rows-longrun-v4-2026-10-26.jsonl` (v4) | 6 | 1 | 1 | 0 | 5 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 3 | 1 | 0 | 0 | 3 |
| `rows-longrun-v5-tools.jsonl` | 3 | 0 | 0 | 0 | 3 |
| **overall** | **66** | **2** | **3** | **4** | **59** |

## 5. Delta table — per arm, and overall (both denominators)

`frozen pass / widened match / widened mismatch`, over the arm's cells. `match` counts non-pass
cells that assert the right value **plus** frozen-pass cells the widened reading confirms; the
non-pass split is the `6 asserting` column.

| arm | cells | frozen pass | widened match | widened mismatch | non-passes | non-passes asserting | wrong | right |
|---|---|---|---|---|---|---|---|---|
| lease-reopen | 12 | 0 | 0 | 3 | 12 | 3 | 3 | 0 |
| pointer-stable | 24 | 2 | 2 | 1 | 22 | 2 | 1 | 1 |
| transcript-compact | 12 | 0 | 0 | 0 | 12 | 0 | 0 | 0 |
| transcript-grow | 18 | 0 | 1 | 0 | 18 | 1 | 0 | 1 |
| **overall** | **66** | **2** | **3** | **4** | **64** | **6** | **4** | **2** |

The sentence a reader needs:

> **Of the 64 frozen non-passes (63 of them the `never_answered` set), 6 assert a value in
> writing; 4 of those are wrong and 2 are right.** Every rate on this page is `n/64` for
> non-passes and `n/66` for cells.

That is the whole delta: **6 of 64** frozen non-passes are decided by prose, and the frozen column
scores all 6 as "never answered".

## 6. The six changed cells, quoted verbatim

`text_chars` is the exact character count of the turn text; the quote is verbatim with an ellipsis
where text is omitted. Nothing is paraphrased.

1. `base · lease-reopen · cp.0.t12` — **287 chars**, `cap_hit`, asserts `1` vs truth `64` → **wrong**
   > `…The default per-turn resolve budget is **1 ref** — this is derivable from `refs/experiments/ptr-engine/ptr_engine/resolve.py#L39`,`

2. `c · lease-reopen · cp.0.t12` — **4 chars**, `prose_asserts_value`, asserts `2000` vs `64` → **wrong**
   > `2000`

3. `c · lease-reopen · cp.2.t46` — **143 chars**, asserts callee `self._reject` vs `ledger.record_refusal` → **wrong**
   > `_refuse calls `self._reject` and passes the `reason` string. … Evidence: `resolve.py#L66-L71` shows `_refuse` containing `self._reject(reason)`.`

4. `c · pointer-stable · cp.1.t24` — **196 chars**, asserts `7` vs truth `31` → **wrong**
   > `7 … Evidence: `errors.py` defines `PtrNotAReferenceError`, `PtrUnresolvedRefError`, `PtrBodyMismatchError`, and three more classes within lines 15–142, totaling seven distinct `Ptr*` error classes.`

5. `c · pointer-stable · cp.2.t46` — **77 chars**, asserts the exact call → **right**
   > `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)`

6. `c · transcript-grow · cp.2.t46` — **422 chars**, names the right callee in prose → **right**
   > `I need to read resolve.py L66–L71 to see `_refuse`. … _refuse_ calls `ledger.record_refusal`. It passes four arguments: `scope=scope_name` (here `scope.name`), `serialized_ref=text` (here `format_ref(ref)`), and `code=error.code` (here `exc.code`).`

Cell 6 is a widening beyond `NEVER-ANSWERED-ROOT`'s count of 5 asserted values: that document filed
this turn as `prose_other` because its call detection required parentheses, while the prose names
the callee in backticks. A reader would score it — it is right — so the widened column counts it.
That is the only cell the two counts disagree on.

Two other cells are **not** counted and must not be read as counts of the change:

- `c · pointer-stable · cp.0.t12` (**650 chars**) asserts, in prose, that the budget
  `defaults to `None` (unbounded)` — a wrong *qualitative* claim with no numeral. The extractor
  returns integers and callees, so it returns `None` here; `NEVER-ANSWERED-ROOT` records it as a
  separate qualitative finding.
- `v4-tools · pointer-stable · cp.0.t12` (**440 chars**, frozen **pass**, `num_equal`) — the grade
  document's `answer_raw` is `ANSWER: 64`, but the turn's last row `content` is tool-call narration
  (`I need to find the actual file location first. …`). The widened column reads the turn text and
  therefore says `no_value`. **The columns are not nested**, and this is the one cell where the
  frozen column knows something the widened column does not — it is listed here rather than
  smoothed away.

## 7. Errata text — drafted, NOT applied

`PARM-1` is frozen. What follows is the errata an operator would sign; it is recorded here so the
decision is theirs, not a silent edit.

> **PARM-1 errata (draft, unapplied) — add `asserted_value_accuracy` beside `checkpoint_accuracy`.**
> Report, for every cell, a second correctness column computed by
> `experiments/ptr-engine/tools/asserted_value.py` over the same rows file, arm and turn, reading an
> asserted answer from the contract line **or** from prose (`is`/`=`/`equals`/`default of`, a bare
> leading or trailing integer, an integer in backticks, or a qualified callee named in prose), and
> scoring it against the frozen `truth[].expected` with `match` / `mismatch` / `no_value`.
> `checkpoint_accuracy` is retained unchanged as the *contract-compliance* number; the two are
> reported side by side and neither replaces the other. **No threshold changes**: every arm
> comparison, every gate and every published margin stays as frozen, because this corpus' margins
> are computed on `checkpoint_accuracy` and this errata adds a column, not a verdict.

The frozen sentences it would change, exactly (all six cells above, all `never_answered` →
`answered_wrong_value` or `answered_right_value` in the widened column):

1. `base · lease-reopen · cp.0.t12` — "never answered" → **answered, wrong (`1` vs `64`)**.
2. `c · lease-reopen · cp.0.t12` — "never answered" → **answered, wrong (`2000` vs `64`)**.
3. `c · lease-reopen · cp.2.t46` — "never answered" → **answered, wrong (`self._reject`)**.
4. `c · pointer-stable · cp.1.t24` — "never answered" → **answered, wrong (`7` vs `31`)**.
5. `c · pointer-stable · cp.2.t46` — "never answered" → **answered, right**.
6. `c · transcript-grow · cp.2.t46` — "never answered" → **answered, right**.

## 8. What this means for the frozen quality number

The frozen `checkpoint_accuracy` on this population measures **contract compliance** in the cells
where the model wrote prose instead of `ANSWER:` — it measures answer *production through the
required channel*, not pointer mechanics and not correctness. **6 of 64** frozen non-passes (6 of
the 63 `never_answered`) change the moment prose counts: 4 become wrong answers, 2 become right
answers. No published pass total changes — the 2 frozen passes are both confirmed — but the
"0 wrong values" reading of the corpus does not survive, and the non-pass column is
6/64 answer-*capture* failures by construction.
