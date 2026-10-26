# UNIT PROBE-CP3-V6 — un-starve the checkpoint (v4 tools2 fixture, pointer-stable)

Card: 4e559586. Lane: PROBE-CP3 (V5 handoff `orchestration/handoffs/PROBE-CP3-V5.json`).
Fixture (untouched): `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json`
(sha256 recorded in every row as `fixture_sha256`). Endpoint `http://192.168.2.168:8012/v1`,
model `occamy-1.0-NVFP4`, `--thinking off --max-tokens 4096` (frozen comparability flags).
Bound: <=80 live requests, <=45 tool calls. Automated: no user, no questions.

## PREDICTION STATED BEFORE THE RUN (to falsify)
`rounds_left_at_t46 > 0` (i.e. `fetch_rounds_used` at T46 is below the per-arm cap of 24)
**and** `cp.t46` grades pass. Report either way; a failed prediction with clean rows is a
result, not a failure.

## The two bounded changes (`experiments/ptr-engine/longrun/run_longrun.py`)
(a) **Serve from the prompt, bill no round.** `pinned_views(fixture, prompt)` finds the item
    bodies the planner ACTUALLY pinned into that turn's prompt (the exact `body_block(item)`
    text is searched in the built prompt — the runner's own view, no per-arm special case),
    and maps them onto file line ranges via each item's `source.pointer` (`#L36-L110` → 36..110).
    `find_pinned_view` matches a call by path (equality or `/`-anchored suffix, so
    `ptr_engine/resolve.py` matches `experiments/ptr-engine/ptr_engine/resolve.py`) and then
    STRICTLY by range: the requested lines must lie wholly inside the pinned range.
    `serve_from_prompt` injects those lines as a `<tool_result … base="prompt"
    served_from="prompt">` block, records `served_from="prompt"`, `executed=false`,
    `billed=false` on the `tool_calls` record, and increments no round. Toggle:
    `TOOL_SERVE_FROM_PROMPT` (a module flag so the offline test can prove red-before-green).
(b) **Cap fetch rounds per turn at 3.** `TOOL_FETCH_ROUNDS_PER_TURN = 3`, overridable with
    `--fetch-rounds-per-turn` (0 = unbounded, the pre-V6 behaviour, kept for the red case).
    Calls past the cap are refused host-side with `error="per_turn_round_cap"` and bill
    nothing. The value is frozen in the manifest (`tools.max_fetch_rounds_per_turn`) and
    stamped on every row (`fetch_rounds_cap_per_turn`).

### The accounting that makes the prediction testable (stated, not hidden)
A prompt-served result the model never sees is not a result, so a served call still rides
the ONE follow-up request a round would have bought — it just does not consume the per-arm
ROUND budget. Requests are the binding resource at 80 (48 turn requests + 24 follow-ups), so
the follow-up allowance is the same 24 and every not-yet-reached declared checkpoint holds one
request back (`followups_bought + reserved < pool`). Without that reservation a T3-style burst
spends the requests T46 needs; that is the same defect as (b), one ledger over. Both counters
are recorded per row: `fetch_rounds_used` (billed rounds) and `fetch_followup` rows (requests).

## Acceptance evidence
1. `tests/test_tool_channel2.py` -> exit 0 (V5 regression: 5/5, incl. duplicate billing and resume counter).
2. `tests/test_tool_channel3.py` -> exit 0, red-before-green for (a) and (b) plus tools-off inert.
3. dry run on the tools2 fixture -> exit 0, `would_send_total=48`.
4. live rows: 48 turn rows, `requests_spent <= 80`.
5. `grade_v3.py` per checkpoint.
6. tools-off inertness: `manifests/v6-proof-off-{before,after}.{txt,json}` — stdout byte-identical
   after filtering the one manifest line, manifest identical minus `created_utc`.

## Mid-run correction (disclosed, 2026-10-26)
The live cell was started, reached T6 (12 requests), then stopped and resumed at T7 with one
code correction: the per-arm round cap was checked once per TURN, so a spent round budget
(24/24) would have refused the T46 read even though a pinned-range serve bills nothing — the
v5 failure re-entering through the cap branch. It is now checked PER CALL: a call that would
need a fresh disk read past the cap is refused `fetch_budget_exhausted`, while a
prompt-served call is still served. A BILLED round still cannot exceed 24.
Rows 1-6 were written before the patch; it is inert on them (`fetch_rounds_used` was 0-5/24 at
T6, so the `rounds_used >= 24` branch was never taken), and no turn row was rewritten. The
frozen manifest was not touched, so `--resume` re-used it (sha checked against row 1).
Verified offline: at 24/24 spent, `resolve.py` L66-71 is served `served_from="prompt"` with a
round count of 24 and one follow-up request — the T46 path is reachable with the round budget
gone.

## RESULT
Prediction `rounds_left_at_t46 > 0 AND cp.t46 pass`: **first half HOLDS (4 rounds left),
second half FALSIFIED** (cp.2.t46 = `refused_while_knowable`).

| number | value | where |
|---|---|---|
| requests_spent | 72 (48 turn + 24 follow-up) | rows `turn`+`tool-followup` counts |
| fetch_rounds_used curve | 0,0,2,5,5,5,5,5,8,11,12,13,14,14,17,20 then 20 to T48 | rows `fetch_rounds_used` by `turn` |
| rounds_left_at_t46 | 4/24 | row `turn=46` |
| cp.0.t12 | PASS (`ANSWER: 64`) | grade `arms.pointer-stable.checks[0]` |
| cp.1.t24 | FAIL `marker_missing` | grade `checks[1]` |
| cp.2.t46 | FAIL `refused_while_knowable` ("marker dropped anchors; missing raising") | grade `checks[2]` |
| verified_success | False (acc 1/3) | grade `arms.pointer-stable.verified_success` |
| tokens total | 369,355 (prompt 356,740 / completion 12,615) | sum over rows |

At T46 the channel was CLEAN: the pinned read `ptr_engine/resolve.py` L66-71 was served
`served_from="prompt"` (0 rounds, `billed=false`), the last follow-up request was bought
(24/24), the arm received `_refuse`'s body and answered — `ledger.record_refusal(
scope=scope_name, serialized_ref=text, code=error.code)` — then lost the checkpoint on the
`^ANSWER:` marker's anchor set ("before re-raising"). Channel defect is gone; what remains at
T46 is answer discipline.

**Channel vs policy.** V5's T46 failure was a channel defect: the read was refused host-side,
so no content ever reached the model. V6 delivers it and the model restates the fact
correctly; the residual failure is a policy (marker/anchor) defect. The other regression,
cp.1.t24, is a *request* defect of the V5 family one ledger over: 24 follow-up requests cannot
cover 48 turns that each ask to read, and T24's request was reserved-away.
