"""Quantisation: make the append cost a choice instead of a lottery.

Measured law (see ``experiments/miss-law/LAW.md``): on a prefix-cached server with
cache block size ``B``, appending ``L`` tokens to a primed prefix of ``P1`` tokens
re-bills

    R = (P1 mod B) + L                      # the unaligned tail plus what you appended

and there is one discontinuity worth more than the formula: **if ``P1 mod B`` is 0 or
1 the server reports no cache at all and bills the whole prefix** (``R = P1 + L``).
The engine controls ``P1`` -- it is the length of the prompt the engine itself
assembles -- so the compiled index lands wherever it lands, and a compile that happens
to fall on residue 0 or 1 pays for the entire prefix on every append.

This module is the lever. It is **pure**: no socket is opened unless a caller
explicitly constructs :class:`ServerTokenizer`, no clock is read, no randomness, and
the same input produces byte-identical output in every process.

Three functions are the contract:

    token_len(text, tokenizer)                     -> int
    choose_padding(compiled_text, target_residue, B, tokenizer) -> Padding
    predict_billed(P1, L, B)                       -> (predicted_uncached, avalanche)

plus two that exist because a measurement needed them: :func:`cycle_bill` (does
padding pay for *this* P1?) and :func:`compact_index` (fewer bytes per index line
without losing resolution).

Honesty note, measured by ``experiments/ptr-engine/measure/RESULTS.md``: padding to
residue 2 is not free. It pays enormously when the compile landed on 0 or 1, pays
modestly when the residue is large, and **costs tokens when the residue is small but
legal** -- because reaching residue 2 from residue ``r`` means adding ``66 - r``
tokens to save ``r - 2`` of tail. :func:`cycle_bill` is the arithmetic, and a host
that pads unconditionally is leaving tokens on the table just as surely as one that
never pads.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterator, Optional, Protocol, Sequence, Tuple

from .errors import PtrAnnotationError

#: Cache block size the law was measured at on the SGLang endpoint (``:8012``).
BLOCK_SIZE_DEFAULT = 64

#: The cheapest legal residue: a 2-token tail, and as far from an avalanche as a
#: 64-token block allows with one token of margin.
DEFAULT_TARGET_RESIDUE = 2

#: Residues at which the server reports no cache at all and bills the whole prefix.
AVALANCHE_RESIDUES = frozenset({0, 1})

#: Semantically inert filler: one token per repetition on the measured tokenizer
#: (``" the"`` -> token 279, verified by ``POST /v1/tokenize``).
NEUTRAL_TOKEN = " the"

#: Marker written into a compacted header, so a reader can tell the two forms apart.
COMPACT_MAGIC = "ptr-index/1c"

#: Hex characters of the body digest an index line shows in the compact form. The
#: line's digest is a *display* handle; the store re-hashes the full sha256 on read,
#: so shortening it cannot change which bytes a ref designates.
COMPACT_HASH_CHARS = 6


class Tokenizer(Protocol):
    """Anything that can count the tokens of a string exactly."""

    def count(self, text: str) -> int:  # pragma: no cover - protocol
        ...


def _token_count(tokenizer: Any, text: str) -> int:
    """Dispatch on a tokenizer: ``.count(text)`` or a bare ``callable(text)``."""
    if tokenizer is None:
        raise PtrAnnotationError(
            "a tokenizer is required: pass StubTokenizer() offline or "
            "ServerTokenizer(url) for the exact count the server will bill",
            tokenizer=None,
        )
    counter = getattr(tokenizer, "count", None)
    try:
        if callable(counter):
            return int(counter(text))
        if callable(tokenizer):
            return int(tokenizer(text))
    except PtrAnnotationError:
        raise
    except Exception as exc:  # network, JSON, HTTP -- reported, never swallowed
        raise PtrAnnotationError(
            f"tokenizer failed to count {len(text)} characters: {exc}",
            tokenizer=type(tokenizer).__name__,
            error=type(exc).__name__,
        ) from exc
    raise PtrAnnotationError(
        "tokenizer must be callable or expose count(text), got "
        f"{type(tokenizer).__name__}",
        tokenizer=type(tokenizer).__name__,
    )


def token_len(text: str, tokenizer: Any = None) -> int:
    """The exact token count of ``text`` under ``tokenizer``.

    Never estimates. ``ServerTokenizer`` asks the server that will bill the request
    (``POST /v1/tokenize``); ``StubTokenizer`` is the deterministic offline double
    the tests use. A missing tokenizer is an error, not a guess.
    """
    if not isinstance(text, str):
        raise PtrAnnotationError(
            f"token_len takes text, got {type(text).__name__}",
            got=type(text).__name__,
        )
    count = _token_count(tokenizer, text)
    if count < 0:
        raise PtrAnnotationError(f"tokenizer returned a negative count {count}")
    return count


@dataclass(frozen=True)
class StubTokenizer:
    """Deterministic offline tokenizer: one token per whitespace-delimited word.

    It exists so the quantiser can be tested without a server, and it is *not* a
    model of any real tokenizer -- it is deliberately simple and honest about it:
    ``" the the"`` is 2 tokens, ``""`` is 0, and the same string always counts the
    same. A caller who needs the server's number uses ``ServerTokenizer``.
    """

    def tokenize(self, text: str) -> Tuple[str, ...]:
        if not isinstance(text, str):
            raise PtrAnnotationError(
                f"StubTokenizer takes text, got {type(text).__name__}"
            )
        return tuple(text.split())

    def count(self, text: str) -> int:
        return len(self.tokenize(text))


@dataclass(frozen=True)
class ServerTokenizer:
    """The server's own token count: ``POST {base_url}/v1/tokenize``.

    Opt-in by construction. Nothing in this package constructs one, no import opens
    a socket, and every other function here works with a tokenizer the caller
    supplies -- which is what keeps ``ptr_engine`` a pure library with exactly one
    explicitly networked accessory.

        ServerTokenizer("http://192.168.2.168:8012/v1").count(" the")
    """

    base_url: str = "http://192.168.2.168:8012/v1"
    timeout: float = 60.0

    def count(self, text: str) -> int:
        if not isinstance(text, str):
            raise PtrAnnotationError(
                f"ServerTokenizer takes text, got {type(text).__name__}"
            )
        url = self.base_url.rstrip("/") + "/tokenize"
        body = json.dumps({"prompt": text, "model": "occamy-1.0"}).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise PtrAnnotationError(
                f"POST {url} failed: {exc}", url=url
            ) from exc
        for key in ("count", "value", "num_tokens"):
            if key in payload:
                return int(payload[key])
        tokens = payload.get("tokens")
        if isinstance(tokens, list):
            return len(tokens)
        raise PtrAnnotationError(
            f"POST {url} returned no token count (keys: {sorted(payload)})", url=url
        )


@dataclass(frozen=True)
class Padding:
    """A padded variant of a compiled prompt, and exactly what was added to it.

    The padding is never silent. ``text == compiled_text + padding`` byte for byte,
    ``padding_tokens`` is the added count, and ``as_dict()`` is what a measurement
    row records -- so a reader of the artefact can always see the 2-token
    intervention that moved the residue.
    """

    text: str
    padding: str
    padding_tokens: int
    target_residue: int
    block_size: int
    base_tokens: int
    padded_tokens: int
    residue_before: int
    residue_after: int
    token_source: str = "unknown"
    offset_tokens: int = 0

    @property
    def applied(self) -> bool:
        return self.padding_tokens > 0

    @property
    def prompt_tokens(self) -> int:
        """The ``P1`` this padding implies, once the caller's fixed offset is added."""
        return self.padded_tokens + self.offset_tokens

    def as_dict(self) -> dict[str, Any]:
        return {
            "padding_tokens": self.padding_tokens,
            "padding": self.padding,
            "target_residue": self.target_residue,
            "block_size": self.block_size,
            "base_tokens": self.base_tokens,
            "padded_tokens": self.padded_tokens,
            "offset_tokens": self.offset_tokens,
            "prompt_tokens": self.prompt_tokens,
            "residue_before": self.residue_before,
            "residue_after": self.residue_after,
            "applied": self.applied,
            "token_source": self.token_source,
        }

    def summary(self) -> str:
        return (
            f"B={self.block_size} residue {self.residue_before}->{self.residue_after} "
            f"pad={self.padding_tokens} token(s) ({self.base_tokens}->{self.padded_tokens})"
        )


