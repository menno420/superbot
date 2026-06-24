"""Welcome greeting-card renderer — the welcome phase-2 image (Q-0110).

The production home for the join greeting card promoted from the UX-lab
prototype (``utils/ux_patterns/image_builders.render_welcome_card``, which now
delegates here so the gallery preview and the live feature share one source of
truth).

Same contract as :mod:`utils.mining_render` / :mod:`utils.character_render`:
**lazy PIL import**, ``bytes | None`` return (``None`` = Pillow unavailable →
the welcome service keeps its embed-only fallback), pure inputs in / bytes out
— **no network**.  The avatar is a generated initials disc (the
fallback-silhouette path, per the platform-limits doc §4): rendering never
fetches the member's real avatar, so the card is content-free and cannot block
or fail on a CDN round-trip.  The real avatar still rides the embed thumbnail.
"""

from __future__ import annotations

from utils.card_render import get_theme, initials, new_canvas

# Card geometry.
_WIDTH = 960
_HEIGHT = 360


def render_welcome_card(
    member_name: str = "AstroFox",
    server_name: str = "Demo Server",
    member_number: int = 1235,
) -> bytes | None:
    """Render the join greeting card: avatar disc + greeting + member number.

    Pure / no-network; returns JPEG bytes, or ``None`` when Pillow is absent so
    callers fall back to the embed-only greeting.  The defaults make it a
    self-contained gallery sample (the UX-lab preview calls it bare).

    Drawn on the shared :class:`utils.card_render.CardCanvas` (theme
    ``midnight`` — the dark-blurple palette this card always used), so the
    palette, font loader, width-fit and initials-disc primitives are the one
    engine code path, not private copies.
    """
    canvas = new_canvas(_WIDTH, _HEIGHT, get_theme("midnight"))
    if canvas is None:  # Pillow unavailable → caller keeps the embed fallback.
        return None
    canvas.initials_disc((180, 180), 96, initials(member_name), size=56)
    # Text column: x=340 to the right margin — clamp both lines so an unbounded
    # member/server name can never run off the card edge.
    text_x = 340
    text_max = _WIDTH - text_x - 60
    canvas.text(
        (text_x, 110),
        f"Welcome, {member_name}!",
        size=56,
        bold=True,
        max_width=text_max,
    )
    canvas.text(
        (text_x + 2, 196),
        f"You are member #{member_number:,} of {server_name}",
        size=30,
        color=canvas.theme.subtle,
        max_width=text_max,
    )
    canvas.draw.line(
        (text_x, 260, _WIDTH - 60, 260),
        fill=canvas.theme.accent,
        width=3,
    )
    return canvas.to_jpeg(quality=85)


__all__ = ["render_welcome_card"]
