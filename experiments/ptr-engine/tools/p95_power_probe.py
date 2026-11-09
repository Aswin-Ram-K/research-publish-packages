#!/usr/bin/env python3
"""p95_power_probe.py — independent re-derivation of the P95-POWER numbers from the rows.

Read-only, zero inference, no import of the generator. It loads every `rows-*.jsonl` itself,
recomputes the closed-form quantities (n, p50, p95, p50/p95 gaps, lag-1 autocorrelation, median
lag-1, Fisher-z pooled lag-1, implied effective n) and compares each to P95-POWER.json at the
precision the JSON records. It then re-applies the generator's stated verdict rule to the stored
paired-resample percentages and to the stored per-grid separation, and reports whether the verdict
string follows from them.

The bootstrap percentages themselves (disjoint_pct, p95 interval widths) are NOT reproduced here:
that is the job of experiments/ptr-engine/measure/p95-power-verify.sh, which regenerates the whole
file byte-for-byte. This probe checks that those stored numbers are the ones the arithmetic from the
pinned rows requires, i.e. that no statistic drifted while the digest did.

Usage: python3 experiments/ptr-engine/tools/p95_power_probe.py [--quiet]
Exit 0 = every recomputed value matches and the verdict follows from the stated rule.
"""
import glob
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MEAS = os.path.join(ROOT, 'experiments', 'ptr-engine', 'measure')
JSON_PATH = os.path.join(MEAS, 'P95-POWER.json')

failures = []


def check(label, got, want, tol=0.0):
    ok = (got == want) if tol == 0.0 else (got is not None and want is not None and abs(got - want) <= tol)
    if not ok:
        failures.append('%s: recomputed %r != recorded %r' % (label, got, want))
    return ok


def usable(rows):
    out = []
    for r in rows:
        if r.get('kind') != 'turn':
            continue
        t = r.get('ttft_ms')
        if not isinstance(t, (int, float)) or t <= 0:
            continue
        if r.get('timing_usable') is False:
            continue
        out.append((r.get('turn'), float(t)))
    out.sort(key=lambda x: (x[0] is None, x[0]))
    return [t for _, t in out]


def lag1(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 3:
        return None
    xm = x - x.mean()
    v = float((xm * xm).sum())
    return float((xm[:-1] * xm[1:]).sum()) / v if v > 0 else None


def main():
    doc = json.load(open(JSON_PATH, encoding='utf-8'))
    sets = {}
    for f in sorted(glob.glob(os.path.join(MEAS, 'rows-*.jsonl'))):
        arms = {}
        for r in open(f, encoding='utf-8'):
            r = r.strip()
            if not r:
                continue
            r = json.loads(r)
            if r.get('kind') == 'turn':
                arms.setdefault(r.get('arm') or '?', []).append(r)
        for arm, rs in arms.items():
            vals = usable(rs)
            if len(vals) >= 10:
                sets['%s::%s' % (os.path.basename(f)[:-6], arm)] = vals

    check('set count', len(sets), len(doc['sets']))
    for sid, vals in sorted(sets.items()):
        rec = doc['sets'].get(sid)
        if rec is None:
            failures.append('set %s missing from JSON' % sid)
            continue
        a = np.asarray(vals)
        check('%s n' % sid, len(a), rec['n'])
        check('%s p50' % sid, round(float(np.median(a)), 2), rec['p50_ms'])
        check('%s p95' % sid, round(float(np.quantile(a, 0.95)), 2), rec['p95_ms'])
        check('%s mean' % sid, round(float(a.mean()), 2), rec['mean_ms'])
        check('%s sd' % sid, round(float(a.std(ddof=1)), 2), rec['sd_ms'])

    # gaps and per-grid separation, recomputed from the raw timings
    grids = {}
    for sid in sets:
        stem, arm = sid.split('::', 1)
        grids.setdefault(stem + '.jsonl', {})[arm] = sid
    for key, rec in doc['power'].items():
        g = key.split('::')[0]
        a = sets[grids[g]['pointer-stable']]
        b = sets[grids[g]['transcript-grow']]
        check('%s p50_gap' % key, round(float(np.median(b) - np.median(a)), 2), rec['observed_p50_gap_ms'])
        check('%s p95_gap' % key, round(float(np.quantile(b, 0.95) - np.quantile(a, 0.95)), 2),
              rec['observed_p95_gap_ms'])

    # autocorrelation
    rs = []
    for sid, vals in sets.items():
        r = lag1(vals)
        if r is None:
            continue
        rs.append((sid, r))
        for rec in doc['autocorrelation']['per_set']:
            if rec['set'] == sid:
                check('%s lag1' % sid, round(r, 4), rec['lag1'])
                check('%s n_eff' % sid,
                      round(len(vals) * (1 - r) / (1 + r), 2) if r < 1 else None,
                      rec['n_eff_at_n'], tol=0.0)
    check('n_sets', len(rs), doc['autocorrelation']['n_sets'])
    values = [r for _, r in rs]
    med = round(float(np.median(values)), 4)
    z = np.arctanh(np.clip(np.array(values), -0.999, 0.999))
    pooled = round(float(np.tanh(z.mean())), 4)
    check('median_lag1', med, doc['autocorrelation']['median_lag1'])
    check('fisher_z_pooled', pooled, doc['autocorrelation']['fisher_z_pooled_lag1'])
    for k, want in doc['autocorrelation']['implied_effective_n'].items():
        check('n_eff@%s' % k, round(int(k) * (1 - pooled) / (1 + pooled), 1), want, tol=0.0)

    # verdict rule, applied to the stored numbers by the rule the generator states
    primary = None
    for k in sorted(doc['power']):
        if k.startswith('rows-longrun-c'):
            primary = doc['power'][k]
    d144 = {x['n']: x['disjoint_pct'] for x in primary['disjoint']}[144]
    verdict = 'A* sufficient' if d144 >= 80 else 'A* underpowered'
    check('verdict', verdict, doc['verdict'])
    check('primary d144>=80', d144 >= 80, doc['verdict'].startswith('A* sufficient'))
    not_sep = [g['pair'] for g in doc['per_grid_summary'] if not g['separable_at_144']]
    check('grids not separating at 144', len(not_sep), 2)
    check('separating grid is rows-longrun-c',
          bool(primary['observed_p95_gap_ms'] > 0 and not_sep == [
              'rows-longrun-v3-2026-10-26.jsonl::pointer-stable_vs_transcript-grow',
              'rows-longrun-v4-2026-10-26.jsonl::pointer-stable_vs_transcript-grow']), True)

    print('probe: %d sets, %d failure(s)' % (len(sets), len(failures)))
    for f in failures:
        print('  FAIL', f)
    print('verdict reproduces:', doc['verdict'], '| d144 =', d144, '%')
    print('p50 gaps (c, v3, v4) ms:',
          [g['p50_gap_ms'] for g in doc['per_grid_summary']],
          '| p95 gaps:', [g['p95_gap_ms'] for g in doc['per_grid_summary']])
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