def choose_padding(
    compiled_text: str,
    target_residue: int = DEFAULT_TARGET_RESIDUE,
    B: int = BLOCK_SIZE_DEFAULT,
    tokenizer: Any = None,
    *,
    offset_tokens: int = 0,
    neutral_token: str = NEUTRAL_TOKEN,
    max_blocks: int = 4,
) -> Padding:
    """Pad ``compiled_text`` so the PROMPT lands on ``target_residue`` mod ``B``.

    ``offset_tokens`` is everything the request carries that this text does not: the
    other messages plus the chat template's own framing tokens. It matters more than
    it looks -- the residue the server bills is ``(token_len(prompt)) mod B``, and a
    quantiser that aligns only its own text is off by exactly that offset (measured:
    two cells aimed at residue 2 and 0 landed on 23 and 21 before this was threaded
    through).

    The padding is repetitions of a semantically inert token (default ``" the"``,
    one token each), appended at the end, so the compiled prompt keeps its meaning
    and gains only a tail of filler. The minimal padding that lands on target is
    used; a non-minimal one is tried only if the tokenizer merges the filler (which
    is reported, never papered over).

    Raises ``PTR_ANNOTATION_INVALID`` when the residue cannot be hit with inert
    filler, naming the measured count -- a silent under-pad would leave the
    avalanche in place while looking fixed.
    """
    if not isinstance(compiled_text, str):
        raise PtrAnnotationError(
            f"choose_padding takes the compiled prompt text, got {type(compiled_text).__name__}",
            got=type(compiled_text).__name__,
        )
    if not isinstance(B, int) or isinstance(B, bool) or B <= 0:
        raise PtrAnnotationError(f"block_size must be a positive int, got {B!r}")
    if (
        not isinstance(target_residue, int)
        or isinstance(target_residue, bool)
        or not 0 <= target_residue < B
    ):
        raise PtrAnnotationError(
            f"target_residue must be an int in [0, {B}), got {target_residue!r}"
        )
    if not isinstance(neutral_token, str) or not neutral_token:
        raise PtrAnnotationError("neutral_token must be a non-empty string")
    if not isinstance(offset_tokens, int) or isinstance(offset_tokens, bool):
        raise PtrAnnotationError(f"offset_tokens must be an int, got {offset_tokens!r}")
    token_source = getattr(tokenizer, "base_url", None) or type(tokenizer).__name__

    base_tokens = token_len(compiled_text, tokenizer)
    residue_before = (base_tokens + offset_tokens) % B
    text_target = (target_residue - offset_tokens) % B
    first = (text_target - base_tokens % B) % B

    attempts: list[int] = [first]
    for block in range(1, max(1, max_blocks) + 1):
        attempts.append(first + block * B)
    measured: list[str] = []
    for padding_tokens in attempts:
        padding = neutral_token * padding_tokens
        text = compiled_text + padding
        padded_tokens = token_len(text, tokenizer)
        if (
            padded_tokens == base_tokens + padding_tokens
            and padded_tokens % B == text_target
        ):
            return Padding(
                text=text,
                padding=padding,
                padding_tokens=padding_tokens,
                target_residue=target_residue,
                block_size=B,
                base_tokens=base_tokens,
                padded_tokens=padded_tokens,
                residue_before=residue_before,
                residue_after=(padded_tokens + offset_tokens) % B,
                token_source=str(token_source),
                offset_tokens=offset_tokens,
            )
        measured.append(
            f"pad {padding_tokens} -> {padded_tokens} tokens "
            f"(prompt residue {(padded_tokens + offset_tokens) % B})"
        )
    raise PtrAnnotationError(
        "inert padding could not land on the target residue: " + "; ".join(measured),
        base_tokens=base_tokens,
        offset_tokens=offset_tokens,
        target_residue=target_residue,
        block_size=B,
    )


