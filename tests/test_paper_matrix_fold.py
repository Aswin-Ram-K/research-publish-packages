"""Red->green guard: the 2x2 matrix (C63) is measured, separable, and mapped.

Why this file exists
--------------------
Until MATRIX-FOLD the package could not separate an *engine* effect from a *model* effect:
Section 9a compared SGLang on occamy-1.0 with vLLM on qwen3.5-9b, so every cross-engine
contrast carried the model change with it.  Four cells now measure the same byte-identical
32k/71-turn schedule (arms R/A/C/H) and C63 decomposes the four cell means into an engine
main effect, a model main effect and their interaction.  The failure mode is a package that
keeps quoting the 2x2 while the numbers drift, or that states the effects but not which
factor is conditional -- so this file pins both the prose and the recompute.

What is in scope
----------------
(1) ``MANUSCRIPT.md`` has the section, names C63, and every cell figure and effect in it
    equals ``recompute.c63()`` recomputed from the four row files.
(2) The abstract's sixth result carries the engine number and names C63.
(3) ``CLAIMS.md`` maps C63 to the four cells and to one command; ``READER-MAP.md`` maps it
    to the ``c63`` function.
(4) Red->green: mutating one pinned C63 value, or dropping one of the four cells, makes the
    recompute fail.

Red->green (proven 2026-10-24, ``PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
tests/test_paper_matrix_fold.py -q``)
--------------------------------------------------------------------------
  RED-1 (pinned value).  ``EXPECTED["C63"]["engine_effect"] += 1.0`` ->
  ``recompute.check("C63")`` returns 1 (one FAIL line).
  RED-2 (missing cell).  ``C63_CELLS`` cut to three cells -> ``recompute.c63()`` raises.
  GREEN.  Both restored; ``recompute.py C63`` prints 41/41 values match.

Offline: reads three Markdown files, `recompute.py` and the four row files off disk; no
network, no lock.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "papers" / "context-cache"
MANUSCRIPT = PACKAGE / "MANUSCRIPT.md"
CLAIMS = PACKAGE / "CLAIMS.md"
READER = PACKAGE / "READER-MAP.md"
RECOMPUTE = PACKAGE / "recompute.py"


def read(path: Path) -> str:
    assert path.is_file(), f"{path} is missing -- the guard has nothing to read"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rec():
    spec = importlib.util.spec_from_file_location("cc_recompute_matrix", RECOMPUTE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def section(text: str, heading: str) -> str:
    start = text.find(heading)
    assert start >= 0, f"MANUSCRIPT.md no longer has the '{heading}' section"
    nxt = text.find("\n## ", start + len(heading))
    return text[start: nxt if nxt > start else len(text)]


def test_matrix_section_exists_and_names_its_claim() -> None:
    body = section(read(MANUSCRIPT), "## 9b.")
    assert "C63" in body, "MANUSCRIPT.md Section 9b no longer names C63"
    assert "2x2" in body or "four-cell" in body.lower(), (
        "MANUSCRIPT.md Section 9b no longer says the design is a 2x2"
    )


def test_every_cell_figure_in_the_manuscript_equals_the_recompute(rec) -> None:
    """The four-row table is the measurement; each row must match c63() exactly."""
    body = section(read(MANUSCRIPT), "## 9b.")
    rows = [ln for ln in body.splitlines() if ln.startswith("| ") and "---" not in ln]
    got = rec.c63()
    problems = []
    for model, engine, n, hit, unc, unit in got["cells"]:
        want_hit = f"{hit:.6f}"
        want_unc = f"{unc:,.2f}"
        want_unit = f"{unit:,}"
        model_tok = "occamy-1.0" if model == "occamy-1.0" else "qwen3.5-9b"
        engine_tok = "vLLM" if engine == "vllm" else "SGLang"
        match = [r for r in rows if model_tok in r and engine_tok in r
                 and want_hit in r and want_unc in r]
        if not match:
            problems.append(f"{model}/{engine}: no row carries {want_hit}, {want_unc}")
        elif want_unit not in match[0]:
            problems.append(f"{model}/{engine}: row lacks cache unit {want_unit}: {match[0]}")
        elif str(n) not in match[0] and n != got["rows_per_cell"]:
            problems.append(f"{model}/{engine}: row lacks row count {n}")
    assert not problems, "MANUSCRIPT.md Section 9b table disagrees with c63(): " + "; ".join(problems)


def test_every_effect_sentence_in_the_manuscript_equals_the_recompute(rec) -> None:
    """The effect numbers are quoted prose; a drift here is invisible to CLAIMS.md."""
    got = rec.c63()
    body = " ".join(section(read(MANUSCRIPT), "## 9b.").split())

    def ci(pair: tuple[float, float]) -> str:
        return f"[{pair[0]:,.1f}, {pair[1]:,.1f}]"

    required = [
        f"+{got['engine_effect']:,.2f}",
        ci(got["engine_ci"]),
        f"{got['engine_positive_turns']} of {got['paired_turns']}",
        f"+{got['model_effect']:,.2f}",
        ci(got["model_ci"]),
        f"+{got['interaction']:,.2f}",
        ci(got["interaction_ci"]),
        f"+{got['model_vllm']:,.2f}",
        ci(got["model_vllm_ci"]),
        f"+{got['model_sglang']:,.2f}",
        ci(got["model_sglang_ci"]),
        f"{got['model_sglang_positive_turns']} of {got['paired_turns']}",
        f"{got['engine_ratio_mean']:.4f}x",
        f"{got['engine_ratio_moe']:.4f}x",
        f"{got['engine_ratio_dense']:.4f}x",
        f"{got['model_ratio_mean']:.4f}x",
        f"{got['model_ratio_vllm']:.4f}x",
        f"{got['model_ratio_sglang']:.4f}x",
        f"{got['engine_over_model']:.4f}x",
        f"{got['engine_share_of_grand']:.4f}",
        f"{got['cell_mean_grand']:,.2f}",
        f"{got['model_effect_ratio_vllm_over_sglang']:.2f}x",
    ]
    arms_e = [v for _a, v in got["per_arm_engine"]]
    arms_m = [v for _a, v in got["per_arm_model"]]
    required += [f"{min(arms_e):,.1f}-{max(arms_e):,.1f}",
                 f"{min(arms_m):,.1f}-{max(arms_m):,.1f}"]
    missing = [t for t in required if t not in body]
    assert not missing, (
        "MANUSCRIPT.md Section 9b no longer states these recomputed values: "
        + repr(missing)
    )


def test_abstract_carries_the_sixth_result(rec) -> None:
    text = read(MANUSCRIPT)
    head = text[: text.find("\n## 1.")]
    assert "sixth result" in head.lower(), "the abstract dropped its sixth-result paragraph"
    got = rec.c63()
    assert f"{got['engine_effect']:,.2f}" in head, "the abstract lost the engine effect"
    assert "C63" in head, "the abstract's sixth result no longer cites C63"


def test_claims_and_reader_map_map_c63_to_four_cells_and_one_command() -> None:
    raw = read(CLAIMS)
    for token in ("C63", "MOE-VLLM-rows", "G3-rows", "WIN-VLLM-rows", "DENSE-SGL-rows"):
        assert token in raw, f"CLAIMS.md no longer maps C63 to {token}"
    assert "recompute.py C63" in raw, "CLAIMS.md's C63 row lost its single command"
    assert re.search(r"^\|\s*C63\s*\|", raw, re.MULTILINE), "CLAIMS.md has no C63 row"
    reader = read(READER)
    assert re.search(r"^\|\s*C63\s*\|\s*c63\s*\|", reader, re.MULTILINE), (
        "READER-MAP.md no longer maps C63 to the c63 function"
    )
    assert "MOE-VLLM" in reader and "DENSE-SGL" in reader, (
        "READER-MAP.md's C63 row lost one of the matrix cells"
    )


def test_recompute_is_green_before_the_red_tests(rec) -> None:
    assert rec.check("C63") == 0, "recompute.check('C63') is not green on the unmodified tree"


def test_c63_fails_when_one_pinned_value_is_mutated(rec) -> None:
    """RED-1: a drifted pin must fail the claim, not pass on the other 40 values."""
    saved = rec.EXPECTED["C63"]["engine_effect"]
    rec.EXPECTED["C63"]["engine_effect"] = float(saved) + 1.0
    try:
        assert rec.check("C63") == 1, "a mutated engine_effect did not fail C63"
    finally:
        rec.EXPECTED["C63"]["engine_effect"] = saved


def test_c63_fails_when_one_cell_is_missing(rec) -> None:
    """RED-2: the claim is a four-cell contrast; three cells must not recompute."""
    saved = rec.C63_CELLS
    rec.C63_CELLS = tuple(c for c in saved if c[2] != "WIN-VLLM")
    try:
        with pytest.raises(Exception):
            rec.c63()
    finally:
        rec.C63_CELLS = saved
