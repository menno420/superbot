-- Member-facing sign-up counter on role menus (reaction-roles overhaul follow-on).
--
-- An opt-in per-menu flag: when on, the public menu embed renders a LIVE
-- participant headcount beside each role (current holders) + a distinct-member
-- total. This is the member-facing "how many people pressed the button" counter
-- the owner asked for (event-RSVP use case) — distinct from the operator-only
-- cumulative `role_menu_pickup_stats` rollup (migration 081), which counts
-- lifetime pickup/removal EVENTS for Diagnostics, not current holders.
--
-- Additive + default FALSE → every existing menu renders byte-identically; no
-- data backfill. The count itself is derived live from `guild.members` at render
-- time (no stored counter to drift), so only this one flag needs persisting.

ALTER TABLE role_menus
    ADD COLUMN IF NOT EXISTS show_counts BOOLEAN NOT NULL DEFAULT FALSE;
