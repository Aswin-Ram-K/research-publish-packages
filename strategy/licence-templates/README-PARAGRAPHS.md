# README paragraphs — the exact wording for each of the two cases

> **DRAFT — templates for the author to place.** See [`PLACEMENT.md`](PLACEMENT.md).
> Use these verbatim wherever the wording is repeated, so the statement is consistent everywhere
> (README, package metadata, release notes, artifact description).

Placeholders are filled (2026-10-16): `2026`, `Aswin-Ram-K`, and the published repository's own
issue tracker (`https://github.com/Aswin-Ram-K/research-publish-packages`). There is no
project-name placeholder: the author does not reserve the name, so the reservation line that used
it was removed (see the record in `PLACEMENT.md`).

---

## Case A — the main Consonance repository (proprietary, private)

Place this paragraph in the README of the **private / proprietary** repository:

> This repository is **confidential and proprietary**. It is not public, not source-available, and
> not open source. Copyright (c) `2026` `Aswin-Ram-K`. **All rights reserved.** No
> licence is granted: nothing here gives you permission to use, copy, run, modify, distribute or
> disclose any part of it, and access to it does not give you that permission either. The designs
> and mechanisms in it are maintained as **trade secrets**. Access is restricted to authorised
> persons and is governed by a separate written agreement. See `LICENSE` and
> `TRADE-SECRET-NOTICE.md`.

---

## Case B — each extracted piece released publicly

Place this paragraph in the README of **every repository that is released publicly**:

> This project is **source-available, not open source**. It is released under the **PolyForm
> Noncommercial License 1.0.0** — free to use, study, modify and redistribute for personal, hobby,
> research and other **noncommercial** purposes. **Any commercial use requires a paid commercial
> licence, obtained through the published repository's own issue tracker at
> <https://github.com/Aswin-Ram-K/research-publish-packages>** (see `COMMERCIAL.md`). No personal
> address is published. The Noncommercial licence
> does not cover commercial use; the reason is the licence's own qualifier, *"without any anticipated
> commercial application"*, read with its exhaustive list of permitted purposes — a business
> evaluating the software in order to buy falls outside all of them. That is an **inference from the
> quoted clause**, not a clause that names "evaluation": so there is no free commercial evaluation.
> **Academic, public-research, public-health, public-safety, environmental and government
> institutions are permitted users of this same licence**, not prospective licensees — it permits use
> by "any charitable organization, educational institution, public research organization, public
> safety or health organization, environmental protection organization, or government institution …
> regardless of the source of funding or obligations resulting from the funding." **Forks and
> published noncommercial modifications are welcome**; only *ideas* are considered for integration —
> code contributions and patches are not accepted or merged (`CONTRIBUTING.md`). Notice line, already
> filled: `Required Notice: Copyright 2026 Aswin-Ram-K`.

Standalone (use where only the carve-out is needed — a docs page, a `README` section, or a listing):

> **Academic, public-research, public-health, public-safety, environmental and government
> institutions are permitted users of this same licence.** The PolyForm Noncommercial License 1.0.0
> permits use by "any charitable organization, educational institution, public research organization,
> public safety or health organization, environmental protection organization, or government
> institution … regardless of the source of funding or obligations resulting from the funding."

---

## Notes on use (not part of the paragraphs)

- **Say "source-available", never "open source".** The Noncommercial licence is not an open-source
  licence. §5.1 and §6 (rule 5) of `CODE_LICENSING_STRATEGY.md` require this wording.
- **Keep the two paragraphs apart.** A repo carries exactly one of them — the proprietary one, or
  the released-piece one. Never both.
- **Name the academic carve-out in every released README — it is now drafted above.** The licence's
  *Noncommercial Organizations* clause permits use by charitable, educational, public-research,
  public-safety, environmental and government institutions *"regardless of the source of funding or
  obligations resulting from the funding."* §6 (rule 6) recommends naming it deliberately; the
  sentence is drafted above in the licence's own words (inside the Case B paragraph and as a
  standalone line), and `PLACEMENT.md` requires it in every released piece's README. Without it
  these institutions read "noncommercial" as a blocker and self-exclude.
- **The "no free commercial evaluation" phrasing is an inference, here and in `COMMERCIAL.md`.**
  This file now marks it as one (quoted qualifier plus the exhaustive permitted-purpose list). The
  same wording at `RELEASED-PIECE/COMMERCIAL.md:16` was **not** edited by UFIX7 — that file is
  outside this unit's write paths; a follow-up should mark it there too. The conclusion is sound and
  relied on by UCODE1 and UTS1.
- **The contact gap — RESOLVED (2026-10-16).** `CODE_LICENSING_STRATEGY.md` supplies no commercial
  contact address, and no personal address is published: the contact is the published repository's
  own issue tracker, `https://github.com/Aswin-Ram-K/research-publish-packages`.
