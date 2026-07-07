"""Public ``/submit`` intake — the bug/suggestion form + INSERT path (unit P4).

Fills the P1 stub (plan §5 — P1 owns ``app.py`` and wires the routes; this module owns
its own ``router`` and the ``/submit`` behaviour, so it lands without touching
``app.py``). The flow, end to end (plan §2.3 / §4.2 / the layout note):

* ``GET /submit`` renders the form (``templates/submit.html``) — also the thank-you
  state after a successful POST (post/redirect/get), and a friendly "temporarily
  unavailable" state when the store is dormant.
* ``POST /submit`` is the only write the public site performs. In order:
  **honeypot** (a hidden field real users never fill → silently drop bots),
  **rate-limit** (per-IP sliding window, copied stdlib limiter — no shared import),
  **validate + sanitise + INSERT** one ``status='pending'`` row via
  ``submissions_db.insert_pending`` (which trims, strips control chars, length-caps,
  checks the required ``kind`` / ``title`` / ``body``, and stores a **salted IP hash**
  — never the raw IP). On success it redirects (PRG) to the thank-you state.

Security posture (plan §4.4): this module imports only the INSERT-only
``submissions_db`` write seam — it cannot read, list, or moderate. Nothing it stores is
ever shown publicly; every row is moderation-gated on the dev site before it reaches
GitHub. It never imports ``disbot`` (web-tier decoupling).

The form body is parsed with **stdlib** ``urllib.parse`` (no ``python-multipart``
dependency — mirrors the dashboard's ``_form`` helper); the app holds no secret beyond
the INSERT-only submissions DSN.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# The app puts botsite/ on sys.path (the dashboard-style shim in app.py) so these
# sibling imports resolve identically whether the app is loaded as a package, a
# top-level module (Railway Root Directory = botsite), or by file path in tests.
_BASE_DIR = Path(__file__).resolve().parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

import chrome  # noqa: E402  - sibling, after the sys.path shim above
import ratelimit  # noqa: E402  - sibling, after the sys.path shim above
import submissions_db  # noqa: E402  - sibling, after the sys.path shim above

# The form's own templates dir + the SHARED chrome context processor
# (``chrome.site_context``) so base.html's nav/footer render identically here as on the
# marketing app — notably the "Add to Discord" install button, which a separate Jinja
# env would otherwise render as an empty href. Still self-contained: ``chrome`` is a
# sibling module (no app.py coupling).
_templates = Jinja2Templates(
    directory=str(_BASE_DIR / "templates"),
    context_processors=[chrome.site_context],
)

# Hidden field a human never sees/fills; any value means an automated submitter.
_HONEYPOT_FIELD = "website"

# Per-IP abuse-brakes on the public, no-login form (plan §4.2 — "a few per minute, a
# couple dozen per hour"). Coarse + per-process; the moderation gate is the real
# spam-as-publication defense, these just blunt bursts. Module-level so tests can
# ``.reset()`` between cases.
_SUBMIT_LIMITER_MINUTE = ratelimit.SlidingWindowLimiter(
    max_events=5,
    window_seconds=60.0,
)
_SUBMIT_LIMITER_HOUR = ratelimit.SlidingWindowLimiter(
    max_events=24,
    window_seconds=3600.0,
)

# Surface choices (plan §2.3 — maps to the bug issue-template dropdown). Presentation
# only: an unknown value is dropped to NULL by the store's sanitiser, so this list is
# the form's options, not a security gate.
SURFACE_CHOICES: tuple[str, ...] = ("bot", "dashboard", "CI", "other")

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    """Best-effort client IP — first ``X-Forwarded-For`` hop (Railway proxy), else peer.

    Mirrors the dashboard's helper. Returns ``None`` when no address is resolvable so
    the stored ``source_ip_hash`` stays NULL rather than hashing a placeholder.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    client = request.client
    return client.host if client else None


async def _parse_form(request: Request) -> dict[str, str]:
    """Parse an ``application/x-www-form-urlencoded`` body (stdlib, no multipart).

    Same approach as ``dashboard/app.py._form`` — read the raw body and ``parse_qs``,
    so the public site needs no ``python-multipart`` dependency.
    """
    raw = (await request.body()).decode("utf-8", "replace")
    parsed = parse_qs(raw, keep_blank_values=True)
    return {key: values[0] for key, values in parsed.items()}


