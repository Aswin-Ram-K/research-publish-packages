# VERIFICATION_REPORT_5 — independent verification of `strategy/TRADE_SECRET_AUDIT.md` (unit UTS1)

**Unit:** UVER5 · **Role:** independent verifier, *not* the author · **Written:** 2026-10-15 (UTC)
**Artifact under test:** [`strategy/TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) (507 lines, unit UTS1)
**Target (read-only):** `/home/zer0null/Duval` at HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`

## VERDICT: `pass-with-corrections`

**Headline.** The five statutory citations **all hold verbatim** against primary sources re-fetched today.
The artifact claims are substantially accurate, and every reproduction-critical count UTS1 published
(`StateClass` ×32, `grantPolicy` ×30, `manifest` ×30, `expanded[]` ×6, `admit()` ×4, `content-addressed` ×3,
2,220 fixture lines, 7 `DecisionKind` kinds, 6 namespaces, 16-section list, §1.4 contribution 2, §6.4 quote)
**reproduced exactly**. The audit's *conclusions* survive — and one of them is **strengthened** by this
verification (see C1). Four corrections are warranted; **none overturns the strategy** the audit supports.

**Corrections, in severity order:**

| # | Severity | Correction |
|---|---|---|
| **C1** | **Material** | §5.2's cheap option — *"redacting the `rationale` and `namespaces` fields … removing the 335 lines that narrate kernel internals"* — is **insufficient**. The fixture's **`question` text is itself disclosure-bearing** and carries **more** kernel vocabulary than the rationales (71 vs 38 prose lines by my vocabulary; e.g. `:288`, `:571–575`, `:620–627`). Redacting rationale+namespaces would leave the questions naming `StateClass`, `GrantPolicy`, scope narrowing, `manifest`, `expanded[]`. Since the questions are the *only* load-bearing field (they are what the model is shown), the fixture is closer to `withhold` than to a cheap redaction. **The audit's own direction is right (M11 is time-sensitive); its proposed remedy understates the work.** |
| **C2** | Minor | `U9` is **contradicted**. There is **no file-count discrepancy**: `MANIFEST.json` declares `"files": 42` and states *"MANIFEST.json is the only file absent from its own list"*; `find` reports **43** = 42 + `MANIFEST.json`. The audit attributes the "42" to `EXCLUDED.md` — **`EXCLUDED.md` contains no file count at all** (it names 15 exclusion classes, E1–E15, which matches `MANUSCRIPT.md:832`). Replacement source: `repro/encoder-crossover-190/MANIFEST.json:36–40`. U9 should be **closed, not carried as unverified**. |
| **C3** | Minor | The `MANUSCRIPT.md` line citations **do not reproduce against the file on disk** (`§7 availability :772–780`; `## Data and code availability :738–754`). The on-disk file has `## Data and code availability` at **`:782`** and the quoted withholding sentence at **`:826–827`**. **Attribution: not UTS1.** `MANUSCRIPT.md` mtime `2026-10-15 15:35:50` **postdates** the audit's `15:31:34`, and `papers/**` is owned by concurrent units — the offset (+44 at that section) is consistent with a post-audit edit. Recorded as `not_reproduced` (stale), not as an author error. |
| **C4** | Minor | The mosaic claim (§5.3) is **overstated in magnitude** — see the judgement below. Direction and decision are unaffected. |

---

## 1. Priority 1 — the five statutory citations (all `confirmed`)

Re-fetched 2026-10-15 (UTC) from Cornell LII, the same mirror UTS1 used. Three fetches, HTTP 200.

| # | Claim in UTS1 | Verdict | Verified text (primary source) |
|---|---|---|---|
| **1** | **18 U.S.C. §1839(3)(A)/(B)** — two elements; (A) carries "reasonable measures", (B) carries "independent economic value … from not being generally known" | **`confirmed`** | **(A)** *"the owner thereof has taken reasonable measures to keep such information secret; and"* · **(B)** *"the information derives independent economic value, actual or potential, from not being generally known to, and not being readily ascertainable through proper means by, another person who can obtain economic value from the disclosure or use of the information"* — verbatim. Prong assignment is **correct**. Source: <https://www.law.cornell.edu/uscode/text/18/1839> |
| **2** | **§1839(6)(B)** — reverse engineering / independent derivation are **not** "improper means" | **`confirmed`** | **(6)(B)** *"does not include reverse engineering, independent derivation, or any other lawful means of acquisition"* — verbatim. Excludes exactly those three categories from "improper means"; (6)(A) defines what it *includes* (theft, bribery, misrepresentation, breach or inducement of breach of a duty to maintain secrecy, espionage). Source: same URL |
| **3** | **§1836(b)(1)** — the DTSA private civil action | **`confirmed`** | *"(b) Private Civil Actions.— (1) In general.— An owner of a trade secret that is misappropriated may bring a civil action under this subsection if the trade secret is related to a product or service used in, or intended for use in, interstate or foreign commerce."* — verbatim. Source: <https://www.law.cornell.edu/uscode/text/18/1836> |
| **4** | **35 U.S.C. §102(a)(1)** — a **printed publication** is public disclosure; effect on patentability | **`confirmed`** | *"(a) Novelty; Prior Art.— A person shall be entitled to a patent unless— (1) the claimed invention was patented, described in a printed publication, or in public use, on sale, or otherwise available to the public before the effective filing date of the claimed invention; or"* — verbatim. Source: <https://www.law.cornell.edu/uscode/text/35/102> |
| **5** | **DTSA = "Pub. L. 114–153, May 11, 2016, 130 Stat. 376"**, from the amendment notes | **`confirmed`** | §1836 source credit, verbatim: *"amended Pub. L. 114–153, §2(a), (d)(1), May 11, 2016, **130 Stat. 376**, 381."* §1836 Amendments note, verbatim: *"Subsecs. (b) to (d). Pub. L. 114–153, §2(a), added subsecs. (b) to (d) and struck out former subsec. (b) …"* §1839 Amendments note, verbatim: *"2016—Par. (3)(B). Pub. L. 114–153, §2(b)(1)(A), substituted "another person who can obtain economic value from the disclosure or use of the information" for "the public"."* |

**Additional citation also verified:** §1839(4) *"owner"* — *"the person or entity in whom or in which rightful legal or equitable title to, or license in, the trade secret is reposed"* — **verbatim** as quoted in UTS1 §1.2.

**Precision notes (not corrections):**
- `130 Stat. 376` is the **first page of Pub. L. 114–153** (the Act). §1839's *own* source credit reads *"130 Stat. 380"*, because the DTSA's §2(b) amendments begin there. UTS1's citation is correct for the Act and its `130 Stat. 376, 381` quote is correctly sourced to §1836's credit block.
- UTS1 truncates §1836's amendment note with an ellipsis, omitting *"and struck out former subsec. (b) which read as follows: 'The district courts … shall have exclusive original jurisdiction …'"*. The ellipsis is honest, but the omitted clause is substantively relevant (DTSA **replaced** the former civil-action provision rather than adding one). Worth un-truncating in any downstream use.

---

## 2. Priority 2 — the inferences UTS1 flagged (`U5`, `U6`, `U8`)

### `U5` — "publication destroys trade-secret status" is an inference from §1839(3)(B) — **`confirmed` as sound, and now authority-backed**

The inference **holds**, and it is no longer unsourced. The Supreme Court states the disclosure effect
directly in **Ruckelshaus v. Monsanto Co., 467 U.S. 986 (1984)**, Part IV-C ¶46 (decided 1984-06-26):

> *"With respect to a trade secret, the right to exclude others is central to the very definition of the
> property interest. **Once the data that constitute a trade secret are disclosed to others, or others are
> allowed to use those data, the holder of the trade secret has lost his property interest in the data.**"*

Source: <https://www.law.cornell.edu/supremecourt/text/467/986> · retrieved 2026-10-15 UTC · also at
<https://caselaw.findlaw.com/court/us-supreme-court/467/986.html> (Justia returned HTTP 403 to this agent;
Cornell LII served the full opinion).

