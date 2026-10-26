# VERIFICATION REPORT 7 — unit UVER7 (independent verifier)

**Scope:** the 7 drafted files in `strategy/licence-templates/` (author unit **ULIC2**), with priority on
the deployable licence text in `RELEASED-PIECE/LICENSE`.

**Verdict: `pass-with-corrections`.** The licence text is byte-identical to upstream and complete; the
three load-bearing clauses say what ULIC2/UCODE1/UTS1 claimed. Three corrections are recorded — **two
stale statements inside the templates themselves** (`C1`, `C2`) and one target-integrity observation
(`C3`) that does not touch the licence. None requires re-drafting the PolyForm text.

**Worst-outcome check (the reason this unit exists): NOT triggered.** There is no corrupted, truncated
or subtly edited licence text. The drafted body is bit-for-bit the upstream text.

---

## Contradicted items (with replacements)

### C1 — `TRADE-SECRET-NOTICE.md` still declares the audit it cites to be missing (stale, false)
`strategy/licence-templates/TRADE-SECRET-NOTICE.md:44-47` reads:

> **Gap (recorded, not filled):** at the time this template was drafted,
> `strategy/TRADE_SECRET_AUDIT.md` was **not present on disk** in this workspace. …

That is now **false**. The audit exists and the pointer at line 41 resolves. Verified:
`stat` → **507 lines / 48,851 bytes / mtime 2026-10-15 15:31:34** (exactly the figures PLACEMENT §5.3
claims). UFIX5 corrected this fact **in `PLACEMENT.md` §5.3 but not in the file that carries the
pointer** — so the template still reads as though its legal basis is absent.

**Replacement (drop the stale block, or reword to):**

> **Legal basis supplied.** `strategy/TRADE_SECRET_AUDIT.md` is present on disk in this workspace
> (unit UTS1; 507 lines / 48,851 bytes; written 2026-10-15 15:31:34). It is the citation for the
> position above. Its findings are not imported here; no legal proposition is asserted in this file.

Severity: **medium-low.** It is a statement *about the workspace*, not licence terms, so it cannot
mislicense anyone — but it is wrong as written and it undercuts the notice's own legal basis in a file
intended to be deployed.

### C2 — `PLACEMENT.md:96` cites SUPERSEDED line numbers that are stale by 10
`PLACEMENT.md:96` claims the memo's §5.1 and §6 Stage 0 are "marked **SUPERSEDED** in place
(`:423`, `:590`)". The markers exist and say what is claimed, but they are at **`:433` and `:600`**
(verified: `grep -c SUPERSEDED` = **2**, at lines 433 and 600). The citation is off by exactly 10 —
the ERRATA block added at the top of the memo shifted them.

**Replacement:** `:433`, `:600`. Severity: **low** (cosmetic, but it is a citation a reader will follow).

### C3 — "nothing changed" in `/home/zer0null/Duval` is false for `.git/**`, true for the worktree
The narrow claim is **confirmed**: `/home/zer0null/Duval/LICENSE` md5 **`eb1e647870add0502f8f010b19de32af`**,
mtime **2026-09-28 12:30:24**, 34,523 bytes — unchanged, as two prior units recorded.

The broad claim ("nothing changed") is **not** supported:

| Probe | Result |
|---|---|
| Duval worktree (excl. `.git`) modified since 2026-10-01 | 28,380 files |
| **Newest worktree file** | `docs/migration/DIRECTIVE_2026-10-15.md` — **2026-10-15 13:15:11** |
| `.git/index`, `.git/HEAD` | 2026-10-15 12:51:58 |
| **`.git/objects/pack/pack-5eb3f8d4….pack` + loose objects** | **2026-10-15 15:32:23** ← *inside the build window* |

So: the **working tree saw no write during the licence window** (newest worktree file 13:15:11, ~2h15m
before ULIC2 drafted at 15:29), which is consistent with ULIC2's "never modified the target". But
**git object store writes did occur at 15:32:23 today**, i.e. after that. AGENTS.md forbids *git state
changes* in a target. **Attribution is unknown** — I cannot tell from mtimes whether a workspace unit ran
a `git` command in Duval (an auto-gc repack would look exactly like this) or whether an unrelated
concurrent process touched a repo that is clearly under active multi-branch development. **Not a licence
defect; reported for the main session to route.** I ran no `git` command in the target.

