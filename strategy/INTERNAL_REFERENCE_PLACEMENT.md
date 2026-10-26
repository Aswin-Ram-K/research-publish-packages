# INTERNAL_REFERENCE_PLACEMENT.md — where manuscript citations point at internal records

**Author unit:** UPLACE1 (read-only review). **Status:** recommendation only — **not applied**.
**Scope:** `papers/encoder-crossover-190/`, `papers/gated-read-batching/`,
`papers/replay-record-not-decision/` — `MANUSCRIPT.md` and shipped `submission/main.tex`.
**Blocker note:** `papers/encoder-crossover-190/submission/main.tex` is being edited by `UAUTHOR1`;
the edits below are for a *fresh* unit, applied after UAUTHOR1 stops.

## 0. Headline

- **In-abstract internal-record references: 3 occurrences, on 2 lines, in 2 of the 3 shipped papers.**
  - `encoder-crossover-190/submission/main.tex:19` — `\texttt{REPORT.md:189}`, **twice**, inside the
    abstract (`\begin{abstract}` line 16 … `\end{abstract}` line 25).
  - `replay-record-not-decision/submission/main.tex:21` — `\texttt{l1-head-to-head.jsonl}`, **once**,
    inside the abstract (lines 20–23).
  - `gated-read-batching/submission/main.tex` — **0** (abstract lines 18–23 are clean).
- **Class size in the shipped payload is not trivial but is dominated by one paper.** Matching-line
  counts in `submission/main.tex` (`grep -cE 'REPORT\.md|analysis\.json|eval-[a-z-]+\.json|DECIDER_STACK|GATED_READ|LEARNINGS\.md|EXP#|[a-z0-9_-]+\.jsonl|metrics\.json|RUN\.json'`):
  encoder **21**, gated **0**, replay **15**.
- **The one hard defect is the encoder abstract.** `REPORT.md:189` is a real, followable citation
  (the file ships, and line 189 really does say "cannot be re-scored"), but it is provenance that a
  reader meets *before the paper*. It should move to §4/§7, not be deleted from the record.
- **Everything else in the abstracts is defensible** — see §4 (leave-alone) and §5.

## 1. Method / commands

```
grep -n 'begin{abstract}\|end{abstract}' papers/*/submission/main.tex
  → encoder 16/25 · gated 18/23 · replay 20/23
grep -cE '<pattern above>' papers/encoder-crossover-190/submission/main.tex   → 21
grep -cE '<pattern above>' papers/gated-read-batching/submission/main.tex     → 0
grep -cE '<pattern above>' papers/replay-record-not-decision/submission/main.tex → 15
find scratch/uneutral10/package -type f -printf '%s\t%p\n'  → 30 files (sizes quoted below)
wc -l scratch/uneutral10/package/results/REPORT.md  → 303
sed -n '188,190p' scratch/uneutral10/package/results/REPORT.md
  → 188 blank · 189 "* **`decider-4b 0.6684` (D-067) cannot be re-scored.** No per-case rows for that
     specific measurement are in the tree, so F5 cannot check it directly; …"
  → 190 "* **`imajev-4b 0.645` is mislabelled in pre-registration §3.** …"
tar tzf papers/encoder-crossover-190/submission/encoder-crossover-190.tar.gz      → main.tex (only)
tar tzf papers/gated-read-batching/submission/gated-read-batching.tar.gz          → main.tex (only)
tar tzf papers/replay-record-not-decision/submission/replay-record-not-decision.tar.gz → main.tex (only)
```

**Bound caveat.** The initial broad sweep was truncated (250 of 1007 matching lines), so the
`MANUSCRIPT.md` body inventory below is complete for the abstracts and for the lines quoted, but is
**not** an exhaustive line-by-line sweep of all 918/263/340 `MANUSCRIPT.md` lines. The shipped-payload
counts in §0 are exact.

## 2. Abstract hits — exact before/after edit pairs (apply these)

### Edit A1 — paper #3, `papers/encoder-crossover-190/submission/main.tex:19` (occurrence 1 of 2)
Before (substring, unique in the file because of the trailing `---`):
`--- which \texttt{REPORT.md:189} states \textbf{cannot be re-scored} from the tree ---`
After:
`--- which \textbf{cannot be re-scored} from the tree ---`

### Edit A2 — paper #3, `papers/encoder-crossover-190/submission/main.tex:19` (occurrence 2 of 2)
Before:
`and which \texttt{REPORT.md:189} states cannot be re-scored from the tree.`
After:
`and which cannot be re-scored from the tree.`

