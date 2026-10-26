# FETCH-CHANNEL-FIX — make a fetch land, bill it once (zero requests)

**Status:** done · **Verdict:** FETCH-CHANNEL-FIXED · **Requests sent:** 0
**Card:** 65834223-28f9-4bf9-8f90-9bf3b8616348 (executionCount=2 — authored by execution 1, verified by execution 2)

## Objective
The live probe PROBE-CP3-FETCH spent 68 requests and delivered **not one tool result**: the arm emitted
`ptr_engine/resolve.py` (its own fixture-index shape) and `resolve_read_path` resolved from the workspace
root only, so 54 rows refused `path_not_found`; `fetch_rounds` reset on `--resume` (8/8 reported, 20 spent);
the 8 rounds were spent by t30 so the t46 CP3 call was refused `fetch_budget_exhausted`; and a duplicate
call was re-bought per turn. Fix the channel, offline.

## What changed (all inside the `--tools` path)
1. **Two bases.** `resolve_read_path_base(path, root, engine_root)` → workspace root FIRST, then
   `experiments/ptr-engine/`; the match is reported as `<tool_result … base="workspace|engine">` and on the
   `tool_calls` record. The refusal rules (absolute, `~`, `..`, realpath escape, secret-shaped) run once on
   the raw string, so they are identical for both bases — `path_refused`, zero reads, from either.
2. **Advertised form.** New fixture `tasks-v4/runtime-v4/LR-01.v4.tools2.json`: one sentence added to the
   system prompt — *"paths may be engine-relative, e.g. `ptr_engine/resolve.py`"*, plus 24 rounds, plus the
   cache rule. Checks/turns/items/checkpoints are byte-identical to `LR-01.v4.tools.json` (verified by diff).
3. **Durable rounds.** `fetch_rounds_spent(rows)` derives spent rounds from `kind='tool-followup'` /
   `fetch_followup` rows and any `fetch_rounds_used` stamp; `--resume` takes
   `max(manifest tools.fetch_rounds_used, derived)`, so neither a reset manifest nor a short row file
   can re-open the cap (the request budget still adds the full cap, and `requests_sent` stays exact:
   turns + follow-ups actually spent).
4. **No double billing.** A per-turn cache and a per-cell `served` cache: within a turn two identical calls
   execute once and bill once (`calls_billed == 1`); across turns the identical call returns the same block
   with `cached="true"` and buys no follow-up request.
5. **Cap 24/arm** (was 8) — 8 was arbitrary and starved CP3; the real bound is the card's request budget, and
   `requests_sent = turns + follow-ups actually spent` stays exact.

## Evidence (see handoff for the full block)
- `test_tool_channel2.py` exit **0**, `test_tool_channel.py` exit **0** (offline: sockets raise, `send_chat` = 0).
- (a) `ptr_engine/resolve.py` → engine base, L66-71 of the real file; (b) `../../etc/passwd` and
  `/etc/passwd` `path_refused`, 0 reads from both bases; (c) `calls_billed == 1`, second record
  `cached="true"`; (d) 24 derived rounds → next call `fetch_budget_exhausted`, 0 requests; (e) `--tools` off
  filtered stdout sha `20dbb377…` identical pre-fix and post-fix.
- Dry-run on `…v4.tools2.json`, `pointer-stable`, `--tools read_file`: exit **0**, `would_send_total=48`,
  `fetch_rounds_cap=24`.

## Bound
Declared 28 tool calls; execution 1 reported ~41 (harness restart + per-call `/tmp` + a secret-shaped-string
block on a probe command). Execution 2 used 24. No request, no network, no write outside the declared paths.
