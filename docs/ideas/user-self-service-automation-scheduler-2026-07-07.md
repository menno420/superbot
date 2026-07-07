# User-facing self-service automation scheduler (personal "cron jobs")

> **Status:** `ideas` — capture only, not approved for implementation. Dropped by the owner
> 2026-07-07 during the rebuild-plan review session, as a design input for the not-yet-built K9
> durability band. **Subsystem:** none (cross-cutting kernel capability; consumed by many
> subsystems once built).
>
> **Timing note:** this is worth folding in *before* K9 is built (canonical plan
> [`rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md) §5
> step 10), not after — K9's `ManagedTaskSpec`/`sb_due_queue` machinery already exists on paper for
> exactly this shape of problem (Interval/Cron/OneShot/EventTrigger, misfire/catch-up, boot-reconcile).
> Bolting a user-facing variant on after the port bands ship would recreate the "smeared feature"
> pattern the whole rebuild exists to kill.

## The ask, in the owner's words

> "there should be an easy way for users to set cron jobs for themselves in the bot, with
> guardrails ofcourse, and in an unlockable way for certain features, like a user should be able to
> set a recurring command for themselves, or a recurring notification etc, to automate some parts
> of games or stat checking etc... this should probably also be a foundational function used by
> multiple subsystems, like recurring roles or channels etc"

Concrete examples given: "send my rank every morning at 8am"; "after every 6 hours check on the
chicken farm." The explicit constraint: it must improve quality of life, **not** become an unfair
advantage over players who don't set one up.

## Why this isn't already covered

Prior art exists, but all of it is narrower than what's being asked for here:

- `!remind` exists today but is **in-memory only — loses every reminder on restart**
  (`docs/ideas/fun-and-ease-brainstorm-2026-06-09.md` C4, an owner ease-pick, still unbuilt).
- `docs/ideas/competitive-teardown-2026-06-10.md` #8 ("RemindMe + user-facing scheduler slice")
  scoped this as a reminder-command port, not a cross-subsystem primitive with fairness guardrails.
- `docs/ideas/future-product-direction-2026-06-07.md` ("Notification subscription profiles") is
  the closest prior framing — extend the existing scheduler/notification ownership — but is about
  *subscribing to system-generated events* (health/mod digests), not user-declared recurring
  triggers against arbitrary game state.
- The rebuild's own automation ruling (canonical plan §2.4 B-2) frames automation as **admin/system**
  facing: scheduled announcements, retention sweeps, health loops. Nothing in the frozen specs
  reserves a *user-scoped* producer the way `Producer.HUMAN_SETUP` was reserved for the setup wizard
  (§11 A-9). This idea is asking for the equivalent: a `Producer.USER_SELF_SERVICE` (or similar)
  kind on the same K9 due-queue.

## The two categories, and why they carry very different risk

**A. Notify-only ("send my rank every morning at 8am").** Low risk. This is a scheduled *read* of
already-current state, delivered as a DM/ping. It changes nothing about game balance — the user
still has to act on what they see. This is functionally identical to the reminders idea already on
the books, generalized to "any read-only query a subsystem opts into," not just a free-text note.

**B. Recurring *checks tied to action* ("check on the chicken farm every 6 hours").** Higher risk.
Depending on what "check" means, this can silently become an unfair-advantage lever:

- If "check" means **notify** ("your chicken farm is ready to collect") — safe, same as category A.
- If "check" means **auto-collect/auto-claim on the user's behalf** — this is where fairness breaks.
  A user who never has to remember to log in gets strictly more value than one who does, for the
  same amount of attention. That is the exact failure mode the owner is flagging.

**Recommended default: automations are notify-only by default.** A subsystem may explicitly opt an
action into "automatable" status only when the action is provably idempotent-and-time-bounded in a
way that manual and automated execution produce the *same* outcome a player would get by remembering
to log in at any point in the window (e.g., claiming a daily reward that doesn't decay is fine to
automate; something with decay, streak bonuses, or a limited-window bonus is not, because automation
would then reliably capture value a forgetful human player would miss).

## Design sketch (for whoever picks this up)

1. **One kernel primitive, subsystem opt-in.** Extend K9's `ManagedTaskSpec` grammar with a
   user-scoped trigger kind. Each subsystem's manifest declares which of its read-only queries
   (category A) or idempotent claim-actions (category B, opt-in only) are "automation-eligible," at
   what minimum interval, and whether it's notify-only or action-taking. This keeps the fairness
   call where it belongs — with whoever designs that specific game/subsystem — instead of the
   kernel silently exposing every command to automation.
2. **Guardrails, enforced centrally so no subsystem has to reinvent them:**
   - a floor on interval (e.g. no more often than every N minutes) to stop notification spam and
     cap any residual advantage;
   - a per-user cap on total active personal automations (prevents one power-user from turning the
     bot into their personal automation farm);
   - unlock gating — tie the *capability* (not each individual automation) to something like rank,
     level, or a cosmetic-currency unlock, consistent with the existing "cosmetic-only, no bot-side
     billing" decision (Q-0039) — makes automation itself a QoL reward, not a day-one default;
   - quiet hours / timezone respect, reusing the timezone/locale idea already noted against
     `!remind`/birthdays (`docs/ideas/superbot-vision-2026-06-10.md`);
   - delivery through the existing notification/settings authority, not a bespoke path.
3. **Durability for free.** Because this rides K9's due-queue, restart-survival, misfire policy, and
   boot-reconcile come along at no extra design cost — this is the concrete payoff of doing it as a
   kernel extension instead of a per-feature bolt-on.
4. **"Recurring roles/channels"** (the owner's other example) is a related but distinct case —
   *admin-declared* time-based lifecycle automation (temp roles that expire, scheduled channel
   archival), which the canonical plan already partly covers as K9 consumers (role_grants expiry
   sweep, §11 A-8). Worth naming explicitly as a sibling consumer of the same due-queue, but it does
   not need the fairness guardrails above since it's operator-declared, not user-self-service.

## Open question that is genuinely the owner's to make, not an agent's

Whether *any* category-B action-taking automation should ever ship, versus notify-only forever.
The notify-only default above is a recommendation, not a ruling — this is a product-feel call
about how much "idle game" behavior is wanted, and it should get an explicit answer once a
subsystem actually wants to use category B (no subsystem does yet, so nothing is blocked today).

## Recommended routing

Fold as a K9 landing when Phase-B's per-step plan for K9 (canonical plan §5 step 10) is written —
analogous to how §11 A-8's background-obligation landings were added. Until then this stays a
capture; nothing here blocks the rebuild start.
