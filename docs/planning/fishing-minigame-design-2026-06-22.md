# Plan — Fishing minigame: the interactive catch loop (sim-backed design)

> **Status:** `plan` — design exploration 2026-06-22, owner-directed. Answers the **Q-0175 open
> question** "Catch mechanic: deterministic roll, or a minigame? what determines success?" with a
> **simulation** (`tools/sim/fishing_minigame_sim.py`) rather than a guess. The owner is the
> designer and is "still finalizing the idea — we can go many directions"; this captures a
> recommended direction + the data behind it + the choices that are genuinely his to make.
> Builds on `docs/planning/fishing-open-world-expansion-plan-2026-06-18.md` (the Phase-1/Phase-2
> vision). Verify against source + the owner before building.

## The ask

> "Currently it's prefix commands only, no buttons… it should become an interactable menu leaning
> toward a real minigame feeling. Create and run a simulation to find the most fun way to play it.
> I was thinking `cast line → waiting…, waiting…, bite! → reel in`, but I'm not sure that's best.
> What's a correct time for the fish to bite, how long can the reaction window be, what's the best
> rod-upgrade system? Add a boat (already planned) — fishing from the boat grants deepwater fish vs
> the shoreline. The menu should feel like you can do multiple things, be fun and rewarding, but
> also fair." — owner, 2026-06-22

## The one insight that drives everything: the Discord latency chain

A reaction minigame on Discord buttons is **not** a reflex test, and trying to make it one makes it
unfair. When the bot edits a message to `🐟 BITE! reel now`, the real timeline is:

```
bot edits message ──L_down──▶ player's client renders it
                              ──R──▶ player perceives + clicks the button
                                     ──L_up──▶ click reaches the bot
```

The bot can only measure the **whole round trip** `L_down + R + L_up` against whatever window `W`
it set. Even a perfect-reflex player spends ~0.5–1.3 s of that budget on network + render they
can't control. So:

- **Sub-second "twitch" windows are unwinnable over Discord** — they fail players for their
  *connection*, not their skill.
- **What a reaction window actually tests is presence / attention** — are you watching, and can you
  hold your nerve. That is the correct thing to design around, and it's still fun and skill-y.

The simulation (`tools/sim/fishing_minigame_sim.py`) models this chain explicitly across 120k
simulated casts by a varied player population (reaction time, network latency, patience,
impulsivity all vary). Every recommendation below is an output of that model. **Re-run it after the
minigame ships** with real measured bite→click round trips to re-tune the `NET_*` / `RT_*`
constants — they are the load-bearing assumption.

## What the sim found

### 1. The mechanic: `cast → wait → BITE → reel` is right — add a reel-fight for trophies

| mechanic | catch | unfair-fail | agency (skill matters?) | lag-unfairness (bad conn punished?) |
|---|---|---|---|---|
| `roll` (today) | 100% | 0% | **+0.00** (none — a slot machine) | +0.00 |
| `bite_reel` (your idea) | 86% | 0% | +0.05 | −0.06 |
| `tension` (bite + reel-fight) | 71% | 0% | **+0.32** | −0.30 |

The current deterministic roll has **zero agency** — skill is statistically uncorrelated with
success. `bite_reel` adds real agency cheaply. `tension` (a short reel-fight after the bite) adds
the *most* agency and reward texture but also the most failure. **Recommendation: a hybrid** — a
single reel for ordinary fish (keeps shore relaxing), and the reel-fight only for big/trophy fish
(earns the dopamine, scales risk with size). Note `lag-unfairness` stays near zero at a generous
window — the design is fair to bad connections, which is the whole point.

### 2. Reaction window: **~2.5 s base** (it's a presence check, not a reflex test)

Sweeping `W` on the **starter rod** (worst case), the unfair "lag ate it" failure rate:

```
  W=0.5s  ████████████████████████   49.8%   ❌ unwinnable
  W=1.0s  █████···················   10.6%   ⚠️ punishes connections
  W=1.5s  █·······················    2.1%   ✅ fair knee
  W=2.0s  ························    0.5%   ✅
  W=2.5s  ························    0.2%   ✅ recommended
  W=5.0s  ························    0.0%   (diminishing — dilutes tension)
```

**Recommendation: 2.5 s base window on shore.** Below ~1 s the network alone blows it; the unfair
curve flattens near zero at 2–2.5 s; longer just dilutes tension. Rods *add* to this (§4), so a
weak connection on a decent rod is fully comfortable — that's where the "gear helps, isn't
required" budget should go.

### 3. Bite timing: randomised **3–6 s, with a ~1.5 s floor + a fake-out**

Longer waits don't reduce catch rate much, but they erode attention and bore the player
(`sec/catch` climbs, fair-misses creep up past ~9 s). The sweet spot is short enough to stay
engaged, long enough to build anticipation:

| mean wait | feel |
|---|---|
| 2 s | too fast — no anticipation |
| **3–6 s** | **✅ sweet spot — anticipation without boredom** |
| 9 s+ | dragging / AFK-inducing |

