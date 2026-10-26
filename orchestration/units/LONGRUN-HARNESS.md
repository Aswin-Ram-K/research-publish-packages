# LONGRUN-HARNESS — run_longrun.py (four arms), dry-run proven

**Status:** done · **Bound:** 24 tool calls · **Zero requests sent.**

## Deliverable
`experiments/ptr-engine/longrun/run_longrun.py`: one (task × arm × rep) cell per run; one NDJSON row per request into `measure/rows-longrun-<date>.jsonl`; frozen manifest under `longrun/manifests/` before turn 1 (absent manifest ⇒ abort, exit 3).

## Arms
- `transcript-grow`: replays all history; FIFO-truncates at the 64k cap (first truncation T23 on the test fixture).
- `transcript-compact`: replay until 64k, then one ~700-token digest request replaces older turns; recent 4 raw (digests at T23/T53).
- `pointer-stable`: byte-identical index+bodies prefix (prefetch one body/turn), frozen from T12; tail = state line + new note + question.
- `lease-reopen`: host-side close at [23,56]; reopen with pointer index + ≤400-tok distilled state + current turn.

## Proof (offline)
- `--dry-run` exit 0; 242 requests for 4×60 turns + 2 B digests; 12/12 preview bodies sha-verified; 4 manifests written.
- Previews: A≡B 0/3 (identical by design pre-wall); every other pair 3/3 differ.
- `--self-test`: None→0 (SGLang), None→null (vLLM), one function (`normalize_cached_tokens`, L98).
- Manifest abort: `--manifest-path /proc/...` → exit 3 before any prompt; no network, no row.
- Fixture tree is a stub ⇒ constructed `/tmp/longrun-fixture/LR-01.json` (schema `consonance.longrun-fixture/1`) was used; the real fixture is card 2a6c4761's.

## Not done
- Live path never executed (no network by instruction). `--stream` uses `include_usage`; usage absence is recorded as null with `usage_missing`, not imputed.
- Proposed budget: 2,880 core + 24 B digests + 36 repair reserve + 4 controls = **2,944 requests**, NOT RUN.

## Evidence
`orchestration/handoffs/LONGRUN-HARNESS.json` (full command/output list).

## Next
- Operator authorises 2,944; then run LR-01..LR-06, reps 1–2, and score with `score_longrun.py` when card b16be695 lands.
