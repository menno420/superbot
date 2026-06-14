#!/usr/bin/env python3
"""Read and edit SuperBot's Railway service variables (env vars) — read + WRITE.

Companion to ``railway_logs.py``. It lets an agent verify the bot's production
environment variables and change them quickly, via the Railway public GraphQL API.
Unlike the logs reader, this tool can **mutate** (set / unset), so it needs a
**write-capable** token.

    list                 list variable names (values masked)
    list --reveal        list names + full values  (PRINTS SECRETS to stdout)
    get NAME             print one variable's value (to verify it)
    set NAME [VALUE]     create/update a variable (VALUE from arg, or stdin if omitted)
    unset NAME           delete a variable

Config comes from the environment (never the repo):

    RAILWAY_TOKEN           a **write-capable** project token (preferred; the var
                            Railway's Tokens page tells you to set). RAILWAY_API_TOKEN
                            works too (account token). RAILWAY_PROJECT_TOKEN is an alias.
    RAILWAY_PROJECT_ID      the project's id
    RAILWAY_ENVIRONMENT_ID  the environment's id (required — variables are per-environment)
    RAILWAY_SERVICE_ID      the bot service's id

Guardrails: read subcommands (``list`` / ``get``) never mutate; ``list`` masks
values unless ``--reveal``; writes print an audit line to stderr and never echo the
token; ``set`` can take the value on stdin so secrets stay out of argv. Endpoint and
transport are shared with the read-only logs reader.

Provenance: owner directive Q-0130 (env-var read+write grant, 2026-06-14). The owner
explicitly authorised write access to service variables, accepting the risk.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

# Reuse the logs reader's GraphQL transport + error type (same dir on sys.path when
# run as a script). resolve_token is re-implemented here with a write-aware message.
from railway_logs import RailwayError, build_poster

VARIABLES_QUERY = """
query variables($projectId: String!, $environmentId: String!, $serviceId: String) {
  variables(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId)
}
""".strip()

UPSERT_MUTATION = """
mutation variableUpsert($input: VariableUpsertInput!) {
  variableUpsert(input: $input)
}
""".strip()

DELETE_MUTATION = """
mutation variableDelete($input: VariableDeleteInput!) {
  variableDelete(input: $input)
}
""".strip()


def resolve_token() -> tuple[str, bool]:
    """Return ``(token, is_project_token)`` for a **write-capable** token.

    ``RAILWAY_TOKEN`` = project token (Project-Access-Token); ``RAILWAY_API_TOKEN``
    = account/workspace token (Bearer); ``RAILWAY_PROJECT_TOKEN`` is an alias for
    ``RAILWAY_TOKEN``. The token must have write scope to set/unset variables.
    """
    project = (
        os.environ.get("RAILWAY_TOKEN", "").strip()
        or os.environ.get("RAILWAY_PROJECT_TOKEN", "").strip()
    )
    account = os.environ.get("RAILWAY_API_TOKEN", "").strip()
    if project:
        return project, True
    if account:
        return account, False
    raise RailwayError(
        "No Railway token found. Editing variables needs a WRITE-capable token in "
        "RAILWAY_TOKEN (project token) or RAILWAY_API_TOKEN (account token). "
        "Get one at https://railway.com/account/tokens.",
    )


def resolve_ids(args: argparse.Namespace) -> tuple[str, str, str]:
    """Return ``(project_id, environment_id, service_id)`` from args/env."""
    project = args.project_id or os.environ.get("RAILWAY_PROJECT_ID", "")
    environment = args.environment_id or os.environ.get("RAILWAY_ENVIRONMENT_ID", "")
    service = args.service_id or os.environ.get("RAILWAY_SERVICE_ID", "")
    missing = [
        name
        for name, value in (
            ("RAILWAY_PROJECT_ID", project),
            ("RAILWAY_ENVIRONMENT_ID", environment),
            ("RAILWAY_SERVICE_ID", service),
        )
        if not value
    ]
    if missing:
        raise RailwayError(
            "Missing required id(s): "
            + ", ".join(missing)
            + ". Variables are scoped per environment, so all three are required. "
            "Get them from the dashboard URL "
            "railway.com/project/<PROJECT_ID>/service/<SERVICE_ID> and the "
            "environment selector.",
        )
    return project, environment, service


def get_variables(
    post: Any,
    *,
    project_id: str,
    environment_id: str,
    service_id: str,
) -> dict[str, str]:
    """Return ``{name: value}`` for the service's variables."""
    data = post(
        VARIABLES_QUERY,
        {
            "projectId": project_id,
            "environmentId": environment_id,
            "serviceId": service_id,
        },
    )
    return dict(data.get("variables") or {})


