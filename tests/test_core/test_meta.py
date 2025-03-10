from datetime import datetime, timedelta

import pytest

from sidas.core import AssetStatus, MetaBase


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


class TestMetaBase:
    """Tests for the MetaBase class."""

    def test_default_initialization(self):
        """Test that a new MetaBase instance has the expected default values."""
        before = datetime.now()
        meta = MetaBase()
        after = datetime.now()

        assert meta.status == AssetStatus.INITIALIZED
        assert before <= meta.initialized_at <= after
        assert meta.materializing_started_at is None
        assert meta.materializing_stopped_at is None
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is None
        assert before <= meta.updated_at <= after

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        now = datetime.now()
        meta = MetaBase(
            status=AssetStatus.MATERIALIZED,
            initialized_at=now,
            materializing_started_at=now - timedelta(minutes=5),
            materializing_stopped_at=now,
            updated_at=now,
        )

        assert meta.status == AssetStatus.MATERIALIZED
        assert meta.initialized_at == now
        assert meta.materializing_started_at == now - timedelta(minutes=5)
        assert meta.materializing_stopped_at == now
        assert meta.persisting_started_at is None
        assert meta.persisting_stopped_at is None
        assert meta.updated_at == now

    def test_update_status_initialized(self):
        """Test updating status to INITIALIZED."""
        meta = MetaBase(status=AssetStatus.MATERIALIZED)
        before = datetime.now()
        meta.update_status(AssetStatus.INITIALIZED)
        after = datetime.now()

        assert meta.status == AssetStatus.INITIALIZED
        assert before <= meta.initialized_at <= after
        assert before <= meta.updated_at <= after

    def test_update_status_materializing(self):
        """Test updating status to MATERIALIZING."""
        meta = MetaBase()
        before = datetime.now()
        meta.update_status(AssetStatus.MATERIALIZING)
        after = datetime.now()

        assert meta.status == AssetStatus.MATERIALIZING
        assert meta.materializing_started_at is not None
        assert before <= meta.materializing_started_at <= after
        assert meta.materializing_stopped_at is None
        assert before <= meta.updated_at <= after

    def test_update_status_materializing_failed(self):
        """Test updating status to MATERIALIZING_FAILED."""
        meta = MetaBase()
        meta.update_status(AssetStatus.MATERIALIZING)

        before = datetime.now()
        meta.update_status(AssetStatus.MATERIALIZING_FAILED)
        after = datetime.now()

        assert meta.status == AssetStatus.MATERIALIZING_FAILED
        assert meta.materializing_started_at is not None
        assert meta.materializing_stopped_at is not None
        assert before <= meta.materializing_stopped_at <= after
        assert before <= meta.updated_at <= after

    def test_update_status_materialized(self):
        """Test updating status to MATERIALIZED."""
        meta = MetaBase()
        meta.update_status(AssetStatus.MATERIALIZING)

        before = datetime.now()
        meta.update_status(AssetStatus.MATERIALIZED)
        after = datetime.now()

        assert meta.status == AssetStatus.MATERIALIZED
        assert meta.materializing_started_at is not None
        assert meta.materializing_stopped_at is not None
        assert before <= meta.materializing_stopped_at <= after
        assert before <= meta.updated_at <= after

    def test_update_status_persisting(self):
        """Test updating status to PERSISTING."""
        meta = MetaBase()
        meta.update_status(AssetStatus.MATERIALIZED)

        before = datetime.now()
        meta.update_status(AssetStatus.PERSISTING)
        after = datetime.now()

        assert meta.status == AssetStatus.PERSISTING
        assert meta.materializing_stopped_at is not None
        assert meta.persisting_started_at is not None
        assert before <= meta.persisting_started_at <= after
        assert meta.persisting_stopped_at is None
        assert before <= meta.updated_at <= after

    def test_update_status_persisting_failed(self):
        """Test updating status to PERSISTING_FAILED."""
        meta = MetaBase()
        meta.update_status(AssetStatus.PERSISTING)

        before = datetime.now()
        meta.update_status(AssetStatus.PERSISTING_FAILED)
        after = datetime.now()

        assert meta.status == AssetStatus.PERSISTING_FAILED
        assert meta.persisting_started_at is not None
        assert meta.persisting_stopped_at is not None
        assert before <= meta.persisting_stopped_at <= after
        assert before <= meta.updated_at <= after

    def test_update_status_persisted(self):
        """Test updating status to PERSISTED."""
        meta = MetaBase()
        meta.update_status(AssetStatus.PERSISTING)

        before = datetime.now()
        meta.update_status(AssetStatus.PERSISTED)
        after = datetime.now()

        assert meta.status == AssetStatus.PERSISTED
        assert meta.persisting_started_at is not None
        assert meta.persisting_stopped_at is not None
        assert before <= meta.persisting_stopped_at <= after
        assert before <= meta.updated_at <= after

    def test_status_chaining(self):
        """Test the full lifecycle of status updates with method chaining."""
        meta = MetaBase()

        # Test method chaining
        result = (
            meta.update_status(AssetStatus.MATERIALIZING)
            .update_status(AssetStatus.MATERIALIZED)
            .update_status(AssetStatus.PERSISTING)
            .update_status(AssetStatus.PERSISTED)
        )

        assert result is meta  # Confirm method chaining returns self
        assert meta.status == AssetStatus.PERSISTED
        assert meta.materializing_started_at is not None
        assert meta.materializing_stopped_at is not None
        assert meta.persisting_started_at is not None
        assert meta.persisting_stopped_at is not None
        assert meta.persisting_started_at > meta.materializing_stopped_at

    def test_in_progress(self):
        """Test the in_progress method."""
        meta = MetaBase()

        assert not meta.in_progress()  # INITIALIZED is not in progress

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
        meta = MetaBase()

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
        original = MetaBase(
            status=AssetStatus.PERSISTED,
            initialized_at=now - timedelta(minutes=10),
            materializing_started_at=now - timedelta(minutes=8),
            materializing_stopped_at=now - timedelta(minutes=5),
            persisting_started_at=now - timedelta(minutes=3),
            persisting_stopped_at=now - timedelta(minutes=1),
            updated_at=now,
        )

        # Convert to JSON
        json_data = original.to_json()

        # Create a new instance from the JSON
        recreated = MetaBase.from_json(json_data)

        # Verify all fields match
        assert recreated.status == original.status
        assert recreated.initialized_at == original.initialized_at
        assert recreated.materializing_started_at == original.materializing_started_at
        assert recreated.materializing_stopped_at == original.materializing_stopped_at
        assert recreated.persisting_started_at == original.persisting_started_at
        assert recreated.persisting_stopped_at == original.persisting_stopped_at
        assert recreated.updated_at == original.updated_at

    def test_json_validation_error(self):
        """Test that invalid JSON data raises a validation error."""
        with pytest.raises(Exception):  # Pydantic will raise a validation error
            MetaBase.from_json('{"status": "INVALID_STATUS"}')
