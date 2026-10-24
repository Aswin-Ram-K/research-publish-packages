# UFIX15 — repair documents citing the deleted denylist gate

**Status:** done. **Gate behaviour changed:** none — prose/citations only.

## Identity re-derived
- `sha256sum orchestration/units/UBUILD1.build.sh` = `5c837c8deba0c33b568a7206872a1fbd7117b503a346903d36f4f47a78815a35`, **1019 lines** (matches UFIX14; this is the pre-edit identity and the sha256 the 95,606-token count was measured against).
- Real gate anchors (grep -n): positive vocabulary checker written just after `cat > "$DEST/gate.sh" <<'GATE_EOF'`, **:771–897**; word lists **:685–770**; `chmod +x "$DEST/gate.sh"` **:897**; invocation `bash "$DEST/gate.sh"` **:1005** (block :1003–1017).

## Defects repaired (13 line-count-neutral regions; verbatim before/after in `orchestration/handoffs/UFIX15.json` and `scratch/ufix15/edits.json`)
1. **Stale citations** — `strategy/PUBLISH_PACKAGE_MANIFEST.md:8` and `:252`, `orchestration/units/UCURATE1.md:37`, `orchestration/units/UTOK1.md:36`, `experiments/token-substitution-test/REPORT.md:168`: each now names the anchor (positive vocabulary checker just after `cat > "$DEST/gate.sh" <<'GATE_EOF'`, currently `:771–897`) rather than only line numbers; surviving denylist-era result lines are marked superseded.
2. **Emitted-README prose** — `orchestration/units/UBUILD1.build.sh:500` and `:520–521`: the shipped README no longer says the package is checked by a HARD-FAIL/REVIEW denylist; it describes the positive vocabulary checker (`vocabulary/{english,code,public}.txt`).
3. **§12.5** — rewritten to the UVER12-verified position (`redact.py:855-895` recomputes `flag = (sh == h)` correctly; regenerated MANIFEST 25 flag-True / 0 contradictions; the 8 contradictions are the stale shipped MANIFEST — UREGEN1's 6 plus 2 pre-existing), with a dated correction naming UVER12 the contradicting verifier and UREGEN1 the source of the original shipped rows. History preserved.
4. **Gate count** — re-measured by UFIX15: **95,606** out-of-vocabulary tokens (`GATE RESULT: FAIL -- 95606 out-of-vocabulary token(s).`, BUILD_RC=1, scratch/ufix15/build.log:473/475/479). Reproduces UFIX14; supersedes ULICENCE3's pre-UFIX14 95,597. Recorded at `strategy/PUBLISH_PACKAGE_MANIFEST.md:255`.

## Constraint compliance
- All builds under `scratch/ufix15/`; the real `/home/zer0null/research-publish-packages` never written.
- No `git` run against `/home/zer0null/Duval`; `redact.py` not edited.
- Every before-string asserted unique in its file before slicing; every file's line count unchanged.

## Note on the build-script digest after these edits
- The `:500` / `:520–521` prose edits change the file's bytes, so its sha256 becomes `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`; the **line count stays 1019**, so every line-number citation to this file still resolves, and UFIX14's cited `5c837c8deba0c33b568a7206872a1fbd7117b503a346903d36f4f47a78815a35` is superseded.
