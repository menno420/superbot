# Production eval checklist — the 2026-06-09/10 burst

> **Status:** `audit` — the maintainer's **dedicated eval session** working doc.
> Companion to [`past-day-verification-2026-06-10.md`](past-day-verification-2026-06-10.md) §6
> (which named this walk "the single highest-value next action").
> Covers everything user-visible from PRs **#606–#672**. Tick boxes as you go;
> report findings in the usual "X should be Y / X is currently Z" style — each
> one becomes a precise diagnosis target for the ride-along agent.

**How to read this:** items are ordered by *who can test them*. Tier 1 is
things **only production can verify** (the sandbox has no AI provider key —
these gate the next AI work). Tier 2 is the new game economy (your balance
feel gates mining structures §7.5). Tier 3 closes BTD6 decode-status item 4.
Tiers 4–5 are quick panel walks and a regression sweep.

**Already machine-verified — don't burn time re-proving:** boot, migrations,
all 2,022 BTD6 menu embeds in-limits, the grounding *facts* for every Tier-3
question below (re-probed against source today with `scripts/btd6_probe.py`),
chain-service audit round-trip, Help render-path characterization (28 tests),
settings taxonomy invariants, CI mirror 8,840 green. What the machine cannot
see: the **model actually using** the tools/facts, real button clicks at
Discord's pace, image quality, and whether the game *feels* right.

---

## Step 0 — verify the build AND the data (learned live, 2026-06-10 evening)

- [ ] `!btd6 status` shows **game version 55.1** and no **⚠️ Data drift**
      field. *(Corrected diagnosis:* the first walk's "(55.0)" stamps were
      **not** a stale code deploy — auto-deploy worked; the Railway log shows
      the new container serving them. Production runs
      `BTD6_DATA_BACKEND=postgres`, so BTD6 fixtures come from the
      `btd6_data_blobs` table, and **data PRs never refresh that store** —
      it served the old blobs until `!btd6ops seed-data` ran. Since PR #676,
      seed-data **applies immediately** (no restart) and both boot logs and
      `!btd6 status` surface the drift loudly.)*
