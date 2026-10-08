"""Class guard: **every long flag the wrapper emits must exist in the real help**.

The defect this makes impossible to reintroduce
-----------------------------------------------
``Graphify.update()`` used to emit ``--graph``.  ``graphify update`` has no such
option, so the real CLI exited **2** with ``error: unknown update option:
--graph`` — and because the wrapper did not line-buffer its child either, the
failure arrived with no progress on stdout.  Two bugs, one class: *an argv the
wrapper invents that the tool does not accept*.

What this file checks
---------------------
1. :func:`parse_help` turns the captured, authoritative help text
   (``state/logs/graphify-0.9.80-help.txt`` for graphify **0.9.80**) into
   ``{subcommand -> {accepted long flags}}``.  Both help styles are handled:
   the indented flag block (``--backend B`` in ``extract``) and inline
   bracket declarations (``--backend=<name>`` in ``label``, and the whole
   ``export <kind>`` family).  See :data:`AMBIGUITIES` for where the help text
   is ambiguous and how attribution was resolved — never by silent skipping.
2. Every wrapper method that spawns a subprocess is invoked against
   ``Graphify(binary=..., dry_run=True)``, which runs the **same** argv builder
   as a live call but spawns nothing.  The argv's long flags are extracted and
   asserted to be a subset of that subcommand's accepted set.  All violations
   are collected and reported together, so fixing one class of bug cannot hide
   the other three.
3. ``--no-viz`` is legal for ``cluster-only`` and illegal for ``extract``;
   ``--graph`` is legal for ``cluster-only``/``query``/… and illegal for
   ``update``.  :func:`test_no_viz_scope_is_a_real_distinction` and
   :func:`test_graph_is_illegal_for_update` pin exactly those distinctions.

Red -> green proof (pasted verbatim, see also ``state/logs/U1.6-{red,green}.txt``)
---------------------------------------------------------------------------------
A deliberately bogus flag was injected into ``update()``'s argv builder::

    bools={"force": force, "no_cluster": no_cluster, "definitely_not_a_flag": True}

then the guard alone was run (red), the injection reverted, and the guard re-run
(green).  Verbatim output, also saved to ``state/logs/U1.6-red.txt`` and
``state/logs/U1.6-green.txt``::

    $ .venv/bin/python -m pytest tests/test_kg_graphify_flags.py -k flag_guard -q
    F                                                                        [100%]
    =================================== FAILURES ===================================
    _______________ test_flag_guard_every_wrapper_flag_is_documented _______________
    ...
    E       AssertionError: graphify flag guard failed:
    E           method update() emits --definitely-not-a-flag which graphify 'update' does not accept
    E       assert not ["method update() emits --definitely-not-a-flag which graphify 'update' does not accept"]
    =========================== short test summary info ============================
    FAILED tests/test_kg_graphify_flags.py::test_flag_guard_every_wrapper_flag_is_documented
    1 failed, 12 deselected in 0.03s

    $ cp state/kg-update-test/graphify.py.orig src/resextract/kg/graphify.py   # revert
    $ .venv/bin/python -m pytest tests/test_kg_graphify_flags.py -k flag_guard -q
    .                                                                        [100%]
    1 passed, 12 deselected in 0.02s

The red failure names all three things: the offending method (``update``), the
invented flag (``--definitely-not-a-flag``) and the subcommand (``'update'``).
The same red/green is reproducible in-process, with no source edit, by
:func:`test_guard_has_teeth_on_a_bogus_flag`.

Current status: 13 tests in this file (the guard, its teeth, the strict audit,
the two scope distinctions, the update fix, line buffering) and
``tests/test_kg_graphify.py`` still passes 12/12 unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import pytest

from resextract.kg.graphify import (
    LINE_BUFFER_PREFIX,
    Graphify,
    UnsupportedGraphTarget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HELP_PATH = PROJECT_ROOT / "state" / "logs" / "graphify-0.9.80-help.txt"

# A command declaration: exactly two leading spaces, then the command words.
# The second word is optional so that two-word forms ("global add",
# "hook install", "diagnose multigraph", "trae-cn install") match first.
_COMMAND_LINE = re.compile(
    r'^  (?P<cmd>[a-z][a-z0-9-]*(?: [a-z][a-z0-9-]*)?)(?=\s{2,}|\s+[<\[]|\s+"|$)'
)
_FLAG_TOKEN = re.compile(r"--([a-z][a-z0-9-]*)")

# --------------------------------------------------------------------------- #
# Help-text ambiguities (explicit, reported in the handoff — see unit U1.6)
# --------------------------------------------------------------------------- #

AMBIGUITIES: list[str] = [
    "clone: help declares 'clone <github-url>' (line 21) with no flag block of its "
    "own; its --branch / --out <dir> options are printed inside the *merge-graphs* "
    "flag block (lines 28-29). Attribution resolved by override: 'branch' and 'out' "
    "are credited to clone (see _HELP_ATTRIBUTION_OVERRIDES).",
    "merge-graphs: for the same reason '--branch' would be credited to merge-graphs "
    "and is removed by override (_HELP_ATTRIBUTION_REMOVALS); its own --out <path> "
    "(line 24) and --previous (line 25) are genuine.",
    "export <kind>: documents its flags inline in [...] brackets on the command and "
    "continuation lines (lines 124-135), unlike every other command's indented flag "
    "block. Per-kind attribution is exact: --no-viz/--node-limit exist only for "
    "'export html', --dir only for 'export obsidian', --labels for everything except "
    "graphml/neo4j/falkordb.",
    "no command-independent global flags exist in 0.9.80's help: --graph is "
    "re-declared per command and is deliberately absent from 'update' (that absence "
    "is the defect this file guards).",
    "install [--platform P] and uninstall --purge (lines 4-6) are parsed but not "
    "reachable from the wrapper, so they are not covered by the method matrix.",
    "merge-driver, prs and watch document no flags at all in 0.9.80.",
]

# --------------------------------------------------------------------------- #
# Deliberate deviations: a wrapper-emitted flag the help does NOT accept.
# Explicit allowlist entries with a reason — never a silent skip.
# --------------------------------------------------------------------------- #

KNOWN_DEVIATIONS: dict[tuple[str, str], str] = {
    ("extract", "no-viz"): (
        "extract() forwards --no-viz only when the caller explicitly passes "
        "no_viz=True. 0.9.80 documents --no-viz under cluster-only and the CLI "
        "rejects it for extract. A previous unit kept this opt-in deliberately "
        "(not a default); the guard therefore drives extract() with the default "
        "no_viz=False, and this entry plus "
        "test_extract_no_viz_is_illegal_and_deliberately_opt_in pin the deviation."
    ),
}


def parse_help(text: str) -> tuple[dict[str, frozenset[str]], list[str]]:
    """``{subcommand -> accepted long flags}`` from 0.9.80's help output.

    Attribution rule, stated explicitly:

    * a line indented by exactly two spaces and starting with a command word
      opens a new subcommand; any ``--flag`` written inline on that line belongs
      to it (this is how ``install [--platform P]`` and every ``export <kind>``
      are documented);
    * every subsequent line indented four or more spaces belongs to the current
      subcommand — both the ``    --flag VALUE`` blocks and any continuation
      prose.  Continuation prose only ever repeats a flag of the same command
      (``--password`` in the neo4j/falkordb notes), so this is safe;
    * a column-0 line (the trailing banner) closes the current subcommand;
    * the two exceptions found in the real text are applied from the override
      tables below and are listed in :data:`AMBIGUITIES`.
    """
    accepted: dict[str, set[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        match = _COMMAND_LINE.match(line)
        if match:
            current = match.group("cmd")
            accepted.setdefault(current, set())
            accepted[current].update(_FLAG_TOKEN.findall(line[match.end() :]))
            continue
        if line.startswith("    ") and current is not None:
            accepted[current].update(_FLAG_TOKEN.findall(line))
            continue
        if not line.startswith(" "):
            current = None
    for command, flags in _HELP_ATTRIBUTION_OVERRIDES.items():
        accepted.setdefault(command, set()).update(flags)
    for command, flags in _HELP_ATTRIBUTION_REMOVALS.items():
        accepted.setdefault(command, set()).difference_update(flags)
    return {command: frozenset(flags) for command, flags in accepted.items()}, list(AMBIGUITIES)


_HELP_ATTRIBUTION_OVERRIDES: dict[str, set[str]] = {
    # help lines 28-29: clone's flags, printed under merge-graphs' block
    "clone": {"branch", "out"},
}

_HELP_ATTRIBUTION_REMOVALS: dict[str, set[str]] = {
    # ... and therefore not merge-graphs' flag
    "merge-graphs": {"branch"},
}

# --------------------------------------------------------------------------- #
# The method matrix: (label, subcommand key, call -> CommandResult)
# --------------------------------------------------------------------------- #

Invocation = tuple[str, str, Callable[[Graphify], Any]]

_BOGUS = "definitely-not-a-flag"


def _export_invocations() -> list[Invocation]:
    """One invocation per ``export <kind>``, using only that kind's own flags."""
    specs: dict[str, dict[str, Any]] = {
        "html": {"graph": "/g.json", "labels": "/l.json", "node_limit": 5, "no_viz": True},
        "callflow-html": {"graph": "/g.json", "labels": "/l.json", "output": "/o.html"},
        "obsidian": {"graph": "/g.json", "labels": "/l.json", "dir": "/vault"},
        "wiki": {"graph": "/g.json", "labels": "/l.json"},
        "svg": {"graph": "/g.json", "labels": "/l.json"},
        "graphml": {"graph": "/g.json"},
        "neo4j": {"graph": "/g.json", "push": "neo4j://x", "user": "u", "password": "p"},
        "falkordb": {"graph": "/g.json", "push": "redis://x", "user": "u", "password": "p"},
    }
    return [
        (
            f"export({kind})",
            f"export {kind}",
            (lambda g, k=kind, kw=kwargs: g.export(k, **kw)),
        )
        for kind, kwargs in specs.items()
    ]


