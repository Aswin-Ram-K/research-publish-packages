# gated-read-batching — per-decision gate records + verification

Data and verification for paper #7, *Gated read batching* (the note is a separate work and is not part of this deposit).
This package ships the raw per-decision rows of the 2026-09-30 gate run, the run report and summary as
records, and a checker that re-derives every headline number from the shipped bytes.

---

## ⚠ Validity limitation — the gold labels are stored, not reproducible (recorded, not hidden)

**The stored gold labels cannot be rebuilt from anything in this package.** The manuscript's §3.2 says
the harness "recomputes gold from the bytes on every run rather than trusting a stored label"; the raw
record does not support that. Re-deriving the gold set from corpus content under the rule the fixture
states ("file contains the answer substring; harness dir excluded") yields **127 gold pairs in the
pinned snapshot tree and 130 in the live tree, against 120 stored** — stored-only 12 (pinned) / 14
(live), recomputed-only 19 (pinned) / 24 (live). **10 of the 12 stored-only pairs are a single file,
`AGENTS.md`.** No harness or fixture script reproducing the stored `gold` field exists on disk, and
`tasks.json` lists 90 paths with no hashes, so the fixture is not pinned by digest.

**Consequence — a validity limitation, not a bookkeeping one.** The **120-pair gold count**, the
**6.7 % base rate** (120/1,800) and **every precision, recall, F1 and accuracy figure** in the paper are
obtained from *recorded verdicts*, not reproduced from the fixture. The batching comparison is not
endangered — all five configurations share the same stored labels — but a reader cannot rebuild the
labels, and the numbers describe label-consistent behaviour rather than an independently reproducible
fixture. Two readings remain inseparable: the harness applied a labelling rule the note does not
capture, or the corpus drifted between the 2026-09-30 run and the Oct-8 snapshot.

*Recorded 2026-10-15 from the raw-record re-verification; the full text is held in the project's gap
register, entry G-25, which is not part of this deposit.*

---

## What ships

| path | contents |
|---|---|
| `data/gated-read-rows.jsonl` | the 9,260 per-decision rows the recomputation reads — the proven-minimal closure |
| `results/gated-read-summary.json` | the aggregates the harness wrote (has `prompt_tok_total: null` for bs16/bs90 — see the note below) |
| `results/GATED_READ_2026.md` | the run report (340 lines) |
| `results/GATED_READ_PROVENANCE.md` | literature provenance and fetched URLs (backs the Related Work numbers) |
| `verify/recompute-claims.py` | re-derives every headline number from `data/` alone; stdlib only |
| `README.md`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `MANIFEST.json` | package documentation, licence and manifest |
| `CITATION.cff` | deposit-level citation — added by the archive recipe, not package content |
| `README_DEPOSIT.md` | deposit-level front matter — added by the archive recipe, not package content |

The package is **10 files**; the deposit archive adds those 2 metadata files on top, so the shipped tree is **12 files**. See `README_DEPOSIT.md` §"Integrity".

## What does not ship

**The harness, the corpus and the task fixture.** There is no `harness/` or `tools/gated-read/`
directory, no 90-file corpus, no `tasks.json`, and no model service. This is why the checker recomputes
only from the rows, and why the recorded gold sets above cannot be rebuilt here.

Two corpus-scale numbers therefore are **not** recomputed by the checker and are stated from the run
report only: corpus size **90 files**, measured **2,426,190 B pinned / 2,886,664 B live** — the report's
recorded **"1.83 MB" is withdrawn** as unsupported (`GAPS.md` G-25). The summary's `prompt_tok_total` is
`null` for `gate16_none`/`gate90_none`; the paper quotes those two prompt-token totals only because they
were re-derived from the raw rows, which is what `verify/recompute-claims.py` does.

## How to verify

```bash
python3 verify/recompute-claims.py        # exit 0 == every published number reproduced
```