**What this does and does not do.**
- It **does** supply the missing authority for the audit's central inference: disclosure to others, or public
  disclosure, extinguishes the trade-secret property interest. The audit's §1.1/§2 statements are therefore
  **not** this unit's invention, and `U5`'s "*no case law … was fetched or cited*" can be **retired**.
- It is a **Fifth Amendment takings** case applying **Missouri** trade-secret law — **not** a DTSA §1836
  holding. It is the canonical statement of the principle, not a DTSA merits decision.
- The precise limit the audit's flat phrasing blurs: disclosure defeats element (B) when it is **public** or
  to someone **under no obligation of confidentiality**. Ruckelshaus's own footnote (as returned by search
  surfaces) puts it as disclosure *"to others who are under no obligation to protect the confidentiality of
  the information, or otherwise publicly discloses the secret"*. A disclosure under NDA is **not** the same
  event. UTS1's §2 table is right about *publication*; it should not be read as "any disclosure to anyone".
- DTSA element (B) is **fact-bound** ("generally known … to another person who can obtain economic value"),
  and secrecy need not be absolute. That is a merits question for a lawyer, not a document audit.

### `U6` — "reasonable measures" is undefined in the statute — **`confirmed` (statute); `not_reproduced` (guidance)**

- **Confirmed:** I read §1839 in full. Definitions (1)–(7) are: foreign instrumentality, foreign agent,
  trade secret, owner, misappropriation, improper means, Trademark Act of 1946. **None defines "reasonable
  measures"**, and the statute prescribes **no minimum set**. UTS1's H1–H12 checklist is therefore correctly
  labelled as assembled from the statutory phrase plus general practice, **not** from an enumerating authority.
