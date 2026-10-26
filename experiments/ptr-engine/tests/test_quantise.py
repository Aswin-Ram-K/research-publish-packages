"""Tests for the quantiser -- the module that makes the append cost a choice.

What is pinned here, in the order the contract states it:

* ``token_len`` is exact and refuses to guess (no tokenizer -> a coded error);
* ``choose_padding`` lands the PROMPT on the target residue, including when the
  request carries an offset (the other messages + the template's framing), which is
  the defect the first measurement pass caught;
* padding is VISIBLE in the artefact: ``text == base + padding``, counted, and the
  row-shaped ``as_dict()`` carries it;
* the same input gives byte-identical output in another process;
* ``predict_billed`` reproduces the measured law at residues 0, 1, 2 and 63 (the
  last legal residue), including the avalanche;
* ``compact_index`` drops only redundancy -- a compacted line still parses and
  resolves to the same full sha256 -- and refuses a line it cannot account for.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ptr_engine import PtrAnnotationError, Scope, parse, resolve
from ptr_engine.quantise import (
    AVALANCHE_RESIDUES,
    BLOCK_SIZE_DEFAULT,
    COMPACT_HASH_CHARS,
    DEFAULT_TARGET_RESIDUE,
    NEUTRAL_TOKEN,
    ServerTokenizer,
    StubTokenizer,
    choose_padding,
    compact_index,
    cycle_bill,
    predict_billed,
    token_len,
)

ENGINE_ROOT = Path(__file__).resolve().parents[1]


def _words(count: int) -> str:
    """A string the stub counts as exactly ``count`` tokens."""
    return " ".join(f"w{i}" for i in range(count))


# ------------------------------------------------------------------ token_len
def test_token_len_counts_exactly_and_refuses_a_missing_tokenizer():
    stub = StubTokenizer()
    assert token_len("", stub) == 0
    assert token_len(" the the the", stub) == 3
    assert token_len(_words(37), stub) == 37

    with pytest.raises(PtrAnnotationError) as excinfo:
        token_len("x", None)
    assert excinfo.value.code == "PTR_ANNOTATION_INVALID"

    with pytest.raises(PtrAnnotationError):
        token_len(123, stub)  # type: ignore[arg-type]


def test_token_len_is_never_a_guess_about_the_server():
    """The server-backed tokenizer is opt-in; nothing else in the module dials out."""
    signature = inspect.signature(choose_padding)
    assert signature.parameters["tokenizer"].default is None
    assert signature.parameters["offset_tokens"].default == 0
    assert inspect.isclass(ServerTokenizer)
    assert not isinstance(ServerTokenizer, ServerTokenizer)


# -------------------------------------------------------------- choose_padding
@pytest.mark.parametrize("target", [0, 1, 2, 63])
@pytest.mark.parametrize("residue", [0, 1, 2, 3, 37, 62, 63])
def test_choose_padding_lands_the_prompt_on_the_target_residue(target, residue):
    stub = StubTokenizer()
    padding = choose_padding(_words(residue), target, BLOCK_SIZE_DEFAULT, stub)
    assert padding.padded_tokens % BLOCK_SIZE_DEFAULT == target % BLOCK_SIZE_DEFAULT
    assert padding.residue_after == target
    assert padding.residue_before == residue
    assert padding.token_source == "StubTokenizer"


def test_choose_padding_accounts_for_the_request_offset():
    """The residue the server bills is the whole PROMPT's, not the text's alone.

    Measured defect this pins: aiming the text at residue 2 with a 22-token offset
    landed the prompt on residue 24, and the control cell meant for residue 0
    landed on 22 -- both cells measured the wrong question.
    """
    stub = StubTokenizer()
    text = _words(64)                       # 64 tokens: residue 0 on its own
    offset = 22
    padding = choose_padding(
        text, DEFAULT_TARGET_RESIDUE, BLOCK_SIZE_DEFAULT, stub, offset_tokens=offset
    )
    assert padding.prompt_tokens % BLOCK_SIZE_DEFAULT == DEFAULT_TARGET_RESIDUE
    assert padding.residue_after == DEFAULT_TARGET_RESIDUE
    assert padding.residue_before == offset % BLOCK_SIZE_DEFAULT
    assert padding.as_dict()["offset_tokens"] == offset


def test_padding_is_visible_and_semantically_inert():
    stub = StubTokenizer()
    base = _words(10)
    padding = choose_padding(base, 2, BLOCK_SIZE_DEFAULT, stub)

    # visible: the artefact is the base plus exactly the padding, nothing else
    assert padding.text == base + padding.padding
    assert padding.padding == NEUTRAL_TOKEN * padding.padding_tokens
    assert padding.padding_tokens > 0
    assert set(padding.padding.split()) == {"the"}          # inert filler only
    assert padding.applied is True

    row = padding.as_dict()
    assert row["padding"] == padding.padding
    assert row["padding_tokens"] == padding.padding_tokens
    assert row["applied"] is True
    assert row["residue_after"] == 2
    assert json.dumps(row, sort_keys=True)                  # the row is serialisable


def test_zero_padding_is_reported_as_zero_not_hidden():
    stub = StubTokenizer()
    padding = choose_padding(_words(2), 2, BLOCK_SIZE_DEFAULT, stub)
    assert padding.padding_tokens == 0
    assert padding.padding == ""
    assert padding.applied is False
    assert padding.as_dict()["applied"] is False


def test_choose_padding_refuses_bad_geometry():
    stub = StubTokenizer()
    with pytest.raises(PtrAnnotationError):
        choose_padding(_words(4), 64, 64, stub)             # residue >= B
    with pytest.raises(PtrAnnotationError):
        choose_padding(_words(4), 2, 0, stub)               # block size 0
    with pytest.raises(PtrAnnotationError):
        choose_padding(_words(4), 2, 64, None)              # no tokenizer
    with pytest.raises(PtrAnnotationError):
        choose_padding(1234, 2, 64, stub)                   # type: ignore[arg-type]


def test_choose_padding_is_byte_identical_in_another_process():
    base = _words(37)
    local = choose_padding(base, 2, BLOCK_SIZE_DEFAULT, StubTokenizer())
    local_digest = hashlib.sha256(local.text.encode()).hexdigest()
    program = (
        "import hashlib, sys;"
        f"sys.path.insert(0, {str(ENGINE_ROOT)!r});"
        "from ptr_engine.quantise import StubTokenizer, choose_padding;"
        f"p = choose_padding({base!r}, 2, 64, StubTokenizer());"
        "print(hashlib.sha256(p.text.encode()).hexdigest(), p.padding_tokens, p.residue_after)"
    )
    out = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=True
    ).stdout.split()
    assert out[0] == local_digest
    assert int(out[1]) == local.padding_tokens
    assert int(out[2]) == local.residue_after


# -------------------------------------------------------------- predict_billed
@pytest.mark.parametrize(
    "residue,expected,avalanche",
    [
        (0, 8013, True),     # 8000 mod 64 == 0 -> whole prefix re-billed
        (1, 8014, True),
        (2, 15, False),      # 2 + 13
        (63, 76, False),     # 63 + 13
    ],
)
def test_prediction_matches_the_law_at_residues_0_1_2_63(residue, expected, avalanche):
    P1 = 8000 + residue
    assert P1 % 64 == residue
    assert predict_billed(P1, 13, 64) == (expected, avalanche)


def test_the_law_is_a_tail_plus_payload_except_at_the_avalanche():
    assert AVALANCHE_RESIDUES == frozenset({0, 1})
    for P1 in range(8000, 8000 + 64):
        uncached, avalanche = predict_billed(P1, 13, 64)
        residue = P1 % 64
        if residue in AVALANCHE_RESIDUES:
            assert (uncached, avalanche) == (P1 + 13, True)
        else:
            assert (uncached, avalanche) == (residue + 13, False)


def test_predict_billed_refuses_a_bad_argument():
    with pytest.raises(PtrAnnotationError):
        predict_billed(-1, 13, 64)
    with pytest.raises(PtrAnnotationError):
        predict_billed(8000, 13, 0)


# ------------------------------------------------------------------ cycle_bill
def test_cycle_bill_says_padding_pays_only_when_it_dodges_or_the_residue_is_large():
    avalanche = cycle_bill(8000, 13, 64)
    assert avalanche["avalanche_without_padding"] is True
    assert avalanche["pays"] is True
    assert avalanche["breakeven_turns"] == 0            # pays on the first append
    assert avalanche["padding_tokens"] == 2

    large = cycle_bill(8063, 13, 64)                    # residue 63: pad 3, save 61
    assert large["padding_tokens"] == 3
    assert large["pays"] is True
    assert large["delta"] == 3 - 61

    small_legal = cycle_bill(8006, 13, 64)              # residue 6: pad 60, save 4
    assert small_legal["padding_tokens"] == 60
    assert small_legal["pays"] is False
    assert small_legal["delta"] == 56
    assert small_legal["breakeven_turns"] == 15         # ceil(60 / 4) warm turns


# --------------------------------------------------------------- compact_index
def test_compact_index_cuts_bytes_without_losing_resolution(index, ledger):
    compact = compact_index(index.index_text)
    assert compact.entries == len(index.lines) == 12
    assert compact.bytes_len < index.index_size
    assert compact.per_line < index.index_size / len(index.lines)
    assert compact.revision == index.revision
    assert compact.ratio(30_000) > 30_000 / index.index_size

    scope = Scope(name=index.scope, index=index, max_refs=16)
    lines = compact.text.splitlines()
    assert len(lines) == 1 + len(index.lines)
    by_text = {entry.text: entry for entry in index.entries.values()}
    for line, entry in zip(lines[1:], index._sorted()):
        text, digest, size = line.split()
        assert len(digest) == COMPACT_HASH_CHARS
        assert entry.target.digest.startswith(digest)     # same bytes, shorter handle
        assert int(size) == entry.size
        assert text not in by_text or entry.text.startswith(text)  # revision dropped
        ref = parse(text)
        assert ref.revision is None
        target = resolve(ref, scope, ledger)              # re-pinned from the header
        assert target.hash == entry.target.hash           # nothing lost


def test_compact_index_refuses_what_it_cannot_account_for():
    with pytest.raises(PtrAnnotationError):
        compact_index("")
    with pytest.raises(PtrAnnotationError):
        compact_index("ptr-index/1 scope=s revision=1 block_size=64 entries=2\n@knowledge:a@1 deadbeef 3\n")
    with pytest.raises(PtrAnnotationError):
        compact_index("not an index header\n")
    with pytest.raises(PtrAnnotationError):
        compact_index(
            "ptr-index/1 scope=s revision=1 block_size=64 entries=1\n- @knowledge:a@1 deadbeef\n"
        )


def test_the_quantise_module_carries_no_clock_and_no_randomness():
    source = (ENGINE_ROOT / "ptr_engine" / "quantise.py").read_text(encoding="utf-8")
    for forbidden in ("import random", "from random", "import time", "from time",
                      "import datetime", "uuid"):
        assert forbidden not in source, forbidden


# ==================================================================== shape search
# ENGINE-R2. The search must PREFER a free shape over a padded one, must NEVER
# return a shape on residue 0 or 1, and when no free variant can reach a cheap
# residue it must pad -- and say so. Every number here is a PREDICTION from the law.

from ptr_engine.quantise import (  # noqa: E402
    PAD_FOR_FREE_RESIDUE,
    ShapeVariant,
    calibration_limits,
    choose_shape,
    projection_variant,
    quick_bill,
)


def _variant(name: str, tokens: int, **kwargs) -> ShapeVariant:
    """A variant the ``StubTokenizer`` counts as exactly ``tokens`` whitespace words."""
    return ShapeVariant(name=name, text=_words(tokens), **kwargs)


def test_quick_bill_is_the_law_restated_and_reproduces_the_four_measured_cells():
    """PREDICTED numbers; the four inputs are ENGINE-R1's MEASURED P1 values."""
    assert quick_bill(325, 13) == 343          # cell A, residue 5
    assert quick_bill(386, 13) == 401          # cell B, residue 2 (60 filler tokens)
    assert quick_bill(384, 13) == 781          # cell C, residue 0 -> avalanche
    assert quick_bill(322, 13) == 337          # cell D, residue 2
    assert quick_bill(272, 13) == 301          # cell D unpadded, residue 16


