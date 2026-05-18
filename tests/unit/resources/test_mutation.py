"""Phase 2a unit tests — ResourceMutationPipeline shell contract."""

from __future__ import annotations

import pytest

from core.resources.mutation import (
    ResourceMutationPipeline,
    ResourceProvisioningError,
    UnauthorizedResourceProvisioningError,
)
from core.resources.types import ResourceKind


def test_validate_inputs_rejects_empty_payload():
    pipeline = ResourceMutationPipeline()
    with pytest.raises(ResourceProvisioningError, match="empty or non-dict"):
        pipeline._validate_inputs(ResourceKind.CHANNEL, {})


def test_validate_inputs_rejects_non_dict_payload():
    pipeline = ResourceMutationPipeline()
    with pytest.raises(ResourceProvisioningError, match="empty or non-dict"):
        pipeline._validate_inputs(ResourceKind.CHANNEL, [])  # type: ignore[arg-type]


def test_validate_inputs_rejects_invalid_kind():
    pipeline = ResourceMutationPipeline()
    with pytest.raises(ResourceProvisioningError, match="unexpected resource kind"):
        pipeline._validate_inputs(
            "channel",  # type: ignore[arg-type]
            {"name": "x"},
        )


def test_validate_inputs_accepts_well_formed():
    pipeline = ResourceMutationPipeline()
    # No exception
    pipeline._validate_inputs(ResourceKind.CHANNEL, {"name": "test"})


def test_validate_authority_rejects_none_actor():
    pipeline = ResourceMutationPipeline()
    with pytest.raises(
        UnauthorizedResourceProvisioningError,
        match="authenticated actor",
    ):
        pipeline._validate_authority(None)


def test_validate_authority_accepts_non_none():
    pipeline = ResourceMutationPipeline()
    # No exception
    pipeline._validate_authority(object())


@pytest.mark.asyncio
async def test_provision_channel_raises_not_implemented():
    pipeline = ResourceMutationPipeline()
    with pytest.raises(NotImplementedError, match="Phase 7.5"):
        await pipeline.provision_channel(object(), {"name": "x"}, object())


@pytest.mark.asyncio
async def test_provision_role_raises_not_implemented():
    pipeline = ResourceMutationPipeline()
    with pytest.raises(NotImplementedError, match="Phase 7.5"):
        await pipeline.provision_role(object(), {"name": "x"}, object())


@pytest.mark.asyncio
async def test_delete_resource_raises_not_implemented():
    pipeline = ResourceMutationPipeline()
    with pytest.raises(NotImplementedError, match="Phase 7.5"):
        await pipeline.delete_resource(
            object(),
            ResourceKind.CHANNEL,
            42,
            object(),
        )


def test_pipeline_is_stateless_per_instance():
    """Instances do not retain state; tests should be able to create
    fresh ones freely."""
    a = ResourceMutationPipeline()
    b = ResourceMutationPipeline()
    assert a is not b
    # Both have the same public methods
    assert hasattr(a, "provision_channel")
    assert hasattr(b, "provision_channel")
