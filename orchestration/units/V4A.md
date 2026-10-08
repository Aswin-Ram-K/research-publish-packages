# U4.1 — Assessment stage (evidence + verdicts) · **verifier unit V4A**

**Status:** `done` at `orchestration/handoffs/U4.1.json` · **verifier:** V4A (independent, author = U4.1)
**Overall verdict:** **PASS** (with 1 correction and 3 items flagged `UNVERIFIED`/not-reproduced)
**Bound:** ≤35 tool calls · **used: 30** · live LLM calls: **0** (Occamy endpoint DOWN, 1 probe)

## Purpose
Independently re-derive the claim that the assessment stage (`src/resextract/assess/{__init__,evidence,verdicts}.py`)
**refuses to claim novelty from a broken search**. All gate inputs below were constructed by V4A from
scratch (`state/verify/V4A/c2_adversarial.py`) — **no U4.1 test fixture was reused** — and the live run
was driven by V4A's own bounded driver (`state/verify/V4A/c3_live.py`).

## C1 — the two suites (PASS)
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_assess_evidence.py tests/test_assess_verdicts.py -q`
→ **`37 passed`**, split confirmed by file: evidence **14**, verdicts **23**. The claimed figure is exact.
Pre-check sha256 matched the claimed release bytes: `evidence.py b4b3b385…`, `verdicts.py d03a5c21…`.

## C2 — the gates, re-derived adversarially (PASS)

| # | input (V4A-constructed) | verdict | evidence_ids | why |
|---|---|---|---|---|
| 1 | degraded empty, `absence_is_meaningful=False`, `unresponsive_engines=["google: access denied"]` | `UNVERIFIED` | `[]` | 0 records; 1 degraded search; engine named verbatim in rationale |
| 2 | clean empty, `absence_is_meaningful=True`, slow, no engine errors | `UNVERIFIED` | `[]` | **distinct** reason: *"a clean search … found no matching prior art; finding nothing is not evidence of novelty"*; `absence_reason` differs from #1 |
| 3 | suspect fetch (`404: Not Found` body) | `UNVERIFIED` | `[]` | `records=0`, `suspect_fetches=1`, `fetch_attempts=1`, `fetched=0`; *"excluded from evidence"* |
| 4 | 2 real records, LLM cites **zero** ids | `UNVERIFIED` | `[]` | `rejected=true`, rationale `no evidence cited`, `model_calls=1` |
| 5 | 2 real records, LLM cites real id `11` | `CONFIRMS` | `[11]` | accepted; id recorded (mocked `producer="model"`) |
| 6 | LLM cites **only fabricated** `999` (valid = 11,12) | `UNVERIFIED` | `[]` | **REJECTED** — `no evidence cited` |
| 6b | LLM cites real `11` + fabricated `999` | `CONFIRMS` | `[11]` | fabricated silently dropped; only valid ids recorded |
| 7 | no client at all, supporting evidence + ids | `EXTENDS` | `[11,12]` | deterministic cap; **18-combo sweep produced only `{EXTENDS, UNVERIFIED}` — `CONFIRMS` absent** |
| 8 | replay client (`is_replay=True`) asserts `CONFIRMS` | `EXTENDS` | `[11]` | capped, with explicit `[capped at EXTENDS: producer=replay]` |
| 9 | `producer_hint="replay"` | `EXTENDS` | — | capped |
| 10 | all searches degraded, weak-only records | `UNVERIFIED` | `[]` | gate 2 fires **before** any client; engines named |

**Fabricated evidence id ⇒ REJECTED.** The failure mode the card called out as a potential `FAIL` does not exist.
All four `unresponsive_engines` shapes tested (including a 2-engine list) are named in the rationale; the two
shapes U4.1 reports were **both observed live** (§C3), not merely asserted.

## C3 — live re-derivation (PASS; SearXNG still degraded)
V4A's own driver, real degraded SearXNG (`127.0.0.1:8080`), fresh copy of `state/claims/store-copy.sqlite`
(`sha256 8f451fe0…`, 9 claims) → `state/verify/V4A/claims-v4a.sqlite`. Bounds **enforced in code**:
`max_claims=8, max_queries=1` (≤8 query bound) and a `CapFetcher(cap=2)` that refuses the 3rd real fetch.
No client was passed at all (deterministic path ⇒ zero LLM exposure).

| metric | V4A observed |
|---|---|
| SearXNG state | **degraded** (not recovered) |
| claims assessed | **8** (V4A bound; U4.1 used 9 with a ≤12-query budget) |
| by_verdict | `CONFIRMS 0 · EXTENDS 0 · CONTRADICTS 0 · UNVERIFIED 8` |
| evidence_rows | **0** |
| searches / degraded_searches | **8 / 8** |
| fetches / suspect_fetches | **0 / 0** |
| model_calls / producer / partial | **0 / `"none"` / `false`** |
| real HTTP searches / real fetches | **8 / 0** |
| query_sources | `{"lexical": 8}` |

**The headline holds: no positive verdict anywhere, and no evidence row can exist.** Every one of the 8
rationales contains *"no evidence records were gathered"*, *"this absence proves nothing"*, the degradation
latch, and the engine self-report.

**Verbatim rationale (claim 1):**
> `no evidence: no evidence records were gathered. 1 search(es) were degraded, so this absence proves nothing: 1 engine(s) reported themselves unresponsive (google: access denied) -- SearXNG said the search was broken; the client's degradation latch is set (engine_unresponsive); empties from a degraded client are unverified for its lifetime [unresponsive: google: access denied]`

