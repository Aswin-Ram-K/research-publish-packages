# GATE-CHAIN — the only door to a live request

`experiments/ptr-engine/longrun/cell.py` is the conductor. Three offline cards built the
conditions under which a live cell may spend a request: **REQUEST-LEDGER** (the cap),
**PROJECTION-CALIBRATION** (the calibrated wall clock), and **PREREG-ARM-RUN** (PARM-1).
Each proved itself alone. This document describes the **join**: one entry point, one
refusal surface, three gates, all of them consulted before any request.

## 1. Where the gates sit

```
1  preflight     fixture gradable?                       exit 2
2  harness       freeze measurement-input digests        exit 2
3  budget        runner's own --dry-run + headroom       exit 3
3a G1 ledger     projected cost <= remaining quota       exit 4
3b G2 projection calibrated wall <= --max-wall           exit 8
3c G3 prereg     n supports the claim it will state      exit 12
   manifest      verdicts + artefact sha256 written      (cell-<arm>-<stamp>.gates.json)
4  run           run_longrun.py (gate inside, pass-through) exit 4 / 5 / 6 / 7 / 9 (the cap-gate 9 arrives as 14)
5  grade         grade_v5.py                             exit 10
6  analyse       analyze_stats.py (number or refusal)    exit 11
6b consistency   grader vs analyser population           exit 9
7  record        JSON + markdown                         —
```

The chain runs **after** the budget stage so a budget refusal (3) is never preempted by
G2 (8), and **before** `stage_run`, so no live path reaches `client.chat()` without a
recorded verdict from all three gates. `--offline` sends no request and therefore
consults no gate; the cell record says so explicitly (`gates.skipped = true` with a
reason) rather than leaving the field absent.

## 2. Final exit-code table (pinned, distinct, honoured)

| code | meaning | owner |
|---|---|---|
| 0 | cell completed; gate verdicts recorded | cell |
| 2 | preflight / harness refusal, unreadable gate artefact (**not** G3 — see `12`) | cell |
| 3 | budget refusal | cell |
| 4 | **the ledger's cap refusal** — G1, and the ledger's own `EXIT_OVER` propagated from the runner | `tools/request_ledger.py` |
| 5 | runner crash | `run_longrun.py` |
| 6 | runaway-turn abort (`--runaway-turns` / turn-wall cap) | `run_longrun.py` |
| 7 | record refusal (runner could not write rows) | `run_longrun.py` / cell |
| 8 | **projection refusal** — G2 | `docs/PROJECTION-CALIBRATION.md` |
| 9 | grader/analyser population disagreement (`--allow-inconsistent` overrides) | cell |
| 14 | `capgate-unrecorded` — cap-gate refusal at **cell** level: the runner's reconcile found unrecorded spend (`delta < 0`) or a row no request bought (`delta > 0`). The runner still exits 9; the cell reports 14 so a refusal is never read as a crash | cell |
| 10 | grade refusal | cell |
| 11 | analyse refusal | cell |
| 12 | **prereg refusal** — G3: the cell's n cannot support its claim, or it declared none | cell |

**One renumber, stated rather than smuggled.** Codes 5 and 6 were previously *grade*
and *analyse*; `run_longrun.py` already returns 5 for a crash and 6 for a runaway abort,
and collapsing them into one code made a runaway indistinguishable from a crash. Grade
and analyse now use 10 and 11, so every code in the table means exactly one thing. The
table is printed in the module docstring.

## 3. G1 — the ledger's cap, counted by the ledger

- Cost of the cell: `turns × arms × reps` **plus the fetch follow-up allowance**.
  `arms` is the comma-separated `--arm` list. The allowance is
  `ceil(turns×arms×reps × 68/801)` (`FETCH_FOLLOWUP_RATIO`), measured from the corpus the
  ledger bundled: **68 rows of kind `tool-followup` against 801 rows of kind `turn`**.
  The ledger bills a follow-up (docs/REQUEST-LEDGER.md rule 2), so G1 budgets for it;
  `--fetch-followup-allowance N` overrides the measurement.
- The decision is taken by `request_ledger.build_report(paths, cap, reserve, would_spend)`
  over the very row files `experiments/ptr-engine/measure/REQUEST-LEDGER.json` lists, with
  that artefact's own `cap`/`reserve`. There is no second accounting: a refusal reuses the
  ledger's `EXIT_OVER` (**4**).
- An artefact that is missing, unparseable or has no `budget.cap` → **refuse** (exit 2).
  A gate that cannot read its limit must never allow.

## 4. G2 — the calibrated projection

- Consumes `experiments/ptr-engine/measure/PROJECTION.json`: the per-turn wall is the
  artefact's `defaults.projected_turn_wall_s` (60) unless `--projected-turn-wall` or a
  `--projected-from <rows.jsonl>` p90 replaces it. `--turn-wall-cap` (180 s) is printed
  as the worst case and remains the live abort the runner enforces — G2 does not touch it.
- Refusal keeps **exit 8** and quotes both second counts, e.g.
  `computed 8640 s | limit 3600 s (--max-wall)`.
