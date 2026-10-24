# UFIX9 — reconcile `strategy/WITHHELD.md` to UDISC2's settled M11 finding

**Unit:** UFIX9 · **Date:** 2026-10-15 · **Bound:** 25 tool calls (used 23). **Status:** done.

## Purpose (one)
Correct the stale M11 status in `strategy/WITHHELD.md` so it matches UDISC2's settled
`disclosed` finding, using UWITH1's own §6 append-only change control (mark and quote as
withdrawn; never delete).

## Why it was stale
`WITHHELD.md` (UWITH1) was written from UVER6's **earlier** facts, before UDISC2 read
`decisions/DECISION_LOG.md`. It recorded 12 of 13 public and M11 `undetermined` at `§8.1`
(12-row table), `:104`, `§8.2` and the `:203–205` correction clause. Third instance this
session of a unit recording a fact true from an earlier report and false against disk.

## Evidence checked (step 1 — before any edit)
- `strategy/DISCLOSURE_INVENTORY.md` `:74` — M11 `disclosed — settled by UDISC2`, citing fetched
  public `decisions/DECISION_LOG.md` **D-024**, D-045, D-048, with D-024 quoted verbatim and
  naming exactly the audit's **six kernel namespaces**.
- `:78` — tally **13 disclosed · 0 not disclosed · 0 cannot determine**.
- `:215` / `§8.5` — nuance: **`worker.class`** and **`context.package`** not located in D-001–D-049.
- **No hash recorded by UDISC2 for M11** → its row cites the verbatim quote and says so; no hash invented.

## Edits (all marked, nothing deleted)
1. Header `:14` — 12-of-13 corrected to 13-of-13 with the UDISC2 citation.
2. `:104` §2 M11 row — disclosure status settled `disclosed`; release-set decision stays the author's.
3. §5 correction — public list now `M1–M10, M11, M12 and M13`.
4. §6 change-control clause — the `undetermined` half quoted as **WITHDRAWN**; the M12 half stands.
5. §7.3 — qualifier: M11 is disclosed via `DECISION_LOG.md`, not via the paper.
6. §8 preamble — `12 of the 13` corrected to 13 of 13.
7. §8.1 heading → `M1–M13`; **new M11 row** added (location D-024/D-045/D-048, date 2026-09-29,
   **MIT**, verbatim quote, explicitly **no hash**); hash-derivation note scoped to M1–M10/M12/M13.
8. §8.1 item 1 → `M1–M13`; item 2 prior-art dates extended to M11's 2026-09-29.
9. §8.2 heading marked **SUPERSEDED**; body closing sentence quoted as withdrawn; text kept as issued.
10. §8.5 — the `undetermined` clause quoted as withdrawn.
11. §8.8 change log — UFIX9 row added.
12. **New §8.9** — M11 is DISCLOSED; quote-not-hash; the `worker.class`/`context.package` nuance;
    and explicitly: **M11 being public does not weaken §8.3** (implementation still private —
    404 at every historical ref vs control README 200).

## Protective conclusion — unchanged
§8.3 still narrows the register to the **implementation** (`src/**`, `kernel/**`, concrete types,
private corpora, `tools/**`, weights, unpublished prose). M11's disclosure does not widen it.

## Write paths touched (exactly three)
`strategy/WITHHELD.md`, `orchestration/units/UFIX9.md`, `orchestration/handoffs/UFIX9.json`.
Target `/home/zer0null/Duval` never written; no `git` run there; no other strategy file touched.

## Not done
No re-audit of the mechanism question (UDISC2 settled it); no edit to `DISCLOSURE_INVENTORY.md`.
