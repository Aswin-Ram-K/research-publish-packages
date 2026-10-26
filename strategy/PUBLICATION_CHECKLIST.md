# Publication checklist — three papers, grouped by experiment

**Sequence and status only.** This document owns *what to do, in what order, and where each step stands*. It deliberately does **not** restate artifact sizes or digests: they change on every rebuild, and restating them is what left 22 stale values after the last sweep. The numbers live in the two files that own them (§2.1), §2.2 names what exists, and §2.3 records the values this consolidation removed so nothing is silently dropped.

**Shipped** = a reader can obtain it (archive, zip, PDF, TMLR variant). **Author-side** = working record that never reaches a reader.

## §1 · One row per experiment

| Experiment | Paper slug | Title | Deposit DOI | State |
|---|---|---|---|---|
| **EXP#12** (cites EXP#11) | `papers/encoder-crossover-190/` | The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33 and to a majority-class control | **`10.5281/zenodo.23463944`** (concept DOI) | **deposited** 2026-10-18; no preprint posted; TMLR variant built, not submitted |
| **EXP#7** | `papers/replay-record-not-decision/` | Replay reproduces the record, not the decision | **`10.5281/zenodo.23482511`** (concept DOI) | **deposited** 2026-10-19, latest v2 = record `23483304`; no preprint posted; TMLR variant built, not submitted — (Superseded 2026-10-19: this row previously read "none yet" and "**bundled** — deposit archive + Preprints zip exist, no DOI") |
| **no EXP number** | `papers/gated-read-batching/` | Cheap batches, weak gate: batching binary read-gate decisions 16–90-way at `effort=none` does not measurably degrade them, and a purpose-conditioned read gate on header and structure alone is not yet a classifier | **`10.5281/zenodo.23483314`** (concept DOI) | **deposited** 2026-10-19, latest v2 = record `23485733`; no preprint posted; TMLR variant built, not submitted — (Superseded 2026-10-19: this row previously read "none yet" and "**bundled** — deposit archive + Preprints zip exist, no DOI") |

**On the gated paper's provenance (established, not guessed).** A grep for `EXP#` across `papers/gated-read-batching/` returns **zero hits**. Its provenance is a dated measurement run, not an experiment number: `results/GATED_READ_2026.md:3-9` records *"Date (UTC): 2026-09-30 … Agent: deepseek-v4.1-flash (mimo-v2.6-flash runtime), branch measure/gated-read … Fixture: tools/gated-read/tasks.json (20 tasks × 90 corpus files …) … Harness: tools/gated-read/bench.py"*, and `MANUSCRIPT.md:3` says *"prepared from a closed 2026-09-30 measurement run"*. The repo's pre-registered series is EXP#1–#7, #3b, #10–#12 (`dockets/duval/duval-u55-pinned/material/docs/README.md:52-60`); the gated-read lane is not one of them. Its **"7" is paper candidate rank #7** (`strategy/PAPER_CANDIDATES.md:81`), which is a different thing from **EXP#7** — see §5.

## §2 · Artifact inventory — paths only

### §2.1 · Where the numbers live

Two owners, neither of them this file:

- **Upload files** — `submission-kit/README.md`. One row per file (three Preprints zips, three TMLR `main.pdf`, three abstracts), each with bytes and sha256, re-verified after copying. Upload from `submission-kit/`, never from the paper trees.
- **Released trees** — `MANIFEST.json` inside each `<slug>-released.tar.gz`: per-member paths with bytes and digests for the payload. The archive's own digest is whatever `sha256sum papers/<slug>/released/<slug>-released.tar.gz` returns at the moment you quote it.
- **Anything else on disk** — measure it yourself. A digest quoted from a checklist is a digest of a build that no longer exists.

Rule for this document: an *identifier* (DOI, Zenodo record id, line reference, `generated_utc`) may be written down; a *measurement* (bytes, sha256, md5, page count) may not, because the next rebuild invalidates it. The one exception is §4.2, which has to quote a measurement to make its point and says when it was taken.

### §2.2 · What exists

Nothing below carries a size or a digest. Paths are relative to `papers/<slug>/` unless the row says otherwise.