---

## Priority 1 — the PolyForm text is complete and unmodified

**Re-fetched myself**, live, from `https://polyformproject.org/licenses/noncommercial/1.0.0.txt`:
HTTP **200**, **4,563 bytes**, sha256 **`ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`**.

Drafted body = `strategy/licence-templates/RELEASED-PIECE/LICENSE` **lines 10–140** (from
`# PolyForm Noncommercial License 1.0.0` through `of your licenses.`).

| Comparison | Result |
|---|---|
| upstream size | **4,563 bytes** |
| drafted body size | **4,563 bytes** |
| sha256 (both) | **`ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`** |
| `diff -u upstream drafted-body` | **empty output, exit 0** |
| `cmp upstream drafted-body` | **IDENTICAL** |
| non-ASCII / BOM in body | none (first bytes `23 20 50` = `# P`) |
| CR characters / trailing whitespace | none in either |

Verbatim `diff -u` result: *(no output)* — the upstream file does not exist in the diff, so the two
inputs are byte-for-byte equal. **ULIC2's byte-identical claim is CONFIRMED, and the 4,563-byte figure
is CONFIRMED.**

**The one subtle-edit risk is closed by construction:** the comparison is over the exact byte range
declared by the draft's own delimiters, and I proved my comparison is **sensitive, not vacuous** — with a
single `License`→`Licence` character swap applied in memory (no file touched) the same `diff` reports
**DIFFERS**, while the unmutated body reports **IDENTICAL**. A silently edited body cannot pass this test.

### Section-by-section completeness checklist (drafted vs upstream)

Both files carry the title `# PolyForm Noncommercial License 1.0.0` plus the canonical URL line. Upstream
`## ` headers, in order, are the 15 below; **every one is present in the drafted body, in the same order,
byte-identical**:

| # | Section | Present? | Notes |
|---|---|---|---|
| 0 | Title + canonical URL | ✅ | `<https://polyformproject.org/licenses/noncommercial/1.0.0>` |
| 1 | `Acceptance` | ✅ | strict obligations + conditions |
| 2 | `Copyright License` | ✅ | **the copyright grant** ("The licensor grants you a copyright license …") |
| 3 | `Distribution License` | ✅ | |
| 4 | `Notices` | ✅ | **the Required Notice requirement** lives here |
| 5 | `Changes and New Works License` | ✅ | |
| 6 | `Patent License` | ✅ | **Patent terms present** |
| 7 | `Noncommercial Purposes` | ✅ | "Any noncommercial purpose is a permitted purpose." |
| 8 | `Personal Uses` | ✅ | **prong (a)** — see Priority 2 |
| 9 | `Noncommercial Organizations` | ✅ | see Priority 2 |
| 10 | `Fair Use` | ✅ | |
| 11 | `No Other Rights` | ✅ | |
| 12 | `Patent Defense` | ✅ | |
| 13 | `Violations` | ✅ | 32-day cure |
| 14 | `No Liability` | ✅ | |
| 15 | `Definitions` | ✅ | licensor / software / You / Your company / Your licenses / Use |

**Missing sections: none.** Flagged items that are **not** missing and **not** author failures:

- **`END OF TERMS AND CONDITIONS` marker — absent, and absent from upstream too.** PolyForm
  Noncommercial 1.0.0 has **no such marker** (that marker belongs to Apache-2.0). A faithful copy
  *cannot* contain it. Recorded as `not_reproduced`, not as a defect. The draft substitutes its own
  explicit delimiters (`--- The licence terms begin … ---` / `--- The licence terms end … ---`), which is
  a clearer boundary than the upstream file has.
- **`Contributions` terms — absent, and absent from upstream too.** PolyForm NC 1.0.0 contains **no**
  contribution clause. Its absence is faithful, not truncation. (The draft handles the contribution
  question separately, in prose, in `RELEASED-PIECE/CONTRIBUTING.md`.)
