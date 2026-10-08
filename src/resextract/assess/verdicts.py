"""Verdicts for the assessment stage (unit U4.1).

:func:`assess_claim` judges one claim from the evidence
:mod:`resextract.assess.evidence` gathered, and **refuses to judge** when the
evidence does not support a judgement.  The gate order is fixed and must not be
reordered:

1. **no evidence records** -> ``UNVERIFIED`` with the gather reason;
2. **every search degraded and no usable evidence** -> ``UNVERIFIED`` naming the
   engine errors SearXNG reported;
3. **with a client** -> an LLM verdict, constrained to cite evidence ids; a
   response citing none is *rejected* and falls back to
   ``UNVERIFIED("no evidence cited")``;
4. **without a client** -> a deterministic verdict: evidence whose quote shares
   the claim's key terms yields at most ``EXTENDS``, otherwise ``UNVERIFIED``.

**A replay/stub path never yields ``CONFIRMS``, and neither does an undeclared
client.**  There is no display of judgement in a replayed run: only an explicit,
in-vocabulary ``producer="model"`` declaration *from a client that genuinely
makes requests* enables a positive ``CONFIRMS``, and even then only with cited
evidence.  An undeclared client resolves to ``unknown`` -- never ``model``, and
never ``none`` -- and ``unknown`` is non-model and therefore capped at
``EXTENDS``: the absence of a declaration is not evidence of a model.

Two differently-scoped producer values are recorded, under names that cannot be
confused with each other:

* ``run_producer`` -- what actually produced this verdict's content: ``model``
  when the model path ran, ``replay`` when a non-model client ran, ``none`` when
  no client was consulted at all (``producer`` survives as a deprecated
  read-only alias of this field for older callers);
* ``client_producer`` -- what the client *declared*, validated against the
  shared ``PRODUCER_VOCAB`` (``model | replay | fixture | unknown``, identical to
  the store's ``candidates.producer`` CHECK), or ``None`` when no client verdict
  was produced.

Both are reported because a replay run must never be mistaken for model-derived
work -- and the store's ``verdicts``/``evidence`` tables have **no producer
column**, so that gap is reported rather than silently dropped.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .evidence import (
    EvidenceRecord,
    GatherResult,
    gather_evidence,
    evidence_hash,
    key_terms,
    term_ratio,
    utcnow,
)
from ..store import (
    MODEL_PRODUCER,
    PRODUCER_VOCAB,
    SchemaTooOldError,
    producer_is_model,
)

__all__ = [
    "PROMPT_VERSION",
    "VERDICT_VOCAB",
    "AssessReport",
    "Verdict",
    "assess_claim",
    "assess_claims",
]

#: Bump when the verdict prompt (or the deterministic rule) changes shape.
PROMPT_VERSION = "assess-v1"

#: The store's CHECK vocabulary; kept identical on purpose.
VERDICT_VOCAB: tuple[str, ...] = ("CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED")

_POSITIVE = frozenset({"CONFIRMS", "EXTENDS", "CONTRADICTS"})

#: The client-declaration vocabulary and the model-standing constant are NOT
#: defined here: both are **imported from** :mod:`resextract.store` (the
#: migration-3 CHECK on ``candidates.producer``) so exactly one definition exists
#: in the codebase.  ``assess.value`` imports them from the same place, and
#: ``may_back_model_claim`` below *is* ``store.producer_is_model``.
#: ``unknown`` is the honest default: a client that does not declare itself is
#: *not* assumed to be a model.

#: What an undeclared client resolves to.  Never ``"none"``: ``none`` describes
#: a *run* that consulted no client, and reusing that word here is what made the
#: two differently-scoped producer fields confusable.
DEFAULT_CLIENT_PRODUCER = "unknown"


class ProducerDeclarationError(ValueError):
    """Typed rejection of a producer declaration outside :data:`PRODUCER_VOCAB`.

    Declarations are matched **exactly** -- case-sensitive, no normalisation.
    ``"Model"``, ``"MODEL"``, ``"gpt"`` and ``""`` are all rejected rather than
    coerced: a producer is a provenance claim, and rounding a near-miss up to
    model standing would be the fail-open direction this module forbids.
    """

    def __init__(self, declared: Any, source: str) -> None:
        self.declared = declared
        self.source = source
        self.allowed = PRODUCER_VOCAB
        super().__init__(
            f"{source} declared producer {declared!r}, which is not one of "
            f"{list(PRODUCER_VOCAB)}; the declaration is rejected rather than "
            "coerced (an unrecognised producer is not a model)"
        )


#: The assess-side spelling of the single model-standing predicate.  It **is**
#: ``store.producer_is_model`` -- the same function object, not an equal copy --
#: so the gate that decides whether a ``CONFIRMS`` verdict may be published and
#: the store filters that read model-produced rows can never disagree.  (Do not
#: confuse it with ``store.may_back_model_claim``, which takes a *row*; this one
#: takes a *producer string*.)
may_back_model_claim = producer_is_model

#: Reasoning is counted *inside* ``max_tokens`` on this server, so a small cap
#: yields empty content with ``finish_reason="length"``.  Think on, and size for
#: reasoning + answer.
VERDICT_MAX_TOKENS = 2048


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Verdict:
    """One claim's judgement -- or its honest refusal to judge."""

    claim_id: int | None
    verdict: str
    rationale: str
    evidence_ids: list[int] = field(default_factory=list)
    #: what produced this verdict's content: ``model`` | ``replay`` | ``none``
    run_producer: str = "none"
    #: what the client declared (a :data:`PRODUCER_VOCAB` value), or ``None``
    #: when no client verdict was produced
    client_producer: str | None = None
    checked_at: str = ""
    #: additive observability (the store schema has nowhere to put these)
    absence_reason: str | None = None
    rejected: bool = False
    model_calls: int = 0
    replay_calls: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "verdict": self.verdict,
            "rationale": self.rationale,
            "evidence_ids": list(self.evidence_ids),
            "run_producer": self.run_producer,
            "client_producer": self.client_producer,
            # deprecated alias of ``run_producer``, kept for older consumers
            "producer": self.run_producer,
            "checked_at": self.checked_at,
            "absence_reason": self.absence_reason,
            "rejected": self.rejected,
            "model_calls": self.model_calls,
            "replay_calls": self.replay_calls,
        }

    @property
    def producer(self) -> str:
        """Deprecated alias of :attr:`run_producer` (what produced the text)."""
        return self.run_producer


