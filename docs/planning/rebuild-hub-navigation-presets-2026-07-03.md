# Rebuild Phase A — hub topology · navigation contract · interface presets (2026-07-03)

> **Status:** `plan` — **Phase-A companion decisions log #3**, continuing the
> [conventions freeze](rebuild-conventions-invocation-authority-2026-07-03.md). Records the
> owner-live decisions on the bot's **information architecture**: one unified help hub, the
> universal navigation contract, and per-guild interface presets. **Provenance:** owner + agent
> live session 2026-07-03 (PR #1684). Owner rulings → **Q-0230…Q-0232**. Frozen capstone
> artifacts unedited; feeds Gate-0 (design-spec NavigationSpec / PanelSpec / the hub engine).
> Source wins over this doc (Q-0120). Everything below is **one engine steered by declarations**
> (S-1, Q-0219) applied to navigation + presentation.

---

## 1. Hub topology — one unified help hub (Q-0230)

**Decision.** A **single help hub** is the bot's front door — *not* two separate player/operator
trees. Admin lives **inside** the one hub as a **permission-gated node**: a button that is locked
unless the viewer has the right permission, opening a full admin help menu. Everything is one
panel; admins simply see one extra (gated) door.

**Top-level buckets (working set — refine in Stage 2).** Owner broadly agrees with, and wants to
improve:
- 🎮 **Games / World** — blackjack, fishing, mining, explore, casino, …
- 👤 **You** — profile, balance, inventory, rank
- 🏘️ **Community** — leaderboards, spotlight, karma, giveaways, starboard
- 🧠 **Knowledge / AI** — btd6, project moon, ask-anything, media generation
- 🛠️ **Admin** — the gated operator menu (setup, moderation config, logging, …)

*(These are a starting spine; the exact bucket set + per-subsystem placement is Stage-2 work,
decided per-subsystem against this framework.)*

**Gating rule (binds an existing repo view-rule):** the admin node's availability is a **declared
authority gate** (Q-0227) and is **re-checked at click time**, never only at panel-open — opening
the hub does not authorize a later admin click.

> **⚑ AMENDED by Q-0237(c), 2026-07-03 (owner, final-judgment sitting):** the admin node is
> **HIDDEN** from those without permission, **not shown-locked**. The one-unified-hub model here is
> kept; only "gated *visible* node" → "hidden node" changes. A viewer sees only the operator
> surface(s) they hold the tier for (moderator slice for mods, full admin for admins).

## 2. The navigation contract (Q-0231) — framework-guaranteed, not per-panel discipline

Every one of these is **injected by the panel framework into every rendered state**, so no
individual panel has to remember them (the discipline that always drifts). One navigation engine
owns it; each panel only declares its identity + semantic parent + content.

1. **Back + Home on every state, at every depth, across unlimited re-renders.** Two *distinct*
   controls:
   - **Back** = pop the actual path the user took (contextual — follows the real navigation stack,
     correct even after many in-place updates and regardless of how the panel was reached).
   - **Home** = jump to the help root (absolute — always the same destination).
2. **Every hub / sub-hub is directly openable by its own command** — admin via `!admin` (and
   `/admin`), and the same for every node (`!games`, `!profile`, …). Deep-linking, not click-down-
   the-tree-every-time. (Generalizes the owner's admin-specific request per S-1.)
3. **Semantic parent declared per panel** — so **Back** has a target even on *direct* entry (when
   there is no navigation stack because the user jumped straight in via a command). Runtime Back
   follows the real stack when present; falls back to the declared semantic parent otherwise.
4. **Panels are persistent and restart-safe** — no premature timeout. Implemented as persistent
   views (no per-instance timeout, matched by a **versioned custom_id**, generated-from-state so
   content re-derives from the manifest + DB on each render). **Payoff specific to this bot:**
   because merge = deploy redeploys the worker constantly (Q-0193), in-memory panels would die on
   every deploy; persistent generated panels simply re-render themselves after a restart. "Don't
   time out too soon" and "survive the constant redeploys" are the **same fix**, and it falls out
   of the generated model for free. Trade-off (a non-issue here): a persistent panel can't stash
   secret in-memory state between clicks — it doesn't need to, because it re-derives content from
   declarations + DB every time.

## 3. Interface presets — customizable hub, per guild, with live preview (Q-0232)

**Decision.** The hub is **not a fixed layout** — it is **customizable per server**, and setup
offers **presets** that reshape the help menu to fit the server type (e.g. a *Game-server* preset:
btd6 info + moderation + server functions + message levels + a few light games for a bot channel),
alongside a **safe-default** preset (the full hub). Setup presents presets with a **clear preview**
and simple choices: pick a preset, tweak it, or hand-pick — always with the safe default available.

**This is the preset primitive (Q-0215 / Q-0070) pointed at the hub — not a new mechanism.** The
hub is generated from *(the manifest of all possible nodes)* × *(this guild's visibility config)*;
a **preset is a named bundle of that per-guild config.**

- **The preview is the real thing.** Because the hub is generated, "preview this preset" renders
  the actual hub with that config — no separate mockup to build or keep in sync. The preview *is*
  the output.
- **Follows the Q-0215 three-requirement pattern:** pick a preset → edit from it → or manual, with
  the safe default always present.
- **Features declare their own preset membership (anti-drift).** Each subsystem declares *which
  presets it belongs to* (data on the feature); presets are assembled from those declarations —
  so a new subsystem next year slots into the right presets automatically, and no central preset
  list goes stale.
- **Presets ≠ triage (different layers).** The Stage-2 triage (D-5) decides what *exists in the
  bot at all*; presets decide what's *visible/on per server*. A dropped subsystem is gone
  everywhere; a preset-excluded one still exists, just not surfaced in that guild.

**✅ RESOLVED by Q-0237(a), 2026-07-03 (owner, final-judgment sitting):** preset exclusion is
**visibility-only — hidden from the hub but still runnable by command**, preserving the shipped
Q-0055/HLP-4 invariant that display-hide is presentation-only. A guild may *additionally* disable
via an explicit per-preset toggle, but exclusion alone never disables. (This **reverses** the
original agent recommendation of "hidden = off" below, which 5 of the day's 7 reviewers flagged as
a contract reversal.) Keep **visibility** (hub surfacing) and **activation** (can-run) as distinct
axes.

> *(Original open sub-decision, now superseded — kept for provenance:)* when a preset *excludes* a
> bucket, does that mean the features are **hidden from the hub but still runnable by command**, or
> **disabled entirely** for that guild? *Agent recommendation was:* default **hidden = off**, with a
> per-guild toggle to hide-without-disabling.

## 4. Improve + centralize — this already exists and works (Q-0232)

Verified in shipped source this session — the capability is **real and working**, but **reinvented
many times**, which is exactly what "centralize" targets:

- **Working today:** the setup wizard's **preset selector** (`views/setup/sections/preset_select.py`
  — bundled presets, `preview_preset`, applied via setup operations) **and** the **help
  customization subsystem** (`views/help/home_builder.py` + `views/help/editor.py` (642 lines) +
  `services/help_overlay.py` + `services/help_projection.py` (662 lines)). So per-server interface
  customization + preset-at-setup + preview all exist.
- **The fragmentation:** presets/templates are reimplemented **≥7 times** —
  `ai_preset_service`, `ai_orchestration_presets`, `automation_templates`, `setup_role_templates`,
  `logging_presets`, `edit_number_presets`, `preset_picker` — *plus* the setup `preset_select`;
  and the help-overlay editor is a **separate customization path** from the setup preset selector.
- **Rebuild job (retrofit — the proven mode):** collapse to **one preset/template primitive
  (C-3, Q-0228)** feeding **one generated hub**, with the setup preset step and the help editor
  becoming two views onto the *same* per-guild config. The existing `preset_select` + help editor
  are the **prior art to port**, not reinvent.

## 5. What this feeds / what's next

- **Feeds Gate-0:** NavigationSpec (§2), the hub/PanelSpec generation (§1), the preset primitive
  unification (§3–4, with C-3).
- **Stage-2 inputs:** the exact top-level bucket set + each subsystem's hub placement + preset
  membership declarations.
- **Open before this freezes:** the §3 hide-vs-disable choice.
- **Also resolved as a side effect:** the first-run **onboarding/setup spine** — first-run setup
  *is* "choose your interface preset, preview, done."

## 6. Pointers

- Parent: [`rebuild-conventions-invocation-authority-2026-07-03.md`](rebuild-conventions-invocation-authority-2026-07-03.md) · [`rebuild-stage1-global-review-2026-07-03.md`](rebuild-stage1-global-review-2026-07-03.md)
- Generalization standard: Q-0219 · authority: Q-0227 · presets: Q-0215/Q-0070 · centralization set: Q-0228
- Shipped prior art: `disbot/views/setup/sections/preset_select.py`, `disbot/views/help/` (`home_builder`, `editor`), `disbot/services/help_projection.py`, `help_overlay.py`
- Owner rulings: **Q-0230 (hub) · Q-0231 (navigation contract) · Q-0232 (interface presets + centralize)** in [`../owner/maintainer-question-router.md`](../owner/maintainer-question-router.md)
- Session log: `.sessions/2026-07-03-rebuild-hub-navigation.md` (PR #1684)
