# Q0-ANSWER-DEGENERACY — why the checkpoints score zero

**Unit:** `Q0-ANSWER-DEGENERACY` · **Date:** 2026-10-26 · **Live requests spent: 0** (offline only).
**Question:** from the recorded rows alone, *why* do the checkpoints score zero — and does 0/3 license
any statement about arm quality?

---

## Verdict (one paragraph)

The config-C grid's `0/3` is a **fixture/instruction artefact, not an arm effect**. Two of the three
checkpoint values were **not present anywhere in the working set the model was shown**: the v2 fixture
pins `resolve.py#L66-L110` (line 39, `DEFAULT_MAX_REFS = 64`, is outside it) and `errors.py#L114-L126`
(**3** `Ptr*` classes, against an expected answer of **31**). A model obeying its own system prompt
("never restate a fact you did not read") cannot answer cp.t12 or cp.t24 from what it was given, and
the recorded text says so in the model's own words. The `^ANSWER:` marker — the thing this card was
written to test — **never applied to the config-C grid at all**: the v2 fixture declares no
`answer_marker`, so `grade_v3.py` ran with `marker_required = False` and every one of the 192 rows
carries `marker_lines = 0`. The marker rule only came into existence in the v4 fixture, which is
simultaneously the fixture that repaired both starved pointers and added the marker to the system
prompt — which is exactly why v4 is the only grid where a checkpoint ever passed. The single cause
that, if true, makes 0/3 an artefact is **cause 1 (starved pinned working set)**; it is true, and it is
proven below by the v2→v4 item diff.

---

## 1. Per arm × per checkpoint turn: classification

Class definitions used (mechanical, and the ones `tools/answer_degeneracy_check.py` recomputes):

| class | rule |
|---|---|
| `NO_ANSWER_TEXT` | no non-empty line in `content` |
| `NO_MARKER` | non-empty answer, no line matching `^ANSWER:\s*\S.*$` anywhere |
| `MALFORMED_MARKER` | a marker-shaped line exists but is not the last non-empty line, **or** the last line's payload is `NOT-AN-ANSWER` |
| `MARKER_ACCEPTED` | last non-empty line is `^ANSWER: <payload>`, payload not a refusal |

`ANSWER: NOT-AN-ANSWER` is classed `MALFORMED_MARKER` on purpose: the line is present and
well-formed but it declines to conclude, which per `GRADER-V3.md` §5 is a *refusal*, not an answer.

### The config-C table (recomputed; `evidence.table` in the handoff)

| arm | t12 | t24 | t46 |
|---|---|---|---|
| transcript-grow | `NO_MARKER` | `NO_MARKER` | `NO_MARKER` |
| transcript-compact | `NO_MARKER` | `NO_MARKER` | `NO_MARKER` |
| pointer-stable | `NO_MARKER` | `NO_MARKER` | `NO_MARKER` |
| lease-reopen | `NO_MARKER` | `NO_MARKER` | `NO_MARKER` |

**12/12 cells are `NO_MARKER`.** Classes (iii) `MALFORMED_MARKER` and (iv) `MARKER_ACCEPTED` are
**empty in the config-C grid** — the fixture never asks for a marker and the grader never requires one,
so the grid cannot produce either class. The recorded `marker_census` for all four arms is
`{"marker_lines": 0, "turns": 48}`
(`rows-longrun-c-2026-10-26.grade-v3.json`).

### Quoted rows

**(ii) `NO_MARKER` — `rows-longrun-c-2026-10-26.jsonl:142`** (`pointer-stable`, t46, 3 words,
`prompt_tokens=2240`). First 200 chars:

> `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)`

This is the **substantively correct answer to cp.t46** — right call, right three arguments — and it was
graded `missing_anchor:raising`. The grader's expected string is

> `ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), before re-raising`

and §4 requires *every* anchor token of that string, including `raising`. The English clause that
carries no source semantics is the token that failed a correct answer. (The same `raising` word is
available to the model — `LR-01.v2.json` item `resolve.py` body contains the docstring
`"Record the refusal before re-raising."` — so this is anchor strictness, not starvation.)

**(ii) `NO_MARKER` — `rows-longrun-c-2026-10-26.jsonl:108`** (`pointer-stable`, t12, 89 words,
`prompt_tokens=2225`). First 200 chars:

