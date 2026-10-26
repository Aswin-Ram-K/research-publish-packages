# C7-SCOPE-NOTE — close contradiction C7 in the record

**Purpose (one):** append one subsection to `experiments/ptr-engine/quality/RESULTS.md` stating that the
append-cost law is scoped to a single warm append (`experiments/miss-law/LAW.md:206`) while
`PREREG.json:30` billed a 4-turn run with it, so the billed-token figures in §3 and §4 are outside the
law's scope and inside a broken instrument.

**Bound:** 14 tool calls. **Used:** 14. **Status:** done.

**Write paths**
- `experiments/ptr-engine/quality/RESULTS.md` (append only)
- `orchestration/handoffs/C7-SCOPE-NOTE.json`
- `orchestration/units/C7-SCOPE-NOTE.md`

## What was done
1. Handoff stub written first so a death left a trace.
2. Baselines captured before editing: whole-file sha256 `b19e0210…f175`, `wc -l` 272,
   `head -n 190 | sha256sum` = `1f5c944e…5385`, greps above the append point (64:4, 12:18, 3.2:5).
   Backup at `/tmp/C7-RESULTS.before.md`.
3. Appended `### 4.2 The law's scope, and the regime this unit applied it to (2026-10-26)` immediately
   after §4.1 (i.e. after the normative blank line 190, before `## 5.` at line 191).
4. Nothing above line 190 changed: no renumbering, no table or number edits, Corrections untouched.

## Evidence
- `head -n 190 RESULTS.md | sha256sum` = `1f5c944e09c3dabc601d6e0a75066c5253eb7e64113fbb2206f3f8dca8a95385` (identical before/after)
- `wc -l` 272 → 302; `grep -c '4.2 The law'` = 1
- pre-existing numbers above the append unchanged (64:4, 12:18, 3.2:5; whole-file cap-3:4, residue-1:1)

## Sources quoted in the subsection
- `experiments/miss-law/LAW.md:206` — "a law about **one append onto an already-primed prefix**…"
- `experiments/ptr-engine/quality/PREREG.json:30` — `billing_law: uncached = (P1 mod 64) + L …`
- `runner.py:490`/`:495` — `L` computed as the whole prefix; `runner.py:585-596` — `cached_tokens` read, never persisted

## Assumptions
- The card's `runner.py:467` citation is stale: the `L` composition is at `runner.py:490` and `:495`.
- "`runner_v2.py` never run against a server" is the card's assertion; no v2 rows artifact was found, which
  is not proof, so no stronger claim is made.
- C7's presence in `experiments/ptr-engine/RECORD.md` was not asserted (outside write paths).

**Blocker** — none.
