import logging
import os
from typing import Any

import boto3

from ....core import (
    AssetStore,
    Coordinator,
    DefaultHasMaterializerProtocol,
    MaterializeUsecase,
    MaterializeUsecaseInput,
)
from .config import (
    LAMBDA_COORDINATOR_LAMBDA_ARN,
    LAMBDA_COORDINATOR_REGION_NAME,
)
from .entities import ExecutionEvent


class LambdaCoordinator(Coordinator):
    def __init__(self) -> None:
        super().__init__()
        self.lambda_execution_arn = os.environ[LAMBDA_COORDINATOR_LAMBDA_ARN]
        self.client = boto3.client(
            "lambda", region_name=os.environ[LAMBDA_COORDINATOR_REGION_NAME]
        )
        logging.info("initialized lambda coordinator")

    def trigger_materialization(self, asset: DefaultHasMaterializerProtocol) -> None:
        logging.info(f"trigger materialization for asset: {asset.asset_id()}")
        self.client.invoke(
            FunctionName=self.lambda_execution_arn,
            InvocationType="Event",
            Payload=ExecutionEvent(asset.asset_id()).to_json(),
        )


def lambda_coordinator_materialization_handler(event: dict[str, str], context: Any):
    asset_id = ExecutionEvent.from_event(event).asset_id
    logging.info(f"materializing asset: {asset_id}")
    asset_store = AssetStore()
    asset_store.asset(asset_id).materialize()
    usecase = MaterializeUsecase(asset_store)
    data = MaterializeUsecaseInput(asset_id)
    usecase(data)
