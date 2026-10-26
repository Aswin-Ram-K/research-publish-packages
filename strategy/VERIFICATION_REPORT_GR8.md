# VERIFICATION REPORT GR8 — independent re-check of UFIXGR8 (paper #7 pointer/prose fix)

**Verifier:** UVERGR8 (did not author any file under review).
**Subject:** `papers/gated-read-batching/MANUSCRIPT.md`, `papers/gated-read-batching/submission/main.tex`,
`papers/gated-read-batching/submission/gated-read-batching.tar.gz`; author card `orchestration/units/UFIXGR8.md`,
handoff `orchestration/handoffs/UFIXGR8.json`.
**Overall verdict: PASS.** Every reported claim was independently reproduced. No claim was contradicted, overstated,
or left unreproduced. Two limits are recorded (`unverified`, §8). `/home/zer0null/Duval` was not touched; no git
command ran against it. All commands that could write ran only on copies under `scratch/uvergr8/`, except the
converter runs, which write the live `main.tex` and were followed by a proven byte-identical restore (§4).

---

## 1. Pointer sweep — REPRODUCED

Whole-file regex over both shipped bodies for `CLAIMS.md`, `GAPS.md`, `REFS.md`, `EVIDENCE_NOTES.md`,
`OPEN_QUESTIONS.md`, `REFERENCE_NOTES.md`, `UNSOURCED_RETAINED.md`, and bare `scratch/`:

- `papers/gated-read-batching/MANUSCRIPT.md` → **0 occurrences**
- `papers/gated-read-batching/submission/main.tex` → **0 occurrences** (also 0 for `/home/`)

The pre-edit copy `scratch/ufixgr8/MANUSCRIPT.before.md` shows exactly **5** occurrences, at `:3`, `:84`, `:127`,
`:223`, `:225` — matching UFIXGR8's count of 5 (and superseding the third party's count of 3). Disposition present on
each reworded line, verbatim:

| line (before → after) | before | after |
|---|---|---|
| 3 | `**Status:** draft manuscript …` | `**Scope:** prepared from a closed …` |
| 84 | `… stated in full at GAPS.md G-25.]**` | `… stated in full in this record's internal gap log (entry G-25; an internal working record not included in the released material).]**` |
| 127 | `… traced to a source file and line in \`CLAIMS.md\` (exact-line accuracy 71/73; …` | `… traced to a source file and line (exact-line accuracy 71/73; …` |
| 223 | `… maintained in [\`REFS.md\`](REFS.md).` | `… maintained in this record's internal reference notes (an internal working record not included in the released material).` |
| 225 | `(Venue not verified — see REFS.md.)` | `(Venue not verified.)` |

Each after-line at `papers/gated-read-batching/MANUSCRIPT.md:3/:84/:127/:223/:225` reads as a coherent sentence with
no dangling filename. No reader-visible sentence **requires** a file the paper does not ship.
Sibling check: `EVIDENCE_NOTES.md`, `OPEN_QUESTIONS.md`, `REFERENCE_NOTES.md`, `UNSOURCED_RETAINED.md` do not exist
under `papers/gated-read-batching/` at all, so they could not have been resolvable; `CLAIMS.md`, `GAPS.md`,
`REFS.md` and `DISCLOSURE_CHANGES.md` do exist in that directory but are not referenced from either shipped body.
(The tarball ships exactly one member, `main.tex` — §4 — so a reader of the deliverable cannot resolve them.)

## 2. The banner — REPRODUCED

`papers/gated-read-batching/MANUSCRIPT.md:3` is now:
`**Scope:** prepared from a closed 2026-09-30 measurement run. Single model, single corpus, single task family. Short note / workshop scope.`
`grep -inE 'draft|to be supplied|status:' papers/gated-read-batching/MANUSCRIPT.md` → **no match**.
Title (`:1`) and abstract (`:7`) are intact and unchanged in wording; the converter emits 1 `\begin{abstract}`.
**Nuance (not a defect):** the literal phrase `TO BE SUPPLIED` does survive in the shipped LaTeX, but only inside the
author slot at `papers/gated-read-batching/submission/main.tex:10`
(`\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`) — that is the required single author placeholder, not a
draft-status banner. It is not in `MANUSCRIPT.md`.

## 3. The UFIXGR7 markers — REPRODUCED

Both dated provenance markers survive, grep count 2 in `MANUSCRIPT.md`:
- `papers/gated-read-batching/MANUSCRIPT.md:82` → `**[correction 2026-10-15, UFIXGR7, from the raw-record re-verification.]**` — date, unit id and correction content (raw-record re-verification of the withdrawn 1.83 MB figure, 2,426,190 / 2,886,664 bytes) intact.
- `papers/gated-read-batching/MANUSCRIPT.md:84` → `**[correction 2026-10-15, UFIXGR7: … yields 127 pairs in the pinned snapshot tree / 130 in the live tree, against 120 stored; … 6.7 % base rate … validity limitation, stated in full in this record's internal gap log (entry G-25; an internal working record not included in the released material).]**` — date, unit id and the full correction substance (127 / 130 / 120 stored / 6.7 %) preserved.

As expected, `UFIXGR7` appears **0** times in `main.tex` (converter rule S2 strips internal unit ids; converter log
line 4: `sanitisation: ["removed internal unit ids: ['UFIXGR7']"]`).

## 4. Regeneration — REPRODUCED

