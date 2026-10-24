# UFIX7 — apply UVER7's corrections to the licence templates

**Unit:** UFIX7 (correction unit, applying `strategy/VERIFICATION_REPORT_7.md`).
**Bound:** max 30 tool calls — **used ~13**, stopped well inside.
**Target repo:** `/home/zer0null/Duval` — strictly read-only; untouched (no write, no `git`).

## Purpose

Re-confirm every item in UVER7's report against the disk, then apply the corrections it recorded, without
editing the PolyForm licence body (`RELEASED-PIECE/LICENSE` lines 10–140).

## Declared write paths (touched nothing else)

- `strategy/licence-templates/TRADE-SECRET-NOTICE.md`
- `strategy/licence-templates/PLACEMENT.md`
- `strategy/licence-templates/README-PARAGRAPHS.md`
- `strategy/licence-templates/RELEASED-PIECE/CONTRIBUTING.md`
- `orchestration/units/UFIX7.md`
- `orchestration/handoffs/UFIX7.json`

## Re-confirmed before editing

| Item | Probe | Result |
|---|---|---|
| C1 | `wc -l/-c` + `stat` on `strategy/TRADE_SECRET_AUDIT.md` | **507 lines / 48,851 bytes / 2026-10-15 15:31:34** — exists |
| C2 | `grep -n SUPERSEDED strategy/CODE_LICENSING_STRATEGY.md` | **2 hits, lines 433 and 600** (not 423/590) |
| Body | `sed -n '10,140p' RELEASED-PIECE/LICENSE \| sha256sum` | **`ffcca388…c94cc8`** — matches upstream |

## Changes applied

1. **C1 — `TRADE-SECRET-NOTICE.md:44–47`.** Replaced the stale "was not present on disk" gap block with
   UVER7's suggested "Legal basis supplied" wording (path, 507 lines / 48,851 bytes / 2026-10-15
   15:31:34), plus an append-only correction marker.
2. **C2 — `PLACEMENT.md:96`.** Citation `:423`, `:590` → **`:433`, `:600`**, with a marker recording the
   prior value.
3. **C3.1 — `README-PARAGRAPHS.md`.** "Placeholder-free notice line" → "Notice line — fill both
   placeholders before shipping", naming them (`<YEAR>`, `<COPYRIGHT HOLDER>`).
4. **C3.2 — `README-PARAGRAPHS.md`.** The "no free commercial evaluation" line now states it is an
   **inference** from the licence's own qualifier *"without any anticipated commercial application"* plus
   the exhaustive permitted-purpose list — not a clause that names "evaluation". Conclusion kept.
5. **C3.3 — `RELEASED-PIECE/CONTRIBUTING.md` §Name and logo, and `PLACEMENT.md` §4.** Recorded that
   PolyForm's `Notices` clause propagates only the terms, canonical URL and `Required Notice:` lines, so
   the name/logo reservation is **not carried to forks by the licence**.
6. **Academic carve-out sentence — drafted** (see below). Added to the Case B paragraph in
   `README-PARAGRAPHS.md` and repeated as a standalone line; the notes bullet that called it an unfilled
   gap is corrected; `PLACEMENT.md` §5.5 now records it as **required in every released piece's README**.

## Academic carve-out sentence (as drafted)

> **Academic, public-research, public-health, public-safety, environmental and government
> institutions are permitted users of this same licence.** The PolyForm Noncommercial License 1.0.0
> permits use by "any charitable organization, educational institution, public research organization,
> public safety or health organization, environmental protection organization, or government
> institution … regardless of the source of funding or obligations resulting from the funding."

Quoted from the licence's `Noncommercial Organizations` clause; no invented wording.

## Left as a gap (correctly)

- **`<CONTACT>` remains unfilled.** The author must supply the commercial contact address; not invented.
- The same "no free commercial evaluation" phrasing at `RELEASED-PIECE/COMMERCIAL.md:16` was **not**
  edited (outside this unit's write paths) — flagged for a follow-up in the README notes and in the
  handoff `next_unit_hint`.

## Did not do

- Did not edit the PolyForm body (`RELEASED-PIECE/LICENSE` lines 10–140): re-hashed after editing,
  `ffcca388…c94cc8`, unchanged.
- Did not edit `strategy/VERIFICATION_REPORT_7.md` or any file outside the declared write paths.
- Did not write to `/home/zer0null/Duval`; ran no `git` command anywhere in it.
- Did not investigate the `.git` write question (owned by the orchestrator).