def _invocations() -> list[Invocation]:
    """Every subprocess-issuing method, with representative legal arguments."""
    calls: list[Invocation] = [
        (
            "extract",
            "extract",
            lambda g: g.extract(
                "/tmp/t",
                backend="ollama",
                model="m",
                max_concurrency=1,
                token_budget=1,
                code_only=True,
                out="/tmp/o",
                global_=True,
                as_="tag",
                no_cluster=True,
                mode="deep",
                api_timeout=1,
                max_workers=1,
                force=True,
                google_workspace=True,
                postgres="dsn",
                cargo=True,
                no_gitignore=True,
            ),
        ),
        (
            "cluster_only",
            "cluster-only",
            lambda g: g.cluster_only(
                "/tmp/t",
                no_viz=True,
                graph="/g.json",
                no_label=True,
                backend="ollama",
                model="m",
                max_concurrency=1,
                batch_size=1,
            ),
        ),
        ("update", "update", lambda g: g.update("/tmp/t", force=True, no_cluster=True)),
        (
            "label",
            "label",
            lambda g: g.label(
                "/tmp/t",
                backend="ollama",
                model="m",
                batch_size=1,
                max_concurrency=1,
                missing_only=True,
            ),
        ),
        (
            "query",
            "query",
            lambda g: g.query("q", graph="/g.json", budget=1, dfs=True, context=["c1", "c2"]),
        ),
        ("explain", "explain", lambda g: g.explain("x", graph="/g.json")),
        ("path", "path", lambda g: g.path("a", "b", graph="/g.json")),
        (
            "affected",
            "affected",
            lambda g: g.affected("x", depth=1, relation=["r1", "r2"], graph="/g.json"),
        ),
        ("god_nodes", "god-nodes", lambda g: g.god_nodes(top=1, json_=True, graph="/g.json")),
        (
            "diagnose_multigraph",
            "diagnose multigraph",
            lambda g: g.diagnose_multigraph(
                graph="/g.json",
                json_=True,
                max_examples=1,
                directed=True,
                undirected=True,
                extract_path="/x",
            ),
        ),
        (
            "add_url",
            "add",
            lambda g: g.add_url("https://e/x", dir="/d", author="a", contributor="c"),
        ),
        ("global_add", "global add", lambda g: g.global_add("/g.json", as_="t")),
        ("global_list", "global list", lambda g: g.global_list()),
        ("global_path", "global path", lambda g: g.global_path()),
        ("global_remove", "global remove", lambda g: g.global_remove("tag")),
        ("hook_install", "hook install", lambda g: g.hook_install()),
        ("hook_uninstall", "hook uninstall", lambda g: g.hook_uninstall()),
        ("hook_status", "hook status", lambda g: g.hook_status()),
        (
            "save_result",
            "save-result",
            lambda g: g.save_result(
                "q",
                "a",
                type_="query",
                nodes=["n1", "n2"],
                outcome="useful",
                correction="c",
                memory_dir="/m",
            ),
        ),
        (
            "reflect",
            "reflect",
            lambda g: g.reflect(
                memory_dir="/m",
                out="/o.md",
                graph="/g.json",
                analysis="/a.json",
                labels="/l.json",
                half_life_days=1,
                min_corroboration=1,
            ),
        ),
        ("clone", "clone", lambda g: g.clone("https://e/r", branch="b", out="/o")),
        (
            "merge_graphs",
            "merge-graphs",
            lambda g: g.merge_graphs(["/a.json", "/b.json"], out="/o.json", previous="/p.json"),
        ),
        ("benchmark", "benchmark", lambda g: g.benchmark("/g.json")),
        (
            "tree",
            "tree",
            lambda g: g.tree(
                graph="/g.json",
                output="/o.html",
                root="/r",
                max_children=1,
                top_k_edges=1,
                label="L",
            ),
        ),
        ("check_update", "check-update", lambda g: g.check_update("/tmp/t")),
        ("watch", "watch", lambda g: g.watch("/tmp/t")),
        ("provider", "provider", lambda g: g.provider("list")),
    ]
    return calls + _export_invocations()


