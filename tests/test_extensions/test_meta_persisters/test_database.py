import os

import pytest

from sidas.core import AssetId, MetaBase
from sidas.extensions.meta_persisters.database import (
    SqlMetaPersistert,
)
from sidas.extensions.resources.databases import SqliteResource


class A(MetaBase): ...


ASSET_ID = AssetId("SOMETHING")


@pytest.fixture
def sqlite_file(tmp_path):
    # Create a path for the SQLite file
    db_file = tmp_path / "test.db"

    # Yield the engine to the test
    yield db_file

    # Teardown: Remove the database file
    try:
        os.remove(db_file)
    except OSError as e:
        print(f"Error: {db_file} : {e.strerror}")


def test_load_missing_metadata(sqlite_file) -> None:
    db = SqliteResource(sqlite_file)
    persister = SqlMetaPersistert(db)
    meta = persister.load(ASSET_ID, A)
    assert isinstance(meta, A)


def test_load_stored_metadata(sqlite_file) -> None:
    meta = A()
    db = SqliteResource(sqlite_file)
    persister = SqlMetaPersistert(db)
    persister.save(ASSET_ID, meta)

    loaded = persister.load(ASSET_ID, A)
    assert meta == loaded


# def test_save_heartbeat() -> None:
#     metadata_store = SqlMetaPersistert(provider="sqlite", file=":memory:")
#     metadata_store.heartbeat()
#     metadata_store.heartbeat()


# def test_initialize_from_env_vars() -> None:
#     import os

#     os.environ[SIDA_METADATA_STORE_PROVIDER] = "sqlite"
#     os.environ[SIDA_METADATA_STORE_FILE] = ":memory:"
#     persister = SqlMetaPersistert()
#     meta = persister.load(ASSET_ID)
#     assert isinstance(meta, A)
