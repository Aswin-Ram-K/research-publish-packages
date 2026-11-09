# CANARY-ARGV — the claim mode a 12-turn canary must carry

**Unit:** `CANARY-CLAIM-MODE` · **Cost:** 0 inference requests, 0 sockets, 0 live cells.
**Answer: the canary is NOT safe as the launch card is currently written.** The launcher
hard-codes `--hypothesis H2` (`experiments/ptr-engine/tools/run_a_star.py:182`), so all 48
canary rows would be written `claim: "H2"`, `comparison_eligible: true` — ungraded rows
inside the arm pool, eligible for R-all at n=144. The fix is one argv value:
`--hypothesis smoke`.

## 1. Every claim spelling the two CLIs accept today

There is exactly one resolver: `claim_mode.resolve_claim` (`experiments/ptr-engine/longrun/claim_mode.py:206-224`).
`run_longrun.py` and `cell.py` differ in flag name, not in decision.

| consumer | flag | `file:line` | accepted values | row / verdict shape | refusal |
|---|---|---|---|---|---|
| runner | `--claim-mode` | `run_longrun.py:2831-2839` (argparse), resolved `run_longrun.py:2962` | `smoke`, `plumbing`, `H1`, `H2`, `H3` (case-insensitive) | `smoke`/`plumbing` → `claim:"none"`, `comparison_eligible:false`, mode `smoke`; `H#` → `claim:"H#"`, `comparison_eligible:true` | absent / empty / `none` / unknown → **exit 12**, no row, no request (`run_longrun.py:2971-2975`) |
| conductor | `--hypothesis` | `cell.py:1887` (argparse), resolved `cell.py:1311-1325` | same five | same two shapes; G3 verdict carries `claim` + `comparison_eligible` (`cell.py:1404-1418`), smoke gets `smoke_prereg_verdict` (`cell.py:1427-1429`) | **exit 12** at `3c/7 G3 prereg gate` (`claim_mode.py:170-199`) |
| analyser | — | `analyze_stats.py:173` `INCOMPARABLE_CLAIM`, `:216-240` `require_comparable_claim`, `:1345-1353` | reads `claim`/`comparison_eligible` from rows + `.claim.json` sidecar | `claim:"none"` rows are **refused by name** `incomparable_claim`, never filtered | reported on the analysis record; comparison withheld |

Two edges worth knowing:

- **Scratch rows are exempt from the refusal.** A rows path under `tempfile.gettempdir()` with
  no `--claim-mode` is not refused: it is stamped `claim=none` and runs
  (`run_longrun.py:1754-1763` `_scratch_rows`, `:2965-2970`). So a `/tmp` canary looks safe
  even when the flag is missing — the corpus path (`experiments/ptr-engine/measure/`) is the
  one that exits 12.
- **A row with no claim fields is LEGACY, not claim-free** (`claim_mode.py:79-82`): it is
  accepted. The refusal keys on the explicit `claim:"none"`, which is why the marker must be
  written, not omitted.

## 2. Does `cell.py` forward the claim to the runner? YES — today

`cell.py:1590-1594`:

```python
    # CLAIM-ROW-STAMP: thread the ALREADY-resolved claim (cell's cached record, one
    # parse in claim_mode) to the runner, so every row it writes is stamped.
    _claim_rec = _resolved_claim(args)
    if not isinstance(_claim_rec, Exception):
        argv += ["--claim-mode", "smoke" if _claim_rec.is_smoke else _claim_rec.claim]
```

`cell.py` also writes the claim sidecar the analyser reads (`cell.py:1566-1587`,
`rows_path + ".claim.json"`). So **no claim wiring is needed.** The missing forward is
`--tools`: `cell.py` has no `--tools` argument (`grep` finds none), which is why
`run_a_star.py:52-66` installs the `CELL_RUNNER_PATH` runpy shim that appends
`--tools read_file` without touching the runner bytes (`harness_sha256` stays valid).
The claim mode rides the same hop: `cell.py` passes it to whatever `RUNNER` names, shim or not.

**Smallest wiring needed (NOT applied — separate card):** `run_a_star.py:182` writes
`"--hypothesis", "H2"` as a literal and `run_cell(..., hypothesis="H2")` (`:194`) records a
value it never uses. The one-line change is `cell_argv(arm, rep, hypothesis="smoke")` /
`argv` carrying the parameter, plus a `--canary` switch. Until then the canary inherits H2.

## 3. The exact 12-turn era-B canary argv (one arm, cell 1)

Run one per arm, 4 arms → 12 turns × 4 arms = **48 requests** (`GRID-PARAMS.json` :: `canary`).

