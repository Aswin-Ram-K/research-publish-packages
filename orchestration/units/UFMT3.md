# UFMT3 — Corrections applied to strategy/FORMATTING_REQUIREMENTS.md

**Status:** done (skeleton written before any work). **Bound:** 12 tool calls.
**Purpose:** apply the seven verifier-measured corrections from `strategy/VERIFICATION_REPORT_FMT1.md` (VUFMT1),
re-measuring each before writing and preserving every old value as a dated superseded note.
**Write paths:** strategy/FORMATTING_REQUIREMENTS.md, scratch/ufmt3/**, orchestration/units/UFMT3.md,
orchestration/handoffs/UFMT3.json. **Nothing under papers/ was touched.**

## Corrections (old -> new, measured 2026-10-16 by UFMT3)
1. §6 rows: **40 -> 44** (R1-R44).
2. Quoted requirements: **34 -> 21**; rule stated (row's Source cell contains `*"..."*`); both the source-cell
   and any-cell readings give 21.
3. Not-stated: **6 -> 2** §6 rows (R12, R15) + the prose's **≥9** distinct items (14 phrase occurrences);
   scopes stated separately; §6 summary's separate "3 not stated" corrected too.
4. URLs: **33 -> 52**, rule stated (distinct scheme-bearing http(s) URLs, dedup on lower-cased host
   (www. stripped) + path (trailing slash/query/fragment ignored)); raw and normalized both = 52.
5. `ABSTRACT.txt`: **3,416 B -> 3,416 chars incl. trailing newline / 3,462 B**; 3,415 chars excl. NL /
   524 words retained as correct; units reconciled at both places (item 12 and §6).
6. Tarball divergence recorded as history with VUFMT1's offsets (**78,405 B / 13:52 vs 80,780 B / 14:18,
   first divergence byte 15,750, line 81**). UFMT3 re-measured: UFIXFMT1's rebuild had landed, tarball member
   and on-disk `main.tex` now **byte-identical 83,774 B, mtime 14:55 CDT, sha256 30e162b4cc6d...** -> DIVERGENCE
   RESOLVED as of measurement (recorded in the note; scratch/ufmt3/measure.json).
7. Research Square: quote moved to `legal/editorial` only; `researchers/preprints` marked as not carrying it
   (re-checked against scratch/vufmt1/fetched/rs_ed.html HIT / rs_pp.html MISS).

Asserted `old_string.count()==1` for all eight edit anchors before replacing one occurrence each.
