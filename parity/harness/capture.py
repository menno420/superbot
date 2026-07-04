"""Observation normalization — raw captures → deterministic, readable goldens.

Two goals, in tension, resolved explicitly:

* **Determinism across runs and code versions.** Snowflakes minted during a
  run depend on how many ids the code path allocates — a refactor that sends
  one extra embed must not cascade id-noise through the whole golden. All
  run-minted ids are rewritten to stable symbolic refs (``<msg:1>``,
  ``<msg:2>``, …) in order of first appearance; world constants become names
  (``<guild>``, ``<#general>``, ``<@member>``).
* **Honesty.** Only *known-volatile* values are scrubbed (nonces, timestamps,
  run-minted ids). Everything else — copy, embed structure, component
  custom_ids, flags, colors — is captured verbatim. A scrub rule added here
  widens the blind spot of every golden, so each one is documented.
"""

from __future__ import annotations

import re
from typing import Any

from parity.harness.fake_http import OutboundCall
from parity.harness.world import DEFAULT_PERSONAS, World

__all__ = ["Normalizer"]

# Discord relative-timestamp markup <t:1750000000:R> — wall-clock leakage.
_DISCORD_TS = re.compile(r"<t:\d+(:[a-zA-Z])?>")
# ISO datetimes embedded in copy (embeds that print utcnow()).
_ISO_TS = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(\+\d{2}:\d{2}|Z)?",
)
# Any 15–20 digit integer is snowflake-scale.
_SNOWFLAKE = re.compile(r"\b\d{15,20}\b")
# UUID strings (workflow mutation_ids etc.) — per-run randomness.
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
)
# discord.py auto-generates a random 32-hex custom_id for components that
# don't declare one (session views) — stable *refs*, not stable strings.
_AUTO_CID = re.compile(r"\b[0-9a-f]{32}\b")
# unpinned datetime.now() leaks: "Updated 12:14 UTC" footers and
# fractional epoch stamps inside composed ids (xp_reset:...:1782994447.52)
_SHORT_TIME = re.compile(r"\b\d{1,2}:\d{2} UTC\b")
_EPOCH_FLOAT = re.compile(r"\b\d{10}\.\d+\b")

#: payload keys that are pure client-side randomness
_DROP_KEYS = {"nonce", "enforce_nonce"}


class Normalizer:
    """Rewrites one case's observations into their stable symbolic form."""

    def __init__(self, world: World) -> None:
        self._names: dict[int, str] = {}
        self._names[world.guild_id] = "<guild>"
        self._names[World.BOT_USER_ID] = "<@bot>"
        for key, persona in DEFAULT_PERSONAS.items():
            self._names[persona["id"]] = f"<@{key}>"
        for channel_name, cid in world.channels.items():
            self._names[cid] = f"<#{channel_name}>"
        from parity.harness.world import _ADMIN_ROLE_ID  # single constant

        self._names[_ADMIN_ROLE_ID] = "<@&admin>"
        self._minted: dict[int, str] = {}
        self._auto_cids: dict[str, str] = {}

    # ------------------------------------------------------------ primitives

    def _sym(self, snowflake: int) -> str:
        known = self._names.get(snowflake)
        if known is not None:
            return known
        ref = self._minted.get(snowflake)
        if ref is None:
            ref = f"<msg:{len(self._minted) + 1}>"
            self._minted[snowflake] = ref
        return ref

    def _normalize_str(self, text: str) -> str:
        text = _DISCORD_TS.sub("<t>", text)
        text = _ISO_TS.sub("<ts>", text)
        text = _UUID.sub("<uuid>", text)
        text = _SHORT_TIME.sub("<hh:mm> UTC", text)
        text = _EPOCH_FLOAT.sub("<epoch>", text)

        def _sub_cid(match: re.Match[str]) -> str:
            cid = match.group(0)
            ref = self._auto_cids.get(cid)
            if ref is None:
                ref = f"<cid:{len(self._auto_cids) + 1}>"
                self._auto_cids[cid] = ref
            return ref

        text = _AUTO_CID.sub(_sub_cid, text)

        def _sub_id(match: re.Match[str]) -> str:
            return self._sym(int(match.group(0)))

        return _SNOWFLAKE.sub(_sub_id, text)

    def normalize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                k: self.normalize(v) for k, v in value.items() if k not in _DROP_KEYS
            }
        if isinstance(value, list):
            return [self.normalize(v) for v in value]
        if isinstance(value, str):
            return self._normalize_str(value)
        if isinstance(value, int) and len(str(value)) >= 15:
            return self._sym(value)
        if isinstance(value, float):
            # embed color floats etc. — keep; NaN can't serialize
            if value != value:  # noqa: PLR0124 - NaN check
                return "<nan>"
            return value
        return value

    # ------------------------------------------------------------- documents

    def calls(self, calls: list[OutboundCall]) -> list[dict[str, Any]]:
        out = []
        for call in calls:
            entry: dict[str, Any] = {"method": call.method}
            if call.args:
                entry["args"] = self.normalize(call.args)
            if call.payload is not None:
                entry["payload"] = self.normalize(call.payload)
            out.append(entry)
        return out

    def events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.normalize(e) for e in events]

    def db_delta(self, delta: dict[str, Any]) -> dict[str, Any]:
        return self.normalize(delta)
