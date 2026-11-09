# HARNESS-PIN

**Pinned harness digest:** `1f7c67914e5b76680616f08c16708635060a81ab3932c20806e597a5343f3285`
**Pinned at:** 2026-10-26T18:59:12Z by `HARNESS-REPIN` (offline; this unit edited no harness file)
**Supersedes:** `c4541802…` — additive and dated; the older pin stays on the record.
**Machine-readable pin:** [`HARNESS-PIN.json`](experiments/ptr-engine/measure/HARNESS-PIN.json)

## What the digest covers

`experiments/ptr-engine/longrun/cell.py:128-135` names the set (`HARNESS_FILES`) and
`cell.py:334-346` (`stage_harness`) folds it as `sha256` over `"name:sha256\n"` for the sorted
names, with the fixture added as the sixth input. `cell.py` is **not** in its own list, so it is
pinned separately here (it is the program that computes the digest, not one of its inputs).

| file | sha256 | size | mtime (UTC) |
|---|---|---|---|
| `experiments/ptr-engine/longrun/run_longrun.py` | `0d581d1f2ef90b1c3667c5cffcbe2088c60e6892188d4f643248a06b2fd32eb3` | 154535 | 2026-10-26T18:45:18Z |
| `experiments/ptr-engine/longrun/client.py` | `5aa23bb5470b7e0909992b3f0947867953ba39204e5d03eff0f95c30e57ca7bb` | 41593 | 2026-10-26T16:13:55Z |
| `experiments/ptr-engine/longrun/grade_v5.py` | `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` | 44739 | 2026-10-26T17:12:56Z |
| `experiments/ptr-engine/longrun/analyze_stats.py` | `800c8f6c2a483895febbe1bdc1a946408d6d4d01bdb7c1accda83d70364cdf6c` | 82694 | 2026-10-26T18:55:52Z |
| `experiments/ptr-engine/tools/det_verify.py` | `12ccc74ea31c3843021f1ae6fa771b458082f78393e2117cd86960fd221b6439` | 46515 | 2026-10-26T14:13:23Z |
| `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` | 57242 | 2026-10-26T17:02:46Z |
| `experiments/ptr-engine/longrun/cell.py` (pinned separately) | `c29a9fb36e9e8f0e166583d56db00b2184fbc12a97b77b1a72ca9f612c1a9c59` | 112724 | 2026-10-26T18:55:57Z |

## Which card moved which file

