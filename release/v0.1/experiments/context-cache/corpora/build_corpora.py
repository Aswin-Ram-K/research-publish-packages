#!/usr/bin/env python3
"""Deterministic corpus builder for the context-cache experiment.

Builds three text corpora consumed by the cache-reuse harness:

* ``volatility.json`` -- E1: 4 agent sessions x 6 render depths (2..48).
* ``compaction.json`` -- E3: 3 long sessions with compaction points at
  ~8k / ~16k / ~24k estimated tokens and a canned summary hint per session.
* ``endtoend.json``   -- E5: 2 sessions of 60 turns ending in a question whose
  answer appears verbatim in exactly one earlier turn.

Everything is a pure function of ``SEED``: no wall clock, no unseeded
randomness, no dependence on filesystem order or dict iteration order.
Running the script twice produces byte-identical files; ``MANIFEST.json``
records the sha256 and byte size of each corpus.

The turn text is the *stable* content shared by every render policy.  The
per-turn ``volatile`` mapping is deliberately kept out of the text: where
those values are interpolated is the renderer's decision
(``resextract.context.render``), which is the variable E1 measures.

Usage::

    python3 build_corpora.py                # writes next to this script
    python3 build_corpora.py --out DIR      # writes into DIR (for diffing)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
from typing import Any

SEED = 1729
BUILDER = "build_corpora.py"
DEPTHS = [2, 4, 8, 16, 32, 48]
VOLATILITY_TURNS = 48
COMPACTION_TURNS = 58
ENDTOEND_TURNS = 60

ESTIMATOR = "max(1, (len(text) + 3) // 4)  # chars//4; identical to resextract.context.default_est_tokens"

PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")


def est_tokens(text: str) -> int:
    """Same estimator the experiment core uses, so budgets line up."""

    return max(1, (len(text) + 3) // 4)


def fill(template: str, slots: dict[str, Any]) -> str:
    """Substitute ``{name}`` placeholders; raise on an unknown name."""

    return PLACEHOLDER.sub(lambda m: str(slots[m.group(1)]), template)


def pick(seq: list[Any], i: int) -> Any:
    return seq[i % len(seq)]


SHARED_SYSTEM = """You are an autonomous software agent working inside a checked-out repository on a Linux box. You have a shell, a file editor, and a test runner. You have no access to production systems and no network egress beyond the package mirror already configured in the image. Work in small, verifiable steps: reproduce before you fix, read the code you are about to change, and prefer the smallest patch that makes a failing check pass without weakening it.

Ground rules:
- Every claim you make about behaviour must come from a command you ran in this session. Quote the command and the relevant output lines.
- Never edit tests, fixtures, or gold files to make a failure disappear. If a fixture is wrong, say so and prove it separately, in its own step.
- Keep a running decision log in the reply: what you tried, what you observed, what you concluded, and what you will do next.
- State file paths as repository-relative paths, with a line number when you cite code.
- Do not touch generated artefacts, lockfiles, or vendored sources, and do not reformat files you are not fixing.
- If a step needs a human decision -- a schema change, a dependency major bump, a data backfill -- stop and ask instead of guessing.
- Report uncertainty explicitly. "I did not verify X" is a valid and expected sentence.
- At most one tool call per reasoning step. Batch independent reads, but never batch commands that mutate state.
- When you finish, leave the tree in a state where the next agent can rerun your last command and get the same result.
"""

BRIEFS: dict[str, str] = {
    "api": """Repository: `orders-api`, a FastAPI service in front of a pricing service. It accepts an order, validates it with pydantic, writes an idempotency fingerprint to Redis, and returns 202 with a request id. The public response schema is frozen: downstream clients read `order_id`, `status`, and `request_id`.

The regression under investigation: p95 on `POST /v1/orders` rose from about 180 ms to about 900 ms in release 2026.10.3. That release contained two dependency changes (pydantic 2.7.4, redis-py 5.0.7) and one behavioural change (the retry wrapper now re-validates the payload on each attempt). Error rate is flat and measured Redis latency is unchanged, so this is not saturation.

Where to look: `src/api/handlers/orders.py` (request path), `src/api/schemas/order.py` (validation models), `src/api/middleware/retry.py` (retry with backoff, budget 500 ms), `src/api/clients/redis_client.py` (idempotency lookup), `src/api/telemetry/metrics.py` (prometheus counters), `scripts/replay.py` (offline replay of recorded traffic).

What you can run: `pytest -q` for the unit suite; `python -m scripts.replay --fixture fixtures/orders_2026_10.jsonl --limit 400` for the replay; `python -m scripts.latency_report --window 1h` for the in-process histogram. There is no production access; the replay fixture is the only traffic sample.

Rules of engagement: do not change the response schema, do not edit fixtures, do not downgrade a dependency without a measurement. Prefer one minimal patch with a regression test. Record each decision with the file and line you relied on.""",
    "docs": """Repository: `extract-pipeline`, the document-extraction service behind the research indexer. It parses PDFs with docling, normalises cells, attaches captions to tables, and writes a JSON table file that the labelling step compares against gold.

The defect: on the 2025 annual report (`fixtures/annual_report_2025.pdf`), the caption `Revenue by segment` is attached to table 6 instead of table 7 on page 12, and three other two-column pages show the same one-table shift. Gold (`tests/gold/tables_2025.json`) records the correct owner. The likely mechanism is reading order: docling emits blocks in column-major order on two-column pages, so "the next block after the table" is the caption of the wrong table.

Where to look: `pipeline/table_extract.py` (block walk and caption attach), `pipeline/anchors.py` (anchor policy, currently page order), `pipeline/docling_bridge.py` (docling document to blocks), `pipeline/normalise.py` (cell grid and merged headers), `pipeline/diff_tables.py` (gold diff).

What you can run: `python -m pipeline.extract --doc fixtures/annual_report_2025.pdf --pages 10-14`; `pytest -q tests/test_table_extract.py`; `python -m pipeline.diff --gold tests/gold/tables_2025.json --pages 10-14`; `python -m pipeline.ocr_probe --page 12` (OCR is off by default -- probe before blaming it).

Rules of engagement: the gold file and the PDF are read-only. A fix that only special-cases page 12 will be rejected. Any change to anchor policy must be recorded with the setting name and the pages it was tested on. Re-extraction must be deterministic: same input, same byte output.""",
    "rust": """Repository: `spanq`, a Rust CLI that scans text for token spans and prints offsets as JSON lines. It builds with no default features; the `metrics` feature adds per-batch counters and a JSON export path.

The failure: `cargo test --features metrics` stopped compiling after the serde bump to 1.0.204. The first error is in `src/metrics.rs` (a missing `Serialize` derive), but the same feature changes the borrow pattern in `src/tokenizer/mod.rs`, so a one-line derive may not be the whole story. The default build is still green, which is why CI did not catch it: CI only builds default features.

Where to look: `src/tokenizer/mod.rs` (span scan and buffer reuse), `src/cli/args.rs` (clap definitions behind the feature), `src/metrics.rs` (counters and export), `tests/cli_smoke.rs` (golden output), `benches/tokenize.rs` (criterion, sample size 20), `Cargo.toml` (feature flags).

What you can run: `cargo test --features metrics`; `cargo clippy --all-targets -- -D warnings`; `cargo bench --bench tokenize -- --sample-size 20`; `cargo tree -e features -i metrics`. The bench is noisy on this box: treat a change under 5% as noise, and compare medians over at least three runs.

Rules of engagement: do not add dependencies, do not weaken the feature gate to make the build pass, and do not silence clippy with `allow` attributes. The tokenizer's output format is a contract with downstream tooling: byte-identical output on the smoke fixture.""",
    "ingest": """Repository: `lakehouse-ingest`, a batch service that copies rows from an upstream Arrow source into a local SQLite state database and then into Parquet. It is the only writer for the `orders` table, so resumability and idempotency are its two hard requirements.

The failure: the 3.2M-row orders backfill dies near row 1.9M with `MemoryError`. The writer commits once per batch of 5,000 rows, but the reader materialises the whole Arrow table before yielding anything, so peak RSS tracks the table size rather than the batch size. The state table also lacks a row fingerprint column, so a resumed run re-inserts rows it already wrote.

Where to look: `ingest/batch_reader.py` (source iteration), `ingest/sqlite_writer.py` (executemany and commit), `ingest/config.py` (batch size, WAL settings), `ingest/migrations/` (state schema), `ops/backfill.py` (resume cursor), `ingest/profile.py` (row-count and RSS probe).

What you can run: `python -m ingest.run --source orders --batch-size 5000`; `pytest -q tests/test_batch_reader.py`; `python -m ops.backfill --table orders --dry-run`; `python -m ingest.profile --rows 3200000` (synthetic rows, no upstream needed). The dry run is the safe way to measure: it does not write Parquet.

Rules of engagement: schema changes must be a numbered migration, never an in-place `ALTER` in application code. Duplicate fingerprints must be ignored, not merged. The dry run's row count must equal the full run's, and the cursor must survive a kill -9 at any batch boundary.""",
}