| Paper | Class | Path |
|---|---|---|
| encoder-crossover-190 | shipped | `preprints/encoder-crossover-190-preprints.zip` |
| encoder-crossover-190 | shipped | `released/encoder-crossover-190-released.tar.gz` |
| encoder-crossover-190 | shipped | `rendered/encoder-crossover-190.pdf` |
| encoder-crossover-190 | shipped | `submission/encoder-crossover-190.tar.gz` |
| encoder-crossover-190 | shipped | `submission/main.tex` |
| encoder-crossover-190 | shipped | `tmlr/LICENSE` |
| encoder-crossover-190 | shipped | `tmlr/fancyhdr.sty` |
| encoder-crossover-190 | shipped | `tmlr/main.pdf` |
| encoder-crossover-190 | shipped | `tmlr/main.tex` |
| encoder-crossover-190 | shipped | `tmlr/tmlr.bst` |
| encoder-crossover-190 | shipped | `tmlr/tmlr.sty` |
| encoder-crossover-190 | payload | `released/encoder-crossover-190-released.tar.gz` — 31 payload members, one top-level directory; member paths and digests are in the archive's `MANIFEST.json`. The unpacked tree is **not** on disk: it was moved, with its history, per `released/SUPERSEDED-UNPACKED-TREE.md` |
| encoder-crossover-190 | author-side | `AVAILABILITY.md` |
| encoder-crossover-190 | author-side | `CHECKLIST.md` |
| encoder-crossover-190 | author-side | `CLAIMS.md` |
| encoder-crossover-190 | author-side | `DISCLOSURE_CHANGES.md` |
| encoder-crossover-190 | author-side | `EVIDENCE_NOTES.md` |
| encoder-crossover-190 | author-side | `GAPS.md` |
| encoder-crossover-190 | author-side | `LICENSE_ANALYSIS.md` |
| encoder-crossover-190 | author-side | `LIMITATIONS_UPDATE.md` |
| encoder-crossover-190 | author-side | `MANUSCRIPT.md` |
| encoder-crossover-190 | author-side | `MANUSCRIPT_CHANGES.md` |
| encoder-crossover-190 | author-side | `OPEN_QUESTIONS.md` |
| encoder-crossover-190 | author-side | `REFERENCES.bib` |
| encoder-crossover-190 | author-side | `REFERENCES_ADDITIONS.bib` |
| encoder-crossover-190 | author-side | `REFS.md` |
| encoder-crossover-190 | author-side | `REFS_VERIFIED.md` |
| encoder-crossover-190 | author-side | `RELATED_WORK_NOTES.md` |
| encoder-crossover-190 | author-side | `UNSOURCED_RETAINED.md` |
| encoder-crossover-190 | author-side | `VERIFIER_CORRECTIONS.md` |
| encoder-crossover-190 | author-side | `released/README_DEPOSIT.md` |
| encoder-crossover-190 | author-side | `released/SUPERSEDED-UNPACKED-TREE.md` |
| encoder-crossover-190 | author-side | `rendered/_superseded/README.md` |
| encoder-crossover-190 | author-side | `rendered/_superseded/encoder-crossover-190-CHROME-headless-a4.pdf` |
| encoder-crossover-190 | author-side | `rendered/_superseded/encoder-crossover-190-html-pre-DOI-refresh-2026-10-16.html` |
| encoder-crossover-190 | author-side | `rendered/_superseded/encoder-crossover-190-latex.pdf` |
| encoder-crossover-190 | author-side | `rendered/_superseded/encoder-crossover-190-tectonic-prior-main-58c22c90.pdf` |
| encoder-crossover-190 | author-side | `rendered/_superseded/encoder-crossover-190-tectonic-prior-main-752747f8.pdf` |
| encoder-crossover-190 | author-side | `rendered/_superseded/encoder-crossover-190-tectonic-prior-main-80b3f3e4.pdf` |
| encoder-crossover-190 | author-side | `rendered/convert.py` |
| encoder-crossover-190 | author-side | `rendered/encoder-crossover-190-libreoffice.pdf` |
| encoder-crossover-190 | author-side | `rendered/encoder-crossover-190.docx` |
| encoder-crossover-190 | author-side | `rendered/encoder-crossover-190.html` |
| encoder-crossover-190 | author-side | `submission/ABSTRACT.txt` |
| encoder-crossover-190 | author-side | `submission/ABSTRACT_METADATA.txt` |
| encoder-crossover-190 | author-side | `submission/BUILD_NOTES.md` |
| encoder-crossover-190 | author-side | `submission/METADATA.md` |
| encoder-crossover-190 | author-side | `tmlr/README.md` |
| replay-record-not-decision | shipped | `preprints/replay-record-not-decision-preprints.zip` |
| replay-record-not-decision | shipped | `released/replay-record-not-decision-released.tar.gz` |
| replay-record-not-decision | shipped | `rendered/replay-record-not-decision.pdf` |
| replay-record-not-decision | shipped | `submission/main.tex` |
| replay-record-not-decision | shipped | `submission/replay-record-not-decision.tar.gz` |
| replay-record-not-decision | payload | `released/replay-record-not-decision-released.tar.gz` — 10 payload members, one top-level directory; member paths and digests are in the archive's `MANIFEST.json`. The unpacked tree is **not** on disk |
| replay-record-not-decision | author-side | `AVAILABILITY.md` |
| replay-record-not-decision | author-side | `CLAIMS.md` |
| replay-record-not-decision | author-side | `GAPS.md` |
| replay-record-not-decision | author-side | `MANUSCRIPT.md` |
| replay-record-not-decision | author-side | `REFERENCES.bib` |
| replay-record-not-decision | author-side | `REFS.md` |
| replay-record-not-decision | author-side | `TMLR_ANONYMITY_NOTE.md` |
| replay-record-not-decision | author-side | `released/CITATION.cff` |
| replay-record-not-decision | author-side | `released/README_DEPOSIT.md` |
| replay-record-not-decision | author-side | `rendered/_superseded/README.md` |
| replay-record-not-decision | author-side | `rendered/_superseded/replay-record-not-decision-tectonic-prior-main-85f13e8c.pdf` |
| replay-record-not-decision | author-side | `submission/ABSTRACT.txt` |
| replay-record-not-decision | author-side | `submission/ABSTRACT_METADATA.txt` |
| replay-record-not-decision | author-side | `submission/BUILD_NOTES.md` |
| replay-record-not-decision | author-side | `submission/METADATA.md` |
| gated-read-batching | shipped | `preprints/gated-read-batching-preprints.zip` |
| gated-read-batching | shipped | `released/gated-read-batching-released.tar.gz` |
| gated-read-batching | shipped | `rendered/gated-read-batching.pdf` |
| gated-read-batching | shipped | `submission/gated-read-batching.tar.gz` |
| gated-read-batching | shipped | `submission/main.tex` |
| gated-read-batching | payload | `released/gated-read-batching-released.tar.gz` — 12 payload members, one top-level directory; member paths and digests are in the archive's `MANIFEST.json`. The unpacked tree **is** on disk at `released/gated-read-batching-released/` (12 files) |
| gated-read-batching | author-side | `CLAIMS.md` |
| gated-read-batching | author-side | `DISCLOSURE_CHANGES.md` |
| gated-read-batching | author-side | `GAPS.md` |
| gated-read-batching | author-side | `MANUSCRIPT.md` |
| gated-read-batching | author-side | `REFS.md` |
| gated-read-batching | author-side | `released/README.md` |
| gated-read-batching | author-side | `rendered/_superseded/README.md` |
| gated-read-batching | author-side | `rendered/_superseded/gated-read-batching-CHROME-headless-a4.pdf` |
| gated-read-batching | author-side | `rendered/_superseded/gated-read-batching-libreoffice.pdf` |
| gated-read-batching | author-side | `rendered/_superseded/gated-read-batching-tectonic-prior-main-ab6da666.pdf` |
| gated-read-batching | author-side | `rendered/_superseded/gated-read-batching.docx` |
| gated-read-batching | author-side | `rendered/_superseded/gated-read-batching.html` |
| gated-read-batching | author-side | `rendered/convert.py` |
| gated-read-batching | author-side | `submission/ABSTRACT.txt` |
| gated-read-batching | author-side | `submission/ABSTRACT_METADATA.txt` |
| gated-read-batching | author-side | `submission/BUILD_NOTES.md` |
| gated-read-batching | author-side | `submission/METADATA.md` |

