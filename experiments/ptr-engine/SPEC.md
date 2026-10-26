# ptr-engine — adoptable contract

A pointer engine for a chat-shaped harness: at turn end it **compiles** the turn's
material into a content-addressed warmpool plus a short index; during the turn it
**resolves** an index line to a verified content identity on demand, and the caller
reads the body.

Nothing here calls a model, opens a socket, or starts a process -- with one deliberate
exception: `quantise.ServerTokenizer` asks the serving endpoint for an exact token count.
It is opt-in by construction (nothing in the package ever builds one, no import dials
out, and every other function takes the tokenizer as an argument). The engine is pure
Python 3.11+ and the suite is `pytest`.

Prior art, cited, not vendored: Duval `src/reference.ts` (`Reference`,
`ResourceRef`, `REF_KINDS`) and `src/state.ts` (`ResourceRef`). This package
re-implements the two types and the text form; it does not import them.

---

## 1. The two identities

```
ResourceRef = { scheme, locator, hash, pin }     # CONTENT identity: which bytes, verified
Reference   = { kind, id, pointer?, revision?, projection? }
                                                 # POSITION: which region of which
                                                 # namespace, at which revision, in which view
```

`hash` is `sha256:<64 hex>`. `locator` is **store-relative** (`aa/<sha256>.ext`), never
absolute, so a warmpool can move without invalidating an index. `pin` is the
caller's retention handle (this engine writes `rev:<n>`); it is metadata and never
part of the key.

`kind` is closed: `task evidence execution capability policy decision artifact
memory knowledge meta world hypothesis lease agent run state` (Duval D-024).

## 2. One-way resolution

Resolution ends at a content hash, so the bridge has exactly one direction:

```
resolve(Reference, Scope, Ledger) -> ResourceRef      # yes
anything(ResourceRef)             -> Reference        # NO. There is no such function.
```

A `ResourceRef` cannot name a `Reference`, because content does not know which
namespace it was reached through, at which revision, or in which view. This is a
property of the API surface, not a type-level guarantee: the package simply has no
such function, and `tests/test_oneway.py` sweeps every public callable with the
exact `ResourceRef` `resolve()` issued (refusing by exception is compliant). A host that needs
to go from content to position is asking a **catalogue** question, not a pointer
question, and must ask its catalogue.

## 3. The envelope: index plus bodies

The text form `@kind:id[#pointer][@revision][?projection]` is a **serialization**, not
the primitive: prompts and logs carry the text, everything downstream carries the
object.

The prompt envelope a host assembles per turn, in this order:

```
<ptr-index>
ptr-index/1 scope=<scope> revision=<n> block_size=<n> entries=<n>
- @kind:id[#pointer]@rev[?projection] <hash8> <body_bytes>
...
</ptr-index>
<ptr-bodies>                       # only if at least one ref was resolved
<ptr-body ref="@kind:id@rev" bytes="<n>">
<body>
</ptr-body>
</ptr-bodies>
```

The index line is deliberately short: the item id, an 8-hex-character prefix of the
body's sha256, and a byte length -- the body's for a plain item, the selected
region's canonicalised length for a pointer item. It is never the body. Measured on the
worked example (12 items, 30,000 chars): **447-byte index, r = 30,000 / 447 = 67.1×**.

## 4. Lifecycle: compile at turn end, resolve during the turn

1. **Turn end.** The host calls
   `compile_turn(material, revision, scope, block_size, store=...)` where `material`
   is a list of `{kind, id, body, pointer?, projection?, ext?}`. Every body is put
   into the store; the index gets one pointer line per item.
2. **Turn start.** The host sends the index block, and only the index block.
3. **During the turn.** The model calls the single tool `fetch(ref)`. The host
   `parse`s the text, `resolve`s it against the current `Scope`, records the ledger
   row, reads the body with `store.get(ResourceRef)`, and appends it.
