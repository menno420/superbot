"""Retention-policy simulator for the context economy (plan §5.B, Lane B5).

A generalized port of superbot's ``tools/sim/retention_policy_sim.py``
(sim-driven design applied to the memory system itself). It models a docs
corpus growing over sessions, agents reading it (boot route, grep discovery,
directory scans, back-references into pruned content, stale encounters), and a
candidate retention policy acting on it. The grid search scores each candidate
on expected agent context cost (words per session) under a hard feasibility
constraint (retrieval-miss risk), with a secondary lean-by-construction
objective (smallest tree at horizon among near-best feasible policies) and a
×1/3–×3 sensitivity sweep over the assumption-grade constants.

The kit ships the SEARCH, not any project's constants: every number returned
by ``default_calibration()`` is an UNVERIFIED illustrative placeholder. Run
``calibration_recipe()`` for the measurement plan, replace the numbers with
your repo's, then re-run ``run_search``.

Calibration shape (one plain dict; all costs are words unless noted)::

    {
      # velocity
      "sessions_per_band": 20.0,     # sessions per reconciliation band
      "words_per_token": 0.75,       # for the tokens-saved line in why-it-won
      "initial_age_bands": 12,       # today's stock spread uniformly this deep
      # living-file stocks and boot route
      "live_files": 100.0,           # living/working docs (non-terminal)
      "live_words": 150000.0,
      "boot_fixed_words": 6000.0,    # always-read orientation route
      "journal_words": 4000.0,       # cappable process-memory journal
      "journal_caps": [1000000, 2000],   # grid toggle: uncapped vs capped
      "ledger_base_words": 1500.0,   # living ledger lean head
      "ledger_tail_per_band": 300.0, # narrative accretion per band if untrimmed
      "ledger_tail_bands_initial": 6,
      "ledger_tail_compressed_bands": 2,
      "index_active_line_words": 20.0,
      "index_hist_line_words": 18.0,
      "tombstone_words": 20.0,       # one tombstone index line
      # discovery tax
      "greps_per_session": 8.0,
      "grep_hits_per_1k_files": 50.0,
      "skim_words_per_hit": 12.0,    # path skim in -l output
      "open_frac_per_hit": 0.10,     # fraction opened before badge-bail
      "open_words_per_hit": 200.0,
      "archive_pollution_w_per_mw": 25.0,  # content-grep noise per Mw archived
      "maintenance_w_per_mw": 8.0,   # sweep/link-check burden per Mw in tree
      "ls_scan_words_per_file": 5.0,
      "ls_scans_per_session": 2.0,
      # back-references into terminal content
      "backref_halflife_bands": 3.0, # demand decays with age (exponential)
      "tombstone_hop_words": 300.0,  # tombstone -> history-recovery effort
      "bare_rederive_words": 3000.0, # no pointer: re-derive / re-decide
      "bare_find_fail": 0.5,         # P(recovery fails without a tombstone)
      # staleness (assumption-grade; sweep it)
      "stale_act_base": 0.01,        # P/session of acting on stale content
      "stale_act_cost": 10000.0,
      # feasibility + search knobs
      "miss_per_band_max": 0.005,    # hard constraint on retrieval-miss risk
      "near_best_frac": 0.05,        # secondary-objective envelope
      "grid_scale": 1,               # widening knob: N multiplies each class's
                                     # candidate windows by 1..N (bigger grid)
      "sensitivity_multipliers": [1/3, 3],
      "sensitivity_keys": ["stale_act_base", "classes.sessions.backref_rate"],
      # document classes (per-class mode × window searched per declarations)
      "classes": [
        {
          "name": "sessions",
          "birth_rate": 1.0,         # new files per session
          "words_each": 700.0,
          "initial_files": 240.0,
          "cited_frac": 0.05,        # inbound-live-reference blocking fraction
          "cascade_unlock_frac": 0.0,  # share of cited_frac released when the
                                       # living tails compress (ledger cascade)
          "backref_rate": 0.05,      # back-reference demand per session
          "tombstone_lines_each": 0.0,  # index lines left per deleted doc
          "indexed": False,          # hist files add boot-index lines
          "active_pool": None,       # or {"initial": F, "lifetime_bands": B}
                                     # for classes born active, then terminal
          "modes": ["keep", "archive", "delete_tomb", "delete_bare"],
          "windows": [1, 2, 4],      # candidate windows, in bands
        },
        ...
      ],
    }

Policy shape (``policy_grid`` builds these; you can hand-craft one too)::

    {"name": str,   # optional on hand-crafted policies; derived when absent
     "classes": {<class name>: {"mode": <RETENTION_MODES member>, "window": int}},
     "ledger_compress": bool, "journal_cap": float,
     "index_hist_tombstones": bool}

Pure stdlib, deterministic per seed (``random.Random`` instances only, no
randomness at import), no I/O, never prints — the CLI wires presentation.
"""

