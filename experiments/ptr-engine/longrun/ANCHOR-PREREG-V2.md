# ANCHOR-PREREG-V2 — rule R2.1 (supersedes R2; R2 is never rewritten)

**Status:** FROZEN / DESIGN-ONLY. Zero live requests, no re-grade of any arm, no new
accuracy number, no arm comparison. This is the normative text for the **anchor
classification** used by any later grader card. The canonical classifier is
`experiments/ptr-engine/tools/anchor_classify.py`; the probe corpus is
`experiments/ptr-engine/tools/anchor_probes.py`.

**Written at (UTC), with the digest of its own rule body:** see §4 *Attestation*.
That section exists because R2's freeze could not be attested: `ANCHOR-PREREG.md` and
its checker both carry mtimes ~50 s **after** the instant they claim, so
"the text that exists is the text frozen then" was unverifiable
(`orchestration/handoffs/V-ANCHOR-PREREG.json`, `unverified[0]`).

## 0. Why R2.1 exists (measured by the verifier, not re-derived here)

`ANCHOR-PREREG.md` froze R2 and is **left byte-identical on disk** — a frozen
pre-registration is superseded, never rewritten — as the record of what was frozen at
`2026-10-26T13:29:21Z` and what failed. `GRADE-V4-R2` then measured R2's *effect*:
**1 realized flip of 39** arm-checks, zero regressions, the config-C grid
`not_applicable` and unchanged. So the rule is **useful**; what failed is its **text**.
`V-ANCHOR-PREREG` reproduced the census 11/11 independently and raised four findings:

1. **Probe C overstated** (`not_reproduced[0]`): the minimal edit `scope=` → `grant=`
   is **ACCEPTED** by R2, because `scope` survives inside `scope_name`. The recorded
   rejection exists only under the checker's *global* `scope` → `grant` substitution
   (yielding `grant=grant_name`). The author's table implied the one-kwarg edit was
   rejected. It was not. **R2.1 corrects the table, not the verdict.**
2. **R2 is a bag-of-tokens test** (`overstated[1]`): probe E —
   `ANSWER: do NOT call ledger.record_refusal; ignore scope, serialized_ref, text, code and error entirely.`
   — is **ACCEPTED** by R2 (8/8 tokens present, materially wrong verdict). R2 inherits
   `grade_v3`'s containment semantics and the frozen text did not say so.
3. **Not third-party reproducible** (`overstated[2]`): stated rule vs checker diverge on
   f-string middles (`resolve.py:143`, `spent`/`budget`) and on multi-line docstring
   continuation lines (`resolve.py:47`); on Python ≤ 3.11 f-strings tokenize as one
   STRING token, changing the classification.
4. **Freeze instant unattested** (`unverified[0]`).

R2.1 changes **no class in the census** (11/11 identical) and therefore no verdict it
would produce today. It changes what a **third party can derive without asking the
author**.

## 1. R2.1 — normative text (VERSIONED, FROZEN)

