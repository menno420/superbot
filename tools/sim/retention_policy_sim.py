#!/usr/bin/env python3
"""
Retention-policy simulator for the AI-memory/docs corpus (sim-driven design,
per docs/planning/simulation-driven-design-2026-07-02.md, applied to the
memory system itself).

WHAT IT MODELS
  The docs corpus growing over sessions (session logs, plans, ideas, recon
  records, ledger tails), agents reading it (boot route, grep discovery,
  index/ls scans, back-references into terminal content, stale encounters),
  and a candidate retention policy acting on it (per-class mode: keep /
  archive / delete+tombstone / delete bare, with an age window in
  reconciliation bands, plus living-file caps). It searches the policy grid
  and scores each candidate on expected agent context cost (words/session)
  plus retrieval-miss risk, under hard safety constraints (live/binding docs
  untouchable; no deletion while inbound live references exist).

CALIBRATION — measured against THIS repo on 2026-07-02 (sources in comments
on each constant; re-measure with --calibrate). The four sim-driven-design
guardrails apply: real combinatorial space; data-grounded objective (the
constants below are measurements, and the assumption-grade ones are swept in
the sensitivity pass); the simulator is kept + re-runnable; deterministic
seed + a "why it won" record in the output.

KEY MEASURED FACTS DRIVING THE MODEL (2026-07-02)
  - corpus: 1,489 tracked .md files, ~1.67M words; 876 files / 924k words
    are TERMINAL (historical/audit/session-log/archive) — 55% of all words.
  - grep noise: over 20 representative working-term greps, 69.6% of file
    hits land in terminal docs.
  - .sessions/: 736 files / ~541k words, ~10-60 new logs/day (median ~25);
    no retention deletion has ever occurred (the one deliberate log deletion
    in history was a wrong-claim removal, owner-directed, PR #1278).
  - back-references: 5.2% of session logs are ever cited from outside
    .sessions/; 3.7% cite a log >3 sessions older. Historical plans: 96%
    cited by live docs — but the top citers are the history tails of
    roadmap.md / router / current-state.md (provenance decoration), so
    deletability CASCADES from compressing those tails first.

Run:  python3.10 tools/sim/retention_policy_sim.py            # full search
      python3.10 tools/sim/retention_policy_sim.py --quick    # smaller grid
      python3.10 tools/sim/retention_policy_sim.py --calibrate  # re-measure
"""

import argparse
import itertools
import random

WORDS_PER_TOKEN = 0.75  # ~1.33 tokens/word; report words, note tokens

# ---------------------------------------------------------------------------
# Calibration (pinned 2026-07-02; sources inline). Re-measure via --calibrate.
# ---------------------------------------------------------------------------

