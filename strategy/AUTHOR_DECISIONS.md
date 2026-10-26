# AUTHOR_DECISIONS — the seven fork points, one page

**Unit:** UDECIDE1 · **Date:** 2026-10-15 · **Sources:** the strategy documents, cited `file:line`.
Nothing here is a new measurement; every number is attributed to the document that states it.
**How to answer:** reply per id (`D1` … `D7`). Each entry is one question, ≤3 options, the cost the sources give,
a recommendation marked as mine, and what is blocked until you answer.
**Context that is already fixed:** `strategy/PAPER_CANDIDATES.md:1037` re-triage — **9 publish, 1 withhold, 5
needs-author-decision**; UVER6 re-derived it and it stands (`PAPER_CANDIDATES.md:1150-1151`). NC1 is one of the
9 publish, blocked by a packaging question (`D6`). The five decision rows are `D1`–`D5`.

---

## D1 — #6 graded progressive disclosure: does the cache-safety claim ship without its emitter?
- **Q.** Publish the finding with the emitter withheld, or build a neutral emitter so a reader can re-run it?
- **Options.** (i) Re-implement a neutral emitter. (ii) Publish the finding, emitter withheld. *(The sources
  offer exactly these two — `PAPER_CANDIDATES.md:1085-1087`.)*
- **Cost / buys.** The finding is separable: *changing only the depth of a reference resolution leaves the
  provider prefix byte-identical, and a graded three-rung knob is 27.8 % cheaper than a binary one at equal
  sufficiency* (`PAPER_CANDIDATES.md:1062-1064`). The artifact is not: the only emitter on disk is the context
  engine (`compiler.ts`, **M7**), so limb (b) of the extracted-project test fails today
  (`PAPER_CANDIDATES.md:1026`). Option (i) **costs an unbudgeted build**; option (ii) ships the result with no
  reproducible harness.
- **Recommendation (mine).** **(i) re-implement the neutral emitter** — the finding is the saleable part and the
  rule requires a releasable artifact (`PAPER_CANDIDATES.md:1005-1006`); (ii) ships a claim a reader cannot check.
- **Blocked until answered.** #6's manuscript and package; the per-paper artifact slot in the release plan.

## D2 — #7: is the paper the batching note, or the full routed-extraction scope?
- **Q.** Scope #7 to the batching result, or keep the staged-routing arm?
- **Options.** (i) Batching note only (R2+R1). (ii) Full scope. *(§B7 had already named the note as the fallback,
  `PAPER_CANDIDATES.md:1090-1091`.)*
- **Cost / buys.** (i) *Batching 16–90 binary decisions at `effort=none`*: calls cut 15–90×, prompt tokens 2.4×,
  F1 within ±0.01 at **n=1800/config** — a standalone positive needing no kernel machinery
  (`PAPER_CANDIDATES.md:1068-1071`), **~1–2 weeks** and 7 files, manuscript to be written (`LEAD_PACKAGE.md:96`).
  (ii) *Routed extraction at 1/14 context, exposure 0/20* — its harness **is** the staged extractor, i.e. the
  gate/absence machinery (**M10**), and n=20 cannot separate the top four arms (`PAPER_CANDIDATES.md:1071-1075`):
  needs round-2 experiments **and** a neutral re-implementation.
- **Recommendation (mine).** **(i) the batching note.** The evidence points there (`PAPER_CANDIDATES.md:1088-1089`)
  and it is the recommended lead of the whole programme (`LEAD_PACKAGE.md:107`).