- **`not_reproduced` (coverage limit, not an author failure):** neither UTS1 nor this verifier fetched an
  authority stating **what suffices**. I did not manufacture one. The checklist's *completeness* remains
  unverified — as UTS1 says.

### `U8` — territorial scope — **`confirmed` as a real limit**

- **Confirmed:** the audit fetched only US federal law. So did this verification.
- **Blocked fetch:** I attempted the EU instrument and **EUR-Lex returned HTTP 202 with an empty body**, so I
  verified **no** non-US definition either. A citation I could not reach is not a defect in UTS1; it is a
  shared coverage limit.
- **Jurisdictional-limits note (required):** UTS1's conclusions are **US-federal-only** and are **not**
  transferable. In particular, the either/or in §2 and the `needs-author-decision` rows rest on the US
  definition. **EU/UK/India were not examined by either unit.** Any use of this audit outside the US must
  first resolve the corresponding instruments — named here as *instruments to examine*, **not** as verified
  content: **Directive (EU) 2016/943** on the protection of undisclosed know-how and business information
  (and the national implementations), the **UK Trade Secrets (Enforcement, etc.) Regulations 2018**, and
  **India**, where trade-secret protection is contract/equity-based rather than statutory. The author's
  India/EU visa work recorded elsewhere in this workspace makes this limit live rather than theoretical.

---

## 3. Priority 3 — the artifact claims

### 3.1 The 16-section list — **`confirmed`, with one class-level entry flagged**

All 16 ranges were opened and read in full against `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`
(719 lines). **No range is empty, and none is a pure measurement.** Fifteen carry construction, format,
file-map or naming disclosure. The weakest entry is flagged below.

| # | Section | Claimed lines | Verdict | What the range actually contains (spot-check) |
|---|---|---|---|---|
| 1 | Abstract | `:11–16` | `confirmed` | The M1 sentence verbatim at `:13–16`. |
| 2 | §1.3 substrate | `:58–68` | `confirmed` | M1 + M10: content-addressed continuation coupling truth and permission (D-001/D-002); *"Enforcement is by **absence**: prohibition is the absence of a grant from `plan()`"* (`:63–64`). |
| 3 | §4.1.1 | `:177–193` | `confirmed` | M12: `src/dag.ts exports: DagRow, DagAppendInput, class Dag` (`:184`); D-023 `StateCommit`. |
| 4 | §4.1.2 | `:195–214` | **`confirmed` (weakest)** | A **capability inventory** — names every absent primitive (observation stream, projector, `uncertain`, write-ahead intent, idempotency key, parser/resolver, `context.search`/`expand`, projection vocabulary, `StateCommit`). This discloses a **vocabulary/roadmap, not a construction**. UTS1's own row text is accurate about this ("the design surface, enumerated"), and under the mosaic theory the audit itself argues it is disclosable material — but it is the one range whose inclusion rests on class, not content. **Not a defect; recorded because an over-broad list is as misleading as a missing one.** |
| 5 | §4.2 | `:216–252` | `confirmed` | M1/M2/M3/M12: twelve typed observations, discriminated union, async hasher, `stateId`/`canonical`, `TransitionRef`, `src/store.ts` `CommitRecord`. |
| 6 | §4.3 | `:254–299` | `confirmed` | M4: `classify()` → `settled`/`uncertain`/`not-dispatched`/`unknown-key` (`:288–292`); write-ahead ordering. |
| 7 | §4.3b | `:301–331` | `confirmed` | M5: claim-before-query; *"atomicity, not earliness"*; *"the gate must be a **write only one racer can win**"*. |
| 8 | §4.4 | `:336–368` | `confirmed` | M6: the token grammar `@<kind>:<id>[#<pointer>][@<revision>][?<projection>]` and the resolver's five responsibilities. |
| 9 | §4.5 | `:370–405` | `confirmed` | M7: paging tools, `expanded[]`, drop-and-name, non-destructive re-expansion. |
| 10 | §4.6 | `:407–444` | `confirmed` | M3/M8: `stream → state → commit → composition → view`, lease heredity, epoch-bound liveness. |
| 11 | §5.1 | `:535–546` | `confirmed` | M1/M8 restated as a running artefact; grant-diff claim. A **restatement**, but it does restate the loop and `expanded[]`. |
| 12 | §5.5 | `:600–611` | `confirmed` | M9: *"a layer may be recomputed from the layer below it, and may never be a source of truth for the layer below it"* (`:602–604`); name-but-do-not-store. |
| 13 | §5.6 | `:613–619` | `confirmed` | M4/M5: the conjunction stated outright at `:616–618` incl. *"with a consume-once gate before the reconcile"*. |
| 14 | §6.3 | `:651–665` | `confirmed` | M5 operating detail: *"The consume-once gate is a `Map`"* (`:661`); unique constraint / conditional write / fencing token. |
| 15 | §7 | `:681–697` | `confirmed` | M13: the `tools/…` inventory and `npm run exp2…exp7` targets. |
| 16 | §8 | `:709–719` | `confirmed` | M13: the branch, `git log --oneline consolidation-vision`, the full `npm run` chain. |

