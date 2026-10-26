# RESIDUALS.md — every known residual mechanism reference in the shipped tree

**Unit:** UFIX10 · **Written:** 2026-10-15 (UTC) · **Owed to:** `strategy/VERIFICATION_REPORT_8.md` (UVER8)
**Subject:** `repro/encoder-crossover-190-SANITISED/` · **Companion to:** [`REDACTION_REPORT.md`](REDACTION_REPORT.md) §7 and §11

UVER8's verdict was `pass-with-corrections` and its criticism of the counting was that one number
("210 → 154") was measured on a subset and published as the whole. This file exists so the author has
**one honest list** to decide with: every file in the shipped tree that matches the strict mechanism regex,
its count, and a one-line judgement — **irreducible** (inside question/option text that *is* the model
input, or a design decision the author owns) versus **fixed** (removed by UFIX10) versus **declared**
(the disclosure/classification itself, which adds no mechanism).

## 1. Scope — the same tree, three honest numbers

Regex (verbatim from `verify/run-verification.sh`, line 133):

```
StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle
```

| scope | as-audited | sanitised (now) | what the scope means |
|---|---:|---:|---|
| **whole shipped tree** | 210 | **330** | everything in the directory, including this tree's `verify/` logs and the `variants/` alternative |
| **the exclusion `REDACTION_REPORT.md` states** (`verify/`, `variants/` removed) | 210 | **216** | what the report's "210" was measured over |
| **instrument files only** (§2 of the report's per-file table, minus the authored `README.md`) | 209 | **154** | the only scope in which "210 → 154" was ever true: **-55** |

**The figure the first release published was `210 → 154 (−56)` — a mixture of scopes 2 and 3.** Over scope 2
the true sanitised figure is **216** (+6 vs as-audited); over scope 3 it is **154**
(-55, instrument-only). Both are stated everywhere in this tree now.

`redact.py` alone contributes **18** of the scope-2 figure and this report **35**: the redaction tool
must name the terms it strips, and the report must classify them. Their hits are *descriptions of the
residual*, not additional mechanism disclosure — but they are counted above rather than excluded silently,
which is the correction UVER8 asked for.

## 2. Per file, with a judgement

| file | strict lines | judgement |
|---|---:|---|
| `variants/no-union/files/fixture/reflex-decisions.ts` | 57 | **declared alternative** — labelled VARIANT B (union removed); its higher count is explained in `REDACTION_REPORT.md` §6. |
| `fixture/reflex-decisions.ts` | 52 | **irreducible** — every hit is inside `question` or option text, i.e. the rendered model input (`tccommon.render`); editing it changes what every arm saw and therefore every number. |
| `harness/data/fixture-190.json` | 50 | **irreducible** — the exported mirror of the same question/option text; regenerated from the fixture. |
| `verify/VERIFICATION.txt` | 39 | **declared, not new disclosure** — verbatim acceptance-test log / scanner output; the scanner must print the terms it searches for. |
| `REDACTION_REPORT.md` | 35 | **declared, not new disclosure** — these lines are the residual classification itself (the term list, the §7 categories and the §11 amendment). They describe what is residual; no kernel rule is added. |
| `redact.py` | 18 | **inherent to the tool** — the deterministic redaction script must name the terms it strips and assert them; it discloses no mechanism beyond the term set already printed in `REDACTION_REPORT.md` §2. |
| `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts` | 9 | **declared alternative** — labelled VARIANT B (union removed); its higher count is explained in `REDACTION_REPORT.md` §6. |
| `results/eval-shuffled-label.json` | 8 | **irreducible** — option labels used as answer keys in a frozen scoring record. |
| `results/eval-deberta-v3-base.json` | 7 | **irreducible** — option labels used as answer keys in a frozen scoring record. |
| `results/eval-majority-class.json` | 7 | **irreducible** — option labels used as answer keys in a frozen scoring record. |
| `results/baselines.json` | 6 | **irreducible** — the same option labels, which are the scoring keys for the baselines. |
| `results/eval-modernbert-base.json` | 6 | **irreducible** — option labels used as answer keys in a frozen scoring record. |
| `results/eval-setfit-mpnet.json` | 6 | **irreducible** — option labels used as answer keys in a frozen scoring record. |
| `README.md` | 4 | **irreducible by design** — the 4 remaining hits are all the `DecisionKind` name, which the variant decision must name (§6). The as-shipped 8 (UVER8 C1: 5 `DecisionKind` + 3 lines re-quoting the withheld vocabulary) was fixed by UFIX10: the 3 re-quoting lines now point at `REDACTION_REPORT.md` §7 and this file. |
| `fixture/DECISION_CASE_SCHEMA.ts` | 3 | **irreducible by design** — the `DecisionKind` *type name* only, which VARIANT A deliberately keeps for the paper's typed-single-label claim. |
| `second-labeller/disagreements.jsonl` | 3 | **irreducible** — `question` text of one disagreement row, which is the run's own output. |
| `variants/no-union/README.md` | 3 | **declared alternative** — labelled VARIANT B (union removed); its higher count is explained in `REDACTION_REPORT.md` §6. |
| `verify/redaction-log.json` | 3 | **declared, not new disclosure** — verbatim acceptance-test log / scanner output; the scanner must print the terms it searches for. |
| `second-labeller/EVIDENCE.md` | 2 | **kept deliberately** — verbatim option-label quotations documenting parser defect D-P1; removing them would leave the defect note uncheckable. |
| `verify/run-verification.sh` | 2 | **declared, not new disclosure** — verbatim acceptance-test log / scanner output; the scanner must print the terms it searches for. |
| `MANIFEST.json` | 1 | **partly fixed** — the private-branch commit id (19 citations) and the `git:` history reference are **removed** (UFIX10); the 1 remaining hit is the `DecisionKind` in the schema-excerpt provenance line, which describes the source of a shipped file and cannot be dropped without losing that provenance. |
| `second-labeller/PREREGISTRATION.md` | 1 | **irreducible** — the frozen pre-registration mentions the `DecisionKind` type declarations; editing it would falsify the pre-registration. |
| `second-labeller/RUN.json` | 1 | **kept deliberately** — the same option-label quotation, as run provenance. |
| `second-labeller/parse_fixture.py` | 1 | **kept deliberately** — docstring quoting the same option label, which is what D-P1 is about. |
| `verify/RESIDUAL-SCAN.txt` | 1 | **declared, not new disclosure** — verbatim acceptance-test log / scanner output; the scanner must print the terms it searches for. |

## 3. What is *not* in this list, and why that matters

- **The private-branch commit id is gone.** It appeared **19×** in `MANIFEST.json` (18
  `git:<sha>:tools/typed-channel/…` provenance citations plus one `branch_commit` field) and in prose in
  `INTEGRITY.md`, `README.md` and `REDACTION_REPORT.md`. The strict regex cannot see it (it contains no term
  for a commit SHA or for `git:`), which is why the earlier scan reported the tree clean. It is now removed
  from all four files; `REDACTION_REPORT.md` §8.1 states what replaced it and why. **Status: fixed.**
- **No VCS objects.** `find` for `.git`, `*.pack`, `*.idx`, `*.bundle`, `ORIG_HEAD`, `packed-refs` → **0 hits**
  across the tree. The tree is a tree, not a checkout.
- **The private path `tools/typed-channel/` survives in the released harness bytes** (68 references across
  `harness/*.py`, `harness/README.md`, `results/REPORT.md`). It cannot be removed without rewriting released
  harness files and destroying their byte-identity with the source blobs. **Status: irreducible, declared.**
- **The `(a) rewrite the 47 questions` vs `(b) ship as-is` decision is the author's** and no re-run is needed
  to make it: the numbers hold either way for this tree. Nothing here changes the experiment.
