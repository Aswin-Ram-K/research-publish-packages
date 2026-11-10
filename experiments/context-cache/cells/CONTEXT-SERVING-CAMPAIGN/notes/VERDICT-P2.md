# VERDICT-P2 — independent recheck of measurement instrument (phase 2)

Verifier authored none of the code. All claims attacked.

## Per-claim verdicts

### 1. Arms (arms/) — REPRODUCED
Commands:
- `PYTHONNOUSERSITE=1 python3 -m pytest arms/tests/test_arms_contract.py -q` → `20 passed`
- gist content-free re-run over D1..D4 and H1..H4 (script in verification) → `leaked=[]` for all 8, masked turns 1..5.
- preamble parity: stripped (remove `ARM:` and `session=` lines) byte-identical across A/B/C/D (test passes).
- salt isolation: same salt byte-identical; different salt differs on exactly one `session=` line (test passes).
- renderer hashes (current, reproducible across 3 runs):
  - A `cbbdf0b0ea92051053638301c5c3fed1e964171caee237f65083f324b0cfaa47`
  - B `7b079fcb9d3267bccb9c64d06f762d81792d6ef4301d5b4068423e4f3164a6e8`
  - C `dcae2b6e7f9a0f9bdcf21880016964c317747c36354b759633c17898bcfc1eb0`
  - D `f64683f9aa5ee60901f6430304415b4b925a3e9541db205217ba351d5bdc9c37`
- Envelope `run/envelopes/CAMPAIGN.json` records stale renderer hashes (A `b9820abb...` etc.) → mismatch (see blocker).

### 2. Tasks (tasks/) — REPRODUCED
Command: `PYTHONNOUSERSITE=1 python3 -m pytest tests/test_campaign_tasks.py -q` → `18 passed`.
- determinism: `gen_instances.generate_all()` twice byte-identical; on-disk seed matches.
- two families per split, disjoint answer-key sets.
- every instance has >=6 turns with source turn <=6 dependency.
- `expect_exact_body` turns present and expected value absent from current event.
- reference artifact passes; 6 negatives (wrong answer, missing key, perturbed-seed hardcode, unresolved ref, outside write, network) fail; truncation → `ok:null`.
- bwrap containment engages (`bubblewrap` version ok; network/outside-write denied; inside-write allowed).

### 3. Driver (run/driver.py, freeze_envelope.py) — REPRODUCED (with caveat)
Commands:
- `PYTHONNOUSERSITE=1 python3 -m pytest tests/test_instrument_driver.py -q` → `13 passed` only after syncing envelope renderer hashes to current; with the committed (stale) envelope the same suite reports 9 `SystemExit: 1` from renderer-mismatch refusal.
- `--envelope` mandatory: subprocess with no args → nonzero (test_missing_envelope_exits pass).
- path escape/historical cell rejected: test_envelope_escape_rejected pass.
- freeze aborts on hand-supplied hash mismatch: test_freeze_aborts_wrong_hand_hash pass.
- renderer-mismatch refusal: test_driver_refuses_mismatched_renderer_hash pass (red→green below).
- stub ledger isolation + `synthetic:true`/`engine.mode=stub`: test_stub_campaign_2x1x3 pass.
- first-row audit: `run/state/preflight.first_row_audit.json` = `{"ok": true, "mismatches": []}`; compares envelope_path, max_tokens, phase, model, engine_fingerprint, seed as claimed.
- salt identical across four arms of a cell: code enforces `_cell_salt_key` equality; test_salt_cell_mode pass.
- serving_flags count = 51 tokens (49 option flags after `sglang serve`); health_check embedded in freeze with `ok` models/server_info.

### 4. Watcher/analyser fuses — REPRODUCED
Command: `PYTHONNOUSERSITE=1 python3 -m pytest tests/test_instrument_failclosed.py -q` → `8 passed`.
- 8 scenarios: missing rows, pre-row stall, killed watcher, cap exhaustion, injected alert, healthy run, uncertainty range, quality refusal.
- analyser excludes `synthetic` rows; null cache field → range (`..` in output) never `0`; refuses winner when an arm has fewer successful tasks than A; task/trajectory is the unit (paired_by line), turns not pooled as independent.

