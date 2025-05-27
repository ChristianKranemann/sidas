from __future__ import annotations

import logging
from datetime import datetime
from typing import Type

from croniter import croniter

from ...core import AssetData, AssetMetaData, AssetStatus, BaseAsset
from ...core.exceptions import AssetDataFailedToRetrieve


class ScheduledAssetMetadata(AssetMetaData):
    """
    Metadata for scheduled assets, including the cron expression and the next scheduled time.

    Attributes:
        cron_expression (str): The cron expression defining the schedule for the asset.
        next_schedule (datetime): The next scheduled time for the asset to be materialized.
    """

    cron_expression: str
    next_schedule: datetime


class ScheduledAsset(BaseAsset[ScheduledAssetMetadata, AssetData]):
    """
    An asset that is scheduled to be materialized based on a cron expression.

    Attributes:
        cron_expression (str): The cron expression defining the schedule for the asset.
    """

    data: AssetData
    # transformation: Callable[..., Any]
    cron_expression: str

    @classmethod
    def meta_type(cls) -> Type[ScheduledAssetMetadata]:
        return ScheduledAssetMetadata

    @classmethod
    def data_type(cls) -> Type[AssetData]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    def set_default_meta(self) -> ScheduledAssetMetadata:
        """
        Sets the default metadata for the scheduled asset.

        Returns:
            ScheduledAssetMetadata: The default metadata for the scheduled asset.
        """
        return ScheduledAssetMetadata(
            cron_expression=self.cron_expression, next_schedule=datetime.now()
        )

    def can_materialize(self) -> bool:
        """
        Determines whether the scheduled asset can be materialized.

        The asset can be materialized if:
        - It is not currently in progress.
        - The current time is equal to or past the next scheduled time.

        Returns:
            bool: True if the asset can be materialized, False otherwise.
        """
        self.load_meta()

        # skip if asset is is initializing or could not initialize
        if self.meta.status in (
            AssetStatus.INITIALIZING,
            AssetStatus.INITIALIZING_FAILED,
        ):
            return False

        # skip if asset is materializing
        if self.meta.in_progress():
            logging.info("can't materialize: materialization in progress")
            return False

        # if the asset has not materialized, do so now:
        # update the next schedule
        if not self.meta.has_persisted():
            logging.info("asset not materialized yet, can materialize")
            return True

        # skip if next schedule is in the future
        if datetime.now() < self.meta.next_schedule:
            logging.info("can't materialize: materialization not yet scheduled")
            return False

        return True

    def after_materialize(self) -> None:
        """
        If materialization was successfull, update the schedule.
        """
        self.load_meta()
        if self.meta.has_persisted():
            cron_iterator = croniter(self.cron_expression)
            self.meta.next_schedule = cron_iterator.next(datetime)
            self.save_meta()


class CumulatingScheduledAsset(ScheduledAsset[AssetData]):
    """
    A scheduled asset that preserves and accumulates state between materializations.
    Combines the time-based execution of ScheduledAsset with state preservation,
    allowing each transformation to build upon previous results.

    Attributes:
        initial_data (AssetData): Base state used for the first materialization
        cron_expression (str): Schedule for materialization in cron format
    """

    initial_data: AssetData

    @classmethod
    def meta_type(cls) -> Type[ScheduledAssetMetadata]:
        return ScheduledAssetMetadata

    @classmethod
    def data_type(cls) -> Type[AssetData]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    def before_materialize(self) -> None:
        """
        Loads previous state or uses initial_data if none exists, then executes
        the scheduled transformation
        """
        super().before_materialize()

        try:
            self.load_data()
        except AssetDataFailedToRetrieve:
            self.data = self.initial_data
