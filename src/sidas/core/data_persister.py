from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, Protocol, Type, TypeVar

from .asset_id import AssetId

AssetData = TypeVar("AssetData")


class DataPersistableProtocol(Protocol[AssetData]):
    data: AssetData

    @classmethod
    def asset_id(cls) -> AssetId: ...

    @classmethod
    def data_type(cls) -> Type[object]: ...

    def load_data(self) -> None: ...
    def save_data(self) -> None: ...


DataPersistable = DataPersistableProtocol[Any]


class DataPersister(ABC):
    """
    Abstract base class defining the interface for persisting asset data.

    DataPersister provides the core functionality for registering, saving, and loading
    asset data. Implementations of this class handle the actual storage and retrieval
    operations for asset data.
    """

    @abstractmethod
    def register(
        self, *asset: DataPersistable | Type[DataPersistable], **kwargs: Any
    ) -> None:
        """
        Registers an asset type with the data persister.

        This method should be implemented to configure how the persister will handle
        a specific asset type, including setting up any necessary storage mechanisms.

        Args:
            *asset: The asset class to register
            **kwargs: Additional keyword arguments for the registration process
        """

    @abstractmethod
    def save(self, asset: DataPersistable) -> None:
        """
        Save the data of the given asset.

        This method should be implemented to store the asset's data in the underlying
        persistence system.

        Args:
            asset: The asset instance whose data should be saved
        """
        ...

    @abstractmethod
    def load(self, asset: DataPersistable) -> None:
        """
        Load the data for the given asset.

        This method should be implemented to retrieve the asset's data from the underlying
        persistence system and update the asset's data attribute.

        Args:
            asset: The asset instance whose data should be loaded
        """
        ...

    def patch_asset(self, asset: DataPersistable | Type[DataPersistable]) -> None:
        """
        Link the load and save methods to the asset class.

        This method monkey-patches the asset class to use this persister's load and save
        methods. This should be called in the register method.

        Args:
            asset: The asset class to update with load and save methods
        """
        if not inspect.isclass(asset):
            asset.__class__.save_data = lambda asset: self.load(asset)  # type: ignore
            asset.__class__.save_data = lambda asset: self.save(asset)  # type: ignore
        else:
            asset.load_data = lambda asset: self.load(asset)  # type: ignore
            asset.save_data = lambda asset: self.save(asset)  # type: ignore
