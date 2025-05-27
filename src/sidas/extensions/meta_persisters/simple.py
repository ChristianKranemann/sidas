from typing import Any, Type

from ...core import (
    AssetId,
    AssetMetaData,
    MetaDataFailedToPersist,
    MetaDataFailedToRetrieve,
    MetaPersistable,
    MetaPersister,
)


class InMemoryMetaPersister(MetaPersister):
    def __init__(self) -> None:
        self._data: dict[AssetId, str] = {}

    def register(
        self, *asset: MetaPersistable | Type[MetaPersistable], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: MetaPersistable) -> None:
        try:
            self._data[asset.asset_id()] = asset.meta.to_json()
        except Exception as e:
            raise MetaDataFailedToPersist(asset.asset_id(), e) from e

    def load(self, asset: MetaPersistable) -> None:
        try:
            meta_raw = self._data[asset.asset_id()]
            meta = asset.meta_type().from_json(meta_raw)
            asset.meta = meta
        except Exception as e:
            raise MetaDataFailedToRetrieve(asset.asset_id(), e) from e

    def heartbeat(self) -> None:
        pass

    def meta(self, asset: MetaPersistable) -> AssetMetaData:
        meta_raw = self._data[asset.asset_id()]
        return asset.meta_type().from_json(meta_raw)


__all__ = ["InMemoryMetaPersister"]
