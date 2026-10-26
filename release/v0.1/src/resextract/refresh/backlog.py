"""Turn measured staleness into specific, actionable rework entries.

Hard rule encoded here: ``model_suggested`` is ``False`` for anything derived
from a git fact or a measurement.  Measured entries are built only from
:class:`~resextract.refresh.staleness.ChangeReport` fields and link-check
digests, and their flag is hardcoded ``False`` — the ``model_suggested``
argument cannot turn a measurement into a suggestion.  It only decides whether
``suggestions`` (genuine LLM proposals, passed in explicitly) are marked.

Backlog files are append-only and deduplicated by ``sha1(reason|source_ref)``.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .staleness import (
    ChangeReport,
    _as_manifest,
    _manifest_dump,
    _span_text,
    iso_now,
    normalise_repo_path,
    short_sha,
)

BACKLOG_NAME = "UPDATE_BACKLOG.md"
WORK_SUGGESTIONS_NAME = "WORK_SUGGESTIONS.md"

HEADER = (
    "# UPDATE_BACKLOG — what would bring this item up to date\n"
    "\n"
    "> `[measured]` = derived from a git fact or a live measurement.\n"
    "> `[model-suggested]` = a proposal from a model, never a measured fact.\n"
    "> Append-only; entries are deduplicated by `key`.\n"
)

LINK_FIX = {
    "changed": "re-cite",
    "gone": "replace or re-verify",
    "suspect": "re-verify",
}


@dataclass(frozen=True)
class ReworkEntry:
    docket_slug: str
    reason: str
    required_work: str
    opened_at: str
    source_ref: str
    model_suggested: bool = False

    @property
    def key(self) -> str:
        raw = f"{self.reason}|{self.source_ref}".encode("utf-8")
        return hashlib.sha1(raw).hexdigest()[:12]

    @property
    def tag(self) -> str:
        return "model-suggested" if self.model_suggested else "measured"

    def line(self) -> str:
        return (
            f"- [{self.tag}] {self.required_work} — {self.reason} · "
            f"src=`{self.source_ref}` · opened=`{self.opened_at}` · key=`{self.key}`"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "docket_slug": self.docket_slug,
            "reason": self.reason,
            "required_work": self.required_work,
            "opened_at": self.opened_at,
            "source_ref": self.source_ref,
            "model_suggested": self.model_suggested,
            "key": self.key,
        }


def _slug_of(manifest: Any) -> str:
    dump = _manifest_dump(manifest)
    lane = dump.get("lane") or {}
    target = dump.get("target") or {}
    return str(lane.get("slug") or target.get("slug") or "docket")


def _field(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(name, default)
    return getattr(item, name, default)


def rework_entries(
    docket: Any,
    change: ChangeReport,
    link_changes: Iterable[Any] = (),
    *,
    model_suggested: bool = False,
    suggestions: Sequence[Any] = (),
    now: Any = None,
) -> list[ReworkEntry]:
    """Specific rework for one docket; measured entries always ``model_suggested=False``."""
    manifest = _as_manifest(docket)
    slug = _slug_of(manifest)
    opened = iso_now(now)
    entries: list[ReworkEntry] = []

    # -- measured: a cited file moved ------------------------------------- #
    from .staleness import claim_provenance_files

    cited = claim_provenance_files(manifest)
    head_ref = short_sha(change.new_head)
    for cid, kind, target_ref, span, resolved in cited:
        if not resolved:
            continue
        hit = None
        for cand in change.changed_files:
            c = normalise_repo_path(cand)
            if c == resolved or (
                c.rsplit("/", 1)[-1] == resolved.rsplit("/", 1)[-1]
                and ("/" in c) == ("/" in resolved)
            ):
                hit = c
                break
        if hit is None:
            continue
        if change.moved and change.old_head and change.new_head:
            reason = (
                f"`{hit}` changed in `{change.range}` (commit {head_ref})"
                + (f"; observed kind `{change.kind}`" if change.kind == "both" else "")
            )
            required = (
                f"re-verify claim {cid}, which cites {_span_text(span)}; "
                f"re-read the current `{hit}` and refresh the claim's evidence"
            )
            source_ref = f"git:{change.new_head}:{hit}"
        else:
            reason = (
                f"`{hit}` has uncommitted working-tree changes in the target "
                f"(observed at {short_sha(change.new_head, 8)})"
            )
            required = (
                f"re-verify claim {cid} after the working tree settles; it cites "
                f"{_span_text(span)} of `{hit}`"
            )
            source_ref = f"worktree:{hit}"
        if kind == "graph":
            source_ref = f"graph:{target_ref}->{hit}"
        entries.append(
            ReworkEntry(
                docket_slug=slug,
                reason=reason,
                required_work=required,
                opened_at=opened,
                source_ref=source_ref,
                model_suggested=False,
            )
        )

    # -- measured: a cited external source moved -------------------------- #
    for check in link_changes:
        url = str(_field(check, "url", "") or "")
        status = str(_field(check, "status", "") or "")
        if not url or status == "unchanged":
            continue
        old = short_sha(_field(check, "old_sha256"), 8)
        new = short_sha(_field(check, "new_sha256"), 8)
        err = _field(check, "error")
        if status == "changed":
            reason = f"cited evidence changed: {url} ({old} → {new})"
            required = (
                f"re-cite {url}: the live copy no longer matches the stored copy "
                f"({old} → {new}); re-verify every claim resting on it"
            )
        elif status == "gone":
            reason = f"cited evidence unreachable: {url}" + (f" ({err})" if err else "")
            required = (
                f"replace {url} or re-verify the claims resting on it: the URL no longer "
                f"resolves" + (f" ({err})" if err else "")
            )
        elif status == "suspect":
            suspicion = _field(check, "suspicion") or "payload too short to be evidence"
            reason = f"cited evidence returned a stub (suspect): {url} ({suspicion})"
            required = (
                f"re-verify {url}: the response was a stub, not content — "
                f"do not treat it as evidence ({suspicion})"
            )
        else:  # pragma: no cover - unknown statuses are reported, not dropped
            reason = f"cited evidence status `{status}`: {url}"
            required = f"inspect {url} and decide whether the claim still holds"
        entries.append(
            ReworkEntry(
                docket_slug=slug,
                reason=reason,
                required_work=required,
                opened_at=opened,
                source_ref=f"web:{url}",
                model_suggested=False,
            )
        )

    # -- genuine model proposals (never mixed with the above) ------------- #
    for item in suggestions:
        if isinstance(item, ReworkEntry):
            entries.append(
                ReworkEntry(
                    docket_slug=item.docket_slug or slug,
                    reason=item.reason,
                    required_work=item.required_work,
                    opened_at=item.opened_at or opened,
                    source_ref=item.source_ref,
                    model_suggested=bool(model_suggested),
                )
            )
        else:
            text = str(item)
            entries.append(
                ReworkEntry(
                    docket_slug=slug,
                    reason="model-proposed follow-up",
                    required_work=text,
                    opened_at=opened,
                    source_ref="model:suggestion",
                    model_suggested=bool(model_suggested),
                )
            )
    return entries


def _existing_keys(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        marker = "key=`"
        idx = line.find(marker)
        if idx >= 0:
            keys.add(line[idx + len(marker) :].split("`", 1)[0])
    return keys


def append_backlog(
    docket_dir: str | os.PathLike[str],
    entries: Sequence[ReworkEntry],
    *,
    filename: str = BACKLOG_NAME,
    dry_run: bool = False,
) -> list[ReworkEntry]:
    """Append entries that are not already present; return the ones added.

    Dedup key is ``(reason, source_ref)`` via :attr:`ReworkEntry.key`; ordering
    within a call is stable (``source_ref``, then ``reason``).
    """
    directory = Path(os.fspath(docket_dir))
    path = directory / filename
    existing = _existing_keys(path)
    ordered = sorted(entries, key=lambda e: (e.source_ref, e.reason, e.required_work))
    added: list[ReworkEntry] = []
    for entry in ordered:
        if entry.key in existing:
            continue
        existing.add(entry.key)
        added.append(entry)
    if not added or dry_run:
        return added
    directory.mkdir(parents=True, exist_ok=True)
    prefix = "" if path.is_file() and path.stat().st_size else HEADER
    with open(path, "a", encoding="utf-8") as fh:
        if prefix:
            fh.write(prefix)
        fh.write("\n".join(e.line() for e in added) + "\n")
    return added


def work_suggestions_text(
    entries: Sequence[ReworkEntry],
    *,
    slug: str = "",
    observed_head: str | None = None,
    change: ChangeReport | None = None,
    generated_at: str | None = None,
) -> str:
    stamp = generated_at or ""
    lines = ["# WORK_SUGGESTIONS — repo-level aggregate", ""]
    if stamp:
        lines.append(f"- generated: `{stamp}`")
    lines.extend(
        [
            f"- target: `{slug or '?'}` · observed head: `{short_sha(observed_head, 8)}`"
            + (f" · change: `{change.kind}` (`{change.range}`)" if change else ""),
            f"- entries: {len(entries)} (measured: {sum(1 for e in entries if not e.model_suggested)}, "
            f"model-suggested: {sum(1 for e in entries if e.model_suggested)})",
            "",
            "> `[measured]` entries are git facts / measurements. `[model-suggested]` entries are",
            "> proposals and must not be read as measured fact.",
            "",
        ]
    )
    if not entries:
        lines.append("_No rework required: no cited file moved, no link changed, no prior-art TTL expired._")
    for entry in sorted(entries, key=lambda e: (e.docket_slug, e.source_ref, e.reason)):
        lines.append(f"### {entry.docket_slug} · {entry.source_ref}")
        lines.append("")
        lines.append(entry.line())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_work_suggestions(
    path: str | os.PathLike[str],
    entries: Sequence[ReworkEntry],
    *,
    slug: str = "",
    observed_head: str | None = None,
    change: ChangeReport | None = None,
    generated_at: str | None = None,
    dry_run: bool = False,
) -> str | None:
    """Write the aggregate iff its content changed; ``None`` means nothing to do."""
    target = Path(os.fspath(path))
    text = work_suggestions_text(
        entries, slug=slug, observed_head=observed_head, change=change, generated_at=generated_at
    )
    if target.is_file() and target.read_text(encoding="utf-8") == text:
        return None
    if dry_run:
        return os.fspath(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return os.fspath(target)


def persist_rework(
    con: Any, entries: Sequence[ReworkEntry], *, docket_id: int | None = None
) -> tuple[int, list[str]]:
    """Persist to the ``rework`` table via ``store.open_rework``.

    ``source_ref`` / ``model_suggested`` are carried through: the table has both
    columns (schema v4), so the stored row states what the backlog entry stated.
    This docstring previously recorded the opposite ("no columns ... only reason +
    ``required_work`` survive"); that note was stale, and it made every persisted
    row look as though it had lost its provenance.
    """
    from resextract import store

    written = 0
    notes: list[str] = []
    for entry in entries:
        try:
            store.open_rework(
                con,
                docket_id=docket_id,
                reason=entry.reason,
                required_work=entry.required_work,
                source_ref=entry.source_ref,
                model_suggested=entry.model_suggested,
                opened_at=entry.opened_at,
            )
            written += 1
        except Exception as exc:  # pragma: no cover - schema drift
            notes.append(f"open_rework failed for {entry.source_ref}: {type(exc).__name__}: {exc}")
    if entries:
        notes.append(
            "rework rows persisted with reason+required_work+source_ref+model_suggested"
        )
    return written, notes
