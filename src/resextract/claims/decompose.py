"""Claim decomposition: mined candidate -> atomic, falsifiable, verified claims.

This is the missing link between the miner (which produces *candidates*) and
assessment (which attaches *evidence* and *verdicts* to claims).  With no
claims, ``split.py`` falls back to candidate provenance, assessment has nothing
to attach to, every lane refuses ``paper``, and no docket can reach ``ready``.

Policy (mirrors the miner, and stated here because it is this module's honesty
mechanism):

* **Zero verified provenance references => reject, never store.**  Every claim's
  references are re-checked with :func:`resextract.mine.provenance.verify_provenance`
  against the loaded graph and the real target tree.  A plausible path with a
  fabricated span does not rescue a claim: the span must be inside the real
  file.  This module never re-implements that verifier; it imports it.
* **An empty ``settled_by`` is not a claim.**  Every claim must name the concrete
  evidence that would settle it (a measurement, a citation, a reproduction
  command, a counter-example).  Missing => rejected with the reason recorded.
* **A fresh claim is ``unverified``.**  Nothing here implies external
  confirmation; the initial state is the honest one and is the value
  ``resextract.docket.materialize`` already defaults to.
* **A replay/injected client is never recorded as model-derived.**  A run driven
  by a stub carries ``producer="replay"`` (or ``fixture``) and ``model_calls==0``.

Vocabularies
------------
The store declares **no** CHECK constraint on ``claims.kind`` or
``claims.verification_state`` (read from the live DDL: both are plain ``TEXT``),
so this module defines both:

* :data:`CLAIM_KINDS` -- ``measured``, ``behavioural``, ``architectural``,
  ``comparative``, ``negative``, ``definitional``.  Assessment and the docket
  only ever print ``kind`` as free text; these six keep a claim's *epistemic
  type* explicit (a measurement is not an architectural assertion, and a
  negative result -- "no test covers X" -- is not a definition).
* :data:`INITIAL_VERIFICATION_STATE` = ``"unverified"`` -- the value
  ``resextract.docket.materialize`` already treats as the default and the only
  honest state for a claim no external source has confirmed.

Metering: :attr:`ClaimReport.model_calls` counts **real outbound requests** (it
is forced to 0 for any producer other than ``"model"``), separately from
:attr:`ClaimReport.usage_records`, which counts usage-sink rows handed back by
the client.  Truncation (``finish_reason="length"`` with empty content) is a
recorded degradation, never "zero claims found".
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from .. import store as store_mod
from ..kg import read_graph
from ..llm import Budget, BudgetExhausted, UnparseableOutput
from ..mine.provenance import verify_provenance

__all__ = [
    "CLAIM_KINDS",
    "INITIAL_VERIFICATION_STATE",
    "Claim",
    "ClaimReport",
    "decompose_candidates",
    "normalise_text",
]

# --------------------------------------------------------------------------- #
# vocabularies (see module docstring: the store declares neither)
# --------------------------------------------------------------------------- #

CLAIM_KINDS: tuple[str, ...] = (
    "measured",
    "behavioural",
    "architectural",
    "comparative",
    "negative",
    "definitional",
)

#: The honest initial state for a freshly decomposed claim.
INITIAL_VERIFICATION_STATE = "unverified"

#: ``max_tokens`` default.  This server counts *reasoning* inside the cap, so a
#: small cap returns empty content with ``finish_reason="length"`` -- the cap is
#: deliberately sized for reasoning + answer.
DECOMPOSE_MAX_TOKENS = 4096

_ClaimKind = Literal[
    "measured", "behavioural", "architectural", "comparative", "negative", "definitional"
]

PROMPT_VERSIONS: tuple[str, ...] = ("v1",)


# --------------------------------------------------------------------------- #
# strict response schema
# --------------------------------------------------------------------------- #


class _ClaimOut(BaseModel):
    """One decomposed claim as the model must return it (extra keys rejected)."""

    model_config = ConfigDict(extra="forbid")

    text: str
    kind: _ClaimKind
    settled_by: str
    provenance_refs: list[str] = Field(default_factory=list)
    confidence: float | None = None


class _Decomposition(BaseModel):
    """The strict top-level object ``call_json`` validates."""

    model_config = ConfigDict(extra="forbid")

    claims: list[_ClaimOut] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #


@dataclass
class Claim:
    """One atomic, falsifiable claim with verified provenance."""

    candidate_id: int | None
    kind: str
    text: str
    provenance_refs: list[str]
    settled_by: str
    confidence: float | None
    verification_state: str = INITIAL_VERIFICATION_STATE
    #: full provenance verdict items (verified *and* failed), so a fabrication
    #: stays visible in what was stored rather than being silently dropped.
    provenance: list[dict[str, Any]] = field(default_factory=list)
    claim_id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "claim_id": self.claim_id,
            "kind": self.kind,
            "text": self.text,
            "provenance_refs": list(self.provenance_refs),
            "provenance": list(self.provenance),
            "settled_by": self.settled_by,
            "confidence": self.confidence,
            "verification_state": self.verification_state,
        }


_CLAIM_FIELDS = (
    "candidate_id",
    "claim_id",
    "kind",
    "text",
    "provenance_refs",
    "provenance",
    "settled_by",
    "confidence",
    "verification_state",
)


@dataclass
class ClaimReport:
    """Outcome of one decomposition run."""

    claims: list[Claim] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    deduped: int = 0
    model_calls: int = 0
    usage_records: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    wall_s: float = 0.0
    partial: bool = False
    degradations: list[dict[str, Any]] = field(default_factory=list)
    producer: str = "unknown"
    # additive (the card fixes the required fields; these make resumability
    # observable without changing any of them)
    resumed: bool = False
    run_key: str = ""
    run_dir: str = ""
    calls_attempted: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "claims": [c.as_dict() for c in self.claims],
            "rejected": list(self.rejected),
            "deduped": self.deduped,
            "model_calls": self.model_calls,
            "usage_records": self.usage_records,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "wall_s": round(self.wall_s, 3),
            "partial": self.partial,
            "degradations": list(self.degradations),
            "producer": self.producer,
            "resumed": self.resumed,
            "run_key": self.run_key,
            "run_dir": self.run_dir,
            "calls_attempted": self.calls_attempted,
        }


# --------------------------------------------------------------------------- #
# small pure helpers
# --------------------------------------------------------------------------- #

_WS_RE = re.compile(r"\s+")
_SENTENCE_BREAK_RE = re.compile(r"[.!?]\s+[A-Z0-9]")


def normalise_text(text: str) -> str:
    """Normalise for cross-candidate dedupe (case, whitespace, trailing stop)."""
    return _WS_RE.sub(" ", (text or "").strip().lower()).rstrip(" .;:!?")


def _field(obj: Any, name: str, default: Any = "") -> Any:
    if isinstance(obj, Mapping):
        value = obj.get(name, default)
    else:
        value = getattr(obj, name, default)
    return default if value is None else value


def _candidate_id(candidate: Any, index: int) -> int | None:
    raw = _field(candidate, "id", None)
    if raw is None:
        raw = _field(candidate, "candidate_id", None)
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _candidate_refs(candidate: Any) -> list[str]:
    """Every provenance ref cited by the candidate.

    Accepts a :class:`resextract.mine.candidates.Candidate` (``provenance_refs``)
    or a store row (``provenance_json`` = list of provenance dicts); refs whose
    recorded ``exists`` flag is explicitly false are dropped, so the model is
    only ever offered refs the miner already checked.
    """
    refs: list[str] = []
    direct = _field(candidate, "provenance_refs", None)
    if direct:
        refs = [str(r) for r in direct if isinstance(r, str) and r.strip()]
    else:
        raw = _field(candidate, "provenance_json", None)
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (ValueError, TypeError):
                raw = []
        if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes, Mapping)):
            for item in raw:
                if isinstance(item, Mapping) and item.get("exists") is False:
                    continue
                ref = item.get("ref") if isinstance(item, Mapping) else item
                if isinstance(ref, str) and ref.strip():
                    refs.append(ref)
    seen: set[str] = set()
    out: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _graph_nodes(candidate: Any) -> list[str]:
    raw = _field(candidate, "graph_nodes", None)
    if not raw:
        raw = _field(candidate, "graph_nodes_json", None)
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raw = []
    return [str(x) for x in raw] if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes, Mapping)) else []


def _confidence(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _atomic_reason(text: str) -> str:
    """Why ``text`` is not one atomic, falsifiable statement ("" when it is)."""
    stripped = (text or "").strip()
    if not stripped:
        return "empty text: no assertion"
    if len(stripped) > 400:
        return f"not atomic: {len(stripped)} chars (>400) - split into separate claims"
    if _SENTENCE_BREAK_RE.search(stripped):
        return "not atomic: more than one sentence - one assertion per claim"
    return ""


def _producer_of(client: Any) -> str:
    """Honest producer identity for ``client``.

    An explicit ``producer`` attribute wins.  The real clients are recognised by
    type name; anything else is an injected/replay double and is **never**
    recorded as model-derived.
    """
    declared = getattr(client, "producer", None)
    if isinstance(declared, str) and declared.strip():
        return declared.strip().lower()
    if type(client).__name__ in ("OccamyClient", "SyncOccamyClient"):
        return "model"
    return "replay"


def _is_truncation(exc: BaseException) -> bool:
    """Whether ``exc`` is this server's empty-content/``finish_reason=length`` reply."""
    if getattr(exc, "finish_reason", None) == "length":
        return True
    if isinstance(exc, UnparseableOutput):
        last = (exc.last_error or "").lower()
        if not (getattr(exc, "raw_text", "") or "").strip():
            return True
        if "finish_reason" in last and "length" in last:
            return True
        if last.startswith("length") or "truncat" in last:
            return True
    return False


