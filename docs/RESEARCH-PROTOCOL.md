# RESEARCH-PROTOCOL — read the published fact before paying for the measurement

Status: process rule, in force for every card that touches an external contract. Owner: this page.
First application: [`docs/research/tool-channel-sglang.md`](research/tool-channel-sglang.md) (record:
[`measure/research/tool-channel-sglang.json`](../measure/research/tool-channel-sglang.json)).

**Why this exists.** A batch spent **256 rounds** rediscovering by experiment what one vendor page states in a
table: structured `tool_calls` from an SGLang server exist only when the server is launched with a
`--tool-call-parser`, and `tool_choice` support depends on the parser/grammar backend. It then measured
**0 structured tool calls in 36 live requests** — 36 requests spent on a fact that was published. Research is
cheaper than measurement when the fact is public. Measurement is mandatory when it is not. This page is the
distinction, written so a worker applies it without judgement calls.

## 1. When research is required

Research is **required before the card starts** when the card:

- **(a) uses a network or API contract we did not write** — an endpoint, a flag name, a response field, an
  error code, a client-library behaviour;
- **(b) proposes a mechanism rather than measuring one** — "the server probably needs X", "the parser should
  emit Y";
- **(c) fixes an instrument whose semantics we are guessing at** — a counter, a parser, a grader input whose
  meaning is documented somewhere we did not read;
- **(d) spends model or live requests on a hypothesis that has a published answer.**

### The two-line test (no judgement calls)

```
Line 1: Does someone who OWNS this contract publish it — vendor docs, API reference, flag list,
        the library's own source, or the server's own --help / /v1/models response?
Line 2: Can I name the exact page or file, and the section in it, that would answer the question?

Both yes  -> RESEARCH FIRST. One bounded fetch, then measure whatever the page does not settle.
Either no -> MEASURE. Do not browse for a fact nobody published; go to the instrument.
```

Practical restatement: **if the answer could be copied out of a document, copy it out of the document.** If it
could only be obtained by running something against *our* rows, stack, or config, it is a measurement and
researching it is waste — the web cannot see our ledger.

Research costs **no inference**: the local web tools (`local_web_search`, `local_web_crawl`,
`local_web_scrape`) are not model requests. That is exactly why the trap in §6.1 is expensive to fall into in
the other direction: a page cannot answer a question about our own data, and no amount of fetching makes it.

## 2. Where research lands

Two files, both mandatory, both named by **SLUG** (lower-kebab, the same slug in both):

| file | carries |
|---|---|
| `docs/research/<SLUG>.md` | the human-readable note: question, sources with URLs and retrieval dates, the **specific** claim taken from each, verified vs inferred vs contradicted, what it changes, what it does not settle |
| `measure/research/<SLUG>.json` | the machine-readable record, gate-checkable: `sources[].url`, `sources[].retrieved_at`, `claims[].status`, `open_questions` |

Checked by [`tools/check_research_notes.py`](../tools/check_research_notes.py) (`python3
tools/check_research_notes.py --note measure/research/<SLUG>.json --doc docs/research/<SLUG>.md`) — a note
that fails it is not landed.

The JSON shape (minimum; extra keys allowed):

```json
{
  "slug": "<slug>",
  "question": "<one sentence>",
  "sources": [
    {"id": "s1", "url": "https://…", "retrieved_at": "YYYY-MM-DD", "kind": "primary|secondary",
     "claim_taken": "<the exact claim this source was used for>"}
  ],
  "claims": [
    {"id": "C1", "claim": "<what we now assert>", "status": "verified|inferred|contradicted",
     "source": "s1", "evidence": "<quote or section that supports it>"}
  ],
  "changes_plan": ["<what this note changes in the current plan>"],
  "open_questions": ["<what this note does NOT settle, and who checks it>"]
}
```

**Status vocabulary — this is the load-bearing part:**

