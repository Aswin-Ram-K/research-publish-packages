"""``resextract run`` — the single command that chains the pipeline.

This module orchestrates the *existing* units (doctor, kg/staging, mine,
claims, lanes, docket/materialize, refresh) into one bounded run and, above
all, **reports honestly what could not run**.  The model endpoint is currently
down; a naive orchestrator would either crash or silently skip the model
stages and claim success — the worst outcome, because it would emit a
"successful" run whose findings were never generated.  Instead a stage that
cannot run is ``blocked`` with its reason and the observed endpoint status, and
the exit code reflects it.

Exit-code contract (deterministic, see :func:`exit_code_for`):

* ``0`` every planned stage ran and nothing degraded;
* ``1`` completed *with degradations* — blocked model stages, a target HEAD
  that moved under the run (``window_sealed=False``), a replay-produced run,
  a non-quiescent target, or a failed optional stage;
* ``2`` a **hard** dependency is down or a preflight gate failed (target
  unresolvable, ``read_only`` not declared, policy ``assert_present``
  violations, store schema stale, a core doctor leg other than the model
  endpoint) — **no stage runs**;
* ``3`` nothing was runnable (every selected stage was blocked/skipped), e.g.
  a budget-exhausted run.

The **model endpoint is deliberately not a preflight-fatal core leg**.  Doctor
classes Occamy as core, but this orchestrator has an honest blocked path for a
missing model, so its absence is a *degradation* (blocked model stages, exit
1), not a refusal to start (exit 2).  The same needs-based rule applies to every
other core leg: a leg a *selected* stage actually invokes (graphify for
``graph``/``staging``/``refresh``, the docling bridge for ``staging``, …) is
fatal when down, while a leg no selected stage invokes (SearXNG, when no stage
performs a web search) is a recorded degradation — a run is never refused for a
dependency it would not have used, and never silently ignores one either.

Two invariants this module will not break:

1. **Nothing is written into the target.**  Every artifact lands under the
   workspace (``state/run/<slug>/``), graphify gets ``--out`` inside it, and
   the *authoritative* store ``state/state.sqlite`` is opened **read-only**: all
   stage writes go to a run-scoped SQLite copy made with the backup API.
2. **A run is never reported sealed when it was not.**  ``window_sealed`` is
   true only when the target was quiescent at the start *and* HEAD was
   identical when re-read after the last stage.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from . import doctor, store

__all__ = [
    "EXIT_DEGRADED",
    "EXIT_HARD_DOWN",
    "EXIT_NOTHING_RUNNABLE",
    "EXIT_OK",
    "MODEL_STAGES",
    "STAGE_ORDER",
    "Preflight",
    "RunContext",
    "RunReport",
    "StageResult",
    "exit_code_for",
    "run_pipeline",
]

# -- exit codes -------------------------------------------------------------- #

EXIT_OK = 0
EXIT_DEGRADED = 1
EXIT_HARD_DOWN = 2
EXIT_NOTHING_RUNNABLE = 3

#: Stage order for a full run.  ``assess`` is batch 4 and has no implementation
#: yet, but it is a *model-dependent* stage, so it takes part in the producer
#: gate and is reported blocked (never silently omitted).
STAGE_ORDER: tuple[str, ...] = (
    "graph",
    "staging",
    "mine",
    "claims",
    "assess",
    "lanes",
    "materialize",
    "refresh",
)

#: Stages that cannot run without the model endpoint.
MODEL_STAGES: tuple[str, ...] = ("mine", "claims", "assess")

STAGE_STATUSES = frozenset({"ok", "blocked", "skipped", "degraded", "failed"})

#: Bounds that keep a run from wandering (documented, not accidental).
CAP_POLICY_FILES = 50_000
STAGING_MAX_FILES = 200
STAGING_MAX_BYTES = 16 * 1024 * 1024
STAGING_MAX_NORMALIZE = 50
GRAPH_TIMEOUT_S = 900.0
GRAPH_TOKEN_BUDGET = 1500
REFUND_WINDOW_DEFAULT_S = 5.0

_ENDPOINT_LEG_HINTS = ("occamy",)
#: Only an explicit ``http <code>`` in doctor's detail is an HTTP status.  A bare
#: ``Errno 111`` (connection refused) is NOT a status code: it means no HTTP
#: response at all, which is reported as ``000``.
_HTTP_RE = re.compile(r"http\s*(\d{3})", re.IGNORECASE)

#: Which selected stages actually *invoke* a doctor leg.  A core leg that no
#: selected stage needs is reported as a degradation (the run continues, exit
#: 1); a core leg a selected stage needs is a fatal preflight gate (exit 2, no
#: stage runs).  An unknown leg is assumed needed — the conservative default.
LEG_STAGE_NEEDS: dict[str, frozenset[str]] = {
    "occamy": frozenset(MODEL_STAGES),
    "graphify": frozenset({"graph", "staging", "refresh"}),
    "docling bridge": frozenset({"staging"}),
    "renderers": frozenset({"materialize"}),
    "crawl bridge": frozenset({"materialize"}),
    "searxng": frozenset(),  # no stage of this pipeline performs a web search
    "dashboard port": frozenset(),  # `serve` owns the port, not `run`
}


def _leg_needs(name: str, selected: Sequence[str]) -> frozenset[str]:
    """The selected stages that will invoke *name* (empty ⇒ not needed)."""
    lowered = str(name).strip().lower()
    for key, needs in LEG_STAGE_NEEDS.items():
        if key in lowered:
            return needs & frozenset(selected)
    return frozenset(selected)  # unknown core leg: assume it is needed


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# -- records ----------------------------------------------------------------- #


@dataclass
class StageResult:
    """One stage's outcome.  ``status`` is one of :data:`STAGE_STATUSES`."""

    name: str
    status: str
    reason: str = ""
    duration_s: float = 0.0
    counts: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in STAGE_STATUSES:  # pragma: no cover - programmer error
            raise ValueError(f"invalid stage status {self.status!r}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "reason": self.reason,
            "duration_s": round(float(self.duration_s), 3),
            "counts": dict(self.counts),
            "artifacts": list(self.artifacts),
        }

    #: alias, so callers that expect ``to_dict`` (the CLI formatters) work.
    to_dict = as_dict


@dataclass
class RunReport:
    """The whole run: the stage table, the seal and the exit code."""

    target: str
    started_at: str = ""
    finished_at: str = ""
    exit_code: int = EXIT_OK
    window_sealed: bool = False
    head_before: str | None = None
    head_after: str | None = None
    stages: list[StageResult] = field(default_factory=list)
    degradations: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    # -- extras (all optional; the report stays renderable without them) ----- #
    target_root: str = ""
    dry_run: bool = False
    preflight: dict[str, Any] = field(default_factory=dict)
    producer_gate: dict[str, Any] = field(default_factory=dict)
    writer_signal: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)
    started_monotonic: float = 0.0
    finished_monotonic: float = 0.0

    @property
    def stage_table(self) -> list[dict[str, Any]]:
        return [s.as_dict() for s in self.stages]

    def stage(self, name: str) -> StageResult | None:
        for s in self.stages:
            if s.name == name:
                return s
        return None

    @property
    def ok(self) -> bool:
        """Derived from ``exit_code`` (the single source of truth)."""
        return int(self.exit_code) == EXIT_OK

    @property
    def status(self) -> str:
        """Derived from ``exit_code`` via :func:`status_for` — never a second verdict."""
        return status_for(self.exit_code)

    def as_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "target_root": self.target_root,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": int(self.exit_code),
            "ok": self.ok,
            "status": self.status,
            "dry_run": bool(self.dry_run),
            "window_sealed": bool(self.window_sealed),
            "head_before": self.head_before,
            "head_after": self.head_after,
            "stages": self.stage_table,
            "degradations": list(self.degradations),
            "artifacts": list(self.artifacts),
            "preflight": dict(self.preflight),
            "producer_gate": dict(self.producer_gate),
            "writer_signal": self.writer_signal,
            "notes": list(self.notes),
            "duration_s": round(float(self.finished_monotonic - self.started_monotonic), 3),
        }

    to_dict = as_dict


@dataclass
class Preflight:
    """The hard gates, evaluated before any stage is allowed to run."""

    ok: bool = False
    failures: list[str] = field(default_factory=list)
    hard_core_down: list[str] = field(default_factory=list)
    degradable_core_down: list[str] = field(default_factory=list)
    #: Core legs the doctor classified ``state="slow"``: reachable (the cheap
    #: liveness check answered) but over their per-leg bound.  Reported here,
    #: never listed as DOWN; a slow leg no selected stage needs is a degradation.
    core_slow: list[str] = field(default_factory=list)
    endpoint_ok: bool = False
    endpoint_status: str = "unknown"
    endpoint_detail: str = ""
    target_root: str = ""
    read_only: bool = False
    registration: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 0
    schema_expected: int = store.SCHEMA_VERSION
    policy_source: str = ""
    policy_violations: list[str] = field(default_factory=list)
    policy_admitted: int = 0
    head_before: str | None = None
    quiescent: bool | None = None
    writer_signal: dict[str, Any] | None = None
    degradations: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "failures": list(self.failures),
            "hard_core_down": list(self.hard_core_down),
            "degradable_core_down": list(self.degradable_core_down),
            "core_slow": list(self.core_slow),
            "endpoint_ok": bool(self.endpoint_ok),
            "endpoint_status": self.endpoint_status,
            "target_root": self.target_root,
            "read_only": bool(self.read_only),
            "registration": dict(self.registration),
            "schema_version": int(self.schema_version),
            "schema_expected": int(self.schema_expected),
            "policy_source": self.policy_source,
            "policy_violations": list(self.policy_violations),
            "policy_admitted": int(self.policy_admitted),
            "head_before": self.head_before,
            "quiescent": self.quiescent,
        }


