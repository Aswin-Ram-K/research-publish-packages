# UPAPER7 — Draft the gated-read batching manuscript

**Status:** done · **Bound:** 50 tool calls (used ~18) · **Write paths:** `papers/gated-read-batching/**`,
`orchestration/units/UPAPER7.md`, `orchestration/handoffs/UPAPER7.json`

## One purpose

Create `papers/gated-read-batching/MANUSCRIPT.md` — a complete, submittable-quality paper for the #7
result that unit **ULEAD1** recommended as the only publishable lead: *batching 16–90 binary gate decisions
at `effort=none` is free on this task*, with the honest R1 negative (best binary gate F1 0.320, precision
0.418 @ recall 0.233) reported as a finding. `ULEAD1`'s dominant cost for #7 was that **no manuscript
existed** — only a run report. That is what this unit fixes.

## Scope

- **R2 (batching) + R1 (gate quality only).** `papers/` previously held one manuscript belonging to the
  excluded item; this is a new, independent package directory.
- **R5 (the end-to-end / staged-extraction arm) is dropped** and said so in Limitations, not silently.
- **R3 (staged shortlist) and R4 (router) are out of scope**, named as such.
- No claim anywhere about downstream task accuracy, context-cost reduction, or prompt-injection exposure.

## Deliverables (all written)

| File | Words | Content |
|---|---|---|
| `papers/gated-read-batching/MANUSCRIPT.md` | 5,193 | Title · Abstract · §1 Introduction · §2 Related work · §3 Method · §4 Results · §5 Discussion · §6 Limitations · §7 Conclusion · References |
| `papers/gated-read-batching/CLAIMS.md` | 2,109 | 73 quantitative claims, each with `file:line` or exact JSON key path, plus a recomputation-vs-source classification for every row |
| `papers/gated-read-batching/REFS.md` | 1,286 | 13 cited references in 3 provenance tiers; 2 re-verified here, 11 verified-in-source-only, 0 UNVERIFIED identifiers cited |
| `papers/gated-read-batching/GAPS.md` | 2,192 | 24 numbered gaps: measurement gaps, dropped-scope justification, disclosure abstractions, ranked reviewer asks, and the unit's own production gaps |

## Method

1. Read `strategy/LEAD_PACKAGE.md` (ULEAD1) as the spec, then `GATED_READ_2026.md` and the summary/data it names.
2. **Re-derived every headline metric from the raw 9,260 per-row records** rather than trusting the report's
   rounded prose. Recomputation confirmed the throughput roster exactly (1,800 / 120 / 20 calls, confirmed against `GATED_READ_2026.md:126-132`;
   631,210 / 269,614 / 261,090 prompt tokens; F1 0.2176 / 0.2268 / 0.2105) and *corrected* one source sentence
   (the "10× the total of bs1-minimal" claim — G-01).
3. Found a nuance the F1 column hides: the three `effort=none` configurations admit 73 / 268 / 146 of 1,800
   pairs at nearly equal F1 — a changed **operating point**. Reported in §4.1 and Limitations, since for a
   gate the operating point is the thing that matters.
4. Verified two load-bearing literature references by live search (BatchPrompt, Batch Prompting) because the
   paper's related-work positioning hinges on them. Did **not** pad §2 with searched citations.
5. Abstracted or excised four classes of source material under the author's *publish the design, keep the
   implementation* posture (recorded as G-16…G-20).

## Evidence

- Word count 5,193; 8/8 prose sections; 73/73 claims carry a source line; 0 invented numbers.
- R1 negative reported: **yes** — §4.2 and Limitations state best F1 0.320 / precision 0.418 @ recall 0.233 and
  call it a negative result. An early design claim that the gate "removes 85 % of the file-read surface for
  about 8 % of the gold" was **not repeated**, because the run report files it under `CLAIM_TO_REPRODUCE`
  (G:321) and the rows give 94.6 % file-level precision at 22.8 % recall — a discrepancy recorded in
  CLAIMS.md's G-01/G-02 notes rather than papered over.
- R5 dropped and noted: **yes** (Limitations + GAPS G-13).
- Mechanism abstracted: **yes** (GAPS table G-16…G-20; the corpus file inventory itself is flagged as still
  needing the rename described in ULEAD1's manifest — flagged, not actioned, because the target is read-only).

## Blocker

None. The package is complete for review.

## Next unit hint

A verifier should: (1) re-fetch the 11 Tier-B references; (2) re-derive C67–C73 from `gated-read-rows.jsonl`;
(3) test the **framing** of the newly authored §1/§2/§5/§6/§7 separately from the numbers, since those sections
are this unit's reasoning rather than edited source text (G-21); (4) treat the two `null` `prompt_tok_total`
fields in `gated-read-summary.json` as a harness gap (G-02), not a paper error.
