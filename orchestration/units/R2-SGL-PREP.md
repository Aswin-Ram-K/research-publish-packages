# R2-SGL-PREP — variant launcher + G0 window gate, mock-tested offline

**Tag:** `automated` (no human present; never ask, never wait).
**Mode:** DRY RUN. 0 docker commands, 0 ssh commands, 0 model requests, 0 lock acquisition.

## Why this unit exists

Two SGLang window cells are about to be scheduled (R2-SGL: `--radix-eviction-policy` and
page-size/`--disable-chunked-prefix-cache` windows on the GX10). Every previous SGLang variant
window lost wall-clock time to *plumbing* rather than science: `WIN-SGL` needed a stop-safety
rewrite of the production container before it could even start; `DENSE-SGL` hand-rolled a second
launcher; the four stacks with a grid have **no in-cell G0** (`GAPS.md` §"Downgrade note — no
in-cell G0 for S1/S2/TUNED"), so their measurements rest on a gate that predates the protocol
they measured. This unit builds and mock-tests the two pieces that remove that risk, so the live
windows do science.

## Objective (one purpose)

Ship `state/config/variant_launcher.py` (the variant launcher) and `state/config/window_gate.py`
(the G0 window gate) as importable, side-effect-free libraries, proven correct by an offline
mock harness that touches no host.

## Hard bound

Max **40 tool calls**, or the stop condition: if the mock harness cannot be made to pass in
**3 fix iterations**, STOP and report `partial` with the failing assertion named.

## Write paths (declared, exclusive)

- `state/config/variant_launcher.py` (new)
- `state/config/window_gate.py` (new)
- `scratch/r2sglprep/` (mock harness, red/green evidence, dry-run artefacts)
- `orchestration/units/R2-SGL-PREP.md` (this card)
- `orchestration/handoffs/R2-SGL-PREP.json`

Nothing else. No existing cell is edited; no existing test is edited. `experiments/**` is
read-only for this unit except that `state/config/variant_launcher.py` **imports** (never
rewrites) `experiments/context-cache/client.py` and the production spec
`state/config/occamy-inspect-pre.json`.

## Deliverable shape

1. `variant_launcher.py` — spec→argv clone (production spec is the only source of flags), dry-run
   default, one `Executor` seam (`MockExecutor` for tests, `SshExecutor` for live), stop-safety
   and restore-proof helpers that are *pure functions* of captured evidence.
2. `window_gate.py` — G0 in-cell gate: tokenizer offset, identical-request cache gate,
   pure-prefix repeat gate, grid parity, window-prefix continuity, request accounting.
   `run_gate(cfg, send, tokenizer)` where `send` is injected, so it is mock-testable.
3. `scratch/r2sglprep/selftest_offline.py` — the harness: green run + ≥3 red runs (mutations
   that MUST fail), each printing the assertion that caught it.
4. Handoff with the evidence lines.

## Kill condition

Any step that would issue `docker`, `ssh`, or an HTTP request to a live endpoint: do not run it.
Record the refused action and continue.

## Scope

Review → design → build → mock-test → report. Case management is the pipeline's job, not this card's.
