from datetime import datetime, timedelta

import pytest

from sidas.core import (
    AssetMetaData,
    AssetStatus,
)


def test_default_initialization():
    """Test that a new MetaBase instance has the expected default values."""
    before = datetime.now()
    meta = AssetMetaData()
    after = datetime.now()

    assert meta.status == AssetStatus.INITIALIZING

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.materializing_started_at is None
    assert meta.materializing_stopped_at is None

    assert before <= meta.updated_at <= after
    assert before <= meta.initializing_started_at <= after


def test_update_status_initialized():
    """Test updating status to INITIALIZED."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.INITIALIZED)

    assert meta.status == AssetStatus.INITIALIZED

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is not None
    assert meta.materializing_started_at is None
    assert meta.materializing_stopped_at is None

    assert meta.initializing_started_at <= meta.initializing_stopped_at


def test_update_status_materializing():
    """Test updating status to MATERIALIZING."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.MATERIALIZING)

    assert meta.status == AssetStatus.MATERIALIZING

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.materializing_started_at is not None
    assert meta.materializing_stopped_at is None

    assert meta.initializing_started_at <= meta.materializing_started_at


def test_update_status_materializing_failed():
    """Test updating status to MATERIALIZING_FAILED."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.MATERIALIZING_FAILED)

    assert meta.status == AssetStatus.MATERIALIZING_FAILED

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.materializing_started_at is None
    assert meta.materializing_stopped_at is not None

    assert meta.initializing_started_at <= meta.materializing_stopped_at


def test_update_status_materialized():
    """Test updating status to MATERIALIZED."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.MATERIALIZED)

    assert meta.status == AssetStatus.MATERIALIZED

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.materializing_started_at is None
    assert meta.materializing_stopped_at is not None

    assert meta.initializing_started_at <= meta.materializing_stopped_at


def test_status_chaining():
    """Test the full lifecycle of status updates with method chaining."""
    meta = AssetMetaData()

    # Test method chaining
    result = (
        meta.update_status(AssetStatus.INITIALIZED)
        .update_status(AssetStatus.MATERIALIZING)
        .update_status(AssetStatus.MATERIALIZED)
    )

    assert result is meta  # Confirm method chaining returns self
    assert meta.status == AssetStatus.MATERIALIZED

    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is not None
    assert meta.materializing_started_at is not None
    assert meta.materializing_stopped_at is not None

    assert meta.initializing_started_at <= meta.initializing_stopped_at
    assert meta.initializing_started_at <= meta.materializing_started_at
    assert meta.materializing_started_at <= meta.materializing_stopped_at


def test_blocked():
    """Test the in_progress method."""
    meta = AssetMetaData()

    meta.update_status(AssetStatus.INITIALIZING)
    assert meta.blocked()

    meta.update_status(AssetStatus.INITIALIZED)
    assert not meta.blocked()

    meta.update_status(AssetStatus.INITIALIZING_FAILED)
    assert meta.blocked()

    meta.update_status(AssetStatus.MATERIALIZING)
    assert meta.blocked()

    meta.update_status(AssetStatus.MATERIALIZING_FAILED)
    assert not meta.blocked()

    meta.update_status(AssetStatus.MATERIALIZED)
    assert not meta.blocked()


def test_has_error():
    """Test the has_error method."""
    meta = AssetMetaData()

    meta.update_status(AssetStatus.INITIALIZING)
    assert not meta.has_error()

    meta.update_status(AssetStatus.INITIALIZED)
    assert not meta.has_error()

    meta.update_status(AssetStatus.INITIALIZING_FAILED)
    assert not meta.has_error()

    meta.update_status(AssetStatus.MATERIALIZING)
    assert not meta.has_error()

    meta.update_status(AssetStatus.MATERIALIZING_FAILED)
    assert meta.has_error()

    meta.update_status(AssetStatus.MATERIALIZED)
    assert not meta.has_error()


def test_json_serialization():
    """Test serialization to and from JSON."""
    # Create a MetaBase with defined timestamps to avoid timing issues
    now = datetime.now()
    original = AssetMetaData(
        status=AssetStatus.MATERIALIZED,
        initializing_started_at=now - timedelta(minutes=10),
        initializing_stopped_at=now - timedelta(minutes=9),
        materializing_started_at=now - timedelta(minutes=3),
        materializing_stopped_at=now - timedelta(minutes=1),
        updated_at=now,
    )

    # Convert to JSON
    json_data = original.to_json()

    # Create a new instance from the JSON
    recreated = AssetMetaData.from_json(json_data)

    # Verify all fields match
    assert recreated.status == original.status
    assert recreated.initializing_started_at == original.initializing_started_at
    assert recreated.initializing_stopped_at == original.initializing_stopped_at
    assert recreated.materializing_started_at == original.materializing_started_at
    assert recreated.materializing_stopped_at == original.materializing_stopped_at
    assert recreated.updated_at == original.updated_at


def test_json_validation_error():
    """Test that invalid JSON data raises a validation error."""
    with pytest.raises(Exception):  # Pydantic will raise a validation error
        AssetMetaData.from_json('{"status": "INVALID_STATUS"}')