def predict_billed(P1: int, L: int, B: int = BLOCK_SIZE_DEFAULT) -> Tuple[int, bool]:
    """``(predicted_uncached, avalanche_flag)`` for an append onto a primed prefix.

    ``P1`` is the PRIME prompt's token length, ``L`` the number of tokens appended
    since (the measured prompt delta, framing included -- never the payload count).
    The law, with its measured discontinuity:

        residue = P1 mod B
        residue in {0, 1}  ->  (P1 + L, True)      # no cache reported; whole prefix billed
        otherwise          ->  (residue + L, False)
    """
    for name, value in (("P1", P1), ("L", L), ("B", B)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise PtrAnnotationError(f"{name} must be a non-negative int, got {value!r}")
    if B <= 0:
        raise PtrAnnotationError(f"B must be a positive int, got {B!r}")
    residue = P1 % B
    if residue in AVALANCHE_RESIDUES:
        return (P1 + L, True)
    return (residue + L, False)


def quick_bill(P1: int, L: int, B: int = BLOCK_SIZE_DEFAULT) -> int:
    """``P1 + predict_billed(P1, L, B)[0]``: the predicted prime-plus-append bill.

    Section 13's law restated as one number, so a caller who already knows ``P1``
    does not have to assemble the dict :func:`cycle_bill` returns (that function
    answers a different question: *does padding to a target pay?*).
    """
    uncached, _avalanche = predict_billed(P1, L, B)
    return P1 + uncached


def cycle_bill(
    P1: int, L: int, B: int = BLOCK_SIZE_DEFAULT, target_residue: int = DEFAULT_TARGET_RESIDUE
) -> dict[str, Any]:
    """Does padding to ``target_residue`` pay for *this* prefix? The arithmetic.

    Two accountings, because the answer differs and a host must know which one it is
    buying:

    * ``delta`` -- the **per-cycle** bill when the compiled prompt is new every turn
      (the index is recompiled, so the padding is re-paid): the prime bills ``P1``
      plus the padding, the append bills the residue plus ``L``, so
      ``delta = k - (residue_before - target)``. Negative only when the padding
      dodges an avalanche or the residue is large.
    * ``breakeven_turns`` -- the **amortised** bill when one padded prefix stays
      resident for ``T`` turns: the padding is paid once and the tail saving repeats,
      so it pays from ``ceil(k / (residue_before - target))`` turns on. ``0`` means
      it pays on the first append (an avalanche was dodged), ``None`` means it never
      pays (there is no tail left to save).
    """
    residue = P1 % B
    k = (target_residue - residue) % B
    unpadded_uncached, avalanche = predict_billed(P1, L, B)
    padded_uncached, padded_avalanche = predict_billed(P1 + k, L, B)
    unpadded_cycle = P1 + unpadded_uncached
    padded_cycle = (P1 + k) + padded_uncached
    tail_saving = residue - target_residue
    if avalanche:
        breakeven: Optional[int] = 0
    elif k > 0 and tail_saving > 0:
        breakeven = -(-k // tail_saving)
    else:
        breakeven = None
    return {
        "P1": P1,
        "L": L,
        "block_size": B,
        "residue": residue,
        "target_residue": target_residue,
        "padding_tokens": k,
        "avalanche_without_padding": avalanche,
        "avalanche_with_padding": padded_avalanche,
        "unpadded_uncached": unpadded_uncached,
        "padded_uncached": padded_uncached,
        "unpadded_cycle": unpadded_cycle,
        "padded_cycle": padded_cycle,
        "delta": padded_cycle - unpadded_cycle,
        "pays": padded_cycle < unpadded_cycle,
        "tail_saving_per_turn": tail_saving if not avalanche else None,
        "breakeven_turns": breakeven,
    }


@dataclass(frozen=True)
class CompactIndex:
    """A compacted index text, plus what was dropped to produce it."""

    text: str
    bytes_len: int
    entries: int
    per_line: float
    original_bytes: int
    header: str
    revision: int
    scope: str
    block_size: int
    hash_chars: int
    dropped: Tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "bytes": self.bytes_len,
            "entries": self.entries,
            "per_line": self.per_line,
            "original_bytes": self.original_bytes,
            "saved_bytes": self.original_bytes - self.bytes_len,
            "hash_chars": self.hash_chars,
            "dropped": list(self.dropped),
        }

    def ratio(self, total_body_bytes: int) -> float:
        """``r = total body bytes / index bytes`` -- the index's own compression."""
        if self.bytes_len <= 0:
            raise PtrAnnotationError("compact index has no bytes")
        return total_body_bytes / self.bytes_len


def _strip_revision(ref_text: str, revision: int) -> str:
    """Drop the ``@<revision>`` component of a serialized reference.

    The revision sits between the optional ``#pointer`` and the optional
    ``?projection`` (``@memory:m01@3?brief``), so it is not simply a suffix: the
    projection is split off first, then the revision, then the projection restored.
    """
    base, sep, projection = ref_text.partition("?")
    suffix = f"@{revision}"
    if base.endswith(suffix):
        base = base[: -len(suffix)]
    return base + sep + projection


def compact_index(index_text: str) -> CompactIndex:
    """Drop redundancy from index lines, keeping every number a resolver needs.

    What is removed, and why nothing is lost:

    * the ``"- "`` bullet -- decoration; the block is already delimited by
      ``<ptr-index>``/``</ptr-index>``;
    * the per-line ``@<revision>`` -- the header carries the revision for the whole
      index, and ``resolve()`` accepts a revision-less reference, so the host
      re-pins it from the header (``ref_index`` in the ledger records both
      spellings);
    * hex characters of the body digest beyond ``COMPACT_HASH_CHARS`` -- the line's
      digest is a *display* handle; ``store.get`` re-hashes the full sha256 on read,
      so which bytes a ref designates cannot change.

    What is deliberately **kept** because dropping it would lose a capability: the
    item id (the model echoes it), the kind (it is part of the address and of the
    scope check) and the byte length (the number a host uses to decide whether a
    body is worth fetching). ``dropped`` names exactly what went.
    """
    if not isinstance(index_text, str):
        raise PtrAnnotationError(
            f"compact_index takes the index text, got {type(index_text).__name__}"
        )
    lines = [line for line in index_text.splitlines() if line.strip()]
    if not lines:
        raise PtrAnnotationError("compact_index got an empty index")
    header = lines[0]
    fields: dict[str, str] = {}
    for token in header.split()[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key] = value
    try:
        revision = int(fields["revision"])
        entries_declared = int(fields["entries"])
    except (KeyError, ValueError) as exc:
        raise PtrAnnotationError(
            f"index header is not parseable: {header!r} ({exc})", header=header
        ) from exc
    block_size = int(fields.get("block_size", BLOCK_SIZE_DEFAULT))
    scope = fields.get("scope", "")

    body_lines = lines[1:]
    if len(body_lines) != entries_declared:
        raise PtrAnnotationError(
            f"header declares {entries_declared} entries, found {len(body_lines)} lines",
            entries=entries_declared,
            lines=len(body_lines),
        )

    compact_header = (
        f"{COMPACT_MAGIC} scope={scope} revision={revision} "
        f"block_size={block_size} entries={entries_declared} hash={COMPACT_HASH_CHARS}"
    )
    out: list[str] = [compact_header]
    for line in body_lines:
        parts = line.split()
        if parts and parts[0] == "-":
            parts = parts[1:]
        if len(parts) != 3:
            raise PtrAnnotationError(
                f"index line is not '<ref> <hash> <bytes>': {line!r}", line=line
            )
        ref_text, digest, size = parts
        ref_text = _strip_revision(ref_text, revision)
        out.append(f"{ref_text} {digest[:COMPACT_HASH_CHARS]} {size}")
    text = "\n".join(out) + "\n"
    return CompactIndex(
        text=text,
        bytes_len=len(text.encode("utf-8")),
        entries=entries_declared,
        per_line=len(text.encode("utf-8")) / entries_declared,
        original_bytes=len(index_text.encode("utf-8")),
        header=compact_header,
        revision=revision,
        scope=scope,
        block_size=block_size,
        hash_chars=COMPACT_HASH_CHARS,
        dropped=(
            "'- ' bullet from every line (the block is tag-delimited)",
            f"per-line '@{revision}' (the header pins the revision; resolve() re-pins it)",
            f"body-digest display handle {8}->{COMPACT_HASH_CHARS} hex chars (store verifies full sha256)",
        ),
    )


# --------------------------------------------------------------------------
# Shape search: move P1 by CUTTING before you move it by ADDING
# --------------------------------------------------------------------------
#
# ENGINE-R1 measured the cost of padding: from residue r to residue 2 is 66-r
# filler tokens against a tail saving of r-2, so at a benign residue the finding
# recompile pays 36-58 billed tokens a cycle for a benefit that only repeats when
# the prefix stays warm. But `compact_index` shows the other direction exists: the
# compact form is 64 bytes -- tens of prompt tokens -- SHORTER, and a shorter
# prefix moves the residue just as surely as a padded one, for nothing.
#
# So `choose_shape` searches every variant a caller offers (full, compact,
# projection-shortened, ...), pads only where padding is free or forced, and
# returns the shape with the LOWEST predicted cycle bill. Every number it produces
# is a PREDICTION from the law; `predicted=True` on the result says so, and a
# caller who measures live must not read these as measurements.

#: Residues whose tail cost makes reaching ONE smaller residue a saving: the tail
#: is ``r + L`` and the bill ``P1 + r + L``, so removing ``k < r`` tokens takes the
#: residue to ``r - k`` and takes ``k`` off the bill twice. Padding is free there.
#: Below this (and above the avalanche at {0, 1}) the tail is shorter than the
#: filler needed to move it, which is exactly the 36-58 tokens ENGINE-R1 billed.
PAD_FOR_FREE_RESIDUE = 33

#: Prefix tokens are replaced by this placeholder when a variant is shortened, so
#: whatever tokenizer counts the shortened form sees the fallback's own cost.
PLACEHOLDER = "?\u2026?"


@dataclass(frozen=True)
class ShapeVariant:
    """One candidate shape of the prompt: a text and what it costs to get there.

    ``cuts`` is not decoration. Each entry names what was removed and the capability
    that went with it, so a variant that is cheap because it lost a capability can
    be seen for what it is rather than mistaken for a free win.
    """

    name: str
    text: str
    index_form: str = "full"
    payload_tokens: int = 0
    cuts: Tuple[str, ...] = ()
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "variant": self.name,
            "index_form": self.index_form,
            "payload_tokens": self.payload_tokens,
            "bytes": len(self.text.encode("utf-8")),
            "cuts": list(self.cuts),
            "note": self.note,
        }