### §2.3 · Consolidation history — 2026-10-19 (ULEDGER1)

This section is the audit trail for §2.1/§2.2. Everything here is **history as of the consolidation**, and every "is" figure was measured on this workspace at 2026-10-19 18:2x CDT (`os.path.getsize` / `sha256sum`). It is stale by the next rebuild by construction; do not quote it as current.

**What was removed.** §2 held 142 path rows, each with a byte count and a sha256 — 284 values — plus one `Release payload: N files, X bytes` line per paper, the per-member digest lists for the three archives, and repeated sizes/digests inside §3's evidence cells and §4.9/§4.10. All replaced by §2.1 (owners) and §2.2 (paths). Totals removed: **284 values from §2**, **3 payload byte totals**, **37 sizes and 9 abbreviated digests in §3**, **6 sizes and 10 abbreviated digests from §4.9/§4.10** — 349 values. Two sizes survive, in §4.2, because that blocker has to quote a measurement to make its point; they were taken by this consolidation. Kept: three concept DOIs, three Zenodo record ids (`23483304`, `23485733`, `23483315`), the archive member counts, file mtimes, and every step, blocker and dated note.

**(a) The 22 stale sizes this sweep measured against disk** (§2 rows and payload totals), `path: was → is`:

- `papers/encoder-crossover-190/tmlr/main.tex`: 83,785 → 84,088 B
- `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md`: 2,404 → 4,430 B
- `papers/replay-record-not-decision/rendered/replay-record-not-decision.pdf`: 94,683 → 101,593 B
- `papers/replay-record-not-decision/submission/main.tex`: 32,350 → 32,766 B
- `papers/replay-record-not-decision/submission/replay-record-not-decision.tar.gz`: 11,425 → 11,533 B
- `papers/replay-record-not-decision/AVAILABILITY.md`: 5,641 → 6,180 B
- `papers/replay-record-not-decision/MANUSCRIPT.md`: 25,965 → 26,364 B
- `papers/replay-record-not-decision/TMLR_ANONYMITY_NOTE.md`: 3,264 → 4,445 B
- `papers/replay-record-not-decision/released/CITATION.cff`: 2,158 → 2,511 B
- `papers/replay-record-not-decision/rendered/_superseded/README.md`: 1,802 → 2,743 B
- `papers/gated-read-batching/rendered/gated-read-batching.pdf`: 110,521 → 117,784 B
- `papers/gated-read-batching/submission/gated-read-batching.tar.gz`: 14,011 → 15,251 B
- `papers/gated-read-batching/submission/main.tex`: 39,351 → 42,531 B
- `papers/gated-read-batching/MANUSCRIPT.md`: 34,871 → 37,913 B
- `papers/gated-read-batching/released/README.md`: 1,340 → 14,170 B
- `papers/gated-read-batching/rendered/_superseded/README.md`: 3,628 → 532 B
- `papers/gated-read-batching/submission/METADATA.md`: 15,329 → 15,908 B
- `gated archive member CITATION.cff`: 1,862 → 2,139 B
- `gated archive member MANIFEST.json`: 4,649 → 4,650 B
- `gated archive member README_DEPOSIT.md`: 9,868 → 10,105 B
- `replay payload total`: 10 files / 1,313,090 → 1,313,443 B
- `gated payload total`: 12 files / 2,383,883 → 2,384,398 B
- `encoder released archive` (stale value only, from the superseded §4.2 text): 159,185 → 159,182 B; the archive moved more than once, so neither figure is current — measure it
- `ZENODO_DEPOSIT.md` §1 report figures (quoted there, not measured here): upload 157,272 B superseded on 2026-10-17 to 157,650 B, payload 851,043 B — against disk 159,182 B / 856,779 B