4. **Next compile** is a new `revision`. Old bodies stay addressable in the store by
   hash: the `ResourceRef` an older `resolve` returned still opens *those* bytes
   (`store.get` on it keeps working, which is what makes the store a store). A
   `Reference` pinned to a superseded revision is REFUSED, deliberately, with
   `PTR_REVISION_MISMATCH`: a stale position must never silently resolve to newer
   bytes. Resolve against an index compiled at that revision, or drop the pin.

The index is **deterministic**: the same `(material, revision, scope, block_size)`
produces byte-identical index bytes in every process, under any warmpool root. Sorted
by `(kind, id)`; no timestamp, no random id, no absolute path.
`tests/test_determinism.py` compiles in two processes under two different roots and
compares sha256.

## 5. Warmpool layout

```
<root>/<aa>/<sha256><ext>          aa = first two hex chars of the digest
```

Key = sha256 of the body bytes; identical content is stored once (idempotent `put`);
`get` re-hashes on read and raises `PTR_HASH_MISMATCH` if the bytes are not the ones
the identity names. Writes are atomic (temp file + `os.replace`).

The root is an **isolated filespace, not a workspace subdirectory**. A root that
resolves inside the repository working tree is refused with
`PTR_WARMPOOL_INSIDE_REPO`; the engine finds "the repository" by walking up from its
own file for `.git` or `pyproject.toml`, so `cd /tmp && compile(...)` cannot smuggle a
store into the tree. Default root: `$PTR_WARMPOOL_ROOT`, else
`$XDG_CACHE_HOME/ptr-engine/warmpool`, else `~/.cache/ptr-engine/warmpool`.

## 6. The four annotations

Pure functions in `annotate.py`; a host reads them to decide residency, grant,
payload size and bookkeeping.

| annotation | signature | meaning |
|---|---|---|
| `depth` | `depth(entry) -> int` | `0` for a root index entry, `1` for a leaf body. A host keeps depth 0 hot and leaves depth 1 cold. |
| `scope` | `scope(entry) -> str` | the capability scope that must be presented to resolve this entry |
| `append_cost` | `append_cost(serialized_ref, block_size) -> int` | `len(serialized_ref.encode()) % block_size` — how far an append lands off the cache grid. `0` means it lands on a block boundary; anything else rewrites the partial tail block. |
| `ledger_id` | `ledger_id(scope, serialized_ref, seq) -> str` | `<scope>:<seq:04d>:<12 hex of sha256(ref)>` — the id this resolve is recorded under. Deterministic; no clock, no uuid. |

## 7. Ledger row

Append-only JSONL, one row per request (a resolve, not a turn):

```json
{"ledger_id":"sess-01:0003:1c0d0a2f9d1e","scope":"sess-01",
 "refs_resolved":1,"refs_refused":0,
 "bytes_appended":21,"block_size":64,"append_remainder":21,
 "prompt_tokens":null,"cached_tokens":null,"uncached_tokens":null,
 "token_source":null,"ref":"@knowledge:k01@3","ref_index":"@knowledge:k01@3"}
```

`refs_resolved` / `refs_refused` are counts, so a host that batches several fetches
into one request can record them in one row. A refusal appends a row with
`refs_refused=1` **before** the error is raised, so refused attempts are measurable.

**The token rule.** The token fields are optional, filled by a host that has them.
When the host does not have them the row carries `null` and `"token_source": null`.
It never carries `0`: a zero that means "unknown" is a lie that has already been read
as "free" once in this project. Supplying counts without a `token_source` raises
`PTR_TOKEN_SOURCE_REQUIRED`. What those counts *should* be, per append, is the
billing law in §13.

`ref` is the text the caller presented; `ref_index` is the index's own spelling of
the same entry (they differ when the caller omits a revision the index pins). Both
count as "resolved" for the adapter's check.

## 8. Adapter seam

Two functions, no third:

* `build_prompt(index, resolved_bodies, ledger=None) -> str`
  The index block plus the bodies handed to it. It has no store and cannot fetch, so
  a body that was not resolved cannot appear. Every ref must be enumerated in the
  index; every body's sha256 must equal the body that ref resolves to (else
  `PTR_BODY_MISMATCH`); with a ledger, the ref must carry a successful resolve row
  (else `PTR_UNRESOLVED_REF`). With zero resolutions the prompt is the index alone.
