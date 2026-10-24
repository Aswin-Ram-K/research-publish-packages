#!/usr/bin/env python3
"""U9 deterministic filler corpus.

U9 needs *lengths*, not content: a prompt of ~L tokens whose bytes are stable
within a length (so every rep of that length sends the same body) and different
across lengths (so a 4k rep can never prefix-match an 8k body by accident).

Determinism contract (same discipline as U4's corpus):

* no wall clock, no ``os.urandom``, no ``random`` module, no dict-order
  dependence, no filesystem-order dependence;
* all variation comes from :class:`Lcg`, a 64-bit LCG seeded from a constant,
  so ``filler(n_chars)`` is a pure function and identical on every Python
  version;
* the vocabulary is plain lowercase ASCII words with no apostrophes, hyphens
  or digits, so the chars-per-token ratio does not drift with content.

Why words rather than lorem ipsum or repeated paragraphs: a repeated paragraph
would tokenise in a length-dependent way (BPE merges reinforce themselves), and
the whole point of the length sweep is a *stable* mapping from characters to
tokens that can be calibrated once and then extrapolated to 32k.

Usage::

    python3 u9_corpus.py            # self-check: sizes + digests
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent

#: Target prompt lengths (tokens).  32k may be dropped to 16k if too slow.
LENGTHS = (1024, 2048, 4096, 8192, 16384, 32768)

#: 128 plain words.  Lengths deliberately vary 2..10 chars.
VOCAB = (
    "the of and a to in is that for it with as was on be at by this had not "
    "are but from or have an they which one you were her all she there would "
    "their we him been has when who will more no if out so said what up its "
    "about into than them can only other new some could time these two may "
    "then do first any my now such like our over man me even most made after "
    "also did many before must through back years where much your way well "
    "down should because each just those people mr how too little state good "
    "very make world still own see men work long get here between both life "
    "being under never day same another know while last might us great old "
    "year off come since against go came right used take three states himself "
    "few house use during without again place around however home small found "
    "thought went say part once general high upon school every dont does".split()
)

#: Sentences are 6..17 words; separators keep the stream free of long repeats.
SEP_PLAIN = " "
SEP_COMMA = ", "
SEP_STOP = ". "


class Lcg:
    """64-bit linear congruential generator; identical on every Python."""

    A = 6364136223846793005
    C = 1442695040888963407
    M = 1 << 64

    def __init__(self, seed: int) -> None:
        self.state = (seed ^ 0x9E3779B97F4A7C15) & (self.M - 1)

    def next_u64(self) -> int:
        self.state = (self.A * self.state + self.C) & (self.M - 1)
        return self.state

    def below(self, n: int) -> int:
        """Uniform-ish integer in ``[0, n)``."""

        if n <= 0:
            raise ValueError("n must be positive")
        return self.next_u64() % n


def filler(n_chars: int, *, seed: int = 0) -> str:
    """Deterministic word stream of at least ``n_chars`` characters.

    Truncated at a word boundary so no partial word reaches the tokenizer.
    """

    if n_chars < 1:
        raise ValueError("n_chars must be positive")
    rng = Lcg(seed)
    parts: list[str] = []
    size = 0
    sentence_left = 6 + rng.below(12)
    capitalize = True
    while size < n_chars:
        word = VOCAB[rng.below(len(VOCAB))]
        if capitalize:
            word = word[0].upper() + word[1:]
            capitalize = False
        parts.append(word)
        size += len(word)
        sentence_left -= 1
        if sentence_left <= 0:
            parts.append(".")
            size += 1
            sentence_left = 6 + rng.below(12)
            capitalize = True
        elif rng.below(9) == 0:
            parts.append(",")
            size += 1
        parts.append(" ")
        size += 1
    text = "".join(parts).strip()
    # trim to a word boundary at or just past n_chars
    if len(text) > n_chars:
        cut = text.rfind(" ", 0, n_chars + 1)
        if cut > 0:
            text = text[:cut]
    return text


def body_for(n_chars: int) -> str:
    """The canonical body for a character budget (one seed, so it is stable)."""

    return filler(n_chars, seed=20261020)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    print(f"vocab={len(VOCAB)}")
    for target in LENGTHS:
        # ~3.6 chars/token is the calibration guess; the ratio is measured live
        chars = int(target * 3.6)
        text = body_for(chars)
        print(
            f"target_tokens~{target:6d} chars={len(text):7d} "
            f"sha256={digest(text)[:16]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
