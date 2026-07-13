"""Mineverse WRITE endpoint (``disbot/mining_write_api.py``) — FLAG 2 gates.

The contract of record is superbot-mineverse's
``schemas/mining_action.v1.schema.json`` / ``mining_action_response.v1.schema.json``
(Draft 2020-12) + ``docs/mining-write-contract.md``; vendored copies are pinned
under ``tests/fixtures/mineverse/`` (verbatim from superbot-mineverse main,
2026-07-13 — refresh on additive v1 changes). Two validation layers (the FLAG 1
dual-gate discipline):

* **Full Draft 2020-12 validation** via ``jsonschema`` — dev-only dep,
  ``importorskip``-gated (CI installs ``requirements.txt`` only). Every handler
  response in this file is also checked when the dep is present, plus an
  agreement battery proving the stdlib request classifier and the vendored
  schema give the same valid/invalid verdicts.
* **A stdlib structural gate that always runs** (CI included), deriving its
  required lists / enums / patterns from the vendored schema JSON itself so
  test and schema cannot drift.

Behaviour pins port the semantics of mineverse ``tests/test_actions.py``
(the shim contract fixtures — the FLAG 2 done-criterion) against the real
handler: signing, skew, schema classification, allowlist, actor lookup,
idempotent replay (accepted AND rejected), key-reuse 409, rate limiting with
``Retry-After``, dormancy, and the binding audit requirement.
"""

from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

import mining_write_api as mwa

_FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "mineverse"
ACTION_SCHEMA = json.loads((_FIXTURES / "mining_action.v1.schema.json").read_text())
RESPONSE_SCHEMA = json.loads(
    (_FIXTURES / "mining_action_response.v1.schema.json").read_text()
)

try:  # optional dev-only dep — CI runs the stdlib gate below instead
    import jsonschema
except ImportError:  # pragma: no cover - CI path
    jsonschema = None

SECRET = "test-write-secret-not-a-secret"
TEST_GUILD = "987654321098765432"
OTHER_GUILD = "111111111111111111"
SUID = "100000000000000001"

_uuid_counter = iter(range(1, 10_000))


def new_action_id() -> str:
    return f"00000000-0000-4000-8000-{next(_uuid_counter):012d}"


def make_proposal(action, params, *, suid=SUID, guild_id=TEST_GUILD, action_id=None):
    return {
        "contract_version": "1",
        "action_id": action_id or new_action_id(),
        "guild_id": guild_id,
        "suid": suid,
        "action": action,
        "params": params,
    }


# ---------------------------------------------------------------------------
# The stdlib structural response gate (always runs — CI included)
# ---------------------------------------------------------------------------


def assert_response_conforms(payload: dict) -> None:
    props = RESPONSE_SCHEMA["properties"]
    assert set(RESPONSE_SCHEMA["required"]) <= set(payload), payload
    assert set(payload) <= set(props), "envelope is additionalProperties:false"
    assert payload["contract_version"] == props["contract_version"]["const"]
    assert re.match(props["action_id"]["pattern"], payload["action_id"])
    assert payload["status"] in props["status"]["enum"]
    assert payload["reason_code"] in props["reason_code"]["enum"]
    assert isinstance(payload["message"], str)
    assert isinstance(payload["replayed"], bool)
    if payload["status"] == "accepted":
        # The schema's allOf: accepted iff reason ok iff result present.
        assert payload["reason_code"] == "ok"
        assert "result" in payload
        result = payload["result"]
        rspec = props["result"]
        assert set(rspec["required"]) <= set(result)
        assert set(result) <= set(rspec["properties"])
        assert isinstance(result["state_delta"], dict)
        generated = result["snapshot_generated_at"]
        assert isinstance(generated, str) and generated.endswith("Z")
    else:
        assert payload["reason_code"] != "ok"
        assert "result" not in payload
    if jsonschema is not None:  # the full gate rides along in dev envs
        jsonschema.Draft202012Validator(RESPONSE_SCHEMA).validate(payload)


# ---------------------------------------------------------------------------
# Request/transport plumbing (handler invoked directly — the control_api style)
# ---------------------------------------------------------------------------


def _request(body: bytes, *, headers=None, path=mwa.ACTION_PATH, method="POST"):
    req = MagicMock()
    req.headers = headers or {}
    req.method = method
    req.path = path
    req.app = {"bot": MagicMock()}

    async def _read() -> bytes:
        return body

    req.read = _read
    return req


