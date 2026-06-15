# Session — Hermes model-switch playbook (close out the saga)

> **Status:** `in-progress` — born-red per Q-0133. gpt-5.4-mini is **CONFIRMED WORKING** on the
> owner's own OpenAI key (live reply: "Hi! How can I help?"). Closing out: correct the #916
> "live-reply pending" line and capture the full provider-maze playbook so the next setup is 5
> minutes, not the 2.5 hours this took.

## What I'm about to do (docs-only)
- `hermes-control-plane.md` Model/provider → mark **CONFIRMED WORKING** (custom OpenAI-compatible
  provider via `hermes model`, gpt-5.4-mini, alias added to the project allowlist), correct the
  now-wrong `config set model openai/...` command (prefix routes to nous), and add the **6-trap
  model-switch playbook**: empty `providers:{}` → nous catalog default · prefix routing · stale
  built-in openai-api listing (gpt-4o-mini only) · gpt-4o-mini encrypted-content/reasoning 400 · org
  verification · exact-match allowlist alias-vs-dated-snapshot trap.
- `hermes-terminal-cheatsheet.md` → fix the misleading `config set model openai/...` line; use the
  `hermes model` wizard; point at the playbook.