CAL = {
    # --- velocity (git log measurements, 2026-07-02) ---
    "sessions_per_band": 30,  # ~25 session logs/day, band(30 PR-numbers) ~ 1.4 days
    "band_days": 1.4,  # merged-PR velocity ~21/day median (git log --merges)
    # --- per-class birth rates per session (file counts / ~732 sessions) ---
    "rate_session_log": 1.0,  # every session writes one (.sessions/ discipline)
    "rate_plan": 0.26,  # 190 planning files / 732 sessions
    "rate_idea": 0.24,  # 172 idea files / 732 sessions (Q-0089 file-worthy subset)
    "rate_other_terminal": 0.08,  # audits/pass-records/etc.
    # --- sizes (avg words, measured) ---
    "w_session_log": 735,  # 541,014 words / 736 files (mean 734, median 724)
    "w_plan": 2700,  # hist 199k/71=2800, active 146k/57=2566
    "w_idea": 830,  # 121k/145
    "w_other_terminal": 2000,
    "w_tombstone": 20,  # one index line
    # --- plan lifecycle ---
    "plan_active_frac": 0.45,  # 57 active vs 71 historical today
    "plan_lifetime_bands": 4,  # typical active->historical in a few bands
    # --- boot route (always-read living files, words; measured 2026-07-02;
    #     ~25.6k full any-task route per orientation-cost plan) ---
    "boot_fixed": 14000,  # CLAUDE.md 5,169 + collab-model + AGENT_ORIENTATION + nav docs
    "boot_journal": 8349,  # .session-journal.md (policy-cappable)
    "boot_ledger_base": 3000,  # current-state.md lean head (callout+sectors)
    "boot_ledger_tail_per_band": 700,  # historical narrative accretion/band if untrimmed
    "boot_index_per_active_plan": 22,  # plan-index active line
    "boot_index_per_hist_line": 18,  # plan-index historical/tombstone line
    # --- discovery (measured grep profile; skim weights are conservative) ---
    "greps_per_session": 12,  # typical working greps over *.md surfaces
    "grep_hits_per_1k_files": 60,  # broad terms measured ~150/1k; working greps narrower
    "skim_words_per_terminal_hit": 12,  # path skim in -l output; most never opened
    "open_frac_terminal_hit": 0.10,  # fraction actually opened before badge-bail
    "open_words_terminal_hit": 200,
    "archive_pollution_w_per_Mw": 25,  # content-mode grep noise per Mw archived in-tree
    "maintenance_w_per_Mw": 8,  # sweep/link-check/fix-on-sight burden per Mw in tree
    "ls_scan_words_per_file": 5,  # ls/Glob name-skim cost over .sessions/ etc.
    "ls_scans_per_session": 2,
    # --- back-references into terminal content (measured rates) ---
    "backref_sess_per_session": 0.05,  # 38 ext citations / 732 sessions
    "backref_plan_per_session": 0.25,  # hist plans cited by later logs 58/71 over life
    "backref_age_halflife_bands": 3,  # citations cluster near completion (dates observed)
    "read_words_on_backref": 500,  # what you'd read if the body is present
    "tombstone_hop_words": 300,  # tombstone -> git show equivalent effort
    "bare_delete_rederive_words": 3000,  # no pointer: re-derive / re-decide
    "bare_delete_find_fail": 0.5,  # P(agent fails to recover w/o tombstone)
    # --- staleness (assumption-grade; swept in sensitivity) ---
    "stale_act_base": 0.010,  # P/session of acting on stale content at today's mix
    "stale_act_cost": 25000,  # ~half a wasted session (#804-class incident)
    # --- reference topology (measured) ---
    "plan_cited_by_live_frac": 0.96,  # 68/71 hist plans cited by live docs...
    "plan_cite_via_ledger_frac": 0.85,  # ...but ~85% only via ledger/roadmap/router tails
    "sess_cited_frac": 0.052,  # 38/735
}

BASELINE_TERMINAL_FILES = 876  # today's terminal stock (git ls-files + badge scan)
BASELINE_TERMINAL_WORDS = 924000
BASELINE_LIVE_FILES = 460  # live + unbadged working docs
BASELINE_LIVE_WORDS = 748000


# ---------------------------------------------------------------------------
# Policy space
# ---------------------------------------------------------------------------

MODES = ("keep", "archive", "delete_tomb", "delete_bare")


class Policy:
    __slots__ = (
        "sess_mode",
        "sess_window",
        "plan_mode",
        "plan_window",
        "idea_mode",
        "idea_window",
        "ledger_compress",
        "journal_cap",
        "index_hist_tombstones",
    )

    def __init__(
        self,
        sess_mode,
        sess_window,
        plan_mode,
        plan_window,
        idea_mode,
        idea_window,
        ledger_compress,
        journal_cap,
        index_hist_tombstones,
    ):
        self.sess_mode = sess_mode
        self.sess_window = sess_window  # bands a session log stays in-tree
        self.plan_mode = plan_mode
        self.plan_window = plan_window  # bands after historical-rebadge
        self.idea_mode = idea_mode
        self.idea_window = idea_window
        self.ledger_compress = ledger_compress  # compress living-doc history tails
        self.journal_cap = journal_cap  # words
        self.index_hist_tombstones = (
            index_hist_tombstones  # hist index lines -> 1-liners
        )

    def name(self):
        return (
            f"sess={self.sess_mode}@{self.sess_window}b "
            f"plan={self.plan_mode}@{self.plan_window}b "
            f"idea={self.idea_mode}@{self.idea_window}b "
            f"ledger={'compress' if self.ledger_compress else 'grow'} "
            f"journal<={self.journal_cap} "
            f"idx={'tomb' if self.index_hist_tombstones else 'full'}"
        )


