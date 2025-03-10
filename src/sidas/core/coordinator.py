from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from .asset import AssetId, DataPersister, DefaultAsset, MetaPersister
from .exceptions import AssetNotFoundException
from .loader import load_assets


class Coordinator(ABC):
    """
    A class responsible for managing and coordinating the data assets.
    The coordinator can start processing, load and save asset metadata, and materialize asset value.
    """

    @staticmethod
    def load_coordinator() -> Coordinator:
        try:
            return load_assets(Coordinator)[0]
        except IndexError:
            raise Exception("Failed to load Coordinator Plugin")

    def __init__(
        self,
        assets: Sequence[DefaultAsset],
        persisters: Sequence[DataPersister],
        meta: MetaPersister,
    ) -> None:
        self.assets = assets
        self.persisters = persisters
        self.meta = meta

    @abstractmethod
    def trigger_materialization(self, asset: DefaultAsset) -> None:
        """
        Abstract method to kickoff the materialization of asset's value.
        This method should be implemented by subclasses.
        """

    def validate(self) -> None:
        for asset in self.assets:
            asset.validate()

    def asset(self, asset_id: AssetId) -> DefaultAsset:
        for asset in self.assets:
            if asset.asset_id() == asset_id:
                return asset

        raise AssetNotFoundException()
