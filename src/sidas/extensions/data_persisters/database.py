from typing import Any, Literal, Protocol, TypeVar

import pandas as pd
import pandas._typing as pdt
from dataclasses_json import DataClassJsonMixin

from ...core import AssetId, DataPersister, DefaultAsset
from ..resources.databases import DatabaseResource


class DatabasePersisterMultipleSchemaDefinitionError(Exception):
    """
    Exception if a database schema has been provided on init
    but a additional schmea has been inferred from the AssedId
    """

    def __init__(self, default: str, derived: str) -> None:
        message = f"Default schema is {default} but additional schema {derived} has been derived"
        super().__init__(message)


class DataHandlerProtocoll(Protocol):
    def write(
        self, db: DatabaseResource, schema: str | None, name: str, data: Any
    ) -> None: ...

    def read(self, db: DatabaseResource, schema: str | None, name: str) -> Any: ...


IF_EXISTS = Literal["fail", "replace", "append"]
DTYPE_BACKEND = Literal["numpy_nullable", "pyarrow"]


class PandasHandler:
    def __init__(
        self,
        if_exists: IF_EXISTS = "replace",
        index: bool = True,
        index_label: pdt.IndexLabel | None = None,
        dtype: pdt.DtypeArg | None = None,
        index_col: str | list[str] | None = None,
        coerce_float: bool = True,
        parse_dates: list[str]
        | dict[str, str]
        | dict[str, dict[str, Any]]
        | None = None,
        columns: list[str] | None = None,
        dtype_backend: DTYPE_BACKEND = "numpy_nullable",
    ) -> None:
        self._if_exists: IF_EXISTS = if_exists
        self._index = index
        self._index_label = index_label
        self._dtype = dtype
        self._coerce_float = coerce_float
        self._parse_dates = parse_dates
        self._columns = columns
        self._index_col = index_col
        self._dtype_backend: DTYPE_BACKEND = dtype_backend

    def write(
        self, db: DatabaseResource, schema: str | None, name: str, data: pd.DataFrame
    ) -> None:
        with db.get_connection() as con:
            data.to_sql(
                name,
                con,
                schema,
                if_exists=self._if_exists,
                index=self._index,
                index_label=self._index_label,
                dtype=self._dtype,
            )

    def read(self, db: DatabaseResource, schema: str | None, name: str) -> pd.DataFrame:
        with db.get_connection() as con:
            return pd.read_sql_table(
                name,
                con,
                schema,
                index_col=self._index_col,
                coerce_float=self._coerce_float,
                parse_dates=self._parse_dates,
                columns=self._columns,
                dtype_backend=self._dtype_backend,
            )


DataclassType = TypeVar("DataclassType", bound=DataClassJsonMixin)


class DatabasePersister(DataPersister):
    def __init__(self, db: DatabaseResource, schema: str | None = None) -> None:
        self._db = db
        self._schema = schema
        self._handlers: dict[AssetId, DataHandlerProtocoll] = {}
        super().__init__()

    def _get_table_name(self, assed_id: AssetId) -> str:
        path = assed_id.as_path()
        table_name = path.parts[-1]
        return table_name

    def _get_schema_name(self, assed_id: AssetId) -> str | None:
        path = assed_id.as_path()
        parts = path.parts
        if len(parts) > 1:
            schema = parts[-2]
            if self._schema:
                raise DatabasePersisterMultipleSchemaDefinitionError(
                    self._schema, schema
                )
            return schema
        return self._schema

    def register(
        self,
        asset_id: AssetId,
        handler: DataHandlerProtocoll,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._handlers[asset_id] = handler

    def registered(self, asset_id: AssetId) -> bool:
        return asset_id in self._handlers.keys()

    def load(self, asset: DefaultAsset) -> None:
        asset_id = asset.asset_id()
        name = self._get_table_name(asset_id)
        schema = self._get_schema_name(asset_id)
        handler = self._handlers[asset_id]
        asset.data = handler.read(self._db, schema, name)

    def save(self, asset: DefaultAsset) -> None:
        asset_id = asset.asset_id()
        name = self._get_table_name(asset_id)
        schema = self._get_schema_name(asset_id)
        handler = self._handlers[asset_id]
        handler.write(self._db, schema, name, asset.data)
