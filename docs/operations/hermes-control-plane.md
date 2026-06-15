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
  Research's own free inference endpoint** (`provider: nous`,
  `base_url: https://inference-api.nousresearch.com/v1` — not OpenRouter), with only ~**$0.10 trial
  credit**. Free, quantized, lightweight — fine for chat, too weak *and* too small for reliable
  agentic control-plane work over this repo. Root cause of the "misunderstands / errors" the owner
  reported; no config knob fixes a capability ceiling.
- **Current target (2026-06-15):** `gpt-5.4-mini` on the **owner's own OpenAI key**, via a **custom
  OpenAI-compatible provider** added with the `hermes model` wizard (base url
  `https://api.openai.com/v1`, key in `~/.hermes/.env`). `/new` shows `Provider: openai-api · 400K
  (detected)`. Non-Claude → keeps the independent-reviewer property (Q-0117) while fixing capability;
  output is good when it runs (a coherent repo-health review confirmed the quality).
- **✅ CONFIRMED WORKING (2026-06-15 ~17:50 UTC).** `gpt-5.4-mini` (the **alias**) on the owner's own
  OpenAI key now answers reliably — clean in both Telegram and the OpenAI Playground, no errors. The
  earlier intermittent `Project proj_OJ… does not have access` was **OpenAI allowlist-propagation lag
  after all** — but a *slow, uneven* one: after adding the alias to the project allowlist it **flapped
  (some calls allowed, some denied) for >15 min** before fully converging. **Lesson:** don't conclude
  "not propagation" just because it's been 15 min — OpenAI allowlist/verification changes propagate
  slowly and flap on the way. **If it ever flaps again,** pin the **exact dated snapshot
  `gpt-5.4-mini-2026-03-17`** (re-run `hermes model`, set the custom provider's model to it) — the
  exact id is granted deterministically and skips the alias-propagation wait.
- **Verified specs (gpt-5.4-mini — fetched 2026-06-15; released 2026-03-17, after the Claude build
  cutoff, so these are from current OpenAI / aggregator sources, not model memory):** **400K context
  / 128K max output**, **$0.75 per 1M input · $4.50 per 1M output**, **Aug 2025 knowledge cutoff**, a
  **reasoning** model with tool calling + structured output + text/image input. The `400K (detected)`
  Hermes reports is correct. **Tuning lever:** it honours `agent.reasoning_effort` (the param that
  400'd the non-reasoning gpt-4o-mini) — keep it on a reasoning setting; consider raising it for the
  *review* role and lowering it (`minimal`/`low`) for cheap high-throughput dispatch triage. **Cost
  note:** at $4.50/1M output a long accumulating gateway session is the real spend driver (not the
  window) — so the bounded-session / `/new`-per-task habit is now a **cost** lever, not a capability
  crutch.
- **Recommended `config.yaml` for gpt-5.4-mini (verify key names against the installed version —
  Q-0105 unverified):** `agent.reasoning_effort: medium` (it **is** a reasoning model — never `none`,
  which was only the gpt-4o-mini workaround; the review-merge role can go `high`).
  `compression.threshold: 0.50` (the default) is fine now — on a 400K window that already leaves
  ~200K before compaction, so the old `apply_context_fixes.sh` 0.75 bump is **optional**, not
  required. `prompt_caching.cache_ttl: 1h` trims cost on long sessions. Pin
  `model: gpt-5.4-mini-2026-03-17` (the dated id) **only** if the alias ever flaps again (playbook).
- **Rationale (independence vs. reliability):** Hermes is deliberately a **non-Claude** mind so its
  review is independent of the Claude that builds (Q-0117). The reliability fix was *capability*, not
  *Claude* — a frontier **non-Claude** model (gpt-5.4-mini, or gpt-5.5) keeps the independence and
  fixes the weakness. A Claude key (`anthropic/claude-sonnet-4-6`) is the most-reliable fallback if
  independence is dropped. For the **review** role specifically, a stronger model than the cheap mini
  is worth considering.

#### Model-switch playbook (the ~3-hour maze — so it's 5 minutes next time)

Moving Hermes to a capable own-key model hit these traps, in order:

1. **`providers: {}` empty by default** → the model resolves via the remote `model_catalog` and
   defaults to **`nous`** (Nous Portal). `hermes config set model X` changes only the *name*, not the
   *provider* — it stays on `nous`. (Symptom: "I set the model but it still says nous.")
2. **Prefix routing:** `openai/gpt-5.4-mini` (with the `openai/` prefix) routes to the **Nous Portal
   catalog**, not OpenAI. Don't trust the prefix to pick the provider.
3. **Built-in `openai-api` provider has a stale model list** — only `gpt-4o-mini`; rejects gpt-5.x
   ("Model … not found in this provider's model listing"). For a newer OpenAI model, add a **custom
   OpenAI-compatible provider** via `hermes model` (base url `https://api.openai.com/v1`).
4. **`gpt-4o-mini` then 400s: "Encrypted content is not supported with this model."** Hermes sends
   reasoning/`include` params (driven by `agent.reasoning_effort`) that non-reasoning models reject.
   Use a reasoning model (gpt-5.x), or set `agent.reasoning_effort none` for gpt-4o-mini.
5. **OpenAI gates the gpt-5 family behind org verification** — Settings → Organization → Verify
   (one-time; unlocks all gated models).
6. **Exact-match project allowlist.** OpenAI "Allowed models" lists match the **exact id**. The project
   had the dated `gpt-5.4-mini-2026-03-17` but Hermes requested the alias `gpt-5.4-mini` → "no access."
   Add the alias, or — to skip the propagation wait — use the **exact dated id**.
   **Diagnostic shortcut:** reproduce in OpenAI's own Playground (same project + model) — if it fails
   there too, it's 100 % OpenAI-side, not Hermes.
   **Propagation caveat (verified live):** after you add the alias, access propagates *unevenly* and
   can **flap (allowed ↔ denied) for >15 min** before converging — that's normal eventual consistency,
   not a second bug. Wait it out, or pin the exact dated id to make access deterministic.

**To change the model later** (now the custom provider exists): re-run `hermes model` (keeps the
custom-provider routing) — *not* `hermes config set model …` (reverts to the nous catalog default).
Verify with `/new` (model · provider · context) + a real task.

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

## Roadmap — what's open vs. shipped

> **✅ RESOLVED (2026-06-15): token efficiency / "forgetting."** Root-caused to the **weak free model**,
> not the window — Hermes ran on `stepfun/step-3.7-flash:free` (quantized, ~256K). Fixed by the model
> swap to the capable 400K `gpt-5.4-mini` on the owner's own key (§ Model/provider; arc #913→#921). The
> diagnosis (compaction at 50%, not unbounded growth) is kept in
> [`hermes-token-efficiency-investigation-2026-06-15.md`](hermes-token-efficiency-investigation-2026-06-15.md)
> (now `historical`); the `compression.*` knobs remain optional secondary levers.

### Still open (infrastructure to-dos)

- **SSH key login** — access still uses password login. Add key-based login (Termius), then disable
  root/password SSH. Do this before the VPS becomes important infrastructure.
- **Docker terminal backend** — Hermes runs the `local` backend today; Docker would give safer
  command isolation (install Docker → add `hermes` to the docker group → set
  `terminal.backend: docker` → retest from Telegram). Do it before Hermes runs heavier tooling.
- **Backups** — not urgent, but matters once memory/skills/schedules accumulate. Targets: `~/.hermes`
  (config + `state.db` memory) and the systemd unit; the skill/doc sources are already git-tracked.
  Methods: Hetzner snapshot · periodic `tar`.
- **Discord integration (later)** — Telegram stays the private control surface; a private admin/dev
  channel could later receive repo-health / CI / review summaries. Not a priority.

### Done — items that were on this list (kept as a record)

- **Skill pack** ✅ — the read-only skills in [`hermes-skills/`](./hermes-skills/README.md) are the
  source of truth; `scripts/hermes/build_skills.py` generates installable `SKILL.md` files and
  `install-skills.sh` deploys them to the VPS. (Superseded the aspirational `superbot-*` skill list.)
- **Standing operating prompt** ✅ — [`hermes-operating-prompt.md`](./hermes-operating-prompt.md) is
  installed to `~/.hermes/SOUL.md` via `install-soul.sh` (loads fresh each message).
- **Scheduled work** ✅ — execution runs as bounded **Claude Code routines** on the console
  **Schedule** trigger (every 2h, Q-0146); reconciliation auto-fires at the PR-band boundary. Hermes'
  own cron can still post read-only Telegram reports if wanted. See
  [`autonomous-routines.md`](./autonomous-routines.md).
- **GitHub write access** ✅ (scoped) — Hermes may now author **PRs** (docs, bug reports, small
  self-tooling — Q-0140/Q-0141) and **merge** a PR it independently reviewed (the review-merge gate,
  Q-0117). It never pushes to `main` and never merges outside that gate; the exact boundary is the
  operating prompt's "WHAT YOU MAY WRITE". (Supersedes the old "keep Hermes read-only only" note.)

### Autonomous-loop seams (built 2026-06-12; dispatch now wired)

Three repo-side seams keep Hermes safe while letting it review and dispatch (Q-0113/Q-0114):

- **`superbot-review`** — independent (non-Claude) critique of a plan or PR diff, with a
  plain-language maintainer summary for the approve/deny gate.
- **`scripts/check_phase_gate.py`** — the fix-phase vs. invent-phase signal (agent-originated
  features stay gated until correctness is done).
- **`superbot-dispatch`** + [`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) — turns a
  work order into a Claude Code Routine `/fire` call. **Now wired** via the console **Schedule**
  trigger (every 2h, Q-0146) — no longer pending maintainer setup. Merge gate: self-merge on green
  CI (Q-0113); agent-originated features open a PR and wait for your approve/deny (Q-0114).

### Read-only log triage — shipped

Letting Hermes **read production logs** to diagnose problems (look-but-don't-touch) is live:

- The [`log-triage`](./hermes-skills/log-triage.md) skill + the `scripts/hermes/log_triage.py`
  analyzer (content-free, redacted, deterministic — #906) triage the VPS-local `hermes-gateway`
  logs today and Railway production logs via `scripts/hermes/railway_logs.py`. **Remaining gate:**
  the read-only Railway token on the VPS (owner-provisioned).
- A Neon read-only role can follow the same pattern for DB-level checks. Operating production
  (restart / redeploy / scale) remains a maintainer action.