STATUS_QUO = Policy("keep", 0, "keep", 0, "keep", 0, False, 99999, False)
ARCHIVE_ALL = Policy("archive", 2, "archive", 2, "archive", 2, True, 9000, True)
DELETE_HARD = Policy(
    "delete_bare",
    1,
    "delete_bare",
    1,
    "delete_bare",
    1,
    True,
    9000,
    True,
)


# ---------------------------------------------------------------------------
# Corpus state: aggregate per class, bucketed by age-in-bands since terminal.
# ---------------------------------------------------------------------------


class State:
    def __init__(self, cal):
        # age buckets: index = bands since terminal; start from today's stock,
        # approximated as uniformly aged over ~18 bands of history.
        hist_bands = 18
        self.sess = [736 / hist_bands] * hist_bands  # files per bucket
        self.plans_hist = [71 / hist_bands] * hist_bands
        self.ideas_term = [27 / hist_bands] * hist_bands
        self.other_term = [40 / hist_bands] * hist_bands
        self.plans_active = 57.0
        self.ideas_active = 145.0
        self.archived_words = 0.0  # in-tree archive files (out of route)
        self.tombstones = 0.0
        self.ledger_tail_bands = 14  # untrimmed narrative accretion to date
        self.deleted_tomb = [
            0.0,
        ] * 4  # recent deletions by class-ish (for backref risk)
        self.deleted_bare = [0.0] * 4

    def terminal_files(self):
        return (
            sum(self.sess)
            + sum(self.plans_hist)
            + sum(self.ideas_term)
            + sum(self.other_term)
        )

    def terminal_words(self, c):
        return (
            sum(self.sess) * c["w_session_log"]
            + sum(self.plans_hist) * c["w_plan"]
            + sum(self.ideas_term) * c["w_idea"]
            + sum(self.other_term) * c["w_other_terminal"]
        )


def age_out(buckets, window, keep_frac=0.0):
    """Remove buckets older than window; return (files_removed, files_kept_by_refs)."""
    removed = kept = 0.0
    for i in range(len(buckets)):
        if i >= window and buckets[i] > 0:
            hold = buckets[i] * keep_frac  # still referenced -> can't delete yet
            removed += buckets[i] - hold
            kept += hold
            buckets[i] = hold
    return removed, kept


