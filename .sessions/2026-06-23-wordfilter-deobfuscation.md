# 2026-06-23 — Obfuscation-resistant word filter (beat Sapphire's content filter)

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the deliberate
> final step so auto-merge fires only on a complete PR.
> Owner-directed (chat: *"whatever Sapphire does a lot better than us, find a way to improve that
> even more and add it to the bot"*). The owner steered me off a duplicate word filter (cleanup
> already has one) → the non-duplicative beat-Sapphire move is making the **existing**
> prohibited-words filter **obfuscation-resistant**.

## Arc (in progress)

Comparison conversation (Sapphire vs our bot). Owner named moderation as the one area Sapphire
clearly leads, then corrected me that cleanup already ships a prohibited-words filter. Inspecting
it: the match is a naive `re.compile(rf"\b{word}\b", IGNORECASE)` — the same keyword filter
Sapphire/Carl/MEE6 all use, trivially evaded by `b a d`, `b.a.d`, `b4d`, `ｂａｄ` (fullwidth),
`bаd` (Cyrillic), zero-width insertion. The leap over Sapphire is **de-obfuscation**: normalize
the message to what a human actually reads, then match.

## About to do (this PR)

- `disbot/utils/text_obfuscation.py` — pure, stdlib-only de-obfuscator (`deobfuscate` +
  `find_obfuscated_match`): NFKC fold (fullwidth/math) · zero-width/format strip · accent fold ·
  curated unicode-confusable map · letter-bounded leet map · single-char spaced-run collapse —
  all word-boundary-preserving to keep false positives minimal (no Scunthorpe on normal prose).
- Migration 097 `wordfilter_config` (per-guild `strict` BOOLEAN, **default FALSE = byte-identical**)
  + `db.get_wordfilter_strict` / `set_wordfilter_strict` (mirrors `prohibited_words`).
- Wire opt-in strict mode into `cleanup_cog.remove_unwanted_message` (after the exact pass) +
  a toggle button + status in the existing word panel (no new command → reachability guard clean).
- Thorough unit tests for the pure module (catches + documented false-positive boundaries).
- Fix the stale `docs/subsystems/server-management.md` reaction-roles section (shipped, not debt).
