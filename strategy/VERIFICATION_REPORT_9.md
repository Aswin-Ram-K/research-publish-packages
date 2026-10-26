# VERIFICATION REPORT 9 — `strategy/WITHHELD.md` M11 correction (UFIX9)

**Verifier unit:** UVER9 · **Date:** 2026-10-15 · **Bound:** 35 tool calls (used 23). **Status:** done.
**Object of verification:** [`WITHHELD.md`](WITHHELD.md) as corrected by **UFIX9** (13 of 13; M11 `disclosed`).
**Author checked:** UFIX9 ([`orchestration/units/UFIX9.md`](../orchestration/units/UFIX9.md)) — not this unit.
**Primary source:** [`DISCLOSURE_INVENTORY.md`](DISCLOSURE_INVENTORY.md) (unit UDISC2).
**Target of record:** `/home/zer0null/Duval` — **read-only, never written; no `git` run there.**
**Digest of the reviewed file at verification time (unchanged by this unit):**
`sha256 5c0ff0c250b595b1359c0b14f6a43d947da62ef82a0d7f3a1513b837ab1a327e`, 38,889 B,
mtime `2026-10-15T15:48:11` (UFIX9's own write time; UVER9 wrote nothing).

## Verdict: **pass-with-corrections**

**Contradicted: none.** Every substantive claim UFIX9 makes about M11's status, its source, its
hash status and the retained nuance **is reproduced at source**. One **process** claim — that §5's
stale statement was *marked* rather than replaced — is **overstated** (LOW severity, §3 below). The
protective conclusion is intact and is **not** widened. The M11 correction is sound and may be
relied upon; the change log's description of its own §5 edit should be narrowed or repaired.

---

## 1. Priority 1 — the M11 claim, verified at source (not from the correction)

| Check | Required reading | Found | Result |
|---|---|---|---|
| (a) M11 stated **disclosed** | `DISCLOSURE_INVENTORY.md:74` | `| **M11** | **Decision taxonomy and namespaces** — DecisionKind union + six kernel namespaces | **disclosed — settled by UDISC2** |` | **REPRODUCED** |
| (b) source is a **fetched public document** with a **verbatim quote** | `:74`, `:5`, `:15`, `:60`, `:31` | `:74` cites `decisions/DECISION_LOG.md` **D-024**, D-045, D-048, **MIT**, dated 2026-09-29, and quotes D-024 verbatim (*"Kernel (verified, first-class): `task`, `evidence`, `execution`, `capability`, `policy`, `decision`. Modules …"*). `:5` — *"live public fetches, unauthenticated, 2026-10-15. Every mechanism verdict below rests on a document this unit fetched and read in full."* `:15` — *"M9, M11, M12, M13 are each disclosed in a public document this unit fetched and quoted."* `:31` (P3) inventories `DECISION_LOG.md` (99 decisions) with licence **MIT**. `:60` defines `disclosed` as a fetched URL containing a verbatim settling passage. | **REPRODUCED** |
| (c) tally | `:78` | `**Tally: 13 disclosed · 0 not disclosed · 0 cannot determine.**` — verbatim | **REPRODUCED** |

`:74` says exactly what UFIX9 said it says. **No `contradicted` finding arises on the M11 question.**

## 2. The hash question — checked in **both** directions (no hash invented)

- **Direction A — did UDISC2 record a hash for M11?** No. The M11 row at `:74` carries **no** digest;
  its evidence cell is a quoted passage, and its `Where` cell is a document path plus decision ids.
  A regex sweep for a 64-hex digest in that row returns **zero** hits. The only digest in
  `DISCLOSURE_INVENTORY.md` relevant here is UDISC1/UVER6's `d98c4359…` for `PAPER-DERIVATION.md`,
  which is not used for M11.
- **Direction B — does `WITHHELD.md` assert a hash for M11?** No. `WITHHELD.md` contains exactly
  **one** 64-hex digest in its 454 lines — `:266`,
  `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`, the legitimate
  `PAPER-DERIVATION.md` digest corroborated by UVER6 and re-hashed by UWITH1. The M11 row `:293`
  says in terms: *"**UDISC2 recorded no hash for this row** — the evidence is a verbatim quote from a
  fetched public file, not a digest; none is invented here."* §8.9 `:431–434` repeats it (*"The
  evidence is a quote, not a hash … **No hash is invented.**"*), and `:272–274` correctly excepts M11
  from the hash-derivation argument that covers M1–M10/M12/M13.

**A hash was not invented, and the file does not claim one.** The mechanism the register relies on
here — quote in place of digest — is the honest one, and the exception is stated where the hash
argument is made, not buried.

## 3. The nuance survived (M11 disclosed ⇏ every member name public)

- `DISCLOSURE_INVENTORY.md:215` — *"**`worker.class` and `context.package`** — two `DecisionKind`
  members from the M11 audit wording — were **not located** in `DECISION_LOG.md` D-001–D-049. M11 is
  disclosed on the six namespaces plus five of seven kinds; these two strings are unconfirmed."*
  (also listed `UNVERIFIED` at `:229`, §8 item 5).
- `WITHHELD.md` carries it **without overstating M11 as fully enumerated**: `:436–440` (*"**M11 is
  disclosed; not every last member name is.** … those two strings are unconfirmed. Both statements
  stand together, and neither is allowed to swallow the other."*), `:453` (*"a named residue, not
  secrecy"*), and `:107` in the M11 row (*"`worker.class` / `context.package` remain unlocated"*).

**Reproduced.** M11 is not claimed to be exhaustively enumerated.

## 4. Priority 2 — RED→GREEN (the check can fail)

Harness (written to scratch `/tmp/uver9/`, never into `strategy/`): compares the M11 verdict cell at
`DISCLOSURE_INVENTORY.md:74` against the M11 status cell of `WITHHELD.md`'s §2 row, plus the tally,
hash-invention, stale-count-marker and nuance checks. Tested on a **scratch copy** (`/tmp/uver9/red/WITHHELD.md`,
`sha256 be5872a0…`); the real file was never opened for writing.

```
=== RED (scratch copy: M11 row reverted to the stale 'undetermined' state) ===
INVENTORY M11 verdict: **disclosed — settled by UDISC2**
WITHHELD  M11 status : **withhold — and already partially in the release set**; … M11's public-disclosure status is `undetermined` (§8.2) |
RESULT: FAIL (2)
   - WITHHELD M11 row does not carry the inventory verdict 'disclosed'
   - WITHHELD M11 row asserts 'undetermined' with NO withdrawal/correction marker
RED EXIT=1

=== GREEN (real strategy/WITHHELD.md) ===
RESULT: PASS — all 6 check groups hold
GREEN EXIT=0
```

**The comparison catches the stale state** (exit 1, with the contradiction named) and **holds on the
real file** (exit 0). Containment: the real file's digest before and after the run is
`5c0ff0c2…` — identical; `WITHHELD.md` was read-only throughout. A first iteration of the harness
false-positived on the §8.8 change-log row (which *describes* the withdrawn `12 of 13` string); the
marker rule was widened to accept an explicit withdrawal description, and the change log's framing of
that string as *withdrawn* is correct.

## 5. Priority 3a — append-only norm: 11 of 12 spot-checked loci carry a dated marker; **one does not**

| # | Locus | Superseded wording present? | UFIX9 marker? |
|---|---|---|---|
| 1 | Header `:14–19` | yes — *"**Twelve of the thirteen** mechanisms are already public"* retained | **yes** `:16–19` [CORRECTED … count is now thirteen of thirteen] |
| 2 | §2 M11 row `:107` | yes — `withhold — and already partially in the release set; open author decision` retained | **yes**, inline [CORRECTED … public-disclosure status is settled: `disclosed`] |
| 3 | **§5 `:184–190`** | **no** — the UWITH1 block now reads `M1–M10, **M11**, M12 and M13 are already public (§8.1, **§8.9**)` | **NO** |
| 4 | §6 `:206–212` | yes — *"the one entry whose public-disclosure status is undetermined"* retained | **yes** `:208–210` [WITHDRAWN as stale by UFIX9] |
| 5 | §7.3 `:241–244` | n/a (qualifier added) | **yes** `:241` (UFIX9, M11 via `DECISION_LOG.md`, not the paper) |
| 6 | §8 preamble `:253–255` | yes — *"**12 of the 13** mechanisms are already public"* retained | **yes**, same sentence [corrected … 13 of 13] |
| 7 | §8.1 heading `:259` | yes — previous heading quoted: *"this heading read M1–M10, M12 and M13"* | **yes** |
| 8 | §8.1 `:272–274` | yes — M11 excepted from the hash derivation | **yes** |
| 9 | §8.1 item 1 `:299–300` | yes — *"it read M1–M10, M12 and M13 before"* | **yes** |
| 10 | §8.2 `:318`, `:320–327` | yes — the whole `undetermined` body retained unedited | **yes** — heading SUPERSEDED + body closing WITHDRAWN |
| 11 | §8.5 `:376–379` | yes — the italic clause retained | **yes** [WITHDRAWN as stale] |
| 12 | §8.8 `:413` | n/a (change-log row) | **yes** (new row) |

### `overstated` (LOW) — the §5 claim is not reproduced

UFIX9's change log `:413` states *"the stale `12 of 13` / `undetermined` statements in the header,
§2's M11 row, **§5**, §6, §7.3 and §8.5 **marked withdrawn — nothing deleted**"*, and its card
(`orchestration/units/UFIX9.md`, *Edits* item 3) records *"§5 correction — public list now
`M1–M10, M11, M12 and M13`"*. **§5 contains no UFIX9 marker at all** (grep for `UFIX9` in
`WITHHELD.md` returns zero matches between `:107` and `:208`), and the block it sits in is attributed
to **UWITH1** while citing **§8.9** — a section UFIX9 created — so the current §5 text cannot be
UWITH1's. The stale list is not quoted anywhere on disk (grep for *"M1–M10, M12 and M13 are already
public"*: no match), whereas **every other** superseded statement in the file retains its original
wording beside its withdrawal. The §5 wording was therefore **replaced in place, not quoted as
withdrawn**.

**Not `contradicted`:** the substituted text is true, and §6's letter (*"Nothing in §1–§2 is edited in
place, ever"*) is not breached, because §5 is not §1–§2. **Not `fail`:** nothing a reader relies on
about M11 is wrong. What is overstated is the file's account of **its own** edit.

**Replacement (recommended to a future unit, not performed here — UVER9 does not rewrite the
register):** append to §5 a dated UFIX9 note quoting the superseded list, e.g. *"[UFIX9,
2026-10-15: this clause previously read **"M1–M10, M12 and M13 are already public (§8.1)"**; M11 is
now included, §8.9. The superseded wording is quoted here rather than deleted.]"* — or narrow the
change-log claim to *"§5's list updated in place (superseded wording not retained)"*.

