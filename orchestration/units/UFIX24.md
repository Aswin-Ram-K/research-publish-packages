# UFIX24 — citation-drift closure across five owned files

**status:** done (hard bound 15 tool calls; bound used 15)
**date:** 2026-10-16 · **workspace:** `/home/zer0null/reserach extarctor`
**scope:** make five files *internally complete* — every citation in each that points at another file enumerated, every stale one fixed (live guidance) or annotated (frozen record). No instance list was supplied or used.

## Build-script truth (derived from the file, not copied from the card)

`orchestration/units/UBUILD1.build.sh` = **1,019 lines**, sha256 **`a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`** (unchanged by this unit; read-only). The revision the five files were written against — 826 lines, sha256 `0b617414e5eb0e8a2a86930bdf5f2de1d0cf3fb3f9a93865b36e7380af293115` — is superseded.

| what | unique anchor string | line |
|---|---|---|
| gate heredoc opens | `cat > "$DEST/gate.sh" <<'GATE_EOF'` | 771 |
| gate heredoc closes | `GATE_EOF` | 896 |
| gate made executable | `chmod +x "$DEST/gate.sh"` | 897 |
| gate body (python) | `exec python3 - "$ROOT" <<'GATE_PY'` | 794 |
| gate hard-fail | `print("GATE RESULT: FAIL -- %d out-of-vocabulary token(s)." % flagged)` | 891 |
| code vocabulary list | `cat > "$DEST/vocabulary/code.txt" <<'CODE_VOCAB_EOF'` … close | 695–743 |
| public vocabulary list | `cat > "$DEST/vocabulary/public.txt" <<'PUBLIC_VOCAB_EOF'` … close | 748–769 |
| gate invocation | `bash "$DEST/gate.sh"` | 1005 |
| return-code propagation | `GATE_RC=$?` then `exit "$GATE_RC"` | 1006 / 1015 |
| licence template copy | `LIC_SRC="$SRC/strategy/licence-templates/RELEASED-PIECE"` / `cp "$LIC_SRC/$f" "$DEST/$f"` | 575 / 579 |
| licence digest guard | `[ "$LIC_SHA" = "3d364676…f900" ]` | 584 |
| licence scope append | `cat >> "$DEST/LICENSE" <<'LICENSE_SCOPE_EOF'` … close | 590–602 |
| paper licence instrument | `cat > "$PKG/paper/LICENSE" <<'PAPER_LICENSE_EOF'` … close | 607–637 |

Trap respected: `sys.exit(1)` is **not** unique (`:893` and `:954`; `exit 1` also at `:971`) — none of the anchors above uses it.
Cross-file values derived for this pass: `strategy/licence-templates/RELEASED-PIECE/LICENSE` = **5851 B**, sha256 **`3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900`**; `COMMERCIAL.md` 3512 B; `CONTRIBUTING.md` 3036 B.

## The judgement call (made explicitly)

**Decision: FIX — not record-as-accepted.** The orchestrator framed one site; enumeration found **six**: `strategy/REGEN_ASSESSMENT.md:122`, `:126`, `:263`, `:290` and `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md:350`, `:424`.
*Reasoning.* The cited ranges `redact.py:204-205` / `204–206` hold `SAFE_KEYS`' tail (`:203-204`) and `CASE_FIELD_RE = re.compile(r"^    [a-z_]+:")` (`:205`) — a **different declaration** from the named `CASE_FIELDS = ("question",)` (now `:208`) and its `# options is deliberately NOT here` rationale comment (now `:206-207`). The six sites cite it three inconsistent ways (`:206`, `204-205`, `204–206`); the anchor discipline this unit exists to install requires citing the line that carries the symbol. No measured number and no dated verdict changes, so the frozen-record prohibition on rewriting is not engaged. `REGEN_ASSESSMENT.md:263` was **not** on the card — it was found by enumerating the file's own citational dependence; that is the point of the file-scoped brief.

## Per-file citation tables

Line numbers are as found **before** this unit's edits.

### 1. `orchestration/units/UCURATE1.md` — 14 cross-file citations found, 3 actions