@dataclass
class AssessReport:
    """Outcome of one assessment run over many claims."""

    claims_assessed: int = 0
    by_verdict: dict[str, int] = field(
        default_factory=lambda: {v: 0 for v in VERDICT_VOCAB}
    )
    evidence_rows: int = 0
    searches: int = 0
    fetches: int = 0
    degraded_searches: int = 0
    suspect_fetches: int = 0
    rejected_verdicts: int = 0
    model_calls: int = 0
    usage_records: int = 0
    #: what the run produced: ``model`` | ``replay`` | ``none``
    #: (``producer`` survives as a deprecated read-only alias)
    run_producer: str = "none"
    partial: bool = False
    degradations: list[dict[str, Any]] = field(default_factory=list)
    wall_s: float = 0.0
    #: additive
    verdicts: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    run_dir: str = ""
    run_key: str = ""
    query_sources: dict[str, int] = field(default_factory=dict)
    clean_empty_searches: int = 0
    weak_sources: int = 0
    resumed_claims: int = 0
    replay_calls: int = 0
    client_producer: str | None = None
    #: the run-scoped migration report when ``migrate_store`` copied+upgraded an
    #: under-migrated store (never an in-place write of the caller's database).
    migration: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "claims_assessed": self.claims_assessed,
            "by_verdict": dict(self.by_verdict),
            "evidence_rows": self.evidence_rows,
            "searches": self.searches,
            "fetches": self.fetches,
            "degraded_searches": self.degraded_searches,
            "suspect_fetches": self.suspect_fetches,
            "rejected_verdicts": self.rejected_verdicts,
            "model_calls": self.model_calls,
            "usage_records": self.usage_records,
            "run_producer": self.run_producer,
            "producer": self.run_producer,  # deprecated alias of run_producer
            "partial": self.partial,
            "degradations": list(self.degradations),
            "wall_s": self.wall_s,
            "verdicts": list(self.verdicts),
            "evidence": list(self.evidence),
            "run_dir": self.run_dir,
            "run_key": self.run_key,
            "query_sources": dict(self.query_sources),
            "clean_empty_searches": self.clean_empty_searches,
            "weak_sources": self.weak_sources,
            "resumed_claims": self.resumed_claims,
            "replay_calls": self.replay_calls,
            "client_producer": self.client_producer,
            "migration": self.migration,
        }

    @property
    def producer(self) -> str:
        """Deprecated alias of :attr:`run_producer`."""
        return self.run_producer