VOLATILITY_SPECS: list[dict[str, str]] = [
    {
        "id": "S1",
        "theme": "api",
        "goal": """Session goal: reproduce the p95 regression on POST /v1/orders from the recorded replay fixture, narrow it to a single call path, and fix it without changing the public response schema. This is the first pass on the incident; the handover must state exactly which command produced each timing you quote.""",
        "task": """We shipped orders-api 2026.10.3 on Tuesday. p95 on POST /v1/orders went from about 180 ms to roughly 900 ms, and the 5xx rate is flat, so it is not saturation. The only changes in the release were the pydantic 2.7 bump and redis-py 5.0.7. Reproduce it locally from fixtures/orders_2026_10.jsonl, identify the single slow path, and propose the smallest fix. Do not change the endpoint's response schema; downstream clients depend on it. Quote the command behind every number.""",
    },
    {
        "id": "S2",
        "theme": "docs",
        "goal": """Session goal: find why table captions in the 2025 annual report are attached to the wrong table, and make caption association deterministic on the affected two-column pages. The deliverable is a root cause plus a re-extraction of pages 10-14 that matches gold, not a page-specific patch.""",
        "task": """The Q4 extraction run for fixtures/annual_report_2025.pdf attached the caption `Revenue by segment` to table 6 instead of table 7 on page 12, and three other pages in the same document show the same one-table shift. Gold (tests/gold/tables_2025.json) says table 7 owns that caption. I need the root cause and a fix that generalises to two-column pages; re-extracting pages 10-14 must match gold exactly. Do not edit the gold file or the PDF.""",
    },
    {
        "id": "S3",
        "theme": "rust",
        "goal": """Session goal: get `cargo test --features metrics` compiling again without weakening the feature gate, then confirm the tokenizer benchmark did not regress. Both the default build and the feature build must stay green, and the CLI's JSON output must remain byte-identical on the smoke fixture.""",
        "task": """spanq stopped compiling with --features metrics after the serde bump. The first error is in src/metrics.rs and looks like a missing derive, but the feature also changes the borrow pattern in src/tokenizer/mod.rs, so a one-line derive may not be the whole story. Get the feature build green, keep the default build green, and run benches/tokenize.rs before and after. Do not add dependencies and do not add allow attributes to silence clippy.""",
    },
    {
        "id": "S4",
        "theme": "ingest",
        "goal": """Session goal: stop the ingest job from exhausting memory during the 3.2M-row orders backfill without changing the on-disk Parquet schema or losing idempotency. The dry run and the resumed run must agree on row count, and a kill at a batch boundary must not duplicate rows.""",
        "task": """The orders backfill dies around row 1.9M with a MemoryError. The writer batches at 5,000 rows but the reader materialises the whole Arrow table first. I need a bounded-memory path that commits once per batch, keeps duplicate fingerprints ignored, and can resume from the recorded cursor. The dry run must show the same row count as the full run, and a kill at a batch boundary must not lose or duplicate rows.""",
    },
]

COMPACTION_SPECS: list[dict[str, str]] = [
    {
        "id": "C1",
        "theme": "api",
        "goal": """Session goal: run the full latency investigation on the orders-api retry path -- reproduce from the replay fixture, localise, patch, and verify -- and record each decision so a later reader can resume from a summary of the head of this transcript. The session is expected to run long; every turn should carry enough state to survive summarisation.""",
        "task": """Continue the orders-api latency investigation. Release 2026.10.3 regressed p95 from about 180 ms to about 900 ms; the retry wrapper and the pydantic bump are both suspects. Work from fixtures/orders_2026_10.jsonl, keep a decision log, and do not change the response schema. This session is expected to run long: leave enough state in each turn that the work can be resumed from a summary of the earlier turns, including the open questions and the exact commands that produced each number.""",
    },
    {
        "id": "C2",
        "theme": "docs",
        "goal": """Session goal: a full document-extraction repair across the 2025 annual report -- locate the caption-ordering defect, fix the anchor rule, re-extract the affected pages, and prove the table diff against gold. The session should end with a stated anchor rule that a later reader can re-run from a summary.""",
        "task": """We are repairing the annual-report extraction. The caption shift on page 12 is one symptom; I expect the same defect on every two-column page in the 2025 report. Fix the caption anchor rule, re-extract the affected pages, and diff against tests/gold/tables_2025.json. Record the decision about bbox anchoring: a later reader should be able to re-run the extraction from a summary of this session. Do not touch the gold file or the PDF, and do not change OCR settings unless you can show the OCR text is the cause.""",
    },
    {
        "id": "C3",
        "theme": "ingest",
        "goal": """Session goal: bound the memory of the orders backfill end to end -- profile the reader, change the batching contract, migrate the state table, and verify resumability on 3.2M rows. The session should end with a migration filename and a cursor contract that a later reader can resume from.""",
        "task": """The 3.2M-row orders backfill OOMs near row 1.9M. This session should end with a bounded-memory reader, a writer that commits once per batch, and a resumable cursor. A schema change is allowed but must be a numbered migration; the current state table lacks the row fingerprint column, which is why duplicates are re-inserted on resume. Keep a decision log and leave the exact migration filename in the transcript, because the reviewer will ask for it.""",
    },
]

ENDTOEND_SPECS: list[dict[str, Any]] = [
    {
        "id": "E1",
        "theme": "api",
        "goal": """Session goal: a compact end-to-end incident on orders-api -- reproduce the latency regression, find the retry-path cause, record the schema decision (including the migration's exact filename), ship the fix, and answer a final reviewer question about what changed.""",
        "task": """Incident review for orders-api 2026.10.3. Start from the replay fixture, find why p95 tripled, and fix it. Along the way record the schema decision: the idempotency key column gets renamed by a migration, and the migration's exact filename matters because the reviewer will ask for it. Keep the response schema stable and quote the command behind every number.""",
        "gold_answer": "0042_rename_fingerprint",
        "gold_turn": 17,
        "final_question": """Reviewer question: which migration renamed the idempotency_key column, and what is the new column called? Answer with the migration's exact filename and the new column name.""",
    },
    {
        "id": "E2",
        "theme": "docs",
        "goal": """Session goal: extract the 2025 annual report correctly end to end and settle the caption-anchor rule, so a later reader can answer which anchor mode the pipeline now uses. The reviewer will ask for the exact setting name, so record it in the transcript.""",
        "task": """Run the 2025 annual report extraction from scratch. Caption association is wrong on two-column pages; fix it, prove the fix against gold, and record the anchor mode you settle on -- the reviewer will ask for the exact setting name. No edits to the gold file or the PDF, and no OCR changes unless you can show the OCR text is the cause.""",
        "gold_answer": "anchor_mode=bbox_y1",
        "gold_turn": 23,
        "final_question": """Reviewer question: which anchor_mode does the extractor use now for caption association, and which field does it key on? Answer with the exact setting and value.""",
    },
]

THEMES: dict[str, dict[str, Any]] = {}

