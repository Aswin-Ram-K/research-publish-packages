"""Red->green guard: the C63 engine-conditional ratio is a ratio of RAW means.

Why this file exists
--------------------
The manuscript states the model effect is **-222.89x** the SGLang figure under vLLM (``MANUSCRIPT.md``
abstract and Section 9b), and ``CLAIMS.md``/``SERVING-BRIEF.md`` state the same figure.
That figure has to be a *quotable* number: the printed operands are ``+548.06`` and
``+3.61``, and 548.06/3.61 = 151.8172, but those operands are themselves rounded.  The
ratio the claim actually asserts is the ratio of the two per-level model-effect MEANS,
which is -803.646 / 3.605634 = -222.8887 (MTP-corrected; the pre-correction
548.06 / 3.61 = 152.0 case is the same guard applied to superseded numbers).  Dividing the rounded operands
produces 151.8172, a figure no 4-dp derivation of the raw means can yield.

The failure mode is silent: a package that pins 151.8172 keeps passing ``recompute.py C63``
(it compares the pin against a pin derived the same wrong way), passing ``serving_brief.py
--check``, and passing every manuscript number check -- while the printed quote is not the
ratio of the means it names.  This file pins the ratio to the raw means instead.

What is in scope
----------------
(1) ``EXPECTED["C63"]["model_effect_ratio_vllm_over_sglang"]`` equals
    ``round(model_vllm_raw / model_sglang_raw, 4)``, computed here from the four row files
    without calling ``c63()``, and equals 152.0.
(2) The prose that quotes the ratio quotes that value at 2 dp (``152.00x``), in the
    abstract, Section 9b, ``CLAIMS.md``, the serving brief and the operator facings.

Red->green (proven 2026-10-24, ``PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
tests/test_c63_ratio_raw_operands.py -q``)
--------------------------------------------------------------------------
  RED.   ``EXPECTED["C63"]["model_effect_ratio_vllm_over_sglang"]`` restored to the
         shipped ``151.8172`` (rounded operands) -> ``test_pin_is_ratio_of_raw_means``
         fails with ``151.8172 != 152.0``; ``recompute.py C63`` exits 1.
  GREEN. Pin at ``152.0`` -> this file passes and ``recompute.py C63`` prints 43/43.

Offline: reads Markdown, `recompute.py` and the four cell row files off disk; no network,
no lock, no live request.
"""

from __future__ import annotations

import importlib.util
import statistics
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "papers" / "context-cache"
MANUSCRIPT = PACKAGE / "MANUSCRIPT.md"
CLAIMS = PACKAGE / "CLAIMS.md"
BRIEF = PACKAGE / "SERVING-BRIEF.md"
RECOMPUTE = PACKAGE / "recompute.py"
MATRIX = ROOT / "docs" / "serving-options" / "MATRIX-2x2.md"

#: The ratio of the two RAW per-level model-effect means, to 4 dp.  Hard-coded here on
#: purpose: this file is the independent statement of what the pin must be, so it must not
#: import the number it is checking.
RAW_RATIO_4DP = -222.8887


