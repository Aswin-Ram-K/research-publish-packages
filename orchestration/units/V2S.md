# V2S — recovery verifier, superseding V2R; closure of V2's FAIL (U2.1 -> fixed by U2.2)

**Role:** independent recovery verifier. No prior context. Author of no unit under verification.
cwd `/home/zer0null/reserach extarctor` (only writable area).
**Bound:** target <=40 tool calls — used **33**, disclosed.
**Liveness probe:** `curl -sS -m 5 http://192.168.2.168:8012/v1/models` -> HTTP `000`, curl exit 7,
at 2026-10-08T06:48:53-05:00. **Endpoint DOWN.** Probed once. **Zero live LLM calls.**

## Verdict

**PASS** on the closure question — both of V2's findings are genuinely closed, re-derived from
evidence this unit generated itself. **Recovery: V2R left no guard reverted, `action_taken: none`.**
**GAP** on C6: the new gate is enforced only by a concurrent unit (U5.7) that is *still writing*.

## Recovery (R1-R3) — the predecessor's work

V2R died with **no closing message** but left a **complete** artifact set: a handoff (10794 B,
`overall: PASS`, `tool_calls: 70`), `units/V2R.md`, an appended `VERDICTS.md:362` section,
`state/verify/V2R/` (18 files, incl. `store.py.bak`, `candidates.py.bak`, `shas-before.txt`,
`store_copy.sqlite`), and three `state/logs/V2R-*.txt`. Every claim in it was treated as
**unverified** and re-derived.

**No guard was left reverted.** Current shas == `shas-before.txt` == `.bak` shas == V2R's claimed
restore shas: `store.py` `528adc43…`, `mine/candidates.py` `3b3014ca…`. Zero backup mismatches.
Zero revert tell-tales in `src/resextract/mine/*.py` / `store.py`.
`pytest tests/test_mine_candidates.py tests/test_store_v3.py tests/test_store.py -q` -> **65 passed**
(RC 0) before and after. `action_taken: "none"`. No file was restored because none needed it.

## Checks

| Check | Verdict | Evidence |
|---|---|---|
| C1 FAIL A closed | **PASS** | `{replay:10}`, model 0, NULL 0; CHECK rejects `bogus` (UPDATE+INSERT); half-evidence `unknown`; `runs.model` NULL x4 |
| C2 FAIL B closed | **PASS** | replay `0/2`, model `2/2`, transport saw 2 requests |
| C3 red->green | **PASS** | `assert 'replay' == 'unknown'` @456; `assert 2 == 0` @419; both sha-restored |
| C4 migration | **PASS** | 12/12 tables, `rows_lost={}`, additive only |
| C5 finish_run/run3 | **PASS** | appends; run 3 `failed`/`finished_at NULL` |
| C6 gap | **GAP** | only caller `run.py:1273`; U5.7 in flight; dockets unlabelled |
| C7 honesty | **PARTIAL** | see audit; one self-disclosed `.worktrees/` listing |
| C8 containment | **PASS** | Duval + real store unchanged |

## Artifacts

- `state/verify/V2S/checks.py` · `state/verify/V2S/checks.log` (C1, C2, C4, C5)
- `state/verify/V2S/redgreen.py` · `state/verify/V2S/redgreen.log` (C3)
- `state/verify/V2S/backups/{store.py,candidates.py}.v2s-orig`
- `state/verify/V2S/copies/{c1,v2,half,finish}.sqlite` (the only stores written to)
- `state/verify/V2S/c2/{replay,model}/` (two hermetic mine drives)

## Next

1. Let U5.7's `run.py`/`docket/*` stop moving, then verify the producer gate end-to-end and decide the
   fate of the two pre-gate dockets (no `generated_by.producer`).
2. Relax the four `tests/test_store_v2.py` version pins (U0.12's job) so that suite is live again.
3. Run real mining when the Occamy endpoint returns.