Converter run per UFIXGR8's own command `python3 scratch/uprep7/md2tex.py` from the workspace root.
- Run 1 output sha256 `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4`, and `cmp` against the
  on-disk live `main.tex` **clean** → the shipped file is exactly what the converter produces.
- Run 2 `cmp` against run 1 **clean** → two runs byte-identical.
- Also `cmp scratch/ufixgr8/run1.tex` (author's copy) vs my regen → identical.
- **Restore proof:** live `main.tex` was copied aside before the runs and restored with `cp -p`; post-restore sha256 is
  again `a5d32dd7…`, and `sha256sum -c` over the whole `submission/` directory is **OK for all 6 files** (ABSTRACT.txt,
  ABSTRACT_METADATA.txt, BUILD_NOTES.md, tarball, main.tex, METADATA.md) → nothing outside `main.tex` drifted.
- Converter log: `dropped drafting banner(s): 0` (source banner is now neutral, so S1 has nothing to drop).

LaTeX proofs on `main.tex`: **13** `\bibitem` (13 distinct); **14** `\cite` calls over **13** distinct keys
(15 key instances); **0 uncited** `\bibitem`; **0 unresolved** `\cite` keys; exactly **1** author slot;
**0** non-ASCII bytes; `\begin`/`\end` **19/19**.
Tarball: `tar -tzf` lists exactly **1** member (`main.tex`); `cmp <(tar -xzOf … main.tex) main.tex` **clean**.
Digests confirmed: `main.tex` **37,291 B** `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4`;
tarball **13,270 B** `0899f5b6252f68ac076e67eea1e9b325a5fcd8b9959c0515b861882106969c18`. Both previous digests are
recorded beside them in `papers/gated-read-batching/submission/BUILD_NOTES.md:117`–`:118`.

## 5. Number invariance — REPRODUCED (strong form)

A genuine pre-edit copy **does** exist: `scratch/ufixgr8/MANUSCRIPT.before.md` (33,032 B). Every numeric literal in
before and after was extracted as a multiset and compared:
**497 tokens before, 497 after, zero additions, zero removals** — no number was added, dropped, or altered anywhere
in the manuscript. Specifically the numbers inside the five reworded sentences are all preserved: `2026-09-30`
(line 3), `127` / `130` / `120` / `6.7` (line 84), `71/73` / `C48` / `C65` (line 127); lines 223 and 225 carry none.
Cross-check of the reworded traceability sentence against the internal record it cites:
`papers/gated-read-batching/CLAIMS.md:131` states `exact-line accuracy 71/73 (C48 and C65's second locator originally
missed the line and are corrected in this revision)`, and `:87`/`:109` define `C48` and `C65` — the reworded
manuscript sentence agrees with all of it.

## 6. The two judgement calls — both sound

**(a) Scope line shipping at `main.tex:14` is the correct consequence of rule S1 — REPRODUCED.**
`scratch/uprep7/md2tex.py:7` documents S1 as dropping the leading `**Status:** draft manuscript …` banner, and the
implementation at `scratch/uprep7/md2tex.py:293` is
`if kind == "para" and re.match(r"^(\\textbf\{Status:\}|Status:)", blk):` → a line beginning `**Scope:**` does **not**
match, so S1 cannot fire and the paragraph is emitted. The converter log confirms `dropped drafting banner(s): 0`.
So the neutral `**Scope:**` line shipping at `main.tex:14` is rule-consistent, not an accident.

**(b) The GAPS.md clause inside the dated marker needed minimal rewording — CORRECT.**
Keeping `GAPS.md G-25.` verbatim would have left a bare filename pointing at an unshipped file (violating the
no-bare-pointer requirement); deleting the marker would have destroyed provenance (violating "markers must stay").
The chosen edit preserves date, unit id and the entire correction substance and explicitly labels the record as
internal and not released, which is the only reading satisfying both constraints. **Residual, disclosed not hidden:**
`entry G-25` still names an unreleased record, but the sentence states that up front, so no reader is misled.

## 7. Red→green, non-vacuous — REPRODUCED

Guard: regex over the seven pointer names / bare `scratch/`.
- GREEN: guard on the real `papers/gated-read-batching/MANUSCRIPT.md` → **0**; on `main.tex` → **0**.
- RED: on the copy `scratch/uvergr8/injected.md`, `GAPS.md` was re-injected at line 84 → guard **1 (FAIL)**, and the
  failing line was printed.
- SPECIFICITY: on `scratch/uvergr8/control.md`, an unrelated `NOTES.md` was injected at the same site → guard **0**.
  So the guard keys on the pointer names themselves, not on any `.md` string or on the edit location — it genuinely
  sees a bare filename and is not merely detecting something else.

## 8. Not reproduced / unverified

- `not_reproduced`: none.
- `overstated`: none.
- `unverified`: (i) no TeX toolchain exists on this host, so compileability / PDF rendering of `main.tex` was not
  tested (UFIXGR8 said the same; no PDF was fabricated); (ii) I did not run an independent mtime/lock-free sweep to
  prove UFIXGR8 touched only its seven declared write paths — I verified only that the files it named are correct and
  that my own regeneration left the other five submission files byte-identical.

## 9. Containment

`/home/zer0null/Duval` untouched; no git command of any kind run against it. All writes confined to
`strategy/VERIFICATION_REPORT_GR8.md`, `orchestration/units/UVERGR8.md`, `orchestration/handoffs/UVERGR8.json`,
`scratch/uvergr8/**`. The live `main.tex` was rewritten only by the converter during §4 and restored byte-identically
(sha256 re-proven); the files under review are otherwise unchanged.
