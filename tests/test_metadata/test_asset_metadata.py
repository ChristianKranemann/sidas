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
    assert meta.transforming_kickoff_at is None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is None

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
    assert meta.transforming_kickoff_at is None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is None

    assert meta.initializing_started_at <= meta.initializing_stopped_at


def test_update_status_materializing_kickoff():
    """Test updating status to MATERIALIZING_KICKOFF."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.TRANSFORMING_KICKOFF)

    assert meta.status == AssetStatus.TRANSFORMING_KICKOFF

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.transforming_kickoff_at is not None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is None

    assert meta.initializing_started_at <= meta.transforming_kickoff_at


def test_update_status_materializing():
    """Test updating status to MATERIALIZING."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.TRANSFORMING)

    assert meta.status == AssetStatus.TRANSFORMING

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.transforming_kickoff_at is None
    assert meta.transforming_started_at is not None
    assert meta.transforming_stopped_at is None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is None

    assert meta.initializing_started_at <= meta.transforming_started_at


def test_update_status_materializing_failed():
    """Test updating status to MATERIALIZING_FAILED."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.TRANSFORMING_FAILED)

    assert meta.status == AssetStatus.TRANSFORMING_FAILED

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is not None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is None

    assert meta.initializing_started_at <= meta.transforming_stopped_at


def test_update_status_materialized():
    """Test updating status to TRANSFORMED."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.TRANSFORMED)

    assert meta.status == AssetStatus.TRANSFORMED

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.transforming_kickoff_at is None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is not None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is None

    assert meta.initializing_started_at <= meta.transforming_stopped_at


def test_update_status_persisting():
    """Test updating status to PERSISTING."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.PERSISTING)

    assert meta.status == AssetStatus.PERSISTING

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.transforming_kickoff_at is None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is None
    assert meta.persisting_started_at is not None
    assert meta.persisting_stopped_at is None

    assert meta.initializing_started_at <= meta.persisting_started_at


def test_update_status_persisting_failed():
    """Test updating status to PERSISTING_FAILED."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.PERSISTING_FAILED)

    assert meta.status == AssetStatus.PERSISTING_FAILED

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.transforming_kickoff_at is None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is not None

    assert meta.initializing_started_at <= meta.persisting_stopped_at


def test_update_status_persisted():
    """Test updating status to PERSISTED."""
    meta = AssetMetaData()
    meta.update_status(AssetStatus.PERSISTED)

    assert meta.status == AssetStatus.PERSISTED

    assert meta.updated_at is not None
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.transforming_kickoff_at is None
    assert meta.transforming_started_at is None
    assert meta.transforming_stopped_at is None
    assert meta.persisting_started_at is None
    assert meta.persisting_stopped_at is not None

    assert meta.initializing_started_at <= meta.persisting_stopped_at


def test_status_chaining():
    """Test the full lifecycle of status updates with method chaining."""
    meta = AssetMetaData()

    # Test method chaining
    result = (
        meta.update_status(AssetStatus.INITIALIZED)
        .update_status(AssetStatus.TRANSFORMING_KICKOFF)
        .update_status(AssetStatus.TRANSFORMING)
        .update_status(AssetStatus.TRANSFORMED)
        .update_status(AssetStatus.PERSISTING)
        .update_status(AssetStatus.PERSISTED)
    )

    assert result is meta  # Confirm method chaining returns self
    assert meta.status == AssetStatus.PERSISTED

    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is not None
    assert meta.transforming_kickoff_at is not None
    assert meta.transforming_started_at is not None
    assert meta.transforming_stopped_at is not None
    assert meta.persisting_started_at is not None
    assert meta.persisting_stopped_at is not None

    assert meta.initializing_started_at <= meta.initializing_stopped_at
    assert meta.initializing_started_at <= meta.transforming_kickoff_at
    assert meta.transforming_kickoff_at <= meta.transforming_started_at
    assert meta.transforming_started_at <= meta.transforming_stopped_at
    assert meta.transforming_stopped_at <= meta.persisting_started_at
    assert meta.persisting_started_at <= meta.persisting_stopped_at


def test_in_progress():
    """Test the in_progress method."""
    meta = AssetMetaData()

    meta.update_status(AssetStatus.INITIALIZING)
    assert not meta.in_progress()

    meta.update_status(AssetStatus.INITIALIZED)
    assert not meta.in_progress()

    meta.update_status(AssetStatus.TRANSFORMING_KICKOFF)
    assert meta.in_progress()

    meta.update_status(AssetStatus.TRANSFORMING)
    assert meta.in_progress()

    meta.update_status(AssetStatus.TRANSFORMED)
    assert meta.in_progress()

    meta.update_status(AssetStatus.PERSISTING)
    assert meta.in_progress()

    meta.update_status(AssetStatus.PERSISTED)
    assert not meta.in_progress()


def test_has_error():
    """Test the has_error method."""
    meta = AssetMetaData()

    assert not meta.has_error()  # INITIALIZED has no error

    meta.update_status(AssetStatus.TRANSFORMING_KICKOFF)
    assert not meta.has_error()

    meta.update_status(AssetStatus.TRANSFORMING)
    assert not meta.has_error()

    meta.update_status(AssetStatus.TRANSFORMING_FAILED)
    assert meta.has_error()

    meta.update_status(AssetStatus.TRANSFORMED)
    assert not meta.has_error()

    meta.update_status(AssetStatus.PERSISTING_FAILED)
    assert meta.has_error()


def test_json_serialization():
    """Test serialization to and from JSON."""
    # Create a MetaBase with defined timestamps to avoid timing issues
    now = datetime.now()
    original = AssetMetaData(
        status=AssetStatus.PERSISTED,
        initializing_started_at=now - timedelta(minutes=10),
        transforming_kickoff_at=now - timedelta(minutes=9),
        transforming_started_at=now - timedelta(minutes=8),
        transforming_stopped_at=now - timedelta(minutes=5),
        persisting_started_at=now - timedelta(minutes=3),
        persisting_stopped_at=now - timedelta(minutes=1),
        updated_at=now,
    )

    # Convert to JSON
    json_data = original.to_json()

    # Create a new instance from the JSON
    recreated = AssetMetaData.from_json(json_data)

    # Verify all fields match
    assert recreated.status == original.status
    assert recreated.initializing_started_at == original.initializing_started_at
    assert recreated.transforming_kickoff_at == original.transforming_kickoff_at
    assert recreated.transforming_started_at == original.transforming_started_at
    assert recreated.transforming_stopped_at == original.transforming_stopped_at
    assert recreated.persisting_started_at == original.persisting_started_at
    assert recreated.persisting_stopped_at == original.persisting_stopped_at
    assert recreated.updated_at == original.updated_at


def test_json_validation_error():
    """Test that invalid JSON data raises a validation error."""
    with pytest.raises(Exception):  # Pydantic will raise a validation error
        AssetMetaData.from_json('{"status": "INVALID_STATUS"}')
