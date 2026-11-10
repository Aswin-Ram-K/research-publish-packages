# U-SPCC-55 — the world index advertises the refs the fetch tool accepts

Status: COMPLETE

## Target
`experiments/ptr-engine/longrun/run_longrun.py` (`index_lines`),
`experiments/ptr-engine/longrun/arm_cd.py` (`spcc_world_index`, new `world_index_lines`),
`experiments/ptr-engine/longrun/tests/test_index_refs_are_fetchable.py` (new).
No other path touched. `ptr_engine/layers.py` was NOT changed: it joins and sorts
`index_lines` and never parses the line text, so the layer contract is untouched.

## Defect closed
The index was the only place the model learned which refs exist, and it named a
namespace the fetch tool does not accept. `index_lines` emitted
`- @knowledge:{item[id]}@1 {hash8} {len}` — item ids in the `@knowledge:` namespace —
while the fetch tool resolves `make_ref` refs, `{doc_id}@r{revision}`
(`ptr_engine/pointer_table.py:19-21`). Measured consequence: 12 of 25 fetch attempts
used a ref that does not exist (`ptr_engine/resolve.py` ×4, `knowledge/item-1@1` ×3,
`knowledge/doc-fact-02.txt`, `knowledge/doc-fact-02@r1`, `knowledge/doc-fact-04.md`,
`knowledge/doc-fact-06@r1`, `knowledge/item-1`). The model was guessing at a namespace
it was never shown.

## Changes
1. `arm_cd.world_index_lines(fixture, turn=1)` — one line per ref the fetch tool accepts
   at `turn`, derived from the SAME pointer entries `service_fetches` builds its table
   from (`ArmCDState._doc_entries`), filtered to `state == "live"`. A ref the fetch tool
   would answer `NOT_FOUND` / `STALE_OR_REVOKED` / `SCOPE_UNGRANTED` is not part of the
   addressable world and is not advertised. Line shape `- {ref} {hash8} {bytes}`: the
   ref, a short digest and the body size in bytes, no body text (no fact-value leak).
2. `run_longrun.index_lines` now renders `arm_cd.world_index_lines(fixture)`.
3. `arm_cd.spcc_world_index` now returns the same lines, so the SPCC arm's L1 and the
   masking/fetch arm's index are byte-identical for the same fixture. It previously
   emitted `@knowledge:<id>@r1~<tokens> scope=default` and `@doc:<id>@r<rev>~<tokens>
   scope=default` — a third namespace, also unfetchable. Its `tokenizer` parameter is
   retained for the L1 call site and is now unused (the line carries bytes, not tokens);
   the now-unused `token_len` import was dropped from `arm_cd.py`.

## Index line format
Before: `- @knowledge:item-1@1 5021bb84 33` (1 line, 0 fetchable)
After:  `- doc-config@r1 e89a5778 85` … 13 lines, all fetchable

## Unchanged
The fetch tool, the answer contract, the scoring, the per-turn cap and the per-arm pool.
`doc-secret@r1` (ungranted), `doc-revoked@r1` after turn 5, `doc-versioned@r1` after
turn 20 and `doc-versioned@r2` before turn 20 are still reachable by a guessing model and
still return their declared outcomes — they are simply not advertised as addressable at
the cell's opening turn.

## Comparability
This changes the prompt bytes for BOTH arms (the index is L1 and shared). No result
measured before this commit is comparable to one measured after it.
