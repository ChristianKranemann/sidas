from sidas.core import AssetId
from sidas.extensions.data_persisters import InMemoryDataPersister


def test_store_and_retrieve() -> None:
    asset_id = AssetId("test_asset")
    data = [5]

    persister = InMemoryDataPersister[list[int]]()
    persister.save(asset_id, data)
    assert persister.load(asset_id) == data
