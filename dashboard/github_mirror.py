"""GitHub-issue mirror — the approve-side of the submission flow (dev-site only).

When the owner **approves** a pending submission on ``/admin/moderation``, the dev site
creates **one** GitHub issue in ``menno420/superbot`` from it (plan §2.3 / §4.3). This
module is that single, least-privilege issue-create client.

**Least privilege (plan §4.3).** It reads a fine-grained PAT scoped to *only*
``menno420/superbot`` with the *single* permission **Issues: Read & write** from
``GITHUB_ISSUE_MIRROR_TOKEN``. The token + this action live **only on the dev site** —
never on the public bot site, never in the repo, never in ``site.json`` (plan §4.4
secret matrix). The call runs server-side on approval, behind the owner gate, so the
token never reaches a browser.

**Idempotent (plan §4.2).** ``create_issue`` is a pure POST; the *double-file guard*
lives in the caller — ``dashboard.submissions_db.attach_issue_url`` only records a URL
when it is still NULL, and the moderation route mirrors **only** a still-``pending`` row
whose URL is NULL (a re-approve / double-click is a no-op there). This module therefore
stays a thin, side-effect-honest client: one approved submission → one issue body shaped
by the matching ``.github/ISSUE_TEMPLATE/`` family + its label (``bug`` / ``enhancement``).

Decoupling: part of the web tier — it **never imports** ``disbot``. It talks to the
GitHub REST API with ``httpx`` (already a dashboard dependency, lazy-imported so the
module loads where the driver is absent), never a bot seam.

**Dormant by default.** With ``GITHUB_ISSUE_MIRROR_TOKEN`` unset, :func:`is_configured`
is ``False`` and the moderation page renders an "approve disabled until configured"
state instead of attempting a mirror (same discipline as the control API + the
submissions DB). The owner sets the token on the dev-site Railway service at rollout.
"""

from __future__ import annotations

import html
import os
from typing import Any

# The single repository this mirror is scoped to (plan §4.3 — the fine-grained PAT is
# repo-scoped to exactly this). Hardcoded, not env-driven: a mis-set env must never be
# able to redirect approved user submissions into some other repository.
REPO_OWNER = "menno420"
REPO_NAME = "superbot"

GITHUB_API_BASE = "https://api.github.com"
# GitHub's documented Issues-create media type + API version pin.
_ACCEPT = "application/vnd.github+json"
_API_VERSION = "2022-11-28"

_TOKEN_ENV = "GITHUB_ISSUE_MIRROR_TOKEN"

# kind (submissions.kind: 'bug' | 'suggestion') -> the issue label that matches the
# corresponding .github/ISSUE_TEMPLATE/ family (bug_report.yml -> "bug",
# feature_request.yml -> "enhancement"). Anything else falls back to no special label.
_KIND_LABEL = {"bug": "bug", "suggestion": "enhancement"}

# A human title prefix per kind, mirroring the issue-template ``name`` emoji so a
# mirrored issue is visually consistent with a hand-filed one.
_KIND_TITLE_PREFIX = {"bug": "🐞", "suggestion": "💡"}


class MirrorNotConfiguredError(RuntimeError):
    """Raised by :func:`create_issue` when ``GITHUB_ISSUE_MIRROR_TOKEN`` is unset."""


class MirrorError(RuntimeError):
    """Raised when GitHub rejects the issue-create call (non-2xx response)."""


def token() -> str | None:
    """Return the mirror PAT, or ``None`` when the mirror is dormant."""
    value = os.environ.get(_TOKEN_ENV, "").strip()
    return value or None


def is_configured() -> bool:
    """``True`` when the GitHub-issue mirror token is set (approve can mirror)."""
    return token() is not None


def _require_token() -> str:
    target = token()
    if target is None:
        raise MirrorNotConfiguredError(
            f"{_TOKEN_ENV} is not set — the GitHub-issue mirror is dormant",
        )
    return target


