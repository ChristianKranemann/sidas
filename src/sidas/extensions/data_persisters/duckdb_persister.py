from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Type

import duckdb
import polars as pl

from ...core import (
    AssetDataFailedToPersist,
    AssetDataFailedToRetrieve,
    DataPersistableProtocol,
    DataPersister,
)
from ..resources.databases import DatabaseResource
from ..resources.folder import FolderResource

if TYPE_CHECKING:
    from polars._typing import SchemaDict  # type:ignore
DuckDbPersistable = DataPersistableProtocol[duckdb.DuckDBPyRelation]


@dataclass
class DuckDbPersisterFolderResource:
    folder: FolderResource
    format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"

    def save(self, asset: DuckDbPersistable) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        data = asset.data.pl()

        match self.format:
            case "csv":
                with self.folder.open(path, "w") as f:
                    data.write_csv(f, separator=";")

            case "parquet":
                with self.folder.open(path, "wb") as f:
                    data.write_parquet(f)

            case "json":
                with self.folder.open(path, "w") as f:
                    data.write_json(f)

            case "ndjson":
                with self.folder.open(path, "w") as f:
                    data.write_ndjson(f)

    def load(self, asset: DuckDbPersistable) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        name = asset.asset_id().as_path().name
        schema: SchemaDict = asset.schema if hasattr(asset, "schema") else None  # type: ignore
        columns = list(schema.keys()) if schema else None  # type: ignore

        match self.format:
            case "csv":
                with self.folder.open(path, "r") as f:
                    data = pl.read_csv(
                        f, separator=";", schema=schema, truncate_ragged_lines=True
                    )

            case "parquet":
                with self.folder.open(path, "rb") as f:
                    data = pl.read_parquet(
                        f, schema=schema, allow_missing_columns=True, columns=columns
                    )

            case "json":
                with self.folder.open(path, "r") as f:
                    data = pl.read_json(f, schema=schema)

            case "ndjson":
                with self.folder.open(path, "r") as f:
                    data = pl.read_ndjson(f, schema=schema)

        # register the data alias (only used to avoid unused variable hints)
        duckdb.register("__data__", data)

        # load the data into the asset.data
        asset.data = duckdb.sql("select * from __data__;")

        # load the dat into the duckdb context
        try:
            duckdb.sql(f"drop table {name};")
        except duckdb.CatalogException:
            pass
        duckdb.sql(f"create table {name} as select * from __data__;")


@dataclass
class DuckDbPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"

    def save(self, asset: DuckDbPersistable) -> None:
        name = asset.asset_id().as_path().name
        data = asset.data.pl()
        with self.db.get_connection() as con:
            data.write_database(name, con, if_table_exists=self.if_table_exists)

    def load(self, asset: DuckDbPersistable) -> None:
        name = asset.asset_id().as_path().name
        schema: SchemaDict = asset.schema if hasattr(asset, "schema") else None  # type: ignore
        columns = list(schema.keys()) if schema else None  # type: ignore
        query = f'select * from "{name}";'

        with self.db.get_connection() as con:
            data = pl.read_database(query, con, schema_overrides=schema)

        if columns:
            for c in data.columns:
                if c not in columns:
                    data = data.drop(c)

            for c in columns:
                if c not in data.columns:
                    data = data.with_columns(pl.lit(None).alias(c))

        # register the data alias (only used to avoid unused variable hints)
        duckdb.register("__data__", data)

        # load the data into the asset.data
        asset.data = duckdb.sql("select * from __data__;")

        # load the dat into the duckdb context
        try:
            duckdb.sql(f"drop table {name};")
        except duckdb.CatalogException:
            pass
        duckdb.sql(f"create table {name} as select * from __data__;")


DuckDbPersisterResource = DuckDbPersisterFolderResource | DuckDbPersisterDBResource


class DuckDbPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self, resource: DuckDbPersisterResource) -> None:
        self.resource = resource

    def register(
        self, *asset: DuckDbPersistable | Type[DuckDbPersistable], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: DuckDbPersistable) -> None:
        try:
            self.resource.save(asset)
        except Exception as e:
            raise AssetDataFailedToPersist(asset.asset_id(), e) from e

    def load(self, asset: DuckDbPersistable) -> None:
        try:
            self.resource.load(asset)
        except Exception as e:
            raise AssetDataFailedToRetrieve(asset.asset_id(), e) from e