def test_shape_search_prefers_a_free_variant_over_a_padded_one():
    """A cut at residue 33 beats paying filler, and the free row is chosen with no filler.

    Padding raises P1 by the filler and lowers the tail by (residue - 2): with the
    target at 2 and B = 64 it wins only when the filler is under half the residue,
    i.e. residue >= 35. So plant the free variant at the boundary -- residue 33, where
    the filler is 33 and the tail 31, the last residue at which padding does not pay
    -- and give it a rival at residue 7 that would need 59 filler to save 5. The
    search must take the cut and pad nothing.
    """
    stub = StubTokenizer()
    choice = choose_shape(
        [_variant("full", 71), _variant("compact", 33, index_form="compact")],
        target_residue=2, B=64, tokenizer=stub, L=13,
    )
    assert choice.chosen.variant == "compact", choice.table()
    assert choice.chosen.padding_tokens == 0
    assert choice.padded is False
    assert choice.chosen.residue == 33                 # legal, and free
    assert choice.chosen.cycle_bill == quick_bill(33, 13) == 79
    padded = [c for c in choice.candidates if c.padding_tokens > 0]
    assert padded, choice.table()                      # the padded route was considered


def test_the_search_does_not_chase_residue_two_when_padding_cannot_pay():
    """Padding costs filler ONCE and saves tail PER APPEND: 8 filler buys 56 tokens.

    A free variant at residue 58 is merely legal, and 8 inert tokens take it to 2 for
    a predicted saving of 36 -- so the search DOES pad, and that is the law speaking,
    not a preference for residue 2. Push the residue down to where the tail is shorter
    than the filler (residue 5: 61 filler for 3 of tail) and it must leave it alone.
    """
    stub = StubTokenizer()
    cheap = choose_shape([_variant("full", 58)], 2, 64, stub, L=13)
    assert cheap.padded is True
    assert cheap.chosen.padding_tokens == 8
    assert cheap.chosen.padding_tokens == (2 - 58) % 64
    assert cheap.chosen.cycle_bill < quick_bill(58, 13)

    leave = choose_shape([_variant("full", 5)], 2, 64, stub, L=13)
    assert leave.padded is False, leave.table()
    assert leave.chosen.residue == 5
    assert "NO PADDING" in leave.padding_reason


