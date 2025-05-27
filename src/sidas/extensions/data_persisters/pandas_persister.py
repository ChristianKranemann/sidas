from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Type

import pandas as pd
import polars as pl

from ...core import (
    AssetDataFailedToPersist,
    AssetDataFailedToRetrieve,
    DataPersistableProtocol,
    DataPersister,
)
from ..resources.databases import DatabaseResource
from ..resources.file import FileResource

if TYPE_CHECKING:
    from polars._typing import SchemaDict  # type:ignore

PandasPersistable = DataPersistableProtocol[pd.DataFrame]


@dataclass
class PandasPersisterFileResource:
    file: FileResource
    format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"

    def save(self, asset: PandasPersistable) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        data = pl.from_dataframe(asset.data)
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

    def load(self, asset: PandasPersistable) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        schema: SchemaDict = asset.schema if hasattr(asset, "schema") else None  # type: ignore
        columns = list(schema.keys()) if schema else None  # type: ignore

        match self.format:
            case "csv":
                with self.file.open(path, "r") as f:
                    data = pl.read_csv(
                        f, separator=";", schema=schema, truncate_ragged_lines=True
                    )

            case "parquet":
                with self.file.open(path, "rb") as f:
                    data = pl.read_parquet(
                        f, schema=schema, allow_missing_columns=True, columns=columns
                    )

            case "json":
                with self.file.open(path, "r") as f:
                    data = pl.read_json(f, schema=schema)

            case "ndjson":
                with self.file.open(path, "r") as f:
                    data = pl.read_ndjson(f, schema=schema)

        asset.data = data.to_pandas()


@dataclass
class PandasPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"
    batch: int | None = None

    def save(self, asset: PandasPersistable) -> None:
        name = asset.asset_id().as_path().name
        data = pl.from_dataframe(asset.data)
        chunks = [data]
        if self.batch:
            chunks = [
                data[i : i + self.batch] for i in range(0, data.height, self.batch)
            ]

        with self.db.get_connection() as con:
            first_batch = True
            for chunk in chunks:
                if first_batch:
                    chunk.write_database(
                        name, con, if_table_exists=self.if_table_exists
                    )
                    first_batch = False
                else:
                    chunk.write_database(name, con, if_table_exists="append")

        with self.db.get_connection() as con:
            data.write_database(name, con, if_table_exists=self.if_table_exists)

    def load(self, asset: PandasPersistable) -> None:
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

        asset.data = data.to_pandas()


# @dataclass
# class PandasPersisterFileResource:
#     file: FileResource
#     format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"

#     def save(self, asset: PandasPersistable) -> None:
#         path = asset.asset_id().as_path(suffix=self.format)

#         match self.format:
#             case "csv":
#                 with self.file.open(path, "w") as f:
#                     asset.data.to_csv(f, sep=";")

#             case "parquet":
#                 with self.file.open(path, "wb") as f:
#                     asset.data.to_parquet(f)

#             case "json":
#                 with self.file.open(path, "w") as f:
#                     asset.data.to_json(f, orient="records")

#             case "ndjson":
#                 with self.file.open(path, "w") as f:
#                     asset.data.to_json(f, orient="records", lines=True)

#     def load(self, asset: PandasPersistable) -> None:
#         path = asset.asset_id().as_path(suffix=self.format)

#         match self.format:
#             case "csv":
#                 with self.file.open(path, "r") as f:
#                     asset.data = pd.read_csv(f, sep=";")

#             case "parquet":
#                 with self.file.open(path, "rb") as f:
#                     asset.data = pd.read_parquet(f)

#             case "json":
#                 with self.file.open(path, "r") as f:
#                     asset.data = pd.read_json(f, orient="records")

#             case "ndjson":
#                 with self.file.open(path, "r") as f:
#                     asset.data = pd.read_json(f, orient="records", lines=True)


# @dataclass
# class PandasPersisterDBResource:
#     db: DatabaseResource
#     if_table_exists: Literal["append", "replace", "fail"] = "replace"
#     batch: int | None = None

#     def save(self, asset: PandasPersistable) -> None:
#         name = asset.asset_id().as_path().name
#         with self.db.get_connection() as con:
#             asset.data.to_sql(
#                 name,
#                 con,
#                 if_exists=self.if_table_exists,
#                 index=False,
#                 chunksize=self.batch,
#             )

#     def load(self, asset: PandasPersistable) -> None:
#         name = asset.asset_id().as_path().name
#         with self.db.get_connection() as con:
#             asset.data = pd.read_sql_table(name, con)


PandasPersisterResource = PandasPersisterFileResource | PandasPersisterDBResource


class PandasPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self, resource: PandasPersisterResource) -> None:
        self.resource = resource

    def register(
        self, *asset: PandasPersistable | Type[PandasPersistable], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: PandasPersistable) -> None:
        try:
            self.resource.save(asset)
        except Exception as e:
            raise AssetDataFailedToPersist(asset.asset_id(), e) from e

    def load(self, asset: PandasPersistable) -> None:
        try:
            self.resource.load(asset)
        except Exception as e:
            raise AssetDataFailedToRetrieve(asset.asset_id(), e) from e
