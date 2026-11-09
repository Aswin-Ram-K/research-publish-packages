# BUDGET-STAGE-MAX-TURNS

**Unit contract (as received):** make the budget stage price *the cell that will actually
run*, and nothing else. One function, one line of logic, five proofs. OFFLINE only.

**Status: partial** — the defect is fixed and proven, but one of the five required proofs
(the literal `run_a_star.py --canary --dry-run` end-to-end) cannot be produced right now:
the harness pin is stale for a reason outside this unit (see §5).

**Write paths (exactly these):**
`experiments/ptr-engine/longrun/cell.py` ·
`experiments/ptr-engine/longrun/tests/test_budget_turn_scope.py` ·
`orchestration/units/BUDGET-STAGE-MAX-TURNS.md` ·
`orchestration/handoffs/BUDGET-STAGE-MAX-TURNS.json` ·
`orchestration/journals/BUDGET-STAGE-MAX-TURNS.jsonl`

---

## 1. The defect, restated from measurement (not from the card)

`stage_budget` (cell.py:354) asked the runner's own `--dry-run` what the cell would send,
but built its argv **without** `--max-turns`, while `stage_run` (cell.py:1557-1565) does:

```python
n_turns = int(args.turns or 0)
...
truncated = bool(n_turns and fixture_n and n_turns != fixture_n)
if truncated:
    argv += ["--max-turns", str(n_turns)]
```

## 2. PREMISE CORRECTION #1 — forwarding the flag alone is a no-op (measured)

The card's proposed one-line fix was "forward `--max-turns` under the same condition as
`stage_run`". I measured the runner's side first, as instructed:

```
$ python3 run_longrun.py --dry-run --fixture tasks-v6/LR-01.v8.json --arms pointer-stable --reps 1
  pointer-stable      turn_requests=48 (N=48 x reps=1)  digest_requests=0  cell_total=48
  would_send_total=48

$ python3 run_longrun.py --dry-run --fixture tasks-v6/LR-01.v8.json --arms pointer-stable --reps 1 --max-turns 12
  pointer-stable      turn_requests=48 (N=48 x reps=1)  digest_requests=0  cell_total=48
  would_send_total=48
```

`--max-turns` **is** a supported runner flag — `run_longrun.py:2825-2826`
`ap.add_argument("--max-turns", type=int, default=0, help="stop each cell after this many
turns (0 = the fixture's N)")` — and the runner does derive `n_turns` from the fixture's
own `N`, then cap it (`run_longrun.py:457-460`):

```python
n_turns = int(fixture["N"])
max_turns = int(getattr(cfg, "max_turns", 0) or 0)
if max_turns > 0:
    n_turns = min(n_turns, max_turns)
```

But that cap lives in `projected_requests` (:457) and `run_cell` (:2235) — the **live**
paths. The **dry-run** path never consults it: `run_dry` (:2042) loops
`for t in range(1, int(fixture["N"]) + 1)` (:2079) and the REQUEST COUNTS block prints
`turns = int(fixture["N"]) * c["reps"]` (:2121-2127). So a forwarded `--max-turns` would
have moved the LIVE run and left the price at N — the card's one line would have fixed the
argv, not the ticket.

**What was therefore implemented, still inside `stage_budget` only:** forward
`--max-turns` (argv parity with `stage_run`, and correct the day the runner's dry run
honours it) **plus** one scoping line that removes exactly the turns that will not run,
priced at the runner's own per-arm `N`:

```diff
@@ -358,6 +358,18 @@
     argv = [sys.executable, RUNNER, "--dry-run", "--fixture", args.fixture,
             "--arms", args.arm, "--reps", str(args.reps)]
+    # BUDGET-TURN-SCOPE: price the cell the LIVE path will actually run. stage_run caps a
+    # partial cell at --turns (same condition, read the same way: n_turns set AND different
+    # from the fixture's N); this argv used to omit it, so the runner priced the fixture.
+    n_turns = int(args.turns or 0)
+    fixture_n = 0
+    try:
+        fixture_n = int(_load_fixture(args.fixture).get("N") or 0)
+    except (OSError, json.JSONDecodeError):
+        pass
+    truncated = bool(n_turns and fixture_n and n_turns != fixture_n)
+    if truncated:
+        argv += ["--max-turns", str(n_turns)]
@@ -367,6 +379,17 @@
     would = int(m.group(1))
+    priced_n = max([int(x) for x in re.findall(r"N=(\d+)", out or "")] or [fixture_n])
+    if truncated and priced_n > n_turns:
+        would -= (priced_n - n_turns) * _arms_count(args.arm) * int(args.reps or 1)
     required = int(math.ceil(would * (1.0 + BUDGET_HEADROOM)))
```