# --------------------------------------------------------------------------- #
# one claim
# --------------------------------------------------------------------------- #


def assess_claim(
    claim: Any,
    gather: GatherResult,
    *,
    client: Any = None,
    store: Any = None,
    evidence_ids: Sequence[int] | None = None,
    claim_id: int | None = None,
    producer_hint: str | None = None,
    prompt_version: str = PROMPT_VERSION,
    budget: Any = None,
    usage_sink: Any = None,
    checked_at: str | None = None,
) -> Verdict:
    """Judge ``claim`` from ``gather``; never invent a positive verdict."""
    text = _claim_text(claim)
    cid = claim_id if claim_id is not None else _claim_id(claim)
    now = checked_at or _utcnow()
    ids = list(evidence_ids) if evidence_ids is not None else None
    if ids is None and store is not None:
        ids = _persist_records(store, cid, gather.records)
    if ids is None:
        ids = []

    # -- gate 1: no evidence records ------------------------------------- #
    if not gather.records:
        degraded = _degraded_reasons(gather)
        clean = [
            r for r in gather.reasons if "clean search" in r or "no matching prior art" in r
        ]
        bits = ["no evidence: no evidence records were gathered"]
        if degraded:
            bits.append(
                f"{len(gather.degraded_searches)} search(es) were degraded, so this "
                f"absence proves nothing: {'; '.join(degraded)}"
            )
        if clean:
            bits.append(f"a clean search found no matching prior art ({clean[0]})")
        if gather.suspect_fetches:
            bits.append(
                f"{len(gather.suspect_fetches)} fetch(es) were suspect stubs and were "
                "excluded from evidence"
            )
        if not degraded and not clean and gather.reasons:
            bits.append("; ".join(gather.reasons[:3]))
        return Verdict(
            claim_id=cid,
            verdict="UNVERIFIED",
            rationale=". ".join(bits),
            evidence_ids=[],
            run_producer="none",
            checked_at=now,
            absence_reason=degraded[0] if degraded else (clean[0] if clean else None),
        )

    usable = [r for r in gather.records if not _is_weak(r)]

    # -- gate 2: every search degraded and no usable evidence ------------- #
    if gather.degraded_searches and not usable:
        degraded = _degraded_reasons(gather)
        engines = _engine_errors(gather)
        return Verdict(
            claim_id=cid,
            verdict="UNVERIFIED",
            rationale=(
                f"every search was degraded ({len(gather.degraded_searches)} of "
                f"{len(gather.searches)}) and no usable evidence was gathered; the "
                "search backend denied access, so no positive verdict is possible: "
                + "; ".join(degraded)
                + (f" -- unresponsive engines: {', '.join(engines)}" if engines else "")
            ),
            evidence_ids=[],
            run_producer="none",
            checked_at=now,
            absence_reason=degraded[0] if degraded else None,
        )

    # -- gate 3: model verdict ------------------------------------------- #
    if client is not None:
        client_producer = _client_producer(client, producer_hint)
        is_model = may_back_model_claim(client_producer)
        #: what this run produced: a model-backed call, or a non-model call.  An
        #: ``unknown`` (undeclared) client counts as non-model -- the *safe*
        #: direction: never mistaken for model-derived work.
        run_producer = MODEL_PRODUCER if is_model else "replay"
        try:
            if budget is not None:
                budget.begin_call()
            payload = client.call_json(
                _verdict_messages(text, gather, ids),
                _verdict_schema(),
                thinking=True,
                max_tokens=VERDICT_MAX_TOKENS,
                label="assess.verdict",
                **({"sink": usage_sink} if usage_sink is not None else {}),
            )
        except Exception as exc:  # noqa: BLE001 - BudgetExhausted is re-raised above
            if type(exc).__name__ == "BudgetExhausted":
                raise
            name = type(exc).__name__
            rationale = (
                f"the model path produced no usable verdict ({name}); refusing to "
                f"infer anything: {exc}"
            )
            if name == "UnparseableOutput":
                rationale = (
                    "the model path produced unparseable output and, per the sizing "
                    "rule (reasoning is counted inside max_tokens), that is treated as "
                    "truncation, not as an empty result; refusing to infer anything"
                )
            return Verdict(
                claim_id=cid,
                verdict="UNVERIFIED",
                rationale=rationale,
                evidence_ids=[],
                run_producer=run_producer,
                client_producer=client_producer,
                checked_at=now,
                absence_reason=f"model path failed: {name}",
                model_calls=1 if is_model else 0,
                replay_calls=0 if is_model else 1,
            )

        cited = _valid_citations(payload, ids)
        if not cited:
            return Verdict(
                claim_id=cid,
                verdict="UNVERIFIED",
                rationale="no evidence cited",
                evidence_ids=[],
                run_producer=run_producer,
                client_producer=client_producer,
                checked_at=now,
                absence_reason="the model verdict cited no evidence ids and was rejected",
                rejected=True,
                model_calls=1 if is_model else 0,
                replay_calls=0 if is_model else 1,
            )
        verdict = str(getattr(payload, "verdict", "UNVERIFIED")).upper()
        if verdict not in _POSITIVE:
            verdict = "UNVERIFIED"
        rationale = str(getattr(payload, "rationale", "") or "").strip()
        if verdict == "CONFIRMS" and not is_model:
            verdict = "EXTENDS"
            rationale = (
                rationale + " [capped at EXTENDS: this run was not model-produced "
                f"(client_producer={client_producer}), so it cannot assert CONFIRMS]"
            ).strip()
        return Verdict(
            claim_id=cid,
            verdict=verdict,
            rationale=rationale or "the model returned no rationale",
            evidence_ids=cited,
            run_producer=run_producer,
            client_producer=client_producer,
            checked_at=now,
            model_calls=1 if is_model else 0,
            replay_calls=0 if is_model else 1,
        )

    # -- gate 4: deterministic ------------------------------------------- #
    terms = key_terms(text)
    supporting = [r for r in usable if term_ratio(r.quote, terms) > 0]
    if supporting and ids:
        n = min(len(supporting), len(ids))
        cited = ids[:n]
        return Verdict(
            claim_id=cid,
            verdict="EXTENDS",
            rationale=(
                f"{len(supporting)} evidence record(s) share the claim's key terms "
                f"({', '.join(terms[:6])}); a deterministic replay path caps at "
                "EXTENDS and never asserts CONFIRMS"
            ),
            evidence_ids=cited,
            run_producer="none",
            checked_at=now,
        )
    if supporting and not ids:
        return Verdict(
            claim_id=cid,
            verdict="UNVERIFIED",
            rationale=(
                "evidence shares the claim's key terms but no evidence ids are "
                "available to cite, so no verdict may be recorded"
            ),
            evidence_ids=[],
            run_producer="none",
            checked_at=now,
            absence_reason="positive verdict refused: no citable evidence id",
        )
    weak = len(gather.records) - len(usable)
    return Verdict(
        claim_id=cid,
        verdict="UNVERIFIED",
        rationale=(
            "no evidence record shares the claim's key terms "
            f"({len(usable)} usable, {weak} weak), so nothing supports the claim; "
            "a replay path caps at EXTENDS and this is below it"
        ),
        evidence_ids=[],
        run_producer="none",
        checked_at=now,
        absence_reason="no evidence shares the claim's key terms",
    )


