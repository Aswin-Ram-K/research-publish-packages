# UARCHGUARD1 — make the Zenodo re-upload impossible to get wrong

**Status:** done
**Bound:** 25 tool calls (used 10). No stop condition hit.
**Write paths (declared):** `scratch/archguard1/**`, `scratch/_superseded-archives/**`,
`orchestration/units/UARCHGUARD1.md`, `orchestration/handoffs/UARCHGUARD1.json`.
**Read-only, untouched:** `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`
(sha256 still `bcdbf75e…`, mtime `2026-10-18 03:22:41 -0500`, i.e. unchanged since before this unit ran),
`/home/zer0null/Duval`, any git index.

## Why

The author uploaded a superseded 158,762-byte archive instead of the intended 158,956-byte one, so the
public `CONTRIBUTING.md` is the *"DRAFT — template for the author to place."* notice. Six non-canonical
archives existed under three digests, none git-tracked, one of them at a scratch path that merely *looks*
canonical (`scratch/vdeposit2/root/papers/.../released/…`).

## Measured inventory (re-measured, not taken from the card)

`find . -name node_modules -prune -o -name '*encoder-crossover-190-released*.tar.gz' -print | sort`
returned **7 files / 3 distinct digests** — the card's table matches byte-for-byte, but the card's prose
says **"six"** archives; the correct count is **seven**. Disagreement reported.

| bytes | md5 | sha256 | path | verdict |
|---|---|---|---|---|
| 158956 | `77a757006802600e3026b02f4494dc3d` | `bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2` | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | **CORRECT** |
| 158956 | same | same | `scratch/ufixdep2/build/encoder-crossover-190-released.tar.gz` | duplicate of canonical; moved (path rule) |
| 157650 | `1005a7e15ded3502177aaf9f07867c50` | `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` | `scratch/ufixman1/prev-encoder-crossover-190-released.tar.gz` | SUPERSEDED |
| 157650 | same | same | `scratch/uplace2/rev/released/encoder-crossover-190-released.tar.gz` | SUPERSEDED |
| 158762 | `42be2211728254f8c8799d256b464987` | `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` | `scratch/vdeposit1/prev-encoder-crossover-190-released.tar.gz` | SUPERSEDED — **the uploaded digest** |
| 158762 | same | same | `scratch/vdeposit2/root/papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | SUPERSEDED (looks canonical) |
| 158762 | same | same | `scratch/vdeposit2/root/scratch/ufixdep2/build/encoder-crossover-190-released.tar.gz` | SUPERSEDED |

## Proof by extraction (not by name or size)

Each distinct digest was `tar xzf`-ed to `scratch/archguard1/extract/<md5-12>/`:

- `77a757006802` → `CONTRIBUTING.md` sha256 `3b5e59622b3e4b7d4b9326101b615bcef484ddd80b31b78306ba416698a87996`, head blockquote *"Released research artefact."*; its `MANIFEST.json` `files[2]` entry records the identical sha256 (`bytes: 3547`). → **CORRECT**
- `1005a7e15ded` → `CONTRIBUTING.md` sha256 `dd8b8ee416c2bc79b6f4da5502aa6dce258ae8e128f2c901d4fbe5b103fab45b`, head blockquote *"DRAFT — template for the author to place."*; manifest `files[1]` records the same (`bytes: 3036`). → **SUPERSEDED**
- `42be22117282` → same DRAFT `dd8b8ee4…` / 3036 B; manifest `files[2]` records it. → **SUPERSEDED** (this is what reached Zenodo)

## Actions taken

1. Quarantined **all six** non-`papers/` archives into `scratch/_superseded-archives/`, flattened as
   path-derived names (`scratch__vdeposit1__prev-encoder-crossover-190-released.tar.gz`, …). Moved, never
   deleted; `scratch/archguard1/moved.tsv` and `scratch/_superseded-archives/README.md` map every moved
   file to its original path, size, md5, sha256 and reason.
2. Left exactly one archive outside the quarantine dir — the canonical `papers/…` file.
3. Guard `scratch/archguard1/check_upload_candidate.sh`: requires exact path, size 158956 and sha256
   `bcdbf75e…`; prints size/sha256/md5; exit 0 GREEN, 1 RED.
4. `scratch/archguard1/UPLOAD_NOTE.md`: one path, size, sha256, md5, and the single rule *upload only from
   `papers/`, never from `scratch/`*.

## Evidence

- Guard RED on the uploaded stale digest: `[X] path …`, `size : 158762 bytes (expected 158956)`,
  `sha256 : 956d6363…` → `RED — REFUSE: do NOT upload this file.` exit 1.
- Guard GREEN on canonical: `[ok] path`, `158956`, `bcdbf75e…` → `GREEN — canonical archive confirmed.` exit 0.
- Guard RED by **path alone** on the byte-identical duplicate (size and sha256 both match) — proves the
  single-source rule is enforced even when bytes are right.
- `python3 tools/package/check_manifest.py --package "$PWD/scratch/archguard1/canon/encoder-crossover-190-released"`
  → `missing=0 hash_mismatch=0 … VERDICT PASS`, exit 0 (absolute `--package` used as required).
- `(cd "$ROOT" && python3 verify/recompute-claims.py)` → `ALL PUBLISHED NUMBERS REPRODUCED: True`,
  `VERDICT: PASS`, exit 0.

## Blocker

None. `next_unit_hint`: a verifier can re-run the three guard invocations and both checkers; the only
caveat is `scratch/archguard1/extract/` and `scratch/archguard1/canon/` are throwaway extractions and may
be deleted at will.
