from dataclasses import dataclass
from typing import Any, Literal, Type

import polars as pl

from ...core import (
    BaseAsset,
    DataPersister,
    MetaBase,
)
from ..resources.databases import DatabaseResource
from ..resources.file import FileResource

PolarsAsset = BaseAsset[MetaBase, pl.DataFrame]


@dataclass
class PolarsPersisterFileResource:
    file: FileResource
    format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"

    def save(self, asset: PolarsAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)

        match self.format:
            case "csv":
                with self.file.open(path, "w") as f:
                    asset.data.write_csv(f, separator=";")

            case "parquet":
                with self.file.open(path, "wb") as f:
                    asset.data.write_parquet(f)

            case "json":
                with self.file.open(path, "w") as f:
                    asset.data.write_json(f)

            case "ndjson":
                with self.file.open(path, "w") as f:
                    asset.data.write_ndjson(f)

    def load(self, asset: PolarsAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)

        match self.format:
            case "csv":
                with self.file.open(path, "r") as f:
                    asset.data = pl.read_csv(f, separator=";")

            case "parquet":
                with self.file.open(path, "rb") as f:
                    asset.data = pl.write_parquet(f)

            case "json":
                with self.file.open(path, "r") as f:
                    asset.data = pl.read_json(f)

            case "ndjson":
                with self.file.open(path, "r") as f:
                    asset.data = pl.read_ndjson(f)


@dataclass
class PolarsPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"

    def save(self, asset: PolarsAsset) -> None:
        name = asset.asset_id().as_path().name
        with self.db.get_connection() as con:
            asset.data.write_database(name, con, if_table_exists=self.if_table_exists)

    def load(self, asset: PolarsAsset) -> None:
        name = asset.asset_id().as_path().name
        query = f"select * from {name};"
        with self.db.get_connection() as con:
            asset.data = pl.read_database(query, con)


PolarsPersisterResource = PolarsPersisterFileResource | PolarsPersisterDBResource


class PolarsPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self, resource: PolarsPersisterResource) -> None:
        self.resource = resource

    def register(
        self, asset: PolarsAsset | Type[PolarsAsset], *args: Any, **kwargs: Any
    ) -> None:
        self.patch_asset(asset)

    def load(self, asset: PolarsAsset) -> None:
        self.resource.load(asset)

    def save(self, asset: PolarsAsset) -> None:
        self.resource.save(asset)
