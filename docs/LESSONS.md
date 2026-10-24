# LESSONS — process findings worth keeping

Written by **U8.2**, derived only from what is on disk (`orchestration/handoffs/*.json`,
`orchestration/VERDICTS.md`, `docs/PLAN_CORRECTIONS*.md`) — no finding is invented. Each lesson
names the incident/unit it came from. A claim with no corroboration on disk is marked
`reported-only`.

## 1. A missing closing message is not missing artifacts

A unit reported as failed-with-no-message (`V4`) had in fact written its handoff **after** its
revert cycles: `orchestration/handoffs/V4.json` exists with `overall: "PARTIAL"`, so the earlier
"left no report" premise was wrong. `V4R` was launched to recover it and had to re-establish what
was already there (`V4R.recovery.v4_artifacts_present`). **Check for the handoff on disk before
assuming nothing exists.** (`U1.7` is the genuine no-handoff case: it died with neither card nor
handoff.)

## 2. Write the handoff early, then update it

`U1.7` died mid-flight leaving **no handoff and no card**, so its evidence is lost/reconstructed.
The rule "persist a `status: partial` handoff immediately after step 0, rewrite it after each
step" exists because of that — units like `U2.2` and `U4.0` persisted partial handoffs while
still in flight, which is the behaviour that survives a death.

## 3. Stale-bytecode hazard

A byte-length-neutral revert can leave a same-second `.pyc` and produce a **false** failure on a
restored file. `U1.7R` recorded that "every run used `PYTHONDONTWRITEBYTECODE=1` after a
`__pycache__` purge"; `U7.2` carries the same `bytecode_discipline` and `U3.4` purges `__pycache__`
around both of its reverts. Run revert/restore comparisons that way.

## 4. Numbers must travel with their context

Three counting errors were caught only by a second unit re-checking the first: (i) a
node/edge/community triple (2685/7102/128) was quoted against a **moved-HEAD** artifact — V1's
rebuild at `b44e0e1` read 2695/7151/119; (ii) `U3.1`'s `unresponsive_engines: []` claim was
refuted live by V3 (correction **l**) — the field was non-empty; (iii) `.worktrees/` is pruned by
policy as **one directory** and never enumerated (`U1.4`: ".git/, .worktrees/, node_modules/ …
never walked"; `U1.7R` `worktrees_rejected: 1`), yet `U4.2`'s card cites "441 files under
`.worktrees/run-1/`" — a count of a path the policy never walks, and the verifier recorded that
the figure "was **not** re-counted" (`orchestration/VERDICTS.md`:213). A number without its
artifact, sha, window — or a path that is actually enumerated — is not evidence.

## 5. A green test suite is not a guarantee

V3 proved an invariant correct **in code** with **no test guarding it** (correction **n**:
transport failures are never cached — `_negative_cache == {}`, `ok=False` for 4xx/5xx/empty/
malformed — and none of those paths is asserted by `tests/test_web_search.py`). That is the
failure mode that survives review and dies in a refactor. The remedy shape is `U1.6`'s fail-closed
bound-flag guard: a bogus flag fails in the suite (`1 failed`) instead of at runtime.

## 6. The sealed window

A single pre-run quiescence check cannot certify a run. The foreign writer is **bursty**: 8 HEAD
moves inside one 3-minute reflog window while 5 s and 25 s windows both read `quiescent`
(`files_touched_in_window = 0`) — V7 corrections **q**/**y** — and `detect_concurrent_writer` was
blind to writes inside an **existing** untracked path until that was fixed (correction **u**, with
a new-untracked-entry control). Assert quiescence **before**, re-verify HEAD/porcelain **after**,
and report both.

## 7. Fail toward correctness, not speed

The graph-copy reuse guard now re-stages whenever a label, the copy HEAD or the head itself cannot
be confirmed (correction **t**, `U7.1`): a graph staged at an older head while
`graph_state.json` claims a newer one is worse than a redundant rebuild — the state file's
`observed_head` was not a truthful provenance label.

## 8. Producer identity is not optional

V2 found candidates produced by a **replay client** stored indistinguishably from model-mined rows
(`state='mined'`, no producer/mode/model column on `candidates`/`runs`, no producer key in
`report.json`; only the `run_id` `live-u21-replay` and a title prefix hint at it) — the same class
of failure as fabricated reasoning. A stored row must carry who made it. (`V2` unit-level FAIL
remains open; `V2R` recovery is `partial` with no verdict on disk as of this ledger.)

## 9. The unit-id space is the orchestrator's

`U0.7` re-authored `cli.py` so a placeholder owner names a **batch** (`batch 2 (mining)`), never a
live unit id (`U2.1`) — a live id names an agent that will finish and be superseded — and added the
regression test asserting no placeholder owner matches `U\d+\.\d+[a-z]?` (14 passed).
`cli.PLACEHOLDERS` is now conformant; the Batch-0 tree had collided strings.

## 10. An automated session with no no-questions rule stalls silently

A board card whose `prompt` was one thin line, handed to a session that was never told it had no answerer,
cost **8h31m** and produced **zero artefacts**. `session-7e3c8cc9-6347-4419-b4b4-5b03729810cd` (unit `U3`)
called `ask_user_question` at step 3 asking for the unit objective, because the contract lived only in the
card's `description` — a field the board does not send — while `prompt` carried "Live measurement unit. Hold
the `.occamy.lock` for the whole cell batch." The `U6` session asked **9** times and also produced nothing;
three task-board execution sessions stalled the same way on 2026-10-21. The fix has two halves, both now
stated in [`AGENTS.md`](../AGENTS.md) §"Automated sessions never ask the user": every card's `prompt` must be
the **whole** unit contract, and every executable card carries an `automated` tag whose `promptPrefix`
forbids questions. A prompt that needs the `description` to be understood is not a prompt.
