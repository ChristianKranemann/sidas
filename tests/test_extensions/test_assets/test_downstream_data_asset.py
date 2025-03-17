from sidas.extensions.assets.downstream_asset import (
    DownstreamAsset,
    DownstreamAssetMetadata,
    DownstreamAssetRefreshMethod,
)
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
