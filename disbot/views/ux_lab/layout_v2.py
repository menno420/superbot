"""UX Lab wing 5 — Components V2 layouts (EXPERIMENTAL lane).

A Components-V2 message replaces ``content``/``embeds`` entirely, so these
exhibits cannot render inside the classic wing browser. Each browser page
explains the layout and carries a **📤 Render** button that sends the real
``LayoutView`` message into the channel (self-deleting). Send failures are
reported verbatim — a failed render IS probe data.

Intentional divergence (architecture note): ``_LabLayout`` extends
``discord.ui.LayoutView`` directly — it cannot extend ``BaseView`` because
LayoutView is a sibling of ``discord.ui.View``, not a subclass. This is the
lab's sanctioned experimental lineage (UX Lab plan §2); adopting LayoutView
for real panels stays a separate ADR decision. Author-lock and timeout
semantics are mirrored from ``BaseView`` below.
"""

from __future__ import annotations

import discord

from utils.ux_patterns import PatternCategory, PatternSpec, PatternStatus, register
from views.ux_lab.wing import ExhibitRender, ExhibitWingView

_CAT = PatternCategory.LAYOUT_V2
_CV2_LIMITS = (
    "40 components total (nested count) per message",
    "4000 display characters across all text items",
    "replaces content/embeds; polls/stickers unavailable",
)
# Stable public placeholder images (Discord's default avatars).
_AVATARS = tuple(f"https://cdn.discordapp.com/embed/avatars/{n}.png" for n in range(5))
_RENDER_TTL = 120  # seconds before a rendered CV2 demo message self-deletes


def _cv2_spec(
    pattern_id: str,
    title: str,
    *,
    recommended_for: tuple[str, ...],
    anti_patterns: tuple[str, ...] = (),
    notes: str = "",
    extra_limits: tuple[str, ...] = (),
) -> None:
    register(
        PatternSpec(
            pattern_id=pattern_id,
            title=title,
            category=_CAT,
            status=PatternStatus.EXPERIMENTAL,
            uses_components_v2=True,
            recommended_for=recommended_for,
            anti_patterns=anti_patterns,
            limits=(*extra_limits, *_CV2_LIMITS),
            notes=notes or "Press 📤 Render — the layout posts below (self-deletes).",
        ),
    )


_cv2_spec(
    "cv2_text_only",
    "Text-display message (no embed chrome)",
    recommended_for=("long-form markdown without the embed frame",),
    anti_patterns=("content that needs fields/columns — embeds still win there",),
)
_cv2_spec(
    "cv2_section_accessory",
    "Sections with thumbnail / button accessory",
    recommended_for=("list rows with a per-row image or action",),
    extra_limits=("≤3 text displays per section + exactly 1 accessory",),
)
_cv2_spec(
    "cv2_container_dashboard",
    "Container dashboard (accent colour card)",
    recommended_for=("rich status cards without embeds; the 'future panel' look",),
)
_cv2_spec(
    "cv2_media_gallery",
    "Media gallery grid",
    recommended_for=("image sets (welcome banners, screenshots) in one grid",),
    extra_limits=("≤10 items per gallery",),
)
_cv2_spec(
    "cv2_file_display",
    "Inline file component",
    recommended_for=("showing a generated text/log file inside the message body",),
    extra_limits=("the attachment must be referenced by the component",),
)
_cv2_spec(
    "cv2_settings_page",
    "Settings page recreation (the SettingsHub comparison)",
    recommended_for=("judging whether real settings panels should adopt CV2",),
    anti_patterns=("adopting for real panels before the ADR decision",),
)
_cv2_spec(
    "cv2_mobile_compact",
    "Dense vs compact (the phone check)",
    recommended_for=("checking a layout on desktop AND a phone before approving",),
    notes="Render it, then open Discord on your phone — same message, different feel.",
)
_cv2_spec(
    "cv2_interactive_mix",
    "Interactive components inside containers",
    recommended_for=("verifying buttons/selects fire normally inside CV2",),
)


class _LabLayout(discord.ui.LayoutView):
    """Author-locked, short-lived LayoutView for lab renders.

    Mirrors the two BaseView behaviors that matter here: only the invoker
    may interact, and the message is short-lived (``delete_after`` on send
    handles cleanup, so no ``on_timeout`` edit is needed).
    """

    def __init__(self, author_id: int) -> None:
        super().__init__(timeout=_RENDER_TTL)
        self._author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self._author_id:
            await interaction.response.send_message(
                "This demo isn't yours.",
                ephemeral=True,
            )
            return False
        return True


def _ack_button(label: str, *, style: discord.ButtonStyle) -> discord.ui.Button:  # type: ignore[type-arg]
    btn: discord.ui.Button = discord.ui.Button(label=label, style=style)  # type: ignore[type-arg]

    async def _cb(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"**{label}** fired from inside a Components-V2 container.",
            ephemeral=True,
        )

    btn.callback = _cb  # type: ignore[method-assign]
    return btn


