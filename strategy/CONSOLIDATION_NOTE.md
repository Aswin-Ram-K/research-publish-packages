# Consolidation note — papers #2 and #3

**Status: RECORDED, NOT ACTIONED.** Dated 2026-10-19 (UPKGINSTALL7), from an observation and an
explicit instruction by the author.

## The observation

The author's view: paper #2 (*Replay reproduces the record, not the decision*) and paper #3 (*The
small-encoder crossover is a prompted-baseline artefact …*) are **closely related enough that they
would have made more sense as one consolidated paper** than as two separate notes.

## The instruction

**Keep them as they are now.** Record the observation and do nothing about it. This note is that
record; no other artifact changes because of it.

Explicitly **not** done, by instruction:

- no merge or re-draft of either manuscript;
- no change to either released package, deposit archive, `CITATION.cff` or DOI;
- no renumbering or renaming of the papers;
- no edit to either paper's `MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md` or release area.

## The measured fact behind the observation

The two works are not merely topically adjacent — **they share one corpus.** Both are built on the same
**190 cases**, with the same per-kind counts **30 / 30 / 26 / 22 / 26 / 28 / 28**. Paper #3's released
stimulus fixture is that instrument (`papers/encoder-crossover-190/released/encoder-crossover-190-released/fixture/fixture-190.json`,
a 190-entry list); paper #2 states that its companion fixture "carries the **same 190 cases** … with the
**same per-kind counts**" and "is **not** an independent corpus and not a differently-sampled one"
(`papers/replay-record-not-decision/MANUSCRIPT.md:308–317`).

The two releases tag those kinds differently — paper #3's fixture uses neutralised `K`/`N` tags, paper
#2's records use their own kind names — and **the correspondence is uniquely recoverable**: ordering
each kind's cases by numeric suffix, the per-kind sequence of `correct` values admits exactly one
bijection of the seven kinds (`papers/replay-record-not-decision/MANUSCRIPT.md:315–316`):

| paper #3 tag | paper #2 kind |
|---|---|
| `K01` | `escalation` |
| `K02` | `worker.class` |
| `K03` | `acquisition` |
| `K04` | `topology` |
| `K05` | `capability.family` |
| `K07` | `memory.admission` |
| `N10` | `context.package` |

Neither release states the mapping; it must be recovered by the rule above. That is a fact about how the
two deposits relate, not a defect in either, and it changes nothing while the papers stay separate.

## What a reader should take from this

Recorded for future reference only: if the author ever revisits the split, the shared 190-case corpus
and the recoverable tag bijection are the concrete ground for consolidation. Until then, treat the two
papers and their deposits as **independent works that happen to share an instrument**.
