# STYLE_COMPLIANCE.md — internal cleanliness & compliance pass on `encoder-crossover-190`

**Unit:** USTYLE1 · **Date:** 2026-10-15 · **Mode:** report only, nothing edited.
**Scope (source of truth):** `papers/encoder-crossover-190/MANUSCRIPT.md` — 877 lines (note: `submission/BUILD_NOTES.md:8`
claims 864 lines / 66,671 bytes; actual is **877 lines / 68,075 bytes** — the manuscript grew after the build).
**Cross-checked artifacts:** `CLAIMS.md`, `AVAILABILITY.md`, `GAPS.md`, `submission/main.tex` (445 lines, 80,780 bytes),
`submission/ABSTRACT.txt`, `submission/ABSTRACT_METADATA.txt`, `submission/METADATA.md`, `submission/BUILD_NOTES.md`,
and the on-disk released subset `repro/encoder-crossover-190/`.
**Method:** every pointer in `MANUSCRIPT.md` was extracted and resolved against the filesystem; every bibliography key
was cross-counted against `REFERENCES.bib`; every quantitative claim was re-spelled per artifact; absence claims were
made only after a negative grep. Exact quotes are given for every failure.

---

## CHECK 1 — Cross-reference resolution

### 1a. Manuscript-internal section pointers — all resolve

| item | location in `MANUSCRIPT.md` | verdict | action |
|---|---|---|---|
| `§1` | `:278`, `:812` | RESOLVES → `## 1. Introduction` (`:60`) | none |
| `§2` | `:22`, `:569`, `:669` | RESOLVES → `:114` | none |
| `§2.1` | `:24`, `:83`, `:95`, `:225`, `:246`, `:524`, `:677`, `:877` | RESOLVES → `:116` | none |
| `§2.2` | `:191` | RESOLVES → `:193` | none |
| `§3.2` | `:392` | RESOLVES → `:275` | none |
| `§3.3` | `:13` (×2), `:665` | RESOLVES → `:305` | none |
| `§3.4` | `:156`, `:460` | RESOLVES → `:349` | none |
| `§4.1`, `§4.2`, `§4.3`, `§4.5`, `§4.6`, `§4.7` | `:96`, `:100`, `:103`, `:105`, `:156`, `:336`, `:344`, `:345` | RESOLVE → `:389/:400/:451/:469/:479/:494` | none |
| `§5.1`, `§5.2`, `§5.3` | `:346`, `:444`, `:526` | RESOLVE → `:508/:528/:538` | none |
| `§6`, `§6.1`, `§6.2`, `§6.3`, `§6.4`, `§6.5` | `:52`, `:56`, `:106`, `:108`, `:110`, `:142`, `:226`, `:273`, `:347`, `:381`, `:726`, `:732`, `:817`, `:877` | RESOLVE → `:554/:556/:582/:655/:667/:687` | none |
| `(see §6.1)` | `:52` — the manuscript's only `(see …)` | RESOLVES | none |

### 1b. Pointers that FAIL

