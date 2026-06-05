"""Shared lifecycle-mutation primitives (server-management PR3).

The reusable request / preview / result / reversibility / audit contract that
coordinated domain lifecycle services (channels, roles) build on — the same
shape :class:`services.resource_provisioning.ResourceProvisioningPipeline`
already uses for create/reuse, generalised for rename / move / delete /
overwrite / reorder operations that provisioning does not own.

See :mod:`services.lifecycle.contracts` for the types.  The first consumer is
:class:`services.channel_lifecycle_service.ChannelLifecycleService`.
"""

from __future__ import annotations

from services.lifecycle.contracts import (
    BLOCKED,
    COMPENSATABLE,
    DECLINED,
    DISCORD_FAILED,
    IRREVERSIBLE,
    PARTIAL,
    REVERSIBLE,
    SUCCESS,
    LifecyclePreview,
    LifecycleResult,
    StepResult,
    emit_lifecycle_audit,
    now_utc,
)

__all__ = [
    "BLOCKED",
    "COMPENSATABLE",
    "DECLINED",
    "DISCORD_FAILED",
    "IRREVERSIBLE",
    "PARTIAL",
    "REVERSIBLE",
    "SUCCESS",
    "LifecyclePreview",
    "LifecycleResult",
    "StepResult",
    "emit_lifecycle_audit",
    "now_utc",
]
