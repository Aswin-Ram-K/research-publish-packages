# SOCIAL_PRESENCE — a platform-by-platform plan to build a credible public research presence that compounds into O-1-grade evidence

**Unit:** US1 · **Date:** 2026-10-11 · **Grounded in:** [`strategy/PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) (UP1's ranked inventory of the Duval / Consonance corpus)
**Scope of this document:** *how to be seen* by the field that the corpus's candidates are addressed to. It is not a
plan for finishing the papers — [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §E already gives that (ship #3, then
#1, build the O-1 narrative around #4). This document assumes that plan and asks the next question: **what does
the person do on Monday morning, on which platform, and what evidence does it leave behind?**

**Verification note.** SearXNG is degraded in this workspace (see [`orchestration/STATUS.md`](../orchestration/STATUS.md) §1)
and both the built-in `web_search` and DuckDuckGo/Bing/Mojeek paths returned no usable results; pages were therefore
fetched **directly by URL** from primary sources. Every load-bearing claim below carries a source id `[S#]` and a
date, or is explicitly marked `UNVERIFIED`. The direct-fetch method is itself a limitation: I could verify what I
could name, not what I would have found by searching.

---

## 0. The one thing that reframes the whole plan

Two facts, both from the primary source, change what "recognition by the field" can mean mechanically:

1. **You cannot petition for yourself.** For an O-1 petition, "O beneficiaries may not petition for themselves.
   However, a separate legal entity owned by the beneficiary, such as a corporation or limited liability company,
   may file the petition on their behalf" — and a U.S. agent may file in cases involving "workers who are
   traditionally self-employed" `[S10]` (USCIS Policy Manual 2 USCIS-PM M.3, page footer "Current as of October 02,
   2026"; the underlying policy alert adding critical-and-emerging-technology evidence examples is dated
   2025-01-08).
2. **The standard is not the criteria.** "the evidentiary requirements are not the standard for the
   classification, but are instead the mechanism for establishing whether the standard is met… the fact that the
   petitioner has produced evidence satisfying at least three evidentiary criteria does not necessarily establish
   that the beneficiary is eligible" `[S9]` (2 USCIS-PM M.4). The standard is "sustained national or international
   acclaim" and being "one of the small percentage who have arisen to the very top of the field" `[S11]`
   (2 USCIS-PM M.2).

Consequence for this strategy: **visibility is an input, never the output.** The output is a set of artefacts that
*other people* cite, reuse, review, invite, and write letters about. Any platform activity that does not end in a
citable object, a recorded invitation, or a named expert who has read the work is recreation.

---

## 1. Positioning (this drives everything)

### 1.1 The one-sentence identity

> **I research how to measure agent systems honestly — pre-registered experiments with controls that could have
> said no — and the claim I can defend in public today is that *replay reproduces the record, not the decision*:
> re-binding 3,040 already-recorded agent decisions to different models diverges in **41.8 %** of cases, against a
> **244/244** zero control in which re-issuing the identical request returned an identical decision.**

Every element is quoted from [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §A2: 41.8 % re-binding divergence, 32.2 %
relabelling, 0 % replication control, 31.6 % stable set, corpus of 4 models × 190 cases × 4 variants = 3,040
recorded outputs, and the 244/244 identical-decision control on non-decomposable cases. The control is what makes
the sentence *defensible* rather than *asserted* — it is the single most quotable asset in the corpus, because it
lets the claim survive the first question a technical reader asks ("how do you know your instrument can say zero?").

The **programme-level** identity (used on the site, in a bio, in a letter-writer's first paragraph) is the method
claim, not the system claim:

> **I research agent state and decision measurement: what a control that could have said no reveals about claims
> in agent evaluation.**

That framing is the corpus's own conclusion. [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §F.1: "The measurement
discipline is the corpus's real asset and its real novelty… **Whoever writes the papers should lead with this**."
And §A1 names the framing failure mode directly: "Framing must be: **method contribution first, system second.**"

### 1.2 The three anchor assets, and the order to release them

Chosen against §E's leverage formula — `P(accepted at a recognised venue) × (audience size / citation pool) × (how
well it demonstrates a contribution to a letter-writer)` — and against a fourth criterion this document adds:
**how quickly a stranger can check it.**

| Order | Asset | Why it leads | The one-line public claim | Audience |
|---|---|---|---|---|
| **1** | **#3 · A fine-tuned encoder head does not beat a fine-tuned 4B decider** | Fastest *decisive* result in the corpus: paired McNemar `b=27, c=90, Δ=−0.3316`, exact **p = 4.167e−09**, harm ≈ 2× the paired MDE (0.1595); both controls can report the opposite (majority-class **0.4526** > best head **0.3474**; shuffled-label 0.2316, below the 0.2911 chance floor); and the correction chain resolved **asymmetrically**: `setfit-mpnet` moved **down** (0.3158 → 0.2947 → **0.2632**), but `modernbert-base` moved **up** (**0.342105** → **0.347368**), so the defects **inflated the gap between the arms** rather than uniformly depressing the candidate — harvested as M12, narrowed to that reading. *[corrected by UCORR4, 2026-10-15: the prior wording ("every correction moved the affected arm **down**") was a false universal; `DEFECT-EVIDENCE.json` `.passes.final.arms["modernbert-base"].accuracy` = 0.347368 > `.passes.pass1_buggy_order_probe.arms["modernbert-base"].accuracy` = 0.342105. The row's ranking argument does not depend on the universal.]* It corrects a belief practitioners actually hold. | "Against a *fine-tuned* 4B decider, the small-encoder crossover disappears — the published wins compare encoders to *prompted* baselines." | Efficiency / model-selection practitioners — the largest pool of engineers who will *run* your code |
| **2** | **#2 · Replay reproduces the record, not the decision** | The identity-setting result of §1.1. Cross-checked on a second, independent corpus (51.6 % divergence, `l1-head-to-head.jsonl`, 380 rows), and M7 records that a control caught a predicate inversion that would otherwise have been published as "51 % replication divergence". The concept is prior art (arXiv 2605.20173, cited in the paper) — the contribution is **the measurement with a zero control**, which is exactly the honest framing. | "A deterministic log makes the record replayable, not the decision: 41.8 % divergence against a 244/244 zero control." | Agent-reliability / evaluation — the conversation that includes the papers the corpus already cites |
| **3** | **#1 · Deriving agent state from an observation stream** (the anchor) | The umbrella that makes the *rest of the corpus citable and legible as one body of work*. 719 lines, abstract, related work, bounds, reproduction section, and 8 experiments all exit 0 with named check counts (EXP#1 15/15, #2 16/16, #3 13/13, #3b 10/10, #4 17/17, #5 13/13, #6 19/19, #7 5/5). Method contribution and system contribution presented as co-equal. | "Agent state should be a deterministic projection of an append-only observation stream that records what was supplied, permitted, requested, executed, mutated and verified — with a first-class *unknown-effect* state." | ML-systems / agent infrastructure — smaller, but the deepest readers |

**Why #3 before #2.** §E already recommends #3 as the fastest accepted artifact; for *public presence* the argument
is stronger still. #3 is a **checkable negative result with a p-value in the single digits of e−09**, which means
the first thing a stranger does — try to break it — mostly fails. That buys the credibility that #2's percentile
argument needs. #2 is the better *identity*, but it invites "prompt sensitivity measured again" (its own stated
risk, §A2) and it is better received by a reader who already believes your instruments can say zero, which is what
#3 demonstrates.

**And #4 is deliberately not an anchor.** §E selects #4 (self-refinement degradation) as the highest-leverage O-1
paper, and it should be the flagship the ladder builds toward — but it is the one candidate that must **not** be
released early. Its pre-registered MDE was unpaired while the design is paired; the paired test gives 7/7 discordant
pairs, exact **p = 0.0156**, which **does not survive Bonferroni for four comparisons (0.0125)**. The evidence is
the pattern across two models, not any single p-value. §A4: "If the paper is written without the paired-power
correction front and centre, it is *wrong*, not merely weak." Posting #4's headline before the powered replication
would burn the corpus's strongest O-1 asset on a number a competent reader can dismantle in one reply.

### 1.3 What to stop doing — and what never to post

The failure mode this corpus is most exposed to is not obscurity. It is **flattening its own numbers**, which the
corpus itself names and penalises. §A1 calls quoting EXP#5's "83.9 % or k=29 without the ratio… the exact
flattening error the corpus elsewhere penalises" (the break-even is a function of the brief:full ratio, ~16:1
here). The same discipline must apply to anything posted publicly.

**Stop / never post:**

| Never post | Why (with the corpus's own reason) |
|---|---|
| The 22-experiment pre-registered programme, the findings register, `LEARNINGS.md` M1–M14, or the source-verification ledger **as a paper** | arXiv typically does **not** accept "Proposals for future research", "Supplemental material that is not embedded in the full article", "Workshop or conference summaries", "Posters", "Presentation slides", or "Very short work"; articles "should be complete final drafts" `[S6]`. These artefacts belong on the **personal site as an explicitly non-peer-reviewed programme record**, where they help a letter-writer and hurt nobody. |
| EXP#13's H4 claim, or EXP#16's live-cache claim | H4 is **withdrawn/VOID** after three instrument defects, all of which flattered the instrument (M13); EXP#16's live cache claim is **NOT MEASURED** (§B6). A withdrawn claim reposted socially is the single fastest way to lose a technical audience. |
| The GATED_READ end-to-end accuracy comparison at n = 20 | §B7: n = 20 per arm "cannot separate the top four arms (3 vs 2 discordant pairs — 'a coin flip')". Publishing it "would be the plausible-but-wrong number the harness was built to prevent." Publish the **batching** result instead (n = 1800/config) — it is independently publishable as a short note and is the named fallback scope. |
| The 3MODEL pilot as a security win | §C11: ASR was **0.0 % in every condition including the ungated monolith**. The null is the result; the validity work is the contribution; as a security claim it will be read as "no signal". |
| The GX10 pooled "83.7 % of calls / 90.8 % of tokens" as the headline | §B5: pooled figure "is dominated by one synthetic corpus (65 % of classified calls are gated-read probe rows); the honest headline is the per-corpus column" (~49–58 % on the two agentic corpora). |
| "Self-improving agent that moved its own wall" as a capability claim | §C9: **n = 1 cycle**, no positive control, acceptance structurally impossible today because no pinned genuine source exists (EXP#22). The measured behaviour is relabelling its own criteria. Say that. |
| The TIER2/MODEL_ESTATE vendor syntheses, the BIOMAP cross-disciplinary adoption claims, or the "graph engineering" case study as findings | §D: single-estate point-in-time audits with errata; BIOMAP's pre-seal audit **failed** the section it checked; the "graph engineering" case study is described in §D as **fabricated**. These are method-discipline inputs, not results. |
| Anything that reads as "first ever" / "state of the art" | Replay divergence is already a named phenomenon in the literature (§A2.4). The honest novelty is the **control**, and it is stronger than the superlative. |
| O-1 / visa intent on any profile | It reframes every post as an exhibit instead of a contribution. The file is assembled from the work; it is not the reason for it. |
| Public arguments with critics | The corpus's own rule: a control caught the defect (M7). Reply with the file, not the feeling. |

**The guard-rail rule, stated once and applied everywhere below:** *if it is not in the findings register with a
falsifier, it does not go on the internet.* This is the corpus's own method ledger M1–M14 compressed to one line —
"a positive result needs a control that could have said no" (§D closing note) — and it is also the cheapest possible
protection against the exact overclaiming that poisons an O-1 file.

---

## 2. Platform-by-platform plan

Nine surfaces, each with a distinct job. The order matters: **no announcement before the artefact exists.**

---

### 2.1 LinkedIn

**What it is for.** The *institutional-read* surface. It is where the people who write letters, invite speakers,
chair workshops, and (incidentally) hire are looking — and it is the surface where an unaffiliated researcher's
profile most resembles that of an employed one. It is **not** where the technical argument is won. A LinkedIn post
that does not point at a citable artefact has produced warm feelings and no evidence.

**Exact profile setup.**

- **Headline (≤220 chars, keyword-bearing, human).** The field keywords a letter-writer or programme-chair would
  search: *agent evaluation · LLM decision systems · replay determinism · self-refinement · pre-registered
  experiments*. Example shape: `Independent researcher — agent state & decision measurement | pre-registered
  experiments on replay determinism, self-refinement degradation, and decision routing | open-source (AGPL-3.0)`.
  No "Founder | Visionary | AI Enthusiast".
- **About (three short paragraphs, no adjectives without a number).** ¶1 the §1.1 identity sentence. ¶2 the two or
  three measured results *with their numbers and their controls* (41.8 % vs 244/244; 0.3474 head vs 0.4526
  majority-class vs 0.6684 decider; the never-revised control held at exactly 0.6700 across twelve measurements).
  ¶3 the method stance — pre-registration never edited after a run, controls demonstrated to report the opposite,
  errata appended and never rewritten — plus links.
- **Featured (the only real link surface).** Pin, in this order: (i) the current preprint (arXiv/Scholar link),
  (ii) the repository with its Zenodo DOI badge, (iii) the personal site's programme-record page. Four slots;
  the fourth is the current talk or workshop page when one exists.
- **Experience.** Exactly one entry: `Independent Researcher — Consonance programme (2024–present)`, organisation
  field literally `Independent`. **Never a fake or borrowed institution.** arXiv's identity policy is explicit:
  misrepresentation of identity or organisational affiliation "is possible grounds for immediate and permanent
  suspension" `[S3]`. Social norms are softer and the reputational cost is the same.
- **Contact info / custom URL / real photo / truthful location.** "Providing services: Research" on if you want
  inbound review and invitation requests — this is the one profile field that has produced O-1 criterion 4
  invitations for unaffiliated people.
- **Skills/keywords:** the six or seven terms above, in the same wording used on the site and in the CFF file.

**Recruiters and researchers read the same profile differently** — build for both, in that order of priority:

| They look at | Recruiter | Researcher / letter-writer |
|---|---|---|
| Headline + skills + location | Decides in ~3 s whether you are hireable | Skims; goes straight to Featured |
| About | Skims for seniority signals | Reads the numbers; checks whether the caveats are stated |
| Featured | Rarely opens | **This is the evaluation.** Clicks the artifact, then opens the repo |
| Experience | Employer brand matters to them | "Independent" is neutral if the artefacts are real |
| Activity | Cadence = "active" | Wants one substantial result, not volume |

**Cadence.** One substantive post per week, one substantive *comment* per day on other people's posts. Tuesday–Thursday,
morning in the audience's main timezone. Posting five times a week is the vanity trap: it forces you to post things
that are not results.

**Content format — "post the finding, not the product."** Every post is one measured claim, one number, one
figure or table image, one link. Structure that survives this audience:

1. the claim in sentence one, with the number;
2. what was measured and on what (`n`, models, fixtures) — the honest scope, in the post, not in a comment;
3. the control that could have said no, and what it returned;
4. the limit (the §A4-style caveat you would want a reviewer to raise);
5. the artifact link.

**Document/carousel posts.** LinkedIn document (PDF) posts are the right container for a *result*, not for
marketing: 6–8 pages, in the order (claim → method → control → result table → what it does not show → how to
reproduce → how to cite). Use them only when a figure or a table is the point. `UNVERIFIED`: the specific 2026
LinkedIn document-post reach mechanics could not be verified from this workspace (no citable primary source
reachable; `local_web_search` returned no results and DuckDuckGo/Bing/Mojeek were blocked or unhelpful). The
format guidance above is therefore platform-invariant content design, not an algorithmic claim.

**LinkedIn Articles / Newsletters — verdict: mirror, not venue.** Use a **Newsletter** only after the first
preprint exists, and only as a re-publication channel whose every issue links to the canonical arXiv/Zenodo object.
LinkedIn Articles have no DOI, no archival status, and no citation mechanism; a letter-writer cannot cite them as
criterion 6 authorship `[S9]`, and an adjudicator receives them as self-published. Long-form on LinkedIn is a
recruitment and reach tool; it is not a publication.

**Comment strategy.** Comment on posts by the people whose work you cite (self-refinement, agent memory, replay
determinism, evaluation methodology) with a **contribution, not praise**: the measured number, the control, and a
specific question. Do not drop links unprompted; let people ask. The objective is narrow and worth stating: to
become **the recognized name in one thread** — "the replay-divergence person" — because that is what turns into
citations, invitations, and eventually an expert letter.

**Failure mode to avoid.** Becoming a LinkedIn presence. Engagement bait, "I built an AI agent" launch posts,
motivational threads, and reposted press all generate impressions and exactly zero citable evidence; worse, they
reposition you from *researcher* to *creator* in the eyes of the one audience that matters. Second failure mode:
posting the same artifact three times in a fortnight.

---

### 2.2 X/Twitter and Bluesky

**What it is for.** The technical-audience channel, and the fastest route to the *free review that improves the
paper*. The cited literature in [`SELF_REFINEMENT_DEGRADATION_2026.md`](PAPER_CANDIDATES.md) — Huang et al. (ICLR
2024), Stechly et al., CriticBench, Valmeekam, CriticGPT — is discussed by people who are on these platforms, and
those people are the future authors of expert letters and the future citers.

**Platform choice — the honest answer.** Post to **both**, via a cross-poster, and spend effort where the *authors
you cite* actually are; measure that, don't assume it. `UNVERIFIED`: the 2026 X-vs-Bluesky researcher-migration
picture could not be verified here. No citable source was reachable (`local_web_search` no results; a Bluesky
stats tracker fetched but returned no extractable numbers `[S17]`; Bing/DuckDuckGo/Mojeek blocked or useless). The
only observed signals collected: arXiv's own 2026 blog pages place a **Bluesky** share button alongside X `[S2]`,
and ACL Rolling Review's site (fetched 2026-10) lists **Bluesky first** and X second among its contact channels
`[S13]`. That is weak evidence of professional-audience gravity and nothing more — treat the question as open and
instrument it (see below).

**Setup.** One canonical handle on both; the same canonical name string as everywhere else; bio = the §1.1 identity
sentence + a link to the **site**, not the repo (the site is where a visitor converts). Pinned post on each =
the current result thread. On Bluesky, build a starter pack / list of the field and follow it; on X, use a list for
the same purpose so the timeline is not the algorithm's.

**Instrument the question.** In a spreadsheet, for each artifact: which platform produced a reply from someone you
*cite*, which produced a question that changed the paper, which produced a citation six months later. That is the
only data that settles "which platform" — and it is exactly the data an O-1 letter can use ("her posted result was
engaged by researchers at X and Y").

**Thread format for a result (the 8-post shape).** Use it identically every time so the audience learns the format:

1. **The claim, one sentence, with the number.** ("Re-binding 3,040 recorded agent decisions to different models
   diverges 41.8 % of the time. The control re-issued the identical request and got an identical decision 244/244.")
2. **What was measured, on what.** `n`, models, fixtures, and where the data lives.
3. **The control that could have said no — and what it returned.** This is the corpus's differentiator; lead the
   thread's credibility with it.
4. **The result**, as one figure or table image.
5. **The mechanism**, in two sentences (e.g. for #4: the only admitted edit kind was `missing_option`, and nothing
   bounds its size, so 2-option questions became 8-option ones).
6. **What it does not show** — the caveat, stated *by you, first*, before anyone else can.
7. **The artefacts**: preprint DOI, code release DOI, data, reproduction command.
8. **The honest ask**: "if this is wrong, here is the file that would show it." For #2 that file is
   `decision-variants.jsonl`; for #3 the `EXP#12-evidence/` tree.

**Getting into the conversation around the cited literature.** Do it by *adding a measurement*, never by agreeing:

- **Self-refinement:** reply to discussion of Huang et al. (ICLR 2024) — the 75.8 → 38.1 collapse — with the two
  things the external review says have **no external match**: **no prior work partitions a never-revised control
  stratum** (§6) and **no study examines option counts in the 2 → 8 range** (§7, R3). Ask the specific open
  question: *does the degradation track critic quality or edit magnitude?* That question is the paper's mechanism
  claim (M10) and it is the one an expert letter can be written about.
- **Agent memory:** engage the memory-taxonomy and long-horizon work with the measured dissociation from §B8 —
  "full history solved 4/4 at every horizon through 48 steps yet collapsed to 0/4 when only filler volume grew,
  while derived projection answered 4/4 at volume L and failed only at 24 steps" — and immediately name the
  weakness (n = 4 per cell) so the thread cannot be accused of hiding it.
- **Replay determinism:** credit arXiv 2605.20173 explicitly as prior art for the *concept*, and state the
  contribution as the **measurement with a zero control**. Being the person who credits prior art accurately is
  itself a reputation.
- **Small-model / encoder efficiency:** engage the small-encoder-efficiency discussion with #3's table (majority-class
  0.4526 > best head 0.3474; decider-4b 0.6684; McNemar p = 4.167e−09) and the M12 note that the corrections
  moved the weakest arm *down* (0.3158 → 0.2947 → 0.2632) while `modernbert-base` moved *up* (0.342105 → 0.347368) —
  an **asymmetric** bias that *widened* the inter-arm gap. *[corrected by UCORR4, 2026-10-15: "all three corrections
  moved the candidate down" was a false universal over the arms.]*

**Cadence.** One thread per artifact (not per week); 3–5 substantive replies a week. Post nothing on days when
there is nothing measured to say.

**Failure mode to avoid.** Threadboi hype — 🧵 openers with no numbers, "this changes everything", ratio-bait,
and the specific disaster of running a results-thread about the 3MODEL pilot as though ASR = 0 were a security win
(§C11). A technical audience forgives a small result; it does not forgive a dressed-up null.

---

### 2.3 Google Scholar profile, ORCID, Semantic Scholar — set up *before* the first preprint

The purpose of all three is the same and it is unrecoverable if skipped: **make the citations attach to the right
identity the first time.** A preprint released before the identifiers exist produces ghost author records that must
be merged by hand later, and merges are lossy.

**ORCID — do this first (≈20 minutes, free, no affiliation required).** The ORCID iD is the join key between arXiv,
Zenodo/DataCite, OpenReview, and Scholar. It is no longer optional infrastructure in this field:

- arXiv "recommend[s] linking your ORCID to your arXiv account to connect your arXiv papers to your scholarly
  record" `[S3]`.
- ACL Rolling Review's sustainable-reviewing policy (2026-09-11) imposes "requirements for all authors to have
  completed OpenReview profiles **including ORCiD**", in effect immediately for NAACL/COLING 2026 submissions `[S13]`.

Fill the record with the (not-yet-existing) works listed as placeholders is not useful; instead add the ORCID to
every artefact's metadata from the first one, and let the record fill from the sources.

**Google Scholar profile — with one honest structural blocker.** Create it now, with a **personal** Google account
(Google recommends this explicitly so the profile can be kept for life), make it public, and add the Homepage field
pointing at the personal site `[S14]`. Then read the following carefully, because it determines what Scholar can and
cannot do for an unaffiliated researcher:

> "To be eligible for inclusion in Google Scholar search results, your profile needs to be public **and needs to
> have a verified email address at your university** (non-institutional email addresses, such as gmail.com,
> hotmail.com, aol.com, yahoo.com, qq.com, etc., are **not suitable for this purpose**)." `[S14]` (Google Scholar
> Profiles help, fetched 2026-10-11)

So: the profile and its h-index/i10/citation graph work, and a direct link to the profile works. What does **not**
work without an institutional address is Scholar's own name-search inclusion `[S14]`. This is a real disadvantage
that no amount of posting fixes, and the honest mitigations are structural, not cosmetic: a visiting or
collaborative affiliation, a journal editorship, or a co-author with an institutional address who lists you on a
paper's author metadata. Plan for it; do not pretend it away.

**Semantic Scholar.** Author pages are generated from the corpus; the practical value is that S2 feeds the "cited by"
graph and its public API, which is what many people's reading tools ingest. Make sure the canonical name and ORCID
travel in the metadata of every artefact so the automatic disambiguation lands correctly. `UNVERIFIED`: the current
S2 page-claiming and ORCID-linkage mechanics were not fetched and are stated here as general practice, not as a
verified procedure.

**Name disambiguation — the concrete rule.** One canonical rendering of the name (exact string, including or
excluding middle initials, chosen once) used identically in: arXiv author metadata; `CITATION.cff`; Zenodo author
block; ORCID; Scholar; the LaTeX `\author{}`; the site's footer; and the git author name on release tags. arXiv
states the reason: "arXiv recommends a consistent representation of your name to aid search and discovery of your
works" `[S3]`. The failure is cumulative and silent: initial-vs-full-name drift splits one career into two
half-careers with half the citations each.

**Failure mode.** (i) Creating Scholar after the first preprint. (ii) Padding the profile with non-peer-reviewed
items — the profile's value is that every entry is checkable, and a padded profile reads as noise to the one
audience that opens it. (iii) Using an institutional email that will later die, splitting the identity you were
trying to consolidate.

---

### 2.4 arXiv + a personal site

**arXiv — the discoverable, citable surface, and now a *social* gate.** The 2026 state of the endorsement system is
the single most load-bearing operational fact for an unaffiliated researcher:

- As of **2026-01-21**, "arXiv will no longer accept institutional email addresses… as the sole qualifier of
  endorsement for new authors." Endorsement now follows two paths: **both** (1) an institutional email **and**
  (2) prior authorship on a paper already accepted in that endorsement domain; **or** seeking **personal
  endorsement** from an established arXiv author in the same domain `[S2]` (arXiv blog, 2026-01-21).
- Endorsement is not peer review: an endorser "should know the person that you endorse **or** should see the paper
  that the person intends to submit", and should check the work suits the subject area `[S1]`.
- arXiv is **not** peer review and moderators cannot give feedback; works are expected to be "self-contained and of
  interest, relevance, and value"; submissions "in need of significant review and revision may also be declined";
  and "Submitters who have had works previously delayed or declined by arXiv should anticipate closer scrutiny on
  future submissions" `[S4]`.
- Rate limit: "Each author may submit up to two new submissions per calendar month with a limit of three active
  submissions" `[S4]`, per the linked 2026-10-01 rate-limit announcement `[S5]`.
- Content types: research articles are the primary content type and "should be complete final drafts"; proposals
  for future research, supplemental material not embedded in the article, posters/slides, and very short work are
  typically not accepted `[S6]`.

**The operational consequence, stated honestly.** For someone with no institutional email and no prior arXiv
authorship, **the first arXiv post is a relationship problem before it is a formatting problem** `[S2]`. The only
routes that work:

1. **Earn the read, then ask.** Put the artefact somewhere the prospective endorser can see it (site + repo +
   preprint on a mirror that does not gate), engage their work publicly with a real measurement, and *then* send a
   two-paragraph email: who you are, the specific result, the specific question, and the endorsement request with
   the code. arXiv's own guidance is to find an endorser "who you know personally and is knowledgeable in the
   subject area of your work", and to include "a link to your ORCID profile… or a copy of your intended submission"
   `[S1]`.
2. **Ask one at a time, and never en masse.** arXiv explicitly calls it "inappropriate to email large numbers of
   potential endorsers at once, or to repeatedly email the same endorser with a request for endorsement" `[S1]`.
   This is the behaviour that gets an unaffiliated researcher remembered for the wrong reason.
3. **Pick the domain by the venue, not by prestige.** The endorsement domain is a high-level subject area; choose
   the one matching the *workshop you will actually submit to*, not the one with the most status.
4. **The structural fix is co-authorship.** A named collaborator or advisor makes the endorsement, the reviewing
   qualification, and the eventual letters all easier. If any candidate can be co-authored legitimately, that is
   worth more than a month of posting.

**A personal site — why it matters *when you have no institution*.** An institution supplies five things a
researcher normally does not have to build: (1) a staff page that says you exist; (2) an email address that implies
an affiliation; (3) an archival home for non-paper artefacts; (4) a postal/correspondence address; and (5) an
implicit claim of scholarly standing. With no institution, the personal site is the *only* one of the five you
control, and it is where the corpus's non-paper 60-odd documents (§D) legitimately live.

Required pages, concretely:

- `/` — the §1.1 identity sentence, the current claim with its number, the three anchor artefacts, and a "last
  updated" date.
- `/publications` — every artifact as a row: title, venue status (*preprint* / *under review* / *accepted at X*),
  DOI, arXiv ID, code DOI, and a **"what it does not show"** column. That column is the credibility engine.
- `/programme` — the **programme record**: pre-registrations, the findings register, the M1–M14 learnings, and an
  errata page. Explicitly labelled **not peer-reviewed**, with machine-readable JSON beside the human page. This is
  the page a letter-writer reads to decide whether you are careful, and it is the page that has no arXiv equivalent
  (proposals for future research are not accepted `[S6]`).
- `/code`, `/cv`, `/contact`, `/cite`.
- Plumbing: real domain, RSS/feed, `sitemap.xml`, and a footer carrying the ORCID and the Scholar profile id.

**Failure mode.** Hosting the preprints *only* on the site and calling that publication (nothing accrues citations,
no DOI, no discoverability); a site with no dates; and letting long-form essays on the site substitute for the
papers. The site is a home, not a venue.

---

### 2.5 GitHub

**What it is for.** The code is the most *verifiable* artefact the corpus has, and criterion 5 now names software
repositories explicitly — but with a clause that decides everything:

> "Contributions to repositories of software, data, designs, protocols, or other technical resources **with evidence
> of significant scientific, scholarly, or business-related impact in the field**" `[S9]` (2 USCIS-PM M.4,
> criterion 5; evidence examples updated by the 2025-01-08 policy alert `[S10]`).