* `fetch_tool_spec() -> dict`
  The one tool the model may call: `fetch(ref)`, one string argument.
  A host resolves it, reads the body, and is done.

## 9. Errors

Every failure is a `PtrError` subclass with a stable `code`; `str(error)` starts with
the code; `error.as_dict()` gives `{code, detail, context}`. The seven negative
controls each raise a different one:

| control | code |
|---|---|
| malformed token | `PTR_SYNTAX` |
| unknown kind | `PTR_UNKNOWN_KIND` |
| unknown id | `PTR_UNKNOWN_ID` |
| ungranted scope | `PTR_SCOPE_UNGRANTED` |
| unenumerated projection | `PTR_PROJECTION_UNENUMERATED` |
| bad pointer | `PTR_POINTER_INVALID` |
| over budget | `PTR_BUDGET_EXCEEDED` |

Also named: `PTR_REVISION_MISMATCH`, `PTR_HASH_MISMATCH`, `PTR_STORE_MISS`,
`PTR_WARMPOOL_INSIDE_REPO`, `PTR_EXTENSION_INVALID`, `PTR_DUPLICATE_ID`,
`PTR_MATERIAL_INVALID`, `PTR_NOT_A_REFERENCE`, `PTR_UNRESOLVED_REF`,
`PTR_BODY_MISMATCH`, `PTR_TOKEN_SOURCE_REQUIRED`, `PTR_ANNOTATION_INVALID`, and the
five ledger codes `PTR_LEDGER_COUNT`, `PTR_LEDGER_BLOCK_SIZE`, `PTR_LEDGER_ID`,
`PTR_LEDGER_SCOPE`, `PTR_LEDGER_REFUSAL_CODE` (`ptr_engine.LEDGER_CODES`).

The seven controls above are fixed and unchanged; the ledger codes are additive, so
the row-contract enumeration is twelve named codes. `tests/test_negative_controls.py`
asserts the two sets are disjoint and the ledger set is complete.

The billing law (§13) adds four more codes, in their own tuple so the row contract's
five stay five: `PTR_LAW_UNKNOWN_SERVER`, `PTR_LAW_BOUND_INVALID`,
`PTR_LAW_SERIES_LENGTH`, `PTR_LAW_OBSERVED_INVALID` (`ptr_engine.LEDGER_LAW_CODES`).
The package therefore names **sixteen** codes: 7 controls + 5 ledger + 4 law.
`tests/test_ledger.py` asserts the three sets are pairwise disjoint and the total is 16.
Ledger and law errors are also `ValueError`s, so a caller written before the codes
existed still catches them: the code is the addition, the exception family is not a break.

## 10. Stated limits (honesty section)

* **Projection is validated, not derived.** A projection is enumerated and checked
  (`PTR_PROJECTION_UNENUMERATED`), and it is carried in the `Reference` and in the
  index line, but this engine returns the item's body. A host that derives views
  supplies them as their own items with the projection set. Deriving views is a
  projection-engine job, not a pointer job.
* **Pointer needs a JSON body.** `#<json-pointer>` selects a region only when the body
  parses as JSON; the selected value is canonicalised (`sort_keys`, `,`/`:` separators)
  and stored as its own content identity. A non-JSON body with a non-empty pointer is
  refused at compile time. Region addressing for plain text is not implemented.
* **The budget is per ledger.** `Scope.max_refs` compares against the successful
  resolves in the ledger it is handed; a host that wants a per-turn budget hands a
  fresh ledger per turn (the file may live for the session).
* **Compile is O(material).** Bodies are hashed and written every compile. That is
  fine at turn granularity (the size of a store is not the size of a prompt); it is
  not a streaming design.
* **No eviction.** The warmpool grows. Retention is the host's policy; content
  identity makes pruning safe (a pruned body becomes `PTR_STORE_MISS`, not a wrong
  read).

## 11. Minimal harness surface