@pytest.fixture(scope="module")
def rec():
    spec = importlib.util.spec_from_file_location("cc_recompute_ratio", RECOMPUTE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def raw_level_means(rec) -> tuple[float, float]:
    """qwen3.5-9b-minus-occamy mean per turn, separately under vLLM and under SGLang.

    Deliberately does not call ``c63()`` or ``tl()``: the point is to re-derive the two
    operands of the ratio straight from the four cells' row files.
    """
    cells = {}
    for model, engine, cell, cfg in rec.C63_CELLS:
        by = {(r["arm"], int(r["turn"])): r for r in rec._c63_cell_rows(cell, cfg)}
        cells[(model, engine)] = by
    arms, turns = rec.C63_ARMS, rec.C63_TURNS

    def per_turn(model: str, engine: str) -> list[float]:
        by = cells[(model, engine)]
        return [statistics.fmean(rec._c63_unc(by[(arm, t)]) for arm in arms)
                for t in range(1, turns + 1)]

    v = per_turn("qwen3.5-9b", "vllm"), per_turn("occamy-1.0", "vllm")
    s = per_turn("qwen3.5-9b", "sglang"), per_turn("occamy-1.0", "sglang")
    under_vllm = statistics.fmean(d - m for d, m in zip(*v))
    under_sglang = statistics.fmean(d - m for d, m in zip(*s))
    return under_vllm, under_sglang


def test_operands_are_the_printed_ones(rec) -> None:
    """The two raw means round to the numbers the prose actually prints."""
    under_vllm, under_sglang = raw_level_means(rec)
    assert round(under_vllm, 2) == -803.65, f"model|vLLM raw mean moved: {under_vllm!r}"
    assert round(under_sglang, 2) == 3.61, f"model|SGLang raw mean moved: {under_sglang!r}"


def test_pin_is_ratio_of_raw_means(rec) -> None:
    """The pinned ratio must be the raw-mean ratio, not 548.06/3.61.

    Red under the shipped pin: 151.8172 is 548.06/3.61 (rounded operands); the raw-mean
    ratio is 152.0.  The claim text quotes this figure at 4 dp, so it has to be 152.0.
    """
    under_vllm, under_sglang = raw_level_means(rec)
    ratio = round(under_vllm / under_sglang, 4)
    assert ratio == RAW_RATIO_4DP, f"raw-mean ratio moved: {ratio!r}"
    pinned = rec.EXPECTED["C63"]["model_effect_ratio_vllm_over_sglang"]
    assert pinned == RAW_RATIO_4DP, (
        f"EXPECTED['C63']['model_effect_ratio_vllm_over_sglang'] is {pinned!r}, but the "
        f"ratio of the raw means is {ratio!r}.  {pinned!r} is reproducible only as "
        f"548.06/3.61 -- a ratio of rounded operands -- and is not a truthful 4-dp figure."
    )
    assert rec.c63()["model_effect_ratio_vllm_over_sglang"] == RAW_RATIO_4DP


@pytest.mark.parametrize("path", [MANUSCRIPT, CLAIMS, BRIEF, MATRIX])
def test_prose_quotes_the_raw_ratio_and_not_the_rounded_operand_ratio(path: Path) -> None:
    """No shipped surface may still quote the ratio as 151.8172 / 151.82x.

    The bare operand pair ``548.06`` and ``3.61`` stays legitimate -- those ARE the two
    level means the prose prints.  What must not survive is the *ratio* derived from them:
    the literal figure ``151.8172`` or the 2-dp quote ``151.82x``.
    """
    assert path.is_file(), f"{path} is missing -- the guard has nothing to read"
    text = path.read_text(encoding="utf-8")
    for stale in ("151.8172", "151.82x", "151.82 x"):
        assert stale not in text, (
            f"{path.relative_to(ROOT)} still quotes {stale!r}: that figure divides the "
            f"rounded operands, not the raw means ({RAW_RATIO_4DP!r})"
        )
    # The prose quotes the ratio at 2 dp ("152.00x"); SERVING-BRIEF renders the same
    # figure at 4 dp from the ledger ("152.0000").  Either form is the raw-mean ratio.
    assert "-222.89x" in text or "-222.8887" in text, (
        f"{path.relative_to(ROOT)} no longer states the ratio as -222.89x / -222.8887"
    )
    # The ratio is negative, so its prose rendering must be too.  A hard-coded leading '+'
    # in the guard let the manuscript print '+-222.89x' and still pass; a double sign is a
    # sign artifact, not a quotable figure.
    assert "+-" not in text, (
        f"{path.relative_to(ROOT)} carries a double-signed figure ('+-...'): render the sign "
        f"of the measured value, not a template's"
    )
