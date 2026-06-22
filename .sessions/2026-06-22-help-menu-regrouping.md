# 2026-06-22 — Help-menu regrouping (simulation + implementation)

> **Status:** `in-progress`

Owner-directed: the help menu has grown crowded; regroup it into a few clear,
logical sections so every feature is reachable in ≤3 button clicks. The owner
asked for a **simulation** to find the most-efficient grouping first.

## What I'm about to do
- Build a stdlib grouping simulation (`tools/sim/help_menu_grouping_sim.py`) that
  loads the live hub + subsystem registries, models the Help click graph
  (index → hub → child, with the 12-item dropdown pagination that breaks the
  3-click guarantee), scores candidate groupings on reachability + cohesion +
  section count, and recommends the most efficient logical sectioning.
- Implement the recommended grouping: home the orphan subsystems (`fishing`,
  `creature`, `welcome`, `counters`, `security`, `channel`, `ai`, `ux_lab`) and
  regroup hubs, keeping registry drift checks + tier filters green.
