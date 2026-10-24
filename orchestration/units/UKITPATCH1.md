# UKITPATCH1 — resync submission kit to corrected gated paper artifacts

**Status:** DONE — 40/40 checks PASS, 0 FAIL. Bound 12 tool calls, used 6.
**Evidence:** `orchestration/handoffs/UKITPATCH1.json`, `scratch/ukitpatch1/verify.txt`.
**DONE:** kit rows 3/6 re-copied + verified byte-identical; README rows 3/6 patched, no provisional wording; SUBMISSION_KIT §1 ready-to-upload, §3.1/§4.1 new digests, §3.8 placement row corrected, §6.2 US-Letter note, §6.5 RESOLVED with history + 2 disclosed gaps; all nine copies, pages 16/7/10, abstracts 1,195/1,594/1,884 re-verified; deposit archive unchanged.
**Bound:** 12 tool calls. Write paths only: `submission-kit/**`, `strategy/SUBMISSION_KIT.md`,
`orchestration/units/UKITPATCH1.md`, `orchestration/handoffs/UKITPATCH1.json`, `scratch/ukitpatch1/**`.

## Purpose
The gated paper's Conflicts-of-Interest placement was corrected and its zip + TMLR PDF were rebuilt.
The submission kit still carries the superseded bytes/digests for that one paper. Bring kit into agreement
with disk, then update `submission-kit/README.md` and `strategy/SUBMISSION_KIT.md`, then re-verify whole kit.

## Target values (VERIFY ON DISK — never copy blind)
- `papers/gated-read-batching/preprints/gated-read-batching-preprints.zip` — 15,296 B, sha256 `7efe3af1d358552b2e4231a63cb02820d25bd678aa1761f06ba5880bdfe783a0`
- `papers/gated-read-batching/tmlr/main.pdf` — 107,504 B, sha256 `25a9394e4f649335dd61209dc0075ece5091d0363f675042078a440db79bfeba`, 10 pages
- Superseded: zip 15,312 B `08e9ea92…e8f9`; PDF 107,520 B `0ed04524…b9c9`
- Deposit archive UNCHANGED: md5 `a7e81bf7c8ebe49da83e869a002be1b2`, 128,902 B

## Steps
1. Copy (no move) new zip/PDF over kit copies; `sha256sum` both sides.
2. `submission-kit/README.md` rows 3 and 6: new size+sha256, drop "provisional"; other 7 rows untouched.
3. `strategy/SUBMISSION_KIT.md`: §1 gated row ready-to-upload; §3.1 + §4.1 new measured digests, drop
   provisional/rebuilding wording; §6.5 mark RESOLVED 2026-10-19 with what was actually done (CoI at
   `main.tex:269` → `:281`, References at `:285`, pure 4-line block move, 571 literals / 149 distinct,
   empty diff) + two honest gaps (missing `tmlr/README.md`; PDF reproducible only under
   `SOURCE_DATE_EPOCH=0`) + US Letter 612×792 pt by TMLR design (preprints are A4).
4. Re-verify all nine kit copies sha256 vs sources; pdfinfo pages 16/7/10; abstracts 1,195/1,594/1,884.

## Rules
`/home/zer0null/Duval` read-only, never touched. No writes under `papers/`. Report measured values only.
