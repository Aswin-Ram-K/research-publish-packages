# U-SPCC-22 — record the TX-03 presence finding in the ledger

**Status:** done (documentation only; zero live model requests).

**Inputs:** `experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md` and
`orchestration/handoffs/U-SPCC-20.json`. (The assignment named the source as
`measure/answer-shape-diagnosis-TX03.md`; the file on disk is at the
`experiments/ptr-engine/measure/` prefix, as listed in U-SPCC-20's own `artifacts`.)

## What changed

1. **`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md`**
   - New table row 22: *TX-03 masking cliff is presence, not position* — 8/48 on `:8012` (SGLang, `occamy-1.0`; all 8 at `d2`);
     40 failures with 0 occurrences of the expected value, 8 passes with exactly 1 occurrence + 1 anchor
     hit; units = score out of 48 checkpoints + prompt occurrences; source =
     `experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md` + `orchestration/handoffs/U-SPCC-20.json`;
     generation gen-7; replicate column `not comparable` with replication recorded — same arm/fixture pattern
     on two stacks: 3/3 runs on `:8012` (r1, r2, billed proof) at 8/48, 8/8 at `d2`, 40/40 abstentions;
     `:8014` (vLLM) also 8/48 and 8/8 at `d2` but 39 abstentions + 1 substitution
     (`cp.TX-03.f07.d8` answered `3703`, expected `3603` — a same-column constant from a different document).
     Cross-build comparison not claimed (rule "No cross-build comparison"); status `VERIFIED`.
   - New subsection `### The TX-03 cliff is presence, not position` with the four exclusions (presence binary
     and complete; position excluded by the 0.74 request-token / 0.90 user-content probes; contract strictness
     excluded — all 40 answers are literal `ANSWER: NONE` with `answer_parse_error: null`; fixture
     unanswerability excluded), the turn-6 verbatim prompt, and the mask-turn/intro-turn correspondence
     (`intro+4`, `WINDOW_TURNS = 4`).
   - New subsection `### Recorded defects in the existing rows`: `evicted` (`longrun/run_longrun.py:1453`
     init, assigned only in the `transcript-grow` branch at `:1476`) and `expected_present` (`:2581`,
     computed from `reasoning_raw`, so `False` on all 48 including the 8 correct answers).
   - Open question "Is the distance cliff a matter of presence or position (E3)?" marked closed with a
     pointer to the new subsection.
2. **`RESULTS-TX02-CELL1.md:42`** — monotonicity line labelled in place (not rewritten): not a depth or
   attention gradient; the step is the eviction boundary at `intro+4`; superseded by the TX-03 presence
   finding.
3. **`RESULTS-TX03-CELL1.md:46`** — "policy window boundary of 5" corrected to the mask firing at
   `intro+4`, with a pointer to the new subsection.
4. **`RESULTS-STACK-8014.md:36`** — same off-by-one corrected ("`d=5` is the first checkpoint past the
   mask, not the boundary value"), and the cause restated as eviction rather than depth.

No history was deleted; every superseded sentence is still present and carries a bracketed label.

## Acceptance evidence

```
$ awk -F'|' '/^\|/ {print NR": "NF-2}' experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md
11: 7
12: 7
13: 7
14: 7
15: 7
16: 7
17: 7
18: 7
19: 7
20: 7
22: 7
```

```
$ python3 tools/doc_check.py; echo exit=$?
OK docs clean under /home/zer0null/research extractor
exit=0
```

Depth/distance/attention grep: 34 hits across the ledger and the `RESULTS-*.md` set. Only four offered a
causal reading, and each is now labelled or pointed at the presence subsection:

| hit | content | action |
|---|---|---|
| `FINDINGS-LEDGER.md:43` (old numbering) | open question "distance cliff — presence or position?" | marked closed, presence |
| `RESULTS-TX02-CELL1.md:42` | "monotone non-increasing in distance" | labelled: eviction boundary, superseded |
| `RESULTS-TX03-CELL1.md:46` | "policy window boundary of 5" | corrected to `intro+4` |
| `RESULTS-STACK-8014.md:35-36` | "eviction boundary at 5 turns" | corrected to `intro+4`, cause restated as eviction |

The remaining 30 hits are descriptive distance axes/buckets (`distance {2,5,6,8,20,32}`, per-distance
tables, "the fetch arm is not a distance effect") and already attribute the masking step to masking rather
than to recall/depth; they needed no change.

## Note for the schema owner

Both degenerate columns are recorded as `recorded defect` in the ledger, so rows written before the
`FixDegenerateFields` repair must not be read through `evicted` or `expected_present`.
