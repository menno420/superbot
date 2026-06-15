# Hermes Control Plane Setup

> **Status:** `living-ledger` — operational record of the Hermes agent VPS and Telegram gateway setup. Verified 2026-06-11 (initial setup session). Maintainer owns the Hetzner VPS and Telegram token; agents have no direct access — updates land here as an ops reference.

## Purpose

This document records the current Hermes Agent setup used as a mobile-accessible control plane for SuperBot repository inspection, planning support, and future automation.

Hermes is currently treated as a **repo-aware assistant**, not as a production bot component and not as an autonomous maintainer. Its first responsibility is to provide safe read-only access to SuperBot repo context from mobile through Telegram.

## Current confirmed setup

### VPS

- Provider: Hetzner Cloud
- Project: `hermes-control-plane`
- Server: `hermes-control-plane-01`
- Plan: CX23
- Region: Nuremberg, Germany
- OS: Ubuntu 24.04 LTS
- Public IPv4: configured
- Public IPv6: configured
- Separate volume: not configured
- Backups: not enabled yet
- Firewall: Ubuntu `ufw` was configured for SSH during setup

### Python toolchain

- System interpreter: **Python 3.11** (the Ubuntu 24.04 default `python3`).
- **Python 3.10 installed alongside** (verified 2026-06-14) via the deadsnakes PPA — so the repo's
  `python3.10`-pinned commands run verbatim while `python3` stays 3.11 (nothing else on the VPS is
  repointed). Re-run after a VPS rebuild:
  ```bash
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt-get update
  sudo apt-get install -y python3.10 python3.10-venv python3.10-distutils
  python3.10 --version            # Python 3.10.20
  ```
- The Hermes-run helpers (`build_skills.py`, `check_current_state_ledger.py`, `check_phase_gate.py`,
  `routine_fire.py`, `railway_*`) are stdlib-only and run under **either** `python3` (3.11) or
  `python3.10` — PR #869 de-pinned them, so 3.10 is installed for doc-command parity, not because
  they require it. (The `python3.10` pin in `.claude/CLAUDE.md` is for the CI-parity tools —
  `check_quality`/black/mypy/pytest — which Hermes does not run.)

### Linux users

- Initial setup was performed through `root`
- A dedicated non-root user was created: `hermes`
- Hermes, the SuperBot repo clone, and the Telegram gateway are owned/run under this user

### Hermes installation

Hermes Agent is installed under the `hermes` user.

Confirmed command path:

```text
/home/hermes/.local/bin/hermes
```

Hermes config/data paths shown during setup:

```text
/home/hermes/.hermes/config.yaml
/home/hermes/.hermes/.env
/home/hermes/.hermes/
```

### Model / provider

> Added 2026-06-15 (the Hermes context-management investigation —
> [`hermes-token-efficiency-investigation-2026-06-15.md`](hermes-token-efficiency-investigation-2026-06-15.md)).
> The model is the single biggest driver of Hermes' behaviour, so it belongs in this record.

- **Free default (what Hermes ships with):** `stepfun/step-3.7-flash:free`, served by **Nous
  Research's own free inference endpoint** — `hermes config` shows `provider: nous`,
  `base_url: https://inference-api.nousresearch.com/v1`. Not OpenRouter. A free, quantized,
  lightweight tier — fine for chat, but too weak for reliable agentic control-plane work over this
  repo (it was the root cause of the "misunderstands assignments / errors" the owner reported; no
  config knob fixes a capability ceiling).
- **Switched 2026-06-15 →** `openai/gpt-5.4-mini` on the **owner's own OpenAI key**
  (`OPENAI_API_KEY` in `~/.hermes/.env`). `/model` confirms `Provider: openai-api` (routing left the
  Nous endpoint). 400K context, ~$0.75/$4.50 per 1M tokens. **Live-reply verification pending** — the
  config is set and the provider switched, but a fresh `/status` still showed `Agent Running: No`, so
  confirm Hermes actually answers a task on it.