The load-bearing words are **evidence of impact**. Stars are not that evidence. The things that are: someone else's
paper using the fixture; a citation; an expert letter naming the specific contribution; reuse of the code in
another system; a downstream replication.

**README as a research landing page.** Exact structure, in order:

1. One paragraph: the §1.1 identity sentence and what the repo is.
2. **The claim this repo supports, with numbers.**
3. **The reproduction table** — one row per experiment with its check count and its command. The corpus already has
   this data and should publish it verbatim: EXP#1 15/15, EXP#2 16/16, EXP#3 13/13, EXP#3b 10/10, EXP#4 17/17,
   EXP#5 13/13, EXP#6 19/19, EXP#7 5/5, all EMERGE and all exit 0, invoked via
   `npm run absence-probe && npm run exp2 … exp7` (§A1).
4. **"What this does not show"** — the §A1 gap list, in the README: EXP#2 is a round trip (the fixture emits
   observations *from* the authored state); **nothing was promoted into `src/`** (every artefact lives in `tools/`,
   so this is a result about a *model of* the kernel); the journal is in-memory and the world simulated; characters,
   not tokens, deliberately; EXP#5's break-even depends on the brief:full ratio (~16:1), so `83.9 %` or `k=29` must
   never be quoted without it; no live model anywhere except EXP#7's recorded outputs. A reader who finds these
   themselves concludes you were hiding them; a reader who finds them in the README concludes you are careful.
