#!/usr/bin/env bash
# Install the SuperBot Hermes skill pack onto the control-plane VPS.
#
# Copies the generated SKILL.md files (scripts/hermes/skills/<name>/SKILL.md)
# into Hermes' skills directory. Hermes loads any SKILL.md dropped under
# ~/.hermes/skills/ on next run — no registration step needed.
#
# The committed SKILL.md files are generated from the docs by
# scripts/hermes/build_skills.py; this installer copies the committed
# artifacts, so the VPS needs no Python toolchain. Pass --build to regenerate
# from the docs first (requires python3 in the repo).
#
# Usage (run on the VPS as the `hermes` user, from the repo root):
#   bash scripts/hermes/install-skills.sh             # install (warns if the checkout is stale)
#   bash scripts/hermes/install-skills.sh --pull      # sync to origin/main FIRST, then install
#   bash scripts/hermes/install-skills.sh --dry-run   # show what would happen
#   bash scripts/hermes/install-skills.sh --build      # regenerate then install
#
# STALENESS GUARD: this installer copies whatever SKILL.md is checked out. If the clone is behind
# origin/main, you silently install OLD skills (and their helper scripts under scripts/hermes/ may be
# missing) — the 2026-06-16 "idea_spotlight.py missing in this checkout" incident. By default it now
# does a best-effort `git fetch` and WARNS if you're behind; `--pull` resets the checkout to
# origin/main before installing so skills + helper scripts always match.
#
# Override the target dir with HERMES_SKILLS_DIR (default: ~/.hermes/skills).
set -euo pipefail

DRY_RUN=0
DO_BUILD=0
DO_PULL=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --build) DO_BUILD=1 ;;
    --pull) DO_PULL=1 ;;
    -h | --help)
      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/skills"
DEST_DIR="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"

# Staleness guard — installing from a behind clone silently ships old skills (and helper scripts
# under scripts/hermes/ may be absent). --pull syncs to origin/main first; otherwise just warn.
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  if [[ "$DO_PULL" -eq 1 ]]; then
    echo "Syncing checkout to origin/main first (--pull)…"
    if git -C "$REPO_ROOT" fetch -q origin main && git -C "$REPO_ROOT" checkout -q -B main origin/main; then
      echo "  synced to $(git -C "$REPO_ROOT" rev-parse --short HEAD)"
    else
      echo "  ⚠ sync failed (uncommitted changes / network?) — installing whatever is checked out." >&2
    fi
    echo
  else
    git -C "$REPO_ROOT" fetch -q origin main 2>/dev/null || true
    behind="$(git -C "$REPO_ROOT" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
    if [[ "${behind:-0}" =~ ^[0-9]+$ ]] && [[ "${behind:-0}" -gt 0 ]]; then
      echo "⚠ checkout is $behind commit(s) behind origin/main — you may install STALE skills." >&2
      echo "  Re-run with --pull (or 'git pull' first) so skills + their helper scripts match." >&2
      echo
    fi
  fi
fi

if [[ "$DO_BUILD" -eq 1 ]]; then
  PY="$(command -v python3.10 || command -v python3 || true)"
  if [[ -z "$PY" ]]; then
    echo "error: --build needs python3, none found on PATH" >&2
    exit 1
  fi
  echo "Regenerating SKILL.md files from docs ($PY)..."
  "$PY" "$SCRIPT_DIR/build_skills.py"
fi

if [[ ! -d "$SRC_DIR" ]]; then
  echo "error: no skills directory at $SRC_DIR — run build_skills.py first" >&2
  exit 1
fi

echo "Installing SuperBot Hermes skills"
echo "  from: $SRC_DIR"
echo "  to:   $DEST_DIR"
[[ "$DRY_RUN" -eq 1 ]] && echo "  (dry run — no files will be written)"
echo

count=0
for skill_md in "$SRC_DIR"/*/SKILL.md; do
  [[ -e "$skill_md" ]] || continue
  name="$(basename "$(dirname "$skill_md")")"
  target="$DEST_DIR/$name"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "  would install: $name -> $target/SKILL.md"
  else
    mkdir -p "$target"
    cp "$skill_md" "$target/SKILL.md"
    echo "  installed: $name"
  fi
  count=$((count + 1))
done

echo
echo "Done — $count skill(s)."
if [[ "$DRY_RUN" -eq 0 ]]; then
  echo "Restart the gateway to pick them up:  sudo systemctl restart hermes-gateway"
  echo "Verify from Telegram:                 /skills   (or ask Hermes to list its skills)"
fi