| line | citation | class | what is at the cited location now | action |
|---|---|---|---|---|
| 19 | `harness/analyze.py` | ACCURATE | `:133` is the `manifest.json` read | none |
| 37 | build gate `:771`–`:896`, `chmod` `:897` | ACCURATE | anchors hold | none |
| 71 | build script "826 lines, sha256 `0b6174…`" | STALE (frozen measurement) | script is 1,019 lines / `a2a1df…` | dated pointer inserted at `:73` |
| 106 | `REFS.md` readings | ACCURATE (already superseded) | covered by pre-existing UFIX22 pointer `:110` | none (not duplicated) |
| 117 | `harness/analyze.py` | ACCURATE | as `:19` | none |
| 127 | build-script `:524–545` | ALREADY ANNOTATED | pre-existing UFIX23 pointer `:147` | none (not disturbed) |
| 129 | `strategy/PUBLICATION_STRATEGY.md:570`/`:576` | ACCURATE | MIT prose present | none |
| 131 | `strategy/ARCHIVE_WINDOW_CHECK.md:295` | ACCURATE | "the published root is MIT" present | none |
| 133 | `strategy/CODE_LICENSING_STRATEGY.md:9-31` | ACCURATE | two-tier table present | none |
| 137 | `strategy/WITHHELD.md:132` | ACCURATE | present | none |
| 139–140 | licence template "5,662 bytes, sha256 `25aa637b…`" | STALE (frozen measurement) | now 5851 B / `3d364676…f900` | dated pointer inserted at `:161` |
| 159 | build-script lines 344, 380, 383, 495 | STALE | `:344` is the PolyForm-NC/CC-BY-4.0 package table; `:380`–`:382` README-PARAGRAPHS extraction; `caseB=` `:383`; `:495`–`:497` path caveat | dated pointer inserted at `:170` |
| 159 | `strategy/WITHHELD.md:124` / `:129-133` | ACCURATE | present | none |
| 171 | `strategy/WITHHELD.md:129-133` | ACCURATE | present | none |

**Zero further stale citations in this file.**

### 2. `orchestration/units/UVER11.md` — 9 cross-file citations found, 4 actions

| line | citation | class | what is at the cited location now | action |
|---|---|---|---|---|
| 29 | `UBUILD1.build.sh:612–637` | STALE (deleted heredoc) | no denylist heredoc exists; positive checker at `:771`–`:897` | dated pointer at `:34` |
| 33 | `manifest:286` (218 claim) | ACCURATE | `PUBLISH…:286-290` baseline paragraph | none |
| 37–38 | `:423–458`, `:612–637`, `:640–647` | STALE (deleted heredocs) | all gone; no HARD/REVIEW list | dated pointer at `:45` |
| 37 | `manifest:7` pattern-list citation | STALE | `PUBLISH…:7` is blank; gate ref now `:10` | covered by the same `:45` pointer |
| 44–45 | `LICENSE` MIT `f2eb46b6…`, "0 PolyForm files" | STALE (superseded measurement) | build now copies PolyForm template, pinned `:584` | dated pointer at `:61` |
| 46 | `strategy/CODE_LICENSING_STRATEGY.md:9–40` | ACCURATE | two-tier table present | none |
| 48–49 | build script "`0b6174…`, 826 lines" | STALE (frozen measurement) | 1,019 lines / `a2a1df…` | dated pointer at `:70` |
| 50–53 | gate `:697–699`, `:810–826` | ALREADY ANNOTATED | pre-existing UFIX23 pointer `:55-64` | none (not duplicated) |
| 66–67 | `REFS.md:11` / `:66` | ALREADY ANNOTATED | pre-existing UFIX22 pointer `:69` | none (not disturbed) |
| 72–73 | `manifest:286` / `manifest:7` | 286 ACCURATE; 7 STALE | as rows above | pointer at `:45` names the move |

**Zero further stale citations in this file.**

### 3. `strategy/PUBLISH_PACKAGE_MANIFEST.md` — 9 cross-file citations found, 3 actions

| line | citation | class | what is at the cited location now | action |
|---|---|---|---|---|
| 5 | build script "826 lines, `0b6174…`" | STALE (already annotated) | pre-existing pointer `:8` | none (not duplicated) |
| 10, 254 | build gate "currently `:771–897`" | ACCURATE | anchors hold | none |
| 335 | authored `LICENSE` "(MIT, placeholders)" | STALE | build copies PolyForm template, pinned `:584` | dated pointer at `:342` (outside the fence) |
| 409–412 | build-script `:524–545` | ALREADY ANNOTATED | pre-existing UFIX23 pointer `:411` | none (not disturbed) |
| 437–441 | template sizes/digest 5,662 B / `25aa637b…` / 3,379 B / 4,111 B | STALE (frozen measurement) | 5851 B / `3d364676…` / 3512 B / 3036 B | dated pointer at `:448` |
| 457–459 | build-script 344/380/383/495 as MIT prose | STALE | as UCURATE1 row | dated pointer at `:472` |
| 234–237 | `REFS.md` readings | ACCURATE (UFIX22-corrected) | present | none |
| 72, 123–127, 513–519 | package-internal `path:line` census rows (shipped tree) | FROZEN PROVENANCE | measurements of the ship set, not live guidance; left as the record | none by rule (recorded here) |

**Zero further stale citations in this file.**

### 4. `strategy/REGEN_ASSESSMENT.md` — 15 cross-file citations found, 4 actions

