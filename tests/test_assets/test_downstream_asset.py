from typing import Any

import pytest

from sidas.core import AssetStatus, DefaultAsset
from sidas.extensions.assets import (
    DownstreamAsset,
    DownstreamAssetMetadata,
    DownstreamAssetRefreshMethod,
    SimpleAsset,
)
from sidas.extensions.data_persisters import InMemoryDataPersister
from sidas.extensions.meta_persisters import InMemoryMetaPersister

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
META_TYPE = DownstreamAssetMetadata
DATA_TYPE = int
TRANSFORMATION_RESULT_UPSTREAM = 10
TRANSFORMATION_RESULT_DOWNSTREAM = 30


class Upstream(SimpleAsset[DATA_TYPE]):
    def transformation(self) -> int:
        return TRANSFORMATION_RESULT_UPSTREAM


class DownstreamAll(DownstreamAsset[DATA_TYPE]):
    refresh_method = DownstreamAssetRefreshMethod.ALL_UPSTREAM_REFRESHED

    def transformation(self, upstream: Upstream) -> int:
        return upstream.data + 20


class DownstreamAny(DownstreamAsset[DATA_TYPE]):
    refresh_method = DownstreamAssetRefreshMethod.ANY_UPSTREAM_REFRESHED

    def transformation(self, upstream: Upstream) -> int:
        return upstream.data + 20


ASSET_CLASSES: list[type[DefaultAsset]] = [Upstream, DownstreamAll, DownstreamAny]


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
def upstream(
    data_persister: InMemoryDataPersister, meta_persister: InMemoryMetaPersister
) -> Upstream:
    asset = Upstream()
    data_persister.register(asset)
    meta_persister.register(asset)
    asset.initialize()
    return asset


@pytest.fixture()
def downstream_all(
    data_persister: InMemoryDataPersister, meta_persister: InMemoryMetaPersister
) -> DownstreamAll:
    asset = DownstreamAll()
    data_persister.register(asset)
    meta_persister.register(asset)
    asset.initialize()
    return asset


@pytest.fixture()
def downstream_any(
    data_persister: InMemoryDataPersister, meta_persister: InMemoryMetaPersister
) -> DownstreamAny:
    asset = DownstreamAny()
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
    assert DownstreamAll.meta_type() == META_TYPE


def test_data_type():
    assert DownstreamAll.data_type() == DATA_TYPE


# Methods
# -----------------------------------------------------------------------------
def test_upstream(upstream: Upstream, downstream_all: DownstreamAll):
    assert downstream_all.upstream() == [upstream]


def test_set_default_meta_downstream_all(
    upstream: Upstream, downstream_all: DownstreamAll
):
    meta = downstream_all.set_default_meta()
    assert meta.refresh_method == DownstreamAssetRefreshMethod.ALL_UPSTREAM_REFRESHED
    assert meta.upstream == [upstream.asset_id()]


def test_set_default_meta_downstream_any(
    upstream: Upstream, downstream_any: DownstreamAny
):
    meta = downstream_any.set_default_meta()
    assert meta.refresh_method == DownstreamAssetRefreshMethod.ANY_UPSTREAM_REFRESHED
    assert meta.upstream == [upstream.asset_id()]


def test_can_materialize_initializing(
    upstream: Upstream, downstream_all: DownstreamAll, downstream_any: DownstreamAny
):
    downstream_all.meta.update_status(AssetStatus.INITIALIZING)
    downstream_all.save_meta()
    assert not downstream_all.can_materialize()

    downstream_any.meta.update_status(AssetStatus.INITIALIZING)
    downstream_any.save_meta()
    assert not downstream_any.can_materialize()


def test_can_materialize_initializing_failed(
    upstream: Upstream, downstream_all: DownstreamAll, downstream_any: DownstreamAny
):
    downstream_all.meta.update_status(AssetStatus.INITIALIZING_FAILED)
    downstream_all.save_meta()
    assert not downstream_all.can_materialize()

    downstream_any.meta.update_status(AssetStatus.INITIALIZING_FAILED)
    downstream_any.save_meta()
    assert not downstream_any.can_materialize()


def test_can_materialize_initialized(
    upstream: Upstream, downstream_all: DownstreamAll, downstream_any: DownstreamAny
):
    downstream_all.meta.update_status(AssetStatus.INITIALIZED)
    downstream_all.save_meta()

    downstream_any.meta.update_status(AssetStatus.INITIALIZED)
    downstream_any.save_meta()

    # upstream is initializing
    upstream.meta.update_status(AssetStatus.INITIALIZING)
    upstream.save_meta()
    assert not downstream_all.can_materialize()
    assert not downstream_any.can_materialize()

    # upstream failed to initialize
    upstream.meta.update_status(AssetStatus.INITIALIZING_FAILED)
    upstream.save_meta()
    assert not downstream_all.can_materialize()
    assert not downstream_any.can_materialize()

    # upstream is initialized
    upstream.meta.update_status(AssetStatus.INITIALIZED)
    upstream.save_meta()
    assert not downstream_all.can_materialize()
    assert not downstream_any.can_materialize()

    # upstream is materializing
    upstream.meta.update_status(AssetStatus.MATERIALIZING)
    upstream.save_meta()
    assert not downstream_all.can_materialize()
    assert not downstream_any.can_materialize()

    # upstream failed to materialize
    upstream.meta.update_status(AssetStatus.MATERIALIZING_FAILED)
    upstream.save_meta()
    assert not downstream_all.can_materialize()
    assert not downstream_any.can_materialize()

    # upstream materialized and downstream has not materialized
    upstream.meta.update_status(AssetStatus.MATERIALIZED)
    upstream.save_meta()
    assert downstream_all.can_materialize()
    assert downstream_any.can_materialize()

    # upstream materialized and downstream has materialized later
    downstream_all.meta.update_status(AssetStatus.MATERIALIZED)
    downstream_all.save_meta()
    downstream_any.meta.update_status(AssetStatus.MATERIALIZED)
    downstream_any.save_meta()
    assert not downstream_all.can_materialize()
    assert not downstream_any.can_materialize()


def test_before_materialize(
    upstream: Upstream,
    downstream_all: DownstreamAll,
    data_persister: InMemoryDataPersister,
):
    data_persister.data[upstream.asset_id()] = TRANSFORMATION_RESULT_UPSTREAM

    assert not hasattr(upstream, "data")
    downstream_all.before_materialize()

    assert hasattr(upstream, "data")
    assert upstream.data == TRANSFORMATION_RESULT_UPSTREAM
