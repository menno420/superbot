#!/usr/bin/env bash
# scripts/hermes/redeploy.sh — one-command Hermes redeploy (sync -> reinstall -> restart).
#
# Provenance / reliability header (CLAUDE.md Q-0105 adopt-with-kill-switch):
# - Why: applying a merged Hermes change (SOUL.md / skills) to the live VPS otherwise means
#   hand-running git reset + install-soul + install-skills + a gateway restart in a terminal
#   EVERY time (owner pain point, 2026-06-22). This collapses it to ONE command — and pairs with
#   the systemd timer in scripts/hermes/systemd/ to make it fully automatic (merge=deploy for
#   Hermes, mirroring how Railway auto-redeploys the bot worker).
# - Added 2026-06-22 (Q-0197 follow-on). UNVERIFIED — it cannot run in CI (no VPS / no systemd
#   here); confirm the one-time install once on the VPS (docs/operations/hermes-redeploy.md) and
#   watch the first couple of auto-runs. DELETE this script + the units if they misfire — a manual
#   `git reset --hard origin/main && install-soul && install-skills && sudo systemctl restart
#   hermes-gateway` always works by hand.
#
# Why a DETACHED restart: the gateway cannot restart itself from inside its own process (the CLI
# guards against restart loops, and an in-process restart would kill the live turn). systemd-run
# schedules the restart as a separate transient unit a few seconds out, so this script is safe to
# run even when Hermes invokes it itself from a chat turn.
#
# Usage (VPS, as the `hermes` user, from anywhere):
#   bash scripts/hermes/redeploy.sh              # sync + reinstall + restart (always)
#   bash scripts/hermes/redeploy.sh --if-changed # no-op when already at origin/main (for the timer)
#   bash scripts/hermes/redeploy.sh --dry-run    # show what it would do, change nothing
#
# Override the repo path with HERMES_REPO (default: ~/repos/superbot).
set -euo pipefail

REPO="${HERMES_REPO:-$HOME/repos/superbot}"
IF_CHANGED=0
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --if-changed) IF_CHANGED=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h | --help)
      sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

log() { printf '[hermes-redeploy %s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

# --- Phase 1: sync the mirror to merged main (skipped on the re-exec pass) ---
if [[ -z "${HERMES_REDEPLOY_REEXEC:-}" ]]; then
  cd "$REPO"
  git fetch --quiet origin main
  local_sha="$(git rev-parse HEAD)"
  remote_sha="$(git rev-parse origin/main)"
  if [[ "$IF_CHANGED" -eq 1 && "$local_sha" == "$remote_sha" ]]; then
    log "already at ${remote_sha:0:8} — nothing to redeploy."
    exit 0
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY RUN — would reset ${local_sha:0:8} -> ${remote_sha:0:8}, install SOUL+skills, restart gateway (detached)."
    exit 0
  fi
  log "syncing ${local_sha:0:8} -> ${remote_sha:0:8}"
  git reset --hard --quiet origin/main
  # Re-exec from a stable copy: `git reset` just rewrote this very file, and editing a running
  # script in place is unsafe (bash re-reads from disk by byte offset). Run the freshly-synced
  # post-sync steps from a /tmp copy instead.
  tmp="$(mktemp)"
  cp "$REPO/scripts/hermes/redeploy.sh" "$tmp"
  chmod +x "$tmp"
  HERMES_REDEPLOY_REEXEC=1 exec "$tmp" "$@"
fi

# --- Phase 2: reinstall + restart (the re-exec'd, up-to-date copy) -----------
trap 'rm -f "$0"' EXIT # clean up the /tmp re-exec copy
cd "$REPO"
log "installing SOUL.md + skills"
bash scripts/hermes/install-soul.sh
bash scripts/hermes/install-skills.sh

# Detached restart. Auto-detect a user-managed vs system gateway service so we only use sudo when
# the service genuinely needs it (a `systemctl --user` gateway needs none).
if systemctl --user is-enabled hermes-gateway >/dev/null 2>&1; then
  log "scheduling user-service gateway restart in 3s (no sudo)"
  systemd-run --user --quiet --on-active=3s --unit=hermes-redeploy-restart \
    systemctl --user restart hermes-gateway
else
  log "scheduling system-service gateway restart in 3s (sudo)"
  sudo systemd-run --quiet --on-active=3s --unit=hermes-redeploy-restart \
    systemctl restart hermes-gateway
fi
log "done — gateway restarts momentarily with the new SOUL + skills."
