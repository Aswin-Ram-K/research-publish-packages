# ANCHOR-PREREG — rule R2, frozen before any scoring

**Status:** DESIGN-ONLY / FROZEN. Zero live requests, no re-grade of any arm, no
new accuracy number. This document is the normative text; the machine checker is
`experiments/ptr-engine/tools/anchor_prereg_check.py` (offline, stdlib only).

Frozen at **2026-10-26T13:29:21Z** (UTC). The rule below is written **before** any
arm is scored under it. Nothing in this file was fitted to an arm's output: every
class in the census is derived from the fixture's `expected` string and the engine
source file the checkpoint cites, and the wrong-answer probe in §5 proves the rule
is not a blanket pass.

## 0. Why (measured, not re-derived)

`grade_v3.py:55-63` derives the anchor list from the checkpoint's expected answer
string: it keeps every `[A-Za-z][A-Za-z0-9_]*` token, splits on `_`, drops parts
shorter than 4 characters and parts in `STOPWORDS` (`grade_v3.py:15-22`). The §4
rule then requires **every** derived anchor to appear (`grade_v3.py:178-191`), so an
English connective that survives the stopword filter becomes mandatory. `raising`
survives (7 characters, not a stopword) and it is prose, not code.

Two independent measurements of that defect:

- `measure/rows-longrun-v6-tools.grade-v3.json`, `arms.pointer-stable.checks[2]`
  (`cp.2.t46`): `pass=false`, `reason=refused_while_knowable`,
  `detail="marker dropped anchors; missing raising"`.
- `measure/rows-longrun-c-2026-10-26.jsonl` line 142 via
  `rows-longrun-c-2026-10-26.grade-v3.json`: `missing_anchor:raising`,
  `detail="missing 1/9 anchors: raising"`.

## 1. R2 — normative text (VERSIONED, FROZEN)

> **R2 (anchor rule, frozen 2026-10-26T13:29:21Z):** a checkpoint's `^ANSWER:`
> marker must contain every anchor token classified **CODE-SYMBOL** or **NUMBER**;
> tokens classified **PROSE-CONNECTOR** are informational and are **not** required.
> `required_anchors` is therefore **derived** from (a) the checkpoint's `expected`
> string, via the untouched `grade_v3.anchors()` tokenizer, and (b) the cited
> source file — never hand-written, never hand-pruned.

Normative definitions used by R2 (these are the operational meanings the checker
implements, and the only ones it implements):

- **CODE-SYMBOL** — the anchor token occurs at least once in the cited source file
  **outside** any string literal or comment (i.e. as an identifier, attribute,
  parameter name or keyword). Evidence = the first such `file:line`.
- **NUMBER** — the expected value is a numeric literal. Evidence = the `file:line`
  that establishes the value. Numbers were already graded separately by
  `number_in()` (`grade_v3.py:73-76`); R2 does not change that path.
- **PROSE-CONNECTOR** — the anchor token has **no** code occurrence in the cited
  file: either every occurrence lies inside a string literal / docstring / comment,
  or the token does not occur in that file at all. Such a token is English
  scaffolding carried by the expected string, not a symbol the answer must state.

### 1.1 Recorded amendment to this card's premise (honesty note, read this)

The card's literal definition of PROSE-CONNECTOR was "an English word that does
**not** appear in the cited source". For `raising` that premise is **false**:
`grep -Fn raising experiments/ptr-engine/ptr_engine/resolve.py` returns
`resolve.py:67` — the docstring `"""Record the refusal before re-raising. A
refusal is a measurement too."""`. The token *does* occur in the cited file, and in
the cited range (`#L66-L71`).

The classification above is therefore made on **occurrence context**, not on
absence: `raising` occurs only inside a STRING token, twice nothing else, so it is
PROSE-CONNECTOR. This is strictly narrower than "absent", so it cannot be used to
smuggle a code symbol out of the required set: a token that appears as an
identifier anywhere in the cited file is always CODE-SYMBOL under both readings.
The checker derives this automatically with `tokenize` (`prose_lines()`), so the
class is recomputable without trusting this paragraph.

### 1.2 Explicit non-goals (frozen)

R2 does **not**:

1. relax the `^ANSWER:` requirement itself — `marker_required` and
   `grade_v3.MARKER_RE = ^ANSWER:\s*\S.*$` (`grade_v3.py:26`) are untouched, and a
   missing marker still fails as `marker_missing`;
2. change any `expected` answer string, checkpoint id, turn, or source citation;
3. apply to any existing row — **no re-grade is performed by this card**, no
   accuracy percentage is published, and every historical grade file is left
   byte-identical;
4. relax the concluding-position test (`grade_v3.py:195-205`): the marker line
   must still carry at least one required anchor;
5. touch `grade_v3.py`, `grade_v2.py`, `score_longrun.py`, `analyze_longrun.py`,
   any fixture, or any row/grade file. R2 is text to be implemented by a **later**
   card, under its own pre-registration.

## 2. The v4 fixtures

