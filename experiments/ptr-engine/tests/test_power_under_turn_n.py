#!/usr/bin/env python3
"""Guard: the power artefact is measured with the TURN selector, not the request filter.

`measure/POWER-UNDER-TURN-N.json` claims every per-cell `n` is the analyser's per-turn
count (`analyze_stats.turn_latency_rows`), not the count of ttft-bearing request rows.
This test re-derives the counts from the pinned rows and fails if the artefact was built
with the request filter — the exact substitution the card exists to catch.

    python3 experiments/ptr-engine/tests/test_power_under_turn_n.py            # green
    python3 experiments/ptr-engine/tests/test_power_under_turn_n.py --red-green # green + red proof

`--red-green` reproduces the RED by re-measuring with a request-filter selector in memory
(no file is edited) and showing that measurement DISAGREES with the artefact, i.e. the
guard fires on precisely the mistake it is written against.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
ENGINE = os.path.dirname(HERE)                     # experiments/ptr-engine
ROOT = os.path.dirname(os.path.dirname(ENGINE))    # repository root
ARTEFACT = os.path.join(ENGINE, 'measure', 'POWER-UNDER-TURN-N.json')
ANALYZE = os.path.join(ENGINE, 'longrun', 'analyze_stats.py')

MIN_N_FOR_P95 = 60          # analyze_stats.min_n_for(0.95)
DROP_STOP = ('length', 'runaway_turn')
# (rows file, request-filter n, turn-selector n) for the tools-on grids, where the two differ most
TOOLS_CASES = [
    ('rows-longrun-v4-tools-2026-10-26.jsonl', 68, 47),
    ('rows-longrun-v5-tools.jsonl', 72, 47),
    ('rows-longrun-v6-tools.jsonl', 72, 48),
]


def _analyze():
    spec = importlib.util.spec_from_file_location('analyze_stats_for_power_test', ANALYZE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load(name):
    return [json.loads(line) for line in open(os.path.join(ENGINE, 'measure', name),
                                              encoding='utf-8') if line.strip()]


def _artefact():
    with open(ARTEFACT, encoding='utf-8') as f:
        return json.load(f)


def _turn_series(rows, A):
    """The analyser's own selector: one row per turn, stop-reason exclusions applied."""
    selected, _meta = A.turn_latency_rows(rows)
    out = {}
    for row in selected:
        t = row.get('ttft_ms')
        if not isinstance(t, (int, float)) or isinstance(t, bool) or not (float(t) > 0):
            continue
        if row.get('stop_reason') in DROP_STOP or row.get('truncated') is True:
            continue
        out.setdefault(row.get('arm') or '?', []).append(float(t))
    return out


def _request_series(rows):
    """The WRONG denominator: every ttft-bearing row, follow-ups included, no turn dedup."""
    out = {}
    for row in rows:
        t = row.get('ttft_ms')
        if not isinstance(t, (int, float)) or isinstance(t, bool) or not (float(t) > 0):
            continue
        out.setdefault(row.get('arm') or '?', []).append(float(t))
    return out


def test_the_artefact_names_the_turn_selector():
    method = _artefact()['method']
    assert 'turn_latency_rows' in method['selector'], method['selector']
    assert ('tool-followup' in method['selector']) or ('never a turn' in method['selector'])
    assert method['min_n_for_p95'] == MIN_N_FOR_P95


def test_every_per_cell_n_is_the_turn_selector_count():
    A = _analyze()
    art = _artefact()['cells_turn_n']
    checked = 0
    for key, cell in art.items():
        series = _turn_series(_load(cell['file']), A)
        expect = len(series.get(cell['arm'], []))
        assert cell['n_turn'] == expect, (key, cell['n_turn'], expect)
        assert cell['n_turn'] <= cell['n_request'], key
        checked += 1
    assert checked >= 12, checked


def test_tools_grids_are_counted_per_turn_not_per_request():
    """The whole point of the card: 68/72/72 request rows are 47/47/48 turns."""
    A = _analyze()
    art = _artefact()['cells_turn_n']
    for name, n_request, n_turn in TOOLS_CASES:
        rows = _load(name)
        key = [k for k in art if art[k]['file'] == name]
        assert key, name
        cell = art[key[0]]
        assert cell['n_request'] == n_request, (name, cell['n_request'], n_request)
        assert cell['n_turn'] == n_turn, (name, cell['n_turn'], n_turn)
        assert len(_turn_series(rows, A)['pointer-stable']) == n_turn
        assert len(_request_series(rows)['pointer-stable']) == n_request
        assert cell['n_turn'] != cell['n_request'], name