> `The default per-turn resolve budget is not set by a `max_refs` default in the provided `resolve.py` excerpt; the budget parameter defaults to `None` (unbounded), and the test `test_scope_defaults_to_the_index_block_size` (pinned, name only) indicates the index block size is the default, but the excerpt ends before line 39's implementation. From the visible code, no numeric default budget appears; …`

The tail of the same row is explicit:

> `Evidence: the pinned `resolve.py` body (1680 B) ends at the `PtrUnknownIdError` …`

**The model correctly reported that the working set does not contain `resolve.py#L39`.** It is right;
see §4 cause 1. This row is not a failure of the arm — it is a correct refusal under a defective
fixture.

**(ii) `NO_MARKER` — `rows-longrun-c-2026-10-26.jsonl:156`** (`lease-reopen`, t12, 1 word,
`prompt_tokens=446`). First 200 chars:

> `2000`

A wrong value, from an arm that was given 446 prompt tokens — the smallest context in the grid. Also
`NO_MARKER`, but a different pathology from `:108` (confident wrong number vs correct refusal).

Caveat on the checker's supplementary census: it tests the *leading token* of `expected`, and cp.t46's
expected begins with the literal `ledger.record_refusal(scope=...,` — ellipsis included — so the census
reports `present=False` for `:142` even though the call and all three of its arguments are correct there.
The census is a gross presence probe, not a correctness test; per-cell verdicts come from the recorded
`.grade-v3.json`.

**(i) `NO_ANSWER_TEXT`** — **no row in the config-C grid qualifies.** All 12 checkpoint rows carry
non-empty text (`answer_source` is `content` for every row; `answer_source_none_rows=0` in the sibling
`.analysis.txt`).

**(iii) `MALFORMED_MARKER` — empty in config-C; the class exists only in the v4 grid.**
`rows-longrun-v4-2026-10-26.jsonl:12` (`transcript-grow`, t12, 11 words, `prompt_tokens=4668`):

> `I need to read the specified lines of resolve.py. ANSWER: NOT-AN-ANSWER`

Marker present, in the concluding position, payload is the refusal sentinel. This is the v4 grid's
degeneracy signature: the model learned the *shape* of the marker from the v4 system prompt but used it
to decline. All 48 transcript-grow turns in v4 carry a marker line
(`marker_census: {"marker_lines": 48}`), and cp.t24 of pointer-stable is the same shape
(`rows-longrun-v4-2026-10-26.jsonl:72`: `… ANSWER: NOT-AN-ANSWER`).

**(iv) `MARKER_ACCEPTED` — empty in config-C; exactly two rows in the whole project.**
`rows-longrun-v4-2026-10-26.jsonl:60` (`pointer-stable`, t12, 3 words, `prompt_tokens=4124`):

> `64` `ANSWER: 64`

and the tools-on equivalent `rows-longrun-v4-tools-2026-10-26.jsonl:22` (`pointer-stable`, t12,
62 words, `prompt_tokens=4229`), which spends 60 words on shell fetches
(`<tool_call>find / -name "resolve.py" …`) and then lands the value:

> `… <tool_call>pwd ANSWER: 64`

---

## 2. Does the checkpoint turn ever ask for the marker?

**In the config-C grid: no.** The fixture is `tasks-v2/runtime-v2/LR-01.v2.json`, sha256
`0a07db1b14f30034902c23fe208e5717ad64856f31fe9dcfc1ab873bc2b90848`, and it has **no `answer_marker`
key** (keys: `N, acceptance, adaptation, answer_budget, bytes_per_token, checkpoints, class,
derived_from, expected, fixture_version, items, long_run, objective, repair, schema, system_prompt,
task_id, turns, wall_tokens, window_tokens` — `answer_marker` absent; the v4 fixture has it).

### The exact instruction text for a checkpoint turn, verbatim

`LR-01.v2.json` `turns[11]`, the cp.t12 turn:

```json
{"kind": "checkpoint", "question": "Checkpoint 1/3: What is the default per-turn resolve budget in refs? (answer must be derivable from experiments/ptr-engine/ptr_engine/resolve.py#L39)", "turn": 12}
```

and `run_longrun.py:175-180` renders it to the model as exactly:

```
QUESTION (T12): Checkpoint 1/3: What is the default per-turn resolve budget in refs? (answer must be derivable from experiments/ptr-engine/ptr_engine/resolve.py#L39)
```

