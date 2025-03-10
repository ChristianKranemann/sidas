from sqlalchemy import (
    Column,
    Executable,
    Integer,
    MetaData,
    Selectable,
    String,
    insert,
    select,
)

from sidas.extensions.assets.sql_asset import SqlSimpleAsset, SqlTableAsset
from sidas.extensions.data_persisters.sql_asset_persister import (
    SqlAssetPersister,
)
from sidas.extensions.meta_persisters import InMemoryMetaPersister
from sidas.extensions.resources.databases import SqliteResource

metadata = MetaData()


class A(SqlSimpleAsset):
    # overwrite_table_name = "A"
    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("code", String),
    ]

    def transformation(self) -> Executable:
        query = insert(self.data).values([{"code": "a1"}, {"code": "b2"}])
        return query


class B(SqlTableAsset):
    overwrite_table_name = "X"
    table_meta = metadata

    def transformation(self, a: A) -> Selectable:
        return select(a.data.c.id, a.data.c.code.label("newcode"))


def test_sql_table_asset():
    dbm = InMemoryMetaPersister()
    dbm.register(A, B)

    db = SqliteResource("./test.db")

    dp = SqlAssetPersister(db)
    dp.register(A)
    dp.register(B)

    a = A()
    a.hydrate()
    a.materialize()

    b = B()
    b.hydrate()
    b.materialize()
