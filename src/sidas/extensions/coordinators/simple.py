import subprocess

from ...core.asset import DefaultAsset
from ...core.coordinator import Coordinator


class SimpleCoordinator(Coordinator):
    def __init__(self, cron_expression: str | None = None) -> None:
        super().__init__(cron_expression=cron_expression)

    def trigger_materialization(self, asset: DefaultAsset) -> None:
        asset.in_trigger_materialization()
        self.materialize(asset.asset_id())


class SimpleThreadedCoordinator(Coordinator):
    def __init__(self, cron_expression: str | None = None) -> None:
        super().__init__(cron_expression=cron_expression)

    def trigger_materialization(self, asset: DefaultAsset) -> None:
        asset_id = asset.asset_id()
        subprocess.run(["sidas", "materialize", asset_id])
