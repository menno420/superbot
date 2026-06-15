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
git fetch origin main && git reset --hard origin/main   # Sync the mirror to GitHub before re-installing. Discards local repo edits (it's a read-only mirror); never aborts on divergence.
bash scripts/hermes/install-soul.sh            # Write the operating prompt → ~/.hermes/SOUL.md (backs up first). No restart needed.
bash scripts/hermes/install-skills.sh          # Copy skill files → ~/.hermes/skills/. Restart the gateway after this one.
bash scripts/hermes/install-soul.sh --dry-run  # Preview the prompt without writing it.
```

## Clone diverged from main → `git pull` won't fast-forward (recovery)

`git pull` aborting with *"Not possible to fast-forward"* / *"diverging branches"* means the VPS
clone has local commits that aren't on GitHub. The clone is a read-only **mirror** — reset it to
match (the deploy command above already does this; this is the same fix with a safety snapshot):

```bash
cd /home/hermes/repos/superbot
git branch backup-vps-$(date +%Y%m%d)   # Snapshot the local-only commits first (recoverable via: git log backup-vps-…).
git fetch origin main
git reset --hard origin/main             # Make the clone exactly match GitHub.
git log --oneline -1                     # Confirm you're on the latest commit.
```

Never commit directly to the clone's `main` — Hermes writes on `claude/*` branches it pushes, so
the mirror stays clean and this won't recur.

## Hermes config & identity

```bash
hermes config                                  # Show Hermes' current configuration.
hermes config edit                             # Safely edit config.yaml (e.g. trim joke personalities).
hermes config check                            # Validate the config after editing.
hermes model                                   # Provider+model wizard — use THIS to switch provider/model (e.g. add a custom OpenAI endpoint, base url https://api.openai.com/v1). NOT `config set model` (reverts to the nous catalog). See hermes-control-plane.md → Model-switch playbook.
hermes config set OPENAI_API_KEY sk-...        # Use your own key directly — no OpenRouter needed (also ANTHROPIC_API_KEY for anthropic/* models). Set on the VPS; never share.
hermes --help                                  # Explore the rest of the Hermes CLI.
cat ~/.hermes/SOUL.md                          # View Hermes' current base identity / operating prompt.
ls ~/.hermes/skills/                           # List the skills Hermes has installed.
```

## Hermes memory (built-in — plain-text markdown)

Hermes' persistent memory is two files under `~/.hermes/memories/`, loaded into the system prompt as
a **frozen snapshot at session start** — so an edit takes effect on the next `/new`, never mid-session:

- `MEMORY.md` — the agent's own notes (~2,200 char / ~800 token cap).
- `USER.md` — owner profile / preferences (~1,375 char / ~500 token cap).

```bash
cat ~/.hermes/memories/MEMORY.md            # View what Hermes remembers (its own notes).
cat ~/.hermes/memories/USER.md              # View the owner-profile memory.
cp ~/.hermes/memories/MEMORY.md ~/.hermes/memories/MEMORY.md.bak   # Back up before any hand-edit.
nano ~/.hermes/memories/MEMORY.md           # Hand-edit (allowed, but not the intended path; mind the char cap).
```

**Intended way — let Hermes edit its own memory.** It has a `memory` tool (add / replace / remove by
substring), so in Telegram just instruct it plainly (e.g. *"Remove your memory entry 'Dispatch bridge
pattern'; keep only …"*), then `/new` so it reloads. Keep memory to **stickies only** (owner prefs,
infra ids) — procedures belong in SOUL.md + the skills, which reload every session anyway.

- `/memory pending` · `/memory approve <id>` · `/memory reject <id>` — staged-write approval, **only**
  relevant if `write_approval: true` in `config.yaml` (off by default). `memory_enabled` toggles
  memory entirely. There is **no** `hermes` CLI subcommand that deletes a memory by content — use the
  conversational `memory` tool or a hand-edit.

## Hermes skills — keep the set focused

Skills load by **progressive disclosure**: every turn the agent sees a Level-0 list of *all*
installed skills' names + descriptions (~3k+ tokens), and only loads a skill's full body on demand.
So a bloated catalog costs context **and** adds choice-noise on every message — keep Hermes to the
skills its SuperBot control-plane role uses (the `superbot/*` pack + the github / repo / review /
dispatch skills). The bundled non-SuperBot skills (creative / media / productivity / smart-home /
mlops / note-taking / social-media / etc.) are safe to remove and re-installable later.

```bash
hermes skills list                       # What's installed.
hermes skills uninstall <skill-name>     # Remove one (or `/skills uninstall <name>` in chat).
bash scripts/hermes/install-skills.sh    # (Re)install the SuperBot skill pack from the repo.
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

## Branch hygiene (keeping the repo prunable)

Autonomous sessions create a `claude/*` branch per PR; they pile up fast (hit **626** once,
which broke Acode's branch picker — it can't paginate that far to reach `main`).

```bash
# Prevent buildup (one-time, GitHub web): repo Settings → General → Pull Requests →
#   check "Automatically delete head branches"  → every merged PR self-deletes its branch.

# One-time bulk prune of leftover branches (run from a clone with push rights, e.g. the VPS —
# NOT from a Claude sandbox, whose git proxy 403s on deleting other branches):
cd /home/hermes/repos/superbot && git fetch --prune origin
git branch -r | sed 's#^[[:space:]]*origin/##' | grep -v '^HEAD' \
  | grep -vx main > /tmp/del.txt   # keep main (add more -vx lines to keep others)
wc -l /tmp/del.txt                  # review the count first
xargs -n 50 -a /tmp/del.txt git push origin --delete
```

**Deleting a branch never deletes its PR** — every PR (title, diff, commits, reviews) stays fully
viewable at `…/pulls`, and merged code lives in `main`. Safe to prune freely.

## Notes

- The `hermes …` commands are the Hermes Agent CLI (Nous Research). `hermes config set KEY VAL`
  changes one setting and routes it to the right file automatically.
- Hermes-run helper scripts (`build_skills.py`, `check_*`, `routine_fire.py`, `railway_*`) are
  stdlib-only, so `python3` works (the VPS also has `python3.10` installed for doc-command parity).
- SOUL.md reloads on every message (no restart); skills load on gateway start (restart needed).