@pytest.mark.parametrize("base_tokens", [0, 1, 64, 65, 128, 129])
def test_shape_search_never_returns_a_shape_on_the_avalanche(base_tokens):
    """Residue 0 or 1 on the reference: the search must leave it, whatever it costs."""
    stub = StubTokenizer()
    variants = [
        _variant("full", base_tokens),
        _variant("compact", base_tokens + 1, index_form="compact"),
    ]
    choice = choose_shape(variants, target_residue=2, B=64, tokenizer=stub, L=13)
    assert choice.residue not in AVALANCHE_RESIDUES, choice.table()
    assert choice.chosen.avalanche is False
    assert choice.avalanche_avoided is True


def test_a_free_variant_that_escapes_the_avalanche_is_preferred_to_padding():
    """When cutting alone gets off residue 0, no filler is spent at all."""
    stub = StubTokenizer()
    choice = choose_shape(
        [_variant("full", 64), _variant("compact", 2, index_form="compact")],
        target_residue=2, B=64, tokenizer=stub, L=13,
    )
    assert choice.residue == 2
    assert choice.padded is False
    assert choice.avalanche_avoided is True
    assert choice.chosen.cycle_bill == quick_bill(2, 13) == 17


def test_avalanche_is_dodged_and_the_reason_says_padded():
    """Residue 0 on the only variant: padding is FORCED, and it is reported."""
    stub = StubTokenizer()
    choice = choose_shape([_variant("full", 64)], target_residue=2, B=64, tokenizer=stub, L=13)
    assert choice.padded is True
    assert choice.avalanche_avoided is True
    assert choice.chosen.padding_tokens == 2
    assert choice.residue == 2
    assert choice.chosen.cycle_bill == quick_bill(66, 13)
    assert choice.chosen.cycle_bill < quick_bill(64, 13)
    assert "PADDED" in choice.padding_reason


