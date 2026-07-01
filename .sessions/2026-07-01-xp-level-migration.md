# 2026-07-01 — XP/level migration from other bots (Arcane)

> **Status:** `complete`

**Run type:** `manual`

## Arc

Owner wants SuperBot to migrate chat XP/levels from another bot — the live case is
**Arcane**. Two possible sources: (1) a direct export/import method from the other bot,
or (2) scanning the level-up channel and copying the announced levels.

**Research finding (answers the owner's question):** Arcane has **no** direct
import/export API — imports *from* Arcane are not possible via their API (access is
restricted); the only exits are a browser-console scrape of the web leaderboard
(top-100 on the free tier) or a manual export via Arcane support. So the **channel-scan**
path the owner proposed is the correct primary mechanism.

## What shipped (PR #1607)

End-to-end, admin-gated, **preview-then-confirm**, **raise-only** XP-migration feature:

- **`utils/xp_migration.py`** (pure, discord-free) — announcer-format registry
  (`arcane` default / `mee6` / `superbot` / `generic`), `parse_level_message`
  (mention-first, name-fallback), `reduce_max_levels` (highest level per user), `ScanPlan`.
- **`utils/db/xp.py`** — `total_xp_for_level` (exact inverse of `level_progress`, unit-proven
  round-trip) + the `set_imported_xp` raise-only upsert primitive (`GREATEST` merge; single
  atomic statement; never touches `messages`/`last_xp`/`coins`).
- **`services/xp_service.import_level`** — the one seam that writes imported XP (INV-G honoured;
  I **extended INV-G** to fence `set_imported_xp` too). Level→XP conversion, no events (silent).
- **`services/xp_migration.import_levels`** — batch orchestration: raise-only per member, **one**
  summary audit action, optional level-role sync, no announcement spam.
- **`services/xp_role_sync.py`** — extracted the level-role *planning* (stack/exempt/threshold)
  out of the XP listener into one shared pure planner; the live level-up path **and** the migration
  now grant identical roles (removed a would-be duplication at the root).
- **UI** — `views/xp/import_panel.py` confirm panel (raise-only notice, sample, unmatched names,
  role-sync toggle, admin re-check at the confirm callback); `!xpimport [source] [#channel] [limit]`
  in `xp_cog.py` reads the level-up channel (bot/webhook authors only) and opens the preview.
- **Docs:** `docs/operations/xp-migration.md` (operator guide + the Arcane-no-API finding + the
  direct-provider extension seam); `ownership.md` xp row; `help-command-surface-map.md`; grooming
  note on `ideas/bot-migration-assistant-2026-06-24.md`.
- **Tests (+~55):** pure parsing/level-math, `import_level`, batch orchestration, the shared planner,
  and the repointed listener-role tests. Regenerated the dashboard/site artifacts for the new command.
- **Full CI mirror GREEN** locally (13,535 passed); arch strict 0 errors.

## Decisions made alone (ratify)

- **Raise-only, idempotent** merge as the only mode — an import never lowers a member and re-running
  is a no-op (no overwrite/replace mode). Safest default for a bulk data write; surfaced in the panel.
- **Silent bulk import** — no per-member level-up announcement (would flood the channel) and **one**
  audit action for the whole batch (not per member).
- **Only bot/webhook-authored messages** are scanned, so human chatter can't be mistaken for a level-up.
- **Level-role sync defaults ON** in the confirm panel (migration should restore level roles).
- Extracted the listener's role planning into `services/xp_role_sync.py` (a hot-path refactor) —
  behavior-preserving, covered by the existing listener tests (repointed) + new planner tests.

## Flagged for maintainer (known limits)

- **Not live-verified against a real Arcane channel** (no Discord in the sandbox). Parsing is
  unit-tested against the exact screenshot format; the acceptance test is one real `!xpimport arcane`
  run on the server. **Owner manual step.**
- Scanning a whole busy channel is many history API calls (slow, one-time); the "Scanning…" message
  just sits until done.
- A member named by **plain text** (no mention) who has since left is skipped (listed as "unmatched").
  Arcane *mentions* the leveler, so this is rare in practice.
- MEE6/other **direct-API** providers are documented + seam-ready but not built (Arcane, the actual
  need, has no API).

## 🛠 Friction → guard (Q-0194)

- **Friction:** a new XP write primitive (`set_imported_xp`) could have bypassed the service seam.
  **Guard shipped (enforcing):** extended INV-G's forbidden-names set so `set_imported_xp` is fenced
  to `xp_service` exactly like `add_xp`/`delete_xp` — the whole `xp` column stays one-writer.
- **Friction:** the guild-resources invariant + black/ruff + the dashboard-freshness guard only tripped
  at the **full-mirror** stage (the PostToolUse auto-fix hook doesn't fire on `Write`-created files —
  same recurring snag the prev session hit on the MCP-edit path). **Guard (exists):** the full mirror's
  own black/ruff/invariant/artifact steps *are* the enforcing guards; they caught all four before push.
  The "hook doesn't cover Write/MCP edits" gap is a recurring, owner-gated hook change — noting, not
  wiring (candidate).

## 💡 Session idea (Q-0089)

**Level-up channel auto-detect** for `!xpimport`. Running it bare would fingerprint the server: scan a
sample of recent messages per channel, match each present **bot's application id** + the format regexes,
and suggest `"MEE6 level-ups look present in #levels — import? [Arcane/MEE6/…]"`. Removes the operator
needing to know both the source bot *and* the channel up front — pure win over the parsing already built,
and it feeds the broader bot-migration-assistant's "detect" phase. Not in the backlog yet (dedup-grepped).

## ⟲ Previous-session review (Q-0102)

Reviewed #1595 (inventory item-detail density) — a clean, well-tested completion slice; its
prev-session review + friction lines did the *right* thing by escalating the **dropped `code-quality`
run → close+reopen** CI-recovery, and I confirmed that recovery is now durably in the journal (line
631), so the loop closed. **One improvement it points at (system):** the born-red **rapid two-push**
pattern (card born red → push → flip complete → push) is *exactly* the shape that drops the second
`synchronize` event and stalls auto-merge — so the born-red workflow structurally invites the bug the
last two sessions fought. Worth considering whether the born-red flip should be the *only* second push
(batch all close-out into it, which I did here) and whether `check_loop_health`/the watchdog should
assert the required-context check exists on the final head, not just "a run happened".

## Doc audit (Q-0104)

`check_current_state_ledger --strict` clean (15-PR benign newest-merge lag only, not drift).
`check_docs --strict` passed — the new `docs/operations/xp-migration.md` is reachable via the
`ownership.md` xp-row link. New command `xpimport` reflected in `help-command-surface-map.md` and the
regenerated dashboard/site artifacts. Owner research finding (Arcane has no import API) captured
durably in the operator doc. No chat-only owner decisions beyond the ratify list above. Not adding to
current-state Recently-shipped (merged-PRs-only; the next reconciliation records #1607).

## 📤 Run report

- **Did:** built end-to-end XP/level migration from other bots — scans the level-up channel (Arcane,
  which has no import API) and copies levels raise-only, with preview/confirm + level-role sync ·
  **Outcome:** shipped (local CI mirror green, auto-merge armed; awaiting CI)
- **Shipped:** #1607 — `utils/xp_migration.py` · `utils/db/xp.py` · `services/xp_service.py` ·
  `services/xp_migration.py` · `services/xp_role_sync.py` · `views/xp/import_panel.py` · `cogs/xp_cog.py`
  · docs + tests + dashboard artifacts.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none (raise-only / silent / roles-on defaults noted for awareness).
- **⚑ Owner manual steps:** **live-verify** — run `!xpimport arcane #<level-up-channel>` on the server,
  check the preview, then Apply (the sandbox can't reach Discord). Ensure SuperBot has **Read Message
  History** in that channel first.
- **⚑ Self-initiated:** none — the feature is the owner's request; the `xp_role_sync` extraction is a
  root-cause refactor within it, not an unprompted new lane.
- **↪ Next:** live-verify on the server; then optional follow-ons — MEE6 direct-API importer (seam is
  ready) and the level-up auto-detect idea above; both feed `ideas/bot-migration-assistant-2026-06-24.md`.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (auto-merge armed; awaiting CI) |
| CI-red rounds | 1 born-red (expected) + 1 local full-mirror fix round (black/ruff/guild-resolver/dashboard, caught pre-push) |
| Repo-rule trips | 1 (guild-resources invariant — `guild.get_member` → `resources.resolve_member`) |
| New ideas contributed | 1 (level-up channel auto-detect) |
| Ideas groomed | 1 (bot-migration-assistant — shipped-precedent note) |
