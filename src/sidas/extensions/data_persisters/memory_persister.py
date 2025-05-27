from typing import Any, Type

from ...core import (
    AssetDataFailedToPersist,
    AssetDataFailedToRetrieve,
    AssetId,
    DataPersistable,
    DataPersister,
)


class InMemoryDataPersister(DataPersister):
    def __init__(self) -> None:
        self.data: dict[AssetId, Any] = {}

    def register(
        self,
        *asset: DataPersistable | Type[DataPersistable],
        **kwargs: Any,
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: DataPersistable) -> None:
        try:
            self.data[asset.asset_id()] = asset.data
        except KeyError as e:
            raise AssetDataFailedToPersist(asset.asset_id(), e) from e

    def load(self, asset: DataPersistable) -> None:
        try:
            asset.data = self.data[asset.asset_id()]
        except KeyError as e:
            raise AssetDataFailedToRetrieve(asset.asset_id(), e) from e
