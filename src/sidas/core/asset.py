from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Type

from .asset_id import AssetId
from .data_persister import AssetData, DataPersistableProtocol
from .exceptions import (
    AssetNotRegisteredInDataPersister,
    AssetNotRegisteredInMetaPersister,
    MetaDataNotStoredException,
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

    def validate(self) -> None:
        logging.info("validating asset %s", self.asset_id())
        if type(self).transformation == DefaultAsset.transformation:
            raise Exception(
                f"Asset {self.asset_id()} needs to implement transformation."
            )

        if type(self).set_default_meta == DefaultAsset.set_default_meta:
            raise Exception(
                f"Asset {self.asset_id()} needs to implement set_default_meta."
            )

        if type(self).execute_transformation == DefaultAsset.execute_transformation:
            raise Exception(
                f"Asset {self.asset_id()} needs to implement execute_transformation."
            )

        if type(self).can_materialize == DefaultAsset.can_materialize:
            raise Exception(
                f"Asset {self.asset_id()}needs to implement can_materialize."
            )

        if type(self).save_meta == DefaultAsset.save_meta:
            raise Exception(f"Asset {self.asset_id()} has no meta persister.")

        if type(self).save_data == DefaultAsset.save_data:
            raise Exception(f"Asset {self.asset_id()} has no data persister.")

    def hydrate(self) -> None:
        """
        Initialize or load the asset's metadata.

        Attempts to load existing metadata for the asset. If no metadata exists,
        creates default metadata and saves it.

        Raises:
            MetaDataNotStoredException: If metadata loading fails
        """
        try:
            self.load_meta()
        except MetaDataNotStoredException:
            self.meta = self.set_default_meta()
            self.meta.update_status(AssetStatus.INITIALIZED)
            self.save_meta()

    def load_meta(self) -> None:
        """
        Load the asset's metadata from the registered meta persister.

        This method is intended to be monkey-patched by a MetaPersister implementation.

        Raises:
            AssetNotRegisteredInMetaPersister: If the asset is not registered with a meta persister
        """
        raise AssetNotRegisteredInMetaPersister()

    def save_meta(self) -> None:
        """
        Save the asset's metadata using the registered meta persister.

        This method is intended to be monkey-patched by a MetaPersister implementation.

        Raises:
            AssetNotRegisteredInMetaPersister: If the asset is not registered with a meta persister
        """
        raise AssetNotRegisteredInMetaPersister()

    def load_data(self) -> None:
        """
        Load the asset's data from the registered data persister.

        This method is intended to be monkey-patched by a DataPersister implementation.

        Raises:
            AssetNotRegisteredInDataPersister: If the asset is not registered with a data persister
        """
        raise AssetNotRegisteredInDataPersister()

    def save_data(self) -> None:
        """
        Save the asset's data using the registered data persister.

        This method is intended to be monkey-patched by a DataPersister implementation.

        Raises:
            AssetNotRegisteredInDataPersister: If the asset is not registered with a data persister
        """
        raise AssetNotRegisteredInDataPersister()

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
    def execute_transformation(self) -> AssetData:
        """
        Execute the transformation to generate this asset's data.

        This method should be implemented by concrete asset classes to define
        the logic for generating or transforming the asset's data.

        Returns:
            AssetData: The generated or transformed data for this asset
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

    def before_materialize(self) -> None:
        """
        Prepare the asset for materialization.

        Updates the asset's status to indicate that materialization is in progress.
        """
        self.load_meta()
        self.meta.update_status(AssetStatus.MATERIALIZING)
        self.save_meta()

    def materialize(self) -> None:
        """
        Materialize the asset by executing its transformation and persisting the result.

        This method orchestrates the full materialization process:
        1. Load the asset's metadata
        2. Execute the transformation to generate data
        3. Update the asset's status
        4. Save the generated data

        Any exceptions during transformation or persistence are caught, logged,
        and reflected in the asset's status.
        """
        self.load_meta()

        try:
            self.data = self.execute_transformation()
            self.meta.update_status(AssetStatus.MATERIALIZED)
            self.save_meta()
        except Exception as e:
            msg = f"failed to materialize asset {self.asset_id()}: {e}"
            logging.exception(msg)

            self.meta.update_log(msg)
            self.meta.update_status(AssetStatus.MATERIALIZING_FAILED)
            self.save_meta()
            return

        self.meta.update_status(AssetStatus.PERSISTING)
        self.save_meta()

        try:
            self.save_data()
            self.meta.update_status(AssetStatus.PERSISTED)
            self.save_meta()
        except Exception as e:
            msg = f"failed to persist asset {self.asset_id()}: {e}"
            logging.exception(msg)

            self.meta.update_log(msg)
            self.meta.update_status(AssetStatus.PERSISTING_FAILED)
            self.save_meta()


# Type aliases for convenience
DefaultAsset = BaseAsset[Any, Any]
