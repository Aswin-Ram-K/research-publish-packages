**Per-directory breakdown** -- each instrument is real, not a README claim:

| path | licence | instrument |
|---|---|---|
| `packages/*/code/`, `packages/*/eval/`, `gate.sh` and the repository scripts | PolyForm Noncommercial License 1.0.0 | [`LICENSE`](LICENSE) |
| `packages/*/paper/` (the manuscript and its scholarly apparatus) | **CC BY 4.0** (<https://creativecommons.org/licenses/by/4.0/>) | each package's `paper/LICENSE` |

The root `LICENSE` is the PolyForm Noncommercial License 1.0.0 **with a scope
clause** that defers to each package's `paper/LICENSE` for the paper text, so a
reader who opens only `LICENSE` still learns that the paper is CC BY 4.0.
Commercial licensing: [`COMMERCIAL.md`](COMMERCIAL.md). Contributions:
[`CONTRIBUTING.md`](CONTRIBUTING.md).

The licence texts are complete. The required notice reads "Required Notice:
Copyright 2026 Aswin-Ram-K"; licensing and contribution contact is the
repository's own issue tracker, <https://github.com/Aswin-Ram-K/research-publish-packages>.

**This repository is source-available, not open source** -- the PolyForm
Noncommercial licence is not an open-source licence.

## The exclusion gate

[`gate.sh`](gate.sh) is this repository's acceptance test. It is a **positive
vocabulary checker**, not a denylist: it tokenises every file in the tree and
requires every token to be a declared member of this tree's own vocabulary --
the placeholder/tag grammar, the frozen public-identifier and English word lists
under `vocabulary/`, and generic English. Anything else is listed with file and
line and fails the gate.

```bash
bash gate.sh    # exit 0 = every token declared; exit 1 = out-of-vocabulary tokens listed
```

The checker carries only allowed vocabulary, so it names none of the identifiers
the release withholds, and it does **not** exclude itself from its own scan.
