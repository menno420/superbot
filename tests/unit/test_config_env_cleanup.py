"""PR-7 — command-access env cleanup.

Pins:

* ``config.ALLOWED_CHANNELS`` is deleted — production behaviour is
  owned by the per-guild DB-backed policy (migration 050) read
  through :func:`core.runtime.command_access.resolve_command_access`,
  not by an env var with hardcoded fallback IDs.
* ``config.CLEANUP_WHITELIST_CHANNELS`` is intentionally preserved
  because cleanup whitelist is a separate concern owned by
  ``cogs/cleanup_cog.py``.  A future PR can migrate that to a
  DB-backed policy in the same shape; this test fails loud if
  someone deletes it in the same sweep.
* ``BOT_ALLOWED_CHANNELS`` is no longer read anywhere under
  ``disbot/`` outside of comments referencing the historical
  behaviour — a grep-style check guards against a future drive-by
  edit silently restoring the env override and re-introducing the
  fresh-guild-onboarding bug.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DISBOT = _REPO_ROOT / "disbot"


def test_allowed_channels_is_gone_from_config():
    """``config.ALLOWED_CHANNELS`` must not be importable any more."""
    import config

    assert not hasattr(config, "ALLOWED_CHANNELS"), (
        "config.ALLOWED_CHANNELS was deleted in PR-7 — production "
        "command admission is owned by guild_command_access_policy "
        "(migration 050).  Do not reintroduce the symbol."
    )


def test_cleanup_whitelist_channels_is_preserved():
    """Cleanup whitelist is a separate concern; it stays env-driven
    until a follow-up PR migrates it.  This test fails if someone
    deletes it in the same sweep as ALLOWED_CHANNELS — which would
    silently break the cleanup_cog's whitelist semantics.
    """
    import config

    assert hasattr(config, "CLEANUP_WHITELIST_CHANNELS")
    assert isinstance(config.CLEANUP_WHITELIST_CHANNELS, set)


def test_bot_allowed_channels_env_var_is_not_read_in_production_code():
    """The ``BOT_ALLOWED_CHANNELS`` env var must not be referenced by
    any production read path under ``disbot/``.  Comments referring
    to the historical behaviour are allowed (they document the PR-7
    cleanup); ``os.getenv("BOT_ALLOWED_CHANNELS", …)`` calls are not.
    """
    bad: list[str] = []
    for path in _DISBOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        src = path.read_text()
        # Detect the env-var read shape (not the bare token, which
        # appears in legitimate explanatory comments).
        if 'os.getenv("BOT_ALLOWED_CHANNELS"' in src:
            bad.append(str(path.relative_to(_REPO_ROOT)))
    assert not bad, (
        "BOT_ALLOWED_CHANNELS is no longer consumed by production "
        "code — references in:\n  " + "\n  ".join(bad)
    )


@pytest.mark.parametrize(
    "channel_id",
    [1348795460948590622, 1403818013408624642],
)
def test_hardcoded_main_server_channel_ids_only_appear_in_the_backfill_migration(
    channel_id: int,
):
    """The two main-server channel IDs that used to live in
    ``config.py`` as the ``ALLOWED_CHANNELS`` fallback are now
    confined to the backfill migration (051) for command-access
    semantics.  ``config.py`` retains them in the unrelated
    ``CLEANUP_WHITELIST_CHANNELS`` default — different concern,
    explicitly out of scope for PR-7 — so it stays on the
    allowlist for this scan.  Any OTHER production file
    referencing these IDs would silently re-create the
    fresh-guild-onboarding bug for new deployments.
    """
    # Files where the IDs legitimately appear (and are pinned by
    # other tests).
    _ALLOWED = {
        "disbot/migrations/051_command_access_main_server_backfill.sql",
        # CLEANUP_WHITELIST_CHANNELS preserves the IDs as the cleanup
        # cog's whitelist fallback — pinned by
        # test_cleanup_whitelist_channels_is_preserved above.
        "disbot/config.py",
    }
    bad: list[str] = []
    for path in _DISBOT.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        rel = str(path.relative_to(_REPO_ROOT))
        if rel in _ALLOWED:
            continue
        try:
            src = path.read_text()
        except UnicodeDecodeError:
            continue
        if str(channel_id) in src:
            bad.append(rel)
    assert not bad, (
        f"hardcoded channel id {channel_id} should only live in "
        "migrations/051 (and config.CLEANUP_WHITELIST_CHANNELS for "
        "the unrelated cleanup whitelist); found elsewhere in:\n  " + "\n  ".join(bad)
    )
