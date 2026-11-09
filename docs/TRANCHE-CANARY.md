# The pre-tranche canary

**Tool:** [`experiments/ptr-engine/tools/tranche_canary.py`](../experiments/ptr-engine/tools/tranche_canary.py)
**Tests:** [`tests/test_tranche_canary.py`](../tests/test_tranche_canary.py)
**Record of the replay proof:** [`experiments/ptr-engine/measure/TRANCHE-CANARY.json`](../experiments/ptr-engine/measure/TRANCHE-CANARY.json)

## Why this exists

`TRANCH1-DRYRUN-2` passed **10/10** cells offline: gates allowed, treatments fired by T48,
`design_cap_tokens 10616`, 0 spawns, 0 sockets. The live tranche then died on its first
cell: T27 of 48, with **T3** and **T27** each consuming the full 4,096-token completion
ceiling (`length`, then `runaway_turn`, `truncated: true`), exit 6. **28 requests spent, 0
usable cells** (27 turn rows landed on disk).

An offline rehearsal cannot see this class of failure. It is **model behaviour on the chosen
prompts at the chosen channel** — not a gate, a cap, or a socket — so no amount of dry-run
arithmetic finds it. The cheapest instrument that can see it is a few real turns, and the
recorded cell proves the signal is available early: the **first** cap-length completion is
at **T3**.

## The verdict function

Given an arm's cell-1 launch command, run its first **N** turns (default **N = 12** — corrected, see the dated correction below), read
the resulting rows, and return exactly one verdict:

> **CORRECTION 2026-10-26 — `LAUNCH-PACKAGE-RECONCILE`.** The default above **was N = 5**; it is
> now **N = 12**. The superseded wording is preserved here verbatim: *"run its first **N** turns
> (default **N = 5**), read the resulting rows, and return exactly one verdict"*.
> Why it moved: `experiments/ptr-engine/measure/CANARY-ERA-B-FIX.json` records
> `canary_can_gate_era_b: true` and `definitive_verdicts.at_n5` = *"at N=5 era B is structurally
> blind: the first checkpoint is T12, so no tools-on row can carry answer_verified, and no
> cap/storm occurs in turns 1-5"* — tools-on definitive verdicts **0 of 3 at N=5**, and **3 of 3
> from N=12** (`v6_tools N=12` = `shape_ok`, `v4_tools N=12` = `shape_ok`).
> **The gate is:** `N = 12`, `shape_ok`, `answer_verified >= 1`, `stop_signal_source = finish_reason`.
> This paragraph's N is the window only; the four conditions together are the gate.

| verdict | exit | means |
|---|---|---|
| `shape_ok` | 0 | no turn hit the completion ceiling, no stop signal in `{runaway_turn, turn_wall_cap}`, no tool-call storm, and the arm's own answer contract fired in-window — **which contract is consumed depends on the row shape** (below). |
| `shape_degenerate` | 1 | a cap-length completion appeared within N turns — the turn, `completion_tokens`, `max_tokens`, `wall_ms` and the stop signal **and the field it was read from** are named — or a **tool-call storm** appeared. A 4,096-token completion on a question whose answers are a few tokens is a **channel/prompt mismatch**, not a measurement; 130 tool calls against a cap of 2 is the launch failing to fan in. |
| `shape_unknown` | 2 | fewer than N turns recorded, a stop signal outside the closed vocabulary (or missing), no traffic at all, or the answer contract **did not fire inside the window**. Never rounded to `ok`. |
| *(could not run)* | 3 | bad argv, a missing rows path, or a refused launch (`--launch` without `--live`, `--reps` above 1). |

**Priority: a positive degeneration signal outranks a short window.** A cap-length
completion inside the rows we do have is *evidence*; a window that stopped short is only
*absence of evidence*. Two consequences worth stating plainly:

- `shape_ok` is the only verdict that licenses spending tranche turns, and it requires the
  answer contract to have actually produced something parseable. A clean but silent window
  is `shape_unknown`.
