# UCORR4 — narrow the false universal "every correction moved the affected arm DOWN" in `strategy/SOCIAL_PRESENCE.md`

**Status:** done
**Hard bound:** max 25 tool calls (used ~11). STOP → `partial` if exceeded.
**Target repo:** `/home/zer0null/Duval` — strictly read-only (read only, never written).

## Purpose
UCORR3 corrected the false universal *"every correction moved the affected arm DOWN"* in
`strategy/PAPER_CANDIDATES.md`, but recorded 3 further occurrences in `strategy/SOCIAL_PRESENCE.md`
(`:73`, `:263`, `:919`) outside its declared write paths. UCORR4 owns that file and narrows them to the
reading the raw evidence supports. M12 is **retained and narrowed** (the method learning is real and is
used as argument evidence) — nothing true is deleted.

## Evidence re-verified (step 1 — before editing)
From `/home/zer0null/Duval/docs/research/EXP#12-evidence/`:

| Arm | Pass 1 (buggy order probe) | Final | Direction |
|---|---|---|---|
| `setfit-mpnet` | 0.315789 → 0.3158 → 0.2947 | **0.263158** | **DOWN** |
| `modernbert-base` | **0.342105** | **0.347368** | **UP** |

- `DEFECT-EVIDENCE.json` `.passes.pass1_buggy_order_probe.arms.modernbert-base.accuracy` = 0.342105
  vs `.passes.final.arms.modernbert-base.accuracy` = 0.347368.
- `DEFECT-EVIDENCE.json` `.setfitIntermediates.variants[0..2].accuracy` = 0.3158, 0.3158, 0.2947;
  `.passes.final.arms.setfit-mpnet.accuracy` = 0.263158.
- `eval-setfit-mpnet.json` `.accuracy` = **0.2631578947368421**.

**Correct interpretation:** the instrument defects caused an **asymmetric** bias that **inflated the gap
between the arms**; they did **not** uniformly depress the candidate. No divergence from the brief was
found, so editing proceeded.

## Occurrence sweep (step 2 — whole file + other strategy docs)
Searched all of `strategy/` for `every correction moved`, `all three corrections`, `moved the candidate
down`, `corrections moved`, `M12`, and the five numerals `0.3158 0.2947 0.2632 0.342105 0.347368`.

| File | Line | Kind | Action |
|---|---|---|---|
| `strategy/SOCIAL_PRESENCE.md` | 73 | argument evidence (ranking #3 first) | narrowed, errata marker |
| `strategy/SOCIAL_PRESENCE.md` | 263–264 | social-engagement note | narrowed, errata marker |
| `strategy/SOCIAL_PRESENCE.md` | 919 | method-observation context | narrowed, errata marker |
| `strategy/README.md` | — | no such claim (grep exit 1) | none |
| `strategy/PAPER_CANDIDATES_SUPPLEMENT.md` | 191, 195 | M11/M12 **registry-class cross-walk only** — no downward/upward claim | none (out of scope) |
| `strategy/PUBLICATION_STRATEGY.md`, `VERIFICATION_REPORT*.md`, `VISA_*.md` | — | no such claim | none |

**Occurrences found = 3. Occurrences fixed = 3. Extra files carrying the claim = 0.**

Each edit is marked `[corrected by UCORR4, 2026-10-15: …]` with the reason and the contradicting
key+value, keeping the append-only errata norm.

## Argument judgement (step 3 — wording vs. conclusion)
- **`:73` (ranking #3 first).** The conclusion **does not depend** on the false universal. The row's
  grounds are the paired McNemar result (`b=27, c=90, Δ=−0.3316`, exact p = 4.167e−09), harm ≈ 2× the
  paired MDE, and the two controls that can report the opposite. The corrected asymmetry *strengthens*
  the stated public claim — the defects widened the inter-arm gap, so the encoder head's loss was not an
  artefact of the bugs. **Reworded only; conclusion unchanged.**
- **`:919` (methods honesty list).** Observation context. The honest behaviour — disclosing that the
  corrections cut both ways — survives the narrowing intact. **Reworded only.**
- **`:263` (social engagement).** Not an argument premise. **Reworded only.**

**No conclusion requires re-argument.** `arguments_reworded_only` = 3, `arguments_needing_reargument` = 0,
`conclusion_changed` = no.

## Artifacts
- `strategy/SOCIAL_PRESENCE.md` (3 in-place narrowings + errata markers)

## Blocker
None.

## Next unit hint
The M12 wording is now consistent across `strategy/PAPER_CANDIDATES.md` (UCORR3) and
`strategy/SOCIAL_PRESENCE.md` (UCORR4). A verifier should re-run the sweep over `strategy/` for the
five numerals plus "M12" to confirm zero un-narrowed universals remain (the only surviving match is
UCORR4's own quoted old wording inside an errata marker, which is intended). No further write paths.
