from typing import Any, Type

from ...core import MetaDataFailedToRetrieve, MetaPersistable, MetaPersister
from ..resources.folder import FolderResource


class FileMetaPersister(MetaPersister):
    def __init__(self, folder: FolderResource) -> None:
        self.folder = folder

    def register(
        self, *asset: MetaPersistable | Type[MetaPersistable], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: MetaPersistable) -> None:
        path = asset.asset_id().as_path()
        with self.folder.open(path, mode="w") as f:
            data = asset.meta.to_json()
            f.write(data)

    def load(self, asset: MetaPersistable) -> None:
        path = asset.asset_id().as_path()
        if not self.folder.exists(path):
            raise MetaDataFailedToRetrieve(asset.asset_id(), "File not found")

        with self.folder.open(path, mode="r") as f:
            data = f.read()
            meta = asset.meta_type().from_json(data)
            asset.meta = meta

    def heartbeat(self) -> None:
        pass


__all__ = ["FileMetaPersister"]
