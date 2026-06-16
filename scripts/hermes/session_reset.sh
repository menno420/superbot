#!/usr/bin/env bash
# Reset the Hermes INTERACTIVE chat session on a schedule (so the owner never has
# to type /new). Run by an every-6h systemd timer (or cron) on the control-plane
# VPS — full setup in docs/operations/hermes-session-reset.md.
#
# WHY: Hermes' interactive Telegram session is one long-lived, accumulating
# conversation (the gateway re-sends history every turn → cost grows fast, and old
# context goes stale as the repo moves quickly). A periodic reset keeps every
# "sitting" fresh and cheap — the automated form of the bounded-session /new habit
# in docs/operations/hermes-operating-prompt.md. (Scheduled SKILLS already run
# stateless, so they don't need this — this is only the human chat thread.)
#
# WHAT THIS DOES: runs the command that clears the session (HERMES_RESET_CMD) and
# logs the result. It is the SAFE WRAPPER (scheduling + logging + a no-op when
# unconfigured) — you supply the one reset command for your Hermes version.
#
# THE RESET COMMAND (2026-06-16 incident finding — read first):
# A `hermes_cli` gateway has NO clean CLI to reset the live conversation — verified via
# `hermes gateway --help` (service lifecycle only; restart KEEPS state) and `hermes sessions --help`
# (store mgmt: list/delete/prune). The only clean live reset is `/new` in Telegram. So PREFER the
# continuous fix instead of this timer: lower compaction so sessions never get big
# (`hermes config set compression.threshold 0.25`; see docs/operations/hermes-session-reset.md
# § "Root cause clarification (2026-06-16)"). If you still want a hard periodic reset, set in
# ~/.hermes/reset.env (chmod 600) a delete-current-session-then-restart command, e.g.:
#     HERMES_RESET_CMD='id=$(hermes sessions list ... newest); hermes sessions delete "$id" && sudo systemctl restart hermes-gateway'
# If HERMES_RESET_CMD is unset, this script is a logged no-op (never an error), so
# the timer won't spam failures before you've configured it.
#
# USAGE (on the VPS, as the `hermes` user):
#   bash scripts/hermes/session_reset.sh            # do the reset (or no-op if unconfigured)
#   bash scripts/hermes/session_reset.sh --dry-run  # show what it would run
#
# Invoke with bash (the VPS shell), not the CI-pinned python toolchain.
# Provenance: added 2026-06-16, owner-directed (reset every 6h; "repo updates fast,
# old session context is not always valuable"). Kill-switch (Q-0105): disposable
# operator convenience — `systemctl --user disable --now hermes-session-reset.timer`
# to stop it; delete this script if the reset mechanism changes upstream.
set -uo pipefail

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h | --help)
      sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
RESET_ENV="$HERMES_HOME/reset.env"
RESET_LOG="${HERMES_RESET_LOG:-$HERMES_HOME/reset.log}"

# Load the owner-confirmed reset command (and optional overrides) if present.
# shellcheck disable=SC1090
[[ -f "$RESET_ENV" ]] && source "$RESET_ENV"
RESET_CMD="${HERMES_RESET_CMD:-}"

now() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '%s %s\n' "$(now)" "$*" | tee -a "$RESET_LOG" >/dev/null 2>&1 || true; }

mkdir -p "$HERMES_HOME" 2>/dev/null || true

if [[ -z "$RESET_CMD" ]]; then
  msg="session-reset SKIPPED — HERMES_RESET_CMD not set in $RESET_ENV (see docs/operations/hermes-session-reset.md)"
  log "$msg"
  echo "$msg"
  exit 0  # a no-op, not a failure — don't make the timer report errors pre-config
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "would run: $RESET_CMD"
  echo "would log to: $RESET_LOG"
  exit 0
fi

log "session-reset RUNNING: $RESET_CMD"
if out="$(bash -c "$RESET_CMD" 2>&1)"; then
  log "session-reset OK"
  [[ -n "$out" ]] && log "  output: ${out:0:200}"
  echo "session reset OK ($(now))"
else
  rc=$?
  log "session-reset FAILED (exit $rc): ${out:0:200}"
  echo "session reset FAILED (exit $rc) — see $RESET_LOG" >&2
  exit 0  # still exit 0: a transient reset failure should not red-flag the timer
fi
