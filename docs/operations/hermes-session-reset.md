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

## ⚠️ Root cause clarification (2026-06-16 live incident) — it's TPM (resolved by the per-model cap)

A real incident clarified what actually goes wrong and the cleanest fix — read this before wiring a timer:

> **✅ RESOLVED (2026-06-16): the fix was the per-model TPM cap, not compaction.** The owner's OpenAI
> account caps `gpt-5.4-mini` at **200K TPM** but `gpt-5-mini` at **500K TPM** (2.5×, confirmed on the
> project Rate-limits page) — so the chosen fix is **switching Hermes to `gpt-5-mini`**, which clears
> the wall with headroom to spare. **Compaction was deliberately left at default — the owner declined
> lowering it because it interrupts tasks mid-flow** (it prunes context the turn still needs). The
> compaction guidance below is retained as *general background* for an account with no higher-cap model
> to switch to; it is **not** the path taken here. Full detail + the decision:
> [`hermes-control-plane.md`](./hermes-control-plane.md) § Model/provider ("gpt-5-mini vs gpt-5.4-mini").

- **The failure is a per-minute rate limit, not a context-window overflow.** The gateway logged
  `Rate limit reached for gpt-5.4-mini … on tokens per min (TPM): Limit 200000, Used …, Requested ~100k`
  with `Context: 79 msgs, ~110,571 tokens`. The model's window is **400K**, so a 110K session fits
  fine — but the OpenAI org's limit is **200,000 tokens *per minute***. Every reply re-sends the whole
  conversation (~100K), so **2 replies/min saturate the budget** and the bot can't answer (it looks
  "down" but is `active (running)`). The 3 automatic retries (each re-sending ~100K) guarantee it.
- **There is no first-class CLI command to reset the live gateway conversation.** Verified against
  `hermes gateway --help` (only `run/start/stop/restart/status/install/…` — service lifecycle, and
  **restart does NOT clear context**) and `hermes sessions --help` (store mgmt: `list/delete/prune/
  stats/…` — and the bloated session is the *newest*, so `prune` (old) won't touch it). **The only
  clean live reset is `/new` in Telegram.**
- **Compaction is the durable fix *only when you can't switch to a higher-cap model* (not the path
  taken here — see the RESOLVED note above).** Lower the compaction threshold so the gateway keeps each
  call small *continuously*, well under the TPM budget:
  ```bash
  hermes config                                  # confirm current compression.threshold (≈ 0.50)
  hermes config set compression.threshold 0.25   # compact at ~100K of the 400K window, not ~200K
  sudo systemctl restart hermes-gateway
  ```
  Tune **down** (0.20…) if it still throttles. This is the **opposite** of `apply_context_fixes.sh`
  (which *raises* the threshold for a different, doc-pruning problem — do **not** run it for a TPM
  rate-limit). The real ceiling fix is raising the OpenAI **TPM tier** (200K/min is low for a
  400K-window model); also note a `bg-review` background thread fires its own ~100K calls
  *concurrently*, doubling per-minute pressure.
- **Immediate unstick:** `/new` in Telegram (drops the bloated session), then restart for any new skills.

The auto-reset below is still useful as a coarse "fresh start every 6h," but it is **secondary** and,
given the CLI reality, a true hard reset means `hermes sessions delete <current-id>` **+** `gateway
restart`, or simply relying on `/new`. Order of preference for TPM: **raise the per-model cap (model
swap to 5-mini = 500K)** → then `/new`/auto-reset for hygiene → compaction only if no higher-cap model
is available (and the owner declined it here, as it interrupts tasks).

## The one knob to confirm (UNVERIFIED — like `apply_context_fixes.sh`)

The exact way to clear the session depends on your Hermes build, and it can't be exercised from the
repo (no Hermes in CI). `/new` is the **manual** equivalent you already use in Telegram; the script
just needs the command-line form of it. Discover the candidates on the VPS:

```bash
hermes gateway --help ; hermes sessions --help   # verified 2026-06-16: NO clean live-reset (see above)
```

The reset shapes that actually exist on a `hermes_cli` build (none as clean as `/new`):

```bash
# Hard reset (fragile — needs the live session id): delete it, then restart so the gateway starts fresh.
HERMES_RESET_CMD='id=$(hermes sessions list --json 2>/dev/null | <pick newest>); hermes sessions delete "$id" && sudo systemctl restart hermes-gateway'
# PREFERRED instead of a hard reset: set compression.threshold low (above) so sessions stay small.
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
