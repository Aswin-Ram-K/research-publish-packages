# UTEX1 — Install minimum TeX toolchain, compile paper #3 with LaTeX

**Purpose:** Produce a genuine LaTeX-typeset PDF of `papers/encoder-crossover-190/submission/main.tex`
(84,345 B, self-contained, ASCII-only, inlined `thebibliography`), replacing/augmenting the headless-Chrome fallback.

**Hard bound:** 20 tool calls. Install attempts ≤3; no password workarounds.

**Declared write paths:**
- `papers/encoder-crossover-190/rendered/**`
- `strategy/LATEX_TOOLCHAIN.md`
- `orchestration/units/UTEX1.md`, `orchestration/handoffs/UTEX1.json`
- `scratch/utex1/**`

**Constraints:** `/home/zer0null/Duval` read-only, no git against it; do not modify `main.tex`.

**Environment at start:** `sudo -n true` → exit 1, "The \"no new privileges\" flag is set"; `apt-get` present at /usr/bin/apt-get; `tlmgr`, `pdflatex`, `xelatex`, `lualatex`, `latexmk`, `tectonic`, `bibtex` all absent.

**Plan:** 1) read preamble → package list. 2) apt route blocked by sudo → Tectonic single binary into `scratch/utex1/bin/`, cache `TECTONIC_CACHE_DIR=scratch/utex1/cache`. 3) compile twice → `rendered/encoder-crossover-190-latex.pdf`. 4) assess vs Chrome PDF via pdftotext. 5) record `strategy/LATEX_TOOLCHAIN.md`.
