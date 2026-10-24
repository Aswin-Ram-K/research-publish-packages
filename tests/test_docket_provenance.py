"""U5.7 — the producer gate, **enforced**, and a docket's provenance **visible**.

Before this unit, ``store.may_back_model_claim()`` existed and **nothing called
it**: every docket ever built was replay-derived, and nothing inside the artifact
said so.  An independent verifier called that out as the remaining half of FAIL A
(a replay-produced candidate stored indistinguishably from a model-mined one).

The three claims this module pins, all offline (fixture store + fixture target +
fixture dockets, no network, no model):

1. **Derivation.** A docket's ``generated_by.producer`` is derived from its lane's
   *member candidates* in the store, through the store's own join — never guessed
   by the renderer.  ``model`` / ``replay`` / ``mixed`` / ``unknown``.
2. **The gate bites.** A docket whose producer is not ``model`` is never written
   ``status="ready"``: the default run records ``draft`` plus a ``status_reason``
   that names the producer, and a caller that *explicitly* asks for ``ready`` gets
   :class:`~resextract.docket.materialize.PromotionRefused` instead of a silently
   promoted artifact.
3. **The warning is visible in the artifact**, in ``README.md`` *and*
   ``CHECKLIST.md``, derived from the manifest itself (so re-assembly cannot drop
   it) and absent for a model-produced docket (a warning shown everywhere is a
   warning nobody reads).

Two of these are the unit's **red→green guards**, and each test's docstring
carries the pasted evidence: the failure with the guard reverted, and the pass
with it restored (sha256-identical restore, ``PYTHONDONTWRITEBYTECODE=1``).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

try:  # pragma: no cover - the venv normally has the package importable
    import resextract  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resextract import store
from resextract.docket import assemble as A
from resextract.docket import manifest as M
from resextract.docket import materialize as MAT

REPO = Path(__file__).resolve().parents[1]
SMOKE = REPO / "dockets" / "_smoke"
LANE_SLUG = "prov-lane"
TARGET_SLUG = "fixture"

# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #


def _store_with_members(tmp_path: Path, producers):
    """A real (migrated) store holding one lane and its member candidates.

    ``producers`` is a sequence of ``(producer, model_id)`` pairs.  Rows go in
    through the store's own writer, so every CHECK constraint applies: a bogus
    producer cannot be smuggled into a fixture.
    """
    db = tmp_path / "store.sqlite"
    store.init_db(db)
    con = store.connect(db)
    lane_id = store.upsert_lane(
        con, target=TARGET_SLUG, slug=LANE_SLUG, type="report", status="draft"
    )
    ids = []
    for index, (producer, model) in enumerate(producers, start=1):
        cid = store.insert_candidate(
            con,
            kind="claim",
            title=f"Fixture claim {index}",
            summary=f"Fixture claim {index} rests on the guide.",
            provenance_json=[{"kind": "file_lines", "ref": "docs/GUIDE.md#L1-L3"}],
            score=1.0,
            state="unverified",
            producer=producer,
            model=model,
        )
        con.execute(
            "INSERT OR IGNORE INTO lane_candidates(lane_id, candidate_id) VALUES (?, ?)",
            (lane_id, cid),
        )
        ids.append(cid)
    con.commit()
    return db, con, lane_id, ids


def _target(tmp_path: Path) -> Path:
    root = tmp_path / "target"
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "GUIDE.md").write_text(
        "# Guide\n\nline two\nline three\nline four\n", encoding="utf-8"
    )
    return root


def _lane() -> MAT.LaneSpec:
    return MAT.LaneSpec(
        slug=LANE_SLUG,
        title="Provenance fixture lane",
        thesis="A docket must say who produced its candidates.",
        audience="the verifier",
        type="report",
        members=[MAT.MemberSpec("C1", provenance_refs=["docs/GUIDE.md#L1-L3"])],
        target_slug=TARGET_SLUG,
        head_sha=None,
    )


def _run(tmp_path: Path, db: Path, target: Path, **kw):
    kw.setdefault("window_s", 0.0)
    return MAT.materialize_lane(
        _lane(),
        target_root=str(target),
        docket_root=str(tmp_path / "dockets"),
        db_path=db,
        **kw,
    )


def _manifest_obj(producer: str, **kw) -> M.DocketManifest:
    generated_by = {"app": "resextract", "version": "0.1.0", "model": None}
    if producer is not None:
        generated_by["producer"] = producer
    return M.DocketManifest(
        lane={"slug": "x", "type": "memo"},
        target={"slug": "fixture"},
        generated_by=generated_by,
        **kw,
    )


# --------------------------------------------------------------------------- #
# 1. derivation
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "producers,expected,expected_model",
    [
        ([("model", "fixture-model-U5.7")], "model", "fixture-model-U5.7"),
        ([("replay", None), ("replay", None)], "replay", None),
        ([("model", "fixture-model-U5.7"), ("fixture", None)], "mixed", None),
        ([("unknown", None)], "unknown", None),
        ([], "unknown", None),
        # fixture-only is not a model: it collapses to the gate's safe answer
        ([("fixture", None)], "unknown", None),
        # "any replay ⇒ replay" precedes the mixture clause: a docket that rests
        # partly on replay is replay-tainted, and the more damning label wins.
        ([("model", "m"), ("replay", None)], "replay", None),
    ],
)
def test_derivation_from_fixture_store_rows(tmp_path, producers, expected, expected_model):
    """The producer comes from the lane's member candidates, via the store join."""
    db, con, _lane_id, _ids = _store_with_members(tmp_path, producers)
    try:
        rows = MAT.lane_member_candidates(con, target_slug=TARGET_SLUG, lane_slug=LANE_SLUG)
        assert len(rows) == len(producers)
        assert MAT.derive_producer(rows) == expected
        assert MAT.model_id_for(expected, rows) == expected_model
    finally:
        con.close()


def test_unknown_lane_derives_unknown_not_model(tmp_path):
    """A lane the store does not know cannot accidentally look model-produced."""
    db, con, _lane_id, _ids = _store_with_members(tmp_path, [("model", "m")])
    try:
        assert MAT.lane_member_candidates(con, target_slug=TARGET_SLUG, lane_slug="nope") == []
        assert MAT.derive_producer([]) == "unknown"
    finally:
        con.close()


def test_derived_producer_is_recorded_in_the_manifest(tmp_path):
    """The derivation reaches MANIFEST.json, not just the return value."""
    db, con, _lane_id, _ids = _store_with_members(tmp_path, [("replay", None)])
    con.close()
    result = _run(tmp_path, db, _target(tmp_path))
    raw = json.loads((Path(result.docket_dir) / "MANIFEST.json").read_text(encoding="utf-8"))
    assert raw["generated_by"]["producer"] == "replay"
    assert raw["generated_by"]["model"] is None
    assert result.producer == "replay"
    assert result.member_candidate_count == 1


# --------------------------------------------------------------------------- #
# 2. the gate  (RED->GREEN guard a)
# --------------------------------------------------------------------------- #


