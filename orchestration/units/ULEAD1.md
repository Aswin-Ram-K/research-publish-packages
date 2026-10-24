# ULEAD1 — which package leads `research-publish-packages`

**Purpose (one):** identify the single best package to publish first, and say exactly what it would contain
and what work it needs.

**Hard bound:** 35 tool calls. Used **23** (22 investigation/read + this write batch). Status: `done`.

**Write paths (declared, nothing else touched):**
`strategy/LEAD_PACKAGE.md` · `orchestration/units/ULEAD1.md` · `orchestration/handoffs/ULEAD1.json`

**Target:** `/home/zer0null/Duval` — read only. Commands used: `ls`, `find`, `wc`, `sed`, `head`, `grep`.
No writes, no `git`.

---

## Method

Treated `strategy/PAPER_CANDIDATES.md` §G/§D/§E and the supplement as a **hypothesis to test**, not evidence.
For each viable candidate: located the material on disk, **counted files**, and ran the exclusion pattern set
over the *actual files that would ship*. Outcome: `papers/` holds exactly **one** manuscript (18 files, all
under `papers/encoder-crossover-190/` — the excluded #3), so **no viable candidate has a manuscript**.

## Finding (detail in `strategy/LEAD_PACKAGE.md`)

- **Lead: #7 scoped to R2** — *batching 16–90 binary gate decisions at `effort=none` is free*, n=1,800/config.
  7 files on disk, **no fixture dependency**, gate hits are **losslessly** removable (1 prose sentence at
  `GATED_READ_2026.md:327`; 432 row hits confined to `tag`/`file` metadata columns; `bench.py` and
  `gated-read-summary.json` at 0). **A manuscript must be written** (~3–4k words) — the existing file is a run
  report, not a paper. ~1–2 weeks to a DOI.
- **Runner-up: NC1.** Gate-clean (0 hits in `evals/prevention.ts`; 4 prose hits in `MISTAKES.md`) and
  fixture-free, and its headline invariant is currently **true** (verified by counting the detector table:
  **19 rows — 12 automated, 3 partial, 4 manual**, matching `MISTAKES.md:386`). But its reproducibility
  requires the ~17-file `scripts/` detector set + 3 `.githooks/` + **`tools/trace.ts`, which is in the M13
  withhold block** — so "paper-only, 1–2 weeks" is true for the paper and false for the package.
- **#4 was displaced by measurement, not by preference.** Its gate hits (`admit(` ×3, `expanded[` ×4 per rows
  file) sit **inside the option text the model chose between** — a lossy scrub and the same class as the
  excluded #3. `§G.1` marks #4 `publish` without noticing this.
- **Surveys (#13/#14) are legitimate papers but not legitimate leads**: #13 is gate-clean (1 hit), 1,529 lines
  and the fastest DOI in the corpus, but a survey ships **no artifact**, so it cannot prove a *code+paper*
  pipeline. Recommend as a parallel fast-DOI side-channel only.
