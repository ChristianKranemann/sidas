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

DataclassPersistable = DataPersistableProtocol[list[dict[Any, Any]]]


@dataclass
class JsonPersisterFileResource:
    file: FileResource
    file_format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"
    strict: bool = False

    def save(self, asset: DataclassPersistable) -> None:
        path = asset.asset_id().as_path(suffix=self.file_format)
        schema = asset.schema if hasattr(asset, "schema") else None  # type: ignore
        data = pl.DataFrame(asset.data, schema=schema, strict=self.strict, orient="row")  # type: ignore

        match self.file_format:
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

    def load(self, asset: DataclassPersistable) -> None:
        path = asset.asset_id().as_path(suffix=self.file_format)
        schema: SchemaDict = asset.schema if hasattr(asset, "schema") else None  # type: ignore

        match self.file_format:
            case "csv":
                with self.file.open(path, "r") as f:
                    data = pl.read_csv(f, separator=";", schema=schema)

            case "parquet":
                with self.file.open(path, "rb") as f:
                    data = pl.read_parquet(f, schema=schema)

            case "json":
                with self.file.open(path, "r") as f:
                    data = pl.read_json(f, schema=schema)

            case "ndjson":
                with self.file.open(path, "r") as f:
                    data = pl.read_ndjson(f, schema=schema)

        asset.data = [{**d} for d in data.to_dicts()]


@dataclass
class JsonPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"
    strict: bool = False
    batch: int | None = None

    def save(self, asset: DataclassPersistable) -> None:
        name = asset.asset_id().as_path().name
        schema: SchemaDict = asset.schema if hasattr(asset, "schema") else None  # type: ignore
        data = pl.DataFrame(asset.data, schema=schema, strict=self.strict)

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

    def load(self, asset: DataclassPersistable) -> None:
        name = asset.asset_id().as_path().name
        schema: SchemaDict = asset.schema if hasattr(asset, "schema") else None  # type: ignore
        query = f'select * from "{name}";'
        with self.db.get_connection() as con:
            data = pl.read_database(query, con, schema_overrides=schema)

        asset.data = [{**d} for d in data.to_dicts()]


JsonPersisterResource = JsonPersisterFileResource | JsonPersisterDBResource


class JsonPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(self, resource: JsonPersisterResource, strict: bool = False) -> None:
        self.resource = resource

    def register(
        self, *asset: DataclassPersistable | Type[DataclassPersistable], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: DataclassPersistable) -> None:
        try:
            self.resource.save(asset)
        except Exception as e:
            raise AssetDataFailedToPersist(asset.asset_id(), e) from e

    def load(self, asset: DataclassPersistable) -> None:
        try:
            self.resource.load(asset)
        except Exception as e:
            raise AssetDataFailedToRetrieve(asset.asset_id(), e) from e