def test_residue_one_is_dodged_too_and_the_cost_is_named():
    stub = StubTokenizer()
    choice = choose_shape([_variant("full", 65)], target_residue=2, B=64, tokenizer=stub, L=13)
    assert choice.residue == 2
    assert choice.chosen.padding_tokens == 1
    assert choice.padded is True
    assert (
        choice.candidates[0].cycle_bill < next(
            c for c in choice.candidates if c.padding_tokens == 0
        ).cycle_bill
    )


def test_no_free_variant_reaches_a_cheap_residue_so_it_pads_and_says_so():
    """The planted corpus: every candidate is far from any cheap residue.

    All three variants sit at small legal residues (36, 40, 44 mod 64) -- the band
    where filler costs more per token than the tail it saves -- and the padding cap is
    0, i.e. the host has no filler to spend. Nothing can reach a cheap residue, so the
    search must stay off the avalanche, return the cheapest legal row, pad nothing,
    and SAY that no free variant reached a cheap residue.
    """
    stub = StubTokenizer()
    choice = choose_shape(
        [
            _variant("full", 36),
            _variant("compact", 40, index_form="compact"),
            _variant("projection", 44, index_form="compact", cuts=("digest shortened",)),
        ],
        target_residue=2, B=64, tokenizer=stub, L=13, max_pad=0,
    )
    assert choice.padded is False
    assert all(c.padding_tokens == 0 for c in choice.candidates), choice.table()
    assert choice.chosen.variant == "full"           # 36 + 36 + 13 is the cheap row
    assert choice.residue == 36
    assert choice.chosen.residue not in AVALANCHE_RESIDUES
    assert "NO PADDING" in choice.padding_reason
    assert "did not reach" in choice.padding_reason or "cheap residue" in choice.padding_reason