| item | location in `MANUSCRIPT.md` | verdict | action |
|---|---|---|---|
| `` `verify/recompute-claims.py` `` | `:797`, `:807`, `:827` | **FAILS — file absent from the named subset.** `repro/encoder-crossover-190/` has **no `verify/` directory**; the file exists only at `repro/encoder-crossover-190-SANITISED/verify/recompute-claims.py`. Quote `:797`: *"it carries the sealed fixture, `verify/recompute-claims.py` and the second labeller's `parse_fixture.py` and `compare.py`"* | ship `verify/recompute-claims.py` in `repro/encoder-crossover-190/`, or delete the three sentences |
| `` `harness/data/lint-report.json` `` | `:757` — *"recorded by the withheld harness (`harness/data/lint-report.json`); not part of the released set"* | **FAILS — file IS in the released set** at `repro/encoder-crossover-190/harness/data/lint-report.json` | fix the release boundary or the sentence |
| `PAPER_CANDIDATES.md:269` + quoted sentence | `:430` — *"(`strategy/PAPER_CANDIDATES.md:269`, `experiments/LEARNINGS.md:281`) states *"Every correction moved the affected arm DOWN."**" | **FAILS on content.** `strategy/PAPER_CANDIDATES.md:269` actually reads *"fires on three seeded copies (13/44/57 shared 8-grams) and stays silent over **152,000** training↔fixture"*. The quoted sentence appears (lowercase) only at `:37` inside an errata block | re-point to `:37`/`:271` or drop the line number |
| `experiments/LEARNINGS.md:281` | `:430` | **FAILS — path does not exist** in the workspace; the nearest copy is `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/docs/research/experiments/LEARNINGS.md`, whose `:281` reads *"every correction moved it *down* (0.3158 → 0.2947 → 0.2632)"* — not the quoted uppercase form | give the real root, and quote what is there |
| `strategy/PAPER_CANDIDATES.md:265` + `experiments/LEARNINGS.md:265` p-value encoding claim | `:766-767` — *"The p-value is written with a **typographic minus (U+2212)** in `strategy/PAPER_CANDIDATES.md:265` and `experiments/LEARNINGS.md:265` (`4.167e−09`)"* | **FAILS on content.** `PAPER_CANDIDATES.md:265` = *"0.2632; **majority-class control 0.4526**; shuffled-label 0.2316 (below the 0.2911 chance floor);"* — the p-value is at **`:267`**. `LEARNINGS.md:265` = *"… Paired McNemar: b=27, c=90, p=4.17e−09, **paired"* — `4.167e−09` appears **nowhere** in that file | correct both line numbers and the `4.167` spelling |
| `§F.3` | `:644`, `:649`, `:659` — *"`PAPER_CANDIDATES.md` §F.3 is not discharged"* | **FAILS — no such anchor.** `grep F\.3 strategy/PAPER_CANDIDATES.md` returns **0 hits**; that file references §F.3 only as an external ask (its `:37`) | name the document that actually carries §F.3, or drop the label |
| `EXP#12-typed-channel-comparison.md:95` | `:322`, `:396` — cited for the F1 threshold | **FAILS on name.** No file of that name exists; the released prereg is `repro/encoder-crossover-190/preregistration/EXP12-typed-channel-comparison-prereg.md` (the name given at `:759`/`:811`). Its `:96` is `## 6. Falsifiers`; the `:95` quote was not verifiable | unify to one filename |
| `docs/DECIDER_STACK_DECISION.md` §11.2 / §11.6 / `:415` / `:500` / `:494–495` | `:68`, `:118`, `:121`, `:126`, `:146`, `:154`, `:156`, `:669`, `:763` | **UNRESOLVABLE here** — target-repo document, absent from the workspace (also cited inconsistently as bare `DECIDER_STACK_DECISION.md` at `:118`/`:146`). The §11.6 block quote at `:123-129` therefore could not be verified | state the source root once in §7 |
| `DECIDER_TIER §2` | `:569` | **UNRESOLVABLE** — document never expanded, versioned or rooted | give a path |
| `analysis.json` | `:295`, `:314`, `:315`, `:319`, `:466`, `:487`, `:498` | **UNRESOLVABLE from the released set.** It is not in `repro/encoder-crossover-190/`, is not in the `:752-763` provenance table, and no containing path is given anywhere — yet most cited keys live in it | add its path to the released subset or the provenance table |

### 1c. Pointers that resolve — spot-verified content

