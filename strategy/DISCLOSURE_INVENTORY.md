# DISCLOSURE_INVENTORY — what is already public, what is still private, and what that costs

**Unit:** UDISC2 · **Written:** 2026-10-15 (UTC) · **Extends:** [`PRIOR_DISCLOSURE_AUDIT.md`](PRIOR_DISCLOSURE_AUDIT.md) (UDISC1) — does not repeat it
**Question answered:** UDISC1 left M9, M11, M12, M13 `cannot determine` and 6 of 19 public repositories unread. *"What is my IP status now?"* cannot be answered with four mechanisms and six repos open. This file closes the inventory.
**Ground:** live public fetches, unauthenticated, **2026-10-15**. Every mechanism verdict below rests on a document this unit fetched and read in full. Nothing is inferred from a name match.
**Target of record:** `/home/zer0null/Duval` at HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — read-only, never written (proven in §8).
**Not legal advice.** US-centric (35 U.S.C. §102(a)(1); 18 U.S.C. §1839), inheriting UTS1's §8 jurisdiction limit. EU/India standards were not fetched.

---

## 0. Headline

**All thirteen mechanisms are now settled as DISCLOSED. None is `cannot determine`. None is private.**

UDISC1 reported **9 of 13** disclosed and left four open. This unit settles all four — **M9, M11, M12, M13 are each disclosed in a public document this unit fetched and quoted** — so the count is **13 of 13**, and UDISC1's own warning that its figure was *"a floor, not a ceiling"* was correct.

**The implementation is confirmed still private — and that is now a verified fact rather than an inference.** UDISC1 could only infer it from the repo's own claim (*"the code stays private"*). This unit tested it against the repository's history and found that the author had already force-rewritten the repository so that **no reachable commit contains the source**: at the Consonance-era commit `06d618ca` the tree holds only `resume/ .gitignore CLAIMS.tsv LICENSE README.md SOURCES.tsv`, and `consonance/src/journal.ts` and `src/journal.ts` both return **HTTP 404** at every historical ref tested. The source is gone from the public record (§5).

**But the window is real and must be recorded.** Between **2026-10-09 04:11** (`feat: fold Consonance in as a subdirectory`) and **2026-10-10 07:51** (`refactor: this repository is findings, not code`) the public repository carried the Consonance implementation — **528 commits, 441 files, 16,704 LOC in `src/`**, licensed **AGPL-3.0** — while its README advertised it as present and published. A one-day public window that is retrospectively erased is not the same thing as never published: clones, caches and index snapshots are not recalled by a force-push (§6). This is the single largest new fact in this audit, and it cuts **against** the comfort of the mechanism finding, not with it.

---

## 1. The definitive public / private split

### PUBLIC — anyone can already read it, and (per the licence) reuse it

| # | What | Location | Date | Licence | Reuse |
|---|---|---|---|---|---|
| P1 | **`WHITEPAPER.md`** — the thesis, the measured A/B with exact digests, `admit()` invoked zero times, `layer.broker === null`, commit p50 0.09 ms, per-step 16.7 ms, seven findings, five falsifiers | `github.com/Aswin-Ram-K/publish-present-compete/blob/main/WHITEPAPER.md` | self-dated *October 2026*; public ≤ 2026-10-10 | **MIT** | commercial reuse **granted** |
| P2 | **`findings/PAPER-DERIVATION.md`** — 46,636 B, **byte-identical to the corpus's withheld `docs/research/PAPER_DERIVATION.md`**. Carries the M1–M9 spine, §5.5's five-layer rule, §7's artefact table, §8's command chain | same repo, `findings/` | *started 2026-10-01*; public ≤ 2026-10-10 | **MIT** | commercial reuse **granted** |
| P3 | **`decisions/DECISION_LOG.md`** — **99 decisions**, each with the alternatives rejected and why. Names the six kernel namespaces (D-024), the decision kinds, `admit()`, `plan()`, `src/dag.ts`, the merge-edge defect (D-043) with its reproduced test output | same repo, `decisions/` | entries from **2026-09-28**; public ≤ 2026-10-10 | **MIT** | commercial reuse **granted** |
| P4 | **`experiments/`** — 15 pre-registrations + results + `INDEX.md`; hypothesis, method, falsifier and budget per experiment | same repo | public ≤ 2026-10-10 | **MIT** | commercial reuse **granted** |
| P5 | **`findings/`** — 15 files: `CONSONANCE-FINDINGS.md`, `FINDINGS-REGISTER.md`, `SM-PILOT-RESULTS.md`, `MISTAKES.md`, `LEARNINGS.md`, `M0-ACCEPTANCE.md`, `EXPERIMENT-PROGRAMME.md`, `WORK-ITEMS.md` (14 epics / 99 work items), `OPEN-QUESTIONS.md`, `LANDSCAPE.md`, `COCKPIT-*.md`, `CLAIMS.tsv`, `SOURCES.tsv` | same repo | public ≤ 2026-10-10 | **MIT** | commercial reuse **granted** |
| P6 | **Profile README** — Consonance in one paragraph, *"Enforcement by absence, not refusal"*, the live A/B, the byte-identical digest | `github.com/Aswin-Ram-K` · `Aswin-Ram-K/Aswin-Ram-K` | public ≤ **2026-10-08** | **MIT** | commercial reuse **granted** |
| P7 | **The public repo's README at commit `06d618ca`** — *"528 commits · 441 files · 16,704 LOC in `src/` against 18,967 LOC of tests · 0 runtime dependencies"*, the layout, and an explicit licence table (`consonance/` = **AGPL-3.0**, `app/` = MIT) | `.../blob/06d618ca4caac9bb967eaa742eaef9a6371e4017/README.md` (reachable) | 2026-10-10 06:26 | **MIT** (root README) | commercial reuse **granted** |
| P8 | **Commit messages across the public history** — name `src/journal.ts`, `src/replay.ts`, `src/lease.ts`, `src/invariants.ts`, `src/policy.ts`, `src/commit.ts`, `src/observation.ts`, `src/reference.ts`, `src/constitution.ts`, `src/index.ts`, `src/adapters/stub-agent.ts`, `src/worker-sandboxed.ts`, `tools/coverage.mjs`, `tools/coverage-run.sh`, `scripts/guardrails.sh`, `scripts/docs-gate.mjs`, `constitution/invariants.json`, and reproduce kernel detail (`JOURNAL_EVENT_KINDS` a CLOSED vocabulary; `computeEventHash`, `GENESIS_PREV`, `verifyJournal`; dense strict-successor seq) | `.../commits/main.atom` | **2026-10-06 → 2026-10-10** | MIT (repo) | commercial reuse **granted** |
| P9 | **`resume/`** — résumé, CV, PDF renderer | same repo | public ≤ 2026-10-09 | MIT | personal/PII, not mechanism |
| P10 | **The publication window itself** — the Consonance source under `consonance/` at **AGPL-3.0**, 528 commits / 441 files / 16,704 LOC, folded in at `ccdab112` and removed at `b81b35e` | `github.com/Aswin-Ram-K/publish-present-compete` (history, now rewritten) | **2026-10-09 04:11 → 2026-10-10 07:51** | **AGPL-3.0** | **fetched by anyone in that window; not recalled by the rewrite** |