def _clean(text: str | None) -> str:
    """Trim a submitted value; never ``None`` (so the body builder stays simple)."""
    return (text or "").strip()


def issue_title(submission: dict[str, Any]) -> str:
    """The mirrored issue title — the submitted ``title``, prefixed by kind emoji.

    Plain text only: the title is stored plain and GitHub renders titles literally
    (no markdown/HTML), so there is nothing to escape — but it is length-clamped so a
    pathological submission can't create an unwieldy issue title.
    """
    kind = _clean(submission.get("kind"))
    title = _clean(submission.get("title")) or "(no title)"
    prefix = _KIND_TITLE_PREFIX.get(kind, "")
    full = f"{prefix} {title}".strip() if prefix else title
    return full[:240]


def issue_labels(submission: dict[str, Any]) -> list[str]:
    """The labels for the mirrored issue — the kind's template label (``bug`` /
    ``enhancement``), matching the ``.github/ISSUE_TEMPLATE/`` family, or ``[]``.
    """
    label = _KIND_LABEL.get(_clean(submission.get("kind")))
    return [label] if label else []


def issue_body(submission: dict[str, Any]) -> str:
    """Render the GitHub-issue **markdown body** from a submission, mirroring the
    matching ``.github/ISSUE_TEMPLATE/`` shape (plan §4.3).

    The submitted free text (``body``, ``surface``) is **HTML-escaped** before being
    placed into the markdown — it is untrusted public input (plan §4.2), and although
    GitHub does not execute HTML the way a browser would, escaping keeps the rendered
    issue faithful to what the user typed and removes any raw-HTML surprise. A small
    provenance footer marks the issue as mirrored from a moderated submission (and that
    the original contact, if any, is intentionally withheld — never published, plan
    §2.3).
    """
    kind = _clean(submission.get("kind"))
    body = html.escape(_clean(submission.get("body"))) or "_(no description provided)_"
    surface = html.escape(_clean(submission.get("surface")))

    lines: list[str] = []
    if kind == "bug":
        lines.append("### Where did it happen?")
        lines.append("")
        lines.append(surface or "_(not specified)_")
        lines.append("")
        lines.append("### Report")
    else:  # suggestion / anything else → the feature-request shape
        lines.append("### Proposal")
    lines.append("")
    lines.append(body)
    lines.append("")
    lines.append("---")
    lines.append(
        "_Mirrored from a moderated public submission on the SuperBot site. "
        "Submitter contact, if provided, is withheld._",
    )
    return "\n".join(lines)


async def create_issue(submission: dict[str, Any]) -> str:
    """Create one GitHub issue from an approved ``submission``; return its HTML URL.

    Shapes the issue from the matching ``.github/ISSUE_TEMPLATE/`` family
    (:func:`issue_title` / :func:`issue_body` / :func:`issue_labels`) and POSTs it to
    ``menno420/superbot`` with the least-privilege ``GITHUB_ISSUE_MIRROR_TOKEN``.

    Raises :class:`MirrorNotConfiguredError` when dormant and :class:`MirrorError` on a
    non-2xx response (the moderation route surfaces that as a flash and leaves the row
    ``pending``, so the owner can retry — the row is only flipped to ``approved`` after
    a successful mirror + URL store).
    """
    import httpx  # lazy — keeps module import-safe where httpx is absent

    auth_token = _require_token()
    url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": _ACCEPT,
        "X-GitHub-Api-Version": _API_VERSION,
    }
    payload: dict[str, Any] = {
        "title": issue_title(submission),
        "body": issue_body(submission),
    }
    labels = issue_labels(submission)
    if labels:
        payload["labels"] = labels

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code not in (200, 201):
        raise MirrorError(
            f"GitHub issue create failed (HTTP {resp.status_code})",
        )
    data = resp.json()
    issue_url = data.get("html_url")
    if not issue_url:
        raise MirrorError("GitHub issue create returned no html_url")
    return str(issue_url)