def test_the_fallback_to_padding_is_visible_when_the_cap_bites():
    """With the cap lifted the same corpus pads -- and reports the residue it reached."""
    stub = StubTokenizer()
    choice = choose_shape(
        [_variant("full", 36), _variant("compact", 40, index_form="compact")],
        target_residue=2, B=64, tokenizer=stub, L=13,
    )
    assert choice.padded is True
    assert "PADDED" in choice.padding_reason
    assert choice.chosen.padding_tokens == 26        # compact 40 -> 2
    assert choice.chosen.cycle_bill == quick_bill(66, 13)
    assert choice.chosen.cycle_bill < quick_bill(36, 13)   # the unpadded reference: 85


def test_choose_shape_refuses_what_it_cannot_reason_about():
    stub = StubTokenizer()
    with pytest.raises(PtrAnnotationError):
        choose_shape([], 2, 64, stub)
    with pytest.raises(PtrAnnotationError):
        choose_shape([_variant("a", 5), _variant("a", 6)], 2, 64, stub)
    with pytest.raises(PtrAnnotationError):
        choose_shape([_variant("a", 5)], 2, 64, stub, reference="missing")
    with pytest.raises(PtrAnnotationError):
        choose_shape([_variant("a", 5)], 64, 64, stub)          # target out of range
    with pytest.raises(PtrAnnotationError):
        choose_shape([_variant("a", 5)], 2, 0, stub)            # block size
    with pytest.raises(PtrAnnotationError):
        choose_shape([_variant("a", 5)], 2, 64, stub, L=-1)


def test_the_choice_is_deterministic_and_marks_itself_predicted():
    stub = StubTokenizer()
    variants = [_variant("full", 40), _variant("compact", 40, index_form="compact")]
    first = choose_shape(variants, 2, 64, stub, L=13)
    second = choose_shape(variants, 2, 64, stub, L=13)
    assert first.as_dict() == second.as_dict()
    assert first.predicted is True
    assert "law" in first.basis
    assert calibration_limits(13) == (
        "PREDICTED, not measured: this unit sent no request",
        "the per-placeholder token cost is a hypothesis; the engine has no real tokenizer offline",
        "a short append's cost tracks the template framing, not the prompt's length, so L does not scale with the prompt",
    )
    assert any("L=40" in line for line in calibration_limits(40))


def test_projection_variant_names_the_capability_it_loses():
    index = (
        "ptr-index/1 scope=s revision=1 block_size=64 entries=2\n"
        "- @knowledge:a@1 deadbeef 100\n"
        "- @memory:b@1 cafebabe 200\n"
    )
    variant = projection_variant(index)
    assert variant.text.splitlines()[0].startswith("ptr-index/1")   # header kept
    assert "@knowledge:a@1 d" in variant.text         # first hex char survives
    assert "deadbeef" not in variant.text
    assert "@memory:b@1 c" in variant.text
    assert variant.cuts and "verifiable handle" in variant.cuts[0]
    assert len(variant.text) == len(index)            # a real byte count, no deletion
    with pytest.raises(PtrAnnotationError):
        projection_variant("")


def test_the_choice_never_reads_a_clock_or_a_random_source():
    """The shape search is as pure as the rest of the module."""
    source = (ENGINE_ROOT / "ptr_engine" / "quantise.py").read_text(encoding="utf-8")
    assert "urllib.request.urlopen" in source          # only inside ServerTokenizer
    assert source.count("urllib.request.urlopen") == 1
    for forbidden in ("import random", "import time", "datetime", "uuid"):
        assert forbidden not in source, forbidden
