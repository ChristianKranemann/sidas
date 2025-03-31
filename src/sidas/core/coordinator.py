from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

from .asset import AssetId, DefaultAsset
from .exceptions import (
    AssetNotFoundException,
    CoordinatorNotRegisteredInMetaPersister,
    MetaDataNotStoredException,
)
from .loader import load_assets
from .meta import CoordinatorMetaData, CoordinatorStatus


class Coordinator(ABC):
    """
    A class responsible for managing and coordinating the data assets.
    The coordinator can start processing, load and save asset metadata, and materialize asset value.
    """

    meta: CoordinatorMetaData
    asset_id = AssetId("Coordinator")

    @staticmethod
    def load_coordinator() -> Coordinator:
        try:
            return load_assets(Coordinator)[0]
        except IndexError:
            raise Exception("Failed to load Coordinator Plugin")

    def __init__(
        self, assets: Sequence[DefaultAsset], cron_expression: str | None = None
    ) -> None:
        self.assets = assets
        self.cron_expression = cron_expression or "*/30 * * * * *"

    def set_default_meta(self) -> CoordinatorMetaData:
        return CoordinatorMetaData(
            cron_expression=self.cron_expression, next_schedule=datetime.now()
        )

    def load_meta(self) -> None:
        raise CoordinatorNotRegisteredInMetaPersister()

    def save_meta(self) -> None:
        raise CoordinatorNotRegisteredInMetaPersister()

    def hydrate(self) -> None:
        try:
            self.load_meta()
        except MetaDataNotStoredException:
            self.meta = self.set_default_meta()
            self.save_meta()

    def asset(self, asset_id: AssetId) -> DefaultAsset:
        for asset in self.assets:
            if asset.asset_id() == asset_id:
                return asset

        raise AssetNotFoundException()

    @abstractmethod
    def trigger_materialization(self, asset: DefaultAsset) -> None:
        """
        Abstract method to kickoff the materialization of asset's value.
        This method should be implemented by subclasses.
        """

    def validate_assets(self) -> None:
        for asset in self.assets:
            asset.validate()

    def hydrate_assets(self) -> None:
        for asset in self.assets:
            logging.info("hydrating asset %s", asset.asset_id())
            asset.hydrate()

    def process_assets(self) -> None:
        for asset in self.assets:
            logging.info("checking asset %s", asset.asset_id())

            if not asset.can_materialize():
                logging.info("asset %s cant materialize", asset.asset_id())
                continue

            logging.info("materializing asset %s", asset.asset_id())
            asset.before_materialize()
            self.trigger_materialization(asset)

    def materialize(self, asset_id: AssetId) -> None:
        asset = self.asset(asset_id)
        asset.hydrate()
        asset.materialize()

    def run(self) -> None:
        self.hydrate()

        try:
            self.validate_assets()
            self.meta.update_status(CoordinatorStatus.INITIALIZED)
            self.save_meta()
        except Exception as e:
            msg = f"Error validating assets: {e}"
            self.meta.update_status(CoordinatorStatus.INITIALIZING_FAILED)
            self.meta.update_log(msg)
            self.save_meta()
            return

        self.meta.update_status(CoordinatorStatus.HYDRATING)
        self.save_meta()
        try:
            self.hydrate_assets()
            self.meta.update_status(CoordinatorStatus.HYDRATED)
            self.save_meta()
        except Exception as e:
            msg = f"Error hydrating assets: {e}"
            self.meta.update_status(CoordinatorStatus.HYDRATING_FAILED)
            self.meta.update_log(msg)
            self.save_meta()
            return

        while self.meta.status != CoordinatorStatus.TERMINATING:
            if datetime.now() >= self.meta.next_schedule:
                self.meta.update_status(CoordinatorStatus.PROCESSING)
                self.save_meta()

                try:
                    self.process_assets()

                    # iterated through all assets without error, update the schedule
                    self.meta.update_next_schedule()
                    self.meta.update_status(CoordinatorStatus.PROCESSED)
                    self.save_meta()

                except Exception as e:
                    msg = f"Error processing assets: {e}"
                    self.meta.update_status(CoordinatorStatus.PROCESSING_FAILED)
                    self.meta.update_log(msg)
                    self.save_meta()

            time.sleep(10)
            self.load_meta()

        self.meta.update_status(CoordinatorStatus.TERMINATED)
        self.save_meta()
        return
