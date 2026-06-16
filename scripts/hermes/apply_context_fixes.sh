#!/usr/bin/env bash
# Apply the recommended Hermes context-management fixes on the control-plane VPS.
#
# STATUS (2026-06-15): OPTIONAL / secondary. The root cause of the "forgetting" was the weak free
# model, fixed by switching Hermes to the capable 400K gpt-5.4-mini (arc #913->#921). On a 400K
# window the 50% compaction leaves ~200K headroom, so these compaction knobs are no longer the
# primary fix — keep them only as a marginal tuning lever, not a required step. See
# docs/operations/hermes-control-plane.md § Model/provider.
#
# ⚠️ DO NOT RUN THIS FOR A "tokens per min (TPM)" RATE-LIMIT (2026-06-16 incident). This script
# RAISES compression.threshold (0.50 -> 0.75) = compact LATER = sessions grow BIGGER. That is the
# right direction for the doc-pruning problem this script was built for, but the WRONG direction for
# a per-minute rate limit (`Rate limit reached … on tokens per min (TPM): Limit 200000 …`). A bigger
# session re-sends MORE tokens per reply, so it hits the TPM ceiling sooner. For a TPM error, do the
# opposite — LOWER the threshold (e.g. `hermes config set compression.threshold 0.25`) so each call
# stays small, and/or raise the OpenAI TPM tier. Full incident + fix: docs/operations/hermes-session-reset.md
# § "Root cause clarification (2026-06-16)".
#
# WHY (original diagnosis): Hermes "forgets / misunderstands / loses the thread" because its gateway
# COMPACTS context at 50% of the model window — it summarizes the middle of the
# conversation and DELETES tool outputs larger than ~200 chars. SuperBot's docs are
# large, so even a short, clearly-directed session can cross 50% on the FIRST doc
# read — and Hermes then prunes the very doc it just read. Full diagnosis:
#   docs/operations/hermes-token-efficiency-investigation-2026-06-15.md
#
# WHAT THIS DOES (all reversible, via Hermes' own validated `hermes config set` CLI):
#   - backs up ~/.hermes/config.yaml (timestamped) before any change
#   - compression.threshold      0.50 -> 0.75   (compact LATER, so a doc survives more turns)
#   - compression.protect_last_n 20   -> 30     (keep more recent turns uncompressed)
#   - prompt_caching.cache_ttl   -> 1h          (attempted; key name varies by version)
#   - re-installs the sync-fixed SOUL.md (install-soul.sh) and reports its size vs budget
#   - runs `hermes config check` and reminds you to restart the gateway
#
# USAGE (on the VPS, as the `hermes` user, from the repo root):
#   bash scripts/hermes/apply_context_fixes.sh             # apply (backs up first)
#   bash scripts/hermes/apply_context_fixes.sh --dry-run   # show what it would do; change nothing
#   bash scripts/hermes/apply_context_fixes.sh --set-model=...  # DEPRECATED — prints why + points at `hermes model`
#
# ⚠️ --set-model is INTENTIONALLY a no-op now (2026-06-16). It used `hermes config set model`, but the
# model-switch playbook (docs/operations/hermes-control-plane.md § Model-switch playbook) proved that
# command changes only the *name* and reverts routing to the Nous catalog — wrong for the current
# own-key custom-provider setup. A bash script can't drive the interactive `hermes model` wizard, so
# the flag now explains this and exits instead of silently doing the wrong thing. Switch models by
# re-running `hermes model`.
#
# Provenance: added 2026-06-15 from the Hermes token-efficiency investigation.
# UNVERIFIED: the `hermes config set` calls cannot be exercised in CI (no Hermes there) — only
# --dry-run is. Re-confirm key names with `hermes config` / `hermes config check` on your version.
# Kill-switch (Q-0105): disposable operator convenience — delete this if the knobs change upstream
# or it proves unreliable across sessions.
set -uo pipefail

