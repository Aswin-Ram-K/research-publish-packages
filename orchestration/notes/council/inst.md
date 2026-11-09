# COUNCIL-INST — instrument integrity

**Pick: A** — re-scope `acc.2`–`acc.4`, implemented as *verifier-owned replacement* of the execution evidence, not as weaker proxies.

## What a validity gate is for
Gate 0.1 exists to prove the instrument can certify a good run: a known-good log passes, a wrong-value log fails *on the value*, a missing-fact log fails *distinguishably*, and a tampered fixture exits 2. acc.2–4 as written break that contract: their regex demands `exit 0`, `PtrNotAReferenceError`, `PTR_NOT_A_REFERENCE`, `ledger`, `def test_`, and `9` — facts only producible by running pytest/grep, which the read-only channel (`run_longrun.py:811-812` parses `read_file` only; `:977-984` injects `path_refused` for anything else) cannot produce. The 48-request run confirmed this empirically (zero occurrences; turn 48 answered `NOT-AN-ANSWER`). So acc.2–4 do not certify a good run — they certify confabulation, or impossibility. A gate that can only be passed by fabrication is not a validity gate; it is a trap, and a permanently-red 0.1 (B) fires the stop condition and voids every arm.

## Why A restores rather than deletes the gate
The checks that are genuinely unobservable are the *execution* facts (exit code, grep count). Test execution already belongs to the independent verifier (stage 0.8), not to the agent. Re-homing those two facts there keeps the gate's strength — the verifier actually runs `pytest` and `grep -c` — while the agent-facing checks shrink to read-establishable facts (name the files read, quote the defect lines, identify the missing symbol). Wrong-value and missing-fact logs still fail on distinct check ids, so distinguishability is preserved. The agent is no longer asked to confabulate an exit code it cannot observe.

## Why not C
An exec/shell tool inside an instrument that grades agent behaviour on a shared live server destroys the very thing the negative constraints protect (`no_write` on `test_scope.py`/`test_negative_controls.py`). An agent could edit tests to green, inspect the hidden grader, or exfiltrate; the precedent propagates to every later cell. C trades a fixable scoping bug for an unbounded integrity regression.

## Strongest argument against my pick
A (even verifier-owned) still requires a fixture/grader generation bump and risks the gate degrading into "the agent read some files" — a bar a model could clear by quoting the repo without understanding. The only thing that truly proves the work happened is an execution-style check, which is exactly what C provides; A is a compromise that may keep a weaker gate alive.

## Cheapest evidence that would change my mind
Re-run the existing 48-turn read-only log through a candidate re-scoped fixture and confirm the positive control passes while `neg-one`, `neg-marker`, and `neg-truncated` each fail on *distinct* check ids. If distinguishability collapses, abandon A and take B.
