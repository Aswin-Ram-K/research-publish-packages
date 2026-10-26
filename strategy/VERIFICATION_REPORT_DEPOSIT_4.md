# VERIFICATION REPORT — DEPOSIT 4 (VDEPOSIT4)

Independent verification of **UFIXDEP4** before Zenodo upload (permanent DOI). Verifier did not
author what is checked. **No file was fixed, no archive rebuilt or overwritten, no network call.**
Hard bound 15 tool calls; used 15. Measurements taken 2026-10-18 (workspace clock).

Extraction used for re-checks: `scratch/vdeposit4/extract/encoder-crossover-190-released`
(from the shipped archive, read-only source).

## Overall: **PASS**

Every claim that could be re-measured without rebuilding the shipped archive re-measured true. The
two-build byte-identity claim and one custody baseline were **not reproduced** (see §3, §6) — stated
plainly rather than asserted. One brief expectation (ASCII) is **contradicted**; it is disclosed by
the author and harmless.

## 1. The repair — PASS (one contradicted expectation)

- `scratch/uneutral10/package/CONTRIBUTING.md` = **3,547 B, sha256
  `3b5e59622b3e4b7d4b9326101b615bcef484ddd80b31b78306ba416698a87996`** — matches the claim.
- DRAFT banner and `../PLACEMENT.md` link **gone**: `grep -iE 'draft|PLACEMENT'` → no hits.
- Replacement (file lines 3–7) names the **PolyForm Noncommercial License 1.0.0**, the **paid-licence
  requirement for commercial use**, the **ideas-not-code** policy with the re-implementation
  rationale, and the **repository issue tracker**
  `<https://github.com/Aswin-Ram-K/research-publish-packages>`. No email address invented
  (`@host.tld` / `mailto` regex → 0 hits).
- **Contradicted:** the brief's expectation that the file is ASCII. `file` reports UTF-8 and
  `grep -P '[^\x00-\x7F]'` hits **line 34** and **line 49** — two em dashes (U+2014). UFIXDEP4's own
  handoff discloses this ("File keeps its 2 pre-existing em dashes"), so no author claim is
  falsified; em dashes in a markdown licence banner are harmless for Zenodo.

## 2. Shipped checks re-run on an extraction — PASS, reproduced exactly

- `python3 /home/zer0null/reserach\ extarctor/tools/package/check_manifest.py --package <extracted root>`
  → `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`,
  `manifest_self_recomputes=True`, `VERDICT PASS`, **exit 0**.
- `python3 verify/recompute-claims.py` *inside* the extraction → **exit 0**,
  `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`, fixture digest
  **`c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`** — exact match.

## 3. Byte-identity — archive PASS; rebuild NOT reproduced

- Shipped archive `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`:
  **158,956 B, sha256 `bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2`,
  37 members** (6 `/`-terminated dirs = 1 top-level + 5 subdirs, 31 files). Matches claim.
- `CONTRIBUTING.md` **inside** the archive = 3,547 B / `3b5e5962…` — the repaired file, not the old one.
- **Not reproduced:** UFIXDEP4's "two builds byte-identical" and "extraction checks pass" rebuild
  result. I was forbidden to rebuild or overwrite the shipped archive, so I measured the shipped
  bytes and extracted them; the two-build identity itself is the author's assertion, re-derivable
  only by re-running `scratch/ufixman1/build_archive.sh`, which this unit did not do. Superseded
  digest `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` / 158,762 B is the
  prior release; nothing on disk still holds it.

## 4. The documents and the class sweep — PASS (clean)

All five carry the new digest and match the claimed sizes/digest prefixes:

| document | bytes | measured sha256 (prefix) |
|---|---|---|
| `strategy/DEPOSIT_ARCHIVE.md` | 14,747 | `17cd21877632ab4e…` |
| `strategy/DEPOSIT_METADATA.md` | 29,115 | `0cc82e4550bb8681…` |
| `strategy/ZENODO_DEPOSIT.md` | 29,637 | `074974fcb4eb0c76…` |
| `strategy/SUBMISSION_RUNBOOK.md` | 13,405 | `5daa1dd050a1608c…` |
| `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` | 14,665 | `2aed9d2fd78862cb…` |

Class sweep `grep -rlE '956d6363|7389bd87'` over the whole workspace → **28 files**: 8 carry the new
digest too, **20 are OLD-ONLY**, and every one of the 20 is a frozen record:

- `orchestration/handoffs/{UDEPOSIT2,UDEPOSITDOC1,UDEPOSITDOC2,UFIXDEP1,UFIXDEP2,UFIXDEP3,UFIXMAN1,VDEPOSIT1,VDEPOSIT2,VDEPOSIT3}.json` (10)
- `orchestration/units/{UDEPOSITDOC1,UFIXDEP2,UFIXMAN1,VDEPOSIT1,VDEPOSIT2,VDEPOSIT3}.md` (6)
- `strategy/VERIFICATION_REPORT_DEPOSIT.md`, `strategy/VERIFICATION_REPORT_DEPOSIT_2.md`, `strategy/VERIFICATION_REPORT_DEPOSIT_3.md` (3)
- `scratch/udepositdoc2/EVIDENCE.md` (1)

