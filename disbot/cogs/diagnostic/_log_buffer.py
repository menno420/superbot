"""In-memory ring buffer of recent bot log records for the diagnostic
"Recent Logs / Recent Errors" panel.

History: ``build_query_logs_embed`` read a ``logs`` DB table that **nothing ever
wrote to** (the bot logs to ``bot.log`` + stdout via Python handlers), so the
panel always returned "No logs found" — even right after a crash. This handler
keeps the last ``_MAXLEN`` records of the bot's own loggers in memory — cheap,
no DB/file I/O, no cross-process pollution — for the panel to read. Installed
once (idempotent) from :func:`cogs.diagnostic_cog.setup`.
"""

from __future__ import annotations

import logging
import time
from collections import deque

_MAXLEN = 500
_buffer: deque[dict[str, str]] = deque(maxlen=_MAXLEN)


class _RingBufferHandler(logging.Handler):
    """Append each emitted record to the bounded in-memory buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _buffer.append(
                {
                    "timestamp": time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(record.created),
                    ),
                    "level": record.levelname,
                    "message": record.getMessage(),
                },
            )
        except Exception:  # pragma: no cover — a log handler must never raise
            self.handleError(record)


_installed = False


def install() -> None:
    """Attach the ring-buffer handler to the ``bot`` logger tree (idempotent).

    Records from every ``bot.*`` child propagate up to the ``bot`` logger, so a
    single handler here captures the whole application's logging without
    touching :mod:`bot1`'s root-logger setup.
    """
    global _installed
    if _installed:
        return
    handler = _RingBufferHandler()
    handler.setLevel(logging.INFO)
    logging.getLogger("bot").addHandler(handler)
    _installed = True


def recent(level: str | None = None, limit: int = 10) -> list[dict[str, str]]:
    """Return up to ``limit`` most-recent buffered records, newest first,
    optionally filtered to a single level name (e.g. ``"ERROR"``)."""
    items = list(_buffer)
    if level:
        wanted = level.upper()
        items = [r for r in items if r["level"] == wanted]
    items.reverse()
    return items[: max(1, limit)]


def _reset_for_tests() -> None:
    _buffer.clear()
