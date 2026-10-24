# UFIX21 — mechanical citation sweep vs orchestration/units/UBUILD1.build.sh

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a · **Status:** done · **Bound:** 25 tool calls.
**Script under audit (re-derived, not trusted):**
sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`, **1019 lines**
(`wc -l`). The card's value/line-count reproduced exactly, so the script did not change during this pass;
the staleness is historical (ULICENCE3 replaced the `PATTERNS_HARD`/`PATTERNS_REVIEW` heredocs with the
positive vocabulary checker, moving content under stable line numbers).

## Method (literal)
1. Re-derived sha256 + line count.
2. One regex over `strategy/*.md` + `docs/*.md`
   (`UBUILD1\.build\.sh[^A-Za-z0-9]{0,40}[0-9]{1,4}([^0-9]{0,3}[0-9]{1,4})?`) → **13** filename-adjacent
   line references; **29** lines across **8** files mention the script. Expanding to every line reference
   (multi-range lines, prose-separated ranges) yields the **16 enumerated sites** below.
3. Classified every site against the script's literal text.
4. Fixed STALE hits in live guidance (anchor string + current line number, never a bare number).
5. FROZEN RECORD hits: dated inline pointer, numbers and sentences left unrewritten.
6. Included the two known-stale VR11 sites and the UFIX19 row-mapping item.
7. Briefly checked `redact.py` and `papers/` citations.

## Current anchors in the script (verified literal)
| anchor | line |
|---|---|
| `SHIP_STAGED=(` / closing `)` | `:133` / `:202` |
| `cat > "$DEST/README.md"` … `code` … `paper/LICENSE` … `.gitignore` | `:327`, `:433`, `:543`, `:607`, `:639` |
| `vocabulary/english.txt` write | `:691` |
| `code.txt` heredoc / close | `:695` / `:743` |
| `public.txt` heredoc / close | `:748` / `:769` |
| `cat > "$DEST/gate.sh" <<'GATE_EOF'` / close / `chmod +x` | `:771` / `:896` / `:897` |
| gate hard-fail `sys.exit(1)` | `:893` |
| path rules `RULES = [...]` (three literal rules) | `:916`–`:918` |
| anchor assertion `for anchor in 907fa39 ad301ae` / `exit 1` | `:965` / `:971` |
| `git -C "$DEST" init` / commit | `:983` / `:985`–`:988` |
| `bash "$DEST/gate.sh"` / `GATE_RC=$?` / `exit "$GATE_RC"` | `:1005` / `:1006` / `:1015` |

## Hit table (one row per enumerated site; line numbers are the pre-edit citing lines)
| citing file:line | cited range | classification | what is actually there now | action taken |
|---|---|---|---|---|
| strategy/PUBLISH_PACKAGE_MANIFEST.md:5 | `826 lines, sha256 0b617414…` | STALE / FROZEN RECORD | script is **1019 lines**, sha256 `a2a1df17…` | dated pointer inserted (now :8) |
| strategy/PUBLISH_PACKAGE_MANIFEST.md:8 | `:771–897` | ACCURATE | gate heredoc `:771`–`:896`, `chmod +x` `:897` | none |
| strategy/PUBLISH_PACKAGE_MANIFEST.md:252 | `:771–897` | ACCURATE | same | none |
| strategy/PUBLISH_PACKAGE_MANIFEST.md:407 | build-script lines `524–545` | STALE / FROZEN RECORD | `:524–545` is package-README prose; `LICENSE` digested `:583`, scope appended `:590` | dated pointer inserted (now :409) |
| strategy/REGEN_ASSESSMENT.md:24 | `:771`–`:896`, `:897`, `:691`, `:695–743`, `:748–769`, `:1005` | ACCURATE | both heredoc endpoints, both vacab ranges, invocation — all verified | none |
| strategy/REGEN_ASSESSMENT.md:215 | `:133-181`, `:174-181` | STALE (live guidance) | `SHIP_STAGED=(` `:133`, closes `:202`; `:174–181` VERIFICATION.txt exclusion comment still holds | range fixed in place → `` `SHIP_STAGED=(` list at `UBUILD1.build.sh:133`, closing `:202` `` |
| strategy/VERIFICATION_REPORT_11.md:23 | `:612–637` | STALE / FROZEN, already annotated | `:612–637` is paper-licence text; gate checker `:771`–`:896` | none — UFIX20 pointer at `:26` covers it |
| strategy/VERIFICATION_REPORT_11.md:116 | `:129` | ACCURATE | `:129` = "missing is FATAL. Nothing ships by omission." | none |
| strategy/VERIFICATION_REPORT_11.md:198 | `:775–778` | STALE / FROZEN, unannotated | `:775–778` is gate-heredoc prose; anchor loop `:965`, `exit 1` `:971` | dated pointer inserted (now :200) |
| strategy/VERIFICATION_REPORT_11.md:220/225 | `REFS.md:66` cites `G:` | STALE row-mapping / FROZEN (UFIX19 item) | `REFS.md:66` uses **`P:246`**; only `G:` locator is `:68` (`G:49-51`); `G:` legend `:15`, `P:` `:11` | dated "Corrected" pointer inserted (now :229) |
| strategy/VERIFICATION_REPORT_11.md:231 | `:697–699` | STALE / FROZEN, unannotated (card item 6) | `:697–699` is vocabulary-heredoc text; exit-1 path is `sys.exit(1)` `:893` | dated pointer inserted (now :237) |
| strategy/VERIFICATION_REPORT_11.md:234 | `:810–826` | STALE / FROZEN, unannotated (card item 6) | gate-internal Python; propagation now `:1004`–`:1015` | dated pointer inserted (now :242) |
| strategy/VERIFICATION_REPORT_11.md:247 | `~782–806` | STALE / FROZEN, unannotated | git step now `:977`–`:991` (`init` `:983`, commit `:985`–`:988`) | dated pointer inserted (now :259) |
| strategy/VERIFICATION_REPORT_11.md:264 | `:744`; "lines 327, 398, 499, 523, 547, 577, 612, 640" | STALE / FROZEN, already annotated | `replace()` is `:937`; `cat >` sites now `:327/:433/:543/:607/:639/:695/:748/:771` | none — UFIX20 pointer at `:277` covers it |
| strategy/VERIFICATION_REPORT_11.md:276 | `:423–458`, `:612–637`, `:640–647` | STALE / FROZEN, already annotated | README prose / paper-licence text / `.gitignore` comments | none — UFIX20 pointer at `:290` |
| strategy/VERIFICATION_REPORT_11.md:277 | same as `:276` | STALE / FROZEN, already annotated | same | none — UFIX20 pointer at `:290` |

## Tally
- Raw pre-judgement: 29 script-mentioning lines across 8 files; single regex → 13 filename-adjacent refs;
  full enumeration → **16 citation sites**.
- ACCURATE **4** · STALE-fixed-in-place **1** · STALE/FROZEN-pointer-inserted **6** ·
  STALE/FROZEN-plus-row-mapping-corrected **1** · STALE/FROZEN-already-annotated **4** · NOT-A-CITATION
  (mention-only lines: `PPM:190`, `PPM:394`, `REGEN:25`, `CODE_AGNOSTIC_RELEASE_POLICY.md:40/570/596`,
  `AUTHOR_DECISIONS.md:127`, `VR11:6/121/190/192`, `VR15:7/15`, `VR17:8`) — no line reference.
- Fixed: **1** (REGEN:215). Annotated with dated pointers: **7** (VR11:198/220/231/234/247, PPM:5, PPM:407).

## Other commonly-cited files (checked briefly; not fixed where outside the script set)
- `repro/encoder-crossover-190-SANITISED/redact.py:204–206` / `:206` (`CODE_AGNOSTIC_RELEASE_POLICY.md:350`,`:424`;
  `REGEN_ASSESSMENT.md:126` cites `:204-205`) — ACCURATE in substance, but `CASE_FIELDS = ("question",)` is at
  **`:208`** (the exclusion rationale is `:206–207`). 1–2 line drift; **reported, not fixed** — the file is in a
  read-only/"do not touch" path and the substance holds.
- `redact.py:855-895` (`PUBLISH_PACKAGE_MANIFEST.md:509`, `VERIFICATION_REPORT_12.md:45`) — ACCURATE:
  `flag = (sh == h) if sh else e.get(key)` at `:875`.
- `redact.py:925` (`UNPINNED_MEASUREMENT.md:12`) — ACCURATE: `NEUTRAL_PINS = os.environ.get("REDACT_PINS", "1") != "0"`.
- `papers/encoder-crossover-190/REFS.md:126` (PPM:178) · `papers/gated-read-batching/CLAIMS.md:8`,`:11-15` (PPM:218/220/224) ·
  `REFS.md:11` (PPM:224) · `papers/encoder-crossover-190/MANUSCRIPT.md:793` (CODE_AGNOSTIC:632) — all ACCURATE.
- `VERIFICATION_REPORT_15.md:15` asserts `REGEN_ASSESSMENT.md:23` presents the old heredoc as current fact —
  superseded by REGEN's own ULICENCE3 note; frozen record, no action.

## Unresolved
None blocking. The only un-actioned drift is the 1–2-line `redact.py` case above (read-only path).

## Hard-rule containment
Read `UBUILD1.build.sh` only (never edited; hash unchanged at `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`).
No git command run against `/home/zer0null/Duval`. Nothing written to `/home/zer0null/research-publish-packages`.
`scratch/ubij1-3/**` and `repro/encoder-crossover-190-SANITISED/` read-only/untouched.
Verbation before/after of every changed region: `scratch/ufix21/edits.log`.