The checker prints one line per comparison and **folds every comparison into the exit status**: a single
`[FAIL]` makes it exit 1. (Paper #3's checker once printed `reproduced=False` and still exited 0; that
failure mode is not repeated here.) Two checks are labelled **RUN-REPORT-ONLY** — the **15.279×**
selfselect/stage_route prompt-token ratio and the **exposure 0/20** for `stage_route`. **These are not
manuscript claims:** `MANUSCRIPT.md:195` scopes the end-to-end / injection-exposure arm out of the paper
and makes no claim about it. They are enforced because this packager was contracted to re-derive them;
a reader must not read them as manuscript numbers.

## Closure: the record is one file, proved by cutting

The checker was run on progressively smaller author-side copies of the closure — cuts of the shipped
tree whose per-cut logs are not part of this deposit:

| cut | contents | apparent bytes | checker exit |
|---|---|---|---|
| `c0-all4` | rows + summary + report + provenance | 2,327,290 | **0** (49/49) |
| `c1-rsg` | rows + summary + report | 2,295,611 | **0** (49/49) |
| `c2-rs` | rows + summary | 2,272,020 | **0** (49/49) |
| `c3-r` | **rows alone** — the minimal closure | 2,267,742 | **0** (49/49) |
| `c4-mincols` | rows reduced to the columns `CLAIMS.md`'s rule names (`mode`,`ptok`,`ctok`,`gold`,`pred`,`err`) | 847,714 | **1** — first break |
| `c5-gateonly` | rows trimmed to the gate modes (drops `stage`/`router`/`e2e`) | 2,137,573 | **1** |

**First break: `c4-mincols`, exit 1, literal first failure line:**

```
  [FAIL] rows_sha256                                  published='5732766d67d533a2' recomputed='6d23b25538a0f037'     CLAIMS.md R
```

*(Both digests are the pass-0 recorded output of the cut-ladder experiment, superseded by later
`answer` neutralisation on both sides of the comparison; the failure the ladder establishes — that
`rows_sha256` is the first thing a reduced cut breaks — is unaffected.)*

The byte-identity of the record is the first thing broken, and it is not the only thing: the same cut
also breaks the `calls` column, because **`calls` is not a row** — it is the number of `(task, batch)`
groups recorded in the `tag` field (gate16/gate90 tags carry a `"<batch>:"` prefix, gate1 tags do not):

```
  [FAIL] calls[gate16_none]                           published=120                recomputed=None                   MANUSCRIPT.md:137
```

`c5-gateonly` additionally breaks `rows_total` (9,260 → 9,000). So the closure is exactly
`gated-read-rows.jsonl` as shipped, byte-identical, with its `task` and `tag` columns; every cut below
that breaks immediately. The summary, report and provenance are shipped as records, but **they are not
needed by the recomputation** — proved by cut `c3-r` passing with the rows alone. The `stage`, `router`
and `e2e` rows are load-bearing for the two RUN-REPORT-ONLY checks even though the manuscript does not
report that arm.

## Sources, pinned by digest

`results/gated-read-summary.json` and `results/GATED_READ_PROVENANCE.md` ship byte-identical to the
pinned source material the run read from (`cmp` clean). **Two shipped record files are not
byte-identical to that source tree, and this is the complete list of what was neutralised:**

* `data/gated-read-rows.jsonl` — **six `answer` values** were replaced, at equal length, by neutral
  identifiers: four R5 trace identifiers (pass 1) and two uppercase target-project sentinels (pass 2).
* `results/GATED_READ_2026.md` — **one prose word** (pass 3): the target project's own name, in a
  sentence on how the measurement becomes a project artefact, replaced by the equal-length token
  `Corpusfile`.

