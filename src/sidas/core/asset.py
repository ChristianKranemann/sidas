from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Type

from .asset_id import AssetId
from .data_persister import AssetData, DataPersistableProtocol
from .exceptions import (
    AssetNotRegisteredInDataPersister,
    AssetNotRegisteredInMetaPersister,
    MetaDataFailedToRetrieve,
)
from .meta import AssetMetaDataType, AssetStatus
from .meta_persister import MetaPersistableProtocol


class BaseAsset(
    MetaPersistableProtocol[AssetMetaDataType], DataPersistableProtocol[AssetData], ABC
):
    """
    Abstract base class for all assets in the system.

    BaseAsset provides the core functionality for asset management, including identity,
    metadata handling, data transformation, and persistence. It uses generic typing to
    allow specialized asset implementations with specific metadata and data types.

    Type Parameters:
        AssetMeta: The type of metadata for this asset
        AssetData: The type of data this asset manages

    Attributes:
        assets (ClassVar[dict]): Registry of all asset instances by ID
        asset_identifier (ClassVar[AssetId] | None): Optional explicit asset ID
        meta (AssetMeta): The metadata for this asset
        data (AssetData): The data content of this asset
        transformation (Callable): The transformation function to generate asset data
    """

    assets: ClassVar[dict[AssetId, BaseAsset[Any, Any]]] = {}

    asset_identifier: ClassVar[AssetId] | None = None
    meta: AssetMetaDataType
    data: AssetData

    # transformation: Callable[..., Any]
    transformation_args: tuple[Any, ...] = ()

    @classmethod
    def asset_id(cls) -> AssetId:
        """
        Get the unique identifier for this asset class.

        Returns the explicitly defined asset_identifier if available, otherwise
        constructs an ID from the module and class name.

        Returns:
            AssetId: The unique identifier for this asset class
        """
        if cls.asset_identifier is not None:
            return cls.asset_identifier
        return AssetId(f"{cls.__module__}.{cls.__name__}")

    @classmethod
    def meta_type(cls) -> Type[AssetMetaDataType]:
        """
        Get the metadata type for this asset class.

        Extracts the metadata type from the generic parameters of the class.

        Returns:
            Type[AssetMetaBase]: The metadata type for this asset class
        """
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    @classmethod
    def data_type(cls) -> Type[AssetData]:
        """
        Get the data type for this asset class.

        Extracts the data type from the generic parameters of the class.

        Returns:
            Type[AssetData]: The data type for this asset class
        """
        return cls.__orig_bases__[0].__args__[1]  # type: ignore

    def __init__(self) -> None:
        """
        Initialize a new asset instance.

        Registers this asset instance in the global assets registry using its asset ID.
        """
        self.__class__.assets[self.asset_id()] = self

    def initialize(self) -> None:
        logging.info("initialize asset %s", self.asset_id())

        try:
            self.load_meta()
            self.meta = self.meta.update_status(AssetStatus.INITIALIZING)
        except MetaDataFailedToRetrieve:
            self.meta = self.set_default_meta()

        self.save_meta()

        # check if asset has a meta persister
        if (
            type(self).load_meta == DefaultAsset.load_meta
            or type(self).save_meta == DefaultAsset.save_meta
        ):
            self.meta = self.meta.update_status(AssetStatus.INITIALIZING_FAILED)
            self.save_meta()

            raise AssetNotRegisteredInMetaPersister(self.asset_id())

        # check if asset has a data persister
        if (
            type(self).load_data == DefaultAsset.load_data
            or type(self).save_data == DefaultAsset.save_data
        ):
            self.meta = self.meta.update_status(AssetStatus.INITIALIZING_FAILED)
            self.save_meta()

            raise AssetNotRegisteredInDataPersister(self.asset_id())

        self.meta = self.meta.update_status(AssetStatus.INITIALIZED)
        self.save_meta()

    def load_meta(self) -> None:
        """
        Load the asset's metadata from the registered meta persister.

        This method is intended to be monkey-patched by a MetaPersister implementation.

        Raises:
            AssetNotRegisteredInMetaPersister: If the asset is not registered with a meta persister
        """
        raise AssetNotRegisteredInMetaPersister(self.asset_id())

    def save_meta(self) -> None:
        """
        Save the asset's metadata using the registered meta persister.

        This method is intended to be monkey-patched by a MetaPersister implementation.

        Raises:
            AssetNotRegisteredInMetaPersister: If the asset is not registered with a meta persister
        """
        raise AssetNotRegisteredInMetaPersister(self.asset_id())

    def load_data(self) -> None:
        """
        Load the asset's data from the registered data persister.

        This method is intended to be monkey-patched by a DataPersister implementation.

        Raises:
            AssetNotRegisteredInDataPersister: If the asset is not registered with a data persister
        """
        raise AssetNotRegisteredInDataPersister(self.asset_id())

    def save_data(self) -> None:
        """
        Save the asset's data using the registered data persister.

        This method is intended to be monkey-patched by a DataPersister implementation.

        Raises:
            AssetNotRegisteredInDataPersister: If the asset is not registered with a data persister
        """
        raise AssetNotRegisteredInDataPersister(self.asset_id())

    @abstractmethod
    def transformation(self, *args: Any, **kwargs: Any) -> Any:
        """
        The transformation method
        """

    @abstractmethod
    def set_default_meta(self) -> AssetMetaDataType:
        """
        Initialize the default metadata for this asset.

        This method should be implemented by concrete asset classes to provide
        appropriate default metadata when no existing metadata is available.

        Returns:
            AssetMetaData: The default metadata for this asset
        """

    @abstractmethod
    def can_materialize(self) -> bool:
        """
        Check if this asset can be materialized.

        This method should be implemented by concrete asset classes to define
        the conditions under which the asset can be materialized.

        Returns:
            bool: True if the asset can be materialized, False otherwise
        """

    def in_trigger_materialization(self) -> None:
        self.load_meta()
        self.meta.update_status(AssetStatus.TRANSFORMING_KICKOFF)
        self.save_meta()

    def before_materialize(self) -> None:
        """
        Prepare the asset for materialization.
        """
        pass

    def materialize(self) -> None:
        self.load_meta()
        self.meta.update_status(AssetStatus.TRANSFORMING)
        self.save_meta()

        try:
            self.data = self.transformation(*self.transformation_args)
            self.meta.update_status(AssetStatus.TRANSFORMED)
            self.save_meta()
        except Exception as e:
            msg = f"failed to transform asset {self.asset_id()}: {str(e)}\n{traceback.format_exc()}"
            logging.exception(msg)
            self.meta.update_log(msg)
            self.meta.update_status(AssetStatus.TRANSFORMING_FAILED)
            self.save_meta()
            return

        self.meta.update_status(AssetStatus.PERSISTING)
        self.save_meta()

        try:
            self.save_data()
            self.meta.update_status(AssetStatus.PERSISTED)
            self.save_meta()
        except Exception as e:
            msg = f"failed to persist asset {self.asset_id()}: {str(e)}\n{traceback.format_exc()}"
            logging.exception(msg)

            self.meta.update_log(msg)
            self.meta.update_status(AssetStatus.PERSISTING_FAILED)
            self.save_meta()

    def after_materialize(self) -> None:
        """
        Finalize the asset after materialization.
        """
        pass

    def run_materialize_steps(self) -> None:
        """
        Helper method to run the materialization steps in order. Usefull for testing
        or debugging.
        """
        self.before_materialize()
        self.materialize()
        self.after_materialize()


# Type aliases for convenience
DefaultAsset = BaseAsset[Any, Any]
