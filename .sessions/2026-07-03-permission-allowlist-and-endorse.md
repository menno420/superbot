# 2026-07-03 — Permission allowlist fix + Q-0228 centralization endorsement (owner-live)

> **Status:** `complete` — PR #1683. Owner-directed housekeeping continuing the rebuild
> conventions session. Executable-config + docs; no `disbot/` code.

## What shipped (PR #1683)

1. **`.claude/settings.json`** — added whole-MCP-server allow entries (`mcp__Claude_Code_Remote`,
   `mcp__github`, `mcp__codegraph`, `mcp__context7`) so MCP tools like `send_later` stop
   prompting. The destructive-ops `ask` brake (rm -r, force-push, railway, sudo, psql, docker)
   is untouched. Owner-directed → applied under the Q-0106 executable-config exception.
2. **Router Q-0229** — provenance + the diagnosis: `defaultMode: bypassPermissions` and
   `skipDangerousModePermissionPrompt` were **already** set, but the web/remote surface
   downgrades project-scope bypass for safety and consults the explicit `allow` list instead —
   so the allowlist is the reliable lever, and the truly universal switch lives at the
   code.claude.com environment level. (`AskUserQuestion` prompting is by design, not a gate.)
3. **Q-0228 + conventions log §6** — moved from "proposed, pending reaction" to
   **owner-endorsed foundations** (the C-1…C-7 invocation-stack centralizations), per the owner's
   confirmation that they're "good foundations and should be documented."

## 💡 Session idea (Q-0089)

Covered by this session's earlier cards (#1679 schema-growth ledger, #1680 invocation
centralization set) — per Q-0089's "forced filler is worse than none," no new idea is minted for
this small housekeeping PR; the genuine new idea this working session produced is the C-1…C-7 set,
now owner-endorsed.

## ⟲ Previous-session review (Q-0102)

Previous card: **#1680 (conventions freeze).** It correctly captured C-1…C-7 as *proposals* rather
than decisions — good discipline (didn't put words in the owner's mouth), and the owner did then
endorse them, validating the capture-as-proposal call. **Improvement surfaced:** the permission
friction that triggered *this* PR is a textbook Q-0194 "friction → guard" case — a recurring
prompt that interrupted the session. The durable guard was the allowlist edit (config tier), which
is exactly the right rung of the enforce-ladder; the lesson for next time is to reach for the
config guard the *first* time a prompt recurs, not the third.

## Docs audit (Q-0104)

- `.claude/settings.json` JSON validated; `check_docs --strict` ✓ (run at close)
- Owner decision → Q-0229; Q-0228 status updated; conventions §6 updated ✓
- Ledger entry #1683 added ✓
- Chat-only residue: none — the "universal allow" answer + the environment-level lever are in Q-0229.

## ⚑ Self-initiated

None — the settings change is owner-directed (Q-0229), the Q-0228 update reflects the owner's
explicit endorsement.
