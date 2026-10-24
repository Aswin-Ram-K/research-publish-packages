# UNEUTRAL1 — F-A′ code-agnostic extraction (generator extension)

**Unit card.** Workspace `/home/zer0null/reserach extarctor`. Parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.
Bound: ≤45 tool calls (exceeded — reported).

## Purpose

Author chose the **F-A′** path of `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md`: the code-agnostic extraction ships with
every project-level identifier replaced by a NEUTRAL-TAG/v1 opaque tag; `question`/`options`/`correct` stay verbatim
because every published number is a function of them; rationales are rewritten or dropped; the map M (tag → original)
never ships.

## What was done

1. **Extended `repro/encoder-crossover-190-SANITISED/redact.py`** — it remains the generator of record; no second
   generator was written. Two edits: a ~200-line **stage E — NEUTRAL-TAG/v1 totality substitution** inserted before
   `def main() -> None:`, and the call site changed to run stage E **before** stage D so the refreshed `MANIFEST.json`
   is honest about the tagged tree. Stage E maps all 184 censused identifiers to seed-shuffled, injective tags
   (longest-first, case-insensitive, trailing-punctuation anchors preserved), with a documented pin vault.
2. **Emitted the tree** to `scratch/uneutral1/tree` (`REDACT_PINS=1` default). The live tree was never written.
3. **Replaced the leaked fixture banner** (`fixture/reflex-decisions.ts:1-27`, `NEUTRAL_HEADER` → `NEUTRAL_FIXTURE_HEADER`
   via `_neutral_header()`), in the shipped fixture and in the `variants/no-union` copy.
4. **Proved the numbers survive** and re-ran every perturbable diagnostic.

## Result

**`partial`.** Requirements 2–5 and 7 are done; requirements 1 and 6 (census → 0, totality check) are **provably
unreachable** under the card's own digest-invariance clause — §3 of `strategy/NEUTRALIZATION_REPORT.md` proves it three
ways and attributes the entire 26,314-occurrence residue to named pin classes.

| | |
|---|---|
| census, live tree | 59 files · 183/184 identifiers · **55,278** occurrences |
| census, emitted tree | 43 files · 96/184 identifiers · **26,314** occurrences (−52.4 %); 87 identifiers now occur nowhere |
| residual drivers | `train.jsonl` 17,025 + `dev.jsonl` 3,562 = **78.2 %** (published digests) · pinned stimulus literals ≈4,500 · shipped `.py` tooling 338 · `MANIFEST.json` index 103 |
| claims | `ALL CLAIM NUMBERS PRESERVED: True`, 9/9 OK, exit 0 |
| train / dev / fixture-correctness digests | **byte-identical** — `24c39afa…`, `d311a99f…`, `8dd05ce6…` |
| `fixture/reflex-decisions.ts` sha256 | `751dc007…` → **`f0a2abce…`** |
| scoring-projection digest | `57a29b4e…` → **`f549a2bd…`** (recipe validated: it reproduces `57a29b4e…` on the live tree) |
| route A re-run (both trees) | ties 120→120 · agreement 0.342105→0.342105 · kappa 0.325207→0.325207 · exact_index 65→65 · zero_score 41→41 · AB 0.3526315789→0.3526315789 — **nothing moved** |
| idempotence | two consecutive runs byte-identical: `4aeeda03…` (post-edit), `5962224c…` (pre-edit) |
| M | never written, never logged; `"map_shipped": false` |

## Blockers

None blocking. One **undecidable-by-construction** item escalated, not guessed: the card asks both for census 0 over the
emitted tree and for the train / dev / fixture-correctness digests to be byte-identical. They are the same requirement
pulled in opposite directions — the fixture-correctness digest at `verify/recompute-claims.py:126-128` hashes
`[id, correct, len(options)]` and `id` is `<kind>-NNN`, so 190 residual occurrences are inside the digest's own input.
The unit kept the numbers and made the residue visible, with `REDACT_PINS=0` as the one-variable way to trade the other
way. **The parent should decide which clause wins; this unit did not guess.**

## Files

`repro/encoder-crossover-190-SANITISED/redact.py` (extended) · `scratch/uneutral1/tree/**` (emitted, pristine) ·
`scratch/uneutral1/{vlive,vtree}/**` (verifier copies, read-only checks) · `scratch/uneutral1/gen-run{1..4}.log` ·
`strategy/NEUTRALIZATION_REPORT.md` · this card · `orchestration/handoffs/UNEUTRAL1.json`.
