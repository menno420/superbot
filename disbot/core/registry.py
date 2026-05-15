from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FeatureDefinition:
    name: str
    display_name: str
    description: str
    commands: list[str] = field(default_factory=list)
    settings_keys: list[str] = field(default_factory=list)
    required_bot_permissions: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    default_enabled: bool = True


class FeatureRegistry:
    """Platform metadata for all registered features.

    Used for introspection, dashboard integration, AI discoverability,
    and architectural validation. Cog setup() functions call registry.register().
    """

    def __init__(self) -> None:
        self._features: dict[str, FeatureDefinition] = {}

    def register(self, feature: FeatureDefinition) -> None:
        self._features[feature.name] = feature

    def get(self, name: str) -> FeatureDefinition | None:
        return self._features.get(name)

    def get_for_command(self, command_name: str) -> FeatureDefinition | None:
        return next(
            (f for f in self._features.values() if command_name in f.commands),
            None,
        )

    def all(self) -> list[FeatureDefinition]:
        return list(self._features.values())

    def unregistered_summary(self) -> dict[str, int]:
        """Return feature count for observability."""
        return {"registered_features": len(self._features)}


registry = FeatureRegistry()
