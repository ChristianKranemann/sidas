from copy import copy

import polars as pl

from sidas.extensions.assets import SimpleAsset
from sidas.extensions.data_persisters.polars_persister import (
    PolarsPersister,
    PolarsPersisterDBResource,
    PolarsPersisterFileResource,
)
from sidas.extensions.meta_persisters import FileMetaPersister
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.file import InMemoryFile


class TestAsset(SimpleAsset[pl.DataFrame]):
    def transformation(self) -> pl.DataFrame:
        return pl.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})


def test_init():
    file = InMemoryFile()
    resource = PolarsPersisterFileResource(file)
    persister = PolarsPersister(resource)

    assert persister


def test_load_and_save_to_file():
    file = InMemoryFile()
    resource = PolarsPersisterFileResource(file)
    persister = PolarsPersister(resource)
    persister.register(TestAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)

    test_asset = TestAsset()
    test_asset.hydrate()

    test_asset.materialize()
    materialized = copy(test_asset.data)

    test_asset.load_data()
    assert test_asset.data.equals(materialized)

    # test if overwriting works
    test_asset.materialize()
    test_asset.load_data()
    assert test_asset.data.equals(materialized)


def test_load_and_save_to_db():
    file = InMemoryFile()
    db = SqliteResource("::memory::")
    resource = PolarsPersisterDBResource(db)
    persister = PolarsPersister(resource)
    persister.register(TestAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)

    test_asset = TestAsset()
    test_asset.hydrate()

    test_asset.materialize()
    materialized = copy(test_asset.data)

    test_asset.load_data()
    assert test_asset.data.equals(materialized)

    # test if overwriting works
    test_asset.materialize()
    test_asset.load_data()
    assert test_asset.data.equals(materialized)