def projection_variant(
    index_text: str,
    *,
    name: str = "projection",
    index_form: str = "compact",
) -> ShapeVariant:
    """Shorten each line's body-digest handle and declare exactly what that costs.

    The digest is shortened by replacing every non-final hex character with a
    placeholder, so the variant's byte length is what the real shortened line would
    be and any tokenizer can count it. Nothing else about the text changes.

    **This variant is not free, and the capability it loses is named here:** the
    line's digest stops being a handle a resolver can verify against. ``store.get``
    still re-hashes the full sha256 on read, so *which bytes* a ref designates never
    changes -- but a host can no longer tell a stale line from a fresh one by
    prefix, and the model's echo of the line is no longer checkable against the
    body. ``ShapeVariant.cuts`` says so, and ``choose_shape`` reports it.
    """
    if not isinstance(index_text, str) or not index_text.strip():
        raise PtrAnnotationError("projection_variant takes a non-empty index text")
    lines = index_text.splitlines()
    # The header is whichever line carries a ``revision=`` field: the compact form's
    # magic differs from the full form's, and a caller may hand us an envelope whose
    # first line is the ``<ptr-index>`` tag rather than the header.
    start = next(
        (i for i, line in enumerate(lines) if "revision=" in line.split()[0:2] or
         ("revision=" in line and line.split()[0].startswith("ptr-index"))),
        0,
    )
    out: list[str] = list(lines[: start + 1])
    changed = 0
    for line in lines[start + 1:]:
        if not line.strip() or line.strip().startswith("</"):
            out.append(line)          # envelope tag or trailing blank: not a line
            continue
        parts = line.split()
        if parts and parts[0] == "-":
            parts = parts[1:]
            bullet = "- "
        else:
            bullet = ""
        if len(parts) != 3:
            raise PtrAnnotationError(
                f"index line is not '<ref> <hash> <bytes>': {line!r}", line=line
            )
        ref_text, digest, size = parts
        if len(digest) > 1:
            shortened = digest[:1] + "…" * (len(digest) - 1)
            changed += 1
        else:
            shortened = digest
        out.append(f"{bullet}{ref_text} {shortened} {size}")
    if not changed:
        raise PtrAnnotationError("index has no digests to shorten")
    return ShapeVariant(
        name=name,
        text="\n".join(out) + "\n",
        index_form=index_form,
        cuts=(
            "per-line body digest shortened to the first hex character "
            "(the line stops being a verifiable handle; store.get still re-hashes)",
        ),
        note="cheap because it loses the stale-line / echo check",
    )