- `verified` — read in a **primary** source (the vendor's page, the server's own `--help`/`/v1/models`
  response, the library's source). Must name the source id.
- `inferred` — reasoned from verified claims or from our own behaviour. **Never** presented as documented. An
  inferred claim is a hypothesis that owns a measurement.
- `contradicted` — a claim that disagrees with an observation on our stack, or with another source. A
  contradicted claim is **kept, not deleted**, with the disagreement recorded; resolving it is separate work
  (§5).

"Specific claim taken from it" means the sentence or table row, not the page title. A note that lists a URL
and no claim is not a research note; it is a bookmark.

## 3. The citation rule

1. **A fix card's prompt or handoff must name its research note** by path (`docs/research/<SLUG>.md`). A card
   that proposes a change to an external contract with no note is `inferred` by definition.
2. **A claim about an external contract with no cited source is `inferred`** and must be labelled so in the
   handoff. This covers API shape, flag names, error codes, defaults, version behaviour.
3. **Do not let a documentation fact wear a measurement's clothes.** `verified` describes the *source*, never
   the *stack*. "The docs say the flag exists" (`verified`) is not "our server accepts the flag"
   (`inferred` until checked locally, `contradicted` if the launch argv lacks it).

## 4. The stopping rule

Research stops when **the next action is decidable** — when a worker can say, without further reading, what to
run next and what result would mean which branch. It does **not** stop when it is interesting, thorough, or one
page from done.

**Budget: ≤6 fetches or ≤10 minutes per note, whichever comes first.** When the budget is spent, write the note
with what is verified and move the rest to `open_questions`. Exceeding the budget is a review finding, not
diligence.

Record the stop in the note's JSON `budget.stop_reason`, in the form *"each required question answered by a
primary source, or explicitly moved to open_questions"*. Stop conditions:

- every question in the card's research list is `verified` or explicitly `open`;
- the remaining questions are about our rows, our config, or our version → they are measurements, not research;
- further sources repeat the same primary page (diminishing return reached).

## 5. The precedence rule (in this workspace's terms)

1. A **primary source** — vendor docs, the server's own `--help` / `/v1/models` response, the library's source
   — outranks a blog post, a forum answer, or a model's memory.
2. A **measurement on our stack** outranks both **when they disagree** — and the disagreement must be
   **recorded** in the note (`claims[].status: "contradicted"` plus the observation), never resolved silently
   in favour of whichever is more convenient.

**Today's example.** The SGLang Tool Parser page states that `--tool-call-parser` "defines the parser used to
interpret responses" and every tool-call example launches with it (`verified`, one page). Our stack produced
**0 structured calls in 36 live requests**. That is a disagreement, and it does not make the docs wrong or the
measurement wrong — it makes an unverified premise visible: either the flag is **absent from the launch argv**
(checkable locally), or the **parser name does not match the model family** (checkable locally). Research told
us *where to look*; only measurement can tell us *what is true here*. The docs are not the suspect; our launch
configuration is.

## 6. Anti-patterns, each with a real instance from this batch

1. **Researching instead of measuring when the question is about *our* rows.** The batch's own defect — *how
   many structured calls did our 36 requests return?* — is a question about our request records. No page can
   answer it; only the rows can. Twenty-six fetches would still have returned "0 in 36" only after the
   measurement. Fetch what the contract says, then read the rows.
2. **Citing a doc for a version we are not running.** `docs.sglang.io` is **current-main, unversioned**
   documentation; the server behind `:8012` is a build whose version this card did not read. A parser table
   copied from that page describes the page's build, not necessarily ours — so any claim about `:8012`
   behaviour that comes from the page is `inferred` until the local version (the package version or the
   `--help` output) is read. Name the version you checked, or label the claim inferred.
3. **Treating a workaround as a fix.** A **text-protocol shim** — instructing the model to emit JSON in
   `content`, then parsing it client-side — can recover *arguments* but is **not a working tool channel**: it
   has no structured `tool_calls`, no `tool_choice` enforcement, and no server-side parser contract. If it is
   adopted, the record must say `"workaround": true` and the acceptance criterion for the tool channel stays
   **unmet**; a green shim test is not a green tool channel.

A fourth, cheap to catch in review: **a note with sources and no claims.** URLs are not research; the
`sources[].claim_taken` field exists to make that visible.

## 7. Checklist — a fix card and its handoff are incomplete without these

- [ ] The card names its research note path `docs/research/<SLUG>.md`, or declares that the card is a pure
      measurement of our own rows and needs none (§1, Line 1: *no*).
- [ ] `measure/research/<SLUG>.json` exists, parses, and carries `sources[].url`, `sources[].retrieved_at`,
      `claims[].status ∈ {verified, inferred, contradicted}`, `open_questions`.
- [ ] Every **verified** claim names a source id and quotes the specific text or table row taken from it.
- [ ] Every external-contract claim that no source supports is labelled **`inferred`**.
- [ ] Every disagreement between a source and our stack is recorded as **`contradicted`** with the measured
      observation — not silently resolved.
- [ ] `open_questions` names who owns each unresolved item (a local check, a version read, another card).
- [ ] Any shim or manual workaround is labelled **`workaround: true`** and not counted as the fix.
- [ ] **The handoff carries `research_note`** — the note path, or `null` with the pure-measurement reason —
      **and `claims_status`** — a per-claim map `{"<claim id or text>": "verified|inferred|contradicted"}`
      covering every external-contract claim the card relied on.
- [ ] **The handoff carries `adoption_considered`** — `true` when the card met a hairy problem (§8.1) and the
      adoption step ran, `false` only with a one-line reason naming which §8.1 test failed; when a research
      card exists it also carries **`adoption_memo`** — the memo path `docs/research/ADOPT-<SLUG>.md`, or
      `null` with `adoption_memo_reason`.

## 8. Adopt before build

**Why this section exists.** Operator instruction, verbatim: *"for every new problem we have, always learn
about what's already available out there to easily adopt and increase our throughput and reduce our workload
too — so make researching, when things seem hairy, a common step alongside coordination."* §1–§7 answer *"has
someone published the fact?"*; this section answers *"has someone already built the thing?"* — and makes that
lookup a **step**, not an instinct.

### 8.1 The hairy test

A problem is **hairy** when **any** of these holds:

- the mechanism is unclear (we cannot say which component does what);
- **more than one component must change** to fix it;
- we are about to **write infrastructure** rather than a measurement — a client, a retry loop, a cache, a
  scheduler, a gate, a benchmark harness, a provenance ledger;
- the **same-shaped problem has been solved outside this repo** — serving, batching, caching, tool calls,
  benchmarking, provenance, CI gating.

**Hairy ⇒ a research card comes first, before the build card** — exactly as coordination comes first. The
research card is cheap: it reads what exists and lands a memo; it does not build.

### 8.2 The adoption memo

Two files, same SLUG, same §2 discipline:

| file | carries |
|---|---|
| `docs/research/ADOPT-<SLUG>.md` | the table below, plus what each option actually says and what it does not |
| `measure/research/ADOPT-<SLUG>.json` | `sources[]` (url, retrieved_at, claim_taken), `claims[]` (status), `decisions[]`, `open_questions` |

The table — one row per candidate:

| problem | existing option (name, licence, maturity, last release) | what it would replace here | adopt cost (calls/files/risk) | build cost we would avoid | decision |
|---|---|---|---|---|---|

- **Every row carries a source URL and a retrieval date.** A row with neither is not a candidate; it is a
  guess, and it is marked `unassessed` rather than named.
- `decision ∈ {adopt, adapt, borrow-idea, build, not-applicable}` — `adapt` means adopt with a local patch;
  `borrow-idea` means take the interface/contract but not the dependency; `build` means we write it. A row
  whose candidates were never read says **`unassessed`** — an unread option is not a decision.
- **(licence, maturity, last release)** are three separate checks, not one vibe: an option whose licence was
  not read is not adopted, however convenient.
- A candidate that was **never read** is recorded under `open_questions`, never invented into the table.

### 8.3 The default, stated plainly

When `adopt cost < build cost` **and** the option is maintained, **adopt**. When it is not, write **one
sentence** why — in the memo row, not in chat — rather than defaulting to building because building feels
safer.

**The counter-example this batch earned.** Over roughly 200 rounds we hand-built a gate / budget / verdict /
provenance stack while mature tools exist for several of those layers. That is exactly the workload the
operator wants reduced. The honest counter-arguments — custom semantics that no general tool encodes, frozen
thresholds that may not move mid-experiment, one-writer discipline that a shared service would break — must be
written down **case by case**, with the option named; they may not be assumed for the whole stack.

### 8.4 Anti-patterns added to §6

5. **Adopting a tool to avoid understanding the problem.** A dependency that hides the mechanism turns a
   measurable defect into an unmeasurable one.
6. **A dependency added for a 20-line job.** Adopt scaling, not syntax; the cost is in the lockfile, the
   upgrade, and the debug — not in the diff.
7. **Replacing a frozen measurement path mid-experiment.** The grid's instruments may not move while it is
   being adjudicated. Adoption proposals for frozen paths are **recorded, not executed** — the memo row keeps
   `decision: adopt` with `blocked_by: frozen-path`, because a moving instrument voids the comparison it was
   meant to improve.
8. **Citing a project's README as evidence it works for our case.** A README is an advertisement; the evidence
   is the release, the licence, the maintenance signal, and — where the claim is about behaviour — a read of
   the code or a local measurement.

### 8.5 Handoff fields

§7's checklist gains `adoption_considered` and `adoption_memo`:

```json
"adoption_considered": true,
"adoption_memo": "docs/research/ADOPT-<SLUG>.md"
```

`adoption_considered` is `false` only for a problem that is not hairy under §8.1, and then the handoff says
which test failed. `adoption_memo` is `null` with `adoption_memo_reason` when no memo exists.

### 8.6 The ledger

`docs/research/ADOPTION-LEDGER.md` (+ `measure/research/ADOPTION-LEDGER.json`) is the running table of every
hairy problem this batch met and whether adoption was considered — including its `unassessed` rows, which are
the backlog, not the excuse.