| file | old sha256 | new sha256 | mtime | card that owns the hunk |
|---|---|---|---|---|
| `experiments/ptr-engine/longrun/run_longrun.py` | `29445320…` | `0d581d1f…` | 2026-10-26T18:45:18Z | **RUNAWAY-POLICY** (done, handoff 18:50:02Z): `stop_reason=length` no longer ends the cell; two wall-time runaways still exit 6 — the derivation is at `run_longrun.py:1641-1646` and `run_longrun.py:1925-1926`. Card evidence: `pytest tests/test_runaway_policy.py` 3 passed; red rows `assert 6 == 0` and `assert 0 == 6`. |
| `experiments/ptr-engine/longrun/analyze_stats.py` | `8b829ca4…` | `800c8f6c…` | 2026-10-26T18:55:52Z | **ANALYSIS-CONSUMER-FIX** (done, handoff 18:57:09Z): the `usable_for` / `split_truncated` / `truncated_turns` consumer and the "no usable cells" exit-1 refusal. An intermediate state (`e90a5297…`) sat on disk at 18:54:01Z while the card was still in flight — same write path, same card. |
| `experiments/ptr-engine/longrun/cell.py` | `e24e867b…` | `c29a9fb3…` | 2026-10-26T18:55:57Z (bytes unchanged since 18:54:16Z) | **GATES-MESSAGE-CONSISTENCY** owns the allow/refuse sentence branch — `cell.py:390`, `cell.py:733`, `cell.py:750`, `cell.py:791`, `cell.py:947` — and declares no change to any decision, threshold, exit code or computed/limit/ok value. **The write at 18:54:16Z is UNATTRIBUTED.** |
| `experiments/ptr-engine/longrun/client.py` | `5aa23bb5…` | unchanged | 2026-10-26T16:13:55Z | — |
| `experiments/ptr-engine/longrun/grade_v5.py` | `056eb605…` | unchanged | 2026-10-26T17:12:56Z | — |
| `experiments/ptr-engine/tools/det_verify.py` | `12ccc74e…` | unchanged | 2026-10-26T14:13:23Z | — |
| `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | `0804b515…` | unchanged | 2026-10-26T17:02:46Z | — |

## unattributed-change

`cell.py` was written at **18:54:16Z** and no settled handoff claims it. `BUDGET-48-WIRE`
(handoff 18:54:58Z) only *read* `cell.py:353-395` and `cell.py:1495-1535` and declares GRID-PARAMS
paths; `ANALYSIS-CONSUMER-FIX` and `CANARY-ERA-B-FIX` declare `analyze_stats.py`;
`LEDGER-REBUILD-27` declares none. Nothing was reverted and nothing was normalised — an edit
nobody claims is the finding.

The byte-level hunk cannot be quoted. The previous recorded bytes `e24e867b…` (from the
`TRANCH1-DRYRUN-2` pin of 18:16:29Z) have no copy anywhere in the tree — a bounded scan of
`manifests/`, `manifests/archive/`, `scratch/`, `audit/` and `state/logs/` covering 2406 `.py` files
found no sha match — and `cell.py` is untracked by git (`git ls-files` refuses it), so no baseline
exists to diff against. What is quoted instead is the whole surface that changed: **112724 bytes**,
sha256 **`c29a9fb36e9e8f0e166583d56db00b2184fbc12a97b77b1a72ca9f612c1a9c59`**, mtime 18:54:16Z and re-emitted byte-identical at 18:55:57Z.

## Premise corrections the tools-on rehearsal found

**P1 (load-bearing) — the fetch allowance is a G1 flag, not the channel lever.**
`--fetch-followup-allowance` is declared at `cell.py:1882-1883`, consumed at `cell.py:954` through
`cell.py:1160` (`fetch_followup_allowance(args, turns_total)`), and forwarded by the driver at
`experiments/ptr-engine/tools/run_a_star.py:201`. The runner has **no such flag**. The runner's
per-arm channel cap is the constant **`TOOL_FETCH_ROUNDS_PER_ARM = 24`** at
`experiments/ptr-engine/longrun/run_longrun.py:226`, enforced at `run_longrun.py:940`
(`error=fetch_budget_exhausted`, `billed=false`). Therefore raising the allowance alone moves the
**projection** (`cells[].projection.followup_allowance`) and leaves the **channel** at 24 rounds.
The real levers: `run_longrun.py:226` for the channel, `cell.py:1882` for the G1 projection,
`--turns` / `--reps` for n.

**P2 — a dry run never launches the runner.** The `elif args.dry_run:` branch opens at
`cell.py:1956`, prints the WOULD-REFUSE lines at `cell.py:2005` and returns 0 at `cell.py:2009`. A
dry run proves the G1/G2/G3 projections and that 0 of 3 gates would refuse; it proves nothing about
the runner argv. The `--tools read_file` argv and `tool_channel=read_file fetch_rounds_cap=24`
claim requires launching the shim itself, which is what `DRYRUN-TOOLS-SHAPE` did.

**P3 — the wrong claim's real locator.** `GRID-SHAPE.json` has **no key `2a`** (top-level keys:
`schema, unit, question, answer, era, offline, fixture, invitation_era, factor, grid, cells,
not_touched, abandoned_cell`) and `docs/GRID-SHAPE.md` has no numbered item 2a. The wrong claim is
present under another locator: **`cells[*].cell_py_flags[8] = "--fetch-followup-allowance 24"`** in
all 10 cells. That key path is `superseded_by:
experiments/ptr-engine/measure/HARNESS-PIN.json#premise_corrections[P1]`. The same file's
`factor.ceiling_from` already cites the right lever (`TOOL_FETCH_ROUNDS_PER_ARM=24
(run_longrun.py:226) / 48 turns`), so `GRID-SHAPE.json` is internally half-right; it is a decision
record and was not edited.

