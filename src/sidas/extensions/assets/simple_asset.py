from __future__ import annotations

from typing import Type

from ...core import AssetData, AssetStatus, BaseAsset, MetaBase


class SimpleAsset(BaseAsset[MetaBase, AssetData]):
    """
    A one time Asset. It gets only persisted once.
    """

    @classmethod
    def meta_type(cls) -> Type[MetaBase]:
        return MetaBase

    @classmethod
    def data_type(cls) -> Type[AssetData]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    def set_default_meta(self) -> MetaBase:
        """
        Initialize the default metadata for this asset.

        Returns a new instance of MetaBase with default values.

        Returns:
            MetaBase: The default metadata for this asset.
        """
        return MetaBase()

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

        if self.meta.in_progress():
            return False

        if self.meta.status == AssetStatus.PERSISTED:
            return False

        return True
