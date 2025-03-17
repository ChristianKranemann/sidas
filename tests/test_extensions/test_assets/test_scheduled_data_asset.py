# from sidas.extensions.assets.scheduled_asset import (
#     ScheduledAsset,
#     ScheduledAssetMetadata,
# )


# class ExampleScheduledAsset(ScheduledAsset[list[int]]):
#     cron_expression = "*/5 * * * *"

#     def transformation(self) -> list[int]:
#         return [1]


# def test_scheduled_asset_init() -> None:
#     a = ExampleScheduledAsset()

#     assert a.meta.cron_expression == "*/5 * * * *"
#     assert a.data_type() == list[int]
#     assert a.meta_type() == ScheduledAssetMetadata