The cp.t24 and cp.t46 instruction texts, also verbatim:

```
QUESTION (T24): Checkpoint 2/3: How many Ptr* error classes does errors.py define? (answer must be derivable from experiments/ptr-engine/ptr_engine/errors.py#L15-L142)
QUESTION (T46): Checkpoint 3/3: What does _refuse call, and what does it pass? (answer must be derivable from experiments/ptr-engine/ptr_engine/resolve.py#L66-L71)
```

**Not one of them mentions `ANSWER:`.** Neither does the v2 system prompt, which is the only other
text the model sees (`run_longrun.py:539` sends `[{"role": "system", "content":
self.fixture["system_prompt"]}, …]`). Its whole instruction on answer shape is:

> `At a checkpoint turn the grader compares your ENTIRE answer with the value it expects, so answer with the value alone: no units, no restated question, no commentary, unless the question asks for a phrase or a list.`

The transcript framing compounds it: answers are appended to the transcript as
`ANSWER (T12): <text>` (`run_longrun.py:184`), which is **not** `^ANSWER:` and never teaches the
marker form.

### Where the grader's `^ANSWER:` requirement is satisfied from

Nothing in the config-C path satisfies it, **because nothing in that path requires it**.
`grade_v3.py:404-406`:

```python
marker = fx.get("answer_marker") or {}
marker_required = bool(marker.get("required"))
```

With `answer_marker` absent, `marker_required = False`, and `judge()` never enters its
`if marker_required and mline is None: → marker_missing` branch. So the marker rule is **inert** for
config-C — it is not the cause of 0/3, and the config-C failing reasons confirm it: they are
`number_wrong:…`, `preamble_only`, `missing_anchor:…`, never `marker_missing`.

The requirement becomes real only in `LR-01.v4.json`, where it is satisfied from **two** places at
once: the fixture key `"answer_marker": {"line_regex": "^ANSWER:[ ]*\\S.*$", "required": true}`
(which arms the grader) **and** the last sentence appended to the v4 system prompt (which tells the
model):

> `End every answer with a final line: ANSWER: <the value, or NOT-AN-ANSWER>. The value must appear in that line, never only inside a pasted code block.`

**So the card's hypothetical — "the requirement exists in the grader but never in the prompt the model
sees" — is false for each grid considered separately, and the true defect is worse and simpler: the
requirement was added to both the grader and the prompt in the same fixture revision that also fixed
the working set.** That co-variation is what makes the v4 grid useless as a control for the marker:
v4 changed (a) the pinned items, (b) the cp.t24 source pointer, and (c) the marker rule, all at once.

---

## 3. The control diff: the one passing CP1 row vs a failing CP3 row of the same arm

**Arm:** `pointer-stable` — the only arm that ever passed a checkpoint.

| | passing | failing |
|---|---|---|
| row | `rows-longrun-v4-2026-10-26.jsonl:60` | `rows-longrun-v4-2026-10-26.jsonl:94` |
| turn | t12 (`checkpoint 1/3`) | t46 (`checkpoint 3/3`) |
| fixture | v4 `5a5f8c4b…` | v4 `5a5f8c4b…` (identical) |
| `prompt_tokens` | 4124 | 4151 (**+27**, both ≪ `window_tokens` 65536) |
| words | 3 | 25 |
| last non-empty line | `ANSWER: 64` | `<tool_call>{"path": "experiments/ptr-engine/ptr_engine/resolve.py", "start_line": 66, "end_line": 71}<tool_call>` |
| marker | present & concluding | **absent** |
| grader reason | `ok` → **pass** | `marker_missing` |
| text | `64` + `ANSWER: 64` | `I need to read lines 66-71 of resolve.py to answer what \`_refuse\` calls and what it passes.` + two `<tool_call>` blocks |

Mechanically, four things differ:

1. **The value was inside the pinned item.** In v4 the pinned `resolve.py` item is
   `pointer #L36-L110`, **2785 bytes**, and contains `DEFAULT_MAX_REFS = 64`. Verbatim derivable. The
   CP3 value (`ledger.record_refusal(scope=…, serialized_ref=text, code=error.code), before
   re-raising`) is also inside that same item — so derivability does **not** separate these two rows.
2. **The marker line was emitted and it was last.** The passing row is literally the value plus the
   marker; the failing row ends in `<tool_call>` pseudo-syntax.
