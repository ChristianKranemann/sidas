from typing import Any

import pytest

from sidas.core import (
    AssetId,
    AssetNotFoundException,
    AssetStatus,
    CoordinatorMetaData,
    CoordinatorStatus,
    DefaultAsset,
)
from sidas.extensions.assets import SimpleAsset
from sidas.extensions.coordinators import SimpleCoordinator
from sidas.extensions.data_persisters import InMemoryDataPersister
from sidas.extensions.meta_persisters import InMemoryMetaPersister

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
CRON_EXPRESSION = "*/10 * * * * *"
ASSET_DATA = 10


class ExampleAsset(SimpleAsset[int]):
    def __init__(self) -> None:
        super().__init__()
        self.in_trigger_materialization_executed = False
        self.before_materialize_executed = False
        self.after_materialize_executed = False

    def transformation(self, *args: Any, **kwargs: Any) -> int:
        return ASSET_DATA

    def in_trigger_materialization(self) -> None:
        self.in_trigger_materialization_executed = True
        return super().in_trigger_materialization()

    def before_materialize(self) -> None:
        self.before_materialize_executed = True
        return super().before_materialize()

    def after_materialize(self) -> None:
        self.after_materialize_executed = True
        return super().after_materialize()


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
    return asset


@pytest.fixture()
def coordinator(meta_persister: InMemoryMetaPersister) -> SimpleCoordinator:
    coordinator = SimpleCoordinator(cron_expression=CRON_EXPRESSION)
    meta_persister.register(coordinator)
    return coordinator


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


# Class Methods
# -----------------------------------------------------------------------------
def test_assed_id():
    assert SimpleCoordinator.asset_id() == AssetId("Coordinator")


def test_meta_type():
    assert SimpleCoordinator.meta_type() == CoordinatorMetaData


def test_load_coordinator():
    pass


# Class Methods
# -----------------------------------------------------------------------------
def test_init(coordinator: SimpleCoordinator) -> None:
    assert coordinator
    assert coordinator.assets == []
    assert coordinator.cron_expression == CRON_EXPRESSION


def test_register(coordinator: SimpleCoordinator, asset: ExampleAsset):
    coordinator.register(asset)
    assert coordinator.assets == [asset]


def test_initialize(coordinator: SimpleCoordinator) -> None:
    assert not hasattr(coordinator, "meta")

    coordinator.initialize()
    assert hasattr(coordinator, "meta")
    assert isinstance(coordinator.meta, coordinator.meta_type())
    assert coordinator.meta.status == CoordinatorStatus.INITIALIZED


def test_initialize_with_assets(
    coordinator: SimpleCoordinator, asset: ExampleAsset
) -> None:
    coordinator.register(asset)

    coordinator.initialize()
    assert hasattr(asset, "meta")
    assert isinstance(asset.meta, asset.meta_type())
    assert asset.meta.status == AssetStatus.INITIALIZED


def test_initialize_with_assets_fails_asset_invalid(
    coordinator: SimpleCoordinator,
) -> None:
    """
    Unregistered asset fails validation
    """
    asset = ExampleAsset()
    coordinator.register(asset)

    coordinator.initialize()
    assert coordinator.meta.status == AssetStatus.INITIALIZING_FAILED


def test_get_asset(coordinator: SimpleCoordinator, asset: ExampleAsset):
    with pytest.raises(AssetNotFoundException):
        coordinator.asset(asset.asset_id())

    coordinator.register(asset)

    assert coordinator.asset(asset.asset_id()) == asset


def test_materialize(
    meta_persister: InMemoryMetaPersister,
    data_persister: InMemoryDataPersister,
    coordinator: SimpleCoordinator,
    asset: ExampleAsset,
):
    coordinator.register(asset)
    coordinator.initialize()
    coordinator.materialize(asset.asset_id())

    assert not asset.in_trigger_materialization_executed
    assert asset.before_materialize_executed
    assert asset.after_materialize_executed
    assert data_persister.data[asset.asset_id()] == ASSET_DATA
    assert meta_persister.meta(asset).status == AssetStatus.PERSISTED


def test_materialize_terminating(
    meta_persister: InMemoryMetaPersister,
    data_persister: InMemoryDataPersister,
    coordinator: SimpleCoordinator,
    asset: ExampleAsset,
):
    coordinator.register(asset)
    coordinator.initialize()

    coordinator.meta.status = CoordinatorStatus.TERMINATING
    coordinator.save_meta()

    coordinator.materialize(asset.asset_id())

    assert not asset.in_trigger_materialization_executed
    assert not asset.before_materialize_executed
    assert not asset.after_materialize_executed

    assert meta_persister.meta(asset).status == AssetStatus.INITIALIZED


def test_trigger_materialization(
    meta_persister: InMemoryMetaPersister,
    data_persister: InMemoryDataPersister,
    coordinator: SimpleCoordinator,
    asset: ExampleAsset,
):
    coordinator.register(asset)
    coordinator.initialize()
    coordinator.trigger_materialization(asset)

    assert asset.in_trigger_materialization_executed
    assert asset.before_materialize_executed
    assert asset.after_materialize_executed
    assert data_persister.data[asset.asset_id()] == ASSET_DATA
    assert meta_persister.meta(asset).status == AssetStatus.PERSISTED


def test_materialize_terminate():
    pass
