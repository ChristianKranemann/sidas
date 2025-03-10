from typing import Any, Type

from ...core import (
    DefaultAsset,
    MetaDataNotStoredException,
    MetaPersister,
)
from ..resources.file import FileResource


class FileMetaPersister(MetaPersister):
    def __init__(self, folder: FileResource) -> None:
        self.folder = folder

    def register(
        self, *asset: DefaultAsset | Type[DefaultAsset], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: DefaultAsset) -> None:
        path = asset.asset_id().as_path()
        with self.folder.open(path, mode="w") as f:
            f.write(asset.meta.to_json())

    def load(self, asset: DefaultAsset) -> None:
        path = asset.asset_id().as_path()
        if not self.folder.exists(path):
            raise MetaDataNotStoredException()

        with self.folder.open(path, mode="r") as f:
            data = f.readline()
            meta = asset.meta_type().from_json(data)
            asset.meta = meta

    def heartbeat(self) -> None:
        pass


__all__ = ["FileMetaPersister"]