The 142 row digests were equally stale; they are not reproduced here — the kit README and the archives' `MANIFEST.json` own them, and a stale digest is worthless rather than historical. The encoder payload (31 files / 856,779 B) re-measured exactly.

**(b) Stale values a prior sweep had already named** (kept verbatim from `USIZEFIX1`'s §4.10, which this consolidation folded in here):

- `encoder-crossover-190/tmlr/main.pdf`: 176,971 → 177,298 B, sha256 `a777d2a3…1929acdf` → `fb95f0ac…38cf1109`
- `replay-record-not-decision/preprints` zip: 11,379 → 11,526 B, sha256 `63044528…3260173d` → `1b520f22…4953537d`
- `replay-record-not-decision/released` archive: 107,641 → 107,764 B, sha256 `b5dbe854…e7168ce2` → `e6f920c4…ec3bbe63`
- `gated-read-batching/preprints` zip: 14,094 → 15,296 B, sha256 `feecb7f7…127b74f5` → `7efe3af1…dfe783a0`
- `gated-read-batching/released` archive: 128,559 → 128,902 B, sha256 `1e3b5781…6f38827c` → `e2ceb554…cd464b24`

**(c) `:191` — `released/README.md`, the one row that was wrong by an order of magnitude.** The row named `papers/gated-read-batching/released/README.md` and claimed 1,340 B. Measured: **14,170 B**, sha256 `a453041e21c7a4cda37e5ce5fbb718ec9ea92c28c94fc762dbddda402663a39d` — byte-identical to the archive member `README.md` that the same section already listed at 14,170 B. So the row described **the file it names**; 1,340 B was a stale measurement of an earlier revision of that same path, not a different file. No 1,340-byte file exists anywhere under `papers/gated-read-batching/` (searched), so there is no third file the old number could have meant.

**(d) Dated notes folded into this section.** The inline `(Superseded 2026-10-19 …)` notes in §3 and §4 were the same values again; each now remains at its step as a one-line marker naming the date and the unit, with its values here. The old wording of 4.1, 3.2 step 4 and 3.3 step 4 (the "no DOI" era) is reproduced there as well.

**(e) Side finding while measuring.** The encoder and replay payload trees are not extracted on disk (0 files) — only their `.tar.gz` archives exist; `released/SUPERSEDED-UNPACKED-TREE.md` records why for encoder (moved to `scratch/utrees1/`, UTREES1). Gated's tree is present (12 files). The old §2 payload tables therefore listed 41 paths that no longer existed as paths; §2.2 names the archive and its `MANIFEST.json` instead.

## §3 · Steps, per experiment, in order

The same seven-step path applies to all three; the state differs. Step text is grounded in `strategy/ZENODO_DEPOSIT.md` §1–§5, `strategy/PREPRINTS_SUBMISSION.md` §1, §7, §8, `strategy/TMLR_SUBMISSION.md`, `papers/replay-record-not-decision/TMLR_ANONYMITY_NOTE.md`, `strategy/TMLR_POLICY.md:266`.

Evidence cells name paths, identifiers and states only. No size or digest is restated here: measure the path, or read its owner per §2.1.

### 3.1 `encoder-crossover-190` (EXP#12)

| # | Step | State | Evidence / what remains |
|---|---|---|---|
| 1 | Freeze manuscript, regenerate `submission/main.tex` | **done** | `submission/main.tex` regenerated from `MANUSCRIPT.md`; digest: measure it (§2.1) |
| 2 | Build Preprints bundle + arXiv bundle | **done** | `preprints/encoder-crossover-190-preprints.zip` (upload copy listed in `submission-kit/README.md`) and `submission/encoder-crossover-190.tar.gz` |
| 3 | Build release package + deposit archive | **done, but the archive is being rebuilt right now** | `released/encoder-crossover-190-released.tar.gz`, mtime 2026-10-19 13:23:32 −0500 — see §4.2 |
| 4 | Zenodo deposit | **done** | concept DOI `10.5281/zenodo.23463944`; `released/encoder-crossover-190-released/CITATION.cff:25` `doi: "10.5281/zenodo.23463944"` + `:30-33` "DOI installed 2026-10-18 (UDOIBACK1) … CONCEPT DOI installed 2026-10-18 (UCONCEPT1)" |
| 5 | DOI back-fill into the paper | **done** | `MANUSCRIPT.md:743,794,858` carry the concept DOI; `main.tex` carries `10.5281/zenodo.23463944`; PDF recompiled (`rendered/encoder-crossover-190.pdf`) |
| 6 | Preprints.org submission | **not done** | upload `preprints/encoder-crossover-190-preprints.zip`; see 3.4 |
| 7 | TMLR submission | **not done (built)** | `tmlr/main.tex` + `tmlr/main.pdf`, `tmlr/README.md` "the double-blind (anonymised) submission variant"; see 3.5 — (Superseded 2026-10-19 (USIZEFIX1): the prior size for `tmlr/main.pdf` is in §2.3(b)) |

### 3.2 `replay-record-not-decision` (EXP#7)

| # | Step | State | Evidence / what remains |
|---|---|---|---|
| 1 | Freeze manuscript, regenerate `main.tex` | **done** | `submission/main.tex` regenerated; digest: measure it (§2.1) |
| 2 | Build bundles | **done** | `preprints/replay-record-not-decision-preprints.zip` (upload copy in `submission-kit/README.md`) and `submission/replay-record-not-decision.tar.gz` — (Superseded 2026-10-19 (USIZEFIX1): the prior zip size is in §2.3(b)) |
| 3 | Build release package | **done** | `released/replay-record-not-decision-released.tar.gz`; payload members: the archive's `MANIFEST.json`, `generated_utc 2026-10-19T06:15:00Z` — (Superseded 2026-10-19 (USIZEFIX1): the prior archive size and digest are in §2.3(b)) |
| 4 | Zenodo deposit | **done — published 2026-10-19** | concept DOI `10.5281/zenodo.23482511`, latest version v2 = record `23483304`; packaged `CITATION.cff:34` carries `doi: "10.5281/zenodo.23482511"`; archive digest for the record: `sha256sum` it (§2.1). (Superseded 2026-10-19, old wording kept as dated history: this row previously read "NOT DONE — blocks 5–7" and cited `CITATION.cff:33-36` "DOI: deliberately absent. No DOI exists for this deposit yet.") The paper's citation of `10.5281/zenodo.23463944` in `submission/ABSTRACT.txt:17` is still the **companion** (encoder) deposit, not this one — intentional and unchanged |
| 5 | DOI back-fill | **done** | `CITATION.cff` `doi:` field carries `10.5281/zenodo.23482511`; `MANUSCRIPT.md` carries the persistent identifier; `submission/main.tex` carries the DOI (3 occurrences); `rendered/replay-record-not-decision.pdf` recompiled after the back-fill — (Superseded 2026-10-19: this row previously read "**pending**"; the pre-back-fill size is in §2.3(a)) |
| 6 | Preprints.org | **not done** | upload the zip; the data-availability statement already points at the deposit (`AVAILABILITY.md` carries `10.5281/zenodo.23482511`) — (Superseded 2026-10-19: this row previously said availability "must point at the deposit once it exists") |
| 7 | TMLR | **built, not submitted** | `tmlr/main.tex` + `tmlr/main.pdf` (double-blind variant, `tmlr.sty` present), plus `TMLR_ANONYMITY_NOTE.md` (author-side) — (Superseded 2026-10-19: this row previously read "not done — no variant built") |

### 3.3 `gated-read-batching` (no EXP number)

| # | Step | State | Evidence / what remains |
|---|---|---|---|
| 1 | Freeze manuscript, regenerate `main.tex` | **done** | `submission/main.tex` regenerated; digest: measure it (§2.1) |
| 2 | Build bundles | **done** | `preprints/gated-read-batching-preprints.zip` (upload copy in `submission-kit/README.md`) and `submission/gated-read-batching.tar.gz` — (Superseded 2026-10-19 (USIZEFIX1): the prior zip size is in §2.3(b)) |
| 3 | Build release package | **done** | `released/gated-read-batching-released.tar.gz`; payload members: the archive's `MANIFEST.json`, `generated_utc 2026-10-19T08:10:00Z` — (Superseded 2026-10-19 (USIZEFIX1): the prior archive size and digest are in §2.3(b)) |
| 4 | Zenodo deposit | **done — published 2026-10-19** | concept DOI `10.5281/zenodo.23483314`, latest version v2 = record `23485733`; `released/gated-read-batching-released/CITATION.cff:18` carries `doi: "10.5281/zenodo.23483314"` (its note records v1 record `23483315` and keeps the superseded "no DOI minted" wording as dated history). (Superseded 2026-10-19, old wording kept as dated history: this row previously read "NOT DONE — blocks 5–7" and cited `CITATION.cff:31-34` / `README_DEPOSIT.md` "No DOI has been minted for this deposit yet") |
| 5 | DOI back-fill | **done** | same three files as 3.2 step 5; `submission/main.tex` carries `10.5281/zenodo.23483314`, and `MANUSCRIPT.md` + `AVAILABILITY.md` carry it; `rendered/gated-read-batching.pdf` recompiled — (Superseded 2026-10-19: this row previously read "**pending**"; the pre-back-fill size is in §2.3(a)) |
| 6 | Preprints.org | **not done** | upload the zip; the paper now *has* a root `AVAILABILITY.md` carrying the deposit DOI — (Superseded 2026-10-19: this row previously said the paper had no root `AVAILABILITY.md` and that the statement had to be written) |
| 7 | TMLR | **built, not submitted** | `tmlr/main.tex` + `tmlr/main.pdf`, `tmlr.sty` present — (Superseded 2026-10-19: this row previously read "no anonymised variant and no anonymity note exist for this paper") |

### 3.4 Zenodo deposit — what to do, field by field

From `strategy/ZENODO_DEPOSIT.md` §1–§5 (the encoder run; the same record shape applies to the other two):

- **File:** `papers/<slug>/released/<slug>-released.tar.gz` — one `.tar.gz`, exactly one top-level directory inside.
- **Resource type:** `Dataset`, **and only one** — `ZENODO_DEPOSIT.md:41` is superseded on this point: "Zenodo allows exactly ONE resource type per record". Not `Publication`.
- **Licence:** `polyform-noncommercial-1.0.0` (PolyForm Noncommercial License 1.0.0), verified present in Zenodo's licence vocabulary (`ZENODO_DEPOSIT.md` §4 records the `?q=PolyForm` response, 2 hits). The **paper text** is CC BY 4.0 — a different object; do not put PolyForm on the manuscript record.
- **Leave empty:** affiliation, ORCID (never supplied), `Version` (none assigned by the author), related-identifier DOI for the paper (it does not exist yet), publication date (let Zenodo stamp it — do not back-date). `date-released` in `CITATION.cff` is the package build date and is the author's call to change on upload.
- **Creator split:** family `Kalugasala Moorthy`, given `Aswin Ram`; the author should confirm it renders back to the full name.
- **After publication:** add the **concept** DOI (not the version DOI) to `CITATION.cff` so the citation survives version bumps.

### 3.5 DOI back-fill into the paper

Changes three things and requires a rebuild: (a) `CITATION.cff` `doi:` field in the release payload; (b) the persistent-identifier sentence in `MANUSCRIPT.md` (encoder: `MANUSCRIPT.md:858`); (c) regenerate `submission/main.tex` from the manuscript and **recompile the PDF** — the DOI is in the LaTeX source, so a stale PDF would print the old text. Replay and gated have now completed (a)–(c) as well: their `CITATION.cff` files carry `10.5281/zenodo.23482511` / `10.5281/zenodo.23483314`, their `MANUSCRIPT.md`, `AVAILABILITY.md` and `submission/main.tex` carry the same identifiers, and their PDFs were recompiled. (Superseded 2026-10-19: this sentence previously read "For replay and gated, both (b) and (c) are still ahead, and (a) cannot start until the deposit exists.")

### 3.6 Preprints.org submission

From `strategy/PREPRINTS_SUBMISSION.md` §1 (sources fetched 2026-10-18), §7, §8, and `strategy/DEPOSIT_METADATA.md` §2.3:

- **File:** `papers/<slug>/preprints/<slug>-preprints.zip` — a self-contained LaTeX zip (bibliography inlined in `main.tex`; the `.bib` clause is conditional, "if applicable"). A PDF alone is **not** an accepted source format.
- **Form requires:** title; abstract; **keywords**; name, **affiliation**, **email** for **every** author; manuscript; conflicts-of-interest declaration. First page must carry title, author list, abstract, keywords, corresponding-author contact, affiliations — six elements.
- **Type** `Article`; subject `Computer Science & Mathematics` (the second-level entry is the author's pick — never verified, so do not invent it).
- **DOI field: leave empty.** Preprints.org mints the preprint's own Crossref DOI at posting (`10.20944/preprints<YYMM>.<NNNN>.v<N>`). Do **not** paste the Zenodo DOI there.
- **Licence:** CC BY 4.0, fixed by the platform — posting *is* accepting it. This is not a conflict with PolyForm on the data: two objects, two licences.
- Screening takes "<24 hours"; the author has no co-authors to notify.

### 3.7 TMLR submission

From `strategy/TMLR_SUBMISSION.md`, `papers/encoder-crossover-190/tmlr/README.md`, `papers/replay-record-not-decision/TMLR_ANONYMITY_NOTE.md`, `strategy/TMLR_POLICY.md:266`:

- **Submit the anonymised variant**, `papers/<slug>/tmlr/main.tex` + `main.pdf`, with the **mandatory** `tmlr.sty` (present in each `tmlr/` directory; measure it if a number is needed) — the style file is part of the submission, not a local preference.
- **Anonymity forbids linking to a named version — including the paper's own deposit DOI.** `TMLR_ANONYMITY_NOTE.md`: `10.5281/zenodo.23463944` is a concept DOI that resolves to an author-attributed record, so printing it hands the reviewer a resolvable author link. Withhold the DOI, the Zenodo URL, and any `\texttt{{10.5281/…}}` fragment; cite the companion in the third person ("[citation withheld for double-blind review]"); restore the identifier and standard citation in the camera-ready.
- **There is no major-revision decision.** `strategy/TMLR_POLICY.md:266`: *"There is no 'major revision' option. The only revision state is 'minor', delivered as the camera-ready."* A submission is accepted or rejected; plan for that, not for a revise-and-resubmit round.
- The encoder variant was built by a 2-line transform (byline + one self-identifying sentence); replay and gated have **no** variant built.

## §4 · Blocked or undecided

| # | Item | Reason (grounded) | Who acts |
|---|---|---|---|
| 4.1 | Replay and gated **now have DOIs** (superseded 2026-10-19) | both deposits published 2026-10-19: concept DOIs `10.5281/zenodo.23482511` (replay, latest v2 `23483304`) and `10.5281/zenodo.23483314` (gated, latest v2 `23485733`); each `CITATION.cff`, `MANUSCRIPT.md`, `AVAILABILITY.md` and `submission/main.tex` carries its DOI. This row previously read "Replay and gated have **no DOI** … publish the two deposits" | **done** — the author's deposit action is closed; only the uploads in 3.2/3.3 steps 6–7 remain |
| 4.2 | **The encoder deposit archive is unstable right now** | `released/encoder-crossover-190-released.tar.gz` re-measured 2026-10-19 18:2x CDT at 159,182 B, mtime `2026-10-19 13:23:32 −0500`, payload 31 files / 856,779 B; the same session had already seen a different size minutes before, and `ZENODO_DEPOSIT.md`'s payload figure disagrees with disk (§2.3(a)). Another unit is rebuilding it | **the unit owning that rebuild** — freeze it, then re-measure before anyone quotes a digest |
| 4.3 | Preprints form needs **affiliation + email** for every author | no package contains either; `METADATA.md` records the author slot as resolved but no institution | **author** — supply before submitting |
| 4.4 | `date-released` in every `CITATION.cff` is the **build** date, not a deposit date | each file says so in its own comment | **author** — correct on upload |
| 4.5 | Creator name split (family/given) unconfirmed | `ZENODO_DEPOSIT.md` §2: the split is inferred; "the author should confirm it" | **author** |
| 4.6 | TMLR anonymity vs. the author's own public deposit | single author + published deposit = residual re-identification vectors recorded in `TMLR_SUBMISSION.md` §5 | **author** accepts the residual risk |
| 4.7 | Gated paper has **no `AVAILABILITY.md`, no root `METADATA.md`, no `REFERENCES.bib`** | directory listing: only `CLAIMS.md DISCLOSURE_CHANGES.md GAPS.md MANUSCRIPT.md REFS.md` plus subdirs | **author/next unit** — the availability statement for the preprint form has to be written |
| 4.8 | Gated paper has **no experiment number** | §1 above: provenance is a 2026-09-30 run | **author** — decide whether to assert an EXP id at all; do not invent one |
| 4.9 | Reports vs disk disagreements | `ZENODO_DEPOSIT.md` §1's upload size, its 2026-10-17 supersession, and its payload figure all disagree with disk — the named values are in §2.3, and 4.2 is why they are not resolved here | recorded, not resolved — 4.2 is why |
| 4.10 | **Stale inventory sizes re-measured (USIZEFIX1, 2026-10-19)** | disk vs. what this file said before that pass: five artifacts, all now in §2.3(b) with both their old and new values (old values kept there as dated history) | **next unit** — re-measure before quoting a digest (§4.2 shows the encoder archive is a moving target) |

## §5 · The numbering hazard

Three numberings are in use in this workspace. Always write the **path**; a bare "paper #2" is ambiguous and "paper 7" is not "EXP#7".

| Path | Candidate rank (`PAPER_CANDIDATES.md`) | Alternate numbering (`CASE_SWEEP_REPORT.md`, `orchestration/units/UFIXFINAL1.md`) | Experiment |
|---|---|---|---|
| `papers/encoder-crossover-190/` | **#3** (`PAPER_CANDIDATES.md:76`; `CITATION.cff` of the other two call it "paper #3") | **#1** (`UFIXFINAL1.md:7` "Paper #1"; `CASE_SWEEP_REPORT.md:120` "Paper #1 package … already public on Zenodo") | **EXP#12** |
| `papers/replay-record-not-decision/` | **#2** (`PAPER_CANDIDATES.md:75`) | **#3** (`CASE_SWEEP_REPORT.md:197` "paper #3's package (`papers/replay-record-not-decision/released/`)") | **EXP#7** |
| `papers/gated-read-batching/` | **#7** (`PAPER_CANDIDATES.md:81`) | **#2** (`CASE_SWEEP_REPORT.md:206` "`data/gated-read-rows.jsonl` … is in paper #2's package") | **none** (2026-09-30 run) |

Consequences to carry into any handoff:

1. "paper #2" means **replay** in candidate numbering and **gated** in the alternate numbering — same string, different paper. Name the path.
2. "paper 7" means **gated**; "EXP#7" means **replay's experiment**. They are not the same axis.
3. "paper #1" only exists in the alternate numbering (encoder); in candidate numbering #1 is a *different, unpublished* candidate ("Deriving agent state from an observation stream") — so "paper #1" is also path-required.
