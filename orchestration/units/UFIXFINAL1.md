# UFIXFINAL1 — fix three audited defects, change no measured number

**Bound:** 28 tool calls. **Workspace:** `/home/zer0null/reserach extarctor`.

## Purpose (only these three defects)

1. **Declarations.** Paper #1 `papers/encoder-crossover-190/MANUSCRIPT.md` already carries
   *Author contributions / Funding / Competing interests / Use of AI tools / Compute* (headings at
   `:872/:879/:884/:888`, `## References` at `:897`). Paper #7 `papers/gated-read-batching/` and
   paper #2 `papers/replay-record-not-decision/` carry none. Add **only** Funding, Competing
   interests, Use of AI tools — immediately before the reference list, after the body — in paper
   #1's register, adapted per paper. No compute statement, no author-contributions paragraph.
   AI-tools text must name DeepSeek Harness, `deepseek-v4.1-flash` chiefly, with
   `step-5-preview-free` and `mimo-v2.6-flash` as **subagent** routes.
2. **Released manifest.** `papers/encoder-crossover-190/released/encoder-crossover-190-released/`:
   regenerate `MANIFEST.json` with `python3 tools/package/regen_manifest.py` (never hand-edit JSON),
   verify with `python3 tools/package/check_manifest.py`. Report counts.files / counts.bytes_total /
   listed / on-disk-excluding-manifest before and after.
3. **Stale supersede notes.** Sweep all three `papers/<slug>/submission/METADATA.md` and
   `submission/BUILD_NOTES.md` for "SUPERSEDED — current value …" notes whose current value no
   longer matches disk; correct only the stale value, keep all history.

## Constraints

- `/home/zer0null/Duval` strictly read-only; **no git at all** (never bare `git status`).
- `submission/main.tex` is generated: edit `MANUSCRIPT.md`, then
  `python3 tools/package/md2tex.py --package <slug>`. Never hand-edit `main.tex`.
- Recompile changed papers with
  `scratch/utex1/bin/tectonic -r 1 --keep-logs -o <outdir> <paper>/submission/main.tex`, with
  `TECTONIC_CACHE_DIR` / `TMPDIR` / `HOME` inside the workspace, **without** `-Z continue-on-errors`.
  Install over `papers/<slug>/rendered/<slug>.pdf`. Report exit code, `Undefined control sequence`
  count, LaTeX `!` count.
- Numeric invariance per edited paper: pre copies under `scratch/ufixfinal1/pre/`, bibliography
  stripped from both, numeric multiset shared / added / removed; added and removed must both be 0.
- Rebuild each tarball: exactly one member, byte-identical to shipped `main.tex`; report bytes+sha256
  before/after.
- Re-verify per paper: `\author` lines = 1 = `Aswin Ram Kalugasala Moorthy`; `AUTHOR SLOT` = 0;
  `\bibitem`/`\cite`/distinct cited/uncited/unresolved; 0 non-ASCII.
- `PYTHONPATH=src python3 -m pytest tests/test_md2tex.py -q` — report literal line.
- Write nothing outside declared paths.

## Declared write paths

- `papers/encoder-crossover-190/{MANUSCRIPT.md,METADATA.md,BUILD_NOTES.md,submission/**,rendered/**,released/**}`
- `papers/gated-read-batching/{MANUSCRIPT.md,METADATA.md,BUILD_NOTES.md,submission/**,rendered/**}`
- `papers/replay-record-not-decision/{MANUSCRIPT.md,METADATA.md,BUILD_NOTES.md,submission/**,rendered/**}`
- `orchestration/units/UFIXFINAL1.md`, `orchestration/handoffs/UFIXFINAL1.json`, `scratch/ufixfinal1/**`

(METADATA.md / BUILD_NOTES.md live at `papers/<slug>/submission/`.)
