#!/usr/bin/env python3
"""U10 deterministic corpus: varied word stream + a fixed-width cold marker.

U10 must hit an *exact* prompt length, because the whole question is whether
the first-repeat miss depends on ``L % 64 == 0``.  U9's calibrated-char-count
approach cannot do that: its 16-hex-char salt tokenises to a variable number of
tokens (U9's own logs show declared target 1024 landing on
{1021, 1022, 1023, 1024, 1025} across 43 requests at the same char count), and
a +/-2 token jitter is fatal at a 64-token boundary.

So the cold-isolation marker here is built to have a **constant token cost**:

    "<marker> = 'cell W0 W1 W2 '"   -- three 4-letter words, always 20 chars

All marker words are drawn from :data:`MARKER_WORDS`, a list of common
four-letter lowercase English words (one token each in Qwen-style BPE, with or
without a leading space).  Because every word has the same length and the same
shape, the marker's character count *and* token count are constant, so

    tokens(marker + body(C)) = MARKER_TOKENS + tokens(body(C))

depends only on ``C``.  That is what makes an exact ``prompt_tokens`` target
reachable with one or two calibration probes, and every achieved length is
still read back from the response and recorded.

Cold isolation is unchanged in kind from every other cell: each trial gets its
own **never-reused** marker, deterministically derived from
``salt.make_salt(seed)`` (its first six hex digits select the three words), so
the radix prefix match is 0 by construction and no trial can inherit another
trial's cache.  ``make_salt`` is therefore still the salt generator; only its
*encoding* into the prompt is token-stable.

Determinism: no clock, no ``os.urandom``, no ``random`` module, no dict-order
or filesystem-order dependence.

Usage::

    python3 u10_corpus.py      # self-check: marker widths, prompt char counts
"""

from __future__ import annotations

import hashlib

#: Marker words: 4 letters each, common, lowercase -> one token each.
MARKER_WORDS = (
    "able also area army away baby back bank base body book both call came "
    "care case city come cost dark data date dead deal deep done door down "
    "draw drop each east easy else even ever fact fall farm fast fear feel "
    "fell felt file find fire firm fish five food foot form four free full "
    "fund game gave girl give goes gold gone good grew grow half hall hand "
    "hard harm head hear heat held help here high hold home hope hour huge "
    "idea inch into iron item join just keep kept kind king knew know lack "
    "lady land last late lead left less life like line list live long look "
    "lose loss lost love made main make many mark mass mean meet menu mile "
    "mind mine miss mode more most move much must name near need news next "
    "nice none nose note noun okay once only open oral over page pair park "
    "part past path pick plan play plot plus poem poet pool poor port post "
    "pull pure push race rain rank rare rate read real rear rely rent rest "
    "rice rich ride ring rise risk road rock role roof room root rule safe "
    "said sale same save seat seed seek seem seen self sell send sent ship "
    "shop shot show shut side sign site size skin slip slow snow soft sold "
    "sole some song soon sort soul spot star stay step stop such sure take "
    "talk tall task team tell tend term test than that them then they thin "
    "this thus time tiny told tone took tool tour town tree trip true turn "
    "type unit upon used user vary vast very view vote wait walk wall want "
    "warm wash wave ways wear week well went were west what whom wide wife "
    "wild will wind wine wing wire wise wish with wood word wore work yard "
    "yeah year your zero zone"
).split()

#: Marker shape: "cell " + W0 + " " + W1 + " " + W2 + " " == 20 characters.
MARKER_PREFIX = "cell "
MARKER_CHARS = 20
#: Constant token cost of the marker (verified live: achieved length is a
#: singleton per calibrated char count -- see ``u10_report.json``).
MARKER_TOKENS = 5

#: Varied-sentence body vocabulary (128 plain words, 2..10 chars).
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


class Lcg:
    """64-bit LCG; identical on every Python (no ``random`` module)."""

    A = 6364136223846793005
    C = 1442695040888963407
    M = 1 << 64

    def __init__(self, seed: int) -> None:
        self.state = (seed ^ 0x9E3779B97F4A7C15) & (self.M - 1)

    def next_u64(self) -> int:
        self.state = (self.A * self.state + self.C) & (self.M - 1)
        return self.state

    def below(self, n: int) -> int:
        if n <= 0:
            raise ValueError("n must be positive")
        return self.next_u64() % n


def filler(n_chars: int, *, seed: int = 0) -> str:
    """Deterministic varied-sentence word stream of about ``n_chars`` chars.

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
    if len(text) > n_chars:
        cut = text.rfind(" ", 0, n_chars + 1)
        if cut > 0:
            text = text[:cut]
    return text


def body_for(n_chars: int, variant: int = 0) -> str:
    """Varied-sentence body for a character budget (stable bytes per variant).

    ``variant`` exists because chars->tokens is a staircase: a one-character
    step can jump the token count by two (the body is truncated at a word
    boundary), and for some targets no char count in one word stream lands on
    the wanted token count.  A second, still deterministic stream changes the
    staircase's phase without changing anything else about the experiment.
    """

    if variant < 0:
        raise ValueError("variant must be >= 0")
    return filler(n_chars, seed=20261021 + 7919 * variant)


def marker_for(salt_hex: str) -> str:
    """Fixed-width marker from a 16-hex salt: three word indices from its digits."""

    if len(salt_hex) < 6:
        raise ValueError("salt_hex too short")
    words = [
        MARKER_WORDS[int(salt_hex[2 * i : 2 * i + 2], 16) % len(MARKER_WORDS)]
        for i in range(3)
    ]
    text = MARKER_PREFIX + " ".join(words) + " "
    if len(text) != MARKER_CHARS:  # pragma: no cover - guard, not logic
        raise AssertionError(f"marker width {len(text)} != {MARKER_CHARS}: {text!r}")
    return text


#: Fine-grained length knob: each ``" the"`` appended to the body is one token
#: in Qwen-style BPE, so any token target above the body's own count is
#: reachable.  The body alone is a staircase (it is truncated at word
#: boundaries, so a one-character step can jump two tokens); the tail removes
#: that quantisation from the experiment.
TAIL_UNIT = " the"


def prompt_text(marker: str, body_chars: int, variant: int = 0, tail: int = 0) -> str:
    if tail < 0:
        raise ValueError("tail must be >= 0")
    return marker + body_for(body_chars, variant) + TAIL_UNIT * tail


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))
    from resextract.context.salt import make_salt

    widths, lens, dupes = set(), [], 0
    seen = set()
    for seed in range(64):
        s = make_salt(10_000 + seed)
        m = marker_for(s)
        widths.add(len(m))
        if m in seen:
            dupes += 1
        seen.add(m)
        lens.append(len(prompt_text(m, 3600)))
    print(f"marker_words={len(MARKER_WORDS)} widths={sorted(widths)} dupes={dupes}")
    print(f"prompt_chars_min={min(lens)} max={max(lens)} (should be equal)")
    print(f"words_4_letters={all(len(w) == 4 for w in MARKER_WORDS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
