# Migrating XP / levels from another bot

> **Status:** `reference` — operator how-to. Source (`disbot/cogs/xp_cog.py`,
> `services/xp_migration.py`, `utils/xp_migration.py`) wins if they disagree.

SuperBot can adopt the chat levels a server already earned under a previous
leveling bot, so members keep their rank when you switch. The supported path is
**scanning the old bot's level-up channel** and copying the announced levels.

## Does the other bot have a direct import? (Arcane: no)

Some bots expose an export/API; most don't. The live case here is **Arcane**,
and the answer is **no** — Arcane provides no import/export API that another bot
can call:

- Imports *from* Arcane are blocked by their restricted API access.
- The only ways to get Arcane data out are a browser-console scrape of the web
  leaderboard (capped at the top 100 on the free tier) or a **manual export via
  Arcane's support team**.

So for Arcane — and any bot without a real export — the **channel scan** is the
way, which is exactly what `!xpimport` does. (If a future bot *does* offer a
clean leaderboard API, e.g. MEE6's public endpoint, it plugs into the same
import pipeline — see "Extending" below.)

## How to migrate (operator steps)

1. Make sure SuperBot can **read** the old bot's level-up channel (it needs
   **Read Message History** there). The old bot's announcements must still be
   present — don't delete the channel before migrating.
2. Run, in that channel (Administrator only):

   ```
   !xpimport arcane
   ```

   or point it at a specific channel / cap the scan:

   ```
   !xpimport arcane #level-up 5000
   ```

   - `source` — the old bot's announcer format: `arcane` (default), `mee6`,
     `superbot`, or `generic` (permissive "…level N…"). `!xpimport help` lists
     them.
   - `#channel` — where the level-up messages are (defaults to the current
     channel).
   - `limit` — max messages to scan (defaults to the **whole** channel).

3. SuperBot scans the channel, keeps the **highest** level announced per member,
   and shows a **preview** — how many members, a sample, and any names it
   couldn't match. Nothing is written yet.
4. Toggle **Assign level roles** (on by default) if you want members' XP-threshold
   roles granted as part of the import, then press **✅ Apply import**.

## What it does (and safety)

- **Level → XP.** A "reached level N" is converted to the exact XP total that
  reaches level N on SuperBot's own curve (`db.total_xp_for_level`), so the
  member lands at the start of that level.
- **Raise-only.** An import **never lowers** a member who already earned more XP
  here, and re-running the same import is a **no-op** — so it's safe to run
  again after more history accrues, or if it was interrupted.
- **Quiet.** A bulk import does **not** post level-up announcements (it would
  flood the channel) and records **one** audit action for the whole batch.
- **Level roles.** With the toggle on, each imported member still in the server
  is granted the roles they qualify for, through the same audited role seam and
  the *same* planner the live level-up path uses (stacking vs. single-role mode
  and XP-exempt roles are all honoured). Members who have left get their roles
  on the normal path if they rejoin.
- **Mentions vs. names.** Announcements that *mention* the member (Arcane does)
  resolve exactly. A plain-text name is matched against the current roster; a
  name that matches nobody is listed as "unmatched" in the preview and skipped.
- Only messages from a **bot/webhook** author are parsed, so member chatter in
  the channel can't be mistaken for a level-up.

## Extending to other bots / a direct API

The announcer patterns live in `utils/xp_migration.py` (`FORMATS`) — add a bot by
adding one `AnnouncerFormat` (a level regex + an optional name-fallback regex).

A *direct* provider (a bot that really does expose a leaderboard, e.g. MEE6's
public `/api/plugins/levels/leaderboard/{guild_id}`) doesn't need the channel
scan at all: fetch its `(user, level)` list and feed it straight to
`services.xp_migration.import_levels(guild, records, source=..., apply_roles=...)`
— the same raise-only, audited, role-syncing import the scan uses. Only the
*source* of the records differs.
