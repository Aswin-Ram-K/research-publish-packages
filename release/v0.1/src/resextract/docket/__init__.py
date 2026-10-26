"""Docket assembly package.

Exposes the material copy engine (:mod:`resextract.docket.copy`), the
``MANIFEST.json`` contract (:mod:`resextract.docket.manifest`) and the folder
assembler + verifier (:mod:`resextract.docket.assemble`).

The assembler function is re-exported as ``assemble_docket`` so that the name
``assemble`` keeps referring to the :mod:`resextract.docket.assemble` module
(a plain ``assemble`` re-export would shadow it — and monkeypatching the module
would then silently patch a function).
"""

from __future__ import annotations

from resextract.docket.assemble import (
    AssembledDocket,
    AssemblyRefused,
    BacklogItem,
    DocketVerification,
    EvidenceItem,
    MeasuredResult,
    PriorArt,
    assemble as assemble_docket,
    material_report_from_docket,
    parse_excerpts,
    parse_links,
    verify_docket,
)
from resextract.docket.copy import (
    CopyIntegrityError,
    CopyItem,
    CopyPlan,
    CopyReport,
    CopyRequest,
    Copier,
    is_binary,
    sha256_file,
)
from resextract.docket.manifest import (
    DOCKET_TYPES,
    MANIFEST_NAME,
    SCHEMA,
    VERDICTS,
    Claim,
    DocketManifest,
    Freshness,
    GeneratedBy,
    Lane,
    MaterialItem,
    Target,
    WebSource,
    read_manifest,
    validate_manifest,
    write_manifest,
)

__all__ = [
    "AssembledDocket",
    "AssemblyRefused",
    "BacklogItem",
    "Claim",
    "CopyIntegrityError",
    "CopyItem",
    "CopyPlan",
    "CopyReport",
    "CopyRequest",
    "Copier",
    "DOCKET_TYPES",
    "DocketManifest",
    "DocketVerification",
    "EvidenceItem",
    "Freshness",
    "GeneratedBy",
    "Lane",
    "MANIFEST_NAME",
    "MaterialItem",
    "MeasuredResult",
    "PriorArt",
    "SCHEMA",
    "Target",
    "VERDICTS",
    "WebSource",
    "assemble_docket",
    "is_binary",
    "material_report_from_docket",
    "parse_excerpts",
    "parse_links",
    "read_manifest",
    "sha256_file",
    "validate_manifest",
    "verify_docket",
    "write_manifest",
]