### PRIVATE — never published, or published only inside the one-day window and since scrubbed

| # | What | Why it is still private |
|---|---|---|
| V1 | **`src/**` — the kernel implementation.** Concrete types, the code-level state catalogue, the real `admit()`/`plan()` bodies, `src/dag.ts`, `src/store.ts`, `src/journal.ts`, `src/lease.ts`, `src/invariants.ts`, … | Not in any **reachable** commit (§5, verified by 404). Published only in the P10 window. |
| V2 | **`tools/**` — the experiment trees**: `tools/derivation/`, `tools/resume/engine.ts`, `tools/refs/`, `tools/context/`, `tools/abstraction/`, `tools/replay/exp7.ts`, `tools/absence-probe.ts` | Path **names** are public (M13); the **code** is not in reachable history. |
| V3 | **Private corpora** — the session traces, the 190-case decision fixture, `l1-head-to-head.jsonl`, the recorded-decision fine-tuning corpus | `source-material/` (2.6 MB / 52 files) deliberately omitted from the public mirror; personal spending records in one handoff |
| V4 | **Model weights** — trained encoder heads, deciders, the reflex tier | Never published (UTS1 W6) |
| V5 | **`CONSONANCE.md`** (the thesis document) and the **monograph** (*Self-Improving Build Architecture*, 2,977 lines) | Not in the public tree |
| V6 | **`LAYER_MODEL.md`** — the five-layer *specification*, incl. §4.6.1 intersection errata (UTS1 **W4**) | **Verified still private**: `raw.githubusercontent.com/…/findings/LAYER_MODEL.md` → **HTTP 404**, and `findings/`'s published listing does not contain it. §7 of the public paper links to it — **the link is dead, and the file is not public.** |
| V7 | **The private `Aswin-Ram-K/Consonance` repository** | `github.com/Aswin-Ram-K/Consonance` → **HTTP 404** (2026-10-15), re-confirming UDISC1 |
| V8 | **`source-material/`** and the private working dossier (`AGENTS.md`, `pickup.md`, `PLAN.md`, `discussion*.md`, `publish/`) | Removed before release and documented as deliberately omitted |
| V9 | **The two doc sites that named a plaintext private-key path and a session-signing secret** | Redacted across history at `0ce0441e`, *"the rule, not the location"* |

**Nothing on the mechanism axis is private.** The private column is entirely **expression-level**: code, specs-of-the-whole, corpora, weights, and one specification file.

---

## 2. Per-mechanism table M1–M13 — **definitive**

`disclosed` = a public URL this unit fetched contains a verbatim passage that settles the mechanism. Every M1–M10 row was re-read by this unit in the public `PAPER-DERIVATION.md` / `WHITEPAPER.md` / `DECISION_LOG.md`, not inherited from UDISC1.

