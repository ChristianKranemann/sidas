from typing import Any, Type
from unittest.mock import patch

import pytest

# Assuming the module is named asset_system
from sidas.core import (
    AssetId,
    AssetMetaData,
    AssetNotRegisteredInDataPersister,
    AssetNotRegisteredInMetaPersister,
    AssetStatus,
    BaseAsset,
    DataPersistable,
    DataPersister,
    MetaDataNotStoredException,
    MetaPersistable,
    MetaPersister,
)


class MockDataPersister(DataPersister):
    def __init__(self):
        self.registered_assets: set[Type[DataPersistable]] = set()
        self.saved_data: dict[str, Any] = {}
        self.loaded_data: dict[str, Any] = {}

    def register(self, asset: Type[DataPersistable], *args: Any, **kwargs: Any) -> None:
        self.registered_assets.add(asset)
        self.patch_asset(asset)

    def save(self, asset: DataPersistable) -> None:
        self.saved_data[asset.asset_id()] = asset.data

    def load(self, asset: DataPersistable) -> None:
        if asset.asset_id() in self.saved_data:
            asset.data = self.saved_data[asset.asset_id()]
        else:
            raise Exception("Data not found")


class AssetMetaDataPersister(MetaPersister):
    def __init__(self):
        self.registered_assets = set()
        self.saved_meta = {}

    def register(self, asset: Type[MetaPersistable], *args: Any, **kwargs: Any) -> None:
        self.registered_assets.add(asset)
        self.patch_asset(asset)

    def save(self, asset: MetaPersistable) -> None:
        self.saved_meta[asset.asset_id()] = asset.meta

    def load(self, asset: MetaPersistable) -> None:
        if asset.asset_id() in self.saved_meta:
            asset.meta = self.saved_meta[asset.asset_id()]
        else:
            raise MetaDataNotStoredException("Metadata not found")


TEST_ASSET_DATA = "my data"


class TestAsset(BaseAsset[AssetMetaData, str]):
    asset_identifier = AssetId("test.asset")

    def __init__(self):
        super().__init__()

    def transformation(self) -> str:
        return TEST_ASSET_DATA

    def set_default_meta(self) -> AssetMetaData:
        return AssetMetaData()

    def execute_transformation(self) -> str:
        return self.transformation()

    def can_materialize(self) -> bool:
        return True


class TestBaseAsset:
    def setup_method(self):
        # Clear the asset registry before each test
        BaseAsset.assets = {}

    def test_asset_id_explicit(self):
        asset = TestAsset()
        assert asset.asset_id() == AssetId("test.asset")

    def test_asset_registry(self):
        asset = TestAsset()
        assert BaseAsset.assets[AssetId("test.asset")] is asset

    def test_meta_type(self):
        assert TestAsset.meta_type() == AssetMetaData

    def test_data_type(self):
        assert TestAsset.data_type() is str

    def test_hydrate_new_asset(self):
        asset = TestAsset()
        meta_persister = AssetMetaDataPersister()
        meta_persister.register(TestAsset)

        asset.hydrate()
        assert isinstance(asset.meta, AssetMetaData)
        assert asset.meta.status == AssetStatus.INITIALIZED
        assert AssetId("test.asset") in meta_persister.saved_meta

    def test_hydrate_existing_asset(self):
        asset = TestAsset()
        meta_persister = AssetMetaDataPersister()
        meta_persister.register(TestAsset)

        # Pre-save metadata
        existing_meta = AssetMetaData()
        existing_meta.update_status(AssetStatus.MATERIALIZED)
        meta_persister.saved_meta[AssetId("test.asset")] = existing_meta

        asset.hydrate()
        assert asset.meta is existing_meta
        assert asset.meta.status == AssetStatus.MATERIALIZED

    def test_materialize_success(self):
        asset = TestAsset()
        meta_persister = AssetMetaDataPersister()
        data_persister = MockDataPersister()

        meta_persister.register(TestAsset)
        data_persister.register(TestAsset)

        # Pre-save metadata
        meta = AssetMetaData()
        meta_persister.saved_meta[AssetId("test.asset")] = meta

        asset.materialize()

        assert asset.data == TEST_ASSET_DATA
        assert asset.meta.status == AssetStatus.PERSISTED
        assert AssetId("test.asset") in data_persister.saved_data
        assert data_persister.saved_data[AssetId("test.asset")] == TEST_ASSET_DATA

    @patch("logging.error")
    def test_materialize_transformation_failure(self, mock_log_error):
        asset = TestAsset()
        meta_persister = AssetMetaDataPersister()
        data_persister = MockDataPersister()

        meta_persister.register(TestAsset)
        data_persister.register(TestAsset)

        # Pre-save metadata
        meta = AssetMetaData()
        meta_persister.saved_meta[AssetId("test.asset")] = meta

        # Set up transformation to fail
        def failing_transform():
            raise ValueError("Transformation error")

        asset.transformation = failing_transform

        asset.materialize()

        assert asset.meta.status == AssetStatus.MATERIALIZING_FAILED
        assert mock_log_error.called
        assert (
            "failed to materialize asset test.asset: Transformation error"
            in mock_log_error.call_args[0][0]
        )

    @patch("logging.error")
    def test_materialize_persistence_failure(self, mock_log_error):
        asset = TestAsset()
        meta_persister = AssetMetaDataPersister()
        data_persister = MockDataPersister()

        meta_persister.register(TestAsset)
        data_persister.register(TestAsset)

        # Pre-save metadata
        meta = AssetMetaData()
        meta_persister.saved_meta[AssetId("test.asset")] = meta

        # Make saving data fail
        original_save = data_persister.save

        def failing_save(asset):
            raise ValueError("Save error")

        data_persister.save = failing_save

        asset.materialize()

        assert asset.data == TEST_ASSET_DATA
        assert asset.meta.status == AssetStatus.PERSISTING_FAILED
        assert mock_log_error.called
        assert (
            "failed to persist asset test.asset: Save error"
            in mock_log_error.call_args[0][0]
        )


class TestDataPersister:
    def test_patch_asset(self):
        class TestDataPersisterImpl(DataPersister):
            def register(self, asset, *args, **kwargs):
                self.patch_asset(asset)

            def save(self, asset):
                pass

            def load(self, asset):
                pass

        persister = TestDataPersisterImpl()
        persister.register(TestAsset)

        asset = TestAsset()
        # This should no longer raise AssetNotRegisteredInDataPersister
        asset.save_data()
        asset.load_data()


class TestMetaPersister:
    def test_patch_asset(self):
        class TestMetaPersisterImpl(MetaPersister):
            def register(self, asset, *args, **kwargs):
                self.patch_asset(asset)

            def save(self, asset):
                pass

            def load(self, asset):
                pass

        persister = TestMetaPersisterImpl()
        persister.register(TestAsset)

        asset = TestAsset()
        # This should no longer raise AssetNotRegisteredInMetaPersister
        asset.save_meta()
        asset.load_meta()


class TestExceptionHandling:
    def test_unregistered_asset_exceptions(self):
        asset = TestAsset()

        with pytest.raises(AssetNotRegisteredInMetaPersister):
            asset.save_meta()

        with pytest.raises(AssetNotRegisteredInMetaPersister):
            asset.load_meta()

        with pytest.raises(AssetNotRegisteredInDataPersister):
            asset.save_data()

        with pytest.raises(AssetNotRegisteredInDataPersister):
            asset.load_data()