@dataclass
class RunContext:
    """Mutable run state shared by the stage implementations."""

    target_slug: str
    target_root: Path
    run_dir: Path
    store_path: Path
    db_path: Path
    con: Any = None
    dry_run: bool = False
    allow_active: bool = False
    allow_replay: bool = False
    window_s: float = REFUND_WINDOW_DEFAULT_S
    graph_path: Path | None = None
    #: reuse candidates that were found but rejected as unusable, with reasons
    #: (populated by ``_reuse_candidate``; reported by the build branch).
    graph_rejected: list[dict[str, str]] = field(default_factory=list)
    #: the accepted graph's own provenance, filled by ``_reuse_candidate``
    #: (reported by the graph stage's reuse branch).
    graph_provenance: dict[str, Any] = field(default_factory=dict)
    #: the target HEAD this run observed (``report.head_before``); provenance
    #: is compared against it.  ``None`` ⇒ HEAD unreadable ⇒ "unverified".
    target_head: str | None = None
    #: opt-in refusal of a provably stale graph.  Absent (False) the default
    #: is report-only reuse — never a silent, expensive rebuild.
    require_fresh_graph: bool = False
    #: where the *expected* graph digests live: ``<config_dir>/graph_pin.toml``,
    #: committed, outside ``state/`` and outside the artifact it pins.  The
    #: path is on the context so ``_reuse_candidate`` (one decision, plan and
    #: run) resolves the same pin for both callers.
    config_dir: str = "config"
    #: opt-in override of the digest-mismatch refusal.  Absent (False) a graph
    #: whose bytes do not match its committed pin is **unusable**: not reused,
    #: reported loudly, kept on disk.
    allow_graph_digest_mismatch: bool = False
    staging_dir: Path | None = None
    docket_root: Path | None = None
    claims_dir: Path | None = None
    mine_dir: Path | None = None
    endpoint_ok: bool = False
    endpoint_status: str = "unknown"
    client: Any = None
    client_reason: str = ""
    all_candidates: list[dict[str, Any]] = field(default_factory=list)
    model_candidates: list[dict[str, Any]] = field(default_factory=list)
    producer_counts: dict[str, int] = field(default_factory=dict)
    lanes: list[Any] = field(default_factory=list)
    classifications: dict[str, Any] = field(default_factory=dict)
    lane_ids: list[int] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    degradations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claimed_paths: list[str] = field(default_factory=list)

    # -- shared helpers ------------------------------------------------------ #

    def gate_reason(self, stage: str) -> str:
        """The honest reason a model stage is blocked (endpoint status first)."""
        status = self.endpoint_status
        producers = ", ".join(
            f"{k}={v}" for k, v in sorted(self.producer_counts.items())
        ) or "none"
        return (
            f"model endpoint DOWN (http {status}) — producer gate: "
            f"{len(self.model_candidates)} model-produced candidate(s) "
            f"(store producers: {producers}); {stage} cannot run without the model"
        )

    def record(self, *paths: Any) -> None:
        for p in paths:
            if p is None:
                continue
            text = str(p)
            if text and text not in self.artifacts:
                self.artifacts.append(text)


# -- exit-code mapping ------------------------------------------------------- #


def _ran_anything(stages: Sequence[StageResult]) -> bool:
    return any(s.status in ("ok", "degraded") for s in stages)


def exit_code_for(
    *,
    preflight_failed: bool = False,
    stages: Sequence[StageResult] = (),
    degradations: Sequence[str] = (),
    dry_run: bool = False,
) -> int:
    """Map a run's state to its exit code — the contract, in one place.

    ``2`` preflight failure > ``3`` nothing runnable > ``1`` degradations > ``0``.
    A *successful* dry run returns ``0``: nothing failed, the plan was produced.
    """
    if preflight_failed:
        return EXIT_HARD_DOWN
    if dry_run:
        return EXIT_OK
    if not stages or not _ran_anything(stages):
        return EXIT_NOTHING_RUNNABLE
    if degradations:
        return EXIT_DEGRADED
    return EXIT_OK


#: The status word for each exit code.  One table, one source of truth: the
#: report's ``ok``/``status`` are *derived* from ``exit_code``, never computed
#: a second time, so they cannot disagree with it.
EXIT_STATUS: dict[int, str] = {
    EXIT_OK: "ok",
    EXIT_DEGRADED: "degraded",
    EXIT_HARD_DOWN: "hard_down",
    EXIT_NOTHING_RUNNABLE: "nothing_runnable",
}


def status_for(exit_code: int) -> str:
    """Status word for an exit code — a pure lookup, never a re-derived verdict."""
    return EXIT_STATUS.get(int(exit_code), "unknown")


# -- preflight --------------------------------------------------------------- #


def _doctor_report() -> dict[str, Any]:
    """The core/optional dependency probe.  Overridable in tests."""
    return doctor.run_doctor()


def _is_endpoint_leg(name: str) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in _ENDPOINT_LEG_HINTS)


def _endpoint_leg(report: Mapping[str, Any]) -> dict[str, Any] | None:
    for leg in report.get("legs", []) or []:
        if _is_endpoint_leg(str(leg.get("leg", ""))):
            return dict(leg)
    return None


def _http_status(detail: str, ok: bool) -> str:
    match = _HTTP_RE.search(str(detail or ""))
    if match:
        return match.group(1)
    return "200" if ok else "000"


def _read_only_status(slug: str, root: Path, *, config_dir: str = "config") -> dict[str, Any]:
    """Where the target is registered, and whether it declares ``read_only``."""
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - py3.10 fallback
        import tomli as tomllib  # type: ignore[no-redef]

    cfg = Path(config_dir) / "targets.toml"
    resolved = str(Path(root).resolve())
    if cfg.is_file():
        try:
            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - an unreadable config is reported
            return {"source": str(cfg), "error": f"unreadable: {exc}", "read_only": None}
        for key, block in (data.get("targets") or {}).items():
            if not isinstance(block, dict):
                continue
            try:
                block_path = str(Path(str(block.get("path", ""))).resolve())
            except Exception:  # noqa: BLE001
                block_path = ""
            if str(key) == slug or str(block.get("slug", "")) == slug or block_path == resolved:
                return {
                    "source": str(cfg),
                    "slug": str(key),
                    "read_only": bool(block.get("read_only", False)),
                    "path": block.get("path", ""),
                }
    return {"source": None, "slug": slug, "read_only": None}


def _resolve_target(slug: str, con: Any, *, config_dir: str = "config") -> str | None:
    """Resolve a slug to a directory using the materialize resolver (no edits)."""
    from .docket import materialize as mat

    return mat.resolve_target_root(slug, con=con, config_dir=config_dir)


