# UFIXFMT3 — DONE (2026-10-16)

Swept and redirected every paper-side reference to the unshipped `results/DEFECT-EVIDENCE.json`; refreshed
`strategy/SUBMISSION_READINESS.md` with dated corrections; reported (did not fix) the release tree's own stale
reference and the tree-authority question. Bound 20 tool calls, used 12.

**Ground truth (NOT shipped, not added):** /home/zer0null/Duval/docs/research/EXP#12-evidence/DEFECT-EVIDENCE.json
— 3724 B, sha256 096dec1500693b6e854e3feb7c5fab858b97e7d92cabdb1e23c9455ed940ef35 (re-verified).

**Full hit set (10, all fixed):** AVAILABILITY.md:27; CLAIMS.md:84–88, :122; EVIDENCE_NOTES.md:177, :206, :212.
MANUSCRIPT.md:424,:751 and main.tex:230,:382 already carried the prior unit's corrected wording.

**Tarball after rebuild:** 28403 B, sha256 9f757c0391ec9aaa29e1800d37430885fe4adb22f0d6c5d8f461904f105134e1,
one member `main.tex`, `cmp`-identical. `\bibitem` 13, `\cite` 23 (both unchanged across `md2tex.py`).

**Report-only (Part 3):** `repro/encoder-crossover-190/results/REPORT.md:209` still says the flips are
*"retained in `results/DEFECT-EVIDENCE.json`"*; `repro/encoder-crossover-190/` still ships that file and its
MANIFEST lists it — while the build pin `scratch/urecut1/package` (UBUILD1.build.sh:134) does not.
Detail: `scratch/ufixfmt3/PART3_FINDINGS.md`.

Evidence field: skeleton_written_first=yes.
