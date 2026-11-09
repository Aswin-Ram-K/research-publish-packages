# PREREGISTRATION — G46 (unit G33)

**Written:** before any per-case recorded label (`correct:`) was read by unit G33.
**Status:** FROZEN. Never edited after the first comparison was run. If a revision were ever
needed, it would be appended as a dated addendum and the original text kept verbatim.

## 0. What this experiment is, and what it is NOT

This is a **machine re-labelling baseline and a disagreement catalogue** over
`P05` in the read-only target `the read-only target repository`.

**It is NOT an inter-annotator-agreement study.** A model-generated second pass is not an
independent human annotator. It cannot establish IAA in the sense a reviewer means when they
ask "did two people independently agree?". Every artifact this unit writes must carry this
limitation in the `UNVERIFIED` register; a bare "kappa = X" presented as IAA would be an
overclaim and is forbidden here.

What a second machine pass *can* honestly license is narrower: a lower bound on how much the
labels are a matter of convention rather than of computation, a catalogue of the specific cases
where a competent second reader lands elsewhere, and evidence for or against the presence of
the *mechanical* defect classes (label outside option set, duplicate ids, malformed rows).

## 1. Disclosure — what was seen before freezing

Honesty about blinding matters more than the appearance of it. Before freezing this file, G33
inspected **structure only**:

- `head -12`, `sed -n '12,48p'`, `tail -12`, `sed -n '49,80p'` of the fixture (the file header
  comment, the `S12` / `S02` type declarations, the array opening, and one
  trailing record).
- A field-name census with **values suppressed** (`grep -oE '^[[:space:]]*[A-Za-z_]*:'`).

This was necessary to write a parser that does not guess at the file's structure, as the unit
card requires. Consequences, stated plainly:

1. The interface declaration and the one trailing record (`N06-026`) were visible. That
   is **one** per-case label seen in advance, out of 190. It is recorded here rather than
   concealed. If `N06-026` were held out of the primary agreement statistic, the
   headline number would move by at most 1/190 ≈ 0.5 pp; no such exclusion is applied, because
   the honest move is to disclose and keep the case in.
2. The file header states a **count** ("These 190 cases are a seed") and an **aggregate**
   ("28 cases have G11 as the label"). Aggregates were therefore known in advance.
   Aggregates do not determine per-case labels, but they are disclosed for the same reason.
3. No per-case `correct:` value, and no `rationale:` text, was read before this file was
   written.

## 2. Route A — the deterministic rule (pre-registered, mechanical)

Route A must be a rule a machine executes with no judgement, so that its output is exactly
reproducible from the fixture text. It is fixed as follows, and **this text is the definition**.

Given a case with question text `Q` and option list `O[0..n-1]`:

1. **Tokenisation.** Lower-case `Q` and each option. Extract token sequences matching
   `[a-z0-9]+`. Discard nothing else (no stop-word list — a stop-word list would be an
   undeclared judgement knob).
2. **Option token set.** For option `o`, tokens are the `[a-z0-9]+` matches of `o`. An option
   with no alphanumeric token (e.g. a pure-symbol option) is handled by rule 5.
3. **Score.** `score(o) = |tokens(o) ∩ tokens(Q)|` — the count of *distinct* option tokens that
   also appear anywhere in the question. A multi-word option therefore scores at most
   `len(tokens(o))`.
4. **Substring bonus.** `+0.5` if the full option string, lower-cased and whitespace-collapsed,
   occurs as a substring of the lower-cased whitespace-collapsed `Q`. This is a distinct
   signal from token overlap (it rewards phrase-level presence) and is applied before the
   argmax.
5. **Degenerate cases.** If `n == 1`, the label is index `0` — the case is trivially labelable
   and Route A cannot disagree with any well-formed label. If no option scores above `0`, the
   label is index `0` (argmax over an all-zero vector, lowest index wins).
6. **Tie-break.** Highest score wins; on a tie, the **lowest option index** wins. Ties are
   counted and reported separately, because a tie is Route A admitting it cannot decide.

Route A's known weakness, pre-registered so it cannot be spun after the fact: short semantic
options (`G11`, `G19`, `G21`) are runtime *decisions*, and a question often
describes the situation without naming the decision. Route A is expected to score **low**.
A low Route A agreement is therefore **not** evidence that the recorded labels are wrong; it is
evidence that the labels are not recoverable by surface lexical overlap. That distinction is
fixed here, in advance.

