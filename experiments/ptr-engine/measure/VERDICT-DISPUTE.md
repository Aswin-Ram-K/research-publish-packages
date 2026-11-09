# VERDICT-DISPUTE — three records, two disputes, one adjudication each

**Tree pinned:** `HEAD f17663d1fed0162a7dc3c5a0a58d372c710974c3`, `git status --porcelain` = 345 entries
(count only, 345 at pin / 352 at re-check — 5 of the 7 new entries are this unit's own deliverables and 2
are concurrent writes by other sessions). All five pinned files below hash identically before and after,
and `HEAD` did not move, so no artefact the verdict rests on moved mid-run.

| file | sha256 |
|---|---|
| `experiments/ptr-engine/longrun/cell.py` | `fd4f2b01a6bfdeea425a92de428f770bf9f07fbe3bdc3b1d8cfd1f4a17ee2ec6` |
| `experiments/ptr-engine/longrun/analyze_stats.py` | `0a9a786102ca870edb3ff714538a512e0ea59534e4ced2f3d012aec0e39b493b` |
| `experiments/ptr-engine/tools/fixture_v7_audit.py` | `ae07f2da94b878f104aecbd36a2cb55c75434d38d09b33623cd6ddbe5f251f8f` |
| `experiments/ptr-engine/measure/p95-power-verify.sh` | `e7a12ef473ff6a51b0e7d75042398a9401496e48e561c5b7e80efd706b3a18d8` |
| `orchestration/units/V-GATE-CHAIN-3.md` | `6c3ddd6d1f6630001224177d13010e4cfd4e976bb733bbc4d31c4b5ceaf9afbb` |

