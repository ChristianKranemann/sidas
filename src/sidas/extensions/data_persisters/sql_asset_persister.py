from __future__ import annotations

from typing import Any

from sidas.core import DataPersister, DefaultAsset

from ..assets.sql_asset import SqlAsset, SqlAssetType, SqlTableAsset
from ..resources.databases import DatabaseResource


class SqlAssetPersisterInvalidAsset(Exception):
    def __init__(self, asset: DefaultAsset) -> None:
        message = f"Asset {asset.asset_id()} is not of type SqlAsset"
        super().__init__(message)


class SqlAssetPersister(DataPersister):
    def __init__(self, db: DatabaseResource) -> None:
        self._db = db
        super().__init__()

    def register(
        self,
        asset: SqlAsset | SqlAssetType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.patch_asset(asset)

    def load(self, asset: DefaultAsset) -> None:
        if not isinstance(asset, SqlAsset):
            raise SqlAssetPersisterInvalidAsset(asset)

        if isinstance(asset, SqlTableAsset):
            asset.data = asset.table_meta.tables[asset.table_name()]
            return

        asset.data = asset.get_table()

    def save(self, asset: DefaultAsset) -> None:
        if not isinstance(asset, SqlAsset):
            raise SqlAssetPersisterInvalidAsset(asset)

        # drop the table if it exists
        asset.data.drop(self._db.get_engine(), checkfirst=True)

        # if its not as sql table asset, create the table
        if not isinstance(asset, SqlTableAsset):
            asset.data.create(self._db.get_engine(), checkfirst=True)

        with self._db.get_connection() as con:
            con.execute(asset.executable)
            con.commit()