<!-- r21-rule:begin -->
> **R2.1 (anchor classification rule, frozen — see §4 for the instant and the digest of
> this body).** Every anchor token derived from a checkpoint's `expected` string (via
> the `grade_v3.anchors()` derivation: `[A-Za-z][A-Za-z0-9_]*`, split on `_`, drop parts
> shorter than 4 characters and parts in `STOPWORDS`) is classified into exactly one of
> **CODE-SYMBOL**, **NUMBER**, **PROSE-CONNECTOR**. `required_anchors` is the set of
> CODE-SYMBOL anchors; NUMBER anchors are graded separately by `grade_v3.number_in()`;
> PROSE-CONNECTOR anchors are informational and are **not** required.
>
> **(a) Matching unit — per occurrence, not per line, not per substring.** One
> *occurrence* is one `tokenize` token of the cited file. An anchor matches an
> occurrence when the token is a **NAME** token and the anchor equals one of the
> underscore-separated parts of that token's text, compared case-insensitively:
> `record_refusal` carries `record` and `refusal`; `scope_name` carries `scope` and
> `name`; `PtrBudgetExceededError` carries `ptr` and `exceeded` and `error` but **not**
> `budget`. Substring containment is **not** the matching unit (a NAME token
> `no_record` does carry `record`; a NAME token `recordx` does **not**).
>
> **(b) Range scope.** Only occurrences whose line lies inside the checkpoint's cited
> line range `path#Lstart-Lend` count. A citation carrying a single line (`#L39`) is a
> one-line range. A citation carrying no line fragment scopes to the whole file. The
> cited file is the only file consulted.
>
> **(c) What counts as a code occurrence.** A NAME token inside the range — an
> identifier, an attribute name, a parameter name, a keyword, an imported name, or a
> name used inside an f-string **replacement field** (`f"{ledger.count()}"` on
> CPython ≥ 3.12). A token of type NUMBER, OP, INDENT, DEDENT, NEWLINE, NL or ENCODING
> establishes nothing about an identifier anchor.
>
> **(d) What does not count.** Any occurrence inside a token of type **STRING**
> (a docstring, *including every continuation line of a multi-line docstring*), type
> **COMMENT**, or type **FSTRING_START / FSTRING_MIDDLE / FSTRING_END**. The decision
> is made **per occurrence**: on a line that carries both a string literal and code,
> only the code occurrence counts; a continuation line of a docstring that sits between
> two code lines is **prose**, not code.
>
> **(e) The three classes.**
> *CODE-SYMBOL* — at least one counting code occurrence exists under (a)–(d).
> *NUMBER* — the anchor is a decimal integer literal, decided by the anchor's **own
> form** (it came from a numeric token of `expected`), never by the source; source
> evidence is corroboration: the literal's line when the range contains the literal, or
> — when it does not — the count of top-level `class ` definitions that establishes the
> value, reported as `first-last`.
> *PROSE-CONNECTOR* — every occurrence in the range is prose under (d), **or** the
> anchor does not occur in the range at all. This is decided on occurrence context, not
> on absence (R2 §1.1's amendment, retained: `raising` *does* occur in
> `resolve.py`, at `resolve.py:67`, inside a docstring; it is prose because of the
> context, not because it is missing).
>
> **(f) Evidence.** The class must be reported with the `file:line` of its first
> counting occurrence (CODE-SYMBOL), its establishing line(s) (NUMBER), or the
> `file:line` of its prose occurrence(s) with the token kind (PROSE-CONNECTOR). No cell
> may be reported without evidence.
>
> **(g) What R2.1 judges — and what it does not.** R2.1 governs **which tokens must
> appear** in the `^ANSWER:` marker line. It does **not** check that the answer is
> semantically correct. A sentence that negates everything while naming every anchor
> passes (probe E in §3). That is a **known, accepted limitation** of a mention-based
> checkpoint metric. It is to be complemented by a semantic tier, which is a separate
> card; it is never to be silently upgraded into a semantic check, and no result
> produced under R2.1 may be described as a semantic pass.
<!-- r21-rule:end -->

### 1.1 Worked examples (the three cases that diverged today)

All three were **measured** on CPython 3.14.4 with
`experiments/ptr-engine/tools/anchor_classify.py`; the reproduction command is in §4.

| anchor | citation | R2 (frozen) said | R2.1 says | why |
|---|---|---|---|---|
| `raising` | `resolve.py#L66-L71` | PROSE-CONNECTOR :67 | **PROSE-CONNECTOR** :67 | sole occurrence is the one-line docstring on `:67`; both agree — this is the *only* anchor R2 and R2.1 classify identically for identical reasons |
| `spent` | `resolve.py` (whole file) | CODE-SYMBOL `:143` | **PROSE-CONNECTOR** :143 | `:143` is `f"resolve budget spent: {…}"`; the word sits in an **FSTRING_MIDDLE** token. R2's checker collected prose by the *start line of STRING/COMMENT tokens only* and FSTRING_MIDDLE is not a STRING type, so the line looked like code |
| `budget` | `resolve.py` (whole file) | CODE-SYMBOL `:47`, `:143` | **PROSE-CONNECTOR** `:36`, `:47`, `:143` | `:47` is a **continuation line** of the docstring opened at `:44` and closed at `:50`; `tokenize` emits **one STRING token spanning 44–50**, while R2's checker keyed on that token's start line (`:44`), leaving `:47` unmarked and therefore "code". Its three occurrences are one COMMENT (`:36`), one docstring continuation (`:47`) and one f-string middle (`:143`) — and `:142` `PtrBudgetExceededError` does **not** carry `budget`, because it has no underscore |

