# from unittest.mock import Mock, call, patch

# import pytest

# # Import the classes to test
# from sida.core import (
#     AssetId,
#     CoordinateUsecase,
#     Coordinator,
#     MaterializeUsecase,
# )


# class TestCoordinateUsecase:
#     def setup_method(self):
#         """Set up test fixtures for each test method."""
#         self.coordinator = Mock(spec=Coordinator)
#         self.asset_store = Mock(spec=AssetStore)
#         self.usecase = CoordinateUsecase(self.coordinator, self.asset_store)

#     def test_assets_that_cannot_materialize(self):
#         """Test coordination with assets that cannot be materialized."""
#         # Create mock assets
#         asset1 = Mock()
#         asset1.can_materialize.return_value = False
#         asset2 = Mock()
#         asset2.can_materialize.return_value = False

#         # Configure the asset store
#         self.asset_store.assets = [asset1, asset2]

#         # Call the usecase
#         self.usecase()

#         # Verify interactions
#         for asset in [asset1, asset2]:
#             asset.hydrate.assert_called_once()
#             asset.can_materialize.assert_called_once()
#             asset.before_materialize.assert_not_called()

#         self.coordinator.trigger_materialization.assert_not_called()

#     def test_assets_that_can_materialize(self):
#         """Test coordination with assets that can be materialized."""
#         # Create mock assets
#         asset1 = Mock()
#         asset1.can_materialize.return_value = True
#         asset2 = Mock()
#         asset2.can_materialize.return_value = False
#         asset3 = Mock()
#         asset3.can_materialize.return_value = True

#         # Configure the asset store
#         self.asset_store.assets = [asset1, asset2, asset3]

#         # Call the usecase
#         self.usecase()

#         # Verify interactions
#         for asset in [asset1, asset2, asset3]:
#             asset.hydrate.assert_called_once()
#             asset.can_materialize.assert_called_once()

#         for asset in [asset1, asset3]:
#             asset.before_materialize.assert_called_once()

#         asset2.before_materialize.assert_not_called()

#         assert self.coordinator.trigger_materialization.call_count == 2
#         self.coordinator.trigger_materialization.assert_has_calls(
#             [call(asset1), call(asset3)]
#         )

#     @patch("logging.info")
#     def test_logging(self, mock_logging):
#         """Test that the coordinator logs when starting."""
#         # Configure the mock
#         self.asset_store.assets = []

#         # Call the usecase
#         self.usecase()

#         # Verify logging
#         mock_logging.assert_called_once_with("Starting scheduler...")

#     def test_mixed_assets(self):
#         """Test coordination with a mix of assets that can and cannot be materialized."""
#         # Create mock assets with alternating can_materialize results
#         assets = []
#         for i in range(5):
#             asset = Mock()
#             asset.can_materialize.return_value = i % 2 == 0  # True for even indices
#             assets.append(asset)

#         # Configure the asset store
#         self.asset_store.assets = assets

#         # Call the usecase
#         self.usecase()

#         # Verify interactions
#         materializable_assets = [assets[i] for i in range(5) if i % 2 == 0]
#         non_materializable_assets = [assets[i] for i in range(5) if i % 2 != 0]

#         for asset in assets:
#             asset.hydrate.assert_called_once()
#             asset.can_materialize.assert_called_once()

#         for asset in materializable_assets:
#             asset.before_materialize.assert_called_once()

#         for asset in non_materializable_assets:
#             asset.before_materialize.assert_not_called()

#         assert self.coordinator.trigger_materialization.call_count == len(
#             materializable_assets
#         )
#         self.coordinator.trigger_materialization.assert_has_calls(
#             [call(asset) for asset in materializable_assets]
#         )


# class TestMaterializeUsecase:
#     def setup_method(self):
#         """Set up test fixtures for each test method."""
#         self.asset_store = Mock(spec=AssetStore)
#         self.usecase = MaterializeUsecase(self.asset_store)

#     def test_materialization_flow(self):
#         """Test the complete materialization flow of a single asset."""
#         # Create mock asset
#         asset = Mock()
#         asset_id = AssetId("test.asset")

#         # Configure the asset store
#         self.asset_store.asset.return_value = asset

#         # Create input data
#         input_data = MaterializeUsecaseInput(asset_id=asset_id)

#         # Call the usecase
#         self.usecase(input_data)

#         # Verify interactions
#         self.asset_store.asset.assert_called_once_with(asset_id)
#         asset.hydrate.assert_called_once()
#         asset.materialize.assert_called_once()

#     def test_asset_retrieval(self):
#         """Test that the correct asset is retrieved from the store."""
#         # Create multiple mock assets with different IDs
#         asset_ids = [AssetId(f"test.asset.{i}") for i in range(3)]
#         assets = [Mock() for _ in range(3)]

#         # Configure the asset store to return different assets for different IDs
#         def get_asset(asset_id):
#             idx = asset_ids.index(asset_id)
#             return assets[idx]

#         self.asset_store.asset.side_effect = get_asset

#         # Test each asset ID
#         for i, asset_id in enumerate(asset_ids):
#             input_data = MaterializeUsecaseInput(asset_id=asset_id)
#             self.usecase(input_data)

#             # Verify the correct asset was retrieved
#             self.asset_store.asset.assert_called_with(asset_id)
#             assets[i].hydrate.assert_called_once()
#             assets[i].materialize.assert_called_once()

#     def test_asset_not_found(self):
#         """Test behavior when asset is not found in the store."""
#         # Configure the asset store to raise an exception
#         asset_id = AssetId("nonexistent.asset")
#         self.asset_store.asset.side_effect = KeyError(f"Asset {asset_id} not found")

#         # Create input data
#         input_data = MaterializeUsecaseInput(asset_id=asset_id)

#         # Call the usecase and expect exception
#         with pytest.raises(KeyError) as excinfo:
#             self.usecase(input_data)

#         # Verify the exception details
#         assert str(asset_id) in str(excinfo.value)
#         self.asset_store.asset.assert_called_once_with(asset_id)

#     def test_materialization_error(self):
#         """Test behavior when materialization fails."""
#         # Create mock asset that raises an error during materialization
#         asset = Mock()
#         asset_id = AssetId("test.asset")
#         asset.materialize.side_effect = RuntimeError("Materialization failed")

#         # Configure the asset store
#         self.asset_store.asset.return_value = asset

#         # Create input data
#         input_data = MaterializeUsecaseInput(asset_id=asset_id)

#         # Call the usecase and expect exception
#         with pytest.raises(RuntimeError) as excinfo:
#             self.usecase(input_data)

#         # Verify the exception details and interactions
#         assert "Materialization failed" in str(excinfo.value)
#         self.asset_store.asset.assert_called_once_with(asset_id)
#         asset.hydrate.assert_called_once()
#         asset.materialize.assert_called_once()

#     def test_input_validation(self):
#         """Test validation of the input data structure."""
#         # Test with valid input
#         valid_input = MaterializeUsecaseInput(asset_id=AssetId("test.asset"))
#         asset = Mock()
#         self.asset_store.asset.return_value = asset
#         self.usecase(valid_input)

#         # Test with invalid input type
#         invalid_inputs = [
#             {"asset_id": AssetId("test.asset")},  # Dictionary instead of dataclass
#             AssetId("test.asset"),  # Asset ID directly
#             "test.asset",  # String
#         ]

#         for invalid_input in invalid_inputs:
#             with pytest.raises((TypeError, AttributeError)):
#                 self.usecase(invalid_input)
