# UNIT `DRYRUN-TOOLS-SHAPE` — tools-on launch, rehearsed offline

**Status: done (verdict `no_go`) · tool calls ~27 of 26 (bound overrun from two failed tool calls, recorded)**
**Write paths (exactly):** `experiments/ptr-engine/measure/DRYRUN-TOOLS-SHAPE.json` · `docs/DRYRUN-TOOLS-SHAPE.md` ·
`orchestration/units/DRYRUN-TOOLS-SHAPE.md` · `orchestration/handoffs/DRYRUN-TOOLS-SHAPE.json` ·
`orchestration/journals/DRYRUN-TOOLS-SHAPE.jsonl`

## Purpose

`GRID-SHAPE-TOOLS` chose shape (a) tools-on and carried `--tools read_file` through a `CELL_RUNNER_PATH` runpy shim,
verified by reading code. `TRANCH1-DRYRUN-2` rehearsed 10/10 cells at `--tools off`. Nobody had executed the shim.
This unit does, offline, before the 8h / 720-request tranche.

## What was done (all offline)

1. Ten cells, driver's own dry-run path, exactly as `GRID-SHAPE.json` records them (`--cell N --tools read_file
   --dry-run --budget 67 --hypothesis H2 --fixture .../LR-01.v8.json`). All `rc=0`, 0 would-refuse.
2. The shim executed directly (`ensure_shim()` → `[runner] ... --dry-run --tools read_file`), argv observed at exit,
   runner prints `tool_channel=read_file fetch_rounds_cap=24`, `would_send_total=48`.
3. Gates re-derived per cell from cell.py's own `eval_gate_ledger/projection/prereg`; G1 1,173/4,320,
   would_spend 72 (48+24), G2 2,880/2,880, G3 n=48≥1, `design_cap_tokens` 10,616 on all four arms.
   G3 still refuses H1 at n=48 (`n >= 60`).
4. Zero-traffic proof: `sys.addaudithook` on `socket.*/urllib./http.client` around the whole rehearsal → 0 events.
   `unshare -n` unavailable (rc=1), recorded.
5. Canary imports, `--help` rc 0, dry `classify(rows, n=2)` on the stopped cell's rows → `shape_unknown` /
   `no_parseable_answer` / exit_code 2; rows sha256 unchanged.
6. Verdict: **`no_go`** — `harness_sha256` observed `b45177379e99a05da385a956d90c12cd392322a3ec1471f3a2ce80120d5fe452` ≠ recorded `c4541802…`; `run_longrun.py` and `cell.py` moved
   on disk at 18:45–18:46Z today.

## Hard rules honoured

No live invocation, no network, no edits to `cell.py` / `run_longrun.py` / `run_a_star.py` / fixture / graders /
analyser / row files / `GRID-SHAPE.json` / any published number. The stopped cell's 27-row file is byte-identical
(sha256 before == after). `ask_user_question` never called.