(The comment text is in the file; abbreviated above.) `priced_n` is read from the runner's
own per-arm line, so a runner that later honours `--max-turns` makes the scoping a no-op
instead of a double discount. Digest requests and tool follow-ups stay priced — the line
can raise the price, never lower it below what was committed.

**Untouched:** `BUDGET_HEADROOM`, every gate threshold, `stage_run`, `eval_gate_*`,
`EXIT_TABLE`, `run_longrun.py`.

## 3. PREMISE CORRECTION #2 — editing cell.py cannot move the harness digest

`HARNESS_FILES` (cell.py:130-136) is `run_longrun.py, client.py, grade_v5.py,
analyze_stats.py, tools/det_verify.py` + the fixture. **cell.py is not in its own list**
(the pin file says so itself: `"digest_recipe": "... names = cell.py HARNESS_FILES
(cell.py:128-135) + 'fixture' ... cell.py is NOT in its own list."`). The digest is
therefore identical before and after this unit:

```
harness_sha256_now = a3fa2ee0e771a010cc8c2ca28d2e253a005fc69cb1f2d425ae91a9155a5e970a
```

…and it does **not** match `measure/HARNESS-PIN.json` generation 4
(`fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`) because
**grade_v5.py** moved after the pin was frozen — not because of this unit:

```
SAME  analyze_stats.py 30b07d4d61930e0c pinned 30b07d4d61930e0c
SAME  client.py        5aa23bb5470b7e09 pinned 5aa23bb5470b7e09
SAME  fixture          0804b51575cce345 pinned 0804b51575cce345
MOVED grade_v5.py      3d70ed1d43d2ab09 pinned 056eb605e2baf5c9
SAME  run_longrun.py   b20030386610c58b pinned b20030386610c58b
SAME  tools/det_verify.py 12ccc74ea31c3843 pinned 12ccc74ea31c3843
```

So: **the pin is stale, but not by design of this card and not by this card's edits.** It
was already stale on entry; the next launch needs a regenerated pin either way.

## 4. The five proofs

**(a) canary shape `--turns 12` prices 12, G2 admits 720 s of 900 s**

```
$ python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable --fixture
  experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 12 --reps 1 --budget 1 --hypothesis smoke
cell: 3/7 budget REFUSED(3) would_send_total=12 +10% headroom = 14 exceeds --budget 1 (project quota remaining 3192, best-effort)

$ # same cell, budget 60 and the canary's 900 s wall
cell: 3/7 budget ok would_send_total=12 +10%=14 <= budget=60 (quota_remaining=3192 best-effort)
cell: 3b/7 projection ok turns=12 projected_requests=12 projected_wall~=720s
      (cap-per-turn 180s -> worst case 2160s) cap=900s projected-turn-wall=60.0s source=artefact-mode thinking=absent
```

`--budget 1` is used to stop the cell at stage 3, so no request is ever reached.

**(b) grid shape `--turns 48` (== fixture N): argv byte-identical, no `--max-turns`**

```
(b) AFTER  --turns 48: exit=3
cell: 3/7 budget REFUSED(3) would_send_total=48 +10% headroom = 53 exceeds --budget 1 ...
(b) BEFORE --turns 48: exit=3
cell: 3/7 budget REFUSED(3) would_send_total=48 +10% headroom = 53 exceeds --budget 1 ...
--- argv diff at 48 (empty == byte-identical) ---
DIFF EMPTY
--max-turns in after argv: 0
--max-turns in before argv: 0
```

**(c) `--turns 24` (a partial cell) prices 24**

```
cell: 3/7 budget REFUSED(3) would_send_total=24 +10% headroom = 27 exceeds --budget 1 ...
```

**(d) end-to-end canary dry run — BLOCKED by the stale pin, then green per cell**

Literal command, as specified:

```
$ python3 experiments/ptr-engine/tools/run_a_star.py --canary --dry-run --tools read_file
RUN-A canary arms=4 cells=1,4,7,9 turns=12 requests=48 claim=smoke
RUN-A DRY cell 1 pointer-stable r1 rc=2 no gate line
... cells 4, 7, 9 the same ...
RUN-A DRY END cells=4 refused=4 requests=0 claim=smoke turns=12 max_wall=900 ...
```

The rc=2 is not a G2 refusal; it is the harness pin:

```
cell: 2/7 harness REFUSED(2) harness changed mid-cell: --expect-harness
  fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac but the current digest is
  a3fa2ee0e771a010cc8c2ca28d2e253a005fc69cb1f2d425ae91a9155a5e970a ...
```

