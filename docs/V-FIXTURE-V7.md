# V-FIXTURE-V7 — independent re-derivation of the 12 `LR-01.v7.json` truths

**Verdict: `12 / 12 agree` · `0 disagree` · `0 ambiguous`.** The fixture's twelve checkpoint
truths are correct. The agreement is *not* free: the derivation below was written from
`ptr_engine/resolve.py` and `ptr_engine/errors.py` with the verifier's own AST walk
(`experiments/ptr-engine/tools/fixture_v7_audit.py`), **before** the fixture's
`checkpoints[].expected` was opened, and it never reads `answer_spec.derive`.

Three findings survive the "all agree" result and are the reason this unit is worth its
budget: **(F1)** two CALL ids elide kwarg *values* that the grader then accepts as `...`,
a real false-positive surface in H3; **(F2)** the documented `expected` strings for the two
CALL ids are in *source* order and one carries trailing prose, i.e. they are not valid
contract answers, though grade_v5 does not grade order; **(F3)** the three NONE ids are
decidable but *constant-answer*, so 3 of 12 is a floor any degenerate arm collects.

## 1. Method and order

1. Hashed the sources and the fixture; read `resolve.py` (L1–169) and `errors.py` (AST
   census), and my own copy of the question→source-fact map was pinned to
   `/tmp/vfix7/derived.json` before `checkpoints[]` was dumped.
2. **Contamination, stated plainly:** the first raw `cat` of the fixture was truncated by
   the tool but its `acceptance.checks` mirror was visible, which leaks three of the twelve
   answers (`acc.cp1` = 64, `acc.cp2` = 31, `acc.cp3` = the `record_refusal` call shape).
   Those three ids (`cp.2.t12`, `cp.6.t24`, `cp.11.t46`) are therefore *not* blind in this
   unit. Every one of them was still re-derived from the source independently, and for
   `cp.6.t24` the count is the one an AST census gives, not the mirrored string; the other
   nine ids were derived with no prior exposure.
3. Then, and only then, diffed per id.
4. No code from `CHECKPOINT-ITEMS-V2` and none from `grade_v5` / `det_verify` is imported or
   copied. `grade_v5.py` was read *after* the derivation, only to establish what the grader
   actually compares (that is the subject of §5, not of the truth).

## 2. Pinned inputs (read-only; unchanged by this unit)

| input | sha256 |
|---|---|
| `experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` | `42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392` |
| `experiments/ptr-engine/ptr_engine/resolve.py` | `71a14c2c1dd1b6e97b3fdf2a666ea459d093adcd0f813676cf787271a48da563` |
| `experiments/ptr-engine/ptr_engine/errors.py` | `402dc9589d8e8fd5de82ed6c8f3364390e105bf8285eb7c326b799f8200fdba0` |
| `experiments/ptr-engine/ptr_engine/ledger.py` | `4c40f11b29cbda9dfdc752f7d47549cf083349cfa8a583c96437a8133e00967e` |

**No drift.** `resolve.py` and `errors.py` hashes equal the `sha256:` values the fixture
itself records under `sources[]` (`resolve.py:71a14c2c…`, `errors.py:402dc958…`), so the
fixture was generated against exactly these bytes. `ledger.py` is not cited by any of the
12 items; it is hashed because the CALL ids' callees live on `Ledger`.

## 3. Per-id verdict

| # | id | turn | kind | our derivation | fixture `expected` | verdict |
|---|---|---|---|---|---|---|
| 1 | `cp.0.t06` | 6 | CALL | `ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), block_size=scope.block(), entry_text=entry.text)` — 5 kwargs | same callee, same 5 names, 2 values elided `...` | **agree** |
| 2 | `cp.1.t08` | 8 | CALL | `scope.block()` — 0 kwargs | `scope.block()` | **agree** |
| 3 | `cp.2.t12` | 12 | NUM | `64` | `64` | **agree** |
| 4 | `cp.3.t14` | 14 | NONE | no `*.record_refusal` inside `resolve()` | `NONE` | **agree** |
| 5 | `cp.4.t18` | 18 | NUM | `6` | `6` | **agree** |
| 6 | `cp.5.t20` | 20 | NONE | no `*.resolved_count` inside `_refuse()` | `NONE` | **agree** |
| 7 | `cp.6.t24` | 24 | NUM | `31` | `31` | **agree** |
| 8 | `cp.7.t26` | 26 | NUM | `5` | `5` | **agree** |
| 9 | `cp.8.t32` | 32 | NUM | `2` | `2` | **agree** |
| 10 | `cp.9.t36` | 36 | CALL | `ledger.resolved_count()` at L141 (sites L141, L143, L146) | `ledger.resolved_count()` | **agree** |
| 11 | `cp.10.t42` | 42 | NONE | no `scope.block()` inside `_refuse()` | `NONE` | **agree** |
| 12 | `cp.11.t46` | 46 | CALL | `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)` — 3 kwargs | same callee/3 names, `scope` value elided, `, before re-raising` appended | **agree** |

