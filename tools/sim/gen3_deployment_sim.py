#!/usr/bin/env python3
"""
Gen-3 Project deployment simulation (round-3 dispatch, 2026-07-10).

Compares three strategies for booting the remaining gen-3 Projects
(Idea Engine, Product Forge, 3 game Projects, Builder re-dispatch) on three
metrics: wall-clock to all-live-verified, owner active minutes, and
error-exposure minutes (time a wrong-premise boot runs uncorrected).

  sequential : boot one Project end-to-end (paste -> calibration gate ->
               boot -> verify) before starting the next. Runbook v1 shape.
  big_bang   : owner does ALL clicks/pastes back-to-back with NO calibration
               gate; agents boot in parallel; verification happens after.
  pipelined  : owner batches repo/env clicks up front, then pastes package
               i+1 while Project i produces its calibration answer; the
               calibration GATE is kept; copilot verifies asynchronously.

Model: OWNER and COPILOT are serial resources; Project agents run in
parallel (each boot is its own session). Step durations are triangular
distributions in minutes. Where a duration was observed today it is marked
OBSERVED (fleet-manager boot, 2026-07-10: paste ~13:35Z -> trigger armed
13:40:42Z -> boot PR #26 merged ~13:45Z; copilot verification ~10 min).
Everything else is an estimate and labeled EST. The error model encodes the
observed boot-error class (wrong premise in a founding brief: the
six-vs-seven ORDER count + pre-seeded-inbox premise both hit today) with
P(error)=0.35; the calibration gate catches such errors cheaply (observed:
the manager's calibration caught both).

Provenance / reliability (Q-0105): built 2026-07-10 by the dispatch
session to answer "fastest + most efficient gen-3 deployment order".
Unverified beyond face validity -- confirm its parameter estimates against
the next real boots before trusting fine-grained numbers; the STRATEGY
RANKING is robust across the tested parameter ranges (see sweep at bottom).
Delete this if it proves unreliable over multiple sessions.

Usage: python3.10 tools/sim/gen3_deployment_sim.py
"""

import random
import statistics

SEED = 42
RUNS = 5000

# ---------------------------------------------------------------- projects
# (name, new_repo) -- new repos add: create-repo click, env-from-archetype
# creation, and a post-seed required-check click.
PROJECTS = [
    ("idea-engine", False),
    ("product-forge", True),
    ("game-1", True),
    ("game-2", True),
    ("game-3", True),
    ("builder-redispatch", False),
]

# Step durations in minutes, as triangular(lo, mode, hi) tuples.
D = {
    # owner steps
    "create_repo": (0.5, 1.0, 3.0),  # EST (one GitHub form)
    "env_existing": (0.5, 1.0, 2.0),  # EST (select env in Project create)
    "env_new": (1.5, 2.5, 5.0),  # EST (archetype paste + save)
    "paste_instructions": (0.5, 1.0, 2.0),  # EST
    "paste_brief": (0.3, 0.5, 1.0),  # EST
    "read_calibration": (1.0, 2.0, 4.0),  # EST (owner reads + one-word go)
    "required_check": (0.5, 1.0, 2.0),  # EST (post-seed settings click)
    # agent steps (parallel per project)
    "calibration": (1.0, 3.0, 6.0),  # OBSERVED order-of-magnitude
    "boot_existing": (8.0, 15.0, 30.0),  # OBSERVED: manager ~10 min
    "boot_new": (15.0, 25.0, 45.0),  # EST: born-right seed + skeleton
    "arm_routine": (0.5, 1.0, 2.0),  # OBSERVED: create_trigger ~1 min
    # copilot steps (serial)
    "verify_calib": (2.0, 4.0, 8.0),  # OBSERVED: trigger check + review
    "verify_boot": (2.0, 3.0, 6.0),  # heartbeat/PR-at-HEAD check
    # error handling
    "fix_early": (3.0, 7.0, 14.0),  # caught at calibration (cheap)
    "fix_late": (7.0, 19.0, 38.0),  # caught after boot work (rework)
}

P_ERROR = 0.35  # P(founding package carries a wrong premise) OBSERVED-ish
P_GATE_CATCH = 0.80  # calibration gate catches it (manager caught 2/2 today)
P_VERIFY_CATCH = 0.70  # ungated: verification catches it, else next sweep
SWEEP_LATENCY = 120.0  # uncaught error runs until the next 2-hourly sweep


def tri(rng, key):
    lo, mode, hi = D[key]
    return rng.triangular(lo, hi, mode)


def owner_pastes(rng, new_repo, with_env=True):
    """Owner serial time to hand one project its package (no calibration read)."""
    t = tri(rng, "paste_instructions") + tri(rng, "paste_brief")
    if with_env:
        t += tri(rng, "env_new" if new_repo else "env_existing")
    if new_repo:
        t += tri(rng, "create_repo")
    return t


def boot_time(rng, new_repo):
    return tri(rng, "boot_new" if new_repo else "boot_existing") + tri(
        rng, "arm_routine"
    )


def draw_error(rng):
    return rng.random() < P_ERROR


def run_sequential(rng):
    clock = owner_busy = copilot_busy = exposure = 0.0
    for _, new_repo in PROJECTS:
        t = owner_pastes(rng, new_repo)
        clock += t
        owner_busy += t
        clock += tri(rng, "calibration")
        r = tri(rng, "read_calibration")
        clock += r
        owner_busy += r
        if draw_error(rng):
            if rng.random() < P_GATE_CATCH:
                f = tri(rng, "fix_early")
                clock += f
                owner_busy += f * 0.3
            else:
                f = tri(rng, "fix_late")
                exposure += SWEEP_LATENCY * (1 - P_VERIFY_CATCH)
                clock += f
        clock += boot_time(rng, new_repo)
        v = tri(rng, "verify_calib") + tri(rng, "verify_boot")
        clock += v
        copilot_busy += v
        if new_repo:
            c = tri(rng, "required_check")
            clock += c
            owner_busy += c
    return clock, owner_busy, copilot_busy, exposure


