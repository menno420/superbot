#!/usr/bin/env bash
# Provision the dev environment for SuperBot.
#
# Designed to be the one-shot setup command for Claude Code on the web
# environments (and any local dev environment). Idempotent — re-runs are
# cheap; reinstalls only when requirements.txt, requirements-dev.txt, or
# this script changes.
#
# What it installs into python3.10 (matching CI exactly):
#   1. Runtime deps (requirements.txt: discord.py, asyncpg, etc.)
#   2. Dev tools (requirements-dev.txt: pytest, pytest-asyncio, ruff,
#      mypy) — the same set CI installs in
#      .github/workflows/code-quality.yml. (ruff replaced black + isort, A3.)
#
# In environments that use uv-managed tool venvs at
# /root/.local/share/uv/tools/* (Claude Code on the web's default tool
# layout), the runtime deps are mirrored into the pytest tool venv so
# pytest's plugin discovery — which imports project modules that import
# discord/asyncpg — succeeds. Without this step pytest collects 0 items.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PY="python3.10"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "[setup] ERROR: python3.10 not found. CI and all hooks require Python 3.10."
  exit 1
fi

# Hash requirements files + this script; only reinstall when something changes.
HASH_FILE=".setup_deps_hash"
CURRENT_HASH="$(cat requirements.txt requirements-dev.txt "${BASH_SOURCE[0]}" 2>/dev/null | md5sum | cut -d' ' -f1)"

if [ -f "$HASH_FILE" ] && [ "$(cat "$HASH_FILE" 2>/dev/null)" = "$CURRENT_HASH" ]; then
  echo "[setup] Python 3.10 env up to date."
  exit 0
fi

echo "── SuperBot dev-env setup ──────────────────────────────────"

# Step 1: install runtime + dev deps into python3.10. We do NOT upgrade
# pip itself — distro-packaged pips refuse self-upgrade with a
# "RECORD file not found" error, and the pip version is irrelevant here.
echo "[1/3] pip install runtime deps into python3.10..."
"$PY" -m pip install --quiet -r requirements.txt
echo "[2/3] pip install dev deps into python3.10..."
"$PY" -m pip install --quiet -r requirements-dev.txt

# Step 2: mirror into the uv-managed pytest tool venv if present, so
# `/root/.local/bin/pytest` (the tool-managed entry point) can import
# discord / asyncpg through the project's test modules. No-op otherwise.
if command -v uv >/dev/null 2>&1; then
    PYTEST_VENV_PY="/root/.local/share/uv/tools/pytest/bin/python"
    if [ -x "$PYTEST_VENV_PY" ]; then
        echo "[3/3] mirror runtime deps into uv-managed pytest venv..."
        uv pip install --quiet --python "$PYTEST_VENV_PY" -r requirements.txt
    else
        echo "[3/3] uv present but no pytest tool venv — skipping mirror."
    fi
else
    echo "[3/3] uv not present — skipping uv-managed mirror."
fi

echo "$CURRENT_HASH" > "$HASH_FILE"
echo "✓ dev environment ready ($($PY --version))"
