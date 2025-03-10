from sida.extensions.assets.scheduled_asset import (
    ScheduledAsset,
    ScheduledAssetMetadata,
)


class ExampleScheduledAsset(ScheduledAsset[list[int]]):
    cron_expression = "*/5 * * * *"

    def transformation(self) -> list[int]:
        return [1]


def test_scheduled_asset_init() -> None:
    a = ExampleScheduledAsset()

    assert a.meta.cron_expression == "*/5 * * * *"
    assert a.data_type() == list[int]
    assert a.meta_type() == ScheduledAssetMetadata


# def test_cron_expression_setr():
#     asset = ExampleScheduledAsset()
#     assert asset.cron_expression == "*/5 * * * *"


# def test_materialize():
#     mode_asset1 = ExampleScheduledAsset()
#     mode_asset1.materialize()
#     assert mode_asset1.value == 1


# def test_materialization_required():
#     mode_asset1 = ExampleScheduledAsset()
#     mode_asset1.cron_iterator = MagicMock()

#     # next schedule is 1 min in the past
#     mode_asset1.next_schedule = datetime.now() - timedelta(minutes=1)
#     assert mode_asset1.materialization_required() is True

#     # next schedule is 5 min in the future
#     mode_asset1.next_schedule = datetime.now() + timedelta(minutes=5)
#     assert mode_asset1.materialization_required() is False
