# V-SPAWN-ATTACK-2 — independent attacker on the hardened refusal-spawn validator

**Scope.** `experiments/ptr-engine/longrun/spawn_record.py::validate_refusal` (the repair in
`orchestration/handoffs/SPAWN-VALIDATOR-FIX.json`) and the published record
`experiments/ptr-engine/measure/PREFLIGHT-SPAWN-DECLARE.json`. Rule under test: *a refusing
invocation must produce zero `runner_launch` spawns at every exit in {2,3,4,8,12}; every
preflight spawn must be declared with its phase; an undeclared spawn is a failure; an empty
declaration is not a declaration.*

**Frozen tree seen.** `cell.py` sha256 `b549e45e12beacbd11cd41a523087d2f6f327f608380528bc6b566c296937488`,
`spawn_record.py` sha256 `04db083e7180250e984e9bc59acf0001ce7938d074e8a80975106a752c7c9dc3`,
git HEAD `f17663d1fed0162a7dc3c5a0a58d372c710974c3`. Both audited files are **untracked** in git
(`??` in `git status --porcelain`), so no commit binds them.
Audited files were only READ; every mutation happened on /tmp copies.

## 1. My oracle vs the record vs the validator
Own instrumentation: `strace -f -e trace=execve` around the real `cell.py` (no sitecustomize,
`SPAWN_ORACLE_LOG` stripped from the env) — an execve count, not a Popen subclass.
Three numbers per exit:

| exit | my execve spawns | record declares | record counts | validator (`--observed <mine>`) |
|---|---|---|---|---|
| 2 | 0 | 0 | preflight 0 | OK (exit 0) |
| 3 | 1 | 1 | preflight 1 | OK |
| 4 | 1 | 1 | preflight 1 | OK |
| 8 | 1 | 1 | preflight 1 | OK |
| 12 | 1 | 1 | preflight 1 | OK |

`runner_launch = 0` at every one, and each child is `/usr/bin/python3 <runner> --dry-run …`.
Agrees with the record's `per_exit_code` (0,1,1,1,1) and with the card's claim. **Reproduced.**

## 2. The five listed rejections — all refuse, each naming its part
1. no `spawns` key → *"record has no `spawns` key at all…"* (exit 1)
2. `spawns: []` + no declaration block → *"empty claim: `spawns` is empty AND the record carries no
   declaration block…"*
3. declaration with no phase → *"spawn declared with no phase (purpose='preflight_self_check')…"* +
   *"declaration block names no phase…"*
4. counts off by one (declared 2 vs 1) → *"counts[preflight_self_check]: declared 2 vs recomputed 1 at
   exit 4…"*
5. `runner_launch` entry on a refusal → *"runner_launch entry for refusal exit code 4: - /bin/true"* +
   *"runner_launch=1 on a refusing invocation (must be 0)"*.
All five exit non-zero through the CLI (`spawn_record.py --validate`).

### Two the author did not list — both PASS THE VALIDATOR
6. **Declaration naming exits outside the refusal set.** A structurally valid record whose
   `per_exit_code` declares coverage only for exits **0 and 7** (no refusal exit at all) →
   `spawn_record: OK exit=4 spawns=1 runner_launch=0` (**exit 0**). Related: a record with
   coverage for exit 4 only is equally green, so the validator never checks that a record covers
   {2,3,4,8,12}. The declaration-evidence question is per-call, not per-record.
7. **Duplicate declarations for the same exit that disagree.** Two `"counts"` keys in one JSON
   file (first `preflight_self_check: 9`, second `1`) → Python's last-wins silently discards the
   first; validator prints `OK … spawns=1` (**exit 0**). No duplicate-key detection, no
   canonicalisation. A record's declaration can be rewritten by key order.

## 3. STALE RECORD — finding: a record can outlive its tree
Today the record's `current_tree.cell_sha` (`b549e45e…`) *does* equal the current `cell.py`, so the
sample is honest. But `validate_refusal()` has **no sha/tree input at all** (`validator_has_sha_param:
false`; the only "sha" string in the file is a comment), and both audited files are untracked, so
nothing binds a record to a tree state.
Demonstration on /tmp: took the real exit-4 invocation (same argv, same env), wrapped the real
`cell.py` and made **one gate permissive** (G1 ledger gate returns `ok=True` on an over-cap cell).
Result: the same argv that refused **exit 4** now refuses at **exit 12** (G3 prereg), publishes a
*different* refusal record, and the historical exit-4 record — whose `spawns`/`counts`/`validation`
describe a run that no longer happens — still validates **OK exit=0**.
Verdict for this attack: **(b) accepts it silently** → *a record can outlive its tree*.
(A second mutation of G3 would be needed to reach stage 4/7 and launch a runner; not attempted.)

## 4. Silence and truncation — pass
- Record truncated mid-JSON → CLI exit **2**, `cannot read …: Unterminated string starting at: line 17
  column 5` — a parse failure with a message, no default `ok`.
- `validation.ok: true` with counts declared 3 vs recomputed 1 → **refused**, with
  *"self-reported validation.ok=true contradicted by recomputation at exit 4…"*. The criterion is the
  recomputation/oracle, not the field. **Pass.**

## 5. Non-vacuous green — pass
Real record at exit 4: `OK exit=4 spawns=1 runner_launch=0`. Delete the single
`preflight_self_check` entry (keep `counts`/`rule`): verdict flips to exit 1 with
*"counts[preflight_self_check]: declared 1 vs recomputed 0…"* and *"declaration block names no
phase…"*. The validator is demonstrably reading that entry and that declaration.

## 6. What it still cannot see (report, not fixed)
`cell.py` spawns only through `subprocess.run` at two sites: `cell.py:207` (`_run`, which records
purpose/phase) and `cell.py:1548` (the runner launch). No `os.system`, no `os.exec*`, no
`posix_spawn`, no `fork`, no `threading`, no `multiprocessing` anywhere in `cell.py` today.
The instrumentation is a `sitecustomize` **subclass of `subprocess.Popen`**, and the record's
`SpawnRecord` is filled in by explicit callsites — so it covers exactly one primitive:
Python-level `subprocess.Popen`/`subprocess.run` that goes through the module. It cannot see:
`os.system`, `execv`/`execve`, `posix_spawn`, a C library or third-party package spawning for
itself, or a thread that spawns after the ledger is published.
Demonstrated: a /tmp wrapper calling `os.system('/bin/true')` before a real exit-2 refusal produced
**2** real execve spawns (`/bin/sh`, `/bin/true`) per strace, the record declares **0**, and the
validator says `OK exit=2 spawns=0 runner_launch=0`. Also: `--observed` is caller-supplied, and the
record's own `observed` field is written by the audited process and never re-read by
`validate_refusal` — so with no tripwire mounted the record is the only witness.

## Verdict
`partial`. Listed attacks 1, 2(1–5), 4, 5 pass; attack 3 returns (b) and two unlisted declaration
attacks pass the validator. Not a defeat of the repair — the repaired rejections bite and the
oracle-equality rule holds for Popen-shaped spawns on this tree — but the record is not yet a
tree-bound, coverage-complete, primitive-complete gate.
Bounded at 21/24 tool calls; verdict row PASS recorded on
`python3 -m pytest -q experiments/ptr-engine/longrun/tests/test_spawn_classification.py` @
`f17663d1`.
