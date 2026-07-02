"""Render the project's content docs from templates + filled interview slots.

Templates use ``${slot_name}`` placeholders (``string.Template``). A slot the
interview has filled substitutes in; an unfilled slot is left as ``${slot_name}``
and reported — so a half-onboarded project's gaps stay visible rather than going
silently blank. Templates ship embedded in the bootstrap (the generated
``_TEMPLATES`` dict) and, in the source/pip layouts, under
``engine/templates/`` (inside the package so a wheel ships them).
"""

from __future__ import annotations

import re
from pathlib import Path
from string import Template
from typing import Any

_PLACEHOLDER_RE = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def find_placeholders(text: str) -> set[str]:
    """Return the set of ``${name}`` placeholders remaining in ``text``."""
    return set(_PLACEHOLDER_RE.findall(text))


def render(text: str, context: dict[str, str]) -> str:
    """Substitute ``${slot}`` placeholders from ``context`` (unfilled left as-is)."""
    return Template(text).safe_substitute(context)


def build_context(state: dict[str, Any]) -> dict[str, str]:
    """Build the substitution context from a state document's filled slots."""
    values = state.get("slot_values", {})
    return {slot: str(entry.get("value", "")) for slot, entry in values.items()}


def load_templates() -> dict[str, str]:
    """Return ``{filename: text}`` for every template (embedded or packaged).

    The single-file bootstrap embeds them as ``_TEMPLATES``; the source/pip
    layouts read ``engine/templates/`` (INSIDE the package, so a wheel ships
    them — they once lived a level up and a pip install silently had none).
    An empty template set is a hard error, never a silent no-op render.
    """
    embedded = globals().get("_TEMPLATES")
    if embedded is not None:
        return dict(embedded)
    root = Path(__file__).resolve().parent / "templates"
    templates = {
        p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.tmpl"))
    }
    if not templates:
        msg = f"no templates found at {root} — broken install"
        raise FileNotFoundError(msg)
    return templates
