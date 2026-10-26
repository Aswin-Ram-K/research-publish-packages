"""``resextract.mine`` — the research-candidate miner.

Two pieces:

* :mod:`resextract.mine.provenance` — the honesty mechanism: every reference a
  candidate cites is independently checked against the loaded graph and the
  target tree, and nothing there ever raises.
* :mod:`resextract.mine.candidates` — the miner itself, which drives
  ``graphify query`` over the canned battery, asks Occamy for candidates with
  ``thinking=True``, verifies their provenance, dedupes them and persists only
  what survives.

Typical use::

    from resextract.mine import Miner

    report = Miner("<workspace>", "state/kg/duval/graphify-out/graph.json").mine()
    print(report.accepted, report.rejected, report.reasoning_tokens, report.partial)
"""

from __future__ import annotations

from .candidates import (
    CANDIDATE_KINDS,
    DEFAULT_SUBSTITUTIONS,
    KINDS,
    MODEL_MAX_TOKENS,
    PROMPT_VERSION,
    Candidate,
    Degradation,
    MineReport,
    Miner,
    MinerError,
    Rejected,
)
from .provenance import (
    PROVENANCE_KINDS,
    Provenance,
    ProvenanceVerdict,
    parse_ref,
    verify_provenance,
)

__all__ = [
    "CANDIDATE_KINDS",
    "DEFAULT_SUBSTITUTIONS",
    "KINDS",
    "MODEL_MAX_TOKENS",
    "PROMPT_VERSION",
    "PROVENANCE_KINDS",
    "Candidate",
    "Degradation",
    "MineReport",
    "Miner",
    "MinerError",
    "Provenance",
    "ProvenanceVerdict",
    "Rejected",
    "parse_ref",
    "verify_provenance",
]