### 5. Ledger/quarantine honesty — REPRODUCED (with caveat)
Commands:
- `python3 ledger/ledger.py --ledger-dir ledger status --json` (dynamic; e.g. reserved 23 / spent 22 / voided 318 at verification time).
- `PYTHONNOUSERSITE=1 python3 -m pytest tests/test_campaign_ledger.py -q` → `6 passed`.
- 318 voids, single reason `synthetic stub run (engine=stub)...`; status computes spent as outcomes minus voids and reports `voided_by_reason`.
- journal: 984 lines (331 reserve + 330 record + 318 void + later probe records); append-only (voids appended in a 0.82s window; no edits); index_check OK.
- Exactly 2 real attempts predate quarantine: `vllm occamy smoke completion 1/2` (phase serving); all 318 pre-quarantine reserves are stub labels.
- Caveat: the documented predicate `^(preflight|context|prompt_format|serving|holdout):` matches 324 current reserves, including 6 real post-quarantine probes (`preflight:probe:*`, `preflight:A:D1:t1:answer`? no — the 6 are `preflight:probe:P1_cold...P4` plus `preflight:A:D1:t1:answer`). Re-running the void with the literal regex now would void real probe attempts. The quarantine itself was applied at void-time and is correct; the documented predicate is over-broad for the current journal.

### 6. Live preflight claims — PARTIALLY REPRODUCED
- 6 claimed attempt ids all present in `ledger/journal.jsonl` and `run/rows/preflight.jsonl` (D1 + P1/P2r1/P2r2/P3/P4); rows carry `cached_tokens=null` for all 6.
- first-row audit ok=true, mismatches=[]; compared fields as listed.
- `CACHE_FIELDS_UNRELIABLE` supported for those 6: all `cached_tokens` null.
- Server-side cross-check ("0 device hits" delta) is UNVERIFIED: no metrics snapshot was persisted (pins/logs has no metrics file); current `/metrics` shows device_hit=2432 but that reflects later traffic and cannot be attributed to the past. The report's claim goes beyond recorded evidence.

## Red→green log (one-line mutants)

(a) Gist content-freeness guard
- Mutant: `arms/render_arms.py` line `"bytes": len(b),` → `"bytes": body,`.
- Red: `PYTHONNOUSERSITE=1 python3 -m pytest arms/tests/test_arms_contract.py::test_gist_is_structural_and_content_free -q` → `FAILED ... content leaked in gist: delta-1 in ...` (1 failed).
- Restore: `cp /tmp/render_arms.py.bak arms/render_arms.py`.
- Green: same command → `1 passed`.

(b) Analyser null-vs-zero handling
- Mutant: `run/analyse.py` `any_null_cache = any(...)` → `any_null_cache = False` and `total_cached = sum(int(_cached(r)) ...)` → `sum(int(_cached(r) or 0) ...)`.
- Red: `PYTHONNOUSERSITE=1 python3 -m pytest tests/test_instrument_failclosed.py::test_7_uncertainty_range -q` → `FAILED ... TypeError: int() argument must be ... NoneType` (1 failed).
- Restore: `cp /tmp/analyse.py.bak run/analyse.py`.
- Green: same command → `1 passed`.

(c) Driver renderer-mismatch refusal
- Mutant: `run/driver.py` `if exp is not None and live != exp:` → `if False and exp is not None and live != exp:`.
- Red: `PYTHONNOUSERSITE=1 python3 -m pytest tests/test_instrument_driver.py::test_driver_refuses_mismatched_renderer_hash -q` → `FAILED ... AssertionError: expected refusal` (1 failed).
- Restore: `cp /tmp/driver.py.bak run/driver.py`.
- Green: same command → `1 passed`.

## Blocker
Stale envelope: `run/envelopes/CAMPAIGN.json` renderer hashes (A `b9820abb...`) do not match the current arms source (A `cbbdf0b0...`), so `run/driver.py` fail-closes on every dispatch (`refuse: renderer hash mismatch`) and 9/13 driver tests only pass after a temporary re-freeze. Downstream live phases cannot run until the envelope is re-frozen; the re-freeze also changes `freeze.envelope_sha256`. Secondary: the documented quarantine predicate is over-broad relative to the current journal and must not be re-run verbatim.
