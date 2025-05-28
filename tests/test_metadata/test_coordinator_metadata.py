from datetime import datetime, timedelta

import pytest

from sidas.core import (
    AssetStatus,
    CoordinatorMetaData,
    CoordinatorStatus,
)

CRON_EXPRESSION = "*/30 * * * * *"


def test_default_initialization():
    """Test that a new MetaBase instance has the expected default values."""
    before = datetime.now()
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    after = datetime.now()

    assert meta.status == CoordinatorStatus.INITIALIZING
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is None

    assert before <= meta.updated_at <= after
    assert before <= meta.next_schedule <= after
    assert before <= meta.initializing_started_at <= after


def test_update_status_initialized():
    """Test updating status to INITIALIZED."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.INITIALIZED)

    assert meta.status == AssetStatus.INITIALIZED
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is not None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is None

    assert meta.initializing_started_at <= meta.updated_at
    assert meta.initializing_started_at <= meta.initializing_stopped_at


def test_update_status_hydrating():
    """Test updating status to INITIALIZING."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.INITIALIZING)

    assert meta.status == CoordinatorStatus.INITIALIZING
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is None

    assert meta.initializing_started_at <= meta.updated_at
    assert meta.initializing_started_at <= meta.initializing_started_at


def test_update_status_hydrating_failed():
    """Test updating status to INITIALIZING_FAILED."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.INITIALIZING_FAILED)

    assert meta.status == CoordinatorStatus.INITIALIZING_FAILED
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is not None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is None

    assert meta.initializing_started_at <= meta.updated_at
    assert meta.initializing_started_at <= meta.initializing_stopped_at


def test_update_status_hydrated():
    """Test updating status to INITIALIZED."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.INITIALIZED)

    assert meta.status == CoordinatorStatus.INITIALIZED
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is not None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is None

    assert meta.initializing_started_at <= meta.updated_at
    assert meta.initializing_started_at <= meta.initializing_stopped_at


def test_update_status_processing():
    """Test updating status to PROCESSING."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.PROCESSING)

    assert meta.status == CoordinatorStatus.PROCESSING
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.processing_started_at is not None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is None

    assert meta.initializing_started_at <= meta.updated_at
    assert meta.initializing_started_at <= meta.processing_started_at


def test_update_status_waiting():
    """Test updating status to WAITING."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.WAITING)

    assert meta.status == CoordinatorStatus.WAITING
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is not None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is None

    assert meta.initializing_started_at <= meta.updated_at


def test_update_status_terminating():
    """Test updating status to TERMINATING."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.TERMINATING)

    assert meta.status == CoordinatorStatus.TERMINATING
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is not None
    assert meta.terminating_stopped_at is None

    assert meta.initializing_started_at <= meta.updated_at
    assert meta.initializing_started_at <= meta.terminating_started_at


def test_update_status_terminated():
    """Test updating status to TERMINATED."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)
    meta.update_status(CoordinatorStatus.TERMINATED)

    assert meta.status == CoordinatorStatus.TERMINATED
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is None
    assert meta.processing_started_at is None
    assert meta.processing_stopped_at is None
    assert meta.terminating_started_at is None
    assert meta.terminating_stopped_at is not None

    assert meta.initializing_started_at <= meta.updated_at
    assert meta.initializing_started_at <= meta.terminating_stopped_at


def test_status_chaining():
    """Test the full lifecycle of status updates with method chaining."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)

    # Test method chaining
    result = (
        meta.update_status(CoordinatorStatus.INITIALIZED)
        .update_status(CoordinatorStatus.INITIALIZING)
        .update_status(CoordinatorStatus.INITIALIZED)
        .update_status(CoordinatorStatus.PROCESSING)
        .update_status(CoordinatorStatus.WAITING)
        .update_status(CoordinatorStatus.TERMINATING)
        .update_status(CoordinatorStatus.TERMINATED)
    )

    assert result is meta  # Confirm method chaining returns self
    assert meta.status == CoordinatorStatus.TERMINATED
    assert meta.initializing_started_at is not None
    assert meta.initializing_stopped_at is not None
    assert meta.processing_started_at is not None
    assert meta.processing_stopped_at is not None
    assert meta.terminating_started_at is not None
    assert meta.terminating_stopped_at is not None

    assert meta.initializing_stopped_at > meta.initializing_started_at
    assert meta.processing_stopped_at > meta.processing_started_at
    assert meta.terminating_started_at > meta.processing_stopped_at
    assert meta.terminating_stopped_at > meta.terminating_started_at


def test_in_progress():
    """Test the in_progress method."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)

    for value in CoordinatorStatus:
        meta.update_status(value)
        if value in (
            CoordinatorStatus.INITIALIZING,
            CoordinatorStatus.PROCESSING,
        ):
            assert meta.in_progress()
        else:
            assert not meta.in_progress()


def test_has_error():
    """Test the test_has_error method."""
    meta = CoordinatorMetaData(cron_expression=CRON_EXPRESSION)

    for value in CoordinatorStatus:
        meta.update_status(value)
        if value in (CoordinatorStatus.INITIALIZING_FAILED,):
            assert meta.has_error()
        else:
            assert not meta.has_error()


def test_json_serialization():
    """Test serialization to and from JSON."""
    # Create a MetaBase with defined timestamps to avoid timing issues
    now = datetime.now()
    original = CoordinatorMetaData(
        cron_expression="",
        status=CoordinatorStatus.TERMINATED,
        initializing_started_at=now - timedelta(minutes=10),
        initializing_stopped_at=now - timedelta(minutes=9),
        processing_started_at=now - timedelta(minutes=3),
        processing_stopped_at=now - timedelta(minutes=2),
        terminating_started_at=now - timedelta(minutes=1),
        terminating_stopped_at=now,
        updated_at=now,
    )

    # Convert to JSON
    json_data = original.to_json()

    # Create a new instance from the JSON
    recreated = CoordinatorMetaData.from_json(json_data)

    # Verify all fields match
    assert recreated.status == original.status
    assert recreated.initializing_started_at == original.initializing_started_at
    assert recreated.initializing_stopped_at == original.initializing_stopped_at
    assert recreated.initializing_started_at == original.initializing_started_at
    assert recreated.initializing_stopped_at == original.initializing_stopped_at
    assert recreated.processing_started_at == original.processing_started_at
    assert recreated.processing_stopped_at == original.processing_stopped_at
    assert recreated.terminating_started_at == original.terminating_started_at
    assert recreated.terminating_stopped_at == original.terminating_stopped_at
    assert recreated.updated_at == original.updated_at


def test_json_validation_error():
    """Test that invalid JSON data raises a validation error."""
    with pytest.raises(Exception):  # Pydantic will raise a validation error
        CoordinatorMetaData.from_json('{"status": "INVALID_STATUS"}')