`analyze_stats.py` is **untracked at this HEAD** (`git show HEAD:…` → *"exists on disk, but not in
'HEAD'"*). That single fact explains the second dispute: a digest of an untracked file can drift
without a commit, and nothing in the tree records when it did.

---

## 1. The three records, side by side

| | closure verdict | card's own record | recomputed here |
|---|---|---|---|
| **`V-GATE-CHAIN-3`** (`4e7e8017`, exec `0884f187`) | `PASS f17663d1` | handoff `overall: fail` — "6 bypasses survive, 0 of 3 decision expressions fully validated", `failed_assertions: []` | **exit 0**, `{"failed": [], "cases": 33}` — reproduces |
| **`P95-POWER-FROM-ROWS`** (`3ef6e0e3`, exec `b03377d6`) | `FAIL exit-1 f17663d1` | board post + handoff: `PASS`, "exit 0, P95-POWER.json regenerated identically", 14 rows files sha-pinned | **exit 1**, twice, identically |
| **`V-FIXTURE-V7`** (`c87b53ae`) | `PASS f17663d1` | — | **exit 0**, `{"agree": 12, "disagree": 0, "ambiguous": 0}` — no dispute |

---

## 2. Claim 1 — what the attack script is, and what exit 0 means

Read from `orchestration/units/V-GATE-CHAIN-3.md` between `<!--ATTACK-SCRIPT-START-->` and
`<!--ATTACK-SCRIPT-END-->`.

- **What it asserts:** 26 named assertions over 33 end-to-end `cell.main()` invocations plus 11 direct
  gate evaluations — refusal exit codes with zero live spawns for bad ledger / prereg / fixture, crash
  versus refuse for `inf`/`nan`, live-spawn counts and `argv` inspection for the allow cases, the docs
  code-table coverage, and byte-identity of `cell.py` before and after (`cell_pinned`).
- **What exit 0 means:** *not* "the script completed". It ends `sys.exit(1 if bad else 0)`, so exit 0 means
  all 26 assertions evaluated true and `cell.py` was byte-identical.
- **Does it encode the card's own `overall`?** **No — it encodes its inverse for six of them.** Six
  assertions require the surviving bypasses to be *admitted*:

  | assertion | requires | card finding |
  |---|---|---|
  | `B2_max_wall_1e308_allows` | `exit == 6` | F1, `--max-wall 1e308` is an unlimited mode |
  | `G_tiny_override_allows` | `exit == 6` | F2, `--projected-turn-wall 1e-9` zeroes the projection |
  | `H_artefact_zero_allows` | `exit == 6` | F3, artefact `proj_turn` 0/−12/1e-9 unvalidated |
  | `D_turns0_H3_runs_full_no_maxturns` | `exit == 6` | F4, `--turns 0` prices 0 requests, full cell runs |
  | `D2_turns_neg_runs_full` | `exit == 6` | F5, `--turns -48` makes `would_spend` negative |
  | `I2b_cap_zero_passed_to_runner` | `exit == 6` | F8, `--turn-wall-cap 0` handed to the runner |

  The three decision expressions are handled unequally: **G1** is partly asserted (and the asserted
  values are the *allow* ones); **G2** exists only as a description string in `EXPR['G2_decision']`, and
  the 11 `DIRECT['G2_*']` results are written to `result.json` but referenced by **no** assertion;
  **G3** is not touched by any assertion. That is the card's "0 of 3 fully validated", dead to rights.

### Adjudication 1

**`PASS` is supportable only as "the attack script ran green". It is not supportable as "the gate chain
has no surviving hole", and the two are not close here.** The exit code cannot distinguish them,
because the assertion set was written from observed behaviour rather than from the requirement: a green
run is *compatible* with the six bypasses surviving — it demands that they survive.

For that command to carry the card's verdict it would have to assert, for every operand of G1/G2/G3,
that a value which makes the gate expression true while the priced work exceeds the real bound is
refused with the gate's own exit code and zero live spawns: `--max-wall ∈ {1e308, inf}`,
`--projected-turn-wall 1e-9`, artefact `proj_turn ∈ {0, −12, 1e-9, NaN}`, `--turns ∈ {0, −48}`,
`--fetch-followup-allowance -100`, `--turn-wall-cap 0`. Not rewritten here.

**Winner: the handoff.** `overall: fail` is the true statement about the gate chain.

---

## 3. Claim 2 — why the p95 verifier exits 1 on a reproducing tree

Frozen command, run twice, from the workspace root:

```
bash experiments/ptr-engine/measure/p95-power-verify.sh   ->  exit 1   (run 2: exit 1)
stdout: Files /tmp/p95-power-regen.YGO1t6.json and experiments/ptr-engine/measure/P95-POWER.json differ
stderr: (empty)
```

**The failing assertion** is the script's only one, at its last line:

```bash
diff -q "$OUT" experiments/ptr-engine/measure/P95-POWER.json
```

The generated JSON and the committed JSON differ in **exactly one line**:

```
<   "analyze_stats_sha256_atimport": "0a9a786102ca870edb3ff714538a512e0ea59534e4ced2f3d012aec0e39b493b",
>   "analyze_stats_sha256_atimport": "2c9756f3f6cf9c07174cda290a86cc506b0d608bd1c9a0dc6884540c966b2d1c",
```

Every computed number is **identical**: p95 interval widths, paired disjoint percentages, observed
gaps, autocorrelation, the verdict string. Classifying the cause:

- **Flaky?** No — exit 1 on both runs, same byte, same message.
- **Fixture-dependent?** No — no missing file; the generator exits 0 and produces a full JSON.
- **Tree-state dependent?** **Yes.** `analyze_stats.py` hashed `2c9756…` when the card ran (the handoff
  records exactly that value) and hashes `0a9a78…` today; it is untracked, so no commit brackets the
  change. The generator records the digest as pure provenance — `p95_power_gen.py:271`
  (`'analyze_stats_sha256_atimport': sha(ANALYZE_STATS)`) and `:272` (`'analyze_stats_imported': False`)
  — so the file is hashed and **never imported**.

### Adjudication 2

**`A* sufficient` — `supported`.** The failure is environmental: a stale digest of a file the
computation does not read. The numbers that carry the claim regenerate byte-identically at `f17663d1`,
so the power conclusion is intact; the verdict statement in `docs/P95-POWER.md` §6 is intact with its
scope ("narrowly, and only on the grid A\* replicates … the C-grid pair is already disjoint at n = 47/48").

**Winner, on substance:** the card's `PASS` — it was true at its own tree, and is still true of the
numbers. The closure `FAIL` is not evidence that the power claim broke; it is evidence that the
evidence command conflates substance with provenance. **Winner, on the frozen command:** the closure —
the command really does exit 1 today, and the card's PASS cannot presently be re-earned from it.

Downstream artefacts leaning on it: `docs/P95-POWER.md:21` and `:185`, `P95-POWER.json` (carries the
stale digest), `orchestration/handoffs/P95-POWER-FROM-ROWS.json` (claims exit 0),
`experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` (the 792-request grid, plus its line 98 stop rule on
V-GATE-CHAIN). `docs/PRICE-REPLICATION.md` does not exist; `docs/PARM-1-ERRATA.md` cites the n ≥ 60 floor,
**not** n = 144, so it is untouched by this dispute.

---

## 4. Claim 3 — no dispute

`python3 experiments/ptr-engine/tools/fixture_v7_audit.py` → exit 0, `{"agree": 12, "disagree": 0,
"ambiguous": 0}`. Confirmed.

---

## 5. Consequences — artefacts that must change (none edited by this unit)

1. `orchestration/VERDICTS.md` — the `V-GATE-CHAIN-3` PASS must be re-derived from the handoff, not the exit code.
2. `experiments/ptr-engine/longrun/cell.py` — operand validation for G1/G2/G3 (F1–F8) must land before any grid spend.
3. `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` — the 792-request pricing leans on a paper precondition.
4. `experiments/ptr-engine/measure/P95-POWER.json` — stale `method.analyze_stats_sha256_atimport`.
5. `docs/P95-POWER.md` — the verdict stands; its pointer to the verify command no longer reproduces green.
6. `orchestration/handoffs/P95-POWER-FROM-ROWS.json` — claims exit 0 for a command that exits 1 here.
7. `docs/GATE-CHAIN.md` — §4 "there is no unlimited mode" and the §5 hypothesis-refusal claims, already falsified.

---

## 6. What the verdict row can and cannot prove

A verdict row binds PASS to an exit code. An exit code is only as strong as the assertion behind it, and
this pair of disputes is the same bug pointing in opposite directions:

- **Green without the claim.** `V-GATE-CHAIN-3` exits 0 because its assertions encode the *observed*
  behaviour, including the six bypasses. The row proves "the script agreed with the conductor as it is",
  not "the requirement holds". A script can be green and the system broken.
- **Red without the claim.** `P95-POWER-FROM-ROWS` exits 1 because it asserts byte-equality over a
  provenance digest of a file it never imports. The row proves "an unused input changed", not "the result
  changed". A script can be red and the claim intact.

In both cases the exit code is not a function of the proposition the card asserted — which is the class
of bug. The frozen-command rule protects the *command* from being edited to fit the answer; it does not
protect the answer from being indexed to the wrong proposition, and every precondition that reads
`verdict == PASS` inherits that weakness.

**Smallest assertion that would have caught it.** For the gate chain: flip one line — assert
`by['B2_max_wall_1e308']['exit'] == 8` where the script asserts `== 6`. One assertion, inverted, and the
closure would have read FAIL and agreed with the handoff. For the power script: split the equality into
the payload that carries the claim and the provenance that does not — compare the generated numbers,
report the imported-module digest separately — so a stale hash of an unimported file cannot turn a sound
power result red.

**What a row cannot prove at all:** that the command's assertions were written before the behaviour they
measure, that they cover the requirement rather than a snapshot of it, or what the command would have
caught had the tree been different. It records one exit code at one sha, nothing more.
