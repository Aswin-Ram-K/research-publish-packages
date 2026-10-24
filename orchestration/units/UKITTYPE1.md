# UKITTYPE1 — surface Article type + per-paper Data availability; fix stale mapping

- **Bound:** 10 tool calls.
- **Purpose:** (1) Add a `Article`-type subsection to `strategy/SUBMISSION_KIT.md` §3 before the per-paper rows. (2) Add per-paper concept-DOI table to §3 under Data availability. (3) Fix stale step 8 in `strategy/PREPRINTS_SUBMISSION.md` §8 with dated `Superseded 2026-10-19:` note preserving old wording.
- **Write paths:** `strategy/SUBMISSION_KIT.md`, `strategy/PREPRINTS_SUBMISSION.md`, `submission-kit/README.md`, `orchestration/units/UKITTYPE1.md`, `orchestration/handoffs/UKITTYPE1.json`, `scratch/ukittpye1/**`.
- **Read-only:** `/home/zer0null/Duval` (untouched), `papers/**`, archives/packages.
- **Facts (verified, do not invent):**
  - Type = `Article` for all three; `Conference Paper` only for unpublished DOI-less conference papers.
  - encoder-crossover-190: concept `10.5281/zenodo.23463944`, record `23482311` (v3)
  - replay-record-not-decision: concept `10.5281/zenodo.23482511`, record `23483304` (v2)
  - gated-read-batching: concept `10.5281/zenodo.23483314`, record `23485733` (v2)
- **Verification:** DOIs vs kit §1 status table lines 15-17 (table wins on disagreement); `23463944` gone as instruction for #2/#7; grep `strategy/*.md` for `23463944` and classify each hit.
