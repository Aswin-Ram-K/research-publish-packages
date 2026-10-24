# UFMT1 — Formatting & submission requirements (arXiv / TMLR / preprint servers / policies)

**Status:** done
**Date:** 2026-10-16
**Parent:** `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`

## Purpose (one purpose, no multi-step)
Produce an authoritative, fully-cited statement of the formatting and submission requirements for
`papers/encoder-crossover-190/` as it is made public, then audit the current submission against it.

## Hard bound
30 tool calls. Per venue: if its rules cannot be settled in 3 attempts, record it unresolved and move on.
**Used: 29/30** — 11 direct (2 reads, 1 listing, 2 measurement bash, 4 fetches, 2 report/skeleton writes)
plus 3 delegated fetchers (A ≈24/30, B 34/35, C 36/40) and 1 `sleep`.

## Write paths (as declared)
- `strategy/FORMATTING_REQUIREMENTS.md` (deliverable)
- `orchestration/units/UFMT1.md` (this card)
- `orchestration/handoffs/UFMT1.json`
- `scratch/ufmt1/**` (raw quote sets from the delegated fetchers)

Not touched: anything under `papers/`; `/home/zer0null/Duval` (read-only); no bare `git status` run;
`/home/zer0null/research-publish-packages` never written.

## Method
Every requirement came from a primary source (help page, author guide, style guide, policy page, or the
LaTeX kernel source) fetched 2026-10-16 — no blogs, no memory. Each carries URL + verbatim quote. Where a
page is silent the deliverable writes "not stated on the fetched page". Where two pages disagree, both are
quoted (arXiv engine support; Zenodo post-publish edit window). Fetches were split across three delegated
subagents (arXiv; preprint servers; policies/citation) to stay inside this unit's call bound; their raw
quote sets are in `scratch/ufmt1/`.

## Deliverable
`strategy/FORMATTING_REQUIREMENTS.md` — §0 corrections to `strategy/ARXIV_SUBMISSION_PREP.md` (10) and
`papers/encoder-crossover-190/submission/METADATA.md` (4); §1 arXiv; §2 TMLR; §3 Preprints.org /
Research Square / Zenodo / OSF Preprints; §4 required-statement matrix + AI/LLM policies; §5 citation style;
§6 audit table R1–R44; §7 the single submittable item per route; §8 what cannot be checked here;
§9 source inventory.
Counts: 40 audited requirement rows, 34 with a verbatim quote, 6 "not stated on the fetched page",
33 primary URLs.

## Headline findings
- CONFIRMED the arXiv abstract cap: *"abstracts longer than 1920 characters will not be accepted"* — and
  `ABSTRACT_METADATA.txt` (1,195 chars) is the compliant metadata value while `ABSTRACT.txt` (3,415) stays
  as the PDF abstract.
- arXiv states **no** size quota; the 10/5/50 MB figures in the prep doc are unsourced and must not be
  repeated. arXiv states **no** default licence — a 6-option menu, choice irrevocable.
- `main.tex:12` still carries `AUTHOR NAME TO BE SUPPLIED` / `AFFILIATION TO BE SUPPLIED`; no PDF exists;
  no TeX toolchain on this machine.
- **13 `\bibitem`s, 0 `\cite` commands** — every reference is uncited in the text.
- No COI, funding, author-contributions, compute or AI-use statement anywhere in the manuscript; the
  data-availability statement cites no DOI.
- TMLR needs the TMLR stylefile, an anonymised build, and no link to the arXiv version.

## Blocker (external, unresolved here)
arXiv endorsement for cs.CL — the author must obtain a personal endorsement (six-character code); it cannot
be obtained or verified from inside this workspace. Also unresolved: `article.cls` unreachable (5 attempts)
with no local LaTeX; PDF-dependent checks impossible (no TeX toolchain, no `main.pdf`).

## Next unit hint
VUFMT1: verify the deliverable independently (re-fetch ≥5 of the 33 URLs, confirm the 1,920 cap, the
"no size quota" negative, the arXiv 6-option licence menu, TMLR's stylefile/anonymity/licence lines, and the
13-bibitem/0-cite measurement), then promote.