def _render_form(
    request: Request,
    *,
    status_code: int = 200,
    error: str | None = None,
    submitted: bool = False,
    values: dict[str, str] | None = None,
) -> HTMLResponse:
    """Render the form template with the shared state flags.

    One renderer for every state the single ``/submit`` template shows: the empty
    form, the post-redirect thank-you (``submitted``), a friendly validation error
    (``error`` — never internal text), and the dormant "unavailable" notice
    (``available`` is derived from the store). ``values`` re-populates the fields after
    a rejected POST so the user does not retype everything.
    """
    context = {
        "page": "submit",
        "available": submissions_db.is_configured(),
        "surface_choices": SURFACE_CHOICES,
        "kinds": (submissions_db.KIND_BUG, submissions_db.KIND_SUGGESTION),
        "honeypot_field": _HONEYPOT_FIELD,
        "error": error,
        "submitted": submitted,
        "values": values or {},
    }
    return _templates.TemplateResponse(
        request,
        "submit.html",
        context,
        status_code=status_code,
    )


@router.get("/submit", response_class=HTMLResponse)
def submit_form(request: Request) -> HTMLResponse:
    """Render the public bug/suggestion form (and the thank-you state after a POST).

    ``?about=command:warn`` (the v2 site's suggest-CTA links) prefills the title
    so the report arrives with its subject attached — the context the CTA
    promises is actually carried, not silently dropped. Jinja escapes the value
    on render; anything unparseable is simply ignored.
    """
    values: dict[str, str] = {}
    about = request.query_params.get("about", "")[:80]
    if about:
        prefix, _, name = about.partition(":")
        name = name.strip()
        if name and prefix == "command":
            values["title"] = f"!{name}: "
        elif name and prefix in ("feature", "game", "area"):
            values["title"] = f"{name}: "
    return _render_form(
        request,
        submitted=request.query_params.get("submitted") == "1",
        values=values,
    )


@router.post("/submit", response_model=None)
async def submit_create(request: Request) -> HTMLResponse | RedirectResponse:
    """Validate → honeypot → rate-limit → INSERT one ``pending`` row → thank-you.

    Returns a redirect (PRG) to the thank-you state on success so a refresh can't
    re-file; re-renders the form with a friendly message on validation failure or
    when the store is dormant. A tripped honeypot is silently treated as success
    (the bot sees a normal thank-you, learns nothing, and no row is written).
    """
    form = await _parse_form(request)

    # 1. Honeypot — a filled hidden field means an automated submitter. Silently
    #    pretend success (don't reveal the trap) and never touch the DB.
    if form.get(_HONEYPOT_FIELD, "").strip():
        return RedirectResponse("/submit?submitted=1", status_code=303)

    # 2. Rate-limit (per IP, both windows). A rejected call doesn't consume budget.
    #    Check both before short-circuiting so neither window is skipped by `or`.
    ip = _client_ip(request)
    limit_key = ip or "unknown"
    within_minute = _SUBMIT_LIMITER_MINUTE.allow(limit_key)
    within_hour = _SUBMIT_LIMITER_HOUR.allow(limit_key)
    if not (within_minute and within_hour):
        return _render_form(
            request,
            status_code=429,
            error="You're sending these a bit fast — please wait a minute and try again.",
            values=form,
        )

    # 3. Store dormant (no DSN configured) — friendly notice, no error leaked.
    if not submissions_db.is_configured():
        return _render_form(
            request,
            status_code=503,
            error="Submissions are temporarily unavailable — please try again later.",
            values=form,
        )

    # 4. Validate + sanitise + INSERT. submissions_db.insert_pending is the single
    #    write path: it trims, strips control chars, length-caps, enforces the
    #    required kind/title/body, and stores a SALTED IP hash (never the raw IP).
    try:
        await submissions_db.insert_pending(
            kind=form.get("kind", ""),
            title=form.get("title", ""),
            body=form.get("body", ""),
            surface=form.get("surface") or None,
            contact=form.get("contact") or None,
            source_ip=ip,
        )
    except submissions_db.SubmissionValidationError:
        # Friendly, generic message — never echo the raw validation detail.
        return _render_form(
            request,
            status_code=400,
            error="Please pick a category and fill in both a title and a description.",
            values=form,
        )
    except submissions_db.SubmissionsNotConfiguredError:
        # Raced to dormant between the check above and the insert — same friendly state.
        return _render_form(
            request,
            status_code=503,
            error="Submissions are temporarily unavailable — please try again later.",
            values=form,
        )

    # 5. Success → PRG to the thank-you state (never re-files on refresh).
    return RedirectResponse("/submit?submitted=1", status_code=303)