## 6. Priority 3b — residual-string sweep: none missed, none live

| String | Occurrences | All marked/superseded? |
|---|---|---|
| `Twelve of the thirteen` | `:14` | yes — corrected `:16` |
| `12 of the 13` | `:254`; `:413` | yes — corrected in the same sentence `:254`; `:413` is the change log describing the withdrawn string |
| `12 of 13` | `:413` | yes — as above |
| `13 of 13` | `:17`, `:254`, `:413`, `:417` | correct (live) |
| `undetermined` | `:18`, `:107`, `:208`, `:209`, `:318`, `:323`, `:325`, `:376`, `:378`, `:412`, `:413` | **yes** — every occurrence is either (i) the stale text retained with an adjacent `CORRECTED`/`WITHDRAWN`/`SUPERSEDED` marker, or (ii) a change-log row describing the change. `:412` (UWITH1's row, *"M11 recorded `undetermined` (§8.2)"*) is an accurate historical record of what UWITH1 did, not a live claim. |
| `§7.1 M11 … open author decision` `:231` | 1 | **correct as it stands** — the *release-set* decision remains the author's (§8.9 `:450–453`); it does not assert a disclosure status. |

The harness encodes this rule (every stale count must have a correction/withdrawal marker within 500
characters) and it passes on the real file. **No residual "12 of 13" or live "undetermined" claim
survived UFIX9.** Nothing stale is asserted unmarked.

## 7. Priority 3c — the protective conclusion is unchanged and still matches the evidence

- **What §8.3 protects** (`:335–343`): `src/**`/`kernel/**` (W5), the **code-level state-class
  catalogue**, **private corpora**, `tools/**` (M13), **model weights** (W6), **unpublished prose**,
  **patents** (W7). It is **implementation-only**: no mechanism row, and design prose is expressly
  *publishable* (`:352–360`). The M11 change added **no row** to §8.3 and removed none; §8.9
  `:442–448` restates the boundary and states *"No reader should infer that M11's disclosure widens
  the protected set."* **Not widened, not narrowed.**
- **The evidence for "the implementation is still private"** is on disk and is the one required:
  `DISCLOSURE_INVENTORY.md:17` — at Consonance-era commit `06d618ca` the tree holds only
  `resume/ .gitignore CLAIMS.tsv LICENSE README.md SOURCES.tsv`, and **`consonance/src/journal.ts`
  and `src/journal.ts` both return HTTP 404 at every historical ref tested**; `:177–182` — the
  **control `README.md` at the same `06d618ca` ref returns HTTP 200**, i.e. the ref resolves and the
  *path* is absent; `:184` — *"the implementation … [is] not retrievable from any reachable commit."*
  `WITHHELD.md:444–445` cites this accurately. (Checked, **not** a finding: `WITHHELD.md` writes
  *"404 at every historical ref"* where `:17` says *"every historical ref **tested**"*; the stronger
  phrasing is supported by `:184`'s own conclusion, so no overstatement arises.)
- **Does the register now claim less or more than the evidence supports?** No, on the mechanism
  question — it claims **exactly** 13 of 13, with the two unlocated member names held back. The one
  stand-alone over-claim left in the file is §2's status column still reading `withhold` on M11
  (`:107`); it is explicitly subordinated by the header (`:13`, `:20–24`) and by the row's own inline
  correction, so a reader of the governing sections cannot be misled. Registered as a **residual
  readability risk**, not a claim exceeding evidence — and correcting it is the *author's* act under
  §6, not the verifier's.

## 8. Findings, separated

- **`contradicted` — [] (empty).** No claim in `WITHHELD.md` about M11, its source, its hash status,
  the tally, or the protective set is contrary to `DISCLOSURE_INVENTORY.md`.
- **`overstated` — [1]** UFIX9's change log `:413` / card *Edits* item 3 assert that the **§5** stale
  statement was *marked withdrawn, nothing deleted*; §5 carries no marker and its superseded wording
  is not retained anywhere on disk. Replacement text given in §3 above. **LOW severity; does not
  affect the M11 verdict.**
- **`not_reproduced` — [2]** (coverage limits, not author failures) (i) the **pre-edit bytes of §5** —
  `WITHHELD.md` is **untracked** in the workspace git (`git status` → `?? strategy/WITHHELD.md`,
  `git ls-files` → empty, no commits touch it), and no snapshot exists under another name
  (`glob **/WITHHELD*` → one file), so the §5 finding rests on the three internal-evidence facts in
  §3, not on a byte-level diff; (ii) **independent re-fetch** of `DECISION_LOG.md` D-024 — web tools
  were prohibited for this unit, so M11's disclosure is verified against UDISC2's on-disk
  fetched-and-quoted record (which itself asserts the fetch, `:5`, `:15`), not against the network.
- **`unverified` — [] (empty).** Nothing else in the M11 claim was left unchecked: the source line,
  the tally, the hash question in both directions, the nuance, the red→green behaviour and the
  protective conclusion were all reproduced on disk.

## 9. What would change my verdict

- **To `fail`:** `DISCLOSURE_INVENTORY.md:74` not reading `disclosed`; the tally reading anything but
  `13 · 0 · 0`; the M11 row citing no fetched public document or no verbatim passage; **any** hash
  asserted for M11 (none is — a 64-hex sweep of both M11 rows and of all of `WITHHELD.md` finds only
  the legitimate `d98c4359…`); `worker.class`/`context.package` dropped from `WITHHELD.md`; or a
  mechanism row added to §8.3.
- **To plain `pass`:** a §5 note quoting the superseded list (or a narrowed change-log claim). That
  is the whole of the correction.
- **A snapshot of §5** proving its pre-edit list would not change the verdict — it would confirm the
  `overstated` finding already recorded; it would only make the `not_reproduced` coverage limit go
  away.
- **An independent fetch showing D-024 absent from the public `DECISION_LOG.md`** would flip the M11
  conclusion itself to `contradicted`; that is the only route to a different substantive answer.

## 10. Containment

- `strategy/WITHHELD.md` — **not written by this unit**; digest identical before/after
  (`5c0ff0c2…`), mtime `2026-10-15T15:48:11` (UFIX9's write). The red test ran on
  `/tmp/uver9/red/WITHHELD.md`.
- `/home/zer0null/Duval` — not read in a way that writes, not written, no `git` run there.
- Files written by UVER9 (exactly three): this report, `orchestration/units/UVER9.md`,
  `orchestration/handoffs/UVER9.json`.
- No web tool was used. Tool calls: 23 of the 35-call bound.
