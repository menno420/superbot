#!/usr/bin/env bash
# SessionStart hook: Python env → CodeGraph index → session summary.
#
# Steps are independent — one failing does not skip the rest.
# All steps are idempotent so repeated sessions are fast.

# No -e: we want the session summary to print even if earlier steps fail.
set -uo pipefail

# Locate repo root regardless of which directory the hook fires from.
if [ -d "/home/user/superbot" ]; then
  REPO_ROOT="/home/user/superbot"
else
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
cd "$REPO_ROOT"

# ── 1. Python 3.10 environment ──────────────────────────────────────────────
bash "$REPO_ROOT/scripts/setup_dev_env.sh" || \
  echo "[setup] WARNING: setup_dev_env.sh failed — hooks may not work correctly."

# ── 2. CodeGraph index ──────────────────────────────────────────────────────
CG_PKG="@optave/codegraph@3.11.2"
echo ""
echo "[CodeGraph] Checking index..."

# Resolve the pinned CodeGraph CLI, retrying a few times.  On a fresh container
# the npx cache (/root/.npm/_npx) is cold, so the first `npx -y` must download
# from the registry — and a transient blip there used to print a bare "Package
# unavailable" (the real error swallowed by 2>/dev/null) and silently disable
# CodeGraph for the entire session.  Retry the cold download, and on a genuine
# failure surface the actual error so a real problem (bad/unpublished version,
# registry down) is diagnosable instead of guessed at.
CG_OK=0
CG_ERR=""
for attempt in 1 2 3; do
  if CG_ERR="$(npx -y "${CG_PKG}" --version 2>&1)"; then
    CG_OK=1
    break
  fi
  [ "$attempt" -lt 3 ] && sleep "$((attempt * 2))"
done

if [ "$CG_OK" = 1 ]; then
  LAST_BUILT=".codegraph/last_build_commit"
  HEAD="$(git rev-parse HEAD 2>/dev/null || echo "unknown")"
  SHORT="$(git log -1 --format='%h %s' 2>/dev/null || echo "unknown commit")"

  if [ -f ".codegraph/graph.db" ] \
       && [ -f "$LAST_BUILT" ] \
       && [ "$(cat "$LAST_BUILT" 2>/dev/null)" = "$HEAD" ]; then
    echo "[CodeGraph] Index current — ${SHORT}."
    npx -y "${CG_PKG}" stats 2>/dev/null || true
  else
    echo "[CodeGraph] Building index (${SHORT})..."
    if npx -y "${CG_PKG}" build . 2>&1; then
      mkdir -p .codegraph
      echo "$HEAD" > "$LAST_BUILT"
      echo "[CodeGraph] Build complete."
      npx -y "${CG_PKG}" stats 2>/dev/null || true
    else
      echo "[CodeGraph] Build failed — symbol lookups will fall back to grep."
      echo "             To retry: npx -y ${CG_PKG} build ."
    fi
  fi
else
  echo "[CodeGraph] CLI unavailable after 3 attempts — skipping index build."
  echo "            (symbol lookups fall back to grep.)"
  echo "            Last error: ${CG_ERR:-<none captured>}"
  echo "            Manual retry: npx -y ${CG_PKG} --version"
fi

# ── 3. Session summary ──────────────────────────────────────────────────────
echo ""
python3.10 "$REPO_ROOT/scripts/claude_session_summary.py"