def upsert_variable(
    post: Any,
    *,
    project_id: str,
    environment_id: str,
    service_id: str,
    name: str,
    value: str,
    skip_deploys: bool = False,
) -> None:
    """Create or update one variable.

    By default Railway redeploys the service so the change takes effect; pass
    ``skip_deploys=True`` to stage the value without triggering a deploy.
    """
    variable_input: dict[str, Any] = {
        "projectId": project_id,
        "environmentId": environment_id,
        "serviceId": service_id,
        "name": name,
        "value": value,
    }
    if skip_deploys:
        variable_input["skipDeploys"] = True
    post(UPSERT_MUTATION, {"input": variable_input})


def delete_variable(
    post: Any,
    *,
    project_id: str,
    environment_id: str,
    service_id: str,
    name: str,
) -> None:
    """Delete one variable."""
    post(
        DELETE_MUTATION,
        {
            "input": {
                "projectId": project_id,
                "environmentId": environment_id,
                "serviceId": service_id,
                "name": name,
            },
        },
    )


def mask(value: str) -> str:
    """Mask a secret for display: keep a hint, hide the body."""
    if len(value) <= 4:
        return f"**** ({len(value)} chars)"
    return f"{value[:2]}…{value[-2:]} ({len(value)} chars)"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", help="override RAILWAY_PROJECT_ID")
    parser.add_argument("--environment-id", help="override RAILWAY_ENVIRONMENT_ID")
    parser.add_argument("--service-id", help="override RAILWAY_SERVICE_ID")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="list variable names (values masked)")
    p_list.add_argument(
        "--reveal",
        action="store_true",
        help="show full values (prints secrets)",
    )
    p_list.add_argument("--json", action="store_true", help="print raw JSON")

    p_get = sub.add_parser("get", help="print one variable's value")
    p_get.add_argument("name")

    p_set = sub.add_parser("set", help="create/update a variable")
    p_set.add_argument("name")
    p_set.add_argument(
        "value",
        nargs="?",
        help="value (omit to read from stdin — safer for secrets)",
    )
    p_set.add_argument(
        "--no-deploy",
        action="store_true",
        help="stage the change without triggering a Railway redeploy",
    )

    p_unset = sub.add_parser("unset", help="delete a variable")
    p_unset.add_argument("name")

    return parser


def _run(args: argparse.Namespace, post: Any) -> int:
    project_id, environment_id, service_id = resolve_ids(args)
    ids = {
        "project_id": project_id,
        "environment_id": environment_id,
        "service_id": service_id,
    }

    if args.cmd == "list":
        variables = get_variables(post, **ids)
        if args.json:
            print(json.dumps(variables, indent=2, sort_keys=True))
        else:
            for name in sorted(variables):
                shown = variables[name] if args.reveal else mask(variables[name])
                print(f"{name}={shown}")
        return 0

    if args.cmd == "get":
        variables = get_variables(post, **ids)
        if args.name not in variables:
            raise RailwayError(f"No such variable: {args.name}")
        print(variables[args.name])
        return 0

    if args.cmd == "set":
        value = args.value
        if value is None:
            value = sys.stdin.read().rstrip("\n")
        upsert_variable(
            post,
            name=args.name,
            value=value,
            skip_deploys=args.no_deploy,
            **ids,
        )
        effect = "staged, no redeploy" if args.no_deploy else "Railway will redeploy"
        print(
            f"railway_vars: SET {args.name} on service {service_id} "
            f"env {environment_id} (value: {len(value)} chars; {effect})",
            file=sys.stderr,
        )
        return 0

    if args.cmd == "unset":
        delete_variable(post, name=args.name, **ids)
        print(
            f"railway_vars: UNSET {args.name} on service {service_id} "
            f"env {environment_id}",
            file=sys.stderr,
        )
        return 0

    return 1  # unreachable: subparser is required


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        token, is_project_token = resolve_token()
        post = build_poster(token, is_project_token=is_project_token)
        return _run(args, post)
    except RailwayError as exc:
        print(f"railway_vars: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
