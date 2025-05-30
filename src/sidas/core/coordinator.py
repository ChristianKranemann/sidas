from __future__ import annotations

import logging
import time
import traceback
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
from .meta import AssetStatus, CoordinatorMetaData, CoordinatorStatus


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

    def process(self, asset: DefaultAsset) -> None:
        logging.info("processing asset %s", asset.asset_id())

        # Check if we can materialize. If there is an error, log it and continue
        can_materialize = False
        try:
            can_materialize = asset.can_materialize()
        except Exception as e:
            msg = f"Exception in before_materialize: {str(e)}\n{traceback.format_exc()}"
            logging.exception(msg)
            self.meta.update_log(msg)
            self.save_meta()

        if not can_materialize:
            return

        # setting the assets status to MATERIALIZING
        asset.meta.update_status(AssetStatus.MATERIALIZING)
        asset.save_meta()

        # trigger materialization. If there is an error log it and set the asset status
        # to MATERIALIZING_FAILED
        try:
            self.trigger_materialization(asset)
        except Exception as e:
            asset.meta.update_status(AssetStatus.MATERIALIZING_FAILED)
            asset.save_meta()

            msg = f"Error processing assets: {e}"
            logging.exception(msg)
            self.meta.update_log(msg)
            self.save_meta()

    def run(self) -> None:
        status = self.initialize()
        if status != CoordinatorStatus.INITIALIZED:
            self.meta.terminate()

        while not self.meta.terminating():
            if datetime.now() < self.meta.next_schedule:
                time.sleep(10)
                self.load_meta()
                continue

            self.meta.update_status(CoordinatorStatus.PROCESSING)
            self.save_meta()

            for asset in self.assets:
                self.process(asset)

            self.meta.update_status(CoordinatorStatus.WAITING)
            self.save_meta()

        self.meta.update_status(CoordinatorStatus.TERMINATED)
        self.save_meta()
        return

    def materialize(self, asset_id: AssetId) -> None:
        asset = self.asset(asset_id)
        asset.load_meta()

        try:
            asset.before_materialize()
        except Exception as e:
            asset.meta.update_status(AssetStatus.MATERIALIZING_FAILED)
            asset.save_meta()

            msg = f"Exception in before_materialize: {str(e)}\n{traceback.format_exc()}"
            logging.exception(msg)
            self.meta.update_log(msg)
            return

        try:
            asset.materialize()
        except Exception as e:
            asset.meta.update_status(AssetStatus.MATERIALIZING_FAILED)
            asset.save_meta()

            msg = f"Exception in materialize: {str(e)}\n{traceback.format_exc()}"
            logging.exception(msg)
            self.meta.update_log(msg)
            return

        try:
            asset.after_materialize()
        except Exception as e:
            asset.meta.update_status(AssetStatus.MATERIALIZING_FAILED)
            asset.save_meta()

            msg = f"Exception in after_materialize: {str(e)}\n{traceback.format_exc()}"
            logging.exception(msg)
            self.meta.update_log(msg)
