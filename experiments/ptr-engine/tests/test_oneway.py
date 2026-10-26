"""The one-way rule, asserted structurally rather than documented.

There is no public callable in the package that accepts a ``ResourceRef`` and
returns a ``Reference``. This test does not trust the docs: it imports every module,
calls every public function and public method with a ``ResourceRef`` as the first
argument, and fails if any of them returns a ``Reference``. A function that refuses
the argument (raising) is compliant -- refusing is the correct answer.

A *synthetic* ``ResourceRef`` is not enough to prove that: a registry-backed bridge
that answers only refs ``resolve()`` really issued would pass it while working end
to end (V-ENGINE-P0 check 2b). So the behavioural guard below resolves a real
reference, keeps the exact object ``resolve()`` returned, proves it is issued by
opening its bytes, and only then sweeps the public surface with it.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest

import ptr_engine
from ptr_engine import BodyStore, Reference, ResourceRef

DUMMY = ResourceRef(
    scheme="artifact",
    locator="ab/" + "a" * 64 + ".txt",
    hash="sha256:" + "a" * 64,
    pin="rev:1",
)

DENIED_NAMES = (
    "to_reference",
    "reference_from",
    "from_resource_ref",
    "resourceref_to_reference",
    "resourceref_to_ref",
)


def _modules():
    for info in pkgutil.iter_modules(ptr_engine.__path__):
        yield importlib.import_module(f"ptr_engine.{info.name}")


def _public_callables():
    for module in _modules():
        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                yield f"{module.__name__}.{name}", obj, inspect.signature(obj), False
            elif inspect.isclass(obj) and obj.__module__ == module.__name__:
                for attr, member in vars(obj).items():
                    if attr.startswith("_") or not callable(member):
                        continue
                    if isinstance(member, (staticmethod, classmethod)):
                        raw = member.__func__
                        skip = 0
                    else:
                        raw = member
                        skip = 1
                    try:
                        sig = inspect.signature(raw)
                    except (TypeError, ValueError):  # pragma: no cover
                        continue
                    yield f"{module.__name__}.{obj.__name__}.{attr}", raw, sig, skip


def test_no_public_callable_turns_a_resourceref_into_a_reference():
    offenders: list[str] = []
    examined = 0
    for label, func, sig, skip in _public_callables():
        params = [
            p
            for p in sig.parameters.values()
            if p.kind
            in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)
        ][skip:]
        if not params:
            continue
        args = [DUMMY] + [None] * (len(params) - 1)
        try:
            result = func(*args)
        except Exception:
            examined += 1
            continue  # refusing a ResourceRef is the compliant answer
        examined += 1
        if isinstance(result, Reference):
            offenders.append(f"{label} -> Reference")
    assert examined > 10, "the sweep found almost nothing; it is not doing its job"
    assert offenders == []


def test_no_denied_helper_name_exists_anywhere():
    found = []
    for module in _modules():
        for name, obj in vars(module).items():
            if isinstance(obj, type) and issubclass(obj, Exception):
                continue  # PtrUnresolvedRefError is an error name, not a bridge
            lowered = name.lower()
            if any(denied in lowered for denied in DENIED_NAMES):
                found.append(f"{module.__name__}.{name}")
    assert found == []


def test_resolve_rejects_a_resourceref_by_name(index):
    from ptr_engine import Scope, resolve
    from ptr_engine.errors import PtrNotAReferenceError

    scope = Scope(name="sess-01", index=index)
    with pytest.raises(PtrNotAReferenceError) as excinfo:
        resolve(DUMMY, scope)  # type: ignore[arg-type]
    assert excinfo.value.code == "PTR_NOT_A_REFERENCE"


def test_store_get_returns_bytes_never_a_reference(store):
    ref = store.put(b"content")
    assert isinstance(store.get(ref), bytes)


def test_resolved_target_does_not_remember_its_namespace(scope, store, index):
    """Content identity survives losing the reference it was reached through."""
    from ptr_engine import parse, resolve

    target = resolve(parse("@knowledge:k01@3"), scope)
    assert set(target.__dataclass_fields__) == {"scheme", "locator", "hash", "pin"}
    assert not any(
        word in target.locator for word in ("knowledge", "k01", "sess-01")
    )
    assert store.get(target).startswith(b"knowledge note 1")


# --- the behavioural guard ---------------------------------------------------
# Call every public callable with a ResourceRef that resolve() actually issued.
# Any callable that turns one back into a Reference is a bridge and fails here.

FILLERS: tuple[tuple[object, ...], ...] = ((), (None,))


def _sweep(rref: ResourceRef, extras_grid: tuple[tuple[object, ...], ...]):
    """Sweep the public surface with ``rref``; return ``(offenders, examined)``."""
    offenders: list[str] = []
    examined = 0
    for label, func, sig, skip in _public_callables():
        pos = [
            p
            for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)
        ][skip:]
        kwonly = [
            p
            for p in sig.parameters.values()
            if p.kind is p.KEYWORD_ONLY and p.default is p.empty
        ]
        if not pos and kwonly:
            examined += 1
            kwargs = {p.name: (rref if n == 0 else None) for n, p in enumerate(kwonly)}
            try:
                result = func(**kwargs)
            except Exception:
                continue
            if isinstance(result, Reference):
                offenders.append(f"{label}(**{{{kwonly[0].name}: ResourceRef}}) -> Reference")
            continue
        for extras in extras_grid:
            args = [rref] + [
                extras[i] if i < len(extras) else None for i in range(len(pos) - 1)
            ]
            examined += 1
            try:
                result = func(*args)
            except Exception:
                continue  # refusing a ResourceRef is the compliant answer
            if isinstance(result, Reference):
                offenders.append(f"{label} -> Reference")
    return offenders, examined


def test_no_public_callable_turns_a_resolve_issued_resourceref_into_a_reference(
    scope, store, index
):
    from ptr_engine import PtrError, parse, resolve

    real = resolve(parse("@knowledge:k01@3"), scope)
    assert isinstance(real, ResourceRef)
    # Behavioural proof this is the ref resolve() issued, and DUMMY is not one:
    # only an issued ref opens the stored body.
    assert store.get(real).startswith(b"knowledge note 1")
    with pytest.raises(PtrError):
        store.get(DUMMY)

    offenders, examined = _sweep(real, FILLERS + ((scope,), (store,), (index,)))
    assert examined > 10, "the sweep found almost nothing; it is not doing its job"
    assert offenders == []


def test_no_public_callable_turns_an_issued_region_ref_into_a_reference(scope, store, index):
    from ptr_engine import parse, resolve

    region = resolve(parse("@artifact:plan#/goal@3"), scope)
    assert isinstance(region, ResourceRef)
    assert b"resolve lazily" in store.get(region)
    offenders, examined = _sweep(region, FILLERS + ((scope,), (store,), (index,)))
    assert examined > 10
    assert offenders == []
