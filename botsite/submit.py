"""Public ``/submit`` intake — APIRouter (STUB, filled by a later unit).

This is the *seam* the bot-site app mounts up front (``app.include_router(router)``)
so the app boots with every route wired (plan §5 — P1 owns ``app.py`` and wires all
routes; the submit module owns its own router). **This unit ships an empty router on
purpose** — the real intake (the ``GET``/``POST /submit`` form + honeypot + rate-limit
+ validation + the INSERT via ``botsite.submissions_db.insert_pending``) is unit P4
(plan §5), which owns this file's real content. Keeping the router here, owned by this
module, is what keeps P1's ``app.py`` the single owner of routing while P4 fills the
behaviour without editing ``app.py``.

Contract for P4 (do not change the export name):
* keep ``router`` as the module-level :class:`fastapi.APIRouter` instance,
* add ``GET /submit`` (render the form) + ``POST /submit`` (validate → honeypot →
  rate-limit → ``insert_pending(status='pending')`` → thank-you redirect),
* the form's fields must cover every non-defaulted ``submissions`` column
  (``kind`` / ``title`` / ``body`` / ``surface`` / optional ``contact``) — see
  ``botsite/migrations/001_submissions.sql`` and plan §2.3 / the layout note,
* render the stored body **escaped**; never list submissions publicly.

Until then the router carries no routes, so mounting it is a safe no-op and ``/submit``
simply 404s (the nav/footer can hide the link until P4 lands).
"""

from __future__ import annotations

from fastapi import APIRouter

# The mounted router. Empty by design (P1 stub); P4 attaches the /submit routes.
router = APIRouter()
