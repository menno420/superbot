"""Phase 2a unit tests — core.resources package wiring."""

from __future__ import annotations

from core import resources
from core.resources.status import ResourceStatus
from core.resources.types import (
    CategoryResource,
    ChannelResource,
    GuildResource,
    ResourceKind,
    RoleResource,
    ThreadResource,
)


def test_public_exports_match_all():
    """Every name in __all__ resolves on the package."""
    for name in resources.__all__:
        assert hasattr(resources, name), f"core.resources missing {name!r}"


def test_re_exported_types_round_trip():
    """The package re-exports the same objects as the submodules."""
    assert resources.ResourceStatus is ResourceStatus
    assert resources.ResourceKind is ResourceKind
    assert resources.GuildResource is GuildResource
    assert resources.ChannelResource is ChannelResource
    assert resources.RoleResource is RoleResource
    assert resources.CategoryResource is CategoryResource
    assert resources.ThreadResource is ThreadResource


def test_submodules_re_exported():
    """Submodules are reachable both as attributes and via direct import."""
    from core.resources import (
        channel_service,
        discovery,
        mutation,
        role_service,
        status,
        types,
    )

    assert resources.channel_service is channel_service
    assert resources.discovery is discovery
    assert resources.mutation is mutation
    assert resources.role_service is role_service
    assert resources.status is status
    assert resources.types is types


def test_diagnostics_provider_registered():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("resources")
    assert snap["package"] == "core.resources"
    assert "channel" in snap["kinds"]
    assert "role" in snap["kinds"]
    assert "category" in snap["kinds"]
    assert "thread" in snap["kinds"]
    assert "discovery" in snap["submodules"]
    assert "channel_service" in snap["submodules"]
    assert "role_service" in snap["submodules"]
    assert "mutation" in snap["submodules"]


def test_legacy_helpers_still_delegate():
    """Phase 0's _resource_helpers shim must still resolve to the new code."""
    from views.selectors import _resource_helpers

    assert _resource_helpers._build_channel_options is not None
    assert _resource_helpers._find_role_normalized is not None