What a host must provide for the engine to work. Kept as short as honesty allows.

1. **A turn-end hook** that calls `compile_turn` with the turn's new material.
2. **One model-visible tool**, `fetch(ref)`, that resolves a ref and returns the body.
3. **A ledger writer** pointing at `ledger.py`'s JSONL.
4. **A residency hint carrier**: the index is sent with `depth=0` entries hot and
   bodies cold (`TurnIndex.entry_dicts()` is that carrier).
5. **The host's block size** (cache block granularity) supplied to `compile_turn`, so
   `append_cost` can be computed.
6. **The capability scope of the current session**, presented on every resolve.

Which of these a plain chat harness already has, and which it does not:

| # | plain chat harness | why |
|---|---|---|
| 1 | **has a place for it** | a turn-end hook is where a host already trims history or summarises; the compile call is one line there. |
| 2 | **does not have it** | a plain harness has no per-reference fetch tool. This is the one genuinely new model-visible capability, and it is what makes lazy loading measurable. |
| 3 | **does not have it** | a plain harness logs prompts, not resolve attempts. A JSONL append next to the existing log is small but it does not exist yet. |
| 4 | **partially** | a plain harness sends text, so a "hot index / cold body" distinction is not expressible; the index block is sendable as text today, the cold/hot split only matters once a cache is in play. |
| 5 | **does not have it** | a plain harness has no cache block granularity. Without it `append_cost` cannot be computed, and the number that decides payload size is not available. |
| 6 | **does not have it** | a plain harness has a user, not a capability scope. The engine requires a scope name on every resolve, so the host must invent and thread one. |

Read plainly: items 1 and 4 are surface a chat harness already has or can host with
one line; items 2, 3, 5 and 6 are real work, and 5 is the one that decides whether
`append_cost` is a measurement or a guess.

## 12. Using it in ten lines

```python
from ptr_engine import BodyStore, Ledger, Scope, build_prompt, compile_turn, parse, resolve

store  = BodyStore("/var/tmp/ptr-warmpool")          # outside the repo, by contract
ledger = Ledger("/var/tmp/ptr-warmpool/t3.jsonl", block_size=64)
index  = compile_turn(material, revision=3, scope="sess-01", block_size=64, store=store)
scope  = Scope(name="sess-01", index=index, max_refs=8)

ref    = parse("@knowledge:k03@3")                    # the model echoed an index line
target = resolve(ref, scope, ledger)                  # -> ResourceRef; one ledger row
prompt = build_prompt(index, {ref: store.get(target)}, ledger)
```

## 13. The billing law: one append onto a primed prefix

The engine's billing model is a measured law, not a guess
(`experiments/miss-law/LAW.md`, derived from 774 raw rows and **replayed here
exactly**: `tests/test_ledger.py::test_replay_of_the_measured_rows_reconciles_exactly`
reads `experiments/miss-law/rows.jsonl` and reconciles every single-append turn).

For a prefix of `P1` tokens receiving an append of `L` tokens, the server re-bills

```
SGLang / occamy-1.0,  B = 64:    uncached = (P1 mod B) + L
vLLM   / qwen3.5-9b,  B = 1056:  uncached = (P1 mod B) + B + L      # one whole boundary block
```

**`L` includes the request template's framing tokens** — 12 in the measured shape —
and is never the raw payload count `n`. `law_L(n)` is that conversion
(`n + FRAMING_TOKENS`, `FRAMING_TOKENS == 12`) and the only place the constant lives:
`L = n + 12`, so 1 payload token appends 13.

**The avalanche is a first-class outcome, not a warning.** If `P1 mod B ∈ {0, 1}` the
server reports no cache at all and bills the whole prefix:

```
uncached = P1 + L
```

Measured on 83 null-cache rows, **all** at residue 0 or 1 and at no other residue;
`P1 = 8000` bills 8,013 tokens where the tail formula predicts 13. It is the reason
`HitEntry` stores `avalanche` as its own boolean rather than folding it into a large
`(P1 mod B)`: a host that budgets with the tail formula alone is wrong by four orders
of magnitude at those two residues, and `summarise()` reports the avalanche count, the
tokens the avalanches billed, and the tokens they added over what the tail formula
would have said.

