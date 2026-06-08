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

if npx -y "${CG_PKG}" --version >/dev/null 2>&1; then
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
  echo "[CodeGraph] Package unavailable — skipping index build."
fi

# ── 3. Session summary ──────────────────────────────────────────────────────
echo ""
python3.10 "$REPO_ROOT/scripts/claude_session_summary.py"