def signed_headers(body: bytes, *, secret=SECRET, timestamp=None, signature=None):
    ts = timestamp if timestamp is not None else str(int(time.time()))
    sig = (
        signature
        if signature is not None
        else mwa.sign(secret, "POST", mwa.ACTION_PATH, ts, body)
    )
    return {mwa.HEADER_TIMESTAMP: ts, mwa.HEADER_SIGNATURE: sig}


async def post_raw(body: bytes, headers=None):
    response = await mwa.handle_action(_request(body, headers=headers))
    payload = json.loads(response.text)
    assert_response_conforms(payload)
    return response.status, payload, response


async def send(proposal, **kwargs):
    """Sign + POST a proposal; every response is contract-validated."""
    body = json.dumps(proposal, separators=(",", ":"), sort_keys=True).encode()
    status, payload, response = await post_raw(body, signed_headers(body, **kwargs))
    return status, payload, response


# ---------------------------------------------------------------------------
# Fixtures — configured env, fake idempotency store, audit capture, fake game
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    monkeypatch.setenv(mwa.ENV_SECRET, SECRET)
    monkeypatch.setenv(mwa.ENV_GUILD_ALLOWLIST, TEST_GUILD)
    mwa._reset_rate_limiter_for_tests()
    yield
    mwa._reset_rate_limiter_for_tests()


