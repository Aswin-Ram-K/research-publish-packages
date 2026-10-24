# UVER7 — independent verification of the licence templates (ULIC2)

**Purpose.** Independently verify the 7 drafted files in `strategy/licence-templates/` (author: ULIC2),
with priority on the deployable licence text — a corrupted/truncated licence is worse than a missing one
because it looks authoritative. Try to falsify; do not confirm.

**Write paths (exactly three, all touched).**
- `strategy/VERIFICATION_REPORT_7.md`
- `orchestration/units/UVER7.md`
- `orchestration/handoffs/UVER7.json`

**Hard bound.** Max 45 tool calls. Used **21**. No blocker hit.

**Read-only target.** `/home/zer0null/Duval` — no write, no `git` command, no hook. `LICENSE` md5
`eb1e647870add0502f8f010b19de32af`, mtime 2026-09-28 — **unchanged**. Templates **not edited**; the one
mutation used in the sensitivity test was applied in memory through a pipe.

## Verdict: `pass-with-corrections`

The worst outcome did **not** occur: the licence text is not corrupted, truncated or subtly edited.

### What was verified (method, not assertion)
1. **Re-fetched** `https://polyformproject.org/licenses/noncommercial/1.0.0.txt` myself — HTTP 200,
   4,563 bytes, sha256 `ffcca388…`. Drafted body (`RELEASED-PIECE/LICENSE:10-140`) — 4,563 bytes, same
   sha256. `diff -u` **empty (exit 0)**; `cmp` **IDENTICAL**. **ULIC2's byte-identical claim holds.**
2. **Sensitivity / red→green:** mutating one character in memory made the same `diff` report DIFFERS, so
   the comparison is not vacuous — a silent edit cannot pass. Separately, the AGPL grep pattern matched
   Duval's real AGPL `LICENSE` once, proving that grep non-vacuous too.
3. **Completeness:** all 15 upstream sections present, in order; none missing. The two checklist items
   that *cannot* appear upstream — `END OF TERMS AND CONDITIONS` and `Contributions` — are absent from
   PolyForm 1.0.0 itself, so their absence is faithful (`not_reproduced`, not a defect).
4. **Priority 2 clauses** quoted verbatim: `Personal Uses` covers at-home/hobby use; the
   "without any anticipated commercial application" qualifier excludes a business evaluating to buy;
   `Noncommercial Organizations` carries **"regardless of the source of funding or obligations resulting
   from the funding"** — real, unqualified, and the O-1 cost mitigation.
5. **AGPL:** no AGPL licence text anywhere in `licence-templates/**`; only 4 lines of prose in
   `PLACEMENT.md`, one quoting the 5-word title as evidence about the target.
6. **Other templates:** `PROPRIETARY-LICENSE.txt` coherent; `PLACEMENT.md` order correct + permanence
   warning present + §5 items 3–4 now read resolved/on-disk (underlying facts re-checked);
   `CONTRIBUTING.md` carries the hygiene rule and the name/logo reservation.
7. **Gaps:** `<CONTACT>` genuinely unfilled; academic-carve-out sentence genuinely unworded — and, in my
   assessment, **material** (see below).

### Corrections recorded (details in the report)
- **C1 `contradicted`** — `TRADE-SECRET-NOTICE.md:44-47` still declares `strategy/TRADE_SECRET_AUDIT.md`
  absent; it exists (507 lines / 48,851 bytes / 2026-10-15 15:31:34). UFIX5 fixed this in `PLACEMENT.md`
  §5.3 but not in the file that carries the pointer.
- **C2 `contradicted`** — `PLACEMENT.md:96` cites the SUPERSEDED markers at `:423`, `:590`; they are at
  `:433`, `:600`.
- **C3 `contradicted` (scope: target integrity)** — `/home/zer0null/Duval/.git/**` contains objects written
  **2026-10-15 15:32:23**, inside the build window, so "nothing changed" is false as stated for `.git`.
  Worktree and `LICENSE` are unchanged (newest worktree file 13:15:11). Attribution unknown; **not** a
  licence defect; routed to the main session.
- **3 `overstated`** — the "no free commercial evaluation" line is a sound *inference*, not quoted licence
  text; `README-PARAGRAPHS.md:37-38` calls the notice line "Placeholder-free" while printing placeholders;
  the name/logo reservation in `RELEASED-PIECE/LICENSE` is not propagated to forks by PolyForm's `Notices`
  clause (low severity — trademark is a separate right).

### The academic sentence — my plain view
**Draft it now. The omission is material and asymmetric against the author.** The licence grants
educational, public-research, public-health and government institutions free use *silently*. The Case B
README paragraph instead leads with "any commercial use requires a paid licence" and qualifies the free
grant as "personal, hobby, research and other **noncommercial** purposes" — so institutions reasonably
conclude they are on the paid side. The author then pays the full adoption cost of a non-commercial licence
and collects none of the benefit that the licence deliberately extends to exactly the audience he needs for
adoption and impact. The remedy is one sentence using the licence's own words, with no invented wording and
no legal risk — which removes the stated reason for deferral.

### Note for any future editor (load-bearing detail)
The byte-identity guarantee is defined by the delimiters in `RELEASED-PIECE/LICENSE`: everything from
`# PolyForm Noncommercial License 1.0.0` (line 10) to `of your licenses.` (line 140). **An edit made
*inside* those delimiters silently breaks it.** Additions must stay outside them.

### Handoff
`overall: pass-with-corrections` — the licence is deployable as-is; C1/C2 are text fixes inside the
templates (owned by others — I did not edit them), and the academic sentence is the one substantive
recommendation.