5. **How to cite** (from `CITATION.cff`), the **Zenodo DOI badge**, how to contribute, and who to contact.

**`CITATION.cff` — the repo already has one.** The precise Zenodo behaviour is worth getting right `[S7]` (Zenodo
docs, fetched 2026-10-11): a `CITATION.cff` "can be added to your GitHub repository to describe the software after
it is preserved in Zenodo"; **if a `.zenodo.json` also exists, Zenodo uses only that and ignores `CITATION.cff`
entirely**; but `CITATION.cff` is still recommended "because GitHub uses it to display a citation suggestion on your
repository page". Validate it with `cffconvert` `[S7]`. So: keep the CFF as the single source of the human citation,
and do not add a `.zenodo.json` unless you actually need fields the CFF cannot express.

**Releases with DOIs via Zenodo.** Enable the repository in Zenodo (Zenodo's GitHub settings → repositories), then
**creating a GitHub release triggers the archive**: Zenodo creates a DOI-bearing record, and the record is archived
in **Software Heritage**, with archival status visible under the record page's *External resources → Archived in*
`[S8]` (Zenodo docs "Archive a release from GitHub", fetched 2026-10-11). Practical rules: one **release** per
citable artifact (not per commit); a stable tag name; the DOI quoted in the README, in the paper's artefacts
section, and in the CV; and, because GitHub's release-archive flow is per-release, treat the DOI as the thing that
converts code into a *citable object* — which is precisely what criterion 5 wants. `UNVERIFIED`: the distinction
between a "concept DOI" (all versions) and a per-version DOI is documented in Zenodo's broader help but was not
fetched here; confirm it in the UI before describing it publicly.

**Issue templates that invite collaborators.** Five, and this set is itself a research artifact:

- `reproduce-an-experiment` — asks for OS, commit, exact command, observed vs expected, and the raw output file.
- `claim-challenge` **— the important one.** "Here is a control or a check that would falsify claim X; I ran it and
  got Y." A research repo whose front door invites falsification reads differently from one that invites feature
  requests, and it is the cheapest way to convert a hostile reader into a named collaborator.
- `bug-report` — build/runtime defects.
- `data-request` — for the fixtures (`reflex-decisions.ts` 190 cases, the EXP#7 decision-variant files, the
  l1-head-to-head corpus).
- `propose-collaboration` — field, timezone, what they would run, and what they would need.

**Cadence.** Release per accepted artifact; a tagged `programme-record` release for the register/learnings; a
README refresh whenever a claim's status changes (especially when a claim is *withdrawn* — that edit is the strongest
single signal of integrity the repo can emit).

