# TMLR residue measurement — one rule set, both variants

**Date:** 2026-10-18 · **Unit:** UFIXTMLR6 · **Authority for the defect:** `strategy/VERIFICATION_REPORT_TMLR5.md`
(independent verifier **VUTMLR5**), §5 and the verdict tables.

**What this file replaces.** `UTMLR5` justified its second clearance with the sentence *"residue
`private-doc-name` 2, `private-repo-word` 1 — everything else 0 — equal the previously approved
`UTMLR2` baseline."* VUTMLR5 contradicted that and this unit confirms the contradiction. The
replacement statement is §4 below. **No `.tex` file was touched to produce it** — every number here is a
measurement of artifacts that already existed.

## 1. The rule set — one set, applied byte-identically to both files

21 rules, taken verbatim (by `ast.literal_eval` of the `SWEEP` assignment) from
`scratch/utmlr5/build.py:172-193`, the recipe the variant was actually built with.

| category | regex |
|---|---|
| `author-name` | `Aswin\|Kalugasala\|Moorthy\|Ram[ -]K\b` |
| `affiliation` | `Independent researcher` |
| `email` | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` |
| `orcid` | `orcid\|ORCID\|\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b` |
| `zenodo-doi-pending` | `[Zz]enodo\|DOI pending` |
| `repo-host` | `[Gg]it[Hh]ub\|gitlab\|GitLab\|research-publish-packages\|Aswin-Ram-K` |
| `private-harness` | `DeepSeek\|deepseek-v\|step-5-preview\|mimo-v2` |
| `host-name` | `GX10\|gx10-163b\|GB10` |
| `commit-sha` | `\b(?:ad301ae\|907fa39)[0-9a-f]*\b` |
| `long-hex` | `\b[0-9a-f]{40,64}\b` |
| `private-path` | `evals/\|tools/typed-channel\|harness/\|strategy/\|docs/\|scratch/\|orchestration/\|reserach extarctor\|/home/` |
| `private-doc-name` | `DECIDER_STACK_DECISION\|DECIDER\_STACK\_DECISION\|DECIDER\_TIER\|paper-candidates record\|experiment-learnings record\|evidence record :\|internal checklist` |
| `private-repo-word` | `target repository\|source repository\|read-only target\|source experiment tree\|the target\b` |
| `dated-decision` | `author decision\|2026-10-15` |
| `preprint-word` | `[Pp]reprint\|[Pp]re-print` |
| `url` | `https?://[^\s}\\]*` |
| `doi-literal` | `10\.[0-9]{4,}/[^ ,}\s]+` |
| `analysis-json` | `analysis\.json` |
| `commit-word` | `\bcommit\b` |
| `digest-hex-word` | `sha256` |
| `git-word` | `\bgit\b` |

**Why this set and not `scratch/utmlr2/evidence.json`'s.** The two pattern sets *do* reconcile. The
extended `private-doc-name` rule above is not an `UTMLR5` invention: it is already present, character for
character, in the `UTMLR2` toolchain at `scratch/utmlr2/fix_tmlr2.py:77`, and again at
`scratch/utmlr5/fix_tmlr25.py:77`. What differs is only *which script's output the evidence file
records*: `scratch/utmlr2/evidence.json` was written by `scratch/utmlr2/make_tmlr2.py:277`, whose
`private-doc-name` rule is the shorter `DECIDER_STACK_DECISION|DECIDER\_STACK\_DECISION|DECIDER\_TIER`
— it has no `internal checklist` alternative. So this is one reconciliation, not two incomparable sets:
the same 21 rules, applied to both finals.

## 2. Literal command and raw output

```bash
cd "/home/zer0null/reserach extarctor"
python3 - <<'PY'
import ast, re, pathlib
SWEEP=None
for node in ast.parse(pathlib.Path("scratch/utmlr5/build.py").read_text()).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0],"id",None)=="SWEEP":
        SWEEP=ast.literal_eval(node.value)
files={"UTMLR2":"scratch/utmlr2/tmlr/main.tex","UTMLR5":"scratch/utmlr5/tmlr/main.tex"}
for tag,p in files.items():
    lines=pathlib.Path(p).read_text(errors="replace").splitlines()
    for name,pat in SWEEP:
        rx=re.compile(pat)
        hits=[(i+1,rx.search(l).group(0)) for i,l in enumerate(lines) if rx.search(l)]
        print(tag, f"{name:22s}", len(hits), hits[:8])
PY
```

```
category                UTMLR2  UTMLR5  delta
author-name                  0       0  +0
affiliation                  0       0  +0
email                        0       0  +0
orcid                        0       0  +0
zenodo-doi-pending           0       0  +0
repo-host                    0       0  +0
private-harness              2       2  +0
host-name                    0       0  +0
commit-sha                   0       0  +0
long-hex                     0       0  +0
private-path                 0       0  +0
private-doc-name             2       2  +0
private-repo-word            1       1  +0
dated-decision               0       0  +0
preprint-word                0       0  +0
url                         13      13  +0
doi-literal                 12      12  +0
analysis-json                8       0  -8   <-- DIFF
commit-word                  0       0  +0
digest-hex-word              3       3  +0
git-word                     0       0  +0
```