**Minor internal inconsistency (not a correction):** the M1 row of §4.1 cites the abstract as `:14–16` while
the 16-section table cites it as `:11–16`. Both cover the load-bearing sentence.

### 3.2 §1.4 contribution 2 — **`confirmed` verbatim**

`PAPER_DERIVATION.md:72–76`:

```
1. A measured, re-runnable absence baseline for the derivation loop (§4.1).
2. The loop itself: observation stream → derived state → projection (§4.2–§4.6).
3. An honest bound on the replayability claim (§4.7).
4. A method contribution: the instrument is validated before its findings are believed …
```

Contribution **2** is exactly *"the loop itself: observation stream → derived state → projection
(§4.2–§4.6)"*, matching UTS1's quoted form at audit `:293`. The audit's derived claim — that no minimal edit
exists because the disclosed material **is** the paper's substance — follows: you cannot delete contribution
2 and retain the paper. **Sound.**

### 3.3 The release-package leaks — **counts all `confirmed`; one figure `not_reproduced`**

| Claim | Verdict | Reproduced value |
|---|---|---|
| `DECISION_CASE_SCHEMA.ts` contains the **complete `DecisionKind` union** | `confirmed` | 7 kinds: `worker.class`, `context.package`, `capability.family`, `memory.admission`, `escalation`, `topology`, `acquisition` |
| … and **six kernel namespaces** | `confirmed` | `task\|evidence\|execution\|capability\|policy\|decision` (schema comment, verbatim) |
| … and names its exact source (`target … HEAD 907fa39`, `lines 53-75`) | `confirmed` | verbatim in the schema header |
| … and `rationale` is *"used in review, not fed to the model"* | `confirmed` | verbatim in the schema |
| `reflex-decisions.ts` is **2,220 lines** | `confirmed` | 2,220 |
| **enforcement-by-absence at `:292`** | `confirmed` | `:292` verbatim, including *"absence, not a refusal, and not a gate in admit()."* (with a 2026-10-01 ERRATA clause appended) |
| `StateClass` **32×** | `confirmed` | 32 occurrences |
| `grantPolicy` **30×** | `confirmed` | 30 occurrences |
| `manifest` **30×** | `confirmed` | 30 occurrences |
| `expanded[]` **6×** | `confirmed` | 6 |
| `admit()` **4×** | `confirmed` | 4 |
| `content-addressed` **3×** | `confirmed` | 3 |
| names `src/broker.ts`, `src/scope.ts`, `src/layer.ts`, `src/loop.ts`, `src/policy.ts`, `src/state.ts` | `confirmed` | all six present (1/3/1/2/3/2 occurrences) |
| **"~335 mechanism-narrating lines"** | **`not_reproduced`** | see below |

