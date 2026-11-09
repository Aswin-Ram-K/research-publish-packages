# PATH-REFS-BATCH-FIX-2 — decide the ambiguous wrong_dir citations

**Purpose.** Round 1 left 130 `wrong_dir` citations with 2+ same-basename candidates. This unit
decides them by evidence (content → directory → ownership), and refuses to decide the rest.

**Bound.** 26 tool calls; offline; no `ask_user_question`; one pass, no extension.

**Rules, first that fires wins.** content: exactly one candidate contains the symbol the sentence
is about. dir: exactly one candidate sits in a directory the line names. owner: a unit card citing
an artefact that carries its own unit name as a PATH SEGMENT (not a substring — `V0` must not claim
a `v0.1` tree). Otherwise **undecidable**, with no mtime/recency tiebreak.

**Result.** in scope 121, decided 2 (both `test_cell` citations, both inside other units' cards,
which are outside this unit's write paths, so recorded and not applied), undecidable 119 — 86 of
which have every candidate inside a copy tree (`state/`, `dockets/`, fixtures, `jobs/`), i.e. they
are citations of artefacts that were never produced, not citations that moved.

**Guard.** `path_refs.py --check`: `wrong_dir` 645 → 636 with **0 new** keys. The 9-point drop is
concurrent tree drift (other units deleted scratch material mid-pass); this unit wrote no document
content.

**Artefacts.** `experiments/ptr-engine/tools/path_refs_resolve.py` (imports the guard, never
reimplements it), `tests/test_path_refs_resolve.py` (5 tests, incl. the red case and the
newer-but-still-undecidable case), `experiments/ptr-engine/measure/PATH-REFS-ROUND2.json`,
`docs/PATH-REFS-ROUND2.md`.

**Kill condition respected.** No threshold, hash or number in any published page was changed; no
handoff, journal, `measure/*.json` artefact, cell file, `cell.py`, `run_longrun.py` or fixture was
edited.
