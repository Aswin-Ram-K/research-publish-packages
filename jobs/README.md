# jobs/ — job-search workstream output

This tree holds the output of the **job-search workstream**: five sibling units run at the
same time, each responsible for one geographic/sector subdomain, and each writing only into
its own subdirectory here.

> **Owner note:** `jobs/` is created and documented by unit **USTRUCT**. USTRUCT created the
> parent and this README **only** — it does not create, move, rename or delete anything under
> `jobs/<slug>/`. Those subdirectories are owned by their own units and may appear at any
> moment while other work is in flight.

## The five subdomain slugs

Each slug below is a directory name directly under `jobs/`:

| Slug | Subdomain |
|---|---|
| `us-nonprofit-research` | US nonprofit / think-tank / NGO research roles |
| `us-national-labs` | US national laboratories and federally funded R&D centres |
| `scandinavia-europe` | Scandinavia and wider Europe |
| `evals-safety-foundations` | Evaluation, AI-safety and foundation-model organisations |
| `india-ai` | India-based AI roles |

## Required layout per subdomain

Every `jobs/<slug>/` directory **must** contain at least these two files:

| File | Meaning |
|---|---|
| `FINDINGS.md` | The human-readable result: what was searched, what was found, what was ruled out, and what is still open. Must stand alone for a reader arriving cold. |
| `JOBS.jsonl` | The machine-readable result: **JSON Lines**, one JSON object per line, one line per job posting. Append-only; never rewrite earlier lines to "clean up" — correct by appending. |

Conventions that follow from the above:

- Files are written by the owning unit for that slug only. A unit never writes into another
  unit's slug.
- `JOBS.jsonl` must stay parseable **line by line**: no multi-line JSON objects, no trailing
  commas.
- Evidence (search queries run, URLs, dates, scraped snapshots) belongs inside the slug
  directory too, so the findings can be re-checked without re-running the search.
- 2026-10-15 JOB1: US nonprofit-research sweep complete — 30 orgs attempted, 58 openings in jobs/us-nonprofit-research/JOBS.jsonl, gaps (Open Phil/Palisade board/Simons/RAND) documented in jobs/us-nonprofit-research/FINDINGS.md.
