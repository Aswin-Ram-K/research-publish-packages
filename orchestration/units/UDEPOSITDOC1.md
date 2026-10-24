# UDEPOSITDOC1 — copy-paste deposit metadata sheets + ordered submission runbook

**Status:** in progress
**Author byline of record:** Aswin Ram Kalugasala Moorthy (name only, no affiliation)
**Hard bound:** 25 tool calls. No network writes. No uploads/submissions/contacts.

## Purpose (one)

Write the two copy-paste metadata sheets (Zenodo + Preprints.org) and the ordered runbook the author
follows to publish, sourced strictly from the strategy files, the previous upload text and the paper
submission metadata already on disk.

## Sources of record (read these)

- `strategy/ZENODO_DEPOSIT.md` — Zenodo field plan (UZENODO2). NOTE: its §1/§9 digest rows
  (`157,272` / `a0a210fc…`) are **superseded**; current archive is `157,650` / `7389bd87…`.
- `strategy/DEPOSIT_ARCHIVE.md` — archive state and digests.
- `strategy/TMLR_POLICY.md` — TMLR rules, quoted from primary sources.
- `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` — previous upload text.
- `papers/encoder-crossover-190/submission/METADATA.md` and `ABSTRACT_METADATA.txt`.
- `papers/encoder-crossover-190/released/` — current archive.

## Verified starting state (given in the card, re-checked on disk)

| artifact | bytes | sha256 | members |
|---|---|---|---|
| `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | 157,650 | `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` | 37 |
| `scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip` | 169,869 | `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610` | 29 |
| `scratch/uneutral10/package/MANIFEST.json` | — | `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02` | — |

## Deliverables

1. `strategy/DEPOSIT_METADATA.md` — two copy-paste blocks, every field an exact literal. Zenodo:
   upload type (Dataset vs Software presented honestly, recommendation marked author-overridable),
   title, creators, description, licence `polyform-noncommercial-1.0.0` (scheme `spdx`), version,
   language, keywords, related identifiers. Preprints.org: title, abstract, authors, subject area,
   keywords, licence, DOI field. Creator name split presented as a question, not chosen.
   Description promises **no reproduction of the experiment** (harness withheld).
2. `strategy/SUBMISSION_RUNBOOK.md` — ordered steps (1) Zenodo data deposit + DOI, (2) preprint,
   (3) TMLR later. TMLR leg states the hard constraint: **the TMLR PDF must not link the preprint,
   the Zenodo DOI or the GitHub repo**, and points to the compliance work instead of duplicating it.
   Marks author-only steps.
3. `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` — verified against current digests; correct in place
   if it cites a superseded digest, and say exactly what changed.

## Write paths (nothing else)

`strategy/DEPOSIT_METADATA.md`, `strategy/SUBMISSION_RUNBOOK.md`,
`scratch/urelease9/zenodo/ZENODO_UPLOAD.txt`, `scratch/udepositdoc1/**`,
`orchestration/units/UDEPOSITDOC1.md`, `orchestration/handoffs/UDEPOSITDOC1.json`

## Report back

Handoff with exactly 7 keys: `unit`, `status`, `artifacts`, `evidence`, `blocker`, `next_unit_hint`,
`write_paths`. ≤15-line summary to parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.
