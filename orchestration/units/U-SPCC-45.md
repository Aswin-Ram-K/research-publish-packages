# U-SPCC-45 — Why the same spcc cell scored 20/48 and 22/48

Read-only investigation. No code or row edits. Two artefacts written.

## 0. The two cells

| | A (single-arm) | B (three-arm) |
|---|---|---|
| file | `experiments/ptr-engine/measure/rows-e1-spcc-2026-11-10.jsonl` | `experiments/ptr-engine/measure/rows-e1-final-2026-11-10.jsonl` (spcc rows only) |
| commit | `e18a587` | `e4692f8` |
| `run_id` | `e1-spcc-2026-11-10-spcc-r1` | `e1-final-2026-11-10-spcc-r1` |
| rows | 100 | 100 (of 300) |
| answer turns | 48 | 48 |
| value-correct | **20/48** | **22/48** |
| contract-correct | **19/48** | **21/48** |

Every arm input is identical across the two cells, verified field-by-field on all 100 turns:

- `arm=spcc`, `rep=1`, `seed=42`, `temperature=0.0`, `model=occamy-1.0`,
  `endpoint=http://192.168.2.168:8012/v1`, `max_tokens=4096`, `top_p=None`
- `fixture_id=TX-03.TX-03.v1`,
  `fixture_sha256=f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3`
  (identical in both files)
- `layer_tokens`, `epoch`, `compactions`, `masked_rows`, `evicted`, `expected_present`,
  `fetch_rows`, `fetch_tokens`, `fetch_policy`, `fetch_budget_tokens`, `claim`,
  `digest_at`, `engine`, `channel_token_method`, `comparison_eligible`
  — **all 100 turns equal, zero differences**
- `error=None` and `cap_refused_mid_turn=None` on all 200 rows; `finish_reason=stop` on all

## 1. Turn-by-turn comparison

**`prompt_sha256` is equal at all 100 turns. `prompt_tokens` is equal at all 100 turns.**
There is no turn at which the two cells sent different prompt bytes.

Answers differ at exactly six turns:

| turn | answer_turn | scored | `prompt_sha256` | `prompt_tokens` | `cached_tokens` A/B | A `answer_kind`/`answer_value` | B `answer_kind`/`answer_value` | `expected` | completion_tokens A/B |
|---|---|---|---|---|---|---|---|---|---|
| 5 | no | no | **equal** | 710 / 710 | 704 / 640 | `NONE` / — | `NUM` / 3000 | — | 5 / 10 |
| 41 | no | no | **equal** | 935 / 935 | 832 / 832 | `None` / — (no `answer_raw`) | `NONE` / — | — | 2 / 5 |
| 52 | no | no | **equal** | 729 / 729 | 576 / 576 | `NONE` / — | `NUM` / 3505 | — | 5 / 10 |
| **57** | **yes** | **yes** | **equal** | 964 / 964 | 704 / 768 | `NONE` / — (`verified=False`) | `NUM` / **3501** (`verified=True`) | **3501** | 5 / 10 |
| **60** | **yes** | **yes** | **equal** | 1033 / 1033 | 832 / 832 | `NONE` / — (`verified=False`) | `NUM` / **3503** (`verified=True`) | **3503** | 5 / 10 |
| 80 | no | no | **equal** | 764 / 764 | 704 / 704 | `None` / — (no `answer_raw`) | `NONE` / — | — | 2 / 5 |

`content_sha256` and `content_tokens` differ at exactly these same six turns — i.e. the
*response* bytes differ, never the request bytes.

Only turns **57** and **60** are scored, and they are the whole of the 20→22 delta:

- T57 — checkpoint `cp.TX-03.f06.d5`, question "What is VAL_B of doc-fact-06?", expected `3501`, distance 5.
  A answered `ANSWER: NONE`; B answered `ANSWER: NUM 3501`.
- T60 — checkpoint `cp.TX-03.f06.d8`, question "What is VAL_D of doc-fact-06?", expected `3503`, distance 8.
  A answered `ANSWER: NONE`; B answered `ANSWER: NUM 3503`.

Both are fact-06 checkpoints, and T52 (the fact-06 introduction turn, `intro_turn=52`) is
also one of the six differing turns — A abstained there (`NONE`) where B emitted `NUM 3505`.
So the divergence is localised to the fact-06 block (T52, T57, T60) plus three unrelated
interim turns (T5, T41, T80).