### Edit A3 — paper #3, `papers/encoder-crossover-190/MANUSCRIPT.md` (abstract lines 5–45), occurrence 1
Line 25 ends `… **0.6684** — which`; line 26 currently begins:
Before (line 26):
`` `REPORT.md:189` states **cannot be re-scored** from the tree — the same head loses by **0.3210** ("0.32") against the **secondary** baseline **0.6684**. ``
After (line 26):
`` **cannot be re-scored** from the tree — the same head loses by **0.3210** ("0.32") against the **secondary** baseline **0.6684**. ``

### Edit A4 — paper #3, `papers/encoder-crossover-190/MANUSCRIPT.md`, occurrence 2
Before (line 29, tail):
`` **secondary/published 0.6684**, which is the pre-registered F1 threshold and which `REPORT.md:189` states ``
After (line 29, tail):
`` **secondary/published 0.6684**, which is the pre-registered F1 threshold and which ``
Line 30 (`cannot be re-scored from the tree.`) is unchanged.

**Net effect.** The abstract keeps the *claim* ("cannot be re-scored from the tree") and loses only the
*locator*. Restore the locator as ordinary provenance in §4 (encoder body), where it already appears:
`main.tex:149`/`:153`/`:397` and `MANUSCRIPT.md`. This satisfies the reviewer without weakening the record.

**Do not** change the numbers, the `\cite{source_decider_stack_2026}` key, or the surrounding sentences.

## 3. Paper #3 package — does each target ship? (`scratch/uneutral10/package/`)

| Target as named in the paper | Ships? | Path / size in package | Class |
|---|---|---|---|
| `REPORT.md` (and `REPORT.md:85/104/189/191`) | **YES** | `results/REPORT.md` — 28,629 B / 303 lines; line 189 verified verbatim | (a) body: fine. abstract: (b) |
| `eval-*.json` (5 arms) | **YES** | `results/eval-{modernbert-base,deberta-v3-base,setfit-mpnet,majority-class,shuffled-label}.json` — 63,109 / 63,159 / 63,351 / 62,168 / 63,339 B | (a) |
| `evals/fixtures/reflex-decisions.ts` | **YES, wrong prefix** | `fixture/reflex-decisions.ts` — 81,439 B | (a) + path fix (§6.1) |
| `results/baselines.json` | **YES** | `results/baselines.json` — 57,339 B | (a) |
| `second-labeller/{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json,PREREGISTRATION.md}` | **YES** | 13,064 / 22,500 / 9,551 / 3,477 / 9,587 B | (a) |
| `preregistration/…` (named `EXP#12-typed-channel-comparison.md:95`) | **YES, different name** | `preregistration/EXP12-typed-channel-comparison-prereg.md` — 8,997 B (line offset not re-verified) | (c) dangling-by-name (§6.2) |
| `results/DEFECT-EVIDENCE.json` | **NO — and the paper says so** | not in package; abstract/body explicitly flag it as outside the released set | (a) honest |
| `analysis.json` (+ `.observations.debertaV3Training`, `.baselinesRescored`, `.publishedBaselines`, `.comparisons`, `.falsifiers.F4.fires`, `.resolution`, `.h4.verdict`) | **NO** | not in package tree | **(c) dangling** — the single largest body class one |
| `docs/DECIDER_STACK_DECISION.md` (`§11.6`, `:415`, `:471–473`) | **NO** | private-repo `docs/` path; nothing under it ships | **(c) dangling + (d) identifying** |
| `lint-report.json` / `harness/data/lint-report.json` | **NO** | not in package (package has no `harness/` or `data/` dir) | (c) dangling |
| `EXP#11-evidence/decider-rows.jsonl`, `experiments/second-labeller-190/*`, `LEARNINGS.md`, `DEFECT-EVIDENCE.json` | **NO** | private tree | (c) dangling / already declared withheld |

## 4. Leave-alone list, with reasons

1. **`replay-record-not-decision/submission/main.tex:21` — `\texttt{l1-head-to-head.jsonl}` in the
   abstract. LEAVE IT.** It is not an authority citation; the file is the *object of study* — the
   abstract's whole clause is that this second record is "not an independent corpus". Removing the
   name would remove the referent. The paper's Data availability declares the file released
   (63,238 B / 380 lines / sha256 `6af0e0d8…`) under CC BY 4.0. **But see §7 (open gap): no released
   bundle carrying it exists in this workspace** — `submission/replay-record-not-decision.tar.gz`
   contains `main.tex` only; the only on-disk copies are under the read-only target repo
   (`state/…/duval/repo/docs/research/l1-head-to-head.jsonl`). **Shipping status: UNKNOWN.** Class:
   (a) if it ships, (c) if it does not.
