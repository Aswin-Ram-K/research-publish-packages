# replay-record-not-decision — released data and verification tooling

## What this is

This is the **released data and verification tooling** for the paper

> *Replay reproduces the record, not the decision*

by **Aswin Ram Kalugasala Moorthy** (2026). It is the deposit-level front matter for the archive; the
per-directory detail lives in `README.md` and `MANIFEST.json`.

## What this is not

- **The harness is withheld.** There is no `harness/` directory and no runner. The code that produced
  the records — the replay instrument, the model adapters, the collection and analysis pipeline — is
  deliberately not distributed, nor are any model weights (`laya`, `decider-0.8b`, `decider-2b`,
  `decider-4b` are named in the records; none of them ships).
- **The checks here do not retrain or re-render anything.** They re-derive the published numbers
  **from the stored records** in this package. They read bytes that ship with the deposit; they do not
  regenerate a model input, run an arm, or re-run the evaluation pipeline.
- **This is not a reproduction package.** A reader cannot re-run the measurement from this deposit
  alone. What is verifiable here is that the shipped records are internally consistent with the
  published numbers.
- **This is not the paper text.** The paper manuscript is a separate work under **CC BY 4.0**.

## What ships

| path | contents |
|---|---|
| `data/decision-variants.jsonl` | 1,197,797 B / 3,040 rows — 4 models × 190 cases × 4 recorded variants |
| `data/l1-head-to-head.jsonl` | 63,238 B / 380 rows — the same 190 cases, two models |
| `verify/recompute-claims.py` | re-derives every published number from the bytes in this package |
| `README.md` | the package's own README: schema trap, correspondence, cut ladder, census |
| `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `MANIFEST.json` | licence, commercial terms, contribution terms, integrity manifest |

Both record files are shipped **byte-identical to source** (`identical_to_source: true` in
`MANIFEST.json`); no row, field or byte is added, removed or renamed. **The stimulus fixture is not in
this package** — see "The stimulus fixture is not here" below.

## How to use it — the exact checks and their expected output

Standard-library-only Python 3; no third-party dependencies, no network, no GPU. Run each command from
the top of the extracted directory (the directory holding `verify/`).

### 1. Re-derive the claims

```bash
python3 verify/recompute-claims.py
```

Expected: **exit status `0`** and a tail reading

```
CHECKS: 30/30 passed
ALL PUBLISHED NUMBERS REPRODUCED: True
VERDICT: PASS
```

Before that it prints, per check, a `[PASS]` line and the measured value, including: the V0 binding
divergence **476/1,140 = 41.7544 %**; the per-variant rates **41.7544 / 47.1053 / 40.0000 / 43.3333 %**;
the non-decomposable replication control **244/244 identical** for both V0↔V2 and V1↔V3; prompt-level
**245/760 = 32.2368 %**; `l1` **98/190 = 51.5789 %**; outcome divergence **324/1,140 = 28.4211 %**; and
the `correct`-column trap side by side (summing `correct` as a flag gives `1.0632` where the truth is
`0.4500`). **Every check is folded into the exit status** — `VERDICT: PASS` and exit `0` are the same
event, and any failure exits non-zero naming the claim that failed.

### 2. Re-hash the manifest (9 of 10 — this tree's `files[]`, itself exempt)

Run this at the top of the **extracted archive**:

```bash
python3 - <<'PY'
import hashlib, json, os
m = json.load(open("MANIFEST.json"))
bad = []
for e in m["files"]:
    h = hashlib.sha256(open(e["path"], "rb").read()).hexdigest()
    if h != e["sha256"] or os.path.getsize(e["path"]) != e["bytes"]:
        bad.append(e["path"])