**Verbatim `absence_reason` (a later claim):**
> `1 engine(s) reported themselves unresponsive (google: Suspended: access denied) -- SearXNG said the search was broken; the empty response arrived in 2.1ms, under fast_empty_ms=50ms -- too fast to have searched; the client's degradation latch is set (engine_unresponsive); empties from a degraded client are unverified for its lifetime`

**Raw `unresponsive_engines` observed live (both shapes, kept):** `[["google: access denied"], ["google: Suspended: access denied"]]`

**Four signals — honestly qualified:** 3 of the 4 are present in **all 8** rationales (engine self-report,
degraded latch, "absence proves nothing"). The **sub-threshold-latency** clause appears in **7 of 8** — it is
absent from the *first* claim, whose cold request took **314.7 ms** and therefore latched on
`engine_unresponsive` before any latency heuristic could fire. U4.1's own headline (2.3 ms) does carry it.
So "four signals present" is true of the run, **not of every individual rationale** — a warm-first-request
artefact of the web layer, faithfully forwarded, not an overstatement by U4.1.

## C4 — resume and durability (PASS)
Second run over unchanged inputs: **`searches = 0`**, `resumed_claims = 8`, `claims_assessed = 8`,
`evidence_rows = 0`, `by_verdict` unchanged. Real HTTP searches after run 2: **still 8** (none added).
All five outputs present and well-formed: `EVIDENCE.md`, `VERDICTS.md`, `evidence.jsonl`, `verdicts.jsonl`,
`report.json` (+ `resume.json`). JSONL parses line-by-line; **report counts agree with file line counts**
(`evidence_rows 0 == 0` lines; `claims_assessed 8 == 8` lines).

## C5 — the store gap: judged a **RISK** (confirmed, not implemented)
Real DDL confirms **no producer column**:
- `evidence = id, claim_id, source_kind, source_ref, sha256, quote, context, retrieved_at, copy_path`
- `verdicts = id, claim_id, verdict, rationale, evidence_ids_json, checked_at`

`store.insert_evidence()` / `store.insert_verdict()` have no producer parameter, so a producer cannot reach the store.