3. **Turn position / drift.** At t46 the model emitted a *plan* ("I need to read lines 66-71") plus
   tool calls, on a **tools-off** run where nothing would ever serve the call — so the turn never
   concluded. This is the `RUN-V4-GRID` checkpoint-3 signature already named in
   `run_longrun.py:191-194` ("the pointer arms emit `<tool_call>…read_file…` and nothing ever served
   it"). It is a harness/instruction defect at late turns, not a quality difference between arms.
4. **Answer length.** 3 words vs 25 — but both are far inside the 400-word checkpoint budget, and v4
   `over_budget` is not implicated at this turn.

**What the one marker success had that the others lacked, in one line:** a value that was a single
numeric token genuinely present in the pinned item, and a model that chose to *conclude* in the last
line instead of deferring to a tool — not a better arm, and not merely the marker.

**And the same arm, same turn, on the config-C fixture** (`rows-longrun-c-2026-10-26.jsonl:142`)
concluded the right expression with no marker and failed on `missing_anchor:raising` instead. So across
the two grids cp.t46 of pointer-stable failed for **two different reasons**, neither of which is arm
quality — which is the cleanest demonstration that the checkpoint score is measuring the instrument.

---

## 4. Ranked causes, each with a price

| # | cause | cheapest falsifier | offline? | live requests |
|---|---|---|---|---|
| **1** | **Starved pinned working set (v2).** `resolve.py` pinned `#L66-L110` excludes line 39 (`DEFAULT_MAX_REFS`); `errors.py` pinned `#L114-L126` holds 3 classes. cp.t12 (64) and cp.t24 (31) are **not derivable from what the model saw**. | `grep DEFAULT_MAX_REFS` inside `items[resolve.py].body`; count `^class Ptr` in `items[errors.py].body` — **both false/3** | **yes** | **0** |
| **2** | **cp.t24's own source pointer contradicts its expected value.** Instruction says `errors.py#L15-L142`; that range contains **20** class definitions; expected is **31**, which is the **whole file** (`errors.py`, 250 lines, 31 `Ptr*` classes). Obeying the instruction cannot yield 31. | count `^class ` lines in `experiments/ptr-engine/ptr_engine/errors.py` between L15 and L142 (20) vs L15 and L250 (31) | **yes** | **0** |
| **3** | **Prose-anchor hybrid on cp.t46.** Expected = code expression + English `, before re-raising`; §4 demands every anchor, incl. `raising`. A correct answer (`:142`) failed on the prose half. | the recorded reason `missing_anchor:raising` plus the fact the same word sits in the pinned docstring | **yes** | **0** |
| **4** | **`knowable()` scans the wrong context.** `value_in_prior_context` looks only at *prior answer rows*, never at the pinned items / system prompt, so `ANSWER: NOT-AN-ANSWER` is graded `marker_without_value` instead of the documented `refused_while_knowable` — misdiagnosing honest refusals as empty markers (v4 `transcript-grow` cp.t12/24). | read `grade_v3.py:value_in_prior_context`; v4 grade shows `marker_without_value` while the value *was* in the pinned item | **yes** | **0** |
| **5** | **Late-turn tool-deferral.** At cp turns the model answers with `<tool_call>` blocks and no marker (v4-v2 `:94`; v4-tools `:36`, `:66`; v5 `:36/:48/:70`).  Pattern appears in config-C once (`lease-reopen` t24, `…jsonl:168`). | count checkpoint rows containing `<tool_call>` in each grid | **yes** (detect) | **0** to detect; **192** to test a fix |
| **6** | **Real arm effect** (pointer arms genuinely answer checkpoints worse) | none offline — needs a re-run on a fixture whose items contain the values | **no** | **192** |
| — | *marker requirement never in the prompt* | **not a cause of config-C 0/3** — `marker_required` is `False` for a fixture with no `answer_marker`; `marker_lines=0` everywhere | yes | 0 |

**Which single cause makes 0/3 a fixture/instruction artefact: cause 1.** It is established, not
hypothesised, by the v2→v4 item diff — same source files (`sha256:71a14c2c…` resolve.py,
`sha256:402dc958…` errors.py), different pointers and different bodies:

| item | v2 pointer | v2 bytes | v4 pointer | v4 bytes | consequence |
|---|---|---|---|---|---|
| `resolve.py` | `#L66-L110` | 1680 | `#L36-L110` | 2785 | v4 includes L39 `DEFAULT_MAX_REFS = 64`; **v2 does not** |
| `errors.py` | `#L114-L126` | 331 (3 classes) | `#L15-L250` | 6353 (**31** classes) | v4 makes 31 countable; **v2 shows 3** |
| `test_scope.py` | `#L16-L80` | 2598 | identical | 2598 | unchanged |
| `test_negative_controls.py` | `#L80-L117` | 1412 | identical | 1412 | unchanged |

Cause 2 is independent and reinforces it: the v4 fixture also changed cp.t24's source pointer from
`errors.py#L15-L142` to `errors.py#L15-L250`. **The fixture authors fixed exactly the two pointers that
starved cp.t12 and cp.t24, after the config-C grid was recorded.** Cause 1 and cause 2 together mean
that at most **one** of three checkpoints (cp.t46) was ever legitimately answerable in config-C — and
on that one, cause 3 sank a correct answer.

---

## 5. What `0/3` licenses

`orchestration/handoffs/RUN-C-V2.json` records `frozen_rule_outcome.verdict = "undecidable"`, with
clause (i) holding (p95 356.12 / 838.85 ms, ratio 0.4245 ≤ 0.5), clause (ii) `null` (no verified
success on either side), and clause (iii) `"holds": true` with its own reason field already saying
**"tie at zero — true, but satisfied vacuously because no arm solved any checkpoint."** This unit does
not contradict that outcome; it supplies the mechanism behind the vacuity. Clause (iii) is vacuous for
a stronger reason than "nobody solved one": the config-C checkpoints cp.t12 and cp.t24 had **no
derivable answer in the pinned working set**, so their 0/3 is the floor of a broken instrument, not a
measured floor of capability. **Permitted sentences** from this grid: the four arms were run to N=48
under one fixture and one grader; **no arm scored a correct cp.t12, cp.t24 or cp.t46** under that
fixture; the latency separation of clause (i) stands as measured; the checkpoint instrument produced
no discriminating signal. **Forbidden sentences:** "pointer-stable's quality is no worse than
transcript-grow's" or "the arms tie on quality" (a tie at the instrument floor is not a quality
comparison); "the arms cannot answer checkpoint questions" or any claim that a checkpoint is
unanswerable in principle (v4 tools-off scored 1/3 on a repaired fixture); "`tokens_to_verified_success`
is equal/immeasurable in a way that reflects arm design" (it is `null` because nothing verified);
"compact answers more cheaply at equal quality"; and any attribution of the zero to the `ANSWER:`
marker, which was inert in this grid (`marker_lines = 0`, `marker_required = False`). A paper may
state the zero **only** with the fixture defect attached — the zero is evidence about
`LR-01.v2.json`, not about the four arms.

