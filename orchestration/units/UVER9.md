# UVER9 — independent verification of `strategy/WITHHELD.md`'s M11 correction (UFIX9)

**Unit:** UVER9 · **Date:** 2026-10-15 · **Bound:** 35 tool calls (used 23). **Status:** done.
**Verdict:** `pass-with-corrections`. **Contradicted: none.**
**Author checked:** UFIX9 (not this unit).

## Purpose (one)
Falsify UFIX9's M11 correction in `strategy/WITHHELD.md` against its primary source,
`strategy/DISCLOSURE_INVENTORY.md` (UDISC2), and confirm the register's protective claim did not move.

## Checks run
1. `DISCLOSURE_INVENTORY.md:74` — M11 `disclosed — settled by UDISC2`, citing fetched public
   `decisions/DECISION_LOG.md` D-024/D-045/D-048 with a verbatim D-024 quote; `:78` tally
   `13 disclosed · 0 not disclosed · 0 cannot determine`; `:5`/`:15`/`:60` confirm fetch-and-quote.
   `:215` + `:229` — `worker.class` / `context.package` not located. **All reproduced.**
2. Hash question, **both** directions: no digest in UDISC2's M11 row; `WITHHELD.md` contains exactly
   one 64-hex digest (`:266`, the legitimate `d98c4359…` `PAPER-DERIVATION.md` hash). **No hash
   invented; none claimed.**
3. RED→GREEN on a scratch copy (`/tmp/uver9/red/WITHHELD.md`, `sha256 be5872a0…`): reverting the M11
   row to stale `undetermined` → `FAIL (2)` citing the missing `disclosed` verdict and the unmarked
   `undetermined`; the real file → `PASS`. Real-file digest identical before/after (`5c0ff0c2…`).
4. Append-only spot-check, 12 loci. 11 carry a dated `CORRECTED`/`WITHDRAWN`/`SUPERSEDED` marker with
   the superseded wording retained. **§5 (`:184–190`) carries no marker** and its stale list is
   not quoted anywhere on disk → `overstated` (LOW).
5. Residual sweep: every `Twelve of the thirteen` / `12 of 13` / `undetermined` occurrence is either
   stale text with an adjacent withdrawal or a change-log description. **None live, none missed.**
6. Protective conclusion: §8.3 unchanged, implementation-only, no mechanism row added; UDISC2's
   `journal.ts` 404-at-every-tested-ref vs control `README.md` 200 evidence (`:17`, `:177–182`,
   `:184`) still supports "implementation still private". **Not widened, not narrowed.**

## Finding (one)
`overstated`, LOW — UFIX9's change log `:413` and its card claim §5's stale statement was *marked
withdrawn, nothing deleted*. §5 has no UFIX9 marker (zero `UFIX9` matches between `:107` and `:208`),
and the block citing §8.9 is attributed to UWITH1, so it cannot be UWITH1's text. Replacement:
quote the superseded §5 list in a dated UFIX9 note, or narrow the change-log claim. §6's letter
(nothing in §1–§2 edited in place) is **not** breached — §5 is not §1–§2 — and the substituted text
is true, so this is not `contradicted`.

## Limitation
`WITHHELD.md` is untracked in the workspace git and has no snapshot, so §5's pre-edit bytes are
`not_reproduced`; no web tool was used, so D-024 was checked against UDISC2's on-disk record.

## Containment
`WITHHELD.md` never written (identical digest); `/home/zer0null/Duval` never written, no `git` there;
write paths exactly: this report, this card, `orchestration/handoffs/UVER9.json`.
