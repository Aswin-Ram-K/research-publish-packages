# UDISC1 — Prior public-disclosure audit (resolves UTS1's U13)

**Purpose (one):** establish whether any Consonance/kernel mechanism was **already** publicly disclosed.
**Answers:** `strategy/TRADE_SECRET_AUDIT.md` U13 — *"the largest untested assumption in the audit."*
**Deliverable:** [`strategy/PRIOR_DISCLOSURE_AUDIT.md`](../../strategy/PRIOR_DISCLOSURE_AUDIT.md)
**Bound:** 45 tool calls. **Used: 43.** Status: `done`.

## Outcome — the assumption resolved against the plan

**Yes: the mechanisms are already publicly disclosed.** Not on arXiv, not on a blog, not in a package — on
**GitHub**, in a public repository the workspace had never heard of:
`github.com/Aswin-Ram-K/publish-present-compete` (public, MIT, 38 commits, last commit **2026-10-10**).

Three findings carry the verdict:

1. **The paper UTS1 ruled `withhold` as a set is published byte-for-byte.** Public
   `findings/PAPER-DERIVATION.md` = **46,636 bytes**; Duval `docs/research/PAPER_DERIVATION.md` =
   **46,636 bytes**; identical title and **identical line numbers** (104, 219, 301, 321, 339, 435) for six
   distinctive mechanism strings.
2. **The public profile README states the mechanism** (public ≤ 2026-10-08): *"Capability-materialisation
   kernel for agent runtimes … Enforcement by absence, not refusal. A live A/B holds everything constant
   except the state class — and the workspace digest stays byte-identical when the capability is absent."*
3. **`decisions/DECISION_LOG.md` publishes 99 decisions with the alternatives rejected and why** —
   including D-001–D-006 (state-as-unit, state-as-continuation, engine-only authorship, `State.policyHash`,
   `ResourceRef`/BLAKE3, refusals first-class). The *rationale* is the part hardest to reconstruct, and it is public.

**Verdict: `partly disclosed`.** 9 of 13 mechanism classes are `already disclosed` (M1–M8, M10); 4 are
`cannot determine` (M9, M11–M13) **only because they were not read within bound**, not because of any
evidence of secrecy. The bias of the audit is toward **under**-reporting.

## What is still protectable

The **implementation**, and only that: `src/**`, concrete type declarations, the state-class catalogue in
code, the private corpora, `tools/**`, and unpublished prose (`CONSONANCE.md`, the monograph). The public
repo says so itself: *"The implementation is not published here. The code stays private."*

The withholding plan protects nothing for M1–M10. It also removes the patent fallback for those
mechanisms: the documents are **printed publications** dated 2026-10-01/08/10 and therefore prior art under
35 U.S.C. §102(a)(1). UTS1's O-1 cost calculation — *"the architectural claim is never published"* — is
moot; it is already published, dated and citable.

## Registries: nothing published (0 findings)

npm `consonance-kernel` not found (`consonance` = `jongold`'s font library, 11 years old);
PyPI `consonance` = **Tarek Galal's** WhatsApp-Noise-handshake package, an unrelated project;
crates.io empty; Docker Hub unrelated; GitHub Packages tab = **0**.

## The transferable lesson

**Ten** search phrasings — including the author's full name and the verbatim phrase *"enforcement by
absence"* — returned **nothing** about this project. The public repo was found by **going to the account**,
not by searching. **A clean search result is not evidence of non-disclosure here**, and every prior unit
equated *"the repo is private"* with *"nothing is public"*.

## Discipline

- **`/home/zer0null/Duval` never written to.** HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`;
  `status --porcelain` identical before and after (4 pre-existing untracked paths, **attributed to the
  unrelated concurrent session**). Reads only.
- **Write paths touched:** exactly the three declared. Other `strategy/` files were **read, never modified** —
  no clash with the unit drafting `strategy/`.
- **One deviation, disclosed:** one scratch copy of the public paper at `/tmp/pd.md`, deleted in the same
  run. Nothing was written outside `/tmp` and this workspace.
- Tool-call budget: **43 of 45**. No retry was needed; 2 calls failed benignly (a `cd` quoting error, a
  GitHub API HTTP 403, and a built-in web-search call with no API key).

**Not legal advice.** US-centric; EU/India standards remain unfetched (UTS1 U8).