| ID | Mechanism | Verdict | Where (URL) | Date | Licence | Verbatim evidence |
|---|---|---|---|---|---|---|
| **M1** | Append-only observation stream; state as deterministic projection | **disclosed** | `.../findings/PAPER-DERIVATION.md` (abstract) | 2026-10-01 | MIT | *"an append-only observation stream as the source, state as a deterministic projection of it rather than a narration the model writes"* |
| **M2** | `Observation` as discriminated union over `kind`; async hasher / synchronous projector; twelve typed observations | **disclosed** | same, §4.2 | 2026-10-01 | MIT | *"the same transition is emitted as **twelve typed observations**"* · *"`Observation` had to be a **discriminated union over `kind`**"* · *"The hasher is **async** — a synchronous projector typechecks only if every derived value is awaited."* |
| **M3** | Commit-record shape; chain linked not listed; `stateId`/`canonical`/hasher as address | **disclosed** | same, §4.2 + §4.6; `DECISION_LOG.md` D-042 | 2026-10-01 / 2026-09-29 | MIT | *"`transition: TransitionRef \| null` per D-042"* · *"the chain is linked, not a list"* · D-042: *"`TransitionRef = {ns, name, version, hash}` is a **content-addressed declaration**"* |
| **M4** | First-class unknown-effect state; `classify()` value set; write-ahead intent journal | **disclosed** | same, §4.3 | 2026-10-01 | MIT | *"`classify()` returns `settled` / `uncertain` / `not-dispatched` / `unknown-key`, and **an outcomes-only journal can never return `uncertain`**"* · *"Write-ahead ordering is load-bearing."* |
| **M5** | Consume-once gate taken before the query; atomicity, not earliness | **disclosed** | same, §4.3b | 2026-10-01 | MIT | *"**The repair** is a consume-once claim taken **before** the query, and **F4 identifies what makes it a gate: atomicity, not earliness.**"* |
| **M6** | Reference-token grammar; resolver's five responsibilities; absence indistinguishable from non-existence | **disclosed** | same, §4.4 | 2026-10-01 | MIT | *"The typed reference `@<kind>:<id>[#<pointer>][@<revision>][?<projection>]`, parsed into a `Reference` object and resolved by a resolver owning all five responsibilities H6 §11 names: lookup, authorization, revision selection, projection and budget."* · *"**Absence is indistinguishable from non-existence.**"* |
| **M7** | Context engine; `expanded[]`; budgets drop-and-name; non-destructive re-expansion | **disclosed** | same, §4.5 + §4.6 | 2026-10-01 | MIT | *"Non-destructive re-expansion holds."* · *"Over-budget expansions are **dropped and named**, never truncated."* · *"the view carries **`expanded[]`**"* |
| **M8** | Composition/lease: head is the certificate; grant-subset rule; epoch-bound liveness | **disclosed** | same, §4.6 | 2026-10-01 | MIT | *"liveness is **epoch-bound** (an expired grant is *unrepresentable*, not flagged, and no clock is read)"* · *"`lease.grants ⊆ union(all composed states' grants)`"* · *"the head is the certificate"* |
| **M9** | **Five-layer separation rule** + higher primitives named but not stored | **disclosed — settled by UDISC2** | same, **§5.5** | 2026-10-01 | MIT | *"The design keeps five layers apart — stream, derived state, commit, composition, projection — separated by **kind of truth** rather than by storage, under one rule: **a layer may be recomputed from the layer below it, and may never be a source of truth for the layer below it.**"* · *"That is what makes the higher primitives **named but not stored**."* |
| **M10** | Enforcement by absence; scope narrowing; broker boundary | **disclosed** | same, §1.3; `WHITEPAPER.md` §4–§5.2; `DECISION_LOG.md` D-009 | 2026-10-01 / 2026-09-28 | MIT | *"Enforcement is by **absence**: prohibition is the absence of a grant from `plan()`, never a check against a forbidden value (D-009)."* · *"**The allowlist IS the bind-mount list**"* · *"`admit()` — the policy function — was invoked **zero times**"* |
| **M11** | **Decision taxonomy and namespaces** — `DecisionKind` union + six kernel namespaces | **disclosed — settled by UDISC2** | `decisions/DECISION_LOG.md` **D-024**, D-045, D-048 | 2026-09-29 | MIT | D-024: *"**Decision.** Kernel (verified, first-class): `task`, `evidence`, `execution`, `capability`, `policy`, `decision`. Modules (behind an interface, replaceable per §21): `artifact`, `memory`, `knowledge`, `meta`, `world`, `hypothesis`."* — **exactly the six namespaces of the audit's M11**; kinds verbatim: *"(`topology` +6.8, `memory.admission` +6.2, but `acquisition` −7.7)"* · *"`escalation` is **0.933 for the 2B**"* · *"`capability.family` inverts it"* |
| **M12** | **Internal kernel file/API surface named by path** | **disclosed — settled by UDISC2** | `PAPER-DERIVATION.md` §4.1.1/§4.2; `WHITEPAPER.md` §6.1; `DECISION_LOG.md` D-042/D-043; public commit messages | 2026-10-01 → 2026-10-10 | MIT | §4.1.1: *"src/dag.ts exports: DagRow, DagAppendInput, class Dag"* · §4.2: *"`src/store.ts`'s `CommitRecord` is `{state, commitMs}`, a latency wrapper"* · §6.1: *"The new timer check flagged `src/lifecycle.ts` as unsafe"* · D-043: *"`src/dag.ts` already is, minus the maturity"* · commit `286592b`: *"tools/selfbuild/run.ts uses computeEventHash, GENESIS_PREV, JOURNAL_ENVELOPE_VERSION and verifyJournal from src/journal.ts"* |
| **M13** | **Re-runnable artefact inventory for the core** | **disclosed — settled by UDISC2** | `PAPER-DERIVATION.md` **§7 + §8** | 2026-10-01 | MIT | §7's artefact table gives `tools/absence-probe.ts`, `tools/derivation/`, `tools/resume/engine.ts`, `tools/resume/exp3b.ts`, `tools/refs/`, `tools/context/`, `tools/abstraction/`, `tools/replay/exp7.ts` with their `npm run` targets; §8 gives the whole chain: *"npm run absence-probe && npm run exp2 && npm run exp3 && npm run exp3b && npm run exp4 && npm run exp5 && npm run exp6 && npm run exp7"* |

**Tally: 13 disclosed · 0 not disclosed · 0 cannot determine.**

**Honest residue inside an otherwise-decided row.** M12's audit wording also names `src/scope.ts`, `src/layer.ts`'s `invoke()`, and `grantPolicy`. This unit did **not** locate those three strings in the public documents sampled (`WHITEPAPER.md`, `PAPER-DERIVATION.md`, `DECISION_LOG.md` D-001–D-049, the full `commits/main.atom`). M12 is nonetheless **disclosed** — the audit's primary named artefacts (`src/dag.ts` **with its three exports** and `src/store.ts` with its `CommitRecord` shape) are public verbatim, and the public commit messages name a **longer** `src/**` inventory than the audit's list. The three unlocated strings are recorded as an `UNVERIFIED` residue, not as secrecy.

---

## 3. Full public-repo inventory — `github.com/Aswin-Ram-K`

Taken from the **account's own repositories tab** (`?tab=repositories`, 19 repos, fetched 2026-10-15), not from search — UDISC1's central methodological lesson. All 19 were inspected (UDISC1 reached only 13).

