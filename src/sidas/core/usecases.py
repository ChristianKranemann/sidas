from __future__ import annotations

import logging

from .asset import AssetId
from .coordinator import Coordinator


class CoordinateUsecase:
    def __init__(
        self,
        coordinator: Coordinator,
    ) -> None:
        self.coordinator = coordinator

    def __call__(self) -> None:
        for asset in self.coordinator.assets:
            logging.info("hydrating asset %s", asset.asset_id())
            asset.hydrate()

        for asset in self.coordinator.assets:
            logging.info("checking asset %s", asset.asset_id())

            if not asset.can_materialize():
                logging.info("asset %s cant materialize", asset.asset_id())
                continue

            logging.info("materializing asset %s", asset.asset_id())
            asset.before_materialize()
            self.coordinator.trigger_materialization(asset)


class MaterializeUsecase:
    def __init__(self, coordinator: Coordinator) -> None:
        self.coordinator = coordinator

    def __call__(self, asset_id: AssetId) -> None:
        asset = self.coordinator.asset(asset_id)
        asset.hydrate()
        asset.materialize()
