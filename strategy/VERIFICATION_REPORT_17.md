# VERIFICATION REPORT 17 — independent check of `strategy/AUTHOR_DECISIONS.md`

**Unit:** UVER17 (independent verifier; did not write the artifact under test).
**Target:** `strategy/AUTHOR_DECISIONS.md` — **166 lines**, **10 headings** (1 title + **7** `## D1`–`## D7` + *Already settled* + *Disagreements and stale figures*); the brief's claim of 7 decisions and 75 `file:line` citations is consistent with what is on disk.
**Author under test:** UDECIDE1. **Predecessor:** UVER16 died with a skeleton and no report.
**Verdict:** `partial` — every decision's substance and every priority figure verified except one contradicted D7 detail and one D6 wording overstatement (below). The disputed D6 number resolves **in the brief's favour**.
**Bound:** ≤20 tool calls. **Used: 11.**
**Containment:** `/home/zer0null/Duval` was only *read* (no git command was run against it, not even `--no-optional-locks`). Nothing was written outside the declared paths; `scratch/uver17/**` is the only scratch touched, and `scratch/uver16/**`, `repro/encoder-crossover-190-SANITISED/redact.py`, `orchestration/units/UBUILD1.build.sh` and `AGENTS.md` were not edited.

---

## Priority claims — all opened

| Claim (brief) | Cited | Actual line | Result |
|---|---|---|---|
| D1: "byte-identical prefix … 27.8 % cheaper" | `PAPER_CANDIDATES.md:1062-1064` | "leaves the provider prefix byte-identical, and a graded three-rung knob is 27.8 % cheaper than a binary one at equal sufficiency" | verified |
| D1: artifact fails limb (b) | `PAPER_CANDIDATES.md:1026` | "**fails limb (b)**: a reader cannot run it without the withheld context engine" | verified |
| D2: batching n=1800/config | `PAPER_CANDIDATES.md:1068-1071` | "F1 within ±0.01 at n=1800/config" | verified |
| D2: ~1–2 weeks, 7 files | `LEAD_PACKAGE.md:96` | "**7 files** … Write manuscript (~3–4k words) … **~1–2 weeks**" | verified |
| D2: routed harness *is* M10, n=20 | `PAPER_CANDIDATES.md:1071-1075` | "harness **is** the staged extractor … (M10), and its numbers are underpowered (n=20 …)" | verified |
| D3: "would not be the arm that was measured" | `PAPER_CANDIDATES.md:1092-1096` | `:1094` "A generic re-implementation would not be the arm that was measured" | verified |
| D3: n=4/cell | `PAPER_CANDIDATES.md:1029` | "It is also `needs new experiments` (n=4/cell)" | verified |
| D6 option (i): 1,570,243 B / 1031 hits | `NC1_UNBLOCK.md:133-135` | `:134` "**1,570,243 bytes**, and contains" / `:135` "**1031 gate hits**" | verified |
| D6: "6 of 12 … B1/B2/B4, E1, E4, E5" | `NC1_UNBLOCK.md:126-130` | "6 of 12 rows resolve to nothing — B1/B2/B4 (`scripts/sync-issues.sh`), E1 (`scripts/guardrails.sh`), E4 (`scripts/write-scope-guard.mjs`), E5 (`tools/trace.ts`)" (3+1+1+1=6) | verified |
| D6: "12→11 at best, 12→6 at worst" | `NC1_FIX_PROPOSAL.md:140` | "**12 → 11 at best, 12 → 6 at worst**" | verified |
| D6: UNBLOCK's "12 → 8" | `NC1_UNBLOCK.md:198` | "12 automated → 11 (and possibly 12 → 8 if all six unresolvable rows are demoted…)" | verified (and see §B) |
| D7: no `repro/` tree; 9,260 mirror rows | `PUBLISH_PACKAGE_MANIFEST.md:467-485` | `:481` rows "**absent outside `state/`** — only mirrors of the read-only target"; `:483` "**no `repro/gated-read-batching/` exists at all**" | verified |
| Disagreement: `tools/trace.ts` UNVERIFIED → measured 4 | `LEAD_PACKAGE.md:296`, `NC1_UNBLOCK.md:189` | `:296` "`tools/trace.ts` gate-hit count — **UNVERIFIED** (not scanned)"; `:189` "(RAN: 4 hits — `:5`, `:60`, `:122`, `:380`)" | verified — not an invented disagreement |
| Settled posture not re-opened | `PUBLISH_PACKAGE_MANIFEST.md:446-449`, `:497`, `:458-465`; `LEAD_PACKAGE.md:282-283` | the three "stale framing" lines are all there as quoted | verified (PASS) |

