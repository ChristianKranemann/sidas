from sidas.core import AssetStatus
from sidas.extensions.assets.downstream_asset import (
    DownstreamAsset,
    DownstreamAssetMetadata,
    DownstreamAssetRefreshMethod,
)
from sidas.extensions.data_persisters import InMemoryDataPersister
from sidas.extensions.meta_persisters import InMemoryMetaPersister


class A(DownstreamAsset[int]):
    def transformation(self) -> int:
        return 1


class B(DownstreamAsset[int]):
    def transformation(self, a: A) -> int:
        return 1 + a.data


class C(DownstreamAsset[int]):
    def transformation(self, a: B) -> int:
        return 1 + a.data


def test_downstream_asset_data_type() -> None:
    mp = InMemoryMetaPersister()
    mp.register(A)
    mp.register(B)

    a = A()
    assert a.data_type() is int

    b = B()
    assert b.data_type() is int


def test_downstream_asset_meta_type() -> None:
    a = A()
    assert a.meta_type() is DownstreamAssetMetadata

    b = B()
    assert b.meta_type() is DownstreamAssetMetadata


def test_downstream_asset_meta_serialization() -> None:
    meta = DownstreamAssetMetadata(
        upstream=[str(A.asset_id())],
        refresh_method=DownstreamAssetRefreshMethod.ALL_UPSTREAM_REFRESHED,
    )
    meta_json = meta.to_json()
    assert meta == DownstreamAssetMetadata.from_json(meta_json)


def test_transformation():
    # mp, dp = REGISTER_ASSETS_IN_MEMORY(B, C)

    b = B()
    c = C()
    b.data = 1
    assert c.transformation(b) == 2


def test_persisting() -> None:
    mp = InMemoryMetaPersister()
    dp = InMemoryDataPersister()

    mp.register(A, B, C)
    dp.register(A, B, C)

    a = A()
    b = B()
    c = C()

    a.hydrate()
    b.hydrate()
    c.hydrate()

    a.materialize()
    b.materialize()
    c.materialize()
    assert a.meta.status == AssetStatus.PERSISTED
    assert b.meta.status == AssetStatus.PERSISTED
    assert c.meta.status == AssetStatus.PERSISTED
    assert a.data == 1
    assert b.data == 2
    assert c.data == 3


def test_persisting_2() -> None:
    mp = InMemoryMetaPersister()
    dp = InMemoryDataPersister()

    a = A()
    b = B()
    c = C()

    mp.register(a, b, c)
    dp.register(a, b, c)

    a.hydrate()
    b.hydrate()
    c.hydrate()

    a.materialize()
    b.materialize()
    c.materialize()
    assert a.meta.status == AssetStatus.PERSISTED
    assert b.meta.status == AssetStatus.PERSISTED
    assert c.meta.status == AssetStatus.PERSISTED
    assert a.data == 1
    assert b.data == 2
    assert c.data == 3


def test_persisting_as_list() -> None:
    mp = InMemoryMetaPersister()
    dp = InMemoryDataPersister()

    assets = [A(), B(), C()]
    dp.register(*assets)
    mp.register(*assets)

    [a.hydrate() for a in assets]
    [a.materialize() for a in assets]

    assert assets[0].meta.status == AssetStatus.PERSISTED
    assert assets[1].meta.status == AssetStatus.PERSISTED
    assert assets[2].meta.status == AssetStatus.PERSISTED
    assert assets[0].data == 1
    assert assets[1].data == 2
    assert assets[2].data == 3