# --------------------------------------------------------------------------- #
# many claims
# --------------------------------------------------------------------------- #


def assess_claims(
    claims: Iterable[Any],
    *,
    client: Any = None,
    search: Any = None,
    fetcher: Any = None,
    store_path: str | Path | None = None,
    budget: Any = None,
    out_dir: str | Path = "state/assess",
    max_claims: int | None = None,
    prompt_version: str = PROMPT_VERSION,
    producer_hint: str | None = None,
    migrate_store: bool = False,
    max_queries: int = 3,
    max_sources: int = 3,
    clock: Any = None,
) -> AssessReport:
    """Assess many claims with per-claim isolation and honest resumability.

    Idempotency: a run is keyed by ``(claim identity, prompt_version)`` and the
    stored evidence-set hash from the previous run.  Re-running over unchanged
    inputs therefore performs **zero** searches and re-emits the stored verdicts
    and evidence ids.

    ``BudgetExhausted`` stops the run, keeps every row already produced and
    marks the report ``partial=True``.  One bad claim never kills the run --
    except :class:`~resextract.store.SchemaTooOldError`, which is a run-level
    condition and is **re-raised** rather than degraded into a silent
    ``claims_assessed == 0``.

    ``migrate_store=True`` opts in to a **run-scoped copy**: an under-migrated
    ``store_path`` is copied (the source is backed up with its sha256 recorded
    and is never written) and only the copy is migrated to v4 before any write;
    the migration report is attached to ``report.migration``.  With the default
    ``False``, an under-migrated store raises
    :class:`~resextract.store.SchemaTooOldError` naming the required migration.
    """
    from .. import store as store_mod

    started = time.monotonic()
    claim_list = list(claims)
    if max_claims is not None:
        claim_list = claim_list[: max(0, int(max_claims))]

    identity_key = hashlib.sha256(
        "\n".join(sorted(_claim_identity(c) for c in claim_list)).encode("utf-8")
    ).hexdigest()[:12]
    run_key = f"{prompt_version}-{identity_key}"
    run_dir = Path(out_dir) / run_key
    run_dir.mkdir(parents=True, exist_ok=True)

    con: sqlite3.Connection | None = None
    migration: dict[str, Any] | None = None
    if store_path is not None:
        probe = store_mod.connect(store_path)
        try:
            found_version = store_mod.schema_version(probe)
        finally:
            probe.close()
        target_path: Any = store_path
        if found_version < store_mod.SCHEMA_VERSION:
            if not migrate_store:
                # Typed, loud, at run start -- the exact replacement for the
                # obscure per-row `OperationalError: table verdicts has no column
                # named producer` that produced `claims_assessed == 0`.
                raise SchemaTooOldError(store_path, found_version)
            # An explicit, opt-in step on a **run-scoped copy**: the source is
            # backed up (sha256 recorded) and never written, and the migration
            # report travels on the report -- never a silent in-place upgrade of
            # a caller's database with no signal and no backup.
            migration = store_mod.migrate_copy(store_path)
            target_path = migration["dst"]
        con = store_mod.connect(target_path)
        store_mod.assert_writable_schema(con, target_path)

    resume_path = run_dir / "resume.json"
    resume_index: dict[str, Any] = {}
    if resume_path.exists():
        try:
            resume_index = json.loads(resume_path.read_text("utf-8"))
        except Exception:  # noqa: BLE001 - a corrupt index just means no resume
            resume_index = {}

    report = AssessReport(run_dir=str(run_dir), run_key=run_key)
    report.client_producer = _client_producer(client, producer_hint) if client is not None else None
    report.migration = migration
    evidence_jsonl: list[dict[str, Any]] = []
    verdict_jsonl: list[dict[str, Any]] = []
    gathered: list[dict[str, Any]] = []

    for claim in claim_list:
        identity = _claim_identity(claim)
        prior = resume_index.get(identity)
        try:
            if prior and prior.get("prompt_version") == prompt_version:
                self_prior = prior.get("verdict") or {}
                report.verdicts.append(self_prior)
                report.evidence.extend(prior.get("evidence") or [])
                report.claims_assessed += 1
                report.resumed_claims += 1
                v = str(self_prior.get("verdict") or "UNVERIFIED")
                report.by_verdict[v] = report.by_verdict.get(v, 0) + 1
                if self_prior.get("rejected"):
                    report.rejected_verdicts += 1
                report.model_calls += int(self_prior.get("model_calls") or 0)
                report.replay_calls += int(self_prior.get("replay_calls") or 0)
                verdict_jsonl.append(self_prior)
                evidence_jsonl.extend(prior.get("evidence") or [])
                gathered.append(
                    {
                        "claim": prior.get("claim"),
                        "claim_id": prior.get("claim_id"),
                        "records": list(prior.get("evidence") or []),
                        "reasons": list(prior.get("reasons") or []),
                        "degraded_searches": [],
                        "suspect_fetches": [],
                        "evidence_ids": list(prior.get("evidence_ids") or []),
                        "resumed": True,
                    }
                )
                continue

            if budget is not None:
                budget.check()

            gather: GatherResult = gather_evidence(
                claim,
                search=search,
                fetcher=fetcher,
                client=client,
                budget=budget,
                max_queries=max_queries,
                max_sources=max_sources,
                clock=clock,
            )
            report.searches += len(gather.searches)
            report.degraded_searches += len(gather.degraded_searches)
            report.suspect_fetches += len(gather.suspect_fetches)
            report.fetches += gather.fetch_attempts
            report.clean_empty_searches += sum(
                1 for s in gather.searches if s.get("absence_is_meaningful")
            )
            report.weak_sources += len(gather.weak_sources)
            report.query_sources[gather.query_source] = (
                report.query_sources.get(gather.query_source, 0) + 1
            )

            cid = _claim_id(claim)
            ids: list[int] = []
            if con is not None:
                ids = _persist_records(con, cid, gather.records)
            verdict = assess_claim(
                claim,
                gather,
                client=client,
                store=None,
                evidence_ids=ids,
                claim_id=cid,
                producer_hint=producer_hint,
                prompt_version=prompt_version,
                budget=budget,
            )
            if con is not None:
                # Provenance is recorded, not defaulted to 'unknown' (U2.6
                # enforcement): the verdict's own producer, and the model id
                # **only** when the producer really is ``model``.
                db_producer = _verdict_db_producer(verdict)
                store_mod.insert_verdict(
                    con,
                    claim_id=cid,
                    verdict=verdict.verdict,
                    rationale=verdict.rationale,
                    evidence_ids_json=verdict.evidence_ids,
                    checked_at=verdict.checked_at,
                    producer=db_producer,
                    model=(
                        getattr(client, "model", None)
                        if producer_is_model(db_producer)
                        else None
                    ),
                )
                con.commit()

            vdict = verdict.as_dict()
            report.verdicts.append(vdict)
            report.evidence.extend(r.as_dict() for r in gather.records)
            report.claims_assessed += 1
            report.by_verdict[verdict.verdict] = report.by_verdict.get(verdict.verdict, 0) + 1
            report.rejected_verdicts += 1 if verdict.rejected else 0
            report.model_calls += verdict.model_calls
            report.replay_calls += verdict.replay_calls
            verdict_jsonl.append(vdict)
            evidence_jsonl.extend(r.as_dict() for r in gather.records)
            gathered.append(
                {
                    "claim": _claim_text(claim),
                    "claim_id": cid,
                    "records": [r.as_dict() for r in gather.records],
                    "reasons": list(gather.reasons),
                    "degraded_searches": list(gather.degraded_searches),
                    "suspect_fetches": list(gather.suspect_fetches),
                    "evidence_ids": list(ids),
                }
            )
            resume_index[identity] = {
                "prompt_version": prompt_version,
                "evidence_set_hash": evidence_hash(gather.records),
                "evidence_ids": list(ids),
                "evidence": [r.as_dict() for r in gather.records],
                "verdict": vdict,
                "claim": _claim_text(claim),
                "claim_id": cid,
                "reasons": list(gather.reasons),
            }
            resume_path.write_text(json.dumps(resume_index, indent=2, sort_keys=True), "utf-8")
        except Exception as exc:  # noqa: BLE001 - isolate one bad claim
            if isinstance(exc, SchemaTooOldError):
                # An under-migrated store is a *run-level* condition, not a
                # per-claim failure: re-raise it so it is never degraded into a
                # silent "claims_assessed == 0".  (assert_writable_schema already
                # caught this before the loop; this covers a mid-run change.)
                if con is not None:
                    con.close()
                raise
            if type(exc).__name__ == "BudgetExhausted":
                report.partial = True
                report.degradations.append(
                    {"claim": identity, "stage": "budget", "error": str(exc)}
                )
                break
            report.degradations.append(
                {"claim": identity, "stage": "assess", "error": f"{type(exc).__name__}: {exc}"}
            )
            continue

    report.evidence_rows = len(report.evidence)
    _write_outputs(run_dir, report, gathered, evidence_jsonl, verdict_jsonl)
    if con is not None:
        con.close()
    report.wall_s = round(time.monotonic() - started, 3)
    report.run_producer = _run_producer(report)
    (run_dir / "report.json").write_text(
        json.dumps(report.as_dict(), indent=2, sort_keys=True), "utf-8"
    )
    return report


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _claim_text(claim: Any) -> str:
    if isinstance(claim, Mapping):
        return str(claim.get("text") or "")
    return str(getattr(claim, "text", "") or "")


