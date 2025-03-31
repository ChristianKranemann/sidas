from __future__ import annotations

from pathlib import PurePath
from typing import TypeVar

AssetData = TypeVar("AssetData")


class AssetId(str):
    """
    A string-based identifier for assets that can be converted to a filesystem path.

    AssetId extends the str class to provide additional functionality for working with
    asset identifiers, particularly the ability to convert dot-separated identifiers
    into filesystem paths.

    Examples:
        >>> asset_id = AssetId("my.asset.id")
        >>> asset_id.as_path()
        PurePath('my/asset/id')
    """

    def as_path(self, suffix: str | None = None) -> PurePath:
        """
        Convert the dot-separated asset ID into a filesystem path.

        Returns:
            PurePath: A path object where each component is a part of the dot-separated ID
        """

        path = PurePath(*self.split("."))
        if suffix is not None:
            if suffix.startswith("."):
                path = path.with_suffix(suffix)
            else:
                path = path.with_suffix("." + suffix)
        return path