print("MANIFEST checked:", len(m["files"]), "files; mismatches:", bad or "none")
PY
```

Expected: `MANIFEST checked: 9 files; mismatches: none`. Run the same snippet at the top of the
author-side **package** tree (which has no deposit extras) and the expected line is
`MANIFEST checked: 7 files; mismatches: none`.

### Independent checker (author-side; not shipped)

The author's independent checker re-hashes every listed path and walks the tree for files the manifest
omitted. It exits non-zero if any of `missing`, `hash_mismatch`, `size_mismatch`, `unlisted`,
`listed_but_absent` is non-zero. That checker is author-side build tooling and **does not ship** with
the deposit, so it cannot be run from the archive; the inline re-hash above is the shipped equivalent
for a reader. The author ran it at the top of the **extracted archive**, which reported
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, then `VERDICT PASS`,
**exit `0`** — nothing in the archive is unlisted, deposit extras included. Run against the package
tree (author-side; not shipped), the same checker reported `VERDICT PASS`, **exit `0`**.

## The stimulus fixture is not here — and it is not withheld either

This deposit carries the two record files and the checker, and **no fixture**. The stimulus — the
questions, the option texts and the hand-authored labels — releases with the **companion note** on
Zenodo, concept DOI **`10.5281/zenodo.23463944`** (the companion release, paper #3); it is
**referenced here, not copied**.

That is a change from the earlier release boundary, which described the stimulus as withheld. The
correspondence is stated plainly in `README.md`: the companion fixture carries the **same 190 cases**
with the same per-kind counts (30/30/26/22/26/28/28) under a different neutralised tagging, and the tag
correspondence is recoverable from the data itself. The headline numbers do not depend on the fixture at
all — removing it from the tree leaves every number unchanged.

## Licence

The released artifacts — everything in this directory — are **source-available under the PolyForm
Noncommercial License 1.0.0** (see `LICENSE`), with a **paid commercial licence offered directly by the
author** (see `COMMERCIAL.md`). The PolyForm Noncommercial licence does not cover commercial use and
grants no commercial right. The **paper text is separately licensed CC BY 4.0**. The main project
repository remains **proprietary and closed**; nothing in this deposit is a grant of rights in it, and
the terms above grant **no rights in the withheld harness**.

## Integrity — what `MANIFEST.json` covers, and what it does not

**Package content vs deposit metadata.** The released *package* is **8 files**. The deposit *archive*
wraps that package in a single top-level directory and adds exactly **2 deposit-metadata files** on top
of it — `CITATION.cff` (the deposit-level citation) and this file, `README_DEPOSIT.md`. The archive
therefore ships **10 files**. Those two files are the **only** files in the archive that are not package
content; every one of the other 8 is byte-identical to the package. `README.md` is the package's own
README and ships unchanged.

**The two trees carry two different manifests under the same name.** They are the same file name
because each is the manifest of the tree it sits in:

| tree | `MANIFEST.json` describes | `files[]` entries | `counts.files` | self-exempt |
|---|---|---|---|---|
| the package tree (author-side; not shipped) | the package — its own 8 files | 7 | 8 | itself (`manifest_self`) |
| extracted archive root (the archive) | the archive — its own 10 files | 9 | 10 | itself (`manifest_self`) |

So the archive's manifest enumerates **9** entries: the 7 package entries plus `CITATION.cff` and
`README_DEPOSIT.md`. It does **not** enumerate itself — a self-referential sha256 is impossible — and it
carries its own digest in `manifest_self`; `counts.files` includes it, `counts.bytes_total` excludes its
own bytes. That is the same self-exemption convention the package manifest uses.

Both copies are fail-closed over the files on disk **in the tree that ships them**. The archive's copy
is the package's copy *regenerated after the archive tree is assembled* (see below) — regenerating it
inside the package would make it false of the archive, and regenerating it only in a staging tree that
is not shipped makes it false of both.

The two entries the regeneration *adds* (`CITATION.cff`, `README_DEPOSIT.md`) carry the generator's
explicit note that their source provenance was not established by that regeneration; they are deposit
metadata, not package content, and their digests are the ones on disk in the archive.

### How the archive is assembled (the ordering that makes this true)

1. Stage the package's 8 files into `<stage>/replay-record-not-decision-released/`.
2. Add the 2 deposit extras — `CITATION.cff` and `README_DEPOSIT.md` (this file) — to the stage.
3. **Regenerate `MANIFEST.json` in the stage**, with the project's manifest generator (`--package
   <stage>/replay-record-not-decision-released`, `--no-note` to match the shipped key set, and a pinned
   `--generated-utc` so the command is byte-idempotent). It now describes 10 files.
4. Pack deterministically:
   `tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 -C <stage> -cf -
   replay-record-not-decision-released | gzip -n -9 > replay-record-not-decision-released.tar.gz`.

Step 3 after step 2 is the whole fix: the archive's manifest is generated from the archive's own tree,
after that tree exists. The package's own `MANIFEST.json` is never written by this step and keeps
describing the 8-file package.
