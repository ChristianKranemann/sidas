from sqlalchemy import Column, Executable, Integer, String, insert, select

from sidas.extensions.assets.sql_asset import SqlSimpleAsset, SqlTableAsset
from sidas.extensions.data_persisters.sql_asset_persister import SqlPersister
from sidas.extensions.meta_persisters import FileMetaPersister
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.file import InMemoryFile


class TestAsset(SqlSimpleAsset):
    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("a", String),
        Column("b", String),
    ]

    def transformation(self) -> Executable:
        query = insert(self.data).values(
            [{"a": 1, "b": 10}, {"a": 2, "b": 20}, {"a": 3, "b": 30}]
        )
        return query


class DependentAsset(SqlTableAsset):
    def transformation(self, ta: TestAsset) -> Executable:
        return select((ta.data.c.a * 2).label("a2"), (ta.data.c.b * 3).label("b2"))


def test_init(tmp_path):
    db = SqliteResource(tmp_path / "test.db")
    persister = SqlPersister(db)

    assert persister


def test_load_and_save_to_db(tmp_path):
    file = InMemoryFile()
    db = SqliteResource(tmp_path / "test.db")

    persister = SqlPersister(db)
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
    persister = SqlPersister(db)
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