Census of kinds: NUM 5 · CALL 4 · NONE 3 — matches the fixture and `docs/PARM-1-ERRATA.md`.

## 4. Five derivations in full (so the agreement is checkable)

### `cp.0.t06` — the recording call in `resolve()` (CALL, 5 kwargs)

`ptr_engine/resolve.py:158-165`, one `*.record_resolution(...)` call in the function:

```python
158	    if ledger is not None:
159	        ledger.record_resolution(
160	            scope=scope.name,
161	            serialized_ref=presented,
162	            bytes_appended=len(presented.encode("utf-8")),
163	            block_size=scope.block(),
164	            entry_text=entry.text,
165	        )
```

`ast.unparse` of `bytes_appended`'s value renders **single** quotes:
`len(presented.encode('utf-8'))`. Kwarg set = `{scope, serialized_ref, bytes_appended,
block_size, entry_text}` — **exact**, five of five, no subset and no superset. Source order is
*not* alphabetical; the answer contract demands alphabetical
(`block_size, bytes_appended, entry_text, scope, serialized_ref`). `grade_v5.grade_cell`
compares `set(got_kwargs) != set(expected["kwargs"])` and then values by name, and records
`kwargs_as_written` without grading it, so order is cosmetic — but an agent that copies the
source order still answers correctly while an agent that follows the stated contract also
answers correctly. See **F2**.

### `cp.2.t12` — `DEFAULT_MAX_REFS` (NUM)

`ptr_engine/resolve.py:39`: `DEFAULT_MAX_REFS = 64` (module-level `ast.Assign`; the symbol is
also the `Scope.max_refs` field default at L55). Answer `64`.

### `cp.6.t24` — every `Ptr*` class in `errors.py` (NUM)

