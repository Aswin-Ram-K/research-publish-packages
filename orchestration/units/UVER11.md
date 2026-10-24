# UVER11 — independent verification of UCURATE1

**Unit:** UVER11 (verifier; not the author)
**Verifies:** UCURATE1 (`strategy/PUBLISH_PACKAGE_MANIFEST.md`, staged tree
`.ucurate1/pre/research-publish-packages/`, build script `orchestration/units/UBUILD1.build.sh`)
**Bound:** 40 tool calls · **used:** 30 · **status:** done (verdict **PARTIAL**)

## Purpose
Attempt to break UCURATE1's 11 claims about the publish package by working from the artifact, not the
prose. Deliver an independent gate tally, red→green the prune in both directions, check the ship
list, the licence, the anchors and the build script, and determine whether the gate is advisory or
build-gating.

## Write paths
- `strategy/VERIFICATION_REPORT_11.md` (full report)
- `orchestration/units/UVER11.md` (this card)
- `orchestration/handoffs/UVER11.json`
- `scratch/uver11/` (hard.txt, shiplist.txt, tree.txt, pretransform/, A/ A2/ C/ D/ builds, logs)

## Containment
- `/home/zer0null/Duval` and all registered targets: **read-only, untouched**; no `git` run against
  any target.
- Real `/home/zer0null/research-publish-packages`: **listed only**, never written (0 files, mtime
  Oct 15 18:07 predates this unit).
- All builds redirected to `scratch/uver11/{A,A2,C,D}/`; no remote created; nothing pushed.

## Result summary
- **Headline: REPRODUCED.** My own scan of `.ucurate1/pre/research-publish-packages/` with the build
  script's own 24 HARD patterns (heredoc `UBUILD1.build.sh:612–637`, excluding `gate.sh` and `.git`)
  = **152** distinct hard-fail lines. Per-pattern identical to the manifest: StateClass 62,
  grantPolicy 40, `expanded[` 28, `admit(` 20, REDACTION_REPORT 10, EXCLUDED.md 2, src/broker 2,
  VERIFICATION_REPORT 1, `/home/zer0null` 0, `duval` 0 (165 occurrences / 152 lines).

  > **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** the denylist heredoc cited as
  > `UBUILD1.build.sh:612–637` no longer exists — ULICENCE3 deleted it. The gate is now the positive
  > vocabulary checker written by `cat > "$DEST/gate.sh" <<'GATE_EOF'` (`:771`, closing `:896`, `chmod +x`
  > `:897`), whose word lists are `CODE_VOCAB_EOF` (`:695`–`:743`) and `PUBLIC_VOCAB_EOF` (`:748`–`:769`).
