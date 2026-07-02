"""The capture boundary: a fake HTTPClient + webhook adapter.

Everything the bot would send to Discord crosses one of two seams in
discord.py 2.7.1:

* ``ConnectionState.http`` (an ``HTTPClient``) — channel sends/edits/deletes,
  reactions, member/guild REST fallbacks, application-command sync.
* ``discord.webhook.async_.async_context`` (an ``AsyncWebhookAdapter``
  ContextVar) — interaction responses and followups.

This module fakes both. Outbound calls are recorded as :class:`OutboundCall`
observations (the golden's raw material) and answered with synthetic payloads
so the real state machine keeps working (real ``Message`` objects come back,
views register in the real ``ViewStore``, followups resolve).

Unknown methods fail LOUD (``UnexpectedHTTPCallError``): a golden must never
silently drop an outbound effect. Extend the fake when the surface grows.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "FakeHTTP",
    "FakeWebhookAdapter",
    "OutboundCall",
    "UnexpectedHTTPCallError",
]


class UnexpectedHTTPCallError(RuntimeError):
    """An outbound Discord call the fake does not model — extend, don't drop."""


@dataclass
class OutboundCall:
    """One captured outbound effect (what the bot tried to do to Discord)."""

    method: str
    args: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] | None = None
    #: for sends: the synthetic message id we answered with (click targeting)
    response_id: int | None = None


def _params_payload(params: Any) -> dict[str, Any]:
    """Extract the JSON payload from a MultipartParameters (or dict)."""
    if params is None:
        return {}
    payload = getattr(params, "payload", None)
    if payload is None and isinstance(params, dict):
        payload = params
    out = dict(payload or {})
    files = getattr(params, "files", None)
    if files:
        out["_files"] = [getattr(f, "filename", "?") for f in files]
    return out


class _IDSource:
    """Deterministic snowflake-ish id allocator shared by the driver."""

    def __init__(self, start: int = 10_000) -> None:
        self._next = start

    def allocate(self) -> int:
        self._next += 1
        return self._next


