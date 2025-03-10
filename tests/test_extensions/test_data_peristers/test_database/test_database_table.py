# import os

# import pytest
# import sqlalchemy
# from sqlalchemy import Column, Integer, String

# from sida.extensions.data_persisters.database.database_table import (
#     DatabaseTable,
# )
# from sida.extensions.resources.databases import DatabaseResource, SqliteResource

# # db = PostgresqlResource("localhost", "postgres", "Test1234!", "postgres")

# NAME = "table1"
# SCHEMA = "public"
# D1 = {"id": 1, "name": "D1"}
# D2 = {"id": 2, "name": "D2"}
# D3 = {"id": 3, "name": "D3"}


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


# def has_table(resource: DatabaseResource, name: str, schema: str | None = None) -> bool:
#     engine = resource.get_engine()
#     if schema:
#         return sqlalchemy.inspect(engine).has_table(schema=schema, table_name=name)
#     else:
#         return sqlalchemy.inspect(engine).has_table(table_name=name)


# def test_instantiate() -> None:
#     t1 = DatabaseTable(
#         [Column("id", Integer, primary_key=True), Column("name", String)]
#     )
#     assert len(t1._columns) == 2
#     assert t1._columns[0].name == "id"
#     assert t1._columns[1].name == "name"


# def test_instantiate_with_data() -> None:
#     t1 = DatabaseTable(
#         [Column("id", Integer, primary_key=True), Column("name", String)], [D1]
#     )
#     assert t1[0]["id"] == 1
#     assert t1[0]["name"] == "D1"


# def test_create_and_drop_table(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)

#     t1 = DatabaseTable(
#         [Column("id", Integer, primary_key=True), Column("name", String)]
#     )
#     t1._create_table(db, NAME)
#     assert has_table(db, NAME)

#     t1.cleanup(db, NAME)
#     assert not has_table(db, NAME, SCHEMA)


# def test_insert_and_read_data(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)

#     t1 = DatabaseTable(
#         [Column("id", Integer, primary_key=True), Column("name", String)]
#     )
#     t1.extend([D1, D2])
#     t1.write(db, NAME)

#     t2 = DatabaseTable(
#         [Column("id", Integer, primary_key=True), Column("name", String)]
#     )
#     t2.read(db, NAME)
#     assert t2 == [D1, D2]

#     t1.cleanup(db, NAME)


# def test_insert_and_read_subset_data(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)

#     t1 = DatabaseTable(
#         [Column("id", Integer, primary_key=True), Column("name", String)]
#     )
#     t1.extend([D1, D2])
#     t1.write(db, NAME)

#     t2 = DatabaseTable([Column("name", String)])
#     t2.read(db, NAME)
#     # assert t2 == [D1, D2]
#     print(t2)
#     t1.cleanup(db, NAME)


# def test_from_table(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)

#     t1 = DatabaseTable(
#         [Column("id", Integer, primary_key=True), Column("name", String)]
#     )
#     t1.extend([D1, D2])
#     t1.write(db, NAME)

#     t2 = DatabaseTable.from_table(db, NAME)
#     print(t2)
#     assert t2 == [D1, D2]

#     t2.append(D3)
#     t2.write(db, NAME)

#     t3 = DatabaseTable.from_table(db, NAME)
#     print(t3)
#     assert t3 == [D1, D2, D3]

#     t1.cleanup(db, NAME)


# def test_change_table(sqlite_file) -> None:
#     db = SqliteResource(path=sqlite_file)

#     x1 = {"id": 1, "x": "x"}
#     y1 = {"id": 1, "y": "y"}

#     t1 = DatabaseTable([Column("id", Integer, primary_key=True), Column("x", String)])
#     t2 = DatabaseTable([Column("id", Integer, primary_key=True), Column("y", String)])

#     t1.extend([x1])
#     t1.write(db, NAME)

#     t2.extend([y1])
#     t2.write(db, NAME)

#     t2.cleanup(db, NAME)
