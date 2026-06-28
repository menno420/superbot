# Support tickets — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `ticket` · **Type:** server-fn · **Family:** community
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/ticket_cog.py` (commands + persistent views + Help hook) ·
> `disbot/services/ticket_mutation.py` (the audited write seam) · `disbot/services/ticket_service.py`
> (read model + eligibility + transcript) · `disbot/views/tickets/` (`launcher.py` · `control.py` ·
> `hub.py` · `config_panel.py` · `confirm.py`) · `disbot/utils/db/tickets.py` (migration 098) ·
> setup: `disbot/views/setup/sections/ticket.py`

> Assessed during the completion-first arc (Q-0209). Tickets is a **strong, recent** unit (#1405 →
> #1417/#1421/#1423): open via command, a persistent launcher panel, **or** the AI; a per-ticket private
> channel created through the audited `ChannelLifecycleService` provisioning seam; claim, add/remove
> participants, close with a plain-text transcript posted to the log channel + DMed to the opener; a
> per-user open cap and a blacklist. Every write goes through `ticket_mutation` (one transaction +
> `audit.action_recorded` + a domain event), it's wired into the Setup wizard, and config is a fully
> button/dropdown flow that auto-creates the log channel. The honest gaps are **best-in-class breadth**
> (ticket categories/forms, priority/tags, reassign, CSAT rating, auto-close on inactivity, bulk ops) —
> intentional help-desk minimalism, not defects.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — open (command / persistent launcher button / AI tool with a confirm
      modal), claim, add/remove participant, close with transcript (≤500 msgs, to log channel + DM),
      channel teardown after delivery; per-user open cap + blacklist (`ticket_mutation.py`,
      `ticket_service.py`, `ticket_cog.py`).
- [ ] **Every best-in-class sub-option exists** — ❌ **partial.** **Missing vs Ticket Tool/Carl-bot:**
      multiple ticket **types/forms** (single subject field; `category_id` stored but no per-type
      template) · priority/tags · **reassign** (only claim) · CSAT/rating on close · auto-close on
      inactivity · bulk ops · rich (HTML) transcript. → punch-list #2.
- [x] **Failure modes honest** — one uniform `check_open_eligibility` gate (disabled / not-configured /
      blacklisted / limit-reached) across all open paths; missing Manage-Channels → a clear message;
      missing category → auto-created; close/claim refused on a non-open ticket.
- [x] **Idempotent** — config `upsert_config` (COALESCE preserves unset fields); double-claim refused;
      re-close refused.

### B. Reachability & UI — "the most convenient way"
- [x] **A command panel exists** — the persistent **launcher** (anchor-free "Open a ticket" button,
      static custom_id), the in-channel **control** panel (Claim/Close, persistent), and the `!ticket`
      **hub** (Open / My open tickets / Post panel).
- [x] **Reachable every natural way** — `!ticket` + the launcher panel + the AI `open_support_ticket`
      tool + Help hook (`build_help_menu_view`); Community-hub child (`parent_hub: community`).
- [x] **Integrated into the Setup wizard** — the "Support Tickets" section (order 72,
      `views/setup/sections/ticket.py`) opens the shared config panel; the readiness scan grades tickets
      (#1421).
- [x] **Return navigation** — persistent views survive restart via `add_view` + static custom_ids;
      ephemeral hubs/config panels are author-locked with back-nav; no dead-ends.
- [x] **In-place, not spammy** — config panel updates its embed live as selects change; ticket actions
      post single confirmations.

### C. Convenience
- [x] **One-click open + no-typing setup** — launcher button → modal; config is **dropdowns** (staff
      role + log channel) + a one-click **auto-create log channel** + Enable + Post-panel (#1423,
      `config_panel.py`).
- [x] **Sensible defaults** — staff role required (explicit); log channel optional/auto-creatable;
      category auto-created "Tickets"; max-open default 1 (`!ticketlimit` 1–25); ping-staff-on-open
      default on.
- [x] **Clear feedback** — open/close/claim each confirm; failures surface human-readable eligibility
      reasons.

### D. Authority & safety
- [x] **Authority re-checked at callback** — Claim re-checks `is_ticket_staff`; Close re-checks
      opener-vs-staff; add/remove re-check the staff gate at the callback (`views/tickets/control.py`,
      `ticket_cog.py`).
- [x] **All mutations through the audited seam** — `ticket_mutation` is the sole writer; each op is one
      `db.transaction()` + `audit.action_recorded` (`_emit_audit`) + a post-commit domain event
      (`ticket.opened`/`ticket.closed`).
- [x] **Resource creation uses the provisioning pipeline** — the per-ticket channel **and** the
      auto-created log channel go through `ChannelLifecycleService.create_channels` (P0-4 Q-0100),
      previewed/audited/fail-safe (outside the transaction); the opener+staff+bot overwrite is applied,
      @everyone denied.
- [x] **Reuses governance** — `visibility_tier: user`; capabilities `ticket.ticket.open`/`.manage`/
      `config.update`.

### E. Configuration
- [ ] **Settings lane** — ⚠️ ticket config is a **direct-lane** table (`ticket_config`, migration 098)
      owned by `ticket_mutation`, **not** `SettingsMutationPipeline`. This is a legitimate direct-lane
      choice (a focused, audited, single-domain config), button/dropdown-driven and audited — but it does
      not route through the settings pipeline the rubric prefers for scalars. → punch-list #3 (consistency
      note).
- [x] **Typed widgets** — role + channel **dropdowns** (never free-text ids); enable/auto-create
      buttons; max-open clamped 1–25.
- [x] **Audited config writes** — `upsert_config` + auto-create both emit `audit.action_recorded`.

### F. Wiring & discoverability
- [x] **Registry** — key `ticket`, `category: community`, `visibility_tier: user`,
      `entry_points: [ticket]`, `parent_hub: community`, 3 capabilities (`subsystem_registry.py`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; Community-hub child.
- [x] **Homed in `ownership.md`** — `ticket_config`/`tickets`/`ticket_blacklist` owned by
      `ticket_mutation` (channel creation delegated to `channel_lifecycle_service`).

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_ticket_mutation.py` (open eligibility gate, channel creation, insert,
      audit + bus; claim already-claimed refusal; close; auto-create log channel; config; blacklist);
      `test_ticket_service.py` (eligibility classes; transcript render).