def _open_readonly(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _copy_store(src: Path, dest: Path) -> None:
    """Run-scoped working copy of the authoritative store (never written to).

    The source is WAL, and the backup API copies the database *header* — which
    records the WAL write-version — so a naive copy is itself a WAL database and
    requires ``-wal``/``-shm`` companions for as long as it is open.  Any
    connection a stage leaves open (or a killed process) leaves those sidecars
    behind.  Switching the fresh copy to a rollback journal makes it
    self-contained: one file, no sidecars, nothing to lose on a kill.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    source = _open_readonly(src)
    target = sqlite3.connect(str(dest))
    try:
        source.backup(target)
        target.commit()
        target.execute("PRAGMA journal_mode=DELETE").fetchone()
        target.commit()
    finally:
        target.close()
        source.close()


def _finalize_store(ctx: RunContext) -> None:
    """Leave the run-scoped copy clean and self-contained.

    Only *stale* sidecars are ever removed: ``-wal``/``-shm`` are deleted only
    when the copy no longer reports WAL mode, so nothing a live database needs
    for correctness is removed.  If the copy really is WAL, it is checkpointed
    and its companions are kept, with a note saying why.
    """
    if ctx.dry_run or not ctx.db_path.exists():
        return
    try:
        con = sqlite3.connect(str(ctx.db_path))
        try:
            mode = str(con.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            if mode == "wal":  # genuinely WAL: checkpoint, keep the companions
                con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                ctx.notes.append(
                    "run-scoped store copy is WAL; -wal/-shm kept (required for "
                    "correctness)"
                )
                return
        finally:
            con.close()
        removed = []
        for suffix in ("-wal", "-shm"):
            side = Path(str(ctx.db_path) + suffix)
            if side.exists():
                side.unlink()
                removed.append(side.name)
        if removed:
            ctx.notes.append(
                "removed stale run-scoped store sidecars (copy is not WAL): "
                + ", ".join(removed)
            )
    except Exception as exc:  # noqa: BLE001 - finalisation is best effort, reported
        ctx.notes.append(f"run-scoped store copy could not be finalised: {exc}")


def _preflight(
    ctx: RunContext,
    *,
    doctor_report: Mapping[str, Any] | None,
    real_db: Path,
    selected: Sequence[str] = STAGE_ORDER,
    config_dir: str = "config",
) -> Preflight:
    pf = Preflight()
    pf.target_root = str(ctx.target_root)

    # 1. the authoritative store must exist and be at the current schema version.
    if not real_db.exists():
        pf.failures.append(f"store missing: {real_db}")
    else:
        try:
            ro = _open_readonly(real_db)
            try:
                pf.schema_version = int(store.schema_version(ro))
            finally:
                ro.close()
            if pf.schema_version != int(store.SCHEMA_VERSION):
                pf.failures.append(
                    f"store schema v{pf.schema_version} is not current "
                    f"(v{store.SCHEMA_VERSION}); refusing to run"
                )
        except Exception as exc:  # noqa: BLE001 - an unreadable store is fatal
            pf.failures.append(f"store unreadable at {real_db}: {exc}")

    # 2. read-only registration.
    reg = _read_only_status(ctx.target_slug, ctx.target_root, config_dir=config_dir)
    pf.registration = reg
    if reg.get("read_only") is True:
        pf.read_only = True
    elif reg.get("read_only") is False:
        pf.failures.append(
            f"target {ctx.target_slug!r} is registered read_only=false; refusing to run"
        )
    else:
        pf.failures.append(
            f"target {ctx.target_slug!r} does not declare read_only in "
            f"{reg.get('source') or 'config/targets.toml'}; refusing to run"
        )

    # 3. doctor's core legs.  The model endpoint is degradable, not fatal.
    report = doctor_report if doctor_report is not None else _doctor_report()
    endpoint = _endpoint_leg(report)
    if endpoint is not None:
        detail = str(endpoint.get("detail", "") or "")
        pf.endpoint_ok = bool(endpoint.get("ok"))
        pf.endpoint_status = _http_status(detail, pf.endpoint_ok)
        pf.endpoint_detail = detail
        if str(endpoint.get("state", "") or "").lower() == doctor.SLOW:
            # reachable but over its bound: same blocked-model-stages outcome,
            # honest label -- it is not DOWN.
            pf.core_slow.append("Occamy (model endpoint)")
            pf.degradations.append(
                f"core leg Occamy (model endpoint) is SLOW (reachable but slow, not "
                f"down): {detail or 'no detail'}; model stages will be reported blocked"
            )
        elif not pf.endpoint_ok:
            pf.hard_core_down.append("Occamy (model endpoint)")
            pf.degradations.append(
                f"core leg Occamy (model endpoint) is DOWN: http {pf.endpoint_status} "
                f"— {detail or 'no detail'}; model stages will be reported blocked"
            )
    else:
        pf.endpoint_status = "unknown"
        pf.degradations.append(
            "doctor reported no Occamy leg: endpoint status unknown; model stages "
            "will be reported blocked"
        )
    for leg in report.get("legs", []) or []:
        if leg.get("class") != doctor.CORE:
            continue
        # ``state`` is authoritative when the doctor set it: ``slow`` means
        # reachable-but-over-bound, which is NOT down (U0.22's classification).
        state = str(leg.get("state", "") or "").lower() or (
            "up" if leg.get("ok") else "down"
        )
        if state == "up":
            continue
        if _is_endpoint_leg(str(leg.get("leg", ""))):
            continue
        name = str(leg.get("leg", "?"))
        detail = str(leg.get("detail", "") or "")
        needed = _leg_needs(name, selected)
        if state == doctor.SLOW:
            pf.core_slow.append(name)
            if needed:
                # a selected stage would invoke it: still the pre-U0.25 hard
                # gate (exit 2), but named SLOW, not DOWN.
                pf.hard_core_down.append(name)
                pf.failures.append(
                    f"core dependency slow: {name} (needed by "
                    f"{', '.join(sorted(needed))}) — {detail}"
                )
            else:
                pf.degradations.append(
                    f"core leg {name} is SLOW (reachable but slow, not down) — "
                    f"{detail}; no selected stage invokes it, so this run continues "
                    "(reported, never silently ignored)"
                )
        elif needed:
            pf.hard_core_down.append(name)
            pf.failures.append(
                f"core dependency down: {name} (needed by "
                f"{', '.join(sorted(needed))}) — {detail}"
            )
        else:
            pf.degradable_core_down.append(name)
            pf.degradations.append(
                f"core leg {name} is DOWN — {detail}; no selected stage invokes it, "
                "so this run continues (reported, never silently ignored)"
            )

    # 4. the policy audit's assert_present violations must be empty.
    policy = None
    try:
        from .refresh.writer import policy_for_target

        policy = policy_for_target(ctx.target_root)
    except Exception as exc:  # noqa: BLE001 - a broken policy loader is a degradation
        pf.degradations.append(f"policy loader failed: {exc}")
    if policy is None:
        pf.degradations.append(
            "no TargetPolicy configured for this target: assert_present audit not run"
        )
    else:
        from .kg.policy import policy_audit

        pf.policy_source = str(getattr(policy, "config_path", "") or pf.registration.get("source") or "")
        audit = policy_audit(str(ctx.target_root), policy, cap_files=CAP_POLICY_FILES)
        pf.policy_violations = list(getattr(audit, "violations", []) or [])
        pf.policy_admitted = len(getattr(audit, "admitted", {}) or {})
        if pf.policy_violations:
            pf.failures.append(
                f"policy assert_present violations ({len(pf.policy_violations)}): "
                + "; ".join(pf.policy_violations[:3])
            )

    pf.ok = not pf.failures
    return pf


def _observe_window(ctx: RunContext, pf: Preflight) -> None:
    """Record the writer signal at the start of the sealed window."""
    if ctx.dry_run:
        pf.quiescent = None
        pf.degradations.append("dry run: sealed window not observed")
        return
    try:
        from .refresh.writer import TargetBusyError, assert_quiescent

        signal = assert_quiescent(
            ctx.target_root, window_s=ctx.window_s, allow_active=ctx.allow_active
        )
        pf.writer_signal = signal.as_dict()
        pf.quiescent = bool(signal.quiescent)
    except TargetBusyError as exc:
        pf.quiescent = False
        signal = getattr(exc, "signal", None)
        pf.writer_signal = signal.as_dict() if signal is not None else {"verdict": "busy"}
        pf.degradations.append(
            f"target is NOT quiescent at the start of the run (writer detected): {exc}"
        )
    except Exception as exc:  # noqa: BLE001 - measurement failure must not be silent
        pf.quiescent = None
        pf.degradations.append(f"quiescence could not be measured: {exc}")


def _read_head(target_root: Path) -> str | None:
    from .refresh.staleness import read_target_state

    try:
        return read_target_state(target_root).head_sha
    except Exception:  # noqa: BLE001 - a HEAD we cannot read is reported as unknown
        return None


# -- stage implementations --------------------------------------------------- #


def _graph_candidates(ctx: RunContext) -> list[Path]:
    return [
        Path("state") / "kg" / ctx.target_slug / "graph.json",
        Path("state") / "kg" / ctx.target_slug / "graphify-out" / "graph.json",
        Path("state") / "kg" / ctx.target_slug / "graphify-out" / "combined-graph.json",
    ]


def _graph_unusable_reason(path: Path) -> str | None:
    """Why ``path`` cannot serve as a reusable code-only graph, or ``None``.

    "Usable" is defined by what the graph stage and its downstream readers
    actually consume — not by a bare ``is_file()``:

    * **one JSON object.**  ``read_graph`` builds its lazy typed view over that
      object and ``graph_stats`` locates the ``"nodes"``/``"links"`` arrays by
      name.  A 0-byte file, non-JSON bytes, ``{}`` or a non-object document
      (list/scalar) is therefore unusable.
    * **``nodes`` is a non-empty array of JSON objects.**  Every consumer
      iterates it (``graph_stats.nodes``, ``Graph.nodes``, the miner's graph
      context, the lanes' community attachment) and every consumer reads each
      element as a mapping.  Zero nodes means the whole run would keep going on
      an empty graph while the graph stage reported success; and a *non-empty
      list of non-objects* (``nodes: [100000 ints]``, the U8.11 item-1 hole)
      parsed fine, answered "non-empty", and reached ``graph_stats`` as **0
      nodes** with ``mode=reuse, status="ok"`` — the ok-with-zero-nodes
      signature the non-emptiness check alone did not close.  **Every** element
      is checked, not a sample: the parse that produced this list is already
      O(len(nodes)), so an ``isinstance`` walk is strictly cheaper than the parse
      and cannot be gamed by a valid-looking prefix.
    * **``links`` is present and an array.**  ``Graph.links`` and
      ``graph_stats.edges`` read it and Graphify always emits it.  An empty
      array is fine (a graph with nodes but no edges is still a graph); a
      missing or non-array key means a truncated/corrupt write.
    * **``communities`` is deliberately NOT required.**  The authoritative graph
      in this repo has no top-level ``communities`` key at all, and both
      ``graph_stats`` and the lanes' ``from_store(rows, graph)`` tolerate its
      absence — requiring it would reject the genuine artifact.

    A candidate that parses with a non-zero node count can still be
    *semantically* wrong (stale, built from another repo, truncated mid-file
    yet still valid JSON).  That is not detectable here: it is the documented
    residual of this check.
    """
    try:
        with path.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as exc:  # noqa: BLE001 - unreadable/unparseable is a reason, not a crash
        return f"{type(exc).__name__}: {exc}"
    if not isinstance(doc, dict):
        return f"top-level JSON is {type(doc).__name__}, not an object"
    nodes = doc.get("nodes")
    if not isinstance(nodes, list):
        return f"'nodes' is {type(nodes).__name__}, not an array"
    if not nodes:
        return "'nodes' is an empty array (zero nodes)"
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            return (
                f"'nodes' element {index} is {type(node).__name__}, not an object "
                f"(every node must be a JSON object; all {len(nodes)} elements checked)"
            )
    links = doc.get("links")
    if not isinstance(links, list):
        return f"'links' is {type(links).__name__ if links is not None else 'missing'}, not an array"
    return None


def _note_unusable(
    ctx: RunContext, path: Path, reason: str, *, label: str = "unusable"
) -> None:
    """Record a rejected candidate on the context so the report can name it."""
    entry = {"path": str(path), "reason": reason}
    if entry not in ctx.graph_rejected:
        ctx.graph_rejected.append(entry)
    note = f"graph: ignoring {label} reuse candidate {path}: {reason}"
    if note not in ctx.notes:
        ctx.notes.append(note)


def _same_commit(recorded: str | None, target_head: str | None) -> bool:
    """Whether two commit ids name the same commit (tolerant of abbreviations)."""
    if not recorded or not target_head:
        return False
    a, b = recorded.strip().lower(), target_head.strip().lower()
    width = min(len(a), len(b), 40)
    return width >= 8 and a[:width] == b[:width]


def _graph_provenance(path: Path, target_head: str | None) -> dict[str, Any]:
    """What ``path`` records about when/where it was built, versus *target_head*.

    Graphify stamps ``built_at_commit`` — the HEAD of the repo the graph
    *describes* (its ``extract`` passes the target's own HEAD) — plus
    ``graph.graphify_version`` into ``graph.json``; it records **no** build
    timestamp.  Exactly three states, and no others:

    * ``fresh`` — the recorded commit *is* the target HEAD this run observed;
    * ``stale`` — a commit is recorded and it is not that HEAD: the graph
      describes a revision of the target that no longer exists, and every
      downstream stage would reason about a repository state that is gone;
    * ``unverified`` — nothing is recorded (or the target HEAD is unreadable).
      **Missing provenance is not evidence of freshness**: it is never reported
      as fresh, and it is not a refusal either — the graph is still reused.

    This is the residual made *visible*, not eliminated: a graph whose recorded
    commit matches HEAD but whose bytes were tampered with, and a graph from a
    matching revision that is nonetheless the best available, both stay
    undetectable here.
    """
    state, detail, built, version = "unverified", "", None, None
    try:
        with path.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
        if not isinstance(doc, dict):
            detail = f"top-level JSON is {type(doc).__name__}, not an object"
        else:
            meta = doc.get("graph") if isinstance(doc.get("graph"), dict) else {}
            raw = doc.get("built_at_commit")
            built = raw.strip() if isinstance(raw, str) and raw.strip() else None
            raw_version = meta.get("graphify_version")
            version = raw_version if isinstance(raw_version, str) and raw_version else None
            if built is None:
                detail = (
                    "graph records no built_at_commit (pre-0.9.80 graphify or a "
                    "non-graphify writer): age and origin are unknown"
                )
            elif not target_head:
                detail = (
                    f"graph records built_at_commit={built[:12]} but the target HEAD "
                    "is unreadable"
                )
            elif _same_commit(built, target_head):
                state, detail = "fresh", "recorded commit is the target HEAD"
            else:
                state = "stale"
                detail = f"built at {built[:12]} but target HEAD is {target_head[:12]}"
    except Exception as exc:  # noqa: BLE001 - unreadable provenance is unverified, not a crash
        detail = f"{type(exc).__name__}: {exc}"
    return {
        "built_at_head": built,
        "built_at": None,  # graphify 0.9.80 records no build timestamp; not invented
        "tool_version": version,
        "observed_target_head": target_head,
        "state": state,
        "detail": detail,
    }


#: committed pin file: expected graph digests live OUTSIDE the artifact and
#: outside gitignored ``state/`` (see ``config/graph_pin.toml``).
GRAPH_PIN_FILE = "graph_pin.toml"

#: sha256 is 64 hex characters, and only in the 12-63 range can a short pin be
#: *compared at all*: a pin there is an *abbreviation*, still honoured (refusing
#: a 12-hex pin would force a rewrite of a committed pin for no cryptographic
#: gain) but reported loudly as reduced strength.  A pin of 0 hex is REFUSED
#: as the DISTINCT EMPTY state (``PIN_EMPTY``, reported ``pin empty``) and is
#: never compared at all — it is not a mismatch.  A pin of 1-11 hex is REFUSED
#: as a mismatch: ``_same_digest`` requires ``width >= 12``, so it cannot be
#: compared AT ALL (fail-closed) — never a weaker match, and with no
#: ``PIN ABBREVIATED`` note.  A pin of 65+ hex is refused as over-long.
DIGEST_HEX = 64

#: why ``_graph_pin`` returned what it did — a degraded control is never silent.
PIN_ABSENT = "absent"          #: no pin file at all: a fresh setup
PIN_OK = "ok"                  #: a pin value for this exact path
PIN_UNREADABLE = "unreadable"  #: exists but cannot be read (chmod 000, EISDIR)
PIN_MALFORMED = "malformed"    #: exists but is not a usable TOML pin document
PIN_EMPTY = "empty"            #: entry exists for this path but carries no value
PIN_NO_ENTRY = "no_entry"      #: well-formed file, no expectation for this path


def _pin_hex_len(pin: Any) -> int:
    """A pin's length in hex characters, whitespace-insensitive (0 when absent)."""
    return len(str(pin or "").strip())


def _pin_is_abbreviated(pin: Any) -> bool:
    """Whether the pin supplies *fewer* hex characters than the full digest.

    The rule (U8.19, corrected by U8.24): in the *comparable* range a pin is
    reported at **every** such length, 63 hex exactly as loudly as 12 — a warning
    keyed to some threshold is a warning an operator cannot rely on.  That range
    is 12-63 hex, not "every length below 64": below 12 hex the pin is not warned
    about but REFUSED, because ``_same_digest`` requires ``width >= 12``, so a
    1-11-hex pin cannot be compared at all and lands in the mismatch branch
    (fail-closed, no ``PIN ABBREVIATED`` note).  A 0-hex pin is refused even
    earlier, as the distinct EMPTY state (``PIN_EMPTY``, reported ``pin empty``),
    and is never compared.  ``_same_digest`` compares
    ``min(len(pin), 64)`` characters, so the effective strength of an abbreviated
    pin is exactly its own length in hex.
    """
    return 0 < _pin_hex_len(pin) < DIGEST_HEX


def _pin_is_overlong(pin: Any) -> bool:
    """Whether the pin carries characters *beyond* the full digest.

    A sha256 is exactly ``DIGEST_HEX`` characters.  A shorter value is an
    abbreviation (honoured, loudly); a *longer* one is neither a digest nor a
    prefix of one but a corrupted or mis-edited value, and comparing only its
    first 64 characters blessed it in silence (measured before this fix: pins of
    65 and 100 hex matched with **no** notice at all).  It is refused.
    """
    return _pin_hex_len(pin) > DIGEST_HEX


def _same_digest(reported: str | None, pinned: str | None) -> bool:
    """Whether a reported sha256 agrees with the pinned one, in FULL.

    ``min(len, 64)`` over both sides: with the full 64-hex digest ``_graph_digest``
    now reports, and the 64-hex pin ``config/graph_pin.toml`` records, the
    comparison runs character for character, so a pin whose *tail* is wrong can
    no longer match (U8.11 item 2).  The trailing ``width >= 12`` is a floor, not
    a tolerance: a pin of 12-63 hex that matches is still honoured — 12 hex is
    the historical minimum and refusing it would force a rewrite of a committed
    pin for no cryptographic gain over the status quo — but the caller reports
    that reduced strength loudly (``PIN ABBREVIATED`` run note and a ``REDUCED
    STRENGTH`` clause).  A pin of 1-11 hex returns False here: it cannot be
    compared at all, so it is refused as a mismatch (fail-closed) rather than
    accepted at reduced strength.  A 0-hex pin never reaches this function at
    all: the caller refuses it first as the distinct EMPTY state (``PIN_EMPTY``,
    reported ``pin empty``, never compared).
    """
    if not reported or not pinned:
        return False
    a, b = reported.strip().lower(), pinned.strip().lower()
    width = min(len(a), len(b), 64)
    return width >= 12 and a[:width] == b[:width]


def _graph_pin(path: Path, config_dir: str | Path = "config") -> tuple[str | None, str]:
    """The expected sha256 for ``path``, **and why** — ``(value, state)``.

    The pin is deliberately **outside the artifact it pins** (a digest recorded
    *inside* ``graph.json`` is written by the same writer that wrote the bytes,
    so it can be rewritten by whoever alters the bytes — it can never vouch for
    the artifact) and **durable** (a committed ``config/`` file, not gitignored
    ``state/``).

    The second element is one of the ``PIN_*`` constants, so the caller can tell
    a control that was *never set up* from one that is *present and broken*.
    Before U8.11 every failure returned a bare ``None`` and the two were
    indistinguishable — a malformed or unreadable pin degraded silently to the
    same "no pin" state and the graph was reused with no note (V8C item 3).

    * ``absent`` — no pin file at all: a fresh setup, not evidence of tampering.
    * ``ok`` — a non-blank ``sha256`` is recorded for this exact path.
    * ``unreadable`` — the file exists but cannot be read (EACCES, EISDIR).
    * ``malformed`` — the file exists but is not a usable TOML pin document.
    * ``empty`` — an entry exists for this path but carries no usable value.
    * ``no_entry`` — a well-formed file with no expectation for *this* path.
    """
    pin_file = Path(config_dir) / GRAPH_PIN_FILE
    try:
        raw = pin_file.read_bytes()
    except FileNotFoundError:
        return None, PIN_ABSENT
    except OSError:  # noqa: BLE001 - exists but unreadable (EACCES/EISDIR/...)
        return None, PIN_UNREADABLE
    try:
        import tomllib

        doc = tomllib.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001 - exists but is not a pin we can parse
        return None, PIN_MALFORMED
    graphs = doc.get("graphs") if isinstance(doc, dict) else None
    if not isinstance(graphs, dict):
        return None, PIN_MALFORMED
    wanted = {str(path), Path(path).as_posix()}
    for key, entry in graphs.items():
        if Path(str(key)).as_posix() not in wanted:
            continue
        value = entry.get("sha256") if isinstance(entry, dict) else entry
        if isinstance(value, str) and value.strip():
            return value.strip(), PIN_OK
        return None, PIN_EMPTY
    return None, PIN_NO_ENTRY


def _digest_clause(prov: Mapping[str, Any]) -> str:
    """The digest half of the one shared graph line (empty when not evaluated)."""
    state = str(prov.get("digest_state") or "")
    if not state:
        return ""
    got = _digest12(prov.get("sha256"))
    pinned = str(prov.get("pin_sha256") or "")
    pin = _digest12(pinned)
    if state == "match":
        clause = f"; sha256 {got} matches the pinned digest {pin}"
        if _pin_is_abbreviated(pinned):
            clause += (
                f" — REDUCED STRENGTH: the pin supplies {_pin_hex_len(pinned)} of "
                f"{DIGEST_HEX} hex chars"
            )
        return clause
    if state == "mismatch":
        return (
            f"; sha256 {got} DOES NOT MATCH the pinned digest {pin} — TAMPERED OR "
            "CORRUPT (not reused by default; the file is kept on disk)"
        )
    why = str(prov.get("pin_state") or PIN_ABSENT)
    return (
        f"; sha256 {got} (no pin recorded [{why}] — bytes unverified; see the run "
        "notes: degraded control, not a verified match)"
    )


def _provenance_stamp(prov: Mapping[str, Any], target_head: str | None) -> str:
    """The one provenance clause the plan and the run both print, word for word."""
    built = str(prov.get("built_at_head") or "unknown")[:12]
    head = str(target_head or "unknown")[:12]
    state = str(prov.get("state") or "unverified").lower()
    word = {"fresh": "fresh", "stale": "STALE"}.get(
        state, "UNVERIFIED (no recorded provenance)"
    )
    return f"built at {built}, target head {head} — {word}{_digest_clause(prov)}"


def _add_note(ctx: RunContext, note: str) -> None:
    """Append a run note once: a degraded control is visible in the run's record."""
    if note not in ctx.notes:
        ctx.notes.append(note)


def _reuse_candidate(ctx: RunContext) -> Path | None:
    """The graph the run *would* reuse — one answer, shared by plan and fact.

    Plan and fact call this same function, so the dry run cannot describe a
    ``graphify`` build for a stage the real run will reuse — and, symmetrically,
    cannot promise a reuse the real run will not perform.  ``_graph_unusable_reason``
    is the *only* validity check and it lives here, inside the shared decision:
    a candidate is returned only when it is a usable graph.

    An unusable candidate is **reported**, never deleted or overwritten: its
    path and reason go to ``ctx.graph_rejected`` and ``ctx.notes``, the scan
    continues to the next candidate, and a stage that has to build writes
    beside the bad file so it stays on disk for inspection.

    Provenance (``built_at_commit`` vs the target HEAD) is evaluated here
    too, for the same reason the validity check is: the plan and the run
    must give the *same* answer.  A graph that is provably ``stale`` is still
    reused by default — a rebuild is never silent, and the acceptance
    target's HEAD is moved continuously by a foreign actor, so "stale ⇒
    rebuild" would rebuild on nearly every run.  Refusal is opt-in via
    ``require_fresh_graph``, whose absence is the safe default.

    Byte provenance (the sha256 against the committed pin) is evaluated here
    too, and its default is the opposite: **a graph whose bytes do not match
    the sha256 pinned for it in ``<config_dir>/graph_pin.toml`` is unusable by
    default — not reused, reported loudly as corruption or tampering, and kept
    on disk — unless ``allow_graph_digest_mismatch`` opts into reusing it.  A
    pin that is *absent* or that records nothing for this path is
    ``unpinned``/``unverified`` and still reused — but LOUDLY (a run note), never
    silently; a pin that *exists and cannot be honoured* (unreadable, malformed,
    or an empty value) is refused, because a control that is present and broken
    is not the same state as a control that was never set up.  Mere staleness
    stays report-only.**
    """
    for candidate in _graph_candidates(ctx):
        if not candidate.is_file():
            if candidate.exists() or candidate.is_symlink():
                _note_unusable(
                    ctx, candidate, "not a regular file (directory or dangling symlink)"
                )
            continue
        reason = _graph_unusable_reason(candidate)
        if reason is not None:
            _note_unusable(ctx, candidate, reason)
            continue
        provenance = _graph_provenance(candidate, ctx.target_head)
        # The bytes: a digest *inside* the artifact cannot vouch for the
        # artifact (same writer writes both), so the expectation comes from a
        # committed file outside it.  Reported either way; acted on only here.
        provenance["sha256"] = _graph_digest(candidate)
        pin, pin_state = _graph_pin(candidate, ctx.config_dir)
        provenance["pin_sha256"] = pin
        provenance["pin_state"] = pin_state
        pin_file = Path(ctx.config_dir) / GRAPH_PIN_FILE
        if pin_state in (PIN_UNREADABLE, PIN_MALFORMED, PIN_EMPTY):
            # The pin EXISTS and cannot be honoured.  That is NOT "no pin": a
            # control that is present and broken is refused, so silently
            # degrading it to the fresh-setup state is no longer possible.
            _note_unusable(
                ctx,
                candidate,
                f"pin {pin_state}: {pin_file} exists but supplies no usable sha256 "
                f"for {candidate} — the control is present and unreadable/broken, so "
                "the graph is NOT reused (unlike an absent pin, which is a fresh "
                "setup); the pin file is left untouched",
                label="pin",
            )
            continue
        if pin is not None and _pin_is_overlong(pin):
            # NOT an abbreviation: a digest is exactly DIGEST_HEX characters, so a
            # longer value is a corrupted or mis-edited pin.  Before U8.19 the
            # comparison ran over the first 64 characters and this case matched
            # with NO note and an unvalidated tail.  Present and unusable is
            # refused, exactly like malformed/unreadable/empty.
            _add_note(
                ctx,
                f"graph: PIN OVERLONG: {pin_file} pins {_pin_hex_len(pin)} hex "
                f"characters for {candidate}, {_pin_hex_len(pin) - DIGEST_HEX} more "
                f"than the full {DIGEST_HEX} — a digest is exactly {DIGEST_HEX} hex, "
                "so this is a corrupted or mis-edited pin whose tail was never "
                "validated; re-pin with the full sha256",
            )
            _note_unusable(
                ctx,
                candidate,
                f"pin overlong: {pin_file} supplies {_pin_hex_len(pin)} hex "
                f"characters for {candidate}, not a {DIGEST_HEX}-hex sha256 — a pin "
                "is never partially honoured and the trailing characters are "
                "unvalidated, so the graph is NOT reused; the pin file is left "
                "untouched (unlike an absent pin, which is a fresh setup)",
                label="pin",
            )
            continue
        if pin is None:
            provenance["digest_state"] = "unpinned"
            if pin_state == PIN_ABSENT:
                why = f"no pin file at all at {pin_file} (fresh setup)"
            else:
                why = (
                    f"the well-formed {pin_file} records no sha256 for {candidate} "
                    "(keyed on other graph paths)"
                )
            provenance["digest_detail"] = (
                f"{why}: no expected digest exists for this artifact — bytes "
                "unverified, still reused"
            )
            # LOUD: a degraded control is a note on the run's own record, not
            # only a clause in the stage line.
            _add_note(
                ctx,
                f"graph: PIN DEGRADED ({pin_state}): {why} — no pin recorded for "
                f"{candidate}, so its bytes are UNVERIFIED and reused anyway; this "
                "is a degraded control, not a verified match",
            )
        elif _same_digest(provenance["sha256"], pin):
            provenance["digest_state"] = "match"
            provenance["digest_detail"] = f"bytes match the pinned sha256 {pin[:12]}"
            if _pin_is_abbreviated(pin):
                _add_note(
                    ctx,
                    f"graph: PIN ABBREVIATED: {pin_file} pins only "
                    f"{_pin_hex_len(pin)} hex characters for {candidate}, not the "
                    f"full {DIGEST_HEX} — the comparison has "
                    f"{_pin_hex_len(pin) * 4}-bit effective strength, not 256; "
                    "re-pin with the full sha256 to restore it",
                )
        else:
            provenance["digest_state"] = "mismatch"
            provenance["digest_detail"] = (
                f"bytes hash to {str(provenance['sha256'])[:12]} but "
                f"{Path(ctx.config_dir) / GRAPH_PIN_FILE} pins {pin[:12]}"
            )
            if not ctx.allow_graph_digest_mismatch:
                _note_unusable(
                    ctx,
                    candidate,
                    "digest mismatch: "
                    + provenance["digest_detail"]
                    + " — corruption or tampering, not staleness (the file is kept "
                    "on disk and a fresh graph is built; allow_graph_digest_mismatch "
                    "opts into reusing it)",
                    label="digest",
                )
                continue
        if ctx.require_fresh_graph and provenance.get("state") in ("stale", "unverified"):
            _add_note(
                ctx,
                "graph: require_fresh_graph refused an unvouched-for graph "
                f"({provenance.get('state')}) — the opt-in refuses any graph it "
                "cannot vouch for, stale or unverified; the graph is kept and a "
                "fresh one built",
            )
            _note_unusable(
                ctx,
                candidate,
                f"{provenance.get('state')}: "
                f"{_provenance_stamp(provenance, ctx.target_head)} "
                "(require_fresh_graph opted in — it refuses a graph it cannot vouch "
                "for, whether stale or unverified; the graph is kept on disk and a "
                "fresh one built)",
                label=provenance.get("state"),
            )
            continue
        ctx.graph_provenance = provenance
        return candidate
    return None


def _graph_digest(path: Path) -> str:
    """The **full** 64-hex sha256 of ``path``, or ``"unknown"``.

    It must be the full digest: the pin is compared against this value, and an
    abbreviated one caps the comparison at its own length — a wrong *tail* with
    the same first 12 hex used to report "matches the pinned digest", i.e. 48
    bits of strength instead of 256 (U8.11 item 2).  Abbreviation belongs to the
    human-readable line, which truncates for display via ``_digest12``.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:  # noqa: BLE001 - a graph we cannot hash is reported as unknown
        return "unknown"


def _digest12(value: Any) -> str:
    """The 12-hex display abbreviation of a digest (never used for comparison)."""
    return str(value or "unknown")[:12]


def _stage_graph(ctx: RunContext) -> StageResult:
    """Bounded code-only knowledge graph.  No model, no writes into the target.

    Policy: provenance is *recorded and reported, never acted on*
    (report-only is the default — a stale graph is reused with ``STALE`` in
    this stage's line and in the run notes), because the target's HEAD is
    moved continuously by a foreign actor and "stale ⇒ rebuild" would rebuild
    on nearly every run; ``require_fresh_graph`` is the opt-in refusal.  The
    **bytes** are different: a sha256 that disagrees with the committed pin is
    acted on — the shared decision refuses it by default (``digest mismatch``),
    and this line says so.  Every pin degradation is loud (U8.11 item 3): an
    absent pin, or a pin recording nothing for this path, is reused but noted
    (``PIN DEGRADED``); a pin that exists and cannot be honoured (unreadable,
    malformed, empty value) is refused; an abbreviated pin of 12-63 hex
    characters is accepted only with a ``PIN ABBREVIATED`` note and a
    ``REDUCED STRENGTH`` clause, while a pin of 1-11 hex cannot be compared at
    all (``_same_digest`` needs ``width >= 12``) and is therefore refused as a
    mismatch, fail-closed, without that note; a 0-hex pin is refused as the
    distinct EMPTY state and never compared at all; and an over-long pin
    (more than 64 hex characters) is refused, because comparing only its first
    64 characters blessed a corrupted tail in silence (U8.19).
    """
    from .kg import graph_stats

    reusable = _reuse_candidate(ctx)
    if reusable is not None:
        stats = graph_stats(reusable)
        provenance = dict(ctx.graph_provenance) or _graph_provenance(
            reusable, ctx.target_head
        )
        counts = {
            "mode": "reuse",
            "nodes": int(getattr(stats, "nodes", 0) or 0),
            "edges": int(getattr(stats, "edges", 0) or 0),
            "sha256": provenance.get("sha256") or _graph_digest(reusable),
        }
        provenance["nodes"] = counts["nodes"]
        provenance["edges"] = counts["edges"]
        provenance["sha256"] = counts["sha256"]
        counts["provenance"] = provenance
        stamp = _provenance_stamp(provenance, ctx.target_head)
        reason = (
            f"{'dry run: would reuse' if ctx.dry_run else 'reused'} existing "
            f"code-only graph at {reusable} ({stamp}; graphify not re-run: bounded, "
            "and a re-extract would write inside the target)"
        )
        if provenance.get("digest_state") == "mismatch":
            dnote = (
                f"graph: DIGEST MISMATCH — {stamp}; reused only because "
                "allow_graph_digest_mismatch opted in (corruption or tampering is "
                "not excluded)"
            )
            if dnote not in ctx.notes:
                ctx.notes.append(dnote)
        if provenance.get("state") != "fresh":
            note = (
                f"graph: reuse provenance {provenance.get('state')} — {stamp}; "
                "reused and reported, never silently rebuilt (report-only default)"
            )
            if note not in ctx.notes:
                ctx.notes.append(note)
        if ctx.dry_run:
            return StageResult(
                name="graph",
                status="skipped",
                reason=reason,
                counts=counts,
                artifacts=[str(reusable)],
            )
        ctx.graph_path = reusable
        ctx.record(reusable)
        return StageResult(
            name="graph",
            status="ok",
            reason=reason,
            counts=counts,
            artifacts=[str(reusable)],
        )
    out_dir = ctx.run_dir / "kg"
    # The artifact ``Graphify.extract --out <out_dir>`` really writes is
    # ``<out_dir>/graphify-out/graph.json`` (``Graphify.graph_json``), NOT
    # ``<out_dir>/graph.json``.  Ask the same locator the real build below uses,
    # so the plan cannot name a path the artifact never lands at.
    from .kg import Graphify

    planned = str(Graphify.graph_json(out_dir))
    rejected = list(ctx.graph_rejected)
    why = "; ".join(f"{e['path']} — {e['reason']}" for e in rejected)
    if ctx.dry_run:
        reason = (
            "dry run: would run `graphify extract --code-only --out "
            f"{out_dir}` (token-budget {GRAPH_TOKEN_BUDGET}, no model)"
        )
        if why:
            reason += f"; unusable candidate(s) rejected: {why}"
        return StageResult(
            name="graph",
            status="skipped",
            reason=reason,
            counts={
                "mode": "build",
                "planned_out": planned,
                "rejected_candidates": rejected,
            },
        )

    try:
        gf = Graphify(cwd=ctx.run_dir, timeout=GRAPH_TIMEOUT_S)
        result = gf.extract(
            str(ctx.target_root),
            code_only=True,
            out=str(out_dir),
            token_budget=GRAPH_TOKEN_BUDGET,
            no_viz=True,
        )
        graph_json = Graphify.graph_json(out_dir)
        if not graph_json.is_file():
            return StageResult(
                name="graph",
                status="failed",
                reason=f"graphify produced no graph.json under {out_dir}: {str(result)[:300]}",
                counts={"mode": "build"},
            )
        ctx.graph_path = graph_json
        ctx.record(graph_json)
        if getattr(result, "ok", True) is False:
            return StageResult(
                name="graph",
                status="degraded",
                reason=f"graphify exited non-zero: {str(result)[:300]}",
                counts={"mode": "build"},
                artifacts=[str(graph_json)],
            )
        stats = graph_stats(graph_json)
        provenance = _graph_provenance(graph_json, ctx.target_head)
        if not provenance.get("built_at_head"):
            # This run built the artifact this instant from the tree it read at
            # ``head_before``: that IS provenance, known rather than recorded.
            provenance["built_at_head"] = ctx.target_head
            provenance["built_at"] = utcnow()
            provenance["state"] = "fresh" if ctx.target_head else "unverified"
            provenance["detail"] = (
                "recorded by this run at build time (graphify recorded no commit)"
                if ctx.target_head
                else "target HEAD was unreadable at build time"
            )
        provenance["nodes"] = int(getattr(stats, "nodes", 0) or 0)
        provenance["edges"] = int(getattr(stats, "edges", 0) or 0)
        return StageResult(
            name="graph",
            status="ok",
            reason=(
                f"built code-only graph at {graph_json} (no model calls; "
                f"{_provenance_stamp(provenance, ctx.target_head)})"
            ),
            counts={
                "mode": "build",
                "nodes": provenance["nodes"],
                "edges": provenance["edges"],
                "provenance": provenance,
                "rejected_candidates": rejected,
            },
            artifacts=[str(graph_json)],
        )
    except Exception as exc:  # noqa: BLE001 - a stage failure is data, not a crash
        return StageResult(name="graph", status="failed", reason=f"{type(exc).__name__}: {exc}")


def _stage_staging(ctx: RunContext) -> StageResult:
    """Stage the target's non-code material into the workspace.  No model."""
    out_dir = ctx.run_dir / "staging"
    if ctx.dry_run:
        return StageResult(
            name="staging",
            status="skipped",
            reason=f"dry run: would build the staging corpus under {out_dir}",
            counts={"planned_out": str(out_dir)},
        )
    from .kg.staging import build_staging_corpus, staging_summary

    corpus = build_staging_corpus(
        str(ctx.target_root),
        str(out_dir),
        max_files=STAGING_MAX_FILES,
        max_total_bytes=STAGING_MAX_BYTES,
        max_normalize_files=STAGING_MAX_NORMALIZE,
    )
    summary = staging_summary(corpus)
    counts = {
        k: v for k, v in summary.items() if isinstance(v, (int, float, str, bool)) and k != "out_dir"
    }
    ctx.staging_dir = out_dir
    ctx.record(getattr(corpus, "manifest_path", None), out_dir if out_dir.exists() else None)
    return StageResult(
        name="staging",
        status="ok",
        reason=f"staged non-code material from {ctx.target_root} into {out_dir} (no model)",
        counts=counts,
        artifacts=[str(out_dir)],
    )


def _make_client(ctx: RunContext) -> tuple[Any, str]:
    """Build a model client **only** when the endpoint answered.  Never guesses."""
    if not ctx.endpoint_ok:
        return None, f"model endpoint unavailable (http {ctx.endpoint_status})"
    try:
        from .llm import Budget, OccamyClient

        client = OccamyClient(budget=Budget(max_tokens=50_000, max_calls=8))
        return client, ""
    except Exception as exc:  # noqa: BLE001 - report, never fabricate a client
        return None, f"could not construct OccamyClient: {type(exc).__name__}: {exc}"


def _stage_mine(ctx: RunContext) -> StageResult:
    """Mine candidates.  Blocked — never skipped — when the model cannot run."""
    if not ctx.model_candidates:
        return StageResult(
            name="mine",
            status="blocked",
            reason=ctx.gate_reason("mine"),
            counts={"candidates_in_store": len(ctx.all_candidates)},
        )
    if ctx.client is None:
        return StageResult(
            name="mine",
            status="blocked",
            reason=f"no model client available: {ctx.client_reason or 'unavailable'}",
            counts={"candidates_in_store": len(ctx.all_candidates)},
        )
    from .mine.candidates import Miner

    out_dir = ctx.run_dir / "mine"
    report = Miner(
        ctx.target_root,
        ctx.graph_path,
        client=ctx.client,
        store_path=ctx.store_path,
        out_dir=out_dir,
    ).mine()
    counts = {
        "accepted": int(getattr(report, "accepted", 0) or 0),
        "rejected": int(getattr(report, "rejected", 0) or 0),
        "model_calls": int(getattr(report, "model_calls", 0) or 0),
        "usage_records": int(getattr(report, "usage_records", 0) or 0),
        "queries_run": int(getattr(report, "queries_run", 0) or 0),
    }
    producer = str(getattr(report, "producer", "unknown"))
    status = "ok"
    reason = f"mined with producer={producer} mode={getattr(report, 'mode', '?')}"
    if producer != "model":
        status = "degraded"
        reason += " — NOT a model-produced run (replay/fixture provenance)"
        ctx.degradations.append(f"mine: producer={producer} (not model)")
    ctx.record(out_dir if out_dir.exists() else None)
    return StageResult(name="mine", status=status, reason=reason, counts=counts, artifacts=[str(out_dir)])


def _stage_claims(ctx: RunContext) -> StageResult:
    """Decompose candidates into claims.  Gated on model-produced material."""
    if not ctx.model_candidates:
        return StageResult(
            name="claims",
            status="blocked",
            reason=ctx.gate_reason("claims"),
            counts={"model_candidates": 0},
        )
    if ctx.client is None:
        return StageResult(
            name="claims",
            status="blocked",
            reason=f"no model client available: {ctx.client_reason or 'unavailable'}",
            counts={"model_candidates": len(ctx.model_candidates)},
        )
    from .claims.decompose import decompose_candidates

    out_dir = ctx.run_dir / "claims"
    report = decompose_candidates(
        ctx.model_candidates,
        client=ctx.client,
        graph_path=ctx.graph_path,
        target_root=ctx.target_root,
        store_path=ctx.store_path,
        out_dir=out_dir,
    )
    producer = str(getattr(report, "producer", "unknown"))
    counts = {
        "claims": len(getattr(report, "claims", []) or []),
        "rejected": len(getattr(report, "rejected", []) or []),
        "model_calls": int(getattr(report, "model_calls", 0) or 0),
        "usage_records": int(getattr(report, "usage_records", 0) or 0),
        "partial": bool(getattr(report, "partial", False)),
    }
    status = "ok"
    reason = f"decomposed with producer={producer}"
    if producer != "model":
        status = "degraded"
        reason += " — REPLAY-DERIVED provenance is a degradation, not a success"
        ctx.degradations.append(f"claims: producer={producer} (not model)")
    ctx.record(out_dir if out_dir.exists() else None)
    return StageResult(name="claims", status=status, reason=reason, counts=counts, artifacts=[str(out_dir)])


def _stage_assess(ctx: RunContext) -> StageResult:
    """Assessment (batch 4) has no implementation yet, but it *is* model-gated."""
    if not ctx.model_candidates:
        return StageResult(name="assess", status="blocked", reason=ctx.gate_reason("assess"))
    return StageResult(
        name="assess",
        status="skipped",
        reason="assessment is not implemented in this build (batch 4 — assessment)",
    )


def _stage_lanes(ctx: RunContext) -> StageResult:
    """Build/classify/persist lanes from the candidate bag.  No model."""
    from .lanes import build_lanes, classify_lane, from_store, persist_lanes, write_lanes_md

    rows = list(ctx.all_candidates)
    if not rows:
        return StageResult(
            name="lanes",
            status="skipped",
            reason="no candidates in the store: nothing to group into lanes",
            counts={"candidates": 0, "lanes": 0},
        )
    if ctx.dry_run:
        return StageResult(
            name="lanes",
            status="skipped",
            reason=(
                f"dry run: would build lanes from {len(rows)} candidate(s), classify, "
                f"persist into the run-scoped store and write LANES.md"
            ),
            counts={"candidates": len(rows)},
        )

    graph = None
    if ctx.graph_path is not None:
        try:
            from .kg import read_graph

            graph = read_graph(ctx.graph_path)
        except Exception as exc:  # noqa: BLE001 - a missing graph only costs communities
            ctx.notes.append(f"lanes: graph not usable for community attachment: {exc}")
    candidates = from_store(rows, graph)
    lanes = build_lanes(candidates, min_size=1)
    classifications: dict[str, Any] = {}
    types: dict[str, str] = {}
    for lane in lanes:
        try:
            verdict = classify_lane(lane)
        except Exception as exc:  # noqa: BLE001 - classification is advisory
            ctx.notes.append(f"lanes: classification failed for {lane.slug}: {exc}")
            continue
        classifications[lane.slug] = verdict
        lane_type = getattr(verdict, "lane_type", None) or getattr(verdict, "type", None)
        if lane_type is None:
            payload = getattr(verdict, "as_dict", None)
            if callable(payload):
                lane_type = payload().get("type") or payload().get("lane_type")
        if isinstance(lane_type, str) and lane_type:
            types[lane.slug] = lane_type

    out_dir = ctx.run_dir / "lanes"
    md_path, json_path = write_lanes_md(lanes, out_dir, classifications=classifications)
    ctx.lanes = lanes
    ctx.classifications = classifications
    ctx.lane_ids = persist_lanes(lanes, ctx.con, ctx.target_slug, types=types or None)
    ctx.record(md_path, json_path)
    refused = sorted(
        slug for slug, verdict in classifications.items()
        if (getattr(verdict, "lane_type", None) or getattr(verdict, "type", None)) in (None, "", "refused")
    )
    return StageResult(
        name="lanes",
        status="ok",
        reason=(
            f"built {len(lanes)} lane(s) from {len(rows)} candidate(s), persisted "
            f"{len(ctx.lane_ids)} into the run-scoped store; classifier typed "
            f"{len(types)} and refused {len(refused)} (expected today)"
        ),
        counts={
            "candidates": len(rows),
            "lanes": len(lanes),
            "persisted": len(ctx.lane_ids),
            "typed": len(types),
            "refused_paper": len(refused),
        },
        artifacts=[str(md_path), str(json_path)],
    )


def _stage_materialize(ctx: RunContext) -> StageResult:
    """Docket materialization — gated on model-produced candidates by default."""
    if not ctx.model_candidates:
        if not ctx.allow_replay:
            return StageResult(
                name="materialize",
                status="skipped",
                reason=(
                    "no model-produced candidates "
                    f"(producer gate; endpoint http {ctx.endpoint_status}); "
                    "pass --allow-replay to build a replay-derived docket anyway"
                ),
                counts={"model_candidates": 0, "lanes": len(ctx.lanes)},
            )
        if not ctx.all_candidates:
            return StageResult(
                name="materialize",
                status="skipped",
                reason="--allow-replay given, but there are no candidates (replay or otherwise)",
                counts={"candidates": 0},
            )
        return _materialize_lanes(ctx, replay_derived=True)
    return _materialize_lanes(ctx, replay_derived=False)


def _materialize_lanes(ctx: RunContext, *, replay_derived: bool) -> StageResult:
    from .docket import materialize as mat

    lanes = list(ctx.lanes)
    if not lanes and not ctx.dry_run:
        return StageResult(
            name="materialize",
            status="skipped",
            reason="no lanes were built: nothing to materialize",
            counts={"lanes": 0},
        )
    if ctx.dry_run:
        return StageResult(
            name="materialize",
            status="skipped",
            reason=(
                f"dry run: would materialize {len(lanes)} lane(s) into {ctx.docket_root}"
                + (" (REPLAY-DERIVED: --allow-replay)" if replay_derived else " (model-produced)")
            ),
            counts={"lanes": len(lanes)},
        )

    written: list[str] = []
    failures: list[str] = []
    for lane in lanes:
        lane_row = store.get_lane_by_slug(ctx.con, ctx.target_slug, lane.slug)
        if lane_row is None:
            failures.append(f"{lane.slug}: no lanes row (not persisted)")
            continue
        member_rows = store.candidates_for_lane(ctx.con, int(lane_row["id"]))
        spec = mat.LaneSpec.from_store(lane_row, member_rows)
        if not spec.target_slug:
            spec.target_slug = ctx.target_slug
        try:
            result = mat.materialize_lane(
                spec,
                target_root=str(ctx.target_root),
                docket_root=str(ctx.docket_root),
                graph_path=str(ctx.graph_path) if ctx.graph_path else None,
                dry_run=False,
                db_path=ctx.db_path,
                source_mode="commit",
                window_s=ctx.window_s,
                allow_active=ctx.allow_active,
            )
        except mat.TargetBusyError as exc:
            failures.append(f"{lane.slug}: target not quiescent — {exc}")
            ctx.degradations.append(f"materialize {lane.slug}: target not quiescent")
            continue
        except Exception as exc:  # noqa: BLE001 - one bad lane must not kill the run
            failures.append(f"{lane.slug}: {type(exc).__name__}: {exc}")
            continue
        docket_dir = str(getattr(result, "docket_dir", "") or "")
        if docket_dir:
            written.append(docket_dir)
            ctx.record(docket_dir)
        if getattr(result, "window_sealed", None) is False:
            ctx.degradations.append(
                f"materialize {lane.slug}: docket window NOT sealed (target head moved)"
            )

    if replay_derived:
        reason = (
            f"REPLAY-DERIVED: materialized {len(written)} lane(s) from replay-provenance "
            "candidates under --allow-replay — this is a degradation, not a model-produced "
            "result (docket-side provenance labelling is a separate queued unit)"
        )
        ctx.degradations.append(
            f"materialize: {len(written)} replay-derived docket(s) written (--allow-replay)"
        )
        status = "degraded"
    else:
        reason = f"materialized {len(written)} model-backed lane(s)"
        status = "ok" if not failures else "degraded"
    if failures:
        reason += "; failures: " + "; ".join(failures[:3])
        for failure in failures[:3]:
            ctx.degradations.append(f"materialize: {failure}")
    return StageResult(
        name="materialize",
        status=status,
        reason=reason,
        counts={
            "lanes": len(lanes),
            "dockets": len(written),
            "failures": len(failures),
            "replay_derived": bool(replay_derived),
        },
        artifacts=written,
    )


def _stage_refresh(ctx: RunContext) -> StageResult:
    """The refresh engine.  No model; bounded; nothing written into the target."""
    from .refresh import refresh_target

    if ctx.dry_run:
        return StageResult(
            name="refresh",
            status="skipped",
            reason=(
                f"dry run: would refresh {ctx.target_root} "
                f"(docket_dirs={[str(ctx.docket_root)]}, links not checked, "
                "graph update off — a graph update would copy the target into the workspace)"
            ),
            counts={"planned_docket_root": str(ctx.docket_root)},
        )
    report = refresh_target(
        str(ctx.target_root),
        docket_dirs=[str(ctx.docket_root)],
        check_links=False,
        dry_run=False,
        slug=ctx.target_slug,
        run_graph_update=False,
        persist_store=False,
        db_path=ctx.db_path,
        state_root=str(ctx.run_dir / "refresh"),
        kg_root=str(ctx.run_dir / "kg"),
    )
    payload = report.as_dict() if hasattr(report, "as_dict") else {}
    counts = {
        k: v
        for k, v in payload.items()
        if isinstance(v, (int, float, str, bool)) and k not in ("target", "path")
    }
    state = str(getattr(report, "state", "") or "")
    status = "ok"
    reason = f"refresh engine ran over {ctx.docket_root} (no model, no link fetches)"
    if state and state != "current":
        status = "degraded"
        reason += f"; target state={state}"
        ctx.degradations.append(f"refresh: target state={state}")
    return StageResult(name="refresh", status=status, reason=reason, counts=counts)


STAGE_IMPLS: dict[str, Callable[[RunContext], StageResult]] = {
    "graph": _stage_graph,
    "staging": _stage_staging,
    "mine": _stage_mine,
    "claims": _stage_claims,
    "assess": _stage_assess,
    "lanes": _stage_lanes,
    "materialize": _stage_materialize,
    "refresh": _stage_refresh,
}


# -- the pipeline ------------------------------------------------------------ #


def _select_stages(stages: Sequence[str] | None) -> list[str]:
    if stages is None:
        return list(STAGE_ORDER)
    unknown = [s for s in stages if s not in STAGE_ORDER]
    if unknown:
        raise ValueError(
            f"unknown stage(s) {unknown}; known stages: {', '.join(STAGE_ORDER)}"
        )
    return [s for s in STAGE_ORDER if s in set(stages)]


def _run_stage(
    name: str, impls: Mapping[str, Callable[[RunContext], StageResult]], ctx: RunContext
) -> StageResult:
    impl = impls.get(name)
    if impl is None:  # pragma: no cover - _select_stages validates the name
        return StageResult(name=name, status="skipped", reason="no implementation registered")
    started = time.monotonic()
    try:
        result = impl(ctx)
    except Exception as exc:  # noqa: BLE001 - a crashing stage is reported, not fatal
        result = StageResult(
            name=name, status="failed", reason=f"{type(exc).__name__}: {exc}"
        )
        ctx.degradations.append(f"{name}: failed — {type(exc).__name__}: {exc}")
    result.duration_s = time.monotonic() - started
    if result.status in ("failed", "degraded") and result.reason:
        marker = f"{name}: {result.status}"
        if not any(d.startswith(marker) for d in ctx.degradations):
            ctx.degradations.append(f"{marker} — {result.reason}")
    return result


def run_pipeline(
    target_slug: str,
    *,
    stages: Sequence[str] | None = None,
    dry_run: bool = False,
    allow_active: bool = False,
    allow_replay: bool = False,
    require_fresh_graph: bool = False,
    allow_graph_digest_mismatch: bool = False,
    window_s: float = 5.0,
    stage_impls: Mapping[str, Callable[[RunContext], StageResult]] | None = None,
    doctor_report: Mapping[str, Any] | None = None,
    db_path: str | Path | None = None,
    run_root: str | Path | None = None,
    config_dir: str = "config",
    client: Any = None,
) -> RunReport:
    """Chain the pipeline into one bounded, honest run.

    Preflight is evaluated first; if any hard gate fails, ``exit_code == 2`` and
    **no stage runs** (each planned stage is reported ``skipped`` with the
    preflight reason).  Otherwise the selected stages run in :data:`STAGE_ORDER`
    order, the target HEAD is re-read afterwards, and the exit code comes from
    :func:`exit_code_for`.
    """
    started_at = utcnow()
    started_mono = time.monotonic()
    selected = _select_stages(stages)
    impls = dict(STAGE_IMPLS)
    if stage_impls:
        impls.update(stage_impls)

    real_db = Path(db_path) if db_path is not None else Path(store.default_db_path())
    root = Path(run_root) if run_root is not None else Path("state") / "run"

    con = None
    try:
        con = _open_readonly(real_db) if real_db.exists() else None
    except Exception:  # noqa: BLE001 - reported by preflight
        con = None
    try:
        resolved = _resolve_target(target_slug, con, config_dir=config_dir)
    except Exception:  # noqa: BLE001 - an unresolvable target is a preflight failure
        resolved = None
    if con is not None:
        con.close()

    report = RunReport(
        target=target_slug,
        started_at=started_at,
        dry_run=bool(dry_run),
        started_monotonic=started_mono,
    )
    if not resolved:
        report.preflight = {
            "ok": False,
            "failures": [
                f"target {target_slug!r} is not registered and does not resolve to a directory"
            ],
        }
        report.stages = [
            StageResult(
                name=name,
                status="skipped",
                reason=f"preflight failed: target {target_slug!r} not resolvable",
            )
            for name in selected
        ]
        report.degradations = list(report.preflight["failures"])
        report.exit_code = EXIT_HARD_DOWN
        report.finished_at = utcnow()
        report.finished_monotonic = time.monotonic()
        return report

    target_root = Path(resolved).resolve()
    run_dir = Path(root) / target_slug
    ctx = RunContext(
        target_slug=target_slug,
        target_root=target_root,
        run_dir=run_dir,
        store_path=run_dir / "state.sqlite",
        db_path=run_dir / "state.sqlite",
        dry_run=bool(dry_run),
        allow_active=bool(allow_active),
        allow_replay=bool(allow_replay),
        window_s=float(window_s),
        require_fresh_graph=bool(require_fresh_graph),
        config_dir=str(config_dir),
        allow_graph_digest_mismatch=bool(allow_graph_digest_mismatch),
        docket_root=run_dir / "dockets",
        claims_dir=run_dir / "claims",
        mine_dir=run_dir / "mine",
    )

    pf = _preflight(
        ctx,
        doctor_report=doctor_report,
        real_db=real_db,
        selected=selected,
        config_dir=config_dir,
    )
    ctx.endpoint_ok = pf.endpoint_ok
    ctx.endpoint_status = pf.endpoint_status
    report.target_root = str(target_root)
    report.preflight = pf.as_dict()
    report.degradations.extend(pf.degradations)
    report.notes.extend(pf.degradations)

    if not pf.ok:
        reason = "preflight failed: " + "; ".join(pf.failures)
        report.stages = [
            StageResult(name=name, status="skipped", reason=reason) for name in selected
        ]
        report.exit_code = EXIT_HARD_DOWN
        report.window_sealed = False
        report.head_before = None
        report.head_after = None
        report.finished_at = utcnow()
        report.finished_monotonic = time.monotonic()
        return report

    # Sealed window: observe the writer signal before anything is measured.
    _observe_window(ctx, pf)
    report.preflight = pf.as_dict()
    report.writer_signal = pf.writer_signal
    if pf.degradations:
        for note in pf.degradations:
            if note not in report.degradations:
                report.degradations.append(note)
    report.head_before = pf.head_before or _read_head(target_root)
    pf.head_before = report.head_before
    # The single HEAD the graph's provenance is compared against, shared by the
    # dry plan and the real run (both read it from this one field).
    ctx.target_head = report.head_before

    # Run-scoped working store: the authoritative state.sqlite stays read-only.
    if not ctx.dry_run:
        try:
            _copy_store(real_db, ctx.db_path)
            ctx.con = store.connect(ctx.db_path)
        except Exception as exc:  # noqa: BLE001 - no working store, no writes
            report.degradations.append(
                f"run-scoped store copy failed ({type(exc).__name__}: {exc}); "
                "stage writes will be refused"
            )
            ctx.con = None
        ctx.record(ctx.db_path if ctx.db_path.exists() else None)

    # Producer gate: the honesty check that gates everything downstream.
    # A dry run reads the *authoritative* store read-only (nothing is copied,
    # nothing is written) so the plan can still report the real gate state.
    gate_con = ctx.con
    if ctx.dry_run:
        try:
            gate_con = _open_readonly(real_db) if real_db.exists() else None
        except Exception:  # noqa: BLE001 - reported through an empty gate
            gate_con = None
    if gate_con is not None:
        ctx.all_candidates = store.candidates_by_producer(gate_con)
        ctx.model_candidates = [
            c for c in ctx.all_candidates if store.may_back_model_claim(c)
        ]
        by_producer = store.candidates_by_producer(gate_con)
        counts: dict[str, int] = {}
        for row in by_producer:
            key = str(row.get("producer") or "unknown")
            counts[key] = counts.get(key, 0) + 1
        ctx.producer_counts = counts
        gated = store.model_produced_candidates(gate_con)
        if len(gated) != len(ctx.model_candidates):  # pragma: no cover - defensive
            ctx.notes.append(
                "producer gate disagreement between may_back_model_claim() and "
                "model_produced_candidates(); using the stricter (empty) reading"
            )
            ctx.model_candidates = []
    if ctx.dry_run and gate_con is not None:
        try:
            gate_con.close()
        except Exception:  # noqa: BLE001 - closing is best effort
            pass
    report.producer_gate = {
        "model_produced": len(ctx.model_candidates),
        "total": len(ctx.all_candidates),
        "by_producer": dict(sorted(ctx.producer_counts.items())),
        "endpoint_ok": bool(ctx.endpoint_ok),
        "endpoint_status": ctx.endpoint_status,
        "open": not ctx.model_candidates,
    }
    if not ctx.model_candidates:
        report.degradations.append(
            "producer gate: no model-produced candidates in the store "
            f"(producers: {ctx.producer_counts or 'none'}); mine/claims/assess blocked"
        )

    # The client is built only when the endpoint answered — never guessed.
    if client is not None:
        ctx.client, ctx.client_reason = client, "injected client"
    else:
        ctx.client, ctx.client_reason = _make_client(ctx)
    if ctx.client is None and ctx.endpoint_ok:
        ctx.notes.append(f"model client unavailable: {ctx.client_reason}")

    # --- stages ---------------------------------------------------------- #
    if ctx.dry_run:
        report.stages = [
            StageResult(
                name=name,
                status="skipped",
                reason=f"dry run: planned ({name}) — not executed",
            )
            for name in selected
        ]
        # Planning detail: ask each implementation to describe itself, with no
        # writes possible (ctx.dry_run is true, so every impl returns early).
        planned: list[StageResult] = []
        for name in selected:
            if name in ("mine", "claims", "assess") and not ctx.model_candidates:
                planned.append(
                    StageResult(name=name, status="blocked", reason=ctx.gate_reason(name))
                )
                continue
            planned.append(_run_stage(name, impls, ctx))
        report.stages = planned
    else:
        report.stages = [_run_stage(name, impls, ctx) for name in selected]

    # --- sealed window close --------------------------------------------- #
    report.head_after = _read_head(target_root)
    moved = bool(report.head_before) and report.head_before != report.head_after
    if ctx.dry_run:
        report.window_sealed = False
    elif moved:
        report.window_sealed = False
        report.degradations.append(
            "target HEAD moved during the run: "
            f"{report.head_before} -> {report.head_after} — window NOT sealed"
        )
    elif pf.quiescent is True and report.head_after is not None:
        report.window_sealed = True
    else:
        report.window_sealed = False
        report.degradations.append(
            "sealed window not proven: "
            + (
                f"target busy at start (verdict={(pf.writer_signal or {}).get('verdict', '?')})"
                if pf.quiescent is False
                else "quiescence was not measured"
            )
        )

    for stage in report.stages:
        if stage.status == "blocked" and stage.reason:
            report.degradations.append(f"{stage.name}: {stage.reason}")
    report.degradations.extend(d for d in ctx.degradations if d not in report.degradations)
    report.notes.extend(n for n in ctx.notes if n not in report.notes)
    report.artifacts = list(ctx.artifacts)
    report.exit_code = exit_code_for(
        preflight_failed=False,
        stages=report.stages,
        degradations=report.degradations,
        dry_run=ctx.dry_run,
    )
    report.finished_at = utcnow()
    report.finished_monotonic = time.monotonic()
    if ctx.con is not None:
        try:
            ctx.con.close()
        except Exception:  # noqa: BLE001 - closing is best effort
            pass
    _finalize_store(ctx)
    report.notes.extend(n for n in ctx.notes if n not in report.notes)
    return report


def format_report(report: RunReport, as_json: bool = False) -> str:
    """Human table or JSON for the CLI."""
    if as_json:
        return json.dumps(report.as_dict(), indent=2, sort_keys=True, default=str)
    lines = [
        f"resextract run: target={report.target} "
        f"{'DRY RUN — nothing written' if report.dry_run else 'done'}",
        f"  target root : {report.target_root}",
        f"  exit code   : {report.exit_code}",
        f"  window      : {'sealed' if report.window_sealed else 'NOT SEALED'}"
        + (
            f" (HEAD {str(report.head_before or '?')[:8]} -> "
            f"{str(report.head_after or '?')[:8]})"
            if report.head_before or report.head_after
            else ""
        ),
        f"  producer    : {report.producer_gate.get('model_produced', '?')} model-produced "
        f"of {report.producer_gate.get('total', '?')} candidate(s) "
        f"(endpoint http {report.producer_gate.get('endpoint_status', '?')})",
        "  stages:",
    ]
    for stage in report.stages:
        lines.append(f"    {stage.name:<12} {stage.status:<8} {stage.reason}")
        if stage.counts:
            lines.append(
                "        counts: " + ", ".join(f"{k}={v}" for k, v in sorted(stage.counts.items()))
            )
    if report.degradations:
        lines.append("  degradations:")
        for item in report.degradations:
            lines.append(f"    - {item}")
    return "\n".join(lines)
