# ENGINE-R2 — the shape search: cut the index before you pad the prompt

**Unit:** ENGINE-R2 · **Every number in this file is PREDICTED.** No request was sent: `:8012`
belongs to another unit and `:8014` is taken, so this unit had **no measurement budget**. The
numbers come from the law in `experiments/miss-law/LAW.md` applied to token counts computed
**offline**. A later unit measures the recommendation live; until it does, nothing here is a
measurement, and nothing here is described as one.

**Generator:** `measure/shape_search.py` (offline, deterministic, imports the shipped
`choose_shape` rather than re-implementing it) → `measure/shape-search.json`.
**Contract:** `ptr_engine/quantise.py::choose_shape` / `cycle_bill` / `quick_bill`.
**Tests:** `tests/test_quantise.py` — 63 passed (was 45); full suite **171 passed** (baseline 153).

---

## 0. The answer, before the evidence

**PREDICTED: for this corpus the free-residue idea does not reach a cheap residue, and the search
does not invent one.** The compact index is the cheapest shape available *unpadded* (PREDICTED
−12 per cycle against the full index), but whether it lands on a cheap residue depends on a ~400-token
corpus whose positions are **not pinned**, and the three calibration stubs tried here disagree on the
answer. The engine therefore **pads conditionally, and says so**: the prediction tables below show
it padding 11 tokens to reach residue 2 on one reading and refusing to pad at all on the other.

What this unit actually delivers is the decision procedure, not a win: a search that scores
`(P1 mod B) + L` over every shape and padding depth instead of taking the first shape that hits
residue 2, that never returns a shape on the avalanche, and that reports which capability a cut
cost. Section 5 says exactly what a live unit must measure to settle the corpus question.

## 1. Why padding had to become a comparison

Padding raises `P1` by `k` and lowers the tail by `k` of residue, but each token of filler is paid
**once** (it lives in `P1`) while each token of tail is paid **every append**. Writing the cycle
bill `P1 + (P1 mod B) + L` for a variant whose residue is `r`, padded to target 2 with `k = (2 - r) mod B`:

```
unpadded : B0 + r + L
padded   : B0 + k + 2 + L          with B0 the unpadded base
padded wins  <=>  k + 2 < r  <=>  r > (66 / 2) = 33
```

So there is one clean line in the residue space, and it depends only on `B`, not on the corpus,
the tokenizer, or `L`:

| residue `r` | filler to residue 2 | tail saved | padding pays? |
|---:|---:|---:|---|
| 0, 1 | 2, 1 | the whole prefix | **yes** — dodges the avalanche |
| 2 | 0 | 0 | nothing to do |
| 3 … 32 | 63 … 34 | 1 … 30 | **no** — costs 32…4 per cycle (ENGINE-R1 measured this band: +36 and +58) |
| 33 | 33 | 31 | **no**, by one token |
| 34 … 63 | 32 … 3 | 32 … 61 | **yes** — saves 0…58 per cycle |

`PAD_FOR_FREE_RESIDUE = 33` in `quantise.py` is this line. ENGINE-R1's "pads only at residue ≥ 35"
was the same line computed with `k >= r - k` written out; it is restated here as *the search's
arithmetic*, not as a host's policy — the search computes both and lets the law pick.

### 1.1 The thing ENGINE-R1 got right about the compact index

