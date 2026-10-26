# TMLR submission variant — encoder-crossover-190

**What this is.** The **double-blind (anonymised) submission variant** of paper #1,
built for the TMLR (Transactions on Machine Learning Research) submission route.

**What this is NOT.** This is **not** the identified preprint. Nothing in this
directory is the named/identified version of the paper; that lives elsewhere
(`papers/encoder-crossover-190/released/`, `papers/encoder-crossover-190/preprints/`)
and must never be conflated with this artifact.

## Provenance

Copied — **not moved** — from the build record at `scratch/utmlr6/tmlr/`, which
remains intact. Install unit: **UTMLRHOME1**.

## The artifact

| file | bytes | sha256 |
|---|---|---|
| `main.pdf` | 176971 | `a777d2a30e1f8707d84673d401a8a231cd4526b4ee78f5a1163070961929acdf` |
| `main.tex` | 83785 | `8d6b036c23e4195e9119f67d2a7493831e836bfd68a9a2d73849eecdfbbf0fd0` |
| `tmlr.sty` | 6560 | `816214ff5919aa457b6b443bee52b15d9561421417b7f8a50cc84651519f0002` |
| `tmlr.bst` | 26969 | `306fd454cf40771bee01293eeb98d2c1cd5f4e11ed0cd7296b335f354fc45206` |
| `fancyhdr.sty` | 17086 | `3d2922548e0e5f1a6c5676eda6ebb6dc20d7d305b4d8c2be5f1c833fb1084e6d` |
| `LICENSE` | 11357 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |

**PDF sha256:** `a777d2a30e1f8707d84673d401a8a231cd4526b4ee78f5a1163070961929acdf`
**PDF page count:** 16

Rebuild route (project Tectonic route):

```
HOME=scratch/utmlrhome1/home TMPDIR=scratch/utmlrhome1/tmp \
TECTONIC_CACHE_DIR=<workspace-local cache> \
scratch/utex1/bin/tectonic -X compile main.tex
```

## The one rule that governs this file

**The submission must not link to any version that carries the author's name.**
No DOI, no preprint URL and no repository link may be added to this file. Any edit
that would introduce such a link breaks the double-blind guarantee and must be
rejected.
