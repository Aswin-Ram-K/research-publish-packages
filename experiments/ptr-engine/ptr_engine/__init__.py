"""ptr_engine -- a makeshift pointer engine.

Compile a turn's material into a content-addressed warmpool plus a short index;
resolve an index line on demand to a verified content identity.

    from ptr_engine import BodyStore, Scope, compile_turn, resolve, build_prompt

    store = BodyStore("/var/tmp/ptr-warmpool")
    ledger = Ledger("/var/tmp/ptr-warmpool/turn-0003.jsonl")
    index = compile_turn(material, revision=3, scope="sess-01", block_size=64, store=store)
    scope = Scope(name="sess-01", index=index)
    target = resolve(parse("@knowledge:k03@3"), scope, ledger)   # -> ResourceRef
    prompt = build_prompt(index, {parse("@knowledge:k03@3"): store.get(target)}, ledger)

The one rule the package cannot express in a type: resolution is one-way. A
``Reference`` resolves to a ``ResourceRef``; nothing resolves a ``ResourceRef``
back to a ``Reference``.
"""

from __future__ import annotations

from .adapter import build_prompt, fetch_tool_spec
from .annotate import (
    DEPTH_LEAF,
    DEPTH_ROOT,
    append_cost,
    depth,
    ledger_id,
    scope as entry_scope,
)
from .compile import (
    DEFAULT_PROJECTIONS,
    INDEX_MAGIC,
    Entry,
    TurnIndex,
    compile_turn,
    projections_for,
)
from .errors import (
    PtrAnnotationError,
    PtrBodyMismatchError,
    PtrBudgetExceededError,
    PtrDuplicateIdError,
    PtrError,
    PtrExtensionError,
    PtrHashMismatchError,
    PtrLedgerBlockSizeError,
    PtrLedgerCountError,
    PtrLedgerError,
    PtrLedgerIdError,
    PtrLedgerRefusalCodeError,
    PtrLedgerScopeError,
    PtrLawBoundInvalidError,
    PtrLawError,
    PtrLawObservedInvalidError,
    PtrLawSeriesLengthError,
    PtrLawUnknownServerError,
    PtrMaterialError,
    PtrNotAReferenceError,
    PtrPointerError,
    PtrProjectionUngrantedError,
    PtrRevisionError,
    PtrScopeUngrantedError,
    PtrStoreMissError,
    PtrSyntaxError,
    PtrTokenSourceRequiredError,
    PtrUnknownIdError,
    PtrUnknownKindError,
    PtrUnresolvedRefError,
    PtrWarmpoolViolationError,
)
from .ledger import (
    FRAMING_TOKENS,
    LEDGER_CODES,
    LEDGER_LAW_CODES,
    SERVER_PROFILES,
    VLLM_PROFILE,
    SGLANG_PROFILE,
    HitEntry,
    HitLedger,
    Ledger,
    LedgerSummary,
    Reconciliation,
    ServerProfile,
    TurnCheck,
    law_L,
    predict_uncached,
    read_ledger,
    server_profile,
)
from .reference import (
    REF_KINDS,
    Reference,
    ResourceRef,
    format,
    format_reference,
    parse,
    parse_reference,
)
from .resolve import DEFAULT_MAX_REFS, Scope, resolve
from .store import BodyStore, assert_warmpool_root, default_root, find_repo_root

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # reference
    "REF_KINDS",
    "Reference",
    "ResourceRef",
    "parse",
    "format",
    "parse_reference",
    "format_reference",
    # store
    "BodyStore",
    "assert_warmpool_root",
    "default_root",
    "find_repo_root",
    # compile
    "compile_turn",
    "TurnIndex",
    "Entry",
    "INDEX_MAGIC",
    "DEFAULT_PROJECTIONS",
    "projections_for",
    # resolve
    "Scope",
    "resolve",
    "DEFAULT_MAX_REFS",
    # annotate
    "depth",
    "entry_scope",
    "append_cost",
    "ledger_id",
    "DEPTH_ROOT",
    "DEPTH_LEAF",
    # ledger
    "Ledger",
    "LEDGER_CODES",
    "read_ledger",
    # ledger: the billing law
    "HitLedger",
    "HitEntry",
    "TurnCheck",
    "Reconciliation",
    "LedgerSummary",
    "ServerProfile",
    "SERVER_PROFILES",
    "SGLANG_PROFILE",
    "VLLM_PROFILE",
    "server_profile",
    "predict_uncached",
    "law_L",
    "FRAMING_TOKENS",
    "LEDGER_LAW_CODES",
    # adapter
    "build_prompt",
    "fetch_tool_spec",
    # errors
    "PtrError",
    "PtrSyntaxError",
    "PtrUnknownKindError",
    "PtrUnknownIdError",
    "PtrScopeUngrantedError",
    "PtrProjectionUngrantedError",
    "PtrPointerError",
    "PtrBudgetExceededError",
    "PtrRevisionError",
    "PtrHashMismatchError",
    "PtrStoreMissError",
    "PtrWarmpoolViolationError",
    "PtrExtensionError",
    "PtrDuplicateIdError",
    "PtrMaterialError",
    "PtrNotAReferenceError",
    "PtrUnresolvedRefError",
    "PtrBodyMismatchError",
    "PtrTokenSourceRequiredError",
    "PtrAnnotationError",
    "PtrLedgerError",
    "PtrLedgerCountError",
    "PtrLedgerBlockSizeError",
    "PtrLedgerIdError",
    "PtrLedgerScopeError",
    "PtrLedgerRefusalCodeError",
    "PtrLawError",
    "PtrLawUnknownServerError",
    "PtrLawBoundInvalidError",
    "PtrLawSeriesLengthError",
    "PtrLawObservedInvalidError",
]

# -- residue quantisation (unit ENGINE-R1) ------------------------------------
# Appended rather than merged into the import block above: `quantise.py` was added
# while another card was editing this file, and an append cannot clobber its work.
from .quantise import (  # noqa: E402
    AVALANCHE_RESIDUES,
    BLOCK_SIZE_DEFAULT,
    COMPACT_HASH_CHARS,
    CompactIndex,
    DEFAULT_TARGET_RESIDUE,
    NEUTRAL_TOKEN,
    Padding,
    ServerTokenizer,
    StubTokenizer,
    calibration_limits,
    choose_padding,
    choose_shape,
    compact_index,
    cycle_bill,
    predict_billed,
    quick_bill,
    token_len,
)

__all__ = [
    *__all__,
    "AVALANCHE_RESIDUES",
    "BLOCK_SIZE_DEFAULT",
    "COMPACT_HASH_CHARS",
    "CompactIndex",
    "DEFAULT_TARGET_RESIDUE",
    "NEUTRAL_TOKEN",
    "Padding",
    "ServerTokenizer",
    "StubTokenizer",
    "calibration_limits",
    "choose_padding",
    "choose_shape",
    "compact_index",
    "cycle_bill",
    "predict_billed",
    "quick_bill",
    "token_len",
]