- **"Preamble" — PolyForm 1.0.0 has no separately titled preamble.** The title/URL/`Acceptance` triad is
  the whole of it upstream; nothing is missing.

### Required Notice line

The licence's `Notices` section obligates anyone redistributing to pass on "copies of any plain-text lines
beginning with `Required Notice:` that the licensor provided", and gives the form by example:
`> Required Notice: Copyright Yoyodyne, Inc. (http://example.com)`.

The draft supplies, as **line 1** of `RELEASED-PIECE/LICENSE`:

```
Required Notice: Copyright <YEAR> <COPYRIGHT HOLDER>
```

**Correct in form and position** — a plain-text line beginning `Required Notice: Copyright `, above the
licence terms, so it travels with the software as the clause requires. Its placeholders are unfilled
(recorded below, gap a), which is the author's fill-in step, not a drafting error. Note the draft's own
`Notices` section retains the upstream `Yoyodyne` example verbatim, which is correct — that line is
upstream's illustrative example, not the project's notice.

---

## Priority 2 — the `Noncommercial Purposes` definition (two decisions depend on it)

### 2.1 Prong (a) covers at-home/hobby use — **CONFIRMED**

`## Personal Uses` (drafted `RELEASED-PIECE/LICENSE:65-71`, byte-identical to upstream):

> Personal use for research, experiment, and testing for
> the benefit of public knowledge, personal study, private
> entertainment, hobby projects, amateur pursuits, or religious
> observance, without any anticipated commercial application,
> is use for a permitted purpose.

**Is "somebody running it at home for themselves as a tool" inside it? YES.** Three independent limbs
reach it: **`private entertainment`**, **`hobby projects`**, and **`amateur pursuits`** — and "personal
study" for the study use-case. The user is an individual, at home, for their own benefit, with no
commercial application. Reinforced by `## Noncommercial Purposes`: *"Any noncommercial purpose is a
permitted purpose."* The conclusion **UCODE1 and UTS1 relied on is sound.**

### 2.2 The anticipated-commercial-application exclusion — **CONFIRMED, and it excludes a business evaluating in order to buy**

The exclusion is the qualifier **inside the same `Personal Uses` clause**:

> … or religious observance, **without any anticipated commercial application**, is use for a permitted
> purpose.

Read with the clause list as a whole, a for-profit business evaluating in order to buy is **excluded**:

1. Its evaluation has an **anticipated commercial application** → outside `Personal Uses`.
2. It is not a "noncommercial purpose" → outside `## Noncommercial Purposes`.
3. A for-profit company is not one of the `## Noncommercial Organizations` categories → outside that clause.

So the permitted purposes are exhausted and the use is not licensed. **`COMMERCIAL.md:14-17` and the
Case B README paragraph are right to say there is no free commercial evaluation.**

**One honest caveat (`overstated`, see below):** the licence never uses the word *"evaluation"* and has no
standalone "commercial use is prohibited" clause. The result is an **inference** from the
"anticipated commercial application" qualifier plus the exhaustive category list — a sound inference, but
it should not be presented to a reader as quoted licence text.

### 2.3 The `Noncommercial Organizations` clause and "regardless of funding" — **CONFIRMED, verbatim, and stronger than claimed**

`## Noncommercial Organizations` (drafted `RELEASED-PIECE/LICENSE:73-80`):

> Use by any charitable organization, educational institution,
> public research organization, public safety or health
> organization, environmental protection organization,
> or government institution is use for a permitted purpose
> regardless of the source of funding or obligations resulting
> from the funding.

**All six categories are present** — charitable organization, educational institution, public research
organization, public safety or health organization, environmental protection organization, government
institution. The phrase **"regardless of the source of funding"** **exists**, and goes further than the
claim: it says *"regardless of the source of funding **or obligations resulting from the funding**"* — so
a university lab on industry money, or a public research body under a commercial grant, is still covered.
**This is the mitigation for the O-1 cost, and it is real and unqualified in the text.**

---

## Priority 3 — the other templates

