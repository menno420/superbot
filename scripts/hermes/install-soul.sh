#!/usr/bin/env bash
# Install the SuperBot operating prompt into Hermes' SOUL.md.
#
# SOUL.md (~/.hermes/SOUL.md) is slot #1 of Hermes' system prompt and is loaded
# fresh on every message (no restart needed). This script extracts the operating
# prompt from docs/operations/hermes-operating-prompt.md and writes it there,
# timestamp-backing-up any existing SOUL.md first. It is the SOUL.md sibling of
# install-skills.sh (which handles ~/.hermes/skills/).
#
# Usage (run on the VPS as the `hermes` user, from the repo root):
#   bash scripts/hermes/install-soul.sh             # install (backs up first)
#   bash scripts/hermes/install-soul.sh --dry-run   # print the prompt, write nothing
#
# Override the target with HERMES_SOUL (default: ~/.hermes/SOUL.md).
set -euo pipefail

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h | --help)
      sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOC="$REPO_ROOT/docs/operations/hermes-operating-prompt.md"
DEST="${HERMES_SOUL:-$HOME/.hermes/SOUL.md}"

# Hermes-run helpers are stdlib-only and version-agnostic — python3 is fine.
PY="$(command -v python3.10 || command -v python3 || true)"
[[ -z "$PY" ]] && {
  echo "error: need python3 on PATH" >&2
  exit 1
}

# Extract the first fenced code block after the "## Operating prompt" heading.
PROMPT="$("$PY" - "$DOC" <<'PYEOF'
import pathlib, sys
doc = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
block = doc.split("## Operating prompt", 1)[1].split("```", 2)[1].strip()
if not block.startswith("You are Hermes"):
    sys.exit("operating-prompt block not found / unexpected format")
sys.stdout.write(block + "\n")
PYEOF
)"

# SOUL.md size guard. Hermes loads SOUL.md as system-prompt slot #1 and SILENTLY TRUNCATES it
# if it is too large — an invisible cause of "Hermes forgets its own rules". The exact ceiling is
# not published upstream; HERMES_SOUL_BUDGET defaults to 8000 (aligned with Hermes' documented
# 8000-char per-context-file cap) — confirm against your installed version. Provenance: the Hermes
# token-efficiency investigation, 2026-06-15. DELETE this guard if it proves noisy/wrong over time.
SOUL_BUDGET="${HERMES_SOUL_BUDGET:-8000}"
PROMPT_BYTES="$(printf '%s\n' "$PROMPT" | wc -c | tr -d ' ')"
if [[ "$PROMPT_BYTES" -gt "$SOUL_BUDGET" ]]; then
  echo "⚠ operating prompt is $PROMPT_BYTES bytes — OVER the ~$SOUL_BUDGET-byte budget." >&2
  echo "  Hermes truncates an oversized SOUL.md SILENTLY (it loses rules past the cut)." >&2
  echo "  Trim docs/operations/hermes-operating-prompt.md, or raise HERMES_SOUL_BUDGET if your version allows." >&2
elif [[ "$PROMPT_BYTES" -gt $((SOUL_BUDGET * 8 / 10)) ]]; then
  echo "ℹ operating prompt is $PROMPT_BYTES of ~$SOUL_BUDGET bytes (>80%) — little headroom before truncation." >&2
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "# would write to: $DEST"
  echo "---"
  printf '%s\n' "$PROMPT"
  exit 0
fi

mkdir -p "$(dirname "$DEST")"
if [[ -f "$DEST" ]]; then
  cp "$DEST" "$DEST.bak.$(date +%Y%m%d_%H%M%S)"
fi
printf '%s\n' "$PROMPT" >"$DEST"
echo "Installed SuperBot operating prompt -> $DEST ($(wc -c <"$DEST") bytes)."
echo "SOUL.md loads fresh each message — no restart needed."
