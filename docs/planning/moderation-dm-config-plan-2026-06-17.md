# Plan — server-owner-configurable moderation DMs (per-action)

> **Status:** `plan` — executable implementation plan, owner-aligned (anchored on the **Q-0147**
> standing DM policy). Promoted from the idea
> [`ideas/server-owner-configurable-moderation-dms-2026-06-16.md`](../ideas/server-owner-configurable-moderation-dms-2026-06-16.md)
> by the eleventh Q-0107 reconciliation pass (band-#1020, 2026-06-17) per the Q-0144 idea→plan step:
> the buildable `ready` queue had thinned to dashboard/manifest owner-paced slices, so the best
> ungated owner-aligned idea was promoted into a complete plan to become the executor's next
> ▶ Next action.
> **Routing:** safety / community lane. **One PR, `ready`/`disbot`-runtime.**

## 0. The point (and the key correction the scout surfaced)

The owner's Q-0147 standing rule: the *only* DMs the bot may send without the recipient opting in are
**moderation/warning DMs**, and only when **the server owner has enabled them** with a **clear way to
configure which moderation actions trigger a DM** (warn → DM yes; auto-delete → DM no; per guild).

**The DM machinery already exists** — this is an *extension*, not a new subsystem. Verified in source:

- `disbot/services/moderation_service.py` → `_notify_target(...)` already sends a best-effort,
  fail-open DM (catches `discord.Forbidden`/`HTTPException`), gated today by a single
  `policy.dm_on_action` master bool, ordered correctly per action (before removal for kick/ban,
  after success for warn/timeout).
- `disbot/services/moderation_config.py` → `ModerationPolicy` already carries
  `dm_on_action: bool` + `dm_template: str`, resolved via `services.settings_resolution.resolve_value`
  (lines 126–127, 250–259, 323–324); `render_dm_message(...)` already renders a neutral per-action
  notice with token substitution (never `str.format`).
- The per-action *list* idiom already exists in the same policy: `public_log_actions` (a
  comma-separated action allow-list) + `public_log_channel`. **Mirror it** — do **not** add N separate
  bools.

So the gap is exactly: **(a)** a master enable that an owner controls, and **(b)** per-action
granularity (today `dm_on_action` is all-or-nothing). Both fit the existing seam with **no migration**
and **no new module** — the smallest correct change.

## 1. Scope (one PR)

Turn `dm_on_action` (all-or-nothing) into an owner-controlled, **per-action** DM policy:

1. **Keep** `dm_on_action` as the **master switch** (off by default — unchanged default, so a fresh
   guild behaves exactly as today). When off, **no** moderation DM fires regardless of the per-action
   list.
2. **Add** a `dm_actions` field to `ModerationPolicy` — a comma-separated action allow-list, mirroring
   `public_log_actions` exactly (same parse helper, same validator shape). Default = `"warn,timeout"`
   (the two actions where a "you were actioned, here's why" notice is most useful and least
   surprising; `kick`/`ban`/`auto_delete` opt-in). An action DMs **iff** `dm_on_action` is on **and**
   the action is in `dm_actions`.
3. **Gate `_notify_target` on the per-action membership**, not just the master bool.
4. **Surface both on `!settings` → Moderation** via `cogs/moderation/schemas.py` `SettingSpec`
   entries, mirroring the existing `public_log_actions` / `public_log_channel` specs (the owner's
   "clear way to configure which actions trigger a DM").

Out of scope (capture as follow-up ideas if they come up): an appeal-link template token; rate-limit
backoff beyond Discord's own caps (the existing best-effort swallow already covers closed DMs); a
per-action *template* (one shared `dm_template` stays the single template).

## 2. Turn-key steps

### Step 1 — `disbot/utils/settings_keys/moderation.py` (or wherever the moderation keys live)
Add the constant for the new key next to the existing moderation keys, prefixed to match the
namespace (the existing `dm_on_action` key tells you the prefix convention in this file):

```python
# Per-action DM allow-list — a comma-separated subset of
# warn,timeout,kick,ban,auto_delete. An action DMs the affected member iff the
# master dm_on_action switch is on AND the action appears here. Mirrors
# public_log_actions. Default warn,timeout.
MODERATION_DM_ACTIONS = "dm_actions"   # match the existing key-naming style in this file
```
Re-export it from `disbot/utils/settings_keys/__init__.py` (add the import + `__all__` entry), exactly
as `dm_on_action` is re-exported. **Use the `settings_keys` constant everywhere — never the raw
string** (the `db.get_setting` rule).

### Step 2 — `disbot/services/moderation_config.py`
- Add a `DEFAULT_DM_ACTIONS = "warn,timeout"` constant beside `DEFAULT_DM_ON_ACTION` /
  `DEFAULT_PUBLIC_LOG_ACTIONS`.
- Add `dm_actions: str = DEFAULT_DM_ACTIONS` to `ModerationPolicy` (next to `dm_on_action`).
- Resolve it in `load_policy` exactly like `public_log_actions` (the `resolve_value(... "dm_actions"
  ...)` block — copy the `public_log_actions` resolve block, swap the key/default).
- Add a parsed accessor mirroring the `public_log_actions` one. If `public_log_actions` has a
  `public_log_action_set` property (a normalized `frozenset[str]`), add the parallel
  `dm_action_set` property; reuse the same split/normalize/validate-against-known-actions helper so
  an unknown token can't sneak in. The known-action vocabulary is the keys of `_DM_ACTION_TEXT`
  (`warn`/`timeout`/`kick`/`ban`) plus `auto_delete` — confirm the set against the action strings
  the service actually passes to `_notify_target`.

### Step 3 — `disbot/services/moderation_service.py` → `_notify_target`
Change the gate from the master-only check to master **and** per-action membership:

```python
    # was: if not policy.dm_on_action: return
    if not policy.dm_on_action or action not in policy.dm_action_set:
        return
```
Everything else in `_notify_target` (DM-capability check, `render_dm_message`, the
`Forbidden`/`HTTPException` swallow) stays — the contract is unchanged, only the gate narrows.
**Verify every call site passes the canonical `action` string** that matches the `dm_action_set`
vocabulary (the same strings used for `mod_logs` / `EVT_MOD_ACTION` / `render_dm_message`), so the
membership test lines up. `auto_delete` is the one to double-check (it should default *out* of the
list — the owner's explicit "auto-delete → DM no" example).

### Step 4 — `disbot/cogs/moderation/schemas.py`
Add two `SettingSpec` entries to the moderation subsystem schema, mirroring the existing
`dm_on_action` (bool) + `public_log_actions` (csv) specs:
- `dm_on_action` — confirm it is already surfaced as the **master** "DM members on a moderation
  action" toggle; relabel its hint to name it the master switch ("when on, the actions below DM the
  member"). Disclose the privacy posture in the hint (the member is DMed the action + reason).
- `dm_actions` — a csv/multi-select spec listing `warn,timeout,kick,ban,auto_delete`, default
  `warn,timeout`, validated against the known-action set (reuse the `public_log_actions` validator).

This is the "clear way to configure which actions trigger a DM" the Q-0147 policy requires.

### Step 5 — tests (`tests/unit/services/test_moderation_dm_*.py` or extend the existing moderation test)
- master off ⇒ no DM for any action (current behaviour preserved);
- master on + action in `dm_actions` ⇒ DM sent (assert `render_dm_message` body, spy on `send`);
- master on + action **not** in `dm_actions` (e.g. `auto_delete` with the default list) ⇒ no DM;
- closed-DM (`Forbidden`) ⇒ swallowed, the moderation action still completes (fail-open invariant);
- `dm_action_set` parses/normalizes a messy csv and **rejects an unknown token** (matches the
  `public_log_actions` parsing test);
- default `ModerationPolicy()` is behaviour-identical to today for an unconfigured guild.

## 3. Guardrails (all already satisfied by the seam)

- **Off by default** — `DEFAULT_DM_ON_ACTION` stays the existing default (no behaviour change for an
  unconfigured guild). No migration (legacy KV settings).
- **Fail-open, best-effort** — `_notify_target` already swallows `Forbidden`/`HTTPException`; the
  audited moderation action is authoritative, the courtesy DM never blocks it.
- **No new mutation path** — the DM is a notification *side-effect* of an already-audited action
  through `moderation_service`; no DB writes, no audit change. Architecture clean (services, no
  views/cogs import).
- **Privacy/abuse** — only a member already in the guild, only on an action against *them*, only when
  the owner enabled it and listed that action. Disclosed in the setting hint.

## 4. Verification before push

```
python3.10 scripts/context_map.py disbot/services/moderation_service.py
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full
```
Ships under the standing posture: a contained safety/community feature on an existing audited seam,
off by default. No Hermes carve-out is required (unlike #929/#941 it adds **no** new subsystem and
**no** new external egress — moderation DMs stay inside Discord).

## 5. Why this is the executor's next ▶ ungated slice

The band-#990 §4 named this "moderation-DM config (Q-0147 sibling)" as a `ready`/`plan-first` slice
that "needs a small plan." This is that plan. It is **ungated** (no owner decision pending — the
Q-0147 policy already decided it; no creds; no data gap), **contained** (one PR, existing seam, no
migration), and **owner-aligned** (it directly implements half of the owner's standing DM rule, the
other half being myprofile PR C onboarding). When the next scheduled dispatch fires with an empty
work order and the dashboard/manifest lanes are owner-paced, **this is the slice to build.**
