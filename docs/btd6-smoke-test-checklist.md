# BTD6 Bot — Smoke-Test Checklist

A hands-on script for testing the bot's BTD6 **capabilities** and **limitations**
after a deploy. It covers everything landed in the data/grounding work of
PRs #500–#505 plus the earlier upgrade-detail/faithfulness work, and — just as
importantly — the questions the bot should **honestly decline** rather than
fabricate.

> **Deployment first.** These behaviours are baked into committed data +
> instructions, so they only take effect once the **live bot redeploys** with the
> merged code. If a "✅ expect" answer below is wrong on the live bot, first
> confirm the deployment is current — several mid-session screenshots showed the
> bot estimating because it was still running pre-merge code.

> **How to read this.** ✅ rows are *capabilities* — the bot should give the exact
> grounded value. 🚫 rows are *limitations* — the bot should say it doesn't have
> that data (and **not** invent a number, name, or list). Values are standard
> **Medium** economy, no income towers, current game version.

---

## 0. The faithfulness probes (run these first — they caught every bug)

The recurring failure this whole session was the model **inventing numbers and
calling them "verified."** These probes target that directly:

| Ask | ✅ Expect | 🚩 Red flag |
|---|---|---|
| "how many maps have water" — then reply **"try again"** 3× | The **same** answer every time (67 water / 19 land) | Different counts each retry (it gave 73→77→75→76→77 before the deterministic floor) |
| "how much cash do you earn on round 40" | **$521** (this round) | "$14,600" or any "~$X / typical" estimate |
| Any answer that says **"verified from the tool"** | Only when it matches the tables below | "verified" attached to a wrong number |

If a count/list answer is unstable across retries or labelled "verified" while
wrong, that's the model bypassing its grounding — note it for the faithfulness-
guard work (the systemic open item).

---

## 1. Per-round cash  (PRs #500 · #502 · #504)

| Ask | ✅ Expect |
|---|---|
| "how much cash do you earn on round 40" | **$521** this round (the *per-round* figure, **not** cumulative) |
| "how much cash on round 26" | **$333** |
| "how much cash on round 50" | **$3,016** |
| "how much cash on round 1" | **$121** |
| "cumulative cash by round 80" | **~$98,254** (running total incl. the $650 Medium start) |
| "how much do you earn from r50 to r60" | **$16,824** ( = cumulative 55,134 − 38,310 ) |
| "how much from r70 to r80" | **~$26,939** |
| "how much money total by round 140" | **~$351,267** |

| 🚫 Limitation | ✅ Expect it to decline |
|---|---|
| "how much cash on round 50 on **Hard** / with **Half Cash**" | Only standard/Medium is grounded — should flag difficulty/Half-Cash isn't modelled, not give a number |
| "how much cash on **round 200**" | Rounds 1–140 only — should say it's out of range |
| "how much does a **0-2-0 farm** add per round" | Tower income only if that tier is grounded; otherwise decline (don't estimate) |

---

## 2. Maps — counts & lists  (PR #505)

| Ask | ✅ Expect |
|---|---|
| "how many maps are there" | **86** — 26 Beginner, 25 Intermediate, 22 Advanced, 13 Expert (**not** 89) |
| "how many maps have water" | **67 have water, 19 land-only** |
| "list all maps with water" | the 67, grouped by difficulty |
| "list the land-only maps" | the **19** (incl. Monkey Meadow, Alpine Run, Cornfield, Mesa, Tricky Tracks, Workshop…) |
| "which maps have removables" | the **18** (see §3) |

| 🚫 Limitation | ✅ Expect |
|---|---|
| Look for **Blons / Base Editor Map / Protect the Yacht** in any list | They must **not** appear — non-player (`IsStandard=False`) maps are filtered |

---

## 3. Map removable obstacles  (PR #503 — 18 maps, wiki-sourced)

| Ask | ✅ Expect |
|---|---|
| "what removable obstacles does **Cargo** have" | Two trucks (line-of-sight blockers), removable **only after round 39**, opens placeable terrain |
| "does **Cornfield** have removables" | Thirteen corn patches (LoS blockers) |
| "what's removable on **Quiet Street**" | Two frozen lakes (→ water terrain) + five cars (LoS, → placeable terrain) |
| "removables on **Encrypted**" | Four rock-debris groups, each opens terrain exclusive to one tower category |

| 🚫 Limitation | ✅ Expect |
|---|---|
| "how much does it **cost** to remove the trucks on Cargo" | Decline — removal **costs** aren't in the data set |
| "what removables does **Monkey Meadow** have" (a map not in the 18) | Say it doesn't have that map's removable detail — **don't** guess |

---

## 4. Buffs — stack caps  (PR #501)

| Ask | ✅ Expect |
|---|---|
| "what does **Trade Empire** do" | +$10/round per Merchantman, +$20/round per Favored Trades, +1 dmg (incl. vs Ceramic/MOAB), **stacks up to 20** |
| "how many times does the 0-0-4 Buccaneer **sellback** buff stack" | Up to **3** (+4% each → +12%) |

| 🚫 Limitation | ✅ Expect |
|---|---|
| "how many times does **Pirate Lord** / **Elite Defender**'s aura stack" | It applies once — should **not** invent a stack count |

---

## 5. Buffs — temporary triggers  (PR #501)

| Ask | ✅ Expect |
|---|---|
| "what's the **Desperado Enforcer**'s buff" | +16 range & ×0.6 attack speed **for 15 s when a life is lost** (60 s cooldown); leaked bloons give **2× their value as cash** |
| "what does the **start-of-round** buff (Spike Factory / Engineer) do" | ×0.25 attack cooldown **at the start of each round** |

> Watch the **units**: Desperado must read **seconds** (15 s / 60 s), the
> start-of-round buff must read **each round** — never the reverse. (Same field
> name, two units; the `trigger` disambiguates.)

---

## 6. Upgrades — deep detail & name-collision faithfulness  (earlier session)

| Ask | ✅ Expect |
|---|---|
| "Prince of Darkness minion pierce" | **1** (lives on the Reanimate attack, not the main projectile) |
| "what does **PMFC**'s ability do" | Its actual ability detail |

| 🚩 Faithfulness probe | ✅ Expect |
|---|---|
| "pmfc abilities" | Name PMFC's real ability — must **not** substitute "Prince of Darkness" (a past collision bug) |

---

## 7. Not-yet-implemented (should decline honestly)

| Ask | ✅ Expect |
|---|---|
| "how far does Heli Pilot's **MOAB Shove** push each blimp class" | Decline — the MoabShove push values are decoded but **not rendered yet** (pending semantics confirmation) |
| "per-level stats for **\<hero\>** at level 7" | Per-level hero stats aren't modelled — decline |
| "what bloons is **\<X\>** immune to" beyond camo/lead/black/white/purple | Decline beyond the modelled immunities |

---

## Quick expected-value reference (verified against committed data)

- **Rounds:** r1 $121 · r26 $333 · r40 $521 · r50 $3,016 · r80 $1,400.2 · r140 $1,307.68; cumulative r80 ~$98,254 · r140 ~$351,267.
- **Maps:** 86 total (26/25/22/13) · 67 water · 19 land-only · 18 with removables.
- **Buffs:** Trade Empire stacks ×20 · sellback ×3 · Desperado lives-lost 15 s / 60 s cooldown / +16 range / ×0.6 speed / 2× leak cash · start-of-round ×0.25 each round.
- **Excluded non-player maps:** Blons, Base Editor Map, Protect the Yacht.
