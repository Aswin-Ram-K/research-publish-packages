"""Guard for the H1-CONDITIONING pre-registration (docs/H1-CONDITIONING.md).

Offline, fixture-only. This module is a PLUMBING test, not a measurement:

  * it constructs a synthetic 48-turn row sample (6 rows per regime is enough) and
    checks that every reading's selector is derivable from ROW FIELDS ALONE - the fire
    turn is re-derived from `evicted` / `digest_at` / `lease` / `prefix_sha256`, never
    read back from the fixture's declared constants;
  * it fails if a reading whose n at 3 reps is below `analyze_stats.min_n_for(0.95)`
    is nevertheless carried as a claim;
  * it asserts the fixture's four declared fire turns equal the fire turns observable
    in those rows; and
  * it goes RED on one mutant - a selector that ignores `turn` and returns every row.

The synthetic rows carry fake latencies used only to exercise the n floor and to show
`quantile_ci` admits these n. They are NOT measurements, are not written to disk, and
no `rows-runA-*` file exists or may be inferred from them.

    python3 -m pytest experiments/ptr-engine/longrun/tests/test_h1_conditioning.py -q
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import analyze_stats as A  # noqa: E402  (min_n_for / rank_span / quantile_ci / MIN_N / TAIL_MIN)

FIXTURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "FIXTURE-TREATMENTS.json")

#: The only row fields a selector may read. Named once, asserted by the derivability test.
ROW_FIELDS = ("kind", "turn", "arm", "ttft_ms", "evicted", "digest_at", "lease",
              "prefix_sha256")

#: The one common treated floor: max(fire_turns) = max(21, 21, 23, 2) = 23. R-common is
#: `turn > 23`, so every arm is inside its own treated regime and no arm shares a turn
#: index with a pre-treatment turn of another arm.
COMMON_FLOOR = 23

REPS = 3
HORIZON = 48


# --- the readings, as callable transforms over rows --------------------------
def _usable(rows):
    """Turn rows with a finite ttft_ms. Null/absent ttft is dropped, never coerced to 0."""
    out = []
    for r in rows:
        if r.get("kind") != "turn":
            continue
        v = r.get("ttft_ms")
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        out.append(r)
    return out


def select_r_all(rows, fire_turn=None):
    """R-all (PARM-1 frozen): every completed turn, no turn conditioning at all."""
    return _usable(rows)


def select_r_post(rows, fire_turn):
    """R-post: this arm's own treated regime, `turn >= fire_turn`.

    Inclusive at the fire turn by construction: the fixture's own per-rep counts are
    28 / 28 / 26 / 47, which are the inclusive counts (48-21+1 = 28, 48-23+1 = 26,
    48-2+1 = 47). The untreated prefix is dropped, never trimmed to a fixed length.
    """
    if fire_turn is None:
        raise ValueError("select_r_post: fire_turn must be derived from the rows")
    return [r for r in _usable(rows) if int(r["turn"]) >= int(fire_turn)]


def select_r_common(rows, fire_turn=None):
    """R-common: the common treated window, `turn > COMMON_FLOOR` for every arm."""
    return [r for r in _usable(rows) if int(r["turn"]) > COMMON_FLOOR]


#: reading name -> (selector, is_primary_claim, per-rep n)
READINGS = {
    "R-all": (select_r_all, True, HORIZON),
    "R-post": (select_r_post, False, {"transcript-grow": 28, "transcript-compact": 28,
                                      "lease-reopen": 26, "pointer-stable": 47}),
    "R-common": (select_r_common, False, HORIZON - COMMON_FLOOR),
}


# --- fire turns, derived from rows (never from the fixture constants) --------
def _marker_fires(marker, rows, arm):
    """First turn at which `marker` is observable in `rows` for `arm`, or None."""
    turns = sorted({int(r["turn"]) for r in rows if r.get("arm") == arm
                    and r.get("kind") == "turn"})
    prev = None
    for t in turns:
        sel = [r for r in rows if r.get("arm") == arm and r.get("kind") == "turn"
               and int(r["turn"]) == t]
        r = sel[0]
        if marker == "evicted":
            hit = (r.get("evicted") or 0) > 0
        elif marker == "digest_at":
            hit = bool(r.get("digest_at"))
        elif marker == "lease":
            hit = (r.get("lease") or 1) > 1
        elif marker == "prefix_sha256":
            cur = r.get("prefix_sha256")
            hit = prev is not None and cur is not None and cur != prev
            prev = cur
        else:
            raise ValueError("unknown marker %r" % (marker,))
        if hit:
            return t
    return None


MARKERS = {"transcript-grow": "evicted", "transcript-compact": "digest_at",
           "lease-reopen": "lease", "pointer-stable": "prefix_sha256"}


def infer_fire_turn(rows, arm):
    return _marker_fires(MARKERS[arm], rows, arm)


# --- synthetic rows: plumbing only, never a measurement ---------------------
def synth_rows(arm, fire_turn, horizon=HORIZON):
    """A 48-turn row sample in which `arm`'s marker turns on exactly at `fire_turn`."""
    rows = []
    for t in range(1, horizon + 1):
        r = {"kind": "turn", "arm": arm, "turn": t,
             "ttft_ms": 100.0 + t,          # fake latency: plumbing, not a measurement
             "evicted": 0, "digest_at": None, "lease": 1, "prefix_sha256": "p0"}
        if arm == "transcript-grow" and t >= fire_turn:
            r["evicted"] = 1
        elif arm == "transcript-compact" and t >= fire_turn:
            r["digest_at"] = "digest#1"
        elif arm == "lease-reopen" and t >= fire_turn:
            r["lease"] = 2 + (1 if t >= 40 else 0)
        elif arm == "pointer-stable" and t >= fire_turn:
            r["prefix_sha256"] = "p%d" % (t,)
        rows.append(r)
    return rows