**Recommendation: randomised 3–6 s, memoryless** (never feels scripted), with a **hard ~1.5 s
floor** so it's never instant — the floor *is* the anticipation. Add an optional **fake-out**: a
tiny shake ~0.5 s before the real bite. Reeling on the fake-out scares the fish (a `premature_fail`)
— this turns dead waiting time into a "hold your nerve" skill and gives better rods a real job
(forgiving early clicks, the `premature_grace` knob).

### 4. Rod upgrades: a 5-tier ladder turning **four knobs**, none of which gate basic success

| rod | window+ | bite× | rarity-pull | escape-resist | catch | big-fish | reward/cast |
|---|---|---|---|---|---|---|---|
| starter | +0.0s | 1.00 | 1.00 | 0% | 71% | 0% | 3.3 |
| bronze | +0.4s | 0.95 | 1.10 | 10% | 77% | 0% | 3.9 |
| silver | +0.8s | 0.88 | 1.25 | 22% | 81% | 0% | 4.7 |
| gold | +1.2s | 0.80 | 1.45 | 35% | 84% | 0% | 5.5 |
| diamond | +1.7s | 0.70 | 1.70 | 50% | 87% | 0% | 6.5 |

The starter rod **still catches fine** — upgrades make fishing *nicer and more rewarding*, never
*possible*. Each tier turns four distinct knobs so an upgrade always *feels* like something:

1. **`window_bonus`** (+0 → +1.7 s) — the headline **fairness** upgrade; the first thing a new
   player feels improve.
2. **`bite_speed`** (×1.0 → ×0.7) — faster bites → more casts/min; the **pacing** upgrade.
3. **`rarity_pull`** (×1.0 → ×1.7) — biases catches to the big end of your band; the
   **reward-quality** upgrade (the reason to chase tiers once you catch reliably).
4. **`escape_resist`** (0 → 50%) — matters in the reel-fight / deepwater; the **risk-mitigation**
   upgrade that makes the boat viable (§5).

**Reuse, don't reinvent:** pair this rod ladder (the existing `bronze…diamond` tier names) with the
existing `game_xp` fishing **level**. Two orthogonal axes — **level = *what* you can catch (size
bands), rod = *how well / which-within-band* you catch it.** No parallel progression system.

### 5. Boat / deepwater: a genuine **choice**, not a strict upgrade

