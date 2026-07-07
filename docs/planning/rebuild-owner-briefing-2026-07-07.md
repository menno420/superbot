# The rebuild, in plain language — everything you need to know (2026-07-07)

> **Status:** `reference` — the owner-facing plain-language companion to
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md). Written at the
> owner's request ("tell me everything I need to know in plain language"). Nothing here is new —
> every statement is the plain rendering of something in the canonical plan or its companions;
> where they disagree, they win.
>
> **⚠ AMENDED same day by your own Q-0241 directive (#1776):** this briefing was written hours
> before you retired the gates. Where it says "sitting," "say go," or "gate," read: **nothing
> waits for you anymore.** The agents build in order, test each piece live in a server, and treat
> your silence as approval. The §4 flag list is still worth reading — but as a *veto list you can
> react to anytime*, not a meeting you owe anyone. The in-line corrections below mark the
> sentences this changed.

## 1. Where things stand, in one paragraph

All the thinking is done. Over the past week the agents inventoried everything the current bot
does (all ~55 features), designed the new bot's foundation in detail (14 frozen design documents),
had that design adversarially checked by four independent review fleets (Gate V), and then folded
everything into **one master plan** — the canonical plan. The old scattered planning documents now
point at it. Nothing about the new repo has been *built* yet — ~~no new-repo code until you say
go~~ *(Q-0241: the build proceeds on its own; you watch it happen live and say something only if
you dislike what you see)*.

## 2. What the new bot actually is (the one idea to hold on to)

Today's bot is ~880 hand-written Python files where every feature wires itself up its own way —
which is why the same bug keeps appearing in different clothes, and why two features once crashed
production just by accidentally using the same command name.

The new bot flips this: features are **declared, not hand-wired**. Each feature is a short
*manifest* — "here are my commands, my settings, my panels, my data tables" — and a small, very
well-built **engine core (the "kernel", eleven pieces, K0–K10)** turns those declarations into the
running bot: one place that dispatches every command, one place that checks every permission, one
place that writes every money transaction (all-or-nothing, always audited), one registry that
makes name collisions *impossible before boot* rather than a production crash. We measured — not
guessed — that ~85% of the current bot's surface fits this declarative style; the rest stays
ordinary code behind counted escape hatches.

Three things you asked about got explicit homes in that core: **AI** (the machinery that talks to
providers, routes natural language, and keeps answers grounded is kernel piece K10; the BTD6 and
Limbus *knowledge* stays a plug-in domain on top), **automation/scheduling** (durable timers that
survive restarts + one shared "do these steps atomically" engine — spread across kernel pieces K5,
K9 and K7; today's version silently loses timers on every deploy), and **verification** (a
named layer of its own: the golden-replay harness, the simulators, the test guild, and your live
sign-offs — the machinery that proves the new bot behaves like the old one).

## 3. How we prove the new bot is right (your safety story)

- **465 "goldens"** were captured from the live bot: exact command in → exact reply out. The new
  repo is *born red* — every feature stays failing until it reproduces the old bot's behavior
  byte-for-byte. Agents can't merge around it.
- **Your data is contractually protected**: balances, inventories, XP, karma, settings, and every
  button ID users can click survive verbatim. The import into the new database happens first
  against a *copy* (the "shadow" environment), you review the reconciliation report, and only then
  against reality.
- **The old bot keeps running in production the whole time.** The actual switch is a token swap
  that takes minutes, and for 7 days afterwards the old bot sits intact as an instant rollback.
- **A dedicated test Discord server** (designed, not yet created — 9 zones, ~40 channels, one home
  per feature) is where the new bot lives its whole life before it ever touches your real server.

## 4. What I decided for you, and what's left to you

Per your standing instruction, all the technical calls are **made, not asked** — each with its
reasoning in the canonical plan's decisions log. ~~Your part is one sitting~~ *(Q-0241: no sitting
— skim when you like)*: the plan's **§1 flag list** (five items) is your veto surface; anything
you don't push back on counts as blessed. The five, in plain terms:

1. **Your data carries over via a one-time import you review first** (recommended; alternatives
   rejected as trust-destroying).
2. **The 12 pre-filled safety rulings** — things like "money mismatches are never auto-fixed,
   they're quarantined for you" and "a nightly backup means at most 24 hours of loss; upgrading
   that is a paid decision for later." Eleven of the twelve just bless what's already built. The
   one real choice: if Discord ever denies the bot's message-reading permission, should it **boot
   in slash-command-only mode** (my recommendation) or refuse to boot at all (current default)?
3. **The layer-model corrections** above (AI, automation, verification) — bookkeeping you can wave
   through.
4. **How the test server gets driven**: automated tests type real prefix commands; slash commands
   and buttons get clicked by a human (you, or a spare account you operate) — because Discord's
   rules ban automating a user account, and bots structurally can't click other bots' buttons.
5. **The pass bar for the cold-start experiment** (below): the memory kit must measurably help on
   at least 2 of 3 measures with none getting worse.

## 5. What is happening right now (this session)

The three steps that don't need you are being executed as you read:

1. ✅ **The memory kit's last known bug is fixed** (a state-file write could half-land if a step
   failed mid-way; now it's all-or-nothing — 427 tests green).
2. 🔄 **The cold-start experiment is running** — the one gate that was specced but never run.
   Six fresh agent sessions are working the same three tasks on the same tiny throwaway project,
   half of them with the memory kit installed, half without, followed by a "continue a stranger's
   work" task and an independent judge. It answers the question the whole workflow bet rides on:
   *does the kit actually help a cold agent?* You'll get a written verdict either way.
3. ✅ **The amendment bookkeeping checker exists now** — the design's change-log claimed an
   enforcer that was never built; it's built and wired into CI.

## 6. What happens from here *(was "after you say go" — Q-0241: there is no go to give)*

Agents create the new repo (`superbot-next` on a fresh Railway project), install the memory kit as
its first act, then build the eleven kernel pieces in their frozen order (~5–8 days — this part
can't be parallelized, it's a chain), then fan out and port features band by band — settings and
operator tools first, economy next, **games deliberately late** (the review fleet proved they
don't block anything), AI knowledge last. Each ported feature goes green against its goldens and
auto-merges. Your *reaction windows* (not approvals — the work continues either way, on the
reversible path): the three layout-simulator results during the port, the data-import dry-run
into shadow, and the cutover week with its 7-day rollback window. Realistic active-build time,
measured against how fast the agent fleet actually merges: **about two weeks, floor of ~1.5**.

## 7. The honest caveats

- The cold-start experiment is small (one paired run per task) and partially blind — it's
  evidence, not proof; its verdict says so plainly either way.
- The goldens are broad (96% of commands) but shallow in places (events/tables/settings depth) —
  the plan widens them per band during the port rather than pretending they're complete.
- ~15% of the surface won't fit the declarative style and stays ordinary code — counted and
  visible, not hidden.
- ~~The two-week estimate assumes your gate turnarounds are hours-to-a-day~~ *(Q-0241: no human
  gates remain in the loop — the agents are the pacing item, plus CI.)*

**Bottom line:** read the canonical plan's §1 (five flags) and §5 (the 17-step sequence) whenever
you like. The program no longer waits for anything from you — say something only if what you read,
or what you see happen in the server, bothers you.
