# ENGINE-R1 — does residue quantisation pay on the live endpoint?

**Unit:** ENGINE-R1 · **Server:** `occamy-1.0` on SGLang, `http://192.168.2.168:8012/v1`, cache
block size **B = 64** (measured in `experiments/miss-law/LAW.md`) · **Sole writer** for the whole
unit; no `/flush_cache`, no restart · **Rows:** `measure/rows.jsonl` — 49 rows, 33 of them
requests, flushed **and fsynced** one row at a time, so a kill loses at most the request in flight ·
**Prediction rows are written before their request** (each carries `seq`, and every prediction's
`seq` precedes the `seq` of the request it predicts).

**Answer in one sentence.** Quantisation pays on this server only as avalanche insurance: a
compile that lands on residue 0 bills **397** tokens for a single append and **15** after two
tokens of inert padding (−380 per cycle, 26×), while the same rule applied to the residue the
worked example actually lands on costs **58** billed tokens per cycle to save 3 (full index) and
**36** to save 14 (compact index), paying back only after 21 and 4 warm turns respectively — so
padding must be **conditional** (residue ∈ {0, 1}, or residue ≥ 35), never unconditional.

---

## 1. The four cells, predicted vs observed

Request shape is `LAW.md` §2, unchanged: round 1 `[system: NONCE + "\n\n" + <index block>,
user: "Reply with the single word OK."]`, round 2 the same plus `[assistant "OK.", user " the"*n]`
with `n = 1`. The NONCE is a permutation of ten one-token words, freshly permuted for **every
prime** (84 distinct orderings used), so every prime is cold while `P1` stays fixed inside a cell.
3 reps per cell. `L` below is the **measured** prompt delta (`P2 − P1`), never `n`.

| cell | index | target residue | `P1` | residue measured | pad tokens | `L` | `cached` | `uncached` | predicted | reps matching |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **A** | full, as `worked_example.py` compiles it | — (whatever it lands on) | 325 | **5** | 0 | 13 | 320 | **18** | 18 | **3/3** |
| **B** | same content, padded to 2 | 2 | 386 | **2** | 60 | 13 | 384 | **15** | 15 | **3/3** |
| **C** | same content, padded to **0** (control) | 0 | 384 | **0** | 58 | 13 | **null** | **397** | 397 (avalanche) | **3/3** |
| **D** | **compact** index, padded to 2 | 2 | 322 | **2** | 50 | 13 | 320 | **15** | 15 | **3/3** |

Prediction = `predict_billed(P1, L, 64)` with `L = 13` fixed **before** the request (pre-registered:
payload 1 + framing 12 from `LAW.md` §2); the measured `L` came back 13 in 12/12 rows, so the same
column serves both. **Residual `observed − predicted = 0` in 12/12 measure rows**, and the
avalanche appears at residue 0 in 3/3 and nowhere else:

| residue 0 (cell C) | residue 2 (cells B, D) | residue 5 (cell A) |
|---|---|---|
| `cached = null`, `uncached = P1 + L = 397` | `cached = P1 − 2 = 384 / 320`, `uncached = 2 + L = 15` | `cached = 320`, `uncached = 5 + L = 18` |

`cached = floor((P1 − 2)/B)·B` held in **9/9** non-avalanche rows (the shared prefix ends 2 tokens
before `P1`, as `LAW.md` §2 states) and `cached` was **not reported at all** in the 3 avalanche
rows — the same "the entry is absent, not rounded" signal the law recorded at 8,000 tokens,
reproduced here on a 384-token prefix.

### 1.1 The control did its job
Cell C is the load-bearing row: it was **padded on purpose to residue 0** and it avalanched
(397 billed for a 13-token append, `cached` null, 3/3). The effect is real on a live request at
this prefix size, not an artefact of the 8,000-token grid the law was derived on.

### 1.2 A prediction that failed, and the fix it forced
`choose_padding` aligns the **text**. `P1` also carries the user message and the chat template's
framing, and a padded tail shifts the rendered prompt by **+1 token** relative to additive
`/v1/tokenize` arithmetic (observed: pad 61 → `P1` 387 where 386 was predicted, stable across
cells). The first pass aimed at the text and landed cells B and C on residues **23 and 21** — i.e.
the control never tested the avalanche. Fixed two ways: `choose_padding` now takes
`offset_tokens` (the other messages plus template framing), and every rep **verifies the residue on
the wire** (`prompt_tokens` of its own prime) and re-aims with the measured correction, up to 3
attempts on fresh nonces. 12/12 reps needed exactly one re-aim; the settled attempt is the one
measured. Lesson recorded: *a residue the engine has not read back from the server is a guess.*

## 2. Billed-token deltas against A (the index as compiled)