2. **All `results/REPORT.md` body citations in paper #3** (`main.tex:86,136,148,149,153,202,307,383,
   384,386,395,397`; `MANUSCRIPT.md` body). The target ships and the line numbers resolve. (a).
3. **Paper #2, `gated-read-batching`.** 0 internal-record refs in the shipped LaTeX and 0 in the
   `MANUSCRIPT.md` abstract (lines 7–13). Nothing to do. (Its `GAPS.md`/`REFS.md` are internal working
   records, not shipped, and were out of scope.)
4. **The honest negative citations** (`DEFECT-EVIDENCE.json` "is **not** part of the released set",
   `main.tex:232,384`). Naming a target in order to say it does *not* ship is not a defect.

## 5. Classification summary

| # | Hit | Paper | In abstract? | Ships? | Class |
|---|---|---|---|---|---|
| 1 | `REPORT.md:189` ×2 | encoder | **YES** (`main.tex:19`, `MANUSCRIPT.md:26,29`) | yes (`results/REPORT.md`, 28,629 B) | **(b) followable but misplaced** |
| 2 | `l1-head-to-head.jsonl` | replay | **YES** (`main.tex:21`, `MANUSCRIPT.md:29`) | UNKNOWN (declared released; no bundle located) | (a)/(c) — leave |
| 3 | `docs/DECIDER_STACK_DECISION.md` | encoder | no | no | (c) + (d) identifying |
| 4 | `analysis.json` + dotted keys | encoder | no | no | (c) dangling |
| 5 | `evals/fixtures/reflex-decisions.ts` | encoder | no | yes, as `fixture/reflex-decisions.ts` | (a), path-prefix nit |
| 6 | `EXP#12-typed-channel-comparison.md:95` | encoder | no | yes, under a different filename | (c) dangling-by-name |
| 7 | `lint-report.json` | encoder | no | no | (c) dangling |
| 8 | `eval-*.json`, `baselines.json`, `second-labeller/*`, `results/REPORT.md` | encoder | no | yes | (a) |
| 9 | `DEFECT-EVIDENCE.json` (negative citation) | encoder | no | no | (a) honest |

**Severity call:** low-to-moderate, and concentrated. One genuine placement defect (encoder abstract,
2 occurrences) with a ready mechanical fix; one ambiguous abstract filename (replay) that should be
left; a body-level dangling-reference cluster (`analysis.json`, `docs/DECIDER_STACK_DECISION.md`,
`lint-report.json`) that is a *release-boundary* question, not a prose question.

## 6. Body edits (paper #3) — exact strings, if the release boundary is not changed

### 6.1 Wrong path prefix — safe mechanical fix
`main.tex:104` — before `(\texttt{evals/fixtures/reflex-decisions.ts})`
→ after `(\texttt{fixture/reflex-decisions.ts})`
Mirror in `MANUSCRIPT.md` wherever `evals/fixtures/reflex-decisions.ts` occurs.

### 6.2 Dangling-by-name, the content ships
`main.tex:153` and `:202` — before `\texttt{EXP\#12-typed-channel-comparison.md:95}`
→ after `\texttt{preregistration/EXP12-typed-channel-comparison-prereg.md}` (drop the `:95` — the
offset has **not** been re-verified against the shipped copy).

### 6.3 `docs/DECIDER_STACK_DECISION.md` — annotate, do not silently drop
Preferred minimum edit (keeps provenance, marks non-shipping): append
`; source record, not part of this release` after each `docs/DECIDER\_STACK\_DECISION.md \S…` / `:…`
locator in the shipped LaTeX (`main.tex:28,86` context, `:133,141`) and in `MANUSCRIPT.md`. This
converts an (a)-looking citation into an honest (c). A reader can then stop looking for a file that
will never be in the package.

### 6.4 `analysis.json` — **do not rewrite eight citations blind; ship the file instead**
`analysis.json` does not ship, yet at least eight `main.tex` lines cite dotted keys into it
(`:134,148,149,153,251,268,273,395`; also `MANUSCRIPT.md`). Two options, in preference order:
1. **Add `analysis.json` to `scratch/uneutral10/package/results/`** (and, if present, `lint-report.json`
   to the package). One file change repairs all eight citations and preserves the paper's audit trail.
   UPLACE1 did not locate `analysis.json` in the package and **did not** write anything.
2. If it cannot be released, replace each dotted-key locator with the shipped `results/REPORT.md`
   section that carries the same number. **The key→section mapping was NOT established by this unit
   (UNKNOWN)**; a fresh unit must not guess it.

## 7. Open gaps this unit could not close

- **Replay record shipping: UNKNOWN.** `submission/replay-record-not-decision.tar.gz` = `main.tex`
  only; no released bundle for paper #1 was located. Either ship the two `.jsonl` records or the
  abstract/Data-availability pointer is dangling.
- **`analysis.json` key→`REPORT.md` section mapping: UNKNOWN** (see §6.4).
- **Full `MANUSCRIPT.md` body sweep incomplete** (broad grep truncated; 15-call bound reached).
