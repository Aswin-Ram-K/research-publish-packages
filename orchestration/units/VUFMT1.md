# VUFMT1 — independent verification of strategy/FORMATTING_REQUIREMENTS.md

- **Unit:** VUFMT1 (verifier; did not author the document under test)
- **Purpose:** Re-run the audit's method, not re-read its summary. Re-fetch cited URLs and check quotes against live pages; re-measure counts; audit the "not stated" items; red→green the matcher.
- **Bound:** 25 tool calls maximum. **Used:** 13. **Status:** DONE.
- **Write paths:** `strategy/VERIFICATION_REPORT_FMT1.md`, `orchestration/units/VUFMT1.md`, `orchestration/handoffs/VUFMT1.json`, `scratch/vufmt1/**`
- **FORBIDDEN:** editing `strategy/FORMATTING_REQUIREMENTS.md` — complied; no write to the author's document.

## VERDICT: partial

Core load-bearing findings reproduce. Defects are arithmetic/bookkeeping + one unflagged stale artifact.

## Reproduced
- arXiv abstract cap: live `prep.html` HIT `Keep it short - abstracts longer than 1920 characters will not be accepted; abridge your abstract if necessary`; `1920`×1, `1,920`×0.
- arXiv licence: six menu tokens each ×1; word `default` ×0; both irrevocability quotes HIT; `limited rights to arXiv … limits re-use of any type` HIT; `license/options.html` http=404.
- Negative size quota: no `\d+ (MB|GB)` tokens, no `quota`/`size limit` on `sizes.html`, `tar.html`, `submit_tex.html`, `submit/index.html`, `faq/mistakes.html`; `34 Megapixel`/`600dpi` sentence present.
- TMLR: stylefile / `anonymized` / `double-blind` / CC BY 4.0 from submission / `not linking to another version that includes the authors' names` all HIT; FAQ has ISSN `2835-8856`, DOI ×0.
- Research Square format quote HIT on `legal/editorial`, MISS on `researchers/preprints`.
- `main.tex` sha256 `0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160`: **13 `\bibitem`, 0 `\cite*`**.
- `ABSTRACT_METADATA.txt`: 1,195 chars = 1,195 bytes, 186 words, 0 non-ASCII, no "Abstract".
- Tarball sha256 `0b745948ad00a62ec06818692173ffa7fa1d71a9a6ced17bca28b723169f4901` matches stated prefix.

## Not reproduced / contradicted
1. "§6 holds 40 rows" → **44** rows (R1–R44).
2. "34 carry a verbatim quote" → **21** carry the `*"…"*` marker in §6.
3. "6 recorded as not stated" → §6 has **2** (`R12`, `R15`); ≥9 across prose.
4. "33 distinct primary URLs" → **52** distinct http(s) URLs, no counting rule.
5. `ABSTRACT.txt` called "3,416 **bytes**" → it is **3,416 characters / 3,462 bytes** (28 non-ASCII); "3,415 text chars / 524 words" is right.
6. Unflagged: tarball member `main.tex` = **78,405 B @13:52**, on-disk `main.tex` = **80,780 B @14:18** — audit prints both, never notices, and §7 recommends the stale tarball.

## Red→green (literal)
`GREEN HIT @12302 …1920 characters…` / `RED MISS …1921 characters…` / `RED MISS …lazy dog` / `RED MISS` on wrong page. Raw `grep -cF` on markup returns 0 → normalisation required.

## Overstated
RS format quote shown under both RS sources but verifies only on `legal/editorial`; abstract-cap quote uses `—` where page uses `-`.

## Unverified (named)
Remaining 18 inventory URLs (§4 policy pages, Zenodo, OSF, Preprints.org, NeurlPS/Elsevier/Nature/ICLR, `ltbibl.dtx`); contents of the three `scratch/ufmt1/*_notes.md` provenance files (existence only confirmed).

## Blocker
None.

## Artifacts
- `strategy/VERIFICATION_REPORT_FMT1.md`
- `scratch/vufmt1/match.py`, `scratch/vufmt1/match2.py`, `scratch/vufmt1/fetched/*.html` (15 pages)
- `orchestration/handoffs/VUFMT1.json`