The compact index is **64 bytes / 53 prompt tokens smaller** (PREDICTED here, MEASURED in
ENGINE-R1's cell D). Two consequences, both real:

* **Cutting is always a candidate.** A shorter variant is a *free* residue move: it can land on a
  legal residue, on residue 2 itself, or on a residue far from the avalanche, without spending a
  single filler token. `choose_shape` therefore always scores every variant **unpadded first**.
* **Cutting can also be the cheaper way to residue 2.** A cell-D measurement says 50 filler tokens
  took a 272-token prefix to 322; the unpadded 272 is residue 16 and bills 301, and the padded 322
  bills 337. Padding cost 36 for 14 of tail — the small-residue band, exactly as section 1 says.

## 2. The token counts, and where they come from

The card asked for a deterministic stub **calibrated against ENGINE-R1's two anchors**, and for the
residual to be stated. Doing that honestly produced the central finding: **the anchors cannot both be
met by any counter of this corpus's text.**

The anchors, MEASURED by ENGINE-R1 on the live server:

| anchor | measured `P1` | residue |
|---|---:|---:|
| full index as `worked_example.py` compiles it | **325** | 5 |
| compact index + 50 filler tokens | **322** | 16 |
| ⟹ compact index alone (the brief's derivation, `322 − 50 = 272`) | **272** — *derived, not measured* | 16 |

Facts about the two texts, computed offline from `compile_turn` (MEASURED byte counts, offline):

| | full | compact | difference |
|---|---:|---:|---:|
| index bytes | **447** (ENGINE-R1 also measured 447) | **383** | −64 |
| index words (whitespace tokens) | 53 | 42 | **−11** |
| envelope bytes | 472 | 408 | −64 |
| envelope words | 55 | 44 | −11 |

**The contradiction.** ENGINE-R1's two main-text anchors put the full index at 325 and the compact at
272 — a difference of **53 tokens for 11 fewer words**. The measurement that connects them, cell D,
adds 50 filler tokens to the compact index to move 16 → 2. A filler token is one token (that is what
`" the"` was chosen for). Two statements cannot both be true:

* cutting 53 tokens is what the compact form saves (main-text anchors), **or**
* every filler token is one token (cell D, and legal as a matter of how `/v1/tokenize` behaves).

### 2.1 Three readings, and what none of them can do

`measure/shape_search.py` reports all three so a reader can see the choice being made. **All three
are stubs.** None counts anything the server would count; each was fitted to two measured numbers
and then prints the residual that fitting did not remove.

**(a) `calibrated-anchor`** — `tokens = ⌈(words + 1.0·bytes)/2⌉ + 324`: word merges and byte splits
summed as equals, halved, plus the constant that puts the full index on ENGINE-R1's 325.

| ENGINE-R1 anchor | stub | residual |
|---|---:|---:|
| full index `P1` = 325, residue 5 | 574 → residue **62** | **breaks: not residue 5** |
| one filler token | +3 tokens | **breaks: not 1** |
| compact + 50 filler residue 16 | 22 | **breaks: not 16** |
| compact `P1` = 272, residue 16 | 537 | **breaks: not 16** |

It meets the *length* of the first anchor only by construction. It is kept in the report precisely
because it shows what a plausible-looking stub does when the anchors are incompatible: it conforms to
one and breaks three.

**(b) `words-only`** — one token per whitespace word, the engine's own `StubTokenizer` model, no
free parameters. It meets the full-index anchor *shape* exactly (`P1 = 55`, filler `+1 token`) and
sits at residue 55, not 5, because it lacks the ~270-token constant that the real prompt carries
(user message + template framing + the bytes-vs-words rate). It is shown because every test in the
suite uses this model and the reader should see how much the table depends on it.

**(c) `main-text-with-D`** — one token per whitespace word plus a constant `D` solved so the compact
index lands on the brief's 272. `D = 228`. It meets both main-text anchors by construction (325 and
272) and **still breaks cell D**: 50 filler tokens of `" the"` add 50 words and ~200 bytes, and no
additive-constant model can turn 200 extra bytes into 0 extra tokens.

The honest statement of the residual: **the two main-text anchors and the cell-D anchor are mutually
inconsistent for any stub of this corpus's text, and the engine has no real tokenizer offline.**
A stub that fits the anchors explains 3 of 4 numbers at best.

### 2.2 What the search's *decisions* do and do not depend on

The padding line in section 1 is exactly the same rule under all three readings. What changes
between readings is only *which residue each variant happens to sit on* — and that is a property of
the corpus, not of the engine. This is why the deliverable is the procedure plus a live-measurement
plan, not a claimed win.

## 3. The candidate table — PREDICTED

### 3.1 `words-only` stub (L = 13, ENGINE-R1's measured append, B = 64)

| variant | form | base | pad | `P1` | residue | uncached | cycle bill | Δ vs full | flags |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| full | full | 55 | 11 | 66 | 2 | 15 | **81** | −42 | reference |
| compact | compact | 44 | 22 | 66 | 2 | 15 | 81 | −42 | |
| compact+cut-projection | compact | 44 | 22 | 66 | 2 | 15 | 81 | −42 | cuts-capability |
| compact | compact | 44 | 0 | 44 | 44 | 57 | 101 | −22 | free |
| compact+cut-projection | compact | 44 | 0 | 44 | 44 | 57 | 101 | −22 | free cuts-capability |
| full | full | 55 | 0 | 55 | 55 | 68 | 123 | +0 | reference free |
| full | full | 55 | 8 | 63 | 63 | 76 | 139 | +16 | |
| compact | compact | 44 | 19 | 63 | 63 | 76 | 139 | +16 | |
| compact+cut-projection | compact | 44 | 19 | 63 | 63 | 76 | 139 | +16 | cuts-capability |

Chosen: **full, 11 tokens of filler, PREDICTED cycle 81** — and the search says so:
*"PADDED: full sits at residue 55; 11 inert token(s) take it to 2, which is cheaper once the tail is
paid (101 → 81 predicted)"*. Padding is chosen because 11 < 55, not because the target was 2. The
`compact` variant reaches the same bill with 22 filler instead of 11; it is **not** better, and under
this reading the compact cut saves nothing here because both shapes are padded to the same `P1`.

### 3.2 `calibrated-anchor` stub (L = 13, B = 64)

| variant | form | base | pad | `P1` | residue | uncached | cycle bill | Δ vs full | flags |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| compact | compact | 550 | 0 | 550 | 38 | 51 | **601** | −12 | free **chosen** |
| full | full | 588 | 0 | 588 | 12 | 25 | 613 | +0 | reference free |
| compact+cut-projection | compact | 610 | 0 | 610 | 34 | 47 | 657 | +44 | free cuts-capability |

Chosen: **compact, no padding** — *"NO PADDING: compact lands on residue 38 unpadded; no shape reached
a cheap residue at an acceptable bill"*. Every variant sits in the 3…32 band where filler costs more
than the tail it saves, so padding is correctly refused and the free cut wins by 12. **This is the
case the card anticipated**: the free-residue idea does not reach a cheap residue for this corpus —
the compact form moves the residue but does not make it cheap — and the search declines to pay for a
journey that would cost more than it saves.

### 3.3 `main-text-with-D` stub (L = 13, B = 64)

Identical to 3.1: word counts are the same, the constant cancels in the residue. Reported anyway so
the reader sees that the *decision* is invariant to the additive constant — which is the property
that makes 3.1 and 3.2 the two readings that matter.

### 3.4 The projection variant, and what it costs

`projection_variant(index_text)` shortens each line's 8-hex body digest to its first character,
declaring the capability it loses: **the line stops being a verifiable handle** — a host can no
longer tell a stale line from a fresh one by prefix, and the model's echo of the line can no longer
be checked against the body. `store.get` still re-hashes the full sha256, so *which bytes* a ref
designates does not change.

| reading | Δ bytes on the index body | Δ tokens | Δ cycle bill (PREDICTED) |
|---|---:|---:|---:|
| statement about the text | −12 bytes (1 of 8 hex chars on 12 lines) | not pinned offline | — |
| `calibrated-anchor` stub | +5 bytes (each placeholder is 3 UTF-8 bytes) | +20 | **+44** |
| `words-only` stub | 0 | 0 | 0 (tied at both residues) |

**The honest reading of this row:** the projection cut was expected to be the cheapest cut of all and
the numbers refuse to show it. `calibrated-anchor` predicts it makes the prompt *longer* (+44
per cycle): it is a 12-byte saving on the text, and the stub is wrong enough about per-character
cost that the bytes it saves are outweighed by the placeholders it uses. That is a **warning, not
evidence**: the projection cut is cheap in bytes and its real token saving is unknown. It stays in
the catalogue because it is honest about its cost and because a live unit can settle it in one
`/v1/tokenize` call.

## 4. What the search guarantees, and what it does not

Guaranteed (tested, `tests/test_quantise.py`):

1. **A legal shape is never returned on residue 0 or 1 while any legal row exists** — the avalanche
   bills the whole prefix, and a host with a legal row in hand that returns 0 or 1 has not searched.
   Six parametrised avalanches plus residue 1 explicitly.
2. **Padding only wins when the arithmetic says so.** At residue 5 it pads nothing
   (`NO PADDING: full lands on residue 5 unpadded`); at residue 58 it pads 8 tokens to reach 2; at
   residue 63 it pads 1 token. The rule is the law, not `target_residue`.
3. **A free variant that escapes the avalanche is preferred to padding** (residue 0 → cut to
   residue 2, no filler, PREDICTED 15).
4. **When no free variant reaches a cheap residue it pads and says so** — and when the padding cap
   forbids even that, it pads nothing, stays legal, and prints
   *"no shape reached a cheap residue at an acceptable bill (padding capped at N token(s))"*.
5. **A cut never hides its cost.** `ShapeCandidate.cuts` names the capability, and the table flags
   `cuts-capability`.
6. **Determinism.** Same input, same `as_dict()`; no clock, no randomness, no socket (`quantise.py`
   has exactly one `urlopen`, inside `ServerTokenizer`).

Not guaranteed, not claimed:

* **That any of these bills is real.** `ShapeChoice.predicted` is `True` and `calibration_limits(L)`
  returns the string `"PREDICTED, not measured: this unit sent no request"` for every caller.
* **That the append cost `L` is 13 for these prefixes.** ENGINE-R1 measured `L = 13` on a 325-token
  prefix. The prompts here are 400–600 tokens under the calibrated reading. `L` is a prompt *delta*
  dominated by template framing rather than by prompt length, so it probably does not scale — but
  that is an argument, not a measurement, and `calibration_limits(13)` names `L = 40` etc. as
  unmeasured.
* **That the residue a stub assigns is the residue the server will bill.** That is the whole reason
  the search's recommendation is a candidate for measurement, not a result.

## 5. The live measurement a later unit should run (not run here)

One prime, two shapes, one filler count, all on a 325-token-class prefix, 3 reps, `L` read from
`prompt_tokens` (ENGINE-R1's loop, one re-aim per rep):

1. **Tokenize the six texts** (`/v1/tokenize`): full envelope, compact envelope, compact+projection
   envelope, and each `+" the"` once. This single call settles §2's contradiction and §3.4's sign.
2. **Cell E** — compact index, **unpadded**, residue `R_E = P1_E mod 64`. Predicted bill
   `P1_E + R_E + L`. If `R_E` is legal this is the shape ENGINE-R1 never measured: the compact form
   as the search actually uses it, with no filler at all.
3. **Cell F** — compact + the minimal filler to residue 2, billed `P1_F + 15`.
4. **Report `bill(E) − bill(F)`.** Negative means the search should choose E and the host can stop
   padding at any residue; positive means F, and the search's own rule already says which. Either
   answer is a result — the search's rule is falsifiable by exactly this pair.

The prediction to beat: **if `R_E ∈ [34, 63]`, F is cheaper; if `R_E ∈ [2, 32]`, E is cheaper** —
the same line as section 1, now applied to a shape rather than a padding amount. That is the
falsifiable claim this unit leaves behind.

## 6. Limits of this document

* **No request was sent.** Every table above is PREDICTED from a law that ENGINE-R1 measured, applied
  to offline token counts from a stub.
* **No real tokenizer was available.** Three stubs, three readings, one stated contradiction (§2.1).
* **The projection cut's token cost is unsettled** and the one stub that models bytes says it costs
  more than it saves. It is catalogued with that warning rather than recommended.
* **`n = 12 items, one corpus.** The search is corpus-independent; the residues are not.
* **One machine, one block size.** `B = 64` (SGLang). vLLM's `+B` term (`B = 1056`) is a different
  law; `choose_shape` takes `B` as a parameter but nothing here was validated at 1056.
