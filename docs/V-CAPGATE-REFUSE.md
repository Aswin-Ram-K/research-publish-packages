# V-CAPGATE-REFUSE — attacking the `delta < 0` refusal

Verifier unit. The author's card is `CAPGATE-UNRECORDED-REFUSE`; its handoff is
[CAPGATE-UNRECORDED-REFUSE.json](../orchestration/handoffs/CAPGATE-UNRECORDED-REFUSE.json).
Nothing here was repaired: I did not write it and every mutation lived in `/tmp`.

## 1. The path, re-derived from source (not from the handoff)

`run_longrun.py` (sha256 `29445320c205bfe8c5d52ba150054cdbb4a915f598f0f56588e1b174a9069a61`),
`RequestCapGate.reconcile()` at `experiments/ptr-engine/longrun/run_longrun.py:403-413`:

```python
after = int(report["budget"]["spent"])
expected = self.spent_at_start + self.used_in_run
return {"spent_at_start": ..., "used_in_run": ..., "spent_after": after,
        "expected": expected, "delta": after - expected}
```

`_gate_finish()` at `experiments/ptr-engine/longrun/run_longrun.py:480-540` — branch order is
**manifest write → `delta > 0` → `delta < 0` → else**:

- `:485-488` `except CapRowsUnreadable` → `return {...}, 5` (`CAP GATE ROWS at exit`)
- `:494-508` manifest addendum; a manifest write failure sets `rc = EXIT_CAP_DIVERGENCE`
- `:509-517` `if rec["delta"] > 0:` → `rc = EXIT_CAP_DIVERGENCE` (`RECONCILE DIVERGENCE`)
- `:518-535` `elif rec["delta"] < 0:` → prints `CAP GATE UNRECORDED …`, `rc = EXIT_CAP_DIVERGENCE`
- `:536-538` else → `rc` stays `0` (`reconciled`)

The code leaves the process through `run_cell()`'s single reconcile call,
`run_longrun.py:2585` `_rec, cap_rc = _gate_finish(gate, manifest_path, manifest_sha, rows_path)`
followed by `return cap_rc` (`:2588`); `main()` ends at `run_longrun.py:2914 sys.exit(main())`.
`EXIT_CAP_DIVERGENCE = 9` is declared at `run_longrun.py:297`.

Author's claim that the gate is not in `cell.py` is **true**: `cell.py` has no
`RequestCapGate`/`reconcile`/`UNRECORDED`; it propagates the runner's rc at
`cell.py:1568`.

## 2. Can `delta < 0` still succeed? — no, with one exception in wording

Own fixtures, own gate construction (`RequestCapGate` + real `request_ledger.py`), no author test reused.

| shape | delta | exit | message stream |
|---|---|---|---|
| (b1) last row deleted after the run | −1 | **9** | `CAP GATE UNRECORDED` |
| (b2) every row of the run deleted | −3 | **9** | `CAP GATE UNRECORDED` |
| (b3) the run's rows file never created | −2 | **9** | `CAP GATE UNRECORDED` |
| (a) last line truncated mid-JSON | n/a | **5** | `CAP GATE ROWS at exit: … unparseable row` |
| (c) `delta = -0.0` | 0 | 0 | `reconciled` (correct: `-0.0 == 0`) |
| (c) `delta = -0.5` / `-1.5` | −0.5 / −1.5 | **9** | `CAP GATE UNRECORDED` |

Shape (a) is a **refusal, but not the refusal the card asked for**: an unparseable row file is
classified `CapRowsUnreadable` → exit 5 before `delta` is ever computed. It cannot succeed; the
literal claim "truncated last line exits 9 with UNRECORDED" is not reproduced.

`-0.0` does not slip through: `-0.0 < 0` is false and `delta` 0 genuinely means no divergence.
No production path produces a float (`after` and `expected` are `int`); the float shapes were
fed through a stub gate to exercise the branch condition itself.

All refusal text goes to **stderr** (`print(..., file=sys.stderr)`), never stdout. The card's
"UNRECORDED in stdout" is not what the code does — for a process exit status this is the
conventional stream, but the claim as written is wrong.

## 3. Does the message help?

Yes. Quoted verbatim from the (b1) probe:

