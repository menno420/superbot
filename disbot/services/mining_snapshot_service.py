"""Mining snapshot relay — the bot side of the mineverse READ contract (FLAG 1).

Projects live per-guild mining state into the **v1 mining snapshot envelope**
the superbot-mineverse web app consumes (contract of record on
superbot-mineverse main: ``schemas/mining_snapshot.v1.schema.json``, prose
``docs/mining-data-contract.md``; a vendored copy of the schema is pinned at
``tests/fixtures/mineverse/mining_snapshot.v1.schema.json`` and enforced by
``tests/unit/services/test_mining_snapshot_service.py``).  The web app is a
client only — it never touches Postgres and never holds the bot token — so
this projection is the *only* read path from the live mining economy to the
browser game.

Design rules (mirroring the contract):

* **Projection, not translation** — every per-miner field reads the same
  ``utils/db/games/mining*`` primitives the game itself uses (reads stay
  direct per ``docs/ownership.md`` RS02); ``coins`` reads the economy table
  (``economy_service`` stays the only mutator) and ``xp`` derives from
  ``game_xp`` via the one shared level curve (``db.level_progress``).
* **Snowflakes are strings on the wire** (they exceed IEEE-754 doubles).
* **Energy is settled at projection time** with the pure regen math
  (:func:`utils.mining.energy.settle`) — the snapshot reports the honest
  current bar, never the stale stored value.  Read-only: nothing is written.
* **``gear_wear`` is accumulated wear** (contract semantics), while the DB
  stores *remaining durability* — projected as ``max_durability - remaining``.
* **Dormant by default** (the ``control_api`` discipline): the push loop arms
  only when both relay env vars are set; with either absent the bot behaves
  exactly as before — no loop, no network calls, no config required.
* **Never harms the bot**: the poster catches every network failure, logs it,
  and returns — a dead relay endpoint degrades the *website*, never the bot.

Transport (decided-and-flagged — the contract's honest gap): mineverse FLAG 1
specifies the payload, cadence (~60 s) and validation, but names **no**
bot-side transport or env var for the READ relay (unlike FLAG 2's
``MINING_WRITE_ENDPOINT``); stage-1 of the web app serves a committed fixture.
Chosen seam, symmetric with the write pair: HTTP POST of the snapshot JSON to
``MINING_SNAPSHOT_RELAY_URL``, scoped to guild ``MINING_SNAPSHOT_RELAY_GUILD_ID``
— the receiving ingest is the mineverse lane's follow-up, and the payload is
already validated at ingestion there (mineverse PR #42 refuses non-v1 relays).
"""

from __future__ import annotations

import datetime
import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass

import aiohttp

from utils import db, equipment
from utils.mining import energy, world
from utils.mining.exploration import BIOME_ORDER

logger = logging.getLogger("bot.mining_snapshot")

# The contract major version this builder emits (const "1" in the schema).
SCHEMA_VERSION = "1"

# The shared cross-game XP track this game reports under (game_xp_service).
_XP_GAME = "mining"

# Relay configuration env vars — both must be set for the relay to arm.
# Names chosen bot-side (decided-and-flagged): FLAG 1 names no READ-relay env
# var; these mirror FLAG 2's MINING_WRITE_* naming so the pair reads as one
# family on the Railway variables screen.
ENV_RELAY_URL = "MINING_SNAPSHOT_RELAY_URL"
ENV_RELAY_GUILD_ID = "MINING_SNAPSHOT_RELAY_GUILD_ID"

# One push must never wedge the loop behind a dead endpoint.
_PUSH_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class RelayConfig:
    """The armed relay target — present only when both env vars are set."""

    url: str
    guild_id: int


def relay_config() -> RelayConfig | None:
    """The relay target from the environment, or None (feature-off).

    Reads at call time (the ``CONTROL_API_TOKEN`` dormancy pattern) so tests
    and a restart pick up the variables without an import-order dependency.
    A non-numeric guild id is a misconfiguration: logged once per call site
    and treated as off — never a crash.
    """
    url = os.getenv(ENV_RELAY_URL, "").strip()
    raw_guild = os.getenv(ENV_RELAY_GUILD_ID, "").strip()
    if not url or not raw_guild:
        return None
    if not raw_guild.isdigit():
        logger.warning(
            "mining relay: %s=%r is not a guild snowflake — relay stays off",
            ENV_RELAY_GUILD_ID,
            raw_guild,
        )
        return None
    return RelayConfig(url=url, guild_id=int(raw_guild))


def _iso_utc_now() -> str:
    """ISO 8601 UTC instant, second precision, ``Z`` suffix (contract format)."""
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _count_map(raw: dict[str, int]) -> dict[str, int]:
    """A schema-conformant name→count map: values are non-negative ints.

    A negative quantity would be corrupt state; dropping it keeps the
    snapshot honest about what the miner *has* while never emitting a
    contract-violating value (ingestion refuses the whole payload).
    """
    return {name: int(count) for name, count in raw.items() if int(count) >= 0}