class FakeHTTP:
    """Duck-typed stand-in for ``discord.http.HTTPClient``.

    Only the surface the bot actually exercises is implemented; everything
    else raises :class:`UnexpectedHTTPCallError` via ``__getattr__`` so a new
    outbound effect is a loud capture gap, never a silent one.
    """

    def __init__(
        self,
        *,
        ids: _IDSource,
        clock: Any,
        bot_user_payload: dict[str, Any],
    ) -> None:
        self.calls: list[OutboundCall] = []
        #: capture-integrity: attribute/method gaps hit during a drive —
        #: the runner FAILS a case that touched one (the golden would
        #: otherwise record harness-artifact behavior as bot behavior).
        self.gaps: list[str] = []
        self._ids = ids
        self._clock = clock
        self._bot_user = bot_user_payload
        # discord.Interaction.__init__ reads the name-mangled session attr;
        # interaction defer/response paths read proxy settings directly.
        self._HTTPClient__session = object()
        self.proxy = None
        self.proxy_auth = None
        self.token: str | None = "parity-fake-token"

    # ------------------------------------------------------------- recording

    def _record(
        self,
        method: str,
        args: dict[str, Any],
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.calls.append(OutboundCall(method=method, args=args, payload=payload))

    def _message_response(
        self,
        channel_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Synthesize the message object Discord would return for a send."""
        return {
            "id": str(self._ids.allocate()),
            "channel_id": str(channel_id),
            "author": dict(self._bot_user),
            "content": payload.get("content") or "",
            "timestamp": self._clock.isoformat(),
            "edited_timestamp": None,
            "tts": bool(payload.get("tts", False)),
            "mention_everyone": False,
            "mentions": [],
            "mention_roles": [],
            "attachments": [],
            "embeds": payload.get("embeds") or [],
            "components": payload.get("components") or [],
            "pinned": False,
            "type": 0,
        }

    # --------------------------------------------------------- channel sends

    async def send_message(
        self,
        channel_id: int,
        *,
        params: Any,
    ) -> dict[str, Any]:
        payload = _params_payload(params)
        response = self._message_response(int(channel_id), payload)
        self.calls.append(
            OutboundCall(
                method="send_message",
                args={"channel_id": int(channel_id)},
                payload=payload,
                response_id=int(response["id"]),
            ),
        )
        return response

    async def edit_message(
        self,
        channel_id: int,
        message_id: int,
        *,
        params: Any,
    ) -> dict[str, Any]:
        payload = _params_payload(params)
        self._record(
            "edit_message",
            {"channel_id": int(channel_id), "message_id": int(message_id)},
            payload,
        )
        response = self._message_response(int(channel_id), payload)
        response["id"] = str(message_id)
        return response

    async def delete_message(
        self,
        channel_id: int,
        message_id: int,
        *,
        reason: str | None = None,
    ) -> None:
        self._record(
            "delete_message",
            {
                "channel_id": int(channel_id),
                "message_id": int(message_id),
                "reason": reason,
            },
        )

    async def delete_messages(
        self,
        channel_id: int,
        message_ids: Any,
        *,
        reason: str | None = None,
    ) -> None:
        self._record(
            "bulk_delete_messages",
            {
                "channel_id": int(channel_id),
                "message_ids": [int(m) for m in message_ids],
                "reason": reason,
            },
        )

    async def add_reaction(self, channel_id: int, message_id: int, emoji: str) -> None:
        self._record(
            "add_reaction",
            {
                "channel_id": int(channel_id),
                "message_id": int(message_id),
                "emoji": emoji,
            },
        )

    # ------------------------------------------------------------ moderation

    async def kick(
        self,
        user_id: int,
        guild_id: int,
        reason: str | None = None,
    ) -> None:
        self._record(
            "kick",
            {"guild_id": int(guild_id), "user_id": int(user_id), "reason": reason},
        )

    async def ban(
        self,
        user_id: int,
        guild_id: int,
        delete_message_seconds: int = 86400,
        reason: str | None = None,
    ) -> None:
        self._record(
            "ban",
            {
                "guild_id": int(guild_id),
                "user_id": int(user_id),
                "delete_message_seconds": delete_message_seconds,
                "reason": reason,
            },
        )

    async def unban(
        self,
        user_id: int,
        guild_id: int,
        *,
        reason: str | None = None,
    ) -> None:
        self._record(
            "unban",
            {"guild_id": int(guild_id), "user_id": int(user_id), "reason": reason},
        )

    async def edit_member(
        self,
        guild_id: int,
        user_id: int,
        *,
        reason: str | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        self._record(
            "edit_member",
            {
                "guild_id": int(guild_id),
                "user_id": int(user_id),
                "reason": reason,
            },
            dict(fields),
        )
        return {}

    async def add_role(
        self,
        guild_id: int,
        user_id: int,
        role_id: int,
        *,
        reason: str | None = None,
    ) -> None:
        self._record(
            "add_role",
            {
                "guild_id": int(guild_id),
                "user_id": int(user_id),
                "role_id": int(role_id),
                "reason": reason,
            },
        )

    async def remove_role(
        self,
        guild_id: int,
        user_id: int,
        role_id: int,
        *,
        reason: str | None = None,
    ) -> None:
        self._record(
            "remove_role",
            {
                "guild_id": int(guild_id),
                "user_id": int(user_id),
                "role_id": int(role_id),
                "reason": reason,
            },
        )

    # ------------------------------------------------- guild resource mgmt

    async def create_channel(
        self,
        guild_id: int,
        channel_type: int,
        *,
        reason: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        cid = self._ids.allocate()
        self._record(
            "create_channel",
            {"guild_id": int(guild_id), "type": int(channel_type), "reason": reason},
            dict(options),
        )
        return {
            "id": str(cid),
            "guild_id": str(guild_id),
            "type": int(channel_type),
            "name": options.get("name") or f"channel-{cid}",
            "position": options.get("position", 0),
            "permission_overwrites": [],
            "nsfw": False,
            "parent_id": options.get("parent_id"),
            "topic": options.get("topic"),
            "rate_limit_per_user": 0,
        }

    async def create_role(
        self,
        guild_id: int,
        *,
        reason: str | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        rid = self._ids.allocate()
        self._record(
            "create_role",
            {"guild_id": int(guild_id), "reason": reason},
            dict(fields),
        )
        return {
            "id": str(rid),
            "name": fields.get("name") or f"role-{rid}",
            "color": fields.get("color", 0),
            "hoist": bool(fields.get("hoist", False)),
            "position": 1,
            "permissions": str(fields.get("permissions", "0")),
            "managed": False,
            "mentionable": bool(fields.get("mentionable", False)),
        }

    async def delete_channel(
        self,
        channel_id: int,
        *,
        reason: str | None = None,
    ) -> None:
        self._record(
            "delete_channel",
            {"channel_id": int(channel_id), "reason": reason},
        )

    async def edit_channel(
        self,
        channel_id: int,
        *,
        reason: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        self._record(
            "edit_channel",
            {"channel_id": int(channel_id), "reason": reason},
            dict(options),
        )
        return {
            "id": str(channel_id),
            "type": 0,
            "name": options.get("name", "channel"),
            "position": options.get("position", 0),
            "permission_overwrites": [],
            "nsfw": bool(options.get("nsfw", False)),
            "parent_id": options.get("parent_id"),
            "topic": options.get("topic"),
            "rate_limit_per_user": options.get("rate_limit_per_user", 0),
        }

    async def edit_channel_permissions(
        self,
        channel_id: int,
        target_id: int,
        allow_value: int,
        deny_value: int,
        perm_type: int,
        *,
        reason: str | None = None,
    ) -> None:
        self._record(
            "edit_channel_permissions",
            {
                "channel_id": int(channel_id),
                "target_id": int(target_id),
                "allow": str(allow_value),
                "deny": str(deny_value),
                "type": int(perm_type),
                "reason": reason,
            },
        )

    async def create_invite(
        self,
        channel_id: int,
        *,
        reason: str | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        self._record(
            "create_invite",
            {"channel_id": int(channel_id), "reason": reason},
            dict(fields),
        )
        return {
            "code": "parityinvite",
            "channel": {"id": str(channel_id), "type": 0, "name": "channel"},
            "guild": None,
            "max_age": fields.get("max_age", 0),
            "max_uses": fields.get("max_uses", 0),
            "temporary": False,
            "uses": 0,
        }

    # ------------------------------------------------------------- fetches

    async def get_message(self, channel_id: int, message_id: int) -> dict[str, Any]:
        # `fetch_message` fallback — answer with an empty synthetic message so
        # listener paths that re-fetch (e.g. react-to-thank) keep working.
        self._record(
            "get_message",
            {"channel_id": int(channel_id), "message_id": int(message_id)},
        )
        response = self._message_response(int(channel_id), {})
        response["id"] = str(message_id)
        return response

    async def logs_from(
        self,
        channel_id: int,
        limit: int,
        before: int | None = None,
        after: int | None = None,
        around: int | None = None,
    ) -> list[dict[str, Any]]:
        self._record("logs_from", {"channel_id": int(channel_id), "limit": limit})
        return []

    async def get_user(self, user_id: int) -> dict[str, Any]:
        # UserConverter fallback for ids outside the guild cache
        self._record("get_user", {"user_id": int(user_id)})
        return {
            "id": str(user_id),
            "username": f"user{user_id % 1000}",
            "discriminator": "0000",
            "global_name": f"user{user_id % 1000}",
            "avatar": None,
            "bot": False,
        }

    async def get_from_cdn(self, url: str) -> bytes:
        # avatar/asset fetches (rank cards etc.) — deterministic 1×1 PNG
        self._record("get_from_cdn", {"url": "<cdn>"})
        return bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000d49444154789c626001000000ffff03000006000557bfabd4000000004945"
            "4e44ae426082",
        )

    # ------------------------------------------- application command sync

    async def get_global_commands(self, application_id: int) -> list[dict[str, Any]]:
        self._record("get_global_commands", {})
        return []

    async def get_guild_commands(
        self,
        application_id: int,
        guild_id: int,
    ) -> list[dict[str, Any]]:
        self._record("get_guild_commands", {"guild_id": int(guild_id)})
        return []

    async def bulk_upsert_guild_commands(
        self,
        application_id: int,
        guild_id: int,
        payload: Any,
    ) -> list[dict[str, Any]]:
        self._record("bulk_upsert_guild_commands", {"guild_id": int(guild_id)})
        return []

    async def bulk_upsert_global_commands(
        self,
        application_id: int,
        payload: Any,
    ) -> list[dict[str, Any]]:
        self._record("bulk_upsert_global_commands", {})
        return []

    # ------------------------------------------------------------ lifecycle

    async def close(self) -> None:  # pragma: no cover - harness shutdown only
        return None

    # ------------------------------------------------------------- unknown

    def __getattr__(self, name: str) -> Any:
        self.gaps.append(f"HTTPClient.{name}")
        raise UnexpectedHTTPCallError(
            f"FakeHTTP has no handler for HTTPClient.{name} — a real outbound "
            "effect would be dropped. Add a recording handler to "
            "parity/harness/fake_http.py.",
        )


class FakeWebhookAdapter:
    """Stand-in for the async webhook adapter (interaction responses)."""

    def __init__(self, http: FakeHTTP) -> None:
        self._http = http

    # NOTE: signatures mirror discord.webhook.async_.AsyncWebhookAdapter —
    # positional/keyword shapes matter because discord.py calls these
    # internally.

    def create_interaction_response(
        self,
        interaction_id: int,
        token: str,
        *,
        session: Any,
        proxy: Any = None,
        proxy_auth: Any = None,
        params: Any,
    ) -> Any:
        payload = _params_payload(params)
        self._http._record(
            "interaction_response",
            {"interaction_id": int(interaction_id)},
            payload,
        )

        async def _done() -> dict[str, Any]:
            # InteractionCallbackResponse._update requires interaction.id.
            return {"interaction": {"id": str(interaction_id)}}

        return _done()

    def execute_webhook(
        self,
        webhook_id: int,
        token: str,
        *,
        session: Any,
        proxy: Any = None,
        proxy_auth: Any = None,
        payload: dict[str, Any] | None = None,
        multipart: list[dict[str, Any]] | None = None,
        files: Any = None,
        thread_id: int | None = None,
        wait: bool = False,
        with_components: bool = False,
    ) -> Any:
        body = dict(payload or {})
        if files:
            body["_files"] = [getattr(f, "filename", "?") for f in files]
        self._http._record("followup_send", {"webhook_id": int(webhook_id)}, body)

        async def _done() -> dict[str, Any]:
            return self._http._message_response(0, body)

        return _done()

    def get_original_interaction_response(
        self,
        application_id: int,
        token: str,
        *,
        session: Any,
        proxy: Any = None,
        proxy_auth: Any = None,
    ) -> Any:
        self._http._record("get_original_response", {})

        async def _done() -> dict[str, Any]:
            return self._http._message_response(0, {})

        return _done()

    def edit_original_interaction_response(
        self,
        application_id: int,
        token: str,
        *,
        session: Any,
        proxy: Any = None,
        proxy_auth: Any = None,
        payload: dict[str, Any] | None = None,
        multipart: list[dict[str, Any]] | None = None,
        files: Any = None,
    ) -> Any:
        body = dict(payload or {})
        self._http._record("edit_original_response", {}, body)

        async def _done() -> dict[str, Any]:
            return self._http._message_response(0, body)

        return _done()

    def edit_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: Any,
        proxy: Any = None,
        proxy_auth: Any = None,
        payload: dict[str, Any] | None = None,
        multipart: list[dict[str, Any]] | None = None,
        files: Any = None,
        thread_id: int | None = None,
        with_components: bool = False,
    ) -> Any:
        body = dict(payload or {})
        self._http._record(
            "edit_followup",
            {"webhook_id": int(webhook_id), "message_id": int(message_id)},
            body,
        )

        async def _done() -> dict[str, Any]:
            return self._http._message_response(0, body)

        return _done()

    def delete_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: Any,
        proxy: Any = None,
        proxy_auth: Any = None,
        thread_id: int | None = None,
    ) -> Any:
        self._http._record(
            "delete_followup",
            {"webhook_id": int(webhook_id), "message_id": int(message_id)},
        )

        async def _done() -> None:
            return None

        return _done()

    def __getattr__(self, name: str) -> Any:
        self._http.gaps.append(f"WebhookAdapter.{name}")
        raise UnexpectedHTTPCallError(
            f"FakeWebhookAdapter has no handler for {name} — extend "
            "parity/harness/fake_http.py.",
        )


async def drain_dispatch_tasks(
    *,
    max_rounds: int = 120,
    exclude: set[asyncio.Task[Any]] | None = None,
) -> None:
    """Let fire-and-forget dispatch tasks (listeners, error handlers) finish.

    discord.py dispatches events as unawaited tasks; a deterministic capture
    must wait for them. A task set that stops shrinking is either a flow
    parked on ``bot.wait_for(...)`` user input (bail: the capture honestly
    shows the prompt it stopped at) or a REAL bounded ``asyncio.sleep`` in
    mid-flow (fishing bite windows are 3–6s) — so the stall patience must
    outlast legitimate sleeps or their completions land in a later case
    nondeterministically (observed: sweep.fish). ~7s of stability, then bail.
    """
    current = asyncio.current_task()
    excluded = exclude or set()
    stable_rounds = 0
    previous: set[asyncio.Task[Any]] = set()
    for _ in range(max_rounds):
        pending = {
            t
            for t in asyncio.all_tasks()
            if t is not current and not t.done() and t not in excluded
        }
        if not pending:
            return
        if pending == previous:
            stable_rounds += 1
            if stable_rounds >= 45:  # ≈7s at 0.15s waits
                return
        else:
            stable_rounds = 0
        previous = pending
        await asyncio.wait(pending, timeout=0.15)
