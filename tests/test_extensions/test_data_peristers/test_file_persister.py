from sidas.extensions.data_persisters.jsonfile import JsonFileDataPersister, DictListHandler
from sidas.extensions.resources.file import InMemoryFile
from sidas.core import BaseAsset, MetaBase

class DictListAsset(BaseAsset[MetaBase, list[dict]]):  ...
    

def test_json_file_persister_in_memory() -> None:
    res  =InMemoryFile()
    persister = JsonFileDataPersister(res)

    dict_list_asset = DictListAsset()
    dict_list_asset.data = [{"my": 1, "dictionary": 2.2, "data": False}]

    persister.register(dict_list_asset, DictListHandler())
    persister.save(dict_list_asset)