"""Real-world value axes for the assessment stage (unit U4.4).

**The rule, in one sentence: an axis is either substantiated by a verifiable
source or it is ``unknown``; ``unknown`` is a result, not a failure.**

``docs/PLAN.md`` §4 stage 5 requires assessment to cover *both* novelty verdicts
(:mod:`resextract.assess.verdicts`, the verified first half) **and per-claim
real-world value axes**.  This module is the second half.  It implements exactly
the six axes the plan names:

===================  ==========================================================
``affected_parties``  who is affected — the parties a finding matters to
``unblocks``          what it unblocks — the capability/decision it enables
``measured_delta``    the quantified improvement, if one exists
``reproducibility``   whether a third party could reproduce it, and how
``cost``              what it costs to exploit (compute, money, effort)
``licensing``         any licence constraint on the material or the finding
===================  ==========================================================

Honesty rules (the same discipline the rest of the pipeline uses)
----------------------------------------------------------------

* **No bare assertions.**  An axis with a value but no source is *downgraded to*
  ``unknown`` with the reason recorded — never silently dropped, never published.
* **A source must verify.**  A source is a measured result, a citation, a
  provenance reference (``path#L10-L20``, a graph node id, ``doc:path#Heading``)
  or an explicit evidence id (``evidence:7``).  Every source is checked by the
  *existing* verifier :func:`resextract.mine.provenance.verify_provenance` (or an
  evidence-id lookup) — nothing here re-implements provenance checking.  **A
  fabricated ref therefore cannot substantiate an axis**: a plausible-looking
  path, a span past the end of a short file, or a made-up evidence id is
  rejected and the axis becomes ``unknown`` with the failure recorded.
* **No client ⇒ no invention.**  Without a client the deterministic pass
  derives *only* what the claim's own stored data supports — a licence string
  found in cited material, a measured delta already in the store, and the
  reproducibility affordance of the claim's own verified provenance refs — and
  marks everything else ``unknown``.
* **Producer vocabulary is fail-closed, and shared.**  ``model`` | ``replay`` |
  ``fixture`` | ``unknown`` — imported from
  :mod:`resextract.store`, so there is exactly one vocabulary
  (``store.PRODUCER_VOCAB``, re-exported by ``assess.verdicts``).  ``fixture`` means *derived deterministically by
  this module from stored data, not by a model*.  An **undeclared** client is
  ``unknown`` (``verdicts.DEFAULT_CLIENT_PRODUCER``), never ``model``, and none
  of its axes may be substantiated: it is skipped before any call, because
  unattributable output may not substantiate an axis and spending a call on it
  proves nothing.  *U4.3's fail-closed change landed in* ``verdicts.py`` *while
  this unit was in flight (``PRODUCER_VOCAB``, ``DEFAULT_CLIENT_PRODUCER``,
  ``ProducerDeclarationError``, ``may_back_model_claim``); this module imports
  the vocabulary and mirrors its resolution walk, so the two halves of stage 5
  cannot drift apart.*
* **Truncation is not an empty result.**  This server counts reasoning *inside*
  ``max_tokens``, so a small cap yields empty content with
  ``finish_reason="length"``.  That (or ``UnparseableOutput``) is recorded as a
  degradation and yields **all six axes ``unknown``** for that claim — never a
  partial set presented as complete.
* **``BudgetExhausted`` stops the run**, keeps what is already substantiated and
  marks the report ``partial``.  One claim's failure never kills the run.

Store gap (reported, not silently dropped)
------------------------------------------

Schema v3 has **no value table** — there is nowhere in the store to put an
axis.  The axes therefore live in the run artefacts (``VALUE.md``,
``values.jsonl``, ``report.json``); ``ValueReport.store_gap`` says so
explicitly, and a future schema revision could add such a table.  The data is
kept, not dropped.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ..mine.provenance import parse_ref, verify_provenance
from ..store import MODEL_PRODUCER, PRODUCER_VOCAB, producer_is_model
from .verdicts import (
    DEFAULT_CLIENT_PRODUCER,
    ProducerDeclarationError,
    _client_producer as _verdicts_client_producer,
)

__all__ = [
    "AXIS_NAMES",
    "PRODUCER_VOCAB",
    "PROMPT_VERSION",
    "STORE_GAP",
    "VALUE_MAX_TOKENS",
    "Axis",
    "ValueAssessment",
    "ValueReport",
    "assess_value",
    "assess_values",
    "verify_axis_source",
]

#: Bump when the value prompt (or the deterministic rule) changes shape.
PROMPT_VERSION = "value-v1"

#: The six axes, in fixed order.  All six are always present in an assessment.
AXIS_NAMES: tuple[str, ...] = (
    "affected_parties",
    "unblocks",
    "measured_delta",
    "reproducibility",
    "cost",
    "licensing",
)

#: Producer vocabulary is the shared one from :mod:`resextract.assess.verdicts`
#: (re-exported here): ``fixture`` = derived deterministically here from stored
#: data; ``unknown`` = undeclared/unattributable (fail-closed).

#: The store gap this module reports rather than hides.
STORE_GAP = (
    "no value table exists in schema v3, so per-claim value axes cannot be "
    "persisted in the store; they are kept in the run artefacts (VALUE.md, "
    "values.jsonl, report.json) and a future schema revision could add one"
)

#: Reasoning is counted inside ``max_tokens`` on this server: a small cap yields
#: empty content with ``finish_reason="length"``.  Size for reasoning + answer.
VALUE_MAX_TOKENS = 3072

_EVIDENCE_RE = re.compile(r"^evidence:(\S+)$")
_SPAN_RE = re.compile(r"^(?P<path>.+?)#L(?P<start>\d+)(?:-L?(?P<end>\d+))?$")

#: Licence detection is deliberately token-based and conservative.
_LICENCE_TOKENS: tuple[str, ...] = (
    "MIT",
    "Apache-2.0",
    "Apache 2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSD",
    "GPL-2.0",
    "GPL-3.0",
    "LGPL",
    "AGPL",
    "ISC",
    "MPL-2.0",
    "Unlicense",
    "CC0",
    "CC-BY",
    "proprietary",
)
_LICENCE_RE = re.compile(
    r"(?i)(?:license|licence)\s*[\"']?\s*[:=]\s*[\"']?\s*([A-Za-z0-9][A-Za-z0-9 .\-+]{0,39})"
)
_LICENCE_STANDALONE_RE = re.compile(r"(?i)^\s*([A-Za-z0-9][A-Za-z0-9 .\-+]{0,39}?)\s*(?:license|licence)?\s*\.?\s*$")


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------- #
# data model
# --------------------------------------------------------------------------- #


@dataclass
class Axis:
    """One real-world value axis — substantiated, or honestly ``unknown``."""

    name: str
    substantiated: bool
    value: str | None = None
    source: str | None = None
    producer: str = "unknown"
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "substantiated": self.substantiated,
            "value": self.value,
            "source": self.source,
            "producer": self.producer,
            "reason": self.reason,
        }


@dataclass
class ValueAssessment:
    """The six axes for one claim, plus its honesty bookkeeping."""

    claim_id: int | None = None
    axes: list[Axis] = field(default_factory=list)
    model_calls: int = 0
    usage_records: int = 0
    producer: str = "unknown"
    degradations: list[dict[str, Any]] = field(default_factory=list)

    @property
    def substantiated_count(self) -> int:
        return sum(1 for a in self.axes if a.substantiated)

    @property
    def unknown_count(self) -> int:
        return sum(1 for a in self.axes if not a.substantiated)

    def by_name(self, name: str) -> Axis | None:
        for axis in self.axes:
            if axis.name == name:
                return axis
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "axes": [a.as_dict() for a in self.axes],
            "model_calls": self.model_calls,
            "usage_records": self.usage_records,
            "producer": self.producer,
            "degradations": list(self.degradations),
            "substantiated": self.substantiated_count,
            "unknown": self.unknown_count,
        }


@dataclass
class ValueReport:
    """Outcome of a value-axes run over many claims."""

    claims_assessed: int = 0
    axes_by_name: dict[str, dict[str, int]] = field(
        default_factory=lambda: {n: {"substantiated": 0, "unknown": 0} for n in AXIS_NAMES}
    )
    substantiated: int = 0
    unknown: int = 0
    producer: str = "unknown"
    partial: bool = False
    degradations: list[dict[str, Any]] = field(default_factory=list)
    #: additive
    model_calls: int = 0
    usage_records: int = 0
    assessments: list[dict[str, Any]] = field(default_factory=list)
    run_dir: str = ""
    run_key: str = ""
    store_gap: str = STORE_GAP

    def as_dict(self) -> dict[str, Any]:
        return {
            "claims_assessed": self.claims_assessed,
            "axes_by_name": {k: dict(v) for k, v in self.axes_by_name.items()},
            "substantiated": self.substantiated,
            "unknown": self.unknown,
            "producer": self.producer,
            "partial": self.partial,
            "degradations": list(self.degradations),
            "model_calls": self.model_calls,
            "usage_records": self.usage_records,
            "assessments": list(self.assessments),
            "run_dir": self.run_dir,
            "run_key": self.run_key,
            "store_gap": self.store_gap,
        }


# --------------------------------------------------------------------------- #
# source verification (reuse the existing verifier; never a second one)
# --------------------------------------------------------------------------- #


def verify_axis_source(
    source: str,
    *,
    graph: Any = None,
    target_root: str | Path | None = None,
    evidence: Sequence[Any] | Mapping[str, Any] | None = None,
) -> tuple[bool, str]:
    """Independently check one axis source.  Never raises.

    Two kinds of source are accepted:

    * ``evidence:<id>`` — the id must be present in the evidence records handed
      to the assessment (a citation, not an invention);
    * anything else — handed to
      :func:`resextract.mine.provenance.verify_provenance`, which resolves graph
      node ids and ``path#Lstart-Lend`` / ``doc:path#Heading`` references
      against the loaded graph and the real target tree.

    A file reference cannot be verified without ``target_root``; rather than
    resolve it against an unrelated root, that is reported as unverified.
    """
    if not isinstance(source, str) or not source.strip():
        return False, "empty source"
    text = source.strip()

    match = _EVIDENCE_RE.match(text)
    if match:
        wanted = match.group(1)
        index = _evidence_index(evidence)
        if not index:
            return False, f"no evidence records are available to substantiate evidence id {wanted}"
        if wanted in index:
            item = index[wanted]
            ref = _get(item, "source_ref", "url", "ref") or "?"
            kind = _get(item, "source_kind", "kind") or "evidence"
            return True, f"evidence id {wanted} present ({kind}: {ref})"
        return False, f"evidence id {wanted} does not exist in the gathered evidence"

    kind, _payload, _heading = parse_ref(text)
    if kind in ("file_lines", "doc_section") and target_root is None:
        return False, "no target_root supplied, so a file reference cannot be verified"

    verdict = verify_provenance(
        [text],
        graph=graph,
        target_root=target_root if target_root is not None else Path("."),
    )
    if not verdict.items:
        return False, "no reference to verify"
    item = verdict.items[0]
    if item.exists:
        return True, f"verified {item.kind}: {item.detail}"
    return False, f"fabricated or unresolvable reference rejected by provenance verification: {item.detail}"


def _evidence_index(evidence: Sequence[Any] | Mapping[str, Any] | None) -> dict[str, Any]:
    """Map ``str(id)`` (and source refs) to each evidence record."""
    index: dict[str, Any] = {}
    if evidence is None:
        return index
    items: Iterable[Any]
    if isinstance(evidence, Mapping):
        items = evidence.values()
    else:
        items = evidence
    for item in items:
        raw = _get(item, "evidence_id", "id")
        if raw is not None:
            index[str(raw)] = item
        ref = _get(item, "source_ref", "url")
        if ref:
            index.setdefault(str(ref), item)
    return index


# --------------------------------------------------------------------------- #
# one claim
# --------------------------------------------------------------------------- #


def assess_value(
    claim: Any,
    *,
    client: Any = None,
    evidence: Sequence[Any] | Mapping[str, Any] | None = None,
    results: Sequence[Any] | None = None,
    graph_path: str | Path | None = None,
    target_root: str | Path | None = None,
    budget: Any = None,
    producer_hint: str | None = None,
    prompt_version: str = PROMPT_VERSION,
    usage_sink: Any = None,
    checked_at: str | None = None,
) -> ValueAssessment:
    """Assess the six real-world value axes of one claim.

    With a ``client``: one strict-schema ``call_json`` whose every axis must
    carry a source; an axis without a usable source — or whose source fails
    independent verification — is downgraded to ``unknown`` with the reason
    recorded.  Without a client: a deterministic pass that substantiates only
    what the claim's own data supports.
    """
    del checked_at, prompt_version  # reserved; kept in the public signature
    cid = _claim_id(claim)
    text = _claim_text(claim)
    degradations: list[dict[str, Any]] = []

    graph = None
    if graph_path:
        graph, graph_error = _load_graph(graph_path)
        if graph_error:
            degradations.append({"claim": cid, "stage": "value", "error": graph_error})

    prov_refs = _provenance_refs(claim)
    assessment = ValueAssessment(claim_id=cid, producer="unknown", degradations=degradations)

    if client is not None:
        producer = _client_producer(client, producer_hint)
        if producer == "unknown":
            # Fail-closed: an undeclared client is never "model", and none of its
            # unattributable output may substantiate anything — so we do not even
            # spend a call on it.
            degradations.append(
                {
                    "claim": cid,
                    "stage": "value",
                    "error": (
                        "the client declared no producer (fail-closed: an undeclared "
                        "client is 'unknown', not 'model'), so its axes are treated as "
                        "non-model and none may be substantiated"
                    ),
                }
            )
            assessment.producer = "unknown"
            assessment.axes = _all_unknown(
                "the client declared no producer (fail-closed), so no axis it returns may be substantiated"
            )
            return assessment

        usage_records: list[Any] = []

        def _sink(record: Any) -> None:
            usage_records.append(record)
            if callable(usage_sink):
                usage_sink(record)

        try:
            if budget is not None:
                budget.check()
                budget.begin_call()
            payload = client.call_json(
                _value_messages(text, prov_refs, evidence, results),
                _value_schema(),
                thinking=True,
                max_tokens=VALUE_MAX_TOKENS,
                label="assess.value",
                sink=_sink,
            )
        except Exception as exc:  # noqa: BLE001 - BudgetExhausted stops the run
            if type(exc).__name__ == "BudgetExhausted":
                raise
            name = type(exc).__name__
            truncated = _is_truncation(exc)
            reason = (
                "the model returned empty content (treated as truncation: reasoning is "
                "counted inside max_tokens on this server), so no axis may be inferred"
                if truncated
                else f"the model path produced no usable value axes ({name}: {exc})"
            )
            degradations.append(
                {
                    "claim": cid,
                    "stage": "value",
                    "error": f"{name}: {exc}",
                    "truncated": truncated,
                }
            )
            assessment.model_calls = 1 if producer_is_model(producer) else 0
            assessment.usage_records = len(usage_records)
            assessment.producer = producer
            assessment.axes = _all_unknown(reason)
            return assessment

        if _payload_truncated(payload):
            reason = "the model reply was truncated (finish_reason=length with no axis content)"
            degradations.append({"claim": cid, "stage": "value", "error": reason, "truncated": True})
            assessment.model_calls = 1 if producer_is_model(producer) else 0
            assessment.usage_records = len(usage_records)
            assessment.producer = producer
            assessment.axes = _all_unknown(reason)
            return assessment

        axes = _axes_from_payload(
            payload,
            producer=producer,
            graph=graph,
            target_root=target_root,
            evidence=evidence,
            claim_id=cid,
            degradations=degradations,
        )
        assessment.producer = producer
        assessment.axes = axes
        assessment.model_calls = 1 if producer_is_model(producer) else 0
        assessment.usage_records = len(usage_records)
        return assessment

    # -- no client: deterministic pass ------------------------------------ #
    assessment.axes = _deterministic_axes(
        claim,
        prov_refs=prov_refs,
        evidence=evidence,
        results=results,
        graph=graph,
        target_root=target_root,
        claim_id=cid,
    )
    producers = {a.producer for a in assessment.axes}
    assessment.producer = (
        "fixture" if "fixture" in producers else ("replay" if "replay" in producers else "unknown")
    )
    return assessment


def _axes_from_payload(
    payload: Any,
    *,
    producer: str,
    graph: Any,
    target_root: str | Path | None,
    evidence: Sequence[Any] | Mapping[str, Any] | None,
    claim_id: int | None,
    degradations: list[dict[str, Any]],
) -> list[Axis]:
    """Turn a model payload into exactly six axes, downgrading what it cannot carry."""
    axes: list[Axis] = []
    for name in AXIS_NAMES:
        raw = getattr(payload, name, None)
        value = str(getattr(raw, "value", "") or "").strip()
        source = str(getattr(raw, "source", "") or "").strip()
        if not value or not source:
            axes.append(
                Axis(
                    name=name,
                    substantiated=False,
                    value=None,
                    source=None,
                    producer="unknown",
                    reason=(
                        "the model returned no usable source for this axis (an axis "
                        "without a verifiable source is never substantiated)"
                        if value
                        else "the model returned no value for this axis"
                    ),
                )
            )
            continue
        ok, detail = verify_axis_source(
            source, graph=graph, target_root=target_root, evidence=evidence
        )
        if not ok:
            degradations.append(
                {"claim": claim_id, "stage": "value", "axis": name, "error": detail}
            )
            axes.append(
                Axis(
                    name=name,
                    substantiated=False,
                    value=None,
                    source=None,
                    producer="unknown",
                    reason=f"the axis source was rejected ({source}): {detail}",
                )
            )
            continue
        axes.append(
            Axis(
                name=name,
                substantiated=True,
                value=value,
                source=source,
                producer=producer,
                reason=None,
            )
        )
    return axes


def _deterministic_axes(
    claim: Any,
    *,
    prov_refs: Sequence[str],
    evidence: Sequence[Any] | Mapping[str, Any] | None,
    results: Sequence[Any] | None,
    graph: Any,
    target_root: str | Path | None,
    claim_id: int | None,
) -> list[Axis]:
    """Substantiate only what the claim's own stored data supports."""
    root = target_root if target_root is not None else Path(".")
    verdict = (
        verify_provenance(list(prov_refs), graph=graph, target_root=root) if prov_refs else None
    )
    good = verdict.good if verdict is not None else []
    axes: dict[str, Axis] = {}

    # -- reproducibility: the claim's own verified provenance refs --------- #
    if good:
        ref = good[0]
        axes["reproducibility"] = Axis(
            name="reproducibility",
            substantiated=True,
            value=(
                f"a third party can re-check this claim's own reference {ref.ref} "
                f"({ref.detail}) and re-run the extractor against the same tree"
            ),
            source=ref.ref,
            producer="fixture",
        )
    else:
        detail = verdict.items[0].detail if (verdict and verdict.items) else "no provenance refs"
        axes["reproducibility"] = Axis(
            name="reproducibility",
            substantiated=False,
            reason=(
                "the claim carries no verifiable provenance reference, so how a third "
                f"party could reproduce it is unknown ({detail})"
            ),
        )

    # -- licensing: a licence string in cited material --------------------- #
    licence = _licence_from_evidence(evidence, claim_id)
    if licence is None:
        licence = _licence_from_refs(good, root)
    if licence is not None:
        token, source, where = licence
        axes["licensing"] = Axis(
            name="licensing",
            substantiated=True,
            value=f"{token} — declared in the cited material ({where})",
            source=source,
            producer="fixture",
        )
    else:
        axes["licensing"] = Axis(
            name="licensing",
            substantiated=False,
            reason=(
                "no licence string exists in the claim's own cited material or evidence, "
                "so no licence constraint can be stated"
            ),
        )

    # -- measured_delta: a measured result already in the store ------------ #
    delta = _measured_delta(results, evidence, claim_id)
    if delta is not None:
        value, source, detail = delta
        axes["measured_delta"] = Axis(
            name="measured_delta",
            substantiated=True,
            value=value,
            source=source,
            producer="fixture",
        )
        del detail
    else:
        axes["measured_delta"] = Axis(
            name="measured_delta",
            substantiated=False,
            reason=(
                "no measured result for this claim exists in the store (the evidence "
                "table is empty for it), so no quantified improvement can be quoted"
            ),
        )

    # -- the three that require judgement: never invented without a model -- #
    axes["affected_parties"] = Axis(
        name="affected_parties",
        substantiated=False,
        reason=(
            "which parties a finding matters to requires a judgement the claim's own "
            "stored data does not contain; no client was available to make it"
        ),
    )
    axes["unblocks"] = Axis(
        name="unblocks",
        substantiated=False,
        reason=(
            "what capability or decision the finding enables is not recorded in the "
            "claim's own data; no client was available to infer it"
        ),
    )
    axes["cost"] = Axis(
        name="cost",
        substantiated=False,
        reason=(
            "no compute, money or effort figure for exploiting this claim exists in "
            "the store; no client was available to estimate one"
        ),
    )
    return [axes[name] for name in AXIS_NAMES]