**Failure mode.** Star-chasing and README-as-product-page ("blazingly fast", feature tables, badges for coverage
that don't exist). Also: an AGPL-3.0 licence stated as a caveat rather than a fact, and version tags that don't map
to the DOIs you cite.

---

### 2.6 Hugging Face

**What it is for.** Distribution **specifically to the ML audience** — the place where models, datasets, and
Spaces have a native home, and where *Daily Papers* gives a preprint a second, ML-native front page `[S16]`
(observed: `huggingface.co/papers` is the "Daily Papers" surface, with an email digest).

**Setup.**

- One account (or org) under the canonical name; profile bio = the §1.1 identity sentence + site link.
- **Dataset cards before or with each paper.** The corpus's reusable assets are exactly what HF is for: the
  190-case fixture (`evals/fixtures/reflex-decisions.ts`) that underlies candidates #3, #4, #5 and #10; the EXP#7
  decision-variant files; `l1-head-to-head.jsonl` (380 rows). Ship them with an explicit
  **`known_limitations`** section naming the flagged decidability weak points — §F.3 notes that one fixture flaw
  currently propagates into four papers, and publishing that flaw is both honest and the fastest way to get a
  second independent labeller, which is the fix the corpus itself names (§F.2b).
- **Model cards** for anything released, each with an eval table (not a prose "state of the art" claim) and a
  `paper:` field pointing at the arXiv ID plus a `citation.bibtex` block.
- **A Space that runs the reproduction.** "Things people can run" is the currency here as much as on HN; a Space
  with a button that executes the detector suite (EXP#1's 15/15) converts a reader into a verifier in one click.

**Daily Papers.** Any arXiv paper can be submitted to the Daily Papers surface by the community, where it may appear
on the page and in the digest `[S16]`. `UNVERIFIED`: the exact 2026 submission/curation mechanics (who may submit,
and whether author submission is permitted) were not fetched — confirm before relying on it. Regardless: this is the
highest-leverage single click available to an ML preprint, because it puts the work in front of the exact audience
that cites it.

**Cadence.** One dataset/model card per released artifact, published with the paper, never later.

**Failure mode.** Uploading a model or dataset with no eval table and no limitations section — the ML audience reads
a card without numbers as a marketing page. And uploading the shared fixture *without* its known defects, which
would turn an honest corpus into a silent trap for four of its own papers.

---

### 2.7 ResearchGate / Academia.edu — honest verdict: **skip both as a primary channel**

**Verdict.** Do not invest time in either. Keep an existing profile, if any, as a **redirect stub** (identity
sentence, links out, nothing that exists only there) and stop.

**Why.** (i) They are not where the 2024–2026 agent/LLM literature is read — that is arXiv, HF, X/Bluesky, and the
workshops. (ii) Neither is a venue of record: neither produces a DOI of its own, and neither is what USCIS
criterion 3 or 6 contemplates as a professional publication or major media `[S9]`. (iii) Their historical
differentiators (full-text requests, follow-based distribution, read counts) are redundant now that preprints are
open, and the "reads" metric is one of the purest vanity metrics available — it is not citation, not reuse, and
not attestation. (iv) The cost is not zero: two more profiles to keep consistent with the canonical name and the
current claim, which is exactly the kind of drift that splits an identity.

`UNVERIFIED`: current 2026 reach, feature set, and indexing behaviour of both platforms (no citable source
reachable from this workspace). The verdict above is a judgement on their *role*, and it is stated as a judgement.

**Failure mode.** Treating ResearchGate reads or Academia.edu "top X %" emails as evidence of recognition, and
reporting them to a letter-writer. The one thing worse than no evidence is evidence that a careful reader will
discount — see §4.6.

---

### 2.8 Hacker News / Reddit (r/MachineLearning) / Lobsters

**What they are for.** One-shot distribution of a result you can defend, plus the harshest free review you will ever
receive. A single well-handled HN thread has produced more substantive expert contact for researchers than months
of LinkedIn.

**Hacker News — the norms are explicit, so follow them literally.** Show HN is "for something you've made that other
people can play with"; on-topic are "things people can run on their computers or hold in their hands"; **off-topic
for Show HN**: "blog posts, sign-up pages, newsletters, lists, and other reading material… Those can't be tried out,
so can't be Show HNs. Make a regular submission instead." The project "should be non-trivial"; you "must be
something you've worked on personally and which you're around to discuss"; make it easy to try with no signup or
email; **"Please don't ask friends to upvote or comment. That's not ok on HN."** In comments: be respectful, "ask
questions out of curiosity. Don't cross-examine" `[S12]` (Show HN Guidelines, fetched 2026-10-11).

Applied to this corpus:

- **The Show HN is the harness, not the paper.** Title shape: *"Show HN: A replay harness that reports how often an
  agent decision is reproducible"* — linking the repo plus a one-command demo. The paper itself is a **regular
  submission** with the arXiv link, because reading material cannot be a Show HN `[S12]`. Both are legitimate; they
  are simply different mechanisms.
- **First comment = the falsifier, written by you.** `n`, models, fixtures, the control, and the thing you could not
  show. This pre-empts the top reply and is the entire difference between "interesting" and "overclaiming".
- **Cadence:** at most a few submissions a year, one per genuinely distinct artifact, spaced by months. Never repost.
- **Availability:** block the day. "you're around to discuss" is a norm, and abandoning a thread is remembered.

**Reddit r/MachineLearning.** Use the research flair for the paper and the project flair for code (the subreddit
distinguishes these so self-promotion is legible). The norms that keep you unflagged: **disclose authorship in the
post body**; put the substance in the body (the numbers, the control, the limits) rather than a bare link; one post
per artifact; answer every technical question; do not cross-post the same link to five subreddits on the same day.
`UNVERIFIED`: the current r/MachineLearning rule text could not be fetched from this workspace (reddit.com returned
HTTP 403 for the rules endpoint, and the web UI redirected to login; a Redlib mirror was behind an anti-bot
challenge). The guidance above is long-standing community norm, not a verified 2026 rule quote — read the
subreddit's own sidebar before posting.

**Lobsters.** Small, high-signal, engineering-leaning; the natural home for the *harness* and for negative results
of the shape this corpus produces. Norms: link the thing, no marketing, choose accurate tags (`ai`, `testing`,
`distributed`). Volume is low, so one post per artifact suffices, and it is disproportionately likely to produce
the specific event that becomes a letter: a senior person reads it, replies, and emails you.

**The failure mode, stated as three triggers.** Being flagged as self-promotion happens when you (i) post a bare
link with no numbers, (ii) fail to disclose that it is yours, or (iii) drop the same link across communities within
days. One rule fixes all three: **put the falsifier in the first comment yourself, and say plainly that it is your
work.** And the second failure mode is arguing in the thread — the corpus's own method lesson is that a control, not
an argument, settles the question (M7).

---

### 2.9 Conferences and meetups — how an unaffiliated researcher gets in

**The honest hierarchy of doors, easiest first:**

1. **Non-archival workshops — yes, submit here, and the value is the talk slot, not the proceedings.** A workshop
   acceptance is real peer review (a letter-writer can cite it under criterion 6 `[S9]`), it does not conflict with
   a later main-venue submission because the workshop is non-archival, and it is where this corpus's candidates
   belong anyway: every one of #1–#4 names a **workshop** as its strongest venue class in `PAPER_CANDIDATES.md`.
2. **Email the organizers before the deadline.** This is the single most tractable door for someone with no
   affiliation. Workshop organizers are actively recruiting speakers and are the most accessible gatekeepers in the
   field; a one-paragraph pitch ("here is a measured negative result on X, here is the artifact, I would like to
   present it") reaches a human who is looking for exactly that. State that you want the talk slot.
3. **Registration is the threshold, not an invitation.** Many workshops and most conferences are open-registration.
   Being in the room for one year is the whole game; the invitation culture applies to *speaking*, not attending.
4. **Lightning talks and Birds-of-a-Feather sessions.** The ask is small, which is why it works. A 5-minute slot on
   a specified negative result is a real line on a record and produces real contact.
5. **Being seen asking a good question.** Underrated and true. Prepare **exactly one question per session**, tied to
   your own measured work, asked in the Q&A or the live chat: "did you control for X — because when we ran a
   never-revised stratum it held at 0.6700 across twelve measurements." Then introduce yourself to the speaker
   afterwards in one sentence and hand over a link (a QR code on your phone, or just the site). That is how a
   nameless researcher becomes "the person who asked about the control" — and that phrase, in a letter two years
   later, is O-1 evidence.
6. **Volunteer service.** Workshop reviewing, proceedings help, session chairing, community-organising. Lower
   status, same room, and it produces *service* evidence that maps to criterion 4 `[S9]`.

**Cadence.** One workshop submission per quarter; one conference or meetup per quarter in person where feasible;
one review commitment per cycle once qualified (see §4.3).

**Failure mode.** Paying to attend and speaking to nobody; leaving with a badge and no contact; treating the
conference as networking rather than as the place where your paper's weaknesses are found. The second failure is
the expensive one: a workshop's value is the reviewer who tells you what is wrong with the fixture.

---

## 3. The compounding ladder — a realistic 12-month cadence

**The design rule, and it is the only rule that matters here: every public artifact must produce at least one
citable object** — a DOI, an arXiv ID, a peer-reviewed acceptance, or a recorded invitation/review. Attention that
produces none of those is vanity; attention that arrives *before* the citable object exists is wasted, because it
cannot be converted. So the ladder is **artifact first, announcement second, always.**

| Month | Publish / do | Amplify with | Converts into (the O-1 object) |
|---|---|---|---|
| **1** | **Identity + substrate. Announce nothing.** ORCID iD; Google Scholar profile (knowing the institutional-email limitation `[S14]`); arXiv account registered; personal site v1 with `/programme` (the register + M1–M14 + errata); README rewritten as the research landing page with the reproduction table **and** the "what this does not show" list; `CITATION.cff` audited and validated; **Zenodo GitHub integration enabled**; canonical name string fixed everywhere; five issue templates added; tag a `programme-record` release. Begin the §2.4 *social* work: identify 6–10 prospective endorsers among the authors you cite. | Nothing public yet except the site and repo, which are findable but unannounced. | An identity that citations can attach to; a repo that a stranger can verify; the endorsement groundwork that arXiv now requires `[S2]`. |
| **2** | **Anchor 1 — #3 (encoder crossover).** Assemble `EXP#12-evidence/` (26 files) into a short paper; **declare the primary baseline before submission** (0.6789 same-run vs 0.6684 historical — §A3's own missing item 4); state the fixture-bound caveat and the F6 latency caveat plainly. Post the CFF-versioned release to **Zenodo → DOI**. | 8-post thread (§2.2 shape); LinkedIn document post (6–8 pages, claim→method→control→result→limits→reproduce→cite); HF Daily Papers submission; a **regular** HN submission. | arXiv ID (once endorsed) + **Zenodo DOI** + a workshop submission → an accepted workshop paper. |
| **3** | **Anchor 2 — #2 (replay divergence).** Frame as the measurement *with the zero control*; lead the abstract with the 244/244 control and the compounding argument; credit arXiv 2605.20173 as prior art. Second GitHub release + DOI. | Thread; LinkedIn; r/MachineLearning research post (disclose authorship; numbers in the body); a **Show HN for the replay harness itself** (`npm run exp7`-style one-command demo) — the *harness*, not the paper `[S12]`. | Second arXiv ID; second DOI; a workshop talk slot; the first **independent citation** (this is the one that matters — §F.2's whole point). |
| **6** | **Anchor 3 — #1 (derivation), method-first.** By now a reader has seen #3 and #2, so the umbrella is legible and its related work is partly your own. List the §6 gaps explicitly (EXP#2 round trip, nothing in `src/`, in-memory journal, characters not tokens, ratio-dependent break-even, no live model); if EXP#2b can be run, run it and close gap 1. Publish the **shared fixture** as an HF dataset with its known limitations, inviting a second labeller. **Start the #4 power work now** (third model family, more rounds, pre-registered paired MDE, held-out corpus not authored by the same worker). | Conference attendance (in person); lightning talk; one newsletter issue repeating the month-2/3 results with canonical links. | Two or three arXiv IDs; a fixture in use by others; **first review commitment** (§4.3); first invited talk. |
| **12** | **Flagship — #4 (self-refinement degradation), powered.** This is the O-1 paper: the **never-revised control stratum held at exactly 0.6700 across twelve measurements** (F-EXP11-02) and the two **"no external match found"** results — no prior work partitions a never-revised control stratum, and none examines option counts in the 2 → 8 range. Also ship a **journal version** of #2 or #6 (the latter only if EXP#16's live-cache arm gets measured), plus the second wave (#13/#14 survey form, #5 scoped to the local estate). | A talk where the flagship is presented; targeted press outreach (§4.1); workshop organising. | Journal submission; **expert attestation letters** written by people who have cited or engaged; press with substantial discussion; a **peer-group consultation** for the petition. |

**Conversion mechanics — how attention becomes an artefact O-1 cares about.** For each amplification step, the
conversion is mechanical and should be scheduled, not hoped for:

- after each thread/post → log who replied, whether they are citable authors, and whether the exchange produced a
  change to the paper or a citation (this log is the raw material for "recognition in the field");
- after each release → update the DOI-bearing record, so the citation accrues to a stable object;
- after each workshop → ask the reviewers, in writing, whether they would be willing to review a future submission
  (this is how criterion 4 service begins for the unaffiliated — see §4.3);
- after each expert engagement → a year later, ask for the letter. **Ask after the citation, never before**; a
  letter from someone who has read and cited the work is strong, a letter from a stranger who was flattered is not.

---

## 4. Turning visibility into O-1 evidence

Mapped onto the actual criteria in 2 USCIS-PM M.4 `[S9]`, with the honest yield of each. **Reminder from §0:**
satisfying three criteria is not the standard; the officer then weighs "the totality of all the evidence" against
"sustained national or international acclaim" and "one of the small percentage who have arisen to the very top of
the field" `[S11]`.

### 4.1 Press / media coverage of the work (criterion 3) — *high-yield, and obtainable from a negative result*

The criterion is narrower than people assume: it requires "published material in professional or major trade
publications or major media **about the beneficiary**, relating to the beneficiary's work", and "Published material
that includes only a brief citation or passing reference to the beneficiary's work is **not** 'about' the
beneficiary". The material may cover a broader topic, provided it "includes a substantial discussion of the
beneficiary's work in the field and mentions the beneficiary in connection with the work" `[S9]`.

**How to legitimately attract it.** Note that none of this is "getting press"; it is making the work quotable.

1. **Write the sentence a journalist can lift.** One line, one number, one stated limit. The corpus has several:
   *"a never-revised control stratum held at exactly 0.6700 across twelve measurements while both revised models got
   worse"*; *"41.8 % of recorded agent decisions changed when the same request was re-bound to a different model,
   against a 244/244 identical-decision control"*; *"a majority-class baseline (0.4526) beat every fine-tuned
   encoder head (best 0.3474)"*. Keep a `/press` page with these, a plain-language summary, one image, and a
   contact address.
2. **Pitch after the artefact, to technical trade press first.** One targeted, personalised email per outlet, never
   a blast, and never before the preprint exists — a journalist cannot cover what has no URL. The corpus's subject
   matter (agent reliability, replay determinism, self-refinement failing) is squarely within what technical trade
   outlets cover.
3. **Be available, and hand them the caveat.** A 20-minute call in which you volunteer "this is one fixture and
   `n` = 2 models here" produces an accurate piece; withholding it produces either an inaccurate piece or no piece.
4. **Do not count HN/Reddit/X as press.** Those are forums. They can *lead* to press, and a journalist often finds
   the work there — but a front page is not criterion 3 evidence.

**Yield: high.** A single substantial trade-press piece that discusses the work by name is one of the few
visibility outputs that is directly criterion-shaped.

### 4.2 Invitations to speak, judge, or review (criteria 4 and, partly, 3) — *the highest-yield axis for the unaffiliated*

USCIS's own examples for criterion 4 are: "Reviewer of abstracts or papers submitted for presentation at scholarly
conferences", "Peer reviewer for scholarly publications", "Member of doctoral dissertation committees", "Peer
reviewer for government research funding programs" `[S9]`. Every one of those is reachable without an institution —
and it is the criterion where an unaffiliated researcher has the *least* structural disadvantage, because the work
is judged, not the employer. Two operational points:

- **Invitation alone is not enough.** "The petitioner must show that the beneficiary has not only been invited to
  judge the work of others, but also that the beneficiary actually participated" — the example is the journal's
  request *plus* evidence the review was completed `[S9]`. **Keep the emails.** A CV line "reviewed 3 papers" with
  no invitation record is worth nothing.
- **Talks and judging are the same machine.** An invited workshop talk (criterion 3/6 adjacency) and a review
  invitation (criterion 4) both come from the same pool of people: workshop organisers, program chairs, and journal
  editors, all of whom you meet by *submitting* and by *being in the room* (§2.9).

**Yield: high.** This is the axis to optimise for, and it is downstream of submitting papers, not posting.

### 4.3 Peer-review service for an unaffiliated researcher — *reachable, but genuinely gated in 2026*

**The honest difficulty, with a number.** In ML/NLP, reviewing is now rationed by publication record. ACL Rolling
Review's sustainable-reviewing policy (2026-09-11) reports that **38 % of ~17,000 May 2026 submissions came from
authors with no available publication record**, and from October 2026 each ARR submission must "pay for itself" by
providing a **qualified service contributor** (reviewer or chair), with unqualified submissions going into a
lottery; per-author quotas are 20 submissions and 5 first-author per cycle `[S13]`. Qualification criteria are
publication-based — which is a **circular dependency**: you cannot review without a publication record, and the
record is what you were trying to build. ARR does name the escape hatches: reviewer qualification criteria "are
being broadened (already implemented in Aug 2026)", with "a manual application path for those with equivalent
experience, a mentor-matching program for newcomers, and a certification path" `[S13]`.

**The concrete routes, in order of tractability:**

1. **Workshop program committees.** Workshop PCs are typically recruited openly by email/form and are usually less
   publication-gated than main-track reviewing. Volunteer-review for one; a workshop review is explicitly within
   USCIS's criterion-4 examples ("reviewer of abstracts or papers submitted for presentation at scholarly
   conferences" `[S9]`).
2. **ARR's manual application path** once there is even one accepted paper `[S13]`. Apply early — the policy says
   "close-to-deadline requests for manual verification may not get processed on time".
3. **Journal reviewer databases.** Many publishers let you register reviewer interests and expertise. Register under
   the canonical name with the ORCID; the invitation follows the first relevant publication.
4. **Government funding panels / dissertation committees.** Further out, but real: an agency panel is one of
   USCIS's own examples `[S9]`, and it is sometimes reachable for practitioners without academic posts.
5. **Keep the ORCID record's peer-review section current** — ORCID's peer-review workflow exists precisely so that
   review service is a portable, third-party-verifiable record rather than a self-claim `[S15]`.

**Yield: high once the first paper lands; zero before it.** And the honest sequencing point: this is the one
criterion where the *visibility plan does nothing at all*. Reviews come from submitting, not from posting.

### 4.4 Citations and independent expert attestation (criterion 5) — *the core of the file*

Criterion 5 is "original scientific, scholarly, or business-related contributions of major significance in the
field", and USCIS tells you exactly what it weighs: "published research that has provoked widespread commentary on
its importance from others working in the field, and documentation that it has been **highly cited** relative to
other works in that field"; "Testimonials, letters, and affidavits about the beneficiary's original work and its
significance"; and, since the 2025-01-08 update, "Contributions to repositories of software, data, designs,
protocols, or other technical resources **with evidence of significant… impact in the field**" `[S9][S10]`. It also
warns that publication or funding alone "will not necessarily establish, on its own, that the work is of major
significance", and that letters "should specifically describe the beneficiary's contribution and its significance
to the field and should also set forth the basis of the writer's knowledge and expertise" `[S9]`.

**What follows for this corpus.** The strongest available raw material is not the system — it is the *specific,
nameable novelty* that §E identifies: **no prior work partitions a never-revised control stratum** and **no study
examines option counts in the 2 → 8 range** (§A4, "no external match" findings). A letter-writer can say
concretely *what is new*: "her design has a control the published literature lacks, and it isolates a mechanism
(unbounded edit magnitude) that the literature attributes only to critic quality." That is a criterion-5 sentence.
"Built a system" is not.

"Independent" is doing real work in this criterion: citations from people who do not know you are the only ones
that count. §F.2 names the fix — run one external benchmark (τ-bench, Terminal-Bench/harbor, SWE-bench are already
enumerated with feasibility verdicts in the corpus) and get a second independent labeller for the 190-case fixture.
**An external validation is worth more to this file than any amount of reach.**

**Yield: the highest of all — and it is the one visibility cannot fake.**

### 4.5 Membership in associations requiring outstanding achievement (criterion 2) — *a trap; do not build here*

USCIS's example is illuminating and discouraging: association membership qualifies only where the association
"requires that members have outstanding achievements in the field as judged by recognized experts", giving "IEEE at
the IEEE fellow level" and "membership as a fellow in the Association for the Advancement of Artificial
Intelligence (AAAI)" as possible examples — and it explicitly excludes membership based "solely on a level of
education or years of experience", "on the payment of a fee or by subscribing to an association's publications",
or "on a requirement, compulsory or otherwise, for employment" `[S9]`.

Conclusion: paid membership in ACM/AAAI/ACL is **not** qualifying, fellow-level is not reachable in a year, and
visibility has essentially no effect on this criterion. Keep memberships for their actual benefits (conference
rates, community) and do not count them.

**Yield: near-zero in this timeframe. Stated so it is not mistaken for a plan.**

### 4.6 The structural gaps, named plainly

- **Criterion 7 (critical or essential role for an organisation of distinguished reputation):** the biggest gap. An
  unaffiliated researcher has no distinguished employer, and departmental prestige is one of the factors officers
  weigh `[S9]`. USCIS does soften it — "The organisation need not have directly employed the beneficiary", and
  detailed letters from people with personal knowledge are "particularly helpful" `[S9]` — so the realistic routes
  are: a founder/contributor-of-IP role in a startup with a distinguished reputation; a genuine research position
  (even part-time, visiting, or collaborative); or a documented critical role in an open-source project of
  distinguished reputation. Note also that the manual treats founder/co-founder roles and funding as reputation
  factors. This is a *structuring* problem, not a posting problem.
- **Criterion 8 (high salary):** not addressable by visibility at all. Name it and move on.
- **The petitioner problem (§0):** you cannot self-petition; you need a U.S. employer, a U.S. agent, or "a separate
  legal entity owned by the beneficiary, such as a corporation or limited liability company" `[S10]`. The visibility
  plan is therefore necessary and not sufficient: it must be paired with a bona fide offer of work and an entity or
  agent that can file.
- **The peer-group consultation:** an O-1A petition also requires a consultation (an advisory opinion) from an
  appropriate peer group — a labor organisation, or a "peer group" of practitioners in the field. This is where
  visibility has a genuine, non-cosmetic role: it is what makes a peer group willing to write. Aim the network
  deliberately at the bodies that can (a professional association, a workshop's organising committee, an editorial
  board).

### 4.7 High-yield vs vanity — the ledger

| Tier | Activity | Why |
|---|---|---|
| **Strong** | Peer-reviewed workshop/journal acceptance | The only thing that makes criteria 4 and 6 real; everything else is a path to it |
| **Strong** | **Independent** citations (people who are not you) | Criterion 5's own words: "highly cited relative to other works in that field" `[S9]` |
| **Strong** | Expert attestation letters from people who have read/cited the artifact | Criterion 5; USCIS asks them to state the basis of the writer's knowledge `[S9]` |
| **Strong** | Press with **substantial discussion**, not a passing reference | Criterion 3, in USCIS's own distinction `[S9]` |
| **Strong** | Invited talks; judging/review with **invitation + completion record** | Criteria 4 and 3/6; the record is mandatory, not optional `[S9]` |
| **Strong** | A peer-group consultation for the petition | Structurally required `[S10]` |
| **Strong** | Fixture/dataset/code actually reused by others, with evidence of impact | Criterion 5's software clause names impact as the requirement `[S9]` |
| **Medium** | arXiv preprint | The substrate for citations — but arXiv itself says moderation is not peer review `[S4]`, so it is the *weakest* form of criterion 6 |
| **Medium** | A conference talk slot; a workshop organising role; HF Daily Papers appearance | Real, human-scale recognition; converts to the strong tier when it produces a paper or a letter |
| **Vanity** | Follower counts, LinkedIn impressions, GitHub stars, HN front page, Reddit upvotes, "top voice" badges, blog readership, ResearchGate reads, site visitor counts | None is criterion-shaped. None is "impact in the field" in the sense criterion 5 requires `[S9]` |

**And the warning specific to this file:** a large following with zero independent citations is **actively
negative**. It invites the adjudicator to ask why nobody cites the work, and the record supplies the answer.

---

## 5. A 30-day starter checklist (concrete, ordered, doable this month)

**Days 1–3 — identity layer (no posting).**
1. Create the ORCID iD; make it public; add the canonical name and the site URL. `[S3][S15]`
2. Fix the **canonical name string** once, in writing, and record it in a file (`docs/IDENTITY.md` in the repo and
   the site's `humans.txt`). Use it in every subsequent step.
3. Create the Google Scholar profile with a **personal** Google account; note in writing that search inclusion needs
   a verified institutional email and that this is currently unavailable. `[S14]`
4. Register the arXiv account (choose the endorsement domain by the *target workshop*, not by prestige). Identify
   6–10 prospective endorsers from among the authors the corpus already cites. `[S1][S2]`
5. Personal site v1: `/`, `/publications` (with the "what it does not show" column), `/programme`, `/code`, `/cv`,
   `/contact`, `/cite`, `/press`. Real domain; feed; footer with ORCID + Scholar id.

**Days 4–7 — artefact layer (still no posting).**
6. Audit and validate `CITATION.cff` with `cffconvert`; confirm no `.zenodo.json` is shadowing it. `[S7]`
7. Enable the repository in Zenodo's GitHub integration. `[S8]`
8. Rewrite the README as the research landing page: identity sentence → claim with numbers → reproduction table
   (EXP#1 15/15 … EXP#7 5/5, with commands) → **"what this does not show"** → cite → DOI badge → contribute. (§A1)
9. Add the five issue templates (§2.5), `claim-challenge` first.
10. Tag the `programme-record` release; confirm the DOI appears and the Software Heritage archival status shows. `[S8]`

**Days 8–14 — finish anchor 1 (#3).**
11. Assemble `EXP#12-evidence/` (26 files) into the short paper. Write the limitations section from §A3's four named
    gaps, including F6 latency and the fixture-bound risk.
12. **Declare the primary baseline before submission** (0.6789 same-run vs 0.6684 historical) — §A3's own item 4.
13. Internal adversarial pass: for every number in the abstract, name the control that could have said no and what
    it returned. If a number has no control, remove the number.
14. Create the release; take the DOI; update the README, the site's `/publications`, and the CV.

**Days 15–21 — first public move, in this order.**
15. LinkedIn profile completed to §2.1 (headline, About with numbers, Featured in order, one Experience entry as
    `Independent`). No post yet.
16. Site goes live; `/publications` lists #3 as *preprint (not yet endorsed)* or *under review* — whichever is true.
17. Send the endorsement request(s) — one person, personalised, with the artifact and the ORCID link. Wait; do not
    chase twice. `[S1]`
18. Submit #3 to the target non-archival workshop, and email the organizers a one-paragraph pitch asking for the
    talk slot.

**Days 22–30 — amplify, once.**
19. Post the 8-post thread (§2.2 shape), with the caveat stated by you in post 6.
20. Post the LinkedIn document post (6–8 pages, claim→method→control→result→limits→reproduce→cite).
21. Submit the artifact to HF Daily Papers; publish the evidence tree as an HF dataset with a
    `known_limitations` section. `[S16]`
22. Prepare (do not yet send) the HN **regular submission** for the paper and the **Show HN** for the replay
    harness — the harness, not the paper `[S12]`. Send them once the endorsement lands and the arXiv ID exists, so
    the links are durable.
23. Start the engagement log (platform → who replied → citable author? → changed the paper? → citation?). This is
    the file that later says "recognised in the field", and it cannot be reconstructed after the fact.

**Do not, in the first 30 days:** post the corpus to arXiv (proposals for future research and supplemental material
are typically declined `[S6]`); release #4; post anything from §1.3's table; create ResearchGate/Academia.edu
profiles; buy a domain and then leave the site undated.

---

## 6. Honesty section

### 6.1 What this strategy will not fix

1. **The arXiv endorsement gate.** Visibility does not produce an endorser. Only a person who has read the work
   does, and as of 2026-01-21 an institutional email alone is no longer sufficient for a new submitter `[S2]`.
   This is the first hard wall and the plan routes *around* it (publish on the site first, earn the read, ask one
   person) rather than removing it.
2. **Google Scholar's institutional-email requirement.** A public profile is not enough for inclusion in Scholar
   search results; a verified university address is required and non-institutional addresses are "not suitable" `[S14]`.
   This is a structural disadvantage that no posting behaviour touches. Only an affiliation, a collaboration, or an
   editorial role changes it.
3. **Criteria 7 and 8.** No distinguished employer, no salary story. Visibility cannot manufacture either. These
   are structuring and career problems, and the honest position is that the O-1 file will lean on criteria 3, 4, 5
   and 6, and must be built to survive without 7 and 8.
4. **The petitioner problem.** You cannot self-petition; an entity or agent must file `[S10]`. The plan produces
   evidence, not a petitioner.
5. **The reviewing circularity.** ARR qualification is publication-based, and 38 % of ~17K May 2026 submissions
   came from authors with no publication record `[S13]`. Only a first accepted paper breaks the circle; the manual
   application path and mentorship programme are escape hatches, not a fix.
6. **The corpus's own external-validity gaps.** §F.2: "Every strong candidate's weakness is external validity."
   One 190-case fixture underlies candidates #3, #4, #5 and #10, so one fixture flaw propagates into four papers
   (§F.3); the end-to-end arms have `n` = 20 or 4 runs per cell (§F.4); no external benchmark has been run;
   candidates #8–#12 need new experiments before they are papers at all. **No amount of posting turns a 4-run cell
   into a 20-run cell**, and the corpus's most quotable number (0/4 vs 4/4 at volume L, §B8) currently reads as an
   anecdote for exactly that reason.
7. **Time.** This is a 12-month ladder, and O-1 adjudication is a separate queue behind it. There is no 90-day
   version of this that produces a defensible file.

### 6.2 The risk of optimising for visibility over substance

The mechanism is specific and worth naming. Once posting is a habit, the cheapest content to produce is the content
that has *not* been validated — the interesting half-result, the number without its ratio, the arm that has not been
controlled. This corpus's entire competitive advantage is that it does not do that: pre-registration never edited
after a run, controls demonstrated to report the opposite, errata appended and never rewritten, a recorded run kept
after a missed budget with the overrun named, an author's own summary corrected from archived journals with the
falsification left visible (§F.1). **Posting on a cadence is structurally in tension with that discipline**, because
a cadence demands output and the discipline demands that most output not be published.

The two guards:

- **The content rule:** *if it is not in the findings register with a falsifier, it does not go on the internet.*
- **The cadence rule:** the cadence is **per artifact, not per week.** A month with no post and a finished control
  is a good month. The platform cadences in §2 are ceilings, not quotas.

A second, subtler risk: the *topic* drifts toward what travels. "Self refinement makes agents worse" travels;
"cache-safe graded progressive disclosure costs nothing in prefix bytes and buys 27.8 % at equal sufficiency" does
not — but the second is a real result and the first is currently underpowered. The ladder in §3 deliberately
publishes the *checkable* results (#3, #2) before the *persuasive* one (#4), so that the persuasive one lands with
instruments already known to be able to say zero.

### 6.3 How a technical audience punishes overclaiming — the specific mechanisms

1. **It opens the file and finds the withdrawn arm.** EXP#13's H4 is withdrawn/VOID after three instrument defects
   (§B6); EXP#16's live cache claim is "NOT MEASURED" and F3 is unmeasured-not-passed. Repost either as a claim and
   the reply is a one-line quote of the corpus's own text.
2. **It quotes the scope clause back at you.** §A1: "single-machine, single-project, nothing in `src/`, no external
   system run, no live model" is the programme's own scope, and if the work is read as a *systems claim* rather than
   a pre-registered methodology, "it collapses". §B5: the pooled 83.7 % is dominated by one synthetic corpus. §A1:
   quoting 83.9 % or `k=29` without the ~16:1 brief:full ratio is the flattening error the corpus itself penalises.
3. **It finds the missing control in one line.** §B7: `n` = 20 per arm cannot separate the top four arms ("a coin
   flip"). §B8: 0/4 vs 4/4 rests on 4 runs per arm. §C11: ASR = 0 in the ungated control too, so the security
   experiment measured the fixture. §C9: `n` = 1 cycle, no positive control, and the loop is not deployed anywhere.
4. **It reads the adjective and asks for the antecedent.** "Self-improving" → *where is the positive control?*
   "State of the art" → *against what?* "Robust" → *to what?* Every one of these has a document in the corpus that
   already answers honestly, and the answer is always narrower than the adjective.
5. **The discount is categorical, not proportional.** One inflated claim does not reduce the audience's estimate of
   the work by 10 %; it reclassifies the author as a person whose numbers need checking, and then nothing in the
   corpus gets the benefit of the doubt — including the never-revised control stratum and the 244/244 zero control,
   which are genuinely rare and genuinely valuable.

**The mirror image, and the actual strategy.** The same audience rewards precisely the behaviours this corpus
already exhibits: the **244/244 zero control** that proves the instrument can say zero (§A2); the **never-revised
stratum held at exactly 0.6700 across twelve measurements** that proves the degradation is not drift (§A4); the
**M12 observation** that the corrections resolved *asymmetrically* — the weakest arm *down* (0.3158 → 0.2947 →
0.2632), `modernbert-base` *up* (0.342105 → 0.347368) — so the defects **inflated the inter-arm gap** rather than
uniformly flattering the candidate (§A3) *[corrected by UCORR4, 2026-10-15: prior wording generalised to "all three
corrections moved the candidate down", which the evidence contradicts.]*; the **M7** control that caught a
predicate inversion before publication (§A2); the **confessed fabrication and the failed pre-audit** in the corpus's
own inputs (§D); the **"no external match found"** findings kept as findings rather than softened (§A4 §6–§7). And
the cheapest real paper in the corpus is *about exactly this*: `LEARNINGS.md` M1–M14 as a short methodology paper —
"a positive result needs a control that could have said no" (§D closing note).

So the honest summary of this whole document is narrow and unglamorous: **lead with the controls, publish the
checkable result first, put the caveat in your own sentence before anyone else can, and let the artifacts accumulate
DOIIs and citations.** Everything platform-specific above is machinery for making that happen in public. Reaching
the field is not a substitute for the work being right — it is only the mechanism by which the work can be checked.
Which is, appropriately enough, the research question.

---

## Sources

All pages fetched directly by URL on **2026-10-11** (`web_fetch` / `local_web_scrape`); dates are as stated on the
page. Load-bearing claims are cited inline as `[S#]`. `UNVERIFIED` marks a claim I could not source from a
reachable primary page.

| Id | Source | Date on page | Used for |
|---|---|---|---|
| S1 | https://info.arxiv.org/help/endorsement.html | current | endorsement: who can endorse, how to seek personal endorsement, "not peer review", no mass emailing |
| S2 | https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy | 2026-01-21 | endorsement policy change: institutional email no longer sufficient; both-requirements path; personal endorsement path |
| S3 | https://info.arxiv.org/help/policies/identity_and_affiliation.html | current | misrepresentation of affiliation = possible permanent suspension; consistent name; ORCID recommended |
| S4 | https://info.arxiv.org/help/moderation/index.html | current | moderation is not peer review; decline criteria; closer scrutiny after prior delays; 2 new submissions/calendar month, 3 active |
| S5 | https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/ | 2026-10-01 | the rate-limit announcement linked from `[S4]` (URL observed on the moderation page; post itself not fetched) |
| S6 | https://info.arxiv.org/help/policies/content-types.html | current | accepted/not-accepted content types; articles "should be complete final drafts" |
| S7 | https://help.zenodo.org/docs/github/describe-software/citation-file/ | current | `CITATION.cff` support; `.zenodo.json` overrides it; GitHub citation suggestion; `cffconvert` |
| S8 | https://help.zenodo.org/docs/github/archive-software/github-upload/ | current | enable repo → create GitHub release → record DOI → archived in Software Heritage |
| S9 | https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4 | "current as of 2026-10-02" | the eight O-1A criteria and their considerations, verbatim phrasing; criteria ≠ standard; totality |
| S10 | https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-3 | current; policy alert 2025-01-08 | no self-petition; entity/agent may file; critical-and-emerging-technology evidence update dated 2025-01-08 |
| S11 | https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-2 | current | the standard: sustained national/international acclaim; "one of the small percentage… very top of the field" |
| S12 | https://news.ycombinator.com/showhn.html | current | Show HN norms: runnable things; reading material off-topic; non-trivial; be around; no solicited upvotes |
| S13 | https://aclrollingreview.org/ ; https://aclrollingreview.org/sustainable-reviewing-2026 | 2026-09-11 | ARR reviewing model; 38 % of ~17K May 2026 submissions from authors without a publication record; qualified service contributor; broadened qualifications (Aug 2026); ORCID required on OpenReview |
| S14 | https://scholar.google.com/intl/en/scholar/citations.html | current | Scholar profile setup; **institutional email required for inclusion in Scholar search results** |
| S15 | https://info.orcid.org/what-is-orcid/ (and its nav: peer-review workflow) | current | ORCID is a free researcher identifier and a portable peer-review record; recommended by `[S3]`, required by `[S13]` |
| S16 | https://huggingface.co/papers | current | Daily Papers surface + email digest exist (observed) |
| S17 | https://bsky.jazco.dev/stats | current | fetched; returned only a page title, no extractable figures — cited as a **failed** verification attempt, not as evidence |

**Failed or unavailable sources, recorded honestly:** `local_web_search` (SearXNG) returned "no results" for every
query across the session; the built-in `web_search` is unconfigured (missing API key); DuckDuckGo HTML served a bot
challenge; Mojeek returned HTTP 403; Bing via `local_web_scrape` returned generic results and ignored long queries;
`reddit.com/r/MachineLearning/about/rules.json` returned HTTP 403 and a Redlib mirror was behind an anti-bot
challenge; `huggingface.co/docs/hub/papers` returned HTTP 404. **Consequently the 2026-specific algorithmic
mechanics of LinkedIn reach and the X-vs-Bluesky researcher split are marked `UNVERIFIED`** rather than asserted —
the platform guidance above rests on platform-invariant content norms, not on unverifiable algorithm claims.