`LR-01.v4.json` (sha256 `5a5f8c4b…`) and `LR-01.v4.tools2.json` (sha256
`5bf5f639…`) declare **identical** `checkpoints` arrays — same 3 checkpoints, same
`expected`, same `source`, same `turn`; `tools2` adds only a `tools_channel` key and
a different `runtime`/channel wiring. Both declare
`answer_marker = {"line_regex": "^ANSWER:[ ]*\\S.*$", "required": true}`, so
`grade_v3.py:408` sets `marker_required = True` on this fixture.

Both fixtures therefore produce **one** census; the checker asserts the two
checkpoint arrays are equal before deduplicating cells.

## 3. Task 1 — the anchor census

Derived anchors: cp.0 and cp.1 expect a numeric literal, which `anchors()` ignores
(numbers are graded by `number_in()`), so they contribute one NUMBER row each.
cp.2 contributes 9 derived anchors: `ref` is dropped for length 3 and `before` is a
STOPWORD (`grade_v3.py:15-22`), which is exactly why the recorded grader says
"missing 1/9 anchors".

<!-- census:begin -->
| checkpoint id | anchor token | class | evidence (file:line or absent) |
|---|---|---|---|
| cp.0.t12 | 64 | NUMBER | experiments/ptr-engine/ptr_engine/resolve.py:39 |
| cp.1.t24 | 31 | NUMBER | experiments/ptr-engine/ptr_engine/errors.py:15-247 (31 `^class Ptr` definitions, last at :247) |
| cp.2.t46 | ledger | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:33 |
| cp.2.t46 | record | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:69 |
| cp.2.t46 | refusal | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:69 |
| cp.2.t46 | scope | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:43 |
| cp.2.t46 | serialized | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:70 |
| cp.2.t46 | text | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:66 |
| cp.2.t46 | code | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:70 |
| cp.2.t46 | error | CODE-SYMBOL | experiments/ptr-engine/ptr_engine/resolve.py:66 |
| cp.2.t46 | raising | PROSE-CONNECTOR | experiments/ptr-engine/ptr_engine/resolve.py:67 (docstring/comment only; no code occurrence) |
<!-- census:end -->

Totals: **11 cells** — 2 NUMBER, 8 CODE-SYMBOL, 1 PROSE-CONNECTOR. The single prose
anchor is `raising`, on `cp.2.t46`.

Supporting lines (read-only inspection):

