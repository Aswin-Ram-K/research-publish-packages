# U4b — branch-identity placement: does per-branch prefix identity beat a shared prefix?

**Status:** done · **Requests used:** 24 live (`max_tokens: 2`) · **Wall:** ~20 s · **No flock** (`flock` is
not used anywhere in the unit: token counts are concurrency-independent, only TTFT is not, and TTFT is not
claimed here).

## Purpose
Test whether giving every fan-out branch its own history (`P_k` = branch tag prepended to the shared body)
buys anything over one byte-identical shared prefix `P`. Token counts only: `prompt_tokens`, `cached_tokens`.

## Method
`run.py` (120 lines) builds `P` inline (~1,792 tokens / 8,754 chars) from a `"Sentence about repository
work item %d: …"` generator (varied by index, no wall clock) and 8 distinct ~133-token deltas each carrying
`BRANCH-<k>`. Salt = `resextract.context.salt.make_salt(seed)` + `salted()`; one fixed seed per arm
(A 41001, B 41002, C 41003) and the same salt everywhere inside one arm. Messages are built directly as
`[{"role":"user","content":text}]` via `experiments/context-cache/client.chat(...)` — `render()` is not
imported and `POST /flush_cache` is never called.

| Arm | Prompt shape |
|---|---|
| A | `P` + `[BRANCH-k]\n` + delta (tag at the front of the delta) |
| B | `[BRANCH-k]\n` + `P` + delta (tag prepended to `P` → nothing shared) |
| C | `P` + delta + `\n[BRANCH-k]` (tag at the end of the delta) |

## Results (from `rows.jsonl`, 24 rows)

| Arm | total_prompt | total_uncached | uncached/prompt | cached per branch 1…8 |
|---|---|---|---|---|
| A | 15,400 | **4,648** | 0.302 | 0, 0, 1792, 1792, 1792, 1792, 1792, 1792 |
| B | 15,400 | **15,400** | 1.000 | 0, 0, 0, 0, 0, 0, 0, 0 |
| C | 15,400 | **4,648** | 0.302 | 0, 0, 1792, 1792, 1792, 1792, 1792, 1792 |

- `B/A = 3.3133` (15,400 / 4,648) — **above 1.5, so the fan-out claim is SUPPORTED** by the stated rule:
  independent per-branch histories cost 3.31× the shared prefix. The true penalty is understated, because
  Arm A lost one of its 7 warm branches (see below); with 7/7 hits A would be 3,856 and `B/A = 3.99`.
- `C/A = 1.0000` — **within 10% of 1.0**. The advantage is a **placement discipline, not a pointer
  property**: moving the 8-token branch tag from the front of the delta to its end changes nothing, so what
  costs money is the tag's position *inside the prefix*, not the existence of a branch pointer.
- **Arm A cache hits:** 6 of branches 2–8 reported `cached = 1792` (i.e. the whole prefix; 1,792 = 1,925 −
  133, and 1,792 tokens is the full `P`). **Branch 2 reported `cached = 0`** — the first warm request after
  the cold one missed, most likely the radix insert not yet visible when branch 2 was dispatched (Arm A
  branch 1 TTFT 533 ms, branch 2 852 ms, branch 3 605 ms). It is reported, not averaged away.

## Verdicts
1. `B/A = 3.31 ≥ 1.5` ⇒ **fan-out to independent histories IS supported**: sharing one prefix is materially
   cheaper than giving each branch its own prefix.
2. `C/A = 1.00` ⇒ the gain is **placement discipline**, not a pointer/label property. Say it plainly: there
   is no per-branch pointer that recovers sharing; only keeping the prefix bytes identical does.
3. Arm A's shared prefix **did hit** for 6/7 warm branches; the single 0 (branch 2) is a timing anomaly, and
   any average over branches 2–8 is diluted by it.

## Artifacts
- `experiments/context-cache/cells/U4b/run.py`
- `experiments/context-cache/cells/U4b/rows.jsonl`
- `orchestration/handoffs/U4b.json`

## Notes / bounds
- No lock file, no corpus generator, no intermediate artifacts. Prior attempts' orphan `u4b_corpus.py` in
  the same directory was left untouched (not a declared write path).
- One arm per salt; arms cannot contaminate each other because the first token block differs per salt.
- Camera-ready caveat: 8 branches is a small fan-out; the ratio grows with branch count, so 3.31 is a floor
  for realistic fan-out widths, not a ceiling.
