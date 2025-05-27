from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Type

from .asset import AssetId, DefaultAsset
from .exceptions import (
    AssetNotFoundException,
    CoordinatorNotRegisteredInMetaPersister,
    MetaDataFailedToRetrieve,
)
from .loader import load_assets
from .meta import CoordinatorMetaData, CoordinatorStatus


class Coordinator(ABC):
    """
    A class responsible for managing and coordinating the data assets.
    The coordinator can start processing, load and save asset metadata, and materialize asset value.
    """

    @classmethod
    def asset_id(cls) -> AssetId:
        return AssetId("Coordinator")

    @classmethod
    def meta_type(cls) -> Type[CoordinatorMetaData]:
        return CoordinatorMetaData

    @staticmethod
    def load_coordinator() -> Coordinator:
        try:
            return load_assets(Coordinator)[0]
        except IndexError:
            raise Exception("Failed to load Coordinator Plugin")

    meta: CoordinatorMetaData

    def __init__(self, cron_expression: str | None = None) -> None:
        self.assets: list[DefaultAsset] = []
        self.cron_expression = cron_expression or "*/30 * * * * *"

    def register(self, *assets: DefaultAsset) -> None:
        for asset in assets:
            self.assets.append(asset)

    def load_meta(self) -> None:
        raise CoordinatorNotRegisteredInMetaPersister()

    def save_meta(self) -> None:
        raise CoordinatorNotRegisteredInMetaPersister()

    def initialize(self) -> CoordinatorStatus:
        try:
            self.load_meta()
        except MetaDataFailedToRetrieve:
            self.meta = CoordinatorMetaData(cron_expression=self.cron_expression)
            self.save_meta()

        try:
            for asset in self.assets:
                asset.initialize()
        except Exception as e:
            msg = f"Error validating assets: {e}"
            self.meta.update_status(CoordinatorStatus.INITIALIZING_FAILED)
            self.meta.update_log(msg)
            self.save_meta()
            logging.exception(msg)
            return CoordinatorStatus.INITIALIZING_FAILED

        self.meta.update_status(CoordinatorStatus.INITIALIZED)
        self.save_meta()
        return CoordinatorStatus.INITIALIZED

    def asset(self, asset_id: AssetId) -> DefaultAsset:
        for asset in self.assets:
            if asset.asset_id() == asset_id:
                return asset

        raise AssetNotFoundException(asset_id)

    @abstractmethod
    def trigger_materialization(self, asset: DefaultAsset) -> None:
        """
        Abstract method to kickoff the materialization of asset's value.
        This method should be implemented by subclasses.
        """

    def process_assets(self) -> CoordinatorStatus:
        self.load_meta()
        self.meta.update_status(CoordinatorStatus.PROCESSING)
        self.save_meta()

        try:
            for asset in self.assets:
                logging.info("checking asset %s", asset.asset_id())

                if not asset.can_materialize():
                    logging.info("asset %s cant materialize", asset.asset_id())
                    continue

                logging.info("materializing asset %s", asset.asset_id())
                self.trigger_materialization(asset)
        except Exception as e:
            msg = f"Error processing assets: {e}"
            self.meta.update_status(CoordinatorStatus.PROCESSING_FAILED)
            self.meta.update_log(msg)
            self.save_meta()
            logging.exception(msg)
            return CoordinatorStatus.PROCESSING_FAILED

        self.meta.update_status(CoordinatorStatus.PROCESSED)
        self.meta.update_next_schedule()
        self.save_meta()
        return CoordinatorStatus.PROCESSED

    def materialize(self, asset_id: AssetId) -> None:
        self.load_meta()
        if self.meta.terminating():
            return

        asset = self.asset(asset_id)
        asset.before_materialize()
        asset.materialize()
        asset.after_materialize()

    def run(self) -> None:
        status = self.initialize()
        if status != CoordinatorStatus.INITIALIZED:
            self.meta.terminate()

        while not self.meta.terminating():
            if datetime.now() >= self.meta.next_schedule:
                self.process_assets()
                self.meta.update_status(CoordinatorStatus.WAITING)
                self.save_meta()

            time.sleep(10)
            self.load_meta()

        self.meta.update_status(CoordinatorStatus.TERMINATED)
        self.save_meta()
        return
