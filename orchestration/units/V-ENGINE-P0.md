# UNIT V-ENGINE-P0 — independent verifier of `experiments/ptr-engine/`

Status: **COMPLETE**. Verdict: `pass` on the claim under test, with findings recorded
(one guard-coverage gap, two SPEC sentences the code contradicts, one uncalled property).

I am not the author of `experiments/ptr-engine/`. Nothing under `experiments/`,
`release/`, `papers/` or `src/` was modified; every sabotage was applied to a copy at
`.verify-scratch/engine/` and restored from `.verify-scratch/pristine/`.

## The claim under test

`orchestration/handoffs/PTR-ENGINE-P0.json`: `status: done`, evidence
"95 passed in 0.12s; r = bodies/index = 30000/447 = 67.1x (12 items, exactly 30000 body
bytes, index 447 bytes, zero-resolution prompt 472 bytes)".

## Checks and results

### 1. Suite

```
cd experiments/ptr-engine && PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests -q
95 passed in 0.17s
EXIT=0
python3 -m pytest tests -q --collect-only   ->   95 tests collected in 0.05s
```

95 is the real collected count; no skips, no xfail. Wall time 0.17s vs the claimed
0.12s — immaterial, machine-dependent.

### 2. RED→GREEN — six sabotages, one at a time, restored between

Each was applied to `.verify-scratch/engine/`, the suite run, the file restored from
`.verify-scratch/pristine/`; final state re-run clean (`95 passed`, exit 0).

