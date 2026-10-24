# GUARD-ATTR — a prose guard for C44's attribution

**Status:** done · **Batch:** post-V-PAPER repair · **Written by:** the unit itself (AGENTS.md rule 4).

## Why this unit existed

V-PAPER returned `overall: partial` with exactly one hole, in `not_reproduced`:

> doc-side red->green guard in `tests/test_claims_decompose.py`: that file tests resextract
> claims-store, not context-cache attribution; no test reads the patched docs

`PATCH-CLAIMS` re-attributed U15's 1.700x from a break-cost effect to a post-compaction
**window truncation** effect. `papers/context-cache/recompute.py:840-842`'s C44 guard does flip
to FAIL when `survives_decomposition` is expected True — but that check is code-side: it tests a
number, not a sentence. Nothing in the repo read `papers/context-cache/MANUSCRIPT.md`, so a
revert to the refuted causal sentence would have left every check green.

## Objective (single)

Make that drift fail loudly: a test that reads the paper's own prose and fails when it asserts
or implies that avoiding the break / not creating the break / forking instead of compacting
saves prefix tokens.

## What was built

`tests/test_paper_attribution_guard.py` — 9 tests, offline, no rows, no network:

| test | asserts |
|---|---|
| `test_the_package_documents_exist` | both documents are present |
| `test_no_document_re_attributes_the_1_700x_to_break_cost` | the whole guard over both documents |
| `test_the_figure_is_actually_stated` | the guard is not vacuous |
| `test_the_attribution_is_stated_in_the_abstract_and_in_section_6` | G1 attribution at the two places a reader meets the claim |
| `test_c44_guard_in_recompute_is_not_weakened` | `recompute.py` still expects `survives_decomposition=False` |
| `test_a_quotation_is_exempt` | a double-quoted (historical) span is not a causal assertion |
| `test_a_quotation_cannot_smuggle_the_claim_back` | an *unquoted* statement of the refuted reading is still caught |
| `test_every_denial_pattern_matches_its_own_refuted_sentence` | no dead DENY pattern |
| `test_a_negated_sentence_is_not_a_denial` | G1's own "…, not break-event cost" never reads as the claim |

### Design: presence + denial, not a whitelist

The brief called a table of known-good phrasings "a trap". So the test asserts:

* **(A) presence** — an `ATTRIBUTION_EFFECT` marker (`window truncat` / `compaction-window`
  / `steady-state truncat` / `truncation *plus*`) **and** an `ATTRIBUTION_NEGATION` marker
  near each statement of the figure (window ± 6,000 chars; the abstract paragraph is 1,077
  chars and in `CLAIMS.md` the C21/C24 rows sit 5,034–5,171 chars above C44's re-attribution
  because the table is column-aligned — measured, not assumed);
* **(B) denial** — five refuted *assertions* (DENY-1…DENY-5: the win *is* a break cost;
  avoiding the break *saves* the prefix; forking instead of compacting *preserves* it; not
  compacting *buys* the 1.700x; compacting less often *saves* prefix tokens) plus one
  assembled framing (DENY-6);
* **not a blast radius over the noun**: "break" appears legitimately everywhere here (§ 6's
  table column is literally "Net break cost"), so a bare noun is never a finding.

A rewrite that keeps the G1 cause passes; a rewrite that flips the cause fails.

### Scope: causal claims only

Historical quotations are exempt by a marker the documents already use — double-quoted spans.
`CLAIMS.md` § "Corrections to the source cards" row 7 (`U15: "avoiding the break saves the
prefix"`) and § "Supersessions by C21" are exactly that case. Inline code spans (cards, files,
claim ids) are skipped too. No invisible syntax was invented.

## Verification

```
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_paper_attribution_guard.py -q
```

* **GREEN** on the current tree: `9 passed in 0.03s`.
* **RED-1** (abstract sentence reverted to the U15 reading): `2 failed, 7 passed` —
  `MANUSCRIPT.md:21 [ATTR]`, `MANUSCRIPT.md:28 [ATTR]` ×2, while
  `tests/test_claims_decompose.py` stays `13 passed` and `recompute.py all` stays
  `42 claims checked, all match`.
* **RED-2** (CLAIMS.md C44 row re-described as a break-cost win): `1 failed, 8 passed` —
  `CLAIMS.md:127 [DENY-1]` + `CLAIMS.md:94`/`:97 [ATTR]`.
* Restored bit-identically after each revert; transcript at
  `state/logs/GUARD-ATTR-redgreen.txt`.

## Hard bound

≤ 60 tool calls. Actual: 58.

## Write paths

`tests/test_paper_attribution_guard.py`, `papers/context-cache/RUN.json` (registration block
only), `state/logs/GUARD-ATTR-redgreen.txt`, `orchestration/handoffs/GUARD-ATTR.json`,
`orchestration/units/GUARD-ATTR.md`.

NOT written: `MANUSCRIPT.md` and `CLAIMS.md` were reverted in place for the red proof and
restored to their pre-edit sha256 (asserted in the generator, not just checked by eye).

## Next hint

C44's prose half is now enforced. The next open item is unchanged: CX-V3 on U15
(`RUN.json: verification.still_unverified`) and G15's residual per-break variation.