class FakeStore:
    """Dict twin of ``utils/db/mining_web_actions`` (per-test, in-memory)."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict] = {}
        self.purges = 0

    async def get_web_action(self, guild_id, action_id, *, max_age_hours=24):
        row = self.rows.get((guild_id, action_id))
        return copy.deepcopy(row) if row is not None else None

    async def put_web_action(self, guild_id, action_id, digest, status, response):
        self.rows[(guild_id, action_id)] = {
            "body_digest": digest,
            "http_status": status,
            "response": copy.deepcopy(response),
        }

    async def purge_web_actions(self, *, older_than_hours=24):
        self.purges += 1


@pytest.fixture()
def store(monkeypatch):
    fake = FakeStore()
    monkeypatch.setattr(
        "utils.db.mining_web_actions.get_web_action", fake.get_web_action
    )
    monkeypatch.setattr(
        "utils.db.mining_web_actions.put_web_action", fake.put_web_action
    )
    monkeypatch.setattr(
        "utils.db.mining_web_actions.purge_web_actions", fake.purge_web_actions
    )
    return fake


@pytest.fixture()
def audit_log(monkeypatch):
    calls: list[dict] = []

    async def _capture(**kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr("services.audit_events.emit_audit_action", _capture)
    return calls


@pytest.fixture()
def game(monkeypatch, store, audit_log):
    """A fully stubbed happy-path game: known actor, deterministic workflow
    results, canned projection reads. Returns the workflow mock namespace."""
    monkeypatch.setattr(
        "utils.db.games.mining_player_state.has_player_state",
        AsyncMock(return_value=True),
    )
    workflow = SimpleNamespace(
        mine=AsyncMock(
            return_value=SimpleNamespace(found="diamond", amount=1, depth=3)
        ),
        descend=AsyncMock(return_value=SimpleNamespace(moved=True, depth=3, hint=None)),
        ascend=AsyncMock(return_value=SimpleNamespace(moved=True, depth=2, hint=None)),
        sell=AsyncMock(
            return_value=SimpleNamespace(
                ok=True, message="Sold 3× iron for 30 coins.", new_balance=18480
            )
        ),
        vault_deposit=AsyncMock(
            return_value=SimpleNamespace(ok=True, message="Deposited.")
        ),
        vault_withdraw=AsyncMock(
            return_value=SimpleNamespace(ok=True, message="Withdrew.")
        ),
        equip=AsyncMock(
            return_value=SimpleNamespace(ok=True, message="equipped iron helmet.")
        ),
    )
    for name in vars(workflow):
        monkeypatch.setattr(
            f"services.mining_workflow.{name}", getattr(workflow, name)
        )
    monkeypatch.setattr("utils.equipment.slot_for", lambda item: "helmet")
    reads = {
        "get_mining_inventory": AsyncMock(return_value={"iron": 60, "diamond": 10}),
        "get_vault": AsyncMock(return_value={"gold": 120}),
        "get_equipment": AsyncMock(return_value={"helmet": "iron helmet"}),
        "get_gear_wear": AsyncMock(return_value={}),
        "get_coins": AsyncMock(return_value=18480),
        "get_game_xp": AsyncMock(return_value={"mining": 6245}),
        "get_max_depth": AsyncMock(return_value=2),
    }
    for name, mock in reads.items():
        monkeypatch.setattr(f"utils.db.{name}", mock)
    return workflow


# ---------------------------------------------------------------------------
# Vendored-schema pins: module constants derive from the contract, not vibes
# ---------------------------------------------------------------------------


def test_action_enum_matches_the_vendored_schema():
    assert list(mwa.ACTIONS) == ACTION_SCHEMA["properties"]["action"]["enum"]


def test_equip_slot_enum_matches_schema_and_superbot_slots():
    schema_slots = ACTION_SCHEMA["$defs"]["equipParams"]["properties"]["slot"]["enum"]
    assert list(mwa.EQUIP_SLOTS) == schema_slots
    from utils import equipment

    assert tuple(equipment.SLOTS) == tuple(mwa.EQUIP_SLOTS)


def test_placeholder_action_id_is_uuid_shaped():
    pattern = RESPONSE_SCHEMA["properties"]["action_id"]["pattern"]
    assert re.match(pattern, mwa.PLACEHOLDER_ACTION_ID)


# ---------------------------------------------------------------------------
# Signing (byte-compatible with mineverse server/actions.py)
# ---------------------------------------------------------------------------


def test_sign_verify_round_trip():
    body = b'{"hello":"world"}'
    ts = str(int(time.time()))
    sig = mwa.sign(SECRET, "POST", mwa.ACTION_PATH, ts, body)
    assert mwa.verify(SECRET, "POST", mwa.ACTION_PATH, ts, body, sig) is None


def test_verify_rejects_bad_signatures():
    body = b"{}"
    ts = str(int(time.time()))
    sig = mwa.sign(SECRET, "POST", mwa.ACTION_PATH, ts, body)
    cases = [
        ("", "empty"),
        ("deadbeef", "wrong"),
        (mwa.sign("other-secret", "POST", mwa.ACTION_PATH, ts, body), "wrong key"),
        (mwa.sign(SECRET, "POST", "/other/path", ts, body), "wrong path"),
        (mwa.sign(SECRET, "POST", mwa.ACTION_PATH, ts, b"{ }"), "wrong body"),
    ]
    for bad, label in cases:
        assert (
            mwa.verify(SECRET, "POST", mwa.ACTION_PATH, ts, body, bad)
            == "invalid_signature"
        ), label
    # A tampered timestamp breaks the signature (it is signed).
    assert (
        mwa.verify(SECRET, "POST", mwa.ACTION_PATH, str(int(ts) + 1), body, sig)
        == "invalid_signature"
    )


def test_verify_rejects_stale_timestamps_both_directions():
    body = b"{}"
    for offset in (-mwa.SKEW_SECONDS - 60, mwa.SKEW_SECONDS + 60):
        ts = str(int(time.time()) + offset)
        sig = mwa.sign(SECRET, "POST", mwa.ACTION_PATH, ts, body)
        assert (
            mwa.verify(SECRET, "POST", mwa.ACTION_PATH, ts, body, sig)
            == "stale_timestamp"
        ), offset


def test_verify_checks_signature_before_timestamp():
    # An unsigned request never learns anything about the clock.
    stale = str(int(time.time()) - mwa.SKEW_SECONDS - 999)
    assert (
        mwa.verify(SECRET, "POST", mwa.ACTION_PATH, stale, b"{}", "0" * 64)
        == "invalid_signature"
    )


# ---------------------------------------------------------------------------
# Transport auth through the handler (pre-auth: never audited, never stored)
# ---------------------------------------------------------------------------


async def test_rejects_bad_signature(store, audit_log):
    body = json.dumps(make_proposal("mine", {})).encode()
    status, payload, _ = await post_raw(body, signed_headers(body, signature="0" * 64))
    assert status == 401
    assert payload["reason_code"] == "invalid_signature"
    assert payload["action_id"] == mwa.PLACEHOLDER_ACTION_ID
    assert audit_log == []  # unattributable — never audited
    assert store.rows == {}


async def test_rejects_wrong_secret(store, audit_log):
    body = json.dumps(make_proposal("mine", {})).encode()
    status, payload, _ = await post_raw(
        body, signed_headers(body, secret="some-other-secret")
    )
    assert status == 401
    assert payload["reason_code"] == "invalid_signature"


async def test_rejects_unsigned_probe(store, audit_log):
    # The conformance smoke from mineverse tests/test_actions.py: one unsigned
    # probe draws the pre-auth rejection and can never execute or audit.
    status, payload, _ = await post_raw(b"{}", headers={})
    assert status == 401
    assert payload["reason_code"] == "invalid_signature"
    assert audit_log == []


async def test_rejects_stale_timestamp(store, audit_log):
    body = json.dumps(make_proposal("mine", {})).encode()
    stale = str(int(time.time()) - mwa.SKEW_SECONDS - 60)
    status, payload, _ = await post_raw(body, signed_headers(body, timestamp=stale))
    assert status == 401
    assert payload["reason_code"] == "stale_timestamp"
    assert audit_log == []


async def test_secret_cleared_after_registration_fails_closed(
    monkeypatch, store, audit_log
):
    body = json.dumps(make_proposal("mine", {})).encode()
    headers = signed_headers(body)
    monkeypatch.delenv(mwa.ENV_SECRET)
    status, payload, _ = await post_raw(body, headers)
    assert status == 401
    assert payload["reason_code"] == "invalid_signature"


# ---------------------------------------------------------------------------
# Request-schema classification (the shim's reason-code taxonomy)
# ---------------------------------------------------------------------------


async def test_rejects_malformed_json_body(store, audit_log):
    body = b"{not json"
    status, payload, _ = await post_raw(body, signed_headers(body))
    assert status == 400
    assert payload["reason_code"] == "malformed_request"
    assert payload["action_id"] == mwa.PLACEHOLDER_ACTION_ID
    assert audit_log == []  # schema-invalid — not attributable, not audited


async def test_rejects_non_object_body(store, audit_log):
    body = b"[1, 2, 3]"
    status, payload, _ = await post_raw(body, signed_headers(body))
    assert status == 400
    assert payload["reason_code"] == "malformed_request"


async def test_rejects_unknown_action(store, audit_log):
    status, payload, _ = await send(make_proposal("sell_all", {}))
    assert status == 400
    assert payload["reason_code"] == "unknown_action"


async def test_rejects_invalid_params(store, audit_log):
    status, payload, _ = await send(make_proposal("sell", {"item": "iron"}))
    assert status == 400
    assert payload["reason_code"] == "invalid_params"


async def test_rejects_params_on_parameterless_action(store, audit_log):
    status, payload, _ = await send(make_proposal("mine", {"extra": 1}))
    assert status == 400
    assert payload["reason_code"] == "invalid_params"


async def test_rejects_unsupported_contract_version(store, audit_log):
    proposal = make_proposal("mine", {})
    proposal["contract_version"] = "2"
    status, payload, _ = await send(proposal)
    assert status == 400
    assert payload["reason_code"] == "unsupported_contract_version"


async def test_rejects_extra_envelope_fields_echoing_the_action_id(store, audit_log):
    proposal = make_proposal("mine", {})
    proposal["surprise"] = True
    status, payload, _ = await send(proposal)
    assert status == 400
    assert payload["reason_code"] == "malformed_request"
    assert payload["action_id"] == proposal["action_id"]  # echoable → echoed


async def test_rejects_malformed_action_id_with_placeholder(store, audit_log):
    proposal = make_proposal("mine", {}, action_id="x")
    proposal["action_id"] = "not-a-uuid"
    status, payload, _ = await send(proposal)
    assert status == 400
    assert payload["reason_code"] == "malformed_request"
    assert payload["action_id"] == mwa.PLACEHOLDER_ACTION_ID


@pytest.mark.skipif(jsonschema is None, reason="jsonschema is a dev-only dep")
def test_classifier_agrees_with_the_vendored_schema():
    """The stdlib classifier and Draft 2020-12 must give the same verdicts."""
    validator = jsonschema.Draft202012Validator(ACTION_SCHEMA)
    battery = [
        make_proposal("mine", {}),
        make_proposal("descend", {}),
        make_proposal("ascend", {}),
        make_proposal("sell", {"item": "iron", "quantity": 3}),
        make_proposal("vault_deposit", {"amount": 500}),
        make_proposal("vault_withdraw", {"amount": 200}),
        make_proposal("equip", {"item": "iron helmet", "slot": "helmet"}),
        # invalid shapes
        {**make_proposal("mine", {}), "contract_version": "2"},
        {**make_proposal("mine", {}), "action": "sell_all"},
        {**make_proposal("mine", {}), "surprise": True},
        {**make_proposal("mine", {}), "action_id": "nope"},
        {**make_proposal("mine", {}), "guild_id": "not-digits"},
        {**make_proposal("mine", {}), "suid": 12345},
        make_proposal("mine", {"extra": 1}),
        make_proposal("sell", {"item": "iron"}),
        make_proposal("sell", {"item": "", "quantity": 3}),
        make_proposal("sell", {"item": "iron", "quantity": 0}),
        make_proposal("sell", {"item": "iron", "quantity": True}),
        make_proposal("vault_deposit", {}),
        make_proposal("vault_deposit", {"amount": 0}),
        make_proposal("equip", {"item": "iron helmet", "slot": "hat"}),
        make_proposal("equip", {"item": "iron helmet"}),
        {k: v for k, v in make_proposal("mine", {}).items() if k != "suid"},
    ]
    for proposal in battery:
        schema_ok = not list(validator.iter_errors(proposal))
        classifier_ok = mwa.classify_proposal(proposal) is None
        assert schema_ok == classifier_ok, proposal


# ---------------------------------------------------------------------------
# Allowlist + actor lookup
# ---------------------------------------------------------------------------


async def test_rejects_guild_off_the_allowlist(game, store, audit_log):
    status, payload, _ = await send(make_proposal("mine", {}, guild_id=OTHER_GUILD))
    assert status == 403
    assert payload["reason_code"] == "guild_not_allowed"
    assert audit_log[-1]["extra_fields"]["outcome"] == "rejected:guild_not_allowed"
    assert (OTHER_GUILD, payload["action_id"]) in store.rows  # stored for replay


async def test_empty_allowlist_fails_closed(monkeypatch, game, store, audit_log):
    monkeypatch.delenv(mwa.ENV_GUILD_ALLOWLIST)
    status, payload, _ = await send(make_proposal("mine", {}))
    assert status == 403
    assert payload["reason_code"] == "guild_not_allowed"


async def test_rejects_unknown_actor(game, monkeypatch, store, audit_log):
    monkeypatch.setattr(
        "utils.db.games.mining_player_state.has_player_state",
        AsyncMock(return_value=False),
    )
    status, payload, _ = await send(make_proposal("mine", {}))
    assert status == 404
    assert payload["reason_code"] == "actor_not_found"
    assert audit_log[-1]["extra_fields"]["outcome"] == "rejected:actor_not_found"


# ---------------------------------------------------------------------------
# The happy path, per enum action (each 1:1 onto its mining_workflow op)
# ---------------------------------------------------------------------------


async def test_mine_accepted_with_projected_delta(game, store, audit_log):
    proposal = make_proposal("mine", {})
    assert mwa.classify_proposal(proposal) is None
    status, payload, _ = await send(proposal)
    assert status == 200
    assert payload["status"] == "accepted"
    assert payload["reason_code"] == "ok"
    assert payload["replayed"] is False
    game.mine.assert_awaited_once_with(int(SUID), int(TEST_GUILD))
    delta = payload["result"]["state_delta"]
    assert set(delta) == {"mining_inventory", "gear_wear", "xp"}
    assert delta["mining_inventory"] == {"iron": 60, "diamond": 10}
    assert delta["xp"]["game"] == "mining"
    assert delta["xp"]["game_total"] == 6245


async def test_descend_reports_depth_and_new_record(game, store, audit_log):
    status, payload, _ = await send(make_proposal("descend", {}))
    assert status == 200
    # Stubbed record_before=2, new depth 3 → a record.
    assert payload["result"]["state_delta"] == {"depth": 3, "record_depth": 3}


async def test_ascend_reports_depth_only(game, store, audit_log):
    status, payload, _ = await send(make_proposal("ascend", {}))
    assert status == 200
    assert payload["result"]["state_delta"] == {"depth": 2}


async def test_sell_maps_item_and_quantity(game, store, audit_log):
    status, payload, _ = await send(
        make_proposal("sell", {"item": "iron", "quantity": 3})
    )
    assert status == 200
    game.sell.assert_awaited_once_with(int(SUID), int(TEST_GUILD), "iron", 3)
    delta = payload["result"]["state_delta"]
    assert set(delta) == {"coins", "mining_inventory"}
    assert delta["coins"] == 18480


async def test_vault_ops_map_amount_onto_the_coins_item(game, store, audit_log):
    status, payload, _ = await send(make_proposal("vault_deposit", {"amount": 500}))
    assert status == 200
    game.vault_deposit.assert_awaited_once_with(
        int(SUID), int(TEST_GUILD), "coins", 500
    )
    assert set(payload["result"]["state_delta"]) == {"mining_inventory", "vault"}
    status, payload, _ = await send(make_proposal("vault_withdraw", {"amount": 200}))
    assert status == 200
    game.vault_withdraw.assert_awaited_once_with(
        int(SUID), int(TEST_GUILD), "coins", 200
    )


async def test_equip_flips_the_gear_slot(game, store, audit_log):
    status, payload, _ = await send(
        make_proposal("equip", {"item": "iron helmet", "slot": "helmet"})
    )
    assert status == 200
    game.equip.assert_awaited_once_with(int(SUID), int(TEST_GUILD), "iron helmet")
    assert payload["result"]["state_delta"]["equipment"] == {"helmet": "iron helmet"}


async def test_equip_slot_mismatch_is_an_economy_rejection(game, store, audit_log):
    status, payload, _ = await send(
        make_proposal("equip", {"item": "iron helmet", "slot": "boots"})
    )
    assert status == 422
    assert payload["reason_code"] == "economy_rejection"
    game.equip.assert_not_awaited()  # vetoed before touching the workflow


# ---------------------------------------------------------------------------
# Economy rejections (the game's own verdict, relayed as 422)
# ---------------------------------------------------------------------------


async def test_economy_rejections_are_422(game, store, audit_log):
    game.ascend.return_value = SimpleNamespace(moved=False, depth=0, hint=None)
    status, payload, _ = await send(make_proposal("ascend", {}))
    assert status == 422
    assert payload["reason_code"] == "economy_rejection"
    game.sell.return_value = SimpleNamespace(
        ok=False, message="You only have 0× diamond to sell.", new_balance=None
    )
    status, payload, _ = await send(
        make_proposal("sell", {"item": "diamond", "quantity": 999})
    )
    assert status == 422
    assert payload["reason_code"] == "economy_rejection"
    assert audit_log[-1]["extra_fields"]["outcome"] == "rejected:economy_rejection"


async def test_workflow_fault_is_500_internal_error_never_stored(
    game, store, audit_log
):
    game.mine.side_effect = RuntimeError("db down")
    proposal = make_proposal("mine", {})
    status, payload, _ = await send(proposal)
    assert status == 500
    assert payload["reason_code"] == "internal_error"
    # Retryable with the SAME action_id (contract): nothing was stored.
    assert (TEST_GUILD, proposal["action_id"]) not in store.rows
    assert audit_log[-1]["extra_fields"]["outcome"] == "rejected:internal_error"


# ---------------------------------------------------------------------------
# Idempotent replay
# ---------------------------------------------------------------------------


async def test_replay_returns_original_response_without_reexecuting(
    game, store, audit_log
):
    action_id = new_action_id()
    proposal = make_proposal("mine", {}, action_id=action_id)
    status_1, first, _ = await send(proposal)
    status_2, second, _ = await send(proposal)  # byte-identical replay
    assert (status_1, status_2) == (200, 200)
    assert first["replayed"] is False
    assert second["replayed"] is True
    stripped = dict(second)
    stripped["replayed"] = False
    assert stripped == first  # the ORIGINAL response, verbatim
    game.mine.assert_awaited_once()  # executed exactly once
    assert len(audit_log) == 1  # the replay was not re-audited


async def test_action_id_reuse_with_different_body_is_409(game, store, audit_log):
    action_id = new_action_id()
    await send(make_proposal("mine", {}, action_id=action_id))
    status, payload, _ = await send(make_proposal("descend", {}, action_id=action_id))
    assert status == 409
    assert payload["reason_code"] == "replayed_action"
    assert audit_log[-1]["extra_fields"]["outcome"] == "rejected:replayed_action"
    # And the original response is still intact for a genuine replay.
    status, payload, _ = await send(make_proposal("mine", {}, action_id=action_id))
    assert status == 200
    assert payload["replayed"] is True


async def test_rejected_outcomes_replay_too(game, store, audit_log):
    game.ascend.return_value = SimpleNamespace(moved=False, depth=0, hint=None)
    action_id = new_action_id()
    proposal = make_proposal("ascend", {}, action_id=action_id)
    status_1, first, _ = await send(proposal)
    status_2, second, _ = await send(proposal)
    assert (status_1, status_2) == (422, 422)
    assert second["replayed"] is True
    assert len(audit_log) == 1  # the replay was not re-audited
    game.ascend.assert_awaited_once()


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_rate_limiter_burst_window_and_retry_after():
    limiter = mwa.RateLimiter(((2, 10.0),))
    assert limiter.check("k", now=0.0) is None
    assert limiter.check("k", now=1.0) is None
    assert limiter.check("k", now=2.0) == 8  # oldest (t=0) frees the slot at 10
    assert limiter.check("other", now=2.0) is None  # keys are independent
    assert limiter.check("k", now=10.5) is None  # the window slid


def test_rate_limiter_enforces_both_contract_windows():
    limiter = mwa.RateLimiter()  # the contract defaults: 10/10s + 60/60s
    # Burst: the 11th action inside 10s is refused with a sane Retry-After.
    for i in range(10):
        assert limiter.check("k", now=float(i) * 0.1) is None
    retry = limiter.check("k", now=1.0)
    assert isinstance(retry, int) and 1 <= retry <= 10
    # Sustained: 60 spaced actions consume the minute budget; the 61st while
    # 60 sit inside the sliding minute is refused even with a calm burst rate.
    limiter.reset()
    for i in range(60):
        assert limiter.check("s", now=float(i)) is None, i
    retry = limiter.check("s", now=59.5)
    assert isinstance(retry, int) and retry >= 1


async def test_over_budget_answers_429_with_retry_after(
    game, store, audit_log, monkeypatch
):
    stub = SimpleNamespace(check=lambda key, **kw: 7, reset=lambda: None)
    monkeypatch.setattr(mwa, "_limiter", stub)
    proposal = make_proposal("mine", {})
    status, payload, response = await send(proposal)
    assert status == 429
    assert payload["reason_code"] == "rate_limited"
    assert response.headers["Retry-After"] == "7"
    assert audit_log[-1]["extra_fields"]["outcome"] == "rejected:rate_limited"
    # NOT stored for idempotency: a retry after the window is a fresh run.
    assert (TEST_GUILD, proposal["action_id"]) not in store.rows


async def test_rate_limit_keys_on_suid_and_guild(game, store, audit_log, monkeypatch):
    seen = []

    def _check(key, **kw):
        seen.append(key)
        return None

    monkeypatch.setattr(
        mwa, "_limiter", SimpleNamespace(check=_check, reset=lambda: None)
    )
    await send(make_proposal("mine", {}))
    assert seen == [f"{SUID}:{TEST_GUILD}"]


# ---------------------------------------------------------------------------
# The audit requirement (binding — contract § AUDIT REQUIREMENT)
# ---------------------------------------------------------------------------


async def test_accepted_action_is_audited_with_the_contract_fields(
    game, store, audit_log
):
    proposal = make_proposal("sell", {"item": "iron", "quantity": 2})
    await send(proposal)
    assert len(audit_log) == 1
    entry = audit_log[0]
    # The canonical seam fields (services/audit_events.py).
    assert entry["mutation_id"] == proposal["action_id"]
    assert entry["subsystem"] == "mining"
    assert entry["mutation_type"] == "web_action:sell"
    assert entry["scope"] == "guild"
    assert entry["guild_id"] == int(TEST_GUILD)
    assert entry["actor_id"] == int(SUID)
    assert entry["actor_type"] == "web_player"
    # The mineverse contract fields, riding extra_fields.
    extra = entry["extra_fields"]
    assert extra["action_id"] == proposal["action_id"]
    assert extra["action"] == "sell"
    assert extra["suid"] == SUID
    assert extra["outcome"] == "accepted:ok"
    assert extra["contract_version"] == "1"
    assert extra["origin"] == "web"
    assert len(extra["params_digest"]) == 64  # sha256 hex of the params
    expected_digest = mwa.params_digest({"item": "iron", "quantity": 2})
    assert extra["params_digest"] == expected_digest
    assert extra["timestamp"].endswith("Z")


async def test_every_attributable_rejection_is_audited(game, store, audit_log):
    # guild_not_allowed + actor path already covered; economy_rejection here.
    game.descend.return_value = SimpleNamespace(moved=False, depth=3, hint="too dark")
    await send(make_proposal("descend", {}))
    assert audit_log[-1]["extra_fields"]["outcome"] == "rejected:economy_rejection"
    assert audit_log[-1]["extra_fields"]["action"] == "descend"


async def test_audit_rides_the_real_seam_extra_fields(monkeypatch):
    """emit_audit_action forwards extra_fields into the bus payload (and the
    canonical 11 win a collision) — the additive seam change FLAG 2 relies on."""
    from services import audit_events

    captured = {}

    async def _emit(event, **payload):
        captured[event] = payload

    monkeypatch.setattr("core.events.bus.emit", _emit)
    from datetime import datetime, timezone

    ok = await audit_events.emit_audit_action(
        mutation_id="m-1",
        subsystem="mining",
        mutation_type="web_action:mine",
        target="miner:1",
        scope="guild",
        guild_id=1,
        prev_value=None,
        new_value="accepted:ok",
        actor_id=1,
        actor_type="web_player",
        occurred_at=datetime.now(timezone.utc),
        extra_fields={"origin": "web", "subsystem": "SHADOWED"},
    )
    assert ok is True
    payload = captured[audit_events.EVT_AUDIT_ACTION_RECORDED]
    assert payload["origin"] == "web"
    assert payload["subsystem"] == "mining"  # canonical fields win collisions


# ---------------------------------------------------------------------------
# Log/audit hygiene (CodeQL round: taint-free canonicalizers, scrubbed sinks)
# ---------------------------------------------------------------------------


def test_log_canonicalizers_yield_constants_never_request_bytes():
    assert mwa._clean_action("mine") == "mine"
    assert mwa._clean_action("mine\ninjected") == "<unknown-action>"
    action_id = "00000000-0000-4000-8000-000000000001"
    assert mwa._clean_action_id(action_id) == action_id
    assert mwa._clean_action_id("not-a-uuid\r\n") == mwa.PLACEHOLDER_ACTION_ID
    assert mwa._clean_snowflake("42") == "42"
    assert mwa._clean_snowflake("42\nfake") == "0"


def test_economy_rejection_carries_an_explicit_public_message():
    veto = mwa.EconomyRejectionError("the game said no")
    assert veto.public_message == "the game said no"


def test_audit_failure_log_interpolation_is_newline_scrubbed():
    from services.audit_events import _log_safe

    assert _log_safe("a\r\nb") == "a\\r\\nb"
    assert _log_safe("plain") == "plain"


# ---------------------------------------------------------------------------
# Dormancy + registration (the control_api discipline)
# ---------------------------------------------------------------------------


def test_dormant_without_the_secret(monkeypatch):
    monkeypatch.delenv(mwa.ENV_SECRET)
    app = web.Application()
    assert mwa.register_mining_write_routes(app, MagicMock()) is False
    assert len(app.router.routes()) == 0


def test_registers_when_configured():
    app = web.Application()
    assert mwa.register_mining_write_routes(app, MagicMock()) is True
    routes = [
        (route.method, route.resource.canonical) for route in app.router.routes()
    ]
    assert ("POST", mwa.ACTION_PATH) in routes


def test_allowlist_parses_and_drops_junk(monkeypatch):
    monkeypatch.setenv(
        mwa.ENV_GUILD_ALLOWLIST, f" {TEST_GUILD} , not-a-guild ,, 42 "
    )
    assert mwa.allowed_guilds() == frozenset({TEST_GUILD, "42"})
    monkeypatch.delenv(mwa.ENV_GUILD_ALLOWLIST)
    assert mwa.allowed_guilds() == frozenset()
