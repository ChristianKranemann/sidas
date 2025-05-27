import types
from dataclasses import dataclass
from pathlib import Path
from typing import Type

import pytest
from polars._typing import SchemaDict
from polars.datatypes import Int32, String

from sidas.extensions.assets import SimpleAsset
from sidas.extensions.data_persisters.dataclass_persister import (
    DataclassPersister,
    DataclassPersisterDBResource,
    DataclassPersisterFileResource,
)
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.file import LocalFile


@dataclass
class ExampleClass:
    x: int


NO_SCHEMA = None
MATCHING_SCHEMA: SchemaDict = {"a": Int32}
EXTENDING_SCHEMA: SchemaDict = {"a": Int32, "b": String}


@pytest.fixture()
def csv_persister(tmp_path: Path) -> DataclassPersister:
    file = LocalFile(tmp_path)
    resource = DataclassPersisterFileResource(file, "csv")
    persister = DataclassPersister(resource)
    return persister


@pytest.fixture()
def parquet_persister(tmp_path: Path) -> DataclassPersister:
    file = LocalFile(tmp_path)
    resource = DataclassPersisterFileResource(file, "parquet")
    persister = DataclassPersister(resource)
    return persister


@pytest.fixture()
def json_persister(tmp_path: Path) -> DataclassPersister:
    file = LocalFile(tmp_path)
    resource = DataclassPersisterFileResource(file, "json")
    persister = DataclassPersister(resource)
    return persister


@pytest.fixture()
def ndjson_persister(tmp_path: Path) -> DataclassPersister:
    file = LocalFile(tmp_path)
    resource = DataclassPersisterFileResource(file, "ndjson")
    persister = DataclassPersister(resource)
    return persister


@pytest.fixture()
def db_persister(tmp_path: Path) -> DataclassPersister:
    file = SqliteResource(tmp_path / "test.db")
    resource = DataclassPersisterDBResource(file)
    persister = DataclassPersister(resource)
    return persister


@pytest.fixture()
def persisters(
    csv_persister: DataclassPersister,
    parquet_persister: DataclassPersister,
    json_persister: DataclassPersister,
    ndjson_persister: DataclassPersister,
    db_persister: DataclassPersister,
) -> list[DataclassPersister]:
    return [
        csv_persister,
        parquet_persister,
        json_persister,
        ndjson_persister,
        db_persister,
    ]


def example_asset[T](
    signature: Type[T], data: T, schema: None | SchemaDict = None
) -> SimpleAsset[T]:
    asset = types.new_class("ExampleAsset", [SimpleAsset[signature]])
    asset.data = data
    asset.schema = schema
    return asset  # type: ignore


def test_persist_no_schema(persisters: list[DataclassPersister]):
    @dataclass
    class ExampleClass:
        a: int

    data = [ExampleClass(1), ExampleClass(2)]
    save_asset = example_asset(list[ExampleClass], data, NO_SCHEMA)
    load_asset = example_asset(list[ExampleClass], [], NO_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert save_asset.data == load_asset.data


def test_persist_matching_schema(
    persisters: list[DataclassPersister],
):
    @dataclass
    class ExampleClass:
        a: int

    data = [ExampleClass(1), ExampleClass(2)]
    save_asset = example_asset(list[ExampleClass], data, MATCHING_SCHEMA)
    load_asset = example_asset(list[ExampleClass], [], MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert save_asset.data == load_asset.data


def test_persist_extending_schema(
    persisters: list[DataclassPersister],
):
    @dataclass
    class ExampleClass:
        a: int

    data = [ExampleClass(1), ExampleClass(2)]
    save_asset = example_asset(list[ExampleClass], data, EXTENDING_SCHEMA)
    load_asset = example_asset(list[ExampleClass], [], EXTENDING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert save_asset.data == load_asset.data


def test_persist_reducing_schema(
    persisters: list[DataclassPersister],
):
    @dataclass
    class ExampleClass:
        a: int
        b: None | str

    data = [ExampleClass(1, "x"), ExampleClass(2, "x")]
    save_asset = example_asset(list[ExampleClass], data, MATCHING_SCHEMA)
    load_asset = example_asset(list[ExampleClass], [], MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert load_asset.data == [ExampleClass(1, None), ExampleClass(2, None)]
