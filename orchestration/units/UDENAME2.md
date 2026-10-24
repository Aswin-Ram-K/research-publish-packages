# UDENAME2 — de-naming rule vs. released-stimulus text (Paper #2)

**Status:** done (author-side). Bound 15 tool calls; used 14. 2026-10-19.

## Fix chosen and why
Shape (a): the rule's **replacement** was false, so the replacement changed —
`tools/package/md2tex.py:228` was `("the fixture \`evals/fixtures/reflex-decisions.ts\`", "the withheld stimulus fixture")`,
now `(..., "the stimulus fixture")`; the source literal is **kept**. Shape (b) (delete rule + the source
literal) was rejected because the rule is also the mechanism that keeps the internal source-tree path
`evals/fixtures/...` out of shipped LaTeX — a path the converter's own `forbidden` guard blocks
(`(?<![\w/])(?:evals|tools|strategy|docs)/`, `scratch/`) — so deleting both would drop real coverage
silently, and would force a prose rewrite beyond the minimal fix. Dropping the single word "withheld"
leaves the sentence true and its two clauses in agreement; the guard's purpose is intact (it still
hard-fails if the manuscript stops carrying this literal — proven red below). A dated comment recording
the superseded replacement was added at the rule, following the file's own convention (cf. `:196-200`,
`:239-242`). **No manuscript edit was needed or made; MANUSCRIPT.md is unchanged (its own dated history
at `:269` and `:326-331` already records the 2026-10-19 release).**

## Evidence (all commands run from the workspace root)
| check | result |
| --- | --- |
| regen x2, `python3 tools/package/md2tex.py --package replay-record-not-decision` | exit `0` then `0` |
| `cmp run1.tex run2.tex` | exit `0`; sha256 `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934` for run1, run2 **and** `papers/replay-record-not-decision/submission/main.tex` |
| generated sentence (both clauses) | `lived only in the stimulus fixture (145,031 bytes; 190 cases), which is not part of either \texttt{.jsonl}; since 2026-10-19 that fixture is \textbf{not withheld}` |
| byte diff before→after | exactly one line changed: `submission/main.tex:187` |
| stale-rule guard red (converter copy, source phrase removed from a **staged** manuscript) | `RED_EXIT=1`, stderr `dename_rules: rule matched nothing (stale rule): 'the fixture \`evals/fixtures/reflex-decisions.ts\`'` |
| guard green / restored | `GREEN_EXIT=0`, `GREEN2_EXIT=0`; copy deleted (`copy_removed=YES`); real MANUSCRIPT.md untouched (phrase count 1) |
| numeric-literal multiset, before vs after | distinct `123`/`123`, total `311`/`311`, ADDED `{}`, REMOVED `{}` — identical |
| bibitem / cite / distinct / uncited / unresolved | `8 / 8 / 8 / 0 / 0` both before and after |
| tectonic `-r 1` (HOME/TMPDIR/TECTONIC_CACHE_DIR inside the workspace) | exit `0`; `Undefined control sequence` = `0`; `^!` lines = `0`; pages = `10` (pdfinfo `Pages: 10`; inflated-stream scan `10`); `main.pdf` 101056 bytes |
| deposit archive digest | **UNCHANGED**: pinned inputs all match `scratch/upkginstall2/inputs.sha256` (`INPUTS_ALL_MATCH=YES`); `main.tex` is not an archive input (`0`); deterministic rebuild replicated inside `scratch/udenames2/deposit-build/` is byte-identical to the shipped tarball (`cmp` exit 0) — 107474 bytes, sha256 `7703fe83df2f716b2615416d261d66359b954e1aada793f1045864bb3b1e398f`, md5 `16e2b2bf71450da3caaa060870e67183` |

## Same-class audit — every `dename_rules` entry (16 tuples), replacement false today?
| # | source literal → replacement | matching once? | false now? |
| --- | --- | --- | --- |
| 1-4 | `EXP#7-replay-divergence.md:16-17/48-55/139-154/148-150` → pre-registration record §1/§3/analysis log | yes | no — naming only, not falsified by any current paper text (the record is internal; § numbering unverifiable here) |
| 5 | `scratch/urever2/verify_divergence.py` → "the analysis script released with this note" | yes | no — MANUSCRIPT.md:300-303 "**Released.** ... the analysis script that re-derives every number in §4" confirms it |
| 6-7 | `strategy/PAPER2_REVERIFICATION.md:149/152` → "the re-verification record" | yes | no — naming only (the note's correction at `:245` agrees) |
| 8 | fixture path → **"the withheld stimulus fixture"** | yes | **YES — FIXED** |
| 9 | " (`evals/fixtures/reflex-decisions.ts`)" → "" | yes | no — removes a parenthetical path, no truth claim |
| 10-12 | `tools/replay/exp7.ts` variants → "the pre-registration's analysis script" / "that script" | yes | no — agrees with `:280-282`, `:322-324` (that script is *not* released) |
| 13 | "on the L1 side" → "on the second record's side" | yes | no |
| 14-16 | `CLAIMS.md`/`GAPS.md`/`AVAILABILITY.md` → "this note's internal {claim trace,gap log,availability record}" | yes (CLAIMS x2) | no — internal-record naming |

Stale comment also found (not fixed, out of the minimal change): `tools/package/md2tex.py:216` says
"Targeted prose de-naming (14 rules)" while the tuple carries 16.

## Disagreement with the card (reported, not smoothed)
The card said to rebuild the deposit archive with `sh scratch/upkginstall2/build_archive.sh` **if the
change alters the payload**. It does not: the archive's 10 inputs are the 8 package files plus
`CITATION.cff`/`README_DEPOSIT.md`, and `main.tex` is not among them. Running that script would also
write outside this unit's declared write paths (`scratch/upkginstall2/work`, `scratch/upkginstall2/build`,
`papers/replay-record-not-decision/released/replay-record-not-decision-released/`) — the card's own
write-path list forbids that. I therefore answered the digest question by measurement instead:
`sha256sum -c` on the pinned inputs (all match) plus an exact in-path replication of the script's
deterministic recipe (steps 1-4, GENUTC `2026-10-19T06:10:44Z`), which is byte-identical to the shipped
archive. Digest did **not** move; no re-upload is required.
