"""Offline unit tests for the canned query battery.

Pure data: no subprocess, no network, no graphify.
"""

from __future__ import annotations

import dataclasses
import re

import pytest

from resextract.kg.queries import (
    BATTERY,
    KINDS,
    Query,
    all_queries,
    dedupe,
    queries_for,
    render,
)


def test_battery_is_non_empty_and_typed() -> None:
    battery = all_queries()
    assert battery, "the battery must not be empty"
    assert all(isinstance(q, Query) for q in battery)
    for query in battery:
        assert query.name and query.intent and query.template and query.why
        assert query.template == query.template.strip()


def test_query_names_are_unique() -> None:
    names = [q.name for q in all_queries()]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    assert not duplicates, f"duplicate query names: {duplicates}"
    assert len(names) == len(set(names))


def test_battery_covers_every_stage_two_area() -> None:
    covered = {q.kind for q in all_queries()}
    expected = {_slug(kind) for kind in KINDS}
    assert len(KINDS) == 11
    assert expected <= covered, sorted(expected - covered)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def test_templates_are_generic_no_repo_specific_strings() -> None:
    banned = ("duval", "/home/", "graphify", "resextract", "occamy", ".venv")
    for query in all_queries():
        lowered = query.template.lower()
        for needle in banned:
            assert needle not in lowered, f"{query.name} hard-codes {needle!r}"


def test_render_leaves_unknown_placeholders_intact() -> None:
    template = "where is {symbol} enforced for {subject} after {revision}"
    assert render(template) == template
    assert render(template, symbol="clamp") == "where is clamp enforced for {subject} after {revision}"
    assert render("{unknown}", known="x") == "{unknown}"


def test_render_substitutes_known_values_and_ignores_extras() -> None:
    assert render("what does {component} read", component="the loader", unused=1) == (
        "what does the loader read"
    )
    assert render("{n}", n=3) == "3"
    # literal braces and format specs are left alone rather than raising
    assert render("a {not an ident} b", **{"not an ident": "x"}) == "a {not an ident} b"
    assert render("json: {{'k': 1}}") == "json: {{'k': 1}}"
    assert render("no placeholders") == "no placeholders"


def test_dedupe_removes_duplicates_by_name_and_by_template() -> None:
    keep = Query(name="a", intent="k", template="{x} one", why="w")
    same_name = Query(name="a", intent="k", template="{x} two", why="w")
    same_template = Query(name="b", intent="k", template="{x} one", why="w")
    also_keep = Query(name="c", intent="k", template="{x} three", why="w")
    result = dedupe([keep, same_name, same_template, also_keep, keep])
    assert [q.name for q in result] == ["a", "c"]
    assert dedupe([]) == []
    assert all_queries() == dedupe(all_queries()), "the battery itself must be duplicate-free"


def test_queries_for_filters_by_kind_slug_or_text() -> None:
    novel = queries_for("novel-primitives")
    assert novel, "expected novel-primitives queries"
    assert all(q.kind == "novel-primitives" for q in novel)
    assert queries_for("novel primitives") == novel
    assert queries_for("NOVEL PRIMITIVES") == novel
    for kind in KINDS:
        assert queries_for(kind), f"no queries for {kind}"
    assert queries_for("no-such-area") == []
    assert queries_for("") == []


def test_all_queries_returns_a_fresh_mutable_copy() -> None:
    first = all_queries()
    first.append(Query(name="x", intent="y", template="z", why="w"))
    assert len(all_queries()) == len(BATTERY)
    assert len(BATTERY) == len(all_queries())


def test_query_is_frozen_and_kind_is_derived() -> None:
    query = all_queries()[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        query.name = "mutated"  # type: ignore[misc]
    assert query.kind == _slug(query.intent)
    assert query.fields() == tuple(
        dict.fromkeys(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", query.template))
    )
