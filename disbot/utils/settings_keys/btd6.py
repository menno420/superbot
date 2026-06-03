"""BTD6 subsystem settings keys.

``BTD6_STRATEGY_SUBMISSION_CHANNEL`` is **reserved, not yet wired** (M4):
declared and re-exported so a future strategy-intake feature has a stable
key, but as of today it is **not consumed by any runtime code and has no
SettingSpec** — it is neither operator-manageable (it never appears in the
``!settings`` hub) nor read anywhere, so setting it changes nothing yet.
``tests/unit/invariants/test_reserved_settings_keys.py`` pins its reserved
status so the gap stays explicit rather than implied.

Intended (future) meaning: designate specific channels as strategy
intakes. The central natural-language stage decides whether the user
may talk naturally at all; this key would then decide whether their
message is treated as a strategy submission rather than a question.

``BTD6_CT_GROUP_ID`` stores the Contested Territory **bracket (group) id**
a server pastes for its team, so the bot can show that team's live CT
standing (score + rank vs its weekly bracket). It is written/read through
:mod:`services.btd6_ct_team_service` (never via a raw key) and is set with
the ``!btd6 ctteam`` command. Ninja Kiwi mints a new group id each weekly
event, so the value is expected to be re-pasted when it goes stale.

``BTD6_VERSION_ANNOUNCEMENT_CHANNEL`` stores the Discord channel id (str of
int) where the bot posts an announcement when patch-notes ingestion detects
a newly-released BTD6 version. It is read/written through
:mod:`services.btd6_version_announce` (never via a raw key) and configured
with the ``!btd6ops announcechannel`` admin command; unset (``""``) disables
the announcement for that guild.
"""

BTD6_STRATEGY_SUBMISSION_CHANNEL = "btd6_strategy_submission_channel"

BTD6_CT_GROUP_ID = "btd6_ct_group_id"

BTD6_VERSION_ANNOUNCEMENT_CHANNEL = "btd6_version_announcement_channel"
