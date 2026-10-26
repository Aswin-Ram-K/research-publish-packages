# ANCHOR-PREREG-V2 — ERRATA (text defect only; the body is not edited)

**Corrects:** `experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md`, lines 59–60 (rule §1(a)).
**Written by:** unit `DET-VERIFY`, 2026-10-26. Offline.
**Why an errata file and not an edit:** the normative rule body of that document is
digest-attested. The hashed text is the 60 lines strictly between
`<!-- r21-rule:begin -->` (doc `:45`) and `<!-- r21-rule:end -->` (doc `:106`), markers
excluded; `anchor_classify.rule_digest()` reproduces
`b16548301589593b8d1041325fce833ef60d3b39b8e8c0a205084ee35eb9ad57`, byte-equal to the
recorded value. Any edit inside that block breaks the attestation, so the false sentence
is corrected here and the hashed document stays byte-identical.

| digest | value |
|---|---|
| rule-body digest (attested, `:45`–`:106`) | `b16548301589593b8d1041325fce833ef60d3b39b8e8c0a205084ee35eb9ad57` |
| whole-file sha256 of the uncorrected doc | `173f0c1c1e5f980fb7b0c23ca0f740e5c807bbb37402ebed7a8f43ebf8a844aa` |

R2 (`ANCHOR-PREREG.md`) and R2.1 (`ANCHOR-PREREG-V2.md`) **both stay frozen as historical
record**. Neither is retired; this file adds a correction, it does not supersede either.

## 1. The false sentence, quoted

> `>` `name`; `PtrBudgetExceededError` carries `ptr` and `exceeded` and `error` but **not**
> `budget`. Substring containment is **not** the matching unit (a NAME token
> `no_record` does carry `record`; a NAME token `recordx` does **not**).
> — `ANCHOR-PREREG-V2.md:59-60`

## 2. Why it is false under the document's own rule

Rule §1(a) (`ANCHOR-PREREG-V2.md:55-58`) defines the matching unit as **one `tokenize`
token**, matched when the anchor *equals one of the underscore-separated parts of that
token's text*, case-insensitively. A token with **no underscore** has exactly **one**
part: itself. So for the single NAME token `PtrBudgetExceededError` the only part is
`ptrbudgetexceedederror`, and **no shorter anchor equals it** — not `ptr`, not `exceeded`,
not `error`, and not `budget`.

The paragraph therefore contradicts itself, and the contradiction is visible four
sections later in the same document:

> `-` `:142` `PtrBudgetExceededError` does **not** carry `budget`, because it has no underscore
> — `ANCHOR-PREREG-V2.md:117`

`:117` states the rule correctly and explains *why* (`because it has no underscore`); by
that same reason it carries none of `ptr`, `budget`, `exceeded`, `error`. The class is
defined at `experiments/ptr-engine/ptr_engine/errors.py:66` as
`class PtrBudgetExceededError(PtrError):` — one NAME token, no underscore.

This is exactly the failure mode the design note names at `:57-58`: "Substring
containment is **not** the matching unit." Reading `PtrBudgetExceededError` as carrying
`ptr`/`exceeded`/`error` is substring containment (a CamelCase-aware *word* split), not
the underscore split the rule declares.

## 3. The correct statement

> A CamelCase class name with no underscores — `PtrBudgetExceededError` is the example —
> carries **none** of `ptr`, `budget`, `exceeded`, `error`. Under §1(a) its only
> underscore-separated part is the whole lowercased token `ptrbudgetexceedederror`, so the
> only anchor it can match is an anchor equal to the full class name. `budget` fails for
> the same reason `ptr`, `exceeded` and `error` fail; the reason is the absence of any
> underscore, not the absence of the word "budget" from the name.

## 4. Census impact — 0 of 11 cells

**0/11.** The census (`V-ANCHOR-PREREG` / R2.1 §1.1) is an 11-cell, class-only census over
the resolve/errors anchors. `PtrBudgetExceededError` is not one of those cells: the
committed census rows (`experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.census.json`)
contain no `PtrBudget` entry, and `:131` records the census as **unchanged 11/11 on class**.
The sentence is illustrative prose about the matching rule, not an input to any cell's
computation — no anchor's class, evidence line, or verdict changes if it is corrected.

**Consequence:** text defect only. No measurement, classification, or verdict in R2 or
R2.1 depends on the false clause; the 11/11 census, the R2 → R2.1 reclassifications, and
the frozen verdicts all stand. The document's normative content is self-consistent with
`:117`; only the illustrative example at `:59` is wrong.

## 5. Reproduction

```
python3 - <<'PY'
import sys; sys.path.insert(0, "experiments/ptr-engine/tools")
import anchor_classify as ac
print(ac.rule_digest("experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md"))
PY
# b16548301589593b8d1041325fce833ef60d3b39b8e8c0a205084ee35eb9ad57
sha256sum experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md
# 173f0c1c1e5f980fb7b0c23ca0f740e5c807bbb37402ebed7a8f43ebf8a844aa
python3 -c "import tokenize,io; print([t.string for t in tokenize.generate_tokens(io.StringIO('PtrBudgetExceededError').readline) if t.type==tokenize.NAME])"
# ['PtrBudgetExceededError']  -> no underscore -> one part -> matches no shorter anchor
```