# --------------------------------------------------------------------------- #
# many claims
# --------------------------------------------------------------------------- #


def assess_values(
    claims: Iterable[Any],
    *,
    client: Any = None,
    evidence: Sequence[Any] | Mapping[str, Any] | None = None,
    results: Sequence[Any] | None = None,
    graph_path: str | Path | None = None,
    target_root: str | Path | None = None,
    budget: Any = None,
    out_dir: str | Path = "state/assess",
    max_claims: int | None = None,
    prompt_version: str = PROMPT_VERSION,
    producer_hint: str | None = None,
) -> ValueReport:
    """Assess many claims, isolating failures and writing deterministic artefacts.

    Writes ``VALUE.md``, ``values.jsonl`` and ``report.json`` under
    ``<out_dir>/<prompt_version>-<identity-key>/``.  Both the JSONL rows and the
    claim order are sorted, so identical inputs give byte-identical
    ``values.jsonl``.  The ``report.json`` counts match the JSONL line count
    ``x`` 6 (the six axes are always present).
    """
    started = time.monotonic()
    claim_list = list(claims)
    if max_claims is not None:
        claim_list = claim_list[: max(0, int(max_claims))]
    claim_list.sort(key=_claim_identity)

    identity_key = hashlib.sha256(
        "\n".join(_claim_identity(c) for c in claim_list).encode("utf-8")
    ).hexdigest()[:12]
    run_key = f"{prompt_version}-{identity_key}"
    run_dir = Path(out_dir) / run_key
    run_dir.mkdir(parents=True, exist_ok=True)

    report = ValueReport(run_dir=str(run_dir), run_key=run_key)
    rows: list[dict[str, Any]] = []

    for claim in claim_list:
        try:
            assessment = assess_value(
                claim,
                client=client,
                evidence=evidence,
                results=results,
                graph_path=graph_path,
                target_root=target_root,
                budget=budget,
                producer_hint=producer_hint,
                prompt_version=prompt_version,
            )
        except Exception as exc:  # noqa: BLE001 - one bad claim never kills the run
            if type(exc).__name__ == "BudgetExhausted":
                report.partial = True
                report.degradations.append(
                    {"claim": _claim_identity(claim), "stage": "budget", "error": str(exc)}
                )
                break
            report.degradations.append(
                {
                    "claim": _claim_identity(claim),
                    "stage": "value",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        row = assessment.as_dict()
        rows.append(row)
        report.assessments.append(row)
        report.claims_assessed += 1
        report.model_calls += assessment.model_calls
        report.usage_records += assessment.usage_records
        report.degradations.extend(assessment.degradations)
        for axis in assessment.axes:
            bucket = report.axes_by_name.setdefault(
                axis.name, {"substantiated": 0, "unknown": 0}
            )
            if axis.substantiated:
                bucket["substantiated"] += 1
                report.substantiated += 1
            else:
                bucket["unknown"] += 1
                report.unknown += 1

    rows.sort(key=lambda r: str(r.get("claim_id")))
    seen: set[str] = set()
    report.producer = _run_producer(report.assessments)
    del seen
    _write_outputs(run_dir, report, rows)
    (run_dir / "report.json").write_text(
        json.dumps(report.as_dict(), indent=2, sort_keys=True), "utf-8"
    )
    del started
    return report


def _write_outputs(
    run_dir: Path, report: ValueReport, rows: Sequence[Mapping[str, Any]]
) -> None:
    lines = [
        "# Real-world value axes (U4.4)",
        "",
        "An axis is either substantiated by a verifiable source or it is `unknown`.",
        "`unknown` is a result, not a failure.  Every source below was checked by",
        "`resextract.mine.provenance.verify_provenance` (or an evidence-id lookup).",
        "",
        f"- claims assessed: {report.claims_assessed}",
        f"- substantiated axes: {report.substantiated}",
        f"- unknown axes: {report.unknown}",
        f"- producer: {report.producer}",
        f"- partial: {report.partial}",
        f"- store gap: {report.store_gap}",
        "",
    ]
    for row in rows:
        lines.append(f"## claim {row.get('claim_id')} (producer={row.get('producer')})")
        lines.append("")
        for axis in row.get("axes") or []:
            if axis.get("substantiated"):
                lines.append(
                    f"- **{axis.get('name')}**: {axis.get('value')}  "
                    f"[source: {axis.get('source')}] (producer={axis.get('producer')})"
                )
            else:
                lines.append(f"- {axis.get('name')}: `unknown` — {axis.get('reason')}")
        lines.append("")
    if report.degradations:
        lines.append("## degradations")
        lines.append("")
        for entry in report.degradations:
            lines.append(f"- {json.dumps(entry, sort_keys=True)}")
        lines.append("")
    (run_dir / "VALUE.md").write_text("\n".join(lines), "utf-8")

    with (run_dir / "values.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _all_unknown(reason: str) -> list[Axis]:
    return [
        Axis(name=name, substantiated=False, producer="unknown", reason=reason)
        for name in AXIS_NAMES
    ]


def _client_producer(client: Any, hint: str | None) -> str:
    """Resolve what a client *declares* itself to be.  **Fails closed.**

    Delegates to :func:`resextract.assess.verdicts._client_producer` -- the *same*
    function object, not a mirror of it -- so the two halves of stage 5 cannot
    disagree.  The client's own declaration is authoritative there: a
    ``producer_hint`` may never *upgrade* standing, it may only be ignored or
    deny/downgrade it.  An **undeclared** client resolves to
    :data:`DEFAULT_CLIENT_PRODUCER` (``"unknown"``) -- never ``"model"`` -- so a
    real :class:`resextract.llm.OccamyClient` declares ``model`` through its own
    request-making ``producer`` property, never through a caller-asserted hint.
    """
    return _verdicts_client_producer(client, hint)


def _validate_declaration(declared: Any, source: str) -> str:
    """Return ``declared`` when it is in the shared vocabulary, else raise."""
    if isinstance(declared, str) and declared in PRODUCER_VOCAB:
        return declared
    raise ProducerDeclarationError(declared, source)


def _is_truncation(exc: Exception) -> bool:
    raw = getattr(exc, "raw_text", None)
    if isinstance(raw, str) and not raw.strip():
        return True
    text = str(getattr(exc, "last_error", "") or exc).lower()
    return "length" in text and ("empty" in text or "expecting value" in text)


def _payload_truncated(payload: Any) -> bool:
    finish = getattr(payload, "finish_reason", None)
    if finish != "length":
        return False
    for name in AXIS_NAMES:
        raw = getattr(payload, name, None)
        if str(getattr(raw, "value", "") or "").strip() or str(getattr(raw, "source", "") or "").strip():
            return False
    return True


def _value_messages(
    text: str,
    prov_refs: Sequence[str],
    evidence: Sequence[Any] | Mapping[str, Any] | None,
    results: Sequence[Any] | None,
) -> list[dict[str, str]]:
    refs = "\n".join(f"- {ref}" for ref in prov_refs) or "(none)"
    index = _evidence_index(evidence)
    ev_lines = []
    for key, item in sorted(index.items()):
        if key.isdigit():
            ev_lines.append(
                f"[evidence {key}] {_get(item, 'source_ref', 'url') or '?'}: "
                f"{str(_get(item, 'quote', 'title') or '')[:300]}"
            )
    evidence_body = "\n".join(ev_lines) or "(no evidence records)"
    result_lines = []
    for item in results or []:
        result_lines.append(json.dumps(_plain(item), sort_keys=True, default=str))
    result_body = "\n".join(result_lines) or "(no stored measured results)"
    schema_note = (
        "Reply with JSON only, one object with the six keys "
        + ", ".join(AXIS_NAMES)
        + ". Each key is an object {\"value\": string, \"source\": string}. "
        "A source must be one of: a measured result quoted from the stored results, "
        "a citation, a provenance reference (path#Lstart-Lend or a graph node id), or "
        "an evidence id written as evidence:<id>. If you cannot substantiate an axis, "
        "return empty strings for both value and source -- do NOT guess a source. "
        "An axis without a verifiable source is recorded as unknown."
    )
    return [
        {"role": "system", "content": schema_note},
        {
            "role": "user",
            "content": (
                f"Claim: {text}\n\n"
                f"The claim's own provenance references:\n{refs}\n\n"
                f"Evidence records:\n{evidence_body}\n\n"
                f"Stored measured results:\n{result_body}"
            ),
        },
    ]


def _value_schema() -> type:
    from pydantic import BaseModel, Field

    class _AxisOut(BaseModel):
        value: str = ""
        source: str = ""

    class _AxesOut(BaseModel):
        affected_parties: _AxisOut = Field(default_factory=_AxisOut)
        unblocks: _AxisOut = Field(default_factory=_AxisOut)
        measured_delta: _AxisOut = Field(default_factory=_AxisOut)
        reproducibility: _AxisOut = Field(default_factory=_AxisOut)
        cost: _AxisOut = Field(default_factory=_AxisOut)
        licensing: _AxisOut = Field(default_factory=_AxisOut)

    return _AxesOut


def _load_graph(graph_path: str | Path) -> tuple[Any, str | None]:
    try:
        path = Path(graph_path)
        if not path.is_file():
            return None, f"graph not found at {graph_path}"
        try:
            from ..kg import read_graph

            return read_graph(path), None
        except Exception:  # noqa: BLE001 - fall back to the plain lazy view
            from ..kg import Graph

            return Graph(path), None
    except Exception as exc:  # noqa: BLE001 - a broken graph verifies nothing
        return None, f"graph could not be loaded ({type(exc).__name__}: {exc})"


def _provenance_refs(claim: Any) -> list[str]:
    raw = _get(claim, "provenance_json", "provenance")
    if raw is None:
        single = _get(claim, "ref", "source_ref")
        return [str(single)] if single else []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:  # noqa: BLE001 - a non-JSON blob yields no refs
            return []
    refs: list[str] = []
    if isinstance(raw, Mapping):
        raw = [raw]
    for item in raw if isinstance(raw, (list, tuple)) else []:
        if isinstance(item, str):
            refs.append(item)
            continue
        ref = _get(item, "ref", "source_ref", "path", "node")
        if ref:
            refs.append(str(ref))
    return refs


def _licence_from_evidence(
    evidence: Sequence[Any] | Mapping[str, Any] | None, claim_id: int | None
) -> tuple[str, str, str] | None:
    index = _evidence_index(evidence)
    for key, item in sorted(index.items()):
        if not key.isdigit():
            continue
        blob = " ".join(
            str(_get(item, f) or "")
            for f in ("quote", "context", "title", "copy_path", "source_ref")
        )
        token = _licence_token(blob)
        if token:
            source = _evidence_source(item, key)
            ok, _detail = verify_axis_source(source, evidence=evidence)
            if ok:
                return token, source, f"evidence id {key}"
    return None


def _licence_from_refs(
    refs: Sequence[Any], target_root: Path | str
) -> tuple[str, str, str] | None:
    for ref in refs:
        path_text = ref.ref
        match = _SPAN_RE.match(path_text)
        if match:
            path_text = match.group("path")
        elif path_text.startswith("doc:"):
            path_text = path_text[4:].partition("#")[0]
        elif path_text.startswith("file:"):
            path_text = path_text[5:].partition("#")[0]
        else:
            continue
        real = _resolve_inside(path_text, target_root)
        if real is None or not real.is_file():
            continue
        try:
            if real.stat().st_size > 2_000_000:
                continue
            text = real.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            token = _licence_token(line, strict=True)
            if token:
                source = f"{path_text}#L{number}"
                ok, _detail = verify_axis_source(source, target_root=target_root)
                if ok:
                    return token, source, f"{path_text}:{number}"
    return None


def _licence_token(blob: str, *, strict: bool = False) -> str | None:
    for match in _LICENCE_RE.finditer(blob):
        candidate = match.group(1).strip().strip("\"',;").strip()
        for token in _LICENCE_TOKENS:
            if candidate.lower() == token.lower() or candidate.lower().startswith(
                token.lower() + " "
            ):
                return token
    if strict:
        head = blob.strip().strip("\"',;").strip()
        for token in _LICENCE_TOKENS:
            if head.lower() == token.lower() or (
                len(head) < 60 and head.lower().startswith(token.lower() + " ")
            ):
                return token
    return None


def _measured_delta(
    results: Sequence[Any] | None,
    evidence: Sequence[Any] | Mapping[str, Any] | None,
    claim_id: int | None,
) -> tuple[str, str, str] | None:
    for item in results or []:
        owner = _get(item, "claim_id")
        if owner is not None and claim_id is not None and str(owner) != str(claim_id):
            continue
        metric = _get(item, "metric", "name", "label")
        value = _get(item, "value", "delta", "measured")
        unit = _get(item, "unit", "units")
        if value in (None, "", 0) or not metric:
            continue
        source = _get(item, "source", "source_ref", "evidence")
        if not source:
            continue
        text = str(source)
        if not text.startswith("evidence:"):
            try:
                if str(source).isdigit():
                    text = f"evidence:{source}"
            except Exception:  # noqa: BLE001 - non-numeric source stays as written
                pass
        ok, detail = verify_axis_source(text, evidence=evidence)
        if not ok:
            continue
        rendered = f"{metric} = {value}{(' ' + str(unit)) if unit else ''}"
        return rendered, text, detail
    return None


def _evidence_source(item: Any, key: str) -> str:
    raw = _get(item, "evidence_id", "id")
    if raw is not None:
        return f"evidence:{raw}"
    return f"evidence:{key}"


def _claim_text(claim: Any) -> str:
    return str(_get(claim, "text") or "")


def _claim_id(claim: Any) -> int | None:
    raw = _get(claim, "claim_id", "id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _claim_identity(claim: Any) -> str:
    cid = _claim_id(claim)
    return f"claim:{cid}" if cid is not None else f"text:{_claim_text(claim)}"


def _get(obj: Any, *names: str) -> Any:
    """Read a field from a mapping, a sqlite3.Row, or an object."""
    for name in names:
        try:
            if isinstance(obj, Mapping) and name in obj:
                return obj[name]
        except Exception:  # noqa: BLE001 - a hostile mapping yields nothing
            pass
        try:
            keys = obj.keys()  # sqlite3.Row
            if name in keys:
                return obj[name]
        except Exception:  # noqa: BLE001 - not a row
            pass
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _plain(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return dict(item)
    if hasattr(item, "as_dict"):
        return dict(item.as_dict())
    if hasattr(item, "__dict__"):
        return {k: v for k, v in vars(item).items() if not k.startswith("_")}
    return {"value": str(item)}


def _resolve_inside(path_text: str, target_root: Path | str) -> Path | None:
    if not path_text:
        return None
    root = Path(os.path.realpath(str(target_root)))
    raw = Path(path_text)
    candidate = raw if raw.is_absolute() else root / raw
    real = Path(os.path.realpath(str(candidate)))
    if real == root or root in real.parents:
        return real
    return None


def _run_producer(assessments: Sequence[Mapping[str, Any]]) -> str:
    producers = {str(a.get("producer")) for a in assessments}
    for candidate in PRODUCER_VOCAB:
        if candidate in producers:
            return candidate
    return "unknown"
