# Session — EAP email: two-part / two-author / two-reviewer restructure

> **Status:** `complete`

## What this session did
Owner-directed (continues the EAP-feedback thread). Restructured the send-ready Anthropic email
(`docs/planning/projects-eap-anthropic-email-2026-07-08.md`) into the owner's two-consumers form:

- **Framing note** to Anthropic: the product has **two consumers** (operator + agent workforce), so
  the feedback is written by both and asks to be read by both. Reframed the subject to "feedback from
  both of its users."
- **Part 1 — From the operator** (owner writes it; left a `[Menno writes this…]` scaffold with beats,
  no prose put in his voice).
- **Part 2 — From the project's agents** (the existing positives/negatives/tried/value/asks content),
  now **tagged 👤 / 🤖 / 👤🤖** per finding by which consumer it affects — making the two-users thesis
  concrete rather than just stated.
- **Closing — dual-review request**: a human + a Claude session pointed at the public repo, with
  entry points (probe report, `.sessions/`, claims, eval log, the future `docs/eap/` self-audit) and
  concrete verification tasks — dogfooding their product on our data.

Docs-only. `check_docs --strict` green. Prior PR #1853 (the pre-restructure email) already merged;
this is a fresh branch off main.

## ⚑ Open for the owner (decide-and-flag)
- **Part 1 is yours to write** — the scaffold marks where; everything else is drafted.
- **Keep or cut the framing paragraph** — the structure can speak for itself if you'd rather.
- The **self-audit report** referenced in the closing doesn't exist yet (`docs/eap/`); it's the
  pending Task-B probe. If the email goes before that runs, soften that bullet to "planned."

## 💡 Session idea (Q-0089)
`docs/ideas/agent-readable-external-reviewer-entrypoint-2026-07-08.md` — a stable top-level
`EXTERNAL-REVIEWER-START-HERE.md` written for an external agent reviewer arriving cold with no
injected `CLAUDE.md`; the external mirror of `AGENT_ORIENTATION.md`. Surfaced directly by the
two-reviewer ask (we invite an outside agent to read the repo but give it no front door). Dedup-checked
against `AGENT_ORIENTATION.md` and the self-audit idea.

## ⟲ Previous-session review (Q-0102)
Previous card (`2026-07-08-eap-email-refresh-forward-only-project.md`) did well: it consolidated a
split email into one canonical send-from doc and made the Skip-all-approvals finding the value anchor
cleanly. **What it could have done better:** it structured the email around *content* (positives/
negatives) but not around *audience* — the two-consumers structure the owner asked for this session
was latent in the findings all along (they split 👤/🤖 naturally), and a sharper session might have
proposed that framing itself rather than waiting for the owner to. **System improvement surfaced:**
findings were being written audience-agnostic; going forward, EAP findings should carry the 👤/🤖
consumer tag at *capture* time in the evaluation log, not just at email-assembly time — so the
two-audience view is always available for free. (Candidate convention, not yet promoted.)

## 📋 Doc audit (Q-0104)
`check_docs --strict` green (new idea reachable, badges valid, email doc still `reference`). No
living-ledger entry needed until this PR merges (checker covers it then). Nothing from this session
lives only in chat: the restructured email, the new idea, and the open owner-decisions all have
durable homes. No new binding rule → no router Q needed.
