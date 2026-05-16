"""Static onboarding profile templates.

Pure data — no imports, no logic, no DB access.
Future: profiles become configurable per-guild via governance DB.
"""

from __future__ import annotations

WELCOME_PROFILES: dict[str, dict] = {
    "default": {
        "welcome_channel": "welcome",
        "recommended_channels": ["bot-commands", "economy", "games", "roles"],
        "beginner_commands": ["help", "daily", "work", "inventory"],
        "description": ("Welcome! Here are the channels and commands to get started."),
    },
}


def get_profile(name: str = "default") -> dict:
    return WELCOME_PROFILES.get(name, WELCOME_PROFILES["default"])
