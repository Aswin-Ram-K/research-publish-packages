# Prompt Engine v1 — stable-prefix context compiler

Implements `experiments/ptr-engine/ptr_engine/layers.py::compile_prompt`.

## Layers (byte-stable from the front)

| Layer | Content | Rewritten |
|---|---|---|
| L0 CONTRACT | system text, canonicalised tool schema (sorted keys, no whitespace variance), answer grammar, frozen `RUN` header (model id, fixture id, generation) | never within a run |
| L1 WORLD INDEX | sorted lines `@kind:id@rev ~{tokens} {scope}` for every addressable object | only at a compaction boundary |
| L2 JOURNAL | append-only `T{n}|{role}|{content}` plus refs emitted that turn | never (append only) |
| L3 WORK | current task question, then fetched bodies in arrival order | every turn, always last |
| L4 CONTRACT-LINE | the answer-contract line | per arm |

## Line formats

Journal line: `T{n}|{role}|{content}` — pipe-delimited, no trailing spaces, one line per turn; multi-line content escaped by replacing `\n` with `⏎`.

World index line: `@doc:key@r1~312 scope=default` — sorted lexicographically by the reference string so the index is deterministic.

Example index lines:
```
@artifact:plan@3~12 scope=default
@doc:key@r1~312 scope=default
@knowledge:k03@3~48 scope=default
```

Example journal lines:
```
T1|user|what is the goal?
T2|assistant|fetch @artifact:plan@3
T3|assistant|T⏎second line
```

## Epoch / compaction rule

Every `COMPACT_EVERY = 24` turns, fold L2 into a single summary block appended to L1, increment `epoch`, reset the journal to empty, increment `compactions`. Compaction is the only permitted prefix break and never fires mid-turn. Fetched bodies enter L3 only, so a fetch can never invalidate the cached prefix.

**Journal lifecycle is owned by `compile_prompt`, not by the caller.** The `journal`
argument carries only the lines for the current compile (normally one
`T{n}|{role}|{content}` line for the turn); the function APPENDS them to
`CompactionState.journal`, checks the `COMPACT_EVERY` boundary, and returns the
post-compaction state. A caller must never re-pass lines that were already folded —
that would duplicate history and re-fire compaction one turn early. After a
compaction, `state.journal` is empty and the folded history lives in
`state.index_lines` as one summary block.

`prefix_sha256` is the hash of the **cacheable prefix**, `L0+L1`. `L2` is the
append-only tail: appending to it extends the cached prefix without rewriting any
byte already cached, so within one epoch the metric that must be constant is
`L0+L1`; the sole permitted change is compaction, which rewrites `L1` (it appends
the summary block and resets `L2`). Hashing the growing `L2` would report a change
on every append and could not distinguish a legitimate append from a destructive
rewrite. `L0` is emitted once per run and hashed in the run's own
`CompactionState`; any byte difference between two turns of the same run raises
`PtrPrefixDrift`. Callers that reuse a process across independent runs call
`reset_prefix_state()` (the authoritative baseline now lives on the state object).


## Answer contract

Keeps the four spelled-out kinds already in use:
- `ANSWER: NUM <int>`
- `ANSWER: TEXT <value>`
- `ANSWER: CALL <callee>(<kwargs>)`
- `ANSWER: NONE`

Out-of-vocabulary stays ungradeable and is never counted as an abstention. Tool calls are never wrapped in an `ANSWER:` line; a text-form fetch request is accepted only in strict mode as `protocol_variant=text_call` with `ref_as_emitted` recorded.

## Why this design exists

Measured: masking a body past an eviction boundary scores 0/48 on both stacks (8/48 total, from the d=2 bucket only), while bounded fetch scores 41/48 on `:8012` and 42/48 on `:8014` on single-fact recall. The failure is structural — content evicted and the cache prefix broken — not a model limitation. Separately, Consonance measured that cutting payload 24.2% realised only 2.4% billed saving, because per-step rewriting destroyed the cache (0 cached tokens at every step), while append-only context climbed to 0.489 hit rate. This compiler makes the prefix byte-stable so the cache survives.