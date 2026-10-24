# UVER6 — independent verification of UCAND1's re-triage

**Unit:** UVER6 · **Role:** independent verifier (author of nothing checked) · **Date:** 2026-10-15
**Bound:** 50 tool calls (used 26) · **Status:** done
**Target:** `/home/zer0null/Duval` @ `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — read-only, never written.

## Card

**One purpose.** Re-derive UCAND1's 9/1/5 re-triage from the §G.1 table itself, test the standalone test
against #1 and the borderline set, cross-check `WITHHELD.md` against `TRADE_SECRET_AUDIT.md` §4.1 and
against the terminal fact that the mechanisms are already public (`PRIOR_DISCLOSURE_AUDIT.md`), and sweep
`PUBLICATION_STRATEGY.md` for residual live `#1` dependencies.

**Verdict: `pass-with-corrections`.** Sub-verdicts: `PAPER_CANDIDATES.md` §G = pass-with-corrections;
`PUBLICATION_STRATEGY.md` §13 = pass-with-corrections; **`WITHHELD.md` = fail as issued** (C1).

**Write paths (touched nothing else):** `strategy/VERIFICATION_REPORT_6.md`,
`orchestration/units/UVER6.md`, `orchestration/handoffs/UVER6.json`.

## Headline findings

1. **Split re-derived exactly: 9 publish / 1 withhold / 5 needs-author-decision** from the table's own
   cells — 15 distinct ids, none double-counted, none dropped. The 7-token grep is a duplicate test-cell
   value at #6/#8, **not** a test-vs-verdict disagreement (the card's worse hypothesis is falsified).
2. **#1's withhold is properly grounded — but not on the ground given.** `PAPER_DERIVATION.md:669–672` says
   what is quoted, but §6.4 is a scope limitation, not a releasability admission (overstated). The withhold
   survives on the paper's own contribution list + the M13 artefact inventory.
3. **`WITHHELD.md` over-claims secrecy for 12 of 13 mechanisms.** The public repo's
   `findings/PAPER-DERIVATION.md` is **byte-identical** to the Duval paper (46,636 B, sha256
   `d98c4359…`), and the audit's own *Disclosed at* column anchors M1–M10/M12/M13 in named lines of that
   paper. Only M11 is undetermined. The register conflates **mechanism** (public) with **implementation**
   (still private).
4. **The O-1 cost is moot and unpropagated** — still asserted as live in `WITHHELD.md:132`,
   `PUBLICATION_STRATEGY.md:470–477` and `PAPER_CANDIDATES.md` §G.4; `PUBLICATION_STRATEGY.md:47`
   ("Published artifacts | none") is false as to public disclosure.
5. **No mechanism missing from the register** (audit §4.1 = M1–M13; register §2 = M1–M13; no unsupported
   row), but the register's honesty fails on disclosure status and it omits the release-set leak.
6. **Five residual live `#1` references** (`:67`, `:274–275`, `:292`, `:296`, `:4`) are not covered by
   §13.1's corrections. **§13.4 is intact** — venue/$0/endorsement/TMLR/CC BY 4.0 unchanged, consistent
   with UVER1 and ULIC.
7. **#14's "no Consonance content" claim is contradicted** by its own source document (33 `Consonance`
   mentions, a dedicated §8). #13's equivalent claim reproduces cleanly.

## Containment

HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; `git status --porcelain` before = after =
4 pre-existing untracked paths, **attributed to the unrelated concurrent session** (identical, so no change
to attribute to UVER6). One scratch copy `/tmp/uver6_pd.md` written for hashing and deleted in the same
command. `repro/**` and `papers/**` untouched.

Full verdict, evidence and the four lists: [`strategy/VERIFICATION_REPORT_6.md`](../../strategy/VERIFICATION_REPORT_6.md).
