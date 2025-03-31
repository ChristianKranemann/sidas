from datetime import datetime, timedelta

import pytest

from sidas.core import (
    AssetMetaData,
    AssetStatus,
    CoordinatorMetaData,
    CoordinatorStatus,
)


class TestAssetStatus:
    """Tests for the AssetStatus enumeration."""

    def test_status_values(self):
        """Test that the AssetStatus enum has the expected values."""
        assert AssetStatus.INITIALIZED == "INITIALIZED"
        assert AssetStatus.MATERIALIZING == "MATERIALIZING"
        assert AssetStatus.MATERIALIZING_FAILED == "MATERIALIZING_FAILED"
        assert AssetStatus.MATERIALIZED == "MATERIALIZED"
        assert AssetStatus.PERSISTING == "PERSISTING"
        assert AssetStatus.PERSISTING_FAILED == "PERSISTING_FAILED"
        assert AssetStatus.PERSISTED == "PERSISTED"

    def test_status_conversion(self):
        """Test conversion between enum values and strings."""
        assert str(AssetStatus.INITIALIZED) == "INITIALIZED"
        assert AssetStatus("MATERIALIZED") == AssetStatus.MATERIALIZED


class TestAssetMetaData:
    """Tests for the MetaBase class."""

    def test_default_initialization(self):
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
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is None

        assert before <= meta.updated_at <= after
        assert before <= meta.initializing_started_at <= after

    def test_update_status_initialized(self):
        """Test updating status to INITIALIZED."""
        meta = AssetMetaData()
        meta.update_status(AssetStatus.INITIALIZED)

        assert meta.status == AssetStatus.INITIALIZED

        assert meta.updated_at is not None
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is not None
        assert meta.materializing_started_at is None
        assert meta.materializing_stopped_at is None
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is None

        assert meta.initializing_started_at <= meta.initializing_stopped_at

    def test_update_status_materializing(self):
        """Test updating status to MATERIALIZING."""
        meta = AssetMetaData()
        meta.update_status(AssetStatus.MATERIALIZING)

        assert meta.status == AssetStatus.MATERIALIZING

        assert meta.updated_at is not None
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.materializing_started_at is not None
        assert meta.materializing_stopped_at is None
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is None

        assert meta.initializing_started_at <= meta.materializing_started_at

    def test_update_status_materializing_failed(self):
        """Test updating status to MATERIALIZING_FAILED."""
        meta = AssetMetaData()
        meta.update_status(AssetStatus.MATERIALIZING_FAILED)

        assert meta.status == AssetStatus.MATERIALIZING_FAILED

        assert meta.updated_at is not None
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.materializing_started_at is None
        assert meta.materializing_stopped_at is not None
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is None

        assert meta.initializing_started_at <= meta.materializing_stopped_at

    def test_update_status_materialized(self):
        """Test updating status to MATERIALIZED."""
        meta = AssetMetaData()
        meta.update_status(AssetStatus.MATERIALIZED)

        assert meta.status == AssetStatus.MATERIALIZED

        assert meta.updated_at is not None
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.materializing_started_at is None
        assert meta.materializing_stopped_at is not None
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is None

        assert meta.initializing_started_at <= meta.materializing_stopped_at

    def test_update_status_persisting(self):
        """Test updating status to PERSISTING."""
        meta = AssetMetaData()
        meta.update_status(AssetStatus.PERSISTING)

        assert meta.status == AssetStatus.PERSISTING

        assert meta.updated_at is not None
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.materializing_started_at is None
        assert meta.materializing_stopped_at is None
        assert meta.persisting_started_at is not None
        assert meta.persisting_stopped_at is None

        assert meta.initializing_started_at <= meta.persisting_started_at

    def test_update_status_persisting_failed(self):
        """Test updating status to PERSISTING_FAILED."""
        meta = AssetMetaData()
        meta.update_status(AssetStatus.PERSISTING_FAILED)

        assert meta.status == AssetStatus.PERSISTING_FAILED

        assert meta.updated_at is not None
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.materializing_started_at is None
        assert meta.materializing_stopped_at is None
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is not None

        assert meta.initializing_started_at <= meta.persisting_stopped_at

    def test_update_status_persisted(self):
        """Test updating status to PERSISTED."""
        meta = AssetMetaData()
        meta.update_status(AssetStatus.PERSISTED)

        assert meta.status == AssetStatus.PERSISTED

        assert meta.updated_at is not None
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.materializing_started_at is None
        assert meta.materializing_stopped_at is None
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is not None

        assert meta.initializing_started_at <= meta.persisting_stopped_at

    def test_status_chaining(self):
        """Test the full lifecycle of status updates with method chaining."""
        meta = AssetMetaData()

        # Test method chaining
        result = (
            meta.update_status(AssetStatus.INITIALIZED)
            .update_status(AssetStatus.MATERIALIZING)
            .update_status(AssetStatus.MATERIALIZED)
            .update_status(AssetStatus.PERSISTING)
            .update_status(AssetStatus.PERSISTED)
        )

        assert result is meta  # Confirm method chaining returns self
        assert meta.status == AssetStatus.PERSISTED

        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is not None
        assert meta.materializing_started_at is not None
        assert meta.materializing_stopped_at is not None
        assert meta.persisting_started_at is not None
        assert meta.persisting_stopped_at is not None

        assert meta.initializing_started_at <= meta.initializing_stopped_at
        assert meta.initializing_stopped_at <= meta.materializing_started_at
        assert meta.materializing_started_at <= meta.materializing_stopped_at
        assert meta.materializing_stopped_at <= meta.persisting_started_at
        assert meta.persisting_started_at <= meta.persisting_stopped_at

    def test_in_progress(self):
        """Test the in_progress method."""
        meta = AssetMetaData()

        meta.update_status(AssetStatus.INITIALIZING)
        assert not meta.in_progress()

        meta.update_status(AssetStatus.INITIALIZED)
        assert not meta.in_progress()

        meta.update_status(AssetStatus.MATERIALIZING)
        assert meta.in_progress()

        meta.update_status(AssetStatus.MATERIALIZED)
        assert not meta.in_progress()

        meta.update_status(AssetStatus.PERSISTING)
        assert meta.in_progress()

        meta.update_status(AssetStatus.PERSISTED)
        assert not meta.in_progress()

    def test_has_error(self):
        """Test the has_error method."""
        meta = AssetMetaData()

        assert not meta.has_error()  # INITIALIZED has no error

        meta.update_status(AssetStatus.MATERIALIZING)
        assert not meta.has_error()

        meta.update_status(AssetStatus.MATERIALIZING_FAILED)
        assert meta.has_error()

        meta.update_status(AssetStatus.MATERIALIZED)
        assert not meta.has_error()

        meta.update_status(AssetStatus.PERSISTING_FAILED)
        assert meta.has_error()

    def test_json_serialization(self):
        """Test serialization to and from JSON."""
        # Create a MetaBase with defined timestamps to avoid timing issues
        now = datetime.now()
        original = AssetMetaData(
            status=AssetStatus.PERSISTED,
            initializing_started_at=now - timedelta(minutes=10),
            materializing_started_at=now - timedelta(minutes=8),
            materializing_stopped_at=now - timedelta(minutes=5),
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
        assert recreated.materializing_started_at == original.materializing_started_at
        assert recreated.materializing_stopped_at == original.materializing_stopped_at
        assert recreated.persisting_started_at == original.persisting_started_at
        assert recreated.persisting_stopped_at == original.persisting_stopped_at
        assert recreated.updated_at == original.updated_at

    def test_json_validation_error(self):
        """Test that invalid JSON data raises a validation error."""
        with pytest.raises(Exception):  # Pydantic will raise a validation error
            AssetMetaData.from_json('{"status": "INVALID_STATUS"}')


class TestCoordinatorMeta:
    """Tests for the CoordinatorMeta class."""

    cron_expression = "*/30 * * * * *"

    def test_default_initialization(self):
        """Test that a new MetaBase instance has the expected default values."""
        before = datetime.now()
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        after = datetime.now()

        assert meta.status == CoordinatorStatus.INITIALIZING
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert before <= meta.updated_at <= after
        assert before <= meta.next_schedule <= after
        assert before <= meta.initializing_started_at <= after

    def test_update_status_initialized(self):
        """Test updating status to INITIALIZED."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.INITIALIZED)

        assert meta.status == AssetStatus.INITIALIZED
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is not None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.initializing_stopped_at

    def test_update_status_hydrating(self):
        """Test updating status to HYDRATING."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.HYDRATING)

        assert meta.status == CoordinatorStatus.HYDRATING
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is not None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.hydrating_started_at

    def test_update_status_hydrating_failed(self):
        """Test updating status to HYDRATING_FAILED."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.HYDRATING_FAILED)

        assert meta.status == CoordinatorStatus.HYDRATING_FAILED
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is not None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.hydrating_stopped_at

    def test_update_status_hydrated(self):
        """Test updating status to HYDRATED."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.HYDRATED)

        assert meta.status == CoordinatorStatus.HYDRATED
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is not None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.hydrating_stopped_at

    def test_update_status_processing(self):
        """Test updating status to PROCESSING."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.PROCESSING)

        assert meta.status == CoordinatorStatus.PROCESSING
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is not None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.processing_started_at

    def test_update_status_processing_failed(self):
        """Test updating status to PROCESSING_FAILED."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.PROCESSING_FAILED)

        assert meta.status == CoordinatorStatus.PROCESSING_FAILED
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is not None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.processing_stopped_at

    def test_update_status_processed(self):
        """Test updating status to PROCESSED."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.PROCESSED)

        assert meta.status == CoordinatorStatus.PROCESSED
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is not None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.processing_stopped_at

    def test_update_status_waiting(self):
        """Test updating status to WAITING."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.WAITING)

        assert meta.status == CoordinatorStatus.WAITING
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at

    def test_update_status_terminating(self):
        """Test updating status to TERMINATING."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.TERMINATING)

        assert meta.status == CoordinatorStatus.TERMINATING
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is not None
        assert meta.terminating_stopped_at is None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.terminating_started_at

    def test_update_status_terminated(self):
        """Test updating status to TERMINATED."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)
        meta.update_status(CoordinatorStatus.TERMINATED)

        assert meta.status == CoordinatorStatus.TERMINATED
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is None
        assert meta.hydrating_started_at is None
        assert meta.hydrating_stopped_at is None
        assert meta.processing_started_at is None
        assert meta.processing_stopped_at is None
        assert meta.terminating_started_at is None
        assert meta.terminating_stopped_at is not None

        assert meta.initializing_started_at <= meta.updated_at
        assert meta.initializing_started_at <= meta.terminating_stopped_at

    def test_status_chaining(self):
        """Test the full lifecycle of status updates with method chaining."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)

        # Test method chaining
        result = (
            meta.update_status(CoordinatorStatus.INITIALIZED)
            .update_status(CoordinatorStatus.HYDRATING)
            .update_status(CoordinatorStatus.HYDRATED)
            .update_status(CoordinatorStatus.PROCESSING)
            .update_status(CoordinatorStatus.PROCESSED)
            .update_status(CoordinatorStatus.WAITING)
            .update_status(CoordinatorStatus.TERMINATING)
            .update_status(CoordinatorStatus.TERMINATED)
        )

        assert result is meta  # Confirm method chaining returns self
        assert meta.status == CoordinatorStatus.TERMINATED
        assert meta.initializing_started_at is not None
        assert meta.initializing_stopped_at is not None
        assert meta.hydrating_started_at is not None
        assert meta.hydrating_stopped_at is not None
        assert meta.processing_started_at is not None
        assert meta.processing_stopped_at is not None
        assert meta.terminating_started_at is not None
        assert meta.terminating_stopped_at is not None

        assert meta.initializing_stopped_at > meta.initializing_started_at
        assert meta.hydrating_started_at > meta.initializing_stopped_at
        assert meta.hydrating_stopped_at > meta.hydrating_started_at
        assert meta.processing_started_at > meta.hydrating_stopped_at
        assert meta.processing_stopped_at > meta.processing_started_at
        assert meta.terminating_started_at > meta.processing_stopped_at
        assert meta.terminating_stopped_at > meta.terminating_started_at

    def test_in_progress(self):
        """Test the in_progress method."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)

        for value in CoordinatorStatus:
            meta.update_status(value)
            if value in (
                CoordinatorStatus.INITIALIZING,
                CoordinatorStatus.HYDRATING,
                CoordinatorStatus.PROCESSING,
            ):
                assert meta.in_progress()
            else:
                assert not meta.in_progress()

    def test_has_error(self):
        """Test the test_has_error method."""
        meta = CoordinatorMetaData(cron_expression=self.cron_expression)

        for value in CoordinatorStatus:
            meta.update_status(value)
            if value in (
                CoordinatorStatus.INITIALIZING_FAILED,
                CoordinatorStatus.HYDRATING_FAILED,
                CoordinatorStatus.PROCESSING_FAILED,
            ):
                assert meta.has_error()
            else:
                assert not meta.has_error()

    def test_json_serialization(self):
        """Test serialization to and from JSON."""
        # Create a MetaBase with defined timestamps to avoid timing issues
        now = datetime.now()
        original = CoordinatorMetaData(
            cron_expression="",
            status=CoordinatorStatus.TERMINATED,
            initializing_started_at=now - timedelta(minutes=10),
            initializing_stopped_at=now - timedelta(minutes=9),
            hydrating_started_at=now - timedelta(minutes=5),
            hydrating_stopped_at=now - timedelta(minutes=4),
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
        assert recreated.hydrating_started_at == original.hydrating_started_at
        assert recreated.hydrating_stopped_at == original.hydrating_stopped_at
        assert recreated.processing_started_at == original.processing_started_at
        assert recreated.processing_stopped_at == original.processing_stopped_at
        assert recreated.terminating_started_at == original.terminating_started_at
        assert recreated.terminating_stopped_at == original.terminating_stopped_at
        assert recreated.updated_at == original.updated_at

    def test_json_validation_error(self):
        """Test that invalid JSON data raises a validation error."""
        with pytest.raises(Exception):  # Pydantic will raise a validation error
            CoordinatorMetaData.from_json('{"status": "INVALID_STATUS"}')
