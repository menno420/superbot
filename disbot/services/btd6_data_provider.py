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

import hashlib
import json
import logging
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("bot.services.btd6_data_provider")

# Filename of the integrity manifest written by ``scripts/upload_btd6_data.py``
# and (best-effort) consulted by ``CloudRawProvider`` to flag stale fixtures.
MANIFEST_NAME = "manifest.json"

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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CloudRawProvider:
    """Fetch fixtures from an object store over HTTPS, cached to local disk.

    Built for a **public-read** bucket (Cloudflare R2 / S3 / GCS / CDN): the
    runtime read is a plain, auth-free HTTPS GET of ``{base_url}/{name}``.
    ``warm_cache`` runs once at startup (async) to download the fixtures into a
    local cache dir; ``load`` is then a *sync* read from that cache via a
    ``FileRawProvider``, so ``get_dataset`` never performs network I/O on the
    event loop.

    Resilience (the "cache + degrade gracefully" posture): a fetch failure for
    a fixture already present in the cache is tolerated (serve the cached
    copy). If a *required* fixture is missing with no cache, ``is_available``
    reports ``False`` and the caller degrades rather than crashing the bot.

    ``fetcher`` is an injectable ``async (url) -> bytes`` (used by tests to
    avoid real network + the aiohttp dependency); when ``None`` an ``aiohttp``
    session is used, matching ``btd6_fetch_service``.
    """

    def __init__(
        self,
        base_url: str,
        cache_dir: Path | str,
        *,
        fetcher: Callable[[str], Awaitable[bytes]] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = str(base_url).rstrip("/")
        self._cache_dir = Path(cache_dir)
        self._cache = FileRawProvider(self._cache_dir)
        self._fetcher = fetcher
        self._timeout = timeout
        self._available = False
        self._warmed = False
        self._stale: list[str] = []

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @property
    def stale(self) -> tuple[str, ...]:
        return tuple(self._stale)

    def is_available(self) -> bool:
        return self._available

    def source_label(self) -> str:
        if not self._warmed:
            return f"cloud:{self._base_url} (not warmed)"
        if not self._available:
            return f"cloud:{self._base_url} (unavailable)"
        if self._stale:
            return f"cloud:{self._base_url} (stale: {', '.join(self._stale)})"
        return f"cloud:{self._base_url} (cached)"

    def load(self, name: str) -> dict[str, Any] | None:
        return self._cache.load(name)

    async def warm_cache(
        self,
        *,
        required: Iterable[str] = (),
        optional: Iterable[str] = (),
    ) -> bool:
        """Download fixtures into the local cache; report data availability.

        Required fixtures that fail to fetch fall back to any existing cached
        copy. ``is_available`` (the return value) is True iff every required
        fixture ends up present in the cache.
        """
        required = tuple(required)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        manifest = await self._fetch_manifest()
        self._stale = []
        for name in (*required, *tuple(optional)):
            await self._download_one(name, manifest)
        self._available = all((self._cache_dir / n).exists() for n in required)
        self._warmed = True
        if not self._available:
            logger.warning(
                "BTD6 cloud data unavailable: required fixtures missing from "
                "%s and local cache %s",
                self._base_url,
                self._cache_dir,
            )
        return self._available

    async def _download_one(self, name: str, manifest: dict[str, str] | None) -> None:
        try:
            data = await self._fetch(f"{self._base_url}/{name}")
        except Exception as exc:  # noqa: BLE001 - any fetch error → degrade
            if (self._cache_dir / name).exists():
                logger.info(
                    "BTD6 cloud fetch failed for %s; serving cached copy (%s)",
                    name,
                    exc,
                )
            else:
                logger.warning("BTD6 cloud fetch failed for %s: %s", name, exc)
            return
        (self._cache_dir / name).write_bytes(data)
        if manifest and name in manifest and _sha256(data) != manifest[name]:
            self._stale.append(name)
            logger.warning("BTD6 cloud fixture %s mismatches manifest checksum", name)

    async def _fetch_manifest(self) -> dict[str, str] | None:
        """Best-effort fetch of the integrity manifest (name -> sha256)."""
        try:
            raw = await self._fetch(f"{self._base_url}/{MANIFEST_NAME}")
        except Exception:  # noqa: BLE001 - manifest is optional
            return None
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            return None
        files = data.get("files") if isinstance(data, dict) else None
        if not isinstance(files, dict):
            return None
        out: dict[str, str] = {}
        for path, meta in files.items():
            if isinstance(meta, dict) and isinstance(meta.get("sha256"), str):
                out[path] = meta["sha256"]
        return out

    async def _fetch(self, url: str) -> bytes:
        if self._fetcher is not None:
            return await self._fetcher(url)
        # Route the real network read through the sanctioned HTTP chokepoint so
        # btd6_fetch_service stays the only module touching an HTTP client
        # (pinned by test_no_untrusted_fetches). Lazy import keeps this seam
        # dependency-light and avoids load-time coupling.
        from services.btd6_fetch_service import fetch_url_bytes

        return await fetch_url_bytes(url, timeout=self._timeout)
