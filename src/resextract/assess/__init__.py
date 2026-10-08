"""Assessment stage (unit U4.1): evidence gathering and verdicts.

Public surface::

    from resextract.assess import (
        EvidenceRecord, GatherResult, generate_queries, gather_evidence, quote_from,
        Verdict, AssessReport, assess_claim, assess_claims,
    )
"""

from __future__ import annotations

from .evidence import (
    DEFAULT_QUOTE_CHARS,
    EvidenceRecord,
    GatherResult,
    evidence_hash,
    generate_queries,
    gather_evidence,
    key_terms,
    lexical_queries,
    quote_from,
    term_ratio,
)
from .verdicts import (
    DEFAULT_CLIENT_PRODUCER,
    MODEL_PRODUCER,
    PROMPT_VERSION,
    PRODUCER_VOCAB,
    VERDICT_VOCAB,
    AssessReport,
    ProducerDeclarationError,
    Verdict,
    assess_claim,
    assess_claims,
    may_back_model_claim,
)
from .value import (  # U4.4: the second half of stage 5 — real-world value axes
    AXIS_NAMES,
    Axis,
    ValueAssessment,
    ValueReport,
    assess_value,
    assess_values,
)

__all__ = [
    "AXIS_NAMES",
    "DEFAULT_QUOTE_CHARS",
    "DEFAULT_CLIENT_PRODUCER",
    "MODEL_PRODUCER",
    "PROMPT_VERSION",
    "PRODUCER_VOCAB",
    "VERDICT_VOCAB",
    "AssessReport",
    "Axis",
    "EvidenceRecord",
    "GatherResult",
    "ProducerDeclarationError",
    "ValueAssessment",
    "ValueReport",
    "Verdict",
    "assess_claim",
    "assess_claims",
    "assess_value",
    "assess_values",
    "evidence_hash",
    "may_back_model_claim",
    "gather_evidence",
    "generate_queries",
    "key_terms",
    "lexical_queries",
    "quote_from",
    "term_ratio",
]