- [x] **AI-tool + setup tests** — `test_ticket_ai_tool.py` (offered only with guild+member; refuses
      empty/ineligible without emitting); `test_ticket_section.py` (registration, DM rejection, config
      panel + progress marker).
- [ ] **Coverage gaps** — no explicit add/remove-participant authority test; transcript file
      generation/DM marked best-effort/no-cover. → punch-list #4 (minor).
- [ ] **Live walkthrough recorded** — pending. → punch-list #5.
- [ ] **Owner ✔** — pending. → punch-list #6.

## Punch-list (clear these to certify)

1. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (setup ticket
   section → post panel → open → claim → add a member → close → transcript in log + DM), screenshots.
2. **Best-in-class breadth (rubric A)** *(owner-paced, deepening)* — multiple ticket **types/forms**
   (reuse the stored `category_id`) · priority/tags · **reassign** · CSAT/rating · auto-close on
   inactivity · bulk ops · richer transcript.
3. **Config-lane consistency** *(offline, minor)* — decide whether the `ticket_config` direct lane should
   stay as-is (audited, focused) or route scalars through `SettingsMutationPipeline` for uniformity.
4. **Add/remove-participant authority test + transcript-delivery test** *(offline, minor)*.
5. *(rolled into #1 above)*.
6. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_ticket_mutation.py` · `…/test_ticket_service.py` ·
  `…/test_ticket_ai_tool.py` · `tests/unit/views/setup/sections/test_ticket_section.py`
- **Walkthrough:** pending (punch-list #1)
- **Owner sign-off:** pending (punch-list #6)

## Verdict
Tickets is **functionally solid, fully audited, and provisioning-safe** — three open paths, a private
channel through the audited lifecycle seam, claim/add/remove/close-with-transcript, per-user cap +
blacklist, Setup integration, and a no-typing button/dropdown config that auto-creates the log channel.
It is **not yet `✔ certified`**: the gaps are **best-in-class breadth** (ticket types/forms, reassign,
CSAT, auto-close — #2), a config-lane consistency note (#3), minor test gaps (#4), and the owner
walkthrough/sign-off (#1/#6). No safety/audit/dead-end issues found.