**Judgement: RISK, not an acceptable interim.** The project has *already recognised this exact hazard once*:
migration 3 added `candidates.producer TEXT DEFAULT 'unknown' CHECK (producer IN ('model','replay','fixture','unknown'))`
precisely so a replay-produced candidate could not masquerade as model work (FAIL A). `verdicts` is the
**higher-stakes** table — "producer" there decides whether a novelty claim may be published — yet it carries
the weaker guarantee. `report.json`/`verdicts.jsonl` are **run artefacts, not the system of record**, and
`run_dir` is keyed and rewritten per run, so an importer that reads verdict rows (the obvious next step)
cannot tell a model verdict from a replay one. The claim under test is exactly the one where this matters.

**Recommended minimal fix (not implemented):** schema **v4** — add `producer TEXT DEFAULT 'unknown' CHECK (producer IN ('model','replay','fixture','unknown'))` to **both** `evidence` and `verdicts`, following the migration-3 precedent, and thread it through `insert_evidence` / `insert_verdict`.
**Correction to U4.1's phrasing:** the fix should reuse the *existing* `candidates` vocabulary
(`'unknown'`, not `'none'`) or the two tables will disagree; `Verdict.producer`'s current `"none"` must map to `'unknown'` on write.

## C6 — red→green, sha-proven (PASS on the property; see caveat)
Performed **last**, after C1–C5 were persisted, with `PYTHONDONTWRITEBYTECODE=1` + a `__pycache__` purge
before every run. No sibling-collision was observed in either revert window (both sub-second).

**(a) `evidence.py` — degraded-search-never-positive**
`sha_before = b4b3b385…` → backed up → reverted (degraded empty treated as a clean empty) → `sha_reverted = b0518407…` → purge → failure **verbatim**:
```
>       assert len(gather.degraded_searches) == 1, "the broken search must be visible as degraded"
E       AssertionError: the broken search must be visible as degraded
E       assert 0 == 1
tests/test_assess_evidence.py:179: AssertionError
FAILED tests/test_assess_evidence.py::test_degraded_search_empty_is_never_positive
1 failed in 0.04s
```
→ restored → `sha_restored = b4b3b385…` (`RESTORE_OK_A`, equal to before) → re-run: **`1 passed`**.

**(b) `verdicts.py` — no-evidence-never-calls-the-LLM**
`sha_before = d03a5c21…` → backed up → reverted (gate 1 bypassed so the empty gather reaches the client) → `sha_reverted = 7a0f3ab1…` → purge → failure **verbatim**:
```
>       assert client.calls == [], "a claim with no evidence must not reach the model"
E       AssertionError: a claim with no evidence must not reach the model
E       assert [{'messages':...ss.verdict'}}] == []
E         Left contains one more item: {'messages': [... 'Evidence:\n(no evidence)'], 'kwargs': {'thinking': True, 'max_tokens': 2048, 'label': 'assess.verdict'}}
tests/test_assess_verdicts.py:201: AssertionError
FAILED tests/test_assess_verdicts.py::test_no_evidence_never_calls_the_llm
1 failed in 0.05s
```
→ restored → `sha_restored = d03a5c21…` (`RESTORE_OK_B`) → re-run: **`1 passed`**. Final shas equal the release bytes.

**Caveat (`UNVERIFIED` sub-claim):** the *property* — test goes red when the guard is reverted, green when
restored — is **confirmed for both guards**. U4.1's additional claim that the reverted trees were
*bit-identical* at `8ab93b29…` / `3a6f0838…` is **not independently reproducible**: those reverted trees are
not in the repository and U4.1's diff was not supplied, so V4A's own minimal reconstructions differ
(`b0518407…` / `7a0f3ab1…`). The red→green conclusion does not depend on that sub-claim.