def _claim_id(claim: Any) -> int | None:
    raw = claim.get("claim_id", claim.get("id")) if isinstance(claim, Mapping) else getattr(
        claim, "claim_id", None
    )
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _claim_identity(claim: Any) -> str:
    cid = _claim_id(claim)
    return f"claim:{cid}" if cid is not None else f"text:{_claim_text(claim)}"


def _is_weak(record: EvidenceRecord) -> bool:
    return str(record.context or "").startswith("weak source")


def _degraded_reasons(gather: GatherResult) -> list[str]:
    out: list[str] = []
    for entry in gather.degraded_searches:
        reason = str(entry.get("reason") or "unknown")
        engines = entry.get("unresponsive_engines") or []
        if engines:
            reason = f"{reason} [unresponsive: {', '.join(str(e) for e in engines)}]"
        if reason not in out:
            out.append(reason)
    return out


def _engine_errors(gather: GatherResult) -> list[str]:
    out: list[str] = []
    for entry in gather.degraded_searches:
        for e in entry.get("unresponsive_engines") or []:
            if str(e) not in out:
                out.append(str(e))
    return out


def _persist_records(store: Any, claim_id: int | None, records: Sequence[EvidenceRecord]) -> list[int]:
    from .. import store as store_mod

    ids: list[int] = []
    for rec in records:
        ids.append(
            store_mod.insert_evidence(
                store,
                claim_id=claim_id,
                source_kind=rec.source_kind,
                source_ref=rec.source_ref,
                sha256=rec.sha256,
                quote=rec.quote,
                context=rec.context,
                retrieved_at=rec.retrieved_at,
                copy_path=rec.copy_path,
            )
        )
    return ids