Contract-correct follows the same two turns: `longrun/score_longrun.py:1235` defines
`contract_ok = (ak == "NUM" and value_ok)`, and at T57/T60 A's `answer_kind` is `NONE`
with `answer_value=None`, so both `value_ok` and `contract_ok` flip together. Hence
19/48 → 21/48 is the same two checkpoints, not a separate effect.

## 2. First divergence point

**There is none in the prompt.** `prompt_sha256` is equal at turn 1 and at every turn
through 100, so the two cells never diverged in prompt bytes and there is nothing to diff.

The first divergence in *output* is turn 5 (an unscored interim turn). The first divergence
in *scored* output is turn 57.

## 3. Why the prompt cannot have differed

`longrun/run_longrun.py:1499`:

```python
def messages(self, user: str) -> list[dict]:
    return [{"role": "system", "content": self.fixture["system_prompt"]},
            {"role": "user", "content": user}]
```

The request is **stateless**: a constant fixture system prompt plus the single user prompt.
No prior assistant turns are carried. `prompt_sha256` is `sha256_text(info["prompt"])`
(`longrun/run_longrun.py:3723` and the other `make_row` call sites), i.e. a hash of that
user content. With `fixture_sha256` equal and `prompt_sha256` equal at all 100 turns, the
two cells sent **byte-identical request bodies** at every turn — including T57 and T60,
which is why the differing T52 answer could not have leaked into T57's prompt.

## 4. Git range `e18a587..e4692f8`

```
e4692f8 U-SPCC-44: E1 three-arm cell ran; spcc 22/48 value, 21/48 contract, fetch arm never fetched
03e920e U-SPCC-43: the fetch arm's inline follow-up and the budget exit both reconcile
9a5b811 U-SPCC-42: persist every paid row before a mid-turn refusal unwinds
dbef527 U-SPCC-41: E1 three-arm cell halted before spend; G3 admits n=300 offline
497e94a U-SPCC-40: G3's n carries the arm term; prereg ceiling enforced on actual sends
f29e3e4 U-SPCC-39: G3's n is turns x reps, not requests; E1 unsatisfiable inside its own ceiling
0e31417 U-SPCC-38: test the compaction marker's behaviour, regenerate the derived artefacts
5bc1338 U-SPCC-35 correction: contract-correct 19/48, fetch denominator 48 not 53
3a864ad U-SPCC-37: run_longrun enforces G3 before the first request
```

`git log --oneline e18a587..e4692f8 -- ptr_engine/layers.py longrun/arm_cd.py longrun/run_longrun.py`
returns only `03e920e`, `9a5b811`, `497e94a`, `3a864ad` — all touching `run_longrun.py` alone.

`git diff --stat e18a587..e4692f8` over those three files:

```
 experiments/ptr-engine/longrun/run_longrun.py | 297 ++++++++++++++++++++++----
 1 file changed, 260 insertions(+), 37 deletions(-)
```

`ptr_engine/layers.py` and `longrun/arm_cd.py` are **unchanged** (0 lines) — the arm's
prompt compiler is byte-identical across the range. `longrun/tasks-v7/TX-03.v1.json` is
also unchanged (`git log` over the range is empty for it).

The `run_longrun.py` hunks land at `@@ -596` / `-604` / `-633` / `-676` (`RequestCapGate`),
`@@ -742` (`build_cap_gate`), `@@ -1223` (`followups_spent`), `@@ -1347` (`fetch_rounds`),
`@@ -3348` / `-3397` / `-3472` / `-3503` / `-3588` (`run_cell`), `@@ -4017` (`build_parser`),
`@@ -4136` (`main`). **No hunk touches `Planner` (starts at `run_longrun.py:1474`) or any
prompt-construction code.**

The `run_cell` hunks are the only ones near the turn loop, and they are confined to the
`CapRefusal` / `BudgetExhausted` exit paths — row persistence, not prompt bytes:

```python
             except CapRefusal as exc:
-                # The refusal lands MID-turn: this turn's own request already reached the
-                # wire and is billed, so its row is written before the run stops — rows
-                # written stay equal to the requests legitimately made.
+                # PAID-ROW-PERSISTENCE (U-SPCC-42): the refusal lands MID-turn.  The rows
+                # for the follow-ups already sent were persisted by fetch_rounds before
+                # the refusal unwound; ...
+                partial = list(getattr(exc, "partial_followups", None) or [])
+                last_resp = getattr(exc, "partial_resp", None) or resp
```

and

```python
             except BudgetExhausted as exc:
-                for _f in followup_rows:
-                    append_row(rows_path, _f)
+                partial = list(getattr(exc, "partial_followups", None) or [])
+                last_resp = getattr(exc, "partial_resp", None) or resp
```