def test_every_cell_below_the_floor_is_refused_by_name():
    art = _artefact()['cells_turn_n']
    for key, cell in art.items():
        ci = cell['p95_ci']
        if cell['n_turn'] < MIN_N_FOR_P95:
            assert ci['refused'] is True, key
            assert 'minimum n for p95 is %d' % MIN_N_FOR_P95 in ci['message'], (key, ci['message'])
            assert 'n*(1-q)' in ci['message'], key
        else:  # pragma: no cover - no cell on disk reaches the floor
            assert ci['refused'] is False, key


def test_a_pair_below_the_floor_has_no_admissible_fraction():
    power = _artefact()['power']['rows-longrun-c-2026-10-26.jsonl::pointer-stable_vs_transcript-grow']
    for n in ('47', '48'):
        row = power['n'][n]['turn_n_floor']
        assert row['admissible'] is False, n
        assert row['disjoint_pct'] is None, n
        assert 'minimum n for p95 is %d' % MIN_N_FOR_P95 in row['refusal'], n
    for n in ('60', '96', '144'):
        row = power['n'][n]['turn_n_floor']
        assert row['admissible'] is True, n
        assert isinstance(row['disjoint_pct'], float), n


def test_verdict_is_forced_by_the_effective_n_arithmetic():
    art = _artefact()
    assert art['verdict'] in ('grid_can_adjudicate_h1', 'grid_underpowered', 'h1_not_testable')
    assert art['verdict'] == 'grid_underpowered'
    forcing = art['verdict_forcing_numbers']
    assert forcing['design_pair_raw_turns_per_arm'] >= MIN_N_FOR_P95      # raw floor met
    assert forcing['effective_on_binding_arm'] < MIN_N_FOR_P95            # effective floor not met
    assert forcing['n_would_need_raw_turns_per_arm'] > forcing['design_pair_raw_turns_per_arm']
    price = art['price']
    import math
    # the priced shape is 6 runs x 48 = 288 turns/arm for the pair, rounded UP from the 276 the
    # effective floor needs (PARM-1:137 pins 48 turns/arm, so the lever is runs, not depth).
    turns_pair = max(288, forcing['n_would_need_raw_turns_per_arm'])
    turns = 2 * turns_pair + 2 * 96                                      # pair + ctx at PARM-1:142
    assert price['conformant_four_arm_768_turns_6runs_pair_2runs_ctx'] == math.ceil(turns * price['ledger_factor'])
    assert price['price_of_288_turns_per_arm'] == math.ceil(288 * price['ledger_factor'])
    assert turns_pair % 48 == 0, turns_pair
    assert art['offline'] == {'requests_sent': 0, 'network_events': 0, 'live_cells': 0}


# ---------------------------------------------------------------------------
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    red_green = '--red-green' in argv
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    failures = 0
    for t in tests:
        try:
            t()
            print('PASS', t.__name__)
        except AssertionError as e:
            failures += 1
            print('FAIL', t.__name__, '->', e)
    print('%d/%d green case(s), %d failure(s)' % (len(tests) - failures, len(tests), failures))
    if red_green:
        # RED: measure the same rows with the REQUEST filter and show the artefact's invariant breaks.
        A = _analyze()
        art = _artefact()['cells_turn_n']
        reds = 0
        for name, n_request, n_turn in TOOLS_CASES:
            req = len(_request_series(_load(name))['pointer-stable'])
            published = [c['n_turn'] for c in art.values() if c['file'] == name][0]
            if req != published and req == n_request:
                reds += 1
                print('RED request-filter selector on %s: %d samples, artefact says %d turns'
                      % (name, req, published))
        # the guard's own failure mode: comparing a request count to the turn count
        if reds != len(TOOLS_CASES):
            print('RED FAILED: the request filter produced the same counts as the turn selector')
            failures += 1
        print('%d/%d red case(s) reproduced' % (reds, len(TOOLS_CASES)))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
