"""BTD6 subsystem settings key — **reserved, not yet wired** (M4).

``BTD6_STRATEGY_SUBMISSION_CHANNEL`` is declared and re-exported so a
future strategy-intake feature has a stable key, but as of today it is
**not consumed by any runtime code and has no SettingSpec** — it is
neither operator-manageable (it never appears in the ``!settings`` hub)
nor read anywhere, so setting it changes nothing yet.
``tests/unit/invariants/test_reserved_settings_keys.py`` pins its
reserved status so the gap stays explicit rather than implied.

Intended (future) meaning: designate specific channels as strategy
intakes. The central natural-language stage decides whether the user
may talk naturally at all; this key would then decide whether their
message is treated as a strategy submission rather than a question.
"""

BTD6_STRATEGY_SUBMISSION_CHANNEL = "btd6_strategy_submission_channel"