@dataclass(frozen=True)
class ShapeCandidate:
    """One row of the search: a variant, the padding it took, and its predicted bill."""

    variant: str
    index_form: str
    cuts: Tuple[str, ...]
    base_tokens: int
    padding_tokens: int
    P1: int
    residue: int
    predicted_uncached: int
    avalanche: bool
    prime_bill: int
    cycle_bill: int
    dP1_vs_reference: int
    dcycle_vs_reference: int
    free: bool
    cheap_residue: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "index_form": self.index_form,
            "base_tokens": self.base_tokens,
            "padding_tokens": self.padding_tokens,
            "P1": self.P1,
            "residue": self.residue,
            "predicted_uncached": self.predicted_uncached,
            "avalanche": self.avalanche,
            "prime_bill": self.prime_bill,
            "cycle_bill": self.cycle_bill,
            "dP1_vs_reference": self.dP1_vs_reference,
            "dcycle_vs_reference": self.dcycle_vs_reference,
            "free": self.free,
            "cheap_residue": self.cheap_residue,
            "cuts": list(self.cuts),
        }


@dataclass(frozen=True)
class ShapeChoice:
    """The search's verdict: the best candidate, the whole table, and why it won."""

    chosen: ShapeCandidate
    candidates: Tuple[ShapeCandidate, ...]
    reference: str
    L: int
    B: int
    cheap_residues: Tuple[int, ...]
    padded: bool
    padding_reason: str
    avalanche_avoided: bool
    predicted: bool = True
    basis: str = "law: uncached = (P1 mod B) + L, avalanche at {0, 1}"

    @property
    def residue(self) -> int:
        return self.chosen.residue

    @property
    def cycle_bill(self) -> int:
        return self.chosen.cycle_bill

    def as_dict(self) -> dict[str, Any]:
        return {
            "chosen": self.chosen.as_dict(),
            "reference": self.reference,
            "L": self.L,
            "block_size": self.B,
            "cheap_residues": list(self.cheap_residues),
            "padded": self.padded,
            "padding_reason": self.padding_reason,
            "avalanche_avoided": self.avalanche_avoided,
            "predicted": self.predicted,
            "basis": self.basis,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
        }

    def table(self) -> str:
        """The candidate table a reader can check the choice against."""
        head = (
            f"{'variant':<26}{'form':<9}{'base':>6}{'pad':>5}{'P1':>6}"
            f"{'res':>5}{'uncached':>10}{'cycle':>7}{'dcycle':>8}  flags"
        )
        rows = [head, "-" * len(head)]
        for cand in self.candidates:
            flags = []
            if cand.variant == self.reference:
                flags.append("reference")
            if cand.free:
                flags.append("free")
            if cand.avalanche:
                flags.append("AVALANCHE")
            if cand.cuts:
                flags.append("cuts-capability")
            if cand is self.chosen:
                flags.append("<== chosen")
            rows.append(
                f"{cand.variant:<26}{cand.index_form:<9}{cand.base_tokens:>6}"
                f"{cand.padding_tokens:>5}{cand.P1:>6}{cand.residue:>5}"
                f"{cand.predicted_uncached:>10}{cand.cycle_bill:>7}"
                f"{cand.dcycle_vs_reference:>+8}  {' '.join(flags)}"
            )
        return "\n".join(rows)