**One correction the replay forced.** `boundary_blocks` is capped by the complete
blocks the prefix actually holds:

```
boundary term = min(boundary_blocks, P1 // B) * B
```

A server that re-bills "one whole cached block" has no block to re-bill when
`P1 < B`. The single row the `+B` form could not explain is vLLM at `P1 = 453`
(`cell Bprobe-400`): it billed `467 = P1 + L`, not `P1 + B + L`. With `P1 >= B` the cap
is inert and the law is unchanged. This is one rule, derived from block arithmetic —
not a per-cell special case, which this engine refuses to add.

### 13.1 Profiles: measured, extrapolated, refused

| server | `B` | boundary blocks | avalanche residues | avalanche measured? |
|---|---:|---:|---|---|
| `sglang` | 64 | 0 | `{0, 1}` | **yes** (83/83 null-cache rows) |
| `vllm` | 1056 | 1 | `{0, 1}` | **no** — residue 0/1 was never sampled |

The `+B` term on vLLM rests on one server-side counter, so it wants independent
re-derivation; the avalanche at residue 0/1 on vLLM is genuinely **unmeasured** (27
residues in the sweep, none 0 or 1). The engine predicts it anyway — never
under-predict a bill — and flags every such turn with
`HitEntry.avalanche_extrapolated`, counted by `summarise()`. An unmeasured server is
refused with `PTR_LAW_UNKNOWN_SERVER`: there is no default block size, because
inventing one turns a measurement into a guess.

### 13.2 The accounting layer

```python
hits = HitLedger("sglang")                                  # pure, in-memory, no I/O
hits.record(P1=8000, payload_tokens=1, observed_uncached=8013, cell="res-8000-n1")
hits.predict(8002, law_L(1))                                # -> (15, False)
report = hits.reconcile()                                   # per-turn delta + every mismatch
report.unexplained()                                        # "could not explain" lines
hits.summarise()                                            # billed, avalanche cost, explained fraction
```

`HitEntry` stores `P1`, `L`, `B`, `residue`, `avalanche`, `predicted_uncached`,
`tail_uncached`, `observed_uncached` and `avalanche_extrapolated`. `residue` and
`avalanche` are **stored, not recomputed**, so a later change to a profile cannot
silently redraw the outcome a turn was already billed under.

`reconcile()` returns three distinct outcomes and refuses to merge them: `exact`
(`delta == 0`), `mismatch` (`delta != 0`, named with its **server and cell**), and
`unknown` (no observation — `None` is not zero and is not a match; it stays in the
denominator of the explained fraction). A silent mismatch is a bug: the engine says
"I could not explain this turn" rather than absorbing it.

### 13.3 What the law does not say

* It is a law about **one append onto an already-primed prefix**. Multi-append runs
  were not swept end to end.
* The SGLang avalanche is measured but **not explained**; do not generalise it to
  another build without re-measuring.
* vLLM's numbers rest on one server-side counter; the `+B` term deserves independent
  re-derivation.
* The law is offline by construction: no tokenizer at import time, no network, no clock.

## 14. Quantisation: the append cost is a choice (`quantise.py`)

Measured on the serving endpoint (`experiments/miss-law/LAW.md`, re-measured on a live
request by `measure/RESULTS.md`): for cache block size `B`,

```
uncached = (P1 mod B) + L                          # the unaligned tail plus the append
uncached = P1 + L,  if P1 mod B in {0, 1}          # AVALANCHE: no cache reported at all
```

The engine assembles `P1` itself, so the residue is not fate: a compile that lands on 0
or 1 re-bills the whole prefix on every append. `quantise.py` is the lever. It is pure --
no clock, no randomness, no socket unless a caller builds a tokenizer -- and it is three
functions plus two that a measurement needed.