**No live depositor-facing document is OLD-ONLY.** `strategy/VERIFICATION_REPORT_DEPOSIT.md:133`
even labels itself `**STALE.**`. Nearest trip hazard: the three dated verifier reports under
`strategy/` quote 158,762 B / `956d6363…` as current *within their own date*; they are frozen
records (UFIXDEP4's hint already flags `_3`). A later pointer or a verification report #5 would
close the gap; this unit does not edit them.

## 5. The `:18` wording fix — PASS (true as written)

The proof row in `strategy/DEPOSIT_ARCHIVE.md` now reads: "`diff -r` against the package inputs is
**not** empty — exactly one file differs, `MANIFEST.json`, which is regenerated for the archive
(11,761 B, `23b7fa94…`) and so cannot equal the package's (11,043 B, `fecdc1fb…`); the other 28
package files are byte-identical." Re-measured by per-file `cmp` of all 29 package files against the
archive extraction: **exactly 1 differs (`MANIFEST.json`), 28 identical**, and the archive adds
exactly `CITATION.cff` + `README_DEPOSIT.md`. Archive `MANIFEST.json` =
**11,761 B `23b7fa947fd2ee8c2b58963280dce104e031605b9e91c46e217428c118178856`**,
`counts {files: 31, bytes_total: 844600}`, 30 listed, `manifest_self 6381551c…`; package
`MANIFEST.json` = **11,043 B `fecdc1fbf67820be…`**. The new wording is true.

## 6. Custody — PASS on containment; one baseline unverified

- `tools/package/**` sources unchanged (`check_manifest.py` mtime 2026-10-16 16:29,
  `regen_manifest.py` 2026-10-16 16:33); `scratch/ufixman1/build_archive.sh` sha256 prefix
  `afca433786dd7428` matches VDEPOSIT3's custody baseline `afca4337…`.
- `submission/**` mtimes all ≤ 2026-10-18 03:02 local, i.e. **before** the UFIXDEP4 edit window
  (package `CONTRIBUTING.md`/`MANIFEST.json` and the archive at 03:22 local); no file under
  `papers/`, `submission/`, `tools/`, `strategy/` modified after 2026-10-18 09:00.
- Measured payload digests: `papers/encoder-crossover-190/submission` 6 files agg
  `ff3c32210f132239…`; `papers/gated-read-batching/submission` `a6193aa6162b19a9…`;
  `papers/replay-record-not-decision/submission` `036e258b5b125641…`; `main.tex` sha256
  `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`,
  `d321f8c3e5500518d8bf75783ce8e3620078d52af51d543a8cbf11748624c0c9`,
  `2059e12bda2612a4bcbe3cbb490dc5538a56d6754c71d3f48cab3ce3b74fcf7a`. Only
  `papers/encoder-crossover-190/released/` exists as a released dir.
- **Unverified:** "the three papers' payloads still match what they were". VDEPOSIT3's aggregate
  `papers 36 files 09fb2d08…` could not be reconstructed (papers/ now measures 70 files; 67
  excluding `released/`), so equality rests on mtime + write-path containment, not on a digested
  baseline.
- Side-effect note: the shipped check was run as `python3 tools/package/check_manifest.py`; measured
  `tools/package/__pycache__/*.pyc` mtimes are unchanged (2026-10-16, one 10-18 02:31 for
  `md2tex`), so no byte under `tools/package/**` changed. All writes stayed in `scratch/vdeposit4/**`
  and the three declared report/card/handoff paths.

## 7. The whole question — would a reader deposit the right file? **Yes.**

Following `strategy/DEPOSIT_METADATA.md` §0, the top table of `strategy/DEPOSIT_ARCHIVE.md`, the
UFIXDEP4 block of `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt`, or `strategy/SUBMISSION_RUNBOOK.md:48`
lands on `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`, **158,956 B,
`bcdbf75e…`, 37 members**. Two residual trip hazards, both disclosed and both dated:
(a) `strategy/ZENODO_DEPOSIT.md:22-23` still reads "live value `7389bd87…`" inside its own
"SUPERSEDED 2026-10-17" annotation; the appended UFIXDEP4 section at `:429+` supersedes it and
names `strategy/DEPOSIT_METADATA.md` §0 as authoritative;
(b) the three frozen `strategy/VERIFICATION_REPORT_DEPOSIT*.md` reports quote the older archive as
current within their own scope. No invented email; licence claims all present.

## Red→green guard

`tools/package/check_manifest.py`, on a scratch copy in `scratch/vdeposit4/rg/tree`:

| step | action | result |
|---|---|---|
| GREEN | untouched copy | `missing=0 … unlisted=0`, `VERDICT PASS`, **exit 0** |
| RED | one byte flipped in `CONTRIBUTING.md` | `HASH: CONTRIBUTING.md`, `VERDICT FAIL`, **exit 1** |
| GREEN | byte restored | `VERDICT PASS`, **exit 0** |

The guard is real and falsifiable. **Not demonstrated:** a falsification of `verify/recompute-claims.py`
within the bound. Tampering a stored metrics accuracy (`results/eval-modernbert-base.json`
0.347368→0.999999) did **not** trip it (the script recomputes accuracy from raw labelled data and
enforces published-vs-tree constants); the second attempt mutated the script's own published constant
alongside the tree value, moving both together. Its positive direction (exact pass on the shipped
bytes) is reproduced.

## Classification

- **contradicted:** the brief's expectation that `CONTRIBUTING.md` is ASCII — it is UTF-8 with two em
  dashes at `:34` and `:49` (author-disclosed; harmless).
- **overstated:** none.
- **not_reproduced:** (1) UFIXDEP4's two-build byte-identity / rebuild result (forbidden to rebuild;
  shipped bytes match the stated digest, size and member count); (2) any falsification of the
  `recompute-claims.py` guard within the bound; (3) VDEPOSIT3's `papers 36 files 09fb2d08…` aggregate.
- **unverified:** "the three papers' payloads still match what they were" (no reconstructible digest
  baseline; containment and mtimes hold).