- `wall_ms` is a **cost**, never a verdict. A turn that takes 171 s and finishes cleanly is
  slow, not degenerate — pinned by
  `tests/test_tranche_canary.py::test_ok_with_a_slow_but_untruncated_turn`.

Exit codes come from [`experiments/ptr-engine/longrun/exit_codes.py`](../experiments/ptr-engine/longrun/exit_codes.py)
and are imported, not re-typed: 0 `ok`, 1 `internal-error`, 2 `preflight`, 3 `budget` are
the numbers reused here (the table describes the *conductor's* use of the same integers; the
canary prints its own verdict name beside each). One deliberate departure from convention:
**usage errors exit 3, not argparse's default 2**, because 2 is the canary's
`shape_unknown` verdict and an argv typo must never read as a shape verdict.

## Reading the two row shapes (era A / era B)

The canary is asked about two kinds of rows, and they do **not** agree on which field says
why a turn ended. The tools-off cells write the engine-derived `stop_reason`. The tools-on
(`run_longrun.py`) rows carry only the wire `finish_reason`. Reading only `stop_reason` is
exactly what made **3 of 3** tools-on files `shape_unknown` at every N below 48
(`experiments/ptr-engine/measure/CANARY-FALSE-POSITIVE.json`): the reason was in the row,
just not the field the reader looked at.

### Stop-signal precedence (implemented, quoted from `tranche_canary.STOP_SIGNAL_PRECEDENCE`)

```
("stop_reason", "finish_reason", "truncated", "completion_tokens==max_tokens")
```

First present field wins, and the verdict records **which field it read** in
`stop_signal_source`:

1. **`stop_reason`**, when present and non-null. It is the engine's own derivation and the
   only field the tools-off control carries; a weaker signal never overrides it.
2. **`finish_reason`**, when present and non-null. This is the protocol field the tools-on
   rows write instead; `length` means the completion was cut by `max_tokens`, so it is a
   cap-length completion even when the token arithmetic looks short.
3. **`truncated: true`** — an explicit boolean that the content was cut. Read as `length`
   only when no reason field is present, because it does not say *where* the cut came
   from.
4. **`completion_tokens == max_tokens`** — arithmetic last. It is corroboration, not a
   protocol statement, so it must never outrank a field that names the reason.
5. otherwise `None` → `shape_unknown`, as before.

Trigger order inside `shape_degenerate` is fixed — **completion ceiling, then degenerate
stop reason, then tool-call storm** — so a turn that both consumed the ceiling and stormed
is named by the ceiling. This is what keeps the era A control on `completion_ceiling`.

### Which answer contract the verdict consumes — per shape, never averaged

| row shape | detected by | contract consumed | why |
|---|---|---|---|
| **era A** (tools off) | any turn row carries `stop_reason` | `parseable_answers` | the original gate, **deliberately not loosened** |
| **era B** (tools on) | `finish_reason` and/or `answer_verified` present, `stop_reason` absent | `answer_verified` | `parseable_answers` is **structurally 0** on this shape (no `answer_turn`/`answer_value`), so requiring it would make `shape_ok` unreachable; `answer_verified` is the same contract, stated by the harness that actually parsed the answer, and it is non-null only at checkpoint turns (T12/T24/T46 in the recorded runs) |

Both counts are always reported (`parseable_answers`, `answer_verified`,
`answer_verified_false`) so a reader can see the evidence rather than a number that cannot
move. A failed checkpoint is **not** a degeneration mode: era A treats "no parseable answer
in-window" as unknown because the contract may simply fire later, and era B is held to the
same standard. Era B's checkpoint failure therefore shows up as `answer_verified_false > 0`
and, with no verified answer in-window, as `shape_unknown` (`trigger: no_verified_answer`).

### The tool-call storm rule

```
STORM_MIN_CALLS = 110          # requested tool calls in ONE turn
storm  <=>  len(row["tool_calls"]) >= STORM_MIN_CALLS
```