- **Blocked until answered.** The lead manuscript; and `D7` (the same material's package shape). One unknown to
  close first: whether `tools/gated-read/bench.py` runs standalone is **UNVERIFIED** (`LEAD_PACKAGE.md:273-275`).

## D3 — #8: can the projection arm be a generic summariser?
- **Q.** Withhold the projection arm (and the dissociation claim with it), or disclose the projection mechanism?
- **Options.** (i) Withhold the arm → the paper loses the dissociation. (ii) Disclose **M1/M2**. *(The evidence
  explicitly rejects a third "generic projection" option — `PAPER_CANDIDATES.md:1092-1096`.)*
- **Cost / buys.** The measured projection is the kernel's derived state and its shape is a corpus document
  (`SM_PROJECTION_SHAPE.md`, **M1/M2** — `PAPER_CANDIDATES.md:1029`); a generic re-implementation *would not be
  the arm that was measured*. Independently, the candidate is `needs new experiments` (n=4/cell,
  `PAPER_CANDIDATES.md:1029`), so round 2 is owed either way.
- **Recommendation (mine).** **Withhold / do not publish as a standalone paper this cycle** — the evidence points
  no (`PAPER_CANDIDATES.md:1093`), and the n=4/cell weakness means publishing now would need re-running anyway.
- **Blocked until answered.** #8's package; the full-history vs projection comparison's citable form.

## D4 — #13: write the long-horizon agent-evaluation survey?
- **Q.** Write it as a fast-DOI side-channel, or drop it?
- **Options.** (i) Write it as an optional parallel side-channel. (ii) Drop it. *(It is exempt from the
  extracted-project-with-artifact rule — `PAPER_CANDIDATES.md:1097-1099`.)*
- **Cost / buys.** 1 file, `LONG_HORIZON_EVALS_2026.md` (1,529 lines), 1 gate hit (`StateClass` at `:1343`),
  **~3–7 days to a DOI** (`LEAD_PACKAGE.md:98`) — but it **cannot lead** the package programme: it ships no
  artifact, and the repo's purpose is a code+paper store proving *data → package → DOI* (`LEAD_PACKAGE.md:249-254`).
  It is an internal research note on disk, not a survey, so reframing (title, abstract, scope, excise §6) is real
  work (`LEAD_PACKAGE.md:255-258`); TMLR no longer considers surveys (`PAPER_CANDIDATES.md:1034`).
- **Recommendation (mine).** **(i) side-channel only** — cheap, clean, a DOI is a DOI, but it must not be the lead
  (`LEAD_PACKAGE.md:265-267`).
- **Blocked until answered.** Nothing critical; the release package ship list is unaffected either way.

## D5 — #14: is a survey-only paper worth writing after excision?
- **Q.** Excise §8 and the §4.4 Consonance inference and publish a survey-only paper, or drop the candidate?
- **Options.** (i) Survey-only paper after excision (**~2–3 weeks**, `LEAD_PACKAGE.md:102`). (ii) Drop it. *(The
  position half is not an option: it restates the already-public W3, so its defect is **duplication, not
  disclosure** — `PAPER_CANDIDATES.md:1035`, `:1146-1147`.)*
- **Cost / buys.** As it exists, `docs/research/AGENT_HARNESSES_2026.md` carries **33 `Consonance` mentions** and a
  dedicated §8 "Implications for Consonance" (`:679`), naming `StateClass`, `SandboxSpec`, `Budget` and the gate
  chain (`PAPER_CANDIDATES.md:1035`, corrected by UWITH1 per UVER6 C5). Excising the exposure **removes the
  paper's argument** (`LEAD_PACKAGE.md:261-263`); what survives is the survey half alone.
- **Recommendation (mine).** **(ii) drop it**, or at most fold its survey half into D4's #13 work — #14 is
  recorded as "not a candidate at all" (`LEAD_PACKAGE.md:261`).
- **Blocked until answered.** #14's package slot; the #14 gate-hit item in the release triage
  (`LEAD_PACKAGE.md:102`; 36 hits on 823 lines).

## D6 — NC1: publish M13 `tools/**` + the trace corpus, or re-scope the claim? *(carried forward)*
- **Q.** Which route unblocks NC1 — ship the detectors, or restate NC1 as a method/format paper?
- **Options.** (i) Publish the M13 `tools/**` module set **plus the trace corpus (pinned: 0.83 MB)**. (ii) Restate NC1 as a
  method/format paper and re-derive the `prevention.automated` rows from a published table. *(UNC1A's §9 adds a
  third: if both are declined, re-cast NC1 as a method/format contribution — `NC1_UNBLOCK.md:270-272`, which is
  what (ii) effectively does. I have collapsed it into (ii).)*
- **The blocker, precisely.** One line: `evals/prevention.ts:42 import { DEFAULT_SESSION } from "../tools/trace.ts"`,
  whose value is `tools/trace.ts:122 export const DEFAULT_SESSION = "2026-09-28-duval-m0"`
  (`NC1_UNBLOCK.md:45-47`). It is **incidental** — a plain string constant, nothing executed (`NC1_UNBLOCK.md:65-71`)
  — but fixing it does **not** unblock the package: `tsc` on the reader surface still fails with **19 errors over
  13 distinct withheld modules**, and the eval still fails **4 of its own assertions** (`NC1_UNBLOCK.md:21`,
  `:104-115`; `NC1_FIX_PROPOSAL.md:102-104`).
- **Cost / buys — option (i).** Publishes M13: `tools/trace.ts` (itself gate-dirty, **4 hits** at `:5`, `:60`,
  `:122`, `:380` — `NC1_UNBLOCK.md:189`), the trace corpus `traces/2026-09-28-duval-m0.jsonl` at **866,816 bytes /
  573 records / 573 gated lines / 712 gate occurrences** (measured from the pinned copy
  `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl`, sha256 `431605e6…`;
  `NC1_UNBLOCK.md` §check C, `:133-135`), the commit↔trace history, and — if the reader surface stays
  `registry.ts` — the whole **21-file `src/` closure** (`NC1_FIX_PROPOSAL.md:121-123`). Buys a green first run at
  current numbers. UNC1A marks this **NOT FIXABLE without an explicit author call** (`NC1_FIX_PROPOSAL.md:125-126`).
  *(Superseded figure: **1,031 gate hits** was live-path currency — 1,031 is the line count of the 1,570,243-byte
  blob the live file held at 18:50:03 (`orchestration/units/UCONT1.md` attribution table, trace row, `:30`) — and
  no state reproduces it as a gate count.)*
- **Cost / buys — option (ii).** No new disclosure; ships only `evals/*.ts` + `docs/MISTAKES.md` behind a
  package-local runner that does not import `registry.ts` (`NC1_FIX_PROPOSAL.md:130-133`). But check B finds
  **6 of 12 automated rows resolve to nothing** — B1/B2/B4 (`scripts/sync-issues.sh`), E1 (`scripts/guardrails.sh`),
  E4 (`scripts/write-scope-guard.mjs`), E5 (`tools/trace.ts` — `NC1_UNBLOCK.md:126-130`) — so the headline number
  **must move**. **UNC1A's own two documents disagree on how far:** `NC1_UNBLOCK.md:198` says "possibly 12 → 8",
  while `NC1_FIX_PROPOSAL.md:138-141` says **12 → 11 at best, 12 → 6 at worst**. **Prefer the wider
  FIX_PROPOSAL range (6–11 survive; 6 rows at risk)** because it states the count of all six rows (the rows themselves are named in `NC1_UNBLOCK.md:126-130`, not in FIX_PROPOSAL) — but attribute it:
  FIX_PROPOSAL §D calls its own numbers **a specification, not a measurement** (`NC1_FIX_PROPOSAL.md:177-178`),
  and no independent verifier has re-derived them. Checks C and D also need a decision: mark them package-local
  N/A, or ship the corpus (= option (i)) — `NC1_FIX_PROPOSAL.md:142-146`.
- **Recommendation (mine).** **(ii), with the 2-line inline import fix applied regardless of the answer** — §A is
  behaviour-neutral and closes the named blocker (`NC1_FIX_PROPOSAL.md:13`, `:89-96`), while option (i) buys a
  green run at the price of exactly the disclosure the withhold rule exists to prevent
  (`PAPER_CANDIDATES.md:1003-1006`). Pre-agree the new automated count before an implementer applies it
  (`NC1_FIX_PROPOSAL.md:149-150`).
- **Blocked until answered.** NC1's manuscript and package; the NC1 entry in the ship list; the stale `12 automated`
  figure wherever it appears (`NC1_FIX_PROPOSAL.md:163-166`).

## D7 — `papers/gated-read-batching/`: paper-only entry, or leave it out? *(carried forward)*
- **Q.** Ship it as a **paper-only** package (its 4 documents, source material declared withheld), or leave it out
  entirely until a reproducibility subset exists?
- **Options.** (a) Paper-only: the 4 hard-clean documents + explicit withheld-source statement. (b) Withhold it
  until a subset is built. *(This is verbatim the manifest's "for the orchestrator, not taken here" recommendation —
  `PUBLISH_PACKAGE_MANIFEST.md:487-493`.)*
- **Cost / buys.** The directory has **exactly 5 files**; it is **not in this package at all** — `UBUILD1.build.sh`
  stages `papers/encoder-crossover-190` only (`PUBLISH_PACKAGE_MANIFEST.md:186-192`). `DISCLOSURE_CHANGES.md`
  carries **19 hard hits** and is **dropped, not scrubbed** (its only purpose is the audit record;
  `PUBLISH_PACKAGE_MANIFEST.md:195-200`). The other 4 are **hard-clean, 0 hits each**
  (`PUBLISH_PACKAGE_MANIFEST.md:201`). It **cannot** ship as a "reproducibility package": the **9,260-row**
  `gated-read-rows.jsonl` and the summary exist only as mirrors of the read-only target (`state/…`), there is no
  `repro/gated-read-batching/` at all, and no fixture, exact commands or pre-registration in the workspace
  (`PUBLISH_PACKAGE_MANIFEST.md:467-485`). What a reader loses under (a): the 39 `G:`- and 8 `P:`-located
  references cannot be checked without target-repo access — a cost already *declared* at `CLAIMS.md:8` and
  `REFS.md:11` (`PUBLISH_PACKAGE_MANIFEST.md:239-242`).
- **Recommendation (mine).** **(a) paper-only.** The withholding is already declared and gate-clean, so "the
  manuscript does not need new prose" (`PUBLISH_PACKAGE_MANIFEST.md:215-216`); the material is the recommended lead
  (`LEAD_PACKAGE.md:96`, `:107`), and (b) strands the lead's own paper behind a subset that cannot be built without
  redistributing the target. One paper-side locator note, corrected: the `G:` locator in `REFS.md` is `G:49-51` at `REFS.md:68`, not `:66`
  (whose row uses `P:246`, the locator `REFS.md:11` declares), and the `G:` legend line is `REFS.md:15`. **No fix is owed at `:66`** (`PUBLISH_PACKAGE_MANIFEST.md:232-237`).
- **Blocked until answered.** The release package's ship list, `NEVER_SHIP`, and the gate total
  (`PUBLISH_PACKAGE_MANIFEST.md:493`); the #7 manuscript (with `D2`).

---

## Already settled — do not re-open
The licence posture (**PolyForm Noncommercial 1.0.0** for released artifacts, **CC BY 4.0** for paper text,
Consonance proprietary/closed), **no copyright registration**, and the **code-agnostic release policy** are done.
Three documents still frame parts of this as open — stale framing, recorded not raised:
- `PUBLISH_PACKAGE_MANIFEST.md:446-449` and `:497` — "MIT is STALE … hence flagged, not switched", "author's call".
- `PUBLISH_PACKAGE_MANIFEST.md:458-465` — the licence scope division is declaration-only and "depends on the tier
  decision at §12.1"; the §12.1 tier is the stale open item.
- `LEAD_PACKAGE.md:282-283` — "Whether PolyForm Noncommercial is the settled licence for this package specifically".
The **notice-placement** leftover (no `code/LICENSE` / `paper/LICENSE`, no scoping clause in the root `LICENSE`)
is an implementation detail of a settled posture, not a new decision (`PUBLISH_PACKAGE_MANIFEST.md:458-461`).

## Disagreements and stale figures, one line each
- **NC1 option-(ii) worst case:** `NC1_UNBLOCK.md:198` (12 → 8) vs `NC1_FIX_PROPOSAL.md:140` (12 → 11 best,
  12 → 6 worst). Neither independently verified; prefer the FIX_PROPOSAL range (see `D6`).
- **`gated-read-batching` status is framed both ways in one document:** decided ("the whole directory is outside
  the package", `PUBLISH_PACKAGE_MANIFEST.md:190-193`) and open ("scope recommendation … not taken here",
  `:487-493`). This is the decision carried forward without an answer.
- **`DISCLOSURE_CHANGES.md` hits:** 19 (gate's 24-pattern list, the shipping arbiter) vs UFIX11's 52 (wider sweep
  list). Both are right and **not comparable**; the gate's list governs (`PUBLISH_PACKAGE_MANIFEST.md:196-200`).
- **#7's n:** §G.1 says "n=1800/config" (`PAPER_CANDIDATES.md:1028`); `LEAD_PACKAGE.md:113-120` gives the same
  n=1,800 per config over a 9,260-row corpus. Consistent.
- **Latest verification report touches none of these:** `strategy/VERIFICATION_REPORT_13.md:1-11` re-derives
  `strategy/CPRIME_MEASUREMENT.md` only (verdict `pass`); it neither confirms nor contradicts the figures above.
- **ULEAD1's tools/trace gate count was UNVERIFIED** (`LEAD_PACKAGE.md:296`); UNC1A measured it later at 4 hits
  (`NC1_UNBLOCK.md:189`). **Prefer 4** — it is the later, actually-run figure.
