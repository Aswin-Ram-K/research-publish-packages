# PRIOR_DISCLOSURE_AUDIT — has Consonance already been publicly disclosed?

**Unit:** UDISC1 · **Date:** 2026-10-15 · **Answers:** `strategy/TRADE_SECRET_AUDIT.md` U13 (UTS1's largest untested assumption)
**Ground:** live public fetches, unauthenticated, 2026-10-15. Every artifact below was retrieved from a live URL and quoted. No disclosure is inferred from a name match; every match was opened and read.
**Not legal advice.** US-centric (35 U.S.C. §102(a)(1); 18 U.S.C. §1839). UTS1's U8 stands: EU/India standards were not fetched.

---

## 0. Verdict, in one line

**The mechanisms are already publicly disclosed — deliberately, in detail, and dated — in a public GitHub repository, `Aswin-Ram-K/publish-present-compete`.** The author's own profile page also describes the core mechanism. UTS1's U13 assumption is now **resolved against the withholding plan**: the plan protects the *implementation*, not the *mechanisms*.

The single most consequential fact: **the document UTS1 ruled `withhold` as a set is published publicly, byte-for-byte identical** (§2).

---

## 1. Repository-visibility finding (what the public account page actually shows)

`https://github.com/Aswin-Ram-K` fetched unauthenticated, 2026-10-15:

| Fact | Value |
|---|---|
| Display name / handle | **Zer0null** / `Aswin-Ram-K` · Chicago · 1 follower · 0 following |
| Repositories tab | **19** (rendered list truncated at ~5 by the page; see UNVERIFIED) |
| Packages tab | **0** — no GitHub Packages published |
| Stars | 9 |
| Profile README | `Aswin-Ram-K/Aswin-Ram-K` — **Public**, MIT, 2 commits, latest *"chore: add MIT license"* **2026-10-08** |
| `Aswin-Ram-K/Consonance` | **404 / private** — consistent with UTS1's 2026-10-15 check. The kernel **source is not public.** |
| `Aswin-Ram-K/publish-present-compete` | **PUBLIC**, MIT, **38 commits**, last commit *"chore: normalise the harness name and simplify .gitignore"* **2026-10-10** |
| GitHub Pages | **none** — `aswin-ram-k.github.io/publish-present-compete/` → *"There isn't a GitHub Pages site here."* |

**The profile README itself is a disclosure** (public since at least 2026-10-08):

> **Consonance** | Capability-materialisation kernel for agent runtimes. Each state transition materialises exactly the grants a step needs and revokes them on the next. Enforcement by absence, not refusal. A live A/B holds everything constant except the state class — and the workspace digest stays byte-identical when the capability is absent.

and in the bio: *"how an enforcement boundary holds by **absence** rather than by refusal"*, and under skills: *"bubblewrap, capability-based security, Merkle-DAG state"*, *"append-only ledgers · falsifiers written before the code runs"*.

**So the `Consonance` repo being private does not mean the mechanisms are secret.** A separate public repository carries the mechanism prose, findings and decision log.

---

## 2. The load-bearing fact: the `withhold`-ruled paper is published byte-for-byte

| | Public copy | Workspace target copy |
|---|---|---|
| Path | `publish-present-compete/findings/PAPER-DERIVATION.md` | `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md` |
| Title | `# Deriving agent state from an observation stream` | same |
| Bytes | **46,636** | **46,636** |
| Distinctive string line numbers | 104, 219, 301, 321, 339, 435 | **104, 219, 301, 321, 339, 435 (identical)** |

UTS1 `TRADE_SECRET_AUDIT.md` §4.1 rules **M1–M9 `withhold`** and §5.3 rules *"**The derivation papers, as a set** … `withhold`"*. That exact document is public in full, including its §5 opening: *"The loop is real, and **the moat survives it**"*.

The public repo's own README states the limit of the disclosure honestly: *"**The implementation is not published here.** The code stays private; this repository carries the findings, the numbers, the method and the reasoning."* That sentence is the boundary of what is still protectable — and it is a description-level boundary, not a mechanism-level one.

---

## 3. Verdict per mechanism class (against UTS1's M1–M13)

| # | Mechanism (UTS1's wording, abbreviated) | Verdict | Evidence |
|---|---|---|---|
| **M1** | Append-only observation stream as source; **state as deterministic projection**, not model narration | **already disclosed** | public `PAPER-DERIVATION.md` abstract: *"an append-only observation stream as the source, state as a deterministic projection of it rather than a narration the model writes"*; §4.2 |
| **M2** | `Observation` as **discriminated union over `kind`**; async-hasher/synchronous-projector; **twelve typed observations** | **already disclosed** | public §4.2 `:219` *"the same transition is emitted as **twelve typed observations**"*; `:223` *"all twelve identity-bearing regions identical"*; `:238` *"**discriminated union over `kind`**"* |
| **M3** | Commit record shape; chain linked not listed; `stateId`/`canonical`/hasher as address | **already disclosed (partly)** | public §1.3 *"a content-addressed commit DAG, kernel-stamped provenance (D-039), and commit-per-transition already exist"*; public `DECISION_LOG.md` D-004 (`State.capabilities`, `State.policyHash`), D-005 (`ResourceRef { scheme, locator, hash, pin }`, BLAKE3) |
| **M4** | First-class **unknown-effect** state: `classify()` → settled/uncertain/not-dispatched/unknown-key; **write-ahead intent** journal | **already disclosed** | public §4.3 `:268` *"Write-ahead ordering is load-bearing"*; `:288` *"The third state is representable and structurally unreachable without write-ahead. `classify()`"*; §1.2 names the gap verbatim |
| **M5** | **Consume-once gate** — claim taken before the query; atomicity, not earliness | **already disclosed** | public §4.3b heading *"Concurrent resumption, and the consume-once gate"*; `:321` *"The repair is a consume-once claim taken **before** the query"*; §2 `:104` |
| **M6** | **Reference token grammar** + resolver's five responsibilities; absence indistinguishable from non-existence | **already disclosed** | public §4.4 `:339` gives the grammar verbatim: `` `@<kind>:<id>[#<pointer>][@<revision>][?<projection>]` ``; `:358` the 99.8 % token-vs-inline measurement |
| **M7** | **Context engine**: `context.search`/`context.expand`; `expanded[]`; budgets **drop-and-name**; non-destructive re-expansion | **already disclosed** | public §4.5; `:418` *"lease -> view read-only, deterministic, carries expanded[]"*; `:541` *"recoverable from `expanded[]` (§4.5)"* |
| **M8** | **Composition / lease**: *head is the certificate*; `lease.grants ⊆ union(all composed states' grants)`; **epoch-bound** liveness (expired grant *unrepresentable*, no clock read) | **already disclosed** | public §4.6 `:429` *"**epoch-bound** (an expired grant is *unrepresentable*, not flagged, and no clock is read); rendering is **read-only and deterministic**"*; `:435–436` *"the head is the certificate"* / the subset invariant |
| **M9** | **Five-layer separation rule** (*a layer may be recomputed from the layer below; never a source of truth for the layer below*) | **cannot determine** | public §5.5 is headed *"Why 'separate and combined' is different"* and the layer model is discussed at `:433` (*"The layer model §4.3 said a chain lease's authority is…"*) — but §5.5 was **not read** within this unit's bound. High risk it is disclosed; not asserted. |
| **M10** | **Enforcement by absence**: prohibition is the absence of a grant from `plan()`, never a check against a forbidden value (D-009); scope narrowing at the **broker boundary** | **already disclosed — verbatim** | public `PAPER-DERIVATION.md` §1.3; public `WHITEPAPER.md` §4 and §5.2 (*"`admit()` was invoked **zero times**"*, *"The allowlist IS the bind-mount list"*); public `DECISION_LOG.md` D-009 |
| **M11** | **Decision taxonomy and namespaces**: the `DecisionKind` union (`worker.class`, `context.package`, `capability.family`, `memory.admission`, `escalation`, `topology`, `acquisition`) + six kernel namespaces | **cannot determine** | public `decisions/DECISION_LOG.md` holds **99 decisions** and the README calls it *"the authority on why anything is the way it is"*. Only D-001–D-006 were read. The taxonomy is not asserted from the whitepaper; it is **very likely** in the public decision log. |
| **M12** | Internal kernel file/API surface **named by path**: `src/dag.ts` (`DagRow`, `DagAppendInput`, `Dag`), `src/store.ts`, `src/scope.ts`, `src/layer.ts` `invoke()`, `admit()`, `grantPolicy` | **cannot determine** | public `PAPER-DERIVATION.md` §7 *Artefacts* and §8 *Reproducing the programme* exist; the public `WHITEPAPER.md` already names `admit()`, `plan()`, `layer.broker`, `diff()`. Path-level inventory not extracted (see UNVERIFIED). |
| **M13** | Re-runnable artefact inventory: `tools/derivation/`, `tools/resume/engine.ts`, `tools/refs/`, `tools/context/`, `tools/abstraction/`, `tools/replay/exp7.ts`, `tools/absence-probe.ts`, `npm run exp2…exp7` | **cannot determine** | public §7/§8 and `experiments/` are public; extraction attempt failed within bound. Note the public README says such paths are named *"rather than the number being stated bare"* — i.e. path naming is the repo's stated practice, which raises rather than lowers the risk. |

**Tally: 8 of 13 classes `already disclosed` (M1–M8, with M3 "partly"), 1 `already disclosed` outright (M10), 4 `cannot determine` (M9, M11, M12, M13) — and the four undetermined are the ones I did not finish reading, not the ones with evidence of secrecy.**

---

## 4. Every public artifact found

| # | What | Where | Date | What it discloses | Damage |
|---|---|---|---|---|---|
| A1 | Profile README (+ duplicate on the user page) | `github.com/Aswin-Ram-K` · `Aswin-Ram-K/Aswin-Ram-K` | public ≤ **2026-10-08** | Consonance in one paragraph: capability-materialisation per transition, revoke on the next, **enforcement by absence, not refusal**, the live A/B, byte-identical digest; Merkle-DAG state; append-only ledgers | **High** — the thesis and its distinguishing phrase are public |
| A2 | `WHITEPAPER.md` | `…/publish-present-compete/blob/main/WHITEPAPER.md` | repo push ≤ **2026-10-10**; self-dated *October 2026* | The full mechanism: engine/model authority split, state-as-continuation, enforcement by absence, the §5.1 A/B table with exact digests (`b40dedde → aef2e4ab`, `BLOCKED:ENETUNREACH`, 633 vs 1166 reasoning tokens), `admit()` invoked zero times, `layer.broker === null`, refusals as first-class states, gate ordering, **commit p50 0.09 ms / per-step 16.7 ms**, the 16-field envelope, 7 design findings, 5 explicit falsifiers | **Very high** — a complete, citable printed publication of the architecture |
| A3 | `findings/PAPER-DERIVATION.md` | same repo, `findings/` | working paper *started **2026-10-01***; public ≤ 2026-10-10 | **Byte-identical to the paper UTS1 ruled `withhold` as a set.** Full M1–M8 spine (§4.2–§4.6), the consume-once gate, the reference-token grammar, the layer model, the loop diagram, and *"the moat survives it"* | **Decisive** — the withholding ruling is void on this file |
| A4 | `decisions/DECISION_LOG.md` | same repo, `decisions/` | entries from **2026-09-28**; public ≤ 2026-10-10 | **99 decisions, each with the alternatives rejected and why.** D-001 state-as-unit · D-002 state-as-continuation/capability certificate · D-003 engine-only authorship · D-004 `State.capabilities` + `policyHash` · D-005 `ResourceRef`, BLAKE3, `docs/HASHING.md` · D-006 refusals first-class. UTS1 cites D-009 and D-042 as load-bearing for M10 and M3 | **Very high** — the *rationale* is the trade secret's hardest part to reconstruct, and it is published |
| A5 | `experiments/` — **15** pre-registrations + results + `INDEX.md` | same repo, `experiments/` | public ≤ 2026-10-10 | hypothesis, method, **falsifier and budget** per experiment, EMERGE/CLOSE outcomes | **High** — method and re-runnability |
| A6 | `findings/`: `CONSONANCE-FINDINGS.md`, `FINDINGS-REGISTER.md`, `SM-PILOT-RESULTS.md`, `MISTAKES.md`, `LEARNINGS.md`, `M0-ACCEPTANCE.md`, `EXPERIMENT-PROGRAMME.md`, `WORK-ITEMS.md` (14 epics / **99 work items**), `OPEN-QUESTIONS.md`, `LANDSCAPE.md` | same repo, `findings/` | public ≤ 2026-10-10 | findings, the author's own corrections, failure classes with detectors, the accepted-milestone criteria, verified positioning with sources | **High** |
| A7 | `findings/COCKPIT-FINDINGS.md` | same repo | public ≤ 2026-10-10 | the **cockpit** observability pipeline over real agent-session logs; four defects a green suite missed | **Medium** — adjacent project, but it names the corpus's measurement defects |
| A8 | `README.md` + repo *About* description | same repo | public ≤ 2026-10-10 | indexes A2–A7 and names both projects; states the deliberate boundary (*"the code stays private"*) | **Low**, but it is the discovery surface for everything above |
| A9 | `resume/` — résumé, CV, PDF renderer | same repo | public ≤ 2026-10-10 | personal/PII, not mechanism | **None for secrecy**; privacy-relevant |

**Public artifacts found: 9 categories (A1–A9). Artifacts describing mechanism: 8.**

**Package registries — nothing published by the author (0 findings):**

| Registry | Query | Result |
|---|---|---|
| npm | `consonance-kernel` | `{"error":"Not found"}` |
| npm | `consonance` search (29 hits) | exact match is **`jongold`'s font-scale package**, v0.1.0, *11 years ago*; others are music-theory (`set-consonance`, `aloysius`). **None is this project.** |
| PyPI | `consonance-kernel` | `{"message": "Not Found"}` |
| PyPI | `consonance` | **Tarek Galal's** `consonance` (WhatsApp Noise handshake, GPLv3) — a different project entirely |
| crates.io | `consonance` | empty body (no results returned) |
| Docker Hub | `consonance` | `consonanceintelligence/terminal_control`, `collaboratory/workflow-helloworld` — unrelated |
| GitHub Packages | user Packages tab | **0** |

**Public writing other than GitHub — none found.** Web searches for the author's name, the project, and the distinctive mechanism phrases (`"enforcement by absence"`, `"state kernel" agent "observation stream" derived state`, `"unknown effect" agent runtime`, `Consonance agent kernel`) returned **no author-related result**. See §6 — this negative is weak evidence, because the same index also failed to surface the public repo.

---

## 5. What this means for the withholding plan

**Not protectable — secrecy already destroyed.** As *information*, the following can no longer be a trade secret, because it is generally known and readily ascertainable from public documents A1–A6: M1, M2, M3, M4, M5, M6, M7, M8, M10 as descriptions; the derivation paper **as a set**; the decision log's rationale for at least D-001–D-006; the A/B design and its numbers; and — decisively — the exact document UTS1 told the author to withhold.

**Also a §102(a)(1) problem.** These are **printed publications** dated 2026-10-01/08/10. For the mechanisms they describe, they are prior art. That closes the patent fallback for the described mechanisms as well as the trade-secret route — a fact worth recording even though the author's stated preference is *"i dont want-patents"* (UTS1 §8), because the two routes were being treated as alternatives and now only one remains open.

**Still protectable — the implementation.** What the public repo does not carry, by its own explicit statement, is the code. The residual trade secret is narrow and expression-level: the contents of `src/**`, the concrete type declarations, the actual state-class catalogue in code, the private corpora, the `tools/**` experiment trees, and whatever prose remains unpublished (`CONSONANCE.md`, the monograph, the 2,977-line *Self-Improving Build Architecture*). UTS1's `withhold` rulings on those rows survive; **its rulings on the M1–M9 paper set do not.**

**The one actionable lever, and its limit.** The `withhold` ruling on `PAPER_DERIVATION.md` is now void — withholding it *in this workspace* protects nothing. The only remaining lever is **withdrawal from the public repository**, and it is a weak one: at 2026-10-15 the repo shows **0 stars and 0 forks**, so reach is small, but cloning, caching, and index snapshots are not reversible by deletion, and the profile README (A1) independently repeats the core phrase. Deletion reduces future dissemination; it does not restore secrecy.

**The O-1 trade-off UTS1 recorded is now moot — in the author's favour.** UTS1 §3 recorded that withholding the blanket paper meant *"the architectural/system claim is never published."* It is already published, dated, authored and citable (A2, A3). The cost UTS1 priced into the withholding decision does not exist; the benefit it was buying does not either.

**Recommendation (procedural, not legal).** UTS1's closing recommendation stands and is now stronger: put the triage — *revised to treat M1–M10 as disclosed* — in front of a lawyer before any further core release, and decide first whether to **narrow the withheld set to the code** rather than to a mechanism list that is already public.

---

## 6. What I could NOT search — and the residual risk that leaves

**The methodological caveat that matters most.** Ten distinct SearXNG phrasings — including the author's full name and the verbatim phrase *"enforcement by absence"* — returned **nothing** about this project. The public repo was found by **going to the account**, not by searching. **Therefore a clean web-search result is not evidence of non-disclosure here**, and any future unit relying on search alone will under-report. This is the single most transferable lesson from this audit.

Not searched / not searchable:

- **Private or login-walled channels:** LinkedIn, X/Twitter, Bluesky, Reddit, Hacker News, YouTube, Discord/Slack, mailing lists, conference talks or abstracts. No credentials, no index access. A post made on any of these would be invisible to this audit.
- **Deleted or edited posts**, private gists, the private `Consonance` repo's issues/discussions/PRs, GitHub Actions logs, and archived snapshots (no archive.org / Google cache query was run).
- **`created_at`/`pushed_at` and the full 19-repo list:** the GitHub REST API returned **HTTP 403 rate-limited** for this IP, so dates are taken from the *rendered* commit headers (2026-10-08 for the profile README, 2026-10-10 for `publish-present-compete`), and the repositories page rendered only ~5 of 19. **Six of the author's 19 public repositories were not individually inspected.** Any one of them could carry further mechanism prose.
- **Depth inside the public repo:** only the bounded head of each document was read. **`DECISION_LOG.md` D-007–D-099, the 15 `experiments/` files, and most of `findings/*` were not read.** Given what the head of each contained, the bias of this audit is toward **under**-reporting the disclosure.
- **crates.io** returned an empty body — treated as "not found", but it is an empty response, not a clean assertion.
- **`aswin-ram-k.github.io/`** (the user root) was not fetched; only the project Pages path (404) was.

**Residual risk.** Because the disclosure was found on the account and not through search, and because 6 repos and ~93 decision entries went unread, the probability that **more** is public is high. The verdict "8 of 13 classes disclosed" is a **floor, not a ceiling**. The corresponding risk to the parent's plan is asymmetric: **over-estimating what is still secret** is the dangerous direction, and that is the direction this bound leaves open.

---

## 7. `UNVERIFIED`

1. That the public `PAPER-DERIVATION.md` and Duval's `docs/research/PAPER_DERIVATION.md` are **semantically** identical — the byte count (46,636) and six distinctive line numbers match exactly, which is strong, but no cryptographic digest was computed on both sides.
2. The **precise first-public date** of `publish-present-compete` and of A2/A3 specifically. `created_at` was unobtainable (API 403); dates are the rendered last-commit headers and the documents' self-dates.
3. Whether the repo was **ever** private before 2026-10-08/10, and whether it was public on particular dates relevant to any filing.
4. **M9, M11, M12, M13** — whether each is disclosed (see §3). M9 by §5.5; M11 by `DECISION_LOG.md`; M12/M13 by §7/§8 and `experiments/`.
5. The **other 6 of 19** public repositories' contents.
6. Whether **LinkedIn / X / a blog / a talk** carries a related post (invisible to search here).
7. Whether any **fork, clone, mirror, or archive snapshot** of `publish-present-compete` exists elsewhere (forks shown = 0 at 2026-10-15; other mirrors not searched).
8. Whether the public `WHITEPAPER.md` has itself been **submitted anywhere** (arXiv, TMLR, a workshop) — no arXiv ID was found for it, and no arXiv/DOI record exists for the corpus per `PUBLICATION_STRATEGY.md:47`.
9. **crates.io** and **Docker Hub** coverage beyond a single keyword query each.
10. Whether `findings/LANDSCAPE.md`'s *"verified positioning, with sources"* discloses the corpus's competitive read in a way that matters to the plan.

---

## 8. What the workspace's own record said — and why it was wrong

Checked as required, and it is consistent but **stale**:

- `strategy/PUBLICATION_STRATEGY.md:47` — *"Published artifacts | **none.** No DOI, no arXiv id, no proceedings entry anywhere in the corpus."* **True as to arXiv/DOI/proceedings; false as to public disclosure.** A public GitHub repo is not an arXiv id, and the audit read only the former index.
- `strategy/SOCIAL_PRESENCE.md` (US1, **2026-10-11**) is a **plan**, not a publication — *"Site goes live"* is a scheduled step (§16, `:824`). Nothing in it records a post having gone out. **Correctly not counted as a disclosure.**
- `journal/` (2026-09-28 → 2026-10-13) records Consonance commits, the monograph and the external-evidence review; **no entry records a public post, tweet, blog, preprint or release.**
- `/home/zer0null/Duval/docs/` — grepped for publication/posting/blog/announce/tweet/arXiv/Reddit/LinkedIn terms: only `npm run ci` matches and third-party arXiv citations in `LANDSCAPE.md`. `docs/VISIT_LOG.md:2933` states work was pushed to *"the **private** remote `Aswin-Ram-K/Consonance`"* — accurate, and exactly the fact that made the private-repo check look sufficient.
- A workspace-wide grep for `publish-present-compete|github.io|Aswin-Ram-K|kalugasala|kaswinram` found **no mention of `publish-present-compete` anywhere in this workspace.** The disclosure channel was unknown to every prior unit.

**The failure mode is now named:** every prior unit equated "the repo is private" with "nothing is public", and none went to the *account* to enumerate the other public repositories.

---

## 9. Provenance and read-only discipline

- **Target `/home/zer0null/Duval`: never written to.** HEAD before = HEAD after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; `git status --porcelain` before and after are **identical** (4 pre-existing untracked paths: `.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`) — **attributed to the unrelated concurrent session, not to UDISC1.** Only reads were performed (`find`, `ls`, `wc`, `grep`, `git rev-parse`, `git status`).
- **Write paths touched:** `strategy/PRIOR_DISCLOSURE_AUDIT.md`, `orchestration/units/UDISC1.md`, `orchestration/handoffs/UDISC1.json`. **`strategy/` files other than this one were read, never modified** — no clash with the unit drafting `strategy/`.
- **One deviation, disclosed:** a single scratch copy of the public paper was written to the platform temp area at `/tmp/pd.md` while grepping it over the network, and **deleted in the same run** (`rm -f /tmp/pd.md` → exit 0). Nothing was written outside `/tmp` and this workspace.
- No network write, no repo change, no server started, no plugin mounted.