| function | signature | returns |
|---|---|---|
| `token_len` | `token_len(text, tokenizer) -> int` | the **exact** token count; no tokenizer is an error, never an estimate |
| `choose_padding` | `choose_padding(compiled_text, target_residue=2, B=64, tokenizer=None, *, offset_tokens=0) -> Padding` | a padded variant (`Padding.text == compiled_text + Padding.padding`), the filler, its token count, and the residue before/after |
| `predict_billed` | `predict_billed(P1, L, B=64) -> (predicted_uncached, avalanche_flag)` | the law, including the avalanche |
| `cycle_bill` | `cycle_bill(P1, L, B=64, target_residue=2) -> dict` | does padding pay for *this* prefix: `delta` (per cycle), `tail_saving_per_turn`, `breakeven_turns` |
| `compact_index` | `compact_index(index_text) -> CompactIndex` | the same index with redundancy removed (447 -> 383 bytes, `r` 67.1x -> 78.3x) and `dropped` naming what went |

Tokenizers are supplied, never assumed: `StubTokenizer` (deterministic, one token per
whitespace word) for tests, `ServerTokenizer(url)` for the number the server will bill
(`POST /v1/tokenize`).

```python
from ptr_engine.quantise import ServerTokenizer, choose_padding, cycle_bill, predict_billed

tok    = ServerTokenizer("http://192.168.2.168:8012/v1")
offset = token_len(user_text, tok) + template_framing      # everything but the index
pad    = choose_padding(index_text, 2, 64, tok, offset_tokens=offset)
assert pad.residue_after == 2 and pad.text == index_text + pad.padding

verdict = cycle_bill(P1=pad.prompt_tokens, L=payload + 12, B=64)
if verdict["delta"] > 0 and verdict["breakeven_turns"] is None:
    pad = choose_padding(index_text, pad.prompt_tokens % 64, 64, tok)   # not worth it
```

**Three things a host must not skip.**

1. **`offset_tokens` is mandatory for a real prompt.** `choose_padding` aligns its own
   text; the residue the server bills is the whole prompt's. Aligning only the text put
   two measurement cells on residues 23 and 21 instead of 2 and 0.
2. **Read the residue back from the prime.** `/v1/tokenize` of the raw text and the
   *templated* prompt disagree by one token depending on how the padded tail meets the
   template's trailing marker (measured: +1 at 61 filler tokens, 0 at 60). Aim, send,
   read `prompt_tokens`, re-aim with the correction -- the measurement loop did exactly
   that in 12/12 reps, one re-aim each.
3. **Pad conditionally.** Padding is not free: reaching residue 2 from residue `r` costs
   `66 - r` filler tokens to save `r - 2` of tail per append. It pays immediately only at
   residues 0/1 (it dodges the avalanche: 397 -> 15 billed on an append, measured) and at
   large residues (`r >= 35`); at the residues the worked example actually lands on (5
   full, 16 compact) it costs 58 and 36 billed tokens per cycle and pays back only after
   21 and 4 warm turns. `cycle_bill` is the arithmetic; a host that pads unconditionally
   is as wrong as one that never pads.

Section 13 states the law this module exploits; `quantise.py` is the lever and
`measure/RESULTS.md` the live re-measurement.

The index line's padding is **never silent**: `Padding.as_dict()` is what a ledger row or
a measurement row records (`padding`, `padding_tokens`, `offset_tokens`, `prompt_tokens`,
`residue_before`, `residue_after`, `applied`), and `text == base + padding` byte for byte,
so the intervention is always diffable. `measure/RESULTS.md` is the measurement; the law
it reproduces holds on a live request in 12/12 rows, avalanche included.

## 15. Shape search: cut the index before you pad the prompt (`quantise.py`)

Section 14's conclusion was that padding at a benign residue *costs* 36-58 billed tokens per
cycle. ENGINE-R1's own next hint named the way out: the compact index is 53 prompt tokens
**smaller**, and a shorter prefix moves `P1 mod B` just as surely as a padded one — for nothing.
`choose_shape` is that lever. It is pure, it is offline, and **every number it returns is
PREDICTED**, never measured; `ShapeChoice.predicted` is `True` and `calibration_limits(L)` returns
`"PREDICTED, not measured: this unit sent no request"` for any caller that quotes it.

