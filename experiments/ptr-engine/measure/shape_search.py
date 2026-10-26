#!/usr/bin/env python3
"""The shape search over the 12-item corpus. OFFLINE. Every number PREDICTED.

    python3 experiments/ptr-engine/measure/shape_search.py

This unit has no measurement budget -- ``:8012`` and ``:8014`` belong to other
units -- so **not one request is sent**. What is computed here is what
:func:`ptr_engine.quantise.choose_shape` predicts from the law in
``experiments/miss-law/LAW.md``, given token counts obtained offline:

* the tokenizer stub is **calibrated against the two anchors ENGINE-R1 measured**
  (``measure/RESULTS.md`` section 1): the full index is ``P1 = 325`` at residue 5,
  and the compact index is ``P1 = 322`` at residue 16 after 50 filler tokens. The
  reuse of a *measured* number as a calibration constant is stated, with its
  residual, in ``measure/SHAPE-SEARCH.md`` -- it is not a fabricated reading;
* every bill is ``P1 + (P1 mod B) + L`` with the avalanche at ``{0, 1}``.

The module is imported, never copied: if ``choose_shape`` changes, this table changes.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))
sys.path.insert(0, str(ENGINE_ROOT / "examples"))

from ptr_engine import BodyStore, Ledger, compile_turn  # noqa: E402
from ptr_engine.adapter import build_prompt  # noqa: E402
from ptr_engine.quantise import (  # noqa: E402
    BLOCK_SIZE_DEFAULT,
    COMPACT_MAGIC,
    ShapeVariant,
    choose_shape,
    compact_index,
    projection_variant,
)

BLOCK = BLOCK_SIZE_DEFAULT
L_MEASURED = 13          # ENGINE-R1: one payload token + 12 framing tokens
PAD_A = 324              # m: ENGINE-R1 cell A is base + m = 325
PAD_B = 322 + 15 - 12    # ENGINE-R1 cell D: 322 = compact base + 50 + remainder
PAD_C = 272 + 15 - 12    # the brief's compact anchor, 322 = 272 + 50
PAIR_WEIGHT = 1.0        # a payload byte and a hex byte are one token pair
FULL_BODY_TOKENS = 54    # ENGINE-R1's 312-word body -> 264 token estimate, x1.25


class AnchorTokenizer:
    """Deterministic offline counter, calibrated on ENGINE-R1's two measured anchors.

    The model is deliberately small and wrong in ways that are stated, not hidden:

        tokens(text) = ceil((words + PAIR_WEIGHT * bytes) / 2) + PAD_A

    ``words`` stands in for the tokenizer's whole-word merges and ``bytes`` for its
    sub-word splits; with ``PAIR_WEIGHT = 1`` the two are summed as if every byte
    were a token and every word its own token, and the sum is halved. ``PAD_A`` is
    the constant that makes the full index land on ENGINE-R1's measured ``P1 = 325``.

    ``conflicts`` reports the anchors this model cannot meet, so a reader never has
    to take the fit on trust.
    """

    def __init__(
        self,
        pad_a: int = PAD_A,
        pad_b: int = PAD_B,
        pad_c: int = PAD_C,
        weight: float = PAIR_WEIGHT,
    ) -> None:
        self.pad_a = pad_a
        self.pad_b = pad_b
        self.pad_c = pad_c
        self.weight = weight

    def raw(self, text: str) -> int:
        words = len(text.split())
        return -(-int(words + self.weight * len(text.encode("utf-8"))) // 2)

    def count(self, text: str) -> int:
        return self.raw(text) + self.pad_a

    def conflicts(self, full_index: str, compact_text: str, pad_tokens: int) -> list[str]:
        """Which of the three ENGINE-R1 / brief anchors this calibration breaks."""
        seen: list[str] = []
        if (self.raw(full_index) + self.pad_a) % BLOCK != 5:
            seen.append("full index is not at residue 5")
        if (self.raw(full_index + " the") - self.raw(full_index)) != 1:
            seen.append("one filler token is not one token")
        if (self.raw(compact_text) + self.pad_b) % BLOCK != 16:
            seen.append("cell-D compact anchor is not at residue 16")
        if (self.raw(compact_text) + self.pad_c) % BLOCK != 16:
            seen.append("brief compact anchor (322) is not at residue 16")
        return seen


class WordTokenizer:
    """Plain one-token-per-word counter: the engine's own ``StubTokenizer`` model.

    It is reported beside the calibrated counter because it is the model the test
    suite uses, and seeing both is how a reader judges how much the table depends on
    the calibration.
    """

    def count(self, text: str) -> int:
        return len(text.split())


def corpus_indexes():
    """The compiled full index, its compact form, and the envelope around each."""
    import worked_example as we  # noqa: PLC0415 -- examples/ is on sys.path above

    warmpool = Path(tempfile.mkdtemp(prefix="ptr-shape-search-"))
    try:
        store = BodyStore(warmpool)
        ledger = Ledger(warmpool / "ledger.jsonl", block_size=BLOCK)
        index = compile_turn(
            we.corpus(), revision=1, scope="worked-example", block_size=BLOCK, store=store
        )
        full = build_prompt(index, {}, ledger)          # <ptr-index> ... </ptr-index>
        compact = compact_index(index.index_text).text  # header + lines, no tags
        # wrap the compact body in the same envelope so both variants are comparable
        compact_envelope = "<ptr-index>\n" + compact + "</ptr-index>\n"
        return {
            "full": full,
            "compact": compact_envelope,
            "full_body": index.index_text,
            "compact_body": compact,
            "index_bytes_full": index.index_size,
            "index_bytes_compact": len(compact.encode("utf-8")),
        }
    finally:
        shutil.rmtree(warmpool, ignore_errors=True)


def variants_for(texts):
    """The candidate shapes, each with an honest note about what it costs."""
    return [
        ShapeVariant(
            name="full",
            text=texts["full"],
            index_form="full",
            note="the index as compile_turn writes it",
            payload_tokens=0,
        ),
        ShapeVariant(
            name="compact",
            text=texts["compact"],
            index_form="compact",
            note="bullet, per-line revision and 8->6 digest hex chars dropped (ENGINE-R1 cell D)",
            payload_tokens=0,
        ),
        ShapeVariant(
            name="compact+cut-projection",
            text=projection_variant(texts["compact"], name="compact+cut-projection").text,
            index_form="compact",
            cuts=projection_variant(texts["compact"]).cuts,
            note="LOSES the stale-line / echo check: a named capability, not a free win",
            payload_tokens=0,
        ),
    ]


class MainTextWithDTokenizer:
    """The one hypothesis that meets BOTH main-text anchors for free.

    Body tokens are one per whitespace word, plus ``D = 4`` tokens for the chat
    template and the user message (ENGINE-R1's whole-prompt estimate was 324, i.e. 55
    body (312 words -> 264 tokens, x1.25) + 1 payload + 12 framing + 264 - 264... in
    short: an additive constant). ``D`` is then solved so that the compact body
    reproduces ENGINE-R1's measured cell-D ``P1 = 272``. It is a HYPOTHESIS
    calibrated on two measured points, not a tokenizer: it counts nothing the server
    would count.
    """

    def count(self, text: str) -> int:
        return len(text.split()) + self.constant

    @classmethod
    def fitted(cls, compact_body: str, target_P1: int = 272) -> "MainTextWithDTokenizer":
        instance = cls()
        instance.constant = target_P1 - len(compact_body.split())
        return instance

    constant: int = 0


def stub_scaling(tokenizer, texts, target=2):
    """Does a stub tokenizer need ``L`` rescaled to ``L * mean(text)/mean(anchor text)``?

    ENGINE-R1 measured ``L = 13`` with a 325-token anchor prompt. A stub whose
    per-byte rate differs from the real tokenizer's would move the append cost if the
    append payload were rewritten the same way -- so the honest factor is
    ``L * base(text) / base(anchor)``, and it is reported, not applied silently.
    """
    compact = texts["compact"]
    anchor = tokenizer.count(compact) + (322 - tokenizer.count(compact) - 50) % BLOCK
    base = tokenizer.count(compact)
    return {
        "stub_anchor_P1": anchor,
        "stub_base_P1": base,
        "l_factor": L_MEASURED * base / anchor,
        "note": (
            "L re-scaling in the real tokenizer: an append's cost is a prompt DELTA, "
            "and the real prompt is ~5x longer than this stub models, so L=13 would "
            "average ~66 under uniform scaling -- uniform scaling is demonstrably "
            "wrong (the real encoder pays 13 for 4 extra bytes where this stub pays x)"
        ),
    }


def run():
    texts = corpus_indexes()
    variants = variants_for(texts)
    output = {"predicted": True, "block_size": BLOCK, "L_measured": L_MEASURED, "runs": []}

    main_text = MainTextWithDTokenizer.fitted(texts["compact_body"], 272)
    for label, tokenizer in (
        ("calibrated-anchor", AnchorTokenizer()),
        ("words-only", WordTokenizer()),
        ("main-text-with-D", MainTextWithDTokenizer()),
    ):
        choice = choose_shape(
            variants, target_residue=2, B=BLOCK, tokenizer=tokenizer, L=L_MEASURED,
            payload_tokens=0, reference="full",
        )
        scaling = stub_scaling(tokenizer, texts)
        record = {
            "tokenizer": label,
            "table": choice.table(),
            "chosen": choice.chosen.as_dict(),
            "padded": choice.padded,
            "padding_reason": choice.padding_reason,
            "avalanche_avoided": choice.avalanche_avoided,
            "candidates": [c.as_dict() for c in choice.candidates],
            "l_scaling": scaling,
        }
        if isinstance(tokenizer, AnchorTokenizer):
            body = texts["full_body"]
            record["conflicts"] = tokenizer.conflicts(body, body and texts["compact_body"], PAD_C)
            facts = {
                "stub_tokens_full_body": tokenizer.count(body),
                "stub_tokens_compact_body": tokenizer.count(texts["compact_body"]),
                "stub_tokens_full_plus_1_filler": tokenizer.count(body + " the"),
                "stub_residue_full_body": tokenizer.count(body) % BLOCK,
                "stub_compact_plus_50_filler_residue": (
                    tokenizer.count(texts["compact_body"] + " the" * 50) % BLOCK
                ),
            }
            record["stub_facts"] = facts
        output["runs"].append(record)
    output["envelope_bytes"] = {
        "full": len(texts["full"].encode("utf-8")),
        "compact": len(texts["compact"].encode("utf-8")),
    }
    output["index_bytes"] = {
        "full": texts["index_bytes_full"],
        "compact": texts["index_bytes_compact"],
    }
    return output


def main() -> int:
    result = run()
    here = Path(__file__).resolve().parent
    (here / "shape-search.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print("PREDICTED — no request was sent; every number below comes from the law.")
    for run_record in result["runs"]:
        print()
        print(f"== tokenizer: {run_record['tokenizer']} ==")
        print(run_record["table"])
        print()
        print(f"padded: {run_record['padded']}")
        print(f"reason: {run_record['padding_reason']}")
        scaling = run_record["l_scaling"]
        print(
            f"stub proportional L: anchor P1={scaling['stub_anchor_P1']} "
            f"base={scaling['stub_base_P1']} -> L x{scaling['l_factor']:.2f} "
            "(NOT used: the append cost is a prompt delta, not a per-byte rate)"
        )
        if "conflicts" in run_record:
            print(f"anchors this calibration breaks: {run_record['conflicts']}")
            print(f"its own offline counts: {run_record['stub_facts']}")
    print()
    print(f"index bytes: {result['index_bytes']}")
    print(f"envelope bytes: {result['envelope_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
