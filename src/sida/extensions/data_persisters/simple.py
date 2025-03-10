from typing import Any, Type

from ...core import AssetId, DataPersister, DefaultAsset, HasAssetId


class InMemoryDataPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self) -> None:
        self._data: dict[AssetId, Any] = {}

    def register(
        self, asset: DefaultAsset | Type[DefaultAsset], *args: Any, **kwargs: Any
    ) -> None:
        self._data[asset.asset_id()] = None
        self.patch_asset(asset)

    def load(self, asset: DefaultAsset) -> None:
        asset.data = self._data[asset.asset_id()]

    def save(self, asset: DefaultAsset) -> None:
        self._data[asset.asset_id()] = asset.data

    def set(self, asset: HasAssetId, data: Any) -> None:
        self._data[asset.asset_id()] = data
