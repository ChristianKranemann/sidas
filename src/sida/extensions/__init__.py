from typing import Type

from ..core import DefaultAsset
from .assets import DownstreamAsset, DownstreamAssetRefreshMethod, ScheduledAsset
from .data_persisters.simple import InMemoryDataPersister
from .meta_persisters.simple import InMemoryMetaPersister


def REGISTER_ASSETS_IN_MEMORY(
    *asset: Type[DefaultAsset],
) -> tuple[InMemoryMetaPersister, InMemoryDataPersister]:
    mp = InMemoryMetaPersister()
    dp = InMemoryDataPersister()

    for a in asset:
        mp.register(a)
        dp.register(a)

    return (mp, dp)


__all__ = [
    "InMemoryDataPersister",
    "InMemoryMetaPersister",
    "ScheduledAsset",
    "DownstreamAsset",
    "DownstreamAssetRefreshMethod",
    "REGISTER_ASSETS_IN_MEMORY",
]
