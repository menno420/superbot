"""Pluggable raw-fixture provider for the BTD6 deterministic dataset.

A single seam between :mod:`services.btd6_data_service`'s validation +
caching layer and the *bytes source* of the fixture files. ``FileRawProvider``
preserves the historical behaviour (read JSON from ``disbot/data/btd6/``); the
cloud-storage migration adds a network-backed provider implementing the same
:class:`BTD6RawProvider` Protocol, swapped in via
``btd6_data_service.set_provider`` with **zero changes** to the ~14 dataset
consumers — every read funnels through ``btd6_data_service._load_file``.

Validation (``_require_keys``, alias/uniqueness/RBE checks) and caching
(``get_dataset`` / ``reset_cache``) stay in ``btd6_data_service`` and run over
whatever a provider returns, so any backend inherits the same guarantees.

Layering: this module depends only on the stdlib, so it sits safely below the
service layer and never imports core / cogs / views.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# Root for the committed fixtures. ``btd6_data_service`` re-exports this name
# (tests import ``btd6_data_service.DATA_ROOT``), so it lives here as the
# single source of truth. ``parents[1]`` is the ``disbot/`` package root.
DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "btd6"


@runtime_checkable
class BTD6RawProvider(Protocol):
    """Source of raw fixture JSON objects.

    ``load`` returns the parsed JSON object for ``name`` (e.g.
    ``"towers.json"``), or ``None`` when the fixture is absent — the caller
    decides whether that is fatal (required fixture) or a graceful degrade
    (optional fixture).
    """

    def load(self, name: str) -> dict[str, Any] | None: ...


class FileRawProvider:
    """Read raw fixture JSON from a local directory (historical behaviour).

    ``None`` is returned for a missing file so the caller decides whether the
    fixture is required (``_load_file`` raises) or optional
    (``_load_file_optional`` degrades to an empty category).
    """

    def __init__(self, root: Path | str | None = None) -> None:
        self._root = Path(root) if root is not None else DATA_ROOT

    @property
    def root(self) -> Path:
        return self._root

    def load(self, name: str) -> dict[str, Any] | None:
        path = self._root / name
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
