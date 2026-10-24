# UFIX25 — licence-succession pointers, stale-tree marker, residual-grep re-run, edit-count ruling

**status:** done (hard bound 20 tool calls; bound used 20)
**date:** 2026-10-16 · **workspace:** `/home/zer0null/reserach extarctor`
**purpose:** repair exactly the four items UVER21 reported as not-closed. No scope widening.

## Task 1 — four stale MIT assertions (all four are THIS repo's own licence; 0 third-party)
Pointer added (retaining original sentence and numbers) at: `strategy/VERIFICATION_REPORT_11.md` after
`:154`, after `:181`, after the table at `:310`; and `orchestration/units/UCURATE1.md` after `:147`
(inside item 1, 3-space indent). Pointer text is the house-style dated card:
`> **Superseded 2026-10-16:** the licence described here as MIT is now the PolyForm Non-Commercial
1.0.0 instrument, copied from strategy/licence-templates/RELEASED-PIECE/ by
orchestration/units/UBUILD1.build.sh (LIC_SRC :575, guard :584, sha256 3d364676…f900).`
`strategy/PUBLISH_PACKAGE_MANIFEST.md:448` already carried a pointer — not duplicated, not edited.
Verified pointer counts: V11=3, UCURATE1=1.

## Task 2 — stale pre-licence tree: MARKED, NOT DELETED
73 references to `.ucurate1` across 25 files (strategy/ 35, orchestration/units/ 14,
orchestration/handoffs/ 24) → deletion condition not met. Wrote
`.ucurate1/pre/research-publish-packages/STALE.md` (1,666 B): date, superseding licence set, its own
`.git/` commit `67716cc`, "do not ship". Tree LICENSE untouched (1,077 B, "MIT License").

## Task 3 — residual grep re-run (scoped): ZERO
`grep -rn --include='*.md' --exclude-dir=state --exclude-dir=archive --exclude-dir=jobs
--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv -E '204-205|204–206'` over the five
files → **no output, exit 1**. Independent read-only check:
`repro/encoder-crossover-190-SANITISED/redact.py:206-207` = the `# options is deliberately NOT here`
rationale (routeA.ties 120 -> 119); `:208` = `CASE_FIELDS = ("question",)`.

## Task 4 — edit-count ruling (dated note appended to UFIX24.md)
Counting every action row in UFIX24's five tables: UCURATE1 **3** + UVER11 **4** + PUBLISH **3** +
REGEN **4** + CODE_AGNOSTIC **3** = **17**. The "17 edits" at `:128` is **correct**; the wrong figure
is the `:113` heading "**2 actions**" for CODE_AGNOSTIC, which undercounts its own three action rows
(`:350`, `:424`, `:425`). `3+4+3+4+2=16` only by trusting that stale heading. Frozen number left
unrewritten; dated correction note appended.

## Artifacts
- `.ucurate1/pre/research-publish-packages/STALE.md`
- `strategy/VERIFICATION_REPORT_11.md` (+3 pointers), `orchestration/units/UCURATE1.md` (+1)
- `orchestration/units/UFIX24.md` (dated correction note)
- `orchestration/handoffs/UFIX25.json`