def synth_all(fire_turns):
    rows = []
    for arm, f in fire_turns.items():
        rows.extend(synth_rows(arm, f))
    return rows


def declared_fire_turns():
    with open(FIXTURE, encoding="utf-8") as fh:
        fx = json.load(fh)
    return {arm: int(v["first_fire_turn"]) for arm, v in fx["dry_run_turns"].items()}


# --- the guard itself ------------------------------------------------------
def check_reading(name, rows, fire_turn, reps=REPS):
    """Return (n_per_rep, n_total), asserting the reading is honest at `reps`.

    Fails when (a) the selector's n disagrees with the pre-registered per-rep count -
    which is exactly how a selector that ignores `turn` is caught - or (b) a reading
    carried as a CLAIM sits below `analyze_stats.min_n_for(0.95)`.
    """
    selector, is_claim, per_rep = READINGS[name]
    got = len(selector(rows, fire_turn))
    expected = per_rep if isinstance(per_rep, int) else per_rep[rows[0]["arm"]]
    if got != expected:
        raise AssertionError("%s: selector returned n=%d per rep, pre-registered n=%d "
                             "(selector is not honouring `turn`)" % (name, got, expected))
    n_total = got * reps
    floor = A.min_n_for(0.95)
    if is_claim and n_total < floor:
        raise AssertionError("%s carried as a claim at n=%d < min_n_for(0.95)=%d"
                             % (name, n_total, floor))
    return got, n_total


class TestFireTurnsObservable(unittest.TestCase):
    def test_declared_fire_turns_reproduced_from_rows(self):
        fires = declared_fire_turns()
        rows = synth_all(fires)
        for arm, declared in fires.items():
            self.assertEqual(infer_fire_turn(rows, arm), declared,
                             "%s: fire turn not observable from row fields" % (arm,))

    def test_six_rows_per_regime_is_enough(self):
        """Derivability does not need 48 turns: 6 untreated + 6 treated rows suffice."""
        fires = declared_fire_turns()
        for arm, fire in fires.items():
            full = synth_rows(arm, fire)
            sample = [r for r in full if fire - 6 <= r["turn"] <= fire + 5
                      and r["kind"] == "turn"]
            # 6 rows per regime (the treated side is 6; the fire turn itself is in it).
            # pointer-stable fires at T2, so its untreated regime holds only 1 turn: the
            # untreated side is capped at what the fixture actually has.
            self.assertGreaterEqual(len([r for r in sample if r["turn"] >= fire]), 6)
            self.assertGreaterEqual(len([r for r in sample if r["turn"] < fire]),
                                    min(6, fire - 1))
            self.assertEqual(infer_fire_turn(sample, arm), fire,
                             "%s: fire turn lost at 6-rows-per-regime granularity" % (arm,))


