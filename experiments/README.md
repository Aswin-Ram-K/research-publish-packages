# experiments/ — sandboxed, evidence-tracked experiments

This tree holds **experiments**: self-contained probes, second-labeller runs and method
trials that are allowed to be messy, incomplete or negative. An experiment is *not* part of
the pipeline and nothing in `src/` or `tests/` may depend on it.

> **Owner note:** `experiments/` is created and documented by unit **USTRUCT**. USTRUCT created
> the parent and this README **only**. Each `experiments/<name>/` directory is owned by the unit
> running that experiment and may appear while other work is in flight. The first one expected is
> `experiments/second-labeller-190/`.

## The safety rule — read this first

**An experiment works on a sandbox copy and never on `/home/zer0null/Duval`.**

- `/home/zer0null/Duval` is the acceptance target and is **strictly read-only**. Do not open it,
  do not write it, do not run `git` inside it, do not install hooks in it. This is a hard
  constraint on every unit, not a preference (see `AGENTS.md` → *Hard constraints*).
- If an experiment needs to modify target-shaped files, it first makes a **sandbox copy** under
  its own `experiments/<name>/` directory (or under `state/`) and runs against that copy. The copy
  lives inside this workspace; the original is untouched.
- Nothing is ever written outside this workspace: `/home/zer0null/reserach extarctor`.
- After an experiment, the target may be checked with **read-only** commands only
  (`git status`, mtime sweeps). No `git` state changes in the target, ever.

## Evidence-tracking convention

Every `experiments/<name>/` directory **must** carry:

| File | Meaning |
|---|---|
| `EVIDENCE.md` | The human-readable record: hypothesis, exact commands run, what was observed, raw numbers, and whether the hypothesis survived. Claims must be checkable — paste the command **and** its actual output, not a summary of it. Negative and partial results are results; record them plainly. |
| `RUN.json` | The machine-readable record: one valid JSON object describing the run — at minimum the experiment name, status (`done` / `failed` / `partial`), the commands executed, the artifacts produced, and the exact environment/target revision the run was made against. |

Conventions that follow from the above:

- `RUN.json` must be **valid JSON** — other units and the orchestrator parse it.
- An experiment that changed its method after a failure records **both** runs rather than
  overwriting the first: the failed run is the interesting one.
- Anything an experiment wants to keep must be inside its own directory (or `state/`); do not
  scatter outputs into the workspace root, `src/` or `tests/`.
