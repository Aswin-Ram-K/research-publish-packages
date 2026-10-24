# U6-R — end-to-end with the corrected comparator (E5)

**Session:** autonomous (task board). No human present; no question is asked; every missing value is a
recorded conservative default.

## Objective

Compare two full agent-session renderings over the 60-turn corpus
`experiments/context-cache/corpora/endtoend.json` (2 scenarios × 60 turns, gold answer planted at a
known early turn):

- **BASELINE** — the incumbent's best case: static prefix + append-only history + periodic compaction,
  volatile state only in the delta.
- **SYSTEM** — pointer context + fork compaction.

Equal information in both arms. Measure total prompt tokens, total cached, total uncached, per-turn
uncached, and whether the gold answer is still present in the rendered context at every turn after the
compaction event.

## Hard bound

Max **260 live requests**. Stop when 260 are spent or both scenarios complete. Hold
`/home/zer0null/reserach extarctor/.occamy.lock` (flock) for the whole batch; wait up to **90 minutes**
for it, then STOP and report partial. If `192.168.2.168:8012` refuses **3 consecutive** attempts, STOP
and report failed with the verbatim error.

## Write paths (this unit alone)

- `experiments/context-cache/cells/U6/**`
- `orchestration/handoffs/U6-R.json`
- `orchestration/units/U6-R.md`

## Kill condition (pre-registered; not redefined here)

Fail the claim if **any** of:

1. separation under **1.5×** on total uncached tokens;
2. accuracy drop above **5 points**;
3. the compaction policy **loses the gold answer at any turn after compaction**.

Report which one fired.

## Design (decided before the live run; see `u6_plan.json`)

**Both arms are the same information surface:** same corpus turn texts, same order, same salted
header, same volatile block (turn 1's delta body). Neither arm summarises a caller prompt with a
model — a fold is a deterministic per-turn digest.

- **BASELINE** stores each turn verbatim and never mutates an emitted message. Its view folds every
  turn but the last `KEEP_LAST + 1` into one line each (`[folded <n> <role> <sha12>] ` + first
  `DIGEST_CHARS` chars). The **system header never changes — the prefix never breaks.**
- **SYSTEM** folds the chain into a `[fork] replaces head through …` node carrying the last
  `FORK_LINES` folded lines plus the kept tail. The **prefix breaks at every fold.**

Parameters: `KEEP_LAST=2`, `DIGEST_CHARS=240`, `FORK_LINES=12`.

**Roles come from the corpus**, not from a node's position in a view — position-relative roles made
the two arms disagree about the same turn and let the baseline retain an extra turn per fold.

**Estimand / SEAM-A.** The corpus's own estimand is `4 * "#" * 32`; a run of 32 `#` is *visible to a
4-chars-per-token estimator*, so it is not a discriminating accuracy test. The live run answers
**SEAM-A**: a 4-token pointer line `[SEAM-A] answer=SEAM-A sha256=<digest>`, replacing the run in every
occurrence. The *amplification* (emitting a digest of an in-context value) is the fixture's own design;
only its size is this unit's choice.

**Accuracy basis.** Accuracy is scored on the model's answer to turn 60, so the pre-registered
gold-loss clause stays independent of it. **Known limit, measured and reported:** this worker emits an
agentic turn-by-turn reply even to a direct question, so this quantity is *reproduction fidelity*, not
question-answering accuracy. It is reported as such and not claimed as QA accuracy.

**Request economy.** One request per (arm, turn); the arms share a salt per scenario so turns 1–3 of
the two arms are byte-identical and the second is served from the first's prefix. 240 requests for a
correct plan; the bound allows re-running one scenario (up to 360 would be needed) so a scenario-level
partial stays inside 260.

**Hash machinery.** `StateNode.chain_hash` is O(n) and the shipped `compact` evaluates it per node, so
over 60 nodes it does not return (>40 s, killed inside `nodes.py:27`). The chains here therefore carry
their own extendable hash — sha over the root..self list of `[node_id, kind]` pairs, the same digest
the library builds by re-walking the chain — accumulated one node at a time, so 60 turns cost O(n).

## Result (live, 240/240 requests, 0 refusals)

**Verdict: FAIL.** Clause 1 fired — separation **0.85×** on total uncached tokens, where ≥1.5× was
required; BASELINE spent *fewer* uncached tokens than SYSTEM (185,982 vs 217,852).

| | prompt | cached | uncached | cache hit ratio |
|---|---|---|---|---|
| BASELINE | 546,622 | 360,640 | **185,982** | 0.665 |
| SYSTEM | 323,772 | 105,920 | **217,852** | 0.333 |

SYSTEM's prompts are genuinely shorter (323,772 vs 546,622 prompt tokens, **1.69×** in its favour) but
per turn it is the *less* cached: BASELINE's cached tokens grow with the prompt (3,142 mean by E1 turn
5+, pinned to the warm prefix) while SYSTEM's sit at a small constant (830 mean, 768–832). Baseline
wins the uncached metric in **both** scenarios and in every turn window measured (0.84–0.86 from turn 1,
from turn 4, per scenario) — it is not an artifact of the shared opening turns.

- Clause 2 (accuracy) **did not fire**: drop is −50 points (SYSTEM 1/2 vs BASELINE 0/2). Both are
  single observations and the worker auto-continues turns instead of answering, so this is reported as
  reproduction fidelity, not QA accuracy.
- Clause 3 (gold loss) **did not fire** as written. Under the seam both arms fold the planted turn at
  the first compaction; the fill arm's SYSTEM recovered it in E2, the baseline did not.
- **Caveat that must travel with this row:** the pre-registration's own phrase is "separation on total
  **prompt** tokens", and on that reading the claim PASSES at 1.688×. The delivered number is the cost
  metric (uncached) because that is the one that matters and the one the card lists first; both are in
  `analysis.json` (`separation`, `prompt_token_separation`).

## Kill-condition clauses, as measured offline (before any request)

- Separation was registered on the **cost metric** (total uncached tokens) and reported live from the
  endpoint's own `usage`; the prompt-token reading is reported beside it.
- **Clause 3 was expected to fire offline**: both arms' folds drop the planted answer by turn 60
  (`DIGEST_CHARS=240` against a 23-char answer in a ~1800-char turn). The live batch still ran — it
  measures the token split, and the seam's effect on the final answer is reported separately.