An AST census of `errors.py` top-level `ClassDef` nodes returns **31 classes, all of them
named `Ptr*`**, so the two readings of the question ("how many `Ptr*` classes" vs "how many
classes at all") coincide — that coincidence is worth checking, because a fixture whose
truth came from `len(all classes)` would pass a run that never applied the `Ptr` filter:

```
31 = PtrError, PtrSyntaxError, PtrUnknownKindError, PtrUnknownIdError,
     PtrScopeUngrantedError, PtrProjectionUngrantedError, PtrPointerError,
     PtrBudgetExceededError, PtrRevisionError, PtrHashMismatchError, PtrStoreMissError,
     PtrWarmpoolViolationError, PtrExtensionError, PtrDuplicateIdError, PtrMaterialError,
     PtrNotAReferenceError, PtrUnresolvedRefError, PtrBodyMismatchError,
     PtrTokenSourceRequiredError, PtrAnnotationError, PtrLedgerError, PtrLedgerCountError,
     PtrLedgerBlockSizeError, PtrLedgerIdError, PtrLedgerScopeError,
     PtrLedgerRefusalCodeError, PtrLawError, PtrLawUnknownServerError,
     PtrLawBoundInvalidError, PtrLawSeriesLengthError, PtrLawObservedInvalidError
```

The three sibling counts follow from the same census and are **nested, not disjoint**:
`PtrLedger*` **6** (incl. `PtrLedgerError`), `PtrLaw*` **5**, `PtrUnknown*` **2**; and
`6 + 5 + 2 = 13 < 31`, so no item is double-counted except that `PtrLedgerError` and
`PtrLawError` are *both* prefixes of families (the fixture's question text names the prefix
explicitly, so there is no ambiguity to resolve).

### `cp.9.t36` — first of three `resolved_count()` sites (CALL, 0 kwargs)

`ptr_engine/resolve.py:141,143,146` — three `ledger.resolved_count()` calls inside
`resolve()`; the first is L141 in `if ledger is not None and ledger.resolved_count() >=
scope.max_refs:`. Callee `ledger.resolved_count`, **0 kwargs**, so the only contract-valid
answer is `ANSWER: CALL ledger.resolved_count()`. A zero-arg CALL is the strictest CALL
form: `set() != set()` fails on any invented kwarg, so this id cannot be passed by
decoration.

### `cp.11.t46` — what `_refuse` calls and passes (CALL, 3 kwargs)

`ptr_engine/resolve.py:66-71`, the whole function:

```python
66	def _refuse(ledger: Optional[Ledger], scope_name: str, text: str, error: PtrError) -> None:
67	    """Record the refusal before re-raising. A refusal is a measurement too."""
68	    if ledger is not None:
69	        ledger.record_refusal(
70	            scope=scope_name, serialized_ref=text, code=error.code
71	        )
```

Kwarg set `{scope, serialized_ref, code}` — **exact**, 3/3; values `scope_name`, `text`,
`error.code`. Note the value for `scope` is the *parameter* `scope_name`, **not** `scope` —
a plausible wrong answer is `scope=scope.name`, which the grader would reject on value.
The fixture elides exactly that value as `scope=...`, so an answer of `scope=...` **passes**
(**F1**).

## 5. The three NONE ids — decidable, but constant-answer

"Unanswerable by construction" is **not** what these are, and the distinction matters for H3.
For each, the source fact that would have to exist is named, and it does not exist:

| id | question | fact that would have to exist | does it exist? | graded truth |
|---|---|---|---|---|
| `cp.3.t14` | Does `resolve()` **itself** call `ledger.record_refusal()`? | an `*.record_refusal(...)` Attribute-call node inside `resolve()` (L74–166) | **no.** `resolve()` has one bare `_refuse(...)` at L155 and one `ledger.record_resolution` at L159; the refusal write happens one frame down, inside `_refuse` | `NONE` |
| `cp.5.t20` | Does `_refuse()` call `ledger.resolved_count()`? | an `*.resolved_count(...)` inside `_refuse` (L66–71) | **no.** `_refuse`'s body is one `if` and one `ledger.record_refusal` | `NONE` |
| `cp.10.t42` | Does `_refuse()` call `scope.block()`? | a `*.block(...)` inside `_refuse` (L66–71) | **no** | `NONE` |

So all three **agree**, and all three are **decidable** — `grade_v5` makes NONE a real
verdict (`none_confirmed_absent_in_source` vs `none_contradicted_by_source`, naming the
offending call site when the source does call it). What is *not* true is that they are hard:
the answer is the constant `ANSWER: NONE`, so an arm that answers `NONE` to everything
collects **3/12 = 25 %** of H3's denominator for free. That is `PARM-1-ERRATA` E1's
"constant-answer floor", and this unit independently confirms it as a property of the
fixture, not of the grader.

`cp.3.t14` deserves one extra sentence: its question says "**itself**", and the source does
call `_refuse` from inside `resolve()`, which *indirectly* writes a `record_refusal` row. Read
without the word "itself" the item would be genuininely ambiguous (the behaviour happens;
the call does not). The word is present, so the only defensible reading is NONE — but it is
the one item in the twelve whose truth rests on a word in the question rather than on the
call graph alone. Noted as a residual reading risk, not as a disagreement.

## 6. The double-encoding trap

The grader compares **decoded** strings: `grade_v5` uses `json.load`, so a `\u003d` in the
JSON *text* becomes `=` before any comparison, and the answer contract's `=` separators
never survive as escapes.

Measured, not assumed (`encoding` block of `measure/v-fixture-v7.json`):

- this fixture contains **no `\u003d` escape** (`raw_contains_u003d_escape: false`); its
  `=` characters are literal, and the only escaped sequence is `\u2014` (em dash, in the
  repair prose) — so a checker that compared raw JSON text would *not* have been caught here;
- the escape path is therefore proven by construction: rewriting every `=` in the file to
  `\u003d` yields a file that decodes to a **byte-identical structure**
  (`json.load(escaped) == json.loads(original)` → `True`) and the audit still reports
  **12/12 agree, exit 0**;
- my audit compares `json.loads(raw)` values only, never `raw`; the `raw` text is used for
  exactly one thing — reporting whether the escape is present.

## 7. CALL argument sets and the false-positive surface (F1)

Name-set verdict per CALL id, from the source:

| id | source kwarg set | fixture names | verdict |
|---|---|---|---|
| `cp.0.t06` | 5 (`scope, serialized_ref, bytes_appended, block_size, entry_text`) | same 5 | **exact** |
| `cp.1.t08` | 0 | 0 | **exact** |
| `cp.9.t36` | 0 | 0 | **exact** |
| `cp.11.t46` | 3 (`scope, serialized_ref, code`) | same 3 | **exact** |

**No name subset, no name superset.** That is the good news, and it is enforced at grading
time rather than trusted: `grade_v5._check_documented_call` compares the documented kwarg
**set** with the AST's and calls `_spec_error` — aborting the whole grading — when they
differ, so a fixture that named a subset would not silently pass; it would refuse to grade.

**The silent risk is elsewhere — elided values.** `_check_documented_call` records every
documented kwarg whose value is literally `...` into `cell["elided_kwargs"]`, and
`grade_cell` then does:

```python
if name in truth.get("elided_kwargs", []) and have in ("...", "\u2026"):
    continue          # the fixture itself elides this value; the name is graded
```

Consequences, measured on this fixture:

- `cp.0.t06` elides **2 of 5** values (`bytes_appended`, `entry_text`);
- `cp.11.t46` elides **1 of 3** values (`scope`) — the very value that distinguishes
  `scope=scope_name` from the tempting `scope=scope.name`.

So **3 of the 8 substantive CALL values (37.5 %)** can be answered with a literal `...` and
still grade `pass`. An arm that names the callee and the three or five kwarg names but
elides every unknown value scores **pass on all four CALL ids**. H3's CALL column is
therefore not measuring "the literal values" for those three kwargs; the question text on
`cp.11.t46` ("what does it pass?") asks precisely the thing the truth declines to grade. This
is the one place where a wrong answer can quietly move the quality column, and it is a
*documentation* choice (the `...` is inherited from the v4 slice's `scope=...`), not an AST
error.

A smaller asymmetry in the same vein: because comparison is exact text after whitespace
normalisation, `bytes_appended=len(presented.encode("utf-8"))` with **double** quotes fails
while the AST's `len(presented.encode('utf-8'))` with **single** quotes passes. An eliding
answer is safe; a hand-transcribed but semantically identical answer is not.

## 8. Red case that bites

The checker must be able to say `disagree`. Three runs against `/tmp` copies (the original
fixture was never written):

**Red 1 — one NUM truth mutated** (`cp.6.t24` `expected` `31` → `30`):

```
[disagree] cp.6.t24    t24 NUM  ours="31"
           fixture: "30"
counts: {"agree": 11, "disagree": 1, "ambiguous": 0}
EXIT=1
```

Exactly that id, no others, and a non-zero exit.

**Red 2 — a documented kwarg dropped** (`cp.11.t46` → `ledger.record_refusal(scope=...,
serialized_ref=text)`):

```
[disagree] cp.11.t46   t46 CALL ours={"callee": "ledger.record_refusal", "kwargs": {"scope": "scope_name", "serialized_ref": "text", "code": "error.code"}}
           kwarg name set: SUBSET: fixture omits ['code']
counts: {"agree": 11, "disagree": 1, "ambiguous": 0}
EXIT=1
```

**Green — restore** the untouched fixture and re-run: `counts: {"agree": 12, "disagree": 0,
"ambiguous": 0}`, `EXIT=0`; `sha256sum` of the fixture afterwards is still
`42b4df00…8392`, i.e. identical to the pin in §2.

## 9. What this unit does not claim

- It does **not** claim the 12 truths are hard, only that they are **right**. §5 and §7 say
  where they are cheap.
- It does not re-derive the three non-checkpoint acceptance facts (`acc.1`–`acc.4`) or the
  `repair.t30` item; those are `fixture_coverage.py` / `PARM-1-ERRATA` territory.
- It does not edit, and did not edit, the fixture, any `tasks-v*/` file, any `ptr_engine/*.py`
  or test file, or any measurement file.
- Truth is derived by `grade_v5.derive_truth` from the **live** `experiments/ptr-engine/`
  tree at grading time, not from a snapshot stored in the fixture. It is stable here only
  because `resolve.py` is pinned by the fixture's own recorded sha and by `acceptance`
  constraint `acc.n3b` (`no_write` on `ptr_engine/resolve.py`). If an arm writes
  `resolve.py` — which the long-run *objective* ("make every `resolve()` refusal write its
  ledger row") arguably invites, and which `acc.n3b` forbids — the twelve truths move with
  the tree, and `cp.3.t14` in particular can flip from `NONE` to a CALL. Recorded as an
  observation for whoever owns `RUN-A*`; it is not a defect in the twelve expected values as
  measured against the pinned tree.

## 10. Reproduce

```bash
python3 experiments/ptr-engine/tools/fixture_v7_audit.py            # exit 0, 12/12 agree
python3 experiments/ptr-engine/tools/fixture_v7_audit.py --json      # machine-readable
python3 experiments/ptr-engine/tools/fixture_v7_audit.py --fixture /tmp/mutated.json  # exit 1
```

Note for the next run: in this harness each `bash` call gets a **private `/tmp`**, so a
`/tmp` fixture written in one call is gone in the next — build and consume it inside one
call.