def step_band(state, pol, c, rng, costs):
    """Advance one reconciliation band; apply policy; accumulate per-session costs."""
    n_sessions = c["sessions_per_band"]

    # --- growth ---
    state.sess.insert(0, c["rate_session_log"] * n_sessions)
    completions = state.plans_active / max(c["plan_lifetime_bands"], 1)
    state.plans_active += c["rate_plan"] * n_sessions - completions
    state.plans_hist.insert(0, completions)
    idea_term_rate = (
        0.2  # fraction of active ideas resolving per band (groomed/implemented)
    )
    resolved = state.ideas_active * idea_term_rate * 0.15
    state.ideas_active += c["rate_idea"] * n_sessions - resolved
    state.ideas_term.insert(0, resolved)
    state.other_term.insert(0, c["rate_other_terminal"] * n_sessions)
    if not pol.ledger_compress:
        state.ledger_tail_bands += 1

    # --- policy application (the prune, at band cadence) ---
    def apply(buckets, mode, window, w_each, ref_block_frac, del_idx, tomb_lines):
        # tomb_lines: index lines left per deleted doc (0 = one shared banner —
        # right for session logs, where 95% are never cited; 1 = per-doc line,
        # right for plans, which live docs cite by name)
        if mode == "keep" or window <= 0:
            return
        if mode == "archive":
            moved, _ = age_out(buckets, window, keep_frac=0.0)
            state.archived_words += moved * w_each
        elif mode == "delete_tomb":
            gone, _ = age_out(buckets, window, keep_frac=ref_block_frac)
            state.tombstones += gone * tomb_lines
            state.deleted_tomb[del_idx] += gone
        elif mode == "delete_bare":
            gone, _ = age_out(buckets, window, keep_frac=ref_block_frac)
            state.deleted_bare[del_idx] += gone

    # inbound-ref blocking: without ledger compression, 96% of hist plans are
    # citation-locked; with it, only the genuinely load-bearing ~15% remain.
    plan_block = c["plan_cited_by_live_frac"]
    if pol.ledger_compress:
        plan_block *= 1 - c["plan_cite_via_ledger_frac"]
    sess_block = c["sess_cited_frac"]

    apply(
        state.sess,
        pol.sess_mode,
        pol.sess_window,
        c["w_session_log"],
        sess_block,
        0,
        0,
    )
    apply(
        state.plans_hist,
        pol.plan_mode,
        pol.plan_window,
        c["w_plan"],
        plan_block,
        1,
        1,
    )
    apply(state.ideas_term, pol.idea_mode, pol.idea_window, c["w_idea"], 0.10, 2, 1)
    apply(
        state.other_term,
        pol.plan_mode,
        pol.plan_window,
        c["w_other_terminal"],
        0.10,
        3,
        1,
    )

    # --- per-session costs this band ---
    term_files = state.terminal_files()
    term_words = state.terminal_words(c)
    live_files = BASELINE_LIVE_FILES + state.plans_active + state.ideas_active - 202

    # 1) boot tax
    ledger_tail = (2 if pol.ledger_compress else state.ledger_tail_bands) * c[
        "boot_ledger_tail_per_band"
    ]
    journal = min(c["boot_journal"], pol.journal_cap)
    hist_lines = sum(state.plans_hist) + state.tombstones
    index_words = state.plans_active * c["boot_index_per_active_plan"] + hist_lines * (
        c["w_tombstone"] if pol.index_hist_tombstones else c["boot_index_per_hist_line"]
    )
    boot = c["boot_fixed"] + journal + c["boot_ledger_base"] + ledger_tail + index_words

    # 2) discovery tax: grep noise + ls scans scale with in-tree terminal stock;
    #    archives are off the -l surface (few files) but pollute content-mode
    #    greps in proportion to their mass; everything in-tree carries a small
    #    sweep/maintenance burden
    total_files = term_files + live_files
    hits_per_grep = c["grep_hits_per_1k_files"] * total_files / 1000.0
    term_share = term_files / max(total_files, 1)
    per_hit = (
        c["skim_words_per_terminal_hit"]
        + c["open_frac_terminal_hit"] * c["open_words_terminal_hit"]
    )
    grep_noise = c["greps_per_session"] * hits_per_grep * term_share * per_hit
    ls_noise = c["ls_scans_per_session"] * term_files * c["ls_scan_words_per_file"]
    arch_noise = c["archive_pollution_w_per_Mw"] * state.archived_words / 1e6
    tree_words_now = term_words + BASELINE_LIVE_WORDS + state.archived_words
    maint = c["maintenance_w_per_Mw"] * tree_words_now / 1e6

    # 3) back-reference cost by disposition
    def backref_cost(rate, in_tree_frac, tomb_frac, bare_frac):
        age_decay = 1.0  # rates already lifetime-averaged
        base = rate * age_decay
        cost_in = base * in_tree_frac * 0  # body present: reading it is work, not waste
        cost_tomb = base * tomb_frac * c["tombstone_hop_words"]
        cost_bare = (
            base
            * bare_frac
            * (
                c["bare_delete_find_fail"] * c["bare_delete_rederive_words"]
                + (1 - c["bare_delete_find_fail"]) * c["tombstone_hop_words"] * 2
            )
        )
        return cost_in + cost_tomb + cost_bare

    def dispo(buckets, mode, window, halflife):
        """Fraction of backref demand landing in-tree vs tombstone vs bare, given
        demand decays with age (halflife in bands) and prunes occur past window.
        """
        if mode in ("keep", "archive") or window <= 0:
            return 1.0, 0.0, 0.0
        # P(needed doc is older than window) under exponential decay
        p_old = 0.5 ** (window / max(halflife, 0.1))
        if mode == "delete_tomb":
            return 1 - p_old, p_old, 0.0
        return 1 - p_old, 0.0, p_old

    hl = c["backref_age_halflife_bands"]
    s_in, s_t, s_b = dispo(state.sess, pol.sess_mode, pol.sess_window, hl)
    p_in, p_t, p_b = dispo(state.plans_hist, pol.plan_mode, pol.plan_window, hl)
    backref = backref_cost(
        c["backref_sess_per_session"],
        s_in,
        s_t,
        s_b,
    ) + backref_cost(c["backref_plan_per_session"], p_in, p_t, p_b)

    # 4) staleness: acting on stale content scales with terminal share of the
    #    working tree + the un-compressed ledger tail (both are where agents
    #    read something believing it live)
    stale_scale = (term_words / (BASELINE_TERMINAL_WORDS + 1)) * 0.6 + (
        ledger_tail / (14 * c["boot_ledger_tail_per_band"])
    ) * 0.4
    stale = c["stale_act_base"] * stale_scale * c["stale_act_cost"]

    # retrieval-miss events (risk metric, separate from cost): bare deletions
    # that later get demanded and fail
    miss = (
        c["backref_sess_per_session"] * s_b + c["backref_plan_per_session"] * p_b
    ) * c["bare_delete_find_fail"]

    costs["boot"] += boot
    costs["discovery"] += grep_noise + ls_noise + arch_noise + maint
    costs["backref"] += backref
    costs["stale"] += stale
    costs["miss_events"] += miss
    costs["bands"] += 1
    costs["end_terminal_files"] = term_files
    costs["end_terminal_words"] = term_words
    costs["end_tree_words"] = term_words + BASELINE_LIVE_WORDS + state.archived_words


