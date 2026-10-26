# LaTeX toolchain for this workspace (recorded by UTEX1, 2026-10-17)

## What is installed, and where

- **Tectonic 0.15.0** — single self-contained binary, installed **inside the workspace** (nothing outside it).
  - binary: `scratch/utex1/bin/tectonic` (37,185,032 bytes, `tectonic 0.15.0`)
  - tarball kept: `scratch/utex1/tectonic.tar.gz` (14,175,003 bytes)
  - downloaded from: `https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz`
  - sha256(tarball) = `dfb82876f2986862996e564fa507a9e576e0c1e3bee63c2c1bd677c2543e6407`
  - package cache (populated on first run): `scratch/utex1/cache`
  - scratch/temp/home redirects: `scratch/utex1/tmp`, `HOME=$PWD/scratch/utex1`

## Why not apt / TeX Live

- `sudo -n true` → **exit 1**: `sudo: The "no new privileges" flag is set, which prevents sudo from running as root.`
- `apt-get` exists (`/usr/bin/apt-get`) but the session runs as uid 1000 and apt needs root:
  `E: NOTE: This is only a simulation! apt-get needs root privileges for real execution.` (with `--simulate`)
- `tlmgr` is absent (no TeX Live installed). No `pdflatex`/`xelatex`/`lualatex`/`latexmk`/`bibtex`.
- **No password was ever requested or worked around.** Tectonic needs neither root nor a password.

### Environment gotcha (this is the thing that wasted the first attempt)

Tectonic needs a writable `HOME`, temp dir and cache. `$HOME` (`/home/zer0null`), `~/.cache` and
`/var/tmp` are **read-only** here; `/tmp` and the workspace are writable. First run failed with:

```
error: Read-only file system (os error 30)
```

Fix (always export all three):

```sh
export TECTONIC_CACHE_DIR="$PWD/scratch/utex1/cache" TMPDIR="$PWD/scratch/utex1/tmp" HOME="$PWD/scratch/utex1"
```

## The exact command that compiles paper #3

```sh
cd "/home/zer0null/reserach extarctor"
export TECTONIC_CACHE_DIR="$PWD/scratch/utex1/cache" TMPDIR="$PWD/scratch/utex1/tmp" HOME="$PWD/scratch/utex1"
scratch/utex1/bin/tectonic -Z continue-on-errors -r 1 --keep-logs \
  -o scratch/utex1/out papers/encoder-crossover-190/submission/main.tex
cp scratch/utex1/out/main.pdf papers/encoder-crossover-190/rendered/encoder-crossover-190-latex.pdf
```

- `-r 1` = rerun the engine once (two passes; settles cross-references). Running the command twice
  changes nothing further.
- **CORRECTED 2026-10-19 (UPREPRINT2).** `-Z continue-on-errors` is **NOT required** and must not
  be used.  The strict build of all three regenerated `main.tex` files is clean: **exit 0**, **0
  `Undefined control sequence`**, **0 `!`** lines, page count unchanged (25 / 13 / 10).  The old
  claim is retained below as dated history.
- **SUPERSEDED 2026-10-19 (UPREPRINT2), kept as dated history:** ~~`-Z continue-on-errors` is
  **required** because `main.tex` contains 2 undefined macros (below).  Without it Tectonic
  exits 1 and writes **no PDF**.~~
- Tectonic 0.15.0 has **no `--interaction` flag** (that was the second failed attempt); it is
  non-interactive and never prompts.
- No BibTeX run is needed: the bibliography is inlined as `thebibliography` (13 `\bibitem`s).

## Packages the preamble needs (do not re-derive)

`\documentclass[11pt]{article}` + exactly six `\usepackage`: `inputenc` (utf8), `fontenc` (T1),
`amsmath`, `amssymb`, `array`, `url`. `array` is load-bearing: every table uses
`>{\raggedright\arraybackslash}p{...}`. Tectonic auto-fetched the standard bundle on demand
(`ec-lmr12.tfm`, `cmmi*`, `cmsy*`, `cmex*`, `umsa.fd`, `msam*`, `umsb.fd`, `msbm*`, `t1lmtt.fd`, …).
Nothing from `texlive-latex-extra` is required.

## Timing (warm cache, this host)

- pass 1: **4 s**; pass 2: **1 s**. A clean-cache first run additionally downloads the bundle (network-bound).

## Manuscript defects found (not toolchain problems — do not "fix" by editing main.tex)

**SUPERSEDED 2026-10-19 (UPREPRINT2):** the four `\SB3` / `\SF.3` sites listed below were fixed at
source by the `\S{}` control-word fix in `tools/package/md2tex.py`; the regenerated `main.tex`
compiles with 0 `Undefined control sequence`.  The list is retained as dated history.

- `main.tex:62` — `\SB3` is an **undefined control sequence** (elsewhere the paper writes `\S2`, `\S4`, `\S6`; `\SB3` is a mangled `\S3`).
- `main.tex:335` (twice) and `main.tex:339` — `\SF.3` likewise undefined (`\SF` = 3 occurrences).
- Under `-Z continue-on-errors` the macro is dropped: the PDF reads `internal reference notes 3;` and
  `the paper-candidates record .3 is not discharged`. Chrome's renderer instead printed `§B3` / `§F.`.
  Either way **the author must fix these 4 sites**; until then no renderer is faithful there.
- 42 Overfull / 98 Underfull `\hbox` warnings (the document sets `\sloppy`). Word-bbox measurement over
  all 27 pages shows **no word crosses the 540 pt right margin**, so nothing is off-page.

## Would apt/tlmgr be needed again?

- **Tectonic alone covers another paper** using only base LaTeX + these packages — no apt, no tlmgr, no root.
- `tlmgr` is not present and is not needed for this class of document.
- **The TMLR stylefile is NOT installed.** `main.tex` uses stock `article`, so a TMLR *submission*
  additionally needs `tmlr.sty` (+ the TMLR template's `fancyhdr`/`natbib`/`hyperref`/`booktabs` stack)
  placed where Tectonic can see it (`-Z search-path=<dir>`). That has **not** been done or tested here.
