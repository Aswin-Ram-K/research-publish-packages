#!/usr/bin/env python3
"""STATE-CLIFF run phase: execute the 64->48->32->16 max_mamba_cache_size sweep."""
from __future__ import annotations
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
M4_BATTERY = REPO / "experiments/context-cache/cells/M4/battery.py"
LV = REPO / "experiments/context-cache/cells/WIN-SGL/launch_variant.py"
PROD_UNIT = "gx10-occamy-nvfp4.service"
HOST = "192.168.2.168"
BASE = f"http://{HOST}:8012"
LOG = HERE / "run_sweep.log"
LOCK = REPO / "experiments/context-cache/.occamy.lock"
LADDER = [64, 48, 32, 16]
RESTORE_KEYS = ["page_size","mamba_radix_cache_strategy","radix_eviction_policy",
                "mem_fraction_static","kv_cache_dtype","max_mamba_cache_size"]

def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")

def sh(cmd, timeout=300):
    log(f"$ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip():
        log("  stdout: " + r.stdout.strip()[:500])
    if r.stderr.strip():
        log("  stderr: " + r.stderr.strip()[:500])
    return r

def ssh(cmd, timeout=300):
    return sh(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=no",
               f"zer0null@{HOST}"] + list(cmd), timeout=timeout)

def health(deadline=1800):
    t0 = time.time()
    while time.time() - t0 < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/health", timeout=10) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(5)
    return False

def capture_server_info(path):
    with urllib.request.urlopen(f"{BASE}/get_server_info", timeout=30) as r:
        data = json.loads(r.read())
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return data

def wait_lock_free(deadline=300):
    t0 = time.time()
    while time.time() - t0 < deadline:
        try:
            fd = os.open(str(LOCK), os.O_RDWR | os.O_CREAT)
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            return True
        except (BlockingIOError, OSError):
            time.sleep(2)
    return False

def restore_proof(doc):
    base = json.loads((REPO/"state/config/occamy-restore-baseline.json").read_text())
    mism = []
    for k in RESTORE_KEYS:
        if doc.get(k) != base.get(k):
            mism.append(f"{k}: got {doc.get(k)!r} want {base.get(k)!r}")
    return mism

def make_battery(rung_dir, size):
    src = M4_BATTERY.read_text()
    m4 = str(REPO / "experiments/context-cache/cells/M4")
    rd = str(rung_dir)
    src = src.replace('HERE = Path(__file__).resolve().parent', f'HERE = Path({m4!r})')
    src = src.replace('CELL_DIR = HERE', f'CELL_DIR = Path({rd!r})')
    src = src.replace('UNIT = "M4-EVICT"', f'UNIT = "STATE-CLIFF-{size}"')
    (rung_dir / "battery.py").write_text(src)
    return rung_dir / "battery.py"

def rung(size):
    rung_dir = HERE / f"rung-{size}"
    rung_dir.mkdir(parents=True, exist_ok=True)
    log(f"=== RUNG {size} ===")
    log("stopping production (systemd)")
    ssh(["systemctl","--user","stop",PROD_UNIT], timeout=120)
    time.sleep(3)
    cid = f"sc{size}"
    name = f"gx10-occamy-nvfp4-{cid.lower()}"
    log(f"creating variant {name}")
    r = sh([sys.executable, str(LV), "--config-id", cid,
            f"--flag=--max-mamba-cache-size={size}", "--apply"], timeout=300)
    if r.returncode != 0:
        log(f"variant create failed rc={r.returncode}; restoring production")
        ssh(["systemctl","--user","start",PROD_UNIT], timeout=120)
        health()
        return False
    log("waiting health on variant")
    if not health(900):
        log("health gate FAILED; restoring")
        ssh(["docker","stop","-t","60",name], timeout=120)
        ssh(["docker","rm",name], timeout=120)
        ssh(["systemctl","--user","start",PROD_UNIT], timeout=120)
        health()
        return False
    info = capture_server_info(rung_dir / "server_info.json")
    if info.get("max_mamba_cache_size") != size or info.get("page_size") != 1:
        log(f"READBACK GATE FAILED: mamba={info.get('max_mamba_cache_size')} page={info.get('page_size')}")
        ssh(["docker","stop","-t","60",name], timeout=120)
        ssh(["docker","rm",name], timeout=120)
        ssh(["systemctl","--user","start",PROD_UNIT], timeout=120)
        health()
        return False
    log(f"readback OK: max_mamba_cache_size={info.get('max_mamba_cache_size')}")
    log("waiting for lock free")
    wait_lock_free(300)
    bat = make_battery(rung_dir, size)
    log(f"running battery -> {rung_dir}")
    r = sh([sys.executable, str(bat)], timeout=7200)
    log(f"battery rc={r.returncode}")
    log("stopping+removing variant")
    ssh(["docker","stop","-t","60",name], timeout=120)
    ssh(["docker","rm",name], timeout=120)
    log("starting production (systemd)")
    ssh(["systemctl","--user","start",PROD_UNIT], timeout=120)
    if not health(1800):
        log("PRODUCTION HEALTH FAILED after restore")
        (rung_dir/"restore-proof-FAILED.json").write_text(json.dumps({"reason":"health failed"}))
        return False
    doc = capture_server_info(rung_dir / "restore_server_info.json")
    mism = restore_proof(doc)
    if mism:
        log("RESTORE PROOF FAILED: " + "; ".join(mism))
        (rung_dir/"restore-proof-FAILED.json").write_text(json.dumps({"mismatches":mism}))
        return False
    log(f"restore proof PASS (rung {size})")
    return True

def main():
    LOG.write_text("")
    log("STATE-CLIFF sweep starting")
    for size in LADDER:
        ok = rung(size)
        if not ok:
            log(f"HALTING after rung {size} failure")
            break
    log("SWEEP COMPLETE")

if __name__ == "__main__":
    main()