---

## 6. Reproduce (offline, 0 requests)

```bash
python3 experiments/ptr-engine/tools/answer_degeneracy_check.py
# prints the 12-cell table + value census; exit 0 iff it equals orchestration/handoffs/Q0-ANSWER-DEGENERACY.json evidence.table
python3 experiments/ptr-engine/tools/answer_degeneracy_check.py --table-json
```

Working-set census used in §4 (read-only):

```bash
python3 -c "import json;d=json.load(open('experiments/ptr-engine/longrun/tasks-v2/runtime-v2/LR-01.v2.json'));
[print(i['id'],i['source']['pointer'],i['body_bytes'],'DEFAULT_MAX_REFS' in i['body'],i['body'].count('\nclass ')) for i in d['items']]"
```

## 7. What a later session must not redo

- Do not re-derive that the marker was inert in config-C: `answer_marker` is absent from
  `LR-01.v2.json`, `grade_v3.py:404-406` keys `marker_required` off it, and all 192 rows carry
  `marker_lines = 0`.
- Do not attribute config-C's zero to arm quality, and do not run another grid on `LR-01.v2.json` — it
  cannot grade cp.t12 or cp.t24 by construction.
- Do not "fix" the graders or the fixtures under this unit (forbidden by the card). Repointing
  `items[].source.pointer`, changing the cp.t46 expected string, or extending `knowable()` to read the
  pinned items are **separate cards**; this document is their specification.
- Do not re-score the recorded grid as new evidence; cite `.grade-v3.json` / `.score.json`.
