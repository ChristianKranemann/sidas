from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type

from sidas.core import DefaultAsset, MetaDataNotStoredException, MetaPersister

if TYPE_CHECKING:
    from types_boto3_dynamodb.service_resource import Table
else:
    Table = object

from ..resources.aws import AwsAccount

PRIMARY_ID_KEY = "asset_id"


class DynamoDbMetadataStore(MetaPersister):
    def __init__(self, account: AwsAccount, table_name: str):
        self.account = account
        self.table_name = table_name

    def get_table(self) -> Table:
        return self.account.session().resource("dynamodb").Table(self.table_name)

    def register(
        self, *asset: DefaultAsset | Type[DefaultAsset], **kwargs: Any
    ) -> None:
        for a in asset:
            self.patch_asset(a)

    def save(self, asset: DefaultAsset) -> None:
        asset_id = str(asset.asset_id())
        data = asset.meta.to_json()
        item = {PRIMARY_ID_KEY: asset_id, "data": data}
        self.get_table().put_item(Item=item)

    def load(self, asset: DefaultAsset) -> None:
        asset_id = str(asset.asset_id())
        response = self.get_table().get_item(Key={PRIMARY_ID_KEY: asset_id})
        if "Item" not in response:
            raise MetaDataNotStoredException()
        item = response["Item"]
        data: str = item["data"]  # type: ignore

        meta = asset.meta_type().from_json(data)
        asset.meta = meta

    def heartbeat(self) -> None:
        pass
