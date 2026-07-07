"""Shared template chrome for the bot site — injected into BOTH Jinja environments.

The marketing app (``app.py``) and the ``/submit`` router (``submit.py``) each own a
``Jinja2Templates`` instance but render the **same** ``base.html`` layout. Anything the
layout needs — the freshness-badge build meta and the "Add to Discord" install URL —
must be injected into *both* environments, or a page rendered by one env shows empty
chrome. Defining the context processor here (imported by both) keeps it DRY.

Regression this prevents: ``/submit`` is rendered by ``submit.py``'s own Jinja env, so
when ``base.html``'s nav started using ``{{ add_url }}`` the submit page rendered a dead
``href=""`` install button. Sharing this one processor fixes it at the root (and also
gives ``/submit`` the same freshness badge as every other page).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import Request

# Same sibling-import shim as app.py / submit.py — the module may be imported by file
# path in tests, as a package, or as a top-level module on Railway (Root Dir = botsite).
_BASE_DIR = Path(__file__).resolve().parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

import data_loader  # noqa: E402  - sibling, after the sys.path shim above

# The bot's public install link — single-sourced in site_data.py (stdlib) so the
# Jinja chrome and the generated SBDATA (ADD_URL) can never drift apart.
from site_data import ADD_TO_DISCORD_URL  # noqa: E402,F401  - sibling re-export


def site_context(request: Request) -> dict[str, Any]:
    """Context merged into EVERY page across both Jinja envs (app + submit router).

    Carries the generated-build freshness band + the install CTA URL so the shared
    chrome (``base.html``) renders identically on every route. The public site never
    claims live state here.
    """
    data = data_loader.load_site_data()
    return {
        "build": data_loader.build_meta(data),
        "site_counts": data.get("counts", {}),
        "add_url": ADD_TO_DISCORD_URL,
    }