def simulate(pol, c, horizon_bands=20, seed=1234):
    rng = random.Random(seed)
    state = State(c)
    costs = {
        "boot": 0.0,
        "discovery": 0.0,
        "backref": 0.0,
        "stale": 0.0,
        "miss_events": 0.0,
        "bands": 0,
        "end_terminal_files": 0.0,
        "end_terminal_words": 0.0,
        "end_tree_words": 0.0,
    }
    for _ in range(horizon_bands):
        step_band(state, pol, c, rng, costs)
    b = costs["bands"]
    per = {
        k: v / b
        for k, v in costs.items()
        if k in ("boot", "discovery", "backref", "stale")
    }
    per["total"] = sum(per.values())
    per["miss_per_band"] = costs["miss_events"] / b
    per["end_terminal_files"] = costs["end_terminal_files"]
    per["end_tree_kwords"] = costs["end_tree_words"] / 1000.0
    return per


def policy_grid(quick=False):
    windows_s = (1, 2, 4) if quick else (1, 2, 3, 4, 8)
    windows_p = (2, 4) if quick else (2, 4, 8)
    for sm, sw in itertools.product(
        ("keep", "archive", "delete_tomb", "delete_bare"),
        windows_s,
    ):
        for pm, pw in itertools.product(("keep", "archive", "delete_tomb"), windows_p):
            for lc in (True, False):
                for jc in (9000, 4000):
                    yield Policy(sm, sw, pm, pw, "delete_tomb", 4, lc, jc, True)


