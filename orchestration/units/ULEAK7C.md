# ULEAK7C — case-insensitive leak sweep + deposit-archive repair (§7)

Parent: session-c3d61727-8af8-4c19-b1b9-5922c347a11a · Bound: 30 tool calls (used 22). Status: **done** with one
deliberate non-application and two recorded disagreements.

## JOB 1 — case-insensitive sweep (before any change)
Patterns: `duval` (ci, all case forms), the trace id `2026-09-28-duval-m0`, the host name `CODEX`,
internal unit ids `\bU[A-Z]{2,}[0-9][A-Z0-9]*\b` (ci), plus workspace-name/path probes.
Hits before the fix (package / archive extraction / paper):
- `data/gated-read-rows.jsonl:9235`, `:9239` — `"answer": "DUVAL_HOSTED_LAYER_OK"` (the leak; uppercase → both
  earlier sweeps missed it).
- `scratch/upkg7b/clean/` and the stale `scratch/upkginstall7/verify/extract/` still carried the pass-1 trace-id
  answers and a `README.md:107` path — both are superseded, non-shipped intermediates (reported, not shipped).
- `unitid` zero in every shipped surface; `CODEX` hits are the **literature's** OpenAI Codex in
  `results/GATED_READ_PROVENANCE.md:47,198`, not the host.

## JOB 2 — equal-length neutral replacement
`DUVAL_HOSTED_LAYER_OK` (21) → **`HOSTED_LAYER_CHECK_OK`** (21). Reasoning: it names what the value is (the task's
expected sentinel — the same row's own `paths` already name `tests/hosted-layer.ts`) and carries no project
provenance; exactly the pass-1 convention (`2026-09-28-<name>-m0` → `2026-09-28-trace-m0`). Applied at rows
9235/9239 only. File still **2,267,742 B / 9,260 lines**; new string exactly 2×; old string zero in every case
form across package, archive and paper. Checker unaffected — it never reads `answer`.

## JOB 3 — three document defects
1. README PROVENANCE row `31,679 / ba9f78dd… / 0aca7cdb…` → measured `31,562 / ae14de17… / cfc81ef6…`, superseded
   values kept as a dated note.
2. Both "What ships" tables (`README.md`, `README_DEPOSIT.md`) now list all **12** files, the 2 extras marked as
   deposit metadata added by the recipe.
3. The `+792 B` figure is the **compressed** archive delta; raw additions were `README +1,188`, `recompute-claims.py
   +239`, `MANIFEST.json +1` = **+1,428 B raw** (from `orchestration/units/VPKGFINAL7.md:28`). Recorded in
   `DISCLOSURE_CHANGES.md` Pass 5. The site that originally carried only the compressed figure is
   `orchestration/units/ULEAK7B.md:104-105` — **outside my declared write paths**, so it stands; flagged instead.

## JOB 4 — digests, regenerate, rebuild, re-prove
Digest sites updated: `verify/recompute-claims.py` (`ROWS_SHA256`), package `README.md`, `CLAIMS.md` (claim R,
pass-2 dated note), `DISCLOSURE_CHANGES.md` Pass 5, recipe pins in `build_archive.sh`
(`want_pkg_manifest`, `want_rows`, `want_front`) + a dated re-pin note. `MANIFEST.json` regenerated with
`tools/package/regen_manifest.py` (never hand-edited). Archive rebuilt through `build_archive.sh` from a copy
(probe `scratch/uleak7c/build_probe.sh`, output in `scratch/uleak7c/probe/`) and then installed.

Rows digest: md5 `bc2b2a5a36f331a621437cdf328d0d77`, sha256 `e877d05eb3a06069b7cc35b4ffb5fc06e150b6a3b79efd4a9d7f4a3939da47cb`.

**Installed archive — the digest changed again:**
| | value |
|---|---|
| superseded (ULEAK7B) | `126,639 B` / `0e70ba54188d87fd8d92ab237bede3186358b3ae67bc421f54020a61b99b6a85` / `e2af1616b64f7ca54b9bf61e60427785` |
| **now shipped** | **`127,300 B`** / **`1cfbd15b6f4dccbcf85b02f93971f6c44b405a4e071df516d9b372d4f121d86b`** / **`8e66f1929db1eae6838b19f5a60a4841`** |

Proof on the installed extraction: `check_manifest.py --package <ABS>` 5 counters 0 + `VERDICT PASS` + exit 0;
`recompute-claims.py` exit 0, **49/49 PASS**; red→green flip of one byte → exit 1
`[FAIL] rows_sha256 published='e877d05eb3a06069' recomputed='a7ac8588b31e3005'`, restore → exit 0 and the original
digest; three builds (probe + two real) all `1cfbd15b…`, 16 members / 12 files / one top dir.

## Parent's mid-flight additions (folded in)
**1. `consonance` — measured, classified, demonstrated, NOT applied (recommendation).** Payload count **437 / 225
lines**: 436 in `data/gated-read-rows.jsonl` (224 lines) + 1 prose in `results/GATED_READ_2026.md:327`. In the rows,
by key: `tag` 206, `file` 206, `staged[]` 3, `hit[]` 1, `paths[]` 17 — 10 distinct values (`docs/CONSONANCE_PLAN.md`,
`CONSONANCE.md`, and `0:`-prefixed tags). Only `tag` is read by the checker (the `calls` grouping); `file`/`paths`/
`staged`/`hit` are not. Experiment in `scratch/uleak7c/consexp/`: replacing all 436 with the equal-length
`CORPUSFILE` keeps **49/49 PASS, exit 0**, leaves byte/line counts unchanged, and leaves every `calls[…]` line
byte-identical; the **only** diff is the rows digest. **Not applied**: it would rewrite shipped *run records*
(`file`/`tag`) rather than an accidental canary value, falsify the README's "same source bytes except six `answer`
values" provenance sentence, and overturn the authors' recorded open gap G-23 — an author decision, not mine. The
demonstration means a one-cycle apply is cheap if the parent orders it.
**2. The README leak (`papers/gated-read-batching/released/README.md:11,15`).** **Never applied — not a
regression, not rebuilt.** My JOB 1 pattern set (target name/trace/host/unit ids) never contained internal
workspace paths, so that class was outside this unit's card; the file is author-side (outside the 12-file archive)
and `build_archive.sh` never rewrites it. Same class inside the shipped tree: **zero** in package, payload and
extraction (`scratch-path` sweep); the surviving instances are paper-side `DISCLOSURE_CHANGES.md` records.
**3. Judgements.** `GATED_READ_PROVENANCE.md:7` (`DEEPSEEK_API_KEY missing`) names an environment **variable name**
in a method note, never a value — ordinary tooling detail, not a disclosure. `rows:9028` `keyring` is one of three
`terms` a `router` row grepped for in `docs/BACKLOG.md` — a search term, not key material.
**4. Untouched** as instructed: every other paper's `released/`, and all of `papers/encoder-crossover-190/`.

## Disagreements with the card (not smoothed)
- JOB 3.3's "change record" site is `orchestration/units/ULEAK7B.md` — outside my write paths; I recorded both
  deltas in `DISCLOSURE_CHANGES.md` Pass 5 instead of editing another unit's card.
- JOB 1's pattern list did not include internal workspace paths, which is why the `released/README.md` hits were
  missed; the card's "the lesson is case sensitivity" is true but incomplete — **path and prose classes** were also
  outside the sweep.
- The card's "exactly 2,267,742 bytes and 9,260 lines" held; no published number moved (49/49 PASS throughout).
