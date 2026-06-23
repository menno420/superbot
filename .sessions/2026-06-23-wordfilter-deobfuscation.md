# 2026-06-23 — Obfuscation-resistant word filter (beat Sapphire's content filter)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the deliberate final step.
> Owner-directed (chat: *"whatever Sapphire does a lot better than us, find a way to improve that
> even more and add it to the bot"*). PR #1394 → auto-merges on green CI (Q-0123/Q-0191).

## Arc

A Sapphire-vs-our-bot comparison conversation. The owner named **moderation** as the one area
Sapphire clearly leads, then corrected me twice that we already had pieces (cleanup ships a
prohibited-words filter; reaction roles already shipped). Inspecting the cleanup filter: the match
is a naive `re.compile(rf"\bword\b", IGNORECASE)` — the same keyword filter Sapphire / Carl / MEE6
all use, walked straight through by `b a d`, `b.a.d`, `b4d`, `ｂａｄ` (fullwidth), `bаd` (Cyrillic),
and invisible-character insertion. The owner then flagged the specific evasion their friend used:
invisible characters that "pass some advanced bots but not all."

The non-duplicative, genuinely-beat-Sapphire move: make the **existing** filter
**obfuscation-resistant** rather than add a second one.

## Shipped (PR #1394)

- **`disbot/utils/text_obfuscation.py`** (new, pure, stdlib-only) — `deobfuscate()` +
  `find_obfuscated_match()`. Normalizes a message to *what a human reads* and matches with word
  boundaries: NFKD compatibility fold (fullwidth/mathematical) · combining-mark strip (zalgo) ·
  curated unicode-confusable map (Cyrillic/Greek/symbol) · **letter-bounded** leet fold (so `455`
  never becomes `ass`) · single-char spaced-run collapse (so `b a d`→`bad` but `therapist` never
  trips `rapist`).
- **The invisible-character layer (the owner's specific ask)** — defends *both* sides: strip the
  `Cf`/`Mn`/`Me` Unicode categories (zero-width space/joiner, tag block, variation selectors) **and**
  an explicit set of the invisible-but-not-format characters that category-only strippers miss:
  HANGUL FILLER `U+3164` + choseong/jungseong fillers (category `Lo`), BRAILLE PATTERN BLANK
  `U+2800` (`So`), HALFWIDTH HANGUL FILLER `U+FFA0`. Plus exotic-space normalization (NBSP, en/em,
  ideographic). That `Lo`/`So` set is exactly the "passes advanced bots" gap.
- **Opt-in, default OFF** — migration 097 `wordfilter_config` (per-guild `strict`) +
  `db.get_wordfilter_strict` / `set_wordfilter_strict` (own table, mirrors `prohibited_words`; kept
  off the `guild_settings` KV so it clears the settings-key declaration/mutation invariants). A guild
  that never opts in is byte-identical to today.
- **Wired into** `cleanup_cog.remove_unwanted_message` as a second pass after the exact match (reads
  the strict flag from the per-guild cache `_load_guild` already populates — no extra DB round-trip on
  the hot path), routed through the same audited `moderation_service.auto_delete` seam. Operator
  toggle + status added to the existing `_WordMenuView` (no new command → reachability guard stays
  clean).
- **Tests** — 47 pure-module cases (every evasion class incl. a dedicated invisible-character test +
  the Scunthorpe false-positive boundaries) + 3 cog wiring cases (strict off ignores / strict on
  catches invisible insertion / strict on still ignores clean prose).
- **Docs reconciliation** — fixed the stale `docs/subsystems/server-management.md` reaction-roles
  section (it called the shipped overhaul "documented debt"; corrected to Carl-bot-parity-plus with
  the shipped PR list, only the web builder gated). This folio is what misled me mid-conversation.

CI: full `check_quality.py --full` green (12255 passed); `check_architecture --mode strict` exit 0,
no violations on changed files.

## Decisions made alone (owner should ratify)

- **Feature pick within the owner's directive:** chose word-filter de-obfuscation as the single
  beat-Sapphire slice (over per-channel automod overrides or escalation timers) — most self-contained,
  highest "wow", deterministic, builds on what the owner pointed me to. Not self-initiated (owner
  asked for *a* beat-Sapphire feature), but the *which* was my call.
- **Default OFF + opt-in** (vs. always-on) — matches the codebase's universal default-off filter
  convention and keeps the auto-delete blast radius consenting; the trade is discoverability (an
  operator must flip the toggle).
- **Leetspeak/spacing aggression bounds** — letter-bounded leet + single-char-run-only collapse to
  keep false positives minimal; the residual FP surface (a banned word coincidentally formed by
  ≥3 deliberately-spaced single chars) is accepted and documented.

## Known limits / flagged for maintainer

- **Not live-verified** — logic is exhaustively unit-tested but never exercised on real Discord with
  a real opted-in guild. Worth a 2-minute live check: add a word, flip 🛡️ Anti-evasion on, post an
  obfuscated variant.
- The confusable map is curated, not the full Unicode confusables table — covers the common
  Cyrillic/Greek/symbol look-alikes, not every homoglyph. Easy to extend.

## Context delta

- **Needed but not pointed to:** the cleanup word filter lives in `cleanup_cog` + `db.moderation`,
  not under "automod" — the orientation routed me to `automod_*` first and I'd have built a duplicate
  if the owner hadn't corrected me. The server-management folio's "reaction roles = documented debt"
  line was stale and actively misled the comparison (fixed this session).
- **Pointed to but didn't need:** the settings/`automod_config` schema machinery — the toggle
  deliberately avoided it (a dedicated table sidesteps the `test_no_direct_settings_keys_writes` /
  `test_settings_declared_vs_consumed_parity` invariants).
- **Discovered by hand:** the strict-cache-population invariant — `_get_patterns` triggers
  `_load_guild` which now also loads the strict flag, so the hot path can read the flag from cache
  without a second DB call (also what keeps the existing `test_clean_message` test DB-free).
- **🛠 Friction → guard:** running `ruff`/`black` directly over `tests/` produced 41 false S101
  (assert-in-test) reds — exactly the trap CLAUDE.md §"Match CI exactly" warns about (CI excludes
  `tests/`). Guard already exists (`check_quality.py` pins CI scope); reinforced by trusting it over
  bare `ruff`. No new guard needed.

## 💡 Session idea

**Extend `utils/text_obfuscation.deobfuscate` across the rest of the moderation surface** — the
invite-link detector (`discord(dot)gg`, zero-width-in-URL evasion walks through `_INVITE_RE` today)
and the AI/image-moderation text layer, plus a `!filtertest <text>` operator preview that shows what
the de-obfuscator *sees* (honoring the codebase's "always preview" discipline so an operator can
confirm a suspected evasion is caught before trusting the list). One pure module now hardens three
detectors. Logged here rather than a full idea file — medium-sized, naturally a follow-up PR on this
seam.

## ⟲ Previous-session review

The 2026-06-23 visual-card-engine session (#1349) was a clean born-red→complete exemplar and its
session card was unusually good provenance (it's the card I mirrored for format). One thing it
*could* have done that this session did: it shipped the card engine but left every renderer still on
plain embeds (`§3.6` migration deferred) — a "foundation PR with no consumer migrated" leaves the
win invisible until a follow-up lands. **System improvement surfaced:** the comparison conversation
proved the competitive-positioning docs (`competitive-positioning-north-star`, the Dank Memer /
Sapphire / GiveawayBot teardowns) are *genuinely load-bearing for steering* — they let me answer
"what beats Sapphire" from repo memory instead of guessing. Worth making the teardown set a
first-class, indexed cluster (a `docs/ideas/competitive/` folio) so the next agent finds them by
route, not by grep — I found them by glob luck.

## 📤 Run report

- **Did:** made the existing prohibited-words filter obfuscation-resistant (incl. the invisible-char
  class) + fixed the stale reaction-roles folio · **Outcome:** shipped (pending auto-merge)
- **Shipped:** #1394 — obfuscation-resistant word filter (opt-in, default OFF) + server-management
  folio reconciliation
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none — but two ratify-when-convenient calls in *Decisions made alone*
  (default-OFF opt-in; word-filter as the chosen beat-Sapphire slice)
- **⚑ Owner manual steps:** optional 2-min live check (add a word → flip 🛡️ Anti-evasion on → post an
  obfuscated variant) to confirm the path on real Discord
- **⚑ Self-initiated:** none (owner-directed: "improve whatever Sapphire does better and add it")
- **↪ Next:** extend de-obfuscation to the invite detector + AI moderation + a `!filtertest` preview
  (the 💡 idea above)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 opened (#1394), auto-merges on green CI |
| CI-red rounds | 1 local lint round (black dict reflow + W605 raw-docstrings + RET504) |
| Repo-rule trips | 0 (architecture strict exit 0, no violations on changed files) |
| New ideas contributed | 1 (cross-surface de-obfuscation + `!filtertest`) |
| Ideas groomed | 0 (build session — none moved) |
