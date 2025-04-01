from typing import Any

import pytest

from sidas.core import AssetStatus, CoordinatorStatus
from sidas.extensions.assets import SimpleAsset
from sidas.extensions.coordinators import SimpleCoordinator
from sidas.extensions.data_persisters import InMemoryDataPersister
from sidas.extensions.meta_persisters import InMemoryMetaPersister


class A(SimpleAsset[int]):
    def transformation(self, *args: Any, **kwargs: Any) -> int:
        return 0


def test_init() -> None:
    a = A()
    cron_expression = "test"
    coordinator = SimpleCoordinator([a], cron_expression=cron_expression)
    assert coordinator
    assert coordinator.assets == [a]
    assert coordinator.cron_expression == cron_expression
    assert coordinator.meta.status == CoordinatorStatus.INITIALIZING


def test_hydrate() -> None:
    meta_persister = InMemoryMetaPersister()
    meta_persister.register(SimpleCoordinator)
    coordinator = SimpleCoordinator([])

    coordinator.hydrate()
    assert coordinator.meta is not None
    assert coordinator.meta.status == CoordinatorStatus.INITIALIZED


def test_hydrate_assets() -> None:
    meta_persister = InMemoryMetaPersister()
    meta_persister.register(SimpleCoordinator)
    meta_persister.register(A)

    data_persister = InMemoryDataPersister()
    data_persister.register(A)

    a = A()
    coordinator = SimpleCoordinator([a])

    coordinator.hydrate()
    coordinator.hydrate_assets()

    assert coordinator.meta.status == CoordinatorStatus.HYDRATED
    assert coordinator.assets[0].meta.status == AssetStatus.INITIALIZED


def test_hydrate_assets_failed() -> None:
    meta_persister = InMemoryMetaPersister()
    meta_persister.register(SimpleCoordinator)
    meta_persister.register(A)

    a = A()
    coordinator = SimpleCoordinator([a])

    coordinator.hydrate()

    with pytest.raises(Exception):
        coordinator.hydrate_assets()

    assert coordinator.meta.status == CoordinatorStatus.HYDRATING_FAILED


def test_check_assets() -> None:
    meta_persister = InMemoryMetaPersister()
    meta_persister.register(SimpleCoordinator)
    meta_persister.register(A)

    data_persister = InMemoryDataPersister()
    data_persister.register(A)

    a = A()
    coordinator = SimpleCoordinator([a])

    coordinator.hydrate()
    coordinator.hydrate_assets()
    coordinator.process_assets()

    assert coordinator.meta.status == CoordinatorStatus.PROCESSED
    assert coordinator.assets[0].meta.status == AssetStatus.PERSISTED
