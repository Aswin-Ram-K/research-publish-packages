"""The refresh run: notice a move, re-check citations, write the rework.

``refresh_target`` is idempotent by construction.  Every write goes through
:func:`_write_if_changed` (content compared before replacing) or through
:func:`~resextract.refresh.backlog.append_backlog` (deduplicated by key), and
per-docket history/prior-art appends are guarded by a small ledger
(``.refresh_ledger.json``) recording what has already been recorded.  A second
run with nothing new therefore writes **nothing** and reports ``noop=True``.

Deliberate decision: the refresh never bumps ``target.head_sha`` in
``MANIFEST.json``.  That field records the head the docket's *content* was
verified against; silently advancing it would declare a stale item current.
The observed head lands in ``HISTORY.md``, the ledger and the report instead.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ..docket.manifest import (
    DocketManifest,
    Freshness as ManifestFreshness,
    read_manifest,
    write_manifest,
)
from ..kg import Graphify, read_graph
from ..web.fetch import Fetcher
from .backlog import (
    WORK_SUGGESTIONS_NAME,
    ReworkEntry,
    append_backlog,
    persist_rework,
    rework_entries,
    write_work_suggestions,
)
from .staleness import (
    ChangeReport,
    Freshness,
    TargetState,
    _as_dt,
    detect_change,
    freshness_for,
    iso_now,
    read_target_state,
    short_sha,
)

LINK_STATUSES = ("unchanged", "changed", "gone", "suspect")
LEDGER_NAME = ".refresh_ledger.json"
HISTORY_NAME = "HISTORY.md"
PRIOR_ART_NAME = "PRIOR_ART_REFRESH.md"

#: Below this drift, a recomputed ``age_days`` is not a meaningful manifest
#: change (~15 minutes) and must not turn a no-op run into a write.
AGE_EPSILON_DAYS = 0.01

HISTORY_HEADER = "# HISTORY — append-only\n"
PRIOR_ART_HEADER = "# PRIOR_ART_REFRESH — external re-checks (append-only)\n"


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class LinkCheck:
    url: str
    status: str
    old_sha256: str | None = None
    new_sha256: str | None = None
    http_status: int | None = None
    error: str | None = None
    note: str | None = None
    usable_chars: int = 0
    suspicion: str | None = None
    checked_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "status": self.status,
            "old_sha256": self.old_sha256,
            "new_sha256": self.new_sha256,
            "old8": short_sha(self.old_sha256, 8),
            "new8": short_sha(self.new_sha256, 8),
            "http_status": self.http_status,
            "error": self.error,
            "note": self.note,
            "usable_chars": self.usable_chars,
            "suspicion": self.suspicion,
        }


@dataclass(frozen=True)
class GraphRefresh:
    slug: str
    copy_dir: str
    graph_path: str
    original_graph: str | None
    original_sha256: str | None
    original_unchanged: bool
    copy_sha256: str | None
    nodes: int | None
    edges: int | None
    updated: bool
    affected_files: tuple[str, ...] = field(default=())
    affected_nodes: tuple[str, ...] = field(default=())
    note: str | None = None
    #: The head the staged copy was ACTUALLY copied at (ground truth: the copy's
    #: own ``.git``), never the head merely observed at run time (defect U7.2-2).
    staged_from_head: str | None = None
    #: Whether this run had to re-stage the copy because the provenance label
    #: did not match the copy's real content.
    restaged: bool = False

    @property
    def copy_sha8(self) -> str:
        return short_sha(self.copy_sha256, 8)

    @property
    def original_sha8(self) -> str:
        return short_sha(self.original_sha256, 8)

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "copy_dir": self.copy_dir,
            "graph_path": self.graph_path,
            "original_graph": self.original_graph,
            "original_sha256": self.original_sha256,
            "original_sha8": self.original_sha8,
            "original_unchanged": self.original_unchanged,
            "copy_sha256": self.copy_sha256,
            "copy_sha8": self.copy_sha8,
            "nodes": self.nodes,
            "edges": self.edges,
            "updated": self.updated,
            "affected_files": list(self.affected_files),
            "affected_nodes": list(self.affected_nodes)[:200],
            "note": self.note,
            "staged_from_head": self.staged_from_head,
            "staged_from_head8": short_sha(self.staged_from_head, 8),
            "restaged": self.restaged,
        }


@dataclass
class DocketRefresh:
    slug: str
    dir: str
    old_head: str | None
    freshness: Freshness
    links: tuple[LinkCheck, ...] = field(default=())
    backlog: tuple[ReworkEntry, ...] = field(default=())
    written: list[str] = field(default_factory=list)
    note: str | None = None

    @property
    def state(self) -> str:
        return self.freshness.state

    @property
    def reasons(self) -> tuple[str, ...]:
        return self.freshness.reasons

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "dir": self.dir,
            "old_head": self.old_head,
            "state": self.state,
            "reasons": list(self.reasons),
            "age_days": self.freshness.age_days,
            "links": [c.as_dict() for c in self.links],
            "backlog": [e.as_dict() for e in self.backlog],
            "written": list(self.written),
            "note": self.note,
        }


@dataclass
class RefreshReport:
    target: str
    slug: str
    observed: TargetState
    change: ChangeReport
    dockets: list[DocketRefresh] = field(default_factory=list)
    links: list[LinkCheck] = field(default_factory=list)
    graph: GraphRefresh | None = None
    recorded_head: str | None = None
    recorded_head_source: str | None = None
    written: list[str] = field(default_factory=list)
    planned: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    noop: bool = True
    dry_run: bool = False
    wall_s: float = 0.0
    run_id: str = ""

    @property
    def checked_links(self) -> int:
        return len(self.links)

    @property
    def changed_links(self) -> int:
        return sum(1 for c in self.links if c.status == "changed")

    @property
    def gone_links(self) -> int:
        return sum(1 for c in self.links if c.status == "gone")

    @property
    def suspect_links(self) -> int:
        return sum(1 for c in self.links if c.status == "suspect")

    def as_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "slug": self.slug,
            "run_id": self.run_id,
            "observed": self.observed.as_dict(),
            "recorded_head": self.recorded_head,
            "recorded_head_source": self.recorded_head_source,
            "change": self.change.as_dict(),
            "graph": self.graph.as_dict() if self.graph else None,
            "dockets": [d.as_dict() for d in self.dockets],
            "links": [c.as_dict() for c in self.links],
            "checked_links": self.checked_links,
            "changed_links": self.changed_links,
            "gone_links": self.gone_links,
            "suspect_links": self.suspect_links,
            "written": list(self.written),
            "planned": list(self.planned),
            "noop": self.noop,
            "dry_run": self.dry_run,
            "wall_s": self.wall_s,
            "notes": list(self.notes),
        }


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _sha256_file(path: str | os.PathLike[str]) -> str | None:
    p = Path(os.fspath(path))
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _write_if_changed(path: Path, text: str, *, dry_run: bool, planned: list[str]) -> bool:
    """Replace ``path`` only when its bytes differ.  ``True`` == "this is a write"."""
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == text:
                return False
        except OSError:
            pass
    if dry_run:
        planned.append(os.fspath(path))
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return True


def _append(path: Path, text: str, *, dry_run: bool, planned: list[str]) -> bool:
    """Append + return True (guards decide whether appending is warranted)."""
    if dry_run:
        planned.append(os.fspath(path))
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)
    return True


def _resolve_docket_dirs(docket_dirs: Any) -> list[str]:
    if docket_dirs is None:
        base = Path.cwd() / "dockets"
        return [os.fspath(p) for p in sorted(base.glob("*")) if (p / "MANIFEST.json").is_file()]
    if isinstance(docket_dirs, (str, os.PathLike)):
        docket_dirs = [docket_dirs]
    out = [os.fspath(d) for d in docket_dirs if (Path(os.fspath(d)) / "MANIFEST.json").is_file()]
    return out


def _recorded_head(
    manifests: Mapping[str, DocketManifest], slug: str, db_path: Any = None
) -> tuple[str | None, str | None]:
    for ddir, manifest in manifests.items():
        head = manifest.target.head_sha
        if head:
            return head, f"docket:{ddir}"
    try:
        from resextract import store

        con = store.connect(db_path)
        row = store.get_target(con, slug)
        if row and row.get("head_sha"):
            return str(row["head_sha"]), "store:targets"
    except Exception:  # pragma: no cover - store is optional here
        return None, None
    return None, None


def _reconcile_links(checks: Sequence[LinkCheck], manifest: DocketManifest) -> list[LinkCheck]:
    """Re-base a link's status on the sha256 the *docket recorded*, not the fetcher cache.

    ``Fetcher.refresh`` compares against its own cache, which the first run
    overwrites; the docket's stored sha is the only stable baseline.  Without
    this, a second run would flip ``changed`` to ``unchanged`` and break no-op
    idempotence.
    """
    recorded = {ws.url: ws.sha256 for ws in manifest.web_sources if ws.url}
    out: list[LinkCheck] = []
    for check in checks:
        want = recorded.get(check.url)
        if want and check.status in ("changed", "unchanged"):
            status = "unchanged" if check.new_sha256 == want else "changed"
            check = replace(check, status=status)
        out.append(check)
    return out


def classify_fetch(url: str, result: Any, *, now: Any = None) -> LinkCheck:
    """Map a ``Fetcher.refresh`` result onto ``unchanged|changed|gone|suspect``.

    A suspect payload is reported as ``suspect`` — never as ``unchanged``.
    """
    detail = getattr(result, "detail", None) or {}
    meta = getattr(result, "meta", None)
    if not getattr(result, "ok", False):
        status = "gone"
    elif getattr(result, "suspect", False):
        status = "suspect"
    elif getattr(result, "changed", False):
        status = "changed"
    else:
        status = "unchanged"
    return LinkCheck(
        url=url,
        status=status,
        old_sha256=detail.get("old_sha256"),
        new_sha256=detail.get("new_sha256") or (getattr(meta, "sha256", None) if meta else None),
        http_status=getattr(meta, "http_status", None) if meta else None,
        error=getattr(result, "error", None),
        note=getattr(result, "note", None),
        usable_chars=int(getattr(result, "usable_chars", 0) or 0),
        suspicion=getattr(result, "suspicion", None),
        checked_at=iso_now(now),
    )


def check_cited_links(
    urls: Sequence[str],
    *,
    fetcher: Any,
    max_link_checks: int = 25,
    pace_s: float = 0.0,
    now: Any = None,
) -> list[LinkCheck]:
    """Re-fetch up to ``max_link_checks`` cited URLs, paced; never raises."""
    out: list[LinkCheck] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        if len(out) >= max(0, int(max_link_checks)):
            break
        try:
            result = fetcher.refresh(url)
        except Exception as exc:  # a broken fetcher must not abort the run
            out.append(
                LinkCheck(
                    url=url,
                    status="gone",
                    error=f"{type(exc).__name__}: {exc}",
                    checked_at=iso_now(now),
                )
            )
            continue
        out.append(classify_fetch(url, result, now=now))
        if pace_s:
            time.sleep(float(pace_s))
    return out


def _run_graphify_update(copy_dir: Path, *, timeout: float) -> tuple[bool, int, str]:
    """Run ``graphify update <copy_dir>`` under ``stdbuf`` (the binary block-buffers off-TTY).

    Checked for the flagged foreign-``graph=`` call (U7.2): this module never
    calls ``Graphify.update`` at all, and passes **no** ``graph``/``--graph``
    argument.  ``Graphify.update`` now raises ``UnsupportedGraphTarget`` for a
    foreign ``graph=`` and no longer builds ``--graph``.  The child is spawned
    directly (rather than through the wrapper) only so ``stdbuf`` can be wrapped
    around it and the copy's explicit path stays visible; ``graphify update``
    always rewrites ``<copy_dir>/graphify-out/graph.json``.
    """
    try:
        binary = Graphify().binary
    except Exception as exc:  # pragma: no cover
        return False, 127, f"cannot resolve graphify binary: {exc}"
    argv = ["stdbuf", "-oL", "-eL", os.fspath(binary), "update", os.fspath(copy_dir)]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        tail = (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else ""
        return False, -1, f"graphify update timed out after {timeout}s\n{tail}"
    except OSError as exc:
        return False, 127, f"{type(exc).__name__}: {exc}"
    tail = ((proc.stdout or "") + (proc.stderr or ""))[-2000:]
    return proc.returncode == 0, proc.returncode, tail


def _stage_repo_copy(target: str, copy_root: Path) -> bool:
    """Copy the target tree (minus node_modules/.worktrees) into ``copy_root``."""
    if (copy_root / ".git").exists() or (copy_root / "package.json").exists() or (
        copy_root / "README.md"
    ).exists():
        return False
    copy_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        target,
        copy_root,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("node_modules", ".worktrees"),
        symlinks=True,
    )
    return True


def _copy_head(copy_root: Path) -> str | None:
    """The head of the *staged copy itself* — ground truth for its provenance.

    Reads the copy's own ``.git`` with the staleness module's read-only git
    runner.  ``None`` when the copy carries no readable HEAD, which the reuse
    guard treats as "cannot prove currency" and therefore re-stages.
    """
    from .staleness import _git

    rc, out, _err = _git(copy_root, "rev-parse", "HEAD")
    if rc != 0:
        return None
    sha = out.strip().splitlines()[0].strip() if out.strip() else ""
    return sha or None


def _place_graph(orig: Path, gpath: Path, copy_root: Path) -> None:
    """Copy the preserved graph (and its sidecars) into the staged copy.

    The sidecars land in the **copy's** ``graphify-out`` (``gpath.parent``), not
    back onto the source directory.
    """
    (copy_root / "graphify-out").mkdir(parents=True, exist_ok=True)
    shutil.copy2(orig, gpath)
    for extra in ("manifest.json", ".graphify_root"):
        src = orig.parent / extra
        if src.is_file():
            shutil.copy2(src, gpath.parent / extra)
    (gpath.parent / ".graphify_root").write_text(os.fspath(copy_root), encoding="utf-8")


def _restage_repo_copy(target: str, copy_root: Path, orig: Path, gpath: Path) -> None:
    """Discard the staged copy and copy the target tree again, then re-place the graph.

    Re-staging is the fail-toward-correctness branch: a copy whose provenance
    label does not match its real content cannot be trusted to hold the files of
    the head we are about to record.
    """
    shutil.rmtree(copy_root, ignore_errors=True)
    _stage_repo_copy(target, copy_root)
    _place_graph(orig, gpath, copy_root)


def _graph_refresh(
    target: str,
    slug: str,
    observed: TargetState,
    change: ChangeReport,
    *,
    state_root: Path,
    kg_root: Path,
    original_graph: Any = None,
    run_update: bool = True,
    dry_run: bool = False,
    timeout: float = 900.0,
    notes: list[str] | None = None,
) -> tuple[GraphRefresh | None, Any]:
    """Copy the graph out of the verify-preserved tree, update the copy, read it back."""
    notes = notes if notes is not None else []
    orig = Path(os.fspath(original_graph)) if original_graph else kg_root / slug / "graphify-out" / "graph.json"
    root = state_root / "kg-refresh" / slug
    copy_root = root / "repo"
    gpath = copy_root / "graphify-out" / "graph.json"
    orig_before = _sha256_file(orig)

    if not orig.is_file():
        notes.append(f"no original graph at {orig}: graph refresh skipped")
        return GraphRefresh(
            slug=slug,
            copy_dir=os.fspath(copy_root),
            graph_path=os.fspath(gpath),
            original_graph=os.fspath(orig),
            original_sha256=None,
            original_unchanged=True,
            copy_sha256=None,
            nodes=None,
            edges=None,
            updated=False,
            note=f"no original graph at {orig}",
        ), None

    state_path = root / "graph_state.json"
    prior_state = _read_json(state_path)
    updated = False
    note: str | None = None
    staged_head: str | None = None
    restaged = False

    if dry_run:
        note = "dry_run: graph copy/staging skipped"
        if not gpath.is_file():
            return GraphRefresh(
                slug=slug,
                copy_dir=os.fspath(copy_root),
                graph_path=os.fspath(gpath),
                original_graph=os.fspath(orig),
                original_sha256=orig_before,
                original_unchanged=_sha256_file(orig) == orig_before,
                copy_sha256=None,
                nodes=None,
                edges=None,
                updated=False,
                affected_files=tuple(change.changed_files),
                note=note,
            ), None
    else:
        current_head = observed.head_sha
        copy_exists = gpath.is_file()
        current_sha = _sha256_file(gpath) if copy_exists else None
        copy_head = _copy_head(copy_root) if copy_exists else None
        raw_label = prior_state.get("staged_from_head")
        prior_label = raw_label if isinstance(raw_label, str) and raw_label else None
        raw_observed = prior_state.get("observed_head")
        prior_observed = raw_observed if isinstance(raw_observed, str) and raw_observed else None

        # The reuse guard compares the head the copy was ACTUALLY staged from —
        # and the head its own .git reports — never a label that merely claims a
        # head.  Anything unprovable fails toward re-staging, not toward speed.
        restage_reason: str | None = None
        if not copy_exists:
            restage_reason = "no staged graph copy"
        elif current_head is None:
            restage_reason = "current head is not observable: re-stage rather than reuse"
        elif prior_label is None:
            restage_reason = (
                "graph_state.json has no staged_from_head "
                f"(legacy observed_head={short_sha(prior_observed, 8) or 'none'}) — invalidated"
            )
        elif prior_label != current_head:
            restage_reason = (
                f"copy staged from {short_sha(prior_label, 8)} but the target head is "
                f"{short_sha(current_head, 8)}: re-staging"
            )
        elif copy_head is None:
            restage_reason = "staged copy carries no readable HEAD: currency unprovable"
        elif copy_head != prior_label:
            restage_reason = (
                f"copy content is at {short_sha(copy_head, 8)} but the label claims "
                f"{short_sha(prior_label, 8)}: label does not match the copy — re-staging"
            )
        elif prior_observed is not None and prior_observed != prior_label:
            restage_reason = (
                f"previous observed_head {short_sha(prior_observed, 8)} disagreed with "
                f"staged_from_head {short_sha(prior_label, 8)} — label not trusted"
            )
        elif prior_state.get("graph_sha256") != current_sha:
            restage_reason = "staged graph sha256 does not match the recorded one"

        if restage_reason is not None:
            if copy_exists:
                _restage_repo_copy(target, copy_root, orig, gpath)
                restaged = True
            else:
                copy_root.mkdir(parents=True, exist_ok=True)
                if _stage_repo_copy(target, copy_root):
                    notes.append(
                        f"staged target copy at {copy_root} (node_modules/.worktrees excluded)"
                    )
                _place_graph(orig, gpath, copy_root)
            notes.append(f"graph copy staged at {short_sha(current_head, 8) or 'unknown'}: {restage_reason}")

        if staged_head is None:
            staged_head = current_head or _copy_head(copy_root)

        reuse = restage_reason is None
        if reuse:
            note = f"graph copy already reflects {short_sha(observed.head_sha, 8)}: update skipped"
        elif run_update:
            ok, rc, tail = _run_graphify_update(copy_root, timeout=timeout)
            updated = ok
            note = f"graphify update rc={rc}: {tail.strip().splitlines()[-1] if tail.strip() else ''}"
            if not ok:
                notes.append(f"graphify update on the copy failed (rc={rc})")
        else:
            note = "graph update disabled by caller"

        # Written only when the copy actually moved: a reuse pass at an unchanged
        # head must leave graph_state.json byte-identical (true no-op).
        if restaged or updated or not state_path.is_file():
            payload = {
                "schema": "resextract/refresh-graph/2",
                "observed_head": observed.head_sha,
                "staged_from_head": staged_head,
                "copy_head": _copy_head(copy_root),
                "graph_sha256": _sha256_file(gpath),
                "updated_at": iso_now(),
            }
            _write_if_changed(
                state_path, json.dumps(payload, sort_keys=True, indent=2) + "\n", dry_run=False, planned=[]
            )

    graph_obj = None
    nodes = edges = None
    copy_sha = _sha256_file(gpath)
    if gpath.is_file():
        try:
            graph_obj = read_graph(gpath)
            stats = graph_obj.stats()
            nodes, edges = stats.nodes, stats.edges
        except Exception as exc:  # pragma: no cover - malformed copy
            notes.append(f"cannot read copy graph {gpath}: {type(exc).__name__}: {exc}")

    affected_nodes: list[str] = []
    if graph_obj is not None and change.changed_files:
        wanted = set(change.changed_files)
        for node in graph_obj.nodes:
            src = (getattr(node, "source_file", "") or "").replace("\\", "/")
            if src and src in wanted:
                affected_nodes.append(node.id)

    return (
        GraphRefresh(
            slug=slug,
            copy_dir=os.fspath(copy_root),
            graph_path=os.fspath(gpath),
            original_graph=os.fspath(orig),
            original_sha256=orig_before,
            original_unchanged=_sha256_file(orig) == orig_before,
            copy_sha256=copy_sha,
            nodes=nodes,
            edges=edges,
            updated=updated,
            affected_files=tuple(change.changed_files),
            affected_nodes=tuple(affected_nodes),
            note=note,
            staged_from_head=staged_head,
            restaged=restaged,
        ),
        graph_obj,
    )


# --------------------------------------------------------------------------- #
# per-docket application
# --------------------------------------------------------------------------- #


def _apply_docket(
    ddir: str,
    manifest: DocketManifest,
    *,
    fresh: Freshness,
    change: ChangeReport,
    observed: TargetState,
    entries: Sequence[ReworkEntry],
    links: Sequence[LinkCheck],
    now_iso: str,
    prior_art_ttl_days: float,
    dry_run: bool,
    planned: list[str],
    written: list[str],
) -> list[str]:
    """Write what changed for one docket; return the paths touched-or-planned."""
    touched: list[str] = []
    directory = Path(ddir)
    ledger_path = directory / LEDGER_NAME
    ledger = _read_json(ledger_path)
    new_ledger = dict(ledger)

    # 1. MANIFEST.json — only when the state or a meaningful age_days moved.
    dump = manifest.model_dump(mode="json", by_alias=True)
    old_fresh = dump.get("freshness") or {}
    old_state = str(old_fresh.get("state") or "current")
    old_age = old_fresh.get("age_days")
    age_moved = (
        old_age is None
        or fresh.age_days is None
        or abs(float(fresh.age_days) - float(old_age)) >= AGE_EPSILON_DAYS
    )
    if old_state != fresh.state or age_moved:
        updated = manifest.model_copy(
            update={
                "freshness": ManifestFreshness(
                    verified_at=old_fresh.get("verified_at"),
                    prior_art_checked_at=old_fresh.get("prior_art_checked_at"),
                    age_days=fresh.age_days,
                    state=fresh.state,  # type: ignore[arg-type]
                )
            }
        )
        text = json.dumps(updated.model_dump(mode="json", by_alias=True), sort_keys=True, indent=2) + "\n"
        if dry_run:
            planned.append(os.fspath(directory / "MANIFEST.json"))
            touched.append(os.fspath(directory / "MANIFEST.json"))
        else:
            write_manifest(directory, updated)  # validates; raises only on a really invalid docket
            written.append(os.fspath(directory / "MANIFEST.json"))
            touched.append(os.fspath(directory / "MANIFEST.json"))

    # 2. HISTORY.md — append only for a genuinely new event.  This ledger guard
    #    is what makes a repeat run a no-op: a head move already recorded must
    #    not be re-recorded.
    state_changed = bool(ledger) and ledger.get("last_state") != fresh.state
    head_is_new = bool(ledger) and ledger.get("last_observed_head") != observed.head_sha
    first_change = (not ledger) and change.kind != "none"
    event_new = state_changed or head_is_new or first_change
    if event_new:
        reasons = "; ".join(fresh.reasons) or "no reason recorded"
        counts = (
            f"- links: {len(links)} checked · "
            f"{sum(1 for c in links if c.status == 'changed')} changed · "
            f"{sum(1 for c in links if c.status == 'gone')} gone · "
            f"{sum(1 for c in links if c.status == 'suspect')} suspect"
        )
        block = (
            f"\n## {now_iso} — refresh\n\n"
            f"- head `{short_sha(change.old_head)}` → `{short_sha(observed.head_sha)}` · "
            f"kind `{change.kind}` · commits between: "
            f"{change.commits_between if change.commits_between is not None else 'n/a'}"
            + (f" · note `{change.note}`" if change.note else "")
            + "\n"
            f"- changed files: {len(change.changed_files)}"
            + (f" (truncated)" if change.truncated else "")
            + "\n"
            f"- freshness: `{fresh.state}` — {reasons}\n"
            f"{counts}\n"
            f"- observed mtime digest `{observed.mtime_digest[:16]}` · "
            f"dirty paths: {len(observed.dirty_paths)}\n"
        )
        history_path = directory / HISTORY_NAME
        if not history_path.is_file() and not dry_run:
            history_path.write_text(HISTORY_HEADER, encoding="utf-8")
        elif not history_path.is_file() and dry_run:
            planned.append(os.fspath(history_path))
        if _append(history_path, block, dry_run=dry_run, planned=planned):
            touched.append(os.fspath(history_path))
            if not dry_run:
                written.append(os.fspath(history_path))
        new_ledger["last_observed_head"] = observed.head_sha
        new_ledger["last_state"] = fresh.state

    # 3. PRIOR_ART_REFRESH.md — what moved externally, digest-guarded.
    external = [f"- `{f}` changed in `{change.range}` (commit {short_sha(change.new_head)})" for f in change.changed_files[:50]]
    external += [
        f"- link `{c.url}`: {c.status} (`{short_sha(c.old_sha256, 8)}` → `{short_sha(c.new_sha256, 8)}`)"
        + (f" — {c.error}" if c.error else "")
        for c in links
        if c.status != "unchanged"
    ]
    if external:
        body = (
            f"\n## {now_iso} — external re-check (`{change.kind}`, target @ `{short_sha(observed.head_sha)}`)\n\n"
            + "\n".join(external)
            + "\n"
        )
        digest = hashlib.sha1(body.encode("utf-8")).hexdigest()
        if ledger.get("prior_art_digest") != digest:
            prior_path = directory / PRIOR_ART_NAME
            if not prior_path.is_file() and not dry_run:
                prior_path.write_text(PRIOR_ART_HEADER, encoding="utf-8")
            elif not prior_path.is_file() and dry_run:
                planned.append(os.fspath(prior_path))
            if _append(prior_path, body, dry_run=dry_run, planned=planned):
                touched.append(os.fspath(prior_path))
                if not dry_run:
                    written.append(os.fspath(prior_path))
            new_ledger["prior_art_digest"] = digest

    # 4. UPDATE_BACKLOG.md — append-only, deduplicated.
    added = append_backlog(directory, entries, dry_run=dry_run)
    if added:
        path = os.fspath(directory / "UPDATE_BACKLOG.md")
        touched.append(path)
        if not dry_run:
            written.append(path)

    # 5. ledger — records what has been recorded, so the next run is a no-op.
    new_ledger.setdefault("schema", "resextract/refresh-ledger/1")
    new_ledger["last_refresh_at"] = now_iso
    new_ledger["last_range"] = change.range
    # Never create a ledger just to say "nothing happened": a pristine no-op run
    # writes no files at all.
    if new_ledger != ledger and (ledger or touched):
        text = json.dumps(new_ledger, sort_keys=True, indent=2) + "\n"
        if _write_if_changed(ledger_path, text, dry_run=dry_run, planned=planned):
            touched.append(os.fspath(ledger_path))
            if not dry_run:
                written.append(os.fspath(ledger_path))

    return touched


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #


def refresh_target(
    target_path: str | os.PathLike[str],
    *,
    docket_dirs: Any = None,
    prior_art_ttl_days: float = 30,
    check_links: bool = True,
    dry_run: bool = False,
    max_link_checks: int = 25,
    slug: str | None = None,
    now: Any = None,
    fetcher: Any = None,
    state_root: Any = None,
    kg_root: Any = None,
    original_graph: Any = None,
    run_graph_update: bool = True,
    graph_timeout: float = 900.0,
    persist_store: bool = False,
    db_path: Any = None,
    pace_s: float = 0.0,
) -> RefreshReport:
    """Notice a target move, invalidate dockets, re-check citations, write rework."""
    started = time.monotonic()
    now_dt = _as_dt(now) or datetime.now(timezone.utc)
    stamp = iso_now(now_dt)
    target = os.path.abspath(os.fspath(target_path))
    state_root_p = Path(state_root) if state_root else Path.cwd() / "state"
    kg_root_p = Path(kg_root) if kg_root else state_root_p / "kg"
    slug = slug or Path(target).name.lower().replace(" ", "-")

    notes: list[str] = []
    dirs = _resolve_docket_dirs(docket_dirs)
    manifests: dict[str, DocketManifest] = {}
    for ddir in dirs:
        try:
            manifests[ddir] = read_manifest(ddir)
        except Exception as exc:
            notes.append(f"cannot read MANIFEST.json in {ddir}: {type(exc).__name__}: {exc}")

    observed = read_target_state(target, now=now_dt)
    recorded_head, recorded_source = _recorded_head(manifests, slug, db_path)
    change = detect_change(
        recorded_head, observed.head_sha, target, dirty_paths=observed.dirty_paths
    )
    notes.extend(change.errors)
    notes.extend(change.warnings)

    graph_refresh = None
    graph_obj = None
    if change.moved:
        graph_refresh, graph_obj = _graph_refresh(
            target,
            slug,
            observed,
            change,
            state_root=state_root_p,
            kg_root=kg_root_p,
            original_graph=original_graph,
            run_update=run_graph_update,
            dry_run=dry_run,
            timeout=graph_timeout,
            notes=notes,
        )

    checks: list[LinkCheck] = []
    if check_links:
        urls: list[str] = []
        for manifest in manifests.values():
            urls.extend(ws.url for ws in manifest.web_sources if ws.url)
        if urls:
            fetcher = fetcher if fetcher is not None else Fetcher(cache_dir=state_root_p / "webcache")
            checks = check_cited_links(
                urls,
                fetcher=fetcher,
                max_link_checks=max_link_checks,
                pace_s=pace_s,
                now=now_dt,
            )

    planned: list[str] = []
    written: list[str] = []
    dockets: list[DocketRefresh] = []
    all_entries: list[ReworkEntry] = []

    for ddir in dirs:
        manifest = manifests.get(ddir)
        if manifest is None:
            continue
        mine = {ws.url for ws in manifest.web_sources if ws.url}
        docket_links = _reconcile_links([c for c in checks if c.url in mine], manifest)
        docket_status = {c.url: c.status for c in docket_links}
        fresh = freshness_for(
            manifest,
            change,
            now=now_dt,
            prior_art_ttl_days=prior_art_ttl_days,
            graph=graph_obj,
            link_status=docket_status,
        )
        entries = rework_entries(manifest, change, docket_links, now=now_dt)
        all_entries.extend(entries)
        touched = _apply_docket(
            ddir,
            manifest,
            fresh=fresh,
            change=change,
            observed=observed,
            entries=entries,
            links=docket_links,
            now_iso=stamp,
            prior_art_ttl_days=prior_art_ttl_days,
            dry_run=dry_run,
            planned=planned,
            written=written,
        )
        dockets.append(
            DocketRefresh(
                slug=str(manifest.lane.slug),
                dir=ddir,
                old_head=manifest.target.head_sha,
                freshness=fresh,
                links=tuple(docket_links),
                backlog=tuple(entries),
                written=touched,
            )
        )

    run_id = f"{now_dt.strftime('%Y%m%dT%H%M%SZ')}-{short_sha(observed.head_sha)}"
    agg_path = state_root_p / "refresh" / short_sha(observed.head_sha) / WORK_SUGGESTIONS_NAME
    agg = write_work_suggestions(
        agg_path,
        all_entries,
        slug=slug,
        observed_head=observed.head_sha,
        change=change,
        generated_at="",
        dry_run=dry_run,
    )
    if agg:
        planned.append(agg)
        if not dry_run:
            written.append(agg)

    if persist_store and not dry_run and all_entries:
        try:
            from resextract import store

            con = store.connect(db_path)
            docket_id = None
            row = store.get_docket_by_dir(con, dirs[0]) if dirs else None
            if row:
                docket_id = int(row["id"])
            count, store_notes = persist_rework(con, all_entries, docket_id=docket_id)
            notes.append(f"persisted {count} rework entries to the store")
            notes.extend(store_notes)
        except Exception as exc:
            notes.append(f"store persistence skipped: {type(exc).__name__}: {exc}")

    return RefreshReport(
        target=target,
        slug=slug,
        observed=observed,
        change=change,
        dockets=dockets,
        links=checks,
        graph=graph_refresh,
        recorded_head=recorded_head,
        recorded_head_source=recorded_source,
        written=written,
        planned=planned,
        notes=notes,
        noop=not written and not planned,
        dry_run=dry_run,
        wall_s=round(time.monotonic() - started, 3),
        run_id=run_id,
    )
