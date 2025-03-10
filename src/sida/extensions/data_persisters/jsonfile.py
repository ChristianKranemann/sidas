import json
from io import TextIOWrapper
from json import JSONEncoder
from typing import Any, Protocol, Type

import pandas as pd
from dataclasses_json import DataClassJsonMixin

from ...core import AssetId, DataPersister, DefaultAsset
from ..encoders import EnhancedJsonEncoder
from ..resources.file import FileResource


class DataHandlerProtocoll(Protocol):
    def write(self, file: TextIOWrapper, data: Any) -> None: ...

    def read(self, file: TextIOWrapper) -> Any: ...


class PandasHandler:
    def write(self, file: TextIOWrapper, data: pd.DataFrame) -> None:
        data.to_json(file, orient="records")

    def read(self, file: TextIOWrapper) -> pd.DataFrame:
        return pd.read_json(file, orient="records")


class DictListHandler:
    def __init__(self, encoder: Type[JSONEncoder] | None = EnhancedJsonEncoder) -> None:
        self.encoder = encoder

    def write(self, file: TextIOWrapper, data: list[dict[Any, Any]]) -> None:
        json.dump(data, file, cls=self.encoder)

    def read(self, file: TextIOWrapper) -> list[DataClassJsonMixin]:
        data = json.load(file)
        return data


class DataclassListHandler:
    def __init__(self, data_type: Type[DataClassJsonMixin]) -> None:
        self.data_type = data_type

    def write(self, file: TextIOWrapper, data: list[DataClassJsonMixin]) -> None:
        json_data = [d.to_dict() for d in data]
        json.dump(json_data, file)

    def read(self, file: TextIOWrapper) -> list[DataClassJsonMixin]:
        data = json.load(file)
        return [self.data_type.from_dict(l) for l in data]


class JsonFileDataPersister(DataPersister):
    def __init__(self, resource: FileResource) -> None:
        self._resource = resource
        self._handlers: dict[AssetId, DataHandlerProtocoll] = {}
        super().__init__()

    def register(
        self,
        asset: DefaultAsset | Type[DefaultAsset],
        handler: DataHandlerProtocoll,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._handlers[asset.asset_id()] = handler
        self.patch_asset(asset)

    def save(self, asset: DefaultAsset) -> None:
        asset_id = asset.asset_id()
        path = asset_id.as_path()
        handler = self._handlers[asset.asset_id()]
        with self._resource.open(path, "w") as file:
            handler.write(file, asset.data)

    def load(self, asset: DefaultAsset) -> None:
        asset_id = asset.asset_id()
        path = asset_id.as_path()
        handler = self._handlers[asset_id]
        with self._resource.open(path, "r") as file:
            asset.data = handler.read(file)