def _cheap_residues(B: int) -> Tuple[int, ...]:
    """Residues no append can be cheaper from: not an avalanche, and cuttable."""
    return tuple(
        r for r in range(2, B) if r >= PAD_FOR_FREE_RESIDUE
    )


def _pad_up_to(text: str, residue: int, target: int, B: int, tokenizer: Any,
               neutral_token: str) -> Optional[Tuple[int, int, str]]:
    """Append the fewest inert tokens that take ``residue`` UP to ``target``."""
    need = (target - residue) % B
    if need == 0:
        return (0, residue, "")
    padding = neutral_token * need
    padded = text + padding
    counted = token_len(padded, tokenizer)
    if counted == token_len(text, tokenizer) + need and counted % B == target:
        return (need, target, padding)
    return None


def choose_shape(
    index_variants: Sequence[ShapeVariant],
    target_residue: int = DEFAULT_TARGET_RESIDUE,
    B: int = BLOCK_SIZE_DEFAULT,
    tokenizer: Any = None,
    *,
    offset_tokens: int = 0,
    L: int = 13,
    payload_tokens: int = 0,
    neutral_token: str = NEUTRAL_TOKEN,
    reference: Optional[str] = None,
    max_pad: Optional[int] = None,
) -> ShapeChoice:
    """Pick the index shape with the LOWEST predicted cycle bill, not the first legal one.

    Three ways to move ``P1 mod B``, of which only one costs anything:

    * **cut** -- a shorter variant (compact index, shortened projection) moves the
      residue with no filler at all. Preferred whenever it lands legally, because a
      mid-range legal residue is nearly as cheap as residue 2 and costs nothing;
    * **pad** -- filler tokens. Taken only when it is free (the residue is at least
      ``PAD_FOR_FREE_RESIDUE``, so each filler token removes twice its own cost) or
      forced (the variant landed on residue 0 or 1, the avalanche);
    * **do nothing** -- the unpadded shape, chosen whenever it already wins.

    The predicted cycle bill is ``P1 + (P1 mod B) + L`` per the law, with the whole
    prefix billed when ``P1 mod B`` is 0 or 1. ``payload_tokens`` is added to ``L``
    for the append: the engine's measured ``L`` of 13 is *one* payload token plus 12
    framing tokens, so an append carrying ``m`` payload tokens bills ``(P1 mod B) +
    12 + m``. When the caller reports payloads that differ between variants, the
    cheap append is never cheaper than ``width + min_payload``, which is what the
    search compares against.

    Every number here is **PREDICTED**. ``ShapeChoice.predicted`` is ``True`` and a
    host that measures live must record the measured value beside it, not instead
    of it.
    """
    if not isinstance(B, int) or isinstance(B, bool) or B <= 0:
        raise PtrAnnotationError(f"block_size must be a positive int, got {B!r}")
    if not isinstance(target_residue, int) or isinstance(target_residue, bool):
        raise PtrAnnotationError(f"target_residue must be an int, got {target_residue!r}")
    if not 0 <= target_residue < B:
        raise PtrAnnotationError(
            f"target_residue must be in [0, {B}), got {target_residue!r}"
        )
    if not isinstance(L, int) or isinstance(L, bool) or L < 0:
        raise PtrAnnotationError(f"L must be a non-negative int, got {L!r}")
    if not isinstance(payload_tokens, int) or isinstance(payload_tokens, bool) or payload_tokens < 0:
        raise PtrAnnotationError(
            f"payload_tokens must be a non-negative int, got {payload_tokens!r}"
        )
    if not isinstance(offset_tokens, int) or isinstance(offset_tokens, bool):
        raise PtrAnnotationError(f"offset_tokens must be an int, got {offset_tokens!r}")
    variants = tuple(index_variants)
    if not variants:
        raise PtrAnnotationError("choose_shape needs at least one index variant")
    names = [v.name for v in variants]
    if len(set(names)) != len(names):
        raise PtrAnnotationError(f"variant names must be unique, got {names}")
    if reference is None:
        reference = variants[0].name
    if reference not in names:
        raise PtrAnnotationError(
            f"reference {reference!r} is not one of {names}",
            reference=reference,
            variants=names,
        )

    rows: list[ShapeCandidate] = []
    pad_failure: list[str] = []
    for variant in variants:
        base = token_len(variant.text, tokenizer) + offset_tokens
        residue = base % B
        append_L = L + variant.payload_tokens
        # Padding is a CANDIDATE, not a policy: the law decides whether it pays,
        # because the filler is paid once (it lives in P1) and the tail saving is
        # paid per append. Padding only ever RAISES P1, so an unpadded row at a legal
        # residue bounds every padded row of the same variant from below -- which is
        # what keeps "not worth it" reachable, and was the defect this unit fixed:
        # an earlier draft always tried the target first and so always padded.
        #
        # The target is usually 2. A variant already in the free band
        # (``residue >= PAD_FOR_FREE_RESIDUE``) additionally wants its largest legal
        # residue, so it is also tried at ``B - 1``: still one token clear of the
        # avalanche, and almost the whole tail cut for almost no filler.
        targets = {target_residue}
        if residue >= PAD_FOR_FREE_RESIDUE and residue != B - 1:
            targets.add(B - 1)
        plan: list[tuple[int, int]] = [(0, residue)]
        for target in sorted(targets):
            up = _pad_up_to(variant.text, residue, target, B, tokenizer, neutral_token)
            if up is None or up[0] > (max_pad if max_pad is not None else B):
                continue
            plan.append((up[0], up[1]))
        if residue in AVALANCHE_RESIDUES and len(plan) == 1:
            pad_failure.append(
                f"{variant.name}: avalanche at residue {residue} and inert filler could "
                "not reach a legal residue -- the search has nothing to offer here and "
                "says so rather than returning it"
            )
        for pad_tokens, padded_residue in plan:
            P1 = base + pad_tokens
            uncached, avalanche = predict_billed(P1, append_L, B)
            rows.append(
                ShapeCandidate(
                    variant=variant.name,
                    index_form=variant.index_form,
                    cuts=variant.cuts,
                    base_tokens=base,
                    padding_tokens=pad_tokens,
                    P1=P1,
                    residue=P1 % B,
                    predicted_uncached=uncached,
                    avalanche=avalanche,
                    prime_bill=P1,
                    cycle_bill=P1 + uncached,
                    dP1_vs_reference=0,
                    dcycle_vs_reference=0,
                    free=pad_tokens == 0,
                    cheap_residue=pad_tokens == 0 or padded_residue >= PAD_FOR_FREE_RESIDUE,
                )
            )

    reference_P1 = next(r.base_tokens for r in rows if r.variant == reference)
    ref_row = next(r for r in rows if r.variant == reference and r.padding_tokens == 0)
    rows = [
        ShapeCandidate(
            **{
                **row.__dict__,
                "dP1_vs_reference": row.P1 - reference_P1,
                "dcycle_vs_reference": row.cycle_bill - ref_row.cycle_bill,
            }
        )
        for row in rows
    ]
    # A shape on the avalanche is never returned while a legal row exists: residue 0
    # or 1 bills the whole prefix, and a host with a legal row in hand that returns
    # 0 or 1 has not searched. Deterministic tie-break: cheapest predicted bill, then
    # the row that adds nothing, then the row that cuts nothing, then name.
    legal = [row for row in rows if not row.avalanche] or rows
    legal.sort(key=lambda r: (r.cycle_bill, r.padding_tokens, bool(r.cuts), r.variant))
    chosen = legal[0]
    rows.sort(key=lambda r: (r.cycle_bill, r.padding_tokens, bool(r.cuts), r.variant))

    padded = chosen.padding_tokens > 0
    if padded:
        cheapest_free = min(
            row.cycle_bill for row in rows if row.padding_tokens == 0
        )
        if chosen.cheap_residue and ref_row.avalanche and chosen.variant == ref_row.variant:
            reason = (
                f"PADDED: {chosen.variant} landed on residue {chosen.base_tokens % B} "
                f"(the avalanche); {chosen.padding_tokens} inert token(s) dodge it "
                f"({ref_row.cycle_bill} -> {chosen.cycle_bill} predicted)"
            )
        elif chosen.cycle_bill < cheapest_free:
            reason = (
                f"PADDED: {chosen.variant} sits at residue {chosen.base_tokens % B}; "
                f"{chosen.padding_tokens} inert token(s) take it to {chosen.residue}, "
                f"which is cheaper once the tail is paid "
                f"({cheapest_free} -> {chosen.cycle_bill} predicted)"
            )
        else:
            reason = (
                f"PADDED: every free variant sat below residue {PAD_FOR_FREE_RESIDUE} "
                f"(where the filler costs more than the tail it saves), so none reached "
                f"a cheap residue; {chosen.variant} was cut to residue "
                f"{chosen.base_tokens % B} and padded from there, "
                f"{chosen.padding_tokens} inert token(s) (residue -> {chosen.residue})"
            )
    else:
        reachable = [row for row in rows if not row.avalanche and row.cycle_bill < chosen.cycle_bill]
        reason = f"NO PADDING: {chosen.variant} lands on residue {chosen.residue} unpadded"
        if not reachable:
            reason += (
                "; no shape reached a cheap residue at an acceptable bill"
                + (
                    f" (padding capped at {max_pad} token(s))"
                    if max_pad is not None
                    else ""
                )
            )
    if pad_failure:
        reason += " | " + "; ".join(pad_failure)

    return ShapeChoice(
        chosen=chosen,
        candidates=tuple(rows),
        reference=reference,
        L=L,
        B=B,
        cheap_residues=_cheap_residues(B),
        padded=padded,
        padding_reason=reason,
        avalanche_avoided=bool(ref_row.avalanche and not chosen.avalanche),
    )