class TestSelectorsDerivableFromRows(unittest.TestCase):
    def test_selectors_read_only_row_fields(self):
        fires = declared_fire_turns()
        rows = synth_all(fires)
        for arm in fires:
            sub = [r for r in rows if r["arm"] == arm]
            # every row carries ONLY ROW_FIELDS: a selector reading anything else dies here
            for r in sub:
                self.assertEqual(set(r), set(ROW_FIELDS))
            fire = infer_fire_turn(sub, arm)
            for name in READINGS:
                sel, _, per_rep = READINGS[name]
                expected = per_rep if isinstance(per_rep, int) else per_rep[arm]
                self.assertEqual(len(sel(sub, fire)), expected, "%s/%s" % (name, arm))

    def test_r_post_follows_the_rows_not_a_constant(self):
        """Shift the marker and R-post's n shifts with it - selection is row-driven."""
        arm = "transcript-grow"
        for fire, want in ((21, 28), (23, 26)):
            rows = synth_rows(arm, fire)
            got = len(select_r_post(rows, infer_fire_turn(rows, arm)))
            self.assertEqual(got, want)
            self.assertNotEqual(got, len(select_r_all(rows)))

    def test_r_post_is_inclusive_at_the_fire_turn(self):
        fires = declared_fire_turns()
        rows = synth_all(fires)
        for arm, fire in fires.items():
            sub = [r for r in rows if r["arm"] == arm]
            got = select_r_post(sub, fire)
            self.assertEqual(min(r["turn"] for r in got), fire)


class TestNFloor(unittest.TestCase):
    def test_pre_registered_n_at_three_reps(self):
        fires = declared_fire_turns()
        rows = synth_all(fires)
        floor = A.min_n_for(0.95)
        self.assertEqual(floor, 60)          # read back from analyze_stats, not copied
        got = {}
        for arm in fires:
            sub = [r for r in rows if r["arm"] == arm]
            fire = infer_fire_turn(sub, arm)
            for name in READINGS:
                got[(name, arm)] = check_reading(name, sub, fire)[1]
        self.assertEqual(got[("R-all", "transcript-grow")], 144)
        self.assertEqual(got[("R-post", "transcript-grow")], 84)
        self.assertEqual(got[("R-post", "lease-reopen")], 78)
        self.assertEqual(got[("R-post", "pointer-stable")], 141)
        self.assertEqual(got[("R-common", "lease-reopen")], 75)
        for n in got.values():
            self.assertGreaterEqual(n, floor)

    def test_quantile_ci_admits_all_three_readings(self):
        """Plumbing only: quantile_ci must not raise at these n (fake values, no file)."""
        for n in (144, 84, 78, 141, 75):
            vals = [100.0 + (i % 17) for i in range(n)]
            point, lo, hi, used = A.quantile_ci(vals, 0.95, resamples=200)
            self.assertEqual(used, n)
            self.assertLessEqual(lo, point)
            self.assertGreaterEqual(hi, point)
            self.assertGreaterEqual(n * (1.0 - 0.95), A.TAIL_MIN)


class TestMutantRedGreen(unittest.TestCase):
    def test_green_real_selector(self):
        fires = declared_fire_turns()
        for arm, fire in fires.items():
            rows = synth_rows(arm, fire)
            check_reading("R-post", rows, fire)      # must not raise

    def test_red_selector_ignoring_turn(self):
        """MUTANT: a selector that ignores `turn` and returns every row must go RED."""
        fires = declared_fire_turns()
        bands = dict(READINGS)
        try:
            READINGS["R-post"] = (lambda rows, fire_turn: _usable(rows), False,
                                  bands["R-post"][2])
            for arm, fire in fires.items():
                rows = synth_rows(arm, fire)
                with self.assertRaises(AssertionError):
                    check_reading("R-post", rows, fire)
        finally:
            READINGS.clear()
            READINGS.update(bands)

    def test_red_underfloor_claim(self):
        """MUTANT: R-common promoted to a claim over 1 rep (n=25 < 60) must go RED."""
        fires = declared_fire_turns()
        rows = synth_rows("transcript-grow", fires["transcript-grow"])
        bands = dict(READINGS)
        try:
            READINGS["R-common"] = (bands["R-common"][0], True, bands["R-common"][2])
            with self.assertRaises(AssertionError):
                check_reading("R-common", rows, None, reps=1)
        finally:
            READINGS.clear()
            READINGS.update(bands)


if __name__ == "__main__":
    unittest.main(verbosity=2)
