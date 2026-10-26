"""
tccommon.py — EXP#12 shared rendering and scoring primitives.

Pre-registration: docs/research/experiments/EXP#12-typed-channel-comparison.md (frozen).

WHY THIS MODULE EXISTS. The training renderer and the evaluation renderer MUST be the same renderer,
or the experiment measures a formatting difference. `render()` is defined once here and imported by
`prepare.py`, `train.py` and `evaluate.py`; nothing else is allowed to build a model input.

THE RENDERING, AND WHY IT IS THIS SHAPE
  The 4B deciders were scored on the sealed 190 as (docs/research/L1_HEAD_TO_HEAD.md, "Method"):

      state     = {"kind": kind, "question": question}
      questions = {"choice": {"type": "choice", "instructions": question,
                              "criteria": {opt: opt for opt in options}}}

  so the information a decider saw for a fixture case is: the kind, the question text, and the option
  set. The encoder gets exactly that information — no more, and nothing the decider did not get
  (`rationale` and `namespaces` are never read, and neither is `correct`).

  A corpus row and a fixture row do not carry the same fields: the corpus has `state` (the facts) and
  `instructions` (the family's rules); the fixture has a single `question` paragraph that states both
  the facts and the applicable invariant. The aligned choice is therefore ONE situation slot that
  carries everything the case provides, so the two sides differ in content and not in structure:

      corpus  : situation = state + " " + instructions
      fixture : situation = question

  `criteria` is deliberately NOT in the situation. It is a label-keyed restatement of the rules, the
  fixture has no counterpart for it, and including it on one side only is exactly the structural
  asymmetry this template exists to avoid.

  Per candidate option the model input is three lines, constant across every arm:

      Task: pick the one option the situation selects.
      Kind: <kind>
      Situation: <situation>
      Candidate option: <option>

  The first line is constant for every case in every split and every arm, so it cannot leak.

  `kind` is normalised through KIND_ALIAS because the corpus names some kinds by sub-path
  (`acquisition.path`, `escalation.decision`, `routing.team`) where the fixture names the parent
  (`acquisition`, `escalation`). The alias table is explicit and total: a kind not in the table is
  passed through unchanged, and `kind_aliases_used()` reports what was rewritten so the choice is
  auditable rather than silent.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "out"

CORPUS_PATH = DATA / "corpus.json"
FIXTURE_PATH = DATA / "fixture-190.json"
LINT_REPORT_PATH = DATA / "lint-report.json"

CORPUS_SHA256 = "c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66"
INSTRUMENT_190_SHA256 = "076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796"

TASK_PREFIX = "Task: pick the one option the situation selects."

#: corpus kind -> the fixture's name for the same decision family. Explicit and auditable.
KIND_ALIAS = {
    "acquisition.path": "acquisition",
    "escalation.decision": "escalation",
    "topology.shape": "topology",
    "routing.team": "routing",
}

#: the frozen baselines this experiment is measured against (pre-registration §3).
#: The published figures, each labelled with the stratum it actually comes from. The stratum matters:
#: the re-score showed that `imajev-4b 0.645` is its H-A corpus accuracy, while its 190-instrument
#: accuracy is 0.6368 — the pre-registration §3 lists it beside two fixture figures without saying so.
BASELINES = {
    "decider-4b (published, D-067), instrument190": 0.6684,
    "imajev-4b (published), H-A corpus stratum": 0.645,
    "laya-typed-decisions (published), instrument190": 0.374,
    "decider-4b EXP#11 reproduction, instrument190": 0.6789,
}

#: F1's threshold, exactly as the pre-registration writes it.
F1_THRESHOLD = 0.6684
#: the 4B's measured warm per-decision latency, F6's threshold, in seconds.
F6_4B_LATENCY_S = 0.075


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def kind_aliases_used(kinds) -> dict:
    return {k: KIND_ALIAS[k] for k in sorted(set(kinds)) if k in KIND_ALIAS}


def render_context(kind: str, situation: str) -> str:
    """The case text WITHOUT the candidate line — the shared prefix every option of a case sees."""
    kind_norm = KIND_ALIAS.get(kind, kind)
    return (
        f"{TASK_PREFIX}\n"
        f"Kind: {kind_norm}\n"
        f"Situation: {' '.join(str(situation).split())}"
    )


def render(kind: str, situation: str, option: str) -> str:
    """The one renderer. Every arm and every split goes through this function."""
    return f"{render_context(kind, situation)}\nCandidate option: {' '.join(str(option).split())}"


# ------------------------------------------------------------------ loading


def load_corpus(path: Path = CORPUS_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf8"))


def load_fixture(path: Path = FIXTURE_PATH) -> list:
    return json.loads(Path(path).read_text(encoding="utf8"))


def corpus_situation(case: dict) -> str:
    return f"{case['state']} {case['instructions']}"


def corpus_case_to_example(case: dict) -> dict:
    """One corpus case -> the arm-agnostic example the trainers consume."""
    return {
        "id": case["caseId"],
        "familyId": case["familyId"],
        "clanId": case["clanId"],
        "kind": case["kind"],
        "stratum": case["stratum"],
        "situation": corpus_situation(case),
        "options": list(case["options"]),
        "goldIndex": list(case["options"]).index(case["gold"]),
        "gold": case["gold"],
    }


def fixture_case_to_example(case: dict) -> dict:
    return {
        "id": case["id"],
        "kind": case["kind"],
        "situation": case["question"],
        "options": list(case["options"]),
        "goldIndex": int(case["correct"]),
        "gold": case["options"][int(case["correct"])],
    }


def texts_for_example(example: dict) -> list:
    return [render(example["kind"], example["situation"], o) for o in example["options"]]


# ------------------------------------------------------------------ metrics


def ece(probs, correct, n_bins: int = 10) -> float:
    """Expected calibration error, 10 equal-width bins on the confidence of the chosen option.

    Matches the L1 head-to-head protocol (docs/research/L1_HEAD_TO_HEAD.md), so the encoder's ECE is
    directly comparable to the deciders' published figures.
    """
    bins = [[] for _ in range(n_bins)]
    for p, c in zip(probs, correct):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, c))
    total = len(probs)
    if total == 0:
        return float("nan")
    out = 0.0
    for b in bins:
        if not b:
            continue
        conf = sum(p for p, _ in b) / len(b)
        acc = sum(1 for _, c in b if c) / len(b)
        out += (len(b) / total) * abs(conf - acc)
    return out


def brier(probs, correct) -> float:
    """Brier score on the chosen option's probability: mean (p - 1{correct})^2. Lower is better."""
    if not probs:
        return float("nan")
    return sum((p - (1.0 if c else 0.0)) ** 2 for p, c in zip(probs, correct)) / len(probs)


