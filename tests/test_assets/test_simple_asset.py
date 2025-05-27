from typing import Any

import pytest

from sidas.core import (
    AssetId,
    AssetNotRegisteredInDataPersister,
    AssetNotRegisteredInMetaPersister,
    AssetStatus,
    DefaultAsset,
)
from sidas.extensions.assets import SimpleAsset, SimpleAssetMetaData
from sidas.extensions.data_persisters import InMemoryDataPersister
from sidas.extensions.meta_persisters import InMemoryMetaPersister

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
META_TYPE = SimpleAssetMetaData
DATA_TYPE = int
ASSED_IDENTIFIER = AssetId("myname")
TRANSFORMATION_RESULT = 10


class ExampleAsset(SimpleAsset[DATA_TYPE]):
    def transformation(self, *args: Any, **kwargs: Any) -> int:
        return TRANSFORMATION_RESULT


class ExampleAssetNamed(SimpleAsset[DATA_TYPE]):
    asset_identifier = ASSED_IDENTIFIER

    def transformation(self, *args: Any, **kwargs: Any) -> int:
        return TRANSFORMATION_RESULT


ASSET_CLASSES: list[type[DefaultAsset]] = [
    ExampleAsset,
    ExampleAssetNamed,
]


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_patched_methods():
    """Clear any patched load/save methods before and after each test to ensure clean state."""
    backup: dict[type[DefaultAsset], dict[str, Any]] = {
        asset_class: {} for asset_class in ASSET_CLASSES
    }
    for asset_class in ASSET_CLASSES:
        backup[asset_class]["load_data"] = asset_class.load_data
        backup[asset_class]["save_data"] = asset_class.save_data
        backup[asset_class]["save_meta"] = asset_class.save_meta
        backup[asset_class]["load_meta"] = asset_class.load_meta

    yield

    for asset_class in ASSET_CLASSES:
        asset_class.load_data = backup[asset_class]["load_data"]
        asset_class.save_data = backup[asset_class]["save_data"]
        asset_class.save_meta = backup[asset_class]["save_meta"]
        asset_class.load_meta = backup[asset_class]["load_meta"]


@pytest.fixture()
def data_persister() -> InMemoryDataPersister:
    return InMemoryDataPersister()


@pytest.fixture()
def meta_persister() -> InMemoryMetaPersister:
    return InMemoryMetaPersister()


@pytest.fixture()
def asset(
    data_persister: InMemoryDataPersister, meta_persister: InMemoryMetaPersister
) -> ExampleAsset:
    asset = ExampleAsset()
    data_persister.register(asset)
    meta_persister.register(asset)
    asset.initialize()
    return asset


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


# Class Methods
# -----------------------------------------------------------------------------
def test_asset_id_default():
    assert ExampleAsset.asset_id() == AssetId(
        "tests.test_assets.test_simple_asset.ExampleAsset"
    )


def test_asset_id_explicit():
    assert ExampleAssetNamed.asset_id() == ASSED_IDENTIFIER


def test_meta_type():
    assert ExampleAsset.meta_type() == META_TYPE


def test_data_type():
    assert ExampleAsset.data_type() == DATA_TYPE


# Methods
# -----------------------------------------------------------------------------
def test_init():
    asset = ExampleAsset()
    assert ExampleAsset.assets[ExampleAsset.asset_id()] == asset


def test_initialize_failes_when_not_registered_in_meta_data_persister(
    data_persister: InMemoryDataPersister,
):
    asset = ExampleAsset()
    data_persister.register(asset)
    with pytest.raises(AssetNotRegisteredInMetaPersister):
        asset.initialize()


def test_initialize_failes_when_not_registered_in_data_data_persister(
    meta_persister: InMemoryMetaPersister,
):
    asset = ExampleAsset()
    meta_persister.register(asset)
    with pytest.raises(AssetNotRegisteredInDataPersister):
        asset.initialize()

    assert meta_persister.meta(asset).status == AssetStatus.INITIALIZING_FAILED


def test_initialize_successfull(
    meta_persister: InMemoryMetaPersister,
    data_persister: InMemoryDataPersister,
):
    asset = ExampleAsset()
    meta_persister.register(asset)
    data_persister.register(asset)

    asset.initialize()
    assert meta_persister.meta(asset).status == AssetStatus.INITIALIZED


def test_transformation(asset: ExampleAsset):
    assert asset.transformation() == TRANSFORMATION_RESULT


def test_execute_transformation(asset: ExampleAsset):
    assert asset.execute_transformation() == TRANSFORMATION_RESULT


def test_can_materialize(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.INITIALIZING)
    asset.save_meta()
    assert not asset.can_materialize()

    asset.meta.update_status(AssetStatus.INITIALIZING_FAILED)
    asset.save_meta()
    assert not asset.can_materialize()

    asset.meta.update_status(AssetStatus.INITIALIZED)
    asset.save_meta()
    assert asset.can_materialize()

    asset.meta.update_status(AssetStatus.TRANSFORMING_KICKOFF)
    asset.save_meta()
    assert not asset.can_materialize()

    asset.meta.update_status(AssetStatus.TRANSFORMING)
    asset.save_meta()
    assert not asset.can_materialize()

    asset.meta.update_status(AssetStatus.PERSISTING)
    asset.save_meta()
    assert not asset.can_materialize()

    asset.meta.update_status(AssetStatus.PERSISTING_FAILED)
    asset.save_meta()
    assert asset.can_materialize()

    asset.meta.update_status(AssetStatus.PERSISTED)
    asset.save_meta()
    assert not asset.can_materialize()


def test_materialize_success(
    asset: ExampleAsset,
    meta_persister: InMemoryMetaPersister,
    data_persister: InMemoryDataPersister,
):
    asset.initialize()
    asset.materialize()

    assert meta_persister.meta(asset).status == AssetStatus.PERSISTED
    assert data_persister.data[asset.asset_id()] == TRANSFORMATION_RESULT


def test_materialize_failed_transformation(
    asset: ExampleAsset,
    meta_persister: InMemoryMetaPersister,
):
    asset.transformation = None  # type: ignore
    asset.materialize()

    assert meta_persister.meta(asset).status == AssetStatus.TRANSFORMING_FAILED


def test_materialize_failed_persisting(
    asset: ExampleAsset,
    meta_persister: InMemoryMetaPersister,
):
    asset.save_data = None  # type: ignore
    asset.materialize()
    assert meta_persister.meta(asset).status == AssetStatus.PERSISTING_FAILED
