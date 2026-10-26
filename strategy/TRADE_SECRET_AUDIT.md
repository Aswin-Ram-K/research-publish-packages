# TRADE_SECRET_AUDIT — what the author's own outputs disclose, per mechanism

**Unit:** UTS1 · **Written:** 2026-10-15 (UTC) · **Target of record:** `/home/zer0null/Duval` at HEAD
`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — read-only, never written.

**Purpose (one purpose).** Audit what *the author's own outputs* disclose, and produce a per-mechanism
triage: what can be published without destroying trade-secret status, and what cannot.

> **NOT LEGAL ADVICE.** Every legal statement below traces to a fetched primary source, quoted verbatim with
> URL and retrieval date. Nothing here is a legal opinion, and no attorney–client relationship exists. A
> trade-secret strategy with commercial intent is worth a lawyer's time — the author has a real product, a
> real intent to keep the core secret, and a real plan to release selected pieces; that combination has
> consequences (employee/contractor assignments, licence drafting, export, territorial scope) that a
> document audit cannot settle.

---

## 0. The decision this audit answers, as changed mid-run

The original card was written against the assumption that the umbrella paper
(`/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`) might be *edited* into a publishable state.
**That assumption was withdrawn.** The author's ruling (2026-10-15):

> *"dont publish any blanket papers, only small extracted projects that go public and the papers associated
> with it."*

The organising distinction is therefore **not** "can this paper be made safe?" but:

| | Class | Rule |
|---|---|---|
| **(a)** | **Blanket paper** — describes Consonance as a whole system | **Withhold entirely.** Not edited, not abstracted, not "fixed". |
| **(b)** | **Extracted, standalone, non-core project** — could be released on its own, without the rest of Consonance, and still make sense | **Publishable**, with the project released alongside its own paper. |

**The test that decides (a) vs (b):** *could the project be released on its own, without the rest of
Consonance, and still make sense?* If yes → extracted project. If it only makes sense as part of the whole →
blanket → withhold.

Under that test the answer for the derivation programme is **structural, not editorial**, and this audit
says so without softening: `PAPER_DERIVATION.md` fails the standalone test *by its own admission* (§6.4
`:669–672`: *"Nothing was promoted into `src/`… every result here is a result about **a model of the
kernel**, built against its real types and its real hasher but not inside its boundary"*). It is a blanket
paper. Its disclosure findings are recorded below as **evidence that the withholding decision is correct** —
not as a remediation plan.

---

## 1. The legal standard, from primary sources

All three excerpts below were fetched on **2026-10-15 (UTC)** from the Legal Information Institute, Cornell
Law School — a law-school mirror of the United States Code (the card permits `uscode.house.gov` / govinfo /
a law-school mirror).

### 1.1 The definition of a trade secret — 18 U.S.C. §1839(3)

Source: <https://www.law.cornell.edu/uscode/text/18/1839> · retrieved 2026-10-15 UTC.

> **§ 1839. Definitions**
> As used in this chapter—
> …
> **(3)** the term **"trade secret"** means all forms and types of financial, business, scientific,
> technical, economic, or engineering information, including patterns, plans, compilations, program devices,
> formulas, designs, prototypes, methods, techniques, processes, procedures, programs, or codes, whether
> tangible or intangible, and whether or how stored, compiled, or memorialized physically, electronically,
> graphically, photographically, or in writing **if—**
> **(A)** the owner thereof has taken **reasonable measures to keep such information secret**; and
> **(B)** the information derives **independent economic value, actual or potential, from not being generally
> known to, and not being readily ascertainable through proper means by, another person who can obtain
> economic value from the disclosure or use of the information**;

Two elements are therefore load-bearing for this audit, and they are the two the author's plans stress:

- **§1839(3)(A) — "reasonable measures".** Secrecy is not a property of the information; it is a property of
  the *owner's conduct*. This is why §6 below is a hygiene **checklist**, and why hygiene is an **ongoing
  conduct obligation**, not a one-time election.
- **§1839(3)(B) — "not being generally known".** This is the element that publication destroys. A mechanism
  published in a paper is generally known; the information no longer derives value from *not* being known,
  and the mechanism cannot be a trade secret for anyone, including its author.

**The statutory amendment that created the modern federal private action** (same source, "Amendments" notes
for §1839 — verbatim): *"2016—Par. (3)(B). Pub. L. 114–153, §2(b)(1)(A), substituted "another person who can
obtain economic value from the disclosure or use of the information" for "the public"."* — i.e. the
**Defend Trade Secrets Act** is **Pub. L. 114–153, May 11, 2016, 130 Stat. 376** (the citation block of
§1836 records *"amended Pub. L. 114–153, §2(a), (d)(1), May 11, 2016, 130 Stat. 376, 381"*).

### 1.2 The federal civil action — 18 U.S.C. §1836(b)(1)

Source: <https://www.law.cornell.edu/uscode/text/18/1836> · retrieved 2026-10-15 UTC. (Amendment note,
verbatim: *"2016—… Subsecs. (b) to (d). Pub. L. 114–153, §2(a), added subsecs. (b) to (d)…"* — this is the
DTSA private right of action.)

> **(b) Private Civil Actions.—**
> **(1) In general.—** An **owner of a trade secret that is misappropriated may bring a civil action** under
> this subsection if the trade secret is related to a product or service used in, or intended for use in,
> interstate or foreign commerce.

The right of action belongs to an **owner** — §1839(4), same source: *"the term "owner", with respect to a
trade secret, means the person or entity in whom or in which rightful legal or equitable title to, or license
in, the trade secret is reposed"*. A trade secret the author has published is one he can no longer own
against the world, because element (3)(B) has failed.

### 1.3 The lawful-reimplementation half — 18 U.S.C. §1839(6)(B)

Source: <https://www.law.cornell.edu/uscode/text/18/1839> · retrieved 2026-10-15 UTC.

> **(6)** the term **"improper means"**—
> **(A)** includes theft, bribery, misrepresentation, breach or inducement of a breach of a duty to maintain
> secrecy, or espionage through electronic or other means; and
> **(B)** **does not include reverse engineering, independent derivation, or any other lawful means of
> acquisition**;

This is the second half of the either/or rule in §2: acquiring a mechanism by **independent derivation** or
**reverse engineering** is *expressly not* misappropriation. So once a mechanism is public, a competitor who
reimplements it from the publication has done nothing unlawful under this chapter.

### 1.4 Public disclosure is disclosure — 35 U.S.C. §102(a)(1)

Source: <https://www.law.cornell.edu/uscode/text/35/102> · retrieved 2026-10-15 UTC.

> **(a) Novelty; Prior Art.—** A person shall be entitled to a patent unless—
> **(1)** the claimed invention was patented, **described in a printed publication**, or in public use, on
> sale, or **otherwise available to the public** before the effective filing date of the claimed invention;

**Confirming the card's question 3: yes — a paper describing a mechanism is a public disclosure of that
mechanism.** §102(a)(1) establishes that a *printed publication* is a public disclosure for prior-art
purposes; and §1839(3)(B) establishes that information *generally known* cannot carry independent economic
value from secrecy. Patents are ruled out here, so the §102 point is not about patentability — it is the
statutory demonstration that **a paper is a disclosure event, not a description of one**, and it is the
reason "publish the mechanism and keep it secret" cannot both be true.

---

## 2. The either/or rule, stated plainly

**A trade secret is destroyed by public disclosure. A patent trades disclosure for a monopoly.** With
patents ruled out and the core held as a trade secret, there is no third mechanism that lets the author keep
a technology secret *and* claim it as a published contribution. Each mechanism is therefore an **either/or**:

| | **Publish it** | **Keep it secret** |
|---|---|---|
| Legal effect | Becomes generally known → §1839(3)(B) fails → **no trade secret in it, for anyone** | Retains trade-secret status **so long as** §1839(3)(A) reasonable measures continue |
| Effect on others | Anyone may lawfully reimplement it — §1839(6)(B) excludes independent derivation and reverse engineering from "improper means" | A misappropriator is liable under §1836(b)(1) |
| What the author gets | A **citable published contribution** (priority, citation, O-1 evidence) and **prior art** that can block others from patenting it | **No published contribution. No priority. No citation.** The architectural claim cannot be claimed as a published contribution. |
| What the author loses | The secret, permanently and irrevocably | The citable claim to the design |

**Both cannot hold for the same mechanism.** They are not two halves of a strategy; they are mutually
exclusive outcomes for each mechanism. The audit's whole job is to decide, mechanism by mechanism, which
column it goes in — and the author's chosen split (core secret, selected pieces released) is a *partition*,
not a blend.

**No legal detail in this section is original or asserted.** The two operative sentences are §1839(3)(B)
(quoted §1.1) and §1839(6)(B) (quoted §1.3); the patent half is the well-known bargain, and the only thing
this audit adds is the observation that with patents ruled out, the bargain is unavailable and the either/or
is therefore forced.

---

## 3. The consequence of withholding the blanket paper (O-1), stated as a cost

The parent's premise change asks for this explicitly, and it is recorded, not argued:

**Withholding `PAPER_DERIVATION.md` means the architectural/system claim is never published and therefore
cannot be claimed as a published contribution.** What survives is the **empirical findings** of each
extracted project. Concretely, the sentence *"we built the loop that couples stream, derived state, commit,
composition and projection under one source of truth"* disappears from the citable record; §4.6's
headline-shaped claim that *"the moat survives"* disappears; §5.5's five-layer rule disappears. A reader
will be able to cite the measurements, not the architecture.

**That is a deliberate trade, and it is the correct trade under the stated intent.** It is a cost, not an
error: the author's words are *"i wanna keep the core pieces trade secrets"*, and the core pieces are
precisely what §4.2–§4.6 disclose (see §4 below).

**The mitigation is real and is the lever that preserves citable contribution while keeping the secret:**
behavioural and measurement findings can be published **without disclosing mechanism**. A paper may report
*what was measured* and *what a fix must satisfy* without publishing *how it is built*. Two examples already
sitting in the withheld paper:

- §5.2 *"A read is not a gate"* — *"Two resumers that both ask "did it happen?" before either acts are both
  told no, and both act — so reconciliation alone does not give exactly-once under concurrency, and the
  repair's load-bearing property is atomicity, not earliness."* This is a **general concurrency finding**;
  it names a *requirement* (the gate must be a write only one racer can win), not an implementation. It
  survives extraction.
- §4.5's **break-even** — *"a percentage is meaningless without the point at which it inverts"* — is a
  measurement-methodology finding about how paging results must be reported, and it is stated without any
  of the machinery that produced it.

The general statement of the lever is: **report the result and the constraint; never the construction.**
Where a finding cannot be stated without the construction, it is not a finding — it is the mechanism
wearing a result's clothes, and it goes in the `withhold` column (see M7, M8, M11 below).

---

## 4. Per-mechanism triage

**How to read the table.** *Disclosed* gives file and line. *Publishable as measurement?* asks whether the
passage reports **what was measured** (a number, a bound, an inverted expectation) as opposed to **how it is
built**. *Destroys secrecy?* asks whether the passage, as written, makes the mechanism generally known. The
recommendation uses the card's vocabulary: `publish` / `withhold` / `abstract-to-findings` /
`needs-author-decision`.

`PAPER_DERIVATION.md` = `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`;
`MANUSCRIPT.md` = `papers/encoder-crossover-190/MANUSCRIPT.md`;
`fixture` = `repro/encoder-crossover-190/fixture/reflex-decisions.ts`;
`schema` = `repro/encoder-crossover-190/fixture/DECISION_CASE_SCHEMA.ts`.

### 4.1 Core mechanism — disclose-by-construction (the `withhold` block)

| ID | Mechanism | Disclosed at | Publishable as measurement? | Destroys secrecy? | Recommendation |
|---|---|---|---|---|---|
| **M1** | Append-only observation stream as source; **state as a deterministic projection**, not a model narration | `PAPER_DERIVATION.md` abstract `:14–16`; §1.3 `:60–68`; §4.2 `:216–223`; §5.1 `:537–541`; §5.5 `:600–604` | No — it is the architecture | **Yes** | `withhold` |
| **M2** | `Observation` as a **discriminated union over `kind`**; the async-hasher/synchronous-projector typing constraint; **twelve typed observations** and the identity-bearing regions | `PAPER_DERIVATION.md` §4.2 `:219–223`, `:236–240` | No — buildable design detail | **Yes** | `withhold` |
| **M3** | **Commit record** shape: `transition: TransitionRef \| null` per D-042; chain linked rather than a list; `stateId` / `canonical` / hasher as the address | `PAPER_DERIVATION.md` §4.2 `:249–252`; §4.6 `:414–419` | No | **Yes** | `withhold` |
| **M4** | **First-class unknown-effect state**: `classify()` → `settled` / `uncertain` / `not-dispatched` / `unknown-key`; **write-ahead intent** journal (an outcomes-only journal can never return `uncertain`) | `PAPER_DERIVATION.md` §4.3 `:257–292`; §5.2 `:556–559`; §5.6 `:616–619` | No — the four states *are* the design | **Yes** | `withhold` |
| **M5** | **Consume-once gate**: a claim taken **before** the query; *"atomicity, not earliness"*; the gate must be a write only one racer can win | `PAPER_DERIVATION.md` §4.3b `:301–331`; §5.2 `:550–554`; §6.3 `:658–663` | **Partly** — see F1 | **Yes** as written | `abstract-to-findings` of F1 only; the gate itself `withhold` |
| **M6** | **Reference token grammar** `@<kind>:<id>[#<pointer>][@<revision>][?<projection>]`, the resolver's five responsibilities (lookup, authorization, revision selection, projection, budget), **absence indistinguishable from non-existence**, **closed** projection vocabulary | `PAPER_DERIVATION.md` §4.4 `:336–356` | No — it is a buildable format spec | **Yes** | `withhold` |
| **M7** | **Context engine**: `context.search` / `context.expand`, manifest/tree ref + **`expanded[]`** recording which refs were paged in, budgets **drop-and-name** rather than truncate, non-destructive re-expansion | `PAPER_DERIVATION.md` §4.5 `:380–397`; §4.6 `:418`, `:430–431`; `fixture` `:509`, `:571–575` | No | **Yes** | `withhold` |
| **M8** | **Composition / lease semantics**: `head is the certificate`, `lease.grants ⊆ union(all composed states' grants)`, **epoch-bound liveness** (an expired grant is *unrepresentable*, not flagged, and no clock is read), deterministic read-only view | `PAPER_DERIVATION.md` §4.6 `:421–444`; §5.4 `:590–593` | No | **Yes** | `withhold` |
| **M9** | **Five-layer separation rule**: *"a layer may be recomputed from the layer below it, and may never be a source of truth for the layer below it"*; higher primitives **named but not stored** | `PAPER_DERIVATION.md` §5.5 `:600–611` | No — it is the architecture's axiom | **Yes** | `withhold` |
| **M10** | **Enforcement by absence**: prohibition is the absence of a grant from `plan()`, never a check against a forbidden value (D-009); scope narrowing as one of "the four constructions of the permitted set", enforced at the **broker boundary** | `PAPER_DERIVATION.md` §1.3 `:63–64`; §4.4 `:351–353`; `fixture` `:288`, `:292`, `:390–393` | No | **Yes** | `withhold` |
| **M11** | **Decision taxonomy and namespaces**: the `DecisionKind` union (`worker.class`, `context.package`, `capability.family`, `memory.admission`, `escalation`, `topology`, `acquisition`) and the six kernel namespaces (`task\|evidence\|execution\|capability\|policy\|decision`) | **`schema` (whole file, released)**; `fixture` `:593–597`, and the `kind` field across the 190 records | No — it is the kernel's decision surface | **Yes — and it is already in the release set** | `needs-author-decision` (see §5.2) |
| **M12** | Internal kernel file/API surface named by path: `src/dag.ts` exports `DagRow`, `DagAppendInput`, `class Dag`; `src/store.ts` `CommitRecord`; `src/scope.ts` consulted by `src/layer.ts`'s `invoke()`; `admit()`; `grantPolicy` | `PAPER_DERIVATION.md` §4.1.1 `:179–185`, §4.2 `:250–251`; `fixture` `:288–292`, `:420`, `:627`; `harness/LEAD-WIRING.md` `:31`, `:53` | No — it is a map of the private repo | **Yes** | `withhold` |
| **M13** | Re-runnable artefact inventory for the core: `tools/derivation/`, `tools/resume/engine.ts`, `tools/resume/exp3b.ts`, `tools/refs/`, `tools/context/`, `tools/abstraction/`, `tools/replay/exp7.ts`, `tools/absence-probe.ts`, plus `npm run exp2…exp7` | `PAPER_DERIVATION.md` §7 `:690–697`; §8 `:711–719` | No | **Yes** | `withhold` |

### 4.2 Findings that survive extraction (the `abstract-to-findings` block)

These are stated in the withheld paper as **generalisable results** and are separable from the construction.
Each is a candidate for its own short, **standalone** note — and each passes the standalone test only if the
construction stays out.

| ID | Finding (verbatim anchor) | Where | Independent of the kernel? | Recommendation |
|---|---|---|---|---|
| **F1** | *"A read is not a gate."* Reconciliation alone does not give exactly-once under concurrency; the repair needs **atomicity, not earliness** (a claim with an `await` between check and set is the same race relocated) | `PAPER_DERIVATION.md` §5.2 `:550–554`; §4.3b `:316–325` | **Yes** — a general concurrency result; compare-and-swap/fencing tokens are public prior art | `abstract-to-findings` |
| **F2** | *"An outcomes-only journal cannot represent ambiguity."* Two reachable states (*we did it*, *we know nothing*); the middle value is **structurally unreachable** | `PAPER_DERIVATION.md` §5.2 `:556–559`; §4.3 `:288–292` | **Yes** — a journal-design result | `abstract-to-findings` |
| **F3** | *"Replay reproduces the record, not the decision."* 41.8 % decision divergence across bindings, 32.2 % across relabelled prompts, against a **0 % replication control (244/244)** and a **31.6 % stable set** | `PAPER_DERIVATION.md` §4.7 `:446–483`; §5.2 `:561–563` | **Yes** — pure measurement on already-recorded outputs | `abstract-to-findings` |
| **F4** | *"A percentage without its break-even is not a result."* Paging saves 83.9 % at k=3 of 30 and **loses** at k=30; break-even k=29 and it is a function of the brief:full ratio (~16:1), not a constant | `PAPER_DERIVATION.md` §4.5 `:376–405`; §5.2 `:565–567`; §6.2 `:643–645` | **Yes** — a measurement-methodology result | `abstract-to-findings` |
| **F5** | *"A positive result needs a control that could have said no."* M7: a control caught a predicate inversion that would otherwise have been published ("51 % replication divergence"); the unifying rule from M1–M7 | `PAPER_DERIVATION.md` §5.3 `:569–586` | **Yes** — research-method finding, no kernel content | `publish` (as a method note) |
| **F6** | The **instrument-validation failure taxonomy** M1–M7 (six instrument failures, one analysis failure) | `PAPER_DERIVATION.md` §5.3 table `:574–582` | **Yes**, subject to M12 scrubbing (M4/M6 name `src/` and `tools/` paths) | `abstract-to-findings` |
| **F7** | **EXP#11 negative result**: unbounded option-set revision **hardens the exam** — decider-4b 0.6650 → 0.6300 over six revisions, imajev-4b 0.6450 → 0.5800, against a **never-revised control stratum held at exactly 0.6700 across twelve measurements**; `missing_option` admitted on a single occurrence; a 2-option question became 8-option | `PAPER_DERIVATION.md` §4.8 `:487–529` | **Yes** — a self-refinement measurement; the *bounded-substitution* repair is the mechanism and must stay out | `abstract-to-findings` |
| **F8** | **Instrument/reliability negative results** from paper #3: the crossover is a property of the *baseline*, not the model class; the **majority-class control beats every candidate head** (0.4526 vs 0.3474) | `MANUSCRIPT.md` §4.1–§4.3, §5.1–§5.2 | **Yes** — pure measurement | `publish` |

### 4.3 Paper #3 — the encoder-crossover manuscript (hypothesis tested)

**The working hypothesis was: paper #3 is a pure empirical model-selection measurement that reveals nothing
about the Consonance kernel, so it is publishable as-is. Result: CONFIRMED for the manuscript's own text;
REFUTED for the release package it ships with.** The distinction matters and both halves are recorded.

**CONFIRMED — the manuscript text is a measurement.** Every section of `MANUSCRIPT.md` reports what was
measured: the five arms and their accuracies (§3.2 `:271–299`), the two 4B baselines and the declared primary
0.6789 (§3.3 `:301–343`), the controls and what each *would have shown* (§3.4 `:345–379`), the results and
controls (§4), the limitations (§6). Its only kernel-adjacent content is the **withholding statement itself**
(§7 availability `:772–780`: *"The **agent-state kernel / runtime implementation** (`src/**`, `kernel/**`) is
the system the measurement is about, and it is not released"*) — a sentence that **withholds** rather than
discloses, and which is a strength under §1839(3)(A): it is *documented evidence of a reasonable measure*.
The paper's novelty is explicitly narrowed to the fixture, the order-permutation control and the
majority-class control (§1 `:77–105`) — none of which is a kernel mechanism.

**REFUTED — the *package* is not clean.** The manuscript ships with
`repro/encoder-crossover-190/` (43 files; `EXCLUDED.md` says 42 — a one-file discrepancy, see §8 UNVERIFIED).
Two files in that subset disclose kernel mechanism at the taxonomy/format level:

- `fixture/DECISION_CASE_SCHEMA.ts` — the **complete `DecisionKind` union** (7 decision kinds) and the
  `DecisionCase` interface, plus a comment that names the exact source lines it was extracted from
  (`target: /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts (HEAD 907fa39)`, `lines 53-75`).
  This is M11: the kernel's decision surface, in full, in the release set.
- `fixture/reflex-decisions.ts` — 2,220 lines of case **rationales** written to explain the kernel's own
  semantics. **335 lines** match kernel-internals vocabulary. The fixture names `src/broker.ts`,
  `src/scope.ts`, `src/layer.ts`, `src/loop.ts`, `src/policy.ts`, `src/state.ts`; it uses `StateClass` 32×,
  `grantPolicy` 30×, `manifest` 30×, `expanded[]` 6×, `admit()` 4×, `content-addressed` 3×; and its
  explanatory prose states the mechanism outright — e.g. `:292`: *"Scope narrowing is one of the four
  constructions of the permitted set, and it is enforced at the broker boundary — src/scope.ts, consulted by
  src/layer.ts's invoke() — so the root listing has no entry to resolve and the call fails as ENOENT:
  absence, not a refusal, and not a gate in admit()."* That single sentence discloses M10 (enforcement by
  absence), M12 (internal file map) and part of the permitted-set construction.

**Recommendation for paper #3:** the **manuscript** may be `publish`ed as a measurement (F8). The
**fixture rationales and the schema are `needs-author-decision`** — they are already inside the planned
release and are the audit's most consequential discovery (§5.2). The measurement itself does not need them:
the sealed instrument needs its **questions, options and correct index**; the *rationale* field is
`"used in review, not fed to the model"` (schema, verbatim) and is therefore not needed for reproduction by
a third party at all.

---

## 5. Disclosure-risk list for `PAPER_DERIVATION.md`, and the mosaic

### 5.1 The problem sections (16), and why no minimal edit exists

This section records **confirmation of the withhold decision**, not a remediation plan. The question the card
originally asked — "the minimal change that would let it be published as findings" — has a single honest
answer for this paper, and it is recorded here plainly rather than softened:

> **No minimal change exists, because the disclosed material is not incidental to the paper — it is the
> paper's substance.** The paper's contribution *is* the loop (abstract `:11–16`; §1.4 `:72–76` lists *"the
> loop itself: observation stream → derived state → projection (§4.2–§4.6)"* as contribution 2). To make it
> publishable as findings you would have to delete the loop and keep the numbers — which is **a different
> paper**, not an edited one. That is exactly why the blanket/withhold ruling is correct, and it is the
> finding this unit was asked to confirm.

**The 16 problem sections, with the class of mechanism each discloses:**

| # | Section | Lines | Discloses |
|---|---|---|---|
| 1 | Abstract | `:11–16` | M1 in one sentence: *"an append-only observation stream as the source, state as a deterministic projection of it rather than a narration the model writes … with typed references as the connective tissue"* |
| 2 | §1.3 The substrate | `:58–68` | M1, M10 — content-addressed continuation coupling truth and permission (D-001, D-002); prohibition as absence of a grant from `plan()` (D-009); commit DAG + kernel-stamped provenance (D-039) |
| 3 | §4.1.1 unit of propagation | `:177–193` | M12 — `src/dag.ts` exports and the D-023 `StateCommit` decision |
| 4 | §4.1.2 The measured gap | `:195–214` | The **capability map**: names every absent primitive (observation stream, projector, `uncertain` status, write-ahead intent, idempotency key, reference token parser/resolver, `context.search`/`context.expand`, projection vocabulary, `StateCommit`) — the design surface, enumerated |
| 5 | §4.2 Observation stream → derived state | `:216–252` | M1, M2, M3, M12 — twelve observations, discriminated union, async hasher, `stateId`/`canonical`, `TransitionRef` |
| 6 | §4.3 Uncertain effects | `:254–299` | M4 — `classify()` states, write-ahead ordering, the three-line result table |
| 7 | §4.3b Concurrent resumption | `:301–331` | M5 — the consume-once gate, claim-before-query, atomicity-not-earliness |
| 8 | §4.4 Reference token methods | `:336–368` | M6 — the token grammar, resolver responsibilities, closed projection vocabulary |
| 9 | §4.5 The context engine | `:370–405` | M7 — paging tools, `expanded[]`, drop-and-name, non-destructive re-expansion |
| 10 | §4.6 The user abstraction | `:407–444` | M3, M8 — `stream → state → commit → composition → view`, lease heredity, epoch-bound liveness |
| 11 | §5.1 The loop is real | `:535–546` | M1, M8 — restates the loop as a running artefact and the grant-diff claim |
| 12 | §5.5 Why "separate and combined" is different | `:600–611` | M9 — the five-layer rule and name-but-do-not-store |
| 13 | §5.6 What is occupied, precisely | `:613–619` | M4, M5 — the conjunction claim is stated as *"with a consume-once gate before the reconcile"* |
| 14 | §6.3 Stores and processes | `:651–665` | M5 operating detail — *"The consume-once gate is a `Map`"*, plus the store requirements (unique constraint, conditional write, fencing token) |
| 15 | §7 Artefacts | `:681–697` | M13 — the re-runnable inventory with `tools/…` paths and `npm run` targets |
| 16 | §8 Reproducing the programme | `:709–719` | M13 — the branch, the `git log` command, the full `npm run` chain |

**The three sections with a genuine, minimal, *non-substantive* fix** — and they are hygiene, not
remediation — are §4.1.1 (delete the `src/dag.ts` export list), §7 and §8 (delete the `tools/` paths and
`npm run` targets). Those are **provenance leaks that name the private tree**. Removing them does not make
the paper publishable; it only removes a map of the private repository. They are listed because they would
matter even for internal circulation, where a leak of file paths is gratuitous.

**One further exposure, worth naming even though the paper is withheld.** §4.1.1 `:183` and §4.2 `:250–251`
describe *where in `src/` things are and are not*, and §7 `:699–700` says *"None is wired into CI,
deliberately"* — a statement about the private repo's CI posture. None of this is mechanism, but all of it is
repository-internal information that §1839(3)(A) hygiene would keep internal.

### 5.2 The already-released artifact — the fixture and schema

This is the one finding that is **time-sensitive**: unlike a withheld paper, this material is *already
inside a release set* (`repro/encoder-crossover-190/`, and the manuscript's `## Data and code availability`
`:738–754` announces it as shipping with the paper). It is therefore not a future disclosure decision; it is
a **current exposure** that must be decided before that release happens.

**What it discloses.** M11 (the complete decision taxonomy and the six kernel namespaces) and M12 (internal
kernel file map, `StateClass`, `grantPolicy`, `admit()`, `expanded[]`, `manifest`) and — through the
rationales — substantive statements of M10 (enforcement by absence, the permitted-set constructions) and M7
(the commit's `manifest/tree ref plus expanded[] recording exactly which refs were paged in`, `:509`,
`:575`).

**Why `EXCLUDED.md` did not catch it.** `EXCLUDED.md` E1 withholds *"Agent-state kernel / runtime
implementation … `src/**` (state, commit, ledger, loop, broker, lifecycle, MCP, …)"*. That boundary is
**correct about implementation code and silent about mechanism**. The fixture contains no `src/` code and
imports nothing from the kernel — and yet it names the kernel's decision kinds, its namespaces, its file
layout and its enforcement discipline, because its purpose was to test *the kernel's own decisions*. A
boundary drawn around "the implementation" does not bound "what the implementation's design is".

**Recommendation — `needs-author-decision`, with a cheap option.** The measurement needs the fixture's
`id`, `kind`, `question`, `options`, `correct`; it does **not** need `rationale` (schema, verbatim:
*"used in review, not fed to the model"*) or `namespaces`. Redacting the `rationale` and `namespaces` fields
preserves every headline number (they are never fed to any arm) while removing the 335 lines that narrate
kernel internals. The `DecisionKind` union is a harder call: it is load-bearing for the paper's claim that
the fixture is *typed single-label*, so removing it weakens the contribution. That trade is the author's —
which is why this row is `needs-author-decision` and not `withhold`.

### 5.3 Mosaic risk — code pieces **and** papers read together

**Verdict: `high` for the derivation family; `low` for paper #3.** The mosaic is a small-number problem,
not a large-number one: **three of the pieces above already recompose into a buildable specification.**

**The recomposition, stated concretely.** Take only already-written passages: the abstract's own sentence
(M1: append-only observation stream, state as a deterministic projection, typed references as connective
tissue) + the reference-token grammar and resolver responsibilities (M6, §4.4 `:339–345`) + the consume-once
gate requirement (M5, §4.3b `:321–325`). A competent engineer reading those three passages can build a
smaller version of the loop without seeing a line of the kernel: an append-only typed event log, a projector
that folds it, a token format for references, and a gated reconcile. **That is the core, and no single one of
those passages is damaging alone.** This is precisely why "release some pieces" is a **partition problem**,
not a curation problem, and why the mosaic answer is `high` rather than `medium`.

**The paper-set mosaic.** The new question — *can the released papers, read together, disclose the
architecture no single one discloses?* — has a sharp answer:

- **`MANUSCRIPT.md` (paper #3) is orthogonal.** It measures encoders vs a fine-tuned 4B decider on a sealed
  fixture. Read with any other paper it contributes a measurement, not a mechanism. `low`.
- **The derivation programme's experiments are not six papers; they are one architecture, cut into six.**
  §4.2 (projection) + §4.3/§4.3b (unknown-effect state and the gate) + §4.4 (references) + §4.5 (paging) +
  §4.6 (composition) **are** the loop, and §5.5's single rule ("a layer may be recomputed from the layer
  below it") is the sentence that binds them. Publishing them as separate "extracted projects" would produce
  a set of papers that a reader **can and will** reassemble, because each one is written against the same
  five-layer vocabulary and each cites the same decision numbers (D-001, D-002, D-009, D-023, D-026, D-042).
- **They fail the standalone test on their own testimony.** §6.4 `:669–672`: *"every result here is a result
  about **a model of the kernel**, built against its real types and its real hasher but not inside its
  boundary."* A project that requires the kernel's real types and real hasher to make sense is **not** an
  extracted standalone project. Under the parent's test, the derivation experiments are blanket, and the
  recommendation is `withhold` — all of them, as a set, not one of them as a judgment call.

**Safe / unsafe split for piece-by-piece release.**

| | Piece class | Examples in this corpus | Verdict |
|---|---|---|---|
| **SAFE** | **Pure statistics / analysis code** | `harness/analyze.py`, the bootstrap/McNemar and power code; `second-labeller/compare.py` | `publish` — general method, no kernel semantics |
| **SAFE** | **Generic training/eval plumbing** | `harness/train.py`, `tcmodel.py`, `tccommon.py`, `evaluate.py`, `prepare.py`; calibration/ECE/Brier | `publish` — repeats public libraries |
| **SAFE** | **Result-record formats** | `results/eval-*.json`, `baselines.json` shapes; metric file schema | `publish` — reporting format, not a mechanism |
| **SAFE** | **Data-file integrity utilities** | sha256 sealing of the instrument, leak-lint over 8-grams (`lint.ts` rule) | `publish` — measurement integrity |
| **SAFE** | **The paper text** | `MANUSCRIPT.md` (CC BY 4.0 per author decision 2026-10-15) | `publish` |
| **UNSAFE** | **The decision taxonomy and namespaces** | `DECISION_CASE_SCHEMA.ts`; `fixture` `kind` and `namespaces` fields | `needs-author-decision` |
| **UNSAFE** | **The fixture rationales** | `fixture/reflex-decisions.ts` (335 mechanism-narrating lines) | `withhold` or redact |
| **UNSAFE** | **State derivation** | projector, `stateId`, `canonical`, hasher, the twelve observations, the `Observation` union | `withhold` |
| **UNSAFE** | **Commit / DAG / chain** | `StateCommit`, `TransitionRef`, `DagRow`/`Dag`/`DagAppendInput`, chain linkage | `withhold` |
| **UNSAFE** | **Unknown-effect + concurrency machinery** | `classify()` states, write-ahead intent, consume-once gate, claim store | `withhold` |
| **UNSAFE** | **Typed references** | token grammar, resolver, closed projection vocabulary | `withhold` |
| **UNSAFE** | **Context engine** | `context.search`/`context.expand`, manifest, `expanded[]`, budget drop-and-name | `withhold` |
| **UNSAFE** | **Composition / lease / view** | `compose()`, head-is-certificate, epoch-bound liveness, read-only view | `withhold` |
| **UNSAFE** | **Anything that imports or mirrors kernel types** | every EXP#2–EXP#6 artefact (`tools/derivation/`, `tools/resume/`, `tools/refs/`, `tools/context/`, `tools/abstraction/`, `tools/replay/`); the `tools/typed-channel/` harness's kernel coupling | `withhold` |
| **UNSAFE** | **The derivation papers, as a set** | `PAPER_DERIVATION.md` §4.2–§4.6 + §5.5, published in any division | `withhold` |

**The variable that makes the split unstable, and which the author must control.** The released set is a
**single git repository's** history. `DISCLOSURE_CHANGES.md` §D4 records that the EXP#12 harness was
recovered from branch `a5ef1b28a7baca7dc1094757106b6a6af2c2aaf8` via `git cat-file blob` — i.e. **a closed,
unmerged branch is still fully present in the object store.** Whatever is released, the *history* of the
released repository is the leak surface, and a release must be a fresh export, not a push of an existing
tree. This is a hygiene requirement, not a preference (see §6).

**And the licence does not preserve secrecy.** The plan is to release the safe pieces under **PolyForm
Noncommercial**, with the main Consonance repo unlicensed/proprietary. That is coherent, but note the
trade-secret consequence plainly: **publishing source under any licence discludes it** — PolyForm
Noncommercial restricts *copyright* use for commercial purposes; it does not, and cannot, maintain secrecy
in published text. Once a piece is published, M11-style disclosure cannot be walked back by the licence, and
§1839(6)(B) means a competitor can lawfully reimplement what the licence text disclosed (whether or not that
reimplementation is itself a copyright infringement is a separate, licence question this audit does not
reach).

---

## 6. Trade-secret hygiene checklist

**Hygiene is an *ongoing conduct* obligation, not a one-time choice.** The statute says so directly:
§1839(3)(A) requires that *"the owner thereof has taken reasonable measures to keep such information
secret"* — present-perfect continuous. A trade secret kept perfectly for two years and then neglected is a
trade secret that a court may hold was not protected, and the failure is retroactive: the protection is
assessed on the conduct, so the earlier care does not immunise the later neglect. Every item below is
therefore recurring, and the review gate must precede **every** release, including small ones.

| # | Measure | Status in this corpus (measured, not assumed) |
|---|---|---|
| H1 | **Access control** — the core repository is private; write access least-privilege | `README.md`/`AGENTS.md` treat the target as read-only; the repo is private (LICENSE_ANALYSIS/`DISCLOSURE_CHANGES` §D1: *"the repo is private and the code is not released"*). **Gap:** no evidence found of an access list, role scoping, or a credential/SSH-key inventory. `UNVERIFIED` (U1). |
| H2 | **Confidentiality marking** — every core artefact carries a confidentiality notice | **Gap, measured.** `PAPER_DERIVATION.md` is a working paper with no notice; the fixture and harness files carry none. The only statement of withholding is prose in `EXCLUDED.md` and `MANUSCRIPT.md` §7. Add a marker to every file in `src/**`, `kernel/**`, and every `tools/**` experiment tree. |
| H3 | **NDAs** — before any contractor, reviewer, or second labeller sees unpublished core material | **Gap.** The second-labeller pass (`second-labeller/`) was performed on the fixture; whether a written confidentiality obligation exists is not recorded anywhere this audit read. `UNVERIFIED` (U2). For a labeller seeing only the fixture, an NDA is arguably unnecessary — but for anyone seeing `src/`, it is load-bearing. |
| H4 | **No publication of the covered mechanism** — the one measure this audit can actually enforce | **Partially met, and the partition is the work.** Paper #3 is clean; `PAPER_DERIVATION.md` is blanket and now withheld; the fixture is `needs-author-decision`. |
| H5 | **Publication review gate before every release** | **Gap.** No documented gate was found. This audit is an instance of the gate; it must become a *standing step* — every release, including a "small extracted project", gets a written per-mechanism triage against §4's table before it ships. |
| H6 | **Release by fresh export, never by pushing an existing tree** | **Required, and currently violated in plan.** EXP#12's harness was recovered from a *closed branch* still in the object store (`DISCLOSURE_CHANGES.md` §D4). A push of the existing repo discloses history. Release must be a fresh export with an audited manifest. |
| H7 | **Contributor/contractor onboarding and offboarding** — assignment of rights, removal of access on exit | **Unverified** (U3). No onboarding or exit record was read. |
| H8 | **CI, logs and artefacts discipline** — build logs, traces, caches, run artefacts must not carry kernel paths or code | **Gap, measured.** `harness/LEAD-WIRING.md` `:31`, `:53` carry the **full private `npm run` suite** (`commit-boundary`, `commit-lineage`, `dag`, `dag-merge`, `derivation-coverage`, `decision-record`, `hosted-layer`, `lifecycle`, …) referencing `src/`-level gates. If the harness ships, this file ships it. Exclude or scrub. |
| H9 | **Third-party terms** — cloud/vendor/model terms, and whether they permit or defeat secrecy | **Unverified** (U4). Models are public checkpoints (Apache-2.0 / MIT) fetched at runtime, which is favourable, but no vendor-term review was read. |
| H10 | **Incident response** — a written plan for what happens on suspected disclosure | **Gap.** None found. Once a leak is suspected, the sequence (preserve evidence, assess §1839(3)(B) damage, notify, consider the release decision) should be written *before* it is needed. |
| H11 | **Recorded disclosure decisions** — a written record that each release was *decided*, with reasons | **Partially met.** Author decisions are recorded elsewhere (primary baseline 0.6789, CC BY 4.0); the disclosure decisions are not. This audit's triage table is the first such record for the mechanism dimension. |
| H12 | **Do not let the discipline live only in prose** | The strongest existing asset is that `EXCLUDED.md` names its boundaries explicitly. That practice should be adopted for `src/**` itself, where no equivalent "what is secret and why" file was found. |

---

## 7. What could not be determined, and one closing observation

**The audit can decide the either/or. It cannot make it disappear.** Two mechanisms cannot both be published
and held secret, and the triage above assigns each one. Where the audit's answer is `needs-author-decision`
(M11 and the fixture), that is not evasion: the trade is genuinely the author's, because the cost of
redaction falls on a published contribution he is claiming priority over.

**The single highest-value action this audit identifies:** decide M11 and the fixture rationales **before**
the `repro/encoder-crossover-190/` release ships. Every other row in the table is about a document that is
currently withheld and can be decided at leisure; that one is inside an announced release set.

---

## 8. `UNVERIFIED` list

Nothing below is asserted as fact anywhere above. Each item is named so a reader can disagree with a
specific line.

| ID | Unverified statement |
|---|---|
| U1 | That an access-control list / role scoping / credential inventory exists for the private repo. No such record was found or read. |
| U2 | That a written confidentiality obligation (NDA) covers the second labeller or any other reviewer of unpublished material. Not recorded in anything read. |
| U3 | Contributor/contractor rights assignment and offboarding procedure. Not read. |
| U4 | Third-party (cloud/vendor) terms' interaction with secrecy. No vendor terms were fetched. |
| U5 | **The legal proposition that publication destroys trade-secret status is an *inference* from §1839(3)(B), not a statutory sentence.** The statute's text is *"derives independent economic value … from not being generally known to … another person who can obtain economic value from the disclosure or use of the information"*; the conclusion that a published paper therefore defeats element (B) is this audit's reading. **No case law, Restatement, or treatise was fetched or cited**, and no court decision was read. |
| U6 | **"Reasonable measures" is not defined in the statute and no minimum set was verified.** The H1–H12 checklist is assembled from the statutory phrase plus general practice, **not** from a fetched authority enumerating required measures. Its completeness is unverified. |
| U7 | The claim that a mechanism's *publication* also destroys protection for **improvements** derived from it, or for the un-published neighbouring mechanisms, was not researched. The audit treats each mechanism separately, which may understate the spillover. |
| U8 | Territorial scope. Only **US** federal law was fetched. The author's India/EU visa work (elsewhere in this workspace) implies multi-jurisdiction exposure; EU trade-secret protection (Directive (EU) 2016/943) and Indian law were **not** fetched. |
| U9 | The file-count discrepancy: `EXCLUDED.md` says the subset is 42 files; `find` reports **43** (`EXCLUDED.md`, `INTEGRITY.md`, `LICENCE_TODO.md`, `MANIFEST.json`, `README.md`, the `fixture/`, `harness/`, `preregistration/`, `results/`, `second-labeller/` trees). `EXCLUDED.md`'s "42" may count only the harness-adjacent files or predate a later addition. Not resolved. |
| U10 | Whether the `rationale` and `namespaces` fields are genuinely unused by every released harness step. `MANUSCRIPT.md` and the schema say the rationale is *"used in review, not fed to the model"*; the audit did not re-run the harness to confirm no downstream file depends on them. |
| U11 | The `DecisionKind` union's status as a **kernel** artifact versus a fixture-only taxonomy. The schema says it is extracted *"verbatim"* from the target's `evals/fixtures/reflex-decisions.ts` `lines 53-75` and that *"this snippet is the complete fixture schema"* — whether the same union is declared in `src/` (making it a kernel type) was not checked. |
| U12 | The precise meaning of the author's *"i only wanna even make public some pieces of the core consonance engine itself"*. This audit reads it as permitting selected core pieces to be released; whether the author intends leaf utilities or substantive core pieces is ambiguous, and the `needs-author-decision` rows turn on it. |
| U13 | Whether any **previous** disclosure already destroyed secrecy for any mechanism — e.g. pre-prints, social posts, an arXiv posting, or the `SOCIAL_PRESENCE.md` surface. The audit read the two papers and the repro boundary; it did not audit the author's public/social footprint for prior disclosure. **This is the largest untested assumption in the audit.** |

**Not legal advice.** The one recommendation this audit makes with confidence is procedural: **before the
`repro/encoder-crossover-190/` release ships, and before any selected piece of the core is published, put
this triage in front of a lawyer.** The author's own words — *"i wanna own my own rights and i dont want any
patents - i wanna keep the core pieces trade secrets"* — describe a strategy with commercial intent, which
is exactly the situation where a trade-secret plan is worth professional time rather than a document audit.

---

## 9. Provenance and read-only discipline

- **Target:** `/home/zer0null/Duval`, HEAD before = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`, HEAD after =
  identical. `git status --porcelain` before and after = **exactly the same four untracked paths**:
  `?? .ci-trunk.txt`, `?? .relay/`, `?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`,
  `?? docs/migration/`. **Attribution: not this unit.** Those four are the unrelated concurrent session's
  dirt, matching `repro/encoder-crossover-190/EXCLUDED.md` §5 and
  `papers/encoder-crossover-190/DISCLOSURE_CHANGES.md`, which record the same four at the same HEAD. This
  unit added and removed nothing in the target: no writes, no `git` state changes.
- **Sources fetched (primary, verbatim):** `https://www.law.cornell.edu/uscode/text/18/1839`,
  `…/18/1836`, `…/35/102` — all retrieved **2026-10-15 UTC**.
- **Nothing outside the declared write paths was touched:**
  `strategy/TRADE_SECRET_AUDIT.md`, `orchestration/units/UTS1.md`, `orchestration/handoffs/UTS1.json`.