A worked **range** example, because §1(b) is new relative to the frozen census:

* `ledger` — cited range `resolve.py#L66-L71`; first counting occurrence **`:66`**
  (`def _refuse(ledger: Optional[Ledger], …)`). File-wide it first occurs at `:33`
  (`from .ledger import Ledger`), which is what the frozen census recorded. **Same
  class, different, now-reproducible evidence line.**
* `scope` — in range, first counting occurrence **`:66`** (`scope_name: str`
  parameter). File-wide first is `:43` (`class Scope`). Same class again.
* `record` / `refusal` — one NAME token `record_refusal` at `:69` inside the range
  contributes **both** anchors. File-wide `record` also occurs in `record_resolution`
  at `:159`; class unchanged.

**The census is unchanged 11/11 on class**; only `ledger` and `scope` change their
*evidence* line, because R2.1's scope is the cited range and R2's was the whole file.
That difference is stated here rather than papered over: R2.1 does not "fix" the
census, it makes the same 11 classes derivable from the text alone.

### 1.2 The scope limit of the metric, in so many words

R2.1 is a **mention-based** checkpoint metric. It checks that the answer's marker line
**names** every required token. It does not read the sentence. Therefore:

* `ANSWER: do NOT call ledger.record_refusal; ignore scope, serialized_ref, text, code and error entirely.`
  — every required token present, meaning inverted — is **ACCEPTED** by R2.1.
* Any answer that reverses the call's meaning while keeping the tokens is accepted. The
  probe corpus records this twice (probes E and F) and stamps every result with
  `metric: mention-only` and `semantic: false` so no later reader can quote an
  acceptance as a semantic verdict.
* This is a **known, accepted limitation** of the metric, not a defect to be quietly
  patched by adding words to the anchor list (that would be fitting the rule to
  outputs). The complement is a **semantic tier** — a separate card, with its own
  pre-registration.

### 1.3 Interpreter pin

Classification is deterministic under **CPython ≥ 3.12**, and every number in this
document was measured on **CPython 3.14.4** (the only interpreter on this host). The
pin exists because `tokenize` changed in 3.12: f-strings gained
`FSTRING_START` / `FSTRING_MIDDLE` / `FSTRING_END` tokens and their replacement fields
became ordinary NAME tokens.

**What changes below 3.11** (reasoned from the tokenizer's documented behaviour, *not*
measured on this host — there is no ≤ 3.11 interpreter here):

1. an f-string is **one STRING token**; its replacement fields are no longer NAME
   tokens. Consequence: an anchor occurring **only** inside `f"{…}"` would be
   PROSE-CONNECTOR below 3.12 and CODE-SYMBOL on ≥ 3.12. Inside the V6 fixture this
   changes **nothing**: every census anchor also occurs in plain code at
   `resolve.py:66-70`, so the 11 cells are version-invariant. That invariance was
   checked against the 11 cells, not assumed for arbitrary new anchors.
2. the word `spent` in `f"resolve budget spent: …"` is prose under **both**
   interpretations (whole f-string = STRING below 3.12; FSTRING_MIDDLE on ≥ 3.12), so
   the f-string family in §1.1 is classified identically; only the reported token
   *kind* differs (`string` vs `fstring-middle`).

## 2. The canonical classifier and the census it must reproduce

