import duckdb
import pandas as pd

from sidas.extensions.assets import DownstreamAsset, SimpleAsset
from sidas.extensions.data_persisters.duckdb_persister import (
    DuckDbPersister,
    DuckDbPersisterDBResource,
    DuckDbPersisterFileResource,
)
from sidas.extensions.meta_persisters import FileMetaPersister
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.file import InMemoryFile


class TestAsset(SimpleAsset[duckdb.DuckDBPyRelation]):
    def transformation(self) -> duckdb.DuckDBPyRelation:
        pandas_df = pd.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})
        return duckdb.sql("SELECT * FROM pandas_df")


class DependentAsset(DownstreamAsset[duckdb.DuckDBPyRelation]):
    def transformation(self, ta: TestAsset) -> duckdb.DuckDBPyRelation:
        return duckdb.sql("SELECT a * 2 as a2, b * 3 as b3 FROM TestAsset")


def test_init():
    file = InMemoryFile()
    resource = DuckDbPersisterFileResource(file)
    persister = DuckDbPersister(resource)

    assert persister


def test_load_and_save_to_file():
    file = InMemoryFile()
    resource = DuckDbPersisterFileResource(file)
    persister = DuckDbPersister(resource)
    persister.register(TestAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)

    test_asset = TestAsset()
    test_asset.hydrate()

    test_asset.materialize()
    test_asset.load_data()


def test_load_and_save_downstream_to_file():
    file = InMemoryFile()
    resource = DuckDbPersisterFileResource(file)
    persister = DuckDbPersister(resource)
    persister.register(TestAsset)
    persister.register(DependentAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)
    meta_persister.register(DependentAsset)

    test_asset_1 = TestAsset()
    test_asset_1.hydrate()
    test_asset_2 = DependentAsset()
    test_asset_2.hydrate()

    test_asset_1.materialize()
    test_asset_1.load_data()

    # test if overwriting works
    test_asset_2.materialize()
    test_asset_2.load_data()


def test_load_and_save_to_db(tmp_path):
    file = InMemoryFile()
    db = SqliteResource(tmp_path / "test.db")
    resource = DuckDbPersisterDBResource(db)
    persister = DuckDbPersister(resource)
    persister.register(TestAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)

    test_asset = TestAsset()
    test_asset.hydrate()

    test_asset.materialize()
    test_asset.load_data()

    # test if overwriting works
    test_asset.materialize()
    test_asset.load_data()


def test_load_and_save_downstream_to_db(tmp_path):
    file = InMemoryFile()
    db = SqliteResource(tmp_path / "test.db")
    resource = DuckDbPersisterDBResource(db)
    persister = DuckDbPersister(resource)
    persister.register(TestAsset)
    persister.register(DependentAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)
    meta_persister.register(DependentAsset)

    test_asset_1 = TestAsset()
    test_asset_1.hydrate()
    test_asset_2 = DependentAsset()
    test_asset_2.hydrate()

    test_asset_1.materialize()
    test_asset_1.load_data()

    # test if overwriting works
    test_asset_2.materialize()
    test_asset_2.load_data()