Neither path fired in either cell: `error=None` and `cap_refused_mid_turn=None` on all 200
rows, and both cells ran the full 100 turns. **No commit in the range can change the prompt
bytes for the spcc arm.**

## 5. Verdict

**Genuine nondeterminism — server-side.** Same prompt bytes, different answer.

Evidence chain:

1. `prompt_sha256` equal at all 100 turns; `prompt_tokens` equal at all 100 turns.
2. `fixture_sha256` equal; the request is stateless (`run_longrun.py:1499`), so the system
   prompt plus the hashed user prompt fully determine the body.
3. Every arm input (`layer_tokens`, `epoch`, `compactions`, `masked_rows`, `evicted`,
   `expected_present`, fetch fields, `claim`, `digest_at`) equal at all 100 turns.
4. `layers.py` and `arm_cd.py` unchanged in the range; no `run_longrun.py` hunk touches
   prompt construction; the fixture is unchanged.
5. `content_sha256` differs at exactly the six turns where the answer differs — the
   response bytes moved, the request bytes did not.

Corroborating mechanism: `cached_tokens` differ at **26 of 100 turns** on byte-identical
prompts (turns 1, 2, 3, 5, 8, 10, 24, 30, 33, 45, 51, 53, 54, 55, 56, 57, 58, 59, 61, 67,
69, 70, 71, 74, 77, 89; total cached 79,808 in A vs 81,024 in B, 22 of 26 with B higher).
The same prompt bytes drew different prefix-cache hit counts, so the serving stack's cache
occupancy and batch composition differed between the two runs. On a stateful backend that
is the standard route to temperature-0 divergence: `seed=42` is not honoured as a
determinism guarantee, and the numerics depend on what else the server was doing.

## 6. What this means for every claim resting on temperature 0 and seed 42

**Temperature 0 plus seed 42 does not make this endpoint deterministic.** It is a
best-effort sampling setting, not a reproducibility contract. Measured on this arm:

- per-turn flip rate: **6/100 turns (6%)**
- per-scored-checkpoint flip rate: **2/48 (4.2%)**
- run-to-run spread on the headline metric: **±2/48 = ±4.2 percentage points**

Consequences, stated plainly:

1. **A single-rep cell carries an unquantified noise floor of at least 2/48 (4.2 pp) on
   this fixture.** Any arm-to-arm difference smaller than that is not evidence of a
   treatment effect. E1 ran at `reps=1` (`--reps 1`, `hypothesis=E1, turns=100, reps=1,
   arms=3`), so every E1 arm comparison is subject to this floor.
2. **The 20/48 and 22/48 cells are the same treatment.** Their 2-point gap is pure noise,
   not a replication failure and not a code change. U-SPCC-44's framing — "the 2-checkpoint
   difference is run-to-run non-determinism on the serving stack, not a treatment effect" —
   is correct, and this unit supplies the turn-level proof it previously asserted.
3. **Single-rep cells cannot support a claim of a small effect.** They can support a claim
   only where the observed gap is comfortably larger than ~4 pp, and even then the claim
   needs the noise floor stated alongside it. A single rep cannot distinguish 22/48 from
   20/48, and cannot distinguish either from 21/48.
4. **The noise is not uniform across the fixture.** All three fact-06 turns (T52, T57, T60)
   flipped together, while 94 turns were stable. Divergence clusters on one fact block, so
   the effective independent sample is smaller than 48 and the true variance on a
   fact-level claim is worse than the aggregate 4.2 pp suggests.
5. **Any prereg that fixes `reps=1` and treats the result as a point estimate is
   underpowered by construction.** Either raise reps until the standard error is below the
   effect size of interest, or report every single-rep number with the measured ±2/48 band.
6. **This does not excuse the fetch arm.** The `bounded-context-fetch` degenerate cell
   (43/48 stranded `fetch_followup` rows, `tools_mode=off`, `send_index 0` on all 100 rows)
   is a separate, deterministic defect — the arm never fetched. That is not noise and must
   not be filed under this finding.

## 7. Method / reproduction

Offline only; zero model requests. Comparison script joined the two files on `turn`
(1..100), compared `prompt_sha256`, `prompt_tokens`, `cached_tokens`, `answer_kind`,
`answer_value`, `expected`, `answer_verified`, `content_sha256`, `content_tokens`, and the
arm-input fields listed in §0. Scores recomputed from the rows and matched the recorded
20/48 and 22/48 exactly.
