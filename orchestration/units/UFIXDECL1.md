# UFIXDECL1 — Fill declaration headings (author contributions, AI use, funding, competing interests, compute)

## Purpose
Fill the six declaration headings in `papers/encoder-crossover-190/MANUSCRIPT.md` (emptied by UFIXBODY3) with the
author-approved statements, and the same headings in the other two papers if present. Regenerate main.tex via
`md2tex.py`, rebuild tarballs, recompile PDFs, prove numeric invariance.

## Write paths
- `papers/*/MANUSCRIPT.md`, `papers/*/submission/{main.tex,*.tar.gz,BUILD_NOTES.md}`, `papers/*/rendered/*.pdf`
- `orchestration/units/UFIXDECL1.md`, `orchestration/handoffs/UFIXDECL1.json`, `scratch/ufixdecl1/**`

## Hard bound
18 tool calls. Read-only: /home/zer0null/Duval (never git). Never hand-edit main.tex.

## Content (author-approved)
- Author contributions: single author; question/direction his; he carried out and directed work, wrote paper, takes responsibility.
- Use of AI tools: generative AI assistant helped design and run analysis and experiment, helped draft and edit manuscript; research idea, experimental design, editorial decisions author's; author reviewed, full responsibility; assistant not an author.
- Funding: no external funding.
- Competing interests: none declared.
- Compute and resources: only what record supports; training harness withheld, no run re-executed; wall-clock/GPU-mem/energy not recorded in released record.
- DOI: OUT OF SCOPE (later unit).

## Status
in_progress

## Result
status=done. Only encoder-crossover-190 had the six headings; other two papers carry none. numeric added=removed=0. tectonic exit 0 x3. pytest 7 passed.
