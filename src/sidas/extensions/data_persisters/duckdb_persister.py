from dataclasses import dataclass
from typing import Any, Literal, Type

import duckdb
import polars as pl

from ...core import (
    BaseAsset,
    DataPersister,
    MetaBase,
)
from ..resources.databases import DatabaseResource
from ..resources.file import FileResource

DuckDbAsset = BaseAsset[MetaBase, duckdb.DuckDBPyRelation]


@dataclass
class DuckDbPersisterFileResource:
    file: FileResource
    format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"

    def save(self, asset: DuckDbAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        data = asset.data.pl()

        match self.format:
            case "csv":
                with self.file.open(path, "w") as f:
                    data.write_csv(f, separator=";")

            case "parquet":
                with self.file.open(path, "wb") as f:
                    data.write_parquet(f)

            case "json":
                with self.file.open(path, "w") as f:
                    data.write_json(f)

            case "ndjson":
                with self.file.open(path, "w") as f:
                    data.write_ndjson(f)

    def load(self, asset: DuckDbAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        name = asset.asset_id().as_path().name
        match self.format:
            case "csv":
                with self.file.open(path, "r") as f:
                    data = pl.read_csv(f, separator=";")

            case "parquet":
                with self.file.open(path, "rb") as f:
                    data = pl.write_parquet(f)

            case "json":
                with self.file.open(path, "r") as f:
                    data = pl.read_json(f)

            case "ndjson":
                with self.file.open(path, "r") as f:
                    data = pl.read_ndjson(f)

        try:
            asset.data = duckdb.sql(f"create table {name} as select * from data")
        except duckdb.CatalogException:
            asset.data = duckdb.sql("select * from data")


@dataclass
class DuckDbPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"

    def save(self, asset: DuckDbAsset) -> None:
        name = asset.asset_id().as_path().name
        data = asset.data.pl()
        with self.db.get_connection() as con:
            data.write_database(name, con, if_table_exists=self.if_table_exists)

    def load(self, asset: DuckDbAsset) -> None:
        name = asset.asset_id().as_path().name
        query = f"select * from {name};"
        with self.db.get_connection() as con:
            data = pl.read_database(query, con)

        try:
            asset.data = duckdb.sql(f"create table {name} as select * from data")
        except duckdb.CatalogException:
            asset.data = duckdb.sql("select * from data")


DuckDbPersisterResource = DuckDbPersisterFileResource | DuckDbPersisterDBResource


class DuckDbPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self, resource: DuckDbPersisterResource) -> None:
        self.resource = resource

    def register(
        self, asset: DuckDbAsset | Type[DuckDbAsset], *args: Any, **kwargs: Any
    ) -> None:
        self.patch_asset(asset)

    def load(self, asset: DuckDbAsset) -> None:
        self.resource.load(asset)

    def save(self, asset: DuckDbAsset) -> None:
        self.resource.save(asset)
