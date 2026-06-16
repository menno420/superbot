# Hermes session auto-reset (runbook)

> **Status:** `living-ledger` — the VPS-side runbook for automatically clearing Hermes'
> **interactive** chat session on a schedule, so the owner never has to type `/new`. The repo-side
> piece (`scripts/hermes/session_reset.sh`) is shipped; the timer + the one reset command are
> **maintainer-side VPS actions** (⬜ below). Provenance: owner-directed 2026-06-16 (reset every
> **6 hours** — "so there's never a long session, and the repo updates fast so old context isn't
> always valuable").

## What this is

Hermes' interactive Telegram session is **one long-lived, accumulating conversation**: the gateway
re-sends the history every turn (so spend grows fast), and on a fast-moving repo the older context
goes stale. The bounded-session habit (`hermes-operating-prompt.md` → "finish a task, then `/new`")
fixes that by hand; this automates it — a small timer fires the reset **every 6 hours** so each
sitting starts fresh and cheap.

```text
systemd timer (every 6h)  →  scripts/hermes/session_reset.sh  →  $HERMES_RESET_CMD  →  fresh session
```

**You do NOT need this for the scheduled skills.** `morning-briefing`, `idea-spotlight`, and
`review-merge` already run as **fresh, stateless** sessions on their own cron (a scheduled skill
never accumulates into your chat). This runbook is only about the **interactive** thread you type in.

## The one knob to confirm (UNVERIFIED — like `apply_context_fixes.sh`)

The exact way to clear the session depends on your Hermes build, and it can't be exercised from the
repo (no Hermes in CI). `/new` is the **manual** equivalent you already use in Telegram; the script
just needs the command-line form of it. Discover the candidates on the VPS:

```bash
hermes --help ; hermes session --help ; hermes chat --help   # look for a "new"/"reset"/"clear"
```

Common shapes (use whichever your version exposes):

```bash
HERMES_RESET_CMD="hermes session new"      # if the CLI has it
# HERMES_RESET_CMD="hermes chat reset"     # alternative naming
```

> ⚠️ **Restarting the gateway is NOT a reset.** `systemctl restart hermes-gateway` reloads skills /
> config but the session state persists in `~/.hermes/state.db`, so the conversation survives. Use
> the real `/new` equivalent, not a restart. If your build genuinely has no CLI reset, ask in the
> Hermes/Nous docs for the gateway's session-clear command before wiring the timer.

## Setup (one-time, on the VPS as the `hermes` user)

1. ✅ **The wrapper is in the repo:** `scripts/hermes/session_reset.sh` (logging + a safe no-op when
   unconfigured, so the timer never red-flags before you set the command). Pull `main` to get it.

2. ⬜ **Store the reset command** in `~/.hermes/reset.env` (chmod 600 — keep it out of git):
   ```bash
   echo 'HERMES_RESET_CMD="hermes session new"' > ~/.hermes/reset.env   # ← your confirmed command
   chmod 600 ~/.hermes/reset.env
   bash scripts/hermes/session_reset.sh --dry-run   # confirm it shows your command
   bash scripts/hermes/session_reset.sh             # do one real reset; check ~/.hermes/reset.log
   ```

3. ⬜ **Install the every-6h timer.** A user-level systemd timer is simplest (the `hermes` user owns
   it). Create the two units, then enable:
   ```bash
   mkdir -p ~/.config/systemd/user

   cat > ~/.config/systemd/user/hermes-session-reset.service <<'EOF'
   [Unit]
   Description=Reset the Hermes interactive chat session (clear accumulated context)

   [Service]
   Type=oneshot
   ExecStart=%h/repos/superbot/scripts/hermes/session_reset.sh
   EOF

   cat > ~/.config/systemd/user/hermes-session-reset.timer <<'EOF'
   [Unit]
   Description=Reset the Hermes chat session every 6 hours

   [Timer]
   OnCalendar=*-*-* 00/06:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   EOF

   systemctl --user daemon-reload
   systemctl --user enable --now hermes-session-reset.timer
   loginctl enable-linger hermes        # so the user timer runs even when not logged in
   ```
   `OnCalendar=*-*-* 00/06:00:00` fires at **00:00, 06:00, 12:00, 18:00 UTC** (every 6h). Adjust the
   start hour if you'd rather the resets land at other times.

4. ⬜ **Verify:**
   ```bash
   systemctl --user list-timers hermes-session-reset.timer   # next run time
   journalctl --user -u hermes-session-reset.service -n 20    # last run output
   cat ~/.hermes/reset.log                                    # the script's own log
   ```

### Cron alternative (if you prefer cron to systemd)

```cron
0 */6 * * * /home/hermes/repos/superbot/scripts/hermes/session_reset.sh >> /home/hermes/.hermes/reset.log 2>&1
```

## Kill switch (Q-0105)

This is disposable convenience infrastructure, not load-bearing runtime. To stop it:

```bash
systemctl --user disable --now hermes-session-reset.timer   # (or remove the cron line)
```

Or just unset `HERMES_RESET_CMD` in `~/.hermes/reset.env` — the script then degrades to a logged
no-op and resets nothing. If the reset mechanism changes upstream, delete the script + units rather
than working around them.

## See also

- [`hermes-operating-prompt.md`](./hermes-operating-prompt.md) — the bounded-session habit this
  automates (the manual `/new`).
- [`hermes-skills/README.md`](./hermes-skills/README.md) — the scheduled skills (already stateless;
  unaffected by this).
- `scripts/hermes/apply_context_fixes.sh` — the complementary lever: tune the **compaction**
  threshold so a single session holds context longer (reduces how often a reset matters).
- [`hermes-control-plane.md`](./hermes-control-plane.md) — VPS setup + the gateway service.
