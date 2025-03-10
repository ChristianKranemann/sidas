# import os
# from typing import TypedDict

# import pytest
# from sqlalchemy import Column, Integer, String

# from sida.core import Asset, AssetId, MetaBase
# from sida.extensions.data_persisters.database import (
#     DatabasePersister,
#     DatabasePersisterMultipleSchemaDefinitionError,
#     DatabaseTable,
# )
# from sida.extensions.resources.databases import SqliteResource

# # DATAWAREHOUSE_DB_DATABASE=PostgreSQL
# TABLE_NAME = "mytable"
# SCHEMA_NAME = "myschema"
# SIMPLE_NAME = TABLE_NAME
# COMPLEX_NAME = f"{SCHEMA_NAME}.{TABLE_NAME}"
# D1 = {"id": 1, "name": "D1"}
# D2 = {"id": 2, "name": "D2"}


# class ExampleData(TypedDict):
#     name: str


# class ExampleAsset(Asset[MetaBase, list[ExampleData]]):
#     def transformation(self) -> list[ExampleData]:
#         return [ExampleData(name="test")]


# @pytest.fixture
# def sqlite_file(tmp_path):
#     # Create a path for the SQLite file
#     db_file = tmp_path / "test.db"

#     # Yield the engine to the test
#     yield db_file

#     # Teardown: Remove the database file
#     try:
#         os.remove(db_file)
#     except OSError as e:
#         print(f"Error: {db_file} : {e.strerror}")


# def test_get_table_name_from_simple_asset(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)
#     manager = DatabasePersister(db)

#     assed_id = AssetId(SIMPLE_NAME)
#     table_name = manager._get_table_name(assed_id)
#     assert table_name == TABLE_NAME


# def test_get_table_name_from_complex_asset(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)
#     manager = DatabasePersister(db)

#     assed_id = AssetId(COMPLEX_NAME)
#     table_name = manager._get_table_name(assed_id)
#     assert table_name == TABLE_NAME


# def test_get_table_schema_from_init(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)
#     manager = DatabasePersister(db, schema=SCHEMA_NAME)

#     assed_id = AssetId(SIMPLE_NAME)
#     name = manager._get_schema_name(assed_id)
#     assert name == SCHEMA_NAME


# def test_get_table_schema_from_asset(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)
#     manager = DatabasePersister(db)

#     assed_id = AssetId(COMPLEX_NAME)
#     name = manager._get_schema_name(assed_id)
#     assert name == SCHEMA_NAME


# def test_get_table_schema_error_on_multiple_schema(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)
#     manager = DatabasePersister(db, schema=SCHEMA_NAME)

#     assed_id = AssetId(COMPLEX_NAME)
#     with pytest.raises(DatabasePersisterMultipleSchemaDefinitionError):
#         manager._get_schema_name(assed_id)


# def test_input_output(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)
#     manager = DatabasePersister(db)

#     COLUMNS = [
#         Column("id", Integer, primary_key=True),
#         Column("name", String),
#     ]

#     class A(Asset[MetaBase, list[ExampleData]]):
#         def transformation(self) -> DatabaseTable:
#             return DatabaseTable(COLUMNS, [{"name": "hallo"}])

#     table.extend([D1, D2])
#     manager.save(A.asset_id(), table)
#     result = manager.load(assed_id)
#     assert result == data


# # def test_input_output_with_schema(sqlite_file) -> None:
# #     pass
# #     # Does not work on sqlite

# #     input_context = build_input_context(asset_key=[SCHEMA, NAME])
# #     output_context = build_output_context(name=NAME, metadata={"schema": SCHEMA})

# #     data = DatabaseTable(
# #         [Column("id", Integer, primary_key=True), Column("name", String)], [D1, D2]
# #     )

# #     db = SqliteResource(path=sqlite_file)
# #     manager = DatabasePersister(db)
# #     manager.handle_output(output_context, data)

# #     result = manager.load_input(input_context)

# #     assert result == data
