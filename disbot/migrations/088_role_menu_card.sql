-- Role-menu banner cards (reaction-roles overhaul PR 6, plan §4.6d).
--
-- A role menu may optionally render a PIL banner/header image attached to its
-- message (the welcome-card pattern reused). The chosen card template + an
-- optional overlay text live on the menu row, rendered at post/edit time and
-- degraded to embed-only when Pillow is unavailable. Both columns are NULLABLE
-- with no default: NULL `card_template` = no card, so an existing menu renders
-- byte-identically to the pre-PR-6 bot (purely additive).

ALTER TABLE role_menus ADD COLUMN IF NOT EXISTS card_template TEXT;
ALTER TABLE role_menus ADD COLUMN IF NOT EXISTS card_text TEXT;
