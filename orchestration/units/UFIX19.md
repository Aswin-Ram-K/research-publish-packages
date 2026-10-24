# UFIX19 — locator-attribution repair (D6 "enumerates", D7 `REFS.md:66`, manifest source)

**Bound:** 12 tool calls. **Status:** done — see `orchestration/handoffs/UFIX19.json`.

## Purpose
Factual-attribution corrections to two documents after UVER17 (`strategy/VERIFICATION_REPORT_17.md`).
**No decision substance changed** — no option, recommendation, cost aside or blocked-line re-worded.
The D6 count (**6 of 12, 12 → 11 best / 12 → 6 worst**) is confirmed by UVER17's independent re-derivation
and was not touched.

## Write paths
`strategy/AUTHOR_DECISIONS.md`, `strategy/PUBLISH_PACKAGE_MANIFEST.md`, `scratch/ufix19/**`,
`orchestration/units/UFIX19.md`, `orchestration/handoffs/UFIX19.json`.
Never write `/home/zer0null/research-publish-packages`; never run git against `/home/zer0null/Duval`.
Untouched by this unit: UFIX17's files (`strategy/AGENTS.md`, `strategy/NC1_UNBLOCK.md`,
`strategy/NC1_FIX_PROPOSAL.md`, `strategy/CONTAINMENT_CHECK.md`, `docs/LIVE_TARGET_NOTES.md`) and everything
under `papers/gated-read-batching/`.

## The three sites (anchors, with the brief's line numbers and their drift)
1. **D7 locator sentence in `strategy/AUTHOR_DECISIONS.md`** — brief anchor `:135-136`; **drifted to `:140-141`
   mid-unit** (a concurrent edit inserted a superseded-figure note near `:100`), so the fix was applied by
   unique string match, not offset. Claim: `REFS.md:66` uses a `G:` locator. **Contradicted.** Now states the
   only `G:` locator is `G:49-51` at the `G:` locator legend's sibling row `REFS.md:68`; the `:66` reference
   row uses `P:246`, the locator declared at the `P:` source line `REFS.md:11`; the `G:` legend line is
   `REFS.md:15`; **no fix is owed at `:66`**.
2. **D6 sentence in `strategy/AUTHOR_DECISIONS.md`** — brief anchor `:103-104`; **drifted to `:108-109`** by
   the same concurrent edit. Said `NC1_FIX_PROPOSAL.md:138-141` "enumerates all six rows". **Overstated:**
   that range gives only the count; the rows (B1, B2, B4, E1, E4, E5) are named at the check-B enumeration in
   `NC1_UNBLOCK.md:126-130`. Softened; count unchanged.
3. **`strategy/PUBLISH_PACKAGE_MANIFEST.md:232-236`** — inherited source of the false `:66`/`G:` claim, fixed
   at `:233-235`. Its "**G/R/S** legend lives only in `CLAIMS.md:11-15`" clause was also false for `G`/`P`
   (declared at `REFS.md:15` / `REFS.md:11`); the CLAIMS-only letters are **R/S**. The recommendation
   sentence itself ("add one line to `REFS.md`") was left verbatim.

## House style
Every line number written carries an **anchor name** alongside it. Both edited files are **untracked by git**,
so verbatim before/after is carried in the handoff and each before-string was asserted unique before slicing.

## Stop rules
Same-class defect in a **different** file → reported, not edited. Wanting to re-word a recommendation → stop
and report (the `REFS.md:15` finding makes the manifest's "add one line" recommendation moot; escalated, not
rewritten).
