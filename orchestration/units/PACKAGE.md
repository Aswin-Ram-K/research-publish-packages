# PACKAGE — assemble the publishable package

**Status:** done · **Trigger:** board one-shot 2026-10-23T11:45:20Z (America/Chicago)
**Gate:** `orchestration/handoffs/X-SYNTH.json` status=done — CONFIRMED.
**Bound:** 50 tool calls / 0 live requests / 90 min. Used: 26 calls, 0 live requests.

## Purpose (one)
Assemble the publishable package from the revised manuscript. No re-measuring, no re-arguing a claim.

## Read
`AGENTS.md`; `papers/context-cache/{MANUSCRIPT,CLAIMS,EVIDENCE,GAPS}.md`, `RUN.json`;
handoffs `X-SYNTH`, `V-XSTACK`, `WIN-SGL`, `WIN-VLLM`, `WIN-TUNED`, `M4-EVICT`.

## Write paths (declared)
`papers/context-cache/PACKAGE.md`, `papers/context-cache/READER-MAP.md`,
`papers/context-cache/verify_package.py`, `orchestration/units/PACKAGE.md`,
`orchestration/handoffs/PACKAGE.json`.

**Not touched:** `experiments/**`, `state/**`, any cell, `GAPS.md`, `MANUSCRIPT.md`.

## Result
- `verify_package.py` rewritten so claim ids come from `CLAIMS.md` alone (the old parser read
  the same table format from either file and could not distinguish them); claim ids are now
  regexed as row-starting `| Cnn |`, and functions resolve via `def` **or** `FUNCS`/`SPECIAL`
  dispatch (needed for `grid_guard` = C61).
- `READER-MAP.md` header documents the columns; all 62 rows already present, each exactly once.
- `PACKAGE.md` rewritten: negative results stated as results (pager no-op, HiCache no-go,
  chunked-prefix cannot start, vLLM 3.1×, slru≡lru, 1.700× decomposed), stale counts corrected.

## Evidence
- `recompute.py all` → `59 claims checked, all match` + `GRID GUARD PASS  7/7 configs`, exit 0.
- `u5_recon.py` → 760/760 byte-identical, retention 2280/2280, gold line 190/190 vs 0/190, exit 0.
- `u4_recon.py` → head 44/44 both arms, body digest equal 11/44, `NAIVE_APPEND`, exit 0.
- `verify_package.py` → PASS, 62/62 mapped 1:1, exit 0.
- Red→green: C52 removed from a copy → exit 1 (`missing claim ids in READER-MAP: C52`);
  restored → exit 0. Also red on a nonexistent function and on an absent cell.

## Notes
The pre-existing package understated its own claim count (52/54/58 in different places, handoff
said "50 claims checked"). `CLAIMS.md` holds 62 claim rows; `recompute.py` holds 59 stored-value
claims; C01/C16 are external scripts; C61 is the guard. 59 + 2 + 1 = 62.
