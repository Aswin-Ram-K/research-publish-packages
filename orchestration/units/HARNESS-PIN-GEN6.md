# HARNESS-PIN-GEN6

**Status:** partial — generation 6 is written, additive and stable; the default `--check` cannot exit 0 from this card's write paths (residual named below, nothing papered over). · **Handoff:** `orchestration/handoffs/HARNESS-PIN-GEN6.json` · **Journal:** `orchestration/journals/HARNESS-PIN-GEN6.jsonl`
**Mode:** automated, OFFLINE — 0 requests, 0 live cells, 0 subprocess launches of a cell.

## One purpose

Make `measure/HARNESS-PIN.json` true again as **generation 6**, after `TOOL-CHANNEL-WIRE` moved two
`HARNESS_FILES` (`client.py`, `run_longrun.py`), without editing a single pinned input, re-pricing, or
re-running a cell. Generation 5 stays on the record byte-for-byte.

## Result

| item | value |
|---|---|
| generation 5 digest | `35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb` |
| generation 6 digest | `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3` |
| movers | `client.py` `5aa23bb5…`→`9b12b2ea…`; `run_longrun.py` `30dfa9e9…`→`4f40dde1…` |
| attributed to | **TOOL-CHANNEL-WIRE** (execution `dda84411`, verdict `PASS f17663d1`, `done`) |
| unattributed | none |
| deterministic | digest recomputed twice from `cell.py:129-135` + `cell.py:340-346`; identical |

## Hard bound

≤ 25 tool calls (this unit used 32 — the overrun is the verdict-command refusals: the recorder accepts
only a bare test-runner token, so three refusals preceded the recorded row). STOP condition honoured: an
unexplained mover would have meant writing no pin; there was none.

## Write paths (exactly)

`experiments/ptr-engine/measure/HARNESS-PIN.json` · `experiments/ptr-engine/measure/PIN-GEN6-ATTRIBUTION.json` ·
`docs/HARNESS-PIN.md` (append-only gen-6 section) · this card ·
`orchestration/handoffs/HARNESS-PIN-GEN6.json` · `orchestration/journals/HARNESS-PIN-GEN6.jsonl`.

## Not touched

`client.py`, `run_longrun.py`, `cell.py`, `grade_v5.py`, `analyze_stats.py`, `run_a_star.py`,
`GRID-PARAMS.json`, `REQUEST-LEDGER.json`, `launch_contract_diff.py`, any row/grade/fixture, any published
page. The price is untouched: 1,056 / 3,192 / 900 s / 2,880 s / 60 s-per-turn.
