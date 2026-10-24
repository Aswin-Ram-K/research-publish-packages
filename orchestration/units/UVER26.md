# UVER26 — independent verification of UTOOL1's one-line tooling repair

**Unit:** UVER26 (verifier; not the author of the artifact). **Status:** `done`.
**Bound:** 25 tool calls; **used 23**. Workspace `/home/zer0null/reserach extarctor`.
**Verdict:** `pass` — `pass-with-corrections` not warranted; one cosmetic overstatement recorded.

**Write paths (the only paths written):** `strategy/VERIFICATION_REPORT_26.md`,
`orchestration/units/UVER26.md`, `orchestration/handoffs/UVER26.json`, `scratch/uver26/**`. Nothing in the
forbidden set was written; no git command was run against any target; `scratch/utool1/tree-six` was restored
byte-for-byte (see Containment in the report).

## What I was checking
`second-labeller/parse_fixture.py:16` was repointed from the absent `reflex-decisions.sandbox.ts` to
`os.pardir/fixture/reflex-decisions.ts`. The risk: a tool edited to keep working after material was withheld
could stop being evidence. I re-derived every UTOOL1 claim from disk with my own scripts
(`scratch/uver26/snapshot.py`, `check_manifest.py`, `qdiff.py`, `leak_scan.py`); the author's checker was not run.

## Result
`pass`. All eight claims reproduced: the exact one-line diff against `scratch/udtag1/tree-five`; the three
file identities; the withheld original really is the leaky one (10/10 mechanism tokens, 0 in the shipped
fixture; 47/190 question strings differ); both tools exit 0 with the claimed values; red→green reproduces the
literal `FileNotFoundError` at `:85` (exit 1) and exit 0 after restore; `metrics.json` `6bf39077…` identical
before/after; run output `5d05dd13…` identical to both earlier run trees; `ALL CLAIM NUMBERS PRESERVED: True`;
census 2171 inside / 30 distinct on both trees (total 3354→3356); manifest `0633a0a5…`, 44 listed = 44 on
disk, 0 mismatches, self-reference convention stated in `manifest_self`; two builds byte-identical
(`diff -rq` 0 lines).

**One overstatement (cosmetic):** UTOOL1.md's "only `second-labeller/parse_fixture.py` differs" — `diff -rq`
also reports `MANIFEST.json`, necessarily regenerated; disclosed elsewhere in the same card.

**Framing correction (not an author defect):** the instruction's "byte-identical to the shipped
`fixture/reflex-decisions.ts`" is true of the *emitted tree* (85,044 B, `ba810aa1…`) but not of the
SANITISED package copy (90,738 B, `751dc007…`); UTOOL1 itself distinguishes them correctly. The shipped
`EXCLUDED.md:40` (E15) statement "byte-identical duplicate of the fixture (145,031 B)" is false — pre-existing.

**Containment:** running `recompute-claims.py` against `scratch/utool1/tree-six` created
`second-labeller/__pycache__/parse_fixture.cpython-314.pyc`; I deleted it and re-verified tree-six against a
pre-run snapshot (45 files, diff exit 0). Target dirs untouched (mtimes predate the session).

Full detail, all values and the unverified list: `strategy/VERIFICATION_REPORT_26.md`.

## Blocker
None.

## Next unit hint
Reproduce UTOOL1's builder through its own entry point (`bash scratch/utool1/build_six.py <fresh>` into an
independent tree) rather than against `tree-six`/`tree-six-b`, and decide the pre-existing `EXCLUDED.md:40`
inaccuracy plus the 40/44 `source_sha256` exposure as author decisions.
