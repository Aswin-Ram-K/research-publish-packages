# REACHABILITY-V4 — LR-01 slice repair (`v4-slice-widened`)

**Unit:** `FIXTURE-REACHABILITY-FIX` · **Requests sent: 0** · **Live runs: 0**
**Question this answers:** are the three LR-01 checkpoints answerable from the material a
long-run arm actually receives? The v3 answer was **no for CP1 and CP2 in both arms**; the
fixture, not the arms, was the defect.

## 1. What a correct answer requires (established from the pinned material, not asserted)

| CP | turn | question | correct answer | where it must come from |
|---|---|---|---|---|
| 1 | 12 | default per-turn resolve budget | `64` | `ptr_engine/resolve.py:39` — `DEFAULT_MAX_REFS = 64` |
| 2 | 24 | how many `Ptr*` classes `errors.py` defines | `31` | the whole class block `ptr_engine/errors.py:15-250`; `grep -c '^class Ptr'` = 31 |
| 3 | 46 | what `_refuse` calls and passes | `ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), before re-raising` | `ptr_engine/resolve.py:66-71` (`_refuse` body + docstring "before re-raising") |

v3 pinned `resolve.py#L66-L110` (starts at `_refuse`, so **no L39**), `errors.py#L114-L126`
(ends inside the 3rd declaration, 20 of 31 classes exist only up to L142), i.e. neither value
was in any materialised body. Confirmed against `adapt_fixture.slice_pointer`, which is an
inclusive 1-based line slice — nothing is inferred beyond the pointer.

## 2. The v4 tier

Files: `longrun/tasks-v4/LR-01.v4.json` (authored, `consonance.fixture/1`),
`longrun/adapt_v4.py` (adapter), `longrun/tasks-v4/runtime-v4/LR-01.v4.json` (runtime,
`sha256:5a5f8c4be2027c53038ae31b4db60ebbae03996a5a650d8fb4fe6d872df5e235`).

Only the two slice pointers moved, plus the L-range quoted in the CP2 question (which cited
`#L15-L142`, the truncated range — keeping it would have asked for a count the cited range
cannot produce):

| source | v3 pointer | v4 pointer | body bytes (v4) |
|---|---|---|---|
| `resolve.py` | `#L66-L110` | **`#L36-L110`** | 2785 |
| `errors.py` | `#L114-L126` | **`#L15-L250`** | 6353 |
| `test_scope.py` | `#L16-L80` | unchanged | 2598 |
| `test_negative_controls.py` | `#L80-L117` | unchanged | 1412 |

Unchanged, verified byte-for-byte in the authored diff: `answer_marker.required` and its
sentence, the 150/400-word budget block, all 48 turns (except the CP2 parenthetical), the
repair trap at T30, the three negative constraints, the three checkpoint `expected` values,
and **all twelve `checks_structured` ids and specs**. No corpus file was edited: the source
`sha256` values are the v3 ones and `adapt_fixture.load_items` re-verified every digest.
`fixture_version` changed `v3-answer-marker` → **`v4-slice-widened`** — that is the recorded
fixture-version change; `checks_changed: []`.

**CP1 trade-off (recorded, not hidden).** `64` is *not* written anywhere new: the slice was
widened from L66 down to L36 so the verbatim line `DEFAULT_MAX_REFS = 64` (L39) rides in the
pinned body. It remains a retrieval test — the value is still only in the source, and the
question turn does not state it.

## 3. Before / after matrix (same four fields per cell, same materialiser)

Before = the PLANT-REACHABILITY measurement on `runtime-v3`; after = this unit's re-run of
`longrun/tools/prompt_at_turn.py` on `runtime-v4` (both arms × 12/24/46).

| arm | turn | before: fact in prompt | before: expected present | before: reachable | after: fact in prompt | after: expected present | after: reachable | how |
|---|---|---|---|---|---|---|---|---|
| transcript-grow | 12 | yes | no (`64`×0) | **no** | yes | yes (`64`×1) | **yes** | preloaded (`DEFAULT_MAX_REFS = 64`) |
| transcript-grow | 24 | yes | no (`31`×0) | **no** | yes | no literal (`31`×0) | **yes\*** | resolvable — 31 `^class Ptr` in body |
| transcript-grow | 46 | yes | yes (289 anchors) | yes | yes | yes (476 anchors) | yes | preloaded |
| pointer-stable | 12 | no | no | **no** | no | yes (`64`×1) | **yes** | preloaded (all four bodies are in the frozen prefix) |
| pointer-stable | 24 | yes | no (slice 3 classes) | **no** | yes | no literal (`31`×0) | **yes\*** | resolvable — 31 `^class Ptr` in body |
| pointer-stable | 46 | yes (168 anchors) | yes | yes | yes (355 anchors) | yes | yes | preloaded |

