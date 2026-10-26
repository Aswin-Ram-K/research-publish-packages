# QUALITY-ARM — reachability: can the engine finish a task whose answer is in an old body?

**Unit:** `QUALITY-ARM` · **Status:** done · **Card:** this file
**Write paths (declared):** `experiments/ptr-engine/quality/`, `orchestration/units/QUALITY-ARM.md`,
`orchestration/handoffs/QUALITY-ARM.json`
**Bound (declared, then met):** 50 tool calls / stop if the discrimination check cannot be run.
**Sole writer** on `:8012`; `:8014` untouched; no restart, no `/flush_cache`; no protected path touched.

---

## 1. Objective

Everything measured so far in `ptr-engine` measured **cost** (index bytes, residues, padding). Nothing had
shown that the engine still lets a task **finish** when the answer lives in an early body that a naive
policy has dropped. This unit runs that test, with a control that proves the index is not carrying the
fact.

## 2. Design (fixed before the first request — `quality/PREREG.json`)

* **Corpus** — 12 knowledge items, 9,000 B each, deterministic (`quality/corpus.py`). Exactly one
  (`k01`) names the constant `lumen` and carries its audit code `AUD-4417`; the other 11 carry 11
  different codes and never the word `lumen`.
* **Index** — `ptr_engine.compile_turn` compiles 458 bytes: 12 lines of the form
  `- @knowledge:kNN@1 <hash8> 9000` and nothing else. No fact, no `AUD-` string, no `lumen`.
* **Question (pre-registered):** "…Which audit code belongs to the constant named 'lumen'?" —
  judged by exact match of `AUD-4417`, raw answer kept per row.
* **Arms**, same corpus / questions / model (`occamy-1.0`, `:8012`, `B = 64`), 3 reps each:

  | arm | policy |
  |---|---|
  | **A** `warmpool` | every body retained and resolvable |
  | **B** `cap-3` | last 3 bodies only; older refs must raise a `PtrError` code |
  | **C** `destructive-compaction` | old bodies replaced by a first-200-byte digest at the same locator |
  | **D** `no-body` | control: no body ever resolved |

* **Measures:** task success + raw answer; resolutions / refusals / the code; billed tokens from the law
  (`uncached = (P1 mod 64) + L`, avalanche at residue ∈ {0,1}, `L = prompt_tokens + 12`); turns to finish;
  whether a re-fetch was needed.

## 3. Method that made it a real test

* Turn 1 is the **prime** (index only, one body read); turns 2–4 append — the one-append-onto-a-primed-prefix
  shape `LAW.md` §2 measured, so the billing law applies.
* The **question names no reference**, so the model must choose what to read from the index. The host
  resolves only distractor bodies, never `k01`.
* The model is given the one model-visible tool of `SPEC.md` §8 (`fetch(ref)`); refusals are fed back to
  it **as the `PtrError` code**, so "cannot read" is said out loud rather than returned as an empty body.
* A prediction row is written and fsynced **before** each request; every row is fsynced.

## 4. Result (details in `quality/RESULTS.md`)

| arm | success | refusals | code | billed tokens (median) | turns |
|---|---|---|---|---|---|
| D `no-body` | **0/3** | — | — | 3,386 | 4 |
| A `warmpool` | **3/3** | 0 | — | **34,372** | 4 |
| B `cap-3` | **0/3** | **33** | **`PTR_STORE_MISS`** | 27,622 | 4 |
| C `destructive-compaction` | **3/3** | 0 | — | **34,374** | 4 |

**Discrimination check passed:** D resolves nothing and answers `756741be` (a digest echoed off the index)
3/3 — the index does not leak the fact.

**The answer to the unit's question.** Yes: the engine lets a task finish when the answer is in an old
body — arm A proves it 3/3 and arm C does it after destroying the non-fact body too — while a cap that
removes the bytes cannot finish at all and says so honestly (`PTR_STORE_MISS`, 33/33 attempts); and the
cost gap between finishing by retention and finishing after destruction is **not resolvable at 3 reps**
(medians 34,372 vs 34,374, sign-unstable, dominated by fetch choice and one avalanche turn).

## 5. Honesty notes

* Arm B is a **negative result and a pass**: it is not rescued anywhere, and cheapness-from-failure is
  not counted as a win (it has no cost-per-finished-task).
* Two build-time corrections are disclosed in `RESULTS.md` §6: the question's *preface* wording (never its
  subject, expected fact or judgement rule) and the addition of a turn-3 distractor without which cap-3
  would have passed. D was re-run after both and stays 0/3.
* The bill is **arithmetic on measured `prompt_tokens`**, not a server-reported cache hit. The next unit
  should reconcile per turn against `/generate`'s `cached_tokens_prompt`, fix the fetch script per arm so
  the token column measures the policy, and compact the fact-bearing body on purpose.

## 6. Artefacts

`experiments/ptr-engine/quality/`: `PREREG.json` · `corpus.py` · `runner.py` · `rows.jsonl` (115 rows) ·
`RESULTS.md` · `run.log`. Handoff: `orchestration/handoffs/QUALITY-ARM.json`.