def test_guard_a_non_model_docket_can_never_be_ready(tmp_path):
    """RED->GREEN **guard (a): non-model ⇒ never ``status="ready"``.**

    Reverting the gate (``docket_status = status if producer == "model" else
    "draft"`` → ``docket_status = status``, and the explicit-request raise made
    unreachable) makes this test fail like this::

        E           Failed: DID NOT RAISE PromotionRefused
        FAILED tests/test_docket_provenance.py::test_guard_a_non_model_docket_can_never_be_ready

    Restored (sha256-identical), it passes::

        1 passed in 0.14s

    Why it matters: the real store holds 10 ``replay`` candidates and 0
    ``model``, so without this gate *every* docket this build produces would be
    written ``ready`` while resting on candidates that must not back a
    model-derived claim.
    """
    for producer, members in (
        ("replay", [("replay", None)]),
        ("mixed", [("model", "fixture-model-U5.7"), ("fixture", None)]),
        ("unknown", [("unknown", None)]),
    ):
        case = tmp_path / producer
        case.mkdir()
        db, con, _lane_id, _ids = _store_with_members(case, members)
        con.close()
        target = _target(case)

        # the honest default: build it, label it, do not hide it
        result = _run(case, db, target)
        assert result.status == "draft", producer
        assert result.status_reason and producer in result.status_reason, producer
        assert result.manifest.status == "draft"
        assert result.manifest.status_reason == result.status_reason
        assert result.manifest.generated_by.producer == producer
        assert M.promotion_eligible(result.manifest)[0] is False
        assert "producer gate (U5.7)" in (Path(result.docket_dir) / "HISTORY.md").read_text(
            encoding="utf-8"
        )

        # an explicit promotion attempt is refused, never silently promoted
        with pytest.raises(MAT.PromotionRefused) as caught:
            _run(case, db, target, status="ready")
        assert producer in str(caught.value)
        assert caught.value.producer == producer


def test_model_docket_may_be_ready_and_is_promotion_eligible(tmp_path):
    """``model`` + ``ready`` is the *only* promotable combination."""
    db, con, _lane_id, _ids = _store_with_members(
        tmp_path, [("model", "fixture-model-U5.7")]
    )
    con.close()
    target = _target(tmp_path)
    result = _run(tmp_path, db, target)
    assert result.producer == "model"
    assert result.status == "draft"  # not promoted by default
    assert result.manifest.generated_by.model == "fixture-model-U5.7"
    assert M.promotion_eligible(result.manifest) == (False, "status is 'draft', not 'ready'")

    promoted = _run(tmp_path, db, target, status="ready")
    assert promoted.status == "ready"
    assert promoted.status_reason is None
    assert M.promotion_eligible(promoted.manifest) == (True, None)


# --------------------------------------------------------------------------- #
# 3. the warning  (RED->GREEN guard b)
# --------------------------------------------------------------------------- #


def test_guard_b_replay_warning_is_visible_in_readme_and_checklist(tmp_path):
    """RED->GREEN **guard (b): the visible warning, for replay (and mixed).**

    Reverting the warning (``provenance_warning`` forced to ``return None``)
    makes this test fail like this::

        E               AssertionError: replay: warning missing from README.md
        E               assert 'PROVENANCE: replay-produced' in '# Provenance fixture lane — report docket\n\n**Status:** draft · **Type:** report · **Target:** `fixture` @ `(unknown...t | lines | bytes | sha256 |\n| --- | --- | --- | --- |\n| `material/docs/GUIDE.md` | 1-3 | 39 | `2ae206e9a63f…` |\n\n'

    Restored (sha256-identical), it passes::

        1 passed in 0.12s

    The line is rendered from ``ctx["manifest"].generated_by.producer``, so
    re-assembling the same folder cannot drop it.
    """
    for producer, members, needle in (
        ("replay", [("replay", None)], "PROVENANCE: replay-produced"),
        (
            "mixed",
            [("model", "fixture-model-U5.7"), ("fixture", None)],
            "PROVENANCE: mixed-produced",
        ),
    ):
        case = tmp_path / producer
        case.mkdir()
        db, con, _lane_id, _ids = _store_with_members(case, members)
        con.close()
        result = _run(case, db, _target(case))
        readme = (Path(result.docket_dir) / "README.md").read_text(encoding="utf-8")
        checklist = (Path(result.docket_dir) / "CHECKLIST.md").read_text(encoding="utf-8")
        for name, text in (("README.md", readme), ("CHECKLIST.md", checklist)):
            assert needle in text, f"{producer}: warning missing from {name}"
            assert "Not eligible for publication until real mining runs." in text
            # near the top, where a reader cannot miss it
            assert text.index(needle) < 800, f"{producer}: warning buried in {name}"
        if producer == "mixed":
            assert "mixed" in readme.split("Not eligible")[0]


def test_model_docket_carries_no_warning(tmp_path):
    """``model`` gets no warning — do not train readers to ignore it."""
    db, con, _lane_id, _ids = _store_with_members(
        tmp_path, [("model", "fixture-model-U5.7")]
    )
    con.close()
    result = _run(tmp_path, db, _target(tmp_path), status="ready")
    readme = (Path(result.docket_dir) / "README.md").read_text(encoding="utf-8")
    checklist = (Path(result.docket_dir) / "CHECKLIST.md").read_text(encoding="utf-8")
    assert "PROVENANCE" not in readme
    assert "PROVENANCE" not in checklist
    assert A.provenance_warning({"manifest": result.manifest}) is None