def sensitivity(pol, c):
    """Re-score under x1/3 and x3 on the assumption-grade constants."""
    out = []
    for key in (
        "backref_sess_per_session",
        "backref_plan_per_session",
        "stale_act_base",
        "rate_session_log",
        "archive_pollution_w_per_Mw",
        "grep_hits_per_1k_files",
        "maintenance_w_per_Mw",
    ):
        for mult in (1 / 3, 3):
            c2 = dict(c)
            c2[key] = c[key] * mult
            out.append((key, mult, simulate(pol, c2)["total"]))
    return out


def fmt(per):
    return (
        f"total {per['total']:7,.0f} w/s  (boot {per['boot']:6,.0f} · "
        f"disc {per['discovery']:6,.0f} · backref {per['backref']:4,.0f} · "
        f"stale {per['stale']:4,.0f})  miss/band {per['miss_per_band']:.3f}  "
        f"tree@end {per['end_tree_kwords']:5,.0f}kw"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument(
        "--calibrate",
        action="store_true",
        help="print re-measurement commands (does not run them)",
    )
    args = ap.parse_args()
    if args.calibrate:
        print(__doc__)
        print(
            "Re-measure: badge scan + grep profile + git log rates — see the "
            "measurement block in docs/planning/memory-retention-and-context-"
            "economy-plan-2026-07-02.md §calibration.",
        )
        return

    c = CAL
    print("=== Baselines ===")
    for label, pol in (
        ("status_quo (keep everything)", STATUS_QUO),
        ("archive_all @2 bands", ARCHIVE_ALL),
        ("delete_hard (bare @1 band)", DELETE_HARD),
    ):
        print(f"  {label:32s} {fmt(simulate(pol, c))}")

    print("\n=== Policy search ===")
    scored = []
    for pol in policy_grid(args.quick):
        per = simulate(pol, c)
        # hard constraint proxy: retrieval-miss risk must stay ~0
        feasible = per["miss_per_band"] < 0.005
        scored.append((per["total"], feasible, pol, per))
    scored.sort(key=lambda t: (not t[1], t[0]))

    # secondary objective ("lean by construction"): among feasible policies
    # within 5% of the best primary score, prefer the smallest tree at horizon
    best_total = scored[0][0]
    near = [t for t in scored if t[1] and t[0] <= best_total * 1.05]
    near.sort(key=lambda t: t[3]["end_tree_kwords"])

    print("top 8 feasible policies (lowest expected words/session):")
    for _total, _feas, pol, per in scored[:8]:
        print(f"  {fmt(per)}\n      {pol.name()}")

    print(f"\nwithin 5% of best primary ({len(near)} policies), smallest tree wins:")
    for _total, _feas, pol, per in near[:4]:
        print(
            f"  tree {per['end_tree_kwords']:5,.0f}kw  {per['total']:7,.0f} w/s  {pol.name()}",
        )

    best = near[0] if near else scored[0]
    print("\n=== WHY IT WON ===")
    sq = simulate(STATUS_QUO, c)
    per = best[3]
    print(f"  winner: {best[2].name()}")
    print(
        f"  vs status quo: {sq['total']:,.0f} -> {per['total']:,.0f} words/session "
        f"({100 * (1 - per['total'] / sq['total']):.0f}% lower), "
        f"~{(sq['total'] - per['total']) / WORDS_PER_TOKEN / 1000:.1f}k tokens/session saved",
    )
    print(
        f"  tree size at horizon: {sq['end_tree_kwords']:,.0f}kw -> {per['end_tree_kwords']:,.0f}kw",
    )
    print(
        f"  retrieval-miss events/band: {per['miss_per_band']:.4f} (constraint <0.005)",
    )

    print(
        "\n=== Sensitivity (winner total under x1/3 and x3 on assumption-grade constants) ===",
    )
    base_total = per["total"]
    for key, mult, total in sensitivity(best[2], c):
        print(
            f"  {key:28s} x{mult:<4.2g} -> {total:7,.0f} w/s ({total - base_total:+,.0f})",
        )
    print(
        "\n  (stable winner = rank holds under all sweeps; verify before adopting numbers)",
    )


if __name__ == "__main__":
    main()