Independent re-counts (not just reading the cited doc):
- `papers/gated-read-batching/` = exactly **5 files** (`CLAIMS.md`, `DISCLOSURE_CHANGES.md`, `GAPS.md`, `MANUSCRIPT.md`, `REFS.md`).
- `state/refresh-verify/.../gated-read-rows.jsonl` (`wc -l`) = **9,260** rows; no `repro/gated-read-batching/`.
- `/home/zer0null/Duval/tools/trace.ts:122` = `export const DEFAULT_SESSION = "2026-09-28-duval-m0";` (D6's named blocker is real).
- `/home/zer0null/Duval/docs/research/AGENT_HARNESSES_2026.md` = 823 lines, `grep -c Consonance` = **33**, `:679` = `## 8. Implications for Consonance` (D5).
- `/home/zer0null/Duval/docs/research/LONG_HORIZON_EVALS_2026.md` = **1,529** lines; `:1343` carries `StateClass` (D4).
- `PAPER_CANDIDATES.md:1037` = "9 `publish`, 1 `withhold`, 5 `needs-author-decision`" and `:1150-1151` = UVER6 re-derivation stands (intro block).

Spot-check coverage: **≈55 citation targets opened across 7 source files** (`PAPER_CANDIDATES.md`, `LEAD_PACKAGE.md`, `NC1_FIX_PROPOSAL.md`, `NC1_UNBLOCK.md`, `PUBLISH_PACKAGE_MANIFEST.md`, `REFS.md`, `VERIFICATION_REPORT_13.md`) — exceeds the 18/4 requirement. Both NC1 documents were read in full.

---

## B. Re-done D6 arithmetic — which document the count supports

The only enumeration of the failing check-B rows is `NC1_UNBLOCK.md:126-130`: **6** rows (B1/B2/B4, E1, E4, E5) whose only detector is a non-eval file. Arithmetic: **12 − 6 = 6**. Therefore:

- `NC1_FIX_PROPOSAL.md:138-140` ("Six of twelve rows currently resolve to nothing… **12 → 11 at best, 12 → 6 at worst**") is **internally consistent** with the enumeration.
- `NC1_UNBLOCK.md:197-198` ("12 automated → 11 (and possibly **12 → 8** if **all six** unresolvable rows are demoted…)") is **internally inconsistent**: demoting *all six* gives 12 → 6, not 12 → 8 (8 would require only four demotions, which is not what the sentence says).
- The count supports **FIX_PROPOSAL and the brief's chosen range**. `12 → 11 at best` remains an unmeasured assumption (at least one row must move), but the brief already attributes it and quotes FIX_PROPOSAL §D's own admission that these are "a specification, not a measurement" (`NC1_FIX_PROPOSAL.md:177-178`). No averaging was done.

---

## `contradicted` (false)

1. **`strategy/AUTHOR_DECISIONS.md:135-136` (D7)** — *"One small paper-side fix owed: `REFS.md:66` uses a `G:` locator while `REFS.md:11` declares only `P`"*. **False at the cited line.** `papers/gated-read-batching/REFS.md:66` reads `| Self-RAG **conference venue** | … (**P:246**) … |` — it uses **`P:`**, the declared locator; the only `G:` locator in the file is at **`REFS.md:68`** (`G:49-51`), and `REFS.md:15` documents `G:`. A human told to fix `:66` finds nothing to fix there. The error is **inherited verbatim from `strategy/PUBLISH_PACKAGE_MANIFEST.md:233-234`** ("`REFS.md` uses a `G:` locator at `REFS.md:66`"), which is why the brief's citation to `:232-237` checks out as a citation while the fact does not check out against the paper. (`REFS.md:11` declaring only `P` is correct.)

## `overstated` (true but stronger than the evidence)

1. **`strategy/AUTHOR_DECISIONS.md:103-104` (D6)** — *"Prefer the wider FIX_PROPOSAL range … because it **enumerates** all six rows"*. `NC1_FIX_PROPOSAL.md:138-141` **states the count** ("Six of twelve rows currently resolve to nothing") but does **not name** the six rows; the enumeration (B1/B2/B4, E1, E4, E5) lives in `NC1_UNBLOCK.md:126-130`. The recommendation is still correct; the stated reason is not. Low consequence because the brief cites the list separately.

## `not_reproduced`

None. The one candidate (the `REFS.md:66` G: locator) reproduced as a definite **contradiction**, reported above, not as an inability to check.

## `unverified` (budget / access)

- The **gate hit counts** (1031 on the 1,570,243 B corpus; 4 on `tools/trace.ts`) were read from `NC1_UNBLOCK.md:133-135`/`:189` but **not independently re-measured** — no gate scan or `tsc` was run in this bound.
- The **21-file `src/` closure** and the **19× TS2307 / 4-failing-assertions** measurements (`NC1_UNBLOCK.md:104-115`, `NC1_FIX_PROPOSAL.md:121-123`) were not re-run.
- The corpus byte size was not re-`stat`ed against the pinned copy in `AGENTS.md`.

## Blocked-lines check (D requirement) — PASS

Every "Blocked until answered" names work that depends on its decision: D1 → #6 manuscript/package + artifact slot; D2 → lead manuscript + D7 + standalone-run unknown (`LEAD_PACKAGE.md:273-275`); D3 → #8 package + comparison form; D4 → explicitly nothing critical (**not** overstated); D5 → #14 package slot + triage item (`LEAD_PACKAGE.md:102` = 823 lines / 36 hits); D6 → NC1 manuscript/package + stale `12 automated` (`NC1_FIX_PROPOSAL.md:163-166`); D7 → ship list / `NEVER_SHIP` / gate total (`PUBLISH_PACKAGE_MANIFEST.md:493`) + #7 manuscript. No blocked line names work already done.

## C. Settled decisions — PASS

The brief's *Already settled* section (`:142-151`) states the licence posture (PolyForm Noncommercial 1.0.0 / CC BY 4.0 / Consonance proprietary-closed), no copyright registration, and the code-agnostic release policy as **decided**, and treats the three documents that frame them as open as **stale framing, recorded not raised**. None of D1–D7 presents any of them as open; `PUBLISH_PACKAGE_MANIFEST.md:497`'s "author's call" is recorded as stale, not raised. Not contradicted.

## Red→green

Method `scratch/uver17/cite_check.py` (asserts an expected substring at a given line). On a copy of `NC1_FIX_PROPOSAL.md:140` it returned **GREEN**; after altering `12 → 6 at worst` to `12 → 99 at worst` in the scratch copy it returned **RED** (exit 1). The checking method can fail.

## F. Counts

`strategy/AUTHOR_DECISIONS.md` = **166 lines**; **10** `^#` headings; **7** `^## D[1-7] ` decision headings.

## Verdict

`partial`: the brief is decision-usable and its disputed D6 number is the one to keep, but before a human acts, correct `AUTHOR_DECISIONS.md:135-136` (`REFS.md:68`, not `:66`, carries the `G:` locator; no fix is owed at `:66`) and soften `:103-104` ("enumerates" → "states the count of six, listed in `NC1_UNBLOCK.md:126-130`").