- A **non-positive** `--max-wall` is a refusal, not a disable switch (GATE-CHAIN-FIX D1).
  `--max-wall 0` and `--max-wall -1` both exit **8**, name the value, and say that a
  ceiling of zero or less is not "unlimited". Neither this document nor the flag's help
  text declares an unlimited mode, so there is none; the old verdict
  `ok = not (max_wall > 0 and projected > max_wall)` allowed both.

## 5. G3 — the prereg (PARM-1) claim

- `n = turns × reps` (usable timings per arm).
- **H1** (p95 TTFT): admissible only at `n ≥ analyze_stats.min_n_for(0.95)` = **60**. The
  minimum is imported from the estimator, not copied; a fallback constant of 60 is used
  only if the module cannot be imported.
- **H2** (per-turn prompt work, PARM-1 primary): `n ≥ 1` — a per-turn ratio needs one
  completed turn per arm. The materiality margin (5 % on `prompt_tokens` AND < 1.00× on
  uncached) is recorded in the verdict, not invented.
- **H3** (quality): unadjudicable below 8 decidable of 12 checkpoints, so a fixture
  carrying fewer than 8 checkpoints is refused.
- A cell that declares **no hypothesis** is refused with **exit 12** (G3's own code,
  separate from preflight's 2): silence is not a claim you may spend on. An ABSENT
  `--hypothesis` is read as `none` and refused — there is **no** default. Before
  GATE-CHAIN-FIX the absent flag fell back to PARM-1's `primary` (H2), so the run was
  allowed and the no-hypothesis branch was unreachable from the CLI; that is why
  WIRE-GATES's contract claim 6 ("G3 refuses a run that declares no hypothesis") read as
  true while it was false. `--hypothesis none` and an unknown name are refused the same
  way. Two other cards' test files were edited to name a claim they can honestly make
  (`experiments/ptr-engine/longrun/tests/test_projection_calibration.py` checks a/c at n=48/10 and `experiments/ptr-engine/longrun/tests/test_guards.py`
  (d) now pass `--hypothesis H2`); `test_guards.py`'s old `--max-wall 0` "disabled" red is
  replaced by a source mutation, because a non-positive ceiling is now itself a refusal.
- Every live run records **which hypothesis it will claim and under which thresholds**
  (`record["hypothesis"]`, the manifest, and the markdown record).

## 6. One refusal format

```
<GATE> <name> REFUSED: computed <value> | limit <value> | artefact <path> (sha256 <digest>)
  | to change this decision pass <the exact flag> | <consequence, with the shortfall>
```

Example (G1, near the cap):

```
G1 ledger-cap REFUSED: computed 153 requests | limit 120 requests (cap 120 - reserve 0 -
spent 100) | artefact .../ledger.json (sha256 d93e…) | to change this decision pass
--turns / --reps / --fetch-followup-allowance (or a larger cap in the ledger) | this cell
would need 53 requests (would_spend: 48 turn(s) x 1 arm(s) x 1 rep(s) = 48 requests, plus
a 5-request fetch follow-up allowance) on top of the 100 requests already spent, taking
cumulative spend (projected) to 153 requests against a limit of 120 requests (cap 120 -
reserve 0): shortfall 33 requests, so it must not send
```

Every refusal names the gate, the computed value, the limit, the artefact it came from,
and the flag that would change the answer.

### 6a. One sentence FAMILY per verdict, chosen by `ok` (GATES-MESSAGE-CONSISTENCY)

A verdict's `consequence` is either the **allow** family or the **refuse** family, picked
by that verdict's own `ok` — never by which computation happened to run. Before this
card, G1 (`cell.py` `eval_gate_ledger`) and G2 (`cell.py` `eval_gate_projection`) each
emitted ONE sentence unconditionally, so the recorded artefact
`experiments/ptr-engine/measure/cell-pointer-stable-20261026T182535Z-p4-001.gates.json`
carries three `ok: true` verdicts and two sentences that read as failures:

- G1 — allow: *"this cell needs 1,154 requests … but only 4,320 remain: shortfall -3,166
  requests"*. `projected` (1,154) is the **cumulative spend after this cell**
  (`spent` 1,101 + `would_spend` 53), 4,320 is the **cap** (the limit is cap − reserve),
  and 3,166 is what **remains after** the cell. `would_spend` is the cell's OWN requests;
  the fetch follow-up figure is an allowance, `ceil(turns × 68/801)` unless
  `--fetch-followup-allowance` overrides it.
- G2 — allow: *"exceeds the allowed 2880s"* on a verdict admitted exactly AT the boundary
  (`V-GATE-CHAIN-2`: allow 2,880, refuse 2,881), and *"48 request(s)"* where the cell has
  48 **turns**. The allow family now says "within … by N s of slack" and names turns as
  turns and requests (the runner's would-send count) as requests.

The decision, the thresholds, the exit codes and the values of `computed`/`limit`/`ok` are
untouched by the message fix; `experiments/ptr-engine/longrun/tests/test_gate_messages.py`
asserts the sentences, the G2 boundary pair (2,880 allow / 2,881 refuse) and that all
three `artefact_sha256` digests still match the artefacts they pin.

**Recorded defect, not fixed here.** G1's `limit` string still renders
`<headroom> requests (cap X - reserve Y - spent Z)`, where `<headroom>` is `cap - reserve`
and therefore does not equal `X - Y - Z`. The consequence now states the limit correctly;
changing the `limit` VALUE is out of this card's scope and belongs to its own card.

## 7. `--dry-run` prints the decision, not a promise

```
cell: 0/7 dry-run G1 1,167/4,320 requests · G2 3,600 s of 3,600 s · G3 n=60 ≥ 1
cell: 0/7 dry-run would cost: turns=60 arms=1 reps=1 -> 60 requests (incl. follow-up
      allowance 6), ~3600 s projected wall; 0 requests sent, no endpoint contacted
cell: EXIT 0 — dry run: 0 of 3 gate(s) would refuse; nothing was sent
```

A dry run spawns no runner, opens no socket and exits 0 even when a gate **would**
refuse — the verdict line then reads `WOULD-REFUSE` instead of `allow`. It is a preview
of the decision, not an authorisation.

**The divergence is the contract, not a bug (GATE-OVERRIDE-FIX F3).** `--dry-run` exits
**0** whenever the preview itself ran, even when every gate would refuse: a dry run
authorises nothing, so its exit code is not a decision about the cell, and making it
non-zero would collide with the live refusal codes (0/2/3/4/5/6/7/8/9/10/11/12/14) that
callers already read. Therefore **callers MUST parse** the printed decision — the
`WOULD-REFUSE` verdict lines, or the final `N of 3 gate(s) would refuse` count — and MUST
NOT treat exit 0 from `--dry-run` as "the gates allow". The final line says so in the
same words:

```
cell: EXIT 0 — dry run: N of 3 gate(s) would refuse; exit 0 means the PREVIEW ran, not
      that the gates allow: callers MUST parse this line or the WOULD-REFUSE verdict
      lines, never the exit code; nothing was sent
```

`experiments/ptr-engine/longrun/tests/test_gate_override.py::
test_d_dry_run_contract_matches_the_document` asserts both halves — the code's exit 0 and
this paragraph's sentence — so the two cannot drift apart.

## 8. The manifest (a gate that leaves no trace cannot be audited)

`cell-<arm>-<stamp>-p<pid>-<serial>.gates.json` is written **before** the runner is
invoked, so the limits a run passed under survive a later crash:

```json
{"unit":"WIRE-GATES","arm":…,"stamp":…,"hypothesis":{"name":"H2","source":"default:PARM-1.primary",…},
 "verdicts":[{"gate":"G1","ok":true,"computed":"153 requests","limit":"4,320 requests (…)",
              "artefact":"…/REQUEST-LEDGER.json","artefact_sha256":"…"}, …],
 "artefact_digests":{"…/REQUEST-LEDGER.json":"…","…/PROJECTION.json":"…","…/PREREG-ARM-RUN.json":"…"}}
```

**A manifest name is unique per run (GATE-OVERRIDE-FIX F2).** The name used to be
`cell-<arm>-<stamp>.gates.json` with a second-resolution stamp, while the default
`--out-dir` is the repo's `measure/` directory — two cells started in the same second
therefore wrote ONE file and the second run silently replaced the first run's gate
verdicts (observed as transient rc=1/rc=0 during a live-path probe). The name now carries
the pid and a per-process serial, and `write_gate_manifest` creates the file with `O_EXCL`
and advances the serial on collision, so no run can overwrite another run's verdicts. The
verdicts and digests recorded are still exactly the ones that were consulted: the payload
is built from the same `gates` list the runner was gated on, before the runner starts.

The same verdicts and digests are embedded in the cell record (`record["gates"]`) and in
the markdown record's `## gate chain` section.

## 9. Tests

`experiments/ptr-engine/longrun/tests/test_cell_gates.py` — 15 tests, all offline:

| gate | allow | refuse |
|---|---|---|
| G1 | headroom → runner reached | ledger 120/100 spent → exit 4, names the 33-request shortfall |
| G2 | 48×60 s = 2880 ≤ 3600 → runner reached | 48×180 s = 8640 > 3600 → exit 8, quotes both counts; `--max-wall 0` and `--max-wall -1` → exit 8, names the value, says there is no unlimited mode; `--projected-turn-wall 0` and `-1` → exit 8, zero runner spawns; a `--projected-from` file whose p90 ≤ 0 s → exit 8 (never a silent fallback) |
| G3 | H1 at n=60 and n=144 → runner reached | absent `--hypothesis` → exit 12; `--hypothesis none` → exit 12; unknown name → exit 12; H1 at n=48 → exit 12, names 60 |
| import | `cell.py --help` from the **repo root** with PYTHONPATH scrubbed → exit 0 | — (the red is a bare `import exit_codes`, which the D4 demonstration re-adds: `ModuleNotFoundError`) |
| dry run | 0 sockets / 0 subprocesses (transport tripwire), three verdict lines | — |

Red→green (in-place mutation of `cell.py`, restored byte-identically and asserted so):

```
RED G1: expected exit 4 (the ledger's cap refusal), got 10
RED G2: expected exit 8 (projection refusal), got 10
RED G2-max-wall: expected exit 8 for --max-wall 0 (a ceiling of zero or less is not
  'unlimited'), got 10
RED G2-max-wall-negative: expected exit 8 for --max-wall -1 (a ceiling of zero or less
  is not 'unlimited'), got 10
RED G3: expected exit 12 (prereg refusal), got 10
RED G3-silence: expected exit 12 (no hypothesis declared), got 10
RED G3-code: expected exit 12 (prereg refusal), got 2
```

Exit 10 is the grade refusal, reached only because the runner ran — i.e. the neutered gate
let the cell through. A red for any *other* reason fails the test, so a broken path cannot
masquerade as a demonstration.

Neighbouring suites, re-run unchanged: `test_cell.py` 7/7, `test_projection_calibration.py`
4/4, `test_guards.py` 6/6 GREEN.

`experiments/ptr-engine/longrun/tests/test_gate_override.py` — 7 tests, all offline, all
sentenced against the attack's fifth bypass:

| case | allow | refuse |
|---|---|---|
| (a) per-turn override | 2×5 s = 10 s == `--max-wall 10` → runner reached | `--projected-turn-wall -1` / `0` with `--max-wall 1` → exit 8, zero runner spawns, five facts present |
| (b) `--projected-from` rows | ten 10 s walls, 2 turns → runner reached | a rows file whose walls all price ≤ 0 s → exit 8, names the p90, no fallback |
| (c) manifest name | two writes with the same stamp → two paths, two verdict sets | — (the red is the shared second-resolution name) |
| (d) dry-run contract | exit 0 + `callers MUST parse` in the line and in §7 of this document | — |

Red→green for the three new guards (mutation of `cell.py`, restored byte-identically and
asserted so):

```
RED a-override-negative: expected exit 8 for --projected-turn-wall -1 (a per-turn wall of
  zero or less is not 'unlimited'), got 10
RED b-rows-priced-zero: expected exit 8 for a row file that prices at <= 0 s, got 2
RED c-manifest-unique: two runs in one second share a manifest path: …/cell-transcript-grow-20260101T000000Z.gates.json
RED d-dry-run-contract: the dry-run line no longer tells the caller it must parse it
```

## 10. What was not done

- The runner's **per-turn** ledger call (the `WIRE-CAP-GATE` half) is not wired here; G1 is
  a preflight decision on the cell's projected cost. `experiments/ptr-engine/longrun/tests/test_request_ledger.py` and the
  REQUEST-LEDGER handoff own that remainder.
- No guard was weakened: exit 8, the 180 s live turn cap, `--runaway-turns` and the
  ledger's own counting are consumed exactly as their cards left them.

## The claim: `smoke` runs and why they can never be compared (WIRE-CLAIM-MODE)

G3 does not ask "did you name a hypothesis". It asks **"what claim is this run making?"**
and there are four answers, resolved in exactly ONE place —
`claim_mode.resolve_claim` (`experiments/ptr-engine/longrun/claim_mode.py`), called once
per invocation by `cell._resolved_claim`
(`experiments/ptr-engine/longrun/cell.py:1202-1226`). The inline parse
(`_declared_hypothesis`) is **deleted**; a second parser is a defect even when it agrees.

| `--hypothesis` | record | G3 | exit |
|---|---|---|---|
| `smoke` / `plumbing` | `claim="none"`, `comparison_eligible=false`, `mode="smoke"` | **allowed** — no PARM-1 threshold applies, and `--turns`/`--reps` operands are STILL validated | 0 |
| `H1` / `H2` / `H3` | `claim="H#"`, `comparison_eligible=true` | allowed only when the cell's own `n` supports it (H1 n>=60 (analyze_stats.py:111-112 TAIL_MIN=3, MIN_N=20 -> min_n_for(0.95)=60), H2 n>=1, H3 >=8/12 checkpoints) | 0 / 12 |
| absent / `""` / whitespace | `ClaimRefusal` | **refused**, message verbatim from `claim_mode.refusal_message` | **12** |
| `none` / any unknown spelling | `ClaimRefusal` | **refused** (same class, same stage, same text) | **12** |

Exit 12 is `EXIT_PREREG`, stage `3c/7 G3 prereg gate` — unchanged by the wiring: the
module *builds* that abort (`claim_mode.as_abort`), it does not invent a code.

**What stops a smoke cell from looking comparable downstream.** Two mechanisms, both
in the data rather than in a reviewer's memory:

1. the run stage writes the resolved claim beside the rows
   (`rows-cell-<arm>-<stamp>.jsonl.claim.json`, `cell.py` `stage_run`) and records it in
   the cell record (`run.claim`, `hypothesis.claim`) and the gate manifest;
2. `analyze_stats.require_comparable_claim` refuses a `claim="none"` cell **by name** —
   `incomparable_claim` — whether the rows carry the field themselves or the sidecar
   declares it. It is a refusal in the report (`refused_kind: "incomparable_claim"`,
   one record per refused comparison), never a silent filter: a grouped-by-arm average
   that quietly drops a smoke arm is the defect this exists to prevent.

**The honesty limit.** The wiring makes a claim-free run *possible*; it does not make it
*comparable*. A smoke cell's rows are never pooled with H1/H2/H3 rows: the analyser
refuses the comparison and reports the smoke cell's numbers on their own. Per-row `claim`/`comparison_eligible` fields are now written by the runner
(`run_longrun.py`, CLAIM-ROW-STAMP): every turn-initial, turn, tool-followup
and failure row carries them, resolved once from `--claim-mode`. A rows file
with NEITHER field is LEGACY (written before this mechanism), never a
claim-free one; a half-landed file (one of the two fields) is refused as
`claim_fields_incomplete`.

## Claim stamp on every per-turn row (CLAIM-ROW-STAMP)

`run_longrun.py` now takes `--claim-mode` with `claim_mode`'s own vocabulary (`smoke`,
`plumbing`, `H1`, `H2`, `H3`). The flag is resolved ONCE — `claim_mode.resolve_claim`,
in `main()` before the first row is written — and the resolved record is threaded on
`cfg.claim`; `make_row` stamps `claim` and `comparison_eligible` beside `"arm"` on every
row literal it builds (turn-initial, turn, tool-followup, refusal and failure rows).
There is no second parser: `cell.py` already resolved the decision and passes it to the
runner as `--claim-mode`, so a cell has ONE claim across its gate verdict, sidecar and
rows.

| declared | rows carry | comparison |
|---|---|---|
| `--claim-mode smoke` / `plumbing` | `claim="none"`, `comparison_eligible=false` | never comparable |
| `--claim-mode H1` / `H2` / `H3` | `claim="H#"`, `comparison_eligible=true` | comparable |
| omitted, corpus-shaped `--rows` | no row written | refused **exit 12**, `claim_mode.refusal_message` verbatim |
| omitted, `--rows` under the OS temp dir | `claim="none"`, `comparison_eligible=false`, warning on stderr | never comparable |

**What a downstream reader loses if the stamp is absent.** `LATENCY-REPORT`, `TVS` and
`analyze_stats` group by arm: a claim-free smoke row and a comparable row in the same arm
would be averaged together, and the resulting number would carry a claim the smoke cell
never made — with no field in the data to notice it. The guard is
`claim_mode.assert_comparable` reached through
`analyze_stats.require_comparable_claim`: any row declaring `claim="none"` (or
contradicting its own claim, or carrying only one of the two fields) raises
`IncomparableClaim` starting `incomparable_claim`, naming the offending cell; the report
records the refusal instead of a number. Pooling returns only if the stamp disappears
from the rows (then the row is either LEGACY or refused as incomplete) or if a comparison
path reads rows without passing them through `assert_comparable` — which is why the
analyser refuses rows it cannot qualify rather than filtering them.

## 11. Spawn classification — a diagnostic spawn is not a runner launch

V-GATE-REPIN recorded `not_reproduced` against the literal rule "`popen_calls == 0` on
every refusal": a refusing invocation makes exactly **one** raw Popen call, because stage
3/7 asks the RUNNER's own `run_longrun.py --dry-run` what the cell would send *before* any
gate is evaluated. That is a **diagnostic self-check**, not a live runner, and no
implementation could satisfy "zero spawns" while keeping it. The rule was wrong; the fix
is not to stop counting, but to count **by purpose**.

Every `subprocess` a cell makes is now recorded in `spawn_record.SpawnRecord` as
`{seq, pid, pid_argv, argv, purpose, phase, gate_record, label, declared, at}` with
`purpose ∈ {preflight_self_check, runner_launch, other}` and `phase` the pipeline stage
(`3/7 budget`, `4/7 run`, …). The record is published in the refusal's own document
(`cell-<arm>-<stamp>.refusal.json`: `spawns`, `counts`, `validation`) and in the completed
cell record (`spawns`). The runner launch is the only spawn carrying a `gate_record`, the
gate manifest it ran under.

**The rule that replaces the unsatisfiable one, in one sentence:**

> A refusing invocation must have zero `runner_launch` spawns; any
> `preflight_self_check` spawn must be declared in the same record with its phase; an
> undeclared spawn (`purpose == other`, or a launch with no gate record) is a failure.

The self-check **stayed a spawn** rather than going in-process: it invokes the runner's
own `--dry-run` path (argv parsing, fixture validation, Planner previews written under
`/tmp/longrun-previews/`), and importing that into the gate process would change what is
being measured. Keeping it and naming it is the honest option; the launch — the thing that
can spend a request — remains forbidden on every refusal.

`experiments/ptr-engine/longrun/tests/test_spawn_classification.py` holds the rule to an
**independent oracle**: a `sitecustomize` tripwire subclasses `subprocess.Popen` inside the
child and logs every construction, so a record cannot pass by declaring nothing. Measured
over exit codes `{2,3,4,8,12}`: `runner_launch == 0` everywhere, declared spawns equal
observed Popen calls (0 at exit 2, 1 at 3/4/8/12, always `preflight_self_check` at
`3/7 budget`), and a `/tmp` mutant that spawns without recording fails with
`undeclared spawn: the oracle counted 2 real subprocess.Popen call(s) but the refusal
record declares 1`. The record for that run is
`experiments/ptr-engine/measure/PREFLIGHT-SPAWN-DECLARE.json`.

### §11 addendum — the validator must be able to say NO (SPAWN-VALIDATOR-FIX)

`spawn_record.validate_refusal()` **recomputes**; it does not read a verdict back. The
`spawns` entries are the instrumentation: their per-purpose counts are recomputed and
compared with every DECLARED count (`counts`, `runner_launch`, `preflight_self_check`), and
when a `sitecustomize` tripwire is mounted (`SPAWN_ORACLE_LOG`), `cell.py` passes the raw
`subprocess.Popen` count as `observed`. A disagreement of even 1 is a rejection, and the
message names the pair and the exit code (`counts[preflight_self_check]: declared 1 vs
recomputed 0 at exit 4`). A self-reported `validation.ok: true` is never trusted: if the
recomputation disagrees, the self-report is itself a failure.

Rejected, each naming the offending part:

1. no `spawns` key at all — an empty/truncated record is not proof;
2. `spawns: []` **and** no declaration block (`counts` + rule text) — an empty claim;
3. a declaration block that declares preflight spawns but names no phase (or an unknown
   phase);
4. declared counts that disagree with the recomputed counts by ≥1, per purpose and exit;
5. a `runner_launch` entry published for a refusal exit code in `{2, 3, 4, 8, 12}`.

Green case: the real exit-4 refusal record still validates with `observed == 1`. Measured
on `cell.py` sha `b549e45e…`: `test_spawn_classification.py` 10 passed;
`test_cell_gates` + `test_gate_override` + `test_exit_codes` 52 passed (21 subtests).
CLI: `python3 experiments/ptr-engine/longrun/spawn_record.py --validate FILE --exit-code N
[--observed N]` exits 0 only when the record survives recomputation, 1 when it does not.

### §11 addendum — record bindings D2/D3/D4 (SPAWN-RECORD-BIND)

`V-SPAWN-ATTACK-2` attacked the validator with its own syscall oracle (`strace -f -e
trace=execve`) instead of the record's `Popen` subclass. It measured **real spawns
0/1/1/1/1 at exits {2,3,4,8,12}** on `cell.py` sha `b549e45e…`, every child being
`/usr/bin/python3 <runner> --dry-run` (the pre-flight self-check), and
**`runner_launch == 0` at all five refusals** — the *property* holds. The *certificate*
did not: three record defects let a record pass while claiming less than the property.

**D2 — coverage was never checked. FIXED.** A record whose `per_exit_code` named only
exits `0` and `7` validated OK, and single-exit coverage was also accepted, so "every
refusal is declared" was a claim about the record's shape, not about the refusal set.
`validate_refusal` now judges the coverage of any **aggregate** record (`per_exit_code`
or `covered_exits`) against `REFUSAL_EXITS = {2,3,4,8,12}` and names what is missing:
`missing refusal coverage: 2,3,4,8,12`. `--required-exits 2,4` is the explicit override a
caller must pass to narrow the set on purpose. A **single-invocation** record describes
exactly one exit and is *not* evidence of coverage — that is the point, not an exemption:
coverage is a property of the record SET, so an aggregate record is what carries it.

**D3 — duplicate JSON keys could rewrite a declaration. FIXED.** `json.loads` is
last-wins, so a `counts` object saying `runner_launch: 9` and then `runner_launch: 0`
declared 0 — a declaration rewritable by **key order**. The loader is now
`strict_load`/`strict_loads` (`object_pairs_hook`), which refuses by name:
`duplicate key 'counts.runner_launch' at record.counts`, **exit 1** (a duplicated key is a
refusal, not a read error), at any depth including the root.

**D4 — the instrumentation covered `subprocess.Popen` only, and said so nowhere. FIXED.**
`cell.py` spawns only through `subprocess.run` (`cell.py:207` `_run`, `cell.py:1548`
runner launch), but the *validator's* oracle is a `Popen` subclass, so an
`os.system('/bin/true')` wrapper during an exit-2 refusal yielded 2 `execve` in strace and
0 declared, validator OK. The scope is now **declared and enforced**: every record
carries `instrumentation = {primitive, covers, excludes}` (emitted by
`SpawnRecord.as_dict()`), and `validate_refusal` **rejects a record that omits it** or
half-declares it (`primitive`, `covers` non-empty, `excludes` list).

**The claim, narrowed to exactly what was measured:**

> a refusing invocation must have zero `runner_launch` spawns for `subprocess`-shaped
> spawns at every exit in {2,3,4,8,12}; spawns outside the declared instrumentation are
> outside this guarantee and must be measured with a syscall-level oracle (strace/execve)
> when the claim matters.

**The syscall-level oracle.** `--observed-from-syscall TRACE` compares **counts and argv**
against the record, so the strongest check does not depend on a `Popen` subclass:

```
strace -f -s 4096 -e trace=execve -o /tmp/srb/trace.txt \
    python3 experiments/ptr-engine/longrun/cell.py <refusal argv>
python3 experiments/ptr-engine/longrun/spawn_record.py \
    --validate /tmp/srb/refusal.json --exit-code 4 \
    --observed-from-syscall /tmp/srb/trace.txt
```

`-f` follows children, `-s 4096` keeps long argv untruncated, `-e trace=execve` keeps only
execve so the count cannot be padded. The trace's **first** execve is the traced process
itself (`cell.py`) and is excluded; every later execve must be named by the record. A JSON
trace (`[{"pid": 1, "argv": ["/usr/bin/python3", "runner.py", "--dry-run"]}]`) lists
spawns only. A trace whose execve count exceeds the declaration is **exit 1** naming the
execve the record does not declare — which is how D4's `os.system` blind spot becomes
measurable.

Measured on `cell.py` sha `b549e45e…` (unchanged before and after):
`test_spawn_classification.py` **18 passed** (the original 10 kept, 8 new), and each guard
was reverted in place to show its own test fail with its own message
(`a record covering only exits 0/7 validated OK` / `a duplicated key validated OK
(last-wins rewrite)` / `spawn_record: OK` for a record with no `instrumentation`), then
restored byte-identically.

### Known gap D5 — the record is not tree-bound

`validate_refusal` takes **no tree identity**: nothing binds a record to the tree it
describes, and `cell.py` writes no sha into it. Reproduction, exactly as measured:

> same argv; one gate made permissive in a `/tmp` copy of the tree; the invocation moves
> exit `4 → exit 12`; the **historical exit-4 record still validates OK**.

Consequence: *a validator cannot tell whether the tree it is judging is the tree the
record describes; until D5 is closed, a record must be regenerated in the same session as
the run it certifies.*

D5 is **recorded, not fixed** here: the fix needs a tree identity written by `cell.py`,
which is pinned by `TRANCH1-DRYRUN` (`07bd683a`), and a moved `cell.py` would make that
rehearsal `unstamped`. Do **not** read this section as D5 closed.

### Known gap D6 — the on-disk refusal document drops `instrumentation`

Found while closing D4. `cell.py`'s refusal writer publishes a **fixed key list**
(`spawns`, `counts`, `classification`, `observed`, `validation`) and therefore drops the
top-level `instrumentation` block that `SpawnRecord.as_dict()` emits, so an on-disk
`cell-<arm>-<stamp>.refusal.json` fails the D4 check while the **in-process** verdict
(computed on `as_dict()`) passes. The declaration is a property of the *recorder*, not of
the run, so it is recoverable without re-running anything:
`spawn_record.complete_refusal_document(doc)` restores it before external validation (the
green test uses exactly that, against the real record's untouched `spawns`/`counts`). The
proper fix — writing `instrumentation` (and, with D5, the tree sha) from `cell.py` — is
out of scope while `cell.py` is pinned by `TRANCH1-DRYRUN`.

### D5 CLOSED — the record IS tree-bound (`SPAWN-TREE-BIND`)

The gap text above is kept verbatim as the record of what was open. It is now closed by
`SPAWN-TREE-BIND`: the precondition held (`TRANCH1-DRYRUN` settled, `cell.py` sha
`b549e45e…` before and after that unit), so `cell.py` was edited — now sha `e24e867b…`,
with `spawn_record.py` at `eba15471…`.

The reproduction above now **fails**. Measured: the permissive-G1 `/tmp` tree moves the
same argv from exit `4 → 12`, and the **historical exit-4 record** is refused with
**exit 1**, naming both shas and the field:

```
spawn_record: FAIL: tree binding mismatch (D5): record cell_sha256=b549e45e… but
<perm>/cell.py=<permissive sha> (cell_sha256): this record certifies only the tree whose
shas it carries -- regenerate it with the cell.py under test
```

The refusal record now carries four binding keys, written by `SpawnRecord.as_dict()` (one
record shape, so a writer cannot publish spawns without a tree):

| key | value |
| --- | --- |
| `cell_sha256` | sha256 of the `cell.py` that produced the record |
| `spawn_record_sha256` | sha256 of `spawn_record.py` |
| `argv` | the exact process argv |
| `tree_sha` | the tree's HEAD commit, or the literal `unstamped` |

`validate_refusal` **requires** all four, and holds the two shas against the files named
by `--cell-path` / `--spawn-record-path` (both defaulting to the on-disk pair). A record
with none of them is refused with `no tree binding (D5): record names neither
cell_sha256 nor spawn_record_sha256`; one key stripped empty is refused by name, so
narrowing the binding is not a bypass. `tree_sha` is read from `.git/HEAD` → `refs` →
`packed-refs` **as files**: a recorder that spawned `git` would appear in its own ledger —
and in any syscall oracle — as an undeclared spawn. A tree with no commit says
`unstamped`; it is never empty and never a fabricated sha.

**A record certifies only the tree whose shas it carries.**

### D6 CLOSED — the on-disk refusal carries what the validator demands

`cell.py`'s refusal writer no longer publishes a fixed key list. It starts from
`SpawnRecord.as_dict()` (spawns, counts, `instrumentation`, the D5 binding) and adds the
refusal's own facts, so an on-disk `cell-<arm>-<stamp>.refusal.json` passes
`validate_refusal` **without** a repair helper in between.
`complete_refusal_document()` is retained for documents written before the fix and
deliberately invents no tree binding: a missing binding is a refusal, not something a
helper may paper over.

Measured: `experiments/ptr-engine/longrun/tests/test_spawn_tree_binding.py` **5 passed** (D5 matching / stripped-keys /
historical-vs-permissive / unstamped, D6 document shape) together with
`experiments/ptr-engine/longrun/tests/test_spawn_classification.py` **18 passed** — the D2/D3/D4 tests unmodified. Each
guard was reverted in place to show its own test fail (D5 guard removed → `the historical
record certified a tree it does not describe (exit 0)` and `a record naming no tree
validated OK`; writer reverted to the fixed key list → `the on-disk refusal dropped
instrumentation (D6)` and `the record does not name the cell.py that wrote it`), then
restored byte-identically.


## 9. UNRECORDED-REFUSE — a short ledger refuses instead of narrating

The cap gate reserves each slot before the send (`projected = spent_at_start +
used_in_run + 1`, refuse when `projected > headroom` — exit 4, nothing sent) and
reconciles after the run: `delta = spent_after - (spent_at_start + used_in_run)`.

Before this card, `delta < 0` — requests that reached the wire whose rows were never
persisted — printed `CAP GATE UNRECORDED` and **returned 0**. That is the unsafe
direction: the ledger under-states the bill, so the next check sees more headroom than
exists and a run can walk past the gate by dropping a row.

Now `delta < 0` **refuses with exit 9** (the existing divergence code; no new code was
added), printing the five facts `delta`, `used_in_run`, the missing request count,
`headroom_before`/`headroom_after`, and the rows file path, plus the sentence a caller
needs: *rows were not persisted, so the ledger cannot be trusted for the next check*.
The safe branches are untouched: `delta == 0` is exit 0, `delta > 0` is
`CAP GATE RECONCILE DIVERGENCE` exit 9, and the pre-send refusal is still exit 4 with
zero rows and zero transport calls.

Measured in `experiments/ptr-engine/longrun/tests/test_cap_gate.py` — 13 passed, exit 0, zero requests:

| test | guard | red (guard reverted) | green |
|---|---|---|---|
| `test_unrecorded_spend_refuses` | dropped row → `delta < 0` | `0 != 9` | exit 9, `CAP GATE UNRECORDED` |
| `test_reconciled_run_still_succeeds` | `delta == 0` | `7 != 0` | exit 0, `cap-gate: reconciled` |
| `test_positive_delta_still_diverges` | `delta > 0` | `0 != 9` | exit 9, `RECONCILE DIVERGENCE` |
| `test_presend_refusal_unchanged` | `projected > headroom` | `0 != 4` (brake disabled) | exit 4, 0 rows, 0 calls |

**Can a run now start while its ledger disagrees with the wire? No.** A run whose rows
gained less than the requests it acquired ends at exit 9, and the conductor propagates
that status unmodified (`cell.py` exit-code map).

## G2-BOUND-PRICE — the projection printed term by term, beside its bound

**Superseded shape (kept, so the old records stay readable).** One pooled number, the
worst case in parentheses, no term for the fetch follow-up allowance G1 already bills:

```
cell: 3b/7 projection turns=48 projected_requests=48 projected_wall~=2880s
(cap-per-turn 180s -> worst case 8640s) cap=3600s projected-turn-wall=60.0s
source=artefact-mode thinking=absent
```

**New shape (2026-10-26, G2-BOUND-PRICE).** An addition whose every term names its
source, the fitted estimate G2 compares, the all-in estimate G1 reserves, and — last —
the bound that is true by construction:

```
cell: 3b/7 projection PRICE fitted estimate 2880 s = turns 48 x 60.0 s/turn [source experiments/ptr-engine/measure/PROJECTION.json:defaults.projected_turn_wall_s_by_mode['absent']] = 2880 s + runner-priced extras 0 x 60.0 s/turn [source runner --dry-run would_send_total 48 - turns x reps 48] = 0 s; fetch follow-up allowance ceil(48 x 68/801) = 5 x 60.0 s/turn [source FETCH_FOLLOWUP_RATIO in cell.py, reserved by G1] = 300 s -> all-in estimate 3180 s; HARD CEILING 2880 s = turns 48 x --turn-wall-cap 60 s [policy bound, not a measurement: the runner aborts any turn that reaches it]
```

What each term is, and why the numbers do not move:

- **`turns × per-turn wall`** is read from `PROJECTION.json` for the declared thinking
  mode (`projected_turn_wall_s_by_mode`, p50; `_p90_by_mode` under `--projected-from p90`),
  or from `--projected-turn-wall`, or from the named row file's p90. The calibrated
  `off` figure stays **60 s/turn** and a hostile value is still refused with exit 8.
- **`runner-priced extras`** is `would_send_total − turns × reps`: the digests/warm-ups
  the runner's own `--dry-run` priced. It keeps the printed addition exact to the second.
- **`fetch follow-up allowance`** is `ceil(turns × reps × 68/801)` from
  `FETCH_FOLLOWUP_RATIO` in `cell.py` — the ratio G1 already reads, one source. It is
  **printed with its seconds and not folded into the compared figure**: G1 reserves those
  reservations in the ledger, and G2's measured per-turn wall already spans the follow-ups
  a turn makes, so adding them again would double-count the turn they ride inside.
  Printing them makes GATE-LEDGER's G2-D6 visible instead of silent.
- **`HARD CEILING`** is `turns × --turn-wall-cap`. It is arithmetic on a policy the
  runner enforces live, so no run can exceed it; it is **not** the figure G2 compares
  (at RUN-A*'s flags it would be 48 × 180 = 8,640 s and would refuse the 2,880 s wall,
  which is why the gate compares the fitted estimate and merely prints the bound).

**G2 prices policy, not measurement: the fitted ratio is an estimate and `turns × --turn-wall-cap` is the bound.**

Every refusal is unchanged: `projected > max_wall` → exit 8 with the five facts, a
non-positive `--projected-turn-wall` or an unusable p90 → exit 8, an unmapped thinking
mode → exit 8. The allow/refuse sentences now also carry the hard ceiling, labelled as
policy, so a refusal shows **both** the policy (`--max-wall`) and the bound.

