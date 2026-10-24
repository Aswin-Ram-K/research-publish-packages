# FIX-GAPS-RUN2 — GAPS.md / RUN.json repair, verified not re-derived

**Card:** FIX-GAPS-RUN2 (board) · **Status:** done · **Writes:** `papers/context-cache/GAPS.md`,
`papers/context-cache/RUN.json`, this card, `orchestration/handoffs/FIX-GAPS-RUN2.json`.

## What the card assumed vs what was on disk

The card said the previous attempt "wrote nothing" and that the defects were still live. On disk at
18:57 the two files carried mtime **18:06** (before the 18:28 execution) and **already contained** the
CX-V3 corrections and a 16-cell `cell_digests` block. So the write had landed; the execution that was
supposed to own it had not. This unit therefore **verified** the existing edits against the verdict and
the disk instead of re-applying them, and repaired the defects the 18:06 pass left behind.

## Defects fixed in this pass

1. **GAPS.md:330-332 claimed EVIDENCE.md was still stale.** EVIDENCE.md was fixed by FIX-EVID-DOC at
   18:00 (earlier than GAPS.md's 18:06 write), so GAPS.md was asserting a contradiction that no longer
   existed. Rewritten to record the fix and that EVIDENCE.md belongs to another card.
2. **GAPS.md:342-345 ("What would close it")** still opened with "CX-V3's independent pass is measured,
   not pending" — a closure condition that names no open measurement. Rewritten to the two real
   conditions (graded correctness measure, real summariser) and to say independence is spent.
3. **RUN.json `cell_digests` was stale by three cells**: 16 rows entries, no DENSE-SGL (894 rows on
   disk); MOE-VLLM and STATE-CLIFF absent from both lists. DENSE-SGL pinned; STATE-CLIFF added to
   `no_rows`; MOE-VLLM placed in a new `unpinned_live` list because its `rows.jsonl` was **still being
   appended to** (22 rows at 18:58:27 → 79 at 18:59:08 → 172 by 18:59:33). Pinning a growing file is
   the exact failure this block exists to prevent.
4. **`pins.u4_sessions_payload_sha256_claimed`** now carries an explicit `_note`: the value names no
   file by design (it is the corpus payload digest inside `u4_sessions.json`), and the real file pin is
   `u4_sessions_payload_sha256`.
5. **`verification.synthesis_recompute.script_sha256`** re-measured by this unit: matches
   `85917e480d1aea24…`; the note now records the second measurement.

## Evidence (commands run in this pass)

```
sha256sum papers/context-cache/recompute.py
  85917e480d1aea24d0d5b85ab75ab0464cd2b950ff6d7622ed093be09716abcc

python3 … inventory over experiments/context-cache/cells/
  rows 17 · unpinned_live 1 · no_rows 13 · sum 31 · cells 31 · missing [] · dupes [] · bad digests []

PYTHONDONTWRITEBYTECODE=1 python3 papers/context-cache/verify_package.py
  PASS — 62 claims … UNVERIFIED: none        (exit 0)

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_run_record_digests.py tests/test_paper_claim_census.py -q
  13 passed

pytest tests/test_paper_attribution_guard.py tests/test_claims_decompose.py tests/test_g5_fanout_attribution.py tests/test_no_stray_package_refs.py -q
  38 passed

.venv/bin/python papers/context-cache/recompute.py all   (tail)
  COVERAGE GUARD PASS  62 claims documented, 60 runnable here + 2 script-backed   (rc 0)
```

## Assumptions recorded

- The two GAPS sites named in the card (CX-V3 pending, vacuous closure) were already correct on disk;
  this unit verified them against `orchestration/VERDICTS.md:12` rather than rewriting correct prose.
- `tests/test_gap_closure_ledger.py` (named by the V-FINAL5 card) does not exist on disk. Reported,
  not created — creating a test is outside this card's write paths.
- MOE-VLLM is a live cell; its `rows.jsonl` will need a digest pin after it settles. `unpinned_live`
  names that debt explicitly.
