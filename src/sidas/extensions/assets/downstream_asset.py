from __future__ import annotations

import logging
from datetime import datetime
from enum import StrEnum
from typing import Any, Callable, Type, cast, get_type_hints

from ...core import (
    AssetData,
    AssetDataFailedToRetrieve,
    AssetMetaData,
    BaseAsset,
)

UpstreamAssetType = BaseAsset[AssetMetaData, Any]


class DownstreamAssetMetadata(AssetMetaData):
    """
    Contains metadata for downstream assets, detailing upstream dependencies and the refresh method.

    Attributes:
        upstream (list[str]): Identifiers of upstream assets.
        refresh_method (str): Strategy to refresh the asset.
    """

    upstream: list[str]
    refresh_method: str


class DownstreamAssetRefreshMethod(StrEnum):
    """
    Specifies the refresh strategies for downstream assets.

    Attributes:
        ALL_UPSTREAM_REFRESHED: Refresh when all upstream assets have been refreshed.
        ANY_UPSTREAM_REFRESHED: Refresh when at least one upstream asset has been refreshed.
    """

    ALL_UPSTREAM_REFRESHED = "ALL_UPSTREAM_REFRESHED"
    ANY_UPSTREAM_REFRESHED = "ANY_UPSTREAM_REFRESHED"


class DownstreamAsset(BaseAsset[DownstreamAssetMetadata, AssetData]):
    """
    Represents a downstream asset dependent on upstream assets for data.

    Attributes:
        refresh_method (DownstreamAssetRefreshMethod): Strategy for asset refresh. Default: ALL_UPSTREAM_REFRESHED
    """

    data: AssetData
    transformation: Callable[..., Any]
    refresh_method: DownstreamAssetRefreshMethod = (
        DownstreamAssetRefreshMethod.ALL_UPSTREAM_REFRESHED
    )

    @classmethod
    def meta_type(cls) -> Type[DownstreamAssetMetadata]:
        return DownstreamAssetMetadata

    @classmethod
    def data_type(cls) -> Type[AssetData]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    def upstream(self) -> list[UpstreamAssetType]:
        """
        Retrieves the upstream assets on which this asset depends.

        Returns:
            list[UpstreamAssetType]: The list of upstream assets.
        """
        hints = get_type_hints(self.transformation)
        hints.pop("return")
        classes = cast(list[Type[UpstreamAssetType]], list(hints.values()))
        return [self.assets[c.asset_id()] for c in classes]

    def set_default_meta(self) -> DownstreamAssetMetadata:
        """
        Sets the default metadata for the downstream asset.

        Returns:
            DownstreamAssetMetadata: The default metadata for the downstream asset.
        """
        return DownstreamAssetMetadata(
            upstream=[str(a.asset_id()) for a in self.upstream()],
            refresh_method=self.refresh_method,
        )

    def can_materialize(self) -> bool:
        """
        Checks if the downstream asset is ready to be materialized.

        The asset can be materialized if:
        - It is not currently in progress.
        - All upstream assets have been materialized.
        - The asset has not been materialized yet.
        - The upstream assets have been refreshed since the last materialization of this asset,
          based on the refresh method (ALL_UPSTREAM_REFRESHED or ANY_UPSTREAM_REFRESHED).

        Returns:
            bool: True if the asset can be materialized, False otherwise.
        """
        self.load_meta()

        # skip if asset is materializing
        if self.meta.blocked():
            logging.info("can't materialize: materialization in progress")
            return False

        upstream = self.upstream()
        upstream_meta = [u.meta for u in upstream]

        # skip if any upstream have not persisted
        upstream_persisted = [u.meta.has_materialized() for u in upstream]
        if not all(upstream_persisted):
            logging.info("can't materialize: some upstream assets are not persisted")
            return False

        # if the asset has not materialized, do so now:
        if not self.meta.has_materialized():
            logging.info("asset not materialized yet, can materialize")
            return True

        # else check if the upstream materialization dates are new enough
        # we know that the materializing_started_at and persisted_at are set
        # because we did the asset status checks obove
        upstream_materialized_at = [
            m.materializing_stopped_at
            for m in upstream_meta
            if m.materializing_stopped_at is not None
        ]
        this_last_persisted = cast(datetime, self.meta.materializing_stopped_at)
        is_newer = [this_last_persisted < t for t in upstream_materialized_at]

        if self.refresh_method == DownstreamAssetRefreshMethod.ALL_UPSTREAM_REFRESHED:
            if not all(is_newer):
                logging.info(
                    "can't materialize: at least one uppstream asset has not refreshed"
                )
                return False
            return True

        if self.refresh_method == DownstreamAssetRefreshMethod.ANY_UPSTREAM_REFRESHED:
            if not any(is_newer):
                logging.info("can't materialize: no upstream asets have refreshed")
                return False
            return True

        return True

    def before_materialize(self) -> None:
        """
        Ensuring all upstream assets are loaded.
        """
        super().before_materialize()

        self.transformation_args = tuple(self.upstream())
        for asset in self.transformation_args:
            asset.load_data()


class CumulatingDownstreamAsset(DownstreamAsset[AssetData]):
    """
    An asset that accumulates data from upstream assets.
    Unlike DownstreamAsset which only processes current upstream data, CummulatingAsset
    maintains an initial state and combines it with new upstream data during transformation.

    Attributes:
        initial_data (AssetData): The initial state used when no previous data exists
    """

    initial_data: AssetData

    @classmethod
    def meta_type(cls) -> Type[DownstreamAssetMetadata]:
        return DownstreamAssetMetadata

    @classmethod
    def data_type(cls) -> Type[AssetData]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    def before_materialize(self) -> None:
        super().before_materialize()

        try:
            self.load_data()
        except AssetDataFailedToRetrieve:
            self.data = self.initial_data