| function | signature | returns |
|---|---|---|
| `choose_shape` | `choose_shape(index_variants, target_residue=2, B=64, tokenizer=None, *, offset_tokens=0, L=13, payload_tokens=0, max_pad=None) -> ShapeChoice` | the variant with the lowest predicted cycle bill, the whole candidate table, and `padding_reason` |
| `quick_bill` | `quick_bill(P1, L, B=64) -> int` | `P1 + predict_billed(P1, L, B)[0]` — the predicted cycle bill as one number |
| `projection_variant` | `projection_variant(index_text, *, name="projection", index_form="compact") -> ShapeVariant` | the index with each digest shortened, plus `cuts` naming the capability lost |
| `calibration_limits` | `calibration_limits(L) -> tuple[str, ...]` | what a law-based prediction is and is not anchored to |

### 15.1 The padding line, from the law

The cycle bill is `P1 + (P1 mod B) + L`. Padding to target 2 from residue `r` costs `k = (2 - r) mod B`
filler tokens **once** (they live in `P1`) and saves `r - 2` of tail **per append**, so it pays iff
`k + 2 < r`, i.e.

```
padding pays  <=>  r > B/2 + 1   ->   r >= 34 at B = 64     (PAD_FOR_FREE_RESIDUE = 33)
```

plus the forced case: `r in {0, 1}` is the avalanche, where the whole prefix is billed and padding
always pays. Between 2 and 33 the filler costs more than the tail it saves — the band ENGINE-R1
measured at +36 and +58. `choose_shape` computes both the padded and the unpadded row for every
variant and lets the law pick; it does not chase `target_residue`.

### 15.2 What the search will not do

* **It never returns a shape on residue 0 or 1 while a legal row exists.** Tested on six
  parametrised avalanches; a host that has a legal row in hand and returns 0 or 1 has not searched.
* **It never hides a cut's cost.** `ShapeCandidate.cuts` names the capability that went with the
  bytes — a shortened digest stops being a verifiable handle, even though `store.get` still re-hashes
  the full sha256.
* **It never calls a prediction a measurement.** `ShapeChoice.basis` quotes the law; `predicted`
  is `True`; `calibration_limits(L)` lists what `L` was and was not measured at.
* **It never pads when the cap forbids it.** `max_pad=0` yields a legal unpadded shape and a
  `padding_reason` that says no shape reached a cheap residue.

```python
from ptr_engine.quantise import ShapeVariant, choose_shape, compact_index, projection_variant

compact = compact_index(index.index_text).text
choice = choose_shape(
    [ShapeVariant("full", full_envelope),
     ShapeVariant("compact", "<ptr-index>\n" + compact + "</ptr-index>\n", index_form="compact")],
    target_residue=2, B=64, tokenizer=tok, offset_tokens=0, L=13,
)
print(choice.table())            # every candidate, with residues and predicted bills
print(choice.padding_reason)     # why the winner won, and whether it was padded
```

### 15.3 What is unmeasured, stated in the code

The offline fit was the hardest part of ENGINE-R2 and it produced a **negative** result that the code
carries rather than papers over: ENGINE-R1's two main-text anchors (full `P1 = 325` at residue 5,
compact `P1 = 272` at residue 16) and its cell-D anchor (compact `+ 50` filler = 322) **cannot all be
met by any tokenizer stub of this corpus's text**, because the main-text pair implies 53 tokens saved
across 11 fewer words while cell D requires each filler token to be one token. Three stubs are
reported in `measure/SHAPE-SEARCH.md` §2 with their residuals; none is claimed to be the server's
tokenizer. The search's *rule* (§15.1) is invariant across the three; only the residue each corpus
lands on is not. A later unit settles it with one `/v1/tokenize` of the three texts plus one
unpadded compact prime — the plan is §5 of `measure/SHAPE-SEARCH.md`.
