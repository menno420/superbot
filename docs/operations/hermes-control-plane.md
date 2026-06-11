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
