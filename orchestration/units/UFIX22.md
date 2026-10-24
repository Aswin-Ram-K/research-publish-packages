# UFIX22 — citation repair, `orchestration/` tier (bounded: 12 tool calls)

**Purpose.** Fix the stale citations that UFIX17 reported in five `orchestration/` documents plus the
three UFIX19 reported (`UCURATE1.md`, `UFIX12.md`, `UVER11.md`). Card claims the class is **build-script
line-range drift** in `orchestration/units/UBUILD1.build.sh`; that claim is checked, not assumed.

## Script re-derived by this unit (not copied from the card)
`orchestration/units/UBUILD1.build.sh` = sha256
`a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`, **1,019 lines** — matches the card.
Current gate anchors found by opening the file: heredoc opens `cat > "$DEST/gate.sh" <<'GATE_EOF'` at
`:771`, closes `GATE_EOF` `:896`, `chmod +x "$DEST/gate.sh"` `:897`, fed by `vocabulary/english.txt`
(`:691`–`:692`), `vocabulary/code.txt` `:695`–`:743`, `vocabulary/public.txt` `:748`–`:769`, invoked
`bash "$DEST/gate.sh"` `:1005`. `PATTERNS_HARD` / `PATTERNS_REVIEW` are **absent** from the file.

## Finding on the card's premise (recorded before editing)
**No site in the reported list cites `UBUILD1.build.sh` at all** (`grep -rn 'UBUILD1\|build\.sh\|PATTERNS\|
gate\.sh'` over the five: zero hits). The five sites are UFIX17's Class B, which is the **trace-pin figure**
class, plus shifted `CONTAINMENT_CHECK.md` ranges. The card's build-script framing is a misdescription.
The genuine build-script drift in this tier is at `UFIX12.md:17-18` (in the expanded write paths) and is
fixed; others are reported, not fixed.

## Classifications (all eight sites are dated records -> FROZEN -> dated pointer, no rewrite, no number change)
- `orchestration/VERDICTS.md:335`, `:341` — trace-pin figures; `94495930…` presented as the tracked
  trace's blob (it is the docket repo's own recorded blob, not a target object); `1570243` superseded.
- `orchestration/units/UPOLICY1.md:10`, `:33`, `:34` — same figures; `CONTAINMENT_CHECK.md:161-163` /
  `:261-264` shifted when UFIX17 edited that file (now `:166` / `:270`; `:179`/`:184`/`:191-194` → `:187`/
  `:192`/`:199`).
- `orchestration/units/UVER18.md:14` (with `:13`) — same.
- `orchestration/handoffs/UPOLICY1.json:7-8` — recorded grep command strings (historical).
- `orchestration/handoffs/V5.json:82`, `:97-98`, `:166`, `:256` — frozen verifier verdict, dated.
- `orchestration/units/UCURATE1.md:106`, `orchestration/units/UFIX12.md:22`,
  `orchestration/units/UVER11.md:55` — REFS locator error (UFIX19): `REFS.md:66` is `P:246`, only `G:`
  locator is `:68` (`G:49-51`), `G:` legend already at `:15`.

## Write paths
`orchestration/VERDICTS.md`, `orchestration/units/UPOLICY1.md`, `orchestration/units/UVER18.md`,
`orchestration/handoffs/UPOLICY1.json`, `orchestration/handoffs/V5.json`,
`orchestration/units/UCURATE1.md`, `orchestration/units/UFIX12.md`, `orchestration/units/UVER11.md`,
`scratch/ufix22/**`, `orchestration/units/UFIX22.md`, `orchestration/handoffs/UFIX22.json`.
Never edited: `UBUILD1.build.sh` (read only), `strategy/**`, `docs/**`, `/home/zer0null/Duval`,
`/home/zer0null/research-publish-packages`.

## Bound
12 tool calls. Every before-string asserted unique in its file before editing; both touched JSON handoffs
re-parsed after.

## FINDING ON THE CARD'S PREMISE (recorded plainly)
The card states these sites cite `orchestration/units/UBUILD1.build.sh` line ranges. They do not:
`grep` for `UBUILD1|build\.sh|PATTERNS|gate\.sh` over the five original sites returned **zero hits**. The five
are UFIX17's Class B — the **trace-pin figure** class. The only stale *ranges* present are citations of
`strategy/CONTAINMENT_CHECK.md`, whose line numbers shifted when UFIX17 inserted text on 2026-10-15
(`:179`→`:187`, `:184`→`:192`, `:191-194`→`:199`, `:161-163`→`:166`, `:261-264`→`:270`). No sentence was
rewritten and no number changed. The genuine build-script drift in this tier is `UFIX12.md:17-18` (fixed)
plus `UCURATE1.md:125` and `UVER11.md:51` (reported, not fixed — not on any list).

## Actions applied (all FROZEN → dated pointer, 2026-10-16)
- `orchestration/VERDICTS.md` — pointers at `:340` (blob `94495930` is the docket repo's own, not a target
  object) and `:348` (tracked-trace move is `e25ac80f`→`2ec22a67`; live now 1,624,082 B / 1087 lines /
  `35687221…` at 2026-10-15 21:02:05).
- `orchestration/units/UPOLICY1.md` — pointers at `:12` and `:38`.
- `orchestration/units/UVER18.md` — pointer at `:18`.
- `orchestration/handoffs/UPOLICY1.json` and `orchestration/handoffs/V5.json` — new top-level
  `ufix22_pointer` key at line 2 of each; both re-parsed.
- `orchestration/units/UCURATE1.md` — pointer at `:110`; `orchestration/units/UFIX12.md` — pointers at
  `:20` (build-script) and `:26` (REFS); `orchestration/units/UVER11.md` — pointer at `:57`.

## Verification
Before-string uniqueness asserted per anchor; pointer counts 2/2/1/1/2/1 = 9; all three handoffs parse;
`UBUILD1.build.sh` sha256 `a2a1df17…`, 1,019 lines, recomputed after the edits.
