# GRADER-V3 — the registered rule (written BEFORE any control was run)

Status: **rule of record** for `longrun/grade_v3.py`.
Ordering is deliberate and provable: this file is written and closed before `grade_v3.py`
exists and before any control log is built. `evidence.rule_mtime` MUST be earlier than
`evidence.first_control_result_mtime` in `orchestration/handoffs/GRADER-V3.json`.
Verify with:

    stat -c '%y  %n' experiments/ptr-engine/longrun/GRADER-V3.md \
                      experiments/ptr-engine/longrun/controls/*.grade-v3.json

## 0. Why v3 exists

Two existing instruments are broken in opposite directions and both stay on disk, untouched,
so all three remain reproducible side by side:

| grader | defect (measured) |
|---|---|
| `score_longrun.py` | `:814` `mode = str(item.get("match", "exact"))` — `checkpoints[]` carry no `match` key, so every checkpoint is graded `exact`; `:174-176` then compares the **entire turn content** to `"64"`. Cannot say yes. Reports `verified_success: false, 0/3` on a log where every answer is right. |
| `grade_v2.py` | Too lenient — `neg-one` 7/10, `neg-marker` 10/10, `neg-truncated` 10/10. No concluding position, no marker, no truncation rule. |
| both | **Neither reads the fixture's `answer_marker`** (0 grep hits). |

v3 is the instrument that must pass a correct log and fail four different wrong logs for
four different reasons.

## 1. Inputs

- `--rows` : a `.jsonl` row file; one JSON object per turn (the schema written by
  `run_longrun.py`: `arm, task_id, turn, content, finish_reason, truncated, uncached_tokens, …`).
- `--fixture` : one fixture JSON, or `--fixtures DIR`. A fixture supplies
  `checkpoints[]`, `acceptance.checks[]`, `repair{}`, optional `answer_marker{}`,
  optional `answer_budget{}`.
- Rows are grouped by `arm`; every arm is graded against the fixture named by its `task_id`.

Rows are **read-only input**. The grader writes one JSON file and nothing else.

## 2. What a check is

`checkpoints[]` entries carry **no `kind` and no `match`** this is the defect v3 fixes.
v3 derives the kind deterministically, and if a fixture ever does carry `kind`, the
fixture's value wins.

Classification of a checkpoint `expected` (first rule that matches):

1. `re.fullmatch(r"-?\d+(?:\.\d+)?", expected.strip())` → **`fact` / numeric**, value = that number.
2. `expected` matches `^[A-Za-z_][A-Za-z0-9_.]*(::[A-Za-z0-9_.]+)?$` **and** (is a single
   identifier-shaped token **or** carries `::` / a file suffix `.py|.json|.md|.yaml`) → **`artifact`**.
3. otherwise → **`fact` / prose**.

Additional required checks, taken from `acceptance.checks[]`:

- `kind: artifact` → required; pass iff every named path/symbol in `expected` (or in
  `pattern`) appears in the arm's answers. **A path inside a fence counts** — an artifact
  reference is legitimately code-shaped, so fences are *not* stripped for this kind.
- `kind: constraint` **with** a `pattern` → required, negative: pass iff the pattern matches
  **nowhere** in any answer of that arm.
- `kind: constraint` with only `no_write` → **`unverifiable`, not gating**: rows carry answer
  text, not filesystem-write evidence, so a claim that a file was not edited cannot be read
  off the log. It is reported, never silently passed.
- `kind: fact` with `match: regex` (the `covers_prose` log-restatement checks) →
  **supplementary, not gating**: the spec fixes no concluding-position semantics for a
  multi-clause lookahead regex, so admitting it to `verified_success` would be inventing one.
  Reported for comparison only. **Consequence, stated plainly: v3's `verified_success` is a
  verdict over checkpoints + repair + artifact/symbol + patterned-constraint checks, and is
  not the same 12-check denominator as `grade_v2.py`'s 10-point score.**

`repair{}` is required when the fixture carries one:

- acknowledgement = every anchor phrase of `repair.accept_literal` (see §3) appears in the
  designated `repair.at_turn` row's content, **or** the literal appears verbatim;
- re-assertion = the superseded marker (the hyphenated/backticked distinctive token of
  `repair.wrong_assumption`, e.g. `ledger-only`) appears in any row with
  `turn > repair.at_turn`;
- pass iff acknowledged **and** not re-asserted.

## 3. Anchor phrases and tokenisation (prose, repair, artifact symbols)

    tokens(s) = every [A-Za-z][A-Za-z0-9_]* run in s, each further split on "_"

    anchors(s) = deduplicated tokens of length >= 4, lowercased, minus STOPWORDS,
                 preserving first-appearance order

STOPWORDS (fixed, complete; this list is the rule):

    that this than then them they their there these those with from into over
    also both each only when where which while would should could must have
    has had been being will shall about above across after before below between
    more most some such same just like make makes made used using does doing
    then once only also very much many what whom whose here were was are and
    for the but not you your our its his her all any can may

Matching is case-insensitive on word boundaries, computed on the answer text with fences
**removed** (a value quoted inside a pasted log is not an answer).

## 4. The concluding position — the core of the rule

Fence stripping: a line is *fenced* if it is a fence delimiter (` ``` ` or `~~~`) or lies
between two delimiters. Fenced lines are removed before any prose/numeric judgement, except
for §2's `artifact` kind where fences are kept.

Let `tail` = the **last three non-empty, non-fenced lines** of the turn.

- **`fact` / numeric** — pass iff the number appears as a **standalone token**
  `(?<![\d.])64(?![\d.])` **and** it occurs in a concluding position:
  - if the fixture requires an `answer_marker` (§5), the **marker line**;
  - else if the answer's last non-empty line is itself marker-shaped `^ANSWER:\s*\S`, treat
    that line as a declared conclusion and require the number **in it** (a model that emits
    a marker has made a conclusion claim; the claim is what is graded);
  - else the number must occur within `tail`.
  A number that occurs **only inside a fenced block**, or **only in a reading preamble**
  (i.e. above the tail), **fails**. This is the check that makes `pos-exact-only` fail.
- **`fact` / prose** — pass iff **all** anchor phrases of `expected` appear in the answer,
  **and** at least one of the `tail` lines is a sentence that is (a) not fenced, (b) not
  marker-only, and (c) not a preamble, where a preamble is a line whose first words match
  `^(let me|let's|i will|i'll|i am going to|i'm going to|i need to|i should|first,? i|
   reading|inspecting|i am reading|i'm reading)\b` (case-insensitive).
- **`artifact`** — pass iff every named path/symbol appears anywhere in the answer, fences
  included.
- **`constraint` (negative)** — pass iff the forbidden pattern appears in **no** answer of
  that arm.
- **`repair`** — as §2.

## 5. `answer_marker` (fixture-level) and `refused_while_knowable`

The fixture may declare:

    "answer_marker": {"required": true, "line_regex": "^ANSWER:[ ]*\\S.*$"}

When `required: true`, a turn passes only if its **last non-empty line** matches
`line_regex` (default `^ANSWER:\s*\S.*$`). After the marker, the value is still judged by §4.

A marker line whose payload is **not** the expected value — `ANSWER: NOT-AN-ANSWER` being the
canonical case — is a **refusal to conclude**, and it fails with reason
**`refused_while_knowable`** when **the expected value was present in that arm's context**,
i.e. when the value's token (numeric: the standalone number; prose/artifact: at least one
anchor) appears in some row of the same arm with a smaller `turn` — which is exactly what the
fixture's `long_run.planted_at_turn` guarantees for a planted fact. When the value was never
in context, the same shape fails with reason `marker_without_value` (the model could not have
known; the two cases are not the same failure and are not reported as one).

## 6. Truncation

If `finish_reason == "length"` **or** `truncated is true`:

- if the required value is present **before the cut** (i.e. in the recorded content) it is
  judged normally by §4;
- otherwise the turn **fails** with reason **`truncated_without_value`**. A value is **never
  inferred from partial text** — no completion from the fixture, no "probably 64".

## 7. `verified_success` and the reported fields

- `verified_success` = **all required checks pass** (§2). Nothing else gates.
- `checkpoint_accuracy` = passed checkpoints / total checkpoints for that arm.
- `tokens_to_verified_success` = sum of `uncached_tokens` from `turn 1` through the turn at
  which the **last** required check first passes; `null` if any required check never passes.
  "First passes" is evaluated per check at its own checkpoint turn, not at the arm's end.
- `over_budget_pct` = percent of checkpoint turns whose answer exceeds the turn's word budget.
  Budget source: the fixture's `answer_budget` when present, else the registered table of
  `TASKS-V2-PREREG.md` §2 — **400 words** on a checkpoint/verify turn, **150** on a
  work/plant/repair turn. Word = whitespace token of `content.strip()`.
- Per check: `{id, kind, pass, reason, found_excerpt}` with `found_excerpt` truncated to
  **200 characters**. `reason` is a short machine-readable slug (`ok`,
  `value_not_in_concluding_position`, `number_wrong` with the wrong number named,
  `refused_while_knowable`, `truncated_without_value`, `missing_anchor:<anchor>`,
  `fenced_only`, `preamble_only`, `unverifiable`).

## 8. Determinism

No network, no model, no LLM judge, no wall-clock in the verdict. Same rows + same fixture
⇒ byte-identical JSON apart from the `generated_at` stamp. The grader imports only the
standard library.

## 9. Controls this rule must satisfy (six, registered before implementation)

| log | construction (copy-only from `rows-longrun-c-2026-10-26.jsonl`, arm `pointer-stable`) | required verdict |
|---|---|---|
| `controls/pos-full.jsonl` | every required check genuinely satisfied, numbers stated in the marker line | `true` |
| `controls/neg-one.jsonl` | one checkpoint states `65` | `false`, reason names the wrong number |
| `controls/neg-marker.jsonl` | correct prose, marker line `ANSWER: NOT-AN-ANSWER` | `false`, `refused_while_knowable` |
| `controls/neg-truncated.jsonl` | checkpoint `finish_reason: "length"`, value absent | `false`, `truncated_without_value` |
| `controls/neg-codeonly.jsonl` | correct number only inside a fenced block, marker `NOT-AN-ANSWER` | `false` |
| `controls/pos-exact-only.jsonl` | the bare `64` shape the old grader required | `false` (no marker, no conclusion) |

If `pos-full` cannot pass without weakening §4, this rule is **`RULE-UNSOUND`** and that
check is named — a rule bent to fit its own positive control measures nothing.

## 10. What v3 does not claim

- It does not re-open the 192-row grid's *latency/token* findings; only the **quality**
  verdict is superseded, and only for the numeric/prose checks.
- It does not edit `score_longrun.py`, `grade_v2.py`, `run_longrun.py`, any fixture, any plan,
  or any existing row file. Earlier `0/3` figures stay in the files that produced them.
- It sends no request of any kind.
