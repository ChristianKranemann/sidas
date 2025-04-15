from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, Protocol, Type

from .asset_id import AssetId
from .meta import MetaDataType


class MetaPersistableProtocol(Protocol[MetaDataType]):
    meta: MetaDataType

    @classmethod
    def asset_id(cls) -> AssetId: ...

    @classmethod
    def meta_type(cls) -> Type[MetaDataType]: ...

    def load_meta(self) -> None: ...

    def save_meta(self) -> None: ...


MetaPersistable = MetaPersistableProtocol[Any]


class MetaPersister(ABC):
    """
    Abstract base class defining the interface for persisting asset metadata.

    MetaPersister provides the core functionality for registering, saving, and loading
    asset metadata. Implementations of this class handle the actual storage and retrieval
    operations for asset metadata.
    """

    @abstractmethod
    def register(
        self, *asset: MetaPersistable | Type[MetaPersistable], **kwargs: Any
    ) -> None:
        """
        Registers an asset type with the metadata persister.

        This method should be implemented to configure how the persister will handle
        a specific asset type's metadata, including setting up any necessary storage mechanisms.

        Args:
            *asset: The asset class to register
            **kwargs: Additional keyword arguments for the registration process
        """

    @abstractmethod
    def save(self, asset: MetaPersistable) -> None:
        """
        Save the metadata for a particular asset.

        This method should be implemented to store the asset's metadata in the underlying
        persistence system.

        Args:
            asset: The asset instance whose metadata should be saved
        """
        ...

    @abstractmethod
    def load(self, asset: MetaPersistable) -> None:
        """
        Load the metadata for a particular asset.

        This method should be implemented to retrieve the asset's metadata from the underlying
        persistence system and update the asset's meta attribute.

        Args:
            asset: The asset instance whose metadata should be loaded
        """
        ...

    def patch_asset(self, asset: MetaPersistable | Type[MetaPersistable]) -> None:
        """
        Link the load and save metadata methods to the asset class.

        This method monkey-patches the asset class to use this persister's load and save
        methods for metadata. This should be called in the register method.

        Args:
            asset: The asset class to update with load and save metadata methods
        """
        if not inspect.isclass(asset):
            asset.__class__.load_meta = lambda asset: self.load(asset)  # type: ignore
            asset.__class__.save_meta = lambda asset: self.save(asset)  # type: ignore
        else:
            asset.load_meta = lambda asset: self.load(asset)  # type: ignore
            asset.save_meta = lambda asset: self.save(asset)  # type: ignore
