# GUARD-U4-R2 — pin the U4 "not refuted" qualifier (fresh unit; prior execution was a false success)

**Unit:** GUARD-U4-R2 (author) · **Batch:** context-cache mechanism · **Automated session, no human present**
**Date (UTC):** 2026-10-23 · **Bound:** 40 tool calls · **Live requests: 0 — no lock taken, no endpoint touched**
**Write paths:** `orchestration/handoffs/GUARD-U4-R2.json`, `orchestration/units/GUARD-U4-R2.md`,
`tests/test_context_cache_qualifier.py`, and one prose repair at `papers/context-cache/MANUSCRIPT.md:216-218`
(the refutation stated as fact with no void, see §3)
**Status:** done

## 0. Why this unit is fresh

`GUARD-U4` reported a success that did not exist. Its handoff named
`tests/test_context_cache_qualifier.py` as an artifact and reported the guard as added; the file was
**absent from the tree** when this unit started (`ls` → *No such file or directory*), and its own card
still carried the unfilled stub placeholder. No `GUARD-U4-R1` card or handoff exists either. Under
AGENTS.md §"Unit contract" a unit is never extended: the false success is not repaired, it is superseded
by this fresh unit, which re-derives everything from the tree rather than from the earlier report.

## 1. Objective (the contract)

The package's U4 verdict is a **null result**: the cell driver rendered every arm through one appender
(`RENDER = naive_append`; `POINTER_FORK` never imported, C13), so a fork chain and a summarise chain over
the same nodes emitted identical bytes. U4's "identical break cost" (C11: 21 pairs, 18 exactly 0, p = 1.0)
therefore measures **renderer identity**, not policy, and its card's conclusion — *the edit-vs-fork
hypothesis was REFUTED* — is void. The only correct record is **untested at n>0, not refuted**. Pin that
qualifier so the absence of a refutation cannot be printed as a finding, and prove by red→green that the
pin bites.

## 2. What the guard asserts (`tests/test_context_cache_qualifier.py`, 14 tests)

| Side | Assertion |
|---|---|
| (A) PRESENCE | every document that names the comparison (MANUSCRIPT, CLAIMS, PACKAGE, EVIDENCE, GAPS) states within 500 chars that it is untested / not refuted / remains open |
| (B) DENY | no document asserts the **excluded middle** — neither *refuted* nor *fork and summarise cost the same* (the same null result dressed as a finding), screened so the tree's own dated criteria and quotations do not trip it |
| (self-check) | the deny screen is proved to catch the U4 card's verbatim sentence while NOT flagging the corrected tree's quotation of it |
| (C) PROVENANCE | MANUSCRIPT §5 keeps C13, C16, the 11/44 body count and the 438 rows; the abstract keeps the qualifier it reports as a negative result |
| (D) CODE-SIDE | `recompute.py` still pins C13 (`naive_append`, `POINTER_FORK_in_source: False`) and C11 (21 pairs, 18 zero, p = 1.0) |

## 3. The one prose repair

The guard found a real hole rather than only guarding a correct tree: `MANUSCRIPT.md:216-218` stated
*"On that basis the U4 card concluded the edit-vs-fork hypothesis was refuted and recorded a
kill-condition trigger."* **as fact, with the void only in the next paragraph.** A reader who stopped at
that sentence — or a citing machine that quoted it — took away the refutation. Fixed by appending the void
in the same paragraph: *"**That conclusion is void**: the paragraph below shows the pairs measured renderer
identity, so the hypothesis is not refuted but **untested at n>0** (C13, C16)."* No other document needed
an edit; their prose already carries the qualifier.

## 4. Red→green (measured, `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_context_cache_qualifier.py -q`)

| Run | Mutation | Result |
|---|---|---|
| GREEN (baseline) | none | `14 passed` |
| RED-1 | MANUSCRIPT §5 consequence reverted to `<hypothesis> **was refuted** by the comparison` and the "Writing "refuted" would propagate a null experiment" sentence deleted | `1 failed, 13 passed` — `[DENY]` at `MANUSCRIPT.md` (the §5 paragraph) |
| RED-2 | PACKAGE's bullet reverted to `The edit-vs-fork hypothesis is **refuted**;` and CLAIMS correction 3 to `the hypothesis is refuted` | `2 failed, 12 passed` — `[PRESENCE]` at `PACKAGE.md:95` and `CLAIMS.md:197` |
| RED-3 | `recompute.py`'s C13 expectation flipped to `pointer_fork` / `POINTER_FORK_in_source: True` | `1 failed, 13 passed` — the (D) code-side test |
| GREEN (restored) | all three reverted back | `14 passed`; MANUSCRIPT digest returned byte-identically to `a3defdf3e3a7118c093450ac1549585c4dd3e64ab66fed540b39e105960b1f07` |

## 5. Traps this unit hit (recorded so the next guard does not)

1. **Python 3.14: `[^\n]` does not match** in this build's `re` for this string (`[^\x0a]` fails too;
   `[\s\S]` works). The first RED-1 attempt passed because the deny regex could never span the
   qualifying text — a guard that silently cannot match is worse than no guard. **All character classes
   in the file now use `[\s\S]`.**
2. A `.` inside the qualifying text ("an edit policy") terminates a naive `[^.]` span; the spans are
   `[\s\S]{0,N}` and the caps were measured against the real sentence (61 chars).
3. `/tmp` snapshots are not reliably visible across sandboxed commands here; snapshots live in
   `scratch/u4r2snap/`.

## 6. Not done / open

- The full `tests/` suite is run at the end of this unit; its result is recorded in the handoff.
- No packet-level rebuild: the guard reads prose and one Python file, not rows. `recompute.py C13` and
  `C11` were not re-executed (they are unchanged and outside this unit's write paths other than the
  red-green revert, which was restored byte-identically).
