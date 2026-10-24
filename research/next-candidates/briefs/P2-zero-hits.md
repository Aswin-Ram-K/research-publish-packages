# P2 — Zero hits: what `cached_tokens` can and cannot tell you

> **Prospective and unapproved.** Derived only from `research/next-candidates/2026-10-24-sweep.md`;
> it authorises no request, lock or restart. Every number is quoted from that memo.
## Objective
Make "zero cached tokens" a measurement with a meaning: show that a cached-token zero has at least four
distinct causes, that a hit rate is unmeasurable without the `usage_has_details` flag, and that A1's
0/64 battery result is an observed miss rather than a cache failure — with one re-launch.
## Why now
- `experiments/context-cache/cells/R2-VLLM/` is the only clean instrument: 418 rows,
  `usage_has_details` 418/418, `cached_tokens == None` on 0 rows, arm identity 4/4 distinct in 64/64
  groups, 256/256 battery rows label-carrying.
- Battery repeat hits **OH1 62/64** (A 15, C 16, R 16, H 15) vs **A1 0/64** (0/128 rows); both cold
  passes 0/64; A1's **27** hits are all `arm:null` probe rows of the same launch.
- **WIN-VLLM V2**, same model and same 1056 block, reports a hit rate of **0.868144**.
- `cells/CX-V2/null_coerce.py`: **49/97** U2 and **23/438** U4 usage records were null-coerced;
  **0/5** core row files retain `usage`/`prompt_tokens_details`.
- vLLM 0.27.1 `serving.py:95-96` reports an absent flag as `None`, never `0`; `status` vs
  `http_status` is a second naming trap.
- The in-flight `R2-VLLM-FIX/OH1` 284-row cell (22:43, all 200, hits A 31 / C 38 / H 29 / R 66) is
  identity-less and is analysed only after `POLL-VLLM` settles.
## The four meanings of a cached-token zero
| # | Meaning | Signature |
|---|---|---|
| 1 | flag absent | `None`, never `0` (vLLM 0.27.1 `serving.py:95-96`) |
| 2 | status-name mismatch | `status` read where `http_status` is written |
| 3 | observed miss | `0/128` rows with `usage_has_details: true` (A1) |
| 4 | coercion of absent to zero | 49/97 U2 and 23/438 U4 records (`null_coerce.py`) |
## Design / arms
One A1 re-launch at `--gpu-memory-utilization 0.34`, plus an offline diff of A1 vs V2 launch records
and grid probes (**0 requests**).

| Arm | Content | Purpose |
|---|---|---|
| A1-R | the battery repeat that produced 0/64 | does the zero reproduce with the flag on? |
| A1-P | probe rows of the same launch | prove the cache path works (27/27 earlier) |
| A1-S | short-prompt repeat pair | separate length from policy |
| A1-T | `/tokenize` round-trip | close the tokenizer-count explanation |

**Budget: ~150 requests** total, one launch, no restart.
## Gates / controls
- **Flag first:** `usage_has_details` true on every new row; `cached_tokens` verbatim (`None` stays
  `None`), and another file's zero is not comparable.
- **Identity:** arm distinct per group; cold pass precedes every repeat; same model and same 1056
  block pinned, build recorded before launch.
- **Offline diff first:** the launch and probe records are diffed before spending requests; a
  difference found there can cancel the re-launch.
- **Ordering:** the in-flight 284-row cell is not analysed until `POLL-VLLM` settles.
- **No cap trip:** reuse the 260 cap and report a trip rather than editing rows.
## Kill condition
If the flag is missing or arm identity is unrecoverable, stop and report an instrument failure — do
not interpret a zero. If A1 at 0.34 still shows 0/64 with the flag true while A1-P hits, report a
genuine configuration effect: the methods paper stands, the systems claim shrinks.
## Deliverable
- The four-meaning table as the paper's centrepiece, with one row-level reproduction per meaning.
- `analysis.json` for the offline diff and the re-launch; `CLAIMS.md` rows the paper can cite; a
  methods-paper draft; and a contracted-shape handoff naming artefacts and evidence commands.
## Proposed write paths (future unit)
- `experiments/context-cache/cells/ZEROHIT/plan.md` — pre-launch diff scope; `rows*.jsonl` — new rows
  only (R2-VLLM rows stay frozen); `analysis.json` — diff and re-launch tables.
- `orchestration/units/ZEROHIT1.md` — the unit card; `orchestration/handoffs/ZEROHIT1.json` — handoff.
## Open risks
- Attribution may be mundane eviction at 0.15 gpu-mem; the methods point survives, the systems claim
  shrinks.
- The box window is shared with P1: one lock, one restore proof, sequenced not interleaved.
- The 0.868144 comparison is same model/block but a different cell — not a control.
- The claim is version-specific (vLLM 0.27.1), and `POLL-VLLM` may delay both the 284-row cell and
  the re-launch.
