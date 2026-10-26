# VERIFICATION_REPORT_6 — independent verification of UCAND1's re-triage

**Unit:** UVER6 · **Role:** independent verifier (not the author of anything checked here) · **Date:** 2026-10-15
**Target of record:** `/home/zer0null/Duval` at HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — read-only, never written.
**Artifacts checked:** `strategy/PAPER_CANDIDATES.md` §G (L986–1145) · `strategy/PUBLICATION_STRATEGY.md` §13 (L412–515) · `strategy/WITHHELD.md` (new, 205 L) — cross-checked against `strategy/TRADE_SECRET_AUDIT.md` §4.1/§4.3/§5.1/§5.2 and the terminal update `strategy/PRIOR_DISCLOSURE_AUDIT.md` (UDISC1).

> **Standing of this verdict.** The re-derived split is **correct**. Two of the three artifacts need
> corrections; **`WITHHELD.md` as issued is `fail` and must not be relied on as evidence of reasonable
> measures until it is corrected under its own §6 change control.** See C1.

## Overall verdict: `pass-with-corrections`

| Artifact | Sub-verdict | Why |
|---|---|---|
| `PAPER_CANDIDATES.md` §G | **pass-with-corrections** | Split re-derives exactly (9/1/5 from the table's own cells); test applied consistently for 13/15 rows; corrected on C4 (grep-artifact explanation), C5 (#14 content claim), O1 (#1's §6.4 gloss). |
| `PUBLICATION_STRATEGY.md` §13 | **pass-with-corrections** | §13.1/§13.2 errata are coherent and §13.4's "unaffected" set reproduces against UVER1/ULIC; corrected on C2 (O-1 cost moot), C3 (`:47`), O5 (residual live #1 refs). |
| `WITHHELD.md` | **fail** | C1: M1–M8, M9, M10, M12, M13 are registered `withhold` when they are already generally known from a public repository; C2 (O-1 cost), C3 (W1's premise), C6 (M11 "the one unsettled entry"). A register that claims secrecy it does not have is worse than none. |

---

## 1. Contradicted, each with its replacement

### C1 (severe) — `WITHHELD.md` §2 registers as withheld twelve mechanisms that are already public

**Claim.** `WITHHELD.md` §2 assigns status `withhold` to M1–M13, and §5 lists the register as the first
"measure on record" for a trade-secret position.

**Falsified.** I re-fetched the public artifact UDISC1 identified and hashed both sides myself:

```
Duval/docs/research/PAPER_DERIVATION.md  sha256 d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802  46636 B
raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/main/findings/PAPER-DERIVATION.md
                                         sha256 d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802  46636 B   HTTP 200
```

**They are byte-identical — this resolves UDISC1's `UNVERIFIED` #1 upward from "semantically identical" to
"identical".** `TRADE_SECRET_AUDIT.md` §4.1's own *Disclosed at* column anchors every mechanism below in
`PAPER_DERIVATION.md` at named lines, and that file is public in full. So the disclosure is derivable
without re-reading the network copy:

| Mechanism | Audit §4.1 anchors it in `PAPER_DERIVATION.md` at | Status on the corrected facts |
|---|---|---|
| M1 abstract `:14–16`, §1.3, §4.2, §5.1, §5.5 | yes | **already public** |
| M2 §4.2 `:219–223`, `:236–240` | yes | **already public** |
| M3 §4.2 `:249–252`, §4.6 `:414–419` | yes | **already public** |
| M4 §4.3 `:257–292`, §5.2, §5.6 | yes | **already public** |
| M5 §4.3b `:301–331`, §5.2, §6.3 | yes | **already public** |
| M6 §4.4 `:336–356` | yes | **already public** |
| M7 §4.5 `:380–397`, §4.6, fixture | yes | **already public** |
| M8 §4.6 `:421–444`, §5.4 | yes | **already public** |
| M9 §5.5 `:600–611` | yes | **already public** (UDISC1 said `cannot determine`) |
| M10 §1.3 `:63–64`, §4.4, fixture | yes | **already public** (also verbatim in the public profile README) |
| M11 schema + fixture only | **no paper anchor** | `cannot determine` (would need public `DECISION_LOG.md` D-007–D-099) |
| M12 §4.1.1 `:179–185`, §4.2 `:250–251` | yes | **already public** (UDISC1 said `cannot determine`) |
| M13 §7 `:690–697`, §8 `:711–719` | yes | **already public** (UDISC1 said `cannot determine`) |

I additionally confirmed the second disclosure channel live: the public profile README
(`Aswin-Ram-K/Aswin-Ram-K`, fetched 2026-10-15) states *"Enforcement by absence, not refusal"* and the
capability-materialisation/digest A/B; `WHITEPAPER.md` = HTTP 200 / 16,323 B; `decisions/DECISION_LOG.md`
= HTTP 200 / **339,879 B**.

**So 12 of 13 mechanisms are already generally known; only M11 is undetermined, and only because it was
not read.** UDISC1's 9-of-13 was a floor; the byte-identical hash raises M9/M12/M13 to *already public* and
leaves M11 as the single open row.

**Replacement (for §2, per mechanism).** M1–M10, M12, M13 status →
*"already publicly disclosed — `Aswin-Ram-K/publish-present-compete` (public ≤ 2026-10-10; all MIT) plus the
public profile README; no longer protectable as a trade secret; `35 U.S.C. §102(a)(1)` printed publications
dated 2026-10-01/08/10. Correctly withheld as a **release** decision only."*
M11 → *"cannot determine; the public `DECISION_LOG.md` (99 decisions, D-007–D-099 unread) very likely
contains the taxonomy."* And §2's frame sentence must change from "core mechanisms (withheld)" to
**"core mechanisms — already public (release-side controls only); the residual secret is the
implementation"**, matching UDISC1 §5's boundary (`src/**`, concrete types, code-level state catalogue,
private corpora, `tools/**`, `CONSONANCE.md`/monograph). **The register's conflation of *mechanism*
(public) with *implementation* (private) is the defect; correct the register, do not reword it.**

