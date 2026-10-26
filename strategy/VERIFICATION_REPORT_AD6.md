# VERIFICATION_REPORT_AD6 — independent re-check of UFIXAD6

Unit **UVERAD6** (verifier, not author). Subject: the 9 dated corrections UFIXAD6
applied to `strategy/WITHHELD.md` and `strategy/GATED_READ_DISCLOSURE.md` per
`strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md` (UAD6 handoff `orchestration/handoffs/UAD6.json`).
Author's own report: `orchestration/handoffs/UFIXAD6.json`, `orchestration/units/UFIXAD6.md`.

**VERDICT: `partial`** — all functional corrections are faithful (class set exact,
originals preserved, protective conclusion intact, negative true, red→green
non-vacuous); two blemishes recorded below (date token contradicted; one integrity
sub-check unverified).

---

## Check 1 — The nine anchors hold (§1 corrections)

Read `strategy/WITHHELD.md:443–450` and `strategy/GATED_READ_DISCLOSURE.md` 1–278.
No pre-edit backup of either file exists on disk, so "original preserved" is
established by the original tokens/phrases still being present **alongside** the
appended notes — not by a byte diff. All nine named corrections hold:

| # | Correction | Original still present | Dated note added |
|---|---|---|---|
| 1 | `strategy/WITHHELD.md:443–445` premise | yes — `:444–445` "...`consonance/src/journal.ts` and `src/journal.ts` return **404 at every historical ref** while a control README returns **200**" intact; surrounding §8.3 protective paragraph `:442–448` intact | yes — `strategy/WITHHELD.md:450` "Dated correction (2026-10-15, unit UFIXAD6)" |
| 2 | §1 item 4 | yes — `strategy/GATED_READ_DISCLOSURE.md:27` "**Any `src/**` or `kernel/**` path name** … Includes the grep-hit list …`src/sandbox.ts`." intact | yes — inline on `:27` |
| 3 | §1 item 5 | yes — `strategy/GATED_READ_DISCLOSURE.md:28` original M10 sentence with `strategy/PAPER_CANDIDATES.md:1028` quote intact | yes — inline on `:28` |
| 4 | §1 summary note | n/a (new) | yes — `strategy/GATED_READ_DISCLOSURE.md:37` |
| 5 | X-07 | yes — `:139` class cell still reads `neutralise`; all 6 non-`src/` roots retained | yes — inline on `:139` (`src/` root only) |
| 6 | X-08 | yes — `:140` keeps both tokens `withhold` → `already-disclosed`; original reason `M12 (strategy/WITHHELD.md:108)` kept | yes — inline on `:140` |
| 7 | AD-6 | yes — `:175` keeps "CONFLICTED, must be reconciled" and the original `ARCHIVE_WINDOW_CHECK.md` vs `WITHHELD.md:444–445` evidence cell | yes — inline on `:175`, "RESOLVED (2026-10-15, unit UFIXAD6)" |
| 8 | §4 effect paragraph | yes — `:177–181` original hand-off sentence retained ("handed to the next unit rather than resolved here") | yes — `:182` "that hand-off is discharged — AD-6 is RESOLVED" |
| 9 | U-1 | yes — `:218` original undecided question/conflict text retained after the note | yes — `:218` "DECIDED (2026-10-15, unit UFIXAD6): YES" |

**No correction's original text was missing or altered** (nothing struck, nothing
renumbered; `:452` still says "The `worker.class` / `context.package` strings remain `UNVERIFIED`").

## Check 2 — The negative is true

Command run (both files):
`grep -nE 'ccdab112.*consonance|consonance.*ccdab112' strategy/WITHHELD.md strategy/GATED_READ_DISCLOSURE.md`
→ exactly **2** hit lines, both explicit negations:
- `strategy/WITHHELD.md:450` — "**Do not read `ccdab112` as having carried `consonance/`:** that boundary commit's tree is `.gitignore CLAIMS.tsv README.md SOURCES.tsv` — no `consonance/` directory at all."
- `strategy/GATED_READ_DISCLOSURE.md:175` — "`ccdab112` carried **no** `consonance/` (tree `.gitignore CLAIMS.tsv README.md SOURCES.tsv`)".
No line asserts the pairing. **PASS.** (Bare `grep -n 'ccdab112'` returns only these two lines too.)

## Check 3 — Class changes match the decision exactly

Moved, as decided: `strategy/GATED_READ_DISCLOSURE.md:27` (§1 item 4), `:28` (§1 item 5),
`:139` (X-07 **`src/` component only**), `:140` (X-08), `:218` (U-1 decided YES),
`:175` (AD-6 resolved). Dated class-change markers appear at exactly `:27`, `:28`, `:37`,
`:139`, `:140`, `:175`, `:182`, `:218` — **no unnamed class moved**.

Everything else still reads as withheld/neutralised, untouched:
§1 items 1,2,3,6,7,8,9,10,11,12 → `strategy/GATED_READ_DISCLOSURE.md:24,25,26,29,30,31,32,33,34,35` all still begin "**…**" with no class note; `:37` explicitly states "items **1, 2, 3, 6, 7, 8, 9, 10, 11, 12** are unchanged".
X-01 `:133` `withhold`; X-02 `:134` `withhold`; X-03 `:135` `withhold`; X-04 `:136` `withhold`; X-05 `:137` `neutralise`; X-06 `:138` `neutralise`; X-09 `:141` `withhold`; X-10–X-12 `:142–144` unchanged. X-07 `:139` retains class `neutralise` and lists the non-moved roots. **PASS — no more, no less.**
(`V2`/`V3` have no row of their own in this file; the mapping is carried by §1 item 1 `:24` `tools/**` and items 2–3 `:25–26`, all unchanged.)

## Check 4 — The protective conclusion survives