**Nothing else was neutralised.** No `mode`, `arm`, `ptok`, `ctok`, `ctx_has_a/b`, `gold`, `pred`,
`task`, `tag`, `err` or `hit` value was touched, and no published number, byte count or line count
moved: `data/gated-read-rows.jsonl` is still **2,267,742 bytes, 9,260 lines** and
`results/GATED_READ_2026.md` is still **23,591 bytes, 340 lines**. That source tree is not part of
this deposit; the digests of the bytes shipped here are listed below.

| source | bytes | md5 | sha256 |
|---|---|---|---|
| `gated-read-rows.jsonl` | 2,267,742 | `20727b5c6bed2db935c14bf2e076340f` | `184ab747e87f7d127005ce08316dcde640ae93e5278bb1bd57bf353e23d9c44f` |
| `gated-read-summary.json` | 4,278 | `9bba213e4772692a7eccc7cf13715202` | `496666c44db9b256eaa9539b099c80b3be9c1aee538fe54f055575fffc39c67f` |
| `GATED_READ_2026.md` | 23,591 | `2df66834d3a54bee28da9b78d63855cb` | `c5a054030905944ca5e79ea27ed1310d9fb0ee91a0ba03559a077a87b2e1246d` |
| `GATED_READ_PROVENANCE.md` | 31,562 | `ae14de1721fecacad8e0750da20d2bce` | `cfc81ef63a4e2d4069409fdb897bb8b586e8d0fa9b5b6dd41f36bd7bbd40dd14` |

`CLAIMS.md` records the rows file and **2,267,742 bytes, 9,260 lines, md5 `3aad1ae29e472ef9f5f54e179510faf5`** — the digest as
measured on the pinned source tree (2026-10-15). **Re-measured here: md5 `bc2b2a5a36f331a621437cdf328d0d77`, sha256 `e877d05eb3a06069b7cc35b4ffb5fc06e150b6a3b79efd4a9d7f4a3939da47cb`**
— see the dated notes below. The shipped digest is now md5 `20727b5c6bed2db935c14bf2e076340f`, sha256 `184ab747e87f7d127005ce08316dcde640ae93e5278bb1bd57bf353e23d9c44f` (pass 3).

**Dated note (2026-10-19, pass 1).** Four rows of `data/gated-read-rows.jsonl` — one per R5 arm (`selfselect`, `gate_min`, `stage`, `stage_route`; `mode=e2e`, `task=T10`) — carried the run's
trace identifier in `answer`, which named the target project. It was replaced with the equal-length neutral identifier `2026-09-28-trace-m0`. The file was still **2,267,742 bytes and
9,260 lines**. Superseded digest: md5 `3aad1ae29e472ef9f5f54e179510faf5`, sha256 `5732766d67d533a2b2e2ddce50d04bcb34a2480f70e1087fdee5754cacc35223`; pass-1 digest: md5 `93acbf2e5399e9bc42ac7e84a6b5848e`, sha256 `b063fbae534a8e5f6649e6b36a21f12b2c40f95c8b0a36b290ad1adf650de809`.

**Dated note (2026-10-19, pass 2).** Two further rows (`mode=e2e`, `task=T17`, arms `selfselect` and `stage`) carried the target project's name in **uppercase** in `answer` (the target project's name in uppercase, 21 characters) — pass 1 swept case-sensitively and missed them. They are replaced with the equal-length neutral identifier `HOSTED_LAYER_CHECK_OK` (21 characters); the file is still **2,267,742 bytes and
9,260 lines**. Superseded digest (pass 1): md5 `93acbf2e5399e9bc42ac7e84a6b5848e`, sha256 `b063fbae534a8e5f6649e6b36a21f12b2c40f95c8b0a36b290ad1adf650de809`.

