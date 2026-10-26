# VERIFICATION REPORT 33 — UVER33 vs UPAPER9

Skeleton. Findings appended incrementally as measured.

## UVER33 verdict: PASS (with notes) — 2026-10-16

Re-checked UPAPER9 (`orchestration/units/UPAPER9.md`, `orchestration/handoffs/UPAPER9.json`). Nothing contradicted; one transient artifact trap found and disarmed.

### C1 — fifteen sites handled: CONFIRMED
- `CLAIMS.md:110` now `| 4 |` and `.disagreements_where_routeA_backs_record | = 4 |` (both occurrences).
- `EVIDENCE_NOTES.md:281` still prints `record 5` (frozen) with dated pointer at `:286-289`.
- Missed site `MANUSCRIPT.md:852-855` (pre-edit numbering; now `:856-859`, +4 shift from the new sentence): reads "…have since been completed from the arXiv abstract pages (unit **UBIB1**, 2026-10-15), which supplied title and authors for each". Mirrored at `submission/main.tex:428` with full titles.
- Tally checks: 12 UNEUTRAL10 sites + 3 missed = 15.

### C2 — LIVE/FROZEN split: CONFIRMED
LIVE carry new values: `CLAIMS.md:108/109/110`, `GAPS.md:19`, `MANUSCRIPT.md:381/633/634`, `submission/main.tex:195/335`.
FROZEN keep original bytes + a dated pointer only: `EVIDENCE_NOTES.md:279` (`AB_mutual_agreement: 0.3526315789473684`, `…backs_record: 5`), `:280` (`kappa 0.32520740993294694`), `:281` (`record 5`), note at `:286`; `LIMITATIONS_UPDATE.md:245` (`…0.3526 / 0.3252 / 0.3421…`) note at `:246`; `VERIFIER_CORRECTIONS.md:139` note at `:143`; `DISCLOSURE_CHANGES.md:143` note at `:144`. No frozen record rewritten.

### C3 — no other number moved: CONFIRMED
Sweep of `papers/encoder-crossover-190/` for `0.3252`, `0.32520740993294694`, `0.3526`, `0.3526315789473684`: every remaining hit is inside a frozen record or its dated note (LIMITATIONS_UPDATE 245/247-248, VERIFIER_CORRECTIONS 139/144-145, EVIDENCE_NOTES 279-280/288, DISCLOSURE_CHANGES 143/145-146). New values present at every LIVE site; `routeA_backs_record = 4` at `CLAIMS.md:110`, `MANUSCRIPT.md:634`, `main.tex:335`.

### C4 — limitations sentence: CONFIRMED, not overstated
Verbatim at `MANUSCRIPT.md:635-638` (§6.2). Endpoints check out against the earlier rounds: `0.31988636363636364` is UNEUTRAL8's dotted-only/unpinned round, `0.3248813212427869` is UNEUTRAL9/10's final. Span = 0.004995 ≈ "a few thousandths". The `≈0.33` reference is the paper's own `Δ = −0.3316 ("0.33")` (`MANUSCRIPT.md:313`, best head 0.3474 vs decider 0.6789); 0.3316/0.004995 ≈ 66×, so "an order of magnitude smaller" is conservative. Minor: the pre-neutralisation `0.3252074…` (higher than the stated max) is excluded, which "across our neutralisation rounds" makes defensible.

### C5 — regeneration + UBIB1 regression: CONFIRMED
UPAPER9's own final artifact `scratch/ufixbib2/main.shipped.tex` vs `scratch/upaper9/main.tex.before` = **lines 195 and 335 only** (4 changed lines); 0 non-ASCII bytes; 12 `\bibitem`; route-A agreement `0.3421` intact.
Regression **reproduced**: the pre-fix `md2tex.py` emits at `:435` `…\emph{[Author and/or title not recorded in the corpus --- to be completed before submission.]}` and drops `unpublished internal corpus document (no attributable author)` — in my own scratch regen and in `scratch/ufixbib2/main.generated.tex` (phrase count 0, placeholder 1). UPAPER9's shipped file does **not** have it (`main.shipped.tex` phrase count 1). The author's statement is accurate.

### C6 — red→green: CONFIRMED
`scratch/uver33/checker.py` = 36 checks. Red (copy with `CLAIMS.md:108` reverted 0.3249→0.3252): `CHECKS RUN: 36 FAILURES: 2`, exit 1. Green (real paper): `FAILURES: 0`, exit 0.

### C7 — containment: CONFIRMED
In the UPAPER9 window (14:07:47–14:09:33) the only writes are the 7 paper files, `scratch/upaper9/main.tex.before`, `submission/main.tex`, and its card/handoff. `submission/ABSTRACT_METADATA.txt` last written 14:05:09 (UABSTRACT1, before UPAPER9); `scratch/uneutral10/**` last touched ≤13:57:51 (UNEUTRAL10). UPAPER9 wrote to neither.

### Transient-artifact trap (verifier warning)
UFIXBIB2 (started 14:10:34, concurrent) re-ran the **unpatched** `md2tex.py`, which always writes `papers/encoder-crossover-190/submission/main.tex` directly, so it transiently replaced the live file with the placeholder version (~14:10:44). Sampling the live path at 14:11 briefly shows the regression that UPAPER9 had correctly prevented; UPAPER9's artifact survives as `scratch/ufixbib2/main.shipped.tex`. UFIXBIB2 then added `authornote = {unpublished internal corpus document (no attributable author)}` to `REFERENCES.bib` and taught `md2tex.py` to emit it; current `submission/main.tex` sha256 `5ecb498c40ab286496ee8191981a030b7a9903bac91ef04256babdb4ede06af3`, placeholder count 0, phrase count 1.

### Also reported (not fixed)
- During UPAPER9's tenure `main.tex:428` was restored to the **short**-title wording while `MANUSCRIPT.md:856-859` carried the **full** titles, and `main.tex:431-434` lacked UBIB1's `REFERENCES.bib` provenance; `.tex` and `.md`/`.bib` disagreed until UFIXBIB2's regeneration synced them. UPAPER9's "restore verbatim" fixed the numbers but left that cross-file drift.
- `DISCLOSURE_CHANGES.md` and `VERIFIER_CORRECTIONS.md` are **process records, not shipped**. Freezing them with a dated pointer is defensible and preserves history, but the "FROZEN" label (connoting immutable evidence) overstates their status — they are mutable working notes and an in-place correction would be equally honest.
- UPAPER9's card cites pre-edit `MANUSCRIPT.md:852-855`; after the +4 shift the references paragraph is `:856-859`. Citation-staleness only.
- "its ≈0.33 separation from the decider" attributes the paper's encoder-head Δ (0.3316) to route A; route A agreement 0.3421 vs decider 0.6789 = 0.3368, so it is defensible but slightly loose.
