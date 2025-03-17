from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Type, get_args

import polars as pl

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
else:
    DataclassInstance = object

from ...core import BaseAsset, DataPersister
from ..resources.databases import DatabaseResource
from ..resources.file import FileResource

DataclassAsset = BaseAsset[Any, list[Any]]


@dataclass
class DataclassPersisterFileResource:
    file: FileResource
    format: Literal["csv", "parquet", "json", "ndjson"] = "ndjson"
    strict: bool = False

    def save(self, asset: DataclassAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)
        data = pl.DataFrame(asset.data, strict=self.strict)

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

    def load(self, asset: DataclassAsset) -> None:
        path = asset.asset_id().as_path(suffix=self.format)

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

        asset_type = get_args(asset.data_type())[0]
        asset.data = [asset_type(**d) for d in data.to_dicts()]


@dataclass
class DataclassPersisterDBResource:
    db: DatabaseResource
    if_table_exists: Literal["append", "replace", "fail"] = "replace"
    strict: bool = False
    batch: int | None = None

    def save(self, asset: DataclassAsset) -> None:
        name = asset.asset_id().as_path().name
        data = pl.DataFrame(asset.data, strict=self.strict)

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

    def load(self, asset: DataclassAsset) -> None:
        name = asset.asset_id().as_path().name
        query = f"select * from {name};"
        with self.db.get_connection() as con:
            data = pl.read_database(query, con)

        asset_type = get_args(asset.data_type())[0]
        asset.data = [asset_type(**d) for d in data.to_dicts()]


DataclassPersisterResource = (
    DataclassPersisterFileResource | DataclassPersisterDBResource
)


class DataclassPersister(DataPersister):
    """
    The InMemoryDataPersister provides functionality to register, load, save,
    and directly set data for assets, using an in-memory dictionary to store the data.
    """

    def __init__(
        self, resource: DataclassPersisterResource, strict: bool = False
    ) -> None:
        self.resource = resource

    def register(
        self, asset: DataclassAsset | Type[DataclassAsset], *args: Any, **kwargs: Any
    ) -> None:
        self.patch_asset(asset)

    def load(self, asset: DataclassAsset) -> None:
        self.resource.load(asset)

    def save(self, asset: DataclassAsset) -> None:
        self.resource.save(asset)
