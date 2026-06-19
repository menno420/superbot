"""SuperBot public marketing site — a decoupled web app that renders generated JSON.

The **public** half of the website two-site split
(``docs/planning/website-two-site-split-plan-2026-06-19.md``): a marketing +
reference site (features, command reference, changelog, status) plus a public
bug/suggestion intake form. It is a *separate Railway service* from both the bot and
the developer dashboard.

Two hard invariants this package must never break:

1. **Never import ``disbot``.** It reads only the committed public subset
   ``botsite/data/site.json`` (produced by ``scripts/export_dashboard_data.py``) —
   the same decoupling the dashboard has, with a *redaction-by-construction* data
   boundary (the subset physically cannot contain a private family).
2. **Holds at most one secret** — the INSERT-only submissions DSN (plan §4.4). It
   never holds the GitHub mirror token, the control-API token, or any OAuth secret.

The future gated "manage my server" surface is a **separate service** (plan §4.4),
NOT a router mounted here — so this marketing app stays secret-free and the gated
manager drops in without re-coupling. See ``botsite/README.md``.
"""