## 3. Route B — the blind model second pass (pre-registered protocol)

Route B is the primary second labeller: a **separate agent** (fresh context, not the parent
G33 session), given the blinded case list and nothing else. Its blindness is enforced
structurally: the blinded input file contains `id`, `kind`, `question` and `options` only —
**`correct` and `rationale` are stripped**, because the rationale states why the recorded answer
is right and would leak the label.

**Pre-registered Route B prompt (verbatim, fixed before results):**

> You are a second labeller for a reflex-tier decision fixture. Read
> `G46/blinded_cases.json`.
> For every case, choose the single most defensible label from that case's own `options` array,
> using only the `question` text and the option semantics. Rules: (1) choose exactly one option;
> (2) the answer must be an index into that case's own options; (3) if two options seem equally
> defensible, choose the one you would defend to a reviewer and do not abstain; (4) do not read
> any other file, and specifically do not open `D07.sandbox.ts` or `cases.json` —
> doing so destroys the experiment's validity. Write your answers to
> `G46/labelsB.json` as exactly
> `{"labeller":"routeB-blind-model","labels":{"<id>": <index>, ...}}` — a single JSON object, one
> entry per case, all 190 ids present.

Route B carries **no** knowledge of the recorded labels, of Route A's output, or of the header's
aggregates. Route B is a model pass and is labelled as such everywhere it is reported.

## 4. Metrics — pre-registered definitions and interpretation

Computed over the cases both routes could label (all of them; neither route is permitted to
abstain):

- **Agreement** = (cases where Route X's index equals the recorded index) / N.
- **Cohen's kappa** between recorded labels and Route X labels, over the full label vocabulary
  actually used, with the standard `po`/`pe` formula; `pe` from the product of marginal
  proportions. Kappa is reported with its own caveat: with 2–8 categories and a skewed
  marginal, kappa is depressed mechanically, and it is undefined if `pe = 1`.
- **Disagreement catalogue** = every case where Route B (primary) differs from the recorded
  label, carrying the id, both labels, the question, the recorded rationale, and G33's
  judgement of which is defensible and why.

**Pre-registered interpretation ladder** (so the verdict is not written after seeing the number):

| Outcome | What it licenses |
|---|---|
| Route B agreement ≥ 0.90 and κ ≥ 0.85 | The labels are largely recoverable by a competent independent reader. Label noise is *probably* small. Does **not** establish IAA; does not make a reviewer accept external validity. |
| 0.75 ≤ agreement < 0.90 | Substantial but non-trivial divergence. The disagreement catalogue is the deliverable; per-case adjudication is needed before the fixture is leaned on by four papers. |
| Agreement < 0.75 | Either the labels are noisy or the task is genuinely convention-bound. **Cannot distinguish those two from a machine pass alone** — this is the honest ceiling of the method and must be stated as such, not resolved by assertion. |

**Neither outcome licenses the sentence "the fixture's labels are sound"** or "the fixture's
labels are noisy" as a settled claim. Both are, at best, *reduced risk* for the specific
mechanical defects and *a catalogue* for the semantic ones.

## 5. Defect checks — pre-registered, mechanical, and independent of agreement

These are checked against the fixture text directly and are the strongest results this
experiment can produce, because they need no annotator at all:

1. **`answer ∉ option set`** — any case with `correct < 0` or `correct >= len(options)`. This is
   the class the corpus already flagged as `F-EXP11-11`; a hit here is a **headline** finding.
2. **Duplicate `id`** across cases.
3. **Duplicate or near-duplicate `question`** (exact match after whitespace/case normalisation;
   near-duplicate at `difflib.SequenceMatcher.ratio() ≥ 0.90`), reported with pairs.
4. **Malformed / unparsable row** — any record block where a required field fails to parse, or
   where `options` is empty, or `options` has fewer than 2 or more than 8 entries (the header
   declares "2-8 (never more)").
5. **Declared-vs-actual count** — the header declares 190 cases; the parser reports the true
   count. A mismatch is a documentation defect, not a label defect.

Defects are **recorded, never fixed in the target**. The target is read-only; these are owed
corrections for the subject to make.

## 6. Stopping rule

If the fixture cannot be parsed without guessing at its structure, STOP and report that rather
than inventing a reading. (It parsed; the parser reports per-field failures rather than
silently coercing them.)