**Dated note (2026-10-19, pass 3) — the target project's own name.** A case-sensitive census of the
package found the target project's own name (ten ASCII characters, uppercase) **437 times on 225
lines**: 436 in `data/gated-read-rows.jsonl` (`tag` 206, `file` 206, `staged[]` 3, `hit[]` 1,
`paths[]` 17 — the two corpus paths it records as `<NAME>.md` and `docs/<NAME>_PLAN.md`) and 1 in
prose at `results/GATED_READ_2026.md:327`. Every occurrence was replaced by the equal-length neutral
token `CORPUSFILE` (`Corpusfile` in the prose sentence, matching its case): ten characters to ten
characters, so `data/gated-read-rows.jsonl` is still **2,267,742 bytes, 9,260 lines** and
`results/GATED_READ_2026.md` is still **23,591 bytes, 340 lines**. Superseded (pass 2): rows md5
`bc2b2a5a36f331a621437cdf328d0d77`, sha256 `e877d05eb3a06069b7cc35b4ffb5fc06e150b6a3b79efd4a9d7f4a3939da47cb`;
report md5 `fe1b900525c63ad0c1ee546d23370c6e`, sha256 `17ac3c4eeeb6ac47188fe74424aebf3fff382ba7c6bf5e186a550565cbc9b431`.
Shipped now: rows md5 `20727b5c6bed2db935c14bf2e076340f`, sha256 `184ab747e87f7d127005ce08316dcde640ae93e5278bb1bd57bf353e23d9c44f`; report md5 `2df66834d3a54bee28da9b78d63855cb`, sha256 `c5a054030905944ca5e79ea27ed1310d9fb0ee91a0ba03559a077a87b2e1246d`. This closes gap **G-23**
(`GAPS.md`) — the manifest rename the release contract deferred has been performed. The literal string is not
reproduced anywhere in this package, so a reader cannot recover it from these notes.

No published number is computed from the `answer` field (the shipped checker reads `mode`,
`arm`, `ptok`, `ctok`, `ctx_has_a/b`, `gold`, `pred`, `task`, `tag`, `err` — never `answer`
or `hit`).

**Dated note (2026-10-19) — `GATED_READ_PROVENANCE.md` row corrected.** The row above previously
stated `31,679` bytes / md5 `ba9f78dde8e6f117128347706f7c0fa4` / sha256 `0aca7cdb63dd9dcb5eb8c7af20618094b24eeeb7da7deb2fd2dd93754ccfa31d`;
those values do not match the shipped file, measured `31,562` / `ae14de1721fecacad8e0750da20d2bce` /
`cfc81ef63a4e2d4069409fdb897bb8b586e8d0fa9b5b6dd41f36bd7bbd40dd14`.

## Licence

`LICENSE` is the **PolyForm Noncommercial License 1.0.0** ("Required Notice: Copyright 2026
Aswin-Ram-K"). Its scope section describes this deposit; the official licence body above that section
is unmodified (its digest is recorded inside the file). `COMMERCIAL.md` (md5
`5c50b0c68848c6103856c1ad47d2d74f`) and `CONTRIBUTING.md` (md5 `0d234a26b48fba65978f76fee6d3de27`)
carry the commercial and contribution terms.

`MANIFEST.json` is generated by the project's manifest generator, never by hand (author-side tooling
that does not ship). Per that tool's convention, `counts.files` **includes** `MANIFEST.json` while
`counts.bytes_total` **excludes** it.

## Recorded disagreement with the packaging card

The unit card states that `MANUSCRIPT.md` carries "the **15.279×** token ratio" and "the **exposure
0/20**" as numbers the checker must re-derive. **It does not.** `MANUSCRIPT.md:195` explicitly scopes
the end-to-end / injection-exposure arm out and states that the paper "makes no claim about downstream
task accuracy, context-cost reduction, or injection exposure"; the strings `15.279` and `exposure 0/20`
do not appear in `MANUSCRIPT.md`. `15.279` is the run report's cost ratio
(`GATED_READ_2026.md:206`, errata: "the measured value is 15.3× (21 872 / 1 432)") and `0/20` is the
`stage_route` payload-reached-context column (`GATED_READ_2026.md:199`). Both are re-derived and
enforced here under the RUN-REPORT-ONLY label.
