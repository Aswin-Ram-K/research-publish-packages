# VERIFICATION REPORT — ENCFIX (encoder-crossover-190 published deposit archive)

Verifier: VENCFIX1 (independent; author of none of the work). Date: 2026-10-19.
Own extraction: `scratch/vencfix1/ext/` (from the shipped tarball) and `scratch/vencfix1/base_ext/`
(from `scratch/uencfix1/base/build/encoder-crossover-190-released.tar.gz`). Own builds under
`scratch/vencfix1/{build,red,adv}/`. The shipped artifact was never written; digest before and after
every build: `dbbf7b1a7e8a7884a89b17bf9fecce7e364a0afdbefe4b7c74524bc13a9b1877`.

## Verdicts

| # | Claim | Verdict |
|---|---|---|
| C1 | artifact identity 159,182 B / dbbf7b1a / b4dac172 / 37 members / 31 files | **PASS** |
| C2 | leak gone, case-insensitive, whole byte stream | **PASS** (stronger than stated: no unit-id-shaped token exists at all) |
| C3 | 29 payload files unchanged; only CITATION.cff + MANIFEST.json differ | **PASS**, one wording imprecision (fixture "digest") |
| C4 | check_manifest 5×0 + PASS/0; recompute-claims PASS/0 | **PASS** |
| C5 | guard live, shipped-byte gate narrowed; fresh build reproduces bytes | **PASS** (red exit 1 literal message reproduced; advisory gate proven at exit 0) |
| C6 | BUILD_NOTES.md:350 record true; no other line rewritten | **PARTIAL** — :350 verified true; "no other line rewritten" not independently provable from disk |

Overall: **pass**, with one unverified sub-claim (C6 second half) and one imprecise number description (C3).

## C1 — artifact (re-derived)
`stat`: 159,182 B. `sha256sum`: `dbbf7b1a7e8a7884a89b17bf9fecce7e364a0afdbefe4b7c74524bc13a9b1877`.
`md5sum`: `b4dac172003233d7d6c8c78c909b5594`. `tar -tzf | wc -l` = 37; non-directory members = 31;
directories = 6 (top dir + fixture, preregistration, results, second-labeller, verify).
Decompressed tar stream = 890,880 B. **Claim exact.**

## C2 — leak (re-derived, independent)
Over the full `gzip -dc` byte stream of the shipped tarball, case-insensitive, fixed-string:
`UDOIBACK1` 0, `UCONCEPT1` 0. Raw compressed bytes: both 0. Also 0: `scratch/`, `tools/package/`,
`/home/`, `/home/zer0null`. Regex `U[A-Z]{2,}[0-9][A-Z0-9]*` → **no matches at all**. Further probes, all 0:
`orchestration`, `dockets`, `strategy/`, `handoff`, `STATUS.md`, `PLAN.md`, `inbox`, `worktree`, `tmp/`,
`uencfix`, `ufix`, `zenodo2`, `uzenodo`, `zer0null`, `AGENTS`, `PUA`, `pid=`.
Note: all 31 members are text (md/json/ts/cff/py), so there is no binary member in which a leak could hide;
the check was nonetheless done on bytes, not on files.
Non-matches that look like hits but are scientific vocabulary: `neutral` ×2 (`NEUTRAL-TAG/v1` fixture tag;
prose "or is neutral"), `SUPERSEDED` ×30 across 13 members (fixture schema field "superseded evidence ref",
EVIDENCE.md, CITATION.cff version note) — **not** internal orchestration material.
**Claim exact.**

## C3 — nothing else moved (re-derived)
Base copy verified on disk: 159,185 B, sha256 `196f5311a9b5446af44bafdd688f00035e11f5ec2912f20233e5fa8feedc9a34`.
31 files on each side, identical names (`diff` of sorted name lists exit 0). Per-file sha256 diff: exactly two
lines —
`CITATION.cff` `32bee18fd38d476ba628512bdab8a6bb30c3b8879107cea674d007d92746841b` → `91a64a20819fdac13625ce3eacbc88447f098eed3c15fdc48b840758e96a53c6`;
`MANIFEST.json` `210dc61343cf4274fdf6215f1836201000da230e7dcd2490541a07c6104078b6` → `abfd6935c38fb82f3593aa2476aaac023971bb198f0367d276f17bb1ccf582d1`.
The other **29** payload files are byte-identical, including `fixture/fixture-190.json`.
No published number moved: `verify/recompute-claims.py` on my extraction reproduces every value
(0.3474 / 0.4526 / 0.2911 / 0.6684 quoted-constant / 0.6789, counts 39+27+90+34=190, kappa 0.8837 / 0.914 /
A/B 0.3684210526315789), plus route-A kappa 0.3252 and A/B 0.3684 against the tree.
**Imprecision (not a contradiction):** the "fixture digest `c7696edc…`" is *not* the sha256 of
`fixture/fixture-190.json` — that file's sha256 is `a15224bada6950ad27f693acd2287dec564134419061baa475f6716d2db3852e`.
`c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` is the derived *fixture correctness digest*
printed by recompute-claims.py; it is unchanged because the fixture bytes are unchanged. The claim is true of
the script's derived value, not of the file's digest.

