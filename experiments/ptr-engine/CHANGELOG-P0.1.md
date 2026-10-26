# CHANGELOG-P0.1

Closes the four defects recorded in `orchestration/handoffs/V-ENGINE-P0.json`. No new
features, no index-format change, no change to the seven negative-control codes. Suite
before: 95 passed. Suite after: **100 passed** (`TMPDIR=/var/tmp python3 -m pytest tests -q`;
see "Environment" below -- `/tmp` is quota-exhausted on this machine, unrelated to the code).

## D1 — the one-way guard tested a synthetic `ResourceRef` (the real defect)

`tests/test_oneway.py` swept every public callable with `DUMMY`, a `ResourceRef` no
`resolve()` ever handed out, so a registry-backed bridge that answers only *issued* refs
passed the sweep (V-ENGINE-P0 check 2b) while working end to end.

**Changed.** `tests/test_oneway.py` gains `_sweep(rref, extras)` and two behavioural tests:
they `resolve()` a real reference, keep the exact object it returned, prove issuance
behaviourally (`store.get(real)` opens the body; `store.get(DUMMY)` raises a `PtrError`),
then sweep every public callable -- positional and keyword-only -- with that object, with
extra arguments drawn from `(scope)`, `(store)`, `(index)`. Any callable that turns an
issued `ResourceRef` back into a `Reference` is named in the failure. The synthetic-DUMMY
test is kept unchanged; the region-target path (`@artifact:plan#/goal@3`) gets its own
sweep. The module docstring now states why a synthetic ref is not sufficient.

**Evidence (red -> green, sabotage in a throwaway copy under `.p0-scratch/`, removed).**
A registry-backed `recover(ResourceRef) -> Reference` (`ptr_engine/recover.py`, fed from
`resolve()`'s return) makes the new tests fail and leaves the old one green:

    with bridge:    2 failed, 98 passed in 0.97s
                    FAILED test_no_public_callable_turns_a_resolve_issued_resourceref_into_a_reference
                    FAILED test_no_public_callable_turns_an_issued_region_ref_into_a_reference
                    'ptr_engine.recover.recover -> Reference'
    old test alone: 5 passed, 2 deselected        # the synthetic sweep still says "compliant"
    bridge removed: 100 passed in 1.58s

## D2 — SPEC promised that a superseded-revision reference still resolves

Measured: a `Reference` pinned to rev 1 is REFUSED against a rev-2 index with
`PTR_REVISION_MISMATCH`. The code is right -- the store keeps the bytes, the resolver must
not silently point a stale position at newer bytes -- so SPEC was corrected, not the code.

**Changed.** `SPEC.md:85-92` (section 4, item 4) now says exactly: the `ResourceRef` an
older resolve returned still opens *those* bytes via `store.get`; a `Reference` pinned to a
superseded revision is deliberately refused with `PTR_REVISION_MISMATCH`.

**Evidence.** `tests/test_roundtrip.py::test_a_superseded_revision_is_refused_but_its_bytes_survive`
asserts both halves: the refusal and its code, and that the old `ResourceRef` still returns
the byte-identical body. Passes.

## D3 — "every failure is a `PtrError`" vs six bare `ValueError`s

**Changed.** The six sites in `ptr_engine/ledger.py` (51, 60, 136, 138, 141, 213) now raise
five new coded errors from `ptr_engine/errors.py`: `PTR_LEDGER_COUNT`,
`PTR_LEDGER_BLOCK_SIZE`, `PTR_LEDGER_ID`, `PTR_LEDGER_SCOPE`,
`PTR_LEDGER_REFUSAL_CODE`, declared as `LEDGER_CODES` in `ptr_engine/ledger.py` and
exported. They share `PtrLedgerError(PtrError, ValueError)` so callers (and
`tests/test_ledger.py`'s existing refusal test) that catch `ValueError` are not broken --
the code is additive, the exception family is not. SPEC's enumeration grew from seven
controls to twelve named codes; the seven are untouched and asserted disjoint.

**Evidence.** `grep -c "raise ValueError" ptr_engine/*.py` -> 0 matches across the package.
`tests/test_ledger.py::test_ledger_failures_carry_a_named_code_not_a_bare_valueerror` walks
all five codes and both `block_size` sites; `tests/test_negative_controls.py::test_ledger_codes_extend_the_enumeration_without_colliding`
asserts 5 distinct, disjoint from the 7 fixed controls, total 12.

## D4 — two overstatements and one dead field

* **`SPEC.md:44-47`** said the one-way rule is "enforced structurally". It is not: the
  enforcement is the absence of an API plus a test that sweeps the public surface. Reworded
  to "a property of the API surface, not a type-level guarantee ... the package simply has
  no such function", and the sweep it describes is now the behavioural one from D1.
* **`SPEC.md:72-75`** said an index line carries "the body's byte length". For a pointer item
  it carries the selected region's canonicalised length (`@artifact:plan#/goal@1` reads 25
  for a 45-byte body). Reworded, both cases named.
* **`TurnIndex.body_bytes`** (`compile.py:127-135`) had no caller, no test, and booked a
  region's size against the whole-body hash: it reported 102 where the body is 112 bytes.
  **Deleted** rather than documented -- nothing consumes it and the number could not be
  interpreted by a reader. Not serialised, so index bytes are untouched (see below).

**Evidence.** Property absent from `dir(ptr_engine.TurnIndex)`. Worked example unchanged:
`total body bytes 30000`, `index bytes 447`, `r = 67.1x`, index sha256
`e08700c9876162544ba0f6c73c47868f605d1ebfea2302d2b66eee866a099bd2` -- identical to the
verifier's, so neither the index format nor the ratio moved.

## Corrections to the record (immaterial, recorded)

* The V-ENGINE-P0 handoff's engine/tests line split (claimed 1641/1094, total 3281) measured
  1828/1062; the total was right, the split was not. Measured now, after this card:
  engine **1896**, tests **1222**, `SPEC.md` **260**, `examples/worked_example.py` **144**
  (total 3522). Line counts move with every edit; they are reported measured.
* No wall time is claimed as a property. Observed on this machine: `100 passed in 1.58s`
  (also 0.93s, 1.74s across runs); it is machine- and load-dependent.

## Environment (not a code finding)

`/tmp` on this machine is a 15G tmpfs at 80% with the user quota exhausted: a 5 MB write
fails with `EDQUOT`, so pytest's `tmp_path` fixtures error out with
`OSError: [Errno 122] Disk quota exceeded`. All suite runs above used `TMPDIR=/var/tmp`
(115G free, outside the repository, so the warmpool-outside-repo guard still passes). The
leaked `/tmp/seed-shallow-fixture-*` and `/tmp/dsh-workspace-changes-*` directories belong
to other sessions and were not touched.
