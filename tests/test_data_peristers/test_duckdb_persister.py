import types
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pytest
from polars._typing import SchemaDict  # type: ignore
from polars.datatypes import Int64, String

from sidas.extensions.assets import SimpleAsset
from sidas.extensions.data_persisters.duckdb_persister import (
    DuckDbPersister,
    DuckDbPersisterDBResource,
    DuckDbPersisterFolderResource,
)
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.folder import LocalFolder

NO_SCHEMA = None
MATCHING_SCHEMA: SchemaDict = {"a": Int64}
EXTENDING_SCHEMA: SchemaDict = {"a": Int64, "b": String}


@pytest.fixture()
def csv_persister(tmp_path: Path) -> DuckDbPersister:
    folder = LocalFolder(tmp_path)
    resource = DuckDbPersisterFolderResource(folder, "csv")
    persister = DuckDbPersister(resource)
    return persister


@pytest.fixture()
def parquet_persister(tmp_path: Path) -> DuckDbPersister:
    folder = LocalFolder(tmp_path)
    resource = DuckDbPersisterFolderResource(folder, "parquet")
    persister = DuckDbPersister(resource)
    return persister


@pytest.fixture()
def json_persister(tmp_path: Path) -> DuckDbPersister:
    folder = LocalFolder(tmp_path)
    resource = DuckDbPersisterFolderResource(folder, "json")
    persister = DuckDbPersister(resource)
    return persister


@pytest.fixture()
def ndjson_persister(tmp_path: Path) -> DuckDbPersister:
    folder = LocalFolder(tmp_path)
    resource = DuckDbPersisterFolderResource(folder, "ndjson")
    persister = DuckDbPersister(resource)
    return persister


@pytest.fixture()
def db_persister(tmp_path: Path) -> DuckDbPersister:
    file = SqliteResource(tmp_path / "test.db")
    resource = DuckDbPersisterDBResource(file)
    persister = DuckDbPersister(resource)
    return persister


@pytest.fixture()
def persisters(
    csv_persister: DuckDbPersister,
    parquet_persister: DuckDbPersister,
    json_persister: DuckDbPersister,
    ndjson_persister: DuckDbPersister,
    db_persister: DuckDbPersister,
) -> list[DuckDbPersister]:
    return [
        csv_persister,
        parquet_persister,
        json_persister,
        ndjson_persister,
        db_persister,
    ]


def example_asset(
    data: dict[str, list[Any]] | None, schema: None | SchemaDict = None
) -> SimpleAsset[duckdb.DuckDBPyRelation]:
    asset = types.new_class("ExampleAsset", [SimpleAsset[duckdb.DuckDBPyRelation]])
    asset.schema = schema
    if data:
        _ = pd.DataFrame(data)
        asset.data = duckdb.sql("SELECT * FROM _")
    return asset  # type: ignore


def test_persist_multi_overwrite(persisters: list[DuckDbPersister]):
    save_asset_1 = example_asset({"a": [10, 20]}, NO_SCHEMA)
    save_asset_2 = example_asset({"a": [30, 40]}, NO_SCHEMA)
    load_asset = example_asset({}, NO_SCHEMA)

    for persister in persisters:
        persister.save(save_asset_1)
        persister.save(save_asset_2)
        persister.load(load_asset)

        assert save_asset_2.data.df().equals(load_asset.data.df())  # type: ignore


def test_persist_no_schema(persisters: list[DuckDbPersister]):
    data = {"a": [10, 20]}

    save_asset = example_asset(data, NO_SCHEMA)
    load_asset = example_asset({}, NO_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)

        assert save_asset.data is not None
        assert load_asset.data is not None
        assert save_asset.data.df().equals(load_asset.data.df())  # type: ignore


def test_persist_matching_schema(
    persisters: list[DuckDbPersister],
):
    data = {"a": [10, 20]}

    save_asset = example_asset(data, MATCHING_SCHEMA)
    load_asset = example_asset({}, MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert load_asset.data.df().to_dict() == pd.DataFrame(data=data).to_dict()


def test_persist_extending_schema(
    persisters: list[DuckDbPersister],
):
    data = {"a": [10, 20]}
    expected: dict[str, Any] = {**data, "b": [None, None]}

    save_asset = example_asset(data, EXTENDING_SCHEMA)
    load_asset = example_asset({}, EXTENDING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)

        assert load_asset.data.df().to_dict() == pd.DataFrame(data=expected).to_dict()


def test_persist_reducing_schema(
    persisters: list[DuckDbPersister],
):
    data: dict[str, Any] = {"a": [10, 20], "b": ["x", "y"]}
    expected = {"a": [10, 20]}

    save_asset = example_asset(data, MATCHING_SCHEMA)
    load_asset = example_asset({}, MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)

        assert load_asset.data.df().to_dict() == pd.DataFrame(data=expected).to_dict()
