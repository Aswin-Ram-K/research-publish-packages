# UCLOSE1 — bring the workspace record into line with the closed exposure, and record what remains exposed

**Unit:** UCLOSE1 · **Date:** 2026-10-15 (UTC) · **Hard bound:** 30 tool calls (used 13) · **Status:** done
**Write paths (declared):** `strategy/EXPOSURE_CLOSURE.md`, `strategy/DISCLOSURE_INVENTORY.md`, `orchestration/units/UCLOSE1.md`, `orchestration/handoffs/UCLOSE1.json`. No other file touched. No concurrent unit was running.

## Purpose

The orchestrator closed the live exposure on 2026-10-15. UARCH1's finding — the pre-rewrite Consonance source retrievable unauthenticated by SHA — was **true when written and is now false**. The workspace record therefore overstates live risk, which matters because the author reads these documents to make decisions. One purpose: make the record accurate, and state precisely what is still exposed.

## What was done

1. **Re-ran the verification first-hand** (unauthenticated `curl`, both the short ref and the full object id `89003e7069c9ad79c40d91982720751b1ddf0360`): journal.ts / dag.ts / consonance/LICENSE / `main/findings/PAPER-DERIVATION.md` / `codeload` tarball / `github.com` repo page / `api.github.com` repo — **all 404**. Control url on a public repo of the same account → **200**.
2. **Confirmed repository state:** `visibility: PRIVATE`, `isPrivate: true`, `forkCount: 0`, PUBLIC repo count **18** (was 19).
3. **Proved the objects were NOT deleted:** with the owner-authenticated token the unreferenced commit still resolves (`tree 1aadb1ef509824bd9219e6a917fdf059afcd2f03`) and `contents/consonance/src/journal.ts?ref=89003e70…` returns **size 46450** — the same byte count UARCH1 measured live.
4. **Confirmed the profile-README commit** `2f8d092135039a8b6da5e1b3797833d144b60f96` (*"Profile: remove capability-kernel mechanism description"*, 2026-10-15T21:26:50Z), and derived the "before" state from parent `73ffa8e4b4523e37b3826777571fb2dbb35e404b`: all three strings present (1 each), all three **absent now** (0 each), README 2,352 B → 2,023 B.
5. **Wrote `strategy/EXPOSURE_CLOSURE.md`** — before/after evidence, the private-does/does-not section, the archive-channel finding stated as archive-only, the `forkCount = 0` good news, the AGPL residual, and a **5-item residual decision list** for the author.
6. **Appended §10 to `strategy/DISCLOSURE_INVENTORY.md`** — append-only, nothing deleted: quotes superseded statements A/B/C verbatim, records the closure, corrects the 19→18 count and the header metadata, explains that "implementation still private" is true **again but for a different reason** (visibility, not unreachability), re-triages P10/§1/§4.3/§5/§6/§7.8, and cites `EXPOSURE_CLOSURE.md`.

## Notable findings

- **Location correction (recorded, not fixed):** the card attributed the "retrievable by SHA" statement to `DISCLOSURE_INVENTORY.md`. It is **not** in that file — this file only had the weaker §7.8 *"could not be tested"* note. The "retrievable by SHA" finding lives in **`strategy/ARCHIVE_WINDOW_CHECK.md`** (UARCH1's artifact), which is **outside this unit's write paths** and was not edited. **Its live-exposure rows are now stale and need a dated correction by a unit that owns it.**
- The literal string `IMPLEMENTATION STILL PRIVATE` does not occur in the inventory; the claim it names is carried at §0 and §5 and is corrected there.

## Distinctions carried (the point of the unit)

- **Retrieval is closed. Deletion is NOT done.** Objects remain in GitHub storage, served to the owner.
- **Copies already taken are not recalled.**
- **Archive-channel cleanliness (SWH: none; Wayback: 0 captures; GH Archive: 0 mentions) is a finding about the archive channel ONLY — explicitly not reassurance about the direct channel, which was open until today.**
- **`forkCount = 0`** — no fork preserves a copy; genuinely good news.
- **AGPL-3.0** grant on any copy obtained during the window is a residual that cannot be revoked.

## Constraints honoured

Target `/home/zer0null/Duval` never written, no `git` run there. **No GitHub setting changed and no write to any repository** — `gh`/`curl` GET only. Everything written was run or fetched; no invented code, hash or commit id.

## Report-back

`orchestration/handoffs/UCLOSE1.json`; ≤15-line summary to the parent.