def _project_gear_wear(remaining_by_item: dict[str, int]) -> dict[str, int]:
    """DB *remaining durability* → contract *accumulated wear* per item.

    Items whose max durability is unknown to the gear table cannot be
    projected as wear and are omitted (they also cannot wear).
    """
    wear: dict[str, int] = {}
    for item, remaining in remaining_by_item.items():
        maximum = equipment.max_durability(item)
        if maximum is None:
            continue
        wear[item] = max(0, maximum - remaining)
    return wear


async def _build_miner(
    suid: str,
    guild_id: int,
    display_name: str,
    *,
    now: int,
) -> dict[str, object]:
    """One v1 miner object — the 16 required fields, oracle-named."""
    user_int = int(suid)

    depth = world.clamp_depth(await db.get_depth(suid, guild_id))
    record = world.clamp_depth(await db.get_max_depth(suid, guild_id))
    pos_x, pos_y = await db.get_position(suid, guild_id)

    current, updated_at = await db.get_energy(suid, guild_id)
    settled = energy.settle(energy.EnergyState(current, updated_at), now)

    totals = await db.get_game_xp(user_int, guild_id)
    shared_total = sum(totals.values())
    level = db.level_progress(shared_total)[0]

    equipped = await db.get_equipment(suid, guild_id)

    return {
        "suid": suid,
        "guild_id": str(guild_id),
        "display_name": display_name,
        "depth": depth,
        "record_depth": max(depth, record),
        "position": {"x": pos_x, "y": pos_y},
        "energy": {
            "current": max(0, min(settled.current, energy.MAX_ENERGY)),
            "updated_at": max(0, settled.updated_at),
        },
        "coins": max(0, await db.get_coins(user_int, guild_id)),
        "xp": {
            "game": _XP_GAME,
            "game_total": max(0, totals.get(_XP_GAME, 0)),
            "shared_total": max(0, shared_total),
            "level": max(0, level),
        },
        # Slots are the schema's closed enum — superbot's SLOTS tuple is that
        # exact set, so this is a defensive filter, not a translation.
        "equipment": {
            slot: item for slot, item in equipped.items() if slot in equipment.SLOTS
        },
        "gear_wear": _project_gear_wear(await db.get_gear_wear(suid, guild_id)),
        "mining_inventory": _count_map(
            await db.get_mining_inventory(suid, guild_id),
        ),
        "vault": _count_map(await db.get_vault(suid, guild_id)),
        "vault_level": max(0, min(await db.get_vault_level(suid, guild_id), 6)),
        "skills": _count_map(await db.get_skills(user_int, guild_id)),
        "structures": _count_map(await db.get_structures(user_int, guild_id)),
    }


async def build_snapshot(
    guild_id: int,
    *,
    resolve_display_name: Callable[[str], str | None] | None = None,
    now: int | None = None,
) -> dict[str, object]:
    """The full v1 snapshot envelope for *guild_id* (read-only projection).

    One miner per ``mining_player_state`` row (the contract's population
    rule).  *resolve_display_name* maps a suid to the guild display name
    (the cog passes the member cache); a miss falls back to the suid string
    so the payload stays conformant when a member has left or is uncached.
    The optional world-shape hints (``max_depth`` / ``biomes``) are included
    — they are additive v1 fields the frontend renders when present.
    """
    now_s = int(time.time()) if now is None else now
    miners = []
    for suid in await db.list_guild_miner_ids(guild_id):
        name = resolve_display_name(suid) if resolve_display_name else None
        miners.append(
            await _build_miner(suid, guild_id, name or suid, now=now_s),
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso_utc_now(),
        "guild_id": str(guild_id),
        "max_depth": world.MAX_DEPTH,
        "biomes": [world.BIOME_LABELS[b] for b in BIOME_ORDER],
        "miners": miners,
    }


async def push_snapshot(snapshot: dict[str, object], url: str) -> bool:
    """POST *snapshot* to the relay *url*; True on 2xx, False otherwise.

    Never raises: a relay outage must never affect bot operation — every
    failure class (DNS, refused, timeout, non-2xx, TLS) is caught, logged,
    and absorbed.  The next loop tick simply tries again.
    """
    try:
        timeout = aiohttp.ClientTimeout(total=_PUSH_TIMEOUT_SECONDS)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.post(url, json=snapshot) as resp,
        ):
            if resp.status // 100 == 2:
                return True
            logger.warning(
                "mining relay: push to %s answered HTTP %s",
                url,
                resp.status,
            )
            return False
    except Exception as exc:  # noqa: BLE001 — the relay must never hurt the bot
        logger.warning("mining relay: push to %s failed: %s", url, exc)
        return False


__all__ = [
    "ENV_RELAY_GUILD_ID",
    "ENV_RELAY_URL",
    "SCHEMA_VERSION",
    "RelayConfig",
    "build_snapshot",
    "push_snapshot",
    "relay_config",
]