```bash
python3 experiments/ptr-engine/longrun/cell.py \
  --arm pointer-stable \
  --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json \
  --turns 12 --reps 1 \
  --thinking off \
  --turn-wall-cap 180 --runaway-turns 2 --max-wall 2880 \
  --budget 108 --fetch-followup-allowance 48 \
  --hypothesis smoke \
  --no-cell-handoff \
  --out-dir experiments/ptr-engine/measure \
  --endpoint <endpoint>
```

- `--budget 108` and `--fetch-followup-allowance 48` are the values `GRID-PARAMS.json`
  publishes (`per_cell_budget.recommended = 108`, `fetch_followup_allowance.value = 48`).
  G1 prices `turns_total + allowance` (`cell.py:1160-1175`); `--budget` is the 3/7 preflight
  with 10% headroom (`cell.py:388-392`).
- `--tools read_file` is **not** a `cell.py` flag: it travels through the
  `CELL_RUNNER_PATH` shim (`run_a_star.py:52-66`, precedent `cell.py:122`), which `runpy`s
  `run_longrun.py` with `--tools read_file` appended. The runner bytes are unchanged, so the
  harness pin is unaffected.
- `--max-tokens 4096` is the runner's default (`run_longrun.py:2801`) and no `cell.py` flag
  forwards it; passing it explicitly would need the shim's append list. As written, the
  effective ceiling is 4096 either way.
- `--turns 12` is what makes this a canary: `cell.py` appends `--max-turns 12`
  (`cell.py:1560-1565`), the only rewrite the canary tool would make anyway
  (`tools/tranche_canary.py:91-93`).

## 4. What lands in the row, quoted

From the offline proof (runner's own `make_row`, `run_longrun.py:1766-1838`, synthetic
response, no request):

```
{"arm": "pointer-stable", "claim": "none", "comparison_eligible": false,
 "max_tokens": 4096, "stop_reason": "stop", "turn": 1}
all 12 turns: [('none', False)]
```

Stamp site (`run_longrun.py:1833-1838`):

```python
    claim_fields = (claim_mode.row_fields(cfg.claim)
                    if getattr(cfg, "claim", None)
                    else {"claim": claim_mode.CLAIM_NONE,
                          "comparison_eligible": False})
    row = {
        "arm": arm, **claim_fields, "task_id": fixture["task_id"], "rep": rep, "turn": t,
```

`claim:none` is written by both the `smoke` and `plumbing` spellings — they are synonyms
(`claim_mode.py:96-98`).

## 5. The analyser refuses it by name — quoted

`python3 analyze_stats.py --rows <12 smoke rows>`:

```
  CLAIM REFUSAL  incomparable_claim smoke.jsonl: refusing a comparison that includes 12 cell row(s) which make no claim (claim_free): cell=LR-01 arm=pointer-stable rep=1 turn=1; ... turn=12. A smoke/plumbing cell declares claim='none' with comparison_eligible=false, so its rows can never enter a comparison -- they are not filtered out silently, they stop the comparison. Compare only cells that declare H1|H2|H3, or report the smoke cell's numbers on their own with its claim named.
```

## 6. The opposite case bites — the same rows flipped

Identical 12 rows, `claim` set to `"H2"` and `comparison_eligible` to `true`: the refusal line
is **absent** and analysis proceeds to the arm report (exit 0; `ttft_p50`/`p95` still refuse
at n=12 for a statistical reason — minimum n 20/60 — which is independent of the claim):

```
arm pointer-stable  (rows n=12)
  provenance pointer-stable: fixture_sha256=0804b51575cc model=occamy-1.0-NVFP4 thinking=off tools_mode=on:read_file
  ttft_p50  REFUSED at n=12 ... minimum n for p50 is 20
```

That difference — one `claim` string — is the whole argument: the canary is either named
plumbing or it is arm data.

## 7. The sentence the launch card must carry

> **Canary claim mode:** launch the 12-turn canary with `--hypothesis smoke` (not `H2`): every
> canary row is written `claim: "none"` / `comparison_eligible: false`, so the 48 requests are
> plumbing and can never be pooled into an arm; `analyze_stats` refuses them by name
> (`incomparable_claim`). `--hypothesis H2` would put 48 ungraded rows inside the arm pool.

`--hypothesis none` is **not** an alternative: it is refused with exit 12 ("silence is not a
claim").

## 8. Is the 48-request canary safe as the card is written?

**No.** `run_a_star.py:182` hard-codes `--hypothesis H2`; the canary would be graded as arm
data. One argv value (`smoke`) makes it safe, and the analyser will then refuse it by name.
