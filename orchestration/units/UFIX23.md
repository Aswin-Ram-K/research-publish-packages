# UFIX23 — close the two stale `UBUILD1.build.sh` citations in the unit cards

**Unit:** UFIX23 (bounded citation-repair) · **Bound:** 8 tool calls · **Status:** done
**Write paths:** `orchestration/units/UCURATE1.md` · `orchestration/units/UVER11.md` · `scratch/ufix23/**` · `orchestration/units/UFIX23.md` · `orchestration/handoffs/UFIX23.json`
**Never touched:** `orchestration/units/UBUILD1.build.sh` (read only) · `strategy/**`, `docs/**` · `/home/zer0null/Duval` (no git) · `/home/zer0null/research-publish-packages` · any other handoff.

## Identity — re-derived from the file, not copied from the card
`sha256sum` = `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`; `wc -l` = **1019**; `wc -c` = 52779. Both match the card's stated identity.

## Current anchors (exact strings, each asserted unique in the script before editing)
| region | anchor string | line |
|---|---|---|
| emitted package README heredoc (occupies the old `:524–545`) | `cat > "$PKG/README.md" <<'PKG_README_EOF'` … closes `PKG_README_EOF` | `:433` … `:541` |
| licence template-copy block | `LIC_SRC="$SRC/strategy/licence-templates/RELEASED-PIECE"` | `:575` |
| `## Scope` append | `cat >> "$DEST/LICENSE" <<'LICENSE_SCOPE_EOF'` (heading `## Scope -- which files the licence terms above do not cover` `:592`) | `:590` |
| paper licence heredoc | `cat > "$PKG/paper/LICENSE" <<'PAPER_LICENSE_EOF'` | `:607` |
| gate heredoc | `cat > "$DEST/gate.sh" <<'GATE_EOF'` (closing `:896`, `chmod +x "$DEST/gate.sh"` `:897`) | `:771` |
| gate hard-fail path | `print("GATE RESULT: FAIL -- %d out-of-vocabulary token(s)." % flagged)` → `sys.exit(1)` | `:891`, `:893` |
| gate invocation + propagation | `bash "$DEST/gate.sh"` · `GATE_RC=$?` · `exit "$GATE_RC"` | `:1005`, `:1006`, `:1015` |

Note: `sys.exit(1)` is **not** unique (2 occurrences: `:893` in `GATE_PY`, `:954` in `NEUTRALISE_EOF`), so the unique hard-fail print line is the anchor and `:893` is given by line.

## Sites — verification and classification
1. `orchestration/units/UCURATE1.md:127` — cited `build-script lines 524–545` as the root-LICENSE MIT heredoc. **stale**: that range is now prose inside the emitted package README (heredoc `cat > "$PKG/README.md" <<'PKG_README_EOF'` `:433`, closing `:541`); the licence now comes from the template-copy block (`:575`), the `## Scope` append (`:590`) and the `cat > "$PKG/paper/LICENSE" <<'PAPER_LICENSE_EOF'` heredoc (`:607`). Pointer inserted at the end of the same numbered item (lines 147–157), because the citation sentence is hard-wrapped mid-line and inserting there would split it.
2. `orchestration/units/UVER11.md:51` — cited `UBUILD1.build.sh:697–699` and `810–826`. **stale**: both belong to the earlier **826-line** revision, sha256 `0b617414e5eb0e8a2a86930bdf5f2de1d0cf3fb3f9a93865b36e7380af293115`. `:697–699` is now vocabulary-heredoc text; `:810–826` is now gate-internal Python. Pointer inserted after the gate-semantics bullet (lines 55–65).

## Other stale build-script citations found in the same two files — reported, NOT edited (outside the card's two-site bound)
- `orchestration/units/UCURATE1.md:71` — "Build script: 826 lines, sha256 `0b6174…`" (identity, superseded).
- `orchestration/units/UCURATE1.md:37` — dead `PATTERNS_HARD`/`PATTERNS_REVIEW` range, but already carries an inline "range that is now dead" correction (accurate as annotated).
- `orchestration/units/UVER11.md:29`, `:37–38` — denylist heredocs `:612–637`, `:640–647`, `:423–458`, all deleted by ULICENCE3.
- `orchestration/units/UVER11.md:48–49` — "826 lines" + sha `0b6174…` (identity, superseded).
- `strategy/**` and `docs/**` were not swept or edited; `strategy/VERIFICATION_REPORT_11.md` and `strategy/PUBLISH_PACKAGE_MANIFEST.md:8` already carry UFIX20/UFIX21 pointers.

## Inserted pointer text (verbatim, both files; every pre-existing number left untouched)
See `orchestration/handoffs/UFIX23.json` → `evidence.sites[].before` / `.pointer`.
