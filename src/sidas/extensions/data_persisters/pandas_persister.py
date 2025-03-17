from dataclasses import dataclass
from typing import Any, Literal, Type

import pandas as pd

from ...core import (
    BaseAsset,
    DataPersister,
    MetaBase,
)
from ..resources.databases import DatabaseResource
from ..resources.file import FileResource

PandasAsset = BaseAsset[MetaBase, pd.DataFrame]


@dataclass
class PandasPersisterFileResource:
    file: FileResource
    format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"

    def save(self, asset: PandasAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)

        match self.format:
            case "csv":
                with self.file.open(path, "w") as f:
                    asset.data.to_csv(f, sep=";")

            case "parquet":
                with self.file.open(path, "wb") as f:
                    asset.data.to_parquet(f)

            case "json":
                with self.file.open(path, "w") as f:
                    asset.data.to_json(f, orient="records")

            case "ndjson":
                with self.file.open(path, "w") as f:
                    asset.data.to_json(f, orient="records", lines=True)

    def load(self, asset: PandasAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)

        match self.format:
            case "csv":
                with self.file.open(path, "r") as f:
                    asset.data = pd.read_csv(f, sep=";")

            case "parquet":
                with self.file.open(path, "rb") as f:
                    asset.data = pd.read_parquet(f)

            case "json":
                with self.file.open(path, "r") as f:
                    asset.data = pd.read_json(f, orient="records")

            case "ndjson":
                with self.file.open(path, "r") as f:
                    asset.data = pd.read_json(f, orient="records", lines=True)


@dataclass
class PandasPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"

    def save(self, asset: PandasAsset) -> None:
        name = asset.asset_id().as_path().name
        with self.db.get_connection() as con:
            asset.data.to_sql(name, con, if_exists=self.if_table_exists, index=False)

    def load(self, asset: PandasAsset) -> None:
        name = asset.asset_id().as_path().name
        with self.db.get_connection() as con:
            asset.data = pd.read_sql_table(name, con)


PandasPersisterResource = PandasPersisterFileResource | PandasPersisterDBResource


class PandasPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self, resource: PandasPersisterResource) -> None:
        self.resource = resource

    def register(
        self, asset: PandasAsset | Type[PandasAsset], *args: Any, **kwargs: Any
    ) -> None:
        self.patch_asset(asset)

    def load(self, asset: PandasAsset) -> None:
        self.resource.load(asset)

    def save(self, asset: PandasAsset) -> None:
        self.resource.save(asset)