## C4 — archive is sound (own clean extraction, `scratch/vencfix1/ext/encoder-crossover-190-released`)
`python3 tools/package/check_manifest.py --package <ABS>` →
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`,
`manifest_self_recomputes=True (blank generated_utc; drop manifest_self; sort_keys indent=2)`, `VERDICT PASS`, exit 0.
`python3 verify/recompute-claims.py` (run inside the extraction) → exit 0, `VERDICT: PASS`,
`ALL PUBLISHED NUMBERS REPRODUCED: True`. **Claim exact.**

## C5 — guard red→green (own copy, own inputs; real script untouched)
- Real script: sha256 `e6e5844e72aefe0465d05187f05a3405bfec8e85ac50c6c5051693a68e0715b2`, `want_cit="91a64a20…"` at :43.
- Green (real script, `BUILD_WORK=scratch/vencfix1/build`): bytes=159182, sha256 `dbbf7b1a…`, md5 `b4dac172…`,
  members=37, `cmp` against the shipped file **exit 0** ("BYTE-IDENTICAL"), build exit 0. Shipped digest
  unchanged before/after.
- Red (copy `scratch/vencfix1/build_archive_red.sh` with `want_cit` restored to `32bee18f…`):
  **exit code 1**, stdout empty, stderr literal:
  `CITATION.cff drifted: 91a64a20819fdac13625ce3eacbc88447f098eed3c15fdc48b840758e96a53c6`
- Narrowing still live (real script, `GENUTC=2026-10-19T04:14:51Z`): **exit 0** with
  `BYTE-DIFFERENT: build differs from the currently shipped file (advisory, not fatal)` — the shipped-byte
  gate is advisory, while the input pin stays fatal. Both halves of the claim hold.
**Claim exact** (the red message names CITATION.cff and prints the corrected source digest, so the pin is
comparing the corrected source, not a stale one).

## C6 — records (PARTIAL)
`papers/encoder-crossover-190/submission/BUILD_NOTES.md:350` is the released-archive row: it carries
**159,182 B**, sha256 `dbbf7b1a…`, md5 `b4dac172…`, "37 members / 31 files", and keeps the 159,185 B /
`196f5311…` / md5 `b3b30f66…` figures as dated history. `:350` is also the only line in the file that
mentions `UENCFIX2` (1 occurrence).
**"No other line in that file was rewritten" is not reproducible from disk:**
- the file is untracked in the workspace git repo (`git ls-files --error-unmatch` → not tracked), so no HEAD diff exists;
- `scratch/uencfix2/BUILD_NOTES.after.md` is the *post*-edit state and is byte-identical to the live file (0 changed lines);
- no copy exists that differs from live by exactly the one line (scan of every on-disk `BUILD_NOTES*.md`);
- the nearest earlier snapshot, `scratch/udocsync1/BUILD_NOTES.md`, differs in 30 lines, but every changed line
  carries another unit's dated record or the appended UDOCSYNC1 section — so no *unattributed* change is visible.
Conclusion: consistent with the claim, **not proven**; a pre-edit snapshot or a recorded line-count diff is missing.

## Things the claims did not mention
1. An **unpacked published tree** sits beside the tarball: `papers/encoder-crossover-190/released/encoder-crossover-190-released/`.
   It is also leak-free for `UDOIBACK1`/`UCONCEPT1`, but it is a second shipped surface that no unit's sweep named;
   nothing keeps it in sync with the archive.
2. `fixture/fixture-190.json` sha256 is `a15224ba…`; the `c7696edc…` figure is a derived digest (see C3).
3. `scratch/uencfix1/base/build/` also holds `out1.tgz`/`out2.tgz` identical to the base archive; the base pair
   (determinism proof) is intact.
4. `MANIFEST.json` in the shipped archive has `generated_utc = 2026-10-19T04:14:50Z`, i.e. the pinned default —
   which is why the rebuild is byte-identical rather than merely equivalent.
5. Reproducibility edge: any `GENUTC` other than the pinned default changes `MANIFEST.json` and therefore the
   bytes; the archive is reproducible *given the pin*, not for arbitrary build times.
