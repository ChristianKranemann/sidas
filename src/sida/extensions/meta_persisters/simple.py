from typing import Any, Type

from ...core import AssetId, DefaultAsset, MetaPersister
from ...core.exceptions import MetaDataNotStoredException


class InMemoryMetaPersister(MetaPersister):
    def __init__(self) -> None:
        self._data: dict[AssetId, str] = {}

    def register(
        self, *asset: DefaultAsset | Type[DefaultAsset], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: DefaultAsset) -> None:
        self._data[asset.asset_id()] = asset.meta.to_json()

    def load(self, asset: DefaultAsset) -> None:
        try:
            meta_raw = self._data[asset.asset_id()]
            meta = asset.meta_type().from_json(meta_raw)
            asset.meta = meta
        except KeyError:
            raise MetaDataNotStoredException()

    def heartbeat(self) -> None:
        pass


__all__ = ["InMemoryMetaPersister"]