#: How many append tokens the measured anchors pin. ENGINE-R1 measured L = 13 only.
#: Padding moves the residue by whole inert tokens and an append is a *delta* whose
#: cost depends on how the template frames the tail -- so the residue comparison is
#: anchored while the append's own scaling under a stub is NOT. Stated, not fitted.
CALIBRATED_APPEND_TOKENS = frozenset({13})


def calibration_limits(L: int) -> Tuple[str, ...]:
    """What a law-based prediction here is and is not anchored to.

    Returned as data rather than prose so a report can quote it: the residue channel
    is calibrated against ENGINE-R1's two measured anchors, the append channel is
    calibrated at ``L = 13`` only, and *every* number produced by this module is
    PREDICTED, never measured.
    """
    limits = [
        "PREDICTED, not measured: this unit sent no request",
        "the per-placeholder token cost is a hypothesis; the engine has no real tokenizer offline",
        "a short append's cost tracks the template framing, not the prompt's length, so L does not scale with the prompt",
    ]
    if L not in CALIBRATED_APPEND_TOKENS:
        limits.append(
            f"L={L} was never measured (measured: {sorted(CALIBRATED_APPEND_TOKENS)})"
        )
    return tuple(limits)


__all__ = [
    "AVALANCHE_RESIDUES",
    "BLOCK_SIZE_DEFAULT",
    "CALIBRATED_APPEND_TOKENS",
    "COMPACT_HASH_CHARS",
    "COMPACT_MAGIC",
    "CompactIndex",
    "DEFAULT_TARGET_RESIDUE",
    "NEUTRAL_TOKEN",
    "PAD_FOR_FREE_RESIDUE",
    "PLACEHOLDER",
    "Padding",
    "ServerTokenizer",
    "ShapeCandidate",
    "ShapeChoice",
    "ShapeVariant",
    "StubTokenizer",
    "Tokenizer",
    "calibration_limits",
    "choose_padding",
    "choose_shape",
    "compact_index",
    "cycle_bill",
    "predict_billed",
    "projection_variant",
    "quick_bill",
    "token_len",
]
