# U-SPCC-58 — classify the masking arm's 10 wrong answers

**Status:** DONE. Read-only analysis: 0 endpoint requests, 0 model calls, no code or prompt
change.

## Method

Every one of the 100 `masking-no-fetch` prompts in
`experiments/ptr-engine/measure/rows-e1-indexfix-2026-11-10.jsonl` was rebuilt through the
runner's own `Planner` (`longrun/run_longrun.py:1561`) plus `checkpoint_prompt`
(`longrun/run_longrun.py:2348`, applied on the 48 checkpoint turns), replaying the recorded
`content` as each turn's answer. **All 100 reconstructed prompts hash byte-identically to the
row's `prompt_sha256`** (0 mismatches), so the search below is over the exact bytes the model
saw.

## The 10-row table

| turn | checkpoint | expected | answered | kind | prompt_sha256 (16) | where the answered value came from |
|---:|---|---:|---:|---|---|---|
| 6 | `cp.TX-03.f01.d5` | 3001 | 4000 | NUM | `e25423130ee3ff09` | nowhere — absent from prompt, index, and every fixture body |
| 7 | `cp.TX-03.f01.d6` | 3002 | 5000 | NUM | `7e86deac4faae009` | nowhere |
| 9 | `cp.TX-03.f01.d8` | 3003 | 3103 | NUM | `43cd3bb373005ac4` | **doc-fact-02 body in L3** (`TOOL_OUTPUT (doc-fact-02@1): … VAL_D = 3103`), delivered T8, unmasked at T9 |
| 13 | `cp.TX-03.f02.d5` | 3101 | 4100 | NUM | `71bac924928b289c` | nowhere |
| 14 | `cp.TX-03.f02.d6` | 3102 | 4103 | NUM | `0d5e2409984801c2` | nowhere |
| 22 | `cp.TX-03.f03.d5` | 3201 | 4200 | NUM | `9d8b12c4f7886c48` | nowhere |
| 23 | `cp.TX-03.f03.d6` | 3202 | 4203 | NUM | `f0dfb2a890f66189` | nowhere |
| 25 | `cp.TX-03.f03.d8` | 3203 | 4203 | NUM | `fdff0ee60717e3b1` | **its own T23 answer** (`ANSWER (T23): ANSWER: NUM 4203`) — self-echo of a confabulation |
| 29 | `cp.TX-03.f04.d5` | 3301 | 4300 | NUM | `ee97a259ad1e594e` | nowhere |
| 30 | `cp.TX-03.f04.d6` | 3302 | 4303 | NUM | `c241e39f383bfb14` | nowhere |

## Classification counts

| class | n | turns |
|---|---:|---|
| cross-fact confusion | **1** | 9 |
| index leakage | **0** | — |
| pure confabulation | **9** | 6, 7, 13, 14, 22, 23, 25, 29, 30 |

T25 is pure confabulation by origin: `4203` is not a fact value and not in the index; it is
the model's own T23 confabulation copied forward. It is the only answered value that appears
in the prompt at all besides T9's.

## Evidence

- **No index leakage.** The index lines are `- doc-<name>@r<rev> <hash8> <bytes>`; none of
  `4000 5000 4100 4103 4200 4203 4300 4303` occurs in `index_lines(fixture)`. The index
  carries ref names, a digest and a byte count — no fact value.
- **No fixture-body source.** Searching all 22 fixture bodies (documents + every turn's
  `tool_outputs`) for the eight confabulated numbers returns zero hits. Only `3103` occurs,
  in `doc-fact-02`.
- **The 8 correct turns are unchanged.** Both cells answer `3, 10, 19, 26, 47, 54, 63, 70`
  correctly — all eight are `d2` checkpoints, where the fact body is still inside the
  4-turn window. The index change did not move the correct count.
- **The 10 flipped turns were `NONE` in `parserfix`.** In
  `rows-e1-parserfix-2026-11-10.jsonl` all ten are `answer_kind: NONE`; in `indexfix` all ten
  are `NUM` and wrong. The index change (`b38db8a`) is the only difference.
- **The index change is a prompt-size change.** It adds ~250–290 prompt tokens per turn
  (T6 440→690, T29 1154→1444): 13 index lines instead of 1.

## Verdict

**The 0→10 shift is an artefact of the index change, not a property of the masking arm.**
The arm's design — answer from context or `NONE` — is unchanged, and the values it produced
are not in the context it was given. What changed is the prompt: the shared L1 now advertises
13 fetchable refs to an arm that has no fetch tool. That primes the model to answer with
invented numbers instead of abstaining. No value leaked from the index; the index leaked only
*names* the question already states.

## Consequence for the 8/48

The **8/48 is still a fair retention measure**: the 8 correct are the in-window `d2`
checkpoints, identical in both cells, and the index change did not touch them. The arm retains
nothing past the 4-turn window, and 8/48 states that correctly.

The **0→10 wrong count is not a measure of the arm**. It is measured under a prompt that shows
the arm 13 refs it cannot address, and that prompt converts abstention into confabulation. The
8/48 retention score stands; the wrong-answer count is a prompt-design artefact and must not
be read as an arm property.

## Checks

- `python3 tools/doc_check.py` → `OK docs clean`, exit 0.
- `git --no-optional-locks status --porcelain` shows only pre-existing untracked manifests and
  refusal files, none created by this unit.