| line | citation | class | what is at the cited location now | action |
|---|---|---|---|---|
| 3 | `redact.py` (no line) | NOT A CITATION | file named, no line claimed | none |
| 23–24 | build gate anchors | ACCURATE | hold | none |
| 122 | `redact.py:206` for `CASE_FIELDS` | STALE | symbol is at `:208` | fixed to `:208` |
| 126 | `redact.py:204-205` for the rationale | STALE | rationale is `:206-207` | fixed to `:206-207` |
| 192 | `verify/run-verification.sh:57-62` | ACCURATE | scoring-projection digest block | none |
| 200 | `redact.py:336-338` | ACCURATE (in-class) | redaction routine | none |
| 215 | build `SHIP_STAGED=(` `:133`, close `:202`, exclusion `:174-181` | ACCURATE | all hold | none |
| 229 | `redact.py:884-889` | ACCURATE | redaction routine | none |
| 263 | `redact.py:204-205` for label-substitution cost | STALE — **not on the card** | rationale is `:206-207` | fixed to `:206-207` |
| 278 | `redact.py:201` | ACCURATE | `TOKEN_SKIP_EXT` | none |
| 280 | `tccommon.py:65` | ACCURATE | present | none |
| 282 | `redact.py:188-190` / `:191-200` | ACCURATE | present | none |
| 286–290 | `redact.py:646-668`, `:689`, `:203`, `:682` | ACCURATE | present | none |
| 290 | `:206` for `CASE_FIELDS` | STALE | symbol is at `:208` | fixed to `:208` |

**Zero further stale citations in this file.**

### 5. `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` — 7 citation groups found, 2 actions

| line | citation | class | what is at the cited location now | action |
|---|---|---|---|---|
| 44–46 | build `:695`–`:743`, `:748`–`:769`, invocation `:1005` | ACCURATE | all hold | none |
| 350 | `redact.py:204–206` + `CASE_FIELDS` | STALE | rationale `:206-207`, symbol `:208` | fixed to `:206–207` / `at :208` |
| 424 | `redact.py:204–206 already knows` | STALE | rationale is `:206-207` | fixed to `:206–207` |
| 425 | `CASE_FIELDS … deliberately excludes` | STALE (missing anchor) | symbol is at `:208` | added `(\`:208\`)` |
| 596–599 | build `GATE_EOF` `:771`–`:896`, `chmod` `:897` | ACCURATE | hold; the same passage already records ULICENCE3's deletion of the denylist | none |
| 632–685 | `MANUSCRIPT.md` `:26/:84/:93/:133/:258/:321/:754/:793/:835-840`, digest `076164ac…`, `REFS.md:126`, `docs/DECIDER_STACK_DECISION.md §11.2/§11.6`, commits `ad301ae`/`995fbd1`/`a5efb2` | ACCURATE | all verified present and matching | none |
| 102–329 | census tables of `gate.sh:NN` / `packages/…:line` | FROZEN PROVENANCE | measurements of the *superseded* denylist era, already self-annotated at `:596-597`; not live guidance | none by rule (recorded here) |

**Zero further stale citations in this file.**

## Method / evidence
- `python3 scratch/ufix24/apply.py` applied all 17 edits; each before-string asserted unique in its file (exit 1 otherwise). Verbatim before/after for all 17 in `scratch/ufix24/diff.json` and in the `edits` key of `orchestration/handoffs/UFIX24.json`.
- Marker counts (`Superseded 2026-10-16 (UFIX24`) per file: UCURATE1 0→3, UVER11 0→4, PUBLISH 0→3, REGEN 0→0, CODE_AGNOSTIC 0→0 (the last two are line-number fixes, not records — no pointer belongs there).
- `grep -n '204-205\|204–206'` over the five files returns no match; pre-existing UFIX22/UFIX23 pointers and the PUBLISH denylist heading are intact.
- `orchestration/units/UBUILD1.build.sh` unchanged: sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`, 1,019 lines.

> **Corrected 2026-10-16 (UFIX25, dated note; the number above is left unrewritten as the record).** The per-file heading at `:113` says `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` has "**2 actions**", but that file's own table lists **three** action rows — `:350` (fixed to `:206–207` / `at :208`), `:424` (fixed to `:206–207`) and `:425` (added `(\`:208\`)`). Counting every action row across the five tables: UCURATE1 **3** (`:45`,`:53`,`:54`) + UVER11 **4** (`:64`,`:67`,`:68`,`:70`) + PUBLISH **3** (`:83`-row not applicable; `:85`→`:448`, `:86`→`:472` plus `:335`→`:342`) + REGEN **4** (`98`,`99`,`104`,`109`) + CODE_AGNOSTIC **3** = **17**, which **agrees with the "17 edits" at `:128` and with the 17 before/after entries in `scratch/ufix24/diff.json`**. The wrong figure is therefore the `:113` heading's "2 actions" (an undercount of one); a naive `3+4+3+4+2` sum reaches 16 only by trusting that stale heading.