| # | invariant broken | patch | failing test(s) | assertion |
|---|---|---|---|---|
| a | one-way resolution | new public `recover(ResourceRef) -> Reference` in `reference.py` | `tests/test_oneway.py::test_no_public_callable_turns_a_resourceref_into_a_reference` | `assert ['ptr_engine....-> Reference'] == []` (1 failed, 94 passed) |
| b | no-prefetch | `adapter.build_prompt`: `if ledger is not None and not …` → `if False and …` (ledger gate) | `tests/test_noprefetch.py::test_build_prompt_raises_for_a_ref_with_no_resolve_row` | `DID NOT RAISE PtrUnresolvedRefError` — the hash gate (`adapter.py:117`) fired first with `PTR_BODY_MISMATCH` (1 failed, 94 passed) |
| c | capability scope | `resolve`: `if scope.index.scope != scope.name:` → `if False and …` | `test_scope.py::test_the_wrong_scope_is_ungranted`, `test_negative_controls.py::test_four_ungranted_scope`, `::test_all_seven_codes_are_distinct` | `Failed: DID NOT RAISE PtrScopeUngrantedError` / `DID NOT RAISE PtrError` (3 failed, 92 passed) |
| d | determinism | `compile.py` header gains `compiled={time.time_ns()}` | `test_determinism.py::test_two_processes_two_roots_agree`, `::test_material_order_does_not_matter`, `::test_recompiling_into_the_same_store_is_idempotent` | `AssertionError: index bytes differ between two processes` (3 failed, 92 passed) |
| e | append_cost | `annotate.append_cost` returns constant `16` | `test_annotate.py::test_append_cost_is_length_modulo_block_size`, `::test_off_grid_is_detectable_and_on_grid_is_not` | `assert 16 == (16 % 7)`; `an on-grid append must read as 0` (2 failed, 93 passed) |
| f | body-hash gate (not required; author's own recommendation) | `adapter`: `if actual != expected.hash:` → `if False and …` | `test_noprefetch.py::test_build_prompt_refuses_bytes_that_are_not_the_resolved_body` | `DID NOT RAISE PtrBodyMismatchError` (1 failed, 94 passed) |

**Every required sabotage goes red on a specific, named test.** Invariant (b) is doubly
guarded: disabling the ledger gate alone still fails, because the content-hash gate
catches the invented bytes.

### 2b. FINDING — the one-way guard is narrower than the invariant

A *realistic* reverse bridge survives the whole suite. Patch: `resolve()` records
`_ORIGIN[target.hash] = ref`, and a public `recover(rref)` returns `_ORIGIN[rref.hash]`.
Applied to the copy: **`95 passed`, exit 0**, and the round trip works end-to-end
(`recover(resolve(@knowledge:k01@1))` → `@knowledge:k01@1`, equal to the original).

Why: `tests/test_oneway.py:78` calls each public callable with a synthetic `DUMMY`
ResourceRef that no `resolve()` ever produced; a registry lookup raises `KeyError` and
the sweep treats "refusing" as compliant. The invariant "no public callable turns a
ResourceRef into a Reference" is therefore only guarded against helpers that succeed on
a ResourceRef that could never exist.

### 3. Determinism across processes (independent of their test)

Two separate `python3` invocations, different warmpool roots
(`/tmp/ptr-verify-A-*`, `/tmp/ptr-verify-B-*`), same material:

```
sha256 e08700c9876162544ba0f6c73c47868f605d1ebfea2302d2b66eee866a099bd2  (A)
sha256 e08700c9876162544ba0f6c73c47868f605d1ebfea2302d2b66eee866a099bd2  (B)
index_bytes 447 (both)   DIGESTS_EQUAL: True   SIZES_EQUAL: True
```

### 4. `r` recomputed from `examples/`

```
items 12 | total body bytes 30000 | index bytes 447 | index lines 12
r = 30000/447 = 67.1141 -> 67.1x | zero-resolution prompt 472 bytes
```

30000 / 447 / 67.1x / 472 all reproduce exactly.

### 5. SPEC.md vs code

SPEC states all four things asked about:

* six host requirements — `SPEC.md:210-217`, numbered 1–6, plus a per-item table;
* the one-way rule — `SPEC.md:34-49`;
* warmpool isolation — `SPEC.md:105-110`;
* `token_source: null` — `SPEC.md:140-144`.

**Normative sentences the code does not implement:**

1. `SPEC.md:86-87` — "a reference from an older turn still resolves to *those* bytes".
   Measured: `@knowledge:k01@1` against a revision-2 index → **REFUSED
   `PTR_REVISION_MISMATCH`**. The body survives in the store; the *reference* does not
   resolve. `resolve.py:117-123` is deliberate, so the SPEC sentence is the wrong one.
2. `SPEC.md:166` — "Every failure is a `PtrError` subclass with a stable `code`". Six
   bare `ValueError` sites: `ptr_engine/ledger.py:51,60,136,138,141,213`, and
   `tests/test_ledger.py:97` asserts `ValueError` explicitly.

**Behaviour in the code that SPEC does not state:**

* `DEFAULT_PROJECTIONS = {"*": {full, brief, raw, summary}}` and the `projections=`
  override on `compile_turn` / `Scope` (`compile.py:34-36,278`, `resolve.py:54`);
* `DEFAULT_MAX_REFS = 64` — the default budget a host inherits;
* `Scope.block()` falls back to `index.block_size` when `block_size is None`;
* `find_repo_root()` returns `None` outside any repo, and the isolation rule is then
  unenforced (`store.py:42-55`);
* `BodyStore.path_of` refuses a locator escaping the root with `PTR_STORE_MISS`
  (`store.py:128-136`);
* `put` onto an occupied address with a different size raises `PTR_HASH_MISMATCH`
  (`store.py:161-167`);
* the annotation is exported as `entry_scope` (`__init__.py:29`) where `SPEC.md:120`
  names it `scope`.

**Minor imprecision:** `SPEC.md:72-73` says the index line carries "the body's byte
length"; for a pointer item it carries the selected *region's* canonicalised length
(`- @artifact:plan#/goal@1 ac8ce218 25` for a 45-byte body). Consistent with what a
fetch returns, but not what the sentence says.

### 6. Seven negative controls

Seven distinct codes, in the order the test fixes
(`tests/test_negative_controls.py:104-114`):

`PTR_SYNTAX` · `PTR_UNKNOWN_KIND` · `PTR_UNKNOWN_ID` · `PTR_SCOPE_UNGRANTED` ·
`PTR_PROJECTION_UNENUMERATED` · `PTR_POINTER_INVALID` · `PTR_BUDGET_EXCEEDED`

No two are the same; every control's `_code()` asserts `isinstance(error, PtrError)` and
`str(error).startswith(code)`; none is a bare `Exception`. Package-wide: 20 error
classes carry 20 distinct codes.

### 7. Warmpool isolation, both directions

```
BodyStore(<repo>/scratch/verify-warmpool-must-not-exist) -> REFUSED PTR_WARMPOOL_INSIDE_REPO | exists: False
BodyStore(<repo>)                                        -> REFUSED PTR_WARMPOOL_INSIDE_REPO
BodyStore(<repo>/experiments/ptr-engine)                 -> REFUSED PTR_WARMPOOL_INSIDE_REPO
PTR_WARMPOOL_ROOT=<repo>/cache-warmpool                  -> REFUSED PTR_WARMPOOL_INSIDE_REPO
BodyStore(/tmp/ptr-isolation-*/warmpool)                 -> ACCEPTED, created
default_root()                                           -> /home/zer0null/.cache/ptr-engine/warmpool
```

A refused root leaves no directory behind.

## Containment

Writes only to `orchestration/units/`, `orchestration/handoffs/`, `.verify-scratch/**`.
`/home/zer0null/Duval` never touched — no git command was run against it at all.
Warmpool roots for the runs were `tempfile.mkdtemp()` under `/tmp`, removed in
`finally`; a root under `.verify-scratch/` would be refused by the engine's own rule.

## Bound

40 tool calls; used 32. `diff -r --exclude=__pycache__ .verify-scratch/pristine
experiments/ptr-engine` is clean and `experiments/ptr-engine/` carries no `__pycache__`,
so the shipped tree is byte-identical to the pre-sabotage copy — nothing the verifier did
reached it.
