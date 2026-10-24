# UTMLR1 — anonymised TMLR variant of the primary paper

**Purpose (one):** Build and prove the anonymised variant of the primary paper so it is TMLR-ready
and cannot surprise us later. Do not submit anything.

**Hard bound:** 20 tool calls. Max 3 Tectonic compile attempts; if not clean, STOP and report the
literal errors.

**Write paths (nothing else):** `scratch/utmlr1/**`, `strategy/TMLR_SUBMISSION.md`,
`orchestration/units/UTMLR1.md`, `orchestration/handoffs/UTMLR1.json`

**Inputs (verified by parent):**
- `papers/encoder-crossover-190/submission/main.tex` — 84,223 B, sha256
  `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`, 467 lines. Read-only.
- Byline: exactly one line `\author{Aswin Ram Kalugasala Moorthy}`.
- Converter: `tools/package/md2tex.py`.
- Tectonic: `scratch/utex1/bin/tectonic` (37,185,032 B, sha256
  `dfb82876f2986862996e564fa507a9e576e0c1e3bee63c2c1bd677c2543e6407`). Needs
  `TECTONIC_CACHE_DIR`, `TMPDIR`, `HOME` exported into the workspace.
- Tectonic 0.15: **no `--interaction` flag**; **`-Z continue-on-errors` MUST NOT be used**.
  Only a clean exit with zero errors counts.
- Command shape: `scratch/utex1/bin/tectonic --keep-logs -o <outdir> <file.tex>`

**Tasks**
1. `scratch/utmlr1/anonymous/main.tex` with neutral anonymous byline + all self-identifying strings removed.
2. Identifier sweep (author name any casing, orcid/ORCID/0009-0009-9505-3546, zenodo/Zenodo,
   github/GitHub, Aswin-Ram-K, research-publish-packages, preprint/DOI links) with file+line; report
   what remains and why.
3. Compile with Tectonic: literal exit code, `Undefined control sequence` count, LaTeX `!` error
   count, page count, PDF sha256.
4. Prove numbers did not move: numeric-literal multiset (bibliography stripped) identical before/after;
   `\cite`/`\bibitem`/distinct-key/uncited/unresolved counts unchanged (expect 13/23/13/0/0).
5. Report honestly what a determined reader could still use to re-identify the author.

**Do NOT:** modify `papers/**`; network calls; accounts; submissions; writes outside listed paths;
credentials in any file.