def _dry_graphify() -> Graphify:
    """A wrapper that builds argv exactly like a live one but spawns nothing."""
    return Graphify(binary=PROJECT_ROOT / ".venv" / "bin" / "graphify", dry_run=True)


def _emitted_long_flags(result: Any, subcommand: str) -> list[str]:
    """Long flags in ``result.argv``, after checking the declared subcommand words."""
    argv = [str(a) for a in result.argv]
    words = subcommand.split()
    assert argv[1 : 1 + len(words)] == words, (
        f"argv {argv[1:1 + len(words)]} does not start with the declared subcommand "
        f"{subcommand!r}: {argv}"
    )
    return [arg[2:] for arg in argv if arg.startswith("--")]


def _guard_violations(
    accepted: dict[str, frozenset[str]],
    invocations: list[Invocation],
    deviations: dict[tuple[str, str], str] | None = None,
) -> list[str]:
    """Every emitted flag the real CLI would reject, all at once, naming method/flag/cmd.

    ``deviations`` defaults to :data:`KNOWN_DEVIATIONS`; pass ``{}`` to see what the
    guard would report with no allowlist at all (that is how the deviation tests
    prove the guard would otherwise catch ``extract --no-viz``).
    """
    allowed = KNOWN_DEVIATIONS if deviations is None else deviations
    violations: list[str] = []
    for label, subcommand, call in invocations:
        try:
            result = call(_dry_graphify())
            flags = _emitted_long_flags(result, subcommand)
        except AssertionError as exc:  # subcommand key / matrix drift
            violations.append(f"method {label}(): {exc}")
            continue
        legal = accepted.get(subcommand, frozenset())
        for flag in flags:
            if flag in legal:
                continue
            if (subcommand, flag) in allowed:
                continue
            violations.append(
                f"method {label}() emits --{flag} which graphify {subcommand!r} does not accept"
            )
    return violations


