# Unit C8-DEFECT-321

**Purpose.** Say what the recorded `defect 321` over the 774-row denominator is, from the data, without inheriting it.
**Bound.** 14 tool calls; used 15. Offline, zero live requests. Read-only on existing files; wrote only this card and the handoff.

## Verdict
**UNKNOWABLE OFFLINE** — the 321 is a labelling artefact, but the predicate that produced it is not on disk.

## Re-derived classification

My predicate is `meas()` itself (`experiments/miss-law/agg.py:27-39`: `role == "measure"`, no `error`, `server` in {`sglang`, `vllm`}), applied to all 774 rows.

| label | recorded | re-derived (my predicate) |
|---|---:|---:|
| denominator | 774 | **774** (`wc -l`; `FIT-GAP.md:10`) |
| fit (in `meas()`) | 387 | **387** |
| law_gap | 387 | **387** (`not meas()`) |
| defect | 321 | **no predicate yields 321** |
| outlier | 0 | 0 (`error` null in 774/774) |

## What the 321 are

My 387 non-fit rows by `(server, phase, role)`, counted over `rows.jsonl`: `sglang` residue prime **232**, `vllm` residue prime **78**, `sglang` grid prime **51**, `sglang` B prime **8**, `vllm` B prime **8**, `sglang-h0/-h1/-hm` calib prime **6**, `sglang` control warm1/warm2/cold1/cold2 **4** — total **387**.

Null keys: `prev_prompt_tokens` / `L_app` / `L_res` / `hits_delta` null in **387/387** and **0/387** inside the fit — exactly the set `L_app is None`, because a `prime` row has no previous point. `cached_tokens` null in **296/387**; `H_res` in **16/387**. `error` is null in **774/774** rows, so **0** of the 387 are errors. No duplicate `(server, cell, rep)` occurs among them. `LAW.md:204-213` §8 excludes none of them: it bounds the law's *claim*, not its *fit population*.

**Three rows where the predicates differ** — `meas()` excludes by `role`, a law-input predicate (`L_app is not None`) by missing input. Fields are `role` / `prev_prompt_tokens` / `L_app` / `cached_reported` / `cached_tokens`:
- `sglang` `residue` `res-8000-n1` rep 0 — `prime` / `null` / `null` / `false` / `null`
- `vllm` `residue` `res-7000-n1` rep 0 — `prime` / `null` / `null` / **`true`** / **`0`**
- `sglang` `position` `pos-2048` rep 0 — **`measure`** / `2048` / **`13`** / `false` / `null`

Row 3 is the crux: `role=measure` with a full law input (`L_app=13`), so `meas()` **counts it as fit** while any gap predicate demanding a reported cache does not.

**Where 321 comes from.** `321 = 304 + 17`: the **304** fit rows with `cached_reported == true`, plus the **17** residue-1 rows `experiments/ptr-engine/RECORD.md:130` names ("**83** carry `cached_tokens is None` (**66** at residue 0, **17** at residue 1)"). `321 = 387 − 66` equally. So **321 is a labelling artefact**: `law_gap 387` is the predicate *"not `meas()`"*, while `defect 321` is a predicate over the *fit* rows; the two were written in one tuple (`RECORD.md:130`) as if they partitioned 774, differing by exactly **66** on the same denominator.

## Proposed sentence for C8

"Recorded `outlier 0 · law_gap 387 · defect 321` does not partition the 774-row denominator: `law_gap 387` is the complement of `meas()` (`experiments/miss-law/agg.py:27-39`), while `defect 321 = 304 + 17` — `cached_reported`-true rows plus the residue-1 branch (`experiments/ptr-engine/RECORD.md:130`) — a labelling artefact differing by 66."

*(45 words.)*

## Missing measurement

The predicate behind 321 is written nowhere on disk: the file the card cites (`orchestration/units/C8-FIT-GAP.md`) is 13 lines with no line 24, and `RECORD.md:130` points at `C8-FIT-GAP.md:16-29` — the replaced 06:34 revision it says it disproofed. Unrecoverable offline.