- [ ] After any `!restart`: confirm the bot actually comes back. On the old
      build `!restart` exited 0 and Railway (on-failure policy) never
      relaunched it — fixed by the restart exit-code change (PR #675):
      `!restart` now exits nonzero and relaunches.

### Live-walk deltas (first pass, 2026-06-10 evening — fixes in PR #675)

- ✅ **Tier 1.1 PASSED:** rounds 1–77 = $84,632.40 / cumulative $85,282.40
  with the $650 start (maintainer screenshot) — correct.
- 🔧 **Meta-questions** ("what (kind of things) do you know about btd6",
  "list all the things you know about btd6", "what can you tell me about
  btd6"): were floored to the version-stamped refusal. Now answered
  **deterministically** — expect a "**What I know about BTD6**" summary
  (domains + counts + explicit gaps) even when the model freelances.
- 🔧 **"tier 4 elite lych" / "base HP of Lych per tier":** boss resolution is
  qualifier-tolerant now and per-tier HP grounds (T1 14,000 → T5). Elite HP
  is **not in the dataset** — expect the bot to say the base figures are the
  verified part and treat your +125% as your premise.
- 🔧 **Crosspath nonsense** ("you can only upgrade ONE path", "0-2-4 is
  invalid"): the guidance block now carries the validity rules — re-ask a
  0-2-4 question and report any repeat of the one-path claim.
- ⏳ **"five 0-2-4 dart monkeys by round 60 — what's left?"** (cash − N×cost
  composition): genuinely the next AI family (**§7.5**, sequenced after this
  eval) — these screenshots are its acceptance cases. Expect honest partial
  answers until §7.5 ships, but no more invented game rules.

## Tier 1 — AI model loops (only you can test these; they gate AI §7.5)

The sandbox has no provider key, so every "model loop" below has been tested
deterministically but never end-to-end with a live model. Until this tier is
walked, AI expansion stays gated (Q-0048 posture; §7.5 multi-entity comparison
is explicitly sequenced *after* this check).

### 1.1 Round-cash tool — default profile (PR #612, Q-0043)

No setup needed (the tool is offered under the default profile).

- [ ] Ask the bot (mention it as usual):
      `how much cash do I earn from round 50 to round 60?`
      **Expect:** **$19,840** — inclusive of BOTH endpoints (Q-0043).
      **Report if:** $16,824 appears (that's the old exclusive subtraction bug)
      or any other number, or the model answers without a real figure.

### 1.2 Orchestration profiles + Phase 4 workflow (PRs #619, #634)

The plan→execute→verify workflow only activates under a BTD6-grounded
profile, so first flip one channel onto it:

- [ ] `!aimenu` → **Tools** button → set the **channel** profile to
      **BTD6 grounded**. **Expect:** the picker writes through cleanly and the
      panel shows the new profile.
- [ ] Still in Tools: run the **dry-run analyzer** on that channel.
      **Expect:** resolved profile = `btd6_grounded`, the offered list is only
      BTD6 factual tools (reference / rounds / costs / paragon), withheld tools
      carry reason codes, loop budget shows 3 hops / 4 calls.
- [ ] In that channel ask:
      `I want to afford the upgrade — how much cash from round 50 to 60?`
      **Expect:** a worked answer built on the same $19,840 (the workflow's
      typed answer-with-evidence — it should *explain* the calculation, not
      just drop a number).
- [ ] Optional: try **BTD6 grounded (strict)** — it forces a tool on *every*
      turn, so even `hi` should visibly consult a tool (or refuse social
      chatter awkwardly). That's expected pre-Phase-4-intent-analysis behavior;
      just note how it feels.
- [ ] Optional: **No tools (conversational)** — ask a BTD6 stats question;
      the model must hedge instead of inventing numbers.
- [ ] Set the channel back to **Compatible (today's behaviour)** (or leave
      `btd6_grounded` on a dedicated BTD6 channel if you like it) and confirm
      a normal question still answers.

### 1.3 The three self-awareness tools (PR #639, Q-0047)

Ask each as a natural question; the instruction stack routes them to
read-only tools. If you can, ask once as yourself (owner) and once from a
regular member account — answers are **audience-tiered at construction**.

- [ ] `what can you do here?` / `what tools do you have?`
      **Expect:** a capability catalog with one-line purposes. As a regular
      member, higher-tier tools are **counted, never named**. As owner you see
      more.
      **Report if:** it invents tools, or names owner-only tools to a member.
- [ ] `why didn't you reply to my last message?`
      **Expect:** the effective mode/source/min-level/cooldown for that
      channel + you. Precedence trace and other-user history are admin-only.
- [ ] `what BTD6 data do you know?`
      **Expect:** a domain inventory (towers/heroes/paragons/rounds/…) **with
      explicit unsupported gaps**, versions matching "55.1".

### 1.4 BTD6 grounding routing — the Navarch class (PRs #662, #668)

These reproduce the live screenshot miss that started the whole fix. Phrase
them exactly — the *sloppy* forms are the point.

- [ ] `does the navarch of seas paragon make coins` (article dropped — on
      purpose). **Expect:** **yes — $3,200 at the end of each round**
      (degree-independent), likely plus the Trade Empire +$10/+$20 per-
      Merchantman lines. **Report if:** "no income" (the original bug) or a
      hedge with no figure.
- [ ] **Follow-up in the same channel, as the next turn:**
      `does it make coins at the end of the round?`
      **Expect:** still about the Navarch ("it" carries over — PR #668).
      **Report if:** the bot loses the subject or answers about something else.
- [ ] Bare shorthand: `navarch` ... `does it earn money?` — same expectation.
- [ ] `what's the best paragon?` / `what's the strongest tower?`
      **Expect:** a grounded ranking-style answer (roster facts), not a
      zero-fact freelance.
- [ ] `what does the Mini Sun Avatar do?`
      **Expect:** routes to its **owner** — Sun Temple (Super Monkey 4-0-0),
      with minion stats. Variants worth one try each: `Crushing Sentry`, `UAV`.
- [ ] `what does the pouakai do?` — typed **without** the diacritic.
      **Expect:** grounds to the Pouākai beast normally.

### 1.5 AI policy surfaces still sane

- [ ] `!ai why-no-response` after any ignored message — explanation matches
      reality.
- [ ] `!ai status` / `!ai diagnostics` — render, no errors.

---

## Tier 2 — Mining & games economy (your balance feel gates structures §7.5)

The whole stack below was re-tuned by construction, never by play (the
audit's words). Play it for a few minutes and judge **pace**: coins/hour,
XP soft-cap feel, gear wear rate.

### 2.1 The new panel surface (PR #665)

- [ ] `!minemenu` — **Expect** these buttons: ⛏️ Mine · 🌲 Harvest ·
      🗺️ Explore · 📦 Inventory · 📊 Stats · 🔨 Build · 🔧 Workshop ·
      ⬇️ Descend · ⬆️ Ascend · 🛒 Market · **🧰 Gear** (new) ·
      **📖 Recipes** (new) · 🧍 Character.
- [ ] **🧰 Gear** — equipped items per slot (pickaxe/axe/light/weapon/armor)
      with durability bars; equip/unequip from the panel works.
- [ ] **📖 Recipes** — browsable recipe list; entries match what `!craft`
      actually accepts (they're catalog-reconciled under a lint now — a
      mismatch is a real bug).
- [ ] **📦 Inventory** — renders as a **PIL image card** (falls back to an
      embed only if image rendering fails). Judge the look — Q-0076 chose
      both cards, so visual quality is the acceptance bar.

### 2.2 The economy loop end-to-end (PRs #661, #663–#665, #667)

- [ ] `!mine` a few times → `!sellall` → **Expect:** coins arrive; totals add
      up.
- [ ] `!fastmine` (new) — a quicker mine action; cooldowns feel right?
- [ ] `!market` → buy something you **can't afford** → **Expect:** clean
      rejection, **no coins move, no item appears** (purchases are atomic now
      — a half-applied purchase is the exact bug class #661 killed).
- [ ] Buy something you can afford → coins down, item in inventory, one
      transaction.
- [ ] Fuzzy names: `!equip dlantern` resolves to *diamond lantern*
      (once you own one); `!craft` accepts close-enough names.

### 2.3 Progression: the MAGMA run (PR #665 — was impossible before)

- [ ] Get a **diamond lantern**: craft it (📖 Recipes shows the cost) or buy
      it at `!market` (200 coins).
- [ ] `!equip diamond lantern` → `!descend` repeatedly.
      **Expect:** you reach **🌋 the Magma core** (MAGMA). Before #665 no
      light unlocked it — if you're blocked at Deep with the diamond lantern
      equipped, that's a regression.
- [ ] `!minestats` — **Expect:** 🎮 Game Level (the new shared game-XP track),
      **Deepest** depth record showing your run, totals sane.
- [ ] `!explore` down deep — deeper biomes give richer finds; light-gated
      finds appear with the lantern.

### 2.4 Gear wear in duels (PR #665, Q-0054 closed)

Needs a second person (or alt).

- [ ] Note durability in 🧰 Gear → `!dm @someone` and finish the duel →
      re-open 🧰 Gear. **Expect:** equipped combat gear lost durability.
      Judge the wear *rate* — too punishing / too free is a tuning finding.
- [ ] `!repair` at the 🔧 Workshop fixes it (costs what the panel says).

### 2.5 Game-XP boards + character card (PRs #665, #610)

- [ ] `!leaderboard gamexp` and `!leaderboard crafting` (new boards) render
      with your fresh activity. `!leaderboard` with no argument shows the
      category picker including both.
- [ ] `!character` — the **PIL stat card** image: position, gear, coins, net
      worth, game level. (Q-0076 again — judge the look.)
- [ ] Crafting/repairing at the Workshop awards crafting XP **atomically
      with the action** (the board moves right after).

---

## Tier 3 — BTD6 knowledge spot-check (closes decode-status item 4)

Use `!btd6 ask <question>` for the deterministic path (works without AI),
and/or the natural-language mention path. The grounding facts behind every
expectation below were re-verified against source today.

- [ ] `!btd6 ask what does the Orca do?` — **Expect:** Beast Handler 4-0-0
      (top path), **$12,500**, "drags all but the very largest Bloons into
      the depths… can drag down ZOMGs at max Beast Power".
- [ ] `!btd6 ask how much does Monkey Wall Street make per round?` —
      **Expect:** **$4,000/round income; bananas worth $70** (0-0-5 Farm).
- [ ] A Village check, e.g. `!btd6 ask what does Monkey Intelligence Bureau do?`
      — **Expect:** the MIB description (lets affected towers pop any bloon
      type); discounts questions resolve for the x-2-x line.
- [ ] **Source label:** answers and menu embeds cite **"BTD6 game data 55.1"**
      — not "curated" / not a container path.
- [ ] `!btd6menu` → a **Pro/tier view** for Sun Temple or Spectre —
      **Expect:** 🌀 **Effects** and 🤖 **Minions** sections render (new in
      #658).
- [ ] `!btd6menu` → the **modes panel** — **Expect:** the new 📋 rules lines
      per mode (was dark data before #655).
- [ ] `!btd6 diagnostics` — **Expect:** it **sends** (this exact command used
      to 400 on message length).
- [ ] One banana-economy question, e.g.
      `!btd6 ask how much does a Monkey Bank hold?` — **Expect:** bank
      capacity/interest as concrete numbers (shipped with #653).
- [ ] One bloon question, e.g. `!btd6 ask what is a DDT?` — the deterministic
      bloon branch (new in #658) answers without AI.

---

## Tier 4 — New panels & settings

### 4.1 Settings hub (PRs #640, #654, #672)

- [ ] `!settings` — **Expect:** a curated list of ~**12 actionable groups**
      (not the old blind 28-subsystem list), **no empty pages**; if a page
      paginates, navigation works past 25 entries; groups routed off in this
      guild show **⛔** but stay clickable.
- [ ] The **proof_channel** group exists (new in #672) — open it, bind a
      channel as the proof channel.
- [ ] **BTD6 group** (Q-0064, #654): `btd6.version_announce_channel` is a
      proper channel binding; the **CT group** setting is a guided
      parse → preview → confirm flow, not a raw text field.
- [ ] `!btd6ops announcechannel #somewhere` — **Expect:** it warns that the
      binding shadows it (the binding wins now).

### 4.2 Proof channel / prizes (PR #672)

- [ ] **Before binding** (or after unbinding): `!prizemenu` behaves exactly
      as it always did — the legacy "channel named `proof`" fallback carries
      it. **Report if** anything about prizes changed while unbound.
- [ ] **After binding** a different channel in Settings: the bound channel
      wins over the name-`proof` one.

### 4.3 Server-management hub subpanels (PR #656; preview rebuilt in #671)

- [ ] `!servermanagement` (aliases `!servermenu` / `!guildmenu`) —
      **Expect** buttons: 🛡️ Moderation · 📺 Channels · 🎭 Roles ·
      🧹 Cleanup · 🧩 Setup · **🔓 Access Map** (new) · **👁 Help Preview**
      (new) · 🔄 Refresh.
- [ ] **🔓 Access Map** — per-feature access across the axes
      (command-access / routing / governance). Pick a **declared tier** to
      simulate — the output must carry the explicit **simulation label**
      (§16.4): it's a preview, not live permission change.
- [ ] **👁 Help Preview** — preview Help as a regular user vs as admin:
      the user view advertises fewer entries (governance-denied features
      render as **Hidden**, not "locked"); if you ever hand-edited overlay
      rows, orphaned ones are listed here (and only here).

### 4.4 Chain panel modals (PR #671 — service-verified, never human-clicked)

In a throwaway channel, via `!chainmenu`:

- [ ] **Create** a chain → works, audit-clean.
- [ ] **Create again** on the same channel → clean "already exists" rejection
      (nothing written).
- [ ] **Set limit** → confirm; **set the same limit again** → "no change"
      message (and no pointless audit row).
- [ ] **Remove limit**, then **Delete** the chain → both work.
- [ ] Subtle one if you still have an old channel that ever had ONLY a word
      limit (no chain): creating a chain there must **preserve** the limit —
      resetting it to 0 was a latent bug #671 fixed.

### 4.5 Help (PRs #657, #659, #671)

- [ ] `!help` as **admin** vs as a **regular member** (or via 👁 Help
      Preview): admin sees more; member-hidden features are absent, not
      "locked"-labeled.
- [ ] Typed routes: `!help economy`, `!help games`, `!help admin` — each
      lands on the right hub panel; a subsystem hidden for you behaves as
      **not found** (it shouldn't leak existence).
- [ ] Note: the overlay (hide/rename) has **no editor UI yet** — that's the
      next Help slice. Today it's only visible through Help Preview; nothing
      for you to click-edit.

---

## Tier 5 — 60-second regression sweep

- [ ] `!spotlight` (or `!activity`) — server dashboard renders;
      member count line is sane.
- [ ] `!hub` and `!server` do **NOT** open Spotlight anymore (aliases
      dropped on purpose — they should fall through to whatever owns them
      now / unknown-command).
- [ ] `!blackjack 50` and `!rps 50` — play one hand each; the 🔁 Play-again
      replay row still works.
- [ ] `!leaderboard` classic boards (xp / coins / mining) unaffected.
- [ ] `!platform consistency` — CLEAN (or only known-triaged sections).

---

## Reporting

Drop findings in chat as they come — "X should be Y", screenshots welcome.
Each item is pre-mapped to its owning PR above, so a finding routes straight
to a diagnosis. When the tier-1 items pass, say so explicitly: **that
sign-off is what un-gates AI §7.5** (and the audit's "do not expand AI yet"
posture); tier 2's verdict un-gates mining structures pricing.