**On the 335.** UTS1 does not publish the vocabulary it used, so the figure is not reproducible as stated.
My measurements with stated vocabularies:

| Definition (vocabulary in this report's §5) | Lines |
|---|---|
| Broad term-match over the whole file (`grep -cE`) | **317** |
| Broad term-match **restricted to prose** (question + rationale + header, excluding the 190 structural `namespaces:` lines) | **121** |
| Broad+ (adds `kernel`, `prohibition`, `postcondition`, `grant`) | **419** |
| Very broad (adds `capability`, `verdict`, `commit`, `observation`, `derivation`, `scope`) | **519** |

317 is *near* 335 but not equal, and it is **inflated by structure**, not narration: 190 of those lines are
`namespaces: [...]` tags. **The exact figure is `not_reproduced`; the substance is `confirmed`** — hundreds of
lines carry kernel vocabulary, 121 of them as prose that narrates mechanism. This is a **reproducibility gap
in the audit** (an unpublished word list), not a substantive error. **C1 depends on this**: because the
prose sits mainly in the **questions** (71) rather than the rationales (38), redacting rationale+namespaces
cannot remove it.

**Minor citation imprecision:** M12 cites `fixture :627` as naming internal kernel surface; `:627` is an
`options:` line — the nearest kernel term is `content-addressed` in the rationale at `:629`. `:420` (a
comment block naming `expanded[]`) and `:288–292` are correct.

### 3.4 The mosaic claim — **`overstated` in magnitude; conclusion unaffected**

UTS1 §5.3: abstract M1 + §4.4 `:339–345` + §4.3b `:321–325` *"already recompose into a buildable
specification."*

**I read all three passages.** They do contain what UTS1 says:
- abstract `:13–16` — append-only observation stream as source, deterministic projection, typed references;
- §4.4 `:339–345` — the **complete token grammar** and the resolver's five responsibilities (lookup,
  authorization, revision selection, projection, budget), plus a seven-item refusal-by-name list;
- §4.3b `:321–325` — the consume-once gate: claim **before** the query, *"atomicity, not earliness"*,
  *"a write only one racer can win"*.

**Judgement — sound in direction, overstated in magnitude.**
- *Sound:* those three passages do fix an architecture, a concrete data format, and one non-obvious
  correctness property. A competent engineer could build **a** loop from them, and the audit is right that
  no single passage is damaging alone — so "partition problem, not curation problem" is a fair framing.
- *Overstated:* what the three passages yield is mostly **public prior art**. The paper itself cites event
  sourcing (Azure Architecture Center), JSON Pointer (RFC 6901), JSONPath (RFC 9535) and Kleppmann's fencing
  tokens. "A generic event-sourced loop + pointer-shaped references + compare-and-swap gating" is not a
  Consonance specification, and the phrase **"buildable specification"** claims more than the text supports.
- What is genuinely *Consonance* — `stateId`/`canonical`/hasher addressing, D-023's commit shape, the four
  `classify()` states, lease heredity and epoch-bound liveness, drop-and-name budgets, the five-layer rule —
  is **not** in those three passages. It is in §4.2/§4.3/§4.5/§4.6, which is precisely why UTS1 withholds the
  **set**.
- **Why this does not change the verdict:** the mosaic number drives a `withhold` recommendation. Erring
  high on mosaic risk is the safe direction. The accurate formulation is *"three passages already disclose a
  credible skeleton that names the parts and fixes two interfaces; the distinctive core needs the rest of
  §4.2–§4.6"* — which still yields `withhold`.

### 3.5 The eight findings `F1`–`F8` — **no construction in disguise; labels are mildly loose**

I spot-checked **six of eight** against the corpus.