### `PROPRIETARY-LICENSE.txt` — **CONFIRMED coherent proprietary notice**
All five required elements present: copyright line (`:1`), all rights reserved (`:1`), no permission
granted (`:3`, `:8-10`, `:36` "This notice is not a licence."), confidentiality (`:3`, `:5-6`,
`:21-23`), trade-secret assertion (`:19-23`), plus restricted access (`:25-31`) and
`DO NOT REDISTRIBUTE. DO NOT PUBLISH.` (`:38`). Used as `LICENSE`, replacing AGPL, per PLACEMENT §2.

### AGPL sweep — **CONFIRMED: no AGPL licence text remains in `strategy/licence-templates/**`**
`grep -rn "GNU AFFERO GENERAL PUBLIC LICENSE\|GNU Affero\|AGPL-3.0"` over all 7 files returns **only 4
lines, all in `PLACEMENT.md`, all prose**:
`:28-29` (documenting that the *target's* `LICENSE` is AGPL, quoting its 5-word title as evidence),
`:30-31` ("**Replace it, never amend it** … 'AGPL + no commercial use' is internally contradictory"),
`:32` ("no AGPL file may remain in any repository that is made public"), `:108` (listing what the unit did).
**No AGPL body text — no terms, no grant, no warranty disclaimer — appears anywhere.** The one place the
AGPL string itself appears is a 5-word title quoted inside a sentence that instructs deletion.

*Sensitivity control:* the same pattern matches **1** time against Duval's real AGPL `LICENSE`, so the
grep is not vacuous.

### `PLACEMENT.md` — **CONFIRMED (order and warning), with stale citation C2**
- **Order of operations is right.** §3: (1) fill placeholders, (2) **replace the licence in the private
  main repo first, while still private**, (3) put released-piece files in place **before that repo goes
  public**, (4) **only then** make public, (5) date the release and keep the exact text. Correct: the
  irreversible act (publication under a licence) is last, and step 2/3 beat it.
- **Replace-before-public permanence warning is present.** §3's boxed `⚠️ The one irreversible step`:
  *"Once a version is published under a licence, that grant is **permanent for that version** and cannot
  be withdrawn … Publishing first and fixing the licence afterwards does not undo the grant that
  publication made."* Also correct that it cannot withdraw an earlier grant.
- **§5 items 3 and 4 now read as resolved/on-disk, not open.** ✅ Item 3: *"`strategy/TRADE_SECRET_AUDIT.md`
  **now exists on disk**"* with the corrected figures. ✅ Item 4: *"Reconciliation … — **RESOLVED**"*,
  citing the UMEMO1 ERRATA and the two-tier structure. I verified the underlying facts: the ERRATA block
  exists at `CODE_LICENSING_STRATEGY.md:9`, the two SUPERSEDED markers exist (at `:433`, `:600` — see C2),
  and the audit file exists at the stated size and mtime.
- **§1 destination table is right:** 7 drafts → 7 declared destinations; `RELEASED-PIECE/LICENSE` goes to
  each released piece's root as `LICENSE`; nothing is copied by this workspace.

### `RELEASED-PIECE/CONTRIBUTING.md` — **CONFIRMED**
- **Hygiene rule stated.** `:39-50` "The hygiene rule for the author": *"**Integrate by re-implementation.**
  Never by copy-paste. **Never merge contributor patches or pull requests.**"* and *"**Never accept a patch
  into the tree.** Not even a one-line fix, and not even with attribution — the licence travels with the
  expression."* The reason is stated correctly (`:27-29`): copied NC code cannot lawfully be included in a
  paid commercial licence, so the commercial tier would silently stop covering part of the codebase. That
  is the right rationale, and the ideas/expression distinction at `:31` is correctly drawn.
- **Name/logo reservation present.** `:52-57`: the name and logo "are not licensed", nothing in the file or
  the code licence grants any right to them, and "Trademark is a right separate from copyright". Correct —
  a code licence conveys no trademark rights, and the file says so without asserting a registered mark.

### `TRADE-SECRET-NOTICE.md` — **CONFIRMED on the point asked, with stale text C1**
- **Legal basis points at `strategy/TRADE_SECRET_AUDIT.md`** (`:41`), and the notice **does not assert law
  on its own** — it states practice/hygiene obligations and defers the legal basis to the audit. ✅
- **But** the adjacent gap block (`:44-47`) still says that audit is not on disk. **False — see C1.**

---

## Priority 4 — gaps ULIC2 recorded and did not fill

**(a) `<CONTACT>` commercial address is unfilled — CONFIRMED, correctly left as a gap.**
Occurrences: `PLACEMENT.md:21,40-41,78`; `README-PARAGRAPHS.md:7,32,53`; `COMMERCIAL.md:33`
(`**Contact:** \`<CONTACT EMAIL OR URL — author to fill in>\``); and the other placeholders
(`<YEAR>`, `<COPYRIGHT HOLDER>`, `<PROJECT NAME>`) across `PROPRIETARY-LICENSE.txt:1,6,10`,
`RELEASED-PIECE/LICENSE:1,3`, `README-PARAGRAPHS.md:16,38`. The strategy genuinely does not supply the
address, and the gap is recorded rather than invented. `PLACEMENT.md:42` already requires that nothing
ship with a visible angle-bracket placeholder. **Correctly left as a gap.**

**(b) Academic-carve-out README sentence — recommended but unworded. CONFIRMED as a real gap. My view: DRAFT IT NOW. It is MATERIAL.**

The gap is visible in three places: `PLACEMENT.md:100-101` (§5.5, "recommended but not worded … no wording
has been invented") and `README-PARAGRAPHS.md:48-52` ("§6 (rule 6) recommends naming it deliberately; this
draft does not add such a sentence because `CODE_LICENSING_STRATEGY.md` does not fix its wording — **gap,
left for the author**"). So ULIC2's record is accurate and it did not paper over it.

**Assessment — the omission is material, and it is asymmetric against the author.** The licence grants
these institutions free use *silently*, in the `Noncommercial Organizations` clause. Nothing in the
release makes that visible. The Case B README paragraph instead leads with *"**Any commercial use requires
a paid commercial licence**"* and qualifies the free grant as *"personal, hobby, research and other
**noncommercial** purposes"*. A university research group, a public lab, or a hospital reading that
reasonably concludes that **they** — institutional, often externally funded users — are on the paid side,
and many will never take the step of parsing the licence to discover otherwise. University
tech-transfer/procurement review will often read "noncommercial" as a blocker and route the author to a
licence negotiation that need never happen.

That is the worst of both worlds, and it bears directly on why the author chose this licence: adoption,
citation and demonstrated impact (the O-1 route depends on it). The author therefore **pays the full
adoption cost of a non-commercial licence and collects none of the benefit the licence deliberately
extends to exactly the audience that would otherwise be blocked.** The remedy costs **one sentence and
carries no legal risk**, because the licence's own words supply it in full. Drafted recommendation:

> Academic, public-research, public-health, public-safety, environmental and government institutions may
> use this software **regardless of the source of funding**: the PolyForm Noncommercial License 1.0.0
> permits use by any charitable organization, educational institution, public research organization,
> public safety or health organization, environmental protection organization, or government institution,
> *"regardless of the source of funding or obligations resulting from the funding."*

**Recommendation to the main session: this should be drafted now, not deferred.** It closes a material gap
using quoted licence text with no invented wording — the stated reason for deferral (the strategy fixes no
wording) does not survive contact with the fact that the licence supplies the wording verbatim.

The other recorded gaps are correctly left: the paid commercial agreement is out of scope and needs the
legal review §8 recommends, and "not legal advice" is stated.

---

## The four lists

**`contradicted`** (wrong as written; replacement given)
1. `TRADE-SECRET-NOTICE.md:44-47` — declares `strategy/TRADE_SECRET_AUDIT.md` absent; it exists (507 lines /
   48,851 bytes / 2026-10-15 15:31:34). → replacement in C1.
2. `PLACEMENT.md:96` — SUPERSEDED markers cited at `:423`, `:590`; actual `:433`, `:600`. → replacement in C2.
3. `/home/zer0null/Duval` "nothing changed" — false for `.git/**` (objects written 2026-10-15 15:32:23);
   true for the worktree and for `LICENSE`. → scoped statement in C3.

**`overstated`** (defensible, but stated more strongly than the text supports)
1. "No free commercial evaluation" is an **inference**, not a quoted term: the licence says neither
   "evaluation" nor any general commercial-exclusion clause. Sound, but present it as reasoning.
2. `README-PARAGRAPHS.md:37-38` labels the notice line *"Placeholder-free"* and then prints
   `<YEAR> <COPYRIGHT HOLDER>`. Means "once the placeholders are filled"; the label reads as a
   contradiction with the line beneath it.
3. `PLACEMENT.md` §4 lists `RELEASED-PIECE/LICENSE` among the places the name/logo is reserved. The
   reservation *is* in that file, but PolyForm's `Notices` clause obliges redistributors to carry only the
   terms/URL and `Required Notice:` lines — so the reservation is **not** propagated to forks by the
   licence. Low severity: an unregistered trademark right does not depend on the licence repeating it.

**`not_reproduced`** (coverage limits — *not* author failures)
1. `END OF TERMS AND CONDITIONS` marker — **absent from upstream PolyForm 1.0.0**; no faithful copy can
   contain it. The checklist item is inapplicable to this licence.
2. `Contributions` section and a separately titled `preamble` — **neither exists upstream**; their absence
   is faithful.
3. Deployment into a real repository (fill placeholders → replace → publish) — could not be exercised
   without writing to a target, which is prohibited by design.

**`unverified`**
1. Attribution of the Duval `.git` writes at 2026-10-15 15:32:23 — mtimes alone cannot distinguish a
   workspace unit's `git` command from an unrelated concurrent process on a very active repo.
2. Byte-stability of the upstream URL over time — verified only for the fetch made 2026-10-15 (HTTP 200);
   a future upstream revision would not match this hash.
3. Whether the upstream `.txt` is the canonical rendering *for all time* vs. the site's HTML page — the
   draft cites both; the `.txt` I fetched is what the draft matches exactly.

---

## Target integrity (read-only discipline)

- `/home/zer0null/Duval/LICENSE`: md5 **`eb1e647870add0502f8f010b19de32af`** ✅ (matches both prior units),
  mtime **2026-09-28 12:30:24**, size 34,523 bytes ✅ **unchanged**.
- **No write of any kind was made to `/home/zer0null/Duval` by this unit.** I ran no `git` command in it;
  all probes were `stat`/`find`/`md5sum`/`grep` reads. No file was created, modified or deleted there.
- **This unit wrote exactly three files**, all declared: `strategy/VERIFICATION_REPORT_7.md`,
  `orchestration/units/UVER7.md`, `orchestration/handoffs/UVER7.json`.
- **I did not edit any template.** `strategy/licence-templates/**` was read only; the one mutation applied
  during the sensitivity test was applied **in memory via `sed` in a pipe**, never to disk.

## What would change my verdict

- **→ `fail`:** any byte differing from upstream in `RELEASED-PIECE/LICENSE:10-140` (none today); any
  missing upstream section (none); AGPL licence text appearing in a file intended to be deployed as a
  released piece's `LICENSE` (none); a deployed released piece bearing two licence files.
- **→ correction re-opened:** if a future edit to `RELEASED-PIECE/LICENSE` adds prose inside the
  `licence terms begin`/`end` delimiters, byte-identity must be re-run — the upstream comparison range is
  defined by those delimiters, so editing *inside* them silently breaks the guarantee. **The delimiters
  are load-bearing: any future editor must keep additions outside them.**
- **→ verdict upgrades toward `pass`:** C1, C2 and the three `overstated` items corrected; the academic
  sentence (Priority 4b) drafted; `<CONTACT>` filled.
- **→ integrity escalation:** if the main session can show the 15:32:23 `.git` writes came from a workspace
  unit, that is an AGENTS.md read-only violation independent of this licence work and belongs in
  `orchestration/VERDICTS.md`.