# --------------------------------------------------------------------------- #
# The guard
# --------------------------------------------------------------------------- #


def test_flag_guard_every_wrapper_flag_is_documented() -> None:
    """THE class guard: no wrapper method may invent a flag its subcommand rejects."""
    help_text = HELP_PATH.read_text(encoding="utf-8")
    accepted, ambiguities = parse_help(help_text)
    assert ambiguities, "ambiguity list must not be empty"
    violations = _guard_violations(accepted, _invocations())
    assert not violations, "graphify flag guard failed:\n  " + "\n  ".join(violations)


def test_guard_has_teeth_on_a_bogus_flag() -> None:
    """Same guard, fed a synthetic bogus argv: it must name method, flag and subcommand."""
    accepted, _ = parse_help(HELP_PATH.read_text(encoding="utf-8"))

    class _Stub:
        def __init__(self, argv: list[str]) -> None:
            self.argv = argv

    bogus = _BOGUS
    invocations: list[Invocation] = [
        (
            "update",
            "update",
            lambda g: _Stub([str(g.binary), "update", "/tmp/t", f"--{bogus}"]),
        )
    ]
    violations = _guard_violations(accepted, invocations)
    assert len(violations) == 1, violations
    assert "update" in violations[0]
    assert f"--{bogus}" in violations[0]
    assert "'update'" in violations[0]


