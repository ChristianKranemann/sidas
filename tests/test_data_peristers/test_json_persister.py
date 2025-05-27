import types
from pathlib import Path
from typing import Any, Type

import pytest
from polars._typing import SchemaDict  # type: ignore
from polars.datatypes import Int32, String

from sidas.extensions.assets import SimpleAsset
from sidas.extensions.data_persisters.json_persister import (
    JsonPersister,
    JsonPersisterDBResource,
    JsonPersisterFileResource,
)
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.file import LocalFile

NO_SCHEMA = None
MATCHING_SCHEMA: SchemaDict = {"a": Int32}
EXTENDING_SCHEMA: SchemaDict = {"a": Int32, "b": String}


@pytest.fixture()
def csv_persister(tmp_path: Path) -> JsonPersister:
    file = LocalFile(tmp_path)
    resource = JsonPersisterFileResource(file, "csv")
    persister = JsonPersister(resource)
    return persister


@pytest.fixture()
def parquet_persister(tmp_path: Path) -> JsonPersister:
    file = LocalFile(tmp_path)
    resource = JsonPersisterFileResource(file, "parquet")
    persister = JsonPersister(resource)
    return persister


@pytest.fixture()
def json_persister(tmp_path: Path) -> JsonPersister:
    file = LocalFile(tmp_path)
    resource = JsonPersisterFileResource(file, "json")
    persister = JsonPersister(resource)
    return persister


@pytest.fixture()
def ndjson_persister(tmp_path: Path) -> JsonPersister:
    file = LocalFile(tmp_path)
    resource = JsonPersisterFileResource(file, "ndjson")
    persister = JsonPersister(resource)
    return persister


@pytest.fixture()
def db_persister(tmp_path: Path) -> JsonPersister:
    file = SqliteResource(tmp_path / "test.db")
    resource = JsonPersisterDBResource(file)
    persister = JsonPersister(resource)
    return persister


@pytest.fixture()
def persisters(
    csv_persister: JsonPersister,
    parquet_persister: JsonPersister,
    json_persister: JsonPersister,
    ndjson_persister: JsonPersister,
    db_persister: JsonPersister,
) -> list[JsonPersister]:
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


def test_persist_no_schema(persisters: list[JsonPersister]):
    data = [{"a": 1}, {"a": 2}]

    save_asset = example_asset(list[dict[str, int]], data, NO_SCHEMA)
    load_asset = example_asset(list[dict[str, int]], [], NO_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert save_asset.data == load_asset.data


def test_persist_matching_schema(
    persisters: list[JsonPersister],
):
    data = [{"a": 1}, {"a": 2}]

    save_asset = example_asset(list[dict[str, int]], data, MATCHING_SCHEMA)
    load_asset = example_asset(list[dict[str, int]], [], MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert save_asset.data == load_asset.data


def test_persist_extending_schema(
    persisters: list[JsonPersister],
):
    data = [{"a": 1}, {"a": 2}]
    save_asset = example_asset(list[dict[str, int]], data, EXTENDING_SCHEMA)
    load_asset = example_asset(list[dict[str, int]], [], EXTENDING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert load_asset.data == [{"a": 1, "b": None}, {"a": 2, "b": None}]


def test_persist_reducing_schema(
    persisters: list[JsonPersister],
):
    data: list[dict[str, Any]] = [{"a": 1, "b": None}, {"a": 2, "b": None}]

    save_asset = example_asset(list[dict[str, int]], data, MATCHING_SCHEMA)
    load_asset = example_asset(list[dict[str, int]], [], MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert load_asset.data == [{"a": 1}, {"a": 2}]