THEMES["api"] = {
    "id": "api",
    "repo": "orders-api",
    "brief": BRIEFS["api"],
    "codepaths": [
        "src/api/handlers/orders.py",
        "src/api/schemas/order.py",
        "src/api/middleware/retry.py",
        "src/api/clients/redis_client.py",
        "src/api/telemetry/metrics.py",
        "src/api/settings.py",
        "scripts/replay.py",
    ],
    "paths": [
        "src/api/handlers/orders.py",
        "src/api/schemas/order.py",
        "src/api/middleware/retry.py",
        "src/api/clients/redis_client.py",
        "src/api/telemetry/metrics.py",
        "tests/test_orders_flow.py",
        "src/api/settings.py",
        "scripts/replay.py",
    ],
    "cmds": [
        "pytest -q tests/test_orders_flow.py -x",
        "python -m scripts.replay --fixture fixtures/orders_2026_10.jsonl --limit 400",
        "pytest -q tests/test_retry_middleware.py -k backoff",
        "python -m scripts.replay --profile --limit 200",
        "alembic upgrade head",
        "python -m scripts.latency_report --window 1h",
    ],
    "tests": [
        "test_create_order_returns_202",
        "test_retry_budget_bounds_attempts",
        "test_idempotent_replay_returns_same_order",
        "test_validation_error_names_offending_field",
        "test_redis_timeout_maps_to_503",
    ],
    "funcs": [
        "create_order",
        "validate_payload",
        "retry_with_backoff",
        "fingerprint_request",
        "record_latency",
        "load_idempotency_key",
    ],
    "fields": [
        "items.0.quantity",
        "customer.email",
        "idempotency_key",
        "retry_after",
        "X-Request-Id",
        "total_cents",
    ],
    "errs": [
        """E   pydantic_core._pydantic_core.ValidationError: 2 validation errors for OrderCreate
items.0.quantity
  Input should be a valid integer, got '3x' [type=int_parsing, input_value='3x', input_type=str]
customer.email
  value is not a valid email address: The part after the @-sign is not valid. [type=value_error, input_value='ana@exmaple', input_type=str]""",
        """FAILED tests/test_orders_flow.py::test_retry_budget_bounds_attempts - AssertionError: expected 3 calls to retry_with_backoff, saw 6""",
        """Traceback (most recent call last):
  File "src/api/middleware/retry.py", line 88, in retry_with_backoff
    response = call()
  File "src/api/clients/redis_client.py", line 41, in get_idempotency_key
    return self._client.get(key)
redis.exceptions.TimeoutError: Timeout reading from socket""",
        """E   TypeError: OrderCreate.validate() takes 2 positional arguments but 3 were given""",
    ],
    "errtypes": ["ValidationError", "redis.exceptions.TimeoutError", "TypeError", "KeyError"],
    "deps": ["pydantic 2.7.4", "redis-py 5.0.7", "fastapi 0.111.0", "httpx 0.27.0"],
    "vers": ["2.7.4", "5.0.7", "0.111.0"],
    "metrics": ["p95 latency", "5xx rate", "idempotency hit ratio", "retry count"],
    "beats": ["Reproduce", "Isolate", "Hypothesise", "Patch", "Verify", "Harden"],
    "notes": [
        "Same failure every time: the replay fixture is deterministic once the clock is pinned.",
        "Bisecting the request path; only one branch reaches Redis on a retry.",
        "Writing both competing explanations down before measuring either of them.",
        "Minimal change, behind the existing flag, with a regression test attached.",
        "Replay, unit suite, and latency histogram must agree before the patch counts.",
        "Removing the fixture-only shortcut and documenting the budget arithmetic.",
    ],
    "tool": [
        """`{cmd}` exited {rc} after {ms} ms:
```
{err}
```
{nfail} of {nruns} replays fail the same way, and the slowest request takes {ms2} ms against the {budget} ms budget.""",
        """Profiled {nruns} replays with cProfile. {pct}% of wall time sits in `{func}`, which is entered {count} times per request at `{path}`:{line}. The top three frames are all inside the idempotency lookup, not in the handler.""",
        """Captured one request end to end:
```
POST /v1/orders -> 202 in {warm_ms} ms  request_id={req}
GET  /v1/orders/{oid} -> 500 in {cold_ms} ms  request_id={req2}
redis GET idempotency -> {ms} ms, 1 row
```
The second call re-enters the retry wrapper and hits Redis again instead of the memoised key.""",
        """Working diff touches {nfiles} file(s); the behavioural hunk is in `{path}` around line {line}:
```diff
-    {old}
+    {new}
```
`{cmd2}` still passes {count} tests, so the old branch was not load-bearing.""",
        """Counted retries in the {window} window from the metrics endpoint: {count} attempts, {count2} of them retried, median gap {gap_med} ms, max {gap_max} ms. The counter in `{func}` increments once per attempt, not once per request.""",
        """Reproduced on a clean checkout with `{cmd}`:
```
{err3}
```
The failure appears {count} times in {nruns} replays and disappears when `{field}` is pinned to {val} in the fixture, which is the lever I will use to bisect.""",
    ],
    "analysis": [
        """Two candidate causes remain: the retry wrapper re-validates on every attempt, or the Redis client opens a connection per lookup. The timing split -- {pct}% of the delta inside `{func2}` -- favours re-validation, but connection churn is not excluded yet, so the next measurement counts opens.""",
        """Reading `{path}`:{line}, the code catches `{errtype}` but not `{errtype2}`. A validation failure is therefore retried {count} times before it surfaces, which is why `{test}` asserts {count2} calls and the replay shows {count3}. The test is right; the wrapper is too broad.""",
        """This is not a handler regression: the handler itself accounts for {handler_ms} ms. The remaining {remain_ms} ms is spent in `{func}`, which pydantic 2.7 calls with a different argument shape after the upgrade that moved {dep}. The schema is fine; the call site is not.""",
        """The 503 mapping in `{path}` is correct, but it drops `{field}`. A client cannot correlate a retry with the original attempt, which explains why the replay fixture double-counts requests instead of replaying them idempotently.""",
        """Budget arithmetic: {count} attempts at roughly {attempt_ms} ms each, on top of the handler's {handler_ms} ms, is the same order as the {budget} ms budget; raising the budget would hide the regression rather than fix it. The honest fix makes the per-attempt cost constant and caps attempts at {count2}.""",
    ],
    "action": [
        """Patch plan: memoise the validated payload keyed by `{field}` so retries reuse it, and keep the diff inside `{path}`. Then rerun `{cmd}` and expect the attempt count to drop from {count} to {count2}.""",
        """Decision recorded in `docs/decisions/0007-retry-budget.md`: the retry budget stays at {budget} ms, the backoff base is {attempt_ms} ms, and jitter is disabled under tests so `{cmd2}` is reproducible.""",
        """Next check: add a regression test asserting {count} attempts and the exact `{field}` value, then run `{cmd}` against {fixture} for {nruns} iterations. If it fails once, the fix is not done.""",
        """Verification gate: p95 must be at most {baseline2} ms and the 5xx rate zero over the {window} window before I touch `{path3}`. Until then the change stays behind {flag}.""",
    ],
    "detail": [
        """Turn-local note: fixture row {count} is the one that reproduces; the rows before it are warm-cache noise and should not be quoted as evidence.""",
        """Environment: CPython 3.12.4, uv 0.4.18, {dep}; the replay pins the clock so timings are comparable across runs.""",
        """Sanity check: `git diff --stat` shows {nfiles} file(s) changed and no lockfile churn; the virtualenv carries the same {dep} as CI.""",
    ],
    "closer": [
        """State after this step: attempt {attempt} of {attempts}, no unanswered dependency question, {nfiles} file(s) modified in total.""",
        """Open question I am not guessing at: whether `{field}` can be absent in production traffic. The fixture always sets it, so I will check the recorded headers next.""",
        """Nothing here needs a human decision yet; the next step is reversible and runs offline. Test execution this step: {ms} ms.""",
    ],
    "extras": {
        "old": 'key = payload.get("idempotency_key")',
        "new": "key = fingerprint_request(payload)",
        "fixture": "fixtures/orders_2026_10.jsonl",
        "flag": "ORDERS_FAST_PATH",
        "scope": "src/api",
        "baseline": "180",
        "baseline2": "240",
        "budget": "500",
        "window": "1h",
        "val": '"ORD-0"',
        "commit": "a91f3c2",
        "sha": "9f2c1ab",
        "branch": "fix/retry-budget",
        "req": "req-7f21",
        "req2": "req-7f22",
        "oid": "ord_88213",
    },
}