from __future__ import annotations

import copy
import itertools
import random
from typing import Any

RETENTION_MODES: tuple[str, ...] = ("keep", "archive", "delete_tomb", "delete_bare")


def default_calibration() -> dict[str, Any]:
    """Return a neutral, illustrative calibration — every value UNVERIFIED.

    These numbers exist so the search runs out of the box and the shape is
    executable documentation; they are NOT measurements of any repo. Follow
    ``calibration_recipe()`` to measure your own corpus before trusting a
    winner. The default grid is deliberately small (a few seconds end to end);
    raise ``grid_scale`` to widen the candidate windows.
    """
    return {
        "sessions_per_band": 20.0,
        "words_per_token": 0.75,
        "initial_age_bands": 12,
        "live_files": 100.0,
        "live_words": 150000.0,
        "boot_fixed_words": 6000.0,
        "journal_words": 4000.0,
        "journal_caps": [1000000, 2000],
        "ledger_base_words": 1500.0,
        "ledger_tail_per_band": 300.0,
        "ledger_tail_bands_initial": 6,
        "ledger_tail_compressed_bands": 2,
        "index_active_line_words": 20.0,
        "index_hist_line_words": 18.0,
        "tombstone_words": 20.0,
        "greps_per_session": 8.0,
        "grep_hits_per_1k_files": 50.0,
        "skim_words_per_hit": 12.0,
        "open_frac_per_hit": 0.10,
        "open_words_per_hit": 200.0,
        "archive_pollution_w_per_mw": 25.0,
        "maintenance_w_per_mw": 8.0,
        "ls_scan_words_per_file": 5.0,
        "ls_scans_per_session": 2.0,
        "backref_halflife_bands": 3.0,
        "tombstone_hop_words": 300.0,
        "bare_rederive_words": 3000.0,
        "bare_find_fail": 0.5,
        "stale_act_base": 0.01,
        "stale_act_cost": 10000.0,
        "miss_per_band_max": 0.005,
        "near_best_frac": 0.05,
        "grid_scale": 1,
        "sensitivity_multipliers": [1 / 3, 3],
        "sensitivity_keys": [
            "stale_act_base",
            "grep_hits_per_1k_files",
            "maintenance_w_per_mw",
            "archive_pollution_w_per_mw",
            "classes.sessions.backref_rate",
            "classes.plans.backref_rate",
        ],
        "classes": [
            {
                "name": "sessions",
                "birth_rate": 1.0,
                "words_each": 700.0,
                "initial_files": 240.0,
                "cited_frac": 0.05,
                "cascade_unlock_frac": 0.0,
                "backref_rate": 0.05,
                "tombstone_lines_each": 0.0,
                "indexed": False,
                "active_pool": None,
                "modes": ["keep", "archive", "delete_tomb", "delete_bare"],
                "windows": [1, 2, 4],
            },
            {
                "name": "plans",
                "birth_rate": 0.25,
                "words_each": 2500.0,
                "initial_files": 60.0,
                "cited_frac": 0.90,
                "cascade_unlock_frac": 0.85,
                "backref_rate": 0.20,
                "tombstone_lines_each": 1.0,
                "indexed": True,
                "active_pool": {"initial": 40.0, "lifetime_bands": 4.0},
                "modes": ["keep", "archive", "delete_tomb"],
                "windows": [2, 4],
            },
            {
                "name": "notes",
                "birth_rate": 0.20,
                "words_each": 800.0,
                "initial_files": 40.0,
                "cited_frac": 0.10,
                "cascade_unlock_frac": 0.0,
                "backref_rate": 0.02,
                "tombstone_lines_each": 1.0,
                "indexed": False,
                "active_pool": None,
                "modes": ["delete_tomb"],
                "windows": [4],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Policy space
# ---------------------------------------------------------------------------


def _sim_policy_name(policy: dict[str, Any]) -> str:
    """Render the deterministic display name for one policy dict."""
    parts = [
        f"{name}={spec['mode']}@{spec['window']}b"
        for name, spec in sorted(policy["classes"].items())
    ]
    parts.append(f"ledger={'compress' if policy['ledger_compress'] else 'grow'}")
    parts.append(f"journal<={policy['journal_cap']:g}")
    parts.append(f"idx={'tomb' if policy['index_hist_tombstones'] else 'full'}")
    return " ".join(parts)


def _sim_class_candidates(
    cls_cal: dict[str, Any],
    grid_scale: int,
) -> list[tuple[str, int]]:
    """Return the (mode, window) candidates one class declaration allows.

    ``keep`` collapses to a single ``(keep, 0)`` candidate (its window is
    meaningless); ``grid_scale`` N widens each declared window by factors
    1..N, deduplicated and sorted, so hosts can search deeper without editing
    the class declarations.
    """
    windows = sorted(
        {
            int(w) * f
            for w in cls_cal["windows"]
            for f in range(1, max(grid_scale, 1) + 1)
        },
    )
    candidates: list[tuple[str, int]] = []
    for mode in cls_cal["modes"]:
        if mode == "keep":
            candidates.append(("keep", 0))
        else:
            candidates.extend((mode, w) for w in windows)
    return candidates


def policy_grid(calibration: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the candidate-policy grid from the calibration's class declarations.

    The grid is the cartesian product of every class's ``modes`` × ``windows``
    (widened by ``grid_scale``), crossed with the living-file toggles: ledger
    compression on/off and each ``journal_caps`` value. Historical index lines
    are always tombstone-compressed in generated candidates (the status-quo
    baseline inside ``run_search`` covers the full-line alternative).
    """
    grid_scale = int(calibration.get("grid_scale", 1))
    class_names = [c["name"] for c in calibration["classes"]]
    per_class = [_sim_class_candidates(c, grid_scale) for c in calibration["classes"]]
    journal_caps = calibration.get("journal_caps", [10**9])
    policies: list[dict[str, Any]] = []
    for combo in itertools.product(*per_class):
        for ledger_compress, journal_cap in itertools.product(
            (True, False),
            journal_caps,
        ):
            policy: dict[str, Any] = {
                "classes": {
                    name: {"mode": mode, "window": window}
                    for name, (mode, window) in zip(class_names, combo, strict=True)
                },
                "ledger_compress": ledger_compress,
                "journal_cap": float(journal_cap),
                "index_hist_tombstones": True,
            }
            policy["name"] = _sim_policy_name(policy)
            policies.append(policy)
    return policies


def _sim_status_quo(calibration: dict[str, Any]) -> dict[str, Any]:
    """Return the keep-everything baseline policy for this calibration."""
    policy: dict[str, Any] = {
        "classes": {
            c["name"]: {"mode": "keep", "window": 0} for c in calibration["classes"]
        },
        "ledger_compress": False,
        "journal_cap": float(10**9),
        "index_hist_tombstones": False,
    }
    policy["name"] = _sim_policy_name(policy)
    return policy


# ---------------------------------------------------------------------------
# Corpus state: per class, bucketed by age-in-bands since terminal
# ---------------------------------------------------------------------------


def _sim_initial_state(calibration: dict[str, Any]) -> dict[str, Any]:
    """Build the initial corpus state from the calibration's stocks.

    Each class's initial terminal stock is spread uniformly over
    ``initial_age_bands`` age buckets (bucket index = bands since the file
    went terminal); classes with an ``active_pool`` start with its declared
    active count.
    """
    age_bands = max(int(calibration.get("initial_age_bands", 12)), 1)
    classes: dict[str, dict[str, Any]] = {}
    for cls in calibration["classes"]:
        pool = cls.get("active_pool") or {}
        classes[cls["name"]] = {
            "buckets": [float(cls.get("initial_files", 0.0)) / age_bands] * age_bands,
            "active": float(pool.get("initial", 0.0)),
        }
    return {
        "classes": classes,
        "archived_words": 0.0,
        "tombstone_lines": 0.0,
        "ledger_tail_bands": float(calibration.get("ledger_tail_bands_initial", 0)),
    }


def _sim_age_out(buckets: list[float], window: int, keep_frac: float) -> float:
    """Prune buckets older than ``window`` in place; return files removed.

    ``keep_frac`` is the citation-locked fraction that stays in place (still
    referenced by living docs, so not yet removable).
    """
    removed = 0.0
    for i in range(len(buckets)):
        if i >= window and buckets[i] > 0:
            hold = buckets[i] * keep_frac
            removed += buckets[i] - hold
            buckets[i] = hold
    return removed


def _sim_grow(
    state: dict[str, Any],
    calibration: dict[str, Any],
    rng: random.Random,
) -> None:
    """Advance one band of corpus growth (births, completions, tail accretion).

    Births carry a small deterministic-per-seed jitter (±10%) so the seed is
    load-bearing; the draw count per band is policy-independent, which keeps
    same-seed policy comparisons exact.
    """
    n_sessions = float(calibration["sessions_per_band"])
    for cls in calibration["classes"]:
        cs = state["classes"][cls["name"]]
        births = float(cls["birth_rate"]) * n_sessions * (0.9 + 0.2 * rng.random())
        pool = cls.get("active_pool")
        if pool:
            lifetime = max(float(pool.get("lifetime_bands", 1.0)), 1.0)
            completions = cs["active"] / lifetime
            cs["active"] += births - completions
            cs["buckets"].insert(0, completions)
        else:
            cs["buckets"].insert(0, births)


def _sim_prune(
    state: dict[str, Any],
    policy: dict[str, Any],
    calibration: dict[str, Any],
) -> None:
    """Apply one band of the policy's per-class retention actions.

    Inbound-reference blocking: a class's ``cited_frac`` locks that share of
    delete-eligible files in place; when the policy compresses the living
    tails, ``cascade_unlock_frac`` of that lock is released (the deletability
    cascade — provenance decoration in living history tails is the top citer).
    Archiving is never citation-blocked: the body stays recoverable in-tree.
    """
    for cls in calibration["classes"]:
        spec = policy["classes"][cls["name"]]
        mode, window = spec["mode"], int(spec["window"])
        if mode == "keep" or window <= 0:
            continue
        block = float(cls.get("cited_frac", 0.0))
        if policy["ledger_compress"]:
            block *= 1.0 - float(cls.get("cascade_unlock_frac", 0.0))
        buckets = state["classes"][cls["name"]]["buckets"]
        if mode == "archive":
            moved = _sim_age_out(buckets, window, keep_frac=0.0)
            state["archived_words"] += moved * float(cls["words_each"])
        elif mode == "delete_tomb":
            gone = _sim_age_out(buckets, window, keep_frac=block)
            state["tombstone_lines"] += gone * float(
                cls.get("tombstone_lines_each", 1.0),
            )
        elif mode == "delete_bare":
            _sim_age_out(buckets, window, keep_frac=block)


def _sim_dispo(mode: str, window: int, halflife: float) -> tuple[float, float, float]:
    """Split back-reference demand into (in-tree, tombstone, bare) fractions.

    Demand decays exponentially with age (``halflife`` in bands); the share
    older than the prune window lands on the pruned disposition.
    """
    if mode in ("keep", "archive") or window <= 0:
        return 1.0, 0.0, 0.0
    p_old = 0.5 ** (window / max(halflife, 0.1))
    if mode == "delete_tomb":
        return 1.0 - p_old, p_old, 0.0
    return 1.0 - p_old, 0.0, p_old


def _sim_boot_cost(
    state: dict[str, Any],
    policy: dict[str, Any],
    calibration: dict[str, Any],
) -> float:
    """Return the per-session boot tax (always-read route, words)."""
    tail_bands = (
        float(calibration.get("ledger_tail_compressed_bands", 2))
        if policy["ledger_compress"]
        else state["ledger_tail_bands"]
    )
    ledger_tail = tail_bands * float(calibration["ledger_tail_per_band"])
    journal = min(float(calibration["journal_words"]), float(policy["journal_cap"]))
    per_hist = (
        float(calibration["tombstone_words"])
        if policy["index_hist_tombstones"]
        else float(calibration["index_hist_line_words"])
    )
    index_words = state["tombstone_lines"] * float(calibration["tombstone_words"])
    for cls in calibration["classes"]:
        if not cls.get("indexed", False):
            continue
        cs = state["classes"][cls["name"]]
        index_words += cs["active"] * float(calibration["index_active_line_words"])
        index_words += sum(cs["buckets"]) * per_hist
    return (
        float(calibration["boot_fixed_words"])
        + journal
        + float(calibration["ledger_base_words"])
        + ledger_tail
        + index_words
    )


def _sim_discovery_cost(
    state: dict[str, Any],
    calibration: dict[str, Any],
    term_files: float,
    term_words: float,
) -> float:
    """Return the per-session discovery tax (grep noise, scans, maintenance)."""
    live_files = float(calibration["live_files"]) + sum(
        cs["active"] for cs in state["classes"].values()
    )
    total_files = term_files + live_files
    hits_per_grep = float(calibration["grep_hits_per_1k_files"]) * total_files / 1000.0
    term_share = term_files / max(total_files, 1.0)
    per_hit = float(calibration["skim_words_per_hit"]) + float(
        calibration["open_frac_per_hit"],
    ) * float(calibration["open_words_per_hit"])
    grep_noise = (
        float(calibration["greps_per_session"]) * hits_per_grep * term_share * per_hit
    )
    ls_noise = (
        float(calibration["ls_scans_per_session"])
        * term_files
        * float(calibration["ls_scan_words_per_file"])
    )
    arch_noise = (
        float(calibration["archive_pollution_w_per_mw"]) * state["archived_words"] / 1e6
    )
    tree_words = term_words + float(calibration["live_words"]) + state["archived_words"]
    maintenance = float(calibration["maintenance_w_per_mw"]) * tree_words / 1e6
    return grep_noise + ls_noise + arch_noise + maintenance


def _sim_backref_and_miss(
    policy: dict[str, Any],
    calibration: dict[str, Any],
) -> tuple[float, float]:
    """Return (back-reference cost, retrieval-miss events), both per session.

    In-tree demand costs nothing extra (reading a present body is work, not
    waste); a tombstone costs one recovery hop; a bare deletion costs a full
    re-derivation when recovery fails and a doubled hop when it succeeds. The
    miss metric counts only failed bare recoveries — the risk the feasibility
    constraint bounds.
    """
    halflife = float(calibration["backref_halflife_bands"])
    hop = float(calibration["tombstone_hop_words"])
    fail = float(calibration["bare_find_fail"])
    rederive = float(calibration["bare_rederive_words"])
    backref = miss = 0.0
    for cls in calibration["classes"]:
        spec = policy["classes"][cls["name"]]
        _in_tree, tomb, bare = _sim_dispo(spec["mode"], int(spec["window"]), halflife)
        rate = float(cls.get("backref_rate", 0.0))
        backref += rate * tomb * hop
        backref += rate * bare * (fail * rederive + (1.0 - fail) * hop * 2.0)
        miss += rate * bare * fail
    return backref, miss


def _sim_stale_cost(
    state: dict[str, Any],
    policy: dict[str, Any],
    calibration: dict[str, Any],
    term_words: float,
    initial_term_words: float,
) -> float:
    """Return the per-session staleness cost (acting on dead content as live)."""
    tail_bands = (
        float(calibration.get("ledger_tail_compressed_bands", 2))
        if policy["ledger_compress"]
        else state["ledger_tail_bands"]
    )
    ledger_tail = tail_bands * float(calibration["ledger_tail_per_band"])
    norm_tail = max(
        float(calibration.get("ledger_tail_bands_initial", 1)),
        1.0,
    ) * float(calibration["ledger_tail_per_band"])
    scale = (term_words / (initial_term_words + 1.0)) * 0.6 + (
        ledger_tail / max(norm_tail, 1.0)
    ) * 0.4
    return (
        float(calibration["stale_act_base"])
        * scale
        * float(
            calibration["stale_act_cost"],
        )
    )


def simulate_policy(
    policy: dict[str, Any],
    calibration: dict[str, Any],
    *,
    bands: int,
    seed: int = 7,
) -> dict[str, Any]:
    """Simulate one policy over ``bands`` reconciliation bands; score it.

    Returns the per-policy result record: the four per-session cost components
    (``boot``, ``discovery``, ``backref``, ``stale``, band-averaged words per
    session), their ``total``, the ``miss_per_band`` risk metric with its
    ``feasible`` verdict (< ``miss_per_band_max``), and the horizon-end tree
    size (``end_terminal_files``, ``end_tree_kwords``). Deterministic for a
    given (policy, calibration, bands, seed).
    """
    rng = random.Random(seed)
    name = policy.get("name") or _sim_policy_name(policy)
    state = _sim_initial_state(calibration)
    initial_term_words = sum(
        float(c.get("initial_files", 0.0)) * float(c["words_each"])
        for c in calibration["classes"]
    )
    totals = {"boot": 0.0, "discovery": 0.0, "backref": 0.0, "stale": 0.0}
    miss_events = 0.0
    term_files = term_words = 0.0
    n_bands = max(int(bands), 1)
    for _ in range(n_bands):
        _sim_grow(state, calibration, rng)
        if not policy["ledger_compress"]:
            state["ledger_tail_bands"] += 1.0
        _sim_prune(state, policy, calibration)
        term_files = sum(sum(cs["buckets"]) for cs in state["classes"].values())
        term_words = sum(
            sum(state["classes"][c["name"]]["buckets"]) * float(c["words_each"])
            for c in calibration["classes"]
        )
        totals["boot"] += _sim_boot_cost(state, policy, calibration)
        totals["discovery"] += _sim_discovery_cost(
            state,
            calibration,
            term_files,
            term_words,
        )
        backref, miss = _sim_backref_and_miss(policy, calibration)
        totals["backref"] += backref
        miss_events += miss
        totals["stale"] += _sim_stale_cost(
            state,
            policy,
            calibration,
            term_words,
            initial_term_words,
        )
    per = {k: v / n_bands for k, v in totals.items()}
    per_total = sum(per.values())
    miss_per_band = miss_events / n_bands
    return {
        "policy": policy,
        "name": name,
        **per,
        "total": per_total,
        "miss_per_band": miss_per_band,
        "feasible": miss_per_band < float(calibration.get("miss_per_band_max", 0.005)),
        "end_terminal_files": term_files,
        "end_tree_kwords": (
            term_words + float(calibration["live_words"]) + state["archived_words"]
        )
        / 1000.0,
    }


# ---------------------------------------------------------------------------
# Search, sensitivity, why-it-won
# ---------------------------------------------------------------------------


def _sim_scaled(calibration: dict[str, Any], key: str, mult: float) -> dict[str, Any]:
    """Return a deep copy of the calibration with one constant multiplied.

    ``key`` is either a top-level constant name or a class field addressed as
    ``classes.<class name>.<field>``. Unknown class addresses scale nothing
    (the copy is returned unchanged) so pruned class lists stay sweepable.
    """
    scaled = copy.deepcopy(calibration)
    if key.startswith("classes."):
        _, cls_name, field = key.split(".", 2)
        for cls in scaled["classes"]:
            if cls["name"] == cls_name and field in cls:
                cls[field] = float(cls[field]) * mult
        return scaled
    scaled[key] = float(scaled[key]) * mult
    return scaled


def _sim_sensitivity(
    policy: dict[str, Any],
    calibration: dict[str, Any],
    *,
    bands: int,
    seed: int,
    base_total: float,
) -> list[dict[str, Any]]:
    """Re-score the winner under each sweep multiplier on each swept constant."""
    entries: list[dict[str, Any]] = []
    multipliers = calibration.get("sensitivity_multipliers", [1 / 3, 3])
    for key in calibration.get("sensitivity_keys", []):
        for mult in multipliers:
            scaled = _sim_scaled(calibration, key, float(mult))
            total = simulate_policy(policy, scaled, bands=bands, seed=seed)["total"]
            entries.append(
                {
                    "key": key,
                    "multiplier": float(mult),
                    "total": total,
                    "delta": total - base_total,
                },
            )
    return entries


def _sim_why_it_won(
    winner: dict[str, Any],
    baseline: dict[str, Any],
    calibration: dict[str, Any],
    *,
    feasible_count: int,
    grid_size: int,
    near_count: int,
) -> str:
    """Render the WHY-IT-WON record for one search outcome."""
    words_per_token = max(float(calibration.get("words_per_token", 0.75)), 0.01)
    base_total = baseline["total"]
    saved = base_total - winner["total"]
    pct = 100.0 * saved / base_total if base_total > 0 else 0.0
    near_frac = float(calibration.get("near_best_frac", 0.05))
    lines = [
        f"winner: {winner['name']}",
        (
            f"vs keep-everything baseline: {base_total:,.0f} -> "
            f"{winner['total']:,.0f} words/session ({pct:.0f}% lower), "
            f"~{saved / words_per_token / 1000:.1f}k tokens/session saved"
        ),
        (
            f"tree size at horizon: {baseline['end_tree_kwords']:,.0f}kw -> "
            f"{winner['end_tree_kwords']:,.0f}kw"
        ),
        (
            f"retrieval-miss events/band: {winner['miss_per_band']:.4f} "
            f"(constraint < {float(calibration.get('miss_per_band_max', 0.005)):g})"
        ),
        (
            f"feasible policies: {feasible_count} of {grid_size}; secondary "
            f"objective picked the smallest tree among {near_count} within "
            f"{near_frac:.0%} of the best primary score"
        ),
    ]
    if not winner["feasible"]:
        lines.append(
            "WARNING: no candidate met the miss constraint — winner is the "
            "lowest-cost INFEASIBLE policy; loosen windows or drop delete_bare",
        )
    return "\n".join(lines)


def run_search(
    calibration: dict[str, Any],
    *,
    bands: int = 24,
    seed: int = 7,
) -> dict[str, Any]:
    """Run the full policy-grid search and return the winner with its record.

    Primary objective: lowest expected words/session among FEASIBLE policies
    (``miss_per_band`` under the calibration's bound). Secondary objective
    (lean by construction): among feasible policies within ``near_best_frac``
    of the best primary score, the smallest tree at horizon wins. Returns
    ``{"winner", "why_it_won", "feasible_count", "sensitivity"}`` — the winner
    is the full ``simulate_policy`` record (policy dict under ``"winner"["policy"]``).
    If nothing is feasible the search degrades gracefully: the lowest-cost
    infeasible policy wins and ``why_it_won`` carries a loud warning.
    """
    grid = policy_grid(calibration)
    results = [
        simulate_policy(policy, calibration, bands=bands, seed=seed) for policy in grid
    ]
    feasible = [r for r in results if r["feasible"]]
    pool = feasible or sorted(results, key=lambda r: r["total"])
    best_total = min(r["total"] for r in pool)
    near_frac = float(calibration.get("near_best_frac", 0.05))
    near = [r for r in pool if r["total"] <= best_total * (1.0 + near_frac)]
    near.sort(key=lambda r: (r["end_tree_kwords"], r["total"], r["name"]))
    winner = near[0]
    baseline = simulate_policy(
        _sim_status_quo(calibration),
        calibration,
        bands=bands,
        seed=seed,
    )
    sensitivity = _sim_sensitivity(
        winner["policy"],
        calibration,
        bands=bands,
        seed=seed,
        base_total=winner["total"],
    )
    why = _sim_why_it_won(
        winner,
        baseline,
        calibration,
        feasible_count=len(feasible),
        grid_size=len(grid),
        near_count=len(near),
    )
    return {
        "winner": winner,
        "why_it_won": why,
        "feasible_count": len(feasible),
        "sensitivity": sensitivity,
    }


def calibration_recipe() -> str:
    """Return the re-measurement recipe for grounding a calibration in a repo.

    The kit ships the search, not our constants: every default is a
    placeholder. Measure the five profiles below against YOUR corpus, write
    the numbers into a copy of ``default_calibration()``, then re-run
    ``run_search`` — and re-measure whenever the corpus shape shifts.
    """
    return (
        "Calibration recipe — measure your repo, then edit default_calibration()\n"
        "\n"
        "Every default constant is an UNVERIFIED placeholder. Ground each group\n"
        "in measurements before trusting a winner:\n"
        "\n"
        "```sh\n"
        "# 1) Badge census — per-class stocks (initial_files, words_each):\n"
        "#    count and word-count files per lifecycle class (terminal vs live).\n"
        "grep -rlE '\\*\\*Status:\\*\\* .(historical|archived)' docs/ | wc -l\n"
        "grep -rlE '\\*\\*Status:\\*\\* .(historical|archived)' docs/ | xargs wc -w\n"
        "ls .sessions/*.md | wc -l && wc -w .sessions/*.md | tail -1\n"
        "\n"
        "# 2) Grep-noise profile — discovery constants (grep_hits_per_1k_files,\n"
        "#    share of hits landing in terminal docs): run ~20 representative\n"
        "#    working-term greps and count hit locations.\n"
        'for t in <your 20 working terms>; do grep -rl "$t" docs/ ; done |\n'
        "  sort | uniq -c | sort -rn | head\n"
        "\n"
        "# 3) Velocity — sessions_per_band and per-class birth_rate:\n"
        "#    files born per session over recent history.\n"
        "git log --since='30 days ago' --oneline --merges | wc -l\n"
        "git log --since='30 days ago' --name-only --diff-filter=A -- docs/ |\n"
        "  grep '\\.md$' | sort | uniq | wc -l\n"
        "\n"
        "# 4) Back-reference greps — backref_rate and cited_frac per class:\n"
        "#    how often terminal docs are cited from OUTSIDE their own dir.\n"
        "for f in .sessions/*.md; do\n"
        '  grep -rl "$(basename "$f")" docs/ --include=\'*.md\' |\n'
        "    grep -v '^.sessions/'; done | sort -u | wc -l\n"
        "\n"
        "# 5) Boot word count — boot_fixed_words / journal_words /\n"
        "#    ledger_base_words: word-count the always-read orientation route.\n"
        "wc -w CLAUDE.md .session-journal.md docs/current-state.md\n"
        "```\n"
        "\n"
        "Sweep discipline: constants you could not measure (staleness, archive\n"
        "pollution) stay assumption-grade — list them in sensitivity_keys so\n"
        "every search re-checks the winner under x1/3 and x3. Adopt a winner\n"
        "only when its rank holds across the whole sweep.\n"
    )
