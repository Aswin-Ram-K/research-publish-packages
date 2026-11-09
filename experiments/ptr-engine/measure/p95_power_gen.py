#!/usr/bin/env python3
"""P95-POWER-FROM-ROWS generator. Read-only on every rows file; zero inference.

Regenerates experiments/ptr-engine/measure/P95-POWER.json deterministically.
Usage: python3 p95_power_gen.py [out.json]
"""
import json, glob, hashlib, importlib.util, os, subprocess, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MEAS = os.path.join(ROOT, 'experiments', 'ptr-engine', 'measure')
ANALYZE_STATS_REL = 'experiments/ptr-engine/longrun/analyze_stats.py'
ANALYZE_STATS = os.path.join(ROOT, ANALYZE_STATS_REL)

RESAMPLES = 10000          # percentile bootstrap for a p95 interval
POWER_OUTER = 1000         # paired resamples for the disjointness question
POWER_INNER = 200          # inner bootstrap depth for each interval in a pair
NS = [24, 48, 60, 96, 144, 384]
POWER_NS = [48, 60, 144]
NEED_NS = [48, 60, 96, 144, 192, 288, 384]
SEED = 20261026


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def git_provenance(path):
    """(tracked, dirty) for `path`, from git itself.

    tracked: `git ls-files --error-unmatch` succeeds. dirty: the bytes are not in HEAD -- either an
    untracked file (which exists in no commit) or a tracked file with local modifications. An
    untracked module therefore reads tracked=false, dirty=true, and cannot be silently assumed
    reproducible from HEAD.
    """
    rel = os.path.relpath(path, ROOT)
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    try:
        t = subprocess.run(['git', '-C', ROOT, 'ls-files', '--error-unmatch', '--', rel],
                           capture_output=True, text=True, env=env)
        tracked = t.returncode == 0
        if not tracked:
            return False, True
        d = subprocess.run(['git', '-C', ROOT, 'status', '--porcelain', '--', rel],
                           capture_output=True, text=True, env=env)
        return True, bool(d.stdout.strip())
    except OSError:
        return False, True