`experiments/ptr-engine/tools/anchor_classify.py` is the **one** implementation of
R2.1: `classify(anchor, source_path)` returns a `Classification` whose `.cls` is
`CODE_SYMBOL` / `NUMBER` / `PROSE_CONNECTOR` and whose `.occurrence_lines` /
`.occurrences` carry the lines the decision was made on, so no caller re-implements the
rule. It is **not** `anchor_prereg_check.py` copied and patched: that file is untouched,
still exits 0 against the frozen R2 doc, and remains the checker for R2. The only thing
carried over is the anchor *derivation*, re-implemented from its description and pinned
to `grade_v3.anchors()` by an equality assertion in the test suite.

Census reproduced by `classify()` — 11 cells, compared on
`(checkpoint, anchor, class)` against `ANCHOR-PREREG.md` §3:

<!-- census-v2:begin -->
| checkpoint | anchor | class | evidence |
|---|---|---|---|
| cp.0.t12 | 64 | NUMBER | `experiments/ptr-engine/ptr_engine/resolve.py#L39` literal at `:39` |
| cp.1.t24 | 31 | NUMBER | `experiments/ptr-engine/ptr_engine/errors.py#L15-L250` class-count `:15-:247` |
| cp.2.t46 | ledger | CODE-SYMBOL | `resolve.py#L66-L71` `:66` |
| cp.2.t46 | record | CODE-SYMBOL | `resolve.py#L66-L71` `:69` (`record_refusal`) |
| cp.2.t46 | refusal | CODE-SYMBOL | `resolve.py#L66-L71` `:69` (`record_refusal`) |
| cp.2.t46 | scope | CODE-SYMBOL | `resolve.py#L66-L71` `:66` (`scope_name` parameter) |
| cp.2.t46 | serialized | CODE-SYMBOL | `resolve.py#L66-L71` `:70` (`serialized_ref`) |
| cp.2.t46 | text | CODE-SYMBOL | `resolve.py#L66-L71` `:66` (parameter) |
| cp.2.t46 | code | CODE-SYMBOL | `resolve.py#L66-L71` `:70` (`error.code`) |
| cp.2.t46 | error | CODE-SYMBOL | `resolve.py#L66-L71` `:66` (parameter) |
| cp.2.t46 | raising | PROSE-CONNECTOR | `resolve.py#L66-L71` `:67` (docstring, STRING) |
<!-- census-v2:end -->

Totals: **11 cells — 2 NUMBER, 8 CODE-SYMBOL, 1 PROSE-CONNECTOR**, identical to the
frozen census on class. Both v4 fixtures (`LR-01.v4.json`, `LR-01.v4.tools2.json`)
declare byte-equal `checkpoints` arrays, so they produce this one census.

## 3. The probe corpus (`tools/anchor_probes.py`)

Every probe carries the classifier's occurrence evidence and the declared metric. The
runner exits non-zero on any mismatch.