Reward/min and big-fish rate by venue and rod (the `tension` mechanic, where the boat's fights bite):

| rod | venue | big-fish | escape-loss | reward/min |
|---|---|---|---|---|
| starter | shore | 0% | 24% | **17.8** |
| starter | deepwater | 7% | 54% | 7.5 |
| diamond | shore | 0% | 14% | 51.4 |
| diamond | deepwater | **35%** | 50% | 38.6 |

On the **starter rod**, deepwater's long waits + high escape make its reward/min *worse* than
relaxed shore fishing — a new player is happy on shore and **isn't forced out**. With a **good rod**
(escape-resist + rarity-pull), deepwater is the only place to get big-fish/trophy rates — so the
boat becomes the **aspirational** venue whose value you *unlock by upgrading*. That's exactly the
"optimization, not a gate" shape the expansion plan asks for. Concretely:

- **Deepwater = exclusive species** (size-ranks 13–21 + boat-only flavour fish). The dex eventually
  *requires* going out — but only when you're ready.
- **Boat-only fish are uncatchable from shore** (shore caps ~rank 12) — the owner's "deepwater fish
  vs shoreline" split.
- **Escape-resist gates deepwater viability**, so the rod ladder and the boat reinforce each other
  instead of being two separate grinds.

## Recommended design (the synthesis)

Your `cast → wait → BITE → reel` instinct is **right**. Three data-driven refinements:

1. **The window is a presence check, tuned generous (~2.5 s).** Sell it as "stay sharp / hold your
   nerve", not "fastest finger" — over Discord it can't be the latter without being unfair.
2. **A reel-fight only for the payoff fish.** Small fish land in one tap (shore stays relaxing);
   trophies take a few taps and can fight free (earns the reward). Risk scales with fish size, so
   the loop doesn't go stale.
3. **The menu is a place, not a button.** One persistent fishing/boat panel (mirroring the
   blackjack view pattern — `discord.ui.View`, author-restricted, disable-on-timeout) with several
   actions so "you can actually do multiple things":

   | action | what it does | why |
   |---|---|---|
   | 🎣 **Cast** | the core wait→bite→reel loop | the heartbeat |
   | 🪱 **Bait** | optional consumable biasing bite rarity/speed for N casts | a coin/resource sink + a second knob beside the rod |
   | 🎒 **Tackle** | swap rod + the Q-0175 fishing-gear loadout preset | progression, made visible |
   | 📖 **Fishdex** | collection / records (exists today) | the completion goal |
   | ⛵ **Set sail / Dock** | toggle shore ↔ deepwater | the venue choice |
   | 🍳 **Cook** | already shipped (#1289) — surface it here | closes the catch → eat loop |

### Starting numbers (tune against live telemetry once shipped)

| knob | shore | deepwater (boat) |
|---|---|---|
| base reaction window | 2.5 s | 2.0 s (rod expected) |
| bite wait (randomised) | 3–6 s, 1.5 s floor | 6–12 s, 3 s floor |
| fake-out before bite | ~0.5 s shake | ~0.5 s shake |
| size-rank band | 1–12 | 13–21 + boat-only |
| base escape (reel-fight) | 8% | 22% |
| reel-fight taps | 1 (trophy: up to 3) | 2–4 by size |
| rod window bonus | +0 → +1.7 s across 5 tiers | same |

## Other ideas surfaced (the owner invited these)

- **Bait as the second economy knob** — fish are now sellable + cookable (#1289), so bait gives the
  coins somewhere to go *and* a pre-cast decision ("spend bait on this deep trip?"). Low-risk, high
  texture. *(captured as an idea — see `docs/ideas/`)*
- **Fake-out bites** — converts waiting from dead time into a nerve-holding skill; makes the
  `premature_grace` rod knob meaningful. Cheap, big feel-payoff.
- **Weather / time-of-day modifier** — a global daily bias (e.g. "storm: rare fish biting,
  shorter windows") gives a reason to fish *today* and a shared talking point, reusing any existing
  daily-seed. Optional, Phase 2-ish.
- **Trophy records per species** (biggest caught) — a cheap long-tail goal layered on the existing
  catch-log; "personal best" beats raw counts for retention.
- **Line-snap as a soft-fail, not a hard-fail** — an escaped fish could leave a clue ("a *big* one
  got away") to bait the next cast rather than just denying the reward — keeps frustration low.

## Owner decisions (resolved 2026-06-22, via AskUserQuestion)

The owner answered the design-feel questions — these are now **decided** and bind the build:

1. **Mechanic depth → HYBRID.** Single reel for ordinary fish (shore stays relaxing); a short
   reel-fight only for big/trophy fish. (The sim's recommended option — best fun-per-complexity.)
2. **Failure stakes → THE FISH GETS AWAY.** A missed reel = no catch (real stakes; makes rods +
   attention matter). Pair with low-stakes "a big one got away" clues to keep frustration down
   (Other-ideas list) rather than an empty, punishing feeling.
3. **Pacing → SOFT ENERGY/COOLDOWN.** Add light pacing so fish can carry **more coin value** than
   today's deliberately-cheap unpaced rate (#1289). Ties into the existing energy/cook loop — design
   the cooldown so cooking-for-energy and fishing pace each other rather than two separate meters.
   *(Re-tune the #1289 fish sell values upward once the cooldown lands — flag for the build PR.)*
4. **Bait → LATER LAYER.** Ship the core cast/reel/boat loop first; add bait as a follow-up economy
   knob once the base feels good. (Keeps v1 scope tight.)
5. **Phase order → shore minigame first** (Phase 1), boat/deepwater second (consistent with the
   expansion plan's phase split; confirm at build time).

### What this means for the build (v1 scope)

- A `views/fishing/` panel (mirroring `views/blackjack/solo_view.py`): 🎣 Cast · 🎒 Tackle · 📖
  Fishdex · 🍳 Cook now; ⛵ Set sail and 🪱 Bait are **Phase 2 / later**.
- Cast loop: randomised 3–6 s wait (1.5 s floor) + fake-out → `BITE` → ~2.5 s reel window (rod adds
  to it). Ordinary fish: one reel, miss = it gets away. Trophy fish (top size-ranks): the reel-fight,
  each fumbled/escaped tap = it gets away.
- A **soft energy/cooldown** on casting (reuse the mining energy seam), and **raise fish sell values**
  off the #1289 floor to match the new pacing.
- Rod tiers (`bronze…diamond`) turning the 4 knobs in §4; level (`game_xp`) still gates size-bands.

## Verification / rollback

Docs + a read-only stdlib simulation only — fully reversible, touches no runtime/money/safety seam.
Reproduce any number here with `python3.10 tools/sim/fishing_minigame_sim.py`. The implementation
(when greenlit) is an additive game feature on the existing `fishing_workflow` + a new
`views/fishing/` panel mirroring `views/blackjack/`; ADR-002 (game state not restart-safe) applies.

## Source anchors

- `tools/sim/fishing_minigame_sim.py` — this sim (the numbers above).
- `docs/planning/fishing-open-world-expansion-plan-2026-06-18.md` — the Q-0175 Phase-1/2 vision.
- `disbot/services/fishing_workflow.py` · `disbot/utils/fishing/` — the current roll + reward seam.
- `disbot/views/blackjack/solo_view.py` — the interactive-view pattern to mirror.
- `disbot/data/fishing/fish.json` — the 21-fish dataset (where boat-only species would append).