THEMES["docs"] = {
    "id": "docs",
    "repo": "extract-pipeline",
    "brief": BRIEFS["docs"],
    "codepaths": [
        "pipeline/table_extract.py",
        "pipeline/anchors.py",
        "pipeline/docling_bridge.py",
        "pipeline/normalise.py",
        "pipeline/diff_tables.py",
    ],
    "paths": [
        "pipeline/table_extract.py",
        "pipeline/anchors.py",
        "pipeline/docling_bridge.py",
        "pipeline/normalise.py",
        "tests/test_table_extract.py",
        "pipeline/diff_tables.py",
        "fixtures/annual_report_2025.pdf",
        "pipeline/ocr_probe.py",
    ],
    "cmds": [
        "python -m pipeline.extract --doc fixtures/annual_report_2025.pdf --pages 10-14",
        "pytest -q tests/test_table_extract.py -x",
        "python -m pipeline.diff --gold tests/gold/tables_2025.json --pages 10-14",
        "python -m pipeline.ocr_probe --page 12",
        "python -m pipeline.bench --repeat 5",
        "python -m pipeline.extract --doc fixtures/annual_report_2025.pdf --pages 10-14 --anchor bbox",
    ],
    "tests": [
        "test_caption_attached_to_own_table",
        "test_two_column_reading_order",
        "test_merged_header_cells",
        "test_page_number_offset",
        "test_empty_table_skipped",
    ],
    "funcs": [
        "extract_tables",
        "attach_captions",
        "normalise_cells",
        "page_blocks",
        "match_gold",
    ],
    "fields": [
        "caption_text",
        "table.bbox.y1",
        "page_index",
        "column_index",
        "row_span",
        "cell_grid",
    ],
    "errs": [
        """AssertionError: table 7 caption 'Revenue by segment' was attached to table 6 (page 12); expected owner table 7 (bbox.y1=418.2)""",
        """E   IndexError: list index out of range
pipeline/table_extract.py:214: in attach_captions
    caption = blocks[i + 1].text""",
        """AssertionError: reading order mismatch on page 12: got [col1, col2, col1], expected [col1, col1, col2]""",
        """ValueError: cannot normalise table with 0 parsed cells (page 13, bbox=(72.0, 96.5, 540.1, 702.8))""",
    ],
    "errtypes": ["AssertionError", "IndexError", "ValueError", "KeyError"],
    "deps": ["docling 2.31.0", "pdfplumber 0.11.2", "pypdfium2 4.30.0", "tabulate 0.9.0"],
    "vers": ["2.31.0", "0.11.2", "4.30.0"],
    "metrics": ["cell F1", "table count", "caption accuracy", "pages/min"],
    "beats": ["Reproduce", "Inspect", "Localise", "Patch", "Re-extract", "Harden"],
    "notes": [
        "The shift is deterministic: same page, same wrong owner, every run of the extractor.",
        "Reading the block emission order around page 12 before forming a theory.",
        "The defect is in caption ownership, not in cell parsing or OCR.",
        "A spatial rule replaces the page-order assumption; gold stays read-only.",
        "Re-extraction over pages 10-14 must match gold before the fix is called done.",
        "Extending coverage to every two-column page in the document, then documenting the rule.",
    ],
    "tool": [
        """`{cmd}` exited {rc} after {ms} ms:
```
{err}
```
{nfail} of {nruns} pages show the same one-table shift; on page {page} the caption lands on table {table} instead of table {table2}.""",
        """Dumped the block order around page {page}:
```
block 41  table   bbox=(72.0, 96.5, 540.1, 402.8)
block 42  text    "Revenue by segment"   y1={y1}
block 43  table   bbox=(72.0, 448.0, 540.1, 702.8)
```
The caption sits between two tables, so "next block" is ambiguous without a spatial rule.""",
        """Re-extracted pages {page}-{page2}:
```
tables written: {count}
captions attached: {count2}
gold diff: {nfail} mismatch(es)
```
Every mismatch is a caption whose owning table is one emission block later than the caption's block.""",
        """Working diff touches {nfiles} file(s); the behavioural hunk is in `{path}` around line {line}:
```diff
-    {old}
+    {new}
```
`{cmd2}` still reports {count} tables, so the change does not drop output.""",
        """OCR probe on page {page}: {count} text blocks, mean confidence {ocr_conf}%, and the caption string is recovered cleanly. OCR is not the cause of the shift -- the block geometry is.""",
        """Compared two anchor rules over pages 10-14:
```
anchor=page_order   caption_accuracy={acc_before}%  ({nfail}/{count} wrong)
anchor=bbox_y1      caption_accuracy={acc_after}% ({nfail2}/{count} wrong)
```
The bbox rule wins on every page that has two columns and ties on single-column pages.""",
    ],
    "analysis": [
        """Docling emits blocks in column-major order. On page {page} the right column is emitted after the left column, so `blocks[i + 1]` after table {table} is the caption of table {table2}. The mechanism is reading order, not caption detection: the caption text itself is parsed correctly.""",
        """The gold file says table {table} owns the caption on page {page}, and the caption's y1 is {y1} while table {table} ends at y1={y2}. The vertical gap is {gap} pt, smaller than the gap to table {table2} ({gap2} pt). Geometry alone picks the right owner; the code never looks at geometry.""",
        """This is a two-column-only defect. On the single-column pages 8 and 9 the page-order rule and the bbox rule agree, which is why the unit suite is green: every fixture except `fixtures/annual_report_2025.pdf` is single-column.""",
        """`pipeline/table_extract.py` line {line} is the whole bug: `caption = blocks[i + 1].text` assumes the next block in emission order belongs to the table just read. The function has no access to the table's bbox, so the fix must pass the table record down or re-derive it in `pipeline/anchors.py`.""",
        """Re-extraction cost is bounded: {count} tables over 240 pages at {ms} ms per page is about {sec} s, so a full verification run is cheap enough to do before and after the patch. That removes the temptation to validate on page {page} only.""",
    ],
    "action": [
        """Patch plan: change `attach_captions` to take the table record and select the nearest caption block by `table.bbox.y1`, then re-extract pages {page}-{page2} and diff against gold. Expect {count} mismatches to fall to zero.""",
        """Decision recorded in `docs/decisions/0012-caption-anchor.md`: caption ownership is decided by vertical proximity to the table's own bbox, not by document order. The setting name and value are recorded there; page order remains the fallback for single-column pages.""",
        """Next check: extend `tests/test_table_extract.py` with a two-column fixture that has two tables and one caption, and assert the caption's owner by table id. Then run `{cmd}` over pages 10-14 for {nruns} repetitions to confirm determinism.""",
        """Verification gate: all {count} extracted tables on pages 10-14 must match gold byte for byte, and `{cmd2}` must report zero mismatches. Until then the change stays behind {flag}.""",
    ],
    "detail": [
        """Turn-local note: on page {page} the caption sits {gap} pt below table {table} and {gap2} pt above table {table2}; the ambiguity is geometric, not a parsing artefact.""",
        """Environment: docling 2.31.0, pdfplumber 0.11.2, CPython 3.12.4; the extractor runs with OCR disabled unless --ocr is passed, and the gold file was produced with OCR disabled.""",
        """Sanity check: `git diff --stat` shows {nfiles} file(s) changed and no lockfile churn; `{cmd2}` reports the same table count as the pre-patch run.""",
    ],
    "closer": [
        """State after this step: pages {page}-{page2} re-extracted, {count} tables compared, {nfail} mismatch(es) remaining, gold file untouched.""",
        """Open question, not guessed: whether page {page} is representative of the other three affected pages. I will re-extract all of them before calling the fix general.""",
        """Nothing here needs a human decision yet; the next step is reversible and runs offline. Test time this step: {ms} ms.""",
    ],
    "extras": {
        "old": "        caption = blocks[i + 1].text",
        "new": "        caption = nearest_caption(table, blocks)",
        "fixture": "fixtures/annual_report_2025.pdf",
        "flag": "EXTRACT_BBOX_ANCHOR",
        "scope": "pipeline",
        "baseline": "0.87",
        "baseline2": "0.94",
        "budget": "240",
        "window": "5 runs",
        "val": '"Revenue by segment"',
        "commit": "3c81de0",
        "sha": "0be7a11",
        "branch": "fix/caption-anchor",
        "req": "page-12",
        "req2": "page-13",
        "oid": "table-07",
    },
}

THEMES["rust"] = {
    "id": "rust",
    "repo": "spanq",
    "brief": BRIEFS["rust"],
    "codepaths": [
        "src/tokenizer/mod.rs",
        "src/cli/args.rs",
        "src/metrics.rs",
    ],
    "paths": [
        "src/tokenizer/mod.rs",
        "src/cli/args.rs",
        "src/metrics.rs",
        "benches/tokenize.rs",
        "tests/cli_smoke.rs",
        ".cargo/config.toml",
    ],
    "cmds": [
        "cargo test --features metrics",
        "cargo clippy --all-targets -- -D warnings",
        "cargo bench --bench tokenize -- --sample-size 20",
        "cargo build --release --features metrics",
        "cargo test --no-default-features",
        "cargo tree -e features -i metrics",
    ],
    "tests": [
        "cli_parses_span_offsets",
        "tokenize_matches_golden",
        "metrics_feature_compiles",
        "empty_input_is_zero_spans",
    ],
    "funcs": ["tokenize", "scan_spans", "Metrics::record", "Args::parse", "flush_batch"],
    "fields": ["self.buf", 'feature = "metrics"', "sample_size", "p99", "SpanIter", "serde_json"],
    "errs": [
        """error[E0277]: the trait bound `Metrics: Serialize` is not satisfied
  --> src/metrics.rs:44:24
   |
44 |     serde_json::to_string(&metrics).unwrap();
   |                             ^^^^^^^ the trait `Serialize` is not implemented for `Metrics`""",
        """error[E0502]: cannot borrow `self.buf` as mutable because it is also borrowed as immutable
  --> src/tokenizer/mod.rs:118:9
   |
118|         let spans: Vec<_> = self.buf.iter().enumerate().collect();
   |                           -------- immutable borrow occurs here""",
        """warning: unused variable: `span`
  --> src/tokenizer/mod.rs:72:13
   |
72 |         for span in spans.iter() {
   |             ^^^^ help: if this is intentional, prefix it with an underscore: `_span`""",
        """error: could not compile `spanq` (bin "spanq") due to 2 previous errors""",
    ],
    "errtypes": ["E0277", "E0502", "E0308", "E0599"],
    "deps": ["serde 1.0.204", "clap 4.5.9", "criterion 0.5.1", "memchr 2.7.4"],
    "vers": ["1.0.204", "4.5.9", "0.5.1"],
    "metrics": ["p50", "p99", "spans/s", "binary size"],
    "beats": ["Compile", "Diagnose", "Minimise", "Patch", "Test", "Harden"],
    "notes": [
        "The feature build fails on the first crate that touches the counters, before any test runs.",
        "Two errors, one trait bound and one borrow; treating them as one bug is the mistake to avoid.",
        "Reducing the failure to a ten-line reproducer before changing either file.",
        "The patch must keep the feature additive: no new dependency, no allow attribute.",
        "Both feature sets have to be green, and the JSON output has to stay byte-identical.",
        "Adding the missing CI job so a default-feature build cannot hide this again.",
    ],
    "tool": [
        """`{cmd}` exited {rc} after {ms} ms:
```
{err}
```
This is the first of {nfail} errors in the same file; the second is a borrow error that only exists because the counters are collected before the buffer is reused.""",
        """`cargo check --features metrics` with an incremental build disabled reports:
```
{err2}
```
Line {line} of `{path}` is where the feature-gated branch diverges from the default build.""",
        """Benchmark, sample size {count}, three consecutive runs:
```
tokenize/4096    time:   [{bench_small} ms {bench_large} ms {bench_small} ms]
tokenize/65536   time:   [{bench_large} ms {bench_small} ms {bench_large} ms]
```
Medians are {bench_small} ms and {bench_large} ms; the run-to-run spread is wider than the difference I am chasing.""",
        """Working diff touches {nfiles} file(s); the behavioural hunk is in `{path}` around line {line}:
```diff
-    {old}
+    {new}
```
`{cmd2}` is green and `cargo tree -e features -i metrics` shows no new dependency edge.""",
        """Clippy with `-D warnings` fires {count} lint(s), all in the feature-gated module: `{field}` is moved but never read, and `{func}` can borrow instead of clone. None of these existed before the serde bump.""",
        """Compared default and feature builds on the smoke fixture:
```
default: {count} spans, sha256={sha}
metrics: {count} spans, sha256={sha}
```
Byte-identical output, so the feature only adds counters; the failure is compile-time, not behavioural.""",
    ],
    "analysis": [
        """The derive is necessary but not sufficient. `Metrics` is constructed in `{func}` and then passed by reference into a `serde_json` call, while `flush_batch` holds `&mut self.buf`. Adding `Serialize` fixes the trait bound; it does not fix the overlapping borrow in `{path}`:{line}.""",
        """`{errtype}` here means the feature gate changes the type of `{field}`: with the feature on the field is `Metrics`, with it off it is `()`. Code that compiles in both configurations must either be generic over that or keep the counter update in a separate function.""",
        """The benchmark regression is not established yet. The median moved from {baseline} ms to {baseline2} ms, but run-to-run spread is {spread_pct}% on this box, so the honest conclusion is "no measurable change" until the sample size goes up. I will not report a regression I cannot reproduce three times.""",
        """Clippy's iterator suggestion would change the borrow pattern in exactly the place that is already fighting me, so I am taking the lint as information rather than instruction. The `-D warnings` gate is satisfied by fixing the clone, not by allowing the lint.""",
        """The default build stays green because `src/metrics.rs` is compiled only under the feature: `Cargo.toml` gates both the module and the export call. CI's default-feature build therefore cannot catch this class of breakage, which deserves its own issue.""",
    ],
    "action": [
        """Patch plan: derive `Serialize` for `Metrics`, and in `{func}` build the counter snapshot before taking `&mut self.buf`. Two hunks, both in `{path}`; no new dependency, no allow attribute.""",
        """Decision recorded in `docs/decisions/0004-feature-builds.md`: CI gains a `cargo test --features metrics` job, because a default-feature build cannot see this module. The feature stays additive and off by default.""",
        """Next check: run `{cmd}` and `{cmd2}` from a clean target directory, then the bench three times and compare medians. Accept the patch only if both builds are green and the median moves less than 5%.""",
        """Verification gate: `cargo clippy --all-targets -- -D warnings` must exit zero for both feature sets, and `{test}` must emit byte-identical JSON to the pre-patch run.""",
    ],
    "detail": [
        """Turn-local note: cargo reuses the target directory between feature sets, so a stale artifact can mask the error. Every measurement here starts with `cargo clean -p spanq`.""",
        """Environment: rustc 1.80.1, cargo 1.80.1, criterion 0.5.1; the box has {count} cores and no CPU pinning, which is part of why the bench spread is wide.""",
        """Sanity check: `git diff --stat` shows {nfiles} file(s) changed and `Cargo.lock` untouched; `{cmd2}` still passes on the default feature set.""",
    ],
    "closer": [
        """State after this step: attempt {attempt} of {attempts}, feature build exit {rc}, default build still green, {nfiles} file(s) modified.""",
        """Open question, not guessed: whether the feature-gated `Metrics::record` call is on the hot path at all. The bench says no, but the bench only covers tokenize.""",
        """Nothing here needs a human decision; the next step is reversible and offline. Compile-and-test time this step: {ms} ms.""",
    ],
    "extras": {
        "old": "        let spans: Vec<_> = self.buf.iter().enumerate().collect();",
        "new": "        let spans: Vec<_> = std::mem::take(&mut self.buf).into_iter().enumerate().collect();",
        "fixture": "tests/gold/spans_smoke.json",
        "flag": "metrics",
        "scope": "src",
        "baseline": "4.12",
        "baseline2": "4.19",
        "budget": "500",
        "window": "3 runs",
        "val": "sample_size=20",
        "commit": "d4b7e19",
        "sha": "c7a1b04",
        "branch": "fix/borrow-in-tokenize",
        "req": "spanq-4096",
        "req2": "spanq-65536",
        "oid": "SpanIter",
    },
}

