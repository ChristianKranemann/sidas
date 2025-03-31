from pathlib import PurePath

# Assuming the module is named asset_system
from sidas.core import (
    AssetId,
)


def test_asset_id_creation():
    asset_id = AssetId("test.asset.id")
    assert asset_id == "test.asset.id"
    assert isinstance(asset_id, str)


def test_as_path_conversion():
    asset_id = AssetId("test.asset.id")
    path = asset_id.as_path()
    assert isinstance(path, PurePath)
    assert str(path) == "test/asset/id"


def test_empty_asset_id():
    asset_id = AssetId("")
    assert asset_id.as_path() == PurePath()


def test_as_path_with_suffixconversion():
    asset_id = AssetId("test.asset.id")
    path = asset_id.as_path(suffix="example")
    assert isinstance(path, PurePath)
    assert str(path) == "test/asset/id.example"

    path = asset_id.as_path(suffix=".example")
    assert isinstance(path, PurePath)
    assert str(path) == "test/asset/id.example"
