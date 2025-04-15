from __future__ import annotations

from typing import Any, Type

from sqlalchemy import Table

from sidas.core import DataPersistableProtocol, DataPersister

from ..assets.sql_asset import SqlAsset, SqlTableAsset
from ..resources.databases import DatabaseResource

SqlPersistable = DataPersistableProtocol[Table]


class SqlPersisterInvalidAsset(Exception):
    def __init__(self, asset: SqlPersistable) -> None:
        message = f"Asset {asset.asset_id()} is not of type SqlAsset"
        super().__init__(message)


class SqlPersister(DataPersister):
    def __init__(self, db: DatabaseResource) -> None:
        self._db = db
        super().__init__()

    def register(
        self, *asset: SqlPersistable | Type[SqlPersistable], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def load(self, asset: SqlPersistable) -> None:
        if not isinstance(asset, SqlAsset):
            raise SqlPersisterInvalidAsset(asset)

        if isinstance(asset, SqlTableAsset):
            asset.data = asset.table_meta.tables[asset.table_name()]
            return

        asset.data = asset.get_table()

    def save(self, asset: SqlPersistable) -> None:
        if not isinstance(asset, SqlAsset):
            raise SqlPersisterInvalidAsset(asset)

        # drop the table if it exists
        asset.data.drop(self._db.get_engine(), checkfirst=True)

        # if its not as sql table asset, create the table
        if not isinstance(asset, SqlTableAsset):
            asset.data.create(self._db.get_engine(), checkfirst=True)

        with self._db.get_connection() as con:
            con.execute(asset.executable)
            con.commit()
