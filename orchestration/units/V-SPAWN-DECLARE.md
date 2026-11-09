# V-SPAWN-DECLARE — independent attack on PREFLIGHT-SPAWN-DECLARE

**Role.** Attacker, not author. Did not write the card. Offline: zero inference requests.
All mutation on `/tmp/vspawn` copies; the audited files (`cell.py`, `spawn_record.py`,
`docs/GATE-CHAIN.md`, the tests) were never edited.

**Tree seen.** `f17663d1fed0162a7dc3c5a0a58d372c710974c3`.

**Claim under test.** A refusing `cell.py` records every spawn `{argv, purpose, phase}`,
`purpose in {preflight_self_check, runner_launch, other}`; a refusal must have
`runner_launch == 0` at every exit in `{2,3,4,8,12}`; every preflight spawn declared with
its phase; undeclared spawn = failure; table 2/3/4/8/12 → declared preflight 0/1/1/1/1,
oracle Popen 0/1/1/1/1, runner_launch 0.

**Method.** Own harness (`/tmp/vspawn/lib.py`, `all.py`), own ledger/runner fixtures, own
`sitecustomize` `subprocess.Popen` subclass as oracle — the author's test module was not
imported. Every case run twice.

**Attacks and results.**
1. Table reproduced exactly, twice (0/1/1/1/1 declared == oracle; runner_launch 0).
2. Oracle not vacuous: a bare child's two real spawns are counted; an unrecorded-spawn
   mutant shows oracle=2 vs declared=1.
3. `validate_refusal()` rejects `purpose=other` and any `runner_launch` row, but **accepts
   a record with the declaration block deleted** and an empty record → fail-open.
4. No invocation in the refusal set launched the runner (`--turns 0`, `--reps 0`,
   `--request-allocation 0`, missing fixture, unwritable out-dir, `--turns 100000`).
   Two of those write no refusal record at all (argparse usage exit 2; unwritable out-dir
   exit 12), so their declared counts are simply unavailable.
5. Doc agrees with code verbatim (`docs/GATE-CHAIN.md:336-353`): same field names, same
   `{2,3,4,8,12}` set, same 0/1/1/1/1 figures. No drift.
6. Only `subprocess.run` is used (2 call sites); recording happens at 2 explicit
   `SpawnRecord`/`validate_refusal` sites. `os.system`, `os.exec*`, `os.fork`,
   `multiprocessing`, `threading`: absent from `cell.py`. Spawns made by a library the
   code calls, or by a bare `subprocess` added without a `record(...)`, are invisible to
   the record — caught only by the oracle-equivalence test, never by `validate_refusal`.

**Verdict.** `partial` — the central claim reproduces; the record-level validator is
fail-open against a deleted/empty declaration block. `RUN-A*`'s gate precondition
(`runner_launch == 0` on every refusal) is met on this tree, provided the oracle test —
not the record's own `validation.ok` — is the gate.
