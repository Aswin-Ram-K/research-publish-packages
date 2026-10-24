# UDEPOSIT2 — Released-artifact hazard removal and deposit re-freeze

## Purpose
Remove the last hazards and inaccuracies from the released-artifact area of the encoder-crossover-190
deposit, then re-freeze the archive only if something that ships inside it changed.
**Nothing is published and nothing is uploaded.**

## Hard bound
25 tool calls. If a rebuild is needed and two-build byte-identity cannot be achieved, STOP and report
the blocker.

## Write paths (nothing else)
- `papers/encoder-crossover-190/released/**`
- `scratch/udeposit2/**`
- `strategy/DEPOSIT_ARCHIVE.md` (append only)
- `orchestration/units/UDEPOSIT2.md`
- `orchestration/handoffs/UDEPOSIT2.json`

## Do NOT
- Modify `scratch/uneutral10/package/**` or `papers/*/submission/**`.
- Delete anything — move and mark instead.
- Call any network API.
- Put any credential, token or ORCID in any file.
- Write outside the listed paths.

## Baseline facts (given, verified on disk before start)
- Good archive: `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`
  157,305 B, sha256 `778818b242922fc1afde984b27c0dfb7c79be7647b6f5146269b1c2ec2026bdb`, 37 members.
- Recipe: `tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 … | gzip -n -9`
- Payload `scratch/uneutral10/package/` = 29 files + 2 extras `CITATION.cff`, `README_DEPOSIT.md`.

## Tasks
1. Move stale unpacked tree `papers/encoder-crossover-190/released/encoder-crossover-190-released/`
   to `scratch/udeposit2/superseded-unpacked-tree/`; leave dated note
   `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md`.
2. Verify "30 of the 31 files" claim in shipping `README_DEPOSIT.md`; correct if false; state measured numbers.
3. Make the two extras unambiguous (top-level `DEPOSIT_README.md` or extend `README_DEPOSIT.md`).
   Do NOT modify the 29 package files.
4. Rebuild tarball with recorded recipe iff a shipping file changed; build twice, prove byte-identity.
5. Re-run soundness checks: manifest checker on payload and archive; three shipped tools in extracted tree.
   Report every literal exit code.
6. Report final archive path, size, sha256, member count, `diff -r` inputs vs extraction.

## Status
in progress
