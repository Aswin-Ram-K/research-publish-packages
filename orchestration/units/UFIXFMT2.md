# UFIXFMT2 — skeleton card (written before any work)

**Purpose.** `papers/encoder-crossover-190/MANUSCRIPT.md:749` (table row) and `:423` (body prose)
tell the reader the released package ships `results/DEFECT-EVIDENCE.json`. Resolve the claim in the
direction the facts support, then regenerate LaTeX + tarball and drop the surviving process comment.

**Hard bound.** 14 tool calls maximum. `partial` result with remainder named rather than overrunning.

**Declared write paths.**
- `papers/encoder-crossover-190/MANUSCRIPT.md`
- `scratch/uprep1/md2tex.py`
- `papers/encoder-crossover-190/submission/*`
- `scratch/ufixfmt2/**`
- `orchestration/units/UFIXFMT2.md`, `orchestration/handoffs/UFIXFMT2.json`

**Plan.**
1. Locate `DEFECT-EVIDENCE.json` in workspace + read-only target `/home/zer0null/Duval`; record
   path/size/sha256/mtime. Target strictly read-only: no writes, no bare `git status`.
2. Read the file; test it for target-repo paths, private identifiers, project vocabulary — the class
   the release neutralises. Decide ship-able vs not on quoted evidence, not vibes.
3. Preferred minimal fix: reword `:749` and `:423` to describe what actually ships. Only if step 2
   proves it safe, add it to the package instead. Choose one, never both.
4. `python3 scratch/uprep1/md2tex.py` from workspace root; rebuild the tarball so it holds exactly one
   member `main.tex`; regenerate twice and `cmp` byte-identical.
5. Delete the process comment `main.tex:9` at its SOURCE in `scratch/uprep1/md2tex.py`.
6. Confirm: `\bibitem`=13, `\cite`=23, 0 non-ASCII, tarball `main.tex` byte-identical to on-disk.

**Do NOT touch.** Any numeric claim, κ value or threshold (`strategy/VERIFICATION_REPORT_33.md` owns
their verified state); `strategy/SUBMISSION_READINESS.md` (another unit's deliverable — report
staleness instead); no PDF build (no TeX toolchain).

**Evidence field:** `"skeleton_written_first":"yes"`.


---

## RESULTS (done)

**Chose the minimal reword.** `DEFECT-EVIDENCE.json` exists (Duval target, 3724 B, sha256
`096dec15…ef35`) but is **not** in the neutralised released subset, whose `results/` holds exactly
seven files. Its provenance fields name artefacts the release excludes by policy
(`NOTES-defects.md`, `out-run3-raw/`, `defect-probe.json`, "H-B development split"), so it must not
be added. The defect chain still ships — in `results/REPORT.md` sec D1-D3 — so both MANUSCRIPT
sentences now point there and say the standalone file is not part of the released set.

- `MANUSCRIPT.md:423` -> "...The released `results/REPORT.md` carries the defect write-up (the
  standalone `results/DEFECT-EVIDENCE.json` is **not** part of the released set), and it shows:"
- `MANUSCRIPT.md:749` -> "| defect chain | `results/REPORT.md` (the D1-D3 defect write-up); the
  standalone `results/DEFECT-EVIDENCE.json` is **not** part of the released set |"
- BUILD NOTE block deleted at source `scratch/uprep1/md2tex.py:299-302`; `main.tex` BUILD NOTE = 0.
- Regenerated twice, byte-identical. Tarball = exactly one member `main.tex`, byte-identical to disk.
- `\bibitem`=13, `\cite`=23, non-ASCII=0, `main.tex` 83700 B sha256 `087aedf10ed06762018fd3da1019ff30317e1fbeed6e62fe6559dcd20b5fd3f1`, tarball 28519 B sha256 `171099a5ca09e8dc91b453f8d29d1876263e2610476e0a9cd393011a0ff51934`.

**Out of write path, reported not fixed:** `AVAILABILITY.md:27`, `CLAIMS.md:84-88,122`,
`EVIDENCE_NOTES.md:177,206,212`, shipped `results/REPORT.md:209`, and two stale
`SUBMISSION_READINESS.md` refs (tarball size; `main.tex:12` -> `:10`).
