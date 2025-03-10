from contextlib import contextmanager
from typing import Iterator, Protocol, runtime_checkable

from sqlalchemy import Connection, Engine, create_engine


@runtime_checkable
class DatabaseResource(Protocol):
    def get_engine(self) -> Engine: ...

    @contextmanager
    def get_connection(self) -> Iterator[Connection]: ...


class SqliteResource(DatabaseResource):
    """ """

    path: str

    def __init__(self, path: str) -> None:
        self.path = path

    def get_engine(self) -> Engine:
        engine = create_engine(f"sqlite:///{self.path}")
        return engine

    @contextmanager
    def get_connection(self) -> Iterator[Connection]:
        connection = self.get_engine().connect()
        yield connection
        connection.close()


class SqlServerResource(DatabaseResource):
    host: str
    user: str
    password: str
    dbname: str
    port: int

    def __init__(
        self, host: str, user: str, password: str, dbname: str, port: int = 1433
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.dbname = dbname
        self.port = port

    def get_engine(self) -> Engine:
        engine = create_engine(
            f"mssql+pyodbc://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}?driver=ODBC+Driver+17+for+SQL+Server"
            # f"mssql+pymssql://{self.user}:{self.password}@{self.host}/{self.dbname}/?charset=utf8"
        )
        return engine

    @contextmanager
    def get_connection(self) -> Iterator[Connection]:
        conn = self.get_engine().connect()
        yield conn
        conn.close()


class PostgresqlResource(DatabaseResource):
    host: str
    user: str
    password: str
    dbname: str
    port: int

    def __init__(
        self, host: str, user: str, password: str, dbname: str, port: int = 5432
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.dbname = dbname
        self.port = port

    def get_engine(self) -> Engine:
        engine = create_engine(
            f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
            # f"mssql+pyodbc://{self.user}:{self.password}@{self.host}/{self.dbname}"
        )
        return engine

    @contextmanager
    def get_connection(self) -> Iterator[Connection]:
        conn = self.get_engine().connect()

        yield conn
        conn.close()
