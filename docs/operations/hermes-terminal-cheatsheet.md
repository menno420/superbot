# Hermes / SuperBot — Terminal Cheatsheet

> **Status:** `reference` — copy-paste command reference for operating Hermes on the VPS and
> the SuperBot repo from a phone/terminal. Pairs with
> [`hermes-control-plane.md`](hermes-control-plane.md) (the setup record) and
> [`hermes-operating-prompt.md`](hermes-operating-prompt.md) (Hermes' identity). Keep it
> current when a script/command changes — it is meant to be opened directly (e.g. in Acode).

**Context:** VPS user `hermes` · repo `/home/hermes/repos/superbot` · Hermes home `~/.hermes`.
Most repo commands assume you ran `cd /home/hermes/repos/superbot` first. Everything under
*read-only* is safe to run anytime — it never mutates the repo, Hermes, or production.

## Hermes service (systemd; restart/stop need `sudo`)

```bash
sudo systemctl restart hermes-gateway          # Restart Hermes. Run after install-skills.sh to load new/updated skills.
systemctl status hermes-gateway --no-pager     # Is Hermes alive? active/failed + recent log lines.
sudo systemctl stop hermes-gateway             # Stop Hermes (e.g. before maintenance).
sudo systemctl start hermes-gateway            # Start it again.
sudo journalctl -u hermes-gateway -n 50 --no-pager   # Last 50 log lines — first stop when Hermes misbehaves.
sudo journalctl -u hermes-gateway -f           # Live-tail the logs (Ctrl+C to stop).
```

## Deploy repo config → Hermes (after a session changes prompts/skills)

```bash
cd /home/hermes/repos/superbot                 # Go to the repo (lines below assume you're here).
git pull origin main                           # Pull the latest changes. Always do this before re-installing.
bash scripts/hermes/install-soul.sh            # Write the operating prompt → ~/.hermes/SOUL.md (backs up first). No restart needed.
bash scripts/hermes/install-skills.sh          # Copy skill files → ~/.hermes/skills/. Restart the gateway after this one.
bash scripts/hermes/install-soul.sh --dry-run  # Preview the prompt without writing it.
```

## Hermes config & identity

```bash
hermes config                                  # Show Hermes' current configuration.
hermes config edit                             # Safely edit config.yaml (e.g. trim joke personalities).
hermes config check                            # Validate the config after editing.
hermes --help                                  # Explore the rest of the Hermes CLI.
cat ~/.hermes/SOUL.md                          # View Hermes' current base identity / operating prompt.
ls ~/.hermes/skills/                           # List the skills Hermes has installed.
```

## Repo state & health (read-only)

```bash
git -C /home/hermes/repos/superbot log --oneline -10   # Last 10 commits — what landed recently.
git -C /home/hermes/repos/superbot status              # Any uncommitted local changes on the VPS clone?
python3 scripts/check_current_state_ledger.py --strict # Is the docs ledger in sync with merged PRs? (clean = nothing to reconcile)
python3 scripts/check_phase_gate.py --phase            # fix-phase or invent-phase? (gates new feature work)
python3 scripts/hermes/build_skills.py --check         # Are the installed skills up to date with the docs?
```

## Production (bot) diagnostics — read-only

```bash
python3 scripts/hermes/railway_logs.py -n 200          # Last 200 lines of the bot's live production logs.
python3 scripts/hermes/railway_logs.py --whoami        # Test that the Railway token works.
python3 scripts/hermes/railway_vars.py list            # List production env vars (values masked).
```

## General Linux (handy on any box)

```bash
df -h                                          # Free disk space (watch this on a small VPS).
free -h                                        # RAM usage.
du -sh ~/.hermes/*                             # What's eating space in Hermes' home (caches, state.db).
top                                            # Live CPU/mem/process viewer (q to quit; 'htop' is nicer if installed).
```

## Notes

- The `hermes …` commands are the Hermes Agent CLI (Nous Research). `hermes config set KEY VAL`
  changes one setting and routes it to the right file automatically.
- Hermes-run helper scripts (`build_skills.py`, `check_*`, `routine_fire.py`, `railway_*`) are
  stdlib-only, so `python3` works (the VPS also has `python3.10` installed for doc-command parity).
- SOUL.md reloads on every message (no restart); skills load on gateway start (restart needed).