Prime + append is one cycle; a cycle is `P1` (the prime) plus the append's uncached tokens.

| cell | cycle bill | Δ vs A | what the delta is |
|---|---:|---:|---|
| A | 325 + 18 = **343** | — | residue 5, no padding |
| B | 386 + 15 = **401** | **+58** | +60 filler to move 5 → 2, −3 of tail; +1 template shift |
| C | 384 + 397 = **781** | **+438** | the avalanche: the 384-token prefix is re-billed in full |
| D | 322 + 15 = **337** | **−6** | compact index is 54 prompt tokens shorter than A; the padding costs +50 |

**D's win is the compact index, not the quantisation.** Its own unpadded residue is 16
(`P1 = 272`), which needs no rescuing: unpadded it would bill `272 + 29 = 301` per cycle, i.e. **36
cheaper than the padded 337**. The honest reading of D is "−64 index bytes and −54 prompt tokens
per turn, plus 36 tokens wasted putting it on residue 2".

### 2.1 When the padding pays back (amortised)
If instead one padded prefix stays resident for `T` warm turns, the filler is paid once and the
tail saving repeats — `cycle_bill(...)["breakeven_turns"]`:

| index | residue | pad to 2 | tail saving/turn | breakeven |
|---|---:|---:|---:|---:|
| full (A) | 5 | 61 | 3 | **21 turns** |
| compact (D) | 16 | 50 | 14 | **4 turns** |
| full at residue 0 | 0 | 2 | avalanche | **0 — first append** |
| full at residue 63 | 63 | 3 | 61 | **1 turn** |

So padding is worth it immediately only when it dodges an avalanche or the residue is large; at
small legal residues it is a bet on the prefix staying warm.

## 3. The compact index

| | full (A/B/C) | compact (D) | change |
|---|---:|---:|---|
| index bytes | **447** | **383** | −64 (−14.3 %) |
| bytes per line (12 items) | 37.25 | **31.92** | −5.33 |
| prompt envelope bytes | 472 | 408 | −64 |
| **r = 30,000 body bytes / index bytes** | **67.1×** | **78.3×** | +11.2 |
| `P1` on the wire (unpadded) | 325 | 272 | −53 tokens |

The full index here is **447 bytes, 37.25 B/line, r = 67.1×** — byte-identical to the artefact
`SPEC.md:75` and `CHANGELOG-P0.1.md` publish, because the run uses the example's own scope
constant (`worked-example`), 12 items and 30,000 chars.

**What was cut, and why nothing was lost** (`compact_index` reports `dropped`):

* the `"- "` bullet on every line — decoration; the block is already tag-delimited;
* the per-line `@1` — the header pins the revision and `resolve()` accepts a revision-less
  reference, re-pinning from the index (`resolve.py:117` refuses only a *mismatching* pin);
* the body digest from 8 to 6 hex chars — the line's digest is a display handle; `store.get`
  re-hashes the full sha256 on read, so which bytes a ref designates cannot change.

`tests/test_quantise.py::test_compact_index_cuts_bytes_without_losing_resolution` proves this
behaviourally: every compacted line parses, resolves through the real `Scope`/`Ledger`, and returns
the **same full sha256** as the line it came from — for the pointer item (`@artifact:plan#/goal`)
and the projected item (`@memory:m01?brief`) too.

**A deeper cut was refused.** Two further cuts were available and are not taken, because each loses
a capability rather than redundancy: dropping the per-line byte length (the number a host uses to
decide whether a body is worth fetching — payload planning) and replacing the kind word with a
one-character legend (the line would no longer parse as a `Reference` without a host-side
dictionary, breaking the "the model echoes the line, the host parses it" contract). Both are worth
a further ~5 and ~7 bytes per line; both were declined rather than quietly taken.

## 4. What this measurement does not say

* **`n = 1` payload only.** The law says payload size does not interact with the residue
  (`LAW.md` §3) and this run does not re-test that; the padding arithmetic is payload-independent,
  but only one `n` was measured here.
* **SGLang `:8012` only.** vLLM's `+B` term (`B = 1056`) is a different law and was not touched;
  `:8014` was never written to.
* **3 reps per cell, deterministic.** Identical values across reps bound transcription error, not
  sampling variance — exactly as in `LAW.md` §8.
* **No multi-turn warm run.** `breakeven_turns` is arithmetic on the law, not a measured warm
  session; the crossover work already showed warm behaviour on this server, but not with padding.
* **A contaminated first pass is on the record.** The first run (rows overwritten) landed cells B
  and C on residues 23 and 21 because the residue was aimed at the text rather than at `P1`; those
  numbers were discarded, and the reason is §1.2. Nothing here was tuned after seeing them — the
  fix is a correctness fix, and the cells are the same four either way.
