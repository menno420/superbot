# 2026-06-14 · Night executor — P0-4 PR 1: channel clone + overwrite convergence

**Trigger:** scheduled `continue` issue #819 (no prior handoff) → STEP 1.C, next big
plan step. Decade queue (band-#800) slot 3 = **P0-4 server-mgmt channel-ownership
convergence (Q-0100)**; P0-3 had just shipped in #817.

## What shipped (the sub-step)

Q-0100 splits the four mixed channel-mutation families two ways: **clone + overwrite →
`ChannelLifecycleService`**, **creation/category → `ResourceProvisioningPipeline`**. This
PR did the first half (the cleaner seam — the lifecycle service already exists and its
contract docstring already named "overwrite" as an owned op).

- **`ChannelLifecycleService`** gained `set_overwrite` (REVERSIBLE) + `clone`
  (COMPENSATABLE) operations: request fields `overwrite_target_id/type/overwrites` +
  `clone_name`; target resolution via `guild_resources.resolve_role/resolve_member`
  (NOT raw `guild.get_*` — that invariant bit me first run); a `LookupError` → failed-step
  path for a vanished overwrite target; `_summary` branches for the audit line.
- **Routed every direct call site** off `.set_permissions()`/`.clone()`:
  `set_access`, `lock_channel`, `unlock_channel`, `modify_permissions`,
  `create_channel_with_role`'s post-create overwrite (creation itself stays direct →
  PR 2), and `views/channels/restrict_panel.py` (one batched apply, typed steps mapped
  back to its succeeded/forbidden/failed buckets). `visibility_panel.py` was a false
  positive in the map — it already routes through `governance_service`.
- **Invariant extended:** `test_no_direct_channel_mutations.py` `_FORBIDDEN` now pins
  `.set_permissions` + `.clone` (was just `.delete`/`.edit`).
- **Cog-size side-quest:** the convergence pushed `channel_cog.py` 739 → 841 LOC (over the
  800 hard ceiling). Per the cog-size test's own remedy (F-3: extract view code), moved the
  `!list` paginator (`_ChannelListPaginatorView` + 3 helpers, ~180 LOC) to a new
  `views/channels/list_panel.py`, re-exported for the importing test. Cog → **640 LOC**
  (now below even the 500 warn-tier). Net: a layering smell removed, not just dodged.

**Verification:** `check_quality.py --full` green (9446 passed); arch 0 errors; new
lifecycle/invariant/restrict tests added.

## Handoff

Opened a `continue` issue for **P0-4 PR 2** — converge creation/category under
`ResourceProvisioningPipeline` and pin `create_*` in the invariant. The wrinkle to design:
ad-hoc operator `!create`/`!evt`/`!bulkcreate` channels have **no declared binding**, so
they don't fit the catalogue-driven pipeline as-is — decide whether to add an ad-hoc
provisioning mode or a dedicated audited create op on the lifecycle service.

## 💡 Session idea (Q-0089)

`scripts/check_layer_residence.py` — a guard that flags `discord.ui.View` subclasses
**defined in `cogs/`** (currently invisible to the baseview ratchet, which only scans
`views/`). The `!list` paginator sat mislayered in `channel_cog.py` for ages precisely
because no check looked there; the cog-size ceiling caught it only by accident this
session. Captured to `docs/ideas/`.

## ⟲ Previous-session review (Q-0102)

Previous run (2026-06-13 substrate-kit 1b checkers / band-#800 reconciliation) did the
masking-range ledger fix well — a genuine durable guard improvement. One miss it could have
flagged: the production-readiness **maps** (e.g. server-mgmt) listed `visibility_panel.py`
as a direct-overwrite path, but it actually routes through `governance_service` — a stale
audit row that would have sent an implementer (me) to convert already-converged code.
**System improvement:** readiness-map rows assert source facts that drift silently; a
lightweight "map row cites a file:symbol — does the claim still hold?" spot-check (even
manual, at reconciliation time) would catch these. Logged as an angle for the next recon.