| ID | Verdict | Evidence reproduced |
|---|---|---|
| **F1** "A read is not a gate" | `confirmed` — genuine **finding** (derived from measured `occurrences=2` vs `1`) | §5.2 `:550–554` and §4.3b `:316–325` verbatim. General concurrency result; discloses no kernel construction. |
| **F2** "An outcomes-only journal cannot represent ambiguity" | `confirmed` — a **logical/design** result, **not a measurement** | §5.2 `:556–559`, §4.3 `:288–292` verbatim (*"an outcomes-only journal can never return `uncertain`"*). No construction disclosed. |
| **F3** Replay reproduces the record, not the decision | `confirmed` — **genuine measurement** | §4.7 `:446–483`, §5.2 `:561–563` verbatim: 41.8 % binding, 32.2 % prompt, **0 % replication control 244/244**, **31.6 % stable set 60/190**. Pure measurement on already-recorded outputs. |
| **F4** A percentage without its break-even is not a result | `confirmed` — **genuine measurement** | §4.5 `:376–405`, §5.2 `:565–567`, §6.2 `:643–645` verbatim: 83.9 % at k=3 of 30, **LOSES at k=30**, break-even **k=29**, a function of ~16:1. |
| **F7** EXP#11 negative result | `confirmed` — **genuine measurement** | §4.8 `:487–529` verbatim: 0.6650→0.6300; 0.6450→0.5800; never-revised control *exactly 0.6700 across twelve measurements*; 2-option → 8-option. UTS1 correctly keeps the *bounded-substitution* repair out. |
| **F8** Crossover is a property of the baseline | `confirmed` — **genuine measurement** | `MANUSCRIPT.md` §5.1 heading (on disk `:507`) is verbatim *"The crossover is a property of the baseline, not of the model class"*; majority-class control **0.4526 vs 0.3474** confirmed at `:281–284`, `:87`, `:97`. |

**F5** (§5.3 `:569–586`) and **F6** (taxonomy table `:574–582`) were located and read in the range given and
are **method findings, not measurements** — UTS1 labels them as a "method contribution" and a "failure
taxonomy", which is accurate.

**Assessment of the block as a whole:** **no `F` is construction in disguise**, which is the test that
matters. The only looseness is taxonomic: the parent card's phrase "measurements without construction"
applies cleanly to **F3, F4, F7, F8** (genuine measurements), loosely to **F1, F2** (structural/logical
findings), and not at all to **F5, F6** (method findings). UTS1's own §4.2 heading — *"Findings that survive
extraction"* — is more accurate than the parent's framing. Not a defect in the audit.

### 3.6 §6.4 `:669–672` — **`confirmed` verbatim**

`PAPER_DERIVATION.md:669–672` reads, verbatim (sentence starts on `:671`):

> *"The kernel is unchanged, so **every result here is a result about a model of the kernel, built against
> its real types and its real hasher but not inside its boundary.**"*

UTS1's use of it is **sound**: a result that by its own words requires the kernel's real types and its real
hasher to make sense is not a standalone extracted project under the parent's test. The quote supports the
withhold ruling for the derivation family.

---

## 4. The four lists, separated

### `contradicted` (wrong; replacement given)

| # | Item | Replacement |
|---|---|---|
| **X1** | Audit `U9` / §4.3: *"`EXCLUDED.md` says 42"* and *"a one-file discrepancy"* | **Neither holds.** `EXCLUDED.md` contains **no file count** (it names 15 exclusion classes E1–E15). The "42" is `MANIFEST.json:37` (`"counts": {"files": 42}`), and `MANIFEST.json` itself explains it: *"not listed (self-referential); MANIFEST.json is the only file absent from its own list"*. Physical count is **43** = 42 listed + `MANIFEST.json`. **There is no discrepancy to resolve.** Replacement source: `repro/encoder-crossover-190/MANIFEST.json:36–42`. |

*(This is the only `contradicted` item. No legal citation is contradicted.)*

### `overstated`

| # | Item | Correction |
|---|---|---|
| **O1** | §5.2: redacting `rationale` + `namespaces` *"remov[es] the 335 lines that narrate kernel internals"* and is *"a cheap option"* | The **`question` text is disclosure-bearing and carries more kernel vocabulary than the rationale** (71 vs 38 prose lines; e.g. `:288` names `GrantPolicy`, scope narrowing, the broker boundary, `StateClass`). Questions are the only load-bearing field, so they cannot simply be deleted. Redaction must extend to the questions or the fixture must be withheld. **This strengthens, not weakens, the audit's `needs-author-decision` call** — but the "cheap option" is not cheap. |
| **O2** | §5.3: three passages *"already recompose into a buildable specification"* | Accurate as *"a credible skeleton that names the parts and fixes two interfaces"*; "buildable specification" of the core overstates, since the distinctive mechanisms are not in those three passages and much of what is there is public prior art. Conclusion `withhold` unchanged. |
| **O3** | `F1`–`F8` presented under a "measurements without construction" framing | F3/F4/F7/F8 are measurements; F1/F2 are structural/logical findings; F5/F6 are method findings. None is construction in disguise. |
| **O4** | §4.1 M12 cites `fixture :627` as internal kernel surface | `:627` is an `options:` line; the kernel term (`content-addressed`) is at `:629`. `:420` and `:288–292` are correct. |