## Would a re-run be `stamped` or `moved`?

Against **these bytes**, yes: the digest is computed with the same recipe `cell.py` uses, so a
re-run on this tree is `stamped` at `1f7c67914e5b76680616f08c16708635060a81ab3932c20806e597a5343f3285`. Against a tree that keeps being edited, no — the
harness moved three times inside this unit's own window (18:45:18Z, 18:54:01Z→18:55:52Z,
18:54:16Z), which is exactly why the pin is dated, additive, and accompanied by an
`unattributed` entry rather than a clean bill.

## Generation 6 — `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3` (appended 2026-10-26T23:26:13Z by `HARNESS-PIN-GEN6`)

**Pinned harness digest:** `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3`
**Supersedes:** `35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb` (generation 5, frozen 2026-10-26T20:05:00Z) — additive and dated; generation 5
stays on the record **byte-for-byte** inside `HARNESS-PIN.json#supersedes_pin_generation_5` because the
canary's 36 rows ran on it.
**Machine-readable pin:** [`HARNESS-PIN.json`](experiments/ptr-engine/measure/HARNESS-PIN.json) (`generation: 6`)

> This section is **appended**. The page header above still names generation 2's digest and was not
> rewritten: history on this page is append-only, so a reader must read the newest generation section,
> not the header, as current. That header drift is recorded here as a gap, not repaired.

### What moved, and who moved it

Recomputed with `cell.py`'s own list (`cell.py:129-135`) and its own recipe (`cell.py:340-346`, `sha256`
over sorted `name:sha256` + newline over the five `HARNESS_FILES` + the fixture). Per-file shas were
compared against generation 5's recorded values, member by member:

| file | sha256 | size | mtime (UTC) | vs gen 5 |
|---|---|---|---|---|
| `experiments/ptr-engine/longrun/run_longrun.py` | `4f40dde188b4812031c01304b3bd07c9f5b64ecc268aa48bb46eb3aabf69a4ca` | 163866 | 2026-10-26T23:17:47Z | **MOVED** (`30dfa9e9…`) |
| `experiments/ptr-engine/longrun/client.py` | `9b12b2ea948b23f0f1600c4bcf4c8f6d72e17e900c046e555e7bc78d6630c0c6` | 50410 | 2026-10-26T23:16:33Z | **MOVED** (`5aa23bb5…`) |
| `experiments/ptr-engine/longrun/grade_v5.py` | `3d70ed1d43d2ab098eeeba4b50fa574273c71e9ff24af5adaa9e519d10c77940` | 51688 | 2026-10-26T19:44:44Z | same |
| `experiments/ptr-engine/longrun/analyze_stats.py` | `30b07d4d61930e0cb863badd553d0e11e8c9bdcfdba7de5973abdbd675253c9a` | 84560 | 2026-10-26T19:14:14Z | same |
| `experiments/ptr-engine/tools/det_verify.py` | `12ccc74ea31c3843021f1ae6fa771b458082f78393e2117cd86960fd221b6439` | 46515 | 2026-10-26T14:13:23Z | same |
| `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` (fixture) | `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` | 57242 | 2026-10-26T17:02:46Z | same |

`cell.py` also moved (mtime 2026-10-26T23:18:37Z) but **`cell.py` is not in its own list**, so it cannot
move this digest.

