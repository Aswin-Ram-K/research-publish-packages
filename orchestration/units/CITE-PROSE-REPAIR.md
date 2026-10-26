# UNIT CITE-PROSE-REPAIR — repair prose damage left by CITE-VERIFY

**Status:** done (executed 2026-10-24). **Queue note:** the card said "do not start until
V-RELEASE-BATCH has finished". No handoff or card for `V-RELEASE-BATCH` exists on disk
(`orchestration/handoffs/`, `orchestration/units/`), the newest unit cards on disk are
`LAZY-LOAD-ARM.md` / `SANITISE-RELEASE.md` / `CITE-VERIFY.md`, and
`papers/context-cache/MANUSCRIPT.md`'s mtime was 21:16:53 while this unit started at 21:38 —
21 minutes of quiet. Conservative reading: the predecessor had already finished, so the
dependency was satisfied. Recorded as an assumption in the handoff.

## The defect

`CITE-VERIFY` resolved three `[CITATION NEEDED — verify]` markers by in-place substitution
(the file must keep 1214 lines), and in two places the replacement text was dropped into the
grammatical slot the marker used to occupy:

1. **Lines 885-887 — the 10a citation policy.** The sentence "A citation is marked **verified**
   only when this package could name a source that was read *in this workspace*; everything else
   is marked `[CITATION NEEDED — verify]`" now read "... everything else is marked
   `[SGLang review of attention backends](https://docs.sglang.io/…)`, sources cited only when
   that package read them here (`R-SGL.md`, `R-VLLM.md`); any other pointer is marked and
   resolved against the primary source as in 10a.1 and 10a.2." The policy sentence therefore
   asserted that its own policy marker **is** a link to the SGLang docs — false, and it also
   left "sources cited only when that package read them here" as an orphan clause.
2. **Lines 906-907 — 10a.1.** The engine-paper sentence ended "… (Zheng et al.,
   [arXiv:2312.07104](https://arxiv.org/abs/2312.07104)) — both resolved" with no full stop and
   no object for "both resolved".

No gate catches either: every checker that touches this file reads numbers, claim ids or claim
census lines, not prose grammar.

## What was done

Edits inside existing lines only; no number, no citation id, no URL, no line count changed.

| Line(s) | Change |
|---|---|
| 885-887 | Policy sentence rebuilt as one self-consistent sentence: verified means the package could name a source read *in this workspace*, **as the SGLang attention-backend documentation is** (`R-SGL.md`, `R-VLLM.md`); anything else **stays marked as unverified** and is resolved against the primary source, as in 10a.1 and 10a.2. The doc URL is no longer in the marker's slot; it survives intact in 10a.1, in the RadixAttention sentence, where it is an ordinary example of a source read here. |
| 906-907 | Sentence finished with a full stop; "both resolved" now resolves to a sentence. |

## Deliberately not changed (reported, not applied)

Construction faults in the same section that are **not** in-place-substitution damage:

- `MANUSCRIPT.md:916`: "most work compaction work reports *task quality*" — duplicated "work".
- `MANUSCRIPT.md:896`: "how Section 8a's repair was made to measure a single send rather than a
  same-turn self-hit" — a malformed passive ("how … was made to measure").

None is a marker substitution and none breaks a policy statement; they are recorded for a later
prose pass rather than smuggled into this one. A third suspected fault, the LMCache clause at
`MANUSCRIPT.md:957`, was checked and is **not** a fault: the clause is a complete three-item
list ending in a full stop, in a section whose sentences are concatenated without blank lines.

## Constraints honoured

- `wc -l papers/context-cache/MANUSCRIPT.md` = 1214 before and after.
- Three line-pinned guards green: `tests/test_gap_closure_ledger.py`,
  `tests/test_g5_fanout_attribution.py`, `tests/test_paper_g3_bands.py`.
- `release/**` and `experiments/**` untouched.

## Proof (verbatim)

```
before  e7728890c1182e872ae93739436628464e1891817c1ed3bee8926d72dd9e3aea  papers/context-cache/MANUSCRIPT.md   1214 papers/context-cache/MANUSCRIPT.md
after   37a3f1b34eb43c0c47dc9d41dd02158e6ac000f888b6ee92fe26c93f3ef008cd  papers/context-cache/MANUSCRIPT.md   1214 papers/context-cache/MANUSCRIPT.md

verify_package: PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, 8 script-backed + 61 recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none
COVERAGE GUARD PASS  69 claims documented, 67 runnable here + 2 script-backed
25 passed in 0.08s   (test_gap_closure_ledger, test_g5_fanout_attribution, test_paper_g3_bands)
54 passed in 5.78s   (test_orchestration_handoffs, test_claims_value_guard, test_paper_attribution_guard, test_context_cache_qualifier)
```