DRY_RUN=0
SET_MODEL=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --set-model=*) SET_MODEL="${arg#*=}" ;;
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_BIN="$(command -v hermes || echo "$HOME/.local/bin/hermes")"
CONFIG="${HERMES_HOME:-$HOME/.hermes}/config.yaml"

say() { printf '%s\n' "$*"; }
rule() { printf -- '------------------------------------------------------------\n'; }

# The reversible compression knobs (see the investigation doc's "Recommended config").
KEYS=("compression.threshold" "compression.protect_last_n" "prompt_caching.cache_ttl")
VALS=("0.75" "30" "1h")

rule
say "Hermes context-management fixes"
rule
say "hermes CLI : $HERMES_BIN"
say "config     : $CONFIG"
say "mode       : $([[ $DRY_RUN -eq 1 ]] && echo DRY-RUN || echo APPLY)"
rule

if [[ $DRY_RUN -eq 0 && ! -x "$HERMES_BIN" ]]; then
  say "✗ hermes CLI not found/executable at: $HERMES_BIN"
  say "  Run this on the VPS as the 'hermes' user (or --dry-run to preview anywhere)."
  exit 1
fi

# 1) Back up config.yaml (apply mode only).
if [[ $DRY_RUN -eq 0 && -f "$CONFIG" ]]; then
  cp "$CONFIG" "$CONFIG.bak.$(date +%Y%m%d_%H%M%S)"
  say "✓ backed up $CONFIG"
  rule
fi

# 2) Apply the knobs through the validated CLI (each set is non-fatal on its own).
set_key() {
  local key="$1" val="$2"
  if [[ $DRY_RUN -eq 1 ]]; then
    say "would run: hermes config set $key $val"
  elif "$HERMES_BIN" config set "$key" "$val"; then
    say "✓ set $key = $val"
  else
    say "⚠ could not set $key — the key name may differ on your version; check 'hermes config'."
  fi
}
for i in "${!KEYS[@]}"; do set_key "${KEYS[$i]}" "${VALS[$i]}"; done
# Model switch is NOT done here. `hermes config set model` only changes the name and reverts routing to
# the Nous catalog (model-switch playbook) — wrong for the own-key custom provider. Re-run `hermes
# model` instead. The flag stays only to catch old muscle memory and explain the correct path.
if [[ -n "$SET_MODEL" ]]; then
  say "⚠ --set-model is a no-op: 'hermes config set model' reverts routing to the Nous catalog."
  say "  To switch to '$SET_MODEL', re-run the wizard:  hermes model   (keeps the custom provider)"
  say "  Then allowlist the exact model id in your OpenAI project. See"
  say "  docs/operations/hermes-control-plane.md § Model-switch playbook."
fi
rule

# 3) Re-install the sync-fixed SOUL.md (+ its size guard reports headroom).
say "re-installing SOUL.md (carries the git-sync fix)…"
if [[ $DRY_RUN -eq 1 ]]; then
  say "would run: bash $SCRIPT_DIR/install-soul.sh"
  bash "$SCRIPT_DIR/install-soul.sh" --dry-run >/dev/null 2>&1 &&
    say "  (dry-run: install-soul.sh extraction OK)"
else
  bash "$SCRIPT_DIR/install-soul.sh"
fi
rule

# 4) Verify + next steps.
if [[ $DRY_RUN -eq 0 ]]; then
  say "verifying (hermes config check):"
  "$HERMES_BIN" config check 2>/dev/null | sed 's/^/    /' || say "    (check unavailable)"
  rule
  say "current settings — see 'hermes config' for the live model + values."
fi
say "tip: a LARGER context-window model pushes the 50% compaction line further out."
say "     to switch models, re-run:  hermes model   (NOT --set-model — see the playbook)"
rule
say "NEXT — restart the gateway to load the changes:"
say "     sudo systemctl restart hermes-gateway"
rule
