# UVER5 — independent verification of `strategy/TRADE_SECRET_AUDIT.md` (UTS1)

**Unit:** UVER5 · **Type:** independent verifier (not the author) · **Date:** 2026-10-15 (UTC)
**Bound:** max 55 tool calls · **Used:** 36

## One purpose

Falsify `strategy/TRADE_SECRET_AUDIT.md` (507 lines, unit UTS1): re-fetch its five statutory citations from
primary sources, test the inferences it flagged (`U5`, `U6`, `U8`) against authority, and re-count its
artifact claims against `/home/zer0null/Duval` and the release package.

## What was verified, and how

| Area | Method | Result |
|---|---|---|
| 18 U.S.C. §1839(3)(A)/(B), (4), (6)(B) | `web_fetch` Cornell LII `18/1839`, HTTP 200 | verbatim match |
| 18 U.S.C. §1836(b)(1) + DTSA citation | `web_fetch` Cornell LII `18/1836`, HTTP 200 | verbatim match; `130 Stat. 376` confirmed |
| 35 U.S.C. §102(a)(1) | `web_fetch` Cornell LII `35/102`, HTTP 200 | verbatim match |
| `U5` inference | `local_web_search` + `web_fetch` Ruckelshaus v. Monsanto, 467 U.S. 986 ¶46 | **inference is authority-backed**; U5 can be retired |
| `U6` | read §1839 (1)–(7) in full | "reasonable measures" **undefined** confirmed; sufficiency not fetched (coverage limit) |
| `U8` | attempted EUR-Lex | HTTP 202 empty — non-US unverified by either unit |
| 16-section list (`:11–16` … `:709–719`) | read `PAPER_DERIVATION.md` in full (719 lines) | all 16 contain disclosure; `#4 :195–214` is the weakest (inventory, not construction) |
| §1.4 contribution 2 `:72–76` | read | confirmed verbatim |
| §6.4 `:669–672` | read | confirmed verbatim |
| fixture counts | `grep -o … \| wc -l`; `wc -l` | StateClass 32, grantPolicy 30, manifest 30, expanded[] 6, admit() 4, content-addressed 3, file 2,220 lines — **all confirmed** |
| `:292` | `sed -n '292p'` | confirmed verbatim |
| "335 lines" | 4 stated vocabularies + python field parse | **not reproduced**: 317 / 121 / 419 / 519 |
| Mosaic (abstract + §4.4 `:339–345` + §4.3b `:321–325`) | read all three | **overstated** in magnitude; conclusion unaffected |
| `F1`–`F8` | 6 of 8 spot-checked | none is construction in disguise; F3/F4/F7/F8 measurements |
| `U9` (42 vs 43 files) | `find`, `MANIFEST.json` | **contradicted** — no discrepancy; 42 = manifest self-exclusion |
| `U10` (rationale consumed?) | grep released `.py`/`.ts` | no consumer found (partial advance) |
| `MANUSCRIPT.md` line cites | mtime + heading map | stale, **attributed to a post-audit concurrent edit** |

## Verdict

`pass-with-corrections` — see `strategy/VERIFICATION_REPORT_5.md`.
Five of five statutory citations hold verbatim. Four corrections, none overturning the strategy; **C1
strengthens** the audit's `needs-author-decision` call on the fixture.

## Write paths (only these three)

`strategy/VERIFICATION_REPORT_5.md`, `orchestration/units/UVER5.md`, `orchestration/handoffs/UVER5.json`

## Read-only discipline

Target `/home/zer0null/Duval`: HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`;
`status --porcelain` identical (same four untracked paths, concurrent session's dirt);
`find -newermt '2026-10-15 15:32:00'` returned nothing. No writes, no `git` state changes.