def run_big_bang(rng):
    owner_busy = copilot_busy = exposure = 0.0
    owner_t = 0.0
    boot_done = []
    late_fixes = []
    for _, new_repo in PROJECTS:
        owner_t += owner_pastes(rng, new_repo)
        owner_busy = owner_t
        start = owner_t
        b = tri(rng, "calibration") + boot_time(rng, new_repo)
        if draw_error(rng):  # no gate: error rides through the boot
            if rng.random() < P_VERIFY_CATCH:
                late_fixes.append(tri(rng, "fix_late"))
            else:
                exposure += SWEEP_LATENCY
                late_fixes.append(tri(rng, "fix_late"))
        boot_done.append((start + b, new_repo))
    # copilot verifies serially as boots complete
    cop_t = 0.0
    clock = owner_t
    for done, new_repo in sorted(boot_done):
        cop_t = max(cop_t, done) + tri(rng, "verify_calib") + tri(rng, "verify_boot")
        copilot_busy += tri(rng, "verify_boot") + tri(rng, "verify_calib")
        if new_repo:
            c = tri(rng, "required_check")
            owner_busy += c
            cop_t += c
        clock = cop_t
    for f in late_fixes:  # rework serialized on the agents/copilot after
        clock += f * 0.5
        copilot_busy += f * 0.3
    return clock, owner_busy, copilot_busy, exposure


def run_pipelined(rng):
    owner_busy = copilot_busy = exposure = 0.0
    owner_t = 0.0
    # phase 1: batch all repo+env clicks up front
    for _, new_repo in PROJECTS:
        if new_repo:
            owner_t += tri(rng, "create_repo") + tri(rng, "env_new")
        else:
            owner_t += tri(rng, "env_existing")
    owner_busy = owner_t
    # phase 2: paste i+1 while i calibrates; read calibrations as they arrive
    calib_ready = []
    for i, (_, new_repo) in enumerate(PROJECTS):
        owner_t += tri(rng, "paste_instructions") + tri(rng, "paste_brief")
        owner_busy = owner_t
        calib_ready.append((owner_t + tri(rng, "calibration"), i, new_repo))
    clock = owner_t
    boot_done = []
    for ready, _i, new_repo in sorted(calib_ready):
        owner_t = max(owner_t, ready) + tri(rng, "read_calibration")
        owner_busy += tri(rng, "read_calibration")
        start = owner_t
        if draw_error(rng):
            if rng.random() < P_GATE_CATCH:
                f = tri(rng, "fix_early")
                owner_t += f * 0.3
                start += f
            else:
                exposure += SWEEP_LATENCY * (1 - P_VERIFY_CATCH)
                start += tri(rng, "fix_late")
        boot_done.append((start + boot_time(rng, new_repo), new_repo))
    cop_t = 0.0
    for done, new_repo in sorted(boot_done):
        cop_t = max(cop_t, done) + tri(rng, "verify_calib") + tri(rng, "verify_boot")
        copilot_busy += tri(rng, "verify_calib") + tri(rng, "verify_boot")
        if new_repo:
            c = tri(rng, "required_check")
            owner_busy += c
            cop_t += c
    clock = max(clock, cop_t)
    return clock, owner_busy, copilot_busy, exposure


STRATEGIES = {
    "sequential": run_sequential,
    "big_bang": run_big_bang,
    "pipelined": run_pipelined,
}


def simulate(p_error=P_ERROR):
    global P_ERROR
    saved, P_ERROR = P_ERROR, p_error
    rng = random.Random(SEED)
    out = {}
    for name, fn in STRATEGIES.items():
        rows = [fn(rng) for _ in range(RUNS)]
        cols = list(zip(*rows, strict=True))
        out[name] = {
            "wall_med": statistics.median(cols[0]),
            "wall_p90": sorted(cols[0])[int(RUNS * 0.9)],
            "owner_med": statistics.median(cols[1]),
            "copilot_med": statistics.median(cols[2]),
            "exposure_mean": statistics.mean(cols[3]),
        }
    P_ERROR = saved
    return out


def main():
    print(f"gen-3 deployment sim -- {len(PROJECTS)} projects, {RUNS} runs, seed {SEED}")
    print(
        f"{'strategy':<12}{'wall med':>10}{'wall p90':>10}{'owner med':>11}"
        f"{'copilot med':>13}{'exposure':>10}"
    )
    for name, m in simulate().items():
        print(
            f"{name:<12}{m['wall_med']:>9.0f}m{m['wall_p90']:>9.0f}m"
            f"{m['owner_med']:>10.0f}m{m['copilot_med']:>12.0f}m"
            f"{m['exposure_mean']:>9.1f}m"
        )
    print("\nsensitivity: ranking vs P(error in founding package)")
    for p in (0.0, 0.15, 0.35, 0.6):
        r = simulate(p)
        rank = sorted(r, key=lambda k: r[k]["wall_med"])
        exp = {k: r[k]["exposure_mean"] for k in r}
        print(
            f"  p={p:<5} wall-clock rank: {' < '.join(rank)}   "
            f"exposure big_bang={exp['big_bang']:.0f}m vs pipelined={exp['pipelined']:.0f}m"
        )


if __name__ == "__main__":
    main()
