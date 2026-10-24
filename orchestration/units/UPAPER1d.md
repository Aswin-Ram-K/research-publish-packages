# UPAPER1d — fix the manuscript's disclosure and availability statements

**Status:** done (2026-10-15). **Hard bound:** 45 tool calls; used ≈26.

## Purpose (one)
Make `papers/encoder-crossover-190/MANUSCRIPT.md` state the **decided** disclosure policy truthfully: CC BY 4.0
paper, minimal reproducibility subset at `repro/encoder-crossover-190/`, kernel/weights withheld, code licence
separate and **undecided**. Availability and licence statements only — **no result changed**.

## Declared write paths
- `papers/encoder-crossover-190/MANUSCRIPT.md` (edited)
- `papers/encoder-crossover-190/DISCLOSURE_CHANGES.md` (new)
- `papers/encoder-crossover-190/AVAILABILITY.md` (new)
- `orchestration/units/UPAPER1d.md` (this card)
- `orchestration/handoffs/UPAPER1d.json`

Nothing else touched; the target `/home/zer0null/Duval` was never written.

## Defects fixed (each verified in the file before editing)
1. **False licence sentence** — ULIC §8.1 item 4 / §10 D1. The "paper's own licence is a separate, deliberate
   choice that a human must still make" + AGPL "mismatch" paragraph is replaced by the CC BY 4.0 decision.
   `AGPL` no longer occurs in the manuscript; the private repo's `LICENSE` is cross-referenced, not resolved.
2. **Local-path exposure** — ULIC §8.1 items 1 and 3. All `/home/zer0null/Duval` strings removed from §7
   (opener, table, read-only discipline) and from Data-and-code availability; statements repointed at
   `repro/encoder-crossover-190/`. `grep -n /home/zer0null MANUSCRIPT.md` → **NONE**.
3. **§7 + availability rewritten to the real subset** — fixture + schema, harness + commands, pre-registrations,
   results (incl. per-case rows in `results/baselines.json`), second-labeller evidence, plus the honest
   limitation from `repro/encoder-crossover-190/README.md` §5: `harness_self_contained = partial` — six Python
   steps re-run from `harness/` with bundled `data/`, steps 1–2 need the source repo's `scripts/run.sh` +
   `tsx` and a repo-shaped layout, their outputs shipped byte-identical. **No full-self-containment claim.**
4. **Provenance** — the EXP#12 harness is **not on trunk**. Verified independently in the read-only target:
   `git merge-base --is-ancestor a5ef1b28… HEAD` → NOT ANCESTOR; branches containing it →
   `EXP#12-typed-channel-comparison` (+remote); `git ls-tree HEAD -- tools/typed-channel/ | wc -l` → **0**;
   branch has 42 files; `repro/.../harness` has **18** files.
5. **Withheld by policy** — kernel/runtime (`src/**`, `kernel/**`) and all weights (three **public** HF
   checkpoints fetched at run time); `EXCLUDED.md`'s 15 exclusion classes summarised, not reproduced.

## Evidence
- `numbers_changed = 0`. Only availability/licence prose and 9 table rows changed (11 prose sentences).
  Headline numerics re-verified present: 0.3474, 0.4526, 0.2911, 0.6684, **0.6789**, κ 0.9014/0.9053,
  0.3252/0.8837/0.9140/0.3526, 4.167e−09, 0.1595, 0.616 / b=27 / c=90, `39+27+90+34=190`.
- Target HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; `git status --porcelain` identical
  (4 untracked paths, the known unrelated concurrent session).
- `ls "docs/research/EXP#12-evidence" | wc -l` → 26, so the retained "26-file" count is accurate.

## Notes / residual gaps
- `MANUSCRIPT.md` is **untracked** in the workspace git repo, so no pre-edit baseline diff exists; the
  sentence-level before/after is recorded verbatim in `DISCLOSURE_CHANGES.md` for the verifier.
- Remaining source-repo identifiers survive as **provenance only**, not as reproducibility pointers:
  `docs/DECIDER_STACK_DECISION.md` §11.6 + commit `ad301ae1…`, and `REPORT.md:104/:189` (now resolving to
  `repro/encoder-crossover-190/results/REPORT.md`).
- The subset's **code licence is open** (`LICENCE_TODO.md`); the paper says so and does not decide it.