Quoted verbatim:
- `strategy/WITHHELD.md:450`: "**The protective conclusion is unaffected and binding:** the implementation expression must not be republished, and no filing, declaration or exhibit may assert the work was never published."
- `strategy/GATED_READ_DISCLOSURE.md:37` (and repeated on `:27`, `:28`, `:139`, `:140`): "**Caveat:** the *fact* is already public, but the paper must still not republish this material and no filing may assert non-publication."

Both requirements (must not republish; no filing may assert non-publication) survive in both files. **PASS.**

## Check 5 — Red→green, non-vacuous

Copies: `scratch/uverad6/GATED_READ_DISCLOSURE.md`→`scratch/uverad6/GATED_READ_REVERTED.md`, `scratch/uverad6/WITHHELD_COPY.md`. Only the **copy** was reverted (line 27 truncated at the end of the original premise `src/sandbox.ts.`), by inline `python3`.

```
GREEN claim on line 27: 1        RED claim on line 27: 0
GREEN premise(src/sandbox.ts) on line 27: 1   RED premise on line 27: 1
diff real vs copy: 2 lines   (only line 27 differs)
real file after revert: 2 dated §1 class-change notes (untouched)
```
The class-change claim disappears from the reverted copy while the original premise text
remains; re-reading the real file shows the claim is back (2 notes). **Non-vacuous because**
the check is line-scoped: had I grepped the whole file, line 28's identical phrase would have
kept the count at 1 and masked a successful revert — I therefore anchored on `:27` only, and
the premise count (1 in both states) proves the revert removed the *annotation*, not the
*original*. The workspace files themselves were never edited.

## Check 6 — Nothing forbidden was edited — **partially unverified**

No backup of any of these files exists.
```
2026-10-15 16:32:27  strategy/ARCHIVE_WINDOW_CHECK.md
2026-10-15 16:29:03  strategy/DISCLOSURE_INVENTORY.md
2026-10-15 15:36:20  strategy/PRIOR_DISCLOSURE_AUDIT.md
2026-10-16 16:35:15  strategy/WITHHELD.md          <- edit
2026-10-16 16:35:15  strategy/GATED_READ_DISCLOSURE.md  <- edit
```
`ARCHIVE_WINDOW_CHECK.md`, `DISCLOSURE_INVENTORY.md`, `PRIOR_DISCLOSURE_AUDIT.md` and the
`papers/encoder-crossover-190/**` files all mtime **≤ 2026-10-16 15:02**, >1 h before the
16:35:15 edit → established unmodified by mtime.
**UNVERIFIED:** `papers/gated-read-batching/{MANUSCRIPT,GAPS,CLAIMS}.md` all mtime
**2026-10-16T16:34:27** — only **48 s** before the two strategy files. UFIXAD6's declared
write paths exclude `papers/`, but no backup exists, so mtime cannot rule out that this unit
(or a concurrent unit in the same batch) touched them. Reported, not assumed.

## Added check — date token is contradicted

`date '+%Y-%m-%d %H:%M:%S %Z'` → **2026-10-16 16:36:13 CDT**; the two edited files are
mtime **2026-10-16 16:35:15**. Yet every UFIXAD6 note is stamped **2026-10-15**:
`strategy/WITHHELD.md:450` and `strategy/GATED_READ_DISCLOSURE.md:27,28,37,139,140,175,182,218`,
and `grep -n '2026-10-16'` over both files returns **nothing (exit 1)**.
So the correction is dated a day *before* the records it corrects. **Caveat:** the whole
register already runs on 2026-10-15 stamps (UCAND1/WITH1/UFIX9 at `strategy/WITHHELD.md:3,13,412,417`),
so this is a workspace-wide date drift, not an AD6-only invention — but it is still a
contradiction a reader would hit. `next_unit_hint` carries the fix.

## Added check — "never published" phrase judgement (no edit)

`strategy/WITHHELD.md:152`: "**Withholding the blanket paper means the architectural/system
claim is never published and cannot be claimed as a published contribution.**"
`strategy/WITHHELD.md:398`: "**§4 is superseded.** The cost it priced — *'the architectural/system
claim is never published'* — **does not exist**."
**Judgement:** `:398` is legible as a cancellation (scare-quoted, explicitly superseding §4).
But `:152` is a **bold flat declarative with no inline supersession pointer**, so a reader
arriving at `:152` alone — in §4, ~250 lines before §8.7 — *could* mistake it for the workspace
asserting the work was never published, which is the very assertion §1 item 10 / `:33` forbids.
Not a contradiction of the withholding rule (it is the record of a cost that was rejected and
then superseded), but a legibility risk worth a forward pointer. Not edited.

## Design question — annotation of §1 items 4/5 is legible

Yes. At §1 the reader sees, on the item line itself (`:27`, `:28`), bold
"**Dated class change (2026-10-15, unit UFIXAD6) — moved to `already-disclosed` (window version only)**",
the evidence (35 `consonance/src/` blobs / 708,575 B / HTTP 200 on the old head), the caveat,
and the authority path; `:37` repeats it for both items. Who, what, when, on-what-evidence and
authority are all present — the only blemish being the contested date token above. No change made.

## Record

- `not_reproduced`: [] — every correction UFIXAD6 claimed was found applied.
- `contradicted`: date token `2026-10-15` in all 9 notes vs host/mtime `2026-10-16`.
- `unverified`: `papers/gated-read-batching/{MANUSCRIPT,GAPS,CLAIMS}.md` mtimes.
- No file outside `strategy/VERIFICATION_REPORT_AD6.md`, `orchestration/units/UVERAD6.md`,
  `orchestration/handoffs/UVERAD6.json`, `scratch/uverad6/**` was written; no `git` command
  was run against `/home/zer0null/Duval`.