| # | Repository | Vis. | Licence | Updated | Discloses mechanism? | Note / URL |
|---|---|---|---|---|---|---|
| 1 | `publish-present-compete` | Public | **MIT** | **2026-10-10** | **YES — all of M1–M13** | `github.com/Aswin-Ram-K/publish-present-compete` |
| 2 | `Aswin-Ram-K` (profile README) | Public | MIT | 2026-10-08 | **YES** — thesis, *"enforcement by absence"*, the A/B, byte-identical digest; **M1–M13 in one paragraph** | A1 in UDISC1 |
| 3 | `ai-pe-deck` | Public | MIT | 2026-10-08* | **No** — power-electronics paper deck; keyword hits are audio homonyms (*"release"*, *"envelope"*) | swept, 12 non-forks full shallow-cloned + grepped |
| 4 | `property-hunt-playground` | Public | MIT | 2026-10-08* | **No** — 95-byte README, design-system host; only *"Key Observations"* as a heading | projects Pages `/property-hunt-playground/` scanned: clean |
| 5 | `algo-trading-bot` | Public | MIT | 2026-10-08* | **No** — HMM regime trading; its *"State-Based/Markov Chain"* is a trading model, not state-as-projection | — |
| 6 | `quant-blackbox` | Public | MIT | 2026-10-08* | **No** — quant platform shell | — |
| 7 | `tape-rewind` | Public | MIT | 2026-10-08* | **No** — walk-forward backtesting | — |
| 8 | `nexus-dashboard` | Public | MIT | 2026-10-08* | **No** — Vue CDN dashboard | — |
| 9 | `yt-extract` | Public | MIT | 2026-10-08* | **No** — deterministic YouTube extraction | — |
| 10 | `splatter` | Public | MIT | 2026-10-08* | **No** (near-miss) — `AgentCapabilities` / *"meta-Herder capability"* is terminal-orchestration vocabulary, **not** capability materialisation | `SKETCH.md` |
| 11 | `agent-skills` | Public | MIT | 2026-10-08* | **cannot determine — repo is empty** (LICENSE only, 1 file, 0 B). Its advertised *"pi agent skills backup"* is unverifiable | — |
| 12 | `herder-agent-orchestration` | Public | MIT | 2026-10-08* | **No** — agent-as-orchestrator in `herdr` panes; *"The skill **is** the deployment manifest"* | no kernel vocabulary |
| 13 | `mastra-agent-system` | Public | MIT | 2026-10-08* | **No** (near-miss) — *"Command allowlist, sandbox, timeout"* and *"Only the PRIMARY agent can call any herdr pane-split…"*: an allowlist **for orchestration power**, not absence-of-grant materialisation. Its *"Observational Memory"* is Mastra's own product term, unrelated to M1 | — |
| 14 | `extensions` | Public | MIT | 2026-10-05 | No — **fork** of `OpenHands/extensions` | third-party |
| 15 | `worldmonitor` | Public | **AGPL-3.0** | 2026-09-24 | No — **fork** of `koala73/worldmonitor` | third-party |
| 16 | `release-drafter` | Public | ISC | 2026-09-23 | No — **fork** of `release-drafter/release-drafter` | third-party |
| 17 | `playwright-ctrf-json-reporter` | Public | MIT | 2026-09-23 | No — **fork** of `ctrf-io/playwright-ctrf-json-reporter` | third-party |
| 18 | `supermemory` | Public | MIT | 2026-09-23 | No — **fork** of `supermemoryai/supermemory` | third-party |
| 19 | `dduckgo-search-tools` | Public | Other | 2026-07-07 | No | — |