def analyze_stats_provenance():
    """Import the module and digest THE FILE THAT WAS IMPORTED.

    The digest is sha256(os.path.realpath(module.__file__)) taken straight after exec_module, not a
    path literal that assumes git tracking. analyze_stats.py has a `__main__` guard and defines only
    functions at module level, so importing it is side-effect free for files.
    """
    spec = importlib.util.spec_from_file_location('analyze_stats_atimport', ANALYZE_STATS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    real = os.path.realpath(mod.__file__)
    tracked, dirty = git_provenance(real)
    return {'imported': True, 'path': ANALYZE_STATS_REL,
            'realpath': os.path.relpath(real, ROOT),
            'sha256_atimport': sha(real), 'tracked': tracked, 'dirty': dirty}


def load(p):
    rows = []
    with open(p, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def usable(rows):
    """kind == 'turn' and a positive ttft_ms. timing_usable==False is tracked, not silently dropped."""
    out, dropped = [], 0
    for r in rows:
        if r.get('kind') != 'turn':
            continue
        t = r.get('ttft_ms')
        if not isinstance(t, (int, float)) or t <= 0:
            continue
        if r.get('timing_usable') is False:
            dropped += 1
            continue
        out.append((r.get('turn'), float(t)))
    out.sort(key=lambda x: (x[0] is None, x[0]))
    return [t for _, t in out], dropped


def p95(x):
    return float(np.quantile(x, 0.95))


def boot_p95(arr, n, rng, resamples=RESAMPLES):
    """Percentile bootstrap of the p95 at sample size n drawn from arr's ECDF."""
    a = np.asarray(arr)
    N = len(a)
    draws = a[rng.integers(0, N, size=(resamples, n))]
    q = np.quantile(draws, 0.95, axis=1)
    return {
        'n': n,
        'observed_n': N,
        'extrapolated': bool(n > N),
        'resamples': resamples,
        'median_p95_ms': round(float(np.median(q)), 2),
        'width_ms': round(float(np.quantile(q, 0.975) - np.quantile(q, 0.025)), 2),
        'ioi_low_ms': round(float(np.quantile(q, 0.025)), 2),
        'ioi_high_ms': round(float(np.quantile(q, 0.975)), 2),
    }


def ci_disjoint(a_sample, b_sample, rng):
    """95 % percentile bootstrap intervals for the two p95s; True when they do not overlap."""
    out = []
    for s in (a_sample, b_sample):
        idx = rng.integers(0, len(s), size=(POWER_INNER, len(s)))
        q = np.quantile(s[idx], 0.95, axis=1)
        out.append((np.quantile(q, 0.025), np.quantile(q, 0.975)))
    (alo, ahi), (blo, bhi) = out
    return ahi < blo or bhi < alo


def power_pair(a, b, n, rng):
    a = np.asarray(a); b = np.asarray(b)
    hit = 0
    for _ in range(POWER_OUTER):
        sa = a[rng.integers(0, len(a), size=n)]
        sb = b[rng.integers(0, len(b), size=n)]
        if ci_disjoint(sa, sb, rng):
            hit += 1
    return {'n': n, 'resamples': POWER_OUTER, 'inner': POWER_INNER,
            'disjoint_pct': round(100.0 * hit / POWER_OUTER, 1),
            'extrapolated': bool(n > min(len(a), len(b)))}


def lag1(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 3:
        return None
    xm = x - x.mean()
    d = float((xm[:-1] * xm[1:]).sum())
    v = float((xm * xm).sum())
    return d / v if v > 0 else None


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MEAS, 'P95-POWER.json')
    files = sorted(glob.glob(os.path.join(MEAS, 'rows-*.jsonl')))
    before = {os.path.basename(f): sha(f) for f in files}

    sets = {}   # set_id -> {'file','arm','grid_kind','timings','dropped'}
    per_file = []
    for f in files:
        rows = load(f)
        arms = {}
        for r in rows:
            if r.get('kind') != 'turn':
                continue
            arms.setdefault(r.get('arm') or '?', []).append(r)
        entry = {'file': os.path.basename(f), 'sha256': before[os.path.basename(f)],
                 'lines': len(rows), 'arms': {}}
        for arm, rs in sorted(arms.items()):
            vals, dropped = usable(rs)
            tools = any((r.get('tool_calls') is not None) or (r.get('fetch_followup') is not None) or
                        (r.get('kind') == 'tool-followup') for r in rows)
            entry['arms'][arm] = {'n_turn_rows': len(rs), 'n_usable': len(vals),
                                  'dropped_timing_usable_false': dropped}
            if len(vals) >= 10:
                sid = '%s::%s' % (os.path.basename(f)[:-6], arm)
                sets[sid] = {'file': os.path.basename(f), 'arm': arm, 'timings': vals,
                             'dropped': dropped,
                             'grid_kind': 'tools' if tools else 'non-tools',
                             'attribution': 'attribution_disputed' if tools else 'clean'}
        per_file.append(entry)

    rng = np.random.default_rng(SEED)

    # observed summaries: p50 and p95 with bootstrap intervals, per set
    observed = {}
    for sid, s in sets.items():
        a = np.asarray(s['timings'])
        observed[sid] = {
            'file': s['file'], 'arm': s['arm'], 'grid_kind': s['grid_kind'],
            'attribution': s['attribution'], 'n': len(a),
            'p50_ms': round(float(np.median(a)), 2),
            'p95_ms': round(p95(a), 2),
        }
        bo = boot_p95(s['timings'], len(a), rng)
        observed[sid]['p95_ci'] = {'low_ms': bo['ioi_low_ms'], 'high_ms': bo['ioi_high_ms'],
                                  'width_ms': bo['width_ms'], 'resamples': RESAMPLES}
        observed[sid]['mean_ms'] = round(float(a.mean()), 2)
        observed[sid]['sd_ms'] = round(float(a.std(ddof=1)), 2)
        observed[sid]['min_ms'] = round(float(a.min()), 2)
        observed[sid]['max_ms'] = round(float(a.max()), 2)

    # step 2: p95 interval width as a function of n, for every set
    p95_vs_n = {}
    for sid, s in sets.items():
        p95_vs_n[sid] = [boot_p95(s['timings'], n, rng) for n in NS]

    # step 3: two-arm disjointness (pointer-stable vs transcript-grow, same grid only)
    grids = {}
    for sid, s in sets.items():
        grids.setdefault(s['file'], {})[s['arm']] = sid
    power = {}
    for g, arms in sorted(grids.items()):
        if 'pointer-stable' in arms and 'transcript-grow' in arms:
            a = sets[arms['pointer-stable']]['timings']
            b = sets[arms['transcript-grow']]['timings']
            key = '%s::pointer-stable_vs_transcript-grow' % g
            cia = observed[arms['pointer-stable']]['p95_ci']
            cib = observed[arms['transcript-grow']]['p95_ci']
            power[key] = {
                'n_a': len(a), 'n_b': len(b),
                'observed_p95_ci_a': [cia['low_ms'], cia['high_ms']],
                'observed_p95_ci_b': [cib['low_ms'], cib['high_ms']],
                'observed_ci_disjoint_no_resampling': bool(cia['high_ms'] < cib['low_ms'] or
                                                           cib['high_ms'] < cia['low_ms']),
                'grid_kind': sets[arms['pointer-stable']]['grid_kind'],
                'observed_p50_gap_ms': round(float(np.median(b) - np.median(a)), 2),
                'observed_p95_gap_ms': round(p95(b) - p95(a), 2),
                'disjoint': [power_pair(a, b, n, rng) for n in POWER_NS],
                'required_n_scan': [power_pair(a, b, n, rng) for n in NEED_NS if n not in POWER_NS],
            }

    # step 4: lag-1 dependence along turn order, per run (one run per arm per file)
    autocorr = []
    for sid, s in sorted(sets.items()):
        r = lag1(s['timings'])
        if r is None:
            continue
        autocorr.append({'set': sid, 'arm': s['arm'], 'n': len(s['timings']),
                         'lag1': round(r, 4),
                         'n_eff_at_n': round(len(s['timings']) * (1 - r) / (1 + r), 2) if r < 1 else None})
    rs = [x['lag1'] for x in autocorr]
    med_r = float(np.median(rs)) if rs else 0.0
    z = np.arctanh(np.clip(np.array(rs), -0.999, 0.999))
    pooled_r = float(np.tanh(z.mean())) if len(z) else 0.0
    eff = {'per_set': autocorr,
           'n_sets': len(autocorr),
           'median_lag1': round(med_r, 4),
           'fisher_z_pooled_lag1': round(pooled_r, 4),
           'implied_effective_n': {str(k): round(k * (1 - pooled_r) / (1 + pooled_r), 1)
                                   for k in (48, 60, 144, 384) if pooled_r < 1}}

    # step 5: verdict, derived from the measured numbers
    primary = None
    for k in sorted(power):
        if k.startswith('rows-longrun-c'):
            primary = power[k]
    if primary is None and power:
        primary = power[sorted(power)[0]]
    grid_summary = []
    for k in sorted(power):
        v = power[k]
        d = {x['n']: x['disjoint_pct'] for x in v['disjoint']}
        d144 = d.get(144)
        grid_summary.append({
            'pair': k, 'n_a': v['n_a'], 'n_b': v['n_b'],
            'p50_gap_ms': v['observed_p50_gap_ms'], 'p95_gap_ms': v['observed_p95_gap_ms'],
            'observed_p95_ci_a': v['observed_p95_ci_a'],
            'observed_p95_ci_b': v['observed_p95_ci_b'],
            'observed_ci_disjoint_no_resampling': v['observed_ci_disjoint_no_resampling'],
            'disjoint_pct': {str(n): d[n] for n in sorted(d)},
            'separable_at_144': bool(d144 is not None and d144 >= 80),
        })
    disagreeing = [g['pair'] for g in grid_summary if not g['separable_at_144']]

    verdict, detail = 'H1 not testable from these distributions', ''
    if primary is not None:
        d = {x['n']: x['disjoint_pct'] for x in primary['disjoint']}
        scan = {x['n']: x['disjoint_pct'] for x in primary['required_n_scan']}
        d144 = d.get(144)
        if d144 is not None and d144 >= 80:
            verdict, detail = 'A* sufficient', 'disjoint at n=144 in %s %% of paired resamples' % d144
        else:
            need = sorted(n for n, p in {**scan, **d}.items() if p >= 80)
            verdict = 'A* underpowered'
            detail = ('disjoint at n=144 in %s %% of paired resamples; '
                      'smallest n reaching 80 %% in the scan: %s' %
                      (d144, need[0] if need else 'not reached up to n=%d' % max(NEED_NS)))
        if eff['implied_effective_n'].get('144', 0) < 60:
            detail += '; effective n at 144 is below the H1 floor of 60'
        detail += ('; scope: the verdict is measured on the grid the A* plan replicates '
                   '(rows-longrun-c, 4 arms x 48 turns). %d of %d grids holding the same two '
                   'arms do NOT separate them at n=144 (%s)'
                   % (len(disagreeing), len(grid_summary), ', '.join(disagreeing) or 'none'))

    try:
        astats = analyze_stats_provenance()
    except Exception as e:  # stated, not silent: the digest keeps its honest fallback
        rt, dd = git_provenance(ANALYZE_STATS)
        astats = {'imported': False, 'path': ANALYZE_STATS_REL,
                  'realpath': os.path.relpath(os.path.realpath(ANALYZE_STATS), ROOT),
                  'sha256_atimport': sha(ANALYZE_STATS) if os.path.exists(ANALYZE_STATS) else None,
                  'tracked': rt, 'dirty': dd,
                  'import_error': '%s: %s' % (type(e).__name__, e)}

    n_max = max(len(s['timings']) for s in sets.values())
    at_max = sorted(sid for sid, s in sets.items() if len(s['timings']) == n_max)
    tools_max = sorted(sid for sid, s in sets.items() if s['grid_kind'] == 'tools')
    doc = {
        'unit': 'P95-POWER-FROM-ROWS',
        'method': {
            'rows_glob': 'experiments/ptr-engine/measure/rows-*.jsonl',
            'usable_row': "kind == 'turn' and ttft_ms > 0 and timing_usable is not False",
            'bootstrap': 'percentile bootstrap of the 95th percentile, %d resamples' % RESAMPLES,
            'ns': NS,
            'power_outer': POWER_OUTER, 'power_inner': POWER_INNER,
            'disjointness': 'two 95 % percentile-bootstrap intervals for the two p95s are disjoint',
            'seed': SEED,
            'inference_requests': 0,
            'analyze_stats': dict(astats, note=(
                'sha256 of os.path.realpath(module.__file__) for the module this generator imports, '
                'taken immediately after import; tracked/dirty come from git ls-files '
                '--error-unmatch and git status --porcelain (untracked => tracked=false, '
                'dirty=true), so a moveless-but-untracked module is a STATED condition, not a '
                'silent mismatch. quantile_ci is NOT used: this generator implements its own '
                'percentile bootstrap, so no statistic below depends on analyze_stats.py.')),
            'analyze_stats_sha256_atimport': astats.get('sha256_atimport'),
            'pooling_policy': ('no pooling across arms or grids; each (rows file, arm) is its own set. '
                               'Tools-grid rows are marked attribution_disputed.'),
        },
        'rows_files': per_file,
        'sets': observed,
        'largest_n_set': {
            'n_max_usable': n_max,
            'sets_at_n_max': at_max,
            'note': ('no single rows file carries more than %d usable timings for any arm; %d is '
                     'reached only by pooling the same arm across separate grid files, which this '
                     'analysis refuses to do. Every n > %d below is an ECDF extrapolation, not an '
                     'observation.' % (n_max, 3 * n_max, n_max)),
            'tools_pointer_stable_sets': tools_max,
        },
        'per_grid_summary': grid_summary,
        'p95_vs_n': p95_vs_n,
        'power': power,
        'autocorrelation': eff,
        'verdict': verdict,
        'verdict_detail': detail,
    }

    after = {os.path.basename(f): sha(f) for f in files}
    doc['rows_files_unchanged'] = (before == after)
    doc['rows_sha256_changed'] = [k for k in before if before.get(k) != after.get(k)]

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write('\n')
    print('wrote', out_path, '| verdict:', verdict, '| sets:', len(sets),
          '| rows unchanged:', doc['rows_files_unchanged'])


if __name__ == '__main__':
    main()
