from typing import Sequence

from ...core.asset import DataPersister, DefaultAsset, MetaPersister
from ...core.coordinator import Coordinator
from ...core.usecases import MaterializeUsecase, MaterializeUsecaseInput


class SimpleCoordinator(Coordinator):
    def __init__(
        self,
        assets: Sequence[DefaultAsset],
        persisters: Sequence[DataPersister],
        meta: MetaPersister,
    ) -> None:
        super().__init__(assets, persisters, meta)

    def trigger_materialization(self, asset: DefaultAsset) -> None:
        usecase = MaterializeUsecase(self)
        usecase(MaterializeUsecaseInput(asset.asset_id()))

        # subprocess.run(["sida", "materialize", asset_id])
