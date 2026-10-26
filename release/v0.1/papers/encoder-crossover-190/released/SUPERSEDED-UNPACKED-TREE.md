# SUPERSEDED — unpacked packaging tree removed from this directory

**Dated:** 2026-10-17 (UDEPOSIT2)

## What was here

`papers/encoder-crossover-190/released/encoder-crossover-190-released/` — an **unpacked directory
tree** of a third, older packaging variant of the same deposit, sitting beside the shippable tarball
under the same name stem. It held **31 files**, all of them superseded:

| file | sha256 | why it is stale |
|---|---|---|
| `COMMERCIAL.md` | `ca86a625288ac6fd9e3ae0ca9ee2a94acf3001891e5d30f347a686a975b5b9d6` | **pre-licence-fix bytes** (3,512 B); the corrected file is 3,520 B |
| `README_DEPOSIT.md` | `b10762bdb746fe8c90cf92f3aa8b548b3e51c9a4390bccfdc3eba0590b7b737f` | superseded wording; claimed a `30 of the 31 files` manifest that does not describe the shipped archive |
| `MANIFEST.json` | `421d18b336fe9cfadd1f73cac0224bd6ac1a62d12621797195c31663dbd69218` | older `counts.files = 31`, `manifest_self = 89ef383627e2e774b01bcbb8f1afdb96ccbe260e8a4fec99e746467b7a6f14be`; enumerated `CITATION.cff` + `README_DEPOSIT.md`, a policy the shipped archive does **not** use |

## Why it was moved

It shared its name stem with the shippable tarball (`encoder-crossover-190-released`). Anyone who
zipped that directory — or unpacked the tarball next to it and picked the wrong entry — would have
shipped the **pre-fix licence bytes** (`ca86a625…`) instead of the corrected `COMMERCIAL.md`. It was
moved, not deleted, so the superseded bytes stay auditable.

Moved to: `scratch/udeposit2/superseded-unpacked-tree/` (31 files, unchanged; per-file digests in
`scratch/udeposit2/superseded-unpacked-tree.sha256`, 31 lines).

## What the correct archive is

| field | value |
|---|---|
| path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` |
| bytes | 157,305 (as of 2026-10-17 17:04 UTC) |
| sha256 | `778818b242922fc1afde984b27c0dfb7c79be7647b6f5146269b1c2ec2026bdb` |
| members | 37 = 1 top-level dir + 5 subdirs + 31 files (29-file package + `CITATION.cff` + `README_DEPOSIT.md`) |
| inputs | `scratch/uneutral10/package/` (29 files) + `scratch/uzenodo2/run2/CITATION.cff` + `scratch/uzenodo2/run2/README_DEPOSIT.md` |
| recipe | `tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 -C <stage> -cf - encoder-crossover-190-released \| gzip -n -9` |

`strategy/DEPOSIT_ARCHIVE.md` is the spec of record for this archive.

---

## 2026-10-19 — two more unpacked trees moved (unit UTREES1)

Two unpacked copies had reappeared in this directory, both **byte-identical to the archive's tree at
the time of moving** (verified by `diff -rq` against a fresh `tar -xzf` of the archive — empty output;
31 files, 856,779 bytes each). Neither was stale, and that is precisely why they were retired: nothing
in this workspace keeps an unpacked copy in sync, and two earlier passes mistook a stale copy for the
live one.

| tree as it sat here | moved to | state at move |
|---|---|---|
| `encoder-crossover-190-released/` | `scratch/utrees1/superseded-unpacked/encoder-crossover-190/encoder-crossover-190-released/` | identical to archive tree (31 files, 856,779 B) |
| `encoder-crossover-190-released (2)/` (name kept a space and a `(2)`) | `scratch/utrees1/superseded-unpacked/encoder-crossover-190/encoder-crossover-190-released-2/` | identical to archive tree (31 files, 856,779 B) |

The `(2)` suffix did not survive as a bare filename fragment: the space was replaced, yielding
`encoder-crossover-190-released-2`. Each destination holds the full tree unchanged plus a per-file
manifest beside it, `<tree-name>.sha256` (31 entries each), verified with `sha256sum -c` (31/31 OK).

**Moved, not deleted.** The trees were not modified in the move.

### Authoritative artifact (measured 2026-10-19, this workspace)

| field | value |
|---|---|
| path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` |
| bytes | 159,182 |
| md5 | `b4dac172003233d7d6c8c78c909b5594` |
| sha256 | `dbbf7b1a7e8a7884a89b17bf9fecce7e364a0afdbefe4b7c74524bc13a9b1877` |

The 157,305-byte / `778818b2…` figure recorded above is the 2026-10-17 generation of this archive and is
historical only — the archive has since changed (licence/CITATION corrections). Compare against
159,182 B / md5 `b4dac172…` when deciding which artifact is authoritative today.

This directory now contains only that archive plus `README_DEPOSIT.md` and this file.