### C2 (severe) — the O-1 cost is asserted as a live sacrifice in all three artifacts; it is moot

`WITHHELD.md:132` (*"the architectural/system claim is never published and cannot be claimed as a published
contribution"*), `PUBLICATION_STRATEGY.md:470–477` (§13.3) and `PAPER_CANDIDATES.md` §G.4/§G.2 all price a
cost that does not exist: the architectural claim **is** published, dated, authored and citable (A2/A3).
DISC1 §5 states this; it has not propagated into UCAND1's three files — a workspace grep for
`publish-present-compete` returns **`strategy/PRIOR_DISCLOSURE_AUDIT.md` only**.

**Replacement (all three files).** *"The cost UTS1 priced (a never-published architectural claim) does not
exist: the claim is already public (A1/A2/A3). The consequence inverts — the (B)(5) 'published
contribution' question must now be answered with a **prior-disclosure date of ≤2026-10-10** attached, and
the residual value being protected is the implementation, not the mechanism."* The §13.3 sub-bullets
((B)(6), (B)(1), (B)(4) unaffected) survive; only the premise sentence and the "deliberate cost" framing
fail.

### C3 — `PUBLICATION_STRATEGY.md:47` "Published artifacts | **none.**"

True as to DOI/arXiv/proceedings; **false as to public disclosure.** It is the row every later unit quotes
(including `PRIOR_DISCLOSURE_AUDIT.md:153`).
**Replacement.** *"Published artifacts: **no DOI, no arXiv id, no proceedings entry.** Publicly disclosed:
yes — `github.com/Aswin-Ram-K/publish-present-compete` (public, MIT, last commit 2026-10-10) carries the
whitepaper, the decision log, 15 pre-registrations and `findings/PAPER-DERIVATION.md` byte-identical
(sha256 `d98c4359…`) to `docs/research/PAPER_DERIVATION.md`."*

### C4 — `WITHHELD.md` W1's premise, and §5's use of the register as a measure

W1 is registered as withheld with the reason *"fails the standalone test by its own admission … publishes
~16 mechanism sections"*. The second clause is true (audit §5.1). The **premise** is void: the file is
public byte-for-byte, so *"withheld: not edited, not abstracted, not fixed"* protects nothing.
**Replacement (W1 "Why withheld").** *"The document is already public (see C1/C3); withholding it here is a
**programme decision not to republish or repackage it**, not a secrecy measure, and §5 item 1 cannot be
listed as a measure protecting this item."* The standalone-test reason survives independently (see §3.1).

### C5 — `PAPER_CANDIDATES.md` §G.1 `#14`: "no mechanism, no Consonance content" is false of the document on disk

The candidate's source document is `docs/research/AGENT_HARNESSES_2026.md` (823 L, per §D `:835`).
I grepped it: **33 occurrences of `Consonance`**, and a dedicated **§8 "Implications for Consonance"**
(`:679–773`) that states the kernel vocabulary outright — *"None of them **materialise** capability per
state transition"*, *"a worker whose class materialises nothing has **no broker object at all**"*,
`StateClass` role definitions, `SandboxSpec` mounts, *"`Budget` in the state envelope, enforced by the
reducer, is the mechanism"*, *"a **typed, content-addressed ledger** where each node also carries its grant
set"*, *"the gate chain"*; and `:374–376` names `Consonance's SandboxSpec`/state recording.
**Replacement (#14's reasoning cell).** *"The survey half survives **only if §8 and the §4.4 Consonance
inference are excised** — as the document exists on disk it is not 'no Consonance content' (33 `Consonance`
mentions; M1/M8/M12-adjacent vocabulary in §8)."* (Secrecy-wise this is now moot per C1; the claim as
written is still false about the content.)

### C6 — `WITHHELD.md` §6 "M11's disposition is open and is **the one entry in §2** that is not settled"

Audit §4.3/§5.2 put **M11 *and* M12 in the release set**, with M10/M7 disclosed through the rationale prose.
I re-verified the M12 half of that: `repro/encoder-crossover-190/fixture/reflex-decisions.ts` carries
**15 `src/` mentions** (`src/broker.ts`, `src/layer.ts`, `src/loop.ts`, `src/policy.ts`, `src/scope.ts`,
`src/state.ts`, …), and the sanitised variant still carries **9** (`src/broker.ts`, `src/loop.ts`,
`src/policy.ts`, …). So M12's flat `withhold` status is also untrue against the current release set.
**Replacement.** *"M11 **and M12** (and, through the rationale prose, M10 and M7) are already inside the
planned release set; the open decision covers the `DecisionKind` union, the schema, the rationales **and the
`src/**` path names**."*

### C7 — `PAPER_CANDIDATES.md` §G.1's own explanation of the 7-token grep is wrong

The self-flag reads *"the test column also carries that value for #6 and #8 **while the verdict column
differs**"*. Extracted per-row cells (awk on `|`-fields) show the verdict column **does not differ**:

```
L1026 #6  test=[needs-author-decision]  verdict=[needs-author-decision]
L1028 #7  test=[pass for the batching note; fail for the full scope]  verdict=[needs-author-decision]
L1029 #8  test=[needs-author-decision]  verdict=[needs-author-decision]
L1034 #13 test=[n/a — not an extracted project]                        verdict=[needs-author-decision]
L1035 #14 test=[n/a — and its position half fails]                     verdict=[needs-author-decision]
```

`grep -o needs-author-decision` over the table body = **7** = five verdict cells + the two *duplicate
test-column* cells at #6/#8. **Cause: a category error in the test column, not a test/verdict
disagreement.** The card's more serious hypothesis (test≠verdict for a candidate) is **not** what happened;
correcting the explanation does not move the split.
**Replacement.** *"7 = 5 verdict cells + 2 test cells (#6, #8) that carry the verdict token rather than a
test outcome; the two columns agree at #6 and #8. The test column there should read `fail` (limb b), per
its own reasoning."*

---

## 2. Priority 1 — the split, re-derived from the table itself

Counted from the §G.1 rows (15 rows; ids #1–#12, NC1, #13, #14 — matches §G's "14 original rows plus the
`NC1` insertion at 6½ … **15 candidates**", `PAPER_CANDIDATES.md:97`):

| Verdict | n | Membership |
|---|---|---|
| `publish` | **9** | #2, #3, #4, #5, **NC1**, #9, #10, #11, #12 |
| `withhold` | **1** | #1 |
| `needs-author-decision` | **5** | #6, #7, #8, #13, #14 |
| **total** | **15** | 15 distinct ids, **no double count, none dropped** |

**UCAND1's 9 / 1 / 5 is re-derived and correct.** It matches §13.1's prose membership exactly
(*"#2, #3, #4, #5, NC1, #9, #10, #11 and #12 … nine … #6, #7, #8, #13 and #14 … #1 is the sole
withhold"*) and §G.1's own count line `:1037`. The grep artifact is confirmed as the duplicate test-cell
value at #6/#8 (C7), **not** a real count change — the split is not affected.

---

## 3. Priority 2 — the standalone test applied independently

Test: *could this project be released on its own, without the rest of Consonance, and still make sense —
with its own fixture/harness/tooling that a reader could run?*

### 3.1 #1 (load-bearing) — verdict `withhold` **follows**, but not on the ground given

I opened `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md:669–672`. The quoted text **is present
verbatim**: `:669` *"Nothing was promoted into `src/`."* and `:671–672` *"every result here is a result
about **a model of the kernel**, built against its real types and its real hasher but not inside its
boundary."* So W1's quotation is accurate as far as it goes — **but the inference from it is not.**

`§6.4` is a **scope-limitation** section, not an admission about releasability. Its middle sentence — which
the ellipsis drops — cuts the other way: *"Every artefact lives in `tools/`, which is the operator's rule:
experiments land outside the kernel … The kernel is unchanged, so…"*. `tools/`-outside-the-boundary is the
condition under which a standalone harness could exist. The one clause that *does* support limb (b)
failing is the tail the audit's own wording keeps (*"built against its real types and its real hasher"*).
The corpus itself reads §6.4 this way — as a **systems-claim** liability, not a releasability finding:
`PAPER_CANDIDATES.md:156` (*"a result about a model of the kernel … a reviewer will call this 'a simulator
of your own kernel'"*), `:194` (*"If a reviewer treats the paper as a systems claim … it collapses"*),
`:925`. → **O1, `overstated`.**

**The withhold still follows, independently of §6.4 and independently of secrecy.** Limb (a) fails: the
paper's own contribution list makes *"the loop itself: observation stream → derived state → projection"*
contribution 2 (`:72–76`, quoted in audit §5.1), i.e. the paper's substance **is** the rest of Consonance;
removing it yields *a different paper*. Limb (b) fails: its §7 artefact inventory is the private `tools/**`
tree (M13). **Verdict `withhold` = correct; the reason to state is audit §5.1's 16 sections + the M13
inventory, not §6.4.**

**The question this leaves for the author (not decided here).** With the document already public under MIT
(C1), "withhold" now means only *"do not make #1 a publication step or repackage it"*. It no longer means
*"keep it secret"*, and it does not undo a disclosure dated ≤2026-10-10.

### 3.2 Borderline #6 — genuinely borderline, test column mislabelled

Test cell reads `needs-author-decision`; the reasoning in the same row says *"Passes limb (a) … but
**fails limb (b)**"*, and §G.3 #1 says *"limb (b) of the test fails **today**"*. The contingency (an
unbudgeted neutral emitter) is a real reason not to route straight to `withhold`, but the test column
should read `fail (limb b)`, not the verdict token (C7). **Deciding question is stated and specific**
(§G.3 #1: re-implement a neutral emitter, or publish the finding and accept non-reproducibility). Passes
as "genuinely borderline"; fails only on column hygiene.

### 3.3 Borderline #7 — genuinely borderline, test and verdict consistent

Test cell: `pass` for the batching note, `fail` for the full scope as written; verdict
`needs-author-decision`. §G.2 (#7) splits finding (i) from mechanism (ii), and §G.3 #2 gives a deciding
question with a direction (the batching note). **Verdict follows from the test; the one constraint is the
M10 gate/absence machinery in the extractor, correctly named.** No correction.

### 3.4 Borderline #8 — test column token again; question stated

Test cell and verdict are both `needs-author-decision`; the reasoning identifies the projection arm as the
kernel's derived-state projection (M1/M2) and §G.3 #3 states the deciding question with a direction
(*"the evidence points **no**"*). Same column-hygiene point as #6; substance holds. (Note also §G.1's own
*"It is also `needs new experiments` (n=4/cell) on its own terms"* — a second, independent reason it is not
shippable today.)

### 3.5 The two surveys — one survives on its content; one does not

- **#13 — `survives` CONFIRMED on content, not assertion.** Source doc
  `docs/research/LONG_HORIZON_EVALS_2026.md` (1,529 L): `Consonance` = **0**, `observation stream` = 0,
  `enforcement by absence` = 0, `DecisionKind` = 0, `src/` = 0, `derived state` = 0. It is a field survey
  as claimed. (Its *utility* is a separate, author-level question, as §G.3 #4 says.)
- **#14 — `survives` CONTRADICTED as written.** See **C5**: 33 `Consonance` mentions and a §8 kernel section.
  The survey/position partition is right in principle; the parenthetical *"no Consonance content"* is false.

### 3.6 Consistency of the test's application

13 of 15 rows apply the stated rule mechanically; #6 and #8 carry a verdict token in the test column (C7);
#7's dual test value is legitimate and explained. **No candidate's verdict was dodged into
`needs-author-decision` without a named deciding question** — all five have one, in §G.3.

---

## 4. Priority 3 — the WITHHELD register against the audit

**Completeness (no missing, no unsupported mechanism).** Audit §4.1's `withhold` block is exactly
**M1–M13 (13 rows)**; `WITHHELD.md` §2 is exactly **M1–M13 (13 rows)**. Every audit mechanism has a register
row and the register adds none the audit does not support. The register's names-only convention is declared
(§2 preamble, *"the names are sufficient here; the disclosures themselves are what must not be
republished"*), so M12's condensed wording is compliant, not lossy.
**→ No mechanism in the audit is missing from the register; no register row lacks audit support.**

**Honesty / over-claim.**
1. **12 of 13 mechanisms claim a secrecy they do not have — C1 (contradicted).** The register is meant to
   be *"documented, dated and deliberate rather than accidental"* (§purpose); the accidental-and-now-public
   fact is exactly what it omits.
2. **The release set is listed as a protective measure while carrying M10/M11/M12 — C6 + O2.** §5 item 3
   *"The release set excludes"* is strictly true of W5/W6 only. Re-verified leak: the original fixture has
   **15 `src/` mentions** and `:292` verbatim (*"Scope narrowing is one of the four constructions of the
   permitted set, and it is enforced at the broker boundary — src/scope.ts, consulted by src/layer.ts's
   invoke() … absence, not a refusal, and not a gate in admit()"*); UTS1's individually cited vocabulary
   counts reproduce **exactly** — `StateClass` 32, `grantPolicy` 30, `manifest` 30, `expanded[]` 6,
   `admit()` 4, `content-addressed` 3. **The register does not claim the subset is clean** (§2 M11, §6,
   §7.1 flag M11/rationales), so this is over-claim-by-omission, not a clean-subset claim.
3. **§7.3 defers correctly** (*"whether any already-published external material discloses a mechanism …
   `TRADE_SECRET_AUDIT.md` §5.2–§5.3 … is the authority"*) — but §7 frames the question as *already-published
   **external** material*, when the decisive object is the author's own public repo. The register cites the
   audit accurately (**no paraphrase-into-a-stronger-claim found**); its failure is what it does not cite.

**New, and not in the register:** a **second** repro directory exists on disk,
`repro/encoder-crossover-190-SANITISED/` (with `redact.py`, `MANIFEST.json`, `LICENCE_TODO.md`), while
§3(d) still says *"The single release set that exists today"*. In the sanitised fixture the `:292` rationale
is gone (`broker boundary` = **0**) but **9 `src/` mentions remain** (`src/broker.ts`, `src/loop.ts`,
`src/policy.ts`, …) — M12's scrub rule is still unmet there. `LICENCE_TODO.md` also says the code licence is
**NOT YET DECIDED** (*"Do not publish this subset until this file is resolved"*), which sits against §3(c)'s
PolyForm Noncommercial 1.0.0 statement. `repro/**` is another unit's write path; I record, I do not edit.

---

## 5. Priority 4 — residual `#1`-as-live references and §13.4's intactness

### 5.1 Residual references a reader could act on

`PUBLICATION_STRATEGY.md` is append-only, and §13.5 deliberately does not rewrite §0/§6/§9 — so a
pre-errata `#1` mention is **not** automatically a defect. What follows is the subset **not covered by any
of §13.1's four named corrections** (Step 2 void; the global *"every occurrence of '#1' as a target is
replaced by the next extracted-project paper"*; the §6 timeline rows; §3.3's `CITATION.cff` gap):

| Line | Text | Why it misdirects |
|---|---|---|
| `:67` | MLSys row: *"#1 as a systems paper is the corpus's own stated stretch (§6.4 …)"* … *"Do not spend the window on it **unless #1 is already assembled**"* | Invites assembling #1 inside the §2 table that §13.4 declares *unaffected*. The global replacement rule cannot repair it: the sentence's logic is *about* #1-as-systems-paper. |
| `:274–275` | §8 category choice: *"Sensible primaries are … cs.SE or cs.PL (**#1**, durable-execution/journaling angle)"* | Assigns a primary arXiv category to #1; §13.4 declares §8 unaffected, so the assignment is left standing. |
| `:292` | §9 *"Best for | **#3, #1, #4 — all three, immediately**"* | Only the TMLR column is corrected by §13.2; this arXiv cell still carries #1 as a target. |
| `:296` | §11: *"then (c) TMLR for **#3 and #1**"* | The execute-list; §11 is not in §13.4's unaffected set and is not named in §13.1, so it is an uncorrected live instruction. |
| `:4` | Grounding: the input sequence *"(**#3 first, #1 second, #4 third**)"* | Superseded only by implication; it is the document's stated input. |

Not defects (correctly marked corrected): `:22` (§0 Step 2 → void), `:111` (§3.3 `CITATION.cff` → corrected),
`:196`/`:201`/`:204`/`:205`/`:211`/`:212` (§6 timeline → corrected in place), `:332` (§10 checklist item 6
→ §13.4), `:62`/`:61`/`:64` (venue cells → global replacement rule).

**No residual makes a withheld paper *publishable*; all five would misdirect a reader about which paper to
prepare next.**

### 5.2 §13.4's "unaffected" set — intact

| §13.4 claim | Independent basis | Disturbed? |
|---|---|---|
| Venue comparison table (§2) | `UVER1.json`: *"PUB L62/L63/L64 minimum-cost premise … no missed fee, $0 premise holds"*; `zero contradicted claims` | **No** |
| $0 route / free-DOI mechanics (§0 Step 0, §3) | `UVER1` L20/L32: arXiv free-DOI + DataCite, Zenodo duplicate-DOI policy verbatim | **No** |
| JOSS block + unblock edge (§5) | `UVER1` L23; the L185 conditionality correction is present at `:292` as `[corrected by UFIX2 per UCAP1/UVER1]` | **No** |
| arXiv endorsement (§8) | `UVER1` did not contradict; §13.1 keeps #3 as first submission, so §8's "week 1" instruction stands | **No** |
| (a)/(b)/(c)/(c′), TMLR conclusion (§9) | `UVER1` L22 (TMLR ~9 weeks, no surveys, technical-correctness framing, ISSN) | **No** — only the target-paper mapping changed (§13.2) |
| Papers **CC BY 4.0** | `ULIC.json` (`tmlr_ccby_confirmed: yes`); `papers/encoder-crossover-190/AVAILABILITY.md:3,52`, `CHECKLIST.md:77` | **No** — code/artifact PolyForm NC split intact (`CODE_LICENSING_STRATEGY.md:24,160`) |

**§13.4 is confirmed: the venue/$0/endorsement/TMLR/CC BY 4.0 conclusions are not disturbed by §13.**

---

## 6. The four lists, separated

**`contradicted` (wrong; replacement given): C1** M1–M10/M12/M13 registered withheld but already public;
**C2** O-1 cost asserted as live (WITHHELD §4, PUB_STRATEGY §13.3, PAPER_CANDIDATES §G.4);
**C3** `PUB_STRATEGY:47` "Published artifacts | none."; **C4** W1's secrecy premise + §5 measure list;
**C5** #14 "no Consonance content"; **C6** §6 "M11 … the one entry not settled" (M12 also in-release);
**C7** the 7-token grep explanation.

**`overstated`: O1** #1 *"fails the standalone test by its own §6.4 admission"* — quote verbatim, inference
is a gloss on a scope-limitation section (verdict survives on audit §5.1 + M13);
**O2** WITHHELD §5 item 3 listing the release set as a measure while it carries M10/M11/M12;
**O3** #14's position-half reason *"restates W3, the withheld architectural claim"* — W3 is not withheld in
fact (A1/A2); the real defect is duplication, not disclosure;
**O4** §13.4's *"unaffected"* for §8/§9 is broader than the corrections actually applied (see 5.1).

**`not_reproduced` (coverage limits, not author failures):** M11's public-disclosure status — needs the
public `DECISION_LOG.md` D-007–D-099 (339,879 B, unread); the other 6 of the author's 19 public repos;
UTS1's *"335 lines match kernel-internals vocabulary"* — every individually cited count reproduced exactly
(32/30/30/6/4/3) and 68 lines match `src/` ∪ that vocabulary, but the 335 figure's full vocabulary set is
unspecified; the release-set file count (43 on disk vs `EXCLUDED.md`'s 42).

**`unverified`:** whether `publish-present-compete` was ever private before 2026-10-08/10 (filing-date
relevance); whether `repro/encoder-crossover-190-SANITISED/` is the intended release set; whether the
register's legal status was ever reviewed by counsel (it is explicitly *"NOT LEGAL ADVICE"*); whether
`findings/LANDSCAPE.md`'s competitive read matters to the plan.

---

## 7. What would change my verdict

- **C1 would lift** if the register is re-issued (or appended, per its own §6) to record that M1–M10/M12/M13
  are already public and that only the implementation remains protectable. The **split would not move** —
  it is independent of the secrecy premise.
- **C5 would lift** if #14 is re-scoped to a survey with §8 excised and the claim reworded to *"survives if
  §8 is removed"*.
- **C2/C3 would lift** if the prior-disclosure fact is propagated into `WITHHELD.md` §1/§4,
  `PUBLICATION_STRATEGY.md` §13.3 and `:47`, and `PAPER_CANDIDATES.md` §G.4.
- **C7 would lift** by editing the two test cells (#6, #8) to `fail` — the count of 7 is *not* a problem and
  needs no change.
- **O1 would lift** if §G.1/W1 drop the *"by its own §6.4 admission"* clause and cite audit §5.1's 16
  sections + M13 instead. I would **not** move #1 off `withhold` on any evidence available.
- **The verdict would move to `fail`** if the split itself were wrong (it is not), if §13.4 had disturbed
  the UVER1/ULIC conclusions (it has not), or if any candidate's `publish` verdict depended on publishing a
  mechanism that `TRADE_SECRET_AUDIT.md` still protects (it does not — but C1 means that dependency is now
  moot in the other direction).
- **A `fail` remains on the table for `WITHHELD.md` alone** unless C1 and C6 are corrected; a register that
  a reviewer could falsify in one hash is not usable as evidence of reasonable measures.

---

## 8. Containment

**Target `/home/zer0null/Duval`:** read-only throughout (`git rev-parse`, `git status --porcelain`, `read`,
`grep`, `wc`, `sed`, `awk`). **HEAD before = HEAD after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`.**
`git status --porcelain` before = after = the same 4 pre-existing untracked paths (`.ci-trunk.txt`,
`.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`) — **attributed to
the unrelated concurrent session, not to UVER6** (identical before and after, so no change to attribute).
One scratch network copy was written to `/tmp/uver6_pd.md` for hashing and deleted in the same command
(`rm -f`). **No file in `strategy/`, `repro/` or `papers/` other than this report was written.**