**Repos: 19 public · 0 private-visible · 4 forks · 15 original.** Packages tab: **0**. Stars 9. Followers 1.
**Repos disclosing mechanism: 2 of 19** — `publish-present-compete` (#1) and the profile README (#2) — the same two UDISC1 found. **All 18 non-primary repos were individually inspected** (12 non-forks full shallow-cloned and grepped: 259 text files, two keyword passes; 5 forks verified byte-identical to upstream by cross-repo compare; 1 empty). **None of the 18 carries M2, M4, M5, M6, M7, M11, M12 or M13.** The profile README reaches M10 only — verbatim, and with no code, no API surface and no file paths. Two *near-misses* use capability vocabulary but do **not** disclose the audited mechanism and are named because a reader could mistake them for disclosure: `mastra-agent-system` (*"Command allowlist, sandbox, timeout"* — an allowlist for **orchestration power**) and `splatter` (*"AgentCapabilities"* — terminal vocabulary). **A repo's existence is not disclosure; read it** — which is what was done, and the two genuinely unreadable cases (an empty repo, six 404 links) are flagged below rather than assumed clean.

**Date caveat, and it corrects an assumption this audit inherited.** All 13 non-fork repos share a `pushed_at` window of **~50 seconds on 2026-10-08**, each gaining a `LICENSE` in the same sweep. Those timestamps are a **batch metadata/licence operation, not content authorship** — they must **not** be read as the date any repo's content was written or first published. Every "2026-10-08" in the table above is marked `*` for this reason.

**Other channels, closed:**

| Channel | Result |
|---|---|
| Gists `gist.github.com/Aswin-Ram-K` | **0 public gists** — *"Aswin-Ram-K doesn't have any public gists yet."* |
| User Pages `aswin-ram-k.github.io/` | **HTTP 404** — no user site (UDISC1 had left this unchecked) |
| Project Pages `/ai-pe-deck/`, `/property-hunt-playground/` | Both **HTTP 200**, both scanned — **no mechanism vocabulary** |
| Issues / PRs on non-fork repos | **0 issues, 0 PRs** everywhere |
| Extra branch `ai-pe-deck@claude/summer-planning-internships-StHgI` (a 21 KB `PLANS.md`) | Scanned — internship planning, no mechanism |
| *"observation stream"*, *"state kernel"*, *"publish-present-compete"* across the 18 | **Absent everywhere** — verified by grep, not inferred |

**Private / not public:** `Aswin-Ram-K/Consonance` → **HTTP 404** (2026-10-15). **Side finding:** the profile README advertises **six** repositories — **[Consonance](https://github.com/Aswin-Ram-K/Consonance)**, `meta-agent`, `Valhalla`, `alfred`, `WEBSEER`, `ticket-fleet` — and **all six return HTTP 404**. The account's one public mechanism disclosure therefore names the project and its headline claims while pointing at repositories that are not public. Their contents could not be determined. `agent-skills` is **empty** (a `LICENSE` and nothing else) despite advertising a skills backup, so its claimed content is unverifiable and cannot be excluded as a vector that once existed. No published packages.

---

## 4. The licensing consequence for what is already public

### 4.1 What MIT grants — verbatim from the repository's own `LICENSE`

`raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/main/LICENSE` (fetched 2026-10-15):

> MIT License
>
> Copyright (c) 2026 **Aswin Ram Kalugasala Moorthy**
>
> Permission is hereby granted, free of charge, to any person obtaining a copy **of this software and associated documentation files (the "Software")**, to deal in the Software without restriction, including without limitation the rights **to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies** of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice **shall be included in all copies or substantial portions of the Software.**
>
> THE SOFTWARE IS PROVIDED "AS IS"…

**Four things follow, and each is load-bearing:**

1. **The grant is unconditional in scope for this repository.** There is no field-of-use limit, no non-commercial clause, no copyleft, no source-disclosure duty, no attribution beyond retaining the copyright notice. Anyone may **sell** the material, sublicense it, or incorporate it into a proprietary product.
2. **The grant expressly reaches the prose, not just code.** MIT's operative phrase is *"this software **and associated documentation files** (the "Software")"*. `WHITEPAPER.md`, `PAPER-DERIVATION.md`, `DECISION_LOG.md`, the 15 `experiments/` files and the 15 `findings/` files are **"associated documentation files" in a repository whose entire `LICENSE` is this one file** — so on the instrument's own text the documents are licensed on the same permissive terms as code. *A software licence applied to prose normally raises a construction question — whether a document is an "associated documentation file" or a separate work — and this is a reason for counsel to look at the repository as a whole rather than at the licence alone. That question is `UNVERIFIED` here (no primary source fetched on it), but the author's own commit history removes the ambiguity as a matter of intent: `f3c6ca4` reads "**make LICENSE pure MIT so GitHub detects it**" — the single MIT file was placed deliberately to govern the repository, and GitHub's detector reports the repo as **MIT**.*
3. **It is not revocable by its own terms.** The text contains **no termination clause, no revocation right, and no time limit**. Copies already distributed remain licensed. Whether that amounts to legal irrevocability is a conclusion for counsel — but there is no clause the author can pull.
4. **It binds the author's future conduct too.** Perpetual licences of this shape are understood to run with the material; relicensing *forward* (new files, new releases) is possible, un-licensing what was published is not. **This matters immediately, because the workspace's own plan points the other way:** `WITHHELD.md` §0 rule 4 and `CODE_LICENSING_STRATEGY.md` §5.1 say future releases use **PolyForm Noncommercial 1.0.0** (source-available, commercial use paid). Everything in P1–P9 above is **already **MIT**, not PolyForm. Two incompatible instruments now govern the same project's public surface, and the older, more permissive one covers the more damaging material.

### 4.2 The AGPL-3.0 layer on the implementation (P10)

The public repo's own README at `06d618ca` states, in a licence table:

> | `consonance/` | **Consonance** | … | **AGPL-3.0** |

and later *"`consonance/` is **AGPL-3.0** — see `consonance/LICENSE`"*. The release commit `0ce0441e` records the deliberate split: *"Added LICENSE (**MIT for the root and app/; consonance/ stays AGPL-3.0**)… set both package.json license fields to MIT"*. The later commit `f3c6ca4` moved the AGPL note out of `LICENSE` into a `NOTICE` file.

**So the implementation was published under AGPL-3.0, not MIT.** AGPL is strong copyleft: it grants everyone the right to run, study, modify and redistribute — and §13 obliges anyone offering the code to network users to offer the corresponding source. It is **not** a secrecy-preserving instrument. Anyone who fetched the tree during the P10 window obtained an irrevocable AGPL grant in it, and cannot be made to forget it.

**And the AGPL note is now unreachable in the current tree** — `NOTICE` and `NOTICE.md` both return **HTTP 404** at `main`, while the commit that claims to have moved the note there remains public in the atom feed. The licence statement for the implementation therefore survives only in the history and in the `06d618ca` README, not at the tip. That is a **records defect**, not a secrecy win.

### 4.3 The one-line answer to the author's question

**Every mechanism is public and reusable under MIT; the implementation was public for one day under AGPL-3.0 and has since been scrubbed from reachable history; the code, the corpora, the weights and `LAYER_MODEL.md` are the only things left that were never published.** The decision the author actually faces is no longer *"should I publish the mechanisms?"* — they are published — but **"what do I do about a repository that has already given the mechanism away commercially and whose licence I have now decided I don't want?"**

---

## 5. What is confirmed still private — and how it was verified

UDISC1 concluded the implementation survived because the public README says *"the code stays private"*. That is the author's intention, not evidence. This unit **tested** it.

| Test | Result |
|---|---|
| Historical tree listing at `06d618ca…` (a Consonance-era commit, 2026-10-10 06:26) | Contains **only** `resume/ .gitignore CLAIMS.tsv LICENSE README.md SOURCES.tsv` — **no `consonance/`, no `app/`** |
| `raw…/06d618ca…/consonance/src/journal.ts` | **HTTP 404** |
| `raw…/06d618ca…/README.md` | HTTP 200 — the ref resolves; the *path* is absent |
| `raw…/d7072672…/src/journal.ts` (pre-fold, Consonance-as-root commit) | **HTTP 404** |
| `raw…/d7072672…/consonance/src/journal.ts` | **HTTP 404** |
| `raw…/main/findings/LAYER_MODEL.md` (UTS1 **W4**) | **HTTP 404**; `findings/`'s published listing does not contain it |

**Conclusion: the implementation and the five-layer specification are not retrievable from any reachable commit of the public repository.** History was rewritten — the commit messages survive, the trees do not. `findings/LAYER_MODEL.md` is a **dead link inside a public paper**, which is the cleanest possible proof that W4 was never released while §5.5's axiom was.

**Therefore UTS1's `withhold` rulings on the expression-level rows survive** — `src/**`, `tools/**`, the corpora, the weights, `LAYER_MODEL.md`, `CONSONANCE.md`, the monograph — exactly as `WITHHELD.md` W4/W5/W6 say.

**The residual risk is the window, not the tip.** The code was in a public repository for **~27 hours** (2026-10-09 04:11 → 2026-10-10 07:51) under a licence that invited copying. At 2026-10-15 the repo shows **0 stars, 0 forks** — reach was small — but a force-push cannot recall: clones, mirror bots, archive crawls (Software Heritage crawls GitHub), and any reader's `git clone` from that day all still hold P10. **Whether P10 was actually fetched by a third party is not determinable from here** (§7). The honest statement is: *the implementation may have been obtained by an unknown party, and no action available now can establish that it was not.*

---

## 6. What remains genuinely protectable

1. **The implementation — `src/**`.** Concrete types, the code-level state catalogue, the actual bodies of `admit()`/`plan()`/`invoke()`, the resolver, the real `src/dag.ts`. Public only as **names and two shapes** (M12); never as code in reachable history.
2. **The experiment trees — `tools/**`.** Public only as a **path list** (M13).
3. **Private corpora and model weights.** Never published in any window; `source-material/` was withheld deliberately and documents its own reason (personal spending records).
4. **`LAYER_MODEL.md` (W4)** — the *specification* as distinct from the *axiom* (M9 is public; the spec is not).
5. **`CONSONANCE.md` and the monograph** — the long-form thesis documents.
6. **The two redacted secret locations** — correctly scrubbed; not a mechanism asset, but the scrub is real and should not be undone.

**Not protectable, and should stop being described as withheld:** M1–M13 as descriptions; `PAPER_DERIVATION.md` as a set; the decision log's rationale for D-001–D-006 **and now D-007–D-049 read here**; the A/B design and its numbers; the consume-once gate; the five-layer rule; the six namespaces; the artefact inventory; the 528-commit/441-file/16,704-LOC provenance figures; the D-043 merge-edge defect and its reproduced failure output.

**The correct framing of the withholding register after this audit.** `WITHHELD.md` §2 lists M1–M13 as `withhold`. Twelve of those thirteen rows now describe **already-published** information; a register that says "we are withholding M11" while `DECISION_LOG.md` D-024 prints the six namespaces verbatim is not a reasonable-measures record — it is the opposite, because it misrepresents the boundary the author is actually enforcing. The register's *expression-level* rows (W4/W5/W6, and §3's release side) remain accurate. **A register is a legal-relevant artefact; the mechanism rows should be moved to a dated "disclosed 2026-10-09/10, not by this programme" entry rather than left asserting a boundary that no longer exists.** (Procedural observation, not legal advice.)

---

## 7. What I could not determine, and what it would take

1. **Whether the P10 source was fetched by any third party during the 2026-10-09/10 window.** Not determinable from public data. Would require server-side access logs (author-only) or evidence of a clone/mirror/archive. **This is the highest-value open question and it is not answerable by more searching from here.**
2. **Software Heritage / archive snapshots of the window.** No archive.org or Software Heritage query was run; a crawl of that day's `consonance/` may exist independently of GitHub.
3. **Depth inside the 18 non-primary repos.** The sweep read every README and root document and grepped 259 text files across the 12 non-forks, but did **not** read every line — notably `splatter`'s `BUILD_PLAN.md`/`SKETCH.md` and `mastra-agent-system`'s ~4,500-line architecture document were keyword-scanned and section-read. For the 5 forks, README + full path listing + commit atom feed + cross-repo compare were verified, which is strong but not exhaustive: a single authored commit buried deep in fork history is not strictly excluded. **All 18 verdicts are `no` on the basis of having read the repo's docs and its full path listing — not on the basis of a failed search.**
4. **The six repositories linked from the profile README** (`Consonance`, `meta-agent`, `Valhalla`, `alfred`, `WEBSEER`, `ticket-fleet`) — **all 404**; private or deleted. Their contents cannot be determined, and the profile links to them as if public. **`agent-skills` is empty**, so its advertised content is unverifiable.
5. **GitHub Issues, Discussions, Actions logs and the Stars tab.** Not read. (Gists and both Pages surfaces *were* read and are clean — see §3.)
5. **Dark channels** — LinkedIn, X, Bluesky, Reddit, HN, YouTube, Discord/Slack, mailing lists, talks. No credentials, no index access. UDISC1's §6 caveat stands unchanged: *a clean web-search result is not evidence of non-disclosure here*, because the same index failed to surface the public repository.
6. **`worker.class` and `context.package`** — two `DecisionKind` members from the M11 audit wording — were **not located** in `DECISION_LOG.md` D-001–D-049. M11 is disclosed on the six namespaces plus five of seven kinds; these two strings are unconfirmed.
7. **`src/scope.ts`, `src/layer.ts` `invoke()`, `grantPolicy`** — not located in the sampled public prose (see §2 residue).
8. **The pre-rewrite commit SHAs.** GitHub may serve force-pushed "dangling" objects by direct SHA for a period; the original SHAs are not discoverable from the rewritten history, so this route could not be tested.
9. **Whether `consonance/LICENSE` actually contained AGPL-3.0** — verified from the author's README **and** the release commit message, not from the licence file itself (unreachable now: 404).
10. **The legal weight of a software licence applied to prose** — no primary source fetched (`UNVERIFIED`, §4.1 note 2).

---

## 8. `UNVERIFIED`

1. That the public `PAPER-DERIVATION.md` and Duval's `docs/research/PAPER_DERIVATION.md` are **semantically** identical — byte count (46,636) and six distinctive line numbers match (UDISC1), and this unit re-read the public copy in full; no digest was computed on both sides.
2. The **precise first-public** date/time of the repo, and of each artifact — the GitHub REST API returned **HTTP 403 rate-limited** again for this IP at 2026-10-15; all dates are rendered commit headers, the atom feed's `<updated>` values, or the documents' self-dates.
3. Whether `publish-present-compete` was ever private, and the exact boundary of the P10 window beyond the two bracketing commit timestamps.
4. **Depth inside the 18 non-primary repos** (§7.3), and the two unreadable cases: **`agent-skills` is empty** and the **six repos linked from the profile README all return 404** (§7.4). Neither is cleared — both are *not determinable*.
5. **`worker.class` / `context.package`** and **`src/scope.ts` / `src/layer.ts` `invoke()` / `grantPolicy`** — not located (§2, §7).
6. Whether any **mirror, fork, clone or archive snapshot** from the P10 window exists.
7. The **pre-rewrite object availability** on GitHub (§7.8).
8. The **legal construction of MIT over prose documents** (§4.1 note 2) — reasoned from the licence's own phrase *"and associated documentation files"* plus the author's commit intent; **not** sourced from a primary authority.
9. That `NOTICE`/`NOTICE.md` ever existed at `main` — the commit message asserts the move; the file is **404**; the assertion is unverified.
10. Coverage of `crates.io`, Docker Hub, npm/PyPI beyond UDISC1's single queries each.

---

## 9. Provenance and read-only discipline

- **Target `/home/zer0null/Duval`: never written to.** HEAD before = HEAD after = **`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`**. `git status --porcelain` before and after are **identical** (4 pre-existing untracked paths: `.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`) — **attributed to the unrelated concurrent session, not to UDISC2**; `.git/HEAD` mtime `2026-10-15 12:51:58 -0500` predates this unit's work. Only reads were performed (`git rev-parse`, `git status`, `stat`).
- **Write paths touched — exactly three:** `strategy/DISCLOSURE_INVENTORY.md`, `orchestration/units/UDISC2.md`, `orchestration/handoffs/UDISC2.json`. **No other file in `strategy/` was modified**; `PRIOR_DISCLOSURE_AUDIT.md`, `TRADE_SECRET_AUDIT.md` and `WITHHELD.md` were read, never edited. No clash with UREDACT1 / UVER5 / UVER6 / UVER7.
- **Network:** read-only fetches to `github.com`, `raw.githubusercontent.com`, `api.github.com` (403). **No network write, no repo change, no server started, no plugin mounted.** One delegated sub-auditor was used for the 18-repo sweep; it was instructed to write nothing.
- **Method inherited from UDISC1 and applied:** the account was enumerated directly (`?tab=repositories`), not discovered by search.

---

## 10. CORRECTION — 2026-10-15, unit UCLOSE1: the exposure was closed

> **This block is appended. Nothing above it is deleted or rewritten.** Where it conflicts with §0, §1, §3, §5 or §7, **this block governs.** Full evidence: [`EXPOSURE_CLOSURE.md`](EXPOSURE_CLOSURE.md).

### 10.1 What is superseded, quoted verbatim

**Superseded statement A — §0 (line 17), headline:**

> **"The implementation is confirmed still private — and that is now a verified fact rather than an inference."** … "found that the author had already force-rewritten the repository so that **no reachable commit contains the source**" … "**The source is gone from the public record (§5).**"

**Superseded statement B — §5 (line 184), conclusion:**

> **"Conclusion: the implementation and the five-layer specification are not retrievable from any reachable commit of the public repository.** History was rewritten — the commit messages survive, the trees do not."

**Superseded statement C — §5 (line 188):**

> "**The residual risk is the window, not the tip.**" … "At 2026-10-15 the repo shows **0 stars, 0 forks** — reach was small"

**Both A and B were FALSIFIED between this file's date and the closure.** Unit UARCH1 fetched the Consonance source **live, unauthenticated**, from the repository's own published events feed: `raw.githubusercontent.com/…/89003e7069c9ad79c40d91982720751b1ddf0360/consonance/src/journal.ts` → **HTTP 200, 46,450 bytes**, its `dag.ts` → 200, its `LICENSE` → 200, 34,523 B (AGPL-3.0 read from the licence text), and the whole 481-entry tree as one unauthenticated `codeload` tarball → HTTP/2 200. The pre-rewrite head SHA was published by `api.github.com/repos/…/events`. **So "gone from the public record" was wrong, and "no reachable commit contains the source" was wrong in the sense that mattered: the object was reachable by SHA and served.** See [`ARCHIVE_WINDOW_CHECK.md`](ARCHIVE_WINDOW_CHECK.md) §"Old head reachable".

**Where the "retrievable by SHA" finding lives — a location correction.** The superseding finding is in **`ARCHIVE_WINDOW_CHECK.md`** (UARCH1's own artifact, rows at its lines 81/83/86/87/88), **not** in this file. `ARCHIVE_WINDOW_CHECK.md` is **outside unit UCLOSE1's write paths and was not edited**, so **its live-exposure rows still read as current and are now stale — they need a dated correction by a unit that owns that file.** This file recorded only the weaker §7.8 note that the dangling-object route *"could not be tested"*; UARCH1 tested it, successfully. Recording the discrepancy rather than inventing a quote.

### 10.2 The correction: retrieval is closed as of 2026-10-15

Re-verified first-hand by UCLOSE1, unauthenticated `curl`, both at the short ref and at the full object id `89003e7069c9ad79c40d91982720751b1ddf0360`:

| URL | UARCH1 (~16:00) | UCLOSE1 (after closure) |
|---|---|---|
| `…/89003e70/consonance/src/journal.ts` | 200, 46,450 B | **404** |
| `…/89003e70/consonance/src/dag.ts` | 200, 44,468 B | **404** |
| `…/89003e70/consonance/LICENSE` | 200, 34,523 B (AGPL-3.0) | **404** |
| `…/main/findings/PAPER-DERIVATION.md` | 200 | **404** |
| `codeload…/tar.gz/89003e70` | HTTP/2 200, 481 entries | **404** |
| `github.com/Aswin-Ram-K/publish-present-compete` | 200 | **404** |
| `api.github.com/repos/Aswin-Ram-K/publish-present-compete` | 200 | **404** |
| **repo visibility** | PUBLIC | **PRIVATE** |
| **public repo count** | 19 (§3 and this file's header) | **18** |
| **forkCount** | 0 | **0** |

Control: `raw.githubusercontent.com/Aswin-Ram-K/ai-pe-deck/main/README.md` → **200**, so the 404s are visibility, not a broken fetcher.

**The header metadata at line 6 ("19 repos") and the §3 tally "19 public · 4 forks" are now stale on the count.** Correct figure: **18 public**, 4 of them forks.

### 10.3 The distinction the register must carry: "IMPLEMENTATION STILL PRIVATE" is true AGAIN, for a DIFFERENT reason

**Note on the phrase.** The literal string `IMPLEMENTATION STILL PRIVATE` **does not occur in this file.** The claim it names is carried at §0 (statement A) and §5's heading. Both are corrected as follows.

After the closure, **the implementation is not unauthenticated-retrievable, so the operative conclusion — the code is not public — holds.** But it holds **by visibility, not by unreachability.** The difference is not cosmetic:

- Before the closure, the code was reachable **even though the history had been rewritten**, because GitHub served the unreferenced object by SHA.
- Now, the same object is **still there and still served to the authenticated owner**: UCLOSE1 fetched it back with the owner token — `gh api repos/…/commits/89003e7069c9ad79c40d91982720751b1ddf0360` → sha `89003e7069c9ad79c40d91982720751b1ddf0360`, tree `1aadb1ef509824bd9219e6a917fdf059afcd2f03`; and `…/contents/consonance/src/journal.ts?ref=89003e70…` → `{"name":"journal.ts","size":46450}` — **the same 46,450 bytes**.

**So: the door is shut; the room is untouched.** A statement that merely restores "the implementation is still private" without saying *why* would let a reader conclude nothing happened and nothing remains to do. Three things must always be attached:

1. **Retrieval is closed.** (Proven by the 404s.)
2. **Deletion is NOT done.** The objects remain in GitHub storage and are served to the owner. **A purge request to GitHub Support, or deleting the repository, is what removes them — and the author has said he will do this himself.** UCLOSE1 changed no setting and filed nothing.
3. **Copies already taken are NOT recalled.** The window was open until today.

### 10.4 P10 and the §1/§5 "private" columns — re-triaged

- **P10 (§1, line 38)** described the publication window as *"fetched by anyone in that window; not recalled by the rewrite."* **That row remains correct and is now the load-bearing row.** The window was real, and UARCH1 proved it was still *open* — not merely historical — right up to today.
- **§1's private column** entries V1 (`src/**`) and V2 (`tools/**`) said *"Not in any **reachable** commit (§5, verified by 404)."* **Now true again** — by visibility. Their real status remains: **published under AGPL-3.0 for ~27.5 h, then withdrawn from the anonymous channel; never deleted.**
- **§6's opening claim** — *"What remains genuinely protectable: 1. The implementation — `src/**` … never as code in **reachable** history"* — **was false when written and is true again now.** It should not be read as if the audit had been right.
- **§7.8** (*"the dangling-object route … could not be tested"*) — UARCH1 tested it and it **worked**. Now closed only by visibility.
- **§4.3's one-line answer** — *"the implementation was public for one day under AGPL-3.0 and has since been scrubbed from reachable history"* — the **grant** analysis stands for copies taken in the window; the **retrieval** claim is now a visibility claim, not an unreachability claim.

### 10.5 Residual public surface — see `EXPOSURE_CLOSURE.md` §4

Recorded there as a **decision list for the author**, not a settled answer: the profile README's `bubblewrap, capability-based security, Merkle-DAG state` skills line (left alone deliberately as generic keywords); the `Consonance` profile link now pointing at a private repo (**dead link**); the profile README's ~7-day public hosting of the mechanism paragraph (removed by commit `2f8d092135039a8b6da5e1b3797833d144b60f96`, *"Profile: remove capability-kernel mechanism description"*, 2026-10-15T21:26:50Z — three strings verified present in parent `73ffa8e4b4523e37b3826777571fb2dbb35e404b` and **absent** now); and the other 17 public repos (membership re-confirmed unchanged; **contents not re-read** by this unit).

### 10.6 Discipline

UCLOSE1 wrote only `strategy/EXPOSURE_CLOSURE.md`, this appended block, `orchestration/units/UCLOSE1.md` and `orchestration/handoffs/UCLOSE1.json`. **No GitHub setting or repository was changed — `gh` and `curl` were used read-only (GET).** No `git` was run in `/home/zer0null/Duval`.
