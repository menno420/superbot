"""``!restart`` exit contract (live miss, 2026-06-10).

``main()`` used to fall through to exit 0 even with a restart pending, and
on-failure restart policies (Railway — our prod) treat exit 0 as "done", so
``!restart`` released the runtime lock and nothing ever relaunched the bot.
A pending restart must exit nonzero; a startup crash must exit 1 (it also
fell through to 0); a plain shutdown stays 0.

Also covers the 429 login-rate-limit backoff: when Discord/Cloudflare returns
429 during bot.start(), sleeping before exit prevents the platform's immediate
restart from hammering Discord again and deepening the ban (live crash loop,
2026-06-12).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import discord
import pytest

import bot1
from core.runtime import lifecycle


def test_restart_exit_code_is_nonzero_and_not_crash():
    assert bot1.RESTART_EXIT_CODE != 0
    assert bot1.RESTART_EXIT_CODE != 1


def test_exit_code_after_main(monkeypatch):
    monkeypatch.setattr(lifecycle, "restart_requested", lambda: False)
    assert bot1._exit_code_after_main(crashed=False) == 0
    assert bot1._exit_code_after_main(crashed=True) == 1

    monkeypatch.setattr(lifecycle, "restart_requested", lambda: True)
    assert bot1._exit_code_after_main(crashed=False) == bot1.RESTART_EXIT_CODE
    # A crash during a restart-pending close is still a crash (1 also
    # relaunches under on-failure policies).
    assert bot1._exit_code_after_main(crashed=True) == 1


# ---------------------------------------------------------------------------
# 429 login-rate-limit backoff
# ---------------------------------------------------------------------------


def _make_http_exc(status: int) -> discord.HTTPException:
    exc = MagicMock(spec=discord.HTTPException)
    exc.status = status
    return exc


def test_maybe_backoff_sleeps_on_429():
    exc = _make_http_exc(429)
    with patch("bot1.time") as mock_time:
        result = bot1._maybe_backoff_on_rate_limit(exc)
    assert result is True
    mock_time.sleep.assert_called_once_with(bot1._LOGIN_RATE_LIMIT_BACKOFF_S)


@pytest.mark.parametrize("status", [400, 401, 403, 500])
def test_maybe_backoff_no_sleep_for_non_429(status: int):
    exc = _make_http_exc(status)
    with patch("bot1.time") as mock_time:
        result = bot1._maybe_backoff_on_rate_limit(exc)
    assert result is False
    mock_time.sleep.assert_not_called()


def test_maybe_backoff_no_sleep_for_non_http_exception():
    exc = RuntimeError("generic crash")
    with patch("bot1.time") as mock_time:
        result = bot1._maybe_backoff_on_rate_limit(exc)
    assert result is False
    mock_time.sleep.assert_not_called()


def test_login_rate_limit_backoff_is_positive():
    assert bot1._LOGIN_RATE_LIMIT_BACKOFF_S > 0
