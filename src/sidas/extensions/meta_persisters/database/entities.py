# from __future__ import annotations

# from datetime import datetime
# from typing import Type

# from sqlmodel import Field, SQLModel  # type: ignore[reportUnknownVariableType]

# from ....core import AssetId, AssetMeta, MetaBase


# class MetadataEntity(SQLModel, table=True):
#     asset_id: str = Field(primary_key=True)
#     asset_metadata: str

#     @classmethod
#     def create(cls, asset_id: AssetId, metadata: MetaBase) -> MetadataEntity:
#         entity = MetadataEntity(asset_id=asset_id, asset_metadata=metadata.to_json())
#         return entity

#     def update(self, metadata: MetaBase) -> None:
#         self.asset_metadata = metadata.to_json()

#     def to_metadata(self, as_type: Type[AssetMeta]) -> AssetMeta:
#         return as_type.from_json(self.asset_metadata)


# class SchedulerMetadata(SQLModel, table=True):
#     key: str = Field(primary_key=True)
#     value: str
#     updated_at: datetime = Field(default_factory=datetime.now)

#     @classmethod
#     def init(cls) -> SchedulerMetadata:
#         return SchedulerMetadata(key="heartbeat", value=datetime.now().isoformat())
