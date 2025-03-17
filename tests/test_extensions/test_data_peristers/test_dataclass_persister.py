from copy import copy
from dataclasses import dataclass

from sidas.extensions.assets import SimpleAsset
from sidas.extensions.data_persisters.dataclass_persister import (
    DataclassPersister,
    DataclassPersisterDBResource,
    DataclassPersisterFileResource,
)
from sidas.extensions.meta_persisters import FileMetaPersister
from sidas.extensions.resources.databases import SqliteResource
from sidas.extensions.resources.file import InMemoryFile


@dataclass
class TestClass:
    x: int


class TestAsset(SimpleAsset[list[TestClass]]):
    def transformation(self) -> list[TestClass]:
        return [TestClass(1), TestClass(2)]


def test_init():
    file = InMemoryFile()
    resource = DataclassPersisterFileResource(file)
    persister = DataclassPersister(resource)

    assert persister


def test_load_and_save_to_file():
    file = InMemoryFile()
    resource = DataclassPersisterFileResource(file)
    persister = DataclassPersister(resource)
    persister.register(TestAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)

    test_asset = TestAsset()
    test_asset.hydrate()

    test_asset.materialize()

    test_asset.load_data()


def test_load_and_save_to_db():
    file = InMemoryFile()
    db = SqliteResource("::memory::")
    resource = DataclassPersisterDBResource(db)
    persister = DataclassPersister(resource)
    persister.register(TestAsset)

    meta_persister = FileMetaPersister(file)
    meta_persister.register(TestAsset)

    test_asset = TestAsset()
    test_asset.hydrate()

    test_asset.materialize()
    materialized = copy(test_asset.data)

    test_asset.load_data()
    assert test_asset.data == materialized

    # test if overwriting works
    test_asset.materialize()
    test_asset.load_data()
    assert test_asset.data == materialized
