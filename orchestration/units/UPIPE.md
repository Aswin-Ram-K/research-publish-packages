# Unit UPIPE — run this workspace's pipeline against the acceptance target

**Status:** done (as an honest negative result). **Tool calls:** 28. **Run budget:** 15 min; used 73 s total.
**Write paths:** `state/logs/UPIPE-*`, `orchestration/units/UPIPE.md`, `orchestration/handoffs/UPIPE.json`,
plus the pipeline's normal `state/**` and `dockets/**` outputs.

## Purpose
Run the workspace's own pipeline (`./.venv/bin/resextract run --target duval`) against the read-only
acceptance target `/home/zer0null/Duval` and report honestly what it produces.

## Result headline
**Nothing changed from the closeout.** `candidates=10 / claims=0 / evidence=0 / verdicts=0`;
**0 dockets `ready`**; **0 writes inside Duval attributable to this pipeline.**

## 1. Search health — baseline probe (3 distinct queries, verbatim)
Endpoint `http://127.0.0.1:8080` (`config/resextract.toml:9`); root `http=200` in 0.0038 s.

| Query | HTTP | results |
|---|---|---|
| `agent state kernel` | 200 (0.51 s) | **6** |
| `self-refinement LLM degradation` | 200 (0.30 s) | **0** |
| `evidence verification pipeline` | 200 (1.08 s) | **2** |

`unresponsive_engines` on every query, verbatim:
`[["brave","Suspended: too many requests"],["duckduckgo","CAPTCHA"],["google cse","Suspended: too many requests"],["mojeek","Suspended: access denied"],["qwant","CAPTCHA"]]`

**8 results across 3 queries.** HTTP 200 with mostly-empty results — the orchestrator's finding is
reproduced and slightly worse (one query returned zero). Full log: `state/logs/UPIPE-search-health.txt`.

## 2. `doctor` — verbatim
```
Occamy           core      ok      model=occamy-1.0; completion HTTP 200 (thinking=off, max_tokens=8, 252 ms)
SearXNG          core      ok      HTTP 200, results=10
crawl bridge     core      ok      HTTP 200, ok=True
graphify         core      ok      graphify 0.9.80; openai 3.26.1
docling bridge   optional  DOWN    ConnectError: [Errno 111] Connection refused (optional)
renderers        optional  ok      missing: pdflatex, pandoc, tectonic (paper dockets emit .tex + markdown)
dashboard port   optional  ok      127.0.0.1:8901 free
core 4/4 green; optional 2/3 green (docling bridge down) -> doctor: OK (exit 0)
```
**Occamy is UP** (`/v1/models` → 200; a real completion → 200 in 252 ms). `doctor` is fully green on
the search leg *because its probe query is generic* (`results=10`) — it does **not** detect the
degradation targeted queries expose. That is a blind spot worth noting.

## 3. Read-only baseline (`/home/zer0null/Duval`, HEAD `24f339c0c3994f7af5c6f505bd8b65744612f853`)
`git status --porcelain` and a named mtime sweep (`-newermt 2026-10-14T19:36:10-05:00`) were taken
**before** and **after**. The sweep was **empty both times**, and HEAD was unchanged.

## 4. Run
`timeout 900 ./.venv/bin/resextract run --target duval` → managed background job, log
`state/logs/UPIPE-run.log`. Finished in **9 s**, **exit 1**, "completed WITH DEGRADATIONS", no mass errors:
```
mine         blocked  ... producer gate: 0 model-produced candidate(s) (store producers: replay=10); mine cannot run without the model
claims       blocked  ... same gate
assess       blocked  ... same gate
lanes        ok       built 5 lane(s) from 10 candidate(s); typed 5, refused 0
materialize  skipped  no model-produced candidates ...; pass --allow-replay to build a replay-derived docket anyway
refresh      ok
```
A second, explicitly-labelled probe run with `--allow-replay` (`state/logs/UPIPE-replay.log`) did
materialize: `dockets=5, failures=0, replay_derived=True` — but all 5 run-scoped dockets are
**`status: draft`**, none `ready`. It is a **degradation**, as the CLI itself says.

## 5. The actual blocker is NOT the model endpoint
The run emits the literal string **`model endpoint DOWN (http 200)`** while the endpoint is up.
`src/resextract/run.py:353-363` (`gate_reason`) hard-codes the `model endpoint DOWN (http {status})`
prefix unconditionally. The real block is the **store producer gate**: `run.py:2008-2012` computes
`model_candidates` from the store *before any stage runs*, and `run.py:2067` blocks
`mine/claims/assess` when that list is empty. All 10 candidates have `producer='replay'`.
`./.venv/bin/resextract --help` lists `mine` as **"not implemented yet — planned for batch 2"**.
So the store can never acquire a model-produced candidate, and `evidence`/`claims`/`verdicts` can
never move off 0 — **regardless of Occamy or SearXNG**. Repairing SearXNG alone will not produce an
evidence row: the run never reaches a search-driven stage.

## 6. Containment — proven, not asserted
Final `git status --porcelain` is byte-identical to baseline (the dirty entries `M AGENTS.md`,
`M docs/COMPACTION_LOG.md`, `M guidance/codex/COMPACTION_LOG.md`, `?? .ci-trunk.txt`,
`?? .lane-j-scratch/`, `?? .relay/`, `?? .run-dashboard/`,
`?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt` were **already present at baseline** and
are the concurrent DSH Lead / Codex session's lane). Final mtime sweep: **empty**.
`/home/zer0null/.codex` was touched after start — the concurrent Codex session, not this unit.
**Writes inside Duval by pipeline: 0. By the other session during this window: 0.**

## 7. Store, read via a copy (never `immutable=1`)
`state/verify/UPIPE/{pre,post,post2}.sqlite`; `sqlite3.connect('file:...?mode=ro', uri=True)`.

| table | pre-run | post-run | post-replay |
|---|---|---|---|
| `candidates` | 10 | 10 | 10 |
| `claims` | 0 | 0 | 0 |
| `evidence` | 0 | 0 | 0 |
| `verdicts` | 0 | 0 | 0 |

`candidates` by producer: `[('replay', 10)]`. `resextract status`: `claims=0 evidence=0 verdicts=0`,
`dockets: total=2 by_freshness={'current': 2}`, all lanes `draft`.
**No verdict ever became capable of `CONFIRMS`** — with 0 claims and 0 verdicts there is nothing to confirm.

## Verdict
The pipeline runs cleanly and honestly on a degraded substrate, and its negative result is stable:
**it produces candidates, 5 lanes, and (only under `--allow-replay`) replay-derived `draft` dockets —
and zero claims, zero evidence, zero verdicts, zero `ready` dockets.** The headline is that
**Occamy's recovery changed nothing**, because the operative blocker is the producer gate plus an
unimplemented `mine` stage — not the model endpoint, and not (for this path) search.
