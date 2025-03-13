import boto3
from moto import mock_aws

from sidas.extensions.assets import SimpleAsset
from sidas.extensions.meta_persisters.dynamodb import (
    PRIMARY_ID_KEY,
    DynamoDbMetadataStore,
)
from sidas.extensions.resources.aws import AwsAccount

TABLE_NAME = "dynamdbmeta"


class TestAsset(SimpleAsset[int]):
    def transformation(self) -> int:
        return 0


def metadata_table() -> str:
    client = boto3.client("dynamodb", region_name="eu-central-1")
    client.create_table(
        TableName=TABLE_NAME,
        AttributeDefinitions=[{"AttributeName": PRIMARY_ID_KEY, "AttributeType": "S"}],
        KeySchema=[{"AttributeName": PRIMARY_ID_KEY, "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )

    return TABLE_NAME


@mock_aws
def test_read_write():
    table_name = metadata_table()
    resource = AwsAccount(region_name="eu-central-1")
    store = DynamoDbMetadataStore(resource, table_name)
    store.register(TestAsset)

    test_asset_1 = TestAsset()
    test_asset_1.hydrate()

    test_asset_2 = TestAsset()
    test_asset_2.load_meta()

    assert test_asset_1.meta == test_asset_2.meta