| probe | answer | R2.1 | why |
|---|---|---|---|
| **A** | the real V6 `cp.2.t46` row, loaded from `measure/rows-longrun-v6-tools.jsonl` (content sha256 `ecdb3fc9d9f0…`, the same text whose excerpt the grade file records) | **ACCEPT** | all 8 required tokens present; R1 rejected it solely on `raising` |
| **B** | A with `record_refusal` → `write_audit` | **REJECT** | missing `record`, `refusal` |
| **C-minimal** | A with `scope=` → `grant=` **only** (the edit R2's §5 table described) | **ACCEPT — labelled ACCEPT** | `scope` survives in `scope_name`. The rejection the author reported came from a **global** `scope` → `grant` substitution, not from this edit |
| **C-global** | A with every `scope` → `grant` (`grant=grant_name`) | **REJECT** | missing `scope` |
| **E** | the verifier's negation probe | **ACCEPT**, `metric: mention-only`, `semantic: false` | all 8 tokens present, meaning inverted; the declared limitation, not a semantic failure of the arm |
| **F** | keeps every anchor, inverts the guard and swaps the arguments (`ledger.record_refusal(scope=text, serialized_ref=scope_name, code=error.code)` prefixed by a `when ledger is None` clause) | **ACCEPT** | every required token is present, and a mention-only metric must accept it; the answer is materially wrong, which is exactly the limitation §1.2 declares |

Probe C-minimal is the correction to the author's table. No probe was weakened to make
it pass; where the honest verdict was inconvenient (C-minimal, E, F), the **verdict**
changed and the limitation was written into the rule text.

## 4. Attestation (the gap that made R2's freeze unverifiable)

The digest below is the sha256 of **the R2.1 rule body only** — the lines strictly
between `<!-- r21-rule:begin -->` and `<!-- r21-rule:end -->` in §1, joined with `\n`
and terminated by one `\n`, read as UTF-8, nothing stripped. Because the digest is
recorded *outside* the delimited body, it is stable and checkable by anyone:

```
python3 -c "import sys; sys.path.insert(0,'experiments/ptr-engine/tools'); \
import anchor_classify as c; \
print(c.rule_digest('experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md'))"
```

- written at (UTC): `2026-10-26T13:46:53Z` — the instant the rule body was hashed. Nothing inside
  the delimited body changed afterwards, and the test suite asserts the digest, so any
  later edit to it breaks `test_rule_digest_is_recorded_in_the_doc` rather than
  silently diverging from the attested text.
- sha256 of the R2.1 rule body (§1, delimited): `b16548301589593b8d1041325fce833ef60d3b39b8e8c0a205084ee35eb9ad57`
- sha256 of the superseded, byte-unchanged `ANCHOR-PREREG.md`: `77ff76b0d167f8b36c7208b554bdbfb5e771b44ee5b52aa91acd6140b13b7584`

## 5. Provenance (re-computed; equals the frozen doc's §7 where both list a file)

| file | sha256 |
|---|---|
| `experiments/ptr-engine/longrun/ANCHOR-PREREG.md` | `77ff76b0d167f8b36c7208b554bdbfb5e771b44ee5b52aa91acd6140b13b7584` |
| `experiments/ptr-engine/tools/anchor_prereg_check.py` | `c3a17b6cb3ef82ec440e20a0abcd2efcbaab790e0ea9d96caae716f8d822012e` |
| `experiments/ptr-engine/ptr_engine/resolve.py` | `71a14c2c1dd1b6e97b3fdf2a666ea459d093adcd0f813676cf787271a48da563` |
| `experiments/ptr-engine/ptr_engine/errors.py` | `402dc9589d8e8fd5de82ed6c8f3364390e105bf8285eb7c326b799f8200fdba0` |
| `experiments/ptr-engine/longrun/grade_v3.py` | `7bfc11f4443ec7f3c191465715ed1a35f7464ffd8301a8b2b6320bab63411bf9` |
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json` | `5a5f8c4be2027c53038ae31b4db60ebbae03996a5a650d8fb4fe6d872df5e235` |
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json` | `5bf5f6393946b89bce4c1e28c1d117f713eb40a191253a5549fefff36a2e6945` |
| `experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json` | `ace2e956280c78fb53d08fee6ae09b5435889c7b55815358edc3304ceef3dc44` |

## 6. Non-goals (frozen)

R2.1 does **not**: relax the `^ANSWER:` marker requirement or the concluding-position
test; change any `expected` string, checkpoint, turn or citation; apply to, re-score or
re-grade any existing row or arm (that is a **later card**); publish any accuracy
number or arm comparison; edit `ANCHOR-PREREG.md`, `anchor_prereg_check.py`,
`grade_v3.py`, `grade_v4.py`, any fixture, or any row/grade file. The classifier is
**text made operational**, not a grader: it classifies anchors and judges a marker line
under the mention metric, and it writes nothing.

## 7. Acceptance

1. `python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py` exits 0:
   the 11-cell census, the f-string case, the multi-line docstring case, the range
   scoping, and a **red case** that fails when the matcher is degraded to substring
   containment.
2. `python3 experiments/ptr-engine/tools/anchor_probes.py` exits 0 with the verdicts in
   §3 (A ACCEPT, B REJECT, C-minimal ACCEPT, C-global REJECT, E ACCEPT, F ACCEPT), each
   carrying occurrence evidence.
3. §4's digest reproduces from the command shown there.
