from unittest.mock import patch

import pytest

from sidas.core import (
    AssetId,
    AssetStatus,
    MetaDataFailedToRetrieve,
)
from sidas.extensions.assets.simple_asset import SimpleAsset, SimpleAssetMetaData
from sidas.extensions.meta_persisters.simple import InMemoryMetaPersister


class TestInMemoryMetaPersister:
    def setup_method(self):
        class TestAsset(SimpleAsset[int]):
            asset_identifier = AssetId("test.asset.id")

            def transformation(self) -> int:
                return 0

        self.persister = InMemoryMetaPersister()
        self.asset_class = TestAsset
        self.asset = TestAsset()

        # Create a meta instance
        self.asset_meta = SimpleAssetMetaData()

        # Set up the asset to return the mock meta
        self.asset.meta = self.asset_meta

    def test_init(self):
        """Test that the persister initializes with an empty data dictionary."""
        assert self.persister._data == {}

    def test_register(self):
        """Test that register calls patch_asset with the provided asset class."""

        with patch.object(self.persister, "patch_asset") as mock_patch_asset:
            self.persister.register(self.asset_class)
            mock_patch_asset.assert_called_once_with(self.asset_class)

    def test_save(self):
        """Test that save stores the asset's meta as JSON in the data dictionary."""
        self.persister.save(self.asset)

        assert self.persister._data[self.asset.asset_id()] == self.asset_meta.to_json()

    def test_load(self):
        """Test that load correctly retrieves and sets the asset's meta from stored JSON."""
        self.persister.save(self.asset)

        self.persister.load(self.asset)
        assert self.asset.meta == self.asset_meta

    def test_load_not_found(self):
        """Test that load raises MetaDataFailedToRetrieve when the asset ID is not found."""
        with pytest.raises(MetaDataFailedToRetrieve):
            self.persister.load(self.asset)


class TestInMemoryMetaPersisterIntegration:
    """Integration tests using actual asset classes."""

    def setup_method(self):
        """Set up test fixtures for integration tests."""
        self.persister = InMemoryMetaPersister()

        # Create a simple implementation of BaseAsset for testing
        class TestAsset(SimpleAsset[int]):
            asset_identifier = AssetId("test.asset.id")

            def transformation(self) -> int:
                return 0

        self.TestMeta = SimpleAssetMetaData
        self.asset_class = TestAsset

        # Register the test asset class with the persister
        self.persister.register(self.asset_class)

        # Create an instance of the test asset
        self.test_asset = self.asset_class()
        self.test_asset.meta = self.TestMeta()

    def test_integration_save_load(self):
        """Test the save and load methods with an actual asset instance."""
        # Update the metadata with a known status
        self.test_asset.meta.update_status(AssetStatus.TRANSFORMED)

        # Save the metadata
        self.persister.save(self.test_asset)

        # Create a new instance of the same asset class
        new_asset = self.asset_class()
        new_asset.meta = self.TestMeta()

        # Verify the new instance has different metadata
        assert new_asset.meta.status != self.test_asset.meta.status

        # Load the metadata into the new instance
        self.persister.load(new_asset)

        # Verify the metadata was loaded correctly
        assert new_asset.meta.status == AssetStatus.TRANSFORMED

    def test_integration_update_status(self):
        """Test that status updates are correctly saved and loaded."""
        # First save the initial state
        self.persister.save(self.test_asset)

        # Update the status
        old_timestamp = self.test_asset.meta.updated_at
        self.test_asset.meta.update_status(AssetStatus.TRANSFORMING)

        # Verify the timestamp was updated
        assert self.test_asset.meta.updated_at > old_timestamp
        assert self.test_asset.meta.transforming_started_at is not None

        # Save the updated state
        self.persister.save(self.test_asset)

        # Create a new instance and load the metadata
        new_asset = self.asset_class()
        self.persister.load(new_asset)

        # Verify the updated status and timestamps
        assert new_asset.meta.status == AssetStatus.TRANSFORMING
        assert new_asset.meta.transforming_started_at is not None
        assert new_asset.meta.updated_at > old_timestamp