- `resolve.py:39` — `DEFAULT_MAX_REFS = 64` (establishes cp.0's 64).
- `errors.py:15` `class PtrError` … `errors.py:247` `class PtrLawObservedInvalidError`
  — 31 lines match `^class Ptr` (establishes cp.1's 31).
- `resolve.py:66-71` — the checkpoint's cited range:
  `def _refuse(ledger: Optional[Ledger], scope_name: str, text: str, error: PtrError) -> None:`
  / `"""Record the refusal before re-raising. A refusal is a measurement too."""` /
  `if ledger is not None:` / `ledger.record_refusal(` /
  `scope=scope_name, serialized_ref=text, code=error.code` / `)`.
- `resolve.py:67` is the **only** occurrence of `raising` in the file, and it is
  inside that docstring.

## 4. Derived required sets

- cp.0.t12: `required_anchors = []` (NUMBER `64`, graded by `number_in`)
- cp.1.t24: `required_anchors = []` (NUMBER `31`, graded by `number_in`)
- cp.2.t46 under **R1**: `[ledger, record, refusal, scope, serialized, text, code,
  error, raising]` (9)
- cp.2.t46 under **R2**: `[ledger, record, refusal, scope, serialized, text, code,
  error]` (8) — `raising` informational

## 5. Task 3 — the two-sided proof (recorded run)

Command: `python3 experiments/ptr-engine/tools/anchor_prereg_check.py`
Probe A input is the **real** V6 row (turn 46, `measure/rows-longrun-v6-tools.jsonl`,
content sha256 short `ecdb3fc9d9f0`), never hand-typed:

```
_refuse calls `ledger.record_refusal` (when ledger is not None), passing `scope=scope_name`,
`serialized_ref=text`, and `code=error.code`.

ANSWER: ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)
```

| probe | under R1 | under R2 |
|---|---|---|
| **A** correct paraphrase (V6 cp.2.t46, verbatim) | **REJECT** `missing_anchor:raising` | **ACCEPT** `ok` (8/8 required present) |
| **B** wrong answer: `record_refusal` → `write_audit` | REJECT `missing_anchor:record` | **REJECT** `missing_anchor:record` (missing `record`,`refusal`) |
| **C** wrong kwarg: `scope=` → `grant=` | REJECT `missing_anchor:scope` | **REJECT** `missing_anchor:scope` |

Two-sided property holds: R2 flips exactly the prose case and refuses both wrong
answers, and it refuses them for the right reason (a missing **code** anchor, not a
missing connective). Probe B/C are not hypothetical: `ledger` has no `write_audit`
method, so B is the shape a plausible-but-wrong answer takes.

**Recorded run (2026-10-26T13:29Z–13:35Z):** `RESULT: PASS`, **exit 0**; the
recomputed census matched the §3 table 11/11 cells. Checker sha256
`c3a17b6cb3ef82ec440e20a0abcd2efcbaab790e0ea9d96caae716f8d822012e`. (The checker
prints the cp.1 NUMBER evidence as "31 class-Ptr definitions, last at :247"; the
§3 cell spells the same fact out with the `^class Ptr` grep — the comparison is on
`(checkpoint, token, class)`, and every recorded row must carry evidence.)

## 6. Task 4 — what R1 would have done historically (counts only)

No re-grade. "Would flip" = the failing check's **entire** missing set consists of
PROSE-CONNECTOR anchors, so R2 could turn it into a pass; nothing is re-scored and
no accuracy number is published.

| grade file (on disk) | arm-checks | would flip ≤N |
|---|---|---|
| `measure/rows-longrun-c-2026-10-26.grade-v3.json` | 12 | **≤2** — `pointer-stable`, `transcript-grow` (both `cp.2.t46`, `missing_anchor:raising`, "missing 1/9") |
| `measure/rows-longrun-v3-2026-10-26.grade-v3.json` | 6 | ≤0 (cp.2 failures miss 6 anchors: `ledger,record,refusal,scope,serialized,text`) |
| `measure/rows-longrun-v3-2026-10-26.grade-v3-final.json` | 6 | ≤0 (same 6-anchor misses) |
| `measure/rows-longrun-v4-2026-10-26.grade-v3.json` | 6 | ≤0 (`transcript-grow` misses 9/9; `pointer-stable` is `marker_missing`) |
| `measure/rows-longrun-v4-tools-2026-10-26.grade-v3.json` | 3 | ≤0 (`marker_missing`) |
| `measure/rows-longrun-v5-tools.grade-v3.json` | 3 | ≤0 (`marker_missing`) |
| `measure/rows-longrun-v6-tools.grade-v3.json` | 3 | **≤1** — `pointer-stable` `cp.2.t46`, `refused_while_knowable`, "missing raising" |
| **total** | **39** | **≤3 of 39 checkpoint arm-checks** |

The honest statement is **"would flip ≤3 of 39 arm-checks, all on the single
checkpoint `cp.2.t46`, all on the single prose anchor `raising`"** — not a new
accuracy figure. The actual re-grade is a later card's job.

## 7. Provenance — sha256 of every inspected file

| file | sha256 |
|---|---|
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json` | `5a5f8c4be2027c53038ae31b4db60ebbae03996a5a650d8fb4fe6d872df5e235` |
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json` | `5bf5f6393946b89bce4c1e28c1d117f713eb40a191253a5549fefff36a2e6945` |
| `experiments/ptr-engine/longrun/grade_v3.py` | `7bfc11f4443ec7f3c191465715ed1a35f7464ffd8301a8b2b6320bab63411bf9` |
| `experiments/ptr-engine/ptr_engine/resolve.py` | `71a14c2c1dd1b6e97b3fdf2a666ea459d093adcd0f813676cf787271a48da563` |
| `experiments/ptr-engine/ptr_engine/errors.py` | `402dc9589d8e8fd5de82ed6c8f3364390e105bf8285eb7c326b799f8200fdba0` |
| `experiments/ptr-engine/measure/ANSWER-DEGENERACY.md` | `8b7eccf4ddf50d9ce7e9d445164fea154bf0e7d68908cc83bbdc1e3a7ad23d9f` |
| `experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl` | `1e78d75f259afbe0406643825941a65b4773b4342b847698005ad5908b3e531e` |
| `experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json` | `ace2e956280c78fb53d08fee6ae09b5435889c7b55815358edc3304ceef3dc44` |
| `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.grade-v3.json` | `a05a13bcb43464292de756a700184db8596ff3a8d02564420e7160717f5dafba` |
| `experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.grade-v3.json` | `d8a48d2aebcc64da4099171781c481d27b571a78051c712b36c3186ba9deb5f4` |
| `experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.grade-v3-final.json` | `89ebde17a098eac8c9e3431f7e969ea33af7997de6bc8c40e927b36855b45505` |
| `experiments/ptr-engine/measure/rows-longrun-v4-2026-10-26.grade-v3.json` | `0498a1a73966768d1c5adcb8a3ba0b0e888ccd3103d86a7040cff34f4a5e1543` |
| `experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.grade-v3.json` | `156639de927b868d6b5c2bf8c5dcc85fbf2e6b1d19dd66b9c8d56e5d846b5a01` |
| `experiments/ptr-engine/measure/rows-longrun-v5-tools.grade-v3.json` | `c9ff53311e68bea2d8bf94441a1dfe5271508ea211ae7f4018ad118cad7c8e0f` |

## 8. Acceptance

`python3 experiments/ptr-engine/tools/anchor_prereg_check.py` exits **0** iff all of:

1. the recomputed census (§3) equals the table recorded above, cell for cell
   (checkpoint id, token, class; every recorded row carrying evidence);
2. probe A: REJECT under R1 **and** ACCEPT under R2;
3. probe B: REJECT under R2, for a missing CODE-SYMBOL anchor.

Exit 1 names every differing cell or violated probe. The checker writes nothing.