\* `resolvable-not-preloaded`: `31` is a **count of declarations**, so no digit appears in the
source text — not before, not after, and no honest widening can manufacture one. What changed
is that the body is now *complete*: every one of the 31 names is in the prompt, so counting is
possible; in v3 only 3 declarations were present and the count was impossible.
`prompt_at_turn.py`'s `reachable` column (a digit-bound literal test) stays `false` for these
two cells by design; the resolvability probe below is the applicable test.

`fact in prompt` is `prompt_at_turn`'s `fact_planted_in_prompt` flag (the T2 plant sentence).
It is `false` on every pointer-stable cell because that arm's tail carries answers, not past
questions — it is not the reachability field and it does not affect answerability.

### Proof the values are present

```
$ grep -c '^class Ptr' experiments/ptr-engine/ptr_engine/errors.py
31
$ grep -c '^class Ptr' <resolve? no: errors.py v4 body>            # from runtime-v4
31        # set-equal to the file's 31 names; every name substring-present in the body
$ grep -n 'DEFAULT_MAX_REFS' (v4 resolve.py body)
DEFAULT_MAX_REFS = 64
    max_refs: int = DEFAULT_MAX_REFS
```

Materialiser run (both arms, three turns, exit 0, `no_http_proof.ok=true`,
`network_attempts=[]`, `requests_sent=0`):

```
$ python3 experiments/ptr-engine/longrun/tools/prompt_at_turn.py \
    --fixture experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json \
    --rows experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.jsonl \
    --turns 12,24,46 --json /tmp/prompt_at_turn_v4.json
arm                 T fact  exp     n reach sha       bytes  answer
transcript-grow    12 True  True    1 True  12/12       15903  ...
transcript-grow    24 True  False   0 False 24/24       18342  ...
transcript-grow    46 True  True  476 True  46/46       23235  ...
pointer-stable     12 False True    1 True  12/12       13993  ...
pointer-stable     24 False False   0 False 24/24       13944  ...
pointer-stable     46 False True  355 True  46/46       14007  ...
NO-HTTP PROOF ok: 5 clients patched, network_attempts=[], requests_sent=0
```

**Read the `sha` column honestly:** it is `mismatches/checked`, and every cell is n/n because
the canned replies replayed are the *v3* rows — a v4 prompt can never hash-match a v3 row. The
prompts are still produced by the runner's own `Planner.build` inside `run_cell`; only the
provenance comparison is inapplicable (there are no v4 rows yet, and this unit may not create
any).

Resolvability probe (re-drives `prompt_at_turn.drive`, inspects the full prompt):

| arm | turn | `64` literal | `errors.py` body present | `^class Ptr` in prompt | `31` literal | `_refuse` call present |
|---|---|---|---|---|---|---|
| transcript-grow | 12 | 1 | yes | 31 | 0 | yes |
| transcript-grow | 24 | 1 | yes | 31 | 0 | yes |
| transcript-grow | 46 | 1 | yes | 31 | 2 (echoed in earlier answers) | yes |
| pointer-stable | 12 | 1 | yes | 31 | 0 | yes |
| pointer-stable | 24 | 1 | yes | 31 | 0 | yes |
| pointer-stable | 46 | 1 | yes | 31 | 0 | yes |

## 4. Grader stays honest

`grade_v3.py` was **not** touched. The control rows need no rebuild (byte-identical copy,
`cmp` clean) because no check id or spec moved:

```
$ python3 experiments/ptr-engine/longrun/grade_v3.py \
    --rows experiments/ptr-engine/longrun/controls/v4/pos-full.v4.jsonl \
    --fixture experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json \
    --out experiments/ptr-engine/longrun/controls/v4/pos-full.grade-v4.json
pointer-stable       verified=True acc=3/3 ttvs=13161 over=0.0% reasons=-
exit=0
```

Same verdict as the v3 positive control (`controls/pos-full.grade-v3.json`: verified true,
3/3). `checks_changed: []`.

## 5. What a 96-request re-run must know

1. **Use `tasks-v4/runtime-v4/LR-01.v4.json`**, not `runtime-v3`; the v3 slices are still
   defective and will reproduce the two unanswerable checkpoints.
2. **CP2 is a counting task.** The prompt now contains all 31 declarations but never the
   numeral `31`. A model that greps for the digit will find nothing and must count
   `^class Ptr` (or note `__all__` lists 31 names). This is the one cell whose answer is not
   literally preloaded; expect a lower first-attempt hit rate there and do not "fix" it by
   inlining — that would make it `RECALL-NOT-RETRIEVAL`.
3. The fixture version string on every row will read `v4-slice-widened`; any analysis that
   partitions rows by `fixture_sha256` must expect a new digest, not a v3 one.