```
CAP GATE UNRECORDED (delta=-1) — refusing, exit 9: 1 request(s) reached the wire but their rows
were not written before the run stopped (used_in_run=2 rows_gained=1 headroom_before=35
headroom_after=34 rows=/tmp/vcap/run/rows-own.jsonl); rows were not persisted, so the ledger
cannot be trusted for the next check — it would grant 1 request(s) beyond the true headroom.
```

It names `delta`, the wire-vs-rows gap (`used_in_run` vs `rows_gained`), the headroom before and
after, the rows path, and the consequence. It is not an "error" message.

## 4. The safe direction does not regress

- `delta == 0` → exit **0**, `cap-gate: reconciled — the run's count 2 equals the rows gained 2`.
- `delta > 0` → exit **9**, `CAP GATE RECONCILE DIVERGENCE (delta=+1) …`.
- pre-send `projected > headroom` → exit **4**, asserted by instrumentation, not intent:
  cap 5 with 1 row already spent → 4 slots granted, **4** transport calls, **4** rows written;
  the 5th `acquire` raised `CapRefusal` (`projected=6 over_by=1 — nothing sent`), the refused
  request added **no** transport call and **no** row, and `_cap_stop` returned 4 after
  `delta=0` reconcile.

## 5. Exit code coherence — the real finding

`9` does **not** mean here what the table says. `exit_codes.EXIT_TABLE[9]["name"] == "inconsistent"`,
raise site `cell.py: stage_consistency()`, i.e. grader/analyser disagreement; `docs/EXIT-CODES.md:55`
repeats it. And `exit_codes.RUNNER_MAPPED_TO_CRASH[9]` says, in the table module itself:

> run_longrun.py's EXIT_CAP_DIVERGENCE … It must NOT be propagated as 9: 9 is the CELL's
> grader/analyser-inconsistency code, owned by DECIDABILITY-SEAM …

So the runner reuses an already-claimed number. The source-scan test still balances
(`experiments/ptr-engine/longrun/tests/test_exit_codes.py`: 20 tests, OK). **Recommendation, not a failure:** the unrecorded
refusal deserves its own code, and `RUNNER_MAPPED_TO_CRASH` is the map that would have to learn it.

## 6. Does the fix survive the caller? — **no**

The handoff says "cell.py propagates exit 9 unmodified". That is false, and the caller is
deliberate about it: `cell.py:1568`

```python
code = rc if rc in _RUNNER_CODES else exit_codes.EXIT_RUNNER_CRASH
```

with `_RUNNER_CODES = {2, 3, 4, 5, 6, 7}` (`cell.py:166` ← `exit_codes.RUNNER_CODES`). A runner
rc of 9 is not a member, so it becomes **5**. Proof by running `cell.stage_run` with a fake
runner that exits 9:

```
abort_code: 5, abort_stage: "4/7 run",
abort_message: "run_longrun.py exited 9 (unmapped runner failure) — rows kept at …"
```

Exit 9 is swallowed and remapped. Through the cell, the unrecorded refusal surfaces as
`runner-crash`, whose documented action ("read the runner's stderr") points a reader at a crash
that did not happen. The refusal is still **non-zero**, so no run succeeds past it.

## Red → green of my own

Mutation in `/tmp` only: `sed 's/    elif rec\["delta"\] < 0:/    elif False:  # MUTANT/'`.
With the branch disabled, all three `delta < 0` shapes exit **0** and print the false comfort
`cap-gate: reconciled — the run's count 2 equals the rows gained 1 (delta 0)`; `-1`, `-0.5`,
`-1.5` all exit 0. Restored pristine source: 9. `run_longrun.py` and `cell.py` sha256 identical
before and after every probe.

## Residual gap (reported, not fixed)

`run_cell()` returns 6 (runaway) at `run_longrun.py:2327`, `:2382`, `:2469`, `:2565` **without**
calling `_gate_finish`, so those exits never reconcile. Exit 6 cannot be mistaken for success,
but a runaway can end with the ledger disagreeing and no `UNRECORDED` line at all.

## Verdict

`overall: partial` — the refusal itself holds for every `delta < 0` shape that reaches it, and
the safe direction is intact; but shape (a) takes a different code (5), the message is on stderr
rather than stdout, and the propagation claim the handoff makes is measurably false (9 → 5).