Absolute counts, absolute hit positions:

| category | `scratch/utmlr2/tmlr/main.tex` (475 lines, sha256 `16a19a2d…`) | `scratch/utmlr5/tmlr/main.tex` (476 lines, sha256 `8d6b036c…`) |
|---|---|---|
| `private-harness` | **2** — L201, L325 (`mimo-v2`) | **2** — L202, L326 (`mimo-v2`) |
| `private-doc-name` | **2** — L119, L345 (`internal checklist`) | **2** — L120, L346 (`internal checklist`) |
| `private-repo-word` | **1** — L297 (`the target`) | **1** — L298 (`the target`) |
| `digest-hex-word` | **3** — L112, L407, L418 (`sha256`) | **3** — L113, L408, L419 (`sha256`) |
| `url` | **13** (all `\bibitem`/inline public URLs) | **13** (same set, +1 line offset) |
| `doi-literal` | **12** | **12** |
| `analysis-json` | **8** — L142, L156, L157, L161, L259, L276, L281, L403 | **0** |
| every other category | **0** | **0** |

The single systematic difference is a **one-line insertion** early in the variant (475 → 476 lines), which
shifts every later hit by exactly +1. The hit *sets* are the same.

## 3. Are the two `private-doc-name` hits new, or newly matched?

**Newly matched. Decisively, not new residue.** Three independent lines of evidence:

1. **The same two hits are in `UTMLR2`'s own artifact.** Swept under the rule set of §1,
   `scratch/utmlr2/tmlr/main.tex` yields `private-doc-name` **2** at L119 and L345, both matched on the
   literal `internal checklist` — the same two sentences, one line earlier. `UTMLR5`'s build did not
   introduce them.
2. **Under `UTMLR2`'s narrower regex both files yield 0.** With
   `DECIDER_STACK_DECISION|DECIDER\_STACK\_DECISION|DECIDER\_TIER` (the rule at
   `scratch/utmlr2/make_tmlr2.py:277`), `scratch/utmlr2/tmlr/main.tex` → **0** and
   `scratch/utmlr5/tmlr/main.tex` → **0**. So `evidence.json`'s recorded 0 is exactly what that regex
   produces — on *both* files. The 0 is a property of the regex, not of the older artifact.
3. **The recorded 0 and the measured 2 are the same fact under two rules.** `scratch/utmlr2/evidence.json`
   → `residue_sweep_final.private-doc-name = {hits: 0, where: []}` is correct *for the rule that wrote it*.
   It is not a rival measurement of the same quantity.

