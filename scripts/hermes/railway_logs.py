#!/usr/bin/env python3
"""Read SuperBot's production logs from the Railway public GraphQL API (read-only).

This is the production-log source the ``superbot-log-triage`` Hermes skill was
waiting on: it resolves the bot service's latest deployment and prints its recent
logs, so Hermes (or any agent) can answer "why is the bot unhappy?" without the
Railway CLI or the dashboard.

**Read-only by design** — it issues GraphQL *queries* only, never a mutation. It
cannot deploy, restart, scale, or delete anything. (Broader Railway access is a
separate, owner-gated decision — see router Q-0130.)

Auth + config come from the environment (never the repo):

    RAILWAY_TOKEN           project token  -> ``Project-Access-Token`` (preferred,
                            least-privilege; this is the var Railway's own Tokens
                            page tells you to set). RAILWAY_PROJECT_TOKEN is an alias.
    RAILWAY_API_TOKEN       account / workspace token -> ``Authorization: Bearer``
                            (RAILWAY_API_KEY is an alias — the var the owner
                            provisioned in the agent env, 2026-06-14)
    RAILWAY_PROJECT_ID      the project's id
    RAILWAY_SERVICE_ID      the bot service's id ("worker")
    RAILWAY_ENVIRONMENT_ID  optional; scopes the lookup to one environment

Get a token at https://railway.com/account/tokens. The project/service ids are in
the dashboard URL: ``railway.com/project/<PROJECT_ID>/service/<SERVICE_ID>``.
Confirm setup: an account token with ``--whoami``; a project token by reading data
(``-n 20`` here, or ``railway_vars.py list``) — project tokens have no ``me`` identity.

Usage:
    python3.10 scripts/hermes/railway_logs.py [-n LINES] [--json]
    python3.10 scripts/hermes/railway_logs.py --whoami           # test the token
    python3.10 scripts/hermes/railway_logs.py --deployment-id <id>

Stdlib-only (urllib) so CI needs no extra dependency. Added 2026-06-14 under owner
directive Q-0130.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

API_URL = "https://backboard.railway.com/graphql/v2"
#: Non-default User-Agent: Cloudflare bans urllib's ``Python-urllib/X.Y`` default
#: with error 1010, so every Railway API call must present a plain client UA.
USER_AGENT = "superbot-railway-tool/1.0"

#: A GraphQL transport: ``post(query, variables) -> data``. Injected so the
#: query/parse logic is unit-testable without touching the network.
PostFn = Callable[[str, dict[str, Any]], dict[str, Any]]

DEPLOYMENTS_QUERY = """
query deployments($input: DeploymentListInput!) {
  deployments(input: $input, first: 5) {
    edges { node { id status createdAt } }
  }
}
""".strip()

LOGS_QUERY = """
query deploymentLogs($deploymentId: String!, $limit: Int) {
  deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
    timestamp
    message
    severity
  }
}
""".strip()

WHOAMI_QUERY = "query { me { id email } }"

#: Railway deployment statuses that mean "this is the live one worth reading".
ACTIVE_STATUSES = {"SUCCESS", "DEPLOYED"}


class RailwayError(RuntimeError):
    """A config or API error worth printing plainly (no traceback)."""


def build_poster(
    token: str,
    *,
    is_project_token: bool,
    timeout: float = 30.0,
) -> PostFn:
    """Return a ``PostFn`` bound to ``token`` and the right auth header."""
    header_name = "Project-Access-Token" if is_project_token else "Authorization"
    header_value = token if is_project_token else f"Bearer {token}"

    def post(query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        req = urllib.request.Request(API_URL, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        # Cloudflare fronts backboard.railway.com and bans urllib's default
        # ``Python-urllib/X.Y`` User-Agent with error 1010 (TLS/client-signature
        # block) — every call 403s without this, regardless of token. A plain
        # client UA passes. (Discovered by an auth-probe routine, 2026-06-14.)
        req.add_header("User-Agent", USER_AGENT)
        req.add_header(header_name, header_value)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RailwayError(f"Railway API HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RailwayError(
                f"Could not reach Railway API ({API_URL}): {exc.reason}",
            ) from exc
        if body.get("errors"):
            raise RailwayError(
                "Railway API returned errors:\n" + json.dumps(body["errors"], indent=2),
            )
        return body.get("data") or {}

    return post


def latest_deployment(
    post: PostFn,
    *,
    project_id: str,
    service_id: str,
    environment_id: str | None = None,
) -> dict[str, Any]:
    """Return the newest active deployment node (falls back to the newest one)."""
    input_obj: dict[str, Any] = {"projectId": project_id, "serviceId": service_id}
    if environment_id:
        input_obj["environmentId"] = environment_id
    data = post(DEPLOYMENTS_QUERY, {"input": input_obj})
    edges = (data.get("deployments") or {}).get("edges") or []
    nodes = [edge["node"] for edge in edges if edge.get("node")]
    if not nodes:
        raise RailwayError(
            "No deployments found — check RAILWAY_PROJECT_ID / RAILWAY_SERVICE_ID.",
        )
    for node in nodes:
        if node.get("status") in ACTIVE_STATUSES:
            return node
    return nodes[0]


def fetch_logs(post: PostFn, *, deployment_id: str, limit: int) -> list[dict[str, Any]]:
    """Return the raw log entries for one deployment, newest window last."""
    data = post(LOGS_QUERY, {"deploymentId": deployment_id, "limit": limit})
    return list(data.get("deploymentLogs") or [])


def format_logs(logs: list[dict[str, Any]]) -> str:
    """Render log entries as ``<timestamp> [SEVERITY] message`` lines."""
    lines: list[str] = []
    for entry in logs:
        timestamp = entry.get("timestamp") or ""
        severity = (entry.get("severity") or "").upper()
        message = entry.get("message") or ""
        prefix = f"{timestamp} " if timestamp else ""
        sev_tag = f"[{severity}] " if severity else ""
        lines.append(f"{prefix}{sev_tag}{message}")
    return "\n".join(lines)


def _resolve_token() -> tuple[str, bool]:
    """Return ``(token, is_project_token)`` from the environment.

    Mirrors Railway's own convention: ``RAILWAY_TOKEN`` is a project token
    (sent as ``Project-Access-Token``); ``RAILWAY_API_TOKEN`` is an account /
    workspace token (sent as ``Authorization: Bearer``). ``RAILWAY_PROJECT_TOKEN``
    is accepted as an alias for ``RAILWAY_TOKEN``. A project token is
    least-privilege and preferred when both are set.
    """
    project = (
        os.environ.get("RAILWAY_TOKEN", "").strip()
        or os.environ.get("RAILWAY_PROJECT_TOKEN", "").strip()
    )
    # ``RAILWAY_API_KEY`` is the var name the owner provisioned in the agent env
    # (2026-06-14); it holds an account/workspace token, so it aliases
    # RAILWAY_API_TOKEN, not the project-token slot.
    account = (
        os.environ.get("RAILWAY_API_TOKEN", "").strip()
        or os.environ.get("RAILWAY_API_KEY", "").strip()
    )
    if project:
        return project, True
    if account:
        return account, False
    raise RailwayError(
        "No Railway token found. Set RAILWAY_TOKEN (a project token — "
        "least-privilege, and the var Railway's Tokens page tells you to set) or "
        "RAILWAY_API_TOKEN / RAILWAY_API_KEY (account/workspace token). "
        "Get one at https://railway.com/account/tokens.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--lines",
        type=int,
        default=200,
        help="how many log lines (default 200)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print raw log JSON instead of text",
    )
    parser.add_argument(
        "--whoami",
        action="store_true",
        help="verify the token, then exit",
    )
    parser.add_argument(
        "--deployment-id",
        help="read this deployment instead of resolving the latest",
    )
    parser.add_argument("--project-id", help="override RAILWAY_PROJECT_ID")
    parser.add_argument("--service-id", help="override RAILWAY_SERVICE_ID")
    parser.add_argument("--environment-id", help="override RAILWAY_ENVIRONMENT_ID")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        token, is_project_token = _resolve_token()
        post = build_poster(token, is_project_token=is_project_token)

        if args.whoami:
            if is_project_token:
                print(
                    "Project token detected (Project-Access-Token) — it has no "
                    "'me' identity, so verify it by reading data instead:\n"
                    "  python3.10 scripts/hermes/railway_logs.py -n 20\n"
                    "  python3.10 scripts/hermes/railway_vars.py list",
                )
                return 0
            print(json.dumps(post(WHOAMI_QUERY, {}), indent=2))
            return 0

        deployment_id = args.deployment_id
        if not deployment_id:
            project_id = args.project_id or os.environ.get("RAILWAY_PROJECT_ID", "")
            service_id = args.service_id or os.environ.get("RAILWAY_SERVICE_ID", "")
            if not project_id or not service_id:
                raise RailwayError(
                    "Set RAILWAY_PROJECT_ID and RAILWAY_SERVICE_ID (from the "
                    "dashboard URL railway.com/project/<id>/service/<id>), or pass "
                    "--deployment-id. Use --whoami to confirm the token first.",
                )
            environment_id = args.environment_id or os.environ.get(
                "RAILWAY_ENVIRONMENT_ID",
            )
            node = latest_deployment(
                post,
                project_id=project_id,
                service_id=service_id,
                environment_id=environment_id,
            )
            deployment_id = node["id"]
            print(
                f"# deployment {deployment_id} "
                f"(status={node.get('status')}, created={node.get('createdAt')})",
                file=sys.stderr,
            )

        logs = fetch_logs(post, deployment_id=deployment_id, limit=args.lines)
        if args.json:
            print(json.dumps(logs, indent=2))
        else:
            print(format_logs(logs))
        return 0
    except RailwayError as exc:
        print(f"railway_logs: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
