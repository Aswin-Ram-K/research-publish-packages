# R2-SGL-CAP — slot budget is the capacity lever: 320 slots, `no_buffer`, and `lfu`, with the resident window re-measured

**Board card:** `dc588446-6d96-4499-8eab-d67f2f1c1c64` · **execution:** `22ca7c41-9275-4960-acae-5d133df4a756`
· `session-7319baa2-1830-4f0b-aa2c-24e4f87395b7` · Round 2, window 2 · operator approval 2026-10-23 20:28 CDT.

## Objective

Test the only capacity lever that can plausibly move the resident window, since Round 1 established
that paging knobs are dead ends and the resident window is **0.1592–0.1645** of declared token capacity.
Three arms, one at a time, each a single measured delta on production:

| arm | flag delta on production | question |
|---|---|---|
| **S1** | `--max-mamba-cache-size 64 → 320` | does the slot budget bind at all? `extra_buffer` ⇒ S = 5 slots/request ⇒ 320/5 = 64 requests ≫ `--max-running-requests 5` |
| **S2** | S1 + `--mamba-radix-cache-strategy extra_buffer → no_buffer` | S = 3 ⇒ 320/3 = 106 requests; more prefixes per slot budget |
| **S3** | `--radix-eviction-policy lru → lfu` (slots stay 64) | does the documented-for-our-shape policy move the window? |

**Hypothesis under test, stated before the numbers:** if the state cache is the binding constraint
(manuscript `MANUSCRIPT.md`:643: "the binding constraint is the state cache (max_mamba_cache_size 64),
not KV token capacity"), then the resident window must scale with the *admitted prefix count*, and
**S1/S2 should move 0.1592–0.1645 substantially while S3 should not.** If S1 does not move it, the
manuscript's C54 attribution is wrong and this card must say so rather than report three null arms
as a no-op.

## Hard bound

**70 tool calls / 900 live requests.** Live request budget: gate ≈ 6, battery 284, eviction ≈ 330,
warm-up ≈ 2 → ≈ 622 per arm. **I can afford ONE full arm**, not three. The arm to spend it on is
therefore chosen by evidence, not by order: the one whose flag delta is what the boot log says binds
(see *Decision rule*). If a variant fails to start, capture the exact error, restore, continue.

## Decision rule (recorded before any live request)

1. Read the **production boot log** and the production `/get_server_info`; resolve empirically whether
   the slot budget binds (`state slots`, `max_mamba_cache_size`, admitted concurrency). The card warns
   that two research lanes disagree — "64 is not obviously binding" vs "12 requests admitted". The
   log decides, not the card.
2. **If the slot budget binds** → the lever is the slot budget: run **S1** (and S2 only if budget
   allows it *after* S1 restores clean).
3. **If the slot budget does not bind** (production's admitted concurrency is already limited by
   `--max-running-requests 5`, and no `state slots` warning is present) → raising 64 → 320 changes
   nothing measurable, and spending the only affordable arm on it would produce a null dressed up as
   a result. Then the lever that CAN move the resident window is eviction policy, and **S3** is the
   arm that runs — with S1's non-binding finding recorded as the reason S1/S2 were not run.
4. Either way: **restore + prove the 6 baseline keys after every arm**, and never `docker rm` production.

## Write paths

`experiments/context-cache/cells/R2-SGL/**` · `state/config/r2-sgl-*.json` ·
`orchestration/handoffs/R2-SGL-CAP.json` · `orchestration/units/R2-SGL-CAP.md`

No `papers/**`, no `RUN.json`, no test edits, no Round-1 cell edits. Holds
`experiments/context-cache/.occamy.lock` for the whole live phase.

## Stop-safety precondition (found in the artefacts, must be handled before any window)

`state/config/occamy-inspect-pre.json` records **`HostConfig.AutoRemove = true`**. Production is an
`--rm` container: `docker stop` **destroys** it and `docker start` has nothing to start — the exact
defect `WIN-SGL` hit live, and the reason `variant_launcher.assert_stop_safe()` exists. Production is
also the `ExecStart` of `systemctl --user gx10-occamy-nvfp4.service`, so a container-level stop cannot
hold `:8012` free — systemd recreates it.

The window therefore runs, in this order and never another: `assert_stop_safe()` → rewrite production
to `AutoRemove=false` **preserving the argv verbatim** → `systemctl --user stop` → prove `:8012` down
→ create + start the variant → measure → `docker rm -f` the variant → `systemctl --user start` →
`prove_restore` on the six keys. A rewrite that does not preserve `Config.Cmd` byte-for-byte is a
launch defect and stops the window before anything is stopped.

## Return shape

≤10 lines: headroom, per arm the resolved strategy + slots/req + admitted concurrency, the
hit / unc-per-turn numbers, the resident ratio vs 0.1592–0.1645, and the restore-proof line.
