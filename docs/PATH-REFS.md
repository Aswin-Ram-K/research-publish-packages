# PATH-REFS — a document may not cite a path the tree does not have

**Guard:** [`experiments/ptr-engine/tools/path_refs.py`](../experiments/ptr-engine/tools/path_refs.py)
· **Tests:** [`test_path_refs.py`](../experiments/ptr-engine/longrun/tests/test_path_refs.py)
· **Baseline:** [`state/logs/path-refs-baseline.json`](../state/logs/path-refs-baseline.json)

```bash
python3 experiments/ptr-engine/tools/path_refs.py --report          # full census, file:line
python3 experiments/ptr-engine/tools/path_refs.py --check           # exit 1 on a NEW bad ref
python3 experiments/ptr-engine/tools/path_refs.py --write-baseline  # re-freeze (forward-only)
python3 -m pytest experiments/ptr-engine/longrun/tests/test_path_refs.py -q   # 6 tests
```

## Why this exists

Four cards in one batch each cost a correction because a document named a path that was not
there: `verdict_with_freeze.py` (twice, two different cards), the phantom `docs/GATE-SIMPLIFY.md` named before it
existed, `docs/PRICE-REPLICATION.md` likewise, and finally the phantom `docs/BUDGET-SCHEDULE.md` — cited by
`docs/PRICE-REPLICATION.md:222`, by `experiments/ptr-engine/measure/price-replication.json`
(:35, :39, :115, :119, :393) and by `orchestration/handoffs/PRICE-REPLICATION.json:27`, while the
artefact was `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` all along.

The patch is cheap; the instrument is the deliverable. A reviewer cannot be the mechanism.

## What it scans

`docs/**/*.md` · `experiments/ptr-engine/measure/*.md` · `experiments/ptr-engine/measure/*.json`
· `orchestration/units/*.md` · `orchestration/handoffs/*.json`

Path-shaped references are matched with

```
\b(docs|experiments|orchestration|papers|tests|state)/[\w./-]+\.(md|json|jsonl|py|sh|txt)\b
```

backticked or bare — markdown links are matched through the `../experiments/...` form, which the
regex picks up from the `experiments/` segment onward.

## Classifications

| class | meaning |
|---|---|
| `ok` | resolves at the cited path, byte for byte |
| `wrong_dir` | does not resolve, but the same basename exists in the tree; `resolved` names where. The two directories this corpus actually moves artefacts between are tried first — `experiments/ptr-engine/measure/<basename>`, `docs/<basename>` — then a unique in-tree location anywhere else |
| `missing` | no file with that basename anywhere in the tree. **Reported, never repaired by creating it** — a deliberate future path is not a defect, and creating the file a citation names is how a phantom becomes a lie |
| `ignored` | the citing line is *discussing* a path, not citing it (allowlist below) |

`wrong_dir` covers a unique location elsewhere in the tree as well as the two legal alternates:
for example, a citation to `tests/test_cap_gate.py` when the file is at
`experiments/ptr-engine/longrun/tests/test_cap_gate.py` is still wrong, even though a human can
guess it. Guessing is what the guard replaces.

## The baseline is forward-only

`--write-baseline` freezes every current `wrong_dir` + `missing` occurrence under the key
`<citing-file>::<cited-path>`, with the class and the resolved path it had when frozen. `--check`
exits **1** for any bad key **not** in the file and **0** when only baselined keys remain. Nothing
is excused silently: every frozen finding is in the file and greppable.

A key that was baselined and is later corrected simply stops being reported — the baseline is not
rewritten when a citation is fixed. The known limitation, inherited from `journal-lint`: a fixed
key that is reintroduced later is exempt again, because it is still a baselined key.

## Allowlist (each entry justified, one line)

A citing line carrying one of these is classified `ignored`:

| phrase | why it is allowed |
|---|---|
| `does not exist` | the record is naming a phantom as a phantom — e.g. `docs/COLD-START-PROBE.md:66` says of `docs/BUDGET-SCHEDULE.md` "**It does not exist**"; suppressing that sentence would delete the finding |
| `not exist` | the bare form of the same sentence, which "does not exist" already contains; kept separate so a line reading "the path does not exist today" is caught even without the auxiliary |
| `nonexistent` | the adjective form of the same statement, used when a section is about absent artefacts |
| `phantom` | the corpus's own word for a cited-but-absent path (`phantom <path>`), used by the cold-start probe and its unit card |
| `WI-` | a withdrawn-item id; `WITHDRAWN.json` intentionally names artefacts that no longer ship, so a line citing `WI-…` is a record of withdrawal |
| `for example` | explicitly illustrative line — the card forbids parsing a path out of an illustrative example |
| `no such file` | the shell error phrasing, quoted in records of a failed run |

The allowlist is deliberately short and phrase-based, not path-based: a path-based allowlist would
excuse the *same* phantom everywhere, including in a citation that means it.

Walks prune `.git`, `node_modules`, caches, and the ephemeral verifier copies `.scratch/` and
`.verify-scratch/`. Without that last prune, a basename "existed" inside a judge's snapshot one
minute and vanished the next, flipping one citation between `wrong_dir` and `missing` between two
runs of the same scan.

## What the first pass found (2026-10-26)

Census over the corpus: **ok 25,232 · wrong_dir 789 · missing 263 · ignored 195**. The dominant
`wrong_dir` family is a shorthand for the longrun tests — for example `tests/test_cap_gate.py` for
`experiments/ptr-engine/longrun/tests/test_cap_gate.py` — which the guard records rather than
rewrites, because rewriting 700 citations of prose is not this card's job and the baseline is the
honest place for them.

The seven `BUDGET-SCHEDULE` citations were corrected, token only, no prose rewritten:

```diff
- docs/PRICE-REPLICATION.md:222                      **`docs/BUDGET-SCHEDULE.md` §7** goes stale
+ docs/PRICE-REPLICATION.md:222    **`experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` §7** goes stale
- price-replication.json:35/39/115/119/393           "…docs/BUDGET-SCHEDULE.md §1/§2/§3/§7…"
+ price-replication.json:35/39/115/119/393   "…experiments/ptr-engine/measure/BUDGET-SCHEDULE.md §…"
- orchestration/handoffs/PRICE-REPLICATION.json:27   "docs/BUDGET-SCHEDULE.md §7 'Default: A*'"
+ orchestration/handoffs/PRICE-REPLICATION.json:27 "experiments/…/measure/BUDGET-SCHEDULE.md §7 'Default: A*'"
```

After the correction the class counts move by exactly those seven (`wrong_dir` 795 → 789 at that
point in the corpus) and `--check` goes **1 → 0**.

## The sentence the record needs

**No.** A document can no longer name a path that is not there without the guard noticing: every
path-shaped reference in the scanned corpus is resolved on every `--check`, and a new `wrong_dir`
or `missing` reference not frozen in `state/logs/path-refs-baseline.json` fails the run with
`file:line`, the class and the resolved path.

What the guard does **not** prove: that a cited path is the *right* path — only that it is *a*
path. A citation to a real but wrong file still passes, and `--check` says nothing about whether
the document reads correctly around the corrected token.
