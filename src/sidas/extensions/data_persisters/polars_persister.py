from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Type

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


PolarsPersistable = DataPersistableProtocol[pl.DataFrame]


@dataclass
class PolarsPersisterFileResource:
    file: FileResource
    format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"

    def save(self, asset: PolarsPersistable) -> None:
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

    def load(self, asset: PolarsPersistable) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        schema: SchemaDict = asset.schema if hasattr(asset, "schema") else None  # type: ignore
        columns = list(schema.keys()) if schema else None  # type: ignore

        match self.format:
            case "csv":
                with self.file.open(path, "r") as f:
                    asset.data = pl.read_csv(
                        f, separator=";", schema=schema, truncate_ragged_lines=True
                    )

            case "parquet":
                with self.file.open(path, "rb") as f:
                    asset.data = pl.read_parquet(
                        f, schema=schema, allow_missing_columns=True, columns=columns
                    )

            case "json":
                with self.file.open(path, "r") as f:
                    asset.data = pl.read_json(f, schema=schema)

            case "ndjson":
                with self.file.open(path, "r") as f:
                    asset.data = pl.read_ndjson(f, schema=schema)


@dataclass
class PolarsPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"
    batch: int | None = None

    def save(self, asset: PolarsPersistable) -> None:
        name = asset.asset_id().as_path().name
        chunks = [asset.data]
        if self.batch:
            chunks = [
                asset.data[i : i + self.batch]
                for i in range(0, asset.data.height, self.batch)
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
            asset.data.write_database(name, con, if_table_exists=self.if_table_exists)

    def load(self, asset: PolarsPersistable) -> None:
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

        asset.data = data


PolarsPersisterResource = PolarsPersisterFileResource | PolarsPersisterDBResource


class PolarsPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self, resource: PolarsPersisterResource) -> None:
        self.resource = resource

    def register(
        self, *asset: PolarsPersistable | Type[PolarsPersistable], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: PolarsPersistable) -> None:
        try:
            self.resource.save(asset)
        except Exception as e:
            raise AssetDataFailedToPersist(asset.asset_id(), e) from e

    def load(self, asset: PolarsPersistable) -> None:
        try:
            self.resource.load(asset)
        except Exception as e:
            raise AssetDataFailedToRetrieve(asset.asset_id(), e) from e