def test_warning_survives_reassembly_without_being_passed_in(tmp_path):
    """Re-assembly derives the producer from the *existing manifest* (no ad hoc arg).

    This is the "cannot be dropped" half: a bare re-assembly of a replay docket,
    with no ``producer=`` argument, still carries the warning.
    """
    db, con, _lane_id, _ids = _store_with_members(tmp_path, [("replay", None)])
    con.close()
    result = _run(tmp_path, db, _target(tmp_path))
    docket_dir = Path(result.docket_dir)

    reassembled = A.assemble(
        docket_dir,
        lane={"slug": LANE_SLUG, "type": "report", "title": "t"},
        claims=[],
        material_report=A.material_report_from_docket(docket_dir),
        target_meta={"slug": TARGET_SLUG},
        freshness={"state": "current"},
    )
    assert reassembled.manifest.generated_by.producer == "replay"
    assert "PROVENANCE: replay-produced" in (docket_dir / "README.md").read_text(
        encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
# 4. promotion_eligible — the truth table
# --------------------------------------------------------------------------- #


def test_promotion_eligible_truth_table():
    """True only for ``model`` **and** ``ready``; derived, so it cannot drift."""
    assert M.promotion_eligible(_manifest_obj("replay", status="ready"))[0] is False
    assert M.promotion_eligible(_manifest_obj("mixed", status="ready"))[0] is False
    assert M.promotion_eligible(_manifest_obj("unknown", status="ready"))[0] is False
    assert M.promotion_eligible(_manifest_obj("fixture", status="ready"))[0] is False
    assert M.promotion_eligible(_manifest_obj("model", status="draft"))[0] is False
    assert M.promotion_eligible(_manifest_obj("model", status="ready")) == (True, None)

    ok, why = M.promotion_eligible(_manifest_obj("replay", status="ready"))
    assert ok is False and "replay" in why
    ok, why = M.promotion_eligible(_manifest_obj("model", status="needs_rework"))
    assert ok is False and "needs_rework" in why

    # derived from the same fields it names: mutate a field, the verdict moves
    manifest = _manifest_obj("replay", status="ready")
    assert M.promotion_eligible(manifest)[0] is False
    manifest.generated_by.producer = "model"
    assert M.promotion_eligible(manifest)[0] is True
    manifest.status = "draft"
    assert M.promotion_eligible(manifest)[0] is False


def test_producer_vocabulary_is_validated():
    """A bogus producer is rejected by the contract, not silently accepted."""
    with pytest.raises(M.ValidationError):
        _manifest_obj("model-ish")
    # U5.15: the per-row classes are the store's tuple, imported; ``mixed`` is
    # the aggregate-only addition (no row may declare it -- the store CHECK).
    assert M.PRODUCERS == store.PRODUCER_VOCAB + ("mixed",)
    assert M.PRODUCERS == ("model", "replay", "fixture", "unknown", "mixed")


# --------------------------------------------------------------------------- #
# 5. backward compatibility
# --------------------------------------------------------------------------- #


def test_pre_u5_7_smoke_manifest_still_loads_and_reports_uncapped_confirms():
    """A frozen pre-U5.7 docket still *loads*; it does **not** verify clean.

    U5.24 restatement.  ``_smoke`` witnesses backward-compatible **loading** --
    the guarantee ``manifest.py`` actually makes ("a pre-existing manifest whose
    claim says ``CONFIRMS`` still loads").  It is *not* a witness that old
    artifacts pass every honesty check: its claim ``C1`` asserts ``CONFIRMS``
    while its assessor is ``'unknown'``, exactly the contradiction
    ``verify_docket`` must now report.  So this test pins the *specific* problem
    reported instead of a clean verdict, and pins the witness as frozen.
    """
    assert SMOKE.is_dir(), f"fixture docket missing: {SMOKE}"

    # 1. Load compatibility -- the promise to keep.  The old artifact is still
    #    structurally valid and still reads back as a pre-U5.7 shape.
    assert M.validate_manifest(SMOKE / "MANIFEST.json") == []
    loaded = M.read_manifest(SMOKE / "MANIFEST.json")
    assert loaded.generated_by.producer == "unknown"  # safe default, never "model"
    assert loaded.status_reason is None
    assert M.promotion_eligible(loaded)[0] is False
    raw = json.loads((SMOKE / "MANIFEST.json").read_text(encoding="utf-8"))
    assert "producer" not in json.dumps(raw.get("generated_by", {}))
    assert "status_reason" not in raw

    # 2. Honesty enforcement -- the new truth, pinned to the exact problem, so
    #    this asserts *which* contradiction was found, not merely "not ok".
    verification = A.verify_docket(SMOKE)
    assert verification.ok is False, verification.problems
    assert verification.problems == [
        "claim C1: standing CONFIRMS contradicts its backing producer "
        "'unknown', not 'model' (docket generated_by.producer='unknown') -- "
        "a non-model run may not assert CONFIRMS; re-derive the claim through "
        "materialize so the cap applies, or record mechanically-verified facts "
        "as a distinct standing (U5.22 follow-up)"
    ], verification.problems

    # 3. The witness is frozen: byte-identical, and never rewritten here
    #    (``dockets/_smoke/`` is read-only).
    import hashlib

    assert hashlib.sha256((SMOKE / "MANIFEST.json").read_bytes()).hexdigest() == (
        "41ec711a4324eb9893b6f031c10a647f21e1cb3521ca73a8e8eb168522b283c6"
    )


def test_manifest_without_the_new_fields_still_loads(tmp_path):
    """A hand-written U5.5-shaped manifest validates and serialises unchanged."""
    old = {
        "schema": M.SCHEMA,
        "lane": {"slug": "legacy", "type": "memo"},
        "target": {"slug": "fixture"},
        "status": "draft",
        "generated_by": {"app": "resextract", "version": "0.0.9", "model": ""},
    }
    assert M.validate_manifest(old) == []
    manifest = M.DocketManifest.model_validate(old)
    assert manifest.generated_by.model == ""
    assert manifest.generated_by.producer == "unknown"
    written = M.dumps_manifest(manifest)
    assert '"producer": "unknown"' in written
    assert M.validate_manifest(json.loads(written)) == []


def test_unknown_producer_cannot_back_a_model_claim(tmp_path):
    """The store-level predicate and the docket-level gate agree."""
    assert store.may_back_model_claim({"producer": "replay"}) is False
    assert store.may_back_model_claim({"producer": "model"}) is True
    ok, _why = M.promotion_eligible(_manifest_obj("model", status="ready"))
    assert ok is True


# --------------------------------------------------------------------------- #
# 4. U5.13 — a claim's standing must not exceed what its backing permits
#
# The third appearance of one bug shape.  On *candidates* a replay-produced row
# was stored indistinguishably from a model-mined one; on *verdicts* an
# undeclared client defaulted to "model" and could publish CONFIRMS.  Here, on
# *dockets*, a declared status string (``confirmed``/``confirms``/``verified``)
# mapped straight to ``CONFIRMS`` with no model check and no record of who
# assessed the claim -- so a replay-derived docket rendered a model-grade,
# unattributed verdict.  Two guards below, both red->green.
# --------------------------------------------------------------------------- #


def _confirmed_lane(*, producer: str | None, state: str = "confirmed") -> MAT.LaneSpec:
    """A one-member lane whose declared state maps to ``CONFIRMS``."""
    member = MAT.MemberSpec(
        "C1",
        provenance_refs=["docs/GUIDE.md#L1-L3"],
        verification_state=state,
    )
    if producer is not None:
        member.producer = producer
    return MAT.LaneSpec(
        slug=LANE_SLUG,
        title="Standing fixture lane",
        thesis="A claim may not assert more than its backing permits.",
        audience="the verifier",
        type="report",
        members=[member],
        target_slug=TARGET_SLUG,
        head_sha=None,
    )


def _materialize_and_read_claims(tmp_path, lane, db=None):
    db = db if db is not None else tmp_path / "standing-store.sqlite"
    store.init_db(db)  # a fresh fixture store: never the real state/state.sqlite
    result = MAT.materialize_lane(
        lane,
        target_root=str(_target(tmp_path)),
        docket_root=str(tmp_path / "dockets"),
        db_path=db,
        window_s=0.0,
    )
    raw = json.loads(
        (Path(result.docket_dir) / "MANIFEST.json").read_text(encoding="utf-8")
    )
    return result, raw["claims"]


def test_guard_a_replay_backed_claim_never_renders_confirms(tmp_path):
    """RED->GREEN **guard (a): the cap.** A non-model backing cannot say CONFIRMS.

    U5.15 moved this guard to :func:`materialize._claim_standing`.  Restoring the
    U5.13 decision path (the coercing ``_claim_producer`` plus the cap keyed off
    the *candidate* producer, with no verdict source) makes this test fail like
    this::

        >       assert claims[0]["verdict"] == "EXTENDS"
        E       AssertionError: assert 'CONFIRMS' == 'EXTENDS'
        FAILED tests/test_docket_provenance.py::test_guard_a_replay_backed_claim_never_renders_confirms

    Restored (sha256-identical), it passes::

        1 passed in 0.09s

    The declare→render pair this pins is exactly the reported defect:
    ``CLAIMS.md:7,13`` / ``MANIFEST.json:21`` said ``CONFIRMS`` for a claim whose
    member candidate the store records as ``replay``.
    """
    _result, claims = _materialize_and_read_claims(
        tmp_path, _confirmed_lane(producer="replay")
    )
    assert claims[0]["verdict"] == "EXTENDS"
    assert "CONFIRMS" not in claims[0]["verdict"]
    # the downgrade is visible, not silent: the reason travels with the claim
    assert claims[0]["verdict_reason"] is not None
    assert "replay" in claims[0]["verdict_reason"]
    assert "EXTENDS" in claims[0]["verdict_reason"]
    # ...and it is bounded by the SAME predicate the assess side uses, not a
    # second string comparison invented here.
    assert store.producer_is_model("replay") is False


def test_guard_b_claim_records_its_producer(tmp_path):
    """RED->GREEN **guard (b): the attribution.** Every claim names its assessor.

    Reverting the attribution (drop ``producer=str(row.get("producer") or
    "unknown")`` from ``MemberSpec.from_store`` and ``_claim_producer``'s return
    from ``_claim_for``, so the claim carries no ``producer`` key and the model
    default applies) makes this test fail like this::

        >       assert spec.members[0].producer == "replay"
        E       AssertionError: assert 'unknown' == 'replay'
        E         - replay
        E         + unknown
        FAILED tests/test_docket_provenance.py::test_guard_b_claim_records_its_producer

    Restored (sha256-identical), it passes::

        1 passed in 0.07s

    The producer is read from the store's own member-candidate row and
    normalised the way ``derive_producer`` normalises it, so claim-level and
    docket-level attribution are one scheme, not two.
    """
    db, con, lane_id, _ids = _store_with_members(tmp_path, [("replay", None)])
    try:
        lane_row = dict(
            con.execute("SELECT * FROM lanes WHERE id=?", (lane_id,)).fetchone()
        )
        candidate_rows = [
            dict(r) for r in con.execute("SELECT * FROM candidates").fetchall()
        ]
        spec = MAT.LaneSpec.from_store(lane_row, candidate_rows)
        assert spec.members[0].producer == "replay"
        _result, claims = _materialize_and_read_claims(tmp_path, spec)
    finally:
        con.close()
    row = claims[0]
    assert row["producer"] == "replay"
    assert row["verdict"] != "CONFIRMS"
    # the docket as a whole is labelled from the same rows: only the claim was
    # the leak, and it is now bounded and attributed.
    assert MAT.derive_producer(candidate_rows) == "replay"
    assert store.producer_is_model(row["producer"]) is False


def test_model_backed_claim_still_renders_confirms(tmp_path):
    """The legitimate case is untouched: a *model verdict* still earns CONFIRMS.

    U5.15: the grant comes from the verdict row.  A candidate row alone -- even
    ``producer='model'`` -- is not an assessment and renders EXTENDS.
    """
    _result, claims = _materialize_from_store(
        tmp_path,
        _store_with_assessed_member(
            tmp_path, producer="model", verdict="CONFIRMS", verdict_producer="model"
        ),
    )
    assert claims[0]["verdict"] == "CONFIRMS"
    assert claims[0]["verdict_reason"] is None
    assert claims[0]["producer"] == "model"
    assert store.producer_is_model(claims[0]["producer"]) is True


def test_unattributed_claim_is_bounded_fail_closed(tmp_path):
    """No producer information ⇒ no ``CONFIRMS``. ``unknown`` is not a model."""
    _result, claims = _materialize_and_read_claims(
        tmp_path, _confirmed_lane(producer=None)
    )
    assert claims[0]["verdict"] == "EXTENDS"
    assert claims[0]["producer"] == "unknown"
    assert claims[0]["verdict_reason"] is not None
    assert store.producer_is_model("unknown") is False


def test_claim_producer_normalises_like_derive_producer():
    """One vocabulary, one unknown-collapsing rule -- not a second scheme.

    U5.15: the comparison is **exact**.  ``"MODEL"`` and ``" replay "`` are not
    ``model``/``replay`` -- they collapse to ``unknown`` here exactly as they do
    in :func:`derive_producer`, consistent with ``store.producer_is_model`` and
    with the assess layer's reject-don't-coerce rule.
    """
    for bogus in ("", None, "MODEL!", "gpt-4", "  ", "MODEL", " replay ", "fixture", "mixed"):
        assert MAT._claim_producer(MAT.MemberSpec(id="x", producer=bogus)) == "unknown"
    assert MAT._claim_producer(MAT.MemberSpec(id="x", producer="model")) == "model"
    assert MAT._claim_producer(MAT.MemberSpec(id="x", producer="replay")) == "replay"
    assert MAT.derive_producer([{"producer": "MODEL!"}]) == "unknown"
    assert MAT.derive_producer([{"producer": "MODEL"}]) == "unknown"


def test_u513_manifest_claim_additions_are_additive_and_optional(tmp_path):
    """Old manifests load; ``_smoke`` still validates; schema string unchanged."""
    assert M.SCHEMA == "resextract/docket/1"
    # a U5.12-shaped claim, written before this unit's fields existed
    old_claim = {"id": "C-curated", "text": "t", "verdict": "CONFIRMS"}
    claim = M.Claim.model_validate(old_claim)
    assert claim.verdict == "CONFIRMS"  # reading is never downgraded...
    assert claim.producer == "unknown"
    assert claim.verdict_reason is None
    # ...the cap is applied at materialize time, which is why re-materializing
    # the real dockets rewrites this to EXTENDS + a reason.
    smoke = M.read_manifest(SMOKE / "MANIFEST.json")
    assert M.validate_manifest(json.loads(M.dumps_manifest(smoke))) == []
    for c in smoke.claims:
        assert c.producer in MAT.PRODUCERS
    # extra="forbid" is kept: a misspelled new field is still a loud error
    with pytest.raises(M.ValidationError):
        M.Claim.model_validate(
            {"id": "C1", "text": "t", "prodcer": "model", "verdict": "EXTENDS"}
        )



# --------------------------------------------------------------------------- #
# 6. U5.15 — the cap is judged on the RAW producer, and standing is keyed off
#    the VERDICT row (``verdicts.producer`` / ``verdicts.verdict``), never off
#    ``candidates.state``.  Two guards, both red->green.
# --------------------------------------------------------------------------- #


def _store_with_assessed_member(
    tmp_path: Path,
    *,
    state: str = "confirmed",
    producer: str = "model",
    verdict: str | None = None,
    verdict_producer: str = "unknown",
):
    """A real store with one lane, one candidate, and optionally one verdict.

    Rows go in through the store's own writers, so every CHECK applies and the
    join under test (``verdicts.claim_id = claims.id`` +
    ``claims.candidate_id = candidates.id``) is the store's real one.
    """
    db = tmp_path / "assessed-store.sqlite"
    store.init_db(db)
    con = store.connect(db)
    lane_id = store.upsert_lane(
        con, target=TARGET_SLUG, slug=LANE_SLUG, type="report", status="draft"
    )
    cid = store.insert_candidate(
        con,
        kind="claim",
        title="Assessed claim",
        summary="Assessed claim rests on the guide.",
        provenance_json=[{"kind": "file_lines", "ref": "docs/GUIDE.md#L1-L3"}],
        score=1.0,
        state=state,
        producer=producer,
        model="m" if store.producer_is_model(producer) else None,
    )
    con.execute(
        "INSERT OR IGNORE INTO lane_candidates(lane_id, candidate_id) VALUES (?, ?)",
        (lane_id, cid),
    )
    if verdict is not None:
        claim_id = store.insert_claim(
            con, candidate_id=cid, kind="claim", text="t", verification_state=state,
            provenance_json=[{"kind": "file_lines", "ref": "docs/GUIDE.md#L1-L3"}],
        )
        store.insert_verdict(
            con,
            claim_id=claim_id,
            verdict=verdict,
            evidence_ids_json=[],
            checked_at="2026-10-08T10:00:01.000Z",
            producer=verdict_producer,
            model="m" if store.producer_is_model(verdict_producer) else None,
        )
    con.commit()
    con.close()
    return db


def _materialize_from_store(tmp_path, db):
    con = store.connect(db)
    try:
        lane_row = dict(
            con.execute("SELECT * FROM lanes WHERE slug=?", (LANE_SLUG,)).fetchone()
        )
        candidate_rows = [
            dict(r) for r in con.execute("SELECT * FROM candidates").fetchall()
        ]
    finally:
        con.close()
    spec = MAT.LaneSpec.from_store(lane_row, candidate_rows)
    return _materialize_and_read_claims(tmp_path, spec, db=db)


def test_guard_u515a_wrong_case_producer_is_not_model(tmp_path):
    """RED->GREEN **guard (a): the coercion.** ``"Model"`` is not ``model``.

    Reached through the unvalidated curated path (``LaneSpec.from_json``, the
    shape ``cli.py:346`` builds).  ``store.producer_is_model("Model")`` is False.
    Restoring the U5.13 decision path -- the coercing
    ``str(raw).strip().lower()`` in ``_claim_producer`` plus the cap keyed off the
    candidate producer -- renders ``Model`` as ``CONFIRMS`` and attributes it
    ``model``, so this test fails like this::

        >       assert claims[0]["verdict"] == "EXTENDS"
        E       AssertionError: assert 'CONFIRMS' == 'EXTENDS'
        FAILED tests/test_docket_provenance.py::test_guard_u515a_wrong_case_producer_is_not_model

    Restored (sha256-identical, full ``__pycache__`` purge), it passes::

        1 passed in 0.09s

    The raw value is judged exactly: only the exact string ``model`` grants model
    standing.  A wrong-case declaration is capped fail-closed AND its reason is
    recorded -- never silently accepted, never coerced.
    """
    spec_path = tmp_path / "curated-lane.json"
    spec_path.write_text(
        json.dumps(
            {
                "slug": LANE_SLUG,
                "type": "report",
                "target_slug": TARGET_SLUG,
                "members": [
                    {
                        "id": "C1",
                        "provenance_refs": ["docs/GUIDE.md#L1-L3"],
                        "verification_state": "confirmed",
                        "producer": "Model",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    lane = MAT.LaneSpec.from_json(spec_path)
    # loading is non-destructive: the raw declaration survives the load...
    assert lane.members[0].producer == "Model"
    # ...and the predicate and the docket agree it is not a model.
    assert store.producer_is_model("Model") is False
    _result, claims = _materialize_and_read_claims(tmp_path, lane)
    assert claims[0]["verdict"] == "EXTENDS"
    assert "CONFIRMS" not in claims[0]["verdict"]
    assert claims[0]["producer"] == "unknown"
    assert "Model" in claims[0]["verdict_reason"]
    assert "case-sensitive" in claims[0]["verdict_reason"]
    for wrong_case in ("Model", "MODEL", "  model  "):
        assert store.producer_is_model(wrong_case) is False
        assert MAT._claim_producer(MAT.MemberSpec(id="x", producer=wrong_case)) == "unknown"
        assert MAT.derive_producer([{"producer": wrong_case}]) == "unknown"


def test_guard_u515b_no_verdict_means_no_confirms(tmp_path):
    """RED->GREEN **guard (b): the source.** Zero verdicts => never ``CONFIRMS``.

    A **model-mined** candidate (``producer='model'``) whose row says
    ``state='confirmed'`` is not an assessment: nothing writes ``candidates.state``
    from a verdict, and the store holds **0 verdicts**.  Reverting the source
    (keying ``_claim_standing`` off the candidate row again, as U5.13 did) makes
    this test fail like this::

        >       assert claims[0]["verdict"] == "EXTENDS"
        E       AssertionError: assert 'CONFIRMS' == 'EXTENDS'
        FAILED tests/test_docket_provenance.py::test_guard_u515b_no_verdict_means_no_confirms

    Restored (sha256-identical, full ``__pycache__`` purge), it passes::

        1 passed in 0.10s

    This is the residual fail-open V5D found; it is now fail-closed.
    """
    db = _store_with_assessed_member(tmp_path, producer="model", state="confirmed")
    con = store.connect(db)
    try:
        assert con.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0] == 0
    finally:
        con.close()
    _result, claims = _materialize_from_store(tmp_path, db)
    assert claims[0]["verdict"] == "EXTENDS"
    assert "CONFIRMS" not in claims[0]["verdict"]
    assert claims[0]["verdict_reason"] is not None
    assert "no verdicts row" in claims[0]["verdict_reason"]


def test_standing_follows_the_verdict_not_the_candidate(tmp_path):
    """Both directions: a ``model`` verdict grants CONFIRMS; ``replay`` caps it.

    The candidate is identical (``producer='model'``, ``state='confirmed'``) in
    both cases, so only the verdict row can explain the difference -- which is
    what proves standing is keyed off ``verdicts`` and not ``candidates``.
    """
    model_dir = tmp_path / "model-verdict"
    model_dir.mkdir()
    db = _store_with_assessed_member(
        model_dir, producer="model", verdict="CONFIRMS", verdict_producer="model"
    )
    _result, claims = _materialize_from_store(model_dir, db)
    assert claims[0]["verdict"] == "CONFIRMS"  # the mirror false negative is gone
    assert claims[0]["verdict_reason"] is None
    assert claims[0]["producer"] == "model"
    assert store.producer_is_model(claims[0]["producer"]) is True

    replay_dir = tmp_path / "replay-verdict"
    replay_dir.mkdir()
    db = _store_with_assessed_member(
        replay_dir, producer="model", verdict="CONFIRMS", verdict_producer="replay"
    )
    _result, claims = _materialize_from_store(replay_dir, db)
    assert claims[0]["verdict"] == "EXTENDS"
    assert "CONFIRMS" not in claims[0]["verdict"]
    assert "replay" in claims[0]["verdict_reason"]


def test_claim_producer_and_derive_producer_agree_row_by_row():
    """One vocabulary, one collapsing rule: a table through **both** functions.

    This is what makes "``_claim_producer`` normalises the way
    ``derive_producer`` normalises" checkable instead of asserted.  ``mixed`` is
    never a member-level answer (a single row cannot be a mixture) and ``fixture``
    collapses to ``unknown`` in both, exactly as the store's gate requires.
    """
    table = [
        "model", "replay", "fixture", "mixed", "unknown",
        "Model", "MODEL", "  model  ", "", "gpt",
        None, {"a": 1}, ["model"], 42, True,
    ]
    for raw in table:
        claim_level = MAT._claim_producer(MAT.MemberSpec(id="x", producer=raw))
        docket_level = MAT.derive_producer([{"producer": raw}])
        assert claim_level == docket_level, (raw, claim_level, docket_level)
    assert MAT.derive_producer([{"producer": "model"}, {"producer": "fixture"}]) == "mixed"
    assert MAT._claim_producer(MAT.MemberSpec(id="x", producer="mixed")) == "unknown"


def test_docket_vocabulary_is_the_store_vocabulary_plus_mixed(tmp_path):
    """``mixed`` is aggregate-only: imported store classes + one derived label."""
    import typing

    assert M.PRODUCERS == store.PRODUCER_VOCAB + ("mixed",)
    assert set(M.PRODUCERS) - {"mixed"} == set(store.PRODUCER_VOCAB)
    assert typing.get_args(M.DProducer) == M.PRODUCERS
    # the store's CHECK refuses ``mixed`` on a row -- so no row, and no claim,
    # can ever carry it; only lane-level aggregation emits it.
    assert "mixed" not in store.PRODUCER_VOCAB
    db = tmp_path / "vocab-store.sqlite"
    store.init_db(db)
    con = store.connect(db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            # the row must be complete enough for the *producer* CHECK to be what fires
            store.insert_candidate(
                con, kind="claim", title="mixed", producer="mixed", provenance_json=[]
            )
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 7. U5.19 — the THIRD rendering site.  "One vocabulary, one normalisation" is a
#    three-site property: the candidate row (``_claim_producer``), the docket
#    aggregate (``derive_producer``) and the *rendered claim* (``_claim_for``,
#    whose verdict branch V5G found uncompared).
# --------------------------------------------------------------------------- #

#: The adversarial set: V5G's inputs plus the lookalikes it named.
U519_TABLE = [
    "model", "replay", "fixture", "mixed", "unknown",
    "Model", "MODEL", "  model  ", "", "gpt",
    None, {"a": 1}, ["model"], 42, True,
    b"model", 1.0, "model\n", "model\x00", "\uff4dodel",
]


def _verdict_site(raw):
    """The producer :func:`_claim_for` renders when a verdict carries ``raw``."""
    member = MAT.MemberSpec(
        id="x", producer=raw, verdict="EXTENDS", verdict_producer=raw
    )
    return MAT._claim_for(member, [])["producer"]


def test_three_way_producer_normalisation_equivalence():
    """**Three** sites, one table -- not two.

    V5G (F1) found the two-way table could not see ``_claim_for``'s verdict
    branch rendering ``producer="fixture"`` for a fixture verdict.  Every row is
    now compared across all three sites over the same adversarial inputs, plus an
    absent verdict producer.
    """
    divergences = [
        (raw, candidate, docket, verdict)
        for raw in U519_TABLE
        for candidate, docket, verdict in [
            (
                MAT._claim_producer(MAT.MemberSpec(id="x", producer=raw)),
                MAT.derive_producer([{"producer": raw}]),
                _verdict_site(raw),
            )
        ]
        if not (candidate == docket == verdict)
    ]
    assert divergences == []
    assert MAT._claim_for(
        MAT.MemberSpec(id="x", producer="model", verdict="EXTENDS"), []
    )["producer"] == "unknown"


def test_guard_u519_f1_fixture_verdict_is_unknown_at_every_site():
    """RED->GREEN **guard (F1)**: a fixture verdict must not render ``fixture``.

    ``fixture`` is in :data:`PRODUCERS`, so it is *representable*; the question
    is whether the claim level preserves it.  It does not.  **Direction: unified
    on ``unknown``** -- two of the three sites already collapsed, ``fixture`` is
    harness/verification material rather than a claim's mining provenance, and
    ``unknown`` is the fail-closed answer (``store.producer_is_model("fixture")``
    is False, so the collapse cannot grant standing).

    Reverted (third site back to ``_normalise_producer(member.verdict_producer)``)::

        >       assert verdict_site == "unknown"
        E       AssertionError: assert 'fixture' == 'unknown'
        FAILED ...::test_guard_u519_f1_fixture_verdict_is_unknown_at_every_site

    Restored (sha256-identical, full ``__pycache__`` purge):: ``1 passed``.
    """
    member = MAT.MemberSpec(
        id="C1", producer="model", verdict="CONFIRMS", verdict_producer="fixture"
    )
    verdict_site = MAT._claim_for(member, [])["producer"]
    assert verdict_site == "unknown"
    assert verdict_site == MAT._claim_producer(
        MAT.MemberSpec(id="C1", producer="fixture")
    )
    assert verdict_site == MAT.derive_producer([{"producer": "fixture"}])
    assert store.producer_is_model(verdict_site) is False
    mixed = MAT.MemberSpec(
        id="C1", producer="replay", verdict="EXTENDS", verdict_producer="mixed"
    )
    assert MAT._claim_for(mixed, [])["producer"] == "unknown"


def test_guard_u519_f2_model_verdict_on_replay_mined_candidate(tmp_path):
    """RED->GREEN **guard (F2)**: pin the standing *and* the mining provenance.

    The mixed case: a **model-produced verdict on a replay-mined candidate**.
    ``store.may_back_model_claim_verdict`` blesses it, so ``CONFIRMS`` stands --
    but ``producer="model"`` alone would let a reader conclude the *material* was
    model-mined while ``generated_by.producer`` says ``replay``.  The claim's
    ``verdict_reason`` now names the mining provenance beside the assessing one.
    A test that pins only the standing is what let this hide.

    Reverted (no mining note)::

        >       assert "mined by 'replay'" in reason
        E       AssertionError: assert "mined by 'replay'" in None
        FAILED ...::test_guard_u519_f2_model_verdict_on_replay_mined_candidate
    """
    mixed_dir = tmp_path / "mixed"
    mixed_dir.mkdir()
    db = _store_with_assessed_member(
        mixed_dir,
        state="confirmed",
        producer="replay",
        verdict="CONFIRMS",
        verdict_producer="model",
    )
    result, claims = _materialize_from_store(mixed_dir, db)
    assert claims[0]["producer"] == "model"  # the ASSESSING producer
    assert claims[0]["verdict"] == "CONFIRMS"  # invariant: a model verdict may
    reason = claims[0]["verdict_reason"]
    assert reason is not None
    assert "mined by 'replay'" in reason  # the MINING provenance, visible
    assert "assessing" in reason
    assert result.manifest.generated_by.producer == "replay"

    # invariant: a replay-backed claim with NO model verdict never CONFIRMS.
    bare_dir = tmp_path / "bare"
    bare_dir.mkdir()
    bare_db = _store_with_assessed_member(
        bare_dir, state="confirmed", producer="replay"
    )
    _bare_result, bare_claims = _materialize_from_store(bare_dir, bare_db)
    assert bare_claims[0]["verdict"] == "EXTENDS"
    assert "CONFIRMS" not in bare_claims[0]["verdict"]
    assert bare_claims[0]["producer"] == "replay"


def test_guard_u523_non_none_verdict_reason_is_not_a_downgrade_marker(tmp_path):
    """U5.23: ``verdict_reason is not None`` is NOT a downgrade marker.

    The F2 note is written on a claim that legitimately stands at ``CONFIRMS``
    (a model verdict blessed replay-mined material), so a consumer must key on
    ``verdict``, not on the reason's presence.  Pins both meanings and the
    reliable discriminators.
    """
    mixed_dir = tmp_path / "mixed"
    mixed_dir.mkdir()
    db = _store_with_assessed_member(
        mixed_dir,
        state="confirmed",
        producer="replay",
        verdict="CONFIRMS",
        verdict_producer="model",
    )
    result, claims = _materialize_from_store(mixed_dir, db)
    reason = claims[0]["verdict_reason"]
    assert reason is not None                      # present ...
    assert claims[0]["verdict"] == "CONFIRMS"      # ... yet NOT a downgrade
    assert "capped at EXTENDS" not in reason       # cap discriminator
    assert "is the *assessing* producer" in reason # F2 discriminator
    assert result.manifest.generated_by.producer == "replay"


def test_guard_u529_cap_reason_carries_the_cap_phrase(tmp_path):
    """RED->GREEN **guard (cap-side presence)**: the CAP phrase is a contract.

    U5.28 pinned the **F2** half of the ``verdict_reason`` discriminator (its
    presence *and* its absence).  The other half -- "``capped at EXTENDS`` means
    this reason is a cap" -- was still only a **hint**: nothing asserted the
    phrase's *presence*, so U5.28 measured that rewording a cap emitter
    (``capped at EXTENDS`` -> ``capped to EXTENDS``) at all four cap sites left
    the suite GREEN.  The **CAP** side was unpinned **in the presence
    direction**, so a cap-detecting consumer could break silently.

    This drives two real cap paths and asserts the phrase on the reason that
    actually reaches ``Claim.verdict_reason``:

    * ``materialize._claim_standing`` :1631 -- declared ``CONFIRMS`` with **no
      verdicts row** (so it is capped and the cap is recorded);
    * ``assemble._cap_uncapped_claims`` :1141-1145 -- a caller-supplied
      ``CONFIRMS`` whose own producer is not exactly ``model``.

    Rewording the phrase at a driven site fails here::

        E       AssertionError: assert 'capped at EXTENDS' in "..."

    **Coverage, stated honestly -- four cap emitters exist, this drives three
    of them.**  Unpinned: ``assess/verdicts.py:404``, whose phrase is written to
    ``Verdict.rationale`` and **never reaches** ``Claim.verdict_reason`` (a grep
    for ``rationale`` over ``materialize.py`` / ``assemble.py`` /
    ``manifest.py`` is empty), so no docket-level assertion can observe it.

    ``literal_count_proxy_used: false``.  A census of the ``"capped at
    EXTENDS"`` source literals would be a **characterization** proxy: it passes
    on a refactor that extracts the phrase into a constant, fails on one that
    adds a legitimate site, and in every case proves nothing about *behaviour*.
    Asserting a **driven cap produces the phrase** is the observable property,
    so that is what is asserted here.
    """
    # (1) materialize.py:1631 -- declared CONFIRMS, zero verdicts rows.
    no_verdict_dir = tmp_path / "no-verdict"
    no_verdict_dir.mkdir()
    db = _store_with_assessed_member(
        no_verdict_dir, state="confirmed", producer="model"
    )
    _result, claims = _materialize_from_store(no_verdict_dir, db)
    assert claims[0]["verdict"] == "EXTENDS"
    cap_reason = claims[0]["verdict_reason"]
    assert cap_reason is not None
    assert "capped at EXTENDS" in cap_reason
    # this reason is a cap and *only* a cap: the F2 discriminator is absent, so
    # the two halves of the discriminator stay separable in both directions.
    assert "is the *assessing* producer" not in cap_reason

    # (2) assemble.py:1141-1145 -- a passed-in CONFIRMS that may not stand.
    passed_in = [
        M.Claim.model_validate(
            {"id": "C1", "text": "t", "verdict": "CONFIRMS", "producer": "replay"}
        )
    ]
    recorded = A._cap_uncapped_claims(passed_in)
    assert passed_in[0].verdict == "EXTENDS"
    assert "capped at EXTENDS" in passed_in[0].verdict_reason
    assert recorded and "capped at EXTENDS" in recorded[0]


def test_guard_u531_replay_verdict_cap_reason_carries_the_cap_phrase(tmp_path):
    """RED->GREEN **guard (cap-side presence, the third emitter)**: ``:1641``.

    U5.29 asserted the cap phrase on two of the four sites that emit
    ``capped at EXTENDS``: ``materialize._claim_standing`` :1631 (declared
    ``CONFIRMS``, **no** verdicts row) and ``assemble._cap_uncapped_claims``
    :1141-1145.  The third -- ``materialize._claim_standing`` :1641 -- is
    *reachable* (``test_standing_follows_the_verdict_not_the_candidate``
    already drives it) but nothing asserted its phrase, so rewording it was
    silent.  This closes that hole.

    Exact inputs: a candidate with ``producer='replay'`` / ``state='confirmed'``
    plus ONE verdict row with ``verdict='CONFIRMS'``, ``producer='replay'``.
    Those reach :1638-1643::

        if verdict == "CONFIRMS" and not _store.producer_is_model(
            member.verdict_producer
        ):
            return "EXTENDS", (
                f"verdict {member.verdict_id} says CONFIRMS but its producer is "
                f"{member.verdict_producer!r}, not 'model'; capped at EXTENDS by the "
                "same rule as assess.verdicts (a non-model run may not assert CONFIRMS)"
            )

    ``member.verdict`` is non-``None``, so the no-verdicts-row branch at
    :1631 is not taken; the verdict's own producer is ``replay`` (not exactly
    ``model``), so the cap applies.  ``producer == verdict_producer``, so the
    F2 attribution note is not appended -- the reason is a cap and only a cap.
    The branch discriminator asserted below is ``"no verdicts row" not in
    reason``: that sentence belongs to :1631 alone, so its absence is positive
    evidence that the *:1641* branch answered instead of a neighbour.
    """
    replay_verdict_dir = tmp_path / "replay-verdict-1641"
    replay_verdict_dir.mkdir()
    db = _store_with_assessed_member(
        replay_verdict_dir,
        state="confirmed",
        producer="replay",
        verdict="CONFIRMS",
        verdict_producer="replay",
    )
    _result, claims = _materialize_from_store(replay_verdict_dir, db)
    assert claims[0]["verdict"] == "EXTENDS"
    cap_reason = claims[0]["verdict_reason"]
    assert cap_reason is not None
    assert "capped at EXTENDS" in cap_reason
    # the :1641 branch answered, NOT the no-verdicts-row branch at :1631 ...
    assert "no verdicts row" not in cap_reason
    # ... and this is a cap, not the F2 provenance note (the two halves of the
    # ``verdict_reason`` discriminator stay separable in both directions).
    assert "is the *assessing* producer" not in cap_reason


def test_u519_producer_literal_sites_are_vocabulary_bound():
    """Item 3: the two census-missed literals, pinned **behaviour-preserving**.

    ``:562`` ``if seen == {"model"}`` -> ``if seen == {_store.MODEL_PRODUCER}``:
    the same value, now the constant (U2.10's ``== "model"`` regex could not
    match either form).  ``:1549`` ``value in ("model", "replay")`` -> the named
    :data:`_CLAIM_PRODUCER_VOCAB` subset applied by
    :func:`_claim_level_producer`.  Both keep the *same* outputs -- the subset is
    genuinely a subset (``fixture``/``unknown``/``mixed`` stay out) -- and this
    test passes on the reverted revision too, which is the proof that Item 3
    changed no behaviour.
    """
    assert MAT._CLAIM_PRODUCER_VOCAB == (store.MODEL_PRODUCER, "replay")
    assert set(MAT._CLAIM_PRODUCER_VOCAB) < set(MAT.PRODUCERS)
    assert set(MAT.PRODUCERS) - set(MAT._CLAIM_PRODUCER_VOCAB) == {
        "fixture",
        "unknown",
        "mixed",
    }
    # :562 -- the constant selects exactly what the literal did
    assert MAT.derive_producer([{"producer": store.MODEL_PRODUCER}]) == "model"
    assert MAT.derive_producer([{"producer": "model"}, {"producer": "model"}]) == "model"
    assert MAT.derive_producer([{"producer": "model"}, {"producer": "replay"}]) == "replay"
    assert MAT.derive_producer([{"producer": "model"}, {"producer": "fixture"}]) == "mixed"
    assert MAT.derive_producer([{"producer": "fixture"}]) == "unknown"
    # :1549 -- the named subset, not bare literals, and not the whole vocabulary
    for raw, expected in [
        ("model", "model"),
        ("replay", "replay"),
        ("fixture", "unknown"),
        ("unknown", "unknown"),
        ("mixed", "unknown"),
        ("Model", "unknown"),
    ]:
        assert MAT._claim_level_producer(raw) == expected
        assert MAT._claim_producer(MAT.MemberSpec(id="x", producer=raw)) == expected


# --------------------------------------------------------------------------- #
# 7. U5.33 — the snapshot rotation is an ACCEPTED side effect, so it is pinned:
#    bounded, destructive, and stable in the half that carries the claim.
# --------------------------------------------------------------------------- #


def test_guard_u533_rotation_window_is_bounded_and_destructive():
    """U5.33 — pin the rotation window: bounded, destructive, log still growing.

    The render is deliberately **not** idempotent (U5.31: making it so would
    rewrite the append-only audit log and change delivery semantics), so a
    re-render has two side effects that a diffing verifier meets: ``HISTORY.md``
    gains a block, and the outgoing ``ITEM.md`` becomes a fresh ``ITEM.md.rN``
    snapshot.  That rotation is **destructive** — once the window is full each
    render also deletes the oldest snapshot.

    Pinned because it is the *accepted* contract, not a defect awaiting repair:
    ``ITEM_SNAPSHOT_KEEP`` exists precisely to bound the one unbounded growth in
    a docket tree, its max-index allocator is documented as load-bearing (the
    docstring of :func:`_preserve_item` explains that first-free would delete the
    *newest* prior revision), and ``ITEM.md`` itself always survives.  Measured
    here: 5 renders fill the window (0 -> 5 snapshots), the 6th keeps the count
    at 5 and evicts the oldest, while ``HISTORY.md`` grows every time.

    What is byte-stable across re-renders is ``ITEM.md``'s **content**, not the
    manifest: U8.43 measured ``ITEM.md``'s sha256 constant r0-r7 while
    ``MANIFEST.json`` keeps its sha only *within* one clock second and changes as
    soon as ``generated_at`` crosses a second (the real clock, ``A._now``) -- so
    a byte-identity expectation for the manifest between two renders is not a
    contract, and the assertion below checks the half that is.

    The amount of the bound is read from :data:`A.ITEM_SNAPSHOT_KEEP`, so
    re-tuning the window is not a failure; removing the bound or the eviction is.
    Every assertion is count/set based and never names a literal ``rN``: the
    eviction is checked as *the smallest index present before the render is gone
    and one index above the previous maximum arrived*, which is robust to a
    snapshot being re-indexed but would (deliberately) flag the first-free
    renumbering that ``_preserve_item`` forbids.
    """
    import hashlib
    import os
    import re
    import shutil
    import uuid

    root = REPO / "state" / "verify" / "U5.33" / "pin" / uuid.uuid4().hex
    root.mkdir(parents=True)
    try:
        db, con, _lane_id, _ids = _store_with_members(root, [("replay", None)])
        con.close()
        result = _run(root, db, _target(root))
        docket = Path(result.docket_dir)
        assert str(docket).startswith(str(REPO / "state" / "verify" / "U5.33"))

        def snapshots() -> list[int]:
            return sorted(
                int(m.group(1))
                for name in os.listdir(docket)
                if (m := re.fullmatch(r"ITEM\.md\.r(\d+)", name))
            )

        def render() -> None:
            A.assemble(
                docket,
                lane={"slug": LANE_SLUG, "type": "report", "title": "t"},
                claims=[],
                material_report=A.material_report_from_docket(docket),
                target_meta={"slug": TARGET_SLUG},
                freshness={"state": "current"},
            )

        history = docket / "HISTORY.md"
        item = docket / "ITEM.md"
        keep = A.ITEM_SNAPSHOT_KEEP
        item_sha: str | None = None

        # while the window fills: exactly one new snapshot per render, never over
        sizes: list[int] = []
        for filled in range(1, keep + 1):
            render()
            assert len(snapshots()) == filled
            assert len(snapshots()) <= keep
            sizes.append(history.stat().st_size)
            if item_sha is None:
                item_sha = hashlib.sha256(item.read_bytes()).hexdigest()
        assert sizes == sorted(set(sizes))  # HISTORY.md grew on every render
        full = snapshots()

        # once full: net 0 snapshots, and the OLDEST is the one that is evicted
        render()
        after = snapshots()
        assert len(after) == keep
        assert set(after) != set(full)
        assert set(full) - set(after) == {min(full)}
        assert set(after) - set(full) == {max(full) + 1}
        assert min(full) not in after

        # the reassuring half: the audit log grows; the claim-bearing record
        # (ITEM.md) is byte-stable across re-renders.  The manifest-sha form of
        # this assertion was DROPPED (U8.43), not weakened: MANIFEST.json is
        # rewritten on every render and its sha changes as soon as generated_at
        # crosses a clock second, so comparing it was clock-dependent -- a latent
        # flake (V5.37 measured 40/40 green only because no probe crossed a
        # boundary).  Measured instead: manifest sha identical within one second,
        # different across it; ITEM.md sha constant r0-r7.
        assert history.stat().st_size > sizes[-1]
        assert hashlib.sha256(item.read_bytes()).hexdigest() == item_sha
    finally:
        shutil.rmtree(root, ignore_errors=True)