**Measured, not chosen.** The manifest cap is `tools.max_calls_per_turn = 2` (identical in
the v4, v5 and v6 manifests). The two recorded storms fired **116** calls (v4 T45) and
**130** (v5 T29) in one turn, both ending `finish_reason=length`, `failed_turn=true`. The
largest fan-out on a turn the engine **contained** — cap refusals (`turn_call_cap`), 2
executed, `finish_reason=stop` — is **101** (v6 T26). 110 is the midpoint of that observed
gap: above every contained turn seen, below every storm seen.

The false negatives are stated rather than hidden:

- a genuine storm **under 110** calls is not caught (v5 T36 fired 25 against the same cap
  of 2 and is not flagged as a storm);
- a **genuinely thorough** turn above 110 calls is declared degenerate.

The rule is a fan-out bound, not a proof of intent. It is reported as `tool_call_storm`
with the turn and the call count named.

## Era B matrix — what the fixed reader actually says

Offline replay of the recorded rows, zero requests
(`experiments/ptr-engine/measure/CANARY-ERA-B-FIX.json`):

| file | N=2 | N=5 | N=8 | N=12 | N=48 |
|---|---|---|---|---|---|
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` (era A control) | unknown | **degenerate T3 `completion_ceiling`** | degenerate T3 | degenerate T3 | degenerate T3 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | unknown | unknown | unknown | **ok** (answer_verified T12) | **degenerate T45 `completion_ceiling`** |
| `rows-longrun-v5-tools.jsonl` | unknown | unknown | unknown | unknown (`answer_verified_false` at T12) | **degenerate T29 `completion_ceiling`** |
| `rows-longrun-v6-tools.jsonl` | unknown | unknown | unknown | **ok** | **ok** |

Read it plainly:

- **The reader was the bug, and it is fixed.** Tools-on files now reach definitive
  verdicts: v6 is `shape_ok` at N=12 and N=48 (no cap-length turn, contained fan-out,
  checkpoint verified at T12), and v4/v5 are `shape_degenerate` at N=48, named by turn
  and field (`finish_reason`).
- **N=5 is structurally blind for era B.** The first checkpoint is T12, so no tools-on file
  can have a verified answer at N=5; with no cap hit and no storm in the first five turns
  either, the honest verdict is `shape_unknown`. Era B's gate cannot be N=5 — it must be
  **N≥12**, which is why the era A control's N=5 story does not transfer.
- **The era A control is untouched**: still `shape_degenerate` at turn 3, still named
  `completion_ceiling` (4096/4096, `stop_reason: length`). The storm rule does not fire
  there — its turn rows carry `tool_calls: null` — so nothing about era A's outcome moved.
- `v5` at N=12 is the one genuinely uncomfortable cell: it is `shape_unknown` because its
  T12 checkpoint answer **failed** verification, one window before its own storm at T29.

## Launch order — one stage, not a habit

```
gates dry-run  ->  canary (N=5 per arm)  ->  tranche
```

1. **Gates dry-run** — `cell.py --dry-run` per arm: G1 ledger cap, G2 projection, G3 prereg.
   This proves the launch is *allowed*. It says nothing about whether the model behaves.
2. **Canary** — the first 5 turns of each arm's cell 1, live, one arm at a time. This proves
   the launch *measures*. `shape_ok` for all four arms is the gate to step 3; any
   `shape_degenerate` sends the arm back to a human-or-card decision (prompt, channel,
   `max_tokens`, thinking mode) **before** a tranche is armed. Any `shape_unknown` is a
   refusal to proceed, not a pass — re-run the canary or fix what made it unreadable.
3. **Tranche** — the real cells, `--turns 48`, multiple reps.

### Cost arithmetic

| | requests |
|---|---|
| canary, 4 arms × 5 turns | **20** (24 with each arm's 1-request warm-up) |
| tranche, 4 arms × 48 turns × reps 2–3, plus warm-ups | **≈720** |
| canary as a share of the tranche | **≈2.8 %** |

A degenerate canary saves the other ≈700 requests. The stopped cell's own numbers make the
point sharper: a canary that aborted at its **first** cap-length turn would have spent **3**
requests; the full N=5 window spends **5**; the cell that ran without one spent **28** and
returned nothing usable.

**The canary spends real requests and must be counted against the project ledger.** It is
not a dry run, it is not free, and 4 arms × 5 turns is not "a few free turns" — it is 20
requests against
[`experiments/ptr-engine/measure/REQUEST-LEDGER.json`](../experiments/ptr-engine/measure/REQUEST-LEDGER.json)
like any other cell. It also deserves the per-arm warm-up, because the warm-up is part of
the shape being tested (a cold prefix cache can itself produce a first-turn cap).

## Replay proof — zero requests

The classifier over the recorded, stopped cell
[`rows-cell-pointer-stable-20261026T182535Z.jsonl`](../experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl)
(27 rows, read-only):

```
$ python3 experiments/ptr-engine/tools/tranche_canary.py \
    --rows experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl --turns 5
