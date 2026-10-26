# REACHABILITY-MATRIX — was the planted fact ever in the pointer arm's prompt?

Unit: `PLANT-REACHABILITY` · fixture `experiments/ptr-engine/longrun/tasks-v3/runtime-v3/LR-01.v3.json`
(sha256 `07abab0bd902bd88c86b8d2544f012caf63a9a4280b68b223bd605d399bd3e0b`, the sha stamped on
every settled row) · rows `experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.jsonl`
(96 rows, 48 per arm, settled) · turns 12 / 24 / 46, rep 1.

## Method — `imported-runner`

`experiments/ptr-engine/longrun/tools/prompt_at_turn.py` imports `run_longrun` (unmodified),
replaces `run_longrun.send_chat` with a recorder that **raises `WouldSend(payload)`** when the
requested turn is reached, and drives `run_longrun.run_cell` itself for turns 1..N, feeding it the
canned assistant reply each turn actually produced (taken verbatim from the settled rows). Prompt
construction is the runner's own `Planner.build` inside its own production loop — not a
re-implementation. Fallback path (`direct-builder`) was **not** needed.

Provenance: for every replayed turn the tool compares `sha256(user content)` against the
`prompt_sha256` stamped on that turn's settled row. **0 mismatches in all six cells** (12 / 24 / 46
turns checked per cell) — the materialised prompt is byte-identical to what the endpoint received.

No-HTTP proof: `urllib.request.urlopen`, `urllib.request.build_opener`,
`http.client.HTTPConnection.connect`, `http.client.HTTPSConnection.connect` and
`socket.create_connection` are patched to raise `AssertionError` before the runner is driven; the
run prints `NO-HTTP PROOF ok: 5 clients patched, network_attempts=[], requests_sent=0`.
Job 2's re-grade (`grade_v3.py`) is offline by construction and was run in a separate process.

## The six cells

| arm | turn | `fact_planted_in_prompt` | `expected_value_in_prompt` | `answer_observed` | `reachable` |
|---|---|---|---|---|---|
| transcript-grow | 12 | **true** (plant *instruction text* only, see note) | **false** — `64` grep count **0** | `I'll read the specified lines of resolve.py. / ANSWER: NOT-AN-ANSWER` | **FALSE** |
| transcript-grow | 24 | **true** (same, text only) | **false** — `31` grep count **0** | `I'll read errors.py to count Ptr* error classes. / ANSWER: NOT-AN-ANSWER` | **FALSE** |
| transcript-grow | 46 | true | **true** — 289 anchor hits (`ledger` 41, `record` 51, `scope` 75, `refusal` 26, `code` 38, `serialized` 1) | `I'll read resolve.py to answer T46. / ANSWER: NOT-AN-ANSWER` | **TRUE** |
| pointer-stable | 12 | **false** | **false** — `64` count **0** | `I need to read the full resolve.py to find the default per-turn resolve budget. Let me look at line 39 and surrounding context. / ANSWER: NOT-AN-ANSWER` | **FALSE** |
| pointer-stable | 24 | **false** | **false** — `31` count **0** | `I need to count the Ptr* error classes defined in errors.py. Let me read that file. <tool_call>READ@1@ptr_engine/errors.py@1-331 … <tool_call>RUN … grep -n "^class Ptr" … / ANSWER: 7 / ANSWER: 7` | **FALSE** |
| pointer-stable | 46 | false | **true** — 168 anchor hits (`ledger` 40, `scope` 60, `code` 20, `refusal` 5, `record` 4, `serialized` 1) | `I cannot answer from the pinned body because resolve.py is truncated at the PtrUnknownIdError( raise (around L66), so lines 66–71 are not available to read. / ANSWER: NOT-AN-ANSWER` | **TRUE** |

Prompts materialised: transcript-grow 8,774 / 11,213 / 16,106 B at T12/T24/T46; pointer-stable
6,864 / 6,815 / 6,878 B.

Counting rule: `64` and `31` are counted with digit boundaries (`(?<![\d.])31(?![\d.])`) because
body headers print byte lengths — the `errors.py (331 B)` header would otherwise be a false hit for
`31`. Prose checkpoints (`cp.t46`) are counted on the grader's own anchor split
(`anchors_of(expected)`, len ≥ 4, all anchors required).

## Why `fact_planted_in_prompt` is true for transcript-grow but plants nothing

The fixture's turn-2 is the `kind: "plant"` turn, but its text is **not a fact**:

```
Read ptr_engine/resolve.py#L66-L110 and list every raise site, noting which are inside the
recorded block. (fact stated here for later checkpoints: see checkpoints[].source)
```

It delegates the fact to `checkpoints[].source` — a *path*, not content. transcript-grow replays
turn-2's user block, so that sentence is in its prompt; pointer-stable's tail carries only the last
three **answers**, so even that sentence is absent. Neither arm ever received a value.

## The shared base carries neither checkpoint 1 nor checkpoint 2

`working_set_block(fixture)` — the 4 pinned item bodies, present in **both** arms' prompts — is
6,339 B and contains **`64`: 0 hits, `31`: 0 hits**, at every turn:

| turn | transcript-grow shared base `64` / `31` | pointer-stable prefix |
|---|---|---|
| 12 | 0 / 0 | same 4 bodies, 0 / 0 |
| 24 | 0 / 0 | same 4 bodies, 0 / 0 |
| 46 | 0 / 2 (incidental) | same 4 bodies, 0 / 2 |

The pinned slices are why:
`resolve.py` (1,680 B) starts at `def _refuse(ledger: Optional[Ledger], scope_name: str, text: str,
error: PtrError) -> None:` and contains no `budget` line at all — `checkpoints[0].source` is
`resolve.py#L39`, which is **outside** the pinned slice (`#L66-L110`).
`errors.py` (331 B) contains **3** `class ` declarations and ends mid-declaration
(`…class PtrBodyMismatchError(PtrError):`), so the 31-class count of `#L15-L142` is **not
derivable** — the slice is truncated before the model can see the classes it was asked to count.

## What this settles

- CP1 (t12, `64`) and CP2 (t24, `31`): **the answer is in neither arm's prompt**. The pointer arm's
  t12 failure is *not* a pointer-design reachability defect — the control arm is equally blind, and
  the grader's phrase "no 64 and it was never in context" is **confirmed and is arm-independent**.
  It is a fixture defect: the plant turn carries a citation, and the pinned working set omits the
  cited lines (L39) and truncates the cited file (errors.py L15-L142).
- CP3 (t46): **both arms are reachable** (289 / 168 anchor hits — the `_refuse` body with
  `ledger.record_refusal(scope=…, serialized_ref=text, code=error.code)` is the *first* thing in the
  pinned `resolve.py` slice) and **both arms answered `NOT-AN-ANSWER`**. The pointer arm's stated
  reason is factually inverted — it claims `resolve.py` is truncated at `PtrUnknownIdError(` (L66)
  "so lines 66–71 are not available", while the slice it was given *begins* at `_refuse` and the
  call it denies seeing is present verbatim. That cell is **behaviour-under-reachability**.