THEMES["ingest"] = {
    "id": "ingest",
    "repo": "lakehouse-ingest",
    "brief": BRIEFS["ingest"],
    "codepaths": [
        "ingest/sqlite_writer.py",
        "ingest/batch_reader.py",
        "ingest/config.py",
        "ops/backfill.py",
    ],
    "paths": [
        "ingest/sqlite_writer.py",
        "ingest/batch_reader.py",
        "ingest/migrations/0043_add_row_fingerprint.sql",
        "ingest/config.py",
        "tests/test_batch_reader.py",
        "ops/backfill.py",
        "ingest/profile.py",
    ],
    "cmds": [
        "python -m ingest.run --source orders --batch-size 5000",
        "pytest -q tests/test_batch_reader.py -x",
        "python -m ops.backfill --table orders --dry-run",
        'sqlite3 state/lake.db "PRAGMA wal_checkpoint(TRUNCATE)"',
        "python -m ingest.profile --rows 3200000",
        "python -m ingest.run --source orders --batch-size 500",
    ],
    "tests": [
        "test_batch_reader_bounds_memory",
        "test_writer_commits_once_per_batch",
        "test_duplicate_fingerprint_is_ignored",
        "test_schema_version_recorded",
    ],
    "funcs": ["write_batch", "iter_batches", "checkpoint", "fingerprint_rows", "load_state"],
    "fields": [
        "idempotency_key",
        "batch_size",
        "wal_autocheckpoint",
        "row_fingerprint",
        "committed_at",
        "cursor",
    ],
    "errs": [
        """sqlite3.OperationalError: database or disk is full
  File "ingest/sqlite_writer.py", line 133, in write_batch
    conn.executemany("INSERT INTO rows ...", rows)""",
        """MemoryError: unable to allocate 1.42 GiB for an array with shape (186000000,) and data type int64""",
        """AssertionError: expected 1 commit per batch, saw 5000 (batch_size=5000)""",
        """sqlite3.OperationalError: no such column: row_fingerprint""",
    ],
    "errtypes": ["sqlite3.OperationalError", "MemoryError", "AssertionError", "KeyError"],
    "deps": ["sqlite3 3.46.0", "pyarrow 17.0.0", "orjson 3.10.6"],
    "vers": ["3.46.0", "17.0.0", "3.10.6"],
    "metrics": ["peak RSS", "rows/s", "commit count", "duplicate rate"],
    "beats": ["Load", "Profile", "Diagnose", "Migrate", "Backfill", "Harden"],
    "notes": [
        "The source loads, then the process dies partway through the writers' first pass.",
        "Measuring peak RSS and commit count before proposing a fix, because both are wrong.",
        "The reader holds the whole Arrow table; the writer's batching is already sound.",
        "The fingerprint column needs a numbered migration, not an in-place ALTER.",
        "The resumed run, the killed run, and the dry run must agree on row count.",
        "Bounding the WAL and documenting the cursor contract for the next operator.",
    ],
    "tool": [
        """`{cmd}` exited {rc} after {ms} ms:
```
{err}
```
Peak RSS reached {rss} MiB at row {row}; the batch size is 5,000 rows, so the reader is holding roughly {rows2} rows at once.""",
        """Profiled with tracemalloc over the first {count} rows:
```
pyarrow.Table      {rss} MiB
batch buffer       {rss2} MiB
sqlite page cache  {rss3} MiB
```
The table dominates; the writer's batch buffer is already bounded by {count} rows.""",
        """Killed the run at batch {count} and resumed from the cursor:
```
rows before kill: {row}
rows after resume: {row2}
duplicates inserted: {nfail}
```
The duplicate count is the fingerprint bug: resume cannot tell a row it wrote from a row it never saw.""",
        """Working diff touches {nfiles} file(s); the behavioural hunk is in `{path}` around line {line}:
```diff
-    {old}
+    {new}
```
`{cmd2}` reports the same row count as before, so batching did not change the result set.""",
        """`PRAGMA wal_checkpoint` after a 5,000-row batch:
```
wal frames: {wal_frames}
autocheckpoint: {val}
checkpoint time: {ms2} ms
```
The WAL grows between commits because the reader yields rows faster than the writer commits.""",
        """Dry run over the full backfill:
```
source rows: {row}
rows already present: {row2}
rows to insert: {count3}
peak RSS: {rss} MiB
```
The dry run and the full run must agree on `rows to insert`; that number is my acceptance check.""",
    ],
    "analysis": [
        """The OOM is a reader problem, not a writer problem: `iter_batches` calls `table.to_pylist()` before yielding, so peak RSS tracks the source table ({row} rows) rather than `batch_size` ({count}). The writer's `executemany` is already bounded; the reader has to yield slices of the Arrow table instead.""",
        """Commit counts confirm the contract: `{test}` expects one commit per batch and sees {count2}, because `write_batch` commits inside the per-row loop. Moving the commit after `executemany` also makes the kill-and-resume boundary equal to the batch boundary.""",
        """Resume is wrong for a second reason: the cursor is the last row's `committed_at`, but the table has no `row_fingerprint` column, so a resumed run cannot tell whether the boundary row was written. The migration in `ingest/migrations/0043_add_row_fingerprint.sql` adds the column and the unique index that makes the insert idempotent.""",
        """`wal_autocheckpoint` is still the SQLite default of 1000 pages, which is why the WAL file grows between commits. Setting it to {val} pages trades a little write amplification for a bounded WAL; that is a config change, not a schema change, so it belongs in `ingest/config.py`.""",
        """The dry run's `rows to insert` is the right acceptance number: it is computed from the fingerprint set, so it changes only if idempotency changes. If the full run inserts a different count, the bug is in the resume path, not in the reader.""",
    ],
    "action": [
        """Patch plan: make `iter_batches` yield `table.slice(offset, batch_size)` and keep the writer's commit after `executemany`. Then rerun the {count}-row dry run and the 3.2M-row backfill, and compare `rows to insert` between them.""",
        """Decision recorded in `docs/decisions/0009-backfill-cursor.md`: the cursor is `(committed_at, row_fingerprint)` and resume replays the batch containing the last committed fingerprint. Migration 0043 is the schema half; it is reversible and does not backfill.""",
        """Next check: kill the run at batch {count} twice, resume each time, and assert the final row count equals the dry run's `rows to insert` in all three runs. A single duplicate fails the check.""",
        """Verification gate: peak RSS below {rss} MiB on 3.2M rows, `{cmd2}` green, and the duplicate rate at zero. Until then the change stays behind {flag}.""",
    ],
    "detail": [
        """Turn-local note: `PRAGMA wal_autocheckpoint={val}` is per connection, so every writer process must set it in `ingest/config.py`; setting it in the shell does nothing for the service.""",
        """Environment: CPython 3.12.4, sqlite 3.46.0 (bundled), pyarrow 17.0.0; the synthetic source in `ingest/profile.py` mirrors the real orders table's column types but not its skew.""",
        """Sanity check: `git diff --stat` shows {nfiles} file(s) changed and `state/lake.db` is untracked; `{cmd2}` still reports the pre-patch row count.""",
    ],
    "closer": [
        """State after this step: attempt {attempt} of {attempts}, dry-run rows {row}, {nfiles} file(s) modified, no migration applied yet.""",
        """Open question, not guessed: whether the upstream source can deliver rows out of order after a restart. If it can, the cursor needs a tiebreaker, not just `committed_at`.""",
        """Nothing here needs a human decision yet; the next step is reversible and runs offline. Wall time this step: {ms} ms of ingest.""",
    ],
    "extras": {
        "old": "        conn.commit()",
        "new": "        conn.commit()  # once per batch, after executemany",
        "fixture": "state/lake.db",
        "flag": "INGEST_SLICE_READER",
        "scope": "ingest",
        "baseline": "4.1",
        "baseline2": "0.9",
        "budget": "900",
        "window": "3 runs",
        "val": "4096",
        "commit": "7e0a2c4",
        "sha": "2bd9f13",
        "branch": "fix/bounded-backfill",
        "req": "batch-0381",
        "req2": "batch-0382",
        "oid": "orders",
    },
}