shape_degenerate exit=1 arm=pointer-stable rep=1 n=5 turns=5 turn 3
  completion_tokens=4096 max_tokens=4096 wall_ms=114838.846 stop_reason=length
  (completion_ceiling) ...
$ echo $?
1
```

```
$ python3 experiments/ptr-engine/tools/tranche_canary.py \
    --rows experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl --turns 2
shape_unknown exit=2 arm=pointer-stable rep=1 n=2 turns=2 ...
  no completion ceiling was hit and every stop reason is in-vocabulary, but the arm's answer
  contract produced no parseable answer in the first 2 turns, so 'ok' is not demonstrated
$ echo $?
2
```

**Why N is not 2.** T1 and T2 are clean: 718 and 342 completion tokens, `stop`, no
truncation. The cap hit is at **T3**, one turn outside the window. A 2-turn canary
therefore cannot tell "healthy but early" from "about to break" — it returns
`shape_unknown`, and that is the honest answer: nothing in the first two turns refutes the
shape, and nothing in them confirms it. Lowering N to make the canary cheap converts its
signal into silence. N=5 reaches past the earliest observed cap (T3) with two turns of
margin, which is the smallest window that would have caught the known failure.

Note the second half of the honest reading: even at N=5 the window ends **before** the
first parseable answer of this arm (T6), so the canary's degeneracy verdict is driven by the
ceiling, not by the answer contract. That is why "no parseable answer in-window" is
`shape_unknown` rather than a fourth degeneration mode — the contract may simply fire later.

## What it may not do

- It **cannot change the shape.** It rewrites exactly one argv value — the `--turns` window
  — and refuses a launch whose `--reps` is not 1, because a multi-rep launch would multiply
  the requests it spends. Arm, fixture, channel, `max_tokens`, thinking mode and budget are
  passed through untouched, and the effective argv is recorded in the verdict.
- It does **not** replace the gates, the fixture checks, or the tranche's own measurements.
  It is a 5-turn smoke, not a miniature tranche: it cannot see treatments at T48, warm-up
  drift across reps, cumulative ledger growth, or anything that only appears after the
  window.
- It **reports.** Whether a `shape_degenerate` arm is re-launched with a changed prompt or
  channel is a human-or-card decision, recorded outside the canary.

## Reproduce

```bash
# offline replay (zero requests)
.venv/bin/python experiments/ptr-engine/tools/tranche_canary.py \
  --rows experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl \
  --turns 5 --json

# tests
.venv/bin/python -m pytest tests/test_tranche_canary.py -q     # 25 passed
```

## Change log

- **TRANCHE-CANARY** (2026-10-26): the tool and this document, 13 tests, era A replay.
- **CANARY-ERA-B-FIX** (2026-10-26): era B reader — stop-signal precedence (finish_reason
  / truncated / arithmetic fallbacks), per-shape answer contract (`answer_verified` for era
  B, `parseable_answers` unchanged for era A), and the measured tool-call storm rule
  (`STORM_MIN_CALLS = 110`). 25 tests. The rule the canary judges by was **not** changed —
  only what it can read. Era A's N=5 outcome is unchanged.
