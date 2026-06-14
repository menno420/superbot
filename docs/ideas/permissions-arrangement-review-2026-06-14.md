# Permissions arrangement review — capture

> **Status:** `captured`. **Not a plan, not approval.**  
> Concerns the bot's runtime permission model — where authorization decisions
> are made, which layers see them, and how they compose across cogs/services.

## Why this needs a look

The bot now has multiple adjacent permission-related surfaces, and it is not
yet clear whether they are arranged intentionally or have accreted.

Observed signals in the current tree:

- `disbot/governance/capability.py` — capability/authority tokens, the
  likely source of truth for *what* is allowed.
- `disbot/services/resource_provisioning.py` and the audit doc
  `docs/audits/platform-runtime-data-layer-audit-2026-06-05.md` — an
  11-step provisioning contract that includes explicit **bot permission
  validation** and **authority validation** steps.
- `disbot/cogs/*` and `disbot/views/*` — command handlers and UI panels
  that embed their own allow/deny logic; the amount of duplicated vs
  centralized checking is not yet mapped.
- `docs/building-roadmap/admin-powers-config-coverage.md` — an admin
  powers review whose §4 asks whether changes raise/lower permissions or
  override defaults, suggesting the current state may not be
  unambiguous.
- `docs/setup-platform/setup_wizard_finalization_plan.md` — explicitly
  rejects **per-user permission overwrites** in favor of role-templates,
  meaning at least one area has a deliberate layering choice. Whether the
  rest of the bot follows that same doctrine is unknown.

## Open questions

1. **Single source of truth?** Is `disbot/governance/` the canonical place
   for *can-do* checks, or do cogs/services also hold local grant tables?
2. **Fail-closed vs. fail-open defaults** — do every UI action and service
   call conservatively deny when the check is missing?
3. **Overlap/occlusion semantics** — does bot-level + role-level +
   channel-level permission compose correctly, or are some layers silently
   bypassed?
4. **Auditability** — can every denied action be traced to the exact grant
   that refused it, without adding new logging?
5. **Migration path** — if the current arrangement is ad hoc, what is the
   cheapest way to harden it without rewriting every cog?

## Initial scope guess (discuss / validate)

Probably an **audit-first** item: a read-only pass that maps each
checkpoint to its owner document/source, flags duplications and gaps, and
turns the result into either “already consistent — just add tests” or
“here is the normalization plan”.

Low implementation risk, moderate architecture value.

## Decision record

Need: OWNERSHIP validation + Risk review before it becomes a planning / PR
item. Recommended gate: review `disbot/governance/` + every cog/view
handler for `check`, `has_permissions`, `authorize`, `capability` usage.
Promote to plan only after that map exists.