| mover | card | execution | window evidence | the change is what the card claimed |
|---|---|---|---|---|
| `client.py` `5aa23bb5…` → `9b12b2ea…` | **TOOL-CHANNEL-WIRE** (`done`) | `dda84411`, verdict `PASS f17663d1` | the card's declared `write_paths` name this file; mtime 23:16:33Z is after gen 5 froze (20:05:00Z) and 5m11s before the card's handoff was written (23:21:44Z) | yes — the schema is sent and gated: `client.py:386` `return {"tools": [json.loads(json.dumps(READ_FILE_TOOL_SCHEMA))],` and `client.py:387` `"tool_choice": tools_choice(cfg)}`; `tools_schema_sent` at `client.py:299`, `client.py:847`, `client.py:948` |
| `run_longrun.py` `30dfa9e9…` → `4f40dde1…` | **TOOL-CHANNEL-WIRE** (`done`) | `dda84411`, verdict `PASS f17663d1` | same declared `write_paths`; mtime 23:17:47Z, 3m57s before the handoff write | yes — structured calls are consumed first: `run_longrun.py:690-702` ("TOOL-CHANNEL-WIRE: a tools-on reply carries `message.tool_calls` … Structured calls are therefore consumed FIRST; the text parser runs only when the reply carries no structured call"), used at `run_longrun.py:1030-1032` and `run_longrun.py:1136`, row field at `run_longrun.py:2043-2044` and `run_longrun.py:2692` |

**`RUN-DRY-TURN-SCOPE` is NOT part of this delta.** Its turn-scope change is already inside generation 5's
`run_longrun.py` (`b2003038…` → `30dfa9e9…`, named in generation 5's own `cause`); its handoff mtime is
2026-10-26T19:56:44Z, before generation 5 froze. Nothing in this generation is unattributed, so the pin
was written (an unexplained mover would have been a stop).

### Epoch consequence — one sentence each

- **What generation 5 still legitimately covers:** the canary's **36 rows** — they ran on the
  generation-5 tree (`35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb`) and must stay labelled generation 5 in every table, never pooled with a
  post-generation-6 row.
- **What cannot be compared across the boundary:** any future row's `request_digest` for a **tools-on**
  request — the body gained a `tools` key (and `tool_choice`), so those digests changed
  (`TOOL-CHANNEL-WIRE` measured `3c0ff847…` after the change); **tools-off request digests are unchanged**
  (`f0499dd1335cccb27db359bee8d29c02a0f3015ee8e734404f288fbff0e2f8da`).
- **Crossing still open:** `run_a_star.py:52-53` still holds `PIN_EXPECTED_GENERATION = 5` /
  `PIN_EXPECTED_DIGEST = 35ff41b7…`, so a grid or canary launch from this tree is refused until a
  successor card advances both (this card may not edit `run_a_star.py`). No live cell may run before that.

### Guard evidence (three checks, quoted)

| command | expected | actual |
|---|---|---|
| `python3 experiments/ptr-engine/tools/launch_contract_diff.py --check` | 0 | **1** — the pin row now matches the bytes (`pinned inputs whose bytes moved: none`), but five non-pin rows still disagree; see the residual below |
| `… --check --pin-generation 5` | 13 `MOVED`, naming the movers | **13** — `moved input: … client.py 5aa23bb5… -> 9b12b2ea…` and `moved input: … run_longrun.py 30dfa9e9… -> 4f40dde1…` |
| `… --check --root /tmp/gen6-tamper` (copy with one byte changed in `client.py`) | 1, a real disagreement | **1** — `harness_pin_digest` `efefd885… | 83ddd7156ea9a0f67bff66f47ef8a9101795a2d714ea633f837037705f965b02 | 35ff41b7…`, `pin drift: client.py` |

### Residual (recorded, not papered over)

`--check` cannot exit 0 from this card's write paths. After the pin, the `harness_pin_digest` row's
remaining old value is **`GRID-PARAMS.json`** (`harness_pin.harness_sha256 = 35ff41b7…`; needs a card that
owns the params bump), and the row's `reason` now names a **stale probe**: it still greps
`^HARNESS_PIN = "([0-9a-f]{64})"` in `run_a_star.py`, a constant `LAUNCHER-GEN5-WIRE` replaced with a pair
read at import time. The other five disagreeing rows (`price_total`, `price_remaining_after`,
`ledger_spent`, `ledger_remaining`, `floor_n60`) are **pre-existing** — the same five disagreed before this
card wrote anything. All of it lives in files this card may not edit (`GRID-PARAMS.json`,
`REQUEST-LEDGER.json`, `launch_contract_diff.py`, published pages).

Updated: 2026-10-26T23:26:13Z (`HARNESS-PIN-GEN6`)
