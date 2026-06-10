"""``!restart`` exit contract (live miss, 2026-06-10).

``main()`` used to fall through to exit 0 even with a restart pending, and
on-failure restart policies (Railway — our prod) treat exit 0 as "done", so
``!restart`` released the runtime lock and nothing ever relaunched the bot.
A pending restart must exit nonzero; a startup crash must exit 1 (it also
fell through to 0); a plain shutdown stays 0.
"""

from __future__ import annotations

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