POOLS: dict[str, dict[str, list[str]]] = {
    "api": {
        "context": [
            """Where the investigation stands: the replay reproduces on every run, the handler is not the bottleneck, and the only unexplained cost is the per-attempt re-validation inside `{func}`. Everything after this turn builds on that, so if the next measurement contradicts it, say so explicitly.""",
            """Earlier turns established two facts worth keeping: p95 is per-attempt (cold {cold_ms} ms versus warm {warm_ms} ms), and pinning the fixture clock is what makes the numbers comparable. Neither fact depends on the patch under discussion.""",
            """The working theory is now narrow: `{field}` is recomputed per retry and `{path}` is re-entered with a fresh connection each time. Both are testable offline, and both can be reverted without touching the response schema.""",
            """Context for this step: release 2026.10.3 changed {dep} and the retry wrapper in the same commit, so a bisect would be ambiguous until one of the two is isolated. That is why every measurement here changes one variable at a time.""",
        ],
        "verify": [
            """Independent check: `{cmd2}` on the pre-patch commit still shows the same {count} failures, so the failure predates the working diff.""",
            """Cross-check: the p95 recomputed from the replay agrees with the latency histogram within {delta_pct}%, which is close enough that I am not chasing the difference.""",
            """Reproducibility: the same command on a second checkout gives exit code {rc} and the same failing line, so the observation is not machine-local.""",
        ],
    },
    "docs": {
        "context": [
            """Where the work stands: the caption text is parsed correctly, the table cells are correct, and only ownership is wrong. That narrows the fix to the block-walk logic, not to docling's table parser.""",
            """Earlier turns established that the shift is one table on every two-column page, and that pages 8 and 9 are clean because they are single-column. Any fix has to keep those two pages byte-identical.""",
            """The current hypothesis is geometric: a caption belongs to the table whose bbox is closest above it. Page order happens to agree on single-column pages, which is why the bug survived the unit suite.""",
            """Context for this step: gold was produced with OCR disabled, so an OCR-side explanation is out of scope unless the probe shows missing text. The probe did not, so the remaining variable is reading order.""",
        ],
        "verify": [
            """Independent check: `{cmd2}` on the unmodified pipeline still reports {nfail} mismatch(es), so the defect is in the code and not in the fixture.""",
            """Cross-check: the block dump and the extractor's own table list agree on {count} tables for pages {page}-{page2}, so no table is being dropped by the walk.""",
            """Reproducibility: two consecutive extractions of page {page} produce identical caption ownership, so this is deterministic, not a race inside docling.""",
        ],
    },
    "rust": {
        "context": [
            """Where the build stands: the default feature set compiles and tests clean, and the failure exists only when `metrics` is on. Any fix therefore has to be validated twice, and a default-only build is not evidence.""",
            """Earlier turns established that the trait bound and the borrow conflict are separate defects that happen to surface together. Fixing only the derive leaves `cargo test --features metrics` failing at line {line}.""",
            """The current belief is that the feature changes the type of `{field}` from `()` to `Metrics`, which forces the call site into a clone it did not need before. A small generic helper would avoid both the clone and an allow attribute.""",
            """Context for this step: the benchmark box is noisy (about {spread_pct}% spread), so a single run cannot support a regression claim. Medians over three runs are the minimum bar, and the report will say so.""",
        ],
        "verify": [
            """Independent check: `{cmd2}` still passes on the default feature set, so the working diff has not broken the shipped build.""",
            """Cross-check: `cargo tree -e features -i metrics` shows the same dependency edges before and after, so no transitive feature was enabled by accident.""",
            """Reproducibility: a clean rebuild of the feature set fails at the same line every time ({count} attempts, {count} failures), so the error is not incremental-build residue.""",
        ],
    },
    "ingest": {
        "context": [
            """Where the backfill stands: the writer's contract is sound, the reader is unbounded, and the state table cannot distinguish a written row from an unseen one. All three have to change together or resume stays unsafe.""",
            """Earlier turns established that peak RSS tracks source rows, not batch size, and that commit count is one per row rather than one per batch. Those two facts explain both the OOM and the WAL growth.""",
            """The current plan is to slice the Arrow table, commit once after `executemany`, and add the fingerprint column through migration 0043. Each change is independently testable on the dry run.""",
            """Context for this step: the dry run computes `rows to insert` from the fingerprint set, so it is the only number that stays comparable across the schema change. The full run must match it exactly.""",
        ],
        "verify": [
            """Independent check: `{cmd2}` on the pre-patch code still reproduces the duplicate count, so the resume defect predates the working diff.""",
            """Cross-check: `PRAGMA wal_checkpoint` reports {count2} frames both before and after the batch, which means the checkpoint is happening but not often enough.""",
            """Reproducibility: two dry runs over the same source produce the same `rows to insert` ({count3}), so the fingerprint computation is deterministic.""",
        ],
    },
}

SUMMARY_HINTS: dict[str, str] = {
    "C1": """Head summary (turns 1-20). Reproduced the p95 regression from fixtures/orders_2026_10.jsonl: cold 904 ms, warm 238 ms, so the cost is per-attempt, not per-request. Profiling puts about 61% of the delta inside retry_with_backoff; the wrapper re-validates the payload on every attempt and re-opens the Redis connection for each idempotency lookup. The retry budget is 500 ms with a 3-attempt cap; the 6 attempts seen in the fixture come from record_latency incrementing once per attempt, not from the budget. Decision: memoise the validated payload keyed by idempotency_key and cap attempts at 3; the response schema is unchanged. Open: whether ORDERS_FAST_PATH should default on in staging. Next: patch src/api/middleware/retry.py and rerun the replay.""",
    "C2": """Head summary (turns 1-20). The caption shift is a reading-order bug on two-column pages: docling emits column-major blocks, so the block after a table is often the caption of the next table. On page 12 the caption 'Revenue by segment' (y1=418.2) belongs to table 7, whose bbox ends at 402.8, not to table 6. Gold ownership on pages 10-14 confirms four affected pages, all two-column. Decision: replace page-order caption attachment with vertical proximity to the table's own bbox, keeping page order as the single-column fallback. OCR was probed and is clean; the PDF and the gold file are untouched. Next: patch pipeline/table_extract.py and pipeline/anchors.py, re-extract pages 10-14, and diff against gold.""",
    "C3": """Head summary (turns 1-20). Peak RSS tracks the source Arrow table, not batch_size: iter_batches materialises the whole table before yielding, so the 3.2M-row backfill OOMs near row 1.9M. Commit counting shows 5,000 commits per 5,000-row batch because write_batch commits inside the row loop. Resume re-inserts boundary rows because the state table has no row_fingerprint column. Decisions: yield table.slice(offset, batch_size); commit once after executemany; add migration 0043_add_row_fingerprint.sql with a unique index; set wal_autocheckpoint=4096. Acceptance: the dry run's rows-to-insert must equal the full run's. Next: patch ingest/batch_reader.py and ingest/sqlite_writer.py.""",
}

GOLD_NOTES: dict[str, str] = {
    "E1": """Decision recorded for handover: migration `0042_rename_fingerprint` renames `idempotency_key` to `request_fingerprint`; this is the settled answer to the reviewer's question and should not be re-opened without new evidence.""",
    "E2": """Decision recorded for handover: caption association keys on the table's own `anchor_mode=bbox_y1`, not on page order; this is the settled answer to the reviewer's question and should not be re-opened without new evidence.""",
}


def preamble_for(spec: dict[str, Any]) -> str:
    theme = THEMES[spec["theme"]]
    return SHARED_SYSTEM + "\n\n" + theme["brief"] + "\n\n" + spec["goal"]


