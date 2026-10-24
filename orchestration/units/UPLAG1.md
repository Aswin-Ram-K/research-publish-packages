# UPLAG1 — Originality and quotation audit

**Purpose (one):** audit `papers/encoder-crossover-190/MANUSCRIPT.md` for (a) every quotation and its
attribution, (b) unmarked borrowed expression, (c) unnamed idea attribution (the author's main worry),
(d) figure/table reuse and licences, (e) third-party model/dataset naming vs attribution files.

**Deliverable:** `strategy/ORIGINALITY_CHECK.md`

**Hard bound:** 25 tool calls. Stop and report `partial` with the remainder named if exceeded.

**Write paths (nothing else):** `strategy/ORIGINALITY_CHECK.md`, `orchestration/units/UPLAG1.md`,
`orchestration/handoffs/UPLAG1.json`, `scratch/uplag1/**`.

**Constraints:** read-only audit; do NOT edit the manuscript. `/home/zer0null/Duval` is read-only.
Never write `/home/zer0null/research-publish-packages`.

**Method:** enumerate quotations by grep; extract 8+ word runs and probe the cited-source and
own-earlier-artifact populations; check each method named in the manuscript against its conventional
citation; fetch open-access/CC-BY sources only; report coverage as a sample, never as a scan.

**Status:** done.
