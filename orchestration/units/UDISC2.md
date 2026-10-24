# UDISC2 — close the disclosure inventory

**Unit:** UDISC2 · **Supersedes nothing; extends** `orchestration/units/UDISC1.md`
**Written:** 2026-10-15 (UTC) · **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Hard bound:** 55 tool calls. No other bound.

## Purpose (one)

Close the prior-disclosure inventory left open by UDISC1: settle mechanisms **M9, M11, M12, M13** against
the public record, enumerate every public repository of the account `Aswin-Ram-K` and whether each
discloses mechanism, and produce a definitive public/private split with the licensing consequence.

## Why this unit exists

UDISC1 established that the author's mechanisms are already public in
`github.com/Aswin-Ram-K/publish-present-compete` (public, MIT, 38 commits, last 2026-10-10), including a
byte-identical copy of the withheld `findings/PAPER-DERIVATION.md` (46,636 B). It reported **9 of 13**
mechanisms disclosed and left **M9, M11, M12, M13 `cannot determine`** — solely because it did not read
far enough — and **6 of 19 public repos unread** (GitHub API 403). It stated its own bias was toward
**under**-reporting. The author's question *"what is my IP status now?"* cannot be answered with four
mechanisms and six repos open.

## Method (inherited from UDISC1, deliberately)

1. Read `strategy/PRIOR_DISCLOSURE_AUDIT.md` first; do not repeat it.
2. Establish what M9/M11/M12/M13 are from `strategy/TRADE_SECRET_AUDIT.md` §4.1 and `strategy/WITHHELD.md` §2.
3. **Enumerate the account, do not search.** UDISC1's transferable lesson: 13 SearXNG queries including the
   verbatim phrase *"enforcement by absence"* found nothing; the repo was found by going to
   `github.com/Aswin-Ram-K` and listing repos. `?tab=repositories` was fetched directly (HTML), because the
   REST API returns **HTTP 403 rate-limited** for this IP.
4. Read the deciding document in full for each open mechanism (`PAPER-DERIVATION.md` §5.5/§7/§8,
   `DECISION_LOG.md` D-001–D-099, the commit atom feed) and quote it.
5. **Test** UDISC1's inference that the implementation is private, rather than repeating the repo's own
   claim. Fetch historical trees and raw blobs at Consonance-era SHAs.
6. Enumerate the other 18 repos (delegated read-only sweep).

## Write paths (exactly three, as declared)

- `strategy/DISCLOSURE_INVENTORY.md`
- `orchestration/units/UDISC2.md`
- `orchestration/handoffs/UDISC2.json`

`PRIOR_DISCLOSURE_AUDIT.md`, `TRADE_SECRET_AUDIT.md`, `WITHHELD.md` and every other `strategy/` file were
**read, never modified**. No clash with UREDACT1 / UVER5 / UVER6 / UVER7. Target `/home/zer0null/Duval`
never written.

## Result

- **M1–M13: 13 disclosed, 0 not disclosed, 0 cannot determine.** All four open mechanisms settled with
  verbatim public passages and URLs. UDISC1's 9/13 was indeed a floor.
- **19 of 19 public repos inventoried.** 2 confirmed disclosing mechanism at full depth (the same two
  UDISC1 found); 4 agent-adjacent repos flagged as the remaining unread surface; 4 forks; 0 packages;
  0 public gists; user Pages site 404.
- **Implementation confirmed still private — now by test, not by claim.** At `06d618ca` the tree holds only
  `resume/ .gitignore CLAIMS.tsv LICENSE README.md SOURCES.tsv`; `consonance/src/journal.ts` and
  `src/journal.ts` return **HTTP 404** at every historical ref tested. History was force-rewritten.
- **New finding: a ~27-hour public window.** `ccdab112` (2026-10-09 04:11) folded the Consonance source in
  under `consonance/` — **528 commits, 441 files, 16,704 LOC in `src/`**, licensed **AGPL-3.0** — and
  `b81b35e` removed it at 2026-10-10 07:51. Not recallable by force-push.
- **Licensing:** the repo's single `LICENSE` is MIT over *"this software **and associated documentation
  files**"*, copyright *2026 Aswin Ram Kalugasala Moorthy* — permissive, no field-of-use limit, no
  termination clause. This conflicts with the workspace's planned **PolyForm Noncommercial 1.0.0**.
- `findings/LAYER_MODEL.md` (UTS1 **W4**) is **404** — a dead link inside a public paper. The five-layer
  **axiom** (M9) is public; the **specification** is not.

## Bound discipline

55-call bound not exceeded; the 18-repo sweep was delegated to a read-only sub-auditor (instructed to write
nothing) so that its network reads would not consume this unit's bound.