def _usage_token(record: Any, name: str) -> int:
    for source in (
        getattr(record, "usage", None),
        record,
        getattr(record, "raw_usage", None),
    ):
        if source is None:
            continue
        value = source.get(name) if isinstance(source, Mapping) else getattr(source, name, None)
        if value:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return 0


def _candidate_identity(candidate: Any, index: int) -> dict[str, Any]:
    return {
        "id": _candidate_id(candidate, index),
        "index": index,
        "title": str(_field(candidate, "title", "")),
        "refs": _candidate_refs(candidate),
    }


def _run_key(
    identities: Sequence[Mapping[str, Any]],
    prompt_version: str,
    producer: str,
    model: str | None,
    max_claims: int,
) -> str:
    blob = json.dumps(
        {
            "prompt_version": prompt_version,
            "producer": producer,
            "model": model,
            "max_claims": max_claims,
            "candidates": list(identities),
        },
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# prompt
# --------------------------------------------------------------------------- #

_SYSTEM = (
    "You decompose ONE mined research candidate into atomic, falsifiable claims.\n"
    "Rules:\n"
    "1. One assertion per claim. Never a paragraph, never two facts joined by 'and'.\n"
    "2. text must be checkable: a reader with the repository can mark it true or false.\n"
    "3. settled_by is REQUIRED and non-empty: the concrete evidence that would settle\n"
    "   the claim - a measurement, a citation, a reproduction command, a counter-example.\n"
    "4. provenance_refs must be copied verbatim from the candidate's provenance menu.\n"
    "   A claim whose refs cannot be checked is worthless and will be rejected.\n"
    "5. Do not invent line numbers, node ids or files.\n"
    f"Allowed kind values: {', '.join(CLAIM_KINDS)}.\n"
    "Return JSON only."
)


def _messages(
    candidate: Any,
    refs: Sequence[str],
    *,
    max_claims: int,
    prompt_version: str,
) -> list[dict[str, Any]]:
    menu = "\n".join(f"- {ref}" for ref in refs) if refs else "(no verified refs available)"
    payload = {
        "kind": str(_field(candidate, "kind", "")),
        "title": str(_field(candidate, "title", "")),
        "summary": str(_field(candidate, "summary", "")),
        "evidence_quote": str(_field(candidate, "evidence_quote", "")),
        "rationale": str(_field(candidate, "rationale", "")),
        "graph_nodes": _graph_nodes(candidate),
        "provenance_menu": list(refs),
    }
    user = (
        f"prompt_version={prompt_version}\n"
        f"Produce at most {max_claims} claims for this candidate.\n\n"
        "CANDIDATE\n"
        f"{json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)}\n\n"
        "PROVENANCE MENU (copy refs verbatim)\n"
        f"{menu}\n"
    )
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user},
    ]