## C7 — honesty audit
**Confirmed.** The `37 tests` figure is exact. The `0 real fetches` claim is true **and correctly explained**:
0 fetches occurred because the degraded search returned **0 candidate URLs** (`candidate_urls=[]`,
`fetch_attempts=0`) — *not* because fetching is skipped. V4A verified the complementary direction: with a
candidate URL present, `fetch_attempts` becomes 1 and the fetcher is called (C2 #3). Both raw
`unresponsive_engines` shapes are **genuinely handled** (both observed live and both named in rationales).
The deterministic no-client path **cannot** reach `CONFIRMS` by any route (only `EXTENDS`/`UNVERIFIED`
literals exist in gate 4; an 18-combo sweep found no counterexample).

**Correction — residual risk in the producer guard.** `_client_producer()` (`verdicts.py:657`) **defaults an
undeclared client to `"model"`**. V4A confirmed: a client exposing only `call_json` (no `producer`, no
`is_replay`, no `is_stub`) is classified `producer="model"` and its `CONFIRMS` is **accepted, not capped**
(observed: `verdict=CONFIRMS producer=model ids=[1]`). The named gates hold as written (no client ⇒ cap;
*self-declaring* replay client ⇒ cap), but the cap is enforced by the client's own self-declaration. A replay
harness that forgets to declare itself would publish `CONFIRMS` indistinguishable from a model verdict.
Minimal hardening: default to `"replay"` (the conservative direction) or require an explicit hint.

**Flagged as confusing.** A reader of `report.json` sees `producer: "none"` alongside `client_producer: "replay"`
(U4.1's run) and can reasonably read `producer "none"` as "no client was used", when a replay client **was**
wired in and did supply queries. `producer` is really "what produced the *verdict*" while `client_producer` is
"what was *injected*". Two differently-scoped fields share one word. V4A's own run has `client_producer: null`,
so the ambiguity is U4.1's replay configuration, not intrinsic.

**Unbuilt after deferral.** `docs/PLAN.md` §4 stage 5 (line 202) obliges the Assess stage to emit, per claim,
**"real-world value axes (who is affected, what it unblocks, measured delta, reproducibility, cost,
licensing)"**. These were deferred for budget and are **not built**: no value-axis field exists on `Verdict`,
no axis is prompted for or persisted, and no test covers one. The stage-5 *verdict* half and the
"Unverifiable claims are kept and labelled" clause **are** built and verified here; the **value-axis half of
the same plan line is unbuilt**, so §4 stage 5 is only partially satisfied.

## C8 — containment
- Nothing written outside this workspace. All V4A writes fall inside the declared paths:
  `orchestration/handoffs/V4A.json`, `orchestration/VERDICTS.md`, `orchestration/units/V4A.md`,
  `state/logs/V4A-c2.log`, `state/logs/V4A-c3.log`, `state/verify/V4A/**`.
- **Real store untouched:** `claims/evidence/verdicts = 0/0/0` **before and after**.
- Only `src/resextract/assess/{evidence,verdicts}.py` were ever reverted, both restored sha-identical to
  `b4b3b385…` / `d03a5c21…`. `tests/**` never modified. `U4.1`'s own outputs (`state/assess/**`,
  `state/claims/**`) were never written — V4A copied the claim store into its own directory.
- **Duval:** `/home/zer0null/Duval` HEAD moved `55710509…` → `cf2f516b…` **during** this unit
  (`git status --porcelain` unchanged, same two foreign untracked entries `.ci-trunk.txt`,
  `.lane-j-scratch/`). V4A made **no** write to Duval and holds no permission to; this is the expected
  foreign writer. No `.worktrees/` read was made (0).
- Live-budget compliance: **1** Occamy probe (DOWN, HTTP `000`, curl exit 7), **0** live LLM calls,
  **8** real searches (= the ≤8 bound), **0** real fetches (≤2 bound).

## Verdict
**PASS.** Every gate U4.1 claimed is real under inputs V4A generated itself, including the dangerous one:
**a fabricated evidence id is rejected**, and **a broken search never yields a positive verdict**. The live
run independently reproduces the headline — degraded SearXNG ⇒ 8/8 `UNVERIFIED`, **0 evidence rows**,
0 model calls — so the pipeline demonstrably refuses to claim novelty from a broken search.
Carried forward: the **store-gap risk** (C5, recommend schema v4), the **undeclared-client default-to-model**
hole, and the **unbuilt value axes** of plan §4 stage 5.
