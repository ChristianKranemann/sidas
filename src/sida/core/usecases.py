from __future__ import annotations

import logging
from dataclasses import dataclass

from .asset import AssetId
from .coordinator import Coordinator


class CoordinateUsecase:
    def __init__(
        self,
        coordinator: Coordinator,
    ) -> None:
        self.coordinator = coordinator

    def __call__(self) -> None:
        logging.info("checking assets ...")

        for asset in self.coordinator.assets:
            logging.info("checking asset %s", asset.asset_id())

            asset.hydrate()
            if not asset.can_materialize():
                continue

            logging.info("materializing asset %s", asset.asset_id())
            asset.before_materialize()
            self.coordinator.trigger_materialization(asset)


@dataclass
class MaterializeUsecaseInput:
    asset_id: AssetId


class MaterializeUsecase:
    def __init__(self, coordinator: Coordinator) -> None:
        self.coordinator = coordinator

    def __call__(self, data: MaterializeUsecaseInput) -> None:
        asset = self.coordinator.asset(data.asset_id)
        asset.hydrate()
        asset.materialize()
