# U-SPCC-15 — refresh `docs/CURRENT-REPO-STATE.md`, regenerate billed-proof score

Owner: RefreshStateAndScore · 2026-11-10

## Target 1 — `docs/CURRENT-REPO-STATE.md`

Two assertions were false: it claimed `HEAD: dfba6aa`, and that `origin/main` "shares no
common ancestor with this branch". Measured truth: `HEAD` = `17182ff`, `origin/main` =
`5554d82`, merge-base = `5554d82`, so `origin/main` **is** an ancestor.

Rewrote the 17-line file in place (no banner) to state the measured graph:

|Fact|Value|
|---|---|
|branch|`research/next-candidates-2026-10-24`|
|HEAD|`17182ff`|
|backup ref|`origin/backup/screened-dirty-progress-2026-11-10-1348` = `17182ff`|
|`origin/main`|`5554d82` (ancestor; merge-base `5554d82`)|
|preservation|`9fadcc9`|
|paper-candidates merge|`afe4d78`|
|origin/main merge|`ca9d65e` → reverted by `1977d30`, repair recorded in `59c1c60`|
|vendored vLLM removal|`dfba6aa`|

Reading rule added: the work is pushed, `main` has not moved.

Note: the ticket said `ca9d65e` was "reverted by `59c1c60`"; measurement shows `59c1c60` is the
`U-SPCC-0B` record commit (3 docs files, no revert) and the revert commit itself is `1977d30`.
Both hashes are in the file with their measured roles.

Row-file paragraph removed: it was a snapshot (92 files / 7,869 rows) that no longer describes the
trees the same way and is not part of "current repo state".

## Target 2 — `experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json`

The file carried `"billed_tokens": 0` (stale, pre-scorer-fix). Regenerated with its own generator
rather than hand-edited:

```
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py \
  experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json \
  experiments/ptr-engine/measure/rows-spcc-billedproof-2026-11-10.jsonl \
  --pretty --out experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json
```

Exit code **1** — expected: the scorer exits non-zero on answer-shape checks. Regeneration
succeeded; `billed_tokens` is now `14303` and `grep -c '"billed_tokens": 0'` returns 0.

Billing block unchanged from the run the main agent measured read-only:
prompt 174047, cached 159744, uncached 13746, billed 14303 (`derived`), coverage 0.98,
billed_coverage 1.0, reconcile delta 557 vs tolerance 1740 (within), checkpoint accuracy 8/48,
fixture sha equal at run and at score (`f0a636fe…620c3`).

## Gates

`python3 tools/doc_check.py` → `OK docs clean`, exit 0.

## Constraints respected

No live model requests. No `git add/commit/push/checkout/stash`. No edits to row files,
`docs/STATE.md`, `orchestration/STATUS.md`, or `serving/`.