- **Contradicted:** the `218` untransformed-ship-set figure (manifest:286). Reverse-neutralising the
  built ship set gives **156** (152 + 4 path-only lines); the build's own log says
  `4 occurrence(s) in 2 file(s)`. The 66-line gap implied by `218 − 152` does not exist.
  (Notably, 156 ≈ the contract's 158, weakening the "incomparable numbers" framing.)
- **Overstated:** pattern-list citation `UBUILD1.build.sh:423–458` (manifest:7) is wrong; the HARD
  heredoc is `UBUILD1.build.sh:612–637`, REVIEW `640–647`. Content correct, location wrong.

  > **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** `:423–458`, `:612–637` and `:640–647`
  > are all deleted denylist heredocs (ULICENCE3); the current build carries no HARD/REVIEW pattern list,
  > shipping instead the positive vocabulary checker at `GATE_EOF` (`:771`–`:896`). The `manifest:7` reference
  > has also moved: `strategy/PUBLISH_PACKAGE_MANIFEST.md:7` is now blank and its gate reference sits at `:10`
  > (`:771–897`). The script is now **1,019 lines**, sha256
  > `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`.
- **Prune red→green (both directions):** unlisted probe → `DROP code/harness/UNLISTED_PROBE.txt`,
  staged 67 = 52 kept + 15 dropped, 0 survivors, rc 1; omitted listed file → `FATAL: ship-list names
  a file the package does not have: code/harness/train.py`, rc 1, gate not reached.
- **Ship list:** 52 `SHIP_STAGED` + 6 authored = **58 distinct**; 0 listed-but-absent; the only
  present-but-unlisted are exactly the 6 authored files.
- **Licence:** `LICENSE` first line `MIT License`, sha256
  `f2eb46b60685fe9bcb4a0075c865404d1f67a77363d3905025c46fcc335fb915`, 0 PolyForm files. Memo
  `strategy/CODE_LICENSING_STRATEGY.md:9–40` says each **released piece** is **PolyForm
  Noncommercial 1.0.0**. Conflict stated, **not resolved** (known open item).

  > **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** the MIT `LICENSE` measured above was
  > replaced by ULICENCE3: the build copies the PolyForm Noncommercial 1.0.0 template
  > (`LIC_SRC="$SRC/strategy/licence-templates/RELEASED-PIECE"` `:575`, `cp "$LIC_SRC/$f" "$DEST/$f"` `:579`)
  > and pins it at `:584` to sha256
  > `3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900`; the `f2eb46b6…` hash and
  > "0 PolyForm files" are the record.
- **Anchors / script:** 907fa39 in 12 files, ad301ae in 7; build script sha256
  `0b617414e5eb0e8a2a86930bdf5f2de1d0cf3fb3f9a93865b36e7380af293115`, 826 lines — all match.

  > **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** the script is now **1,019 lines**,
  > sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`; the two revisions are still
  > asserted, now by `for anchor in 907fa39 ad301ae` (`:965`). The 12-file / 7-file counts are the record.
- **Gate semantics (task H):** **build-gating, not advisory** — `gate.sh` exits 1 on hard-fail
  (`UBUILD1.build.sh:697–699`), the build propagates it (`810–826`, log tail
  `BUILD COMPLETE — the exclusion gate FAILED (exit 1).`). Nuance: the tree is committed **before**
  the gate runs, so the failing package still exists on disk.

  > **Superseded 2026-10-16 (UFIX23, dated record left unrewritten):** both ranges cite the earlier
  > **826-line** revision of `orchestration/units/UBUILD1.build.sh` (sha256
  > `0b617414e5eb0e8a2a86930bdf5f2de1d0cf3fb3f9a93865b36e7380af293115`). The script is now **1,019 lines**,
  > sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`; `:697–699` is now
  > vocabulary-heredoc text and `:810–826` is now gate-internal Python. The hard-fail path is
  > `print("GATE RESULT: FAIL -- %d out-of-vocabulary token(s)." % flagged)` (`:891`) then `sys.exit(1)`
  > (`:893`) inside `cat > "$DEST/gate.sh" <<'GATE_EOF'` (`:771`, closing `:896`, `chmod +x "$DEST/gate.sh"`
  > at `:897`); the propagation is `set +e` (`:1004`), `bash "$DEST/gate.sh"` (`:1005`), `GATE_RC=$?`
  > (`:1006`), `set -e` (`:1007`) and `exit "$GATE_RC"` (`:1015`). Verify the anchors before relying on
  > the numbers.

- **REFS mismatch real:** `papers/gated-read-batching/REFS.md:11` declares only **P**;
  `REFS.md:66` cites `G:49-51`.

  > **Superseded 2026-10-16 (UFIX22, dated record left unrewritten):** the `REFS.md` reading above is wrong. `papers/gated-read-batching/REFS.md:66` uses **`P:246`**, not a `G:` locator; the only `G:` locator is `REFS.md:68` (`G:49-51`); and the `G:` legend already exists at `REFS.md:15` (`P:` at `:11`), so the recommendation to add a legend line is moot.

## Next unit hint
Correct or delete the `218` claim in `strategy/PUBLISH_PACKAGE_MANIFEST.md` §8 (line 286) and fix the
pattern-list citation at manifest:7; leave the 152 headline and the exit-1 gate as verified. The
licence conflict (MIT shipped vs PolyForm-NC-for-released-pieces memo) remains an **open decision**,
not a verifier item.