def _client_producer(client: Any, hint: str | None) -> str:
    """Resolve what a client *declares* itself to be.  **Fails closed.**

    Returns one of :data:`PRODUCER_VOCAB`.  An undeclared client resolves to
    ``unknown`` -- *not* ``model``.  Omission is not a provenance claim, and the
    only value that grants model standing is exactly ``model``.

    The **client's own declaration is authoritative**: ``producer_hint`` may
    never *upgrade* standing (a ``producer_hint="model"`` over a client that
    declared ``replay``/``fixture``/nothing is **ignored**), it may only be
    ignored or used to deny/downgrade -- because a hint is caller-asserted, and
    routing model standing through it would bypass the request-making invariant.

    A ``producer`` attribute on the client (or on any client it wraps) *is* a
    declaration and is validated exactly against :data:`PRODUCER_VOCAB`; an
    out-of-vocabulary hint or attribute raises :class:`ProducerDeclarationError`
    rather than being coerced.  ``is_replay``/``is_stub`` remain boolean
    shorthands for a ``replay`` declaration.
    """
    declared = _client_declaration(client)
    if hint is None:
        return declared
    proposed = _validate_declaration(hint, "producer_hint")
    if producer_is_model(proposed) and not producer_is_model(declared):
        # Never upgrade: the hint wanted model standing the client did not declare.
        return declared
    return proposed