### `not_reproduced` (coverage or reproducibility limits — **not** author failures)

| # | Item | What blocked / limited it |
|---|---|---|
| **N1** | Exact figure **"335 mechanism-narrating lines"** | UTS1 does not publish the vocabulary used. My stated vocabularies yield **317** (whole-file term match, inflated by 190 structural `namespaces:` lines), **121** (prose only), **419** (broad+), **519** (very broad). Substance confirmed; exact figure not reproducible. |
| **N2** | `MANUSCRIPT.md` line citations (`§7 availability :772–780`; `## Data and code availability :738–754`) | Do not reproduce on disk (`:782`, `:826–827`). **Attribution: a post-audit concurrent edit to `papers/**`** — `MANUSCRIPT.md` mtime `15:35:50` > audit mtime `15:31:34`, and the +44-line offset at that section is consistent. Quoted text confirmed verbatim. |
| **N3** | `U6` — what suffices as "reasonable measures" | No enumerating authority fetched by UTS1 or by this verifier. Statute confirmed to contain no definition; checklist completeness unverified. |
| **N4** | `U8` — non-US regimes | EUR-Lex returned **HTTP 202 with an empty body**; no EU/UK/India instrument verified by either unit. |
| **N5** | Cross-host races / store atomicity behind the consume-once gate | The paper's own bound (`§4.3b`, `§6.3`); not testable from this workspace. |

### `unverified`

| # | Item | Status |
|---|---|---|
| **V1** | `U7` — spillover of publication onto neighbouring/unpublished mechanisms and improvements | Not researched by UTS1 or by me. The audit's per-mechanism treatment may understate spillover. |
| **V2** | `U13` — prior disclosure via pre-prints, arXiv, social posts | **Still the largest untested assumption**, exactly as UTS1 says. I did not audit the public footprint either. |
| **V3** | `U1`–`U4` (access control, NDAs, contributor assignments, vendor terms), `U12` (author intent) | Not read; no evidence found in my pass either. One **partial advance**: `U10` (whether any released harness step consumes `rationale`/`namespaces`) — I found **no named consumer** in any released `.py`/`.ts`: only the fixture itself references those fields, and `harness/prepare.py` renders from `question`/`options`/`correct` (`:128`, `:150`). U10's risk is **not realised in the released harness**, which is further support for redaction — subject to `O1`. |
| **V4** | §1839(3)(A) present-perfect reading ("has taken") as an ongoing-conduct obligation | Statutory phrase confirmed verbatim; the audit's gloss that failure is *"retroactive"* is its own interpretation and is **not** verified against authority. |

---

## 5. Method, vocabulary and tooling (reproducibility of this verification)

- **Vocabulary used for all term counts** (stated so the count is reproducible):
  `src/`, `StateClass`, `GrantPolicy`, `grantPolicy`, `manifest`, `expanded[`, `admit(`, `broker`,
  `namespaces`, `permitted set`, `scope narrow`, `content-address`, `projector`, `stateId`, `canonical`,
  `TransitionRef`, `StateCommit`, `DagRow`, `classify(`, `lease`, `epoch`, `consume-once`,
  `observation stream`, `derived state`, `commit DAG`. The broad+ and very-broad variants add terms listed in §3.3.
- **Commands** (all in `/home/zer0null/reserach extarctor`):
  `grep -o <term> <file> | wc -l` (occurrence counts); `grep -cE '<vocab>' <file>` (line counts);
  `python3` field-block parse for the question/rationale attribution; `find . -type f | wc -l` for the package count.
- **Sources fetched** (2026-10-15 UTC, HTTP 200): Cornell LII `18/1839`, `18/1836`, `35/102`,
  `supremecourt/text/467/986`. **Blocked:** Justia (HTTP 403), EUR-Lex (HTTP 202, empty).
- **Read-only discipline.** `/home/zer0null/Duval` — HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`.
  `git status --porcelain` before = after = **exactly the same four untracked paths** (`?? .ci-trunk.txt`,
  `?? .relay/`, `?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `?? docs/migration/`).
  **Attribution: not UVER5 and not UTS1** — the unrelated concurrent session's dirt, matching `EXCLUDED.md` §5
  and `MANUSCRIPT.md` §7. A `find -newermt '2026-10-15 15:32:00'` sweep over the target returned **nothing**:
  no target file was modified during this verification. This unit wrote only inside the workspace.

