# Hermes redeploy — apply merged changes to the live VPS without a terminal

> **Status:** `reference` — setup + operation guide for `scripts/hermes/redeploy.sh` and its
> systemd timer. Pairs with [`hermes-control-plane.md`](hermes-control-plane.md) (the setup record),
> [`hermes-terminal-cheatsheet.md`](hermes-terminal-cheatsheet.md) (command reference), and
> [`hermes-session-reset.md`](hermes-session-reset.md) (the same user-timer pattern).

## The problem this solves

A merged Hermes change (the operating prompt in `SOUL.md`, or a skill) does **not** go live on its
own. Until now, applying it meant opening a terminal and running, every time:

```bash
cd ~/repos/superbot
git fetch origin main && git reset --hard origin/main
bash scripts/hermes/install-soul.sh
bash scripts/hermes/install-skills.sh
sudo systemctl restart hermes-gateway
```

That's the chore. Two ways to kill it:

- **One command** — `scripts/hermes/redeploy.sh` does all of the above in a single call (and Hermes
  can run it itself).
- **Zero commands** — a user systemd timer runs `redeploy.sh --if-changed` on a schedule, so
  **merging a Hermes change to `main` makes it live on its own within ~10 minutes** — the same
  "merge = deploy" model Railway already gives the bot worker (Q-0193).

> **Why Hermes can't just `systemctl restart` itself:** the gateway refuses to restart from inside
> its own process (anti-restart-loop guard), and an in-process restart would kill the live turn.
> `redeploy.sh` sidesteps this by **detaching** the restart with `systemd-run --on-active=3s`, so
> the restart fires from a separate transient unit after the turn ends. That's what makes a
> self-service / automatic redeploy possible at all.

## `redeploy.sh`

```bash
bash scripts/hermes/redeploy.sh              # sync + reinstall SOUL/skills + restart (always)
bash scripts/hermes/redeploy.sh --if-changed # no-op when already at origin/main (used by the timer)
bash scripts/hermes/redeploy.sh --dry-run    # show what it would do, change nothing
```

It is safe to run from inside a Hermes chat turn (the restart is detached) **and** from the timer.
After `git reset`, it re-execs itself from a `/tmp` copy so resetting the script mid-run is safe.

**`sudo` note (auto-detected):** if `hermes-gateway` is a **user** service (`systemctl --user`),
`redeploy.sh` restarts it with **no sudo at all**. If it's a **system** service (the current
setup — `sudo systemctl restart hermes-gateway`), the detached restart needs passwordless sudo for
that one action. Grant it narrowly (visudo):

```
hermes ALL=(root) NOPASSWD: /usr/bin/systemd-run *
```

(Or, cleaner long-term, run the gateway as a `systemctl --user` service so no sudo is ever needed.)

## Automatic mode — the merge=deploy timer (recommended)

User-level systemd units, same pattern as [`hermes-session-reset.md`](hermes-session-reset.md).
The unit templates live in [`scripts/hermes/systemd/`](../../scripts/hermes/systemd/). One-time
install, as the `hermes` user:

```bash
mkdir -p ~/.config/systemd/user
cp ~/repos/superbot/scripts/hermes/systemd/hermes-redeploy.service ~/.config/systemd/user/
cp ~/repos/superbot/scripts/hermes/systemd/hermes-redeploy.timer   ~/.config/systemd/user/

systemctl --user daemon-reload
systemctl --user enable --now hermes-redeploy.timer
loginctl enable-linger hermes        # so the timer runs even when you're not logged in
```

That's the last terminal session you need: from here on, merge a Hermes change and it deploys
itself. Tune the cadence by editing `OnUnitActiveSec` in the timer (default 10 min).

### Verify

```bash
systemctl --user list-timers hermes-redeploy.timer        # next run time
journalctl --user -u hermes-redeploy.service -n 30        # last run output
```

## On-demand mode (no timer)

Skip the timer and just run `bash scripts/hermes/redeploy.sh` when you want — or tell Hermes
"redeploy" and let it run the script itself. Same effect, manually triggered.

## Kill switch (Q-0105)

This is convenience automation, **disposable**. If it misfires:

```bash
systemctl --user disable --now hermes-redeploy.timer   # stop the auto loop
```

…and the manual five-command sequence at the top of this doc always works by hand. Delete
`scripts/hermes/redeploy.sh` + `scripts/hermes/systemd/hermes-redeploy.*` if it proves unreliable
over several runs. **UNVERIFIED until confirmed on the VPS** — it can't be exercised in CI (no
systemd there), so watch the first couple of auto-runs in `journalctl`.