def _client_declaration(client: Any) -> str:
    """Walk a (possibly wrapped) client for its **own** declaration; fail closed."""
    seen: set[int] = set()
    node: Any = client
    while node is not None and id(node) not in seen:
        seen.add(id(node))
        declared = getattr(node, "producer", None)
        if declared is not None:
            return _validate_declaration(declared, f"{type(node).__name__}.producer")
        if getattr(node, "is_replay", False) or getattr(node, "is_stub", False):
            return "replay"
        node = getattr(node, "client", None)
    return DEFAULT_CLIENT_PRODUCER


def _validate_declaration(declared: Any, source: str) -> str:
    """Return ``declared`` when it is in :data:`PRODUCER_VOCAB`, else raise.

    Case-sensitive and exact on purpose: ``"Model"``, ``"MODEL"`` and ``""`` are
    rejected, not normalised -- a near-miss must not be rounded up to model
    standing.
    """
    if isinstance(declared, str) and declared in PRODUCER_VOCAB:
        return declared
    raise ProducerDeclarationError(declared, source)


def _verdict_messages(text: str, gather: GatherResult, ids: Sequence[int]) -> list[dict[str, str]]:
    lines = []
    for i, rec in zip(ids, gather.records):
        lines.append(
            f"[evidence {i}] {rec.source_ref} (page_date={rec.page_date or 'unknown'}, "
            f"sha256={rec.sha256[:16]}...)\nquote: {rec.quote}"
        )
    body = "\n\n".join(lines) if lines else "(no evidence)"
    return [
        {
            "role": "system",
            "content": (
                "You assess one technical claim against outside evidence. Reply with "
                "JSON only. Your verdict must be one of CONFIRMS, EXTENDS, CONTRADICTS, "
                "UNVERIFIED. You MUST cite at least one evidence id in evidence_ids when "
                "you do not answer UNVERIFIED. Never claim novelty from an absent or "
                "broken search."
            ),
        },
        {"role": "user", "content": f"Claim: {text}\n\nEvidence:\n{body}"},
    ]