def softmax(xs, temperature: float = 1.0):
    m = max(xs)
    if not math.isfinite(m):
        # an all-(-inf) row cannot happen (masked slots are dropped before the softmax) but a
        # non-finite maximum must not silently become NaN
        raise ValueError("softmax received a non-finite maximum")
    exps = [math.exp((x - m) / temperature) for x in xs]
    s = sum(exps)
    return [e / s for e in exps]


def fit_temperature(logit_sets, gold_indices) -> float:
    """Fit one scalar temperature on the development split by minimising NLL.

    Scalar temperature scaling (Guo et al. 2017): it cannot change the argmax, so it cannot change
    accuracy — only the calibration numbers. Grid search over a fixed, reported grid, so the fitted
    value is reproducible without an optimiser dependency.
    """
    # A GEOMETRIC grid from 0.01 to 10.0: a linear grid put the fitted optimum on its own boundary for
    # two of the three heads on the first run (T = 0.25 and T = 0.05), which would have reported a
    # calibration number the fit had not actually reached. Temperature cannot move the argmax, so a
    # wider grid cannot change accuracy — only the calibration read.
    grid = [round(1e-3 * (1e5 ** (i / 199.0)), 6) for i in range(200)]  # 0.001 .. 100.0
    best_t, best_nll = 1.0, float("inf")
    for t in grid:
        nll = 0.0
        for logits, gold in zip(logit_sets, gold_indices):
            p = softmax(logits, t)[gold]
            nll += -math.log(max(p, 1e-12))
        nll /= max(len(logit_sets), 1)
        if nll < best_nll:
            best_t, best_nll = t, nll
    return best_t


def accuracy(pred_idx, gold_idx) -> float:
    if not gold_idx:
        return float("nan")
    return sum(1 for p, g in zip(pred_idx, gold_idx) if p == g) / len(gold_idx)


def per_kind_accuracy(rows) -> dict:
    """rows: dicts with `kind`, `predIndex`, `goldIndex`."""
    agg: dict = {}
    for r in rows:
        a = agg.setdefault(r["kind"], {"n": 0, "correct": 0})
        a["n"] += 1
        a["correct"] += int(r["predIndex"] == r["goldIndex"])
    return {k: {"n": v["n"], "correct": v["correct"], "accuracy": v["correct"] / v["n"]} for k, v in sorted(agg.items())}


def per_class_accuracy(rows) -> dict:
    """Per-GOLD-LABEL accuracy over the fixture's option labels (H2/F3's per-class read)."""
    agg: dict = {}
    for r in rows:
        a = agg.setdefault(r["gold"], {"n": 0, "correct": 0})
        a["n"] += 1
        a["correct"] += int(r["predIndex"] == r["goldIndex"])
    return {k: {"n": v["n"], "correct": v["correct"], "accuracy": v["correct"] / v["n"]} for k, v in sorted(agg.items())}


def bootstrap_ci(values, n_boot: int = 2000, seed: int = 20261004, alpha: float = 0.05):
    """Percentile bootstrap CI of a mean — used for accuracy and ECE intervals."""
    import random

    rng = random.Random(seed)
    n = len(values)
    if n == 0:
        return (float("nan"), float("nan"))
    means = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += values[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[min(int((1 - alpha / 2) * n_boot), n_boot - 1)]
    return (lo, hi)


def write_json(path: Path, obj) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf8")
