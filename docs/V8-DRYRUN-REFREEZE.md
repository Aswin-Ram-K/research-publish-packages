# V8 dry-run re-freeze — manifest provenance vs the runner's actual wall

**Unit:** `V8-DRYRUN-REFREEZE` · **Offline:** zero requests · **Head:** f17663d
**Measurement:** [`../experiments/ptr-engine/measure/V8-DRYRUN-REFREEZE.json`](../experiments/ptr-engine/measure/V8-DRYRUN-REFREEZE.json)

## Why

`RUNNER-WALL-KEY` fixed `run_longrun.py` to resolve each arm's wall from
`wall_tokens_by_arm` and refuse the top-level fallback. v8 declares both:
`wall_tokens = 3838` (a dead legacy value, *below its own first prompt* at 3848) and
`wall_tokens_by_arm = 10616` for all four arms. The pre-freeze manifests still recorded
`engine_flags.design_cap_tokens = 3838`, so the grid's provenance named a cap the runner
never used.

## Inventory

| manifest | design_cap_tokens | state |
|---|---|---|
| `archive/pre-wallkey/dryrun-LR-01-lease-reopen-r1.json` | 3838 | stale |
| `archive/pre-wallkey/dryrun-LR-01-pointer-stable-r1.json` | 3838 | stale |
| `archive/pre-wallkey/dryrun-LR-01-transcript-compact-r1.json` | 3838 | stale |
| `archive/pre-wallkey/dryrun-LR-01-transcript-grow-r1.json` | 65536 | mislabeled: fixture sha `fc44cb20…` is `/tmp/red.json`, not v8's `0804b515…` |
| `dryrun-LR-01-{transcript-grow,transcript-compact,pointer-stable,lease-reopen}-r1.json` | 10616 | current (re-frozen 2026-10-26T17:29:07Z) |

Stale manifests were **moved**, never deleted: `manifests/archive/pre-wallkey/`.

## Dry run

```
cell.py --dry-run … --turns 48 --reps 1 --hypothesis H2 --arm transcript-grow   exit 0
runner --dry-run --arms <all four> --reps 1                                    exit 0
G1 allow computed=1,154 / limit=4,320 requests · G2 allow 2,880 s / 3,600 s · G3 allow n=48 ≥ 1
```

No network: `sys.addaudithook` over `socket.*`, `urllib.Request`, `http.client.connect`
around an in-process invocation showed **0 events**; the runner prints
`(offline: zero requests; exact request bodies under /tmp/longrun-previews/)`.
`unshare -n` is unavailable here (`Operation not permitted`).

## Finding

**Yes** — the grid would previously have been graded against manifests quoting **3838**
(and, for `transcript-grow`, **65536**) while the runner ran at **10616**. Three of the
four pre-freeze manifests disagreed with the runner by 6,778 tokens; the fourth
disagreed by 54,920.

## Guard

`experiments/ptr-engine/longrun/tests/test_manifest_cap_consistency.py` fails any live
manifest naming `LR-01.v8` (or carrying v8's sha) whose `design_cap_tokens != 10616`,
and requires at least one such manifest to exist. Red→green: 2 passed → reinstating the
archived 65536 manifest 1 failed / 1 passed → removed, 2 passed.