**Do they matter?** Marginally, and not for anonymity. The matched text is the generic phrase
`internal checklist` — it names no repository, path, URL, person, host, or dataset. The disclosing
sentence is already carried openly in the prose (§6.2 / §F.3: "an internal working record states it for
one pass"); the phrase adds no identifier beyond that. So: no new identity leak, but the honest statement
is that the variant carries **two mentions of an internal working document**, and so did its predecessor.

## 4. The corrected statement

> Residue was re-measured on both TMLR variants under **one** rule set — the 21-rule `SWEEP` of
> `scratch/utmlr5/build.py:172-193`, which contains the extended `private-doc-name` alternative already
> present at `scratch/utmlr2/fix_tmlr2.py:77`. Absolute counts on `scratch/utmlr2/tmlr/main.tex` →
> `scratch/utmlr5/tmlr/main.tex`: `private-harness` 2 → 2, `private-doc-name` 2 → 2,
> `private-repo-word` 1 → 1, `digest-hex-word` 3 → 3, `url` 13 → 13, `doi-literal` 12 → 12,
> `analysis-json` 8 → **0**; every other category 0 → 0. The variant is therefore **no worse than its
> predecessor in any swept category and strictly better in one** (`analysis-json`, 8 hits removed), but
> it is **not at zero residue**: it retains 2 `private-harness` (`mimo-v2`), 2 `private-doc-name`
> (`internal checklist`), 1 `private-repo-word` (`the target`) and 3 `digest-hex-word` (`sha256`).
> The two `private-doc-name` hits are **pre-existing text that `UTMLR2`'s recorded sweep did not match**,
> not residue introduced by this variant: `scratch/utmlr2/evidence.json`'s recorded 0 comes from a
> `private-doc-name` regex without the `internal checklist` alternative, and that same regex returns 0 on
> both files.

**The correct framing is a re-derived, like-for-like comparison — not an "approved baseline".**
`scratch/utmlr2/evidence.json` is a *record of one earlier measurement*, produced by a script whose
rules were narrower; nothing in `strategy/TMLR_VERIFICATION.md` or `strategy/TMLR_VERIFICATION_2.md`
mentions `private-doc-name`, `private-repo-word`, or states any residue baseline, and **no approval
record for `scratch/utmlr2/**` exists anywhere in the workspace**. Calling it "approved" attributed an
authority that no document grants. The defensible claim is: *same counts as its predecessor, measured the
same way, with one category improved* — a comparison, not a clearance against a certified standard.

## 5. What can and cannot be concluded

**Can be concluded**
- Under one stated rule set, the two artifacts carry identical residue counts except `analysis-json`
  (8 → 0). Directly measured, hits listed above.
- The `private-doc-name` discrepancy between the `UTMLR5` claim and `scratch/utmlr2/evidence.json` is a
  **pattern-set mismatch**, not a regressed scrub: the two hits exist in the `UTMLR2` artifact too.
- The counts themselves (`2`, `1`) reproduce; only their provenance as a "baseline" did not.
- `tmlr.sty`'s runtime `\setcitestyle{authoryear,round,...}` call is at **line 21**, not 20
  (`grep -n`: `15:\RequirePackage{natbib}`, `21:\setcitestyle{...}`; line 20 is the comment
  `% modification to natbib citations`). VUTMLR5 found this; it is corrected in the UTMLR5 records.

**Cannot be concluded**
- That `UTMLR2`'s artifact was ever approved, certified, or signed off as a residue standard. It was not.
- That residue is zero, or "everything else 0". It is not: 8 hits remain across 4 categories.
- That the variant is *anonymous*. This sweep bounds string residue in one source file. It says nothing
  about images, embedded fonts, annotations, stylometry, rephrased self-citation, or repository history
  (see `strategy/VERIFICATION_REPORT_TMLR5.md` §4 for the same bound on the PDF).
- That `private-harness` 2 (`mimo-v2`) or `digest-hex-word` 3 (`sha256`) are harmless — they are
  non-identifying by inspection but were never adjudicated by a verifier as acceptable.
- That any category omitted from a sweep is clean. `analysis-json` was never in `UTMLR2`'s recorded final
  sweep at all, which is why its 8 occurrences went unremarked until this measurement.

## 6. Containment

No `.tex` file, paper, `tools/package/**` file, verifier record, or released archive was written by this
unit. Before and after sha256, identical:

```
16a19a2d7e3fccdf9acef8d9a9affd328cf38ae9fb252be5f81edc24790e6b7f  scratch/utmlr2/tmlr/main.tex
8d6b036c23e4195e9119f67d2a7493831e836bfd68a9a2d73849eecdfbbf0fd0  scratch/utmlr5/tmlr/main.tex
```

---

## UTMLR6 — DOI residue measurement (appended 2026-10-18)

Source: `papers/encoder-crossover-190/submission/main.tex`, 84,786 B, sha256
`1468b61e5baf1a2dc110e5612b70c9d83adc0a91e3101a9fe5b5cfdac6294c6b` (reproduces the UTMLR6 card exactly).

| literal | source | anon | pass1 | pre-scrub | final |
|---|---|---|---|---|---|
| `10.5281/zenodo.23463945` | 3 | 3 | 3 | 3 | **0** |
| `10.5281/zenodo.23463944` | 1 | 1 | 1 | 1 | **0** |
| `10.5281` (any) | 4 | 4 | 4 | 4 | **0** |
| `Zenodo` (case-insensitive) | 7 | 7 | 7 | 7 | **0** |

Rule counts (**absolute**, from the built `scratch/utmlr6/build.py` and its run, recorded in
`scratch/utmlr6/evidence.json`): SCRUB3 rules 1–7 → 1/1/1/1/1/1/1; SCRUB4 rules 1–3 (re-anchored
pass-1 rules) → 1/1/1; SCRUB4 rules 4–5 (safety net, expected 0) → 0/0. Frozen chain:
`make_tmlr26` applied **68** literal replacements with **12** expected-1 anchors matching 0 (the stale
pass-1 set); `fix_tmlr26` reported **3** rule misses — two genuine, re-anchored by SCRUB3 rules 3 and
7, and one `n=2` duplicate match applied to both occurrences, as UTMLR5 recorded.

**Honest scope note.** These counts are UTMLR6's **23-rule** sweep (UTMLR5's 20 rules plus
`zenodo-word`, `doi-pending`, `doi-5281`, `affiliation`, `doi-literal`). A like-for-like re-run of the
21-rule set used by UFIXTMLR6 (correction C1 above) was **not** performed, so this section neither
restates nor contradicts the C1 figures. UTMLR6's non-zero categories: `doi-literal` 12 (all
third-party cited works), `url` 13 (all third-party), `private-harness` 2 (`mimo-v2`),
`private-doc-name` 2 (`internal checklist` ×2), `private-repo-word` 1 (`the target`),
`digest-hex-word` 3 (`sha256`) — matching the predecessor artifact, which is byte-identical to UTMLR6's.
