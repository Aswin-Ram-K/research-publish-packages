# UPKG2C — repoint paper #2 at paper #3's fixture; drop fixture from package

**Purpose:** paper #2 (`papers/replay-record-not-decision/`) §7 says the stimulus fixture is *Withheld*
("the largest gap"). Its release package (`scratch/upkg2b/package/`) currently ships paper #3's
neutralised fixture, which contradicts the paper. Author's instruction: do NOT ship the fixture;
reference paper #3's released fixture by concept DOI `10.5281/zenodo.23463944` instead.

**Write paths (only):** `papers/replay-record-not-decision/**`, `scratch/upkg2c/**`,
`orchestration/units/UPKG2C.md`, `orchestration/handoffs/UPKG2C.json`.
Target repos (incl. `/home/zer0null/Duval`) remain strictly read-only.

**Bound:** 30 tool calls. 3 attempts max per unverifiable item, then STOP and report `unverified`.

**Jobs**
1. Independently re-derive the fixture↔records join (per-kind counts, constancy of `correct` per
   case, uniqueness of the kind bijection) with an own script under `scratch/upkg2c/`.
2. Edit `MANUSCRIPT.md` availability section: stimulus released with the companion note, DOI cited,
   correspondence stated honestly, no independence claim, no measured number changed, superseded
   wording preserved as dated history.
3. `scratch/upkg2c/package/`: remove `fixture/`, regenerate MANIFEST with the project tool, prove
   manifest PASS + recompute PASS + red→green on `data/l1-head-to-head.jsonl` (digest
   `6af0e0d8…b2a1e7`) + cut ladder (either record file breaks; fixture removal does not).
4. `md2tex.py` payload regen ×2 (byte-identity), numeric-literal delta, bibitem/cite counts, DOI as
   new literal; compile with `scratch/utex1/bin/tectonic` (never `-Z continue-on-errors`).
5. `TMLR_ANONYMITY_NOTE.md` — what double-blind requires of this citation.

**Status:** in progress.

---

## Result (2026-10-19)

**JOB 1 — DONE (reproduced, with one unit correction).** `scratch/upkg2c/reproduce-join.py` →
`scratch/upkg2c/join-results.json`. Fixture sha256 `a15224bada6950ad27f693acd2287dec564134419061baa475f6716d2db3852e`,
records `c5ec44a799ddeb963f862fc5c054ddad6ef2fce6ad90edfafd7c1755ac4370e7`. **Disagreement with the
card:** its per-kind counts (30/30/26/22/26/28/28) are **per distinct case**; the record file has
**16 rows per case** (3,040 rows / 190 cases), so per-row counts are 16× larger. Collapsed to distinct
cases, counts match as multisets on both sides; `correct` is constant per case on both sides (0
non-constant); **exactly 1** kind bijection matches all seven ordered `correct` sequences, identical to
the card's (`K01→escalation, K02→worker.class, K03→acquisition, K04→topology, K05→capability.family,
K07→memory.admission, N10→context.package`).

**JOB 2 — DONE.** `MANUSCRIPT.md`: abstract, §1 related work, §2, §6 first limitation and §7 rewritten;
superseded wording kept as dated history in §6 and §7. No measured number changed; no independence
claim added (the text says explicitly the companion is **not** an independent corpus). `exp7.ts` is
still withheld/unexecuted and §7 now says exactly that.

**JOB 3 — DONE.** `scratch/upkg2c/package/` (8 files): `fixture/` removed; checker's fixture section
made conditional; README repointed. `check_manifest.py` → all five counters 0, `VERDICT PASS`, exit 0.
Clean extraction: `CHECKS: 30/30 passed`, `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`,
exit 0. Red→green on `data/l1-head-to-head.jsonl` offset 98 (`0x31→0x30`, sha `6af0e0d8…` →
`9e3280b9…`): exit 1 with 4 named failures; restored → exit 0. Cut ladder
(`scratch/upkg2c/cut_ladder.py`): dropping either record file exits 1 (c07, c08); every fixture cut
exits 0 (c01 no-fixture, c01b add-then-drop, c01c with-companion-fixture); first break c03 (one row).

**JOB 4 — DONE.** `md2tex.py --package replay-record-not-decision` exit 0 twice, byte-identical
(`b18f9506d754fa9fa82b202f6862b9a4dba52985f4169f1cf5c9555bbfbb96f7`, 32,359 B; was 28,852 B). Note:
the converter's `dename_rules` guard failed until the manuscript re-used three of its required literal
phrases (`tools/package/md2tex.py` is outside my write paths — the *manuscript* was conformed, not the
tool). Numeric literals 389→442 (+53), distinct 124→138; ADDED as in `scratch/upkg2c/md2tex-delta.json`,
REMOVED none; the DOI is a **new** literal (`10`, `10.5281`, `23463944`). Bibliography: 8 `\bibitem` /
8 distinct / 8 `\cite` / 8 cited / 0 uncited / 0 unresolved. Tectonic `-r 1`: exit 0, 0 `Undefined
control sequence`, 0 `!` lines, 10 pages, PDF 101,052 B.

**JOB 5 — DONE.** `papers/replay-record-not-decision/TMLR_ANONYMITY_NOTE.md`.

**Extension beyond the card (same declared write path):** `AVAILABILITY.md` and `GAPS.md` also said the
stimulus was withheld; a dated 2026-10-19 update block was inserted at the top of each, preserving the
older text as history. Report this as an in-scope consistency fix, not a silent rewrite.
