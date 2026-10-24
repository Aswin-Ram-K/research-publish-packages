# UNIT UGATEDREADME — restore loose released/README.md to byte-identical with its in-archive twin

**Purpose (single):** remove the loose-vs-in-archive README divergence in `papers/gated-read-batching/released/`
by copying the archive's own `README.md` over the loose copy. Archive and `SUPERSEDED-UNPACKED.md` untouched; nothing deleted; no hand edits.

**Bound:** 6 tool calls (used 3). **Write paths:** `papers/gated-read-batching/released/README.md`,
`scratch/ugatedreadme/**`, `orchestration/units/UGATEDREADME.md`, `orchestration/handoffs/UGATEDREADME.json`.
**Forbidden:** touching the archive; any `git` command against any target repo; deleting anything.

## Method
1. `tar -tzf` the archive, extract member `gated-read-batching-released/README.md` to
   `scratch/ugatedreadme/inarchive/` (before-state recorded).
2. `cp` the extracted file over the loose copy — no hand editing.
3. Verify: `cmp` exit 0; archive size/md5 unchanged; `SUPERSEDED-UNPACKED.md` sha256 unchanged.

## Result: DONE
| item | before | after |
|---|---|---|
| loose `README.md` | 1787 B, sha256 `852ded3585efe4c92472beb26a26d5c7d4737c0bcdbdb63b11e4fb3c2e549a88` | 14170 B, sha256 `a453041e21c7a4cda37e5ce5fbb718ec9ea92c28c94fc762dbddda402663a39d` |
| in-archive `README.md` | 14170 B, sha256 `a453041e21c7a4cd…39d` | unchanged |
| `gated-read-batching-released.tar.gz` | 128902 B, md5 `a7e81bf7c8ebe49da83e869a002be1b2` | unchanged |
| `SUPERSEDED-UNPACKED.md` | 2625 B, sha256 `c416e56262abcde7…ba3` | unchanged |

`cmp` loose vs in-archive: **exit 0**. Pre-copy it exited 1 (`differ: byte 27, line 1`).

## Correction to the unit card's premise
The card described a +132-byte tail annotation (in-archive 1,655 B). Measured in-archive is **14,170 B** and the
divergence starts at byte 27 of line 1: the loose file was a *different* 25-line directory-index README for
`released/`, not the package README with an appended note. The stated **digests** were correct and matched exactly.

## Residual risk
The overwritten directory-index text is the only thing not preserved in full; it survives partially in
`scratch/ugatedreadme/diff-before.txt` (captured with `head -40`, truncated). If that index role is still wanted,
it belongs in `SUPERSEDED-UNPACKED.md` or its own file — not back in `README.md`, which is the divergence class this
workspace keeps getting bitten by.
