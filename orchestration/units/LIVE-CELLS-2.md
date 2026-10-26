# LIVE-CELLS-2 — locate the engines, then take three cells

Status: **done**. Bound 24 calls, used 16. Rows: `experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl` (27 rows, none edited).

## Phase 1 — locate
- `ss -ltn`: **no** listener on 8012/8014/8016/8017/8020 on this host.
- `127.0.0.1:8012` -> curl exit 7; `127.0.0.1:8014` -> curl exit 7 (refused in 0.0001 s).
- `192.168.2.168:8012/get_server_info` -> 200, `occamy-1.0-NVFP4`, ctx 131072.
- `192.168.2.168:8014/v1/models` -> 200, `qwen3.5-9b`, max_model_len 32768; `/metrics` live.
- **Verdict: the engines were never down - they bind a non-loopback interface.** The earlier probe looked in the wrong place.

## A — SGLang residue-0 warm (C1): P1 = 384, 3/3 reps
- prime 384 (cold) -> identical re-send 384: `cached_tokens` **null (= 0) in 3/3 reps**. SGLang returns `prompt_tokens_details` but omits `cached_tokens` when it is 0, so null is a measured 0, not "unreported".
- append L=13 -> P1 **397**, `cached_tokens` **320** in 3/3 = `(397//64-1)*64`.
- => at residue 0 the boundary-aligned prefix is re-billed whole although its blocks are resident: the very next append hits 320. Same shape as vLLM G6 residue 0 (cached 0, then append cached 5280). **C1 has its SGLang row.**

## B — compact index, UNPADDED (C5)
- compact envelope 408 bytes (full 472), 12 lines, no padding.
- **P1_E = 260 in 3/3 sends; R_E = 260 mod 64 = 4**; cached null then 256.
- => the unpadded compact index lands on residue **4**, not 2: padding to 2 is load-bearing, not free.

## C — vLLM G6 residue 1 (C2), P1 = 7393, B = 1056, 7393 mod 1056 = 1
| row | P1 | cached | ttft_server_s |
|---|---|---|---|
| prime | 7393 | 0 | 2.0017 / 2.0000 |
| identical re-send | 7393 | **6336** | **0.2044 / 0.2069** (warm) |
| append L=13 | 7406 | **0** | **1.7701 / 1.7733** (cold) |
- vs the cited 7394 warm row (0.210802 / 0.211353), append-vs-same: **8.40x / 8.41x**; append-vs-append (0.213763 / 0.212416): **8.28x / 8.30x** - beside the measured 8.5x.
- identical re-send vs the cited 7394 warm row: **0.97x / 0.98x** - no penalty.
- => **residue 1 misses only across the append, never on a re-send.** The failure is prefix *matching* across an append, not block insertion. C2's "residue 1 misses" should read "residue 1 misses on append". **C2's G6 gap is closed.**

## Note
- The first cell-A batch ran off-target (366/365) from a word-slice bug; those rows are kept (append-only contract) and marked `supersedes_offtarget_attempt`. Rep 2 was re-solved offline against `/tokenize` (framing F=22), so all three delivered reps sit at exactly 384.
