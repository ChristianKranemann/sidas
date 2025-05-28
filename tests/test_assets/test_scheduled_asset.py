from datetime import datetime
from typing import Any

import pytest
from freezegun import freeze_time

from sidas.core import (
    AssetId,
    AssetStatus,
    DefaultAsset,
)
from sidas.extensions.assets import (
    ScheduledAsset,
    ScheduledAssetMetadata,
)
from sidas.extensions.data_persisters import InMemoryDataPersister
from sidas.extensions.meta_persisters import InMemoryMetaPersister

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
META_TYPE = ScheduledAssetMetadata
DATA_TYPE = int
CRON_EXPRESSION = "*/5 * * * *"
ASSED_IDENTIFIER = AssetId("myname")
TRANSFORMATION_RESULT = 10


class ExampleAsset(ScheduledAsset[DATA_TYPE]):
    cron_expression = CRON_EXPRESSION

    def transformation(self) -> int:
        return TRANSFORMATION_RESULT


ASSET_CLASSES: list[type[DefaultAsset]] = [ExampleAsset]


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
def test_meta_type():
    assert ExampleAsset.meta_type() == META_TYPE


def test_data_type():
    assert ExampleAsset.data_type() == DATA_TYPE


# Methods
# -----------------------------------------------------------------------------
@freeze_time("2023-01-01 10:00:00")
def test_set_default_meta():
    asset = ExampleAsset()
    meta = asset.set_default_meta()
    assert meta.cron_expression == CRON_EXPRESSION
    assert meta.next_schedule == datetime.now()


def test_can_materialize_initializing(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.INITIALIZING)
    asset.save_meta()
    assert not asset.can_materialize()


def test_can_materialize_initializing_failed(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.INITIALIZING_FAILED)
    asset.save_meta()
    assert not asset.can_materialize()


def test_can_materialize_initalized(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.INITIALIZED)
    asset.save_meta()
    assert asset.can_materialize()


def test_can_materialize_persisting(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.MATERIALIZING)
    asset.save_meta()
    assert not asset.can_materialize()


def test_can_materialize_persisting_failed(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.MATERIALIZING_FAILED)
    asset.save_meta()
    assert asset.can_materialize()


@freeze_time("2023-01-01 10:00:00")
def test_can_materialize_persisted_before_next(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.MATERIALIZED)
    asset.meta.next_schedule = datetime(2023, 1, 1, 10, 10)
    asset.save_meta()

    with freeze_time("2023-01-01 10:03:00"):
        assert not asset.can_materialize()


@freeze_time("2023-01-01 10:00:00")
def test_can_materialize_persisted_after_next(asset: ExampleAsset):
    asset.meta.update_status(AssetStatus.MATERIALIZED)
    asset.meta.next_schedule = datetime(2023, 1, 1, 10, 10)
    asset.save_meta()

    with freeze_time("2023-01-01 10:11:00"):
        assert asset.can_materialize()


def test_after_materialize(asset: ExampleAsset):
    asset.initialize()
    asset.materialize()
