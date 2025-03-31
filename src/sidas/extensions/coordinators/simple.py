import subprocess
from typing import Sequence

from ...core.asset import DefaultAsset
from ...core.coordinator import Coordinator


class SimpleCoordinator(Coordinator):
    def __init__(
        self,
        assets: Sequence[DefaultAsset],
    ) -> None:
        super().__init__(assets)

    def trigger_materialization(self, asset: DefaultAsset) -> None:
        asset_id = asset.asset_id()
        self.materialize(asset_id)


class SimpleThreadedCoordinator(Coordinator):
    def __init__(
        self,
        assets: Sequence[DefaultAsset],
    ) -> None:
        super().__init__(assets)

    def trigger_materialization(self, asset: DefaultAsset) -> None:
        asset_id = asset.asset_id()
        subprocess.run(["sidas", "materialize", asset_id])
