from __future__ import annotations

from typing import Type

from ...core import AssetData, AssetMetaData, BaseAsset


class SimpleAssetMetaData(AssetMetaData): ...


class SimpleAsset(BaseAsset[SimpleAssetMetaData, AssetData]):
    """
    A one time Asset. It gets only persisted once.
    """

    @classmethod
    def meta_type(cls) -> Type[SimpleAssetMetaData]:
        return SimpleAssetMetaData

    @classmethod
    def data_type(cls) -> Type[AssetData]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    def set_default_meta(self) -> SimpleAssetMetaData:
        """
        Initialize the default metadata for this asset.

        Returns a new instance of MetaBase with default values.

        Returns:
            MetaBase: The default metadata for this asset.
        """
        return SimpleAssetMetaData()

    def execute_transformation(self) -> AssetData:
        """
        Execute the transformation to generate this asset's data.

        Calls the transformation function associated with this asset to generate or transform the data.

        Returns:
            AssetData: The generated or transformed data for this asset.
        """
        return self.transformation()

    def can_materialize(self) -> bool:
        """
        Check if this asset can be materialized.

        Determines whether the asset can proceed with materialization based on its current metadata status.
        The asset cannot be materialized if it is already in progress or has successfully been persisted.

        Returns:
            bool: True if the asset can be materialized, False otherwise.
        """

        self.load_meta()

        if self.meta.blocked():
            return False

        if self.meta.has_materialized():
            return False

        return True