def _verdict_schema() -> type:
    from typing import Literal

    from pydantic import BaseModel, Field

    class _VerdictOut(BaseModel):
        verdict: Literal["CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED"]
        rationale: str
        evidence_ids: list[int] = Field(default_factory=list)

    return _VerdictOut


def _valid_citations(payload: Any, ids: Sequence[int]) -> list[int]:
    valid = {int(i) for i in ids}
    cited: list[int] = []
    for raw in list(getattr(payload, "evidence_ids", []) or []):
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value in valid and value not in cited:
            cited.append(value)
    return cited


def _run_producer(report: AssessReport) -> str:
    """What the *run* produced: ``model`` | ``replay`` | ``none``.

    Never conflate this with :func:`_client_producer` (what the client
    *declared*): an ``unknown`` client counts as a non-model call here, so such a
    run is reported as ``replay`` -- the safe direction, never as ``model``.
    """
    if report.model_calls:
        return MODEL_PRODUCER
    if report.replay_calls:
        return "replay"
    return "none"


def _verdict_db_producer(verdict: Verdict) -> str:
    """The store's producer value for a verdict -- derived, never assumed.

    ``model`` only for a verdict a model really produced; otherwise the client's
    own honest declaration (``replay``/``fixture``/``unknown``), or ``fixture``
    when no client was consulted at all (the deterministic pass derives its
    verdict from stored data).  This is the writer half of the v4 ``producer``
    column: defaulting every row to ``'unknown'`` is the provenance loss that
    column exists to prevent.
    """
    if producer_is_model(verdict.run_producer):
        return MODEL_PRODUCER
    declared = verdict.client_producer
    if isinstance(declared, str) and declared in PRODUCER_VOCAB:
        return "replay" if producer_is_model(declared) else declared
    return "fixture"


def _write_outputs(
    run_dir: Path,
    report: AssessReport,
    gathered: Sequence[Mapping[str, Any]],
    evidence_jsonl: Sequence[Mapping[str, Any]],
    verdict_jsonl: Sequence[Mapping[str, Any]],
) -> None:
    lines = [
        "# Evidence (U4.1)",
        "",
        "Every row below carries the URL, the page date, the content sha256 and a",
        "verbatim quote.  Suspect fetches are excluded; weak sources are labelled.",
        "",
    ]
    verdicts_by_claim = {str(v.get("claim_id")): v for v in report.verdicts}
    for item in gathered:
        lines.append(f"## claim {item.get('claim_id')}: {item.get('claim')}")
        lines.append("")
        v = verdicts_by_claim.get(str(item.get("claim_id")), {})
        lines.append(f"- verdict: **{v.get('verdict', 'UNVERIFIED')}** (run_producer={v.get('run_producer')}, client_producer={v.get('client_producer')})")
        for reason in item.get("reasons") or []:
            lines.append(f"- reason: {reason}")
        for rec in item.get("records") or []:
            lines.append(
                f"- [{rec.get('source_kind')}] {rec.get('source_ref')} "
                f"(page_date={rec.get('page_date') or 'unknown'}, sha256={rec.get('sha256')})"
            )
            lines.append(f"  - copy_path: {rec.get('copy_path')}")
            lines.append(f"  - context: {rec.get('context')}")
            lines.append(f"  - quote: {rec.get('quote')}")
        if not item.get("records"):
            lines.append("- no evidence produced for this claim")
        lines.append("")
    (run_dir / "EVIDENCE.md").write_text("\n".join(lines), "utf-8")

    vlines = ["# Verdicts (U4.1)", ""]
    for v in report.verdicts:
        vlines.append(
            f"- claim {v.get('claim_id')}: **{v.get('verdict')}** "
            f"(run_producer={v.get('run_producer')}, client_producer={v.get('client_producer')}, "
            f"evidence_ids={v.get('evidence_ids')})"
        )
        vlines.append(f"  - rationale: {v.get('rationale')}")
        if v.get("absence_reason"):
            vlines.append(f"  - absence_reason: {v.get('absence_reason')}")
    vlines.append("")
    (run_dir / "VERDICTS.md").write_text("\n".join(vlines), "utf-8")

    with (run_dir / "evidence.jsonl").open("w", encoding="utf-8") as fh:
        for row in evidence_jsonl:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    with (run_dir / "verdicts.jsonl").open("w", encoding="utf-8") as fh:
        for row in verdict_jsonl:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
