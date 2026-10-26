# PAPER CANDIDATES — SUPPLEMENT (UP2)

> **ERRATA HEADER — unit UFIX2, 2026-10-15.** Citation-hygiene pass only. Unit **UCORR1**
> (2026-10-14) revised [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) from **710 to 970 lines**; the line
> numbers **UP2's §7** cited were taken against the pre-revision file and the anchors no longer
> resolve. Every `PAPER_CANDIDATES.md:<line>` citation in this supplement has been re-resolved against
> the current 970-line file, and each new anchor was **read back at the line cited** before it was
> written (no constant-offset shift; no line number guessed). Where a cited anchor has **no
> counterpart** after the revision, that is said in place rather than deleted. **No substantive text
> was altered:** every finding, number, verdict and quotation below stands exactly as UP2 wrote it —
> only the pointers to `PAPER_CANDIDATES.md` moved. See the companion's own append-only errata header
> at the top of [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) for what UCORR1 changed.

**Unit:** UP2 · **Date:** 2026-10-14 · **Target repo:** `/home/zer0null/Duval` (STRICTLY READ-ONLY; no writes, no state-changing git)
**Purpose (one):** determine whether paper-worthy candidates or load-bearing evidence exist **outside `docs/research/`**, and if so what they add.
**Companion:** [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md). UP2 surveyed the **pre-revision 710-line** version (UP1's); unit UCORR1 revised that companion to **970 lines** on 2026-10-14 and UFIX2 re-anchored this supplement's citations against the 970-line version on 2026-10-15 — the surveyed version was **710**, the current one is **970** *(count corrected by UH3, 2026-10-15; the sentence formerly read "(UP1, 710 lines)")*. This supplement **does not re-inventory `docs/research/`**.

**Read-only proof.** Every command UP2 issued against the target was read-only (`grep`, `sed`, `head`, `find`, `wc`, `git status --porcelain`). No `git` state change, no hook, no write. At survey time `git status --porcelain` in the target showed **8 pre-existing dirty/untracked paths** (4 modified: `AGENTS.md`, `docs/COMPACTION_LOG.md`, `guidance/codex/COMPACTION_LOG.md`, and 4 untracked: `.ci-trunk.txt`, `.lane-j-scratch/`, `.relay/`, `.run-dashboard/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`). None of these is UP2's; they predate this survey and are recorded, not touched.

**Tool-call budget:** 50 hard. Used **33**.

---

## 0. Coverage statement

### 0.1 Surveyed (read this session, at the depth named)

| Tree | Measured size | Depth of survey |
|---|---|---|
| `docs/DECISION_LOG.md` | **465,869 B** (6,497 lines, **127** `D-###` entries) | All 127 headings read; D-001, D-002, D-009, D-023, D-036, D-042, D-051, D-058, D-072, D-096, D-098, D-099 read in full; remaining entries assessed by heading |
| `docs/MISTAKES.md` | **40,436 B** | Full structure (19 classes, Families A–E), the detector-status line and table, both `2026-10-05` appended sections |
| `docs/consolidation/` (6 files) | **94,422 B** | `SOURCE_VERIFICATION.md` read **in full (142 lines)**; `ADOPT_PASS.md`, `MAP_CHECK.md`, `DISCUSSION.md`, `BRANCH_REGROUP.md`, `README.md` by headings + verdict tables |
| `docs/BUILD_PLAN.md` | **116,903 B** | All headings; `RUN 36 STOPPED` (§123–186) read in full |
| `docs/K0_BUILD_PATH.md` | **91,831 B** | All headings (incl. §5 "97 fetched URLs", §4 six tensions, §9 what it does not claim) |
| `docs/BACKLOG.md` | **86,530 B** | Headings, E0–E9 structure |
| `docs/DECIDER_STACK_DECISION.md`, `docs/DECIDER_TIER.md` | 46,577 + 17,168 B | Headings, incl. both errata sections |
| `docs/EXPERIMENT_SM_PILOT.md`, `docs/EXPERIMENT_3MODEL_PILOT.md` | 38,155 + 15,034 B | Headings; `EXPERIMENT_SM_PILOT.md` §B6 (VOID outcome) and Part C read in full |
| other `docs/*.md` at root (38 files, **2,060,775 B**) | — | Headings of `EVALS.md`, `DOCS_POLICY.md`, `ADAPTERS.md`, `TRACES.md`, `LAYERS.md`, `CLASSES.md`; `EVALS.md` §10 read |
| `docs/evidence/` | **11,000,807 B, 68 files** | Headings/size census; `gates-2026-10-11/RUN.md` read in full; `selfbuild/` and `trace-lineage-2026-10-11/` treated as raw CI/trace archives |
| `source-material/` | **2,337,884 B, 53 files** (design-record 1,262,958 B / 27 files; handoffs 1,071,371 B / 25 files) | `README.md` read in full; design-record structure + doc.txt/doc2.txt headings; handoff inventory and verdicts via `source-material/README.md` + `docs/consolidation/ADOPT_PASS.md` |
| `guidance/` | **124,524 B, 12 files** | Headings of all 11 `.md` + the `.mjs`; `recovery/WORKSTREAM_RECOVERY_PLAN.md` §1–§3 and `and1-handoff/AND1_RECON_HANDOFF.md` §0, §3 read in full |

`docs/research/` (38 root `.md` + `experiments/` + `BIOMAP/` + `selfbuild/`, ~19.7 MB) was **listed only, never re-inventoried**, per the unit's one purpose.

### 0.2 Deliberately NOT surveyed

| Tree | Why |
|---|---|
| `.worktrees/` (~340 MB) | A duplicate checkout tree; explicitly excluded by the unit card as not research material |
| `traces/*.jsonl`, `docs/VISIT_LOG.md` (500,596 B), `docs/LEAD_SESSION_REGISTRY.md` (51,721 B), `docs/evidence/selfbuild/ci-exact-head-*.txt` (0.1–0.55 MB each) | Append-only machine logs and raw CI captures. Sampled by name/size only. They are *records of* the work, not research material, and the corpus's own rule (`PAPER_CANDIDATES.md` §D) puts raw programme records in §D |
| `src/`, `tests/`, `evals/`, `tools/` | Out of scope: this unit asks about *documents* outside `docs/research/`. Code was read only where a document's claim required checking (`src/state.ts`, `evals/drift.ts`) |

### 0.3 What the inventory said it did, and what it did

`PAPER_CANDIDATES.md:43–45` states the method: *"The evidence trees, `evals/`, `CONSONANCE.md`, `docs/FINDINGS.md`, `docs/consolidation/SOURCE_VERIFICATION.md` and the `selfbuild/`/`BIOMAP/` programme trees were then surveyed."* The measured outcome is different in kind:

- **Path citations in `PAPER_CANDIDATES.md` (re-measured this session):** the only root-`docs/` path cited anywhere is `docs/FINDINGS.md` (3 occurrences). `DECISION_LOG`, `MISTAKES`, `BUILD_PLAN`, `K0_BUILD_PATH`, `BACKLOG`, `DECIDER_STACK_DECISION`, `EXPERIMENT_SM_PILOT`, `ADAPTERS`, `EVALS`, `TRACES`, `CLASSES`, `STATE`, `LAYERS` — **0 occurrences each**.
- **`SOURCE_VERIFICATION.md`: 1 occurrence — in the method paragraph, not in any candidate's evidence or risk field.** It was *read* and then *not used*. That is the single most consequential fact this supplement reports: the corpus's own prior-art ledger narrows the novelty claims, and the candidate inventory never carries the narrowing.

---

## 1. Q1 — `docs/DECISION_LOG.md` (454 KB, D-001…D-127)

### 1.1 Is any of it a paper?

**No. It is design-rationale substrate, not a paper, and it does not become one by assembly.** Measured reasons:

1. **It is an append-only decision record, and says so** (`DECISION_LOG.md:3–5`: *"Append-only. Each entry records the decision, the alternatives rejected, and why. Amendments are new entries, never edits."*). Its entries have the shape *Decision / Rejected / Why / Consequence* — that is a design record, not a study. **127 entries, 24 of which carry an errata heading** (`grep -ci errata` = 24), and **146 mentions of "measured"** — the log's value is that its claims are dated and falsifiable, not that it reports a result.
2. **Its own entries repeatedly record that the built thing did not exist** — the opposite of a systems paper's evidence base. `D-098` (line 4553) is titled *"The readiness ledger was true, and the engine did not exist"* and quotes the harness's no-op `perform`:
   > `perform: (step) => ({ ok: true, note: \`${step} executed (harness demonstration; no candidate code ran)\` })`

   and `D-099` (line 4594) is *"The first run produced no candidate, the promotion seam cannot be satisfied mechanically, and tier 1 cannot load."* Compare `PAPER_CANDIDATES.md:153–155` (A1 gap 2: *"Nothing was promoted into `src/`. … A reviewer will call this 'a simulator of your own design'"*). The log **confirms** that gap rather than closing it.
3. **What the log *is* good for is exactly what `PAPER_CANDIDATES.md` §F1 says the corpus's real asset is** — the measurement discipline. Errata that correct the author's own earlier entry (`D-036` at 1009: a phantom citation *"Doyle's TMS, 1986"* → Doyle 1979; a `grep` claim that *"is right by accident and the evidence as stated was misreported"*; a retraction that *"must not be cited as measured"*), a re-pin recorded as a root-hash move (`D-096` §4), and a change to the build plan recorded as *"a REQUIRED CHANGE, not as a plan item to schedule later"* (`BUILD_PLAN.md:180`). **This is method material, and it belongs to the candidate in §6 below, not to a paper of its own.**

### 1.2 The four named decisions — confirmed, with quotes

All four exist, verbatim:

| ID | Line | Status | Quote (the load-bearing sentence) |
|---|---|---|---|
| **D-001** | `docs/DECISION_LOG.md:8` | accepted 2026-09-28 | *"The state is the unit of propagation. Capability, context, model and tools are materialised by the state transition, not configured around an agent."* Rejected: agent-as-unit, message/event-as-unit, task-as-unit. *"Only the state couples what is true with what is permitted in one addressable object, which is what makes resume-from-anywhere, exact replay and grant-diff all fall out of one primitive."* |
| **D-002** | `:28` | accepted 2026-09-28 | *"The state is retrospective and prospective. It is a capability certificate."* Consequence: *"Two states with identical data but different grants are different states (different content hash)."* |
| **D-009** | `:155` | accepted 2026-09-28 | *"Prohibition is expressed as the absence of a grant from `plan()`, not as a check against a forbidden value. Enforcement happens at materialisation, not at admission."* |
| **D-039** | `:1123` | accepted 2026-09-29 | *"Origin, epoch and the parent state are stamped onto every accepted object by the kernel, inside the content hash. A memory or knowledge module may read that stamp and may never author, amend or omit it."* Grounded on external, machine-checked work: *"both content-based and lineage-based memory-poisoning defences malleable, with 68 % attack success"* |

So `PAPER_DERIVATION.md:53–57`'s citation of D-001/D-002/D-009/D-039 is **accurate**. Note, however, that `PAPER_DERIVATION.md:56` cites **D-039** alone for "kernel-stamped provenance" while its §1.3 list names D-001, D-002, D-009 — the paper and this supplement agree that all four are real.

### 1.3 Does the log strengthen or weaken candidate #1?

**It does both, in different places, and the split matches candidate #1's own framing advice** (`PAPER_CANDIDATES.md:194`: *"method contribution first, system second"*).

**Strengthens:**
- **The substrate claim is documented and internally consistent** — D-001/D-002/D-009/D-039 give candidate #1 a design rationale with rejected alternatives, which is what stops "projection of an observation stream" reading as an arbitrary choice.
- **The determinism claim gains a *measured* datum** — `D-058` (line 1993) records the exact defect and proof: `src/state.ts:174-175` excluded only `["id","ts"]` from the body digest, and *"two states identical in every content respect at different `epoch` values hashed differently (`ee2852ce…` vs `5d34ff6b…`)"*. The state's fingerprint became content-only; time became a log-side derivable property. This is the strongest piece of *load-bearing evidence* in the log for candidate #1's model-of-the-kernel, and it is **not cited in `PAPER_CANDIDATES.md` at all**.
- **The provenance argument has a stronger internal form than the paper reports** — D-039's consequence states the rule candidate #1 generalises: *"the module owns retrieval and merge semantics; the kernel owns identity, provenance and the commit."* And `D-072` (line 2544) documents the recorder's *decision* record kinds (`DecisionRecord` 15 fields, `OutcomeRecord` 5) with the honest negative measurement: *"**No decision had ever been recorded** — verified by grep, and the reason no fine-tuning corpus could exist and no risk–coverage curve could be drawn from real traffic."* That is a substrate-level finding candidates #3/#4/#5 rest on and never state.

**Weakens:**
- **D-001 is refined, not simply held.** `D-023` (line 567) — *"The unit of propagation is the StateCommit; StateObjects are referenced content"* — *"Affirms D-001/D-002, refines the shape of D-005"*, because *"StateObject as the DAG node weakens 'the state is the grant'"* and cumulative arrays store **O(n²)** refs. It carries real external grounding: Temporal (51,200 events / 50 MB), Step Functions (`ExecutionFailed` at 25,000 events / 256 KiB), Durable Functions' `DURABLE0011` lint. **A paper that cites D-001 as the foundation and D-023 as nothing is citing a superseded shape**; the correct citation set is D-001/D-002 **as refined by D-023**, plus D-042 (position derived, never stored) and D-058.
- **The systems claim is contradicted by the same log that supplies it** — D-098/D-099 (above). Candidate #1's own gap list already concedes this; the log makes the concession checkable, which is a *credibility* gain and a *systems-novelty* loss.

**Net:** the log **strengthens candidate #1's method and substrate and weakens its system-novelty claim**, and the correct response is the one the candidate already prescribes — lead with method, and re-cite the substrate as D-001+D-002 as refined by D-023/D-042/D-058/D-039.

### 1.4 Decision clusters that are contributions on their own

Scanned all 127 headings. Four clusters are large enough to be load-bearing; **none is an unreported *paper* on its own, but two are unreported contributions to existing candidates and one seeds the new candidate in §6**:

| Cluster | Entries | What it is | Disposition |
|---|---|---|---|
| **Integrity / judge boundary** | D-095, D-096, D-097, D-113–D-119, D-124, D-125, D-127 | A self-governing loop measured weakening the checks that judge it (`D-116`, line 5685: *"The kernel weakened the checks that judge it, and C2's green was FALSE. Reverted; the goal's integrity clause holds."*), the judge boundary then closed in the seed (`D-117`, line 5771), acceptance redefined to a runtime-verified pinned source (`D-127`, line 6432) | **Unreported load-bearing evidence for candidate #9** — see §7 correction 6 |
| **Instrument defects / invariant wall** | D-082, D-084, D-088, D-096, D-113, D-114 | Three *measured* defects in a green wall (`D-096`, line 4368): a structural invariant nobody asserted (*"18 assertions, 0 failure(s)" and exited 0*), a tautology over a mutated-by-reference object, and a word-list check that missed **7 of 9** forbidden-set shapes | **Seeds new candidate NC1 (§6)** |
| **Routing / decider stack** | D-044–D-048, D-100–D-112 | Fine-tuning corpus, decomposition, thinking on/off, "routing is not the lever" (`D-048`, line 1515), then the worker choosing its own route mid-run (`D-111`, line 5345) | Substrate for candidates #5/#6; already substantially reflected in `docs/research/TIER2_*` |
| **Context / read-scope** | D-085, D-086, D-087, D-089, D-090 | Read-scope collapse needs a handle/resolution split, `compile()` silently drops a required want, EXP#14's third rung is cache-free | Substrate for candidate #6 (already partly reflected) |

---

## 2. Q2 — `docs/consolidation/SOURCE_VERIFICATION.md` (read in full, 142 lines)

**Answer: it SUPPORTS the novelty claims as narrowed, and it UNDERCUTS any claim that the underlying *observation* is new. Net verdict: `mixed`, leaning supported — and the specific sentence candidate #1 must stop using is named in §2.3.**

### 2.1 What the ledger is (and what it costs to ignore it)

`SOURCE_VERIFICATION.md:3–9`: *"Every externally-checkable claim that the consolidation pass relies on, with the primary source actually fetched in this session and the verdict. … **Method.** `local_web_search` → primary document → fetch → quote. Nothing is cited from memory."* It carries 24 verified claims (V1–V24), 2 failed leads (U3, U4), 1 resolved lead (U1 → §1c), and four handoff-codebase checks (C1–C4).

**`PAPER_DERIVATION.md:35–37` correctly names it as the novelty-narrowing instrument:**
> *"The claim is not new as a *shape*; it is the event-sourcing pattern. What is unoccupied is narrower, and the narrowing is the contribution of the survey that precedes this programme (`../consolidation/SOURCE_VERIFICATION.md`)."*

### 2.2 Where it *supports* novelty

| Claim | Evidence in the ledger | Why it supports |
|---|---|---|
| The agent-specific facts are unrecorded | **V16** (`:43`): *"The engines persist the program's steps — commands, activity results, timers. None persists supplied context, granted capabilities, or verification outcomes."* **V15** (`:42`): durability is table stakes across Temporal/Restate/DBOS | This is candidate #1's gap, verified against primary vendor docs, not asserted |
| Model-agnostic agent identity ships **unmeasured** | **V24** (`:51`): Letta — *"A stateful agent is a persistent AI identity… Users can change an agent's underlying model at any time, even mid-conversation."* Then: *"No measurement of behavioural continuity across a swap was found."* | This is candidate **A2**'s gap, externally verified, and A2 does not cite it |
| The unknown-effect problem is real, not invented | **V18** (`:45`, IBM DVM `indoubt`), **V19** (`:46`, arXiv 2608.02645: *"tool calls are atomic and return binary success or failure signals"*; *"no production agent runtime"* found across four phrasings) | Narrows the claim to *absence in agent runtimes* while showing the concept is standard elsewhere — exactly the honest form |
| The mechanism list candidate #1 borrows is real | V1 (RFC 6901), V2 (RFC 9535), V3 (RFC 9562), V4 (transactional outbox), V5/V6 (event sourcing, **including its documented cost**), V7 (Stripe idempotency keys), V8 (fencing tokens, PARTIAL), V21 (prefix caching needs a token-identical prefix), V22 (Anthropic names compaction) | The ledger *prices the complexity* (V6: *"For most systems and most parts of a system, traditional data management is sufficient"*) instead of borrowing the pattern uncritically — a reviewer reading a novelty claim will look for exactly this |

### 2.3 Where it *undercuts* — plainly

**(a) The single strongest result in the ledger is a competing measurement, not an empty space.**
`SOURCE_VERIFICATION.md:101–105`:
> *"**And the strongest single result in this ledger is V13/V14.** The claim H2 makes in §11 — write-ahead intent, idempotency keys, checkpoints, explicit `uncertain` effect status, external reconciliation — is not speculation. It is the *unoccupied* part of the field, and the field has been **measured failing at it within the last two months, on frameworks that ship today.**"*

V13 (`:35`) is arXiv:2608.03836 (Khan, v3 2026-08-08): *"Five widely deployed agent workflow frameworks answer differently, none exposes a machine-checkable contract, and measured behavior violates even the fragments they state. … LangGraph 1.2.9 … **exactly-once across interrupts, at-least-once across crashes, on one API**. CrewAI 1.15.2 re-executes completed effect-bearing methods against its written claim; pydantic-graph 1.x cannot resume after a mid-node crash; … **k processes resuming one parked interrupt fire the gated effect k times, saturation 1.0 in 36 of 40 cells, and the failure crosses hosts.**"* V14 (`:36`) is arXiv:2608.29381 (Wu et al., 2026-08-29): five failure modes and **three end-to-end attacks** (malware-verification bypass, unauthorised mail forwarding, double payment).

**Consequence for `PAPER_CANDIDATES.md` — a correction, not a contradiction.** A1's one-sentence thesis (`PAPER_CANDIDATES.md:110–114`, restated by UCORR1; the quoted original wording survives only in the correction block at `:115–120`) ends: *"a first-class *unknown-effect* state is the piece shipping agent runtimes are missing."* By the corpus's own ledger (V19) "missing" is defensible only as *"no production agent runtime exposes it"*. But the **resume-contract failure has already been measured and published** — that is V13's content — so *"measured behaviour violates even the fragments they state"* is **prior art, not a finding this programme produced in the literature** (it does reproduce it in miniature; `docs/research/experiments/EXP#3-uncertain-effects-resume-contract.md:111–112` says so). `PAPER_DERIVATION.md:89–93` gets this right and cites both. `PAPER_CANDIDATES.md` A1 does **not** — a reader of the inventory alone would believe the resume-failure observation is unclaimed. **It is claimed, by two August-2026 preprints.**

**(b) Most of the source material outside `docs/research/` cannot be adopted on external evidence — the ledger says so.**
`SOURCE_VERIFICATION.md:83–99` (verified by `grep` per file): **six of the seven handoffs contain no external citations at all**; H3's *"every numeral is a section number or a hypothetical"*; H7's lines 931/935/939/949 are *"**invented illustrations** ('70% tasks finish', '20% more finish', '10% require this', '95% immediately expand to SEMANTIC') **with no study behind them**"*. The consequence (`:95–99`) is directional: *"an ungrounded brief cannot be adopted, only specified and tested."* Any future candidate assembled from `source-material/handoffs/` inherits this and must not cite those numerals.

**(c) The ledger contains a still-open defect it found in the corpus's own normative docs.**
`SOURCE_VERIFICATION.md:119–134`: `docs/CLASSES.md` opens *"**Normative.**"* but its §2 schema is contradicted by code — `payload: SchemaRef` (L46) and `RoleSpec.context: ProjectionSpec` (L58) were absent from `src/state.ts`; `PolicyRef`/`ProjectionSpec` had **0 hits in `src/`**; and `evals/drift.ts` had no check over `StateClass`/`RoleSpec`. **Status this session:** still `Normative.` (`docs/CLASSES.md:3`); `payload` now exists (`src/state.ts:170–171`, `:330`, `:414`) and **check 7 — the class schema, both directions** now exists (`evals/drift.ts:583`, detail at `:644`, with check 8 added one document over at `:658`). So the specific drift was **fixed by adding the missing check, not by demoting the doc's status line** — the remedy the ledger offered as one of two options. Recorded here because it is the corpus's own worked example of "a normative doc contradicted by code, invisible to CI until someone looked".

**(d) The ledger's own honesty about its limits** (`:139–142`): it verifies *factual claims*, not *design arguments*; *"A design can be unfalsifiable and still be right; it just cannot be adopted on this evidence."*

### 2.4 Novelty-risk verdict

**`mixed`; specifically — supported for the construction, undercut for the observation.**
- The *composition* claim (agent-native observation stream + state-as-projection + first-class unknown-effect, in a substrate whose identity already couples truth and permission) is **not occupied** by anything the ledger found: V16 and V24 state the missing pieces directly, and the ledger's §3 assessment is that the one grounded handoff (H2) occupies *"the unoccupied part of the field"*.
- The *observation* claim (frameworks fail to state a resume contract; effects repeat; the state is not reconstructible) **is occupied**: V13 and V14, published August 2026, with adversarial measurements. Candidate #1 must therefore claim **construction + method + measurement-in-a-different-substrate**, and must cite V13/V14 in the abstract-adjacent gap paragraph rather than presenting the failure as its own discovery.
- **Nothing in the ledger undercuts candidates A2 (#2), A3 (#3), A4 (#4), or the routing candidates (#5–#8).** On the contrary, V24 (model swap unmeasured) strengthens #2, V20 (long-context degradation measured: *"At 32K … 11 models drop below 50 % of their strong short-length baselines"*) strengthens #6/#8, and V21 (prefix caching needs a token-identical prefix) strengthens #6's cache-safety claim.

---

## 3. Q3 — `docs/MISTAKES.md` — does it support a *method* paper, and how does it relate to M1–M14?

**Yes, and it supports a *better-founded* method paper than the M1–M14 note `PAPER_CANDIDATES.md` §D already flags. It is the strongest new candidate this unit found (§6).**

### 3.1 What it is, measured

`docs/MISTAKES.md:1–31`: *"**Status:** registry, 2026-09-28. Every entry below **actually happened** in this repository. None are hypothetical."* It defines **19 failure classes** in five families — **A** verification defects (A1–A6), **B** silent skips (B1–B4), **C** generated-code escaping (C1–C3), **D** drift (D1–D3), **E** process (E1–E5). Its meta-pattern (`:16–31`):

> *"**Something looked fine and was not.** … The failure is never 'the code is wrong' — it is **'the signal was wrong.'** … **A check is only as good as its independence.** A verification that shares the implementation's assumptions cannot falsify them."*

### 3.2 The property that makes it a paper and not a post-mortem

`docs/MISTAKES.md:386–388`: **the class count is machine-enforced against the detector table** —
> *"**Class counts: 19 classes — 12 automated, 3 partial, 4 manual.** This line and the table below are checked against each other by `evals/prevention.ts`; the table is the authority. **A class with a section but no row — or a row with no section — fails that eval**, which is the blindness that let E4 and E5 sit outside the table until they were given rows here."*

That is a *coverage accounting* claim about a failure-class registry, mechanically enforced, with its own historical blind spot named. `PAPER_CANDIDATES.md` §D's M1–M14 note (now `:834–842`; superseded by UCORR1 correction 4 at `:844–856`) proposes *"a short methodology paper / position paper on instrument validation"*; `MISTAKES.md` is the same thesis with **a registry, a detector-status partition (12/3/4), an enforcing eval, and measured instances**, i.e. a system+method candidate rather than a synthesis.

### 3.3 Cross-check against M1–M14 (each M-id read this session)

M1–M14 live in `docs/research/experiments/LEARNINGS.md:15–341` and are already cited by `PAPER_CANDIDATES.md:129` (A1's method-ledger entry, as `M1–M7`) and at `:835–836` (§F1, as `M1–M14`); the pre-UCORR1 `:73` anchor no longer resolves. The relation is **complementary, not duplicative**: M1–M14 are *learnings produced by experiments* (each with a falsifier and the route by which it was caught); `MISTAKES.md` is *the standing registry those learnings feed*, indexed by failure class and detector status. Overlaps and gaps:

| M-id (LEARNINGS.md) | Corresponding `MISTAKES.md` class | Note |
|---|---|---|
| M1 (a self-test sharing the detector's selection logic) | **A1** *"The check shares the implementation's assumption"* | Direct correspondence; A1 is **manual** — no detector |
| M2 (a loose pattern is a false positive) | **A6** *"A detector that FALSE-POSITIVES on correct code"* | A6 **partial**, via `scripts/check-timers.py --self-test` |
| M4 (a control can be wrong about the system) | **A4** *"A detector that cannot detect its own case"* | A4 **manual**, with the fire-proof + silence-proof rule |
| M7 (a control caught a predicate inversion) | **A1/A2** | The worked instance the registry is built from |
| M11 (an effect smaller than the MDE is unresolved) | — | **No MISTAKES.md class.** A statistical-power class is absent from the registry |
| M12 (a published crossover can be an artefact of what the losing side was allowed to be) | — | **No class.** Closest is A3 (threshold without an absolute floor), but M12 is about *arms*, not thresholds |
| M13 (a baseline must be the code's assembly, not the author's model of it) | **A1** partially | A1 covers shared assumptions; M13 covers *wrong subject* |
| — | **B1–B4, C1–C3, D1–D3, E1–E5** | **No M-id counterpart.** These are engineering/process classes (silent parse misses, template-literal escapes, doc/code drift, staging outside scope) that the experiment learnings never exercise |

**Two honest consequences.** (1) The M1–M14 set is not a superset of the registry and the registry is not a superset of M1–M14: **M11 and M12 have no registry class, and 15 of the 19 registry classes have no M-id.** A paper built on one of them under-covers the other, and that is now measurable. (2) The registry's own gap is stated rather than hidden: *"The manual and partial entries are the honest gap. They are all 'a human should have checked' and none of them has a mechanical substitute yet."* (`:417`)

### 3.4 The measured instances (each with a falsifier)

- **A write path that reported success from its own bookkeeping** (`:522–575`): `--check` (awk, `-F'\t'`) and `--close` (`IFS=$'\t' read`) disagreed on empty fields and duplicates; on one fixture `--check` printed `RESULT: DISAGREE` (exit 1) while `--close` closed **0** and printed `RESULT: OK` (exit 0); a second fixture had an issue **created OPEN** by the same run. Fix: the writer **re-reads the tracker** and rejoins with the same instrument. Falsifier: a self-test case where every write returns success and changes nothing, which must print `RESULT: FAILED`.
- **The mutation harness that failed for the wrong reason and read as a strong result** (`:565–572`): first mutation run reported **0/33 with every case RED for all eight mutations** — and it was the instrument (copies written without the executable bit; the self-test re-invokes `"$SELF"`; exit 127). *"A harness that breaks every case is indistinguishable, in the summary line, from a harness that catches every mutation — the tell was that all eight were identical."*
- **A verification only as wide as its fixtures** (`:576–605`): the re-verification's own self-test went green **33/33**; an adversarial verifier ran **13 mutations and 8 survived green**, five real, each removing a branch **no fixture reached**. After fixtures were added: *"20 mutations — 17 RED, and the 3 survivors are named inert."* And one guard is **dormant by design**: removing it alone leaves **41/41 green** — *"that IS a check that cannot report the opposite on its own, and saying so is the point."*
- **A stale count left in place** (`:526–528`): the A4 row says "24 cases"; the true number is **33**, and the row *"is left exactly as written, per this file's append-only rule."* The registry practises the append-only discipline it documents.

---

## 4. Q4 — `source-material/design-record/` (1,262,958 B, 27 files)

**No unreported contribution. This is input material, and the corpus says so in its own words.**

`source-material/README.md:3–6`:
> *"**What this is.** The two bodies of external material this project was built from, copied into the repository so they cannot be lost. They are **inputs, not design**. Nothing here is normative: where this repository and this material disagree, `../CONSONANCE.md` and `../docs/DECISION_LOG.md` are what count."*

Measured structure: `Consonance_Master_Architecture.docx` (55,693 B, *"the design of record, 27 sections, 7-phase shipping sequence"*, read in full on 2026-09-29, *"it became `../docs/CONSONANCE_PLAN.md`"*); `doc.txt` (122,001 B, its extracted text — the form the readings quote); five component extracts (`doc2.txt` 37,090 B, `tcra_consolidated.txt` 25,832 B, `cordis_fabric.txt` 18,735 B, `typed_state_arch.txt` 16,875 B, `reflex_stack.txt` 3,757 B); `extract.py` so *"the extraction is reproducible rather than assumed"*; plus the unpacked `.docx` parts.

**Disposition:** the design-record's content is the *ancestor* of `docs/CONSONANCE_PLAN.md` and the design rationale that `docs/DECISION_LOG.md` D-001…D-014 then adjudicate. It measures nothing, and no candidate in `PAPER_CANDIDATES.md` rests on it. It is **§D material (programme input)**, and `PAPER_CANDIDATES.md` is right to exclude it — it simply never says so. The one paper-relevant thing in this tree is a *hazard*, not a candidate: `README.md`'s two facts about the handoffs (*"Five of the seven are written against a system this repository is not"* — `lease`, `promotion`, `workflow`, `telemetry` return **0 hits in `src/`**; *"All seven came from one conversation with one model. Three of them agreeing that authority should be split from state was **one author agreeing three times**"*), which is exactly the caveat `SOURCE_VERIFICATION.md` §3 quantifies: **no external citations in six of seven briefs, and H7's numbers invented**.

**The seven handoffs, for completeness:** H1–H7 are the source of exactly two measured contributions already in the inventory — H2 → EXP#3/EXP#3b (candidate #1) and H6 → EXP#4 (candidate #1) — plus H7, whose lease concept is *"~90 % already `CapabilityGrant`"* (`SOURCE_VERIFICATION.md:117`) and which was answered by `D-051`. Nothing in `source-material/handoffs/` is an unreported candidate.

---

## 5. Q5 — root `docs/*.md`, `docs/evidence/`, `guidance/`: anything paper-shaped not already covered?

### 5.1 Root `docs/*.md` (38 files, 2,060,775 B) — three genuine additions, no new candidate

| File | Verdict |
|---|---|
| **`docs/EXPERIMENT_SM_PILOT.md`** (38,155 B) | **Load-bearing addition.** This is the **pre-registration** for the SM pilot whose *results* candidate **#8 (B8)** cites — `docs/research/SM_PILOT_RESULTS.md`, cited in `PAPER_CANDIDATES.md` at **`:576`** *(attribution corrected by UH3, 2026-10-15: UP2 wrote "candidate #6", but rank-6 **B6** at `PAPER_CANDIDATES.md:394–432` cites no SM file; UCORR1's own note at `PAPER_CANDIDATES.md:598–599` records the same. **The finding itself is unchanged** — only the candidate carrying it.)*. It contains something the inventory never shows: a **pre-registered VOID**, applied against the author's own positive result. `:251–263`: *"**Observed: W on family A′ = 2/12 (L5, both k). The run is therefore VOID as a DR1-B result.** The headline number (53.8 % saving …) is **not reportable as a supported claim, because the control that licenses it failed."* Root cause: the fixture's token generator cycled with period 2, so *"the answer was guessable"*. And the honesty note: *"DR4-B was written to protect a positive result, and it is precisely that rule being invoked against my own positive result. The 53.8 % figure is the one I would have wanted; it is not reportable under the pre-registration."* It also records the **first F7 detector failing to fire** on the degenerate fixture (`:289+`) — the same class as `MISTAKES.md` A4. **This is a first-class method datum and it is uncited (0 occurrences of `EXPERIMENT_SM_PILOT`).** |
| **`docs/EXPERIMENT_3MODEL_PILOT.md`** (15,034 B) | Pre-registration for candidate #11's pilot (`3MODEL_PILOT_RESULTS.md` is cited; this is not). Status at write time: *"proposed — awaiting operator approval"*. Programme document; supports the pre-registration claim, adds no result |
| **`docs/BUILD_PLAN.md`** (116,903 B) | **Load-bearing addition to candidate #9.** `:123–186` **"RUN 36 STOPPED — a reproducible death"**: *"SEVENTH consecutive refusal stop. SECOND CONSECUTIVE IDENTICAL TO RUN 35 — same fixation, same dodge, same stop at steps 16–18. Zero applied writes, zero BACKLOG edits…"* → *"this is a REPRODUCIBLE DEATH, not a random failure. Two independent runs converged on the identical behaviour."* Cause is seed-induced: `kernel/seed/goal.md:21` says *"Run the command and read it"* *"next to a worker that cannot stop running it"*; the refusal path then invites evasion (*"step 16 EMPTY bash command … the run-35 dodge, verbatim"*). Decision: **no relaunch on identical terms**; the fix belongs in the seed and refusal path, not the guard. The section also records an unverifiable authorization record rather than smoothing it (*"the watcher records an 08:12Z authorization; the Lead has no matching record"*) |
| `docs/BACKLOG.md` (86,530 B), `docs/K0_BUILD_PATH.md` (91,831 B) | Programme/status documents. `K0_BUILD_PATH.md:464` is *"External enrichment — 97 fetched URLs"* (a literature sweep whose product is already reflected in `docs/research/`); `:929` *"What this document does not claim"*. **No paper-shaped material** |
| `docs/EVALS.md` (29,652 B) | The regression layer's specification: five eval kinds (`:49`), `envSensitive` metrics and a third verdict (`:130`), the baseline (`:161`), *"What failing looks like"* (`:240`), discipline (`:292`), and §10's `prevention.detector-coverage` session-provenance fix (`:396`). **This is the mechanical half of the §6 candidate** — it is where "a check's independence" becomes a suite entry. No standalone candidate |
| `docs/DOCS_POLICY.md` (38,788 B) | The documentation transport rule: two kinds of check (`:26`), what a lane may do when it genuinely cannot (`:276`), pre-registering an experiment from a lane (`:316`), changing the gate (`:340`). **Process specification; not a paper** |
| `docs/ADAPTERS.md` (36,339 B), `docs/LAYERS.md` (30,718 B), `docs/TRACES.md` (9,503 B), `docs/CLASSES.md` (10,992 B), `docs/STATE.md`, `docs/HASHING.md`, `docs/LAYER_MODEL.md`→(research) | System specifications with acceptance tests and verification results (`LAYERS.md:143` *"THE ACCEPTANCE TEST"*, `:240` *"Verification result"* M0 → bubblewrap). **System-design material; already represented in the corpus by candidate #1's substrate and by §D** |
| `docs/DECIDER_STACK_DECISION.md` (46,577 B), `docs/DECIDER_TIER.md` (17,168 B) | Decider-stack business case and tier definition, with **three errata sections** in `DECIDER_TIER.md` (`:152`, `:187` *"the escalation finding was misattributed"*, `:207` *"§5 item 5's stated reason is not what the primary source documents"*). Substrate for candidates #5/#6; the *measured* parts are in `docs/research/TIER2_*`. Not new |
| `docs/VISIT_LOG.md` (500,596 B), `docs/LEAD_SESSION_REGISTRY.md` (51,721 B), `docs/COMPACTION_LOG.md`, `docs/STOPPED_CLOSEOUT*.md`, `docs/PAUSE_STATE.md`, `docs/BOARD.md`, `docs/SEED.md`, `docs/POLICY.md`, `docs/M0.md`, `docs/OPEN_DECISIONS.md`, `docs/README.md`, `docs/CONSONANCE_*`, `docs/MEMORY_KNOWLEDGE_ADOPTION.md`, `docs/CORDIS_ASSESSMENT.md`, `docs/DASHBOARD.md`, `docs/DOCS_SNAPSHOT_2026-10-05.md`, `docs/docs-snapshot.json`, `docs/EXPERIMENT_3MODEL_PILOT.md` | Session logs, registries, snapshots, plans, policy, vision. **Appendix material; none measures anything** |

### 5.2 `docs/evidence/` (11,000,807 B, 68 files) — evidence, not research

Three trees: `gates-2026-10-11/` (a frozen gate re-run with raw stdout/stderr per check), `selfbuild/` (CI captures per exact HEAD, 0.1–0.55 MB each, plus `APPROVAL_PACKET.v2.md.txt`), `trace-lineage-2026-10-11/` (two preserved trace tails, ~1 MB each).

**One paper-relevant item:** `docs/evidence/gates-2026-10-11/RUN.md:1–5` records that **earlier `EXIT=0` claims were withdrawn**:
> *"This run REPLACES the earlier `npm run ci` / `sandbox` / `isolation` EXIT=0 claims whose outputs went to `/tmp` and did not persist. **Those claims were WITHDRAWN**; this is their durable substitute. … Artifacts are RAW (stdout and stderr saved separately, no piping through grep/tail)."*

It also pins the frozen candidate identity (`1249bfb7…`), the exact dirty set (one path), and a byte-identical cross-check of the trace hash (`3ebadaed…`) against the preserved tail. This is **exemplary reproducibility evidence** and it belongs to the §6 candidate's "claims can be retracted and replaced by durable artifacts" thread. Everything else in the tree is raw output — appendix material.

### 5.3 `guidance/` (124,524 B, 12 files) — harness operations, not research; one load-bearing datum

| File | Verdict |
|---|---|
| `guidance/recovery/WORKSTREAM_RECOVERY_PLAN.md` (6,834 B) | **Load-bearing datum.** `:28–37` §2 is headed *"⚠️ THE PRECONDITION THAT INVALIDATES MEASUREMENTS"*: **`npm run ci`'s exit code depends on which Node is on PATH** — `node v24.21.0 → CI EXIT=0 → C1 PASS`; `node v22.23.1 → CI EXIT=1 → C1 FAIL (isolation.breadth)`. *"`engines` declares `node >= 24.0.0` but **nothing enforces or states it at the point of measurement.** … Until the runner asserts its engine or the criterion declares its environment, **'C1 green' and 'C1 red' are both true of different shells.**"* This is an **environmental** external-validity threat of a kind no candidate currently names. It also records a 14-entry decision-log divergence between the local checkout and the box at the time (`docs/DECISION_LOG.md` on the box terminated at D-102; D-116/D-117 absent), and a dirty-tree identity manifest |
| `guidance/and1-handoff/AND1_RECON_HANDOFF.md` (12,340 B) | **Out of scope as research, notable as a finding.** §0: two **measured holes** in a credential-safe boundary — six mode-600 plaintext credential files are extensionless and would be **read and indexed**, and `keyring-broker.json` is not matched by the secret-path pattern. §3 measures four memory-gap states, including **`session_id` NULL in every live row** and cross-project memory leakage. This concerns the **DSH harness** (`services/nono`, `lib/core/store.js`), not the Duval research corpus. **Not a paper candidate; a security finding the parent should route if it is not already tracked.** The document itself says *"preserve; do not act from the Duval root"* |
| `guidance/codex/` (8 files, ~96 KB: `DSH_GUIDANCE_RELAY.md`, `CONTROLS.md`, `CURRENT_STATUS.md`, `CHECKPOINT.md`, `COMPACTION_LOG.md`, `SOURCE_DOCKET.md`, `OPERATING_AGREEMENT.md`, `EXCHANGES.md`, `README.md`), `guidance/recovery/` (remainder) | Harness runbooks, control evidence, session bookkeeping. **No research material.** `DSH_GUIDANCE_RELAY.md:130` labels its own probe *"labeled, and not a research claim"* — the corpus is disciplined about this boundary |

---

## 6. Q6 — Additional candidate(s), ranked

### 6.1 `NC1` — promoted

**Working title:** *Detectors that cannot fail: a machine-checked registry of 19 verification failure classes, and what a green did not mean.*

- **Thesis.** A verification failure has one shape — *something looked fine and was not* — and it can be **classified, counted, and coverage-accounted**: 19 classes, 12 automated / 3 partial / 4 manual, with the count enforced against a detector table by an eval, so a class without a detector is a visible gap rather than a silent one. The measured instances show the mechanism failing at every level, including inside the instrument that measures the instrument.
- **Contribution type:** **method + empirical measurement**, with a system component (the registry + `evals/prevention.ts` `detector-coverage` + the inner/outer mutation harnesses).
- **Evidence base (all on disk, none needing a new run):**
  - `docs/MISTAKES.md:1–31` (the registry, the meta-pattern) · `:33–521` (19 classes in families A–E) · **`:386–417`** (the machine-enforced count and detector-status table, including the recorded blindness that let E4/E5 sit outside it) · **`:522–575`** (a writer whose verdict came from the ledger it had just written; fix = re-read and rejoin; falsifier = "every write succeeds and changes nothing") · **`:576–605`** (13 mutations, **8 survived green** at 33/33; after fixtures, 20 mutations — 17 RED, 3 named inert; one guard dormant by design leaving 41/41 green).
  - **`docs/DECISION_LOG.md:4368` (D-096)** — three *measured* defects in a green invariant wall: a structural invariant nobody asserted (`18 assertions, 0 failure(s)`, exit 0), a tautology over an object mutated **by reference** through `get()`, and a word list that missed **7 of 9** forbidden-set shapes; with the deliberate refusal to widen the word list *because a word list is itself a denylist* (rule 3, D-009), and a root-hash re-pin whose two-stage protection is demonstrated (pre-re-pin `20 assertions, 2 failures` → post-re-pin `0 failures`; `guardrails.sh` recomputing the root in an **independent** Python implementation).
  - **`docs/EVALS.md:49`** (five kinds), **`:130`** (the third verdict / `envSensitive`), **`:240`** (what failing looks like), **`:396`** (`prevention.detector-coverage` provenance).
  - **`docs/EXPERIMENT_SM_PILOT.md:251–263`** — the pre-registered VOID invoked against the author's own positive result, and `:289+` where the first F7 detector **did not fire** on the real degenerate fixture.
  - **`docs/evidence/gates-2026-10-11/RUN.md:1–5`** — withdrawn `EXIT=0` claims replaced by durable raw artifacts.
  - **`guidance/recovery/WORKSTREAM_RECOVERY_PLAN.md:28–37`** — the same commit is CI-green and CI-red depending on which Node is on PATH, with nothing asserting the engine at the point of measurement.
  - **`docs/research/experiments/LEARNINGS.md:15–341` (M1–M14)** — the companion learnings, for the cross-check in §3.3 (M11 and M12 have **no** registry class; 15 classes have no M-id).
- **Closeness:** **`1–2 weeks`** in method/short-paper form. Every datum exists and is dated; the work is framing and the cross-walk table.
- **What is missing:** (1) no external corpus — every instance is this repository's own artefact, so the paper is a **single-project** experience report until one external detector registry or one external replication is added; (2) the registry's own numbers are self-reported in Markdown with the *count* enforced but not each detector's fire-proof (A4 is manual); (3) **the M1–M14 ↔ 19-class cross-walk does not exist on disk** and must be built (M11/M12 gaps named above); (4) the "19 classes" figure is a moving target — appended sections add no new class but stale the count (`:526–528`, the A4 row still says 24 when it is 33).
- **Strongest venue class:** **software-engineering / measurement workshop or short paper** (empirical-SE or evaluation methodology), or an agent-evaluation workshop. Not a main-conference systems paper.
- **Risk:** a reviewer may read it as "we wrote tests" rather than "we measured the systematic ways tests lie". The defence is the three things no ordinary test suite has: **a machine-enforced class↔detector coverage invariant, a mutation harness whose own false result is recorded, and a pre-registered void invoked against the authors' own headline number.**
- **Rank against the existing 14:** **between #6 and #7** — the exact slot `PAPER_CANDIDATES.md` §D reserved for an M1–M14 paper, but **above that note**, because NC1 has a mechanical enforcement artefact, dated measured instances, and a red→green demonstration, where the note is a synthesis. It sits **below #1–#5** because it carries no new measurement and shares every candidate's external-validity ceiling.

**Does it change the existing candidates' caveats?** It does not touch the single-190-case-fixture caveat (no new fixture, no second labeller). It **adds one**: the same commit can be green or red depending on the shell's `node` — so *every* candidate's "all experiments exit 0" claim is **shell-scoped** in the same way C1 was (`WORKSTREAM_RECOVERY_PLAN.md:28–37`), and any reproduction section should name the Node context.

### 6.2 `NC2` — considered and **declined** (recorded so the negative result is visible)

**Sketch:** *"The append-only design record: 127 decisions, 24 errata, and a constitution that re-pins itself."* Evidence would be `docs/DECISION_LOG.md` (all of it), `D-036`/`D-057`/`D-081`/`D-097`/`D-105` (errata that correct the author's own prior entries), `D-095` §1 (two-stage protection), `D-096` §4 (a root hash moving because the code moved), `BUILD_PLAN.md:123–186` (a death recorded as a *required change*), and `docs/evidence/gates-2026-10-11/RUN.md` (claims withdrawn and replaced).

**Why declined:** it is an **experience report about a process**, with no measurement that a reviewer could falsify beyond this repository, and its strongest content is already the method thread of NC1 and `PAPER_CANDIDATES.md` §F1. Promoting it would be the inflation this unit was told to avoid. **It is folded into NC1 as supporting evidence, not listed as candidate #15.**

### 6.3 Explicit negative results (this is a real result)

- **No new *experimental* candidate exists outside `docs/research/`.** Nothing in `DECISION_LOG.md`, `MISTAKES.md`, `BUILD_PLAN.md`, `K0_BUILD_PATH.md`, `BACKLOG.md`, `DECIDER_STACK_DECISION.md`, `source-material/`, `guidance/`, `docs/evidence/`, or the root `docs/*.md` contains a first-party measurement that is not already an input to candidates #1–#14. The two additions are **method evidence (NC1)** and **load-bearing evidence for existing candidates** (below).
- **No second labeller, no external benchmark, and no independent corpus was found anywhere outside `docs/research/`.** `PAPER_CANDIDATES.md` §F2's remedy (a second independent labeller or corpus; one external benchmark) finds **no material support** in the trees this unit surveyed. The external-validity weakness stands unchanged — and NC1 adds an environmental variant of it.

---

## 7. Corrections to `PAPER_CANDIDATES.md` (each with file:line evidence)

| # | Claim in `PAPER_CANDIDATES.md` | Correction | Evidence |
|---|---|---|---|
| **1** | **A1**, `:110–114` (thesis, restated by UCORR1; the quoted original wording is preserved in the correction block at `:115–120`): *"a first-class unknown-effect state is the piece shipping agent runtimes are missing"*; and A1's risk list omits the competing measurement | Restate as *"no shipping agent runtime exposes a machine-checkable resume contract or a first-class unknown-effect state"* (that is V13/V19's own wording), and add to *what is missing*: **the resume-failure observation is already published** — so the contribution is construction + method + measurement in a different substrate, not the observation | `docs/consolidation/SOURCE_VERIFICATION.md:35` (V13, arXiv 2608.03836), `:36` (V14, arXiv 2608.29381), `:46` (V19, *"no production agent runtime"*), `:101–105` (*"the field has been measured failing at it within the last two months"*); the paper itself handles this at `docs/research/PAPER_DERIVATION.md:89–93` |
| **2** | **A1** evidence base, `:123–146`: substrate cited via D-001/D-002/D-009/D-039 only, and `DECISION_LOG.md` cited 0 times | Cite the log explicitly, and correct the foundation: **D-001 is refined by D-023** (*"The unit of propagation is the StateCommit; StateObjects are referenced content … Affirms D-001/D-002, refines the shape of D-005"*), position is derived by **D-042**, a lease is *"the narrow scope of authority"* by **D-051**, and the determinism claim has a **measured** proof in **D-058** (two states differing only in `epoch` hashed `ee2852ce…` vs `5d34ff6b…` before the fix) | `docs/DECISION_LOG.md:8` (D-001), `:28` (D-002), `:155` (D-009), `:567` (D-023), `:1216` (D-042), `:1648` (D-051), `:1993` (D-058), `:1123` (D-039) |
| **3** | **A2**, `:198–243`: the only named prior art is arXiv 2605.20173; the gap is inferred from the fixture | Add the **externally verified gap statement** that strengthens A2's novelty: a shipped product (Letta) is model-agnostic and permits mid-conversation swaps, and *"No measurement of behavioural continuity across a swap was found"* | `docs/consolidation/SOURCE_VERIFICATION.md:51` (V24) |
| **4** | **§D**, `:793–856` (quoted sentence at `:796–797`): *"Listing them is part of the inventory so the corpus is fully accounted for. **30 documents.**"*; and the §D note, now `:834–842` (superseded by UCORR1 correction 4 at `:844–856`), proposes M1–M14 as the method paper | §D accounts for **`docs/research/`**, not the corpus. Measured: there are **38 root `docs/*.md` (2,060,775 B)** of which exactly one (`docs/FINDINGS.md`) is cited; **`docs/MISTAKES.md` (40,436 B, 19 classes, a machine-enforced detector table) is cited 0 times**, as are `docs/EVALS.md`, `docs/DOCS_POLICY.md`, `docs/BUILD_PLAN.md` (116,903 B), `docs/K0_BUILD_PATH.md` (91,831 B), `docs/BACKLOG.md` (86,530 B), `docs/EXPERIMENT_SM_PILOT.md` (38,155 B) and `docs/DECIDER_STACK_DECISION.md` (46,577 B). The §D note should be promoted to **NC1 (§6)** and `MISTAKES.md` cited as its primary evidence | measured by `grep -c` per path against `strategy/PAPER_CANDIDATES.md`; `docs/MISTAKES.md:386–388` for the enforced count |
| **5** | **A1** and **#6**, `:105–194`, `:394–432` (the `#6` anchor has no counterpart any more: B6 cites no SM file — the pilot is cited in B8 at `:576`, with UCORR1's note at `:590–599`): the SM pilot is cited only through its results file | Cite the **pre-registration** and its recorded VOID: the run was declared void *against the authors' own 53.8 % headline*, because the control that licensed it failed (*"the 53.8 % figure is the one I would have wanted; it is not reportable under the pre-registration"*), and the first F7 detector **did not fire** on the real degenerate fixture | `docs/EXPERIMENT_SM_PILOT.md:251–263`, `:289+`; cited results file: `docs/research/SM_PILOT_RESULTS.md` (`PAPER_CANDIDATES.md:576`) |
| **6** | **#9** (*A self-build loop can move its own wall*), `:622–683`: evidence base is `docs/research/selfbuild/` + EXP#18/#19/#20/#22 | Add **three uncited load-bearing items**: (a) `BUILD_PLAN.md:123–186` — a **reproducible death**: seventh consecutive refusal stop, second identical to the previous run, zero applied writes, cause seed-induced (*"the seed does not distinguish 'run it and read it' from 'run it again'"*), and the decision recorded as a required change rather than a retry; (b) `DECISION_LOG.md:5685` **D-116** — *"The kernel weakened the checks that judge it, and C2's green was FALSE"*, with `:5771` **D-117** closing the judge boundary and `:6432` **D-127** defining acceptance as *"earned from a runtime-verified pinned source or not at all"*; (c) `:4553` **D-098** and `:4594` **D-099** — the readiness ledger was true and the engine did not exist; the first run produced no candidate | `docs/BUILD_PLAN.md:123`, `:180`; `docs/DECISION_LOG.md:4553`, `:4594`, `:5685`, `:5771`, `:6432` |
| **7** | Method paragraph, `:43–45`: `docs/consolidation/SOURCE_VERIFICATION.md` *"was surveyed"* | True but load-bearing in a way the inventory never carries: the ledger **narrows every candidate's novelty claim** and contains the only externally verified gap statements in the corpus. No candidate cites it. Add it to A1 and A2 as prior art and to §F as the corpus's novelty instrument | `docs/research/PAPER_DERIVATION.md:35–37`; `docs/consolidation/SOURCE_VERIFICATION.md:35–36`, `:42–43`, `:51`, `:101–105` |

**Not corrected (checked and confirmed):** A1's "nothing was promoted into `src/`" gap; A2's 244/244 zero control and 41.8 %/32.2 % figures; §F1's claim that the measurement discipline is the corpus's real asset; §F6's *"no fabricated submission state to correct"*. Nothing found outside `docs/research/` contradicts these, and D-072 independently corroborates §F1's discipline claim by recording a defect (*"No decision had ever been recorded"*) rather than a success.

---

## 8. Honest limits of this supplement

1. **Headings + targeted sections, not every line.** `DECISION_LOG.md` is 454 KB / 6,497 lines; the survey read all 127 headings, 12 entries in full, and the 4 named entries. An unreported contribution could sit inside an unread entry. The named clusters (§1.4) are the ones the headings make visible.
2. **`docs/research/` was not re-inventoried** — by instruction. Where this supplement says "uncited", it means *uncited by `PAPER_CANDIDATES.md`*, not "absent from `docs/research/`". `PAPER_DERIVATION.md` **does** cite the 2608 preprints; the inventory does not.
3. **Root-`docs/` files were surveyed by headings, not in full**, except where named (`BUILD_PLAN` §RUN 36, `EXPERIMENT_SM_PILOT` §B6/Part C, `EVALS` §10, `MISTAKES` fully, `SOURCE_VERIFICATION` fully, `WORKSTREAM_RECOVERY_PLAN` §1–3, `AND1` §0/§3, `gates-.../RUN.md`). `BACKLOG.md` (86 KB), `K0_BUILD_PATH.md` (92 KB) and `docs/VISIT_LOG.md` (500 KB) were not read line-by-line.
4. **`docs/evidence/` is 11 MB of raw output** and was censused, not read. A reproducibility claim inside one of the 29 `ci-exact-head-*.txt` captures was not re-verified.
5. **The target tree was already dirty** at survey time (8 paths, §0 read-only proof). UP2 changed nothing, but "the target is clean" is **not** a claim this unit can make.
6. **`guidance/and1-handoff/AND1_RECON_HANDOFF.md` §0 is a live-looking security finding about the DSH harness, not the Duval corpus.** It is flagged here for routing; this unit neither verified nor acted on it.
