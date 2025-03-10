from __future__ import annotations

from typing import ClassVar, Type

from sqlalchemy import Column, DDLElement, Executable, MetaData, Selectable, Table
from sqlalchemy.ext import compiler

from sidas.core import AssetId

from .downstream_asset import DownstreamAsset
from .scheduled_asset import ScheduledAsset
from .simple_asset import SimpleAsset

META = MetaData()


def get_table_name(access_id: AssetId) -> str:
    return access_id.as_path().name


class SqlSimpleAsset(SimpleAsset[Table]):
    """
    A one time Asset. It gets only persisted once.
    """

    table_meta: ClassVar[MetaData] = META

    overwrite_table_name: str
    columns: list[Column]
    executable: Executable

    def table_name(self) -> str:
        try:
            return getattr(self, "overwrite_table_name")
        except AttributeError:
            return get_table_name(self.asset_id())

    @classmethod
    def data_type(cls) -> Type[Table]:
        return Table

    def get_table(self) -> Table:
        try:
            return self.data
        except AttributeError:
            return Table(
                self.table_name(),
                self.table_meta,
                *self.columns,
            )

    def execute_transformation(self) -> Table:
        self.data = self.get_table()
        self.executable = self.transformation()
        return self.data


class SqlScheduledAsset(ScheduledAsset[Table]):
    """
    A one time Asset. It gets only persisted once.
    """

    table_meta: ClassVar[MetaData] = META

    overwrite_table_name: str
    columns: list[Column]
    executable: Executable

    def table_name(self) -> str:
        try:
            return getattr(self, "overwrite_table_name")
        except AttributeError:
            return get_table_name(self.asset_id())

    def get_table(self) -> Table:
        try:
            return self.data
        except AttributeError:
            return Table(
                self.table_name(),
                self.table_meta,
                *self.columns,
            )

    def execute_transformation(self) -> Table:
        table = self.get_table()
        self.data = table
        self.executable = self.transformation()
        return table


class SqlDownstreamAsset(DownstreamAsset[Table]):
    """
    A one time Asset. It gets only persisted once.
    """

    table_meta: ClassVar[MetaData] = META

    overwrite_table_name: str
    columns: list[Column]
    executable: Executable

    def table_name(self) -> str:
        try:
            return getattr(self, "overwrite_table_name")
        except AttributeError:
            return get_table_name(self.asset_id())

    def get_table(self) -> Table:
        try:
            return self.data
        except AttributeError:
            return Table(
                self.table_name(),
                self.table_meta,
                *self.columns,
            )

    def execute_transformation(self) -> Table:
        upstream = self.upstream()
        for asset in upstream:
            asset.load_data()

        table = self.get_table()
        self.data = table
        self.executable = self.transformation(*upstream)
        return table


class SqlTableAsset(DownstreamAsset[Table]):
    """
    A one time Asset. It gets only persisted once.
    """

    table_meta: ClassVar[MetaData] = META

    overwrite_table_name: str
    executable: Executable

    def table_name(self) -> str:
        try:
            return getattr(self, "overwrite_table_name")
        except AttributeError:
            return get_table_name(self.asset_id())

    def get_table(self, selectable: Selectable) -> Table:
        try:
            return self.data
        except AttributeError:
            return Table(
                self.table_name(),
                self.table_meta,
                *(
                    Column(c.name, c.type, primary_key=c.primary_key)
                    for c in selectable.selected_columns  # type: ignore
                ),
            )

    def execute_transformation(self) -> Table:
        upstream = self.upstream()
        for asset in upstream:
            asset.load_data()

        selectable = self.transformation(*upstream)
        self.executable = CreateTableAs(self.table_name(), selectable)

        return self.get_table(selectable)


SqlAsset = SqlSimpleAsset | SqlScheduledAsset | SqlDownstreamAsset | SqlTableAsset
SqlAssetType = (
    Type[SqlSimpleAsset]
    | Type[SqlScheduledAsset]
    | Type[SqlDownstreamAsset]
    | Type[SqlTableAsset]
)


class CreateTableAs(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


@compiler.compiles(CreateTableAs)
def _create_table_as_defaullt(element, compiler, **kw):
    return "CREATE TABLE %s AS (%s)" % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


@compiler.compiles(CreateTableAs, "sqlite")
def _create_table_as_sqlite(element, compiler, **kw):
    return "CREATE TABLE %s AS %s" % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )
