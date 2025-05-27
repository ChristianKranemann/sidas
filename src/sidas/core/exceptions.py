from .asset_id import AssetId


class CoordinatorNotRegisteredInMetaPersister(Exception):
    """
    Raised when a coordinator is not registered in the meta persister
    """

    def __init__(self):
        msg = "Coordinator is not registered in the meta persister."
        super().__init__(msg)


class AssetNotFoundException(Exception):
    """
    Raised when an asset is not found by the coordinator
    """

    def __init__(self, asset_id: AssetId):
        msg = f"Asset with id {asset_id} not found."
        super().__init__(msg)


class AssetNotRegisteredInMetaPersister(Exception):
    """
    Raised when an asset is not registered in the meta persister
    """

    def __init__(self, asset_id: AssetId):
        msg = f"Asset with id {asset_id} is not registered in the meta persister."
        super().__init__(msg)


class AssetNotRegisteredInDataPersister(Exception):
    """
    Raised when an asset is not registered in the data persister
    """

    def __init__(self, asset_id: AssetId):
        msg = f"Asset with id {asset_id} is not registered in the data persister."
        super().__init__(msg)


class AssetDataFailedToPersist(Exception):
    """
    Raised when a data persister is not able to persist the asset data
    """

    def __init__(self, asset_id: AssetId, error: Exception | str):
        msg = f"Failed to save data for asset {asset_id}: {error}"
        super().__init__(msg)


class AssetDataFailedToRetrieve(Exception):
    """
    Raised when a data persister is not able to retrieve the asset data
    """

    def __init__(self, asset_id: AssetId, error: Exception | str):
        msg = f"Failed to load data for asset {asset_id}: {error}"
        super().__init__(msg)


class MetaDataFailedToPersist(Exception):
    """
    Raised when a meta persister is not able to persist the asset metadata
    """

    def __init__(self, asset_id: AssetId, error: Exception | str):
        msg = f"Failed to persist meta data for asset {asset_id}: {error}"
        super().__init__(msg)


class MetaDataFailedToRetrieve(Exception):
    """
    Raised when a meta persister is not able to retrive the asset metadata
    """

    def __init__(self, asset_id: AssetId, error: Exception | str):
        msg = f"Failed to retrieve meta data for asset {asset_id}: {error}"
        super().__init__(msg)
