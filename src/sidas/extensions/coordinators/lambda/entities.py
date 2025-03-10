from __future__ import annotations

import json
from dataclasses import dataclass

from ....core import AssetId
from .config import LAMBDA_COORDINATOR_EVENT_KEY


@dataclass
class ExecutionEvent:
    asset_id: AssetId

    @classmethod
    def from_event(cls, event: dict[str, str]) -> ExecutionEvent:
        asset_id_str = event[LAMBDA_COORDINATOR_EVENT_KEY]
        asset_id = AssetId(asset_id_str)
        return cls(asset_id)

    def to_json(self) -> str:
        return json.dumps({LAMBDA_COORDINATOR_EVENT_KEY: self.asset_id})