def make_slots(theme: dict[str, Any], i: int, rng: random.Random, off: int) -> dict[str, Any]:
    """All placeholder values for one turn, derived only from (theme, i, off, seed)."""

    s: dict[str, Any] = {}
    s["path"] = pick(theme.get("codepaths", theme["paths"]), i * 3 + off)
    s["path2"] = pick(theme["paths"], i * 5 + off + 2)
    s["path3"] = pick(theme["paths"], i * 7 + off + 4)
    s["cmd"] = pick(theme["cmds"], i * 2 + off)
    s["cmd2"] = pick(theme["cmds"], i * 2 + off + 3)
    s["test"] = pick(theme["tests"], i + off)
    s["func"] = pick(theme["funcs"], i * 2 + off)
    s["func2"] = pick(theme["funcs"], i + off + 2)
    s["field"] = pick(theme["fields"], i * 3 + off)
    s["err"] = pick(theme["errs"], i + off)
    s["err2"] = pick(theme["errs"], i + off + 1)
    s["err3"] = pick(theme["errs"], i + off + 2)
    s["errtype"] = pick(theme["errtypes"], i + off)
    s["errtype2"] = pick(theme["errtypes"], i + off + 2)
    s["dep"] = pick(theme["deps"], i + off)
    s["dep2"] = pick(theme["deps"], i + off + 1)
    s["ver"] = pick(theme["vers"], i + off)
    s["metric"] = pick(theme["metrics"], i + off)
    s["val"] = theme["extras"]["val"]
    s["fixture"] = theme["extras"]["fixture"]
    s["flag"] = theme["extras"]["flag"]
    s["scope"] = theme["extras"]["scope"]
    s["baseline"] = theme["extras"]["baseline"]
    s["baseline2"] = theme["extras"]["baseline2"]
    s["budget"] = theme["extras"]["budget"]
    s["window"] = theme["extras"]["window"]
    s["old"] = theme["extras"]["old"]
    s["new"] = theme["extras"]["new"]
    s["commit"] = theme["extras"]["commit"]
    s["sha"] = theme["extras"]["sha"]
    s["branch"] = theme["extras"]["branch"]
    s["req"] = theme["extras"]["req"]
    s["req2"] = theme["extras"]["req2"]
    s["oid"] = theme["extras"]["oid"]

    s["rc"] = 1 + (off + i) % 3
    s["ms"] = 120 + rng.randrange(3600)
    s["ms2"] = 40 + rng.randrange(680)
    s["pct"] = 30 + rng.randrange(55)
    s["pct2"] = min(99, s["pct"] + 5 + rng.randrange(14))
    s["count"] = 2 + rng.randrange(12)
    s["count2"] = 2 + rng.randrange(16)
    s["count3"] = s["count"] + 1 + rng.randrange(6)
    s["nfail"] = 1 + rng.randrange(3)
    s["nfail2"] = rng.randrange(2)
    s["nruns"] = (4, 5, 6, 8, 10, 12)[(i + off) % 6]
    s["nfiles"] = 1 + rng.randrange(4)
    s["line"] = 11 + rng.randrange(460)
    s["line2"] = s["line"] + 3 + rng.randrange(40)
    s["attempts"] = 4 + (off % 2)
    s["attempt"] = 1 + (i * 3 + off) % s["attempts"]
    s["page"] = 10 + rng.randrange(18)
    s["page2"] = min(30, s["page"] + 1)
    s["table"] = 2 + rng.randrange(12)
    s["table2"] = s["table"] + 1
    s["row"] = 1_400_000 + rng.randrange(900_000)
    s["row2"] = 3_200_000
    s["rows2"] = 180_000 + rng.randrange(400_000)
    s["rss"] = 900 + rng.randrange(1200)
    s["rss2"] = 40 + rng.randrange(120)
    s["rss3"] = 20 + rng.randrange(80)
    s["sec"] = max(1, (s["count"] * s["ms"]) // 1000)
    s["cold_ms"] = 880 + rng.randrange(80)
    s["warm_ms"] = 200 + rng.randrange(60)
    s["handler_ms"] = 220 + rng.randrange(40)
    s["remain_ms"] = 600 + rng.randrange(150)
    s["attempt_ms"] = 30 + rng.randrange(45)
    s["delta_pct"] = 2 + rng.randrange(6)
    s["spread_pct"] = 3 + rng.randrange(6)
    s["ocr_conf"] = 88 + rng.randrange(11)
    s["acc_before"] = 55 + rng.randrange(10)
    s["acc_after"] = 98 + rng.randrange(3)
    s["bench_small"] = f"{4.0 + rng.randrange(20) / 100:.2f}"
    s["bench_large"] = f"{4.1 + rng.randrange(20) / 100:.2f}"
    s["gap_med"] = 40 + rng.randrange(80)
    s["gap_max"] = s["gap_med"] + 20 + rng.randrange(150)
    s["wal_frames"] = 900 + rng.randrange(4000)
    base = 300 + rng.randrange(120)
    s["y1"] = f"{base}.{rng.randrange(10)}"
    s["y2"] = f"{base + 22}.{rng.randrange(10)}"
    s["gap"] = 6 + rng.randrange(14)
    s["gap2"] = s["gap"] + 8 + rng.randrange(16)
    return s


def build_turn_text(theme: dict[str, Any], i: int, n: int, off: int) -> str:
    rng = random.Random(SEED * 100003 + off * 1009 + i)
    s = make_slots(theme, i, rng, off)
    beat = min(len(theme["beats"]) - 1, (i * len(theme["beats"])) // n)
    tails = (
        f"Checkpoint `{s['cmd2']}`; attempt {s['attempt']} of {s['attempts']}.",
        f"Re-running `{s['cmd2']}` before the next change; attempt {s['attempt']} of {s['attempts']}.",
        f"No new state outside `{s['path2']}`; attempt {s['attempt']} of {s['attempts']}.",
        f"Last measured command is still `{s['cmd2']}`; attempt {s['attempt']} of {s['attempts']}.",
    )
    head = f"### {theme['beats'][beat]} -- turn {i + 1}/{n}\n{theme['notes'][beat]} {tails[(i + off) % 4]}"
    tool = fill(theme["tool"][(i * 5 + off) % len(theme["tool"])], s)
    analysis = fill(theme["analysis"][(i * 7 + off) % len(theme["analysis"])], s)
    action = fill(theme["action"][(i * 3 + off) % len(theme["action"])], s)
    context = fill(POOLS[theme["id"]]["context"][(i * 13 + off) % 4], s)
    verify = fill(POOLS[theme["id"]]["verify"][(i * 17 + off) % 3], s)
    detail = fill(theme["detail"][(i * 2 + off) % len(theme["detail"])], s)
    closer = fill(theme["closer"][(i * 11 + off) % len(theme["closer"])], s)
    # Alternate which kind of content leads: tool result first on even turns,
    # reasoning first on odd turns.  Both are assistant content in this corpus.
    if i % 2 == 0:
        parts = [head, tool, analysis, action, context, verify, detail, closer]
    else:
        parts = [head, analysis, tool, action, context, verify, detail, closer]
    return "\n\n".join(parts)


def volatile_for(off: int, i: int) -> dict[str, str]:
    seconds = 18 * 3600 + i * 37 + off * 11
    return {
        "step": str(i),
        "elapsed_ms": str(30000 + (i * 1733 + off * 41) % 90000),
        "task_id": f"T-{(0xA000 + off * 0x31 + i * 0x17) % 0xFFFF:04x}",
        "turn_ts": f"2026-10-20T{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}Z",
    }


def make_turn(role: str, text: str, off: int, i: int) -> dict[str, Any]:
    return {
        "role": role,
        "text": text,
        "volatile": volatile_for(off, i),
        "est_tokens": est_tokens(text),
    }


def task_turn(spec: dict[str, Any], theme: dict[str, Any], off: int) -> dict[str, Any]:
    rng = random.Random(SEED * 100003 + off * 1009)
    s = make_slots(theme, 0, rng, off)
    text = (
        f"{spec['task']}\n\n"
        f"The failing output recorded by the previous run was:\n```\n{s['err']}\n```\n"
        f"Run `{s['cmd']}` yourself to confirm it before changing anything. Repository: `{theme['repo']}`. "
        f"Keep the work tree clean and quote the exact command behind every number you report.\n\n"
        f"Acceptance for this session: the failing check passes twice in a row, the pre-existing suite stays "
        f"green, and the decision log names every file you changed. If you conclude the report is wrong rather "
        f"than the code, stop and say so instead of patching around it. Do not push and do not open a pull request. "
        f"Stop and ask if a decision is not yours to make (a schema change, a dependency bump, a backfill), and "
        f"end with a decision log (tried / observed / concluded / open) rather than a narrative."
    )
    return make_turn("user", text, off, 0)


def session_turns(spec: dict[str, Any], n_turns: int, off: int) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    theme = THEMES[spec["theme"]]
    preamble = preamble_for(spec)
    turns = [task_turn(spec, theme, off)]
    for i in range(1, n_turns):
        turns.append(make_turn("assistant", build_turn_text(theme, i, n_turns, off), off, i))
    return theme, preamble, turns


def total_tokens(preamble: str, turns: list[dict[str, Any]]) -> int:
    return est_tokens(preamble) + sum(t["est_tokens"] for t in turns)


def build_volatility() -> dict[str, Any]:
    scenarios = []
    for spec in VOLATILITY_SPECS:
        off = int(spec["id"][1:]) + 1
        _theme, preamble, turns = session_turns(spec, VOLATILITY_TURNS, off)
        scenarios.append(
            {
                "id": spec["id"],
                "preamble": preamble,
                "turns": turns,
                "depths": DEPTHS,
                "preamble_est_tokens": est_tokens(preamble),
                "est_tokens_total": total_tokens(preamble, turns),
            }
        )
    meta = {
        "corpus": "volatility",
        "seed": SEED,
        "built_by": BUILDER,
        "digest_note": (
            "sha256 is recorded in MANIFEST.json. The builder emits no timestamps and no unseeded "
            "randomness, so two runs are byte-identical; verify with two --out dirs and cmp."
        ),
        "estimator": ESTIMATOR,
        "schema_version": "1",
        "scenario_count": len(scenarios),
        "turn_count": sum(len(s["turns"]) for s in scenarios),
        "depths": DEPTHS,
        "turn_text_note": (
            "Turn text is the stable content shared by every render policy. The per-turn volatile dict "
            "is deliberately absent from the text: where those values are interpolated is the "
            "renderer's decision (resextract.context.render), which is what E1 measures."
        ),
        "est_tokens_total": sum(s["est_tokens_total"] for s in scenarios),
    }
    return {"meta": meta, "scenarios": scenarios}


def build_compaction() -> dict[str, Any]:
    targets = [8000, 16000, 24000]
    scenarios = []
    for k, spec in enumerate(COMPACTION_SPECS):
        off = 5 + k
        _theme, preamble, turns = session_turns(spec, COMPACTION_TURNS, off)
        cumulative = est_tokens(preamble)
        points: list[dict[str, int]] = []
        ti = 0
        for idx, turn in enumerate(turns):
            cumulative += turn["est_tokens"]
            while ti < len(targets) and cumulative >= targets[ti]:
                points.append(
                    {
                        "target_tokens": targets[ti],
                        "at_turn": idx,
                        "cumulative_est_tokens": cumulative,
                    }
                )
                ti += 1
        scenarios.append(
            {
                "id": spec["id"],
                "preamble": preamble,
                "turns": turns,
                "summary_hint": SUMMARY_HINTS[spec["id"]],
                "summary_hint_est_tokens": est_tokens(SUMMARY_HINTS[spec["id"]]),
                "compaction_points": points,
                "preamble_est_tokens": est_tokens(preamble),
                "est_tokens_total": total_tokens(preamble, turns),
            }
        )
    meta = {
        "corpus": "compaction",
        "seed": SEED,
        "built_by": BUILDER,
        "digest_note": (
            "sha256 is recorded in MANIFEST.json; the builder is clock-free and unseeded except for "
            "SEED, so two runs are byte-identical."
        ),
        "estimator": ESTIMATOR,
        "schema_version": "1",
        "scenario_count": len(scenarios),
        "turn_count": sum(len(s["turns"]) for s in scenarios),
        "compaction_targets": targets,
        "compaction_note": (
            "Each entry in compaction_points has the 0-based turn index at which cumulative estimated "
            "tokens (preamble included) first reach target_tokens, plus the cumulative value there. "
            "summary_hint is a canned ~200-token summary a compaction policy may substitute for the "
            "head turns; it is not part of the rendered transcript."
        ),
        "est_tokens_total": sum(s["est_tokens_total"] for s in scenarios),
    }
    return {"meta": meta, "scenarios": scenarios}


def build_endtoend() -> dict[str, Any]:
    scenarios = []
    for k, spec in enumerate(ENDTOEND_SPECS):
        off = 8 + k
        theme, preamble, turns = session_turns(spec, ENDTOEND_TURNS - 1, off)
        # The final turn is the reviewer's question, not an assistant turn.
        turns.append(make_turn("user", spec["final_question"], off, ENDTOEND_TURNS - 1))
        gold_turn = int(spec["gold_turn"])
        if not 0 < gold_turn < len(turns) - 1:
            raise AssertionError(f"{spec['id']}: gold turn out of range")
        turns[gold_turn]["text"] = turns[gold_turn]["text"] + "\n\n" + GOLD_NOTES[spec["id"]]
        turns[gold_turn]["est_tokens"] = est_tokens(turns[gold_turn]["text"])
        gold = spec["gold_answer"]
        occurrences = sum(t["text"].count(gold) for t in turns)
        if occurrences != 1:
            raise AssertionError(f"{spec['id']}: gold answer occurs {occurrences} times, want exactly 1")
        scenarios.append(
            {
                "id": spec["id"],
                "preamble": preamble,
                "turns": turns,
                "final_question": spec["final_question"],
                "gold_answer": gold,
                "gold_turn_index": gold_turn,
                "gold_occurrences": occurrences,
                "preamble_est_tokens": est_tokens(preamble),
                "est_tokens_total": total_tokens(preamble, turns),
            }
        )
    meta = {
        "corpus": "endtoend",
        "seed": SEED,
        "built_by": BUILDER,
        "digest_note": (
            "sha256 is recorded in MANIFEST.json; two runs are byte-identical. gold_answer is a short "
            "verbatim string that appears in exactly one pre-question turn (gold_turn_index)."
        ),
        "estimator": ESTIMATOR,
        "schema_version": "1",
        "scenario_count": len(scenarios),
        "turn_count": sum(len(s["turns"]) for s in scenarios),
        "gold_note": (
            "The last turn of each session is the final user question; gold_answer must be recoverable "
            "from the transcript after any compaction policy has run. gold_occurrences is asserted to "
            "be exactly 1 at build time."
        ),
        "est_tokens_total": sum(s["est_tokens_total"] for s in scenarios),
    }
    return {"meta": meta, "scenarios": scenarios}


def validate(corpus: dict[str, Any], name: str) -> None:
    for scenario in corpus["scenarios"]:
        sid = scenario["id"]
        if not scenario["turns"]:
            raise AssertionError(f"{name}/{sid}: no turns")
        seen: set[str] = set()
        for idx, turn in enumerate(scenario["turns"]):
            text = turn["text"]
            if not text.strip():
                raise AssertionError(f"{name}/{sid}: empty turn {idx}")
            if "\x00" in text:
                raise AssertionError(f"{name}/{sid}: NUL byte in turn {idx}")
            leftover = PLACEHOLDER.search(text)
            if leftover:
                raise AssertionError(f"{name}/{sid}: unresolved placeholder {leftover.group(0)} in turn {idx}")
            if turn["est_tokens"] != est_tokens(text):
                raise AssertionError(f"{name}/{sid}: est_tokens mismatch on turn {idx}")
            if idx > 0:
                if text in seen:
                    raise AssertionError(f"{name}/{sid}: duplicate assistant turn at {idx}")
                seen.add(text)
            for key, value in turn["volatile"].items():
                if not isinstance(value, str) or not value:
                    raise AssertionError(f"{name}/{sid}: bad volatile {key} on turn {idx}")
        if scenario["est_tokens_total"] != total_tokens(scenario["preamble"], scenario["turns"]):
            raise AssertionError(f"{name}/{sid}: est_tokens_total mismatch")
        if name == "volatility":
            if scenario["depths"] != DEPTHS:
                raise AssertionError(f"{name}/{sid}: depths mismatch")
            if len(scenario["turns"]) != VOLATILITY_TURNS:
                raise AssertionError(f"{name}/{sid}: expected {VOLATILITY_TURNS} turns")
        if name == "compaction":
            if len(scenario["compaction_points"]) != 3:
                raise AssertionError(f"{name}/{sid}: expected 3 compaction points")
            if not scenario["summary_hint"].strip():
                raise AssertionError(f"{name}/{sid}: empty summary_hint")
        if name == "endtoend":
            if scenario["turns"][-1]["role"] != "user":
                raise AssertionError(f"{name}/{sid}: last turn is not the question")
            if scenario["gold_occurrences"] != 1:
                raise AssertionError(f"{name}/{sid}: gold occurrences != 1")


def write_json(path: str, payload: dict[str, Any]) -> bytes:
    blob = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(blob)
    return blob


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic context-cache corpora.")
    parser.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    args = parser.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)

    corpora = {
        "volatility.json": build_volatility(),
        "compaction.json": build_compaction(),
        "endtoend.json": build_endtoend(),
    }
    for name, corpus in corpora.items():
        validate(corpus, name.removesuffix(".json"))

    manifest_files = []
    for name, corpus in corpora.items():
        blob = write_json(os.path.join(args.out, name), corpus)
        manifest_files.append(
            {
                "name": name,
                "sha256": hashlib.sha256(blob).hexdigest(),
                "bytes": len(blob),
                "scenarios": len(corpus["scenarios"]),
                "turns": corpus["meta"]["turn_count"],
                "est_tokens": corpus["meta"]["est_tokens_total"],
            }
        )

    manifest = {
        "built_by": BUILDER,
        "seed": SEED,
        "estimator": ESTIMATOR,
        "deterministic": "no wall clock, no unseeded randomness: two runs produce byte-identical files",
        "depths": DEPTHS,
        "files": manifest_files,
        "est_tokens_total": sum(f["est_tokens"] for f in manifest_files),
    }
    write_json(os.path.join(args.out, "MANIFEST.json"), manifest)

    print(f"wrote {len(corpora) + 1} files to {args.out}")
    for entry in manifest_files:
        print(
            f"{entry['name']:<16} {entry['bytes']:>8} bytes  "
            f"{entry['scenarios']} scenarios  {entry['turns']:>3} turns  "
            f"{entry['est_tokens']:>7} est tokens  sha256={entry['sha256']}"
        )
    print(f"{'TOTAL':<16} {'':>8}          {sum(f['scenarios'] for f in manifest_files)} scenarios  "
          f"{sum(f['turns'] for f in manifest_files):>3} turns  "
          f"{manifest['est_tokens_total']:>7} est tokens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
