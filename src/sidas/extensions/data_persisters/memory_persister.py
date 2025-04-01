from typing import Any, Type

from ...core import AssetId, AssetNotFoundException, DataPersistable, DataPersister


class InMemoryDataPersister(DataPersister):
    def __init__(self) -> None:
        self._data: dict[AssetId, Any] = {}

    def register(
        self,
        *asset: DataPersistable | Type[DataPersistable],
        **kwargs: Any,
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: DataPersistable) -> None:
        self._data[asset.asset_id()] = asset.data

    def load(self, asset: DataPersistable) -> None:
        try:
            asset.data = self._data[asset.asset_id()]
        except KeyError:
            raise AssetNotFoundException()
