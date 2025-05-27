import types
from pathlib import Path
from typing import Any

import polars as pl
import pytest
from polars._typing import SchemaDict  # type: ignore
from polars.datatypes import Int64, String

from sidas.extensions.assets import SimpleAsset
from sidas.extensions.data_persisters.polars_persister import (
    PolarsPersister,
    PolarsPersisterDBResource,
    PolarsPersisterFileResource,
)
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.file import LocalFile

NO_SCHEMA = None
MATCHING_SCHEMA: SchemaDict = {"a": Int64}
EXTENDING_SCHEMA: SchemaDict = {"a": Int64, "b": String}


@pytest.fixture()
def csv_persister(tmp_path: Path) -> PolarsPersister:
    file = LocalFile(tmp_path)
    resource = PolarsPersisterFileResource(file, "csv")
    persister = PolarsPersister(resource)
    return persister


@pytest.fixture()
def parquet_persister(tmp_path: Path) -> PolarsPersister:
    file = LocalFile(tmp_path)
    resource = PolarsPersisterFileResource(file, "parquet")
    persister = PolarsPersister(resource)
    return persister


@pytest.fixture()
def json_persister(tmp_path: Path) -> PolarsPersister:
    file = LocalFile(tmp_path)
    resource = PolarsPersisterFileResource(file, "json")
    persister = PolarsPersister(resource)
    return persister


@pytest.fixture()
def ndjson_persister(tmp_path: Path) -> PolarsPersister:
    file = LocalFile(tmp_path)
    resource = PolarsPersisterFileResource(file, "ndjson")
    persister = PolarsPersister(resource)
    return persister


@pytest.fixture()
def db_persister(tmp_path: Path) -> PolarsPersister:
    file = SqliteResource(tmp_path / "test.db")
    resource = PolarsPersisterDBResource(file)
    persister = PolarsPersister(resource)
    return persister


@pytest.fixture()
def persisters(
    csv_persister: PolarsPersister,
    parquet_persister: PolarsPersister,
    json_persister: PolarsPersister,
    ndjson_persister: PolarsPersister,
    db_persister: PolarsPersister,
) -> list[PolarsPersister]:
    return [
        csv_persister,
        parquet_persister,
        json_persister,
        ndjson_persister,
        db_persister,
    ]


def example_asset(
    data: dict[str, list[Any]] | None, schema: None | SchemaDict = None
) -> SimpleAsset[pl.DataFrame]:
    asset = types.new_class("ExampleAsset", [SimpleAsset[pl.DataFrame]])
    asset.schema = schema
    if data:
        asset.data = pl.DataFrame(data)
    return asset  # type: ignore


def test_persist_no_schema(persisters: list[PolarsPersister]):
    data = {"a": [10, 20]}

    save_asset = example_asset(data, NO_SCHEMA)
    load_asset = example_asset({}, NO_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)
        assert save_asset.data.equals(load_asset.data)


def test_persist_matching_schema(
    persisters: list[PolarsPersister],
):
    data = {"a": [10, 20]}

    save_asset = example_asset(data, MATCHING_SCHEMA)
    load_asset = example_asset({}, MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)

        assert load_asset.data.equals(pl.DataFrame(data=data))


def test_persist_extending_schema(
    persisters: list[PolarsPersister],
):
    data = {"a": [10, 20]}
    expected: dict[str, Any] = {**data, "b": [None, None]}

    save_asset = example_asset(data, EXTENDING_SCHEMA)
    load_asset = example_asset({}, EXTENDING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)

        assert load_asset.data.equals(pl.DataFrame(data=expected))


def test_persist_reducing_schema(
    persisters: list[PolarsPersister],
):
    data: dict[str, Any] = {"a": [10, 20], "b": ["x", "y"]}
    expected = {"a": [10, 20]}

    save_asset = example_asset(data, MATCHING_SCHEMA)
    load_asset = example_asset({}, MATCHING_SCHEMA)

    for persister in persisters:
        persister.save(save_asset)
        persister.load(load_asset)

        assert load_asset.data.equals(pl.DataFrame(data=expected))
