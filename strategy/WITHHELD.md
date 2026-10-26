# WITHHELD — the register of what is deliberately not published

**Unit:** UCAND1 · **Written:** 2026-10-15 (UTC) · **Target of record:** `/home/zer0null/Duval` at HEAD
`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — read-only, never written.
**Status:** register of record. **Append-only** — an item leaves this register only by a new, dated,
author-attributed entry (§6), never by deletion.
**Companion documents:** [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G (the re-triage that applies the
same rule candidate by candidate), [`PUBLICATION_STRATEGY.md`](PUBLICATION_STRATEGY.md) §13 (the corrected
plan), [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) (the per-mechanism triage and the quoted legal
standard), [`CODE_LICENSING_STRATEGY.md`](CODE_LICENSING_STRATEGY.md) (the licence that wraps what *is*
released).

> **RE-ISSUED 2026-10-15 by UWITH1 — §8 governs where §1–§4 disagree, and §8.1–§8.3 replace §2's status
> column.** The register as first issued (UCAND1, 2026-10-15) recorded M1–M13 as withheld. **Twelve of the
> thirteen mechanisms are already public** in `Aswin-Ram-K/publish-present-compete` (MIT, public
> ≤ 2026-10-10), and a trade secret in them is **not available** **[CORRECTED 2026-10-15 by UFIX9 — the
> count is now **thirteen of thirteen**: M11 is `disclosed`, settled by UDISC2 against the fetched public
> `decisions/DECISION_LOG.md` D-024/D-045/D-048 (§8.9). This supersedes §8.2's `undetermined`, which
> rested on UDISC1's earlier bound that never read `DECISION_LOG.md`.]** — disclosure destroyed it, and the MIT
> licence already grants free commercial use of those versions. The register's protective claim is narrowed
> to the **implementation** (§8.3): `src/**`, concrete types, the code-level state-class catalogue, private
> corpora, `tools/**`, and unpublished prose. **The corrected strategy, in one place: publish the design,
> keep the code** (§8.4). §1–§2 are **not** edited — they stand as the dated record of what was issued; this
> is an append under §6.

**Purpose (one).** This file records, by name and by reason, what this programme **deliberately does not
publish**, so that the withholding is **documented, dated and deliberate rather than accidental**. That
distinction is the point of the file: a trade secret survives only where the owner has taken reasonable
measures to keep it secret, and a dated, itemised register of decisions-not-to-publish is such a measure.

> **NOT LEGAL ADVICE.** Every legal proposition below is a pointer into
> [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md), which quotes its primary sources with URL and retrieval
> date. This register records decisions; it does not give, and must not be read as, a legal opinion.

---

## 0. The author's rule (2026-10-15), verbatim

> *"dont publish any blanket papers, only small extracted projects that go public and the papers associated
> with it."*

Same session, and binding on this register:

1. **No patents.**
2. **The core Consonance engine is a trade secret.**
3. **The main repository stays proprietary.**
4. **Only selected extracted pieces are released**, under **PolyForm Noncommercial 1.0.0** — source-available,
   not open source; commercial use requires a paid licence
   ([`CODE_LICENSING_STRATEGY.md`](CODE_LICENSING_STRATEGY.md) §5.1).
5. **Every released piece carries its own paper** (and every released paper ships a releasable artifact —
   see §3).

**The deciding test, stated once.** *Could this project be released on its own, without the rest of
Consonance, and still make sense — with its own fixture/harness/tooling that a reader could run?*
**Yes → extracted project** (publishable, must ship an artifact). **No, it only makes sense as part of the
whole → blanket** (withheld). Applied per candidate in
[`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.

**The either/or that makes this register necessary, not optional.** A trade secret is destroyed by public
disclosure; a patent trades disclosure for a monopoly. **Patents are ruled out** (rule 1), so there is no
third mechanism that lets a technology stay secret *and* be claimed as a published contribution. Each
mechanism is therefore an **either/or**, and the author's split (core secret, selected pieces released) is a
**partition, not a blend**. Stated and sourced in [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §2.

---

## 1. Register — blanket papers and blanket documents (withheld)

| # | Withheld item | What it is | Why withheld | Anchored at |
|---|---|---|---|---|
| **W1** | `docs/research/PAPER_DERIVATION.md` (paper candidate **#1**) | the 719-line blanket paper describing the kernel as a whole — abstract, related work, eight experiments, the full system | **Fails the standalone test by its own admission** (`§6.4`: *"Nothing was promoted into `src/`… every result here is a result about **a model of** the kernel"*), and it publishes ~16 mechanism sections. Withheld: **not edited, not abstracted into a "safe" version, not fixed.** **[CORRECTED 2026-10-15 by UWITH1 — (i) the document is already public (§8.1), so this withholding is a programme decision *not to republish* it, not a secrecy measure (UVER6 C4); (ii) the *"by its own admission"* gloss on §6.4 is overstated — §6.4 is a **scope-limitation** section, and the ellipsis drops *"Every artefact lives in \`tools/\`, which is the operator's rule…"* (UVER6 O1). The standalone test still fails, on other grounds: limb (a) via contribution 2 at \`:72–76\`, limb (b) via the private M13 \`tools/**\` inventory (\`PAPER_CANDIDATES.md\` §G.1).]** | `PAPER_CANDIDATES.md` §G.1; `TRADE_SECRET_AUDIT.md` §5.1 |
| **W2** | The **"umbrella" publication step** | the plan step that posted #1 so the corpus could be cited as one body of work | **Void.** With W1 withheld there is no umbrella; there is no document whose function is to make the corpus citable as a whole. Each paper stands alone. | `PUBLICATION_STRATEGY.md` §13(a)–(b) |
| **W3** | The **architectural / system claim** as a citable contribution | the sentence *"we built the loop that couples stream, derived state, commit, composition and projection under one source of truth"* and its siblings (§4.6's *"the moat survives"*, §5.5's five-layer rule) | It **is** mechanisms W4–W16. Publishing the claim publishes the construction. This is the item whose loss is recorded as a cost in §4. | `TRADE_SECRET_AUDIT.md` §3 |
| **W4** | `docs/research/LAYER_MODEL.md` — the five-layer specification | a specification of the whole system, including the §4.6.1 intersection errata | A spec of the whole is a blanket document; its measured errata is a section of W1, not a paper. | `PAPER_CANDIDATES.md` §D |
| **W5** | `src/**` and `kernel/**` — the agent-state kernel / runtime implementation | the product itself | Core trade secret; excluded from every release set. | `repro/encoder-crossover-190/README.md` (*"Withheld: the agent-state kernel / runtime implementation"*) |
| **W6** | **Model weights** (trained encoder heads, deciders) | the trained artifacts behind the measurements | Excluded from every release set, by the same author decision as W5. | `repro/encoder-crossover-190/README.md` |
| **W7** | **Patents** | none filed; none planned | The author ruled patents out. With the patent route gone, the disclose-or-keep either/or is **forced**; a mechanism in this register cannot later be patented without first being disclosed. | `TRADE_SECRET_AUDIT.md` §2 |

**One-line statement of the W1 decision, for any reader who reads only one line.** *#1 `PAPER_DERIVATION.md`
is a blanket paper — it describes the kernel as a whole and fails the standalone test by its own §6.4
admission — so it is withheld outright, and the "umbrella" step that would have made the corpus citable as
one body is void with it.*

---

## 2. Register — core mechanisms (withheld)

The per-mechanism triage, with the disclosure location of each and the legal reasoning, is
[`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §4.1 (`withhold` block). This register lists them at
register level only — **the names are sufficient here; the disclosures themselves are what must not be
republished**, and they are not repeated in this file. Each is withheld because publishing it makes the
mechanism **generally known**, which defeats the trade-secret definition
([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §1.1, quoting 18 U.S.C. §1839(3)).

| ID | Mechanism (name only) | Status |
|---|---|---|
| M1 | Append-only observation stream as source; state as a deterministic projection | **withhold** |
| M2 | The `Observation` discriminated union over `kind`; async-hasher / synchronous-projector typing; the twelve typed observations | **withhold** |
| M3 | Commit-record shape; chain linked rather than a list; `stateId` / `canonical` / hasher as the address | **withhold** |
| M4 | First-class unknown-effect state; the `classify()` value set; write-ahead intent journal | **withhold** |
| M5 | Consume-once gate (the gate itself — see §3 for the finding that survives) | **withhold** |
| M6 | Reference-token grammar and the resolver's five responsibilities; absence indistinguishable from non-existence; closed projection vocabulary | **withhold** |
| M7 | Context engine: paging surfaces, manifest/tree ref + `expanded[]`, budgets that drop-and-name, non-destructive re-expansion | **withhold** |
| M8 | Composition / lease semantics: head as certificate, grant-subset rule, epoch-bound liveness, deterministic read-only view | **withhold** |
| M9 | The five-layer separation rule and "higher primitives named but not stored" | **withhold** |
| M10 | Enforcement by absence; scope narrowing as a construction of the permitted set; enforced at the broker boundary | **withhold** |
| M11 | Decision taxonomy and kernel namespaces (`DecisionKind` union; the six namespaces) | **withhold — and already partially in the release set**; open author decision, `TRADE_SECRET_AUDIT.md` §4.3/§5.2 · **[CORRECTED 2026-10-15 by UFIX9 — the *public-disclosure* status is settled: M11 is **disclosed** (§8.9), superseding §8.2's `undetermined`. Only the *release-set* decision remains the author's, and `worker.class` / `context.package` remain unlocated (§8.9).]** |
| M12 | Internal kernel file/API surface named by path | **withhold** (scrub rule: a released harness must not name `src/**` paths) |
| M13 | The re-runnable artefact inventory *for the core* (`tools/derivation/`, `tools/resume/engine.ts`, `tools/refs/`, `tools/context/`, `tools/replay/exp7.ts`, …) | **withhold** — releasing the inventory maps the private repo. A paper that needs such a harness must ship a **re-implemented, neutral** one (§3). |

---

## 3. What is *not* withheld — the release side, recorded so the register is a partition

Recorded here because a withholding register that does not say what *is* released makes the boundary look
accidental. **Nothing in this section is withheld; nothing in §1–§2 is released.**

**(a) Findings that survive extraction.** Behavioural and measurement findings may be published **without
disclosing mechanism**: *a paper may report **what was measured** and **what a fix must satisfy** without
publishing **how it is built*** ([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §3). The findings triaged
as surviving are F1–F8 in [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §4.2, and per candidate in
[`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.2.

**(b) Released papers.** Public under **CC BY 4.0** (author decision, 2026-10-15). The first one is built:
`papers/encoder-crossover-190/` (candidate #3). The paper texts are measurements and are publishable as
such ([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §4.3).

**(c) Released artifacts — the "minimal reproducibility subset" norm, already implemented.** Per
`repro/encoder-crossover-190/README.md`: *"every paper ships a **minimal reproducibility subset** — fixture
schema, the fixture, the evaluation harness and the exact commands, and the pre-registered protocols.
**Withheld: the agent-state kernel / runtime implementation, and any model weights.**"* The subset itself is
source-available under **PolyForm Noncommercial 1.0.0**; its *content* is covered by the paper's CC BY 4.0
decision, and the two instruments are kept separate on purpose (CC BY-NC is the wrong instrument for code —
[`CODE_LICENSING_STRATEGY.md`](CODE_LICENSING_STRATEGY.md) §3.4).

**(d) The single release set that exists today:** `repro/encoder-crossover-190/` (fixture, schema, harness,
commands, protocols) and `papers/encoder-crossover-190/` (manuscript + availability statement). Every other
extracted-project paper still lacks its subset — recorded, with the artifact named, in
[`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.

---

## 4. The O-1 cost, stated plainly (not argued)

> **[CORRECTED 2026-10-15 by UWITH1 per UVER6 C2 — this premise is false. The architectural/system claim
> **is** published, dated, authored and citable: the loop claim and §5.5's five-layer rule are inside the
> byte-identical public file (§8.1), and the public repo is their address. The cost priced here does not
> exist, and the consequence inverts in the author's favour — the (B)(5) "published contribution" question
> is now answerable *with* a prior-disclosure date of ≤ 2026-10-10. See §8.7. The original text stands below
> as the record of what was issued.]**

**Withholding the blanket paper means the architectural/system claim is never published and cannot be **[Forward pointer (UFIXAD7): this §4 sentence is not a live assertion — §8.7 (`strategy/WITHHELD.md:398`) supersedes §4 and records that the O-1 inversion was corrected: the architectural/system claim *is* published, dated ≤ 2026-10-10.]**
claimed as a published contribution.** What survives is the **empirical findings** from each extracted
project. Concretely, the citable record will contain the measurements and not the architecture: W3 gets no
DOI, no venue, no citation path, and no expert letter can honestly call it a published contribution —
because it is not one.

**This is a deliberate cost the author accepted, and it is the correct trade under the stated intent**
(the author's words: *"i wanna keep the core pieces trade secrets"*). It is recorded as a cost, not as an
error, and it is recorded here rather than only in a strategy file because it changes what the O-1 evidence
chain may claim: the **(B)(5)** "original contributions of major significance" argument must be carried by
**per-paper empirical findings and their independent citations**, not by a systems claim
([`PUBLICATION_STRATEGY.md`](PUBLICATION_STRATEGY.md) §13(e)).

---

## 5. Why this register is itself a measure

A trade secret requires the owner to have taken **reasonable measures** to keep the information secret
([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §1.1, quoting the definition at 18 U.S.C. §1839(3)). The
measures now on record, in the order a reviewer would see them:

1. **This register** — a dated, itemised, author-attributed list of what is deliberately not published, with
   a stated reason per item.
2. **The papers themselves withhold.** The built manuscript states in its availability section that the
   kernel/runtime (`src/**`, `kernel/**`) *"is the system the measurement is about, and it is not
   released"* — a sentence that **withholds rather than discloses**
   ([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §4.3).
3. **The release set excludes.** W5/W6 are excluded by construction from `repro/…`, and the subset's own
   README says so.
4. **The licence is non-open.** PolyForm Noncommercial 1.0.0 for released pieces; the main repository stays
   proprietary.

> **[CORRECTED 2026-10-15 by UWITH1 per UVER6 C4/O2 — item 1 cannot be listed as a measure protecting the
> mechanisms in §2: M1–M10, M11, M12 and M13 are already public (§8.1, §8.9), and a register cannot claim secrecy over
> published material. As re-issued, this register is a measure over the **implementation** only (§8.3). Item 3
> is strictly true of W5/W6; the planned release set still carries M10/M11/M12 vocabulary (UVER6 O2), and
> that is registered as open (§8.5). W1's withholding is a programme decision *not to republish an
> already-public document*, not a secrecy measure (UVER6 C4) — its standalone-test reason survives
> independently (PAPER_CANDIDATES.md §G.1).]**

**What this register is not:** it is not a remediation plan and it is not an edit list. **No minimal edit
exists for W1** — the disclosed material is not incidental to that paper, it *is* the paper
([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §5.1). That is why the entry is `withhold` and not
`abstract-to-findings`.

---

## 6. Change control (append-only)

- **An item is removed from this register only by a new, dated entry below naming the item, the author's
  decision, and the new disposition.** Nothing in §1–§2 is edited in place, ever.
- **Releasing a withheld mechanism is irreversible in the legal sense**: once generally known, the trade
  secret in it is gone for everyone
  ([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §2). A prospective "un-withhold" entry must say so.
- **M11's disposition is open** and is the one entry in §2 that is not settled **[corrected by UWITH1 per
  UVER6 C6, 2026-10-15 — this clause is FALSE. M11 is the one entry whose *public-disclosure* status is
  undetermined (§8.2) **[WITHDRAWN as stale by UFIX9, 2026-10-15: §8.2 is superseded by §8.9 — M11 is
  *disclosed*, and no part of M11's disclosure status is undetermined. The correction still stands on its
  second half, kept verbatim below]**, but it is not the only unsettled entry: `TRADE_SECRET_AUDIT.md` §4.3/§5.2 put **M11
  and M12** in the release set, with **M10 and M7** disclosed through the rationale prose, and UVER6
  re-verified the M12 half — the fixture carries **15 `src/` mentions** and the sanitised variant **9**. See
  §8.5.]**: the `DecisionKind` union and the `DecisionCase` schema are **already inside the planned release set** for candidate #3, and the fixture's
  rationale prose names kernel internals. The deciding question — whether the release keeps the schema, the
  rationales, both, or a reduced fixture — is the author's, and it is stated in
  [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §4.3/§5.2 and
  [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.3. **It is not decided here.**
- **Date of this register:** 2026-10-15. **Author of the rule:** the repository author (relayed verbatim in
  §0). **Unit that compiled it:** UCAND1.

**Change log.**

| Date | Unit | Change |
|---|---|---|
| 2026-10-15 | UCAND1 | Register created. W1–W7 and M1–M13 entered; §3 release side recorded; §4 O-1 cost stated. |

---

## 7. Not determined here (`UNVERIFIED`)

1. **M11 / the `DecisionCase` schema and fixture rationales** — an open author decision, not a register
   entry (§6). Until it is made, the release set for candidate #3 is not final.
2. **The exact release set for every candidate other than #3** — none exists on disk yet; §3(d) and
   [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G name the artifact each paper *must* ship.
3. **Whether any already-published external material discloses a mechanism in §2** — this register covers
   *this workspace's* outputs; [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §5.2–§5.3 covers the
   already-planned release set and the mosaic risk, and is the authority on that question. **[ANSWERED
   2026-10-15 by UWITH1 per UVER6/UDISC1 — the decisive object is not external: it is the author's own public
   repository `Aswin-Ram-K/publish-present-compete`, which discloses M1–M10, M12 and M13 in a byte-identical
   copy of the withheld paper. §8.1; [`PRIOR_DISCLOSURE_AUDIT.md`](PRIOR_DISCLOSURE_AUDIT.md) is the
   authority. §5.2–§5.3 remain the authority on the planned release set.]** *(UFIX9, 2026-10-15: M11 is
   disclosed as well, but through the same public repo's `decisions/DECISION_LOG.md` — not through the
   paper, which carries no M11 anchor; see §8.9. The sentence above is about the paper copy and stays
   true.)*
4. **Legal effect of the register.** Nothing in this file is legal advice; a trade-secret position with
   commercial intent is worth a lawyer's time ([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) preamble).

---

## 8. RE-ISSUE — the mechanisms are public, the implementation is not (UWITH1, 2026-10-15)

**Why this section exists.** The register as issued (§1–§2) recorded M1–M13 as withheld. An independent
prior-disclosure audit found, and an independent verifier re-verified with a hash on both sides, that **12 of
the 13 mechanisms are already public** **[corrected 2026-10-15 by UFIX9: the count is **13 of 13** — M11 was
settled `disclosed` by UDISC2 (§8.9), which read `decisions/DECISION_LOG.md` that UDISC1's bound did not.]**. This section is the correction, appended under §6 — **not a silent
rewrite**. Where this section and §1–§4 disagree, **this section governs**. §1–§2 are not edited: they stand
as the dated record of what was issued, and §6 forbids editing them.

### 8.1 ALREADY PUBLIC — M1–M13 **[M11 added 2026-10-15 by UFIX9, §8.9; this heading read *"M1–M10, M12 and M13"*]**

**The disclosure channel.** `https://github.com/Aswin-Ram-K/publish-present-compete` — **PUBLIC**,
**MIT**-licensed, 38 commits, last commit **2026-10-10** (UDISC1 §1). Its `findings/PAPER-DERIVATION.md` is
**byte-identical** to `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`:

- **46,636 B** on both sides;
- sha256 `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802` on both sides — UVER6 hashed the
  local file *and* the network copy (`raw.githubusercontent.com`, HTTP 200) and they match; **UWITH1
  re-hashed the local file on 2026-10-15 and reproduces the same digest** (`sha256sum`, 46,636 B).

Because `TRADE_SECRET_AUDIT.md` §4.1's own **"Disclosed at"** column anchors each mechanism in that file at
named lines, the disclosure is derivable from the hash alone: the public copy *is* the anchored document.
**[UFIX9, 2026-10-15: that derivation covers M1–M10, M12 and M13. **M11 is the exception** — it has no
anchor in `PAPER-DERIVATION.md`, so its disclosure rests on the quoted `DECISION_LOG.md` passages in its
row below, not on the hash.]**

The lines below are those anchors (as tabulated by UVER6 against audit §4.1). A second, independent channel
exists for M1/M3/M10: the public profile README (`Aswin-Ram-K/Aswin-Ram-K`, MIT, public ≤ 2026-10-08) states
*"Enforcement by absence, not refusal"* and the capability-materialisation/digest A/B; `WHITEPAPER.md` and
`decisions/DECISION_LOG.md` are likewise public in the same repo (UDISC1 §1–§2, §4).

| ID | Public location | Date public | Licence | Anchor (audit §4.1) + evidence |
|---|---|---|---|---|
| **M1** | `publish-present-compete/findings/PAPER-DERIVATION.md` | ≤ **2026-10-10** (self-dated 2026-10-01) | **MIT** | abstract `:14–16`, §1.3, §4.2, §5.1, §5.5; profile README; **byte-identical**, sha256 `d98c4359…` |
| **M2** | same file | ≤ 2026-10-10 | MIT | §4.2 `:219–223`, `:236–240`; **byte-identical** |
| **M3** | same file | ≤ 2026-10-10 | MIT | §4.2 `:249–252`, §4.6 `:414–419`; also public `DECISION_LOG.md` D-004/D-005; **byte-identical** |
| **M4** | same file | ≤ 2026-10-10 | MIT | §4.3 `:257–292`, §5.2, §5.6; **byte-identical** |
| **M5** | same file | ≤ 2026-10-10 | MIT | §4.3b `:301–331`, §5.2, §6.3; **byte-identical** |
| **M6** | same file | ≤ 2026-10-10 | MIT | §4.4 `:336–356`; **byte-identical** |
| **M7** | same file | ≤ 2026-10-10 | MIT | §4.5 `:380–397`, §4.6; **byte-identical** |
| **M8** | same file | ≤ 2026-10-10 | MIT | §4.6 `:421–444`, §5.4; **byte-identical** |
| **M9** | same file | ≤ 2026-10-10 | MIT | §5.5 `:600–611`; **byte-identical** |
| **M10** | same file | ≤ 2026-10-10 | MIT | §1.3 `:63–64`, §4.4; also `WHITEPAPER.md` §4/§5.2 (*"`admit()` was invoked zero times"*) and `DECISION_LOG.md` D-009; profile README; **byte-identical** |
| **M11** | `publish-present-compete/decisions/DECISION_LOG.md` **D-024**, D-045, D-048 **[added 2026-10-15 by UFIX9, §8.9]** | **2026-09-29** (self-dated) | **MIT** | **UDISC2 §2**: D-024 verbatim — *"**Decision.** Kernel (verified, first-class): `task`, `evidence`, `execution`, `capability`, `policy`, `decision`. Modules (behind an interface, replaceable per §21): `artifact`, `memory`, `knowledge`, `meta`, `world`, `hypothesis`."* — **exactly the six namespaces of the audit's M11**; kinds *"(`topology` +6.8, `memory.admission` +6.2, but `acquisition` −7.7)"* · *"`escalation` is **0.933 for the 2B**"*. **UDISC2 recorded no hash for this row** — the evidence is a verbatim quote from a fetched public file, not a digest; none is invented here. |
| **M12** | same file | ≤ 2026-10-10 | MIT | §4.1.1 `:179–185`, §4.2 `:250–251`; **byte-identical** |
| **M13** | same file | ≤ 2026-10-10 | MIT | §7 `:690–697`, §8 `:711–719`; **byte-identical** |

**What that means, stated plainly.**

1. **A trade secret in M1–M13 is not available** **[list corrected 2026-10-15 by UFIX9 — it read *"M1–M10,
   M12 and M13"* before M11 was settled (§8.9)]**. Disclosure destroyed it: the information is
   generally known and readily ascertainable from a document anyone can fetch (18 U.S.C. §1839(3), the
   definition [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §1.1 quotes). No measure — including this
   register — can restore it.
2. **No patent fallback for the described mechanisms either**: these are printed publications dated
   2026-10-01/08/10 (M11, in `DECISION_LOG.md` D-024, is dated **2026-09-29** — earlier still), i.e. prior art under 35 U.S.C. §102(a)(1) (UDISC1 §5). The author's *"No patents"* rule
   (§0 rule 1) is therefore not the operative constraint on this material — disclosure is.
3. **The MIT licence already grants free commercial use of those versions, and it is irrevocable for copies
   already distributed.** A royalty-free permission to use, copy, modify, merge, publish and distribute is
   granted over the already-published material; withdrawing the repository reduces *future* dissemination and
   cannot recall or re-license copies already out (UDISC1 §5, "the one actionable lever, and its limit"). The
   noncommercial instrument planned for released pieces (§0 rule 4) therefore **cannot** be applied
   retroactively to this material.
4. **Withholding these mechanisms inside *this* workspace protects nothing.** What remains withholdable is the
   **implementation** (§8.3) — exactly what the public repo itself says it does not carry: *"The
   implementation is not published here. The code stays private; this repository carries the findings, the
   numbers, the method and the reasoning."* (public `README.md`, quoted in UDISC1 §2).

### 8.2 UNDETERMINED — M11, and only M11 **[SUPERSEDED 2026-10-15 by UFIX9 — see §8.9: M11 is `disclosed`, not `undetermined`. The body below is retained unedited as the record of what was issued.]**

M11 (the `DecisionKind` union and the six kernel namespaces) has **no anchor in `PAPER-DERIVATION.md`**, and
the one public document very likely to carry it — `decisions/DECISION_LOG.md` (99 decisions, 339,879 B) — was
**not read** within the audit's bound (UDISC1 §3 M11; UVER6 `not_reproduced`). It is therefore
**`undetermined`**: not asserted public and not asserted secret. **Do not guess either way.** The one
confirmed fact about M11 is a release-side one: parts of it are already inside candidate #3's planned release
set (§8.5). **[WITHDRAWN as stale by UFIX9, 2026-10-15 — the premise that `DECISION_LOG.md` was out of
bound is no longer true: UDISC2 read it and located D-024/D-045/D-048, so M11 is `disclosed` (§8.9). The
release-side fact above still stands.]**

### 8.3 What this register now protects — the IMPLEMENTATION

The residual protectable asset is the code and the unpublished prose — the thing the public repo explicitly
does not carry (UDISC1 §5, *"Still protectable — the implementation"*). **This section, not §2, is the
register's protective claim.**

| Protected item | Registered as | Basis |
|---|---|---|
| The contents of `src/**` (and `kernel/**`) — the agent-state kernel / runtime implementation, including its concrete type declarations | W5 | Excluded from every release set; `repro/encoder-crossover-190/README.md` (*"Withheld: the agent-state kernel / runtime implementation"*) |
| The **code-level state-class catalogue** — the classes as implemented, as distinct from the published prose about capability materialisation | (named here; covered by W5) | UDISC1 §5; no public artifact carries the code |
| **Private corpora** — the record corpora and any data not in a released subset | (named here; covered by W5) | UDISC1 §5 |
| `tools/**` — the experiment trees: `tools/derivation/`, `tools/resume/engine.ts`, `tools/refs/`, `tools/context/`, `tools/replay/exp7.ts`, … | M13 | `TRADE_SECRET_AUDIT.md` §4.1; publishing the inventory maps the private repo |
| **Model weights** (trained encoder heads, deciders) | W6 | Same author decision as W5 |
| **Unpublished prose** — `CONSONANCE.md`, the monograph, *Self-Improving Build Architecture* | (named here; no public copy) | UDISC1 §5 |
| **Patents** — none filed, none planned | W7 | Author rule 1 (§0) |

The new rows are **named here in prose only**, and are given no new `W`/`M` ids, because they are the same
asset W5/W6/M13 already cover; inventing ids would imply the audit triaged them separately.

### 8.4 The corrected strategy, in one place

> **Publish the design, keep the code.**

That is what this register now records, and it is what the author **has already executed** — a public design
repository (`publish-present-compete`, MIT) and a private implementation repository (`Consonance`, 404 to an
unauthenticated fetch), **whether or not by intention** (UDISC1 §1–§2). Its consequences:

- The **mechanism descriptions are a published contribution** — dated (≤ 2026-10-10), authored, citable.
- The **implementation is the trade secret**, protectable only while it stays out of the public record.
- Every released paper and its subset (`repro/**`, `papers/**`) must therefore be scrubbed of implementation
  detail — `src/**` paths, concrete type declarations, the code-level state catalogue — which is exactly the
  M11/M12 cut already registered as open (§6, §8.5).

**What this re-issue does not change.** The candidate split — **9 `publish` / 1 `withhold` / 5
`needs-author-decision`** — is re-derived and correct (UVER6 §2) and is **not** re-triaged here. Neither is
the release licence split (papers CC BY 4.0; code PolyForm Noncommercial).

### 8.5 C6 corrected — M11 is not "the one entry not settled"

§6 as issued said M11's disposition is *"the one entry in §2 that is not settled"*. **That is false.**
`TRADE_SECRET_AUDIT.md` §4.3/§5.2 put **M11 and M12 in the release set**, with **M10 and M7** disclosed
through the rationale prose. UVER6 re-verified the M12 half on disk: the fixture
`repro/encoder-crossover-190/fixture/reflex-decisions.ts` carries **15 `src/` mentions**, and the sanitised
variant still carries **9** — so M12's flat `withhold` status is also untrue against the current release set.

**Correct statement:** *M11 **and M12** (and, through the rationale prose, M10 and M7) are already inside the
planned release set; the open decision covers the `DecisionKind` union, the schema, the rationales **and the
`src/**` path names**.* M11 may be the only entry whose **public-disclosure** status is undetermined (§8.2) —
but that is a different question from whether it is settled. **[UFIX9, 2026-10-15: the italicised clause is
WITHDRAWN as stale — M11's public-disclosure status is **settled as `disclosed`** (§8.9), not undetermined.
The correction's other half — that M11 is not the only unsettled entry — stands and is unaffected.]**

### 8.6 The licensing consequence of the already-public material

- **The public repository is MIT** (UDISC1 §1). For the material that licence reaches, the grant is
  royalty-free and permits commercial use, modification and redistribution — **for those versions** — and it
  cannot be withdrawn for copies already distributed (§8.1 item 3). The author therefore cannot later sell a
  commercial licence over the already-public descriptions.
- **`UNVERIFIED` — prose under a software licence.** Whether the repo's MIT `LICENSE` reaches the **prose
  documents** (the whitepaper, `DECISION_LOG.md`, `findings/*.md`, the working paper) as distinct from the
  code is **not sourced here**: no primary licence text, `NOTICE` or scope statement from that repository was
  read. A repo-wide software licence attached to a repository containing prose is commonly read as covering
  the repository's contents, but **do not rely on either reading**. This is a question for counsel.
- **NOT LEGAL ADVICE**, as in the preamble: every legal proposition here is a pointer into
  [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) and
  [`PRIOR_DISCLOSURE_AUDIT.md`](PRIOR_DISCLOSURE_AUDIT.md).

### 8.7 The O-1 inversion, corrected (supersedes §4)

**§4 is superseded.** The cost it priced — *"the architectural/system claim is never published"* — **does
not exist**. The claim **is** published (§8.1; UDISC1 A2/A3), dated **≤ 2026-10-10**, authored and citable;
the public repo is its address. **The consequence inverts in the author's favour:** the (B)(5) "original
contributions of major significance" question may now be argued **with a prior-disclosure date attached**,
and the residual value being protected is the **implementation**, not the mechanism. §4's claim that W3 "gets
no DOI, no venue, no citation path" is therefore false as written. The narrow correction that does survive:
**no expert letter or petition line should describe the *code* as a published contribution**, because it is
not published.

### 8.8 Change log (appended)

| Date | Unit | Change |
|---|---|---|
| 2026-10-15 | UCAND1 | Register created. W1–W7 and M1–M13 entered; §3 release side recorded; §4 O-1 cost stated. |
| 2026-10-15 | UWITH1 | **Re-issue per §6, on UVER6's verdict that this register as issued was `fail`.** M1–M10, M12 and M13 moved to **ALREADY PUBLIC** (§8.1) with location, date, **MIT** licence and byte-identical evidence; M11 recorded **`undetermined`** (§8.2); the protective claim narrowed to the **implementation** (§8.3); the strategy stated once as *publish the design, keep the code* (§8.4); **C6 corrected** (§8.5); the licensing consequence of the public material recorded with the prose-under-a-software-licence point `UNVERIFIED` (§8.6); the **O-1 inversion corrected** (§8.7); §4, §5, §6 and §7 marked corrected in place. The `TRADE_SECRET_AUDIT.md` withhold block is **not** edited (another unit's file); where the two disagree on §2's status column, this §8 governs. |
| 2026-10-15 | UFIX9 | **M11 corrected from `undetermined` to `disclosed`** (13 of 13), per UDISC2's `DISCLOSURE_INVENTORY.md` §2 M11 / `:78`, re-verified on disk. Added M11 to §8.1 with its `DECISION_LOG.md` D-024/D-045/D-048 location, date and **MIT** licence; the **`worker.class` / `context.package`** residue carried as the retained nuance; §8.2 marked superseded (text kept as issued); the stale `12 of 13` / `undetermined` statements in the header, §2's M11 row, §5, §6, §7.3 and §8.5 marked withdrawn — nothing deleted. **§8.3 is unchanged: M11 being public does not weaken it.** New §8.9 records the reconciliation. |

---

### 8.9 M11 is DISCLOSED — the register is 13 of 13 (UFIX9, 2026-10-15)

**What changed, and why.** §8.2 recorded M11 as `undetermined` on UDISC1's finding that
`decisions/DECISION_LOG.md` had not been read. **That finding was true of UDISC1 and false against the current
disk state.** UDISC2 — the later, more complete disclosure audit — read the file: its
[`DISCLOSURE_INVENTORY.md`](DISCLOSURE_INVENTORY.md) §2 records M11 as **`disclosed — settled by UDISC2`**,
citing the fetched public `decisions/DECISION_LOG.md` **D-024** (with D-045, D-048) and quoting D-024
verbatim — it names exactly the audit's **six kernel namespaces** (`task`, `evidence`, `execution`,
`capability`, `policy`, `decision`) and the module set. That file's tally at `:78` reads **13 disclosed · 0 not
disclosed · 0 cannot determine.** This unit re-read the M11 row and the tally on disk before editing: the
evidence is a **fetched and quoted** public source, so the correction does not propagate one unit's claim over
another's. UWITH1 wrote from UVER6's *earlier* facts and did not have UDISC2's finding — the third instance in
this session of a unit recording a fact true from an earlier report and false against the latest disk state.

**The evidence is a quote, not a hash.** For M1–M10, M12 and M13, disclosure is derivable from the
byte-identical sha256 `d98c4359…` of `PAPER-DERIVATION.md`. **M11 has no anchor in that file, and UDISC2
recorded no hash for it** — so its §8.1 row cites the D-024 verbatim passage and says so. **No hash is
invented.**

**The nuance is carried across, and it matters.** `DISCLOSURE_INVENTORY.md:215` records that two
`DecisionKind` members from the M11 audit wording — **`worker.class`** and **`context.package`** — were **not
located** in `DECISION_LOG.md` D-001–D-049 (its §8 item 5 lists them `UNVERIFIED`). **M11 is disclosed; not
every last member name is.** The six namespaces and five of seven kinds are public verbatim; those two strings
are unconfirmed. Both statements stand together, and neither is allowed to swallow the other.

**The protective conclusion is unchanged — M11 being public does not weaken §8.3.** It sharpens it: the public
repo carries the design prose and explicitly does not carry the implementation (`README.md`: *"The
implementation is not published here."*), and UDISC2 verified that `consonance/src/journal.ts` and
`src/journal.ts` return **404 at every historical ref** while a control README returns **200**. What this
register protects remains the **implementation** — `src/**`, `kernel/**`, concrete type declarations, private
corpora, `tools/**`, model weights and unpublished prose (§8.3). No reader should infer that M11's disclosure
widens the protected set.

**Dated correction (2026-10-16, unit UFIXAD6).** *(UFIXAD7: this date slip is drift, not an isolated one — the register's older durable notes share the same stale `2026-10-15` token (whole-workspace `*.md` count: 1108 files say `2026-10-15` against 189 saying `2026-10-16`), so mtimes are authoritative and the token is not.)* The paragraph above is preserved as written, but its retrieval premise — *"404 at every historical ref"* — is **false as written** and is corrected here. It held only for *branch/tag-reachable* refs (`main`, `06d618ca`, `d7072672`) and for *path-absent* refs; it was never universal. The code was publicly reachable on the **unreferenced old head `89003e7069c9ad79c40d91982720751b1ddf0360`**, where `consonance/src/journal.ts` returned **HTTP 200 / 46,450 bytes** (also `consonance/src/dag.ts` 200/44,468 B, `consonance/src/store.ts` 200/3,316 B), and the window carried **481 entries, 428 under `consonance/`, with 35 blobs under `consonance/src/` totalling 708,575 bytes**. The `consonance/` → target `src/**` mapping is recorded (`strategy/DISCLOSURE_INVENTORY.md:19`, `:38`, `:44`) and corroborated by three exact byte-size matches against `/home/zer0null/Duval`: `src/journal.ts` 46,450 B, `src/dag.ts` 44,468 B, `src/store.ts` 3,316 B. **Do not read `ccdab112` as having carried `consonance/`:** that boundary commit's tree is `.gitignore CLAIMS.tsv README.md SOURCES.tsv` — no `consonance/` directory at all. The boundary is `ccdab112` (2026-10-09 04:11) → `b81b35e` (2026-10-10 07:51), event-measured 2026-10-09T04:20:17Z → 2026-10-10T07:52:54Z (~27.5 h). **The protective conclusion is unaffected and binding:** the implementation expression must not be republished, and no filing, declaration or exhibit may assert the work was never published. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`.

**What this section does not do.** It does not re-open the mechanism question; it does not edit
`DISCLOSURE_INVENTORY.md` (another unit's file, and the authority here). The release-set question on the
`DecisionKind` union, the `DecisionCase` schema and the fixture remains the **author's** (§6, §8.5), and the
`worker.class` / `context.package` strings remain `UNVERIFIED` — a named residue, not secrecy.

