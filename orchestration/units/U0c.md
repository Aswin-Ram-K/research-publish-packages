# U0c — corpus-builder

**Status:** done (within bound: 22 tool calls, ~14 minutes)

## Purpose

Build the three deterministic text corpora the context-cache experiments render, from ONE
committed, seed-only builder script. Data files only; no code that talks to the model.

## Write paths (declared and observed)

- `experiments/context-cache/corpora/build_corpora.py`
- `experiments/context-cache/corpora/volatility.json`
- `experiments/context-cache/corpora/compaction.json`
- `experiments/context-cache/corpora/endtoend.json`
- `experiments/context-cache/corpora/MANIFEST.json`
- `orchestration/units/U0c.md`
- `orchestration/handoffs/U0c.json`

Not touched (mtimes unchanged): `experiments/context-cache/{client.py,runner.py,analyze.py,__init__.py,README.md}`.
No files under `src/`, `tests/`, `papers/`.

## What was built

`build_corpora.py` (79,587 bytes) writes, with `SEED = 1729`:

| corpus | schema | content |
| --- | --- | --- |
| `volatility.json` | 4 scenarios x 48 turns, `depths [2,4,8,16,32,48]`, preamble + per-turn `volatile` | E1 prefix volatility; four incidents: orders-api latency, annual-report table captions, spanq feature build + bench, SQLite/Arrow bounded backfill |
| `compaction.json` | 3 scenarios x 58 turns, `summary_hint`, `compaction_points` at 8k/16k/24k | E3 long sessions (~24.1k–25.1k est tokens); points are 0-based turn indices where cumulative est tokens (preamble included) cross each target |
| `endtoend.json` | 2 scenarios x 60 turns, last turn is the final user question, `gold_answer` + `gold_turn_index` | E5; gold strings `0042_rename_fingerprint` (turn 17) and `anchor_mode=bbox_y1` (turn 23), each asserted to occur exactly once |

Every turn carries `est_tokens = max(1, (len(text)+3)//4)`, the same estimator as
`resextract.context.default_est_tokens`. Turn text is the stable content shared by all render
policies; the `volatile` dict (`step`, `elapsed_ms`, `task_id`, `turn_ts`) is kept out of the
text because placement is `resextract.context.render`'s decision.

Content is composed from a seeded fragment bank per domain (4 themes: api/docs/rust/ingest) with
per-turn slot values (`rng = random.Random(SEED*100003 + off*1009 + i)`), so every turn is distinct
text while staying inside one coherent incident and one decision-log style.

## Evidence

Determinism — two builds into `experiments/context-cache/corpora/.det_a` and `.det_b`,
`cmp` per file + `diff -r` clean, identical sha256 pairs:

```
6e2fe8979f67e1fe762c3daaa0ff53c30bd59c0d607b796d503e7d710e2bc7db  volatility.json
d702f8f4af2f9d34f68fbca3aa2a096fc8b9cb5f7f7fb32f282c869cbd1f2961  compaction.json
f853d3ea1ecda7e6fd11e6b732e55493725041acb8bc741abf539aeadcf79ff2  endtoend.json
```

(identical in `.det_a/` and `.det_b/`; temp dirs removed after the check)

Structural check (independent of the builder, re-parses the written JSON):

```
MANIFEST: 3 sha256 + byte sizes match disk; total est tokens 206981
all corpora: parse OK, no empty turns, est_tokens consistent, volatile+turn text unique
volatility: 4 x 48 turns, depths [2,4,8,16,32,48], preamble 818-863 est, assistant turns 378-447
compaction C1: 58 turns, total 25092 est, points [(8000,17,8343),(16000,36,16317),(24000,55,24282)] summary_hint 188 est
compaction C2: 58 turns, total 24383 est, points [(8000,17,8139),(16000,37,16253),(24000,57,24383)] summary_hint 178 est
compaction C3: 58 turns, total 24340 est, points [(8000,17,8092),(16000,37,16249),(24000,57,24340)] summary_hint 171 est
endtoend E1: 60 turns, final role user, gold='0042_rename_fingerprint' occurrences=1 at turn 17
endtoend E2: 60 turns, final role user, gold='anchor_mode=bbox_y1' occurrences=1 at turn 23
```

## Deviations / limits

- Compaction totals are 24,340–25,092 est tokens (target ~24,000); turn counts are 58, not 60,
  because the 24k target is met at 58 turns with the authored turn length.
- Assistant turns are 378–447 est tokens (requested ~300–600); user task turns are 300–339;
  the E5 final question is ~44 est tokens, which is inherent to a one-line reviewer question.
- `summary_hint` is 171–188 est tokens (~200 requested).
- The `volatile` values are stable strings generated arithmetically; they change every turn but
  do not appear in turn text (by design, see above).

## Next-unit hint

`U1`/runner can load these with `json.load`; map `turns[i]["text"]` -> `Turn.text` and
`turns[i]["volatile"]` -> `Turn.volatile`; `scenario["preamble"]` -> `Case.preamble`. For E3 the
`summary_hint` is the canned summariser input; `compaction_points[].at_turn` is the turn index the
compaction policy should fire at (0-based, preamble counted in the cumulative).