# --------------------------------------------------------------------------- #
# persistence helpers (the store has no accessor for these reads; see docstring)
# --------------------------------------------------------------------------- #


def _existing_claim_texts(con: sqlite3.Connection) -> set[str]:
    """Normalised texts already stored, so a re-run never duplicates a claim.

    ``store.py`` exposes ``get_claim`` (by id) but no "all claims" reader, and it
    is owned by a sibling unit right now, so this module runs the SELECT itself
    against the same DB path.  Recorded as ``store_gap`` in the handoff.
    """
    try:
        rows = con.execute('SELECT "text" FROM claims').fetchall()
    except sqlite3.OperationalError:
        return set()
    return {normalise_text(r[0] or "") for r in rows}


def _candidate_ids_in_store(con: sqlite3.Connection) -> set[int]:
    try:
        return {int(r[0]) for r in con.execute("SELECT id FROM candidates").fetchall()}
    except sqlite3.OperationalError:
        return set()


# --------------------------------------------------------------------------- #
# output artifacts
# --------------------------------------------------------------------------- #


def _write_artifacts(report: ClaimReport, run_dir: Path, *, prompt_version: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(report.claims, key=lambda c: (c.candidate_id or -1, normalise_text(c.text)))
    with (run_dir / "claims.jsonl").open("w", encoding="utf-8") as handle:
        for claim in ordered:
            handle.write(json.dumps(claim.as_dict(), sort_keys=True, ensure_ascii=False) + "\n")

    lines = [
        "# Claim decomposition",
        "",
        f"- prompt_version: `{prompt_version}`",
        f"- producer: `{report.producer}`",
        f"- run_key: `{report.run_key}`",
        f"- model_calls: {report.model_calls}  usage_records: {report.usage_records}",
        f"- partial: {str(report.partial).lower()}  resumed: {str(report.resumed).lower()}",
        f"- claims: {len(report.claims)}  rejected: {len(report.rejected)}  deduped: {report.deduped}",
        "",
    ]
    if report.producer != "model":
        lines += [
            f"> Model path UNVERIFIED: this run was produced by `{report.producer}` "
            "(no live model call). These claims must not back a model-derived "
            "publication claim until real mining + decomposition run.",
            "",
        ]
    lines += ["## claims (sorted, deterministic)", ""]
    for claim in ordered:
        refs = ", ".join(f"`{r}`" for r in claim.provenance_refs) or "(none)"
        lines += [
            f"### c{claim.candidate_id}: {claim.text}",
            "",
            f"- kind: `{claim.kind}`  state: `{claim.verification_state}`  confidence: {claim.confidence}",
            f"- provenance: {refs}",
            f"- settled_by: {claim.settled_by}",
            "",
        ]
    lines += ["## rejected", ""]
    for item in report.rejected:
        lines.append(f"- `{item.get('reason', '')}` -- {item.get('text', '')}")
    lines.append("")
    (run_dir / "CLAIMS.md").write_text("\n".join(lines), encoding="utf-8")

    payload = report.as_dict()
    payload["status"] = "partial" if report.partial else "complete"
    payload["prompt_version"] = prompt_version
    (run_dir / "report.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load_resume(run_dir: Path, run_key: str) -> ClaimReport | None:
    report_path = run_dir / "report.json"
    if not report_path.is_file():
        return None
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if data.get("run_key") != run_key or data.get("status") != "complete":
        return None
    claims: list[Claim] = []
    jsonl = run_dir / "claims.jsonl"
    if jsonl.is_file():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            claims.append(Claim(**{k: raw.get(k) for k in _CLAIM_FIELDS if k in raw}))
    return ClaimReport(
        claims=claims,
        rejected=list(data.get("rejected") or []),
        deduped=int(data.get("deduped") or 0),
        model_calls=0,
        usage_records=0,
        prompt_tokens=0,
        completion_tokens=0,
        reasoning_tokens=0,
        wall_s=0.0,
        partial=False,
        degradations=list(data.get("degradations") or [])
        + [{"kind": "resumed", "detail": f"run key {run_key[:12]} already complete: zero model calls"}],
        producer=str(data.get("producer") or "unknown"),
        resumed=True,
        run_key=run_key,
        run_dir=str(run_dir),
        calls_attempted=0,
    )


# --------------------------------------------------------------------------- #
# main entry point
# --------------------------------------------------------------------------- #


def decompose_candidates(
    candidates: Iterable[Any],
    *,
    client: Any,
    graph_path: str | Path,
    target_root: str | Path,
    store_path: str | Path,
    out_dir: str | Path = "state/claims",
    max_claims_per_candidate: int = 6,
    budget_tokens: int | None = None,
    prompt_version: str = "v1",
) -> ClaimReport:
    """Decompose ``candidates`` into atomic, provenance-verified claims.

    Per candidate the model is called once through a **strict** schema
    (``thinking=True``, ``max_tokens`` sized for reasoning + answer).  Isolation,
    honesty and resumability:

    * one candidate's :class:`~resextract.llm.UnparseableOutput`, truncation,
      schema failure or client error is a recorded degradation and the run
      continues with the next candidate;
    * :class:`~resextract.llm.BudgetExhausted` stops the run, keeps everything
      already persisted, and reports ``partial=True``;
    * a claim with zero independently verified refs is **rejected and never
      stored** (the miner's policy, applied to claims); an empty ``settled_by``
      is rejected for the same reason;
    * the run key covers ``(prompt_version, candidate identities, producer,
      model, max_claims)``; a second run with the same key makes **zero** model
      calls and reports ``resumed``.

    Persistence uses ``store.insert_claim``; artifacts land in
    ``<out_dir>/<prompt_version>-<producer>-<run_key[:12]>/`` as ``CLAIMS.md``,
    ``claims.jsonl`` and ``report.json``, all deterministically sorted.
    """
    started = time.monotonic()
    cand_list = list(candidates)
    producer = _producer_of(client)
    model = getattr(client, "model", None)
    identities = [_candidate_identity(c, i) for i, c in enumerate(cand_list)]
    run_key = _run_key(identities, prompt_version, producer, model, max_claims_per_candidate)
    run_dir = Path(out_dir) / f"{prompt_version}-{producer}-{run_key[:12]}"

    resumed = _load_resume(run_dir, run_key)
    if resumed is not None:
        return resumed

    report = ClaimReport(producer=producer, run_key=run_key, run_dir=str(run_dir))
    graph = None
    try:
        graph = read_graph(graph_path)
    except Exception as exc:  # noqa: BLE001 - an unreadable graph verifies nothing
        report.degradations.append(
            {"kind": "graph_unreadable", "detail": f"{type(exc).__name__}: {exc}"}
        )

    store_file = Path(store_path)
    if not store_file.exists():
        store_mod.init_db(store_file)
    con = store_mod.connect(store_file)
    try:
        known_ids = _candidate_ids_in_store(con)
        seen = _existing_claim_texts(con)
        budget = Budget(max_tokens=budget_tokens) if budget_tokens is not None else None
        usage_records: list[Any] = []

        def sink(record: Any) -> None:
            usage_records.append(record)

        for index, candidate in enumerate(cand_list):
            try:
                if budget is not None:
                    budget.check()
            except BudgetExhausted as exc:
                report.partial = True
                report.degradations.append(
                    {"kind": "budget_exhausted", "detail": f"{exc} (local budget)"}
                )
                break

            candidate_id = _candidate_id(candidate, index)
            refs = _candidate_refs(candidate)
            messages = _messages(
                candidate, refs, max_claims=max_claims_per_candidate, prompt_version=prompt_version
            )
            report.calls_attempted += 1
            try:
                if producer == "model":
                    report.model_calls += 1
                result = client.call_json(
                    messages,
                    _Decomposition,
                    thinking=True,
                    max_tokens=DECOMPOSE_MAX_TOKENS,
                    temperature=0.0,
                    label="claims.decompose",
                    sink=sink,
                )
            except BudgetExhausted as exc:
                report.partial = True
                report.degradations.append(
                    {
                        "kind": "budget_exhausted",
                        "detail": f"{exc}",
                        "candidate_id": candidate_id,
                    }
                )
                break
            except UnparseableOutput as exc:
                kind = "truncation" if _is_truncation(exc) else "unparseable_output"
                report.degradations.append(
                    {
                        "kind": kind,
                        "candidate_id": candidate_id,
                        "detail": (
                            "finish_reason=length with empty content: max_tokens consumed by "
                            "reasoning (this is truncation, NOT zero claims)"
                            if kind == "truncation"
                            else str(exc.last_error or exc)
                        ),
                    }
                )
                continue
            except Exception as exc:  # noqa: BLE001 - one candidate must not kill the run
                report.degradations.append(
                    {
                        "kind": "client_error",
                        "candidate_id": candidate_id,
                        "detail": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue

            tokens = sum(
                _usage_token(r, "prompt_tokens")
                + _usage_token(r, "completion_tokens")
                + _usage_token(r, "reasoning_tokens")
                for r in usage_records
            )
            if budget is not None:
                try:
                    budget.charge(max(0, tokens - budget.tokens_used))
                except BudgetExhausted as exc:
                    report.partial = True
                    report.degradations.append({"kind": "budget_exhausted", "detail": str(exc)})
                    break

            items = list(getattr(result, "claims", None) or [])
            for item in items[:max_claims_per_candidate]:
                text = str(getattr(item, "text", "") or "")
                kind = str(getattr(item, "kind", "") or "")
                settled_by = str(getattr(item, "settled_by", "") or "")
                claim_refs = [str(r) for r in (getattr(item, "provenance_refs", None) or [])]

                # guard B: an empty settled_by is not a claim
                if not settled_by.strip():
                    report.rejected.append(
                        {
                            "candidate_id": candidate_id,
                            "text": text,
                            "reason": "empty settled_by: no statement of what evidence would settle it",
                        }
                    )
                    continue
                atomic = _atomic_reason(text)
                if atomic:
                    report.rejected.append(
                        {"candidate_id": candidate_id, "text": text, "reason": atomic}
                    )
                    continue
                if kind not in CLAIM_KINDS:
                    report.rejected.append(
                        {
                            "candidate_id": candidate_id,
                            "text": text,
                            "reason": f"kind {kind!r} not in vocabulary {CLAIM_KINDS}",
                        }
                    )
                    continue

                verdict = verify_provenance(claim_refs, graph=graph, target_root=target_root)
                # guard A: zero verified refs => rejected, never stored
                if verdict.verified == 0:
                    failed = "; ".join(f"{p.ref} ({p.detail})" for p in verdict.bad) or "no refs cited"
                    report.rejected.append(
                        {
                            "candidate_id": candidate_id,
                            "text": text,
                            "reason": f"zero verified provenance refs: {failed}",
                            "provenance": verdict.as_dict(),
                        }
                    )
                    continue

                norm = normalise_text(text)
                if norm in seen:
                    report.deduped += 1
                    continue
                seen.add(norm)

                store_candidate_id = candidate_id if candidate_id in known_ids else None
                claim = Claim(
                    candidate_id=store_candidate_id,
                    kind=kind,
                    text=text.strip(),
                    provenance_refs=[p.ref for p in verdict.good],
                    settled_by=settled_by.strip(),
                    confidence=_confidence(getattr(item, "confidence", None)),
                    verification_state=INITIAL_VERIFICATION_STATE,
                    provenance=[p.as_dict() for p in verdict.items],
                )
                claim.claim_id = store_mod.insert_claim(
                    con,
                    candidate_id=store_candidate_id,
                    kind=claim.kind,
                    text=claim.text,
                    provenance_json=claim.provenance,
                    verification_state=claim.verification_state,
                    confidence=claim.confidence,
                )
                con.commit()
                report.claims.append(claim)

        report.usage_records = len(usage_records)
        report.prompt_tokens = sum(_usage_token(r, "prompt_tokens") for r in usage_records)
        report.completion_tokens = sum(_usage_token(r, "completion_tokens") for r in usage_records)
        report.reasoning_tokens = sum(_usage_token(r, "reasoning_tokens") for r in usage_records)
    finally:
        con.close()

    report.wall_s = time.monotonic() - started
    _write_artifacts(report, run_dir, prompt_version=prompt_version)
    return report