def test_strict_audit_finds_only_the_documented_deviation() -> None:
    """Requirement 4's audit, machine-checked: no *other* argv defect exists.

    The only wrapper-emitted flag the 0.9.80 help rejects is the deliberately
    opt-in ``extract --no-viz``; every other method's argv is clean.
    """
    accepted, _ = parse_help(HELP_PATH.read_text(encoding="utf-8"))
    strict: set[tuple[str, str, str]] = set()
    # The matrix deliberately drives extract() with its default no_viz=False, so add
    # an explicit probe for the opt-in deviation; otherwise the strict set would be
    # empty and the audit could not tell "no deviation" from "deviation not probed".
    probes: list[Invocation] = [
        ("extract", "extract", lambda g: g.extract("/tmp/t", no_viz=True)),
    ]
    for label, subcommand, call in _invocations() + probes:
        result = call(_dry_graphify())
        for flag in _emitted_long_flags(result, subcommand):
            if flag not in accepted.get(subcommand, frozenset()):
                strict.add((label, subcommand, flag))
    assert strict == {("extract", "extract", "no-viz")}, (
        "undocumented wrapper argv defects: "
        f"{sorted(strict - {('extract', 'extract', 'no-viz')})}"
    )


# --------------------------------------------------------------------------- #
# The two scope distinctions that matter
# --------------------------------------------------------------------------- #


def test_no_viz_scope_is_a_real_distinction() -> None:
    """``--no-viz`` is documented for cluster-only and NOT for extract."""
    accepted, _ = parse_help(HELP_PATH.read_text(encoding="utf-8"))
    assert "no-viz" in accepted["cluster-only"]
    assert "no-viz" not in accepted["extract"]
    assert "no-viz" not in accepted["update"]


def test_extract_no_viz_is_illegal_and_deliberately_opt_in() -> None:
    """The wrapper keeps emitting --no-viz only when explicitly asked (no regression)."""
    accepted, _ = parse_help(HELP_PATH.read_text(encoding="utf-8"))
    assert "no-viz" not in accepted["extract"]
    g = _dry_graphify()
    assert "--no-viz" not in list(g.extract("/tmp/t").argv)
    assert "--no-viz" in list(g.extract("/tmp/t", no_viz=True).argv)
    assert KNOWN_DEVIATIONS[("extract", "no-viz")], "deviation must carry a reason"


def test_no_viz_emitted_for_extract_would_be_caught() -> None:
    """If extract() ever emitted --no-viz by default, the guard must fail."""
    accepted, _ = parse_help(HELP_PATH.read_text(encoding="utf-8"))

    class _Stub:
        def __init__(self, argv: list[str]) -> None:
            self.argv = argv

    invocations: list[Invocation] = [
        (
            "extract",
            "extract",
            lambda g: _Stub([str(g.binary), "extract", "/tmp/t", "--no-viz"]),
        )
    ]
    violations = _guard_violations(accepted, invocations, deviations={})
    assert len(violations) == 1 and "--no-viz" in violations[0], violations
    # ... and the same argv IS legal for cluster-only, which is the distinction.
    assert "no-viz" in accepted["cluster-only"]