---

## 6. Is a lawyer still needed? — **yes, but not for the statutory reading**

The five citations hold verbatim; the statutory reading in §1–§2 of the audit does not need a lawyer to
**confirm**. The questions that do are **application** questions the statute leaves open, and they cluster on
exactly the item the audit calls time-sensitive (M11 — the fixture already inside the announced release).

**The single question that most deserves the time:**

> **Does releasing the fixture's `question`/`options`/`correct` text — which necessarily names `StateClass`,
> `GrantPolicy`, scope narrowing, `manifest`, `expanded[]`, `admit()` — disclose the *mechanism* (defeating
> §1839(3)(B) for the kernel's decision surface), or is it a *taxonomy of questions about* a mechanism the
> public still cannot build? And if it does disclose, does releasing `DECISION_CASE_SCHEMA.ts`'s
> `DecisionKind` union + six namespaces first (which the paper's "typed single-label" claim needs) create an
> earlier and separate disclosure event?**

Sub-questions worth the same hour:
1. **Redaction sufficiency.** Given `O1`, is redacting `rationale` + `namespaces` enough, or must the
   questions be rewritten (and if so, does the measurement survive)? This is the concrete decision in front of
   the author **before** `repro/encoder-crossover-190/` ships.
2. **"Reasonable measures" minimum.** What must exist, on the record, *now* — access list, confidentiality
   markings, NDAs, onboarding/offboarding, a written disclosure gate — for §1839(3)(A) to be satisfied for
   the **withheld** core? The statute defines nothing (`U6` confirmed), so this is the question where legal
   advice substitutes for an audit.
3. **Spillover (`V1`) and prior disclosure (`V2`).** Whether existing public artefacts already destroyed
   secrecy for any mechanism, and whether publishing selected pieces damages neighbouring unpublished ones.
4. **Territorial scope (`U8`).** Given the author's India/EU exposure, whether the US partition survives
   under Directive (EU) 2016/943 / UK 2018 / Indian law.
5. **History as a leak surface.** The audit's §5.3 point that a released repo's *history* (closed branch
   `a5ef1b28…` still in the object store) discloses more than the working tree — a licence/export question.

**A lawyer is therefore still needed for:** M11/fixture release scope and timing; the "reasonable measures"
record; territory; and the release mechanics. **Not** needed for: whether §1839(3)(A)/(B), §1839(6)(B),
§1836(b)(1), §102(a)(1) and the DTSA citation say what the audit says they say. **They do.**

---

## 7. What would change my verdict

| Finding | Effect on verdict |
|---|---|
| Any of the five statutory quotations shown to diverge from the statute as amended | → **`fail`**. All five matched verbatim; the checked text is quoted in §1 so it can be re-checked. |
| A **DTSA** decision holding that disclosure does **not** defeat element (B), or that (B) tolerates the disclosures in §4 of the audit | → would undercut the either/or in §2. Ruckelshaus states the principle; I found no contrary authority, and I did not exhaustively search DTSA merits decisions. |
| Evidence that the "335" was produced by a published vocabulary I failed to find | → `N1` becomes `confirmed`; no other change. |
| Evidence that `MANUSCRIPT.md` was **already** 859 lines when UTS1 read it (e.g. a pre-15:31 snapshot) | → `N2` becomes a genuine author citation error (still minor). Current mtimes and the +44 offset favour the concurrent-edit explanation. |
| A released harness step that consumes `rationale` or `namespaces` | → `V3`'s partial advance reverses and `O1`'s redaction path narrows further. None found. |
| Evidence that the case **questions** were author-written to avoid mechanism (i.e. that `:288`-style naming is incidental, not systemic) | → `O1` downgrades from *material* to *minor*. My count (71 prose lines in questions) says it is systemic. |
| A non-US instrument reaching a different result for the same partition | → the `pass-with-corrections` verdict stands for the US; the **strategy** would need rework, which is a matter for the main session, not for this unit. |
| Any write to `/home/zer0null/Duval` by this unit | → self-invalidating. HEAD and `status --porcelain` are identical before and after, and the mtime sweep is empty. |

---

**Not legal advice.** This report verifies that a document's citations say what the document says they say.
It is not a legal opinion, and no attorney–client relationship exists.
