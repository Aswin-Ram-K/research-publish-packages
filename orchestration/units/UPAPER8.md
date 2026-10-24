# UPAPER8 — Fix manuscript prose for the withheld-harness release scope

**Status:** done. **Hard bound:** 20 tool calls; used 13.

**Write paths:** `papers/encoder-crossover-190/MANUSCRIPT.md`, `papers/encoder-crossover-190/AVAILABILITY.md`,
`orchestration/units/UPAPER8.md`, `orchestration/handoffs/UPAPER8.json`, `scratch/upaper8/**`
**Report-only (NOT edited):** `papers/encoder-crossover-190/CLAIMS.md`, all other files.

## Purpose
Release scope changed: the public artifact ships the sealed fixture, `verify/recompute-claims.py`, the second
labeller's `parse_fixture.py`/`compare.py`, the `results/` records the claims rest on, the pre-registration and
a README — the harness (model, training, evaluation) is withheld. MANUSCRIPT.md still promised a shipped,
runnable harness.

## Work log
- Written skeleton card + handoff first (as instructed), then worked.
- Read MANUSCRIPT.md :725-857 (once), AVAILABILITY.md (whole), and the shipped trees
  `repro/encoder-crossover-190/` and `repro/encoder-crossover-190-SANITISED/` (which carries
  `verify/recompute-claims.py`, `verify/run-verification.sh`, `verify/RECOMPUTE-CLAIMS.txt`).
- Backups: `scratch/upaper8/MANUSCRIPT.md.orig`, `scratch/upaper8/AVAILABILITY.md.orig`.
- Applied **10 edits to MANUSCRIPT.md** and **8 to AVAILABILITY.md** in one uniqueness-asserted pass: every
  before-string was whitespace-normalised-matched and asserted to match **exactly once** before replacement
  (the script exits non-zero on any ambiguous/missing anchor, so no edit was guessed).
- Verified: numeric census + all nine CLAIMS.md values intact.

## Findings / flags (values deliberately left unchanged, per the "change no number" bound)
1. **Fixture hash may have drifted.** MANUSCRIPT.md:799 still quotes the *as-audited* fixture sha256
   `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`. The sanitised build
   (`repro/encoder-crossover-190-SANITISED/README.md` §4) states the shipped/sanitised bytes hash is
   `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae`, with the as-audited bytes being
   `076164ac…`. **Not changed** — flagged for the owning unit.
2. **`harness/data/lint-report.json` is withheld with the harness**, so the leak-lint claim's evidence is no
   longer in the released set. The table row at :751 was reworded to say exactly that rather than deleted.
3. **Path name.** The prose still says `repro/encoder-crossover-190/`; the sanitised build on disk is
   `repro/encoder-crossover-190-SANITISED/`. Left as-is (not in the named target list) — flagged.
4. **Sentences outside the availability section that assume a shipped harness — reported, NOT edited**
   (task item 4): MANUSCRIPT.md:772 *"Instrument integrity checks a replicator should re-run."* — the F4
   seeded-copy and 152,000-pair checks needed the harness. Adjacent: :299 and :686 ("Training is not
   bit-reproducible") imply training can be re-attempted; :765 and abstract :5 ("per-case rows re-score")
   remain true because `results/baselines.json` ships and `verify/recompute-claims.py` recomputes it.
5. No other manuscript passage mentions the harness (grep over the whole file: hits only in §7 and the
   availability section).