def test_graph_is_illegal_for_update_and_the_wrapper_never_emits_it() -> None:
    """The reported defect: ``--graph`` is unknown to ``update`` (raw CLI exit 2)."""
    accepted, _ = parse_help(HELP_PATH.read_text(encoding="utf-8"))
    assert "graph" not in accepted["update"]
    assert "graph" in accepted["cluster-only"]
    g = _dry_graphify()
    for kwargs in ({}, {"force": True}, {"no_cluster": True}, {"force": True, "no_cluster": True}):
        assert "--graph" not in list(g.update("/tmp/t", **kwargs).argv), kwargs
    # the implied default is the only graph location update() can accept: no-op
    assert "--graph" not in list(
        g.update("/tmp/t", graph="/tmp/t/graphify-out/graph.json").argv
    )


def test_update_rejects_a_foreign_graph_location_with_a_typed_error() -> None:
    """A different graph file is a clear typed error, not a flag the CLI rejects."""
    g = _dry_graphify()
    with pytest.raises(UnsupportedGraphTarget) as excinfo:
        g.update("/tmp/t", graph="/elsewhere/graph.json")
    message = str(excinfo.value)
    assert "cannot target an arbitrary graph file" in message
    assert "/tmp/t/graphify-out/graph.json" in message
    assert "cluster-only" in message
    assert excinfo.value.graph == "/elsewhere/graph.json"
    # the failed call is still journal-visible, and nothing was spawned
    assert g.history == []


# --------------------------------------------------------------------------- #
# Line buffering: applied once, in the shared runner
# --------------------------------------------------------------------------- #


def test_stdbuf_prefix_is_applied_once_in_the_shared_runner() -> None:
    """The argv the runner receives starts with ``stdbuf -oL -eL``."""
    g = _dry_graphify()
    result = g.god_nodes(top=3, graph="/g.json")
    assert tuple(result.spawn_argv[:3]) == LINE_BUFFER_PREFIX == ("stdbuf", "-oL", "-eL")
    assert tuple(result.spawn_argv[3:]) == tuple(result.argv)
    # ``argv`` keeps its long-standing contract (binary first) for existing callers
    assert str(result.argv[0]).endswith("graphify")
    assert result.argv[1] == "god-nodes"


def test_stdbuf_is_applied_to_every_method() -> None:
    g = _dry_graphify()
    for label, _subcommand, call in _invocations():
        result = call(g)
        assert tuple(result.spawn_argv[:3]) == LINE_BUFFER_PREFIX, label


def test_line_buffering_can_be_opted_out() -> None:
    """Per instance and per call — and the wrapper still works either way."""
    off = Graphify(
        binary=PROJECT_ROOT / ".venv" / "bin" / "graphify", dry_run=True, line_buffer=False
    )
    assert list(off.god_nodes().spawn_argv) == list(off.god_nodes().argv)
    on = _dry_graphify()
    per_call = on.run("god-nodes", line_buffer=False)
    assert list(per_call.spawn_argv) == list(per_call.argv)
    assert tuple(on.run("god-nodes").spawn_argv[:3]) == LINE_BUFFER_PREFIX


def test_missing_stdbuf_fails_soft_with_a_recorded_note() -> None:
    g = Graphify(binary=PROJECT_ROOT / ".venv" / "bin" / "graphify", dry_run=True)
    g.stdbuf = None  # simulate a host without GNU coreutils
    g.notes.clear()
    result = g.god_nodes()
    assert list(result.spawn_argv) == list(result.argv)


def test_real_child_still_works_under_stdbuf() -> None:
    """A genuine spawn (no dry_run) with the stdbuf prefix must exit 0."""
    g = Graphify(cwd=PROJECT_ROOT)
    result = g.run("--version")
    assert result.ok and result.exit_code == 0
    assert "graphify" in result.stdout.lower()
    assert tuple(result.spawn_argv[:3]) == LINE_BUFFER_PREFIX
