#!/usr/bin/env bash
# Provision the dev environment for SuperBot.
#
# Designed to be the one-shot setup command for Claude Code on the web
# environments (and any local dev environment).  Idempotent — re-runs
# are cheap.
#
# What it installs:
#   1. Runtime deps (requirements.txt: discord.py, asyncpg, etc.)
#   2. Dev tools (requirements-dev.txt: pytest, pytest-asyncio, black,
#      isort, ruff, mypy) — the same set CI installs in
#      .github/workflows/code-quality.yml.
#
# After this runs, both:
#   * direct ``python -m pytest tests/...``
#   * the project quality script ``python scripts/check_quality.py
#     [--check-only|--full]``
# work end-to-end without further setup.
#
# In environments that use uv-managed tool venvs at
# /root/.local/share/uv/tools/* (Claude Code on the web's default tool
# layout), the runtime deps are mirrored into the pytest tool venv so
# pytest's plugin discovery — which imports project modules that import
# discord/asyncpg — succeeds.  Without this step pytest collects 0
# items in the project's test tree.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "── SuperBot dev-env setup ──────────────────────────────────"

# Step 1: install runtime + dev deps into system Python.  We do NOT
# upgrade pip itself — distro-packaged pips (debian/ubuntu) refuse
# self-upgrade with a "RECORD file not found" error, and the pip
# version is irrelevant to dependency resolution here.
echo "[1/3] pip install runtime deps..."
python -m pip install --quiet -r requirements.txt
echo "[2/3] pip install dev deps..."
python -m pip install --quiet -r requirements-dev.txt

# Step 2: mirror into the uv-managed pytest tool venv if present, so
# `/root/.local/bin/pytest` (the tool-managed entry point) can import
# discord / asyncpg through the project's test modules.  No-op when uv
# tools are not in use.
if command -v uv >/dev/null 2>&1; then
    PYTEST_VENV_PY="/root/.local/share/uv/tools/pytest/bin/python"
    if [ -x "$PYTEST_VENV_PY" ]; then
        echo "[3/3] mirror runtime deps into uv-managed pytest venv..."
        uv pip install --quiet --python "$PYTEST_VENV_PY" -r requirements.txt
    else
        echo "[3/3] uv present but no pytest tool venv — skipping mirror."
    fi
    # Ensure isort is on PATH (CI uses it; the post-edit hook calls
    # `isort` directly and crashes when missing).
    if ! command -v isort >/dev/null 2>&1; then
        uv tool install --quiet isort || true
    fi
else
    echo "[3/3] uv not present — skipping uv-managed mirror."
fi

echo "✓ dev environment ready"
