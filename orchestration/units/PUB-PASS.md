# PUB-PASS — external-publication pass on `papers/context-cache/`

**Status: partial.** Everything chartered is done and green; the batch's second acceptance tail
is red for a reason outside this unit's write scope.

## Purpose (one)

`papers/context-cache/` targets external publication (decision ledger `0b9eb7f7`, answer A1). Add
only what an external reader needs and the manuscript does not have: a related-work section, a
threats-to-validity section that names G4 **and** G12, and a "what this is and is not" note.

## Bound

30 tool calls, bash <= 10. **Used: 20 tool calls, 10 bash.** No network, no live requests, no
containers, no `.occamy.lock`, no git, no `ask_user_question`.

## Write paths

`papers/context-cache/MANUSCRIPT.md`, `orchestration/handoffs/PUB-PASS.json`,
`orchestration/units/PUB-PASS.md`. Nothing else was written. `CLAIMS.md`, `GAPS.md`, `RUN.json`,
`recompute.py`, `recompute_r2.py`, `verify_package.py`, `state/**`, tests and all cell/rows files
were read only.

## What was added (987 -> 1212 lines, +225, zero deletions)

1. **"What this is and is not"** — one bold-lead paragraph between the abstract and `## 1`.
   Untitled on purpose: no heading anchor moves. States that the paper measures serving-stack
   economics and context placement, not model intelligence or answer quality; that the accuracy
   figures are a sensitivity check, not a benchmark; that the summariser is a stub.
2. **`## 10a. Related work`** — before `## 11`, with five subsections:
   10a.1 engines (SGLang radix cache, vLLM chained-hash APC + `--prefix-match-unit`),
   10a.2 agent context management / compaction, 10a.3 pointer/retrieval-structured context,
   10a.4 KV eviction and memory-bound serving, 10a.5 prompt-layout / renderer effects.
   Named `10a.` so `## 11` and `## 12` keep their numbers and no anchor moves.
3. **`### 11.1 Threats to validity`** — appended to `## 11`, T1–T9, each grounded in a measured
   fact and in `GAPS.md`; opens with the law-vs-magnitude split the operator asked for.

## Citations: 11 verified, 3 `[CITATION NEEDED — verify]`

Two of the five families could **not** be supported offline and say so in their own lines rather
than carrying an invented reference:

- **10a.1 tail** — the vLLM/PagedAttention and SGLang/RadixAttention *papers*. This workspace
  pins those engines' **documentation** and source, never their papers, so no arXiv id was
  available. Both engines are still cited to findable primary docs in the body of 10a.1.
- **10a.2 whole family** — no citable agent-memory or compaction reference exists anywhere under
  `docs/serving-options/` or `docs/prompt-system/`. The section states this in one line.
- **10a.5 tail** — no prior work isolating *renderer* choice was found; none asserted.

Every one of the 11 verified citations was read out of a workspace file (`R-CROSS.md`,
`R-PROD.md`, `GAPS.md:498`) and carries its primary URL in the prose. **No year, venue or page
was reconstructed from memory.**

## Acceptance tails

| Command | Exit | Result |
|---|---|---|
| `python3 papers/context-cache/verify_package.py` | **0** | PASS — 69 claims, 69 mapped 1:1, UNVERIFIED: none |
| `pytest test_paper_attribution_guard.py test_claims_decompose.py test_claims_value_guard.py -q` | **1** | 3 failed, 37 passed |

The 3 failures are `tests/test_claims_value_guard.py` C66/C67 value-cell guards **on
`CLAIMS.md`** — a file this unit is forbidden to touch, untouched since 13:04, before the session
started. `test_claims_decompose.py` never failed (19 passed). The manuscript-dependent guard
`test_paper_attribution_guard.py` is **18 passed, exit 0**.

## Attribution guard: fixed the prose, not the guard

The new prose initially tripped the guard at `MANUSCRIPT.md:1110` and `:1178/:1179` — it restated
`1.700x` outside the guard's 6,000-character attribution window. Both statements were reworded to
carry the G1 window-truncation / not-a-fork-append-cost attribution inline. The guard file was
not modified.

## Numbers

**0 changed.** Every measured figure in the new prose was copied verbatim from existing manuscript
text or from `GAPS.md`/`CLAIMS.md`. Details that could not be restated with their attribution
(namely the compaction magnitudes in 10a.2/10a.3) are cited **by name rather than by number**.

## Blocker and next unit

`CLAIMS.md` C66/C67 value-cell drift (plus a stale `UNUSED` waiver key in C67) needs a dedicated
CLAIMS-REPAIR unit with write access to `CLAIMS.md` alone. Separately, a **network-enabled
citation-resolution unit** is required before submission to retire the 3 `[CITATION NEEDED]`
items. Do not submit until both land.
