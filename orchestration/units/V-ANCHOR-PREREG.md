# V-ANCHOR-PREREG (verifier)

Independent re-check of `ANCHOR-PREREG` (`3a2fda6e`). Offline, zero requests.
Bound: ≤24 tool calls (used 21). Write paths: this card + `orchestration/handoffs/V-ANCHOR-PREREG.json`.

**Verdict: `partial`.** The census reproduces exactly; the `raising` finding is real and the rule points the right way, but the normative text is not yet operational for a third party (f-string middles / multi-line docstring continuation lines classify differently under the author's own checker), and recorded probe C does not reproduce from the edit it describes.

## 1. Census — CONFIRMED, re-derived with my own commands
Own tokenizer copy of `grade_v3.anchors()` semantics (`TOKEN_RE` + split `_`, len≥4, STOPWORDS) over the two v4 fixtures: cp arrays byte-equal, cp.2.t46 → 9 anchors; cp.0/cp.1 numeric only.

| cell | my evidence |
|---|---|
| cp.0.t12 `64` NUMBER | `ptr_engine/resolve.py:39` `DEFAULT_MAX_REFS = 64` |
| cp.1.t24 `31` NUMBER | `ptr_engine/errors.py:15..247`, own `grep -c '^class Ptr'` = **31**, last `:247` |
| cp.2.t46 `ledger` CODE | `resolve.py:33` `from .ledger import Ledger` |
| cp.2.t46 `record` CODE | `resolve.py:69` `ledger.record_refusal(` |
| cp.2.t46 `refusal` CODE | `resolve.py:69` |
| cp.2.t46 `scope` CODE | `resolve.py:43` `class Scope:` |
| cp.2.t46 `serialized` CODE | `resolve.py:70` `serialized_ref=text` |
| cp.2.t46 `text` CODE | `resolve.py:66` `text: str` |
| cp.2.t46 `code` CODE | `resolve.py:70` `code=error.code` |
| cp.2.t46 `error` CODE | `resolve.py:66` `error: PtrError` |
| cp.2.t46 `raising` PROSE | `resolve.py:67` docstring, only occurrence |

11 = 8 CODE + 2 NUMBER + 1 PROSE. Every author line number matches mine. The author's checker was **not** used as census evidence.

## 2. `raising` — real find; rule principled in direction, not yet operational
`raising` really is not absent (`resolve.py:67`, docstring). The occurrence-context rule is **strictly narrower** than presence, so it cannot move an identifier out of the required set — principled in direction. Applied to 3 undisputed anchors (`ledger`,`scope`,`code`) it lands as predicted with no judgement call.

But a third party applying the **text** to a **new** anchor diverges from the checker in measured cases:
- `spent` / `budget` at `resolve.py:143` live only inside `FSTRING_MIDDLE`; the checker's `prose_lines()` marks only STRING/COMMENT **start lines**, so it calls that line CODE. The text says "outside any string literal".
- `budget` at `resolve.py:47` is a **continuation line** of the `:44` docstring; same misclassification.

Also under-specified: "the cited source file" vs the cited `#L66-L71` range (for `record`, file-wide adds `record_resolution` at `:159`).
No second divergence **inside this fixture**: all 9 anchors' contexts computed, `raising` is the only prose-only one.

## 3. Probes — rebuilt from my own inputs; added probe D
A = verbatim v6 row (sha256 `ecdb3fc9d9f03b8de6492e0d74da5dfbcef9c2ccba1a0717fa443d6180d3be48`, matches author's `ecdb3fc9d9f0`). A: R1 reject [raising] / R2 accept. B (`write_audit`): reject [record, refusal]. C **only** with the checker's global `scope`→`grant` replacement (`grant=grant_name`): reject [scope]; the **minimal** edit `scope=`→`grant=` (`grant=scope_name`) is **ACCEPTED** by R2. Added **D** (drops `serialized`, keeps the rest): **REJECT** [serialized]; D2 (drops `ledger`, keeps "re-raising"): reject; E (token-stuffing negation containing all 8): ACCEPT — inherited bag-of-tokens limit, true of R1 too.

## 4. Freeze order — holds for judged inputs
Freeze epoch `1793021361`. Newest derivation input `rows-longrun-v6-tools.grade-v3.json` = `1793021038` (322 s earlier). All **15/15** §7 sha256 re-computed and match. No v3 row/grade/fixture/grader mtime ≥ freeze. Recorded, not violations: `ANCHOR-PREREG.md` 08:30:15 and `anchor_prereg_check.py` 08:30:06 post-date the instant they claim by 45–54 s; `measure/V6-RESULT.md` 08:29:50 is narrative, not a graded input. `grade_v4.py` + 9 `*.grade-v4.json` appeared 08:36 (sibling card) — untouched.

## 5. Red→green — guard fails on a corrupted census
Real doc: `anchor_prereg_check.py` → **exit 0 / RESULT: PASS**. `/tmp` copies with `PREREG` repointed (control exit 0): `raising` PROSE→CODE → **exit 1**, `census cell 10: computed ('cp.2.t46','raising','PROSE-CONNECTOR') recorded (...,'CODE-SYMBOL')`; `code` CODE→PROSE → **exit 1**, `census cell 8`. No artifact edited.

## Rule fix (exact sentence proposed in the handoff)
Classify per **occurrence** (tokenize NAME/attribute/keyword) inside the **cited line range**, excluding STRING, f-string parts (`FSTRING_START/MIDDLE/END`), COMMENT and every continuation line of a multi-line string; never per line. Under it the census is unchanged, `raising` stays PROSE, and a new anchor is classifiable without asking the author.

## Not reproduced / overstated / unverified
- **not_reproduced**: §5 probe C as literally described (minimal `scope=`→`grant=` edit is ACCEPTED by R2).
- **overstated**: "refuses them for the right reason" (C depends on a global substring edit); "not a blanket pass" (probe E passes); "recomputable without trusting this paragraph" (only on 3.12+, and not for f-string/continuation occurrences).
- **unverified**: the declared freeze instant itself (no earlier snapshot of the rule text); interpreters other than CPython 3.14.4; §6 Task-4 counts; `grade_v4.py` (forbidden).
