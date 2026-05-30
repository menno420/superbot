"""Pinning test — the BTD6 reserved settings keys stay reserved.

Four settings-key *names* are declared + re-exported but, as of today,
have **no SettingSpec and no runtime consumer**:

  * ``BTD6_STRATEGY_SUBMISSION_CHANNEL``
  * ``BTD6_CACHE_DEFAULT_INTERVAL_SECONDS``
  * ``BTD6_CACHE_CIRCUIT_BREAKER_THRESHOLD``
  * ``BTD6_CACHE_FRESHNESS_WARNING_HOURS``

Their module docstrings (``utils/settings_keys/btd6.py`` and
``utils/settings_keys/btd6_cache.py``) say so explicitly so operators
and future agents do not assume that setting them changes behaviour.
This test pins that contract two ways:

  1. The constants still exist with their documented string values and
     are exported from ``utils.settings_keys``.
  2. No ``cogs/**/schemas.py`` wires any of them into a ``SettingSpec``.

The day a BTD6 cache-cadence / strategy-intake feature lands, it will
add a ``SettingSpec`` (referencing the constant in a schema module) and
the read path together — which trips assertion (2) and forces this
test, plus the ``btd6*.py`` docstrings, to be updated deliberately.
"""

from __future__ import annotations

from pathlib import Path

from utils import settings_keys

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# constant name -> documented string value
_RESERVED: dict[str, str] = {
    "BTD6_STRATEGY_SUBMISSION_CHANNEL": "btd6_strategy_submission_channel",
    "BTD6_CACHE_DEFAULT_INTERVAL_SECONDS": "btd6_cache_default_interval_seconds",
    "BTD6_CACHE_CIRCUIT_BREAKER_THRESHOLD": "btd6_cache_circuit_breaker_threshold",
    "BTD6_CACHE_FRESHNESS_WARNING_HOURS": "btd6_cache_freshness_warning_hours",
}


def test_reserved_keys_exist_with_documented_values() -> None:
    for name, value in _RESERVED.items():
        assert getattr(settings_keys, name) == value
        assert name in settings_keys.__all__


def test_reserved_keys_have_no_schema_spec() -> None:
    """No ``SettingSpec`` references a reserved key (none is manageable)."""
    schema_files = sorted(_DISBOT.glob("cogs/**/schemas.py"))
    assert schema_files, "expected to find cogs/**/schemas.py modules"
    offenders: list[str] = []
    for path in schema_files:
        text = path.read_text(encoding="utf-8")
        for name in _RESERVED:
            if name in text:
                offenders.append(f"{path.relative_to(_REPO_ROOT)} references {name}")
    assert not offenders, (
        "A reserved BTD6 settings key is now wired into a schema. If that "
        "is intentional, add the matching runtime read path and update "
        "utils/settings_keys/btd6*.py docstrings + this test:\n" + "\n".join(offenders)
    )
