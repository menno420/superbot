r"""Mineverse mining WRITE endpoint — the bot side of the v1 write contract.

FLAG 2 of the mineverse lane. The superbot-mineverse web app never touches
Postgres and never holds the bot token; a web "write" is a **proposal**: the
web server POSTs a signed action document here and this module decides,
executes (only ever through the single mining write boundary,
``services/mining_workflow.py``), audits, and answers.

Contract of record (superbot-mineverse main):
``schemas/mining_action.v1.schema.json`` (request) ·
``schemas/mining_action_response.v1.schema.json`` (response) ·
``docs/mining-write-contract.md`` (semantics — reason-code taxonomy, HTTP
mapping, idempotency, audit). Vendored schema copies are pinned under
``tests/fixtures/mineverse/`` and enforced by
``tests/unit/runtime/test_mining_write_api.py``.

Design (the ``control_api`` discipline — same aiohttp app, no second server):

* **Dormant by default.** The route is registered only when
  ``MINING_WRITE_SHARED_SECRET`` is set; every current deploy gets zero
  behaviour change.
* **HMAC transport auth** (contract § "Transport auth"): headers
  ``X-Mineverse-Timestamp`` / ``X-Mineverse-Signature``; the signature is
  ``hex(HMAC_SHA256(secret, METHOD\nPATH\nTIMESTAMP\nsha256_hex(BODY)))``,
  verified constant-time, signature BEFORE the ±300 s skew window (an
  unsigned probe learns nothing about the clock).
* **TEST GUILD ONLY** (the stage-(d) wall): only guilds listed in
  ``MINING_WRITE_GUILD_ALLOWLIST`` (comma-separated snowflakes) may execute;
  every other guild is ``guild_not_allowed`` (403). Widening the allowlist
  to production guilds is the OWNER's stage-(d) live-cutover flag — nothing
  in this module may do it implicitly.
* **Idempotency by ``action_id``** with restart-safe ≥24 h retention in the
  ``mining_web_actions`` table (migration 105): byte-identical replay →
  the original response with ``replayed: true``, never a re-execution; key
  reuse with a different body → 409 ``replayed_action``.
* **Rate limits** per ``(suid, guild_id)``: 10/10 s burst + 60/60 s
  sustained → 429 with ``Retry-After``; rate-limited proposals are NOT
  stored for idempotency (contract § "Rate limits").
* **Audit EVERY attributable action, accepted or rejected** (the contract's
  binding audit requirement — ``mining_workflow`` itself emits no audit):
  ``emit_audit_action(subsystem="mining", actor_type="web_player", ...)``
  carrying action_id / action / suid / guild_id / params_digest / outcome /
  timestamp / contract_version / origin="web". Pre-auth rejections
  (``invalid_signature`` / ``stale_timestamp``) and schema-invalid bodies
  are not attributable to an actor and are not audited (the shim reference
  behaviour); idempotent replays are not re-audited (nothing executed).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any

from aiohttp import web

logger = logging.getLogger("bot.mining_write_api")

# --- contract constants ------------------------------------------------------

ENV_SECRET = "MINING_WRITE_SHARED_SECRET"
ENV_GUILD_ALLOWLIST = "MINING_WRITE_GUILD_ALLOWLIST"

ACTION_PATH = "/relay/mining/action"
HEADER_SIGNATURE = "X-Mineverse-Signature"
HEADER_TIMESTAMP = "X-Mineverse-Timestamp"
SKEW_SECONDS = 300
CONTRACT_VERSION = "1"

#: Echoed when a proposal is too broken to carry a usable action_id
#: (contract: responses always echo a UUID-shaped action_id).
PLACEHOLDER_ACTION_ID = "00000000-0000-4000-8000-000000000000"

#: The CLOSED v1 action enum — each maps 1:1 to a mining_workflow op.
#: Widening it is an additive schema change made in the mineverse repo FIRST.
ACTIONS = (
    "mine",
    "descend",
    "ascend",
    "sell",
    "vault_deposit",
    "vault_withdraw",
    "equip",
)

#: The READ contract's closed equipment-slot enum (byte-identical to
#: ``utils.equipment.SLOTS`` — asserted in tests against the vendored schema).
EQUIP_SLOTS = (
    "tool",
    "light",
    "charm",
    "weapon",
    "shield",
    "helmet",
    "chestplate",
    "leggings",
    "boots",
)

_UUID_V4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_DIGITS = re.compile(r"^[0-9]+$")

_ENVELOPE_KEYS = frozenset(
    ("contract_version", "action_id", "guild_id", "suid", "action", "params")
)

# Rate-limit budgets per (suid, guild_id) — contract § "Rate limits".
RATE_LIMITS = ((10, 10.0), (60, 60.0))  # (max events, window seconds)


# --- host configuration (read at call time — the control_api dormancy rule) --


def shared_secret() -> str | None:
    """The HMAC shared secret, or ``None`` when the endpoint is dormant."""
    # Literal name (== ENV_SECRET) so scan_env_usage.py maps it into
    # docs/operations/env-vars.md — the scanner only sees string literals.
    secret = os.environ.get("MINING_WRITE_SHARED_SECRET", "").strip()
    return secret or None


def allowed_guilds() -> frozenset[str]:
    """The hard test-guild allowlist (string snowflakes) from the env.

    Unset/empty → NO guild may execute (every proposal is 403
    ``guild_not_allowed``) — fail-closed. Non-snowflake entries are logged
    and dropped, never guessed at.
    """
    # Literal name (== ENV_GUILD_ALLOWLIST) — see shared_secret()'s note.
    raw = os.environ.get("MINING_WRITE_GUILD_ALLOWLIST", "")
    guilds = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if _DIGITS.match(part):
            guilds.add(part)
        else:
            logger.warning(
                "mining_write_api: %s entry %r is not a guild snowflake — dropped",
                ENV_GUILD_ALLOWLIST,
                part,
            )
    return frozenset(guilds)


# --- canonical HMAC signing (mirrors mineverse server/actions.py exactly) ----


def string_to_sign(method: str, path: str, timestamp: str, body: bytes) -> str:
    return "\n".join(
        (method.upper(), path, timestamp, hashlib.sha256(body).hexdigest())
    )


def sign(secret: str, method: str, path: str, timestamp: str, body: bytes) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        string_to_sign(method, path, timestamp, body).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify(
    secret: str,
    method: str,
    path: str,
    timestamp: str,
    body: bytes,
    signature: str,
    *,
    now: float | None = None,
) -> str | None:
    """The contract reason_code for a transport-auth failure, or ``None``.

    Signature first (constant-time), THEN the timestamp window — the
    timestamp is part of the signed string, so a valid signature with a
    bad/stale timestamp is ``stale_timestamp`` and everything else is
    ``invalid_signature`` (byte-compatible with mineverse
    ``server/actions.py::verify``, the contract's canonical implementation).
    """
    if (
        not isinstance(signature, str)
        or not signature
        or not isinstance(timestamp, str)
    ):
        return "invalid_signature"
    expected = sign(secret, method, path, timestamp, body)
    if not hmac.compare_digest(expected, signature.lower()):
        return "invalid_signature"
    try:
        signed_at = int(timestamp)
    except ValueError:
        return "stale_timestamp"
    current = time.time() if now is None else now
    if abs(current - signed_at) > SKEW_SECONDS:
        return "stale_timestamp"
    return None


# --- request-schema classification (stdlib twin of the vendored v1 schema) ---


def _is_count(value: Any, *, minimum: int = 1) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _params_failure(action: str, params: Any) -> str | None:
    """An ``invalid_params`` message when *params* fail *action*'s closed
    sub-schema, else ``None`` (mirrors the schema's allOf/if-then blocks).
    """
    if not isinstance(params, dict):
        return "params must be a JSON object"
    if action in ("mine", "descend", "ascend"):
        if params:
            return f"{action} takes no params (send exactly {{}})"
        return None
    if action == "sell":
        if set(params) != {"item", "quantity"}:
            return "sell params are exactly {item, quantity}"
        if not isinstance(params["item"], str) or not params["item"]:
            return "sell item must be a non-empty string"
        if not _is_count(params["quantity"]):
            return "sell quantity must be an integer >= 1"
        return None
    if action in ("vault_deposit", "vault_withdraw"):
        if set(params) != {"amount"}:
            return f"{action} params are exactly {{amount}}"
        if not _is_count(params["amount"]):
            return f"{action} amount must be an integer >= 1"
        return None
    if action == "equip":
        if set(params) != {"item", "slot"}:
            return "equip params are exactly {item, slot}"
        if not isinstance(params["item"], str) or not params["item"]:
            return "equip item must be a non-empty string"
        if params["slot"] not in EQUIP_SLOTS:
            return "equip slot is outside the closed slot enum"
        return None
    return "unhandled action"  # unreachable: caller checked the enum


def classify_proposal(proposal: Any) -> tuple[str, str] | None:
    """``(reason_code, message)`` when *proposal* violates the v1 request
    schema, else ``None`` — the shim's classification order exactly:
    version → enum → envelope (``malformed_request``) → params
    (``invalid_params``).
    """
    if not isinstance(proposal, dict):
        return ("malformed_request", "body is not a JSON object")
    if proposal.get("contract_version") != CONTRACT_VERSION:
        return (
            "unsupported_contract_version",
            "this executor speaks contract version 1 only",
        )
    if proposal.get("action") not in ACTIONS:
        return ("unknown_action", "action is outside the closed v1 enum")
    extra = set(proposal) - _ENVELOPE_KEYS
    if extra:
        return (
            "malformed_request",
            f"unexpected envelope fields: {sorted(extra)}",
        )
    missing = _ENVELOPE_KEYS - set(proposal)
    if missing:
        return (
            "malformed_request",
            f"missing envelope fields: {sorted(missing)}",
        )
    if not isinstance(proposal["action_id"], str) or not _UUID_V4.match(
        proposal["action_id"]
    ):
        return ("malformed_request", "action_id must be a lowercase UUIDv4")
    for field in ("guild_id", "suid"):
        if not isinstance(proposal[field], str) or not _DIGITS.match(proposal[field]):
            return (
                "malformed_request",
                f"{field} must be a string of digits (snowflake)",
            )
    params_failure = _params_failure(proposal["action"], proposal["params"])
    if params_failure is not None:
        return ("invalid_params", params_failure)
    return None


def _echoable_action_id(proposal: Any) -> str:
    if isinstance(proposal, dict):
        candidate = proposal.get("action_id")
        if isinstance(candidate, str) and _UUID_V4.match(candidate):
            return candidate
    return PLACEHOLDER_ACTION_ID


# --- rate limiting (per (suid, guild_id) — burst + sustained windows) --------


class RateLimiter:
    """Sliding windows; ``check`` returns None (allowed, hit recorded) or the
    integer ``Retry-After`` seconds when any window is over budget.
    """

    def __init__(self, limits: tuple[tuple[int, float], ...] = RATE_LIMITS) -> None:
        self.limits = limits
        self._hits: dict[str, list[float]] = {}

    def check(self, key: str, *, now: float | None = None) -> int | None:
        moment = time.monotonic() if now is None else now
        widest = max(window for _, window in self.limits)
        hits = [t for t in self._hits.get(key, ()) if t > moment - widest]
        retry_after = 0.0
        for max_events, window in self.limits:
            in_window = [t for t in hits if t > moment - window]
            if len(in_window) >= max_events:
                # When the oldest in-window hit ages out, one slot frees up.
                retry_after = max(retry_after, in_window[0] + window - moment)
        self._hits[key] = hits
        if retry_after > 0:
            return max(1, int(retry_after + 0.999))
        hits.append(moment)
        return None

    def reset(self) -> None:
        self._hits.clear()


_limiter = RateLimiter()


def _reset_rate_limiter_for_tests() -> None:
    _limiter.reset()


# --- response envelope --------------------------------------------------------


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _envelope(
    action_id: str,
    reason_code: str,
    message: str,
    *,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "action_id": action_id,
        "status": "accepted" if reason_code == "ok" else "rejected",
        "reason_code": reason_code,
        "message": message,
        "replayed": False,
    }
    if result is not None:
        response["result"] = result
    return response


def _json_response(
    status: int, payload: dict[str, Any], *, headers: dict[str, str] | None = None
) -> web.Response:
    return web.Response(
        text=json.dumps(payload),
        status=status,
        content_type="application/json",
        headers=headers,
    )


# --- audit (the contract's binding requirement) --------------------------------


def params_digest(params: dict[str, Any]) -> str:
    """SHA-256 hex of the canonical params JSON (contract audit field)."""
    return hashlib.sha256(
        json.dumps(params, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


async def _audit(proposal: dict[str, Any], outcome: str) -> None:
    """One audit row per attributable web action, accepted or rejected.

    Rides the shared ``audit.action_recorded`` seam: the canonical 11 fields
    plus the mineverse contract fields via ``extra_fields``. Failure-safe by
    the seam's own contract (a dropped audit event is logged, never raised) —
    and the DB/audit pairing here is emit-after-execute in the handler, the
    same post-commit discipline as ``economy_service.transfer``.
    """
    from services.audit_events import emit_audit_action

    await emit_audit_action(
        mutation_id=proposal["action_id"],
        subsystem="mining",
        mutation_type=f"web_action:{proposal['action']}",
        target=f"miner:{proposal['suid']}",
        scope="guild",
        guild_id=int(proposal["guild_id"]),
        prev_value=None,
        new_value=outcome,
        actor_id=int(proposal["suid"]),
        actor_type="web_player",
        occurred_at=datetime.now(timezone.utc),
        extra_fields={
            "action_id": proposal["action_id"],
            "action": proposal["action"],
            "suid": proposal["suid"],
            "params_digest": params_digest(proposal["params"]),
            "outcome": outcome,
            "timestamp": _iso_utc_now(),
            "contract_version": CONTRACT_VERSION,
            "origin": "web",
        },
    )


# --- state_delta projection (READ-contract field names, new values) -----------


def _count_map(raw: dict[str, int]) -> dict[str, int]:
    return {name: int(count) for name, count in raw.items() if int(count) >= 0}


async def _project_field(field: str, suid: str, guild_id: int) -> Any:
    """One READ-contract per-miner field, projected exactly as the snapshot
    relay (FLAG 1) projects it — the same ``utils/db`` readers, same clamps.
    """
    from utils import db, equipment

    user_int = int(suid)
    if field == "mining_inventory":
        return _count_map(await db.get_mining_inventory(suid, guild_id))
    if field == "vault":
        return _count_map(await db.get_vault(suid, guild_id))
    if field == "equipment":
        equipped = await db.get_equipment(suid, guild_id)
        return {
            slot: item for slot, item in equipped.items() if slot in equipment.SLOTS
        }
    if field == "gear_wear":
        wear: dict[str, int] = {}
        for item, remaining in (await db.get_gear_wear(suid, guild_id)).items():
            maximum = equipment.max_durability(item)
            if maximum is None:
                continue
            wear[item] = max(0, maximum - remaining)
        return wear
    if field == "coins":
        return max(0, await db.get_coins(user_int, guild_id))
    if field == "xp":
        totals = await db.get_game_xp(user_int, guild_id)
        shared_total = sum(totals.values())
        return {
            "game": "mining",
            "game_total": max(0, totals.get("mining", 0)),
            "shared_total": max(0, shared_total),
            "level": max(0, db.level_progress(shared_total)[0]),
        }
    raise ValueError(f"unprojectable field {field}")  # a programming error


async def _project_fields(
    fields: tuple[str, ...], suid: str, guild_id: int
) -> dict[str, Any]:
    return {field: await _project_field(field, suid, guild_id) for field in fields}


# --- execution: the closed enum, 1:1 onto mining_workflow ops ------------------


class EconomyRejectionError(Exception):
    """The game said no — ``mining_workflow``'s domain verdict, relayed (422)."""


async def _execute_action(
    action: str, params: dict[str, Any], suid: str, guild_id: int
) -> tuple[dict[str, Any], str]:
    """Run *action* through ``services/mining_workflow`` — the ONLY executor.

    Returns ``(state_delta, message)`` on acceptance; raises
    :class:`EconomyRejectionError` with the domain's own message on a veto.
    Never touches game tables directly (the RS02 write boundary).
    """
    from services import mining_workflow
    from utils import db, equipment

    user_id = int(suid)

    if action == "mine":
        result = await mining_workflow.mine(user_id, guild_id)
        delta = await _project_fields(
            ("mining_inventory", "gear_wear", "xp"), suid, guild_id
        )
        return delta, f"mined {result.amount}× {result.found}"

    if action == "descend":
        record_before = await db.get_max_depth(suid, guild_id)
        result = await mining_workflow.descend(user_id, guild_id)
        if not result.moved:
            raise EconomyRejectionError(result.hint or "cannot descend any further")
        descend_delta: dict[str, Any] = {"depth": result.depth}
        if result.depth > record_before:
            descend_delta["record_depth"] = result.depth
        return descend_delta, f"descended to depth {result.depth}"

    if action == "ascend":
        result = await mining_workflow.ascend(user_id, guild_id)
        if not result.moved:
            raise EconomyRejectionError(result.hint or "already at the surface")
        return {"depth": result.depth}, f"ascended to depth {result.depth}"

    if action == "sell":
        result = await mining_workflow.sell(
            user_id, guild_id, params["item"], params["quantity"]
        )
        if not result.ok:
            raise EconomyRejectionError(result.message)
        delta = await _project_fields(("coins", "mining_inventory"), suid, guild_id)
        return delta, result.message

    if action in ("vault_deposit", "vault_withdraw"):
        # Contract params move COINS; superbot's vault is an item store, so
        # the 1:1 mapping is the vault op on the "coins" item — the domain's
        # own verdict (today: a veto, coins never sit in the mining pack)
        # relays as economy_rejection. Decided-and-flagged in the session card.
        op = getattr(mining_workflow, action)
        result = await op(user_id, guild_id, "coins", params["amount"])
        if not result.ok:
            raise EconomyRejectionError(result.message)
        delta = await _project_fields(("mining_inventory", "vault"), suid, guild_id)
        return delta, result.message

    if action == "equip":
        item = params["item"]
        expected_slot = equipment.slot_for(item.strip().lower())
        if expected_slot != params["slot"]:
            # The proposal names a slot; executing into a DIFFERENT slot would
            # betray it. Same domain function the workflow itself uses.
            raise EconomyRejectionError(
                f"**{item}** does not fit the {params['slot']} slot"
            )
        result = await mining_workflow.equip(user_id, guild_id, item)
        if not result.ok:
            raise EconomyRejectionError(result.message)
        delta = await _project_fields(("equipment",), suid, guild_id)
        return delta, result.message

    raise EconomyRejectionError(f"unhandled action {action}")  # unreachable


# --- the handler ----------------------------------------------------------------


async def _remember(
    proposal: dict[str, Any],
    digest: str | None,
    http_status: int,
    response: dict[str, Any],
) -> None:
    """Store the original outcome for replays (``digest=None`` skips — the
    409 key-reuse case must never overwrite the original action's response),
    then purge aged rows opportunistically.
    """
    if digest is None:
        return
    from utils.db import mining_web_actions

    await mining_web_actions.put_web_action(
        proposal["guild_id"],
        proposal["action_id"],
        digest,
        http_status,
        response,
    )
    await mining_web_actions.purge_web_actions()


async def _reject(
    proposal: dict[str, Any],
    digest: str | None,
    http_status: int,
    reason_code: str,
    message: str,
    *,
    headers: dict[str, str] | None = None,
) -> web.Response:
    """A post-auth, attributable rejection: audited, and (except key reuse /
    rate limiting, ``digest=None``) stored for idempotent replay.
    """
    response = _envelope(proposal["action_id"], reason_code, message)
    await _remember(proposal, digest, http_status, response)
    await _audit(proposal, f"rejected:{reason_code}")
    return _json_response(http_status, response, headers=headers)


async def handle_action(request: web.Request) -> web.Response:
    """``POST /relay/mining/action`` — one signed proposal in, one v1
    response envelope out. Every branch answers a schema-conformant envelope.
    """
    secret = shared_secret()
    body = await request.read()
    auth_failure = (
        verify(
            secret,
            request.method,
            request.path,
            request.headers.get(HEADER_TIMESTAMP) or "",
            body,
            request.headers.get(HEADER_SIGNATURE) or "",
        )
        if secret
        # The route only registers when configured; if the secret vanished
        # from the env since, nothing is verifiable — fail closed, pre-auth.
        else "invalid_signature"
    )
    if auth_failure == "invalid_signature":
        return _json_response(
            401,
            _envelope(
                PLACEHOLDER_ACTION_ID,
                "invalid_signature",
                "request signature is missing or wrong",
            ),
        )
    if auth_failure == "stale_timestamp":
        return _json_response(
            401,
            _envelope(
                PLACEHOLDER_ACTION_ID,
                "stale_timestamp",
                "signature timestamp outside the skew window",
            ),
        )

    try:
        proposal = json.loads(body)
    except ValueError:
        return _json_response(
            400,
            _envelope(
                PLACEHOLDER_ACTION_ID, "malformed_request", "body is not valid JSON"
            ),
        )
    schema_failure = classify_proposal(proposal)
    if schema_failure is not None:
        reason_code, message = schema_failure
        status = 400
        return _json_response(
            status, _envelope(_echoable_action_id(proposal), reason_code, message)
        )

    # Schema-valid — attributable from here: everything below is audited.
    from utils.db import mining_web_actions

    digest = hashlib.sha256(body).hexdigest()
    stored = await mining_web_actions.get_web_action(
        proposal["guild_id"], proposal["action_id"]
    )
    if stored is not None:
        if stored["body_digest"] == digest:
            # Idempotent replay: the ORIGINAL response, never re-executed,
            # never re-audited (contract § "Idempotency").
            replay = dict(stored["response"])
            replay["replayed"] = True
            return _json_response(stored["http_status"], replay)
        return await _reject(  # key reuse IS a client anomaly; never stored
            proposal,
            None,
            409,
            "replayed_action",
            "action_id was already used with a different body",
        )

    retry_after = _limiter.check(f"{proposal['suid']}:{proposal['guild_id']}")
    if retry_after is not None:
        # Not stored for idempotency (contract: a retry after the window is
        # a fresh evaluation) — but audited: it is an attributable rejection.
        return await _reject(
            proposal,
            None,
            429,
            "rate_limited",
            "over the per-player action budget",
            headers={"Retry-After": str(retry_after)},
        )

    if proposal["guild_id"] not in allowed_guilds():
        return await _reject(
            proposal,
            digest,
            403,
            "guild_not_allowed",
            "guild is not on the test-guild allowlist "
            "(live cutover is the owner's stage-d flag)",
        )

    from utils.db.games import mining_player_state

    if not await mining_player_state.has_player_state(
        proposal["suid"], int(proposal["guild_id"])
    ):
        return await _reject(
            proposal,
            digest,
            404,
            "actor_not_found",
            "no mining state for that player in this guild",
        )

    try:
        delta, message = await _execute_action(
            proposal["action"],
            proposal["params"],
            proposal["suid"],
            int(proposal["guild_id"]),
        )
    except EconomyRejectionError as veto:
        return await _reject(proposal, digest, 422, "economy_rejection", str(veto))
    except Exception:
        logger.exception(
            "mining_write_api: internal error executing %s (action_id=%s)",
            proposal["action"],
            proposal["action_id"],
        )
        # 500 is retryable with the SAME action_id (contract) — never stored.
        response = _envelope(
            proposal["action_id"], "internal_error", "executor fault; retry"
        )
        await _audit(proposal, "rejected:internal_error")
        return _json_response(500, response)

    response = _envelope(
        proposal["action_id"],
        "ok",
        message,
        result={"state_delta": delta, "snapshot_generated_at": _iso_utc_now()},
    )
    await _remember(proposal, digest, 200, response)
    await _audit(proposal, "accepted:ok")
    return _json_response(200, response)


# --- registration ----------------------------------------------------------------


def register_mining_write_routes(app: web.Application, bot: Any) -> bool:
    """Register ``POST /relay/mining/action`` on *app* — only when configured.

    Returns ``True`` when the route was added (``MINING_WRITE_SHARED_SECRET``
    set), ``False`` when the endpoint stays dormant (every deploy without the
    secret: zero behaviour change). *bot* is unused today but keeps the call
    signature symmetric with ``register_control_routes``.
    """
    if shared_secret() is None:
        logger.info("mining_write_api: dormant (%s unset) — no route added", ENV_SECRET)
        return False
    guilds = sorted(allowed_guilds())
    app.router.add_post(ACTION_PATH, handle_action)
    logger.info(
        "mining_write_api: enabled — POST %s (HMAC v1 write contract); "
        "test-guild allowlist: %s",
        ACTION_PATH,
        guilds if guilds else "EMPTY — every guild answers 403 guild_not_allowed",
    )
    return True


__all__ = [
    "ACTION_PATH",
    "ACTIONS",
    "CONTRACT_VERSION",
    "ENV_GUILD_ALLOWLIST",
    "ENV_SECRET",
    "HEADER_SIGNATURE",
    "HEADER_TIMESTAMP",
    "PLACEHOLDER_ACTION_ID",
    "SKEW_SECONDS",
    "RateLimiter",
    "allowed_guilds",
    "classify_proposal",
    "handle_action",
    "register_mining_write_routes",
    "shared_secret",
    "sign",
    "verify",
]