- **⚠️ The `/model` Telegram quick-picker is stale** — for `openai-api` it only lists the old
  `gpt-4o-mini` (a 2024 model). That is NOT what runs; `hermes config set model …` is authoritative.
  Don't tap `gpt-4o-mini` expecting an upgrade — it's a downgrade from gpt-5.4-mini (keep it only as a
  known-good fallback if a newer id won't route).
- **Switch the model / use your own key** (no OpenRouter credits needed — own provider keys work
  directly):
  ```bash
  hermes config set OPENAI_API_KEY sk-...        # or ANTHROPIC_API_KEY sk-ant-...  (set on the VPS; never share)
  hermes config set model openai/gpt-5.4-mini    # or anthropic/claude-sonnet-4-6 · openai/gpt-5.5 · …
  sudo systemctl restart hermes-gateway
  hermes config | grep -i model                  # verify
  ```
- **Rationale (independence vs. reliability):** Hermes is deliberately a **non-Claude** mind so its
  review is independent of the Claude that builds (Q-0117). The reliability fix was *capability*, not
  *Claude* — a frontier **non-Claude** model (gpt-5.4-mini, or gpt-5.5) keeps the independence and
  fixes the weakness. A Claude key (`anthropic/claude-sonnet-4-6`) is the most-reliable fallback if
  independence is dropped. For the **review** role specifically, a stronger model than the cheap mini
  is worth considering.

### Terminal backend

Hermes was initially configured with the Docker terminal backend, but Docker was not installed yet. This caused command execution failures.

The active backend was corrected to local:

```yaml
terminal:
  backend: local
```

Current state:

- Local terminal backend: working
- Docker backend: not enabled yet
- Command execution from Hermes: confirmed working

### GitHub

GitHub CLI was installed and authenticated on the VPS.

Confirmed GitHub account:

```text
menno420
```

The SuperBot repository was cloned to:

```text
/home/hermes/repos/superbot
```

Confirmed repo state during setup:

```text
Branch: main
Working tree: clean
Up to date with origin/main
```

Hermes successfully inspected the repo and identified architecture/docs structure without modifying files.

### Telegram gateway

A Telegram bot was created:

```text
SuperBot Hermes
```

Hermes gateway was configured with:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_ALLOWED_USERS
GATEWAY_ALLOW_ALL_USERS=false
```

The Telegram allowlist is enabled so only the configured Telegram user ID can access the tool-enabled gateway.

Manual gateway testing confirmed:

- Telegram bot responds
- Hermes can inspect `/home/hermes/repos/superbot`
- Hermes can report branch/status from Telegram
- Hermes did not modify files during tests

### Always-on service

Hermes Gateway is configured as a systemd service:

```text
hermes-gateway.service
```

Service file path:

```text
/etc/systemd/system/hermes-gateway.service
```

Service command:

```text
/home/hermes/.local/bin/hermes gateway
```

Working directory:

```text
/home/hermes/repos/superbot
```

Confirmed state:

```text
active (running)
enabled on boot
```

This means Hermes Gateway should remain available from Telegram after Termius is closed and after VPS reboot.

## Current capabilities

The current setup allows mobile access to a repo-aware Hermes assistant through Telegram.

Working use cases:

- Check SuperBot repo status
- Confirm current branch
- Inspect files read-only
- Summarize repo structure
- Identify architecture/docs files
- Review recent commits
- Search repo files
- Prepare implementation prompts
- Prepare review prompts
- Triage docs or planning questions
- Support mobile repo awareness without keeping Termius open

Example safe Telegram prompts:

```text
Check the SuperBot repo status at /home/hermes/repos/superbot. Do not modify files.
```

```text
Summarize the latest SuperBot commits and identify any risky areas. Do not modify files.
```

```text
Inspect the docs for inconsistencies around active features. Do not modify files.
```

```text
Review the AI cog and BTD6-related docs enough to tell me the next safe planning step. Do not modify files.
```

```text
Prepare a Claude/Codex prompt for reviewing the latest repo changes. Do not modify files.
```

## Current safety model

Hermes should currently be treated as:

```text
Read-only repo assistant
Planning assistant
Diagnostic assistant
Prompt/report generator
```

Hermes should not yet be treated as:

```text
Autonomous code editor
Production deployer
GitHub maintainer
Secret manager
Database operator
Railway/Neon operator
```

Current recommended instruction pattern:

```text
Before inspecting SuperBot, use /home/hermes/repos/superbot. Do not modify files unless I explicitly say you may edit. Prefer read-only commands first.
```

## Useful commands

> **Full reference:** [`hermes-terminal-cheatsheet.md`](hermes-terminal-cheatsheet.md) — the
> copy-paste command list (service control, repo sync, health checks, prod diagnostics). The
> essentials are repeated here.

Check service status:

```bash
sudo systemctl status hermes-gateway --no-pager
```

Restart gateway:

```bash
sudo systemctl restart hermes-gateway
```

Stop gateway:

```bash
sudo systemctl stop hermes-gateway
```

Start gateway:

```bash
sudo systemctl start hermes-gateway
```

View recent logs:

```bash
sudo journalctl -u hermes-gateway -n 100 --no-pager
```

Follow live logs:

```bash
sudo journalctl -u hermes-gateway -f
```

Check repo status:

```bash
cd /home/hermes/repos/superbot
git status
```

Run Hermes manually:

```bash
cd /home/hermes/repos/superbot
hermes
```

Run gateway manually for debugging:

```bash
cd /home/hermes/repos/superbot
hermes gateway
```

## Suggested next steps

> **▶ Owner-prioritized next (2026-06-15): token efficiency.** Hermes `/status` showed **2.2M
> cumulative tokens "re-sent each call"** after only a few messages (~8–9× the working window) →
> context collapse by the 3rd–4th tool call. Root cause + investigation questions + candidate fixes
> (stateless bounded dispatch · history cap · `soul.md` injection strategy) are captured in
> [`hermes-token-efficiency-investigation-2026-06-15.md`](hermes-token-efficiency-investigation-2026-06-15.md).

### 1. Add SSH key login

Current access still relies on password login. Long-term, add SSH key login through Termius or another SSH client.

Recommended later state:

```text
SSH key login enabled
Root password login disabled
Password SSH disabled if comfortable
Termius configured with key-based login
```

This should be done before the VPS becomes important infrastructure.

### 2. Install Docker and switch Hermes to Docker backend

Hermes currently uses local terminal execution. This works, but Docker would give safer command isolation.

Recommended future sequence:

```text
Install Docker
Add hermes user to docker group
Test docker run hello-world
Switch Hermes terminal backend to docker
Limit container resources if supported
Retest repo inspection from Telegram
```

This should happen before allowing Hermes to run heavier commands or experimental tooling.

### 3. Create SuperBot-specific Hermes skills

Create reusable Hermes skills so prompts can be shorter and behavior is more consistent.

Recommended skills:

```text
superbot-repo-health
superbot-pr-review
superbot-doc-consistency
superbot-ci-triage
superbot-btd6-audit
superbot-ai-cog-audit
superbot-release-summary
superbot-agent-session-briefing
```

Each skill should include:

- Repo path
- Read-only default
- Docs to inspect first
- Architecture boundaries
- Required output format
- Verification commands
- Stop conditions
- No production mutation rule

### 4. Add scheduled reports

Use Hermes cron or system-level scheduling for regular Telegram reports.

Useful schedules:

```text
Daily repo health summary
Daily failed CI check
Weekly stale docs scan
Weekly open plan summary
After-merge docs consistency check
Before-agent-session repo briefing
```

Reports should be read-only and should not modify repo files.

### 5. Improve GitHub access carefully

GitHub CLI is authenticated. Keep Hermes read-only for now.

Possible later permissions:

```text
Read PRs/issues/checks
Draft issue comments
Draft PR review summaries
Create local markdown reports
Open draft PRs only when explicitly requested
```

Avoid for now:

```text
Auto-merge
Direct pushes
Repo admin permissions
Production secret access
Railway deploy access
Neon database access
Broad personal access tokens
```

### 6. Add a stable SuperBot operating prompt

Create a short operating guide for Hermes that defines how it should work in this repo.

Suggested contents:

```text
Repo path
Default branch
No-edit default
Architecture docs to read first
Decision vs analysis boundaries
Affected-system reporting format
Migration/test/docs verification expectations
How to classify risks and ownership
```

This can either be a Hermes skill, a repo doc, or both.

### 7. Add Discord integration later

Telegram is the best private control surface. Discord can be added later for SuperBot ecosystem visibility.

Potential Discord use cases:

```text
Post repo health summaries
Post CI failure alerts
Post PR review summaries
Post docs drift reports
Support private admin/dev channel workflows
```

Keep Discord restricted to a private admin/dev channel.

### 8. Add backup strategy

Backups are not urgent yet, but they become important after adding custom Hermes skills, memory, or schedules.

Recommended backup targets:

```text
/home/hermes/.hermes
/home/hermes/repos/superbot/docs/operations/hermes-control-plane.md
custom skills
systemd service file
```

Possible backup methods:

```text
Hetzner backup
manual snapshot
git-tracked skill/docs files
periodic tar archive
```

## Recommended next project phase

The next best phase is not more infrastructure. The next best phase is a **SuperBot Hermes skill pack**.

Goal:

```text
Make Hermes consistently useful for SuperBot repo review, doc consistency checks, PR summaries, CI triage, and agent-session preparation while preserving a read-only default.
```

This gives the highest value with the lowest risk because it improves behavior without giving Hermes broader write or production access.

**The skill pack has been implemented** — see [`hermes-skills/`](./hermes-skills/README.md)
for the ready-to-use skill prompts. They are now **scripted to install**: the docs are the
source of truth, `scripts/hermes/build_skills.py` generates installable `SKILL.md` files,
and `scripts/hermes/install-skills.sh` copies them onto the VPS. A standing read-only
operating prompt (step 6 below) is implemented as
[`hermes-operating-prompt.md`](./hermes-operating-prompt.md).

### Autonomous-loop seams (built 2026-06-12)

Three repo-side seams of the autonomous-improvement loop now exist (owner decisions
Q-0113/Q-0114), keeping Hermes read-only while letting it review and dispatch:

- **`superbot-review`** — independent (non-Claude) critique of a plan or PR diff, with a
  plain-language maintainer summary for the approve/deny gate.
- **`scripts/check_phase_gate.py`** — the fix-phase vs. invent-phase signal (agent-originated
  features stay gated until correctness is done).
- **`superbot-dispatch`** + **[`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md)** — turn
  a work order into a Claude Code Routine `/fire` call. **Maintainer wiring required** (Routine +
  token) before it can fire; see the runbook's ⬜ steps. The merge gate is full self-merge on
  green CI (Q-0113); agent-originated features open a PR and wait for your approve/deny (Q-0114).

### Next sanctioned capability: read-only log triage

The highest-value graduation from "repo assistant" to "operations assistant" is letting
Hermes **read production logs** and diagnose problems — without granting any write/deploy
power. This stays inside the safety model: it is look-but-don't-touch.

- The [`log-triage`](./hermes-skills/log-triage.md) skill is ready; it triages the
  VPS-local `hermes-gateway` logs today and the production (Railway) logs once a
  **read-only** Railway token + CLI is set up on the VPS.
- A Neon read-only role can follow the same pattern for DB-level checks.
- Operating production (restart / redeploy / scale) remains a maintainer action.
