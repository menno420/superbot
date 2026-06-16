# Session — Free multi-user control panel: identity & authority design

> **Status:** `complete`

## Origin

Owner set a major direction: the website is becoming a **free-to-use control panel** (anyone with
Discord login), where **everyone configures the bot personally** — so the site needs **per-user**
config as well as per-guild. Explicit: *"don't rush it — first the bot needs to be ready."* Docs-only
design capture (router **Q-0159**); no runtime built, per the owner's "don't rush."

## Finding (the bot is closer to ready than feared)

Confirmed the bot **already has both config layers**, audited:

- **Per-user:** `user_participation` (migrations 027/028) + `services.participation_mutation` +
  `core/runtime/user_config.py` + the in-Discord profile editor (`views/profile/`).
- **Per-guild:** `SettingsMutationPipeline` · `help_overlay` · `command_routing`.

So "everyone changes it personally" is **not new bot work** — it's the existing per-user seam. The
real **bot-ready** gap is just (1) the control API and (2) an **identity→authority bridge**: the
control API resolves `(user_id, guild_id)` → member → runs the **existing** capability checks
(`governance.capability`), so the site shows only allowed controls and every write is bot-verified.
The site stores only a session; no second source of truth.

## What shipped (this PR — docs only)

- `docs/planning/dashboard-live-editor-plan.md` § "Free multi-user control panel — identity &
  authority": the multi-user model, the per-user/per-guild seam table, the real readiness gap, and the
  **bot-ready-first** sequencing.
- Router **Q-0159** records the decision + provenance.

## Verification

- `python3.10 scripts/check_quality.py --check-only` → green (docs-only; no `.py` changed).

## 💡 Session idea (Q-0089)

**A read-only "your authority" preview on the website (pre-auth).** Even before login lands, the site
could explain — per subsystem — *which tier/capability* governs each control (already derivable from
`SettingSpec.capability_required` + the access map). It sets correct expectations for the future
control panel ("you'll be able to edit X in servers where you're admin; Y is yours personally") and is
pure read-model — no auth, no bot change. A gentle on-ramp to the multi-user model.

## Documentation audit (Q-0104)

- Owner decision recorded (Q-0159); design has a durable home. `check_docs` green.
- No runtime touched (owner said don't rush). Pending build questions (cog-vs-command enable/disable;
  `/commands` management surface go-ahead) remain open and noted for the next turn.