class LayoutWingView(ExhibitWingView):
    """Wing 5 — Components V2 (browser pages + real CV2 renders)."""

    WING_TITLE = "Components V2"
    WING_EMOJI = "🧱"

    def _exhibit_ids(self) -> tuple[str, ...]:
        return (
            "cv2_text_only",
            "cv2_section_accessory",
            "cv2_container_dashboard",
            "cv2_media_gallery",
            "cv2_file_display",
            "cv2_settings_page",
            "cv2_mobile_compact",
            "cv2_interactive_mix",
        )

    # -- LayoutView builders (one per exhibit) --------------------------------

    def _build_text_only(self, author_id: int) -> _LabLayout:
        view = _LabLayout(author_id)
        view.add_item(
            discord.ui.TextDisplay(
                "## Pure text display\n"
                "This message has **no embed and no `content`** — everything "
                "you read is a `TextDisplay` component.\n"
                "- full markdown\n- no coloured sidebar\n- 4000-char budget",
            ),
        )
        return view

    def _build_sections(self, author_id: int) -> _LabLayout:
        view = _LabLayout(author_id)
        view.add_item(
            discord.ui.Section(
                "**AstroFox** · Lv 42",
                "Top miner this week",
                accessory=discord.ui.Thumbnail(_AVATARS[0]),
            ),
        )
        view.add_item(discord.ui.Separator())
        view.add_item(
            discord.ui.Section(
                "**BananaMage** · Lv 39",
                "Closing in fast",
                accessory=discord.ui.Thumbnail(_AVATARS[1]),
            ),
        )
        view.add_item(discord.ui.Separator())
        view.add_item(
            discord.ui.Section(
                "**Manage members**",
                "A section can carry a button instead of an image →",
                accessory=_ack_button("Open", style=discord.ButtonStyle.primary),
            ),
        )
        return view

    def _build_container(self, author_id: int) -> _LabLayout:
        view = _LabLayout(author_id)
        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay("## 🩺 Server health"),
                discord.ui.TextDisplay(
                    "Gateway **online** · DB **12 ms** · 3 managed tasks",
                ),
                discord.ui.Separator(spacing=discord.SeparatorSpacing.large),
                discord.ui.TextDisplay("-# accent-coloured container, no embed"),
                discord.ui.ActionRow(
                    _ack_button("Refresh", style=discord.ButtonStyle.secondary),
                    _ack_button("Details", style=discord.ButtonStyle.primary),
                ),
                accent_colour=discord.Colour.green(),
            ),
        )
        return view

    def _build_gallery(self, author_id: int) -> _LabLayout:
        view = _LabLayout(author_id)
        view.add_item(discord.ui.TextDisplay("**Media gallery** — 4 items:"))
        view.add_item(
            discord.ui.MediaGallery(
                *(
                    discord.MediaGalleryItem(
                        url,
                        description=f"placeholder avatar {n}",
                    )
                    for n, url in enumerate(_AVATARS[:4])
                ),
            ),
        )
        return view

    def _build_file(self, author_id: int) -> tuple[_LabLayout, list[discord.File]]:
        view = _LabLayout(author_id)
        view.add_item(
            discord.ui.TextDisplay("**Inline file** — rendered in the body:"),
        )
        view.add_item(discord.ui.File("attachment://uxlab-demo.txt"))
        payload = (
            "UX Lab file-component demo\n"
            "==========================\n"
            "A CV2 message must reference every attachment via a component\n"
            "(File / Thumbnail / MediaGallery) — unreferenced uploads are\n"
            "rejected. This file proves the File component path works.\n"
        )
        import io  # noqa: PLC0415 — tiny, send-path only

        file = discord.File(
            io.BytesIO(payload.encode()),
            filename="uxlab-demo.txt",
            description="UX Lab file-component demo text file",
        )
        return view, [file]

    def _build_settings_page(self, author_id: int) -> _LabLayout:
        view = _LabLayout(author_id)
        rows = (
            ("Welcome messages", "ON", discord.ButtonStyle.success),
            ("Server logging", "off", discord.ButtonStyle.secondary),
            ("Automod", "ON", discord.ButtonStyle.success),
        )
        children: list[discord.ui.Item] = [  # type: ignore[type-arg]
            discord.ui.TextDisplay("## ⚙️ Module settings (CV2 recreation)"),
        ]
        for name, state, style in rows:
            children.append(discord.ui.Separator())
            children.append(
                discord.ui.Section(
                    f"**{name}**",
                    f"Currently **{state}** — fake toggle",
                    accessory=_ack_button(state, style=style),
                ),
            )
        view.add_item(
            discord.ui.Container(
                *children,
                accent_colour=discord.Colour.blurple(),
            ),
        )
        return view

    def _build_mobile_compact(self, author_id: int) -> _LabLayout:
        view = _LabLayout(author_id)
        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay("## Dense"),
                discord.ui.TextDisplay(
                    "Three stats on one line: **42** level · **13,370** coins "
                    "· **17🔥** streak — reads fine on desktop, cramped on "
                    "a phone.",
                ),
                accent_colour=discord.Colour.orange(),
            ),
        )
        view.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay("## Compact"),
                discord.ui.TextDisplay("Level **42**"),
                discord.ui.TextDisplay("Coins **13,370**"),
                discord.ui.TextDisplay("Streak **17** 🔥"),
                accent_colour=discord.Colour.green(),
            ),
        )
        view.add_item(
            discord.ui.TextDisplay(
                "-# Open this on your phone — pick the one that survives.",
            ),
        )
        return view

    def _build_interactive(self, author_id: int) -> _LabLayout:
        view = _LabLayout(author_id)
        sel: discord.ui.Select = discord.ui.Select(  # type: ignore[type-arg]
            placeholder="A select inside CV2…",
            options=[discord.SelectOption(label=f"Choice {n}") for n in range(1, 4)],
        )

        async def _pick(interaction: discord.Interaction) -> None:
            await interaction.response.send_message(
                f"Select fired inside CV2: **{sel.values[0]}**",
                ephemeral=True,
            )

        sel.callback = _pick  # type: ignore[method-assign]
        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay("**Interaction parity check**"),
                discord.ui.ActionRow(
                    _ack_button("Button A", style=discord.ButtonStyle.primary),
                    _ack_button("Button B", style=discord.ButtonStyle.secondary),
                ),
                discord.ui.ActionRow(sel),
                accent_colour=discord.Colour.purple(),
            ),
        )
        return view

    # -- browser pages ---------------------------------------------------------

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        explainers = {
            "cv2_text_only": "A message that is *only* TextDisplay components.",
            "cv2_section_accessory": "Rows of text with a thumbnail or button "
            "hanging off each section.",
            "cv2_container_dashboard": "An accent-coloured container card with "
            "text, separator, and an action row — no embed anywhere.",
            "cv2_media_gallery": "Four placeholder images in the native grid.",
            "cv2_file_display": "A generated text file rendered inline via the "
            "File component.",
            "cv2_settings_page": "Today's SettingsHub re-imagined as CV2 "
            "sections with toggle accessories — the direct comparison target.",
            "cv2_mobile_compact": "The same stats twice — dense vs compact — "
            "for a desktop-vs-phone judgement call.",
            "cv2_interactive_mix": "Buttons and a select living inside a "
            "container; every callback answers ephemerally.",
        }
        header = discord.Embed(
            title=f"🧱 {pattern_id}",
            description=(
                f"{explainers[pattern_id]}\n\n"
                "**📤 Render** posts the real Components-V2 message below "
                f"(self-deletes after {_RENDER_TTL}s). A send failure is "
                "reported verbatim — that's probe data, not a bug to hide."
            ),
            color=discord.Color.dark_teal(),
        )
        btn = self.demo_button(
            "📤 Render this layout",
            style=discord.ButtonStyle.primary,
            row=0,
        )

        async def _render(interaction: discord.Interaction) -> None:
            channel = interaction.channel
            if channel is None or not isinstance(channel, discord.abc.Messageable):
                await self.ack(interaction, "No sendable channel here.")
                return
            files: list[discord.File] = []
            try:
                if pattern_id == "cv2_file_display":
                    layout, files = self._build_file(interaction.user.id)
                else:
                    builder = {
                        "cv2_text_only": self._build_text_only,
                        "cv2_section_accessory": self._build_sections,
                        "cv2_container_dashboard": self._build_container,
                        "cv2_media_gallery": self._build_gallery,
                        "cv2_settings_page": self._build_settings_page,
                        "cv2_mobile_compact": self._build_mobile_compact,
                        "cv2_interactive_mix": self._build_interactive,
                    }[pattern_id]
                    layout = builder(interaction.user.id)
                await channel.send(
                    view=layout,
                    files=files,
                    delete_after=_RENDER_TTL,
                )
            except Exception as exc:  # noqa: BLE001 — the failure IS the data
                await self.ack(
                    interaction,
                    f"❌ Render failed — `{type(exc).__name__}: "
                    f"{str(exc)[:300]}`\n(discord.py {discord.__version__})",
                )
                return
            await self.ack(
                interaction,
                f"✅ Rendered below — self-deletes in {_RENDER_TTL}s.",
            )

        btn.callback = _render  # type: ignore[method-assign]
        return ([header], [btn])
