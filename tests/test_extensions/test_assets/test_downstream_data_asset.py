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


# import time

# from sida_core import (
#     Asset,
#     AssetStatus,
#     DownstreamAsset,
#     DownstreamAssetRefreshMethod,
# )


# class ExampleAsset1(Asset[int, None]):
#     def materialization_required(self) -> bool:
#         return True

#     def materialize(self) -> None:
#         self.value = 1


# class ExampleAsset2(Asset[int, None]):
#     def materialize(self) -> None:
#         self.value = 2

#     def materialization_required(self) -> bool:
#         return True


# class DownstreamExampleAsset1(
#     DownstreamAsset[int, tuple[ExampleAsset1, ExampleAsset2]]
# ):
#     def materialize(self) -> None:
#         asset_1, asset_2 = self.upstream
#         self.value = 1 + asset_1.value + asset_2.value


# class DownstreamExampleAsset2(
#     DownstreamAsset[int, tuple[ExampleAsset1, ExampleAsset2]]
# ):
#     refresh_method = DownstreamAssetRefreshMethod.ANY_UPSTREAM_REFRESHED

#     def materialize(self) -> None:
#         asset_1, asset_2 = self.upstream
#         self.value = 1 + asset_1.value + asset_2.value


# def test_contructor_default():
#     asset = DownstreamExampleAsset1()
#     assert asset.refresh_method == DownstreamAssetRefreshMethod.ALL_UPSTREAM_REFRESHED


# def test_contructor_explicit():
#     asset = DownstreamExampleAsset2()
#     assert asset.refresh_method == DownstreamAssetRefreshMethod.ANY_UPSTREAM_REFRESHED


# def test_materialization_required_all_upstream_refreshed():
#     upstream_1 = ExampleAsset1()
#     upstream_2 = ExampleAsset2()

#     asset = DownstreamExampleAsset1()
#     asset.upstream = (upstream_1, upstream_2)

#     # materialization not required, only one upstream ready
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is False

#     # materialization required, both ready
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     upstream_2.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is True

#     # set metadata for asset
#     asset.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     time.sleep(0.1)

#     # materialization not required, only one upstream refresehd
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is False

#     # materialization required, both refreshed
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     upstream_2.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is True


# def test_materialization_required_any_upstream_refreshed():
#     upstream_1 = ExampleAsset1()
#     upstream_2 = ExampleAsset2()

#     asset = DownstreamExampleAsset2()
#     asset.upstream = (upstream_1, upstream_2)

#     # materialization not required, only on upstream ready
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is False

#     # materialization required, both ready
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     upstream_2.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is True

#     # set metadata for asset
#     asset.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     time.sleep(0.1)

#     # materialization required, one upstream refresehd
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is True

#     # materialization required, both refreshed
#     upstream_1.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     upstream_2.metadata.set_asset_status(AssetStatus.MATERIALIZED)
#     assert asset.materialization_required() is True


# def test_materialize():
#     upstream_1 = ExampleAsset1()
#     upstream_2 = ExampleAsset2()

#     asset = DownstreamExampleAsset1()
#     asset.upstream = (upstream_1, upstream_2)

#     upstream_1.materialize()
#     upstream_2.materialize()
#     asset.materialize()
#     assert asset.value == 4