Dropping only `--expect-harness` (the launcher's own pin flag; nothing else changed), the
same four canary cells report **refused = 0** at 12 turns:

```
cell: 0/7 dry-run would cost: turns=12 arms=1 reps=1 -> 12 requests (incl. follow-up
      allowance 2), ~720 s projected wall; 0 requests sent, no endpoint contacted
cell: 0/7 dry-run G2 allow computed=720 s limit=900 s (--max-wall) ...
cell: EXIT 0 — dry run: 0 of 3 gate(s) would refuse ...
```

…for all four arms (`pointer-stable`, `transcript-grow`, `transcript-compact`,
`lease-reopen`). No `--dry-run`-less call was made and no endpoint was contacted.

**(e) red→green**

```
=== BEFORE (reverted /tmp copy) --turns 12 --budget 60 --max-wall 900 ===
cell: 3/7 budget ok would_send_total=48 +10%=53 <= budget=60 (quota_remaining=3192 best-effort)
cell: 3b/7 projection turns=12 projected_requests=48 projected_wall~=2880s ... cap=900s ...
cell: 3b/7 projection REFUSED(8) G2 projection REFUSED: computed 2880 s | limit 900 s (--max-wall)
cell: EXIT 8 — refused at stage 3b/7 projection; nothing was measured

=== AFTER (fixed cell.py), identical command ===
cell: 3/7 budget ok would_send_total=12 +10%=14 <= budget=60 (quota_remaining=3192 best-effort)
cell: 3b/7 projection ok turns=12 projected_requests=12 projected_wall~=720s ... cap=900s ...
dry   --dry-run --fixture ... --arms pointer-stable --reps 1 --max-turns 12
live  --fixture ... --arms pointer-stable --reps 1 --rows ... --max-turns 12 --claim-mode smoke
```

The revert is a `/tmp` copy of the tree with the two added hunks removed; the runner in the
green run is a stub (it records argv and prints the fixture price, sending nothing).

## 5. The guard (task 4): `tests/test_budget_turn_scope.py`

Three cases, run through a stub runner so it is offline and can fail:

* partial cell `--turns 12`: **both** builders pass `--max-turns 12`, and the budget price
  is 12;
* full cell `--turns 48` == N: **neither** builder passes the flag, price stays 48;
* agreement sweep over `--turns 12/24/48`: `_max_turns(dry) == _max_turns(live)`.

Green:

```
$ python3 experiments/ptr-engine/longrun/tests/test_budget_turn_scope.py
Ran 3 tests in 0.782s
OK
```

Red, by mutating **one** builder in a `/tmp` copy (the budget builder loses its forward;
`CELL_UNDER_TEST` points the test at the mutant):

```
--------------- MUTANT: stage_budget forward removed ---------------
FAIL: test_partial_cell_both_builders_scope_the_same_turns
AssertionError: None != '12' : stage_budget did not scope the dry run to the cell's 12 turns:
  ['--dry-run', '--fixture', '.../tasks-v6/LR-01.v8.json', '--arms', 'pointer-stable', '--reps', '1']
FAIL: test_the_two_builders_agree_about_turn_scoping (turns=12)
AssertionError: None != '12' : the budget stage and the run stage disagree about turn
  scoping at --turns 12: dry=None live='12'
FAIL: test_the_two_builders_agree_about_turn_scoping (turns=24)
AssertionError: None != '24' : ... dry=None live='24'
Ran 2 tests in 0.584s
FAILED (failures=3)
```

Regression: the longrun suite is 602 passed / 14 failed, and **all 14 are corpus guards
unrelated to cell.py** (`test_regrade_stamp` failing on the same `grade_v5.py` digest move
that staled the pin, `test_journal_lint` on missing journals of other units,
`test_handoff_lint` on `W_NO_COMMANDS` vs `W_NO_COMMAND`, …). The directly relevant files
(`test_cell`, `test_cell_gates`, `test_gate_*`, `test_exit_codes`, the new test) are 66
passed / 30 subtests passed.

## 6. Why the 12-turn canary could never have run while this line was missing

Because the gate that decides "does this cell fit the wall" was fed a request count from
the wrong shape: the dry-run preview priced 12 turns (720 s of 900 s, ALLOW) while the
live launch's budget stage priced the fixture's full 48 (2880 s of 900 s, REFUSED 8) — the
launcher was authorised by one number and refused by another, so the canary was refused at
exit 8 with zero requests every time, no matter how correct the cell itself was.