| item | location | verdict |
|---|---|---|
| `REPORT.md:189` (`:8`, `:39`, `:42`, `:78`, `:775`) | `repro/encoder-crossover-190/results/REPORT.md:189` | VERIFIED verbatim (*"cannot be re-scored"*) |
| `REPORT.md:104` (`:315`, `:324`, `:775`) | `…/REPORT.md:104` | VERIFIED (`reproduces at 3 d.p. = **None**`) |
| `REPORT.md:85` (`:397`) | `…/REPORT.md:85` | VERIFIED (`F1 — fires when encoder accuracy < 0.6684`) |
| `REPORT.md:191` (`:561`) | `…/REPORT.md:191` | VERIFIED verbatim (latency quote) |
| `REPORT.md` §"Two things … NOT defects" (`:219`), §"A caveat that is not a defect" (`:301`) | `…/REPORT.md:281`, `:294` | RESOLVE (titles lightly paraphrased) |
| `REFS.md` §B3 (`:140`) | `papers/encoder-crossover-190/REFS.md:83` | RESOLVES |
| `experiments/second-labeller-190/EVIDENCE.md:309` (`:645`) | same, `:309` | VERIFIED (*"**It is not IAA.** One pass is a model."*) |
| `preregistration/…-prereg.md` (EXP#12) §1–§9 (`:812`) | `repro/encoder-crossover-190/preregistration/…:23,29,43,53,76,96,110,121,129` | RESOLVES — all nine headings exist |
| `strategy/licence-templates/RELEASED-PIECE/` (`:854`) | exists | RESOLVES |
| `papers/encoder-crossover-190/{CHECKLIST,OPEN_QUESTIONS,UNSOURCED_RETAINED,EVIDENCE_NOTES,CLAIMS}.md` (`:56`, `:142`, `:696`, `:731`, `:747`, `:786`, `:808`) | all exist | RESOLVE |
| fixture sha256 `076164ac…b4796` (`:259`, `:805`, `:219`) | consistent at `:259`, `:805` and in `AVAILABILITY.md:22` | RESOLVES |
| second-labeller set `{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json,PREREGISTRATION.md}` (`:760`) | all present under `repro/encoder-crossover-190/second-labeller/` | RESOLVE |
| B2 set `{RUN2.json,ROBUSTNESS.md,labelsB2.json,disagreementsB2.jsonl,metrics2.json,compare2.py}` (`:761`, `:820`) | all present under `experiments/second-labeller-190/` | RESOLVE |
| `src/**`, `kernel/**`, HF checkpoint ids, `tools/typed-channel/` (18 files) (`:762`, `:834`, `:838`, `:840-841`) | correctly labelled withheld-by-policy; `repro/encoder-crossover-190/harness/` contains **exactly 18 files** | RESOLVES as a *count*, but see Check 4 (the harness is not actually withheld) |

---

## CHECK 2 — Citation ↔ bibliography, both directions

| item | evidence | verdict | action |
|---|---|---|---|
| `REFERENCES.bib` entries | **13** `@…{key,}` entries | — | — |
| `\bibitem` in `submission/main.tex` | **13** | MATCHES `REFERENCES.bib` | none |
| Keyed in-text (backticked key in `MANUSCRIPT.md`) | **8 of 13**: `simmering2025modernbert` ×3 (`:165`, `:677`, `:869`), `zaratiana2024gliner` (`:199`), `zaratiana2025gliner2` (`:204`), `stepanov2025gliclass` (`:209`), `kostina2025llmtextclassification` (`:229`), `li2025smalllanguagemodels` (`:234`), `weller2025seqvsseq` (`:239`), `benayas2024comparative` (`:186`, `:874`) | RESOLVE | none |
| **Unkeyed** but prose-cited | **5 of 13**: `arxiv2602_06370` → arXiv `2602.06370` (`:146`, `:860`); `arxiv2512_12677` → `2512.12677` (`:150`, `:862`); `pride2309_03882` → arXiv `2309.03882` "PriDe" (`:154`, `:863`); `gcd2305_13971` → arXiv `2305.13971` (`:157`, `:864`); `source_decider_stack_2026` → `docs/DECIDER_STACK_DECISION.md` §11.6 + commit `ad301ae` (`:68`, `:118`, `:669`, `:867`) | RESOLVE by identifier only — no `\cite` key in text | mechanical, acceptable; note the paper is a **keyless** citation style in LaTeX (all 13 entries print as an uncited list) |
| Prose author-year citations with no backticked key | Simmering 2025 (`:168`), Benayas/Sicilia/Mora-Cantallops 2024 (`:184`), Kostina et al. 2025 (`:228`), Li et al. 2025 (`:232`), Weller et al. 2025 (`:238`), Zheng et al. (`:863`), Geng et al. (`:865`), Valdes Gonzalez (`:860`), Yousefiramandi & Cooney (`:862`) | each maps to exactly one of the 13 entries | none |
| Third-direction check | no `REFERENCES.bib` key is cited **only** in `CLAIMS.md`/`GAPS.md` and absent from the manuscript | PASS | none |
| Stray second bib file | `papers/encoder-crossover-190/REFERENCES_ADDITIONS.bib` exists outside the declared artifact list | N/A to the manuscript | record or archive it |

---

## CHECK 3 — Number consistency across artifacts

Canonical values agree in **most** places. Every divergence found:

| # | quantity | spelling A | spelling B | verdict | action |
|---|---|---|---|---|---|
| 1 | best encoder head | `0.3474` — `MANUSCRIPT.md:11`, `:28`, `:391`, `:407`, `ABSTRACT.txt:9`; `CLAIMS.md:47` (`.accuracy`) | **`kappa 0.347`** — `submission/ABSTRACT_METADATA.txt:1`: *"The best encoder arms reach kappa 0.347"* | **MISMATCH + WRONG QUANTITY NAME.** 0.3474 is **accuracy**, never κ, in every other artifact. Also a precision drop (3 vs 4 s.f.) | rewrite: *"best encoder arms reach accuracy 0.3474"* |
| 2 | primary baseline | `0.6789` — `MANUSCRIPT.md:4`, `:29`, `:314`, `:408`, `ABSTRACT.txt:10` | `0.679` — `ABSTRACT_METADATA.txt:1` | precision mismatch (3 vs 4 s.f.) | use 0.6789 |
| 3 | secondary baseline | `0.6684` — `MANUSCRIPT.md:6`, `:315`, `:425`, `ABSTRACT.txt:19` | `0.668` — `ABSTRACT_METADATA.txt:1` (*"0.668 on the published pre-registered one"*) | precision mismatch | use 0.6684 |
| 4 | majority-class margin | `+0.1053` — `MANUSCRIPT.md:33`, `:356`, `:531`, `ABSTRACT.txt:14` | `0.105` — `ABSTRACT_METADATA.txt:1` (*"beating every encoder arm by 0.105"*) | precision mismatch | use 0.1053 |
| 5 | exact McNemar p | `4.167e−09` (U+2212) — `MANUSCRIPT.md:31`, `:333`, `:414`, `:514`; `ABSTRACT.txt:12`; `CLAIMS.md:21`, `:67`; `GAPS.md:111`; `main.tex:397` (ASCII hyphen) | `4.2e-09` — `ABSTRACT_METADATA.txt:1`; also `4.17e−09` — `CLAIMS.md:33` (quoting the source) | **three spellings / three precisions.** Source `analysis.json` = `4.166817880507353e-09` (verified ASCII hyphen) | standardise the metadata abstract to `4.167e-09` |
| 6 | McNemar discordance ψ | `0.616` — `MANUSCRIPT.md:30`, `:333`, `:413`, `:422`; `ABSTRACT.txt:11`; `CLAIMS.md:21`; `GAPS.md:152` | `0.6158` — `CLAIMS.md:73`; full precision `0.6157894736842106` — `MANUSCRIPT.md:422` | precision mismatch inside `CLAIMS.md` and against the manuscript | pick 0.616 (or ψ = 0.6158) everywhere |
| 7 | p-value minus glyph | U+2212 `−` in `MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md`, `ABSTRACT.txt` | ASCII `-` in `submission/main.tex:397` (`4.167e-09`) and `ABSTRACT_METADATA.txt:1` | not an error, but the manuscript itself warns of it (`:765-769`) — the warning's own line numbers are wrong (Check 1) | keep ASCII in machine fields, U+2212 in prose, and fix the gotcha's citations |
| 8 | **second model pass** | `MANUSCRIPT.md:377-383`, `:584-592`: **two** readers; B2 = `mimo-v2.6-flash`, agreement `0.8632`, κ `0.8577`, 26/190; mutual κ `0.9125` | `CLAIMS.md:38`: *"second-labeller second model pass | `mimo-v2.6-flash` launched, **returned no file** | yes | exactly one model pass exists"*; `GAPS.md:25-26`: *"A second distinct-model pass (`mimo-v2.6-flash`) was launched and **returned no file**, so exactly **one** model pass exists"* | **CONTRADICTION — the manuscript is right.** `experiments/second-labeller-190/metrics2.json` `.vs_fixture` = `{"n":190,"agreement":0.8631578947368421,"kappa":0.8576984012674637}`, `.vs_UEXP_labelsB.kappa` = `0.9124852462791836` | strike the "returned no file / exactly one pass" claim from both companions |
| 9 | baseline decision state | `MANUSCRIPT.md:4`, `:310`, `:317`, `:662`: primary **declared** = 0.6789 | `GAPS.md:102`, `:132-134`: *"a human must declare one; **this unit does NOT**"* / *"This unit does not choose."* | STALE (historical unit record, now superseded) | mark `GAPS.md` §4 and `CLAIMS.md` §"Discrepancies" as superseded, or a reviewer reads an undecided baseline next to a declared one |
| 10 | manuscript size | `BUILD_NOTES.md:8`: *"864 lines, 66,671 bytes, **9,781 words**"* | actual `MANUSCRIPT.md` = **877 lines / 68,075 bytes**; `main.tex` = **80,780 B** (not 78,405 B as `BUILD_NOTES.md` states) | STALE | refresh the build record |
| 11 | bibliography count | `BUILD_NOTES.md` "Source inventory → Constructs converted": *"12 bibliography entries"* | 13 `@` entries in `REFERENCES.bib`, 13 `\bibitem` in `main.tex` | STALE (the same file's UMERGE1 note at item 8–9 records the bump to 13) | correct the inventory line |

Quantities checked and found **consistent** across the manuscript, `CLAIMS.md`, `GAPS.md`, `AVAILABILITY.md`, `main.tex`,
`ABSTRACT.txt` and (where present) `ABSTRACT_METADATA.txt`: 190 cases / 721 options / 74 labels / 51 once; the five arm
accuracies 0.3474 / 0.3474 / 0.2632 / 0.4526 / 0.2316; Δ −0.3316 and 0.3210; b = 27, c = 90; MDE 0.1595 / 0.1355;
ratios 2.079× / 2.446× / 0.85×; ψ 0.616; χ² 32.85; CI [−0.4316, −0.2263]; chance floor 0.2911; ECE 0.0994 / 0.0551 /
0.1547; SetFit chain 0.3158 → 0.2947 → 0.2632; ModernBERT chain 0.342105 → 0.347368; DeBERTa 1.1288 → 1.1235,
0.50 → 0.495 vs 0.475; training spread 0.5150 / 0.5900, 0.3421 / 0.3474; params 149,015,041 / 183,832,321 / 109,489,537
and 4.66B; κ 0.9014 / 0.8577 / 0.9125 / 0.9053 / 0.8632 / 0.9158 / 0.3249; 152,000 and 160,000 pairs; seeded copies
13 / 44 / 57 (per-pair maxima) with totals 13 / 220 / 233; strata 0.6650 / 0.67 / 0.645 / 0.6368 / 0.374; latency
12.37 / 14.16 / 11.96 / 12.46 ms and 53.06 / 72.85 / 106.92 / 453 / 639 ms.

---

## CHECK 4 — Required statements present?

| required statement | location / quote | verdict | action |
|---|---|---|---|
| data/code availability | `:790` `## Data and code availability`; *":796 The reproducibility subset ships with the paper, at `repro/encoder-crossover-190/`."* | PRESENT | — |
| licence of released artifacts | `:792` *"The paper is public, CC BY 4.0."*; `:848-851` *"The **content** … is covered by CC BY 4.0 … released artifacts are **source-available under PolyForm Noncommercial 1.0.0**, with an **author-offered paid commercial licence**"* | **PRESENT but SELF-CONTRADICTED** — the shipped subset file `repro/encoder-crossover-190/LICENCE_TODO.md` says *"the code licence for this subset is **NOT YET DECIDED**"* and *"**Status: open. Do not publish this subset until this file is resolved.**"* `AVAILABILITY.md:56-58` repeats the "decided" version | resolve `LICENCE_TODO.md` before submission; the two cannot both stand |
| limitations | `:554` `## 6. Limitations` (§6.1–§6.6, `:556-738`) | PRESENT | — |
| reproducibility scope | `:748-749` *"The evaluation harness … is withheld, so the subset verifies the recorded results but cannot regenerate them."*; `:823-829`; `:846` | PRESENT in wording, **factually wrong on the release boundary** (see the harness row below) | restate after the release boundary is fixed |
| compute/resources used | negative grep: 12 hits for "compute" are all "computed"; no H100/A100/GPU-hours/hardware statement for the authors' own runs | **ABSENT** | add a hardware / compute statement (the only host named is incidental — `:565` *"the GX10's GB10"*, `:657` *"evaluated on one host"*; `:724` *"under one dollar, under 15 minutes per arm on one A10G"* is the **counter-case's** premise, explicitly disowned) |
| conflict of interest | grep `conflict of interest` = 0; `competing` = 1, at `:201` in a semantic sense (*"not competing on the same object"*) | **ABSENT** | add a COI statement |
| funding | grep `funding`/`grant`/`financial` = 0 | **ABSENT** | add a funding statement (or "no funding") |
| author contributions | grep `author contributions`/`CRediT` = 0 | **ABSENT** | add a contributions statement |
| AI/LLM assistance disclosure | the paper **does** disclose that the *labellers* were models (`:52-56`, `:377-383`, `:646`); it does **not** disclose AI/LLM assistance in producing the paper or the analysis. Meanwhile the References section names internal pipeline units: `:859` *"unit **UBIB1**, 2026-10-15"*, `:868` *"Unit **UPAPER1c**"*, `:873` *"Unit **UMERGE1**"*. No acknowledgements section exists (grep `acknowledg` = 0) | **ABSENT (and leaked)** | add an AI-assistance disclosure; remove or relocate the unit IDs |
| ethics/IRB, or a statement none was needed | grep `ethics`/`IRB`/`review board` = 0 | **ABSENT** | add "no human-subjects data; no IRB review required" (or the applicable statement) |
| consent for human data | grep `consent` = 0 | **ABSENT** | see next row |
| who labelled the human fixture, and on what basis | `:272` *"The fixture was authored by one worker and carries known flagged weak points"*; `:584` *"agrees with the fixture's hand-authored labels"*; `:657` *"a single 190-case fixture authored by one worker"*. The paper gives **only the role** ("one worker"); no identity/relationship to the authors, no recruitment, compensation, consent, approval, annotation guideline, or data-provenance statement. `§6.2` is about **model** readers and explicitly defers the human labeller (`:644-653`) | **PARTIAL / ABSENT — the desk-reject risk named in the unit card is unaddressed** | state who labelled the fixture, under what instruction and with what consent, and whether it is human-subjects data |
| one-sentence statement of contribution | `:88-89` *"The contribution is the **artefact diagnosis on this fixture**, not the discovery that a fine-tuned generative decider can win."*; plus the numbered list `:91-108` and thesis `:75-77` | PRESENT | — |

---

## CHECK 5 — Structural hygiene

| item | evidence | verdict | action |
|---|---|---|---|
| section numbering contiguous | level-2 headings `:18,:60,:114,:251,:387,:506,:554,:742,:790,:856` = Abstract, 1–7, 2 unnumbered; level-3 `2.1,2.2,3.1–3.4,4.1–4.7,5.1–5.3,6.1–6.6` = 22, no gap, no duplicate | PASS | none |
| orphaned headings | every heading is followed by body text | PASS | none |
| empty sections | none | PASS | none |
| TODO/FIXME/TBD/placeholder in `MANUSCRIPT.md` | grep `TODO\|FIXME\|XXX\|TBD\|PLACEHOLDER\|Lorem` = 0 | PASS | none |
| unresolved `[Author…]` bracket forms in `MANUSCRIPT.md` | grep = 0 | PASS | none |
| — but in `submission/main.tex` | `main.tex:12` `\author{AUTHOR NAME TO BE SUPPLIED \\ AFFILIATION TO BE SUPPLIED}`; `main.tex:13` `\date{}`; `BUILD_NOTES.md` item 7 records visible `[Author and/or title not recorded in the corpus --- to be completed before submission.]` markers for `arxiv2602_06370`, `arxiv2512_12677`, `source_decider_stack_2026` | **FAILS** | complete before submission |
| heading capitalisation | numbered sections are Title Case consistently | PASS | none |
| — except `MANUSCRIPT.md:582` | `### 6.2 Two blind model readers: machine reproducibility of the fixture, **not** inter-annotator agreement` — literal Markdown bold inside a heading, which survives into `main.tex:317` as `\subsection{… \textbf{not} …}` | **FAILS (typographic)** | remove the bold from the heading |
| table headers | 5 tables (`:280-286`, `:312-315`, `:330-336`, `:405-418`, `:752-763`), each with a header row and separator | PASS | none |
| tables referenced from the text | **no `Table N` / `Figure N` / caption appears anywhere in `MANUSCRIPT.md`** (grep `Table|Figure|Fig\.|Eq\.|Appendix` = 0 hits). All 5 tables are uncaptioned and unreferenced | **FAILS** | add captions + numbered references, or state that tables are inline |
| table referenced but missing | none (no references exist) | N/A | — |
| stale heading vs content | `:655` `### 6.3 External validity: one fixture, one host, and a baseline choice awaiting a human` — the baseline **is** declared (`:4`, `:317`, `:662`) | **FAILS (stale)** | retitle §6.3 |
| front-matter working notes visible in the submission | `:3` *"**Draft status:** submission-candidate."*; `:4` *"✅ PRIMARY BASELINE DECLARED — 0.6789 (same-run), author decision 2026-10-15."*; `:10-14` *"⚠ Title figure, changed deliberately and flagged … If the declaration were ever revisited, §3.3 lists the exact sentences that change."* — reproduced verbatim in `main.tex` (BUILD_NOTES item 4) | **FAILS for a public submission** | delete or convert to a proper note |
| emoji/`⚠` glyph handling | `⚠` (U+26A0) occurs 4× in the manuscript (`:10`, `:293`, `:474`, `:488`) and `BUILD_NOTES.md` records the converter maps it to ASCII `!` — the warning sign is lost in the PDF | **FAILS (rendering)** | replace `⚠` with words, or use a package that renders it |
| unit IDs in the references section | `:859`, `:868`, `:873` (`UBIB1`, `UPAPER1c`, `UMERGE1`), `:870` (`UREFS` referenced as "Unit UPAPER1c then merged UREFS's verified additions") | **FAILS (process leakage)** | remove from the paper |

---

## CHECK 6 — Abstract and metadata consistency

| item | measurement | verdict | action |
|---|---|---|---|
| `submission/ABSTRACT.txt` length | **3,415 characters** (524 words; 38 lines incl. trailing newline) | **1,495 characters OVER a 1,920 cap — 1.78× the cap** | shorten the metadata abstract (the full abstract stays in the PDF) |
| `submission/ABSTRACT_METADATA.txt` length | **1,194 characters** (186 words, 1 line) | **726 characters UNDER the cap** | none |
| `MANUSCRIPT.md` abstract section (L20–56) | **3,415 characters** | **byte-identical to `submission/ABSTRACT.txt`** (verified `IDENTICAL`) | none |
| `ABSTRACT.txt` vs manuscript numbers | 0.3474, 0.6789, 0.6684, 0.4526, +0.1053, 0.2316, 0.2911, b = 27, c = 90, ψ = 0.616, Δ = −0.3316, 0.3210, p = 4.167e−09, 152,000, 13/44/57, 0.3158→0.2947→0.2632, 0.342105→0.347368, κ 0.9014 / 0.8577 / 0.9125 — all identical to the manuscript | PASS | none |
| `ABSTRACT_METADATA.txt` vs manuscript | mismatches: `kappa 0.347` (should be accuracy 0.3474 — Check 3 #1), `0.679`, `0.668`, `0.105`, `p = 4.2e-09`; and *"**Five encoder-based arms** and one fine-tuned decision model"* — the manuscript's five arms are **3 heads + 2 controls**, and `majority-class` is a constant answer, not an encoder arm (`:280-286`) | **FAILS** | fix the four precisions, the κ/accuracy mislabel, and "five encoder-based arms" |
| `ABSTRACT.txt` vs `ABSTRACT_METADATA.txt` | consistent on 190 / 2–8 options / 74 labels / 0.2911 / 0.2316 / 0.4526 / "harness withheld, results verifiable but not re-runnable" | PASS on content | — |
| `METADATA.md` title | *"The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33 and to a majority-class control"* = `MANUSCRIPT.md:1` **verbatim** | PASS | none |
| `METADATA.md` abstract length claim | *"3,415 chars / 524 words"* (field "Abstract") | CORRECT (matches the measured 3,415 / 524) | none |
| `METADATA.md` authors / affiliation / date | fields **Authors**, **Affiliation**, **Author email**, **Date** = `NOT SUPPLIED`; "Comments" = *"**NEEDS A NUMBER**"* | **MISSING** (consistent with the manuscript, which also omits them) | author must supply |
| `METADATA.md` cap caveat | *"arXiv's metadata abstract field is commonly capped at about **1,920 characters** … **This cap was NOT verified against arXiv's help pages in this unit**"* | OPEN | see the cannot-judge list |

---

## CHECK 7 — Front matter

| required item | manuscript evidence | verdict |
|---|---|---|
| title | `MANUSCRIPT.md:1` (and `METADATA.md` Title field, verbatim) | PRESENT |
| author block | none — the manuscript names no author anywhere; `main.tex:12` carries `AUTHOR NAME TO BE SUPPLIED`; `METADATA.md` "Authors" = NOT SUPPLIED | **ABSENT** |
| affiliation | none; `main.tex:12` `AFFILIATION TO BE SUPPLIED`; `METADATA.md` = NOT SUPPLIED | **ABSENT** |
| date | none; `main.tex:13` `\date{}` deliberately empty; the only date present is *"author decision 2026-10-15"* inside status notes (`:4`) | **ABSENT** |
| keywords | grep `keyword` = 0 in `MANUSCRIPT.md`; no keywords field in `METADATA.md` | **ABSENT** |
| one-sentence statement of contribution | `:88-89` (plus `:75-77`, `:91-108`) | PRESENT |
| (also absent, expected for a preprint) | corresponding-author email, acknowledgements, MSC/ACM class | not required by the unit card |

---

## MUST FIX BEFORE SUBMISSION (prioritised)

1. **Release-boundary contradiction — the harness.** The manuscript says the evaluation harness is withheld (`:748-749`,
   `:762`, `:809-810`, `:823-829`, `:834-835`, `:846`) and `AVAILABILITY.md:8-11`, `:24`, `:37`, `:43-50` repeats it, but
   `repro/encoder-crossover-190/harness/` **contains the 18 harness files, including `data/lint-report.json`**, and
   `repro/encoder-crossover-190/README.md` advertises *"the evaluation harness and the exact commands"* as released under a
   "publish-the-eval-harness / withhold-the-model" policy. Decide which is true and make the paper, `AVAILABILITY.md`, the
   subset `README.md` and `MANIFEST.json` say the same thing. **This determines the reproducibility-scope sentence, so fix it first.**
2. **Licence contradiction.** `MANUSCRIPT.md:848-854` and `AVAILABILITY.md:56-58` say the subset's code licence is
   **decided** (PolyForm Noncommercial 1.0.0 + paid commercial licence); the shipped
   `repro/encoder-crossover-190/LICENCE_TODO.md` says *"NOT YET DECIDED"* and *"Do not publish this subset until this file
   is resolved."* A file inside the release forbidding publication is a hard blocker.
3. **Missing `verify/recompute-claims.py`** in the named subset (`:797`, `:807`, `:827`), while a file the paper calls
   withheld (`harness/data/lint-report.json`, `:757`) is present. The paper's checklist for a reviewer does not run.
4. **`ABSTRACT_METADATA.txt` factual errors:** *"kappa 0.347"* (κ ≠ accuracy 0.3474), *"Five encoder-based arms"*
   (3 heads + 2 controls; `majority-class` is a constant), and 3-s.f. `0.679 / 0.668 / 0.105 / 4.2e-09` where the
   manuscript uses 0.6789 / 0.6684 / 0.1053 / 4.167e−09.
5. **Front matter:** author, affiliation, date, keywords all **ABSENT**; `main.tex` still carries
   `AUTHOR NAME TO BE SUPPLIED`/`AFFILIATION TO BE SUPPLIED`, an empty `\date{}`, and three
   `[Author and/or title not recorded in the corpus …]` reference markers. No submission is possible without them.
6. **Statements that are ABSENT and expected by a reviewer:** compute/resources; conflict of interest; funding; author
   contributions; AI/LLM assistance disclosure (while internal unit IDs `UBIB1`/`UPAPER1c`/`UMERGE1` leak into the
   References section at `:859`, `:868`, `:873`); ethics/IRB; consent. **Who labelled the 190-case fixture and on what
   basis is unaddressed** (`:272`, `:584`, `:657`) — the unit card's named desk-reject risk.
7. **Broken citations of the correction claim and the p-value gotcha:** `strategy/PAPER_CANDIDATES.md:269`,
   `experiments/LEARNINGS.md:281`, `strategy/PAPER_CANDIDATES.md:265`, `experiments/LEARNINGS.md:265` (`:430`, `:766-767`)
   all mis-resolve; `§F.3` (`:644`, `:649`, `:659`) exists in no named file; `EXP#12-typed-channel-comparison.md:95`
   (`:322`, `:396`) names a file that does not exist; `analysis.json` (`:295`, `:314`, `:466`, `:487`, `:498`) has no
   release path.
8. **Companion artifacts state the opposite of the paper:** `CLAIMS.md:38` and `GAPS.md:25-26` say the second model
   pass *"returned no file"* and *"exactly one model pass exists"*, while the paper reports two readers with
   κ = 0.8577 / 0.9125 (verified real in `experiments/second-labeller-190/metrics2.json`). `GAPS.md:102-134` still
   presents the baseline as undeclared.
9. **Stale numbers in the build/claim record:** `BUILD_NOTES.md:8` (*"864 lines, 66,671 bytes, 9,781 words"* vs 877 /
   68,075), the main.tex size (78,405 vs 80,780 B) and *"12 bibliography entries"* (13).
10. **Structural cosmetics:** no table captions or `Table N` references at all (5 uncaptioned tables); §6.3's heading
    still says *"a baseline choice awaiting a human"*; `MANUSCRIPT.md:582` puts literal `**not**` inside a heading
    (→ `main.tex:317` `\textbf{not}`); the four `⚠` glyphs become ASCII `!` in the PDF; the front-matter status notes
    (`:3-14`) are internal working text reproduced verbatim in `main.tex`.

---

## CANNOT BE JUDGED FROM THE MARKDOWN SOURCE (needs the compiled PDF, or is external)

1. **Page count** — no TeX toolchain on this host (`pdflatex`/`latexmk`/`tectonic`/`xelatex`/`bibtex` all absent per
   `BUILD_NOTES.md`); `METADATA.md`'s "Comments" field is *"NEEDS A NUMBER"* for this reason.
2. **Float placement and table overflow** — whether the 5 `tabular` blocks fit the text width, how many overfull/underfull
   boxes `\sloppy` leaves, and whether any table breaks across pages.
3. **Rendered glyph fidelity** — the `⚠`→`!` substitution's visual effect, the U+2212 → ASCII hyphen change in
   `main.tex:397`, and whether the em-dash/quote conversions read correctly.
4. **Section/TOC rendering** — that LaTeX's automatic numbering reproduces the manuscript's 1–7 and supplements; the
   converter's manual-number-stripping (`BUILD_NOTES.md` item 2) is plausible but unverified by a compiler.
5. **Whether `[Author and/or title not recorded in the corpus …]` markers actually print**, and how the three incomplete
   reference entries look set.
6. **DOI/URL reachability of external sources** — `https://simmering.dev/blog/modernbert-vs-llm/` (`:164`), arXiv ids
   (`2602.06370`, `2512.12677`, `2309.03882`, `2305.13971`, `2507.18546`, `2508.07662`, `2501.08457`, `2507.11412`,
   `2311.08526`), DOI `10.1007/s10579-024-09796-y` and `10.18653/v1/2024.naacl-long.300` / `…/2025.acl-industry.68`.
7. **The target-repo sources quoted in the paper** — `docs/DECIDER_STACK_DECISION.md` §11.2/§11.6 and `:415/:500/:494-495`,
   `DECIDER_TIER §2`, `analysis.json`, `REPORT.md:69`, `evals/fixtures/reflex-decisions.ts`, the EXP#11 decider rows,
   `experiments/LEARNINGS.md`: none are present at the paths the paper names, so their quoted content could not be
   re-checked here (the `docs/…` §11.6 block quote at `:123-129` in particular is unverified).
8. **Whether arXiv's metadata abstract field really caps at 1,920 characters** — `METADATA.md` explicitly records the cap
   as unverified against arXiv's help pages; the measured lengths (3,415 / 1,194) are given above so the author can act
   once the cap is confirmed.
9. **PDF-level metadata** — title/author fields, licence stamp, arXiv categories (`METADATA.md`: cs.CL primary,
   cs.LG cross-list), and the endorsement requirement (`METADATA.md` calls it *"required and absent"*).
