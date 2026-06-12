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
#   bash scripts/hermes/install-skills.sh             # install
#   bash scripts/hermes/install-skills.sh --dry-run   # show what would happen
#   bash scripts/hermes/install-skills.sh --build      # regenerate then install
#
# Override the target dir with HERMES_SKILLS_DIR (default: ~/.hermes/skills).
set -euo pipefail

DRY_RUN=0
DO_BUILD=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --build) DO_BUILD=1 ;;
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
