"""Mining snapshot relay (mineverse FLAG 1) — schema gate + behaviour pins.

The contract of record is superbot-mineverse's
``schemas/mining_snapshot.v1.schema.json`` (Draft 2020-12); a vendored copy is
pinned at ``tests/fixtures/mineverse/mining_snapshot.v1.schema.json`` (copied
verbatim from superbot-mineverse main, 2026-07-13 — refresh it when the v1
schema gains additive fields).  Two validation layers, mirroring mineverse's
own gate:

* **Full Draft 2020-12 validation** via ``jsonschema.Draft202012Validator``
  (the mineverse ``tests/test_schema_gate.py`` discipline) — dev-only dep,
  ``importorskip``-gated because CI installs ``requirements.txt`` only.
* **A stdlib structural gate that always runs** (CI included), deriving its
  required-field lists / enums / bounds *from the schema JSON itself* so the
  test and the schema cannot drift (the mineverse ``REQUIRED_MINER_FIELDS``
  rule).

Behaviour pins: energy is settled at projection time; ``gear_wear`` projects
remaining durability → accumulated wear; snowflakes are strings; the relay is
dormant with the env vars unset; a push failure never raises.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import mining_snapshot_service
from utils.mining import energy

_SCHEMA_PATH = (
    Path(__file__).parent.parent.parent
    / "fixtures"
    / "mineverse"
    / "mining_snapshot.v1.schema.json"
)

GUILD_ID = 987654321098765432
SUID = "100000000000000001"


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text())


# ---------------------------------------------------------------------------
# Fake oracle state — patch.multiple factories (the mining_workflow test style)
# ---------------------------------------------------------------------------

_POPULATED_READS = dict(
    list_guild_miner_ids=lambda: AsyncMock(return_value=[SUID]),
    get_depth=lambda: AsyncMock(return_value=2),
    get_max_depth=lambda: AsyncMock(return_value=3),
    get_position=lambda: AsyncMock(return_value=(4, -2)),
    # 41 energy as of "now" (the test passes now=updated_at so no regen).
    get_energy=lambda: AsyncMock(return_value=(41, 1783728000)),
    get_coins=lambda: AsyncMock(return_value=18450),
    get_game_xp=lambda: AsyncMock(return_value={"mining": 6240, "fishing": 3070}),
    get_equipment=lambda: AsyncMock(
        return_value={
            "tool": "diamond pickaxe",
            "light": "diamond lantern",
            "charm": "lucky charm",
        },
    ),
    # Remaining durability (DB semantics): diamond pickaxe 400-max, lantern 180-max.
    get_gear_wear=lambda: AsyncMock(
        return_value={"diamond pickaxe": 342, "diamond lantern": 158},
    ),
    get_mining_inventory=lambda: AsyncMock(
        return_value={"stone": 42, "iron": 63, "diamond": 9, "torch": 3},
    ),
    get_vault=lambda: AsyncMock(return_value={"gold": 120, "diamond": 34}),
    get_vault_level=lambda: AsyncMock(return_value=3),
    get_skills=lambda: AsyncMock(return_value={"mining": 4, "luck": 2}),
    get_structures=lambda: AsyncMock(return_value={"campfire": 1, "forge": 3}),
)


def _reads(**overrides: object) -> dict[str, object]:
    base = {name: factory() for name, factory in _POPULATED_READS.items()}
    base.update(overrides)
    return base


async def _build(now: int = 1783728000, **overrides: object) -> dict:
    with patch.multiple(
        "services.mining_snapshot_service.db",
        **_reads(**overrides),
    ):
        return await mining_snapshot_service.build_snapshot(
            GUILD_ID,
            resolve_display_name=lambda suid: "DeepDelver",
            now=now,
        )


# ---------------------------------------------------------------------------
# Stdlib structural gate — constants derived from the schema JSON (no drift)
# ---------------------------------------------------------------------------


def _assert_int_in(value: object, spec: dict, where: str) -> None:
    assert isinstance(value, int) and not isinstance(value, bool), where
    if "minimum" in spec:
        assert value >= spec["minimum"], f"{where}: {value} < {spec['minimum']}"
    if "maximum" in spec:
        assert value <= spec["maximum"], f"{where}: {value} > {spec['maximum']}"


def _assert_count_map(value: object, where: str) -> None:
    assert isinstance(value, dict), where
    for name, count in value.items():
        assert isinstance(name, str), f"{where}[{name!r}]"
        _assert_int_in(count, {"minimum": 0}, f"{where}[{name!r}]")


def assert_snapshot_conforms(snapshot: dict, schema: dict) -> None:
    """Structural v1 conformance, driven by the vendored schema document."""
    env_props = schema["properties"]
    # Envelope: closed object, required fields present.
    assert set(schema["required"]) <= set(snapshot)
    assert set(snapshot) <= set(env_props), "envelope is additionalProperties:false"
    assert snapshot["schema_version"] == env_props["schema_version"]["const"]
    assert isinstance(snapshot["generated_at"], str)
    assert snapshot["generated_at"].endswith("Z")
    assert isinstance(snapshot["guild_id"], str) and snapshot["guild_id"].isdigit()
    if "max_depth" in snapshot:
        _assert_int_in(snapshot["max_depth"], env_props["max_depth"], "max_depth")
    if "biomes" in snapshot:
        assert isinstance(snapshot["biomes"], list)
        assert len(snapshot["biomes"]) <= env_props["biomes"]["maxItems"]
        assert all(isinstance(b, str) for b in snapshot["biomes"])

    miner_def = schema["$defs"]["miner"]
    miner_props = miner_def["properties"]
    slot_enum = set(miner_props["equipment"]["propertyNames"]["enum"])
    count_map_fields = {
        name
        for name, spec in miner_props.items()
        if spec.get("$ref") == "#/$defs/countMap"
    }

    assert isinstance(snapshot["miners"], list)
    for i, miner in enumerate(snapshot["miners"]):
        where = f"miners[{i}]"
        assert set(miner_def["required"]) <= set(miner), where
        assert set(miner) <= set(miner_props), f"{where} closed object"
        for field in ("suid", "guild_id"):
            assert isinstance(miner[field], str) and miner[field].isdigit(), (
                f"{where}.{field} must be a digit string"
            )
        assert miner["guild_id"] == snapshot["guild_id"], f"{where} guild match"
        assert isinstance(miner["display_name"], str)
        for field in ("depth", "record_depth", "vault_level", "coins"):
            _assert_int_in(miner[field], miner_props[field], f"{where}.{field}")
        position = miner["position"]
        for axis in miner_props["position"]["required"]:
            _assert_int_in(position[axis], {}, f"{where}.position.{axis}")
        energy_spec = miner_props["energy"]["properties"]
        for key in miner_props["energy"]["required"]:
            _assert_int_in(miner["energy"][key], energy_spec[key], f"{where}.energy.{key}")
        xp = miner["xp"]
        assert set(miner_props["xp"]["required"]) <= set(xp), f"{where}.xp"
        assert xp["game"] and isinstance(xp["game"], str)
        for key in ("game_total", "shared_total", "level"):
            _assert_int_in(xp[key], {"minimum": 0}, f"{where}.xp.{key}")
        assert set(miner["equipment"]) <= slot_enum, f"{where}.equipment slots"
        assert all(isinstance(v, str) for v in miner["equipment"].values())
        for field in count_map_fields:
            _assert_count_map(miner[field], f"{where}.{field}")


# ---------------------------------------------------------------------------
# Schema gate — structural (always) + full Draft 2020-12 (when available)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_populated_snapshot_conforms_structurally():
    assert_snapshot_conforms(await _build(), _schema())


@pytest.mark.asyncio
async def test_empty_guild_snapshot_conforms_structurally():
    snapshot = await _build(list_guild_miner_ids=AsyncMock(return_value=[]))
    assert snapshot["miners"] == []
    assert_snapshot_conforms(snapshot, _schema())


@pytest.mark.asyncio
async def test_snapshot_validates_against_v1_schema_draft202012():
    """The FLAG 1 done-criterion: Draft202012Validator, same as mineverse CI.

    Dev-env only (``requirements-dev.txt``): CI installs ``requirements.txt``
    alone, so this skips there — the stdlib structural gate above still runs.
    """
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(_schema())
    populated = await _build()
    empty = await _build(list_guild_miner_ids=AsyncMock(return_value=[]))
    for snapshot in (populated, empty):
        errors = sorted(validator.iter_errors(snapshot), key=str)
        assert not errors, [e.message for e in errors]


# ---------------------------------------------------------------------------
# Projection semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_miner_fields_project_oracle_state():
    snapshot = await _build()
    assert snapshot["guild_id"] == str(GUILD_ID)
    (miner,) = snapshot["miners"]
    assert miner["suid"] == SUID
    assert miner["display_name"] == "DeepDelver"
    assert miner["depth"] == 2
    assert miner["record_depth"] == 3
    assert miner["position"] == {"x": 4, "y": -2}
    assert miner["coins"] == 18450
    # XP: game slice + shared total + level from the one shared curve.
    assert miner["xp"]["game"] == "mining"
    assert miner["xp"]["game_total"] == 6240
    assert miner["xp"]["shared_total"] == 9310
    from utils import db

    assert miner["xp"]["level"] == db.level_progress(9310)[0]
    assert miner["vault_level"] == 3
    assert miner["mining_inventory"]["iron"] == 63
    assert miner["vault"]["gold"] == 120
    assert miner["skills"] == {"mining": 4, "luck": 2}
    assert miner["structures"] == {"campfire": 1, "forge": 3}


@pytest.mark.asyncio
async def test_gear_wear_projects_accumulated_wear_not_remaining():
    """DB stores remaining durability; the contract wants accumulated wear."""
    (miner,) = (await _build())["miners"]
    # diamond pickaxe max 400, 342 remaining → 58 wear (the sample's value).
    assert miner["gear_wear"] == {"diamond pickaxe": 58, "diamond lantern": 22}


@pytest.mark.asyncio
async def test_energy_is_settled_at_projection_time():
    """A stale (0, 0) row settles to a full bar — never reported raw."""
    now = 1_783_728_000
    snapshot = await _build(now=now, get_energy=AsyncMock(return_value=(0, 0)))
    (miner,) = snapshot["miners"]
    assert miner["energy"] == {"current": energy.MAX_ENERGY, "updated_at": now}


@pytest.mark.asyncio
async def test_display_name_falls_back_to_suid():
    """An uncached / departed member still yields a conformant string."""
    with patch.multiple("services.mining_snapshot_service.db", **_reads()):
        snapshot = await mining_snapshot_service.build_snapshot(
            GUILD_ID,
            resolve_display_name=lambda suid: None,
            now=1783728000,
        )
    assert snapshot["miners"][0]["display_name"] == SUID


@pytest.mark.asyncio
async def test_defensive_clamps_keep_payload_conformant():
    """Out-of-band oracle values are clamped, never emitted (ingestion refuses)."""
    snapshot = await _build(
        get_depth=AsyncMock(return_value=99),
        get_vault_level=AsyncMock(return_value=42),
        get_coins=AsyncMock(return_value=-5),
        get_mining_inventory=AsyncMock(return_value={"stone": 3, "ghost": -1}),
    )
    (miner,) = snapshot["miners"]
    assert miner["depth"] == 3
    assert miner["vault_level"] == 6
    assert miner["coins"] == 0
    assert miner["mining_inventory"] == {"stone": 3}
    assert_snapshot_conforms(snapshot, _schema())


# ---------------------------------------------------------------------------
# Relay config — dormant by default
# ---------------------------------------------------------------------------


def test_relay_config_is_none_when_env_unset(monkeypatch):
    monkeypatch.delenv(mining_snapshot_service.ENV_RELAY_URL, raising=False)
    monkeypatch.delenv(mining_snapshot_service.ENV_RELAY_GUILD_ID, raising=False)
    assert mining_snapshot_service.relay_config() is None


def test_relay_config_requires_both_vars(monkeypatch):
    monkeypatch.setenv(
        mining_snapshot_service.ENV_RELAY_URL,
        "https://relay.example/api/ingest",
    )
    monkeypatch.delenv(mining_snapshot_service.ENV_RELAY_GUILD_ID, raising=False)
    assert mining_snapshot_service.relay_config() is None


def test_relay_config_rejects_non_snowflake_guild(monkeypatch):
    monkeypatch.setenv(
        mining_snapshot_service.ENV_RELAY_URL,
        "https://relay.example/api/ingest",
    )
    monkeypatch.setenv(mining_snapshot_service.ENV_RELAY_GUILD_ID, "not-a-guild")
    assert mining_snapshot_service.relay_config() is None


def test_relay_config_parses_armed_pair(monkeypatch):
    monkeypatch.setenv(
        mining_snapshot_service.ENV_RELAY_URL,
        "https://relay.example/api/ingest",
    )
    monkeypatch.setenv(mining_snapshot_service.ENV_RELAY_GUILD_ID, str(GUILD_ID))
    config = mining_snapshot_service.relay_config()
    assert config == mining_snapshot_service.RelayConfig(
        url="https://relay.example/api/ingest",
        guild_id=GUILD_ID,
    )


# ---------------------------------------------------------------------------
# Push path — mocked HTTP, error tolerance
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False


class _FakeSession:
    """aiohttp.ClientSession stand-in recording the one POST it serves."""

    last: "_FakeSession | None" = None

    def __init__(self, *args, **kwargs) -> None:
        self.posts: list[tuple[str, dict]] = []
        self.status = 200
        _FakeSession.last = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    def post(self, url: str, *, json: dict) -> _FakeResponse:
        self.posts.append((url, json))
        return _FakeResponse(self.status)


@pytest.mark.asyncio
async def test_push_snapshot_posts_json_and_reports_success():
    with patch(
        "services.mining_snapshot_service.aiohttp.ClientSession",
        _FakeSession,
    ):
        ok = await mining_snapshot_service.push_snapshot(
            {"schema_version": "1"},
            "https://relay.example/api/ingest",
        )
    assert ok is True
    assert _FakeSession.last is not None
    assert _FakeSession.last.posts == [
        ("https://relay.example/api/ingest", {"schema_version": "1"}),
    ]


@pytest.mark.asyncio
async def test_push_snapshot_reports_non_2xx_as_failure():
    class _Fake503(_FakeSession):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.status = 503

    with patch(
        "services.mining_snapshot_service.aiohttp.ClientSession",
        _Fake503,
    ):
        ok = await mining_snapshot_service.push_snapshot(
            {"schema_version": "1"},
            "https://relay.example/api/ingest",
        )
    assert ok is False


@pytest.mark.asyncio
async def test_push_snapshot_never_raises_on_network_failure():
    class _ExplodingSession:
        def __init__(self, *args, **kwargs) -> None:
            raise OSError("connection refused")

    with patch(
        "services.mining_snapshot_service.aiohttp.ClientSession",
        _ExplodingSession,
    ):
        ok = await mining_snapshot_service.push_snapshot(
            {"schema_version": "1"},
            "https://relay.example/api/ingest",
        )
    assert ok is False


# ---------------------------------------------------------------------------
# Cog — feature-off no-op + push_now error tolerance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cog_stays_dormant_when_relay_unconfigured(monkeypatch):
    from cogs.mining_relay_cog import MiningRelayCog

    monkeypatch.delenv(mining_snapshot_service.ENV_RELAY_URL, raising=False)
    monkeypatch.delenv(mining_snapshot_service.ENV_RELAY_GUILD_ID, raising=False)
    cog = MiningRelayCog(MagicMock())
    await cog.cog_load()
    assert not cog._push_loop.is_running()
    assert await cog.push_now() is False


@pytest.mark.asyncio
async def test_cog_push_now_absorbs_builder_failure(monkeypatch):
    from cogs.mining_relay_cog import MiningRelayCog

    monkeypatch.setenv(
        mining_snapshot_service.ENV_RELAY_URL,
        "https://relay.example/api/ingest",
    )
    monkeypatch.setenv(mining_snapshot_service.ENV_RELAY_GUILD_ID, str(GUILD_ID))
    cog = MiningRelayCog(MagicMock())
    with patch(
        "cogs.mining_relay_cog.mining_snapshot_service.build_snapshot",
        AsyncMock(side_effect=RuntimeError("db down")),
    ):
        assert await cog.push_now() is False  # logged, never raised
