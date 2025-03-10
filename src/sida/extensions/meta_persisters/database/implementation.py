from __future__ import annotations

from datetime import datetime
from typing import Type

import sqlmodel as sqlm
from sqlalchemy.exc import NoResultFound

from ....core import AssetId, AssetMeta, MetaBase, MetaPersister
from ...resources.databases import DatabaseResource
from .entities import MetadataEntity, SchedulerMetadata


class SqlMetaPersistert(MetaPersister):
    """
    Make sure to set the following env vars:

    export SIDA_COORDINATOR_STORAGE_PATH=/path/to/db
    """

    def __init__(self, db: DatabaseResource) -> None:
        super().__init__()
        self.db = db
        sqlm.SQLModel.metadata.create_all(self.db.get_engine())

    def _load_metadata(
        self, session: sqlm.Session, asset_id: AssetId, meta_type: Type[AssetMeta]
    ) -> AssetMeta:
        statement = sqlm.select(MetadataEntity).where(
            MetadataEntity.asset_id == asset_id
        )
        entry = session.exec(statement).one()
        return entry.to_metadata(meta_type)

    def _insert_metadata(
        self, session: sqlm.Session, asset_id: AssetId, metadata: AssetMeta
    ) -> AssetMeta:
        entry = MetadataEntity.create(asset_id, metadata)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return metadata

    def _update_metadata(
        self, session: sqlm.Session, asset_id: AssetId, metadata: AssetMeta
    ) -> AssetMeta:
        statement = sqlm.select(MetadataEntity).where(
            MetadataEntity.asset_id == asset_id
        )
        entry = session.exec(statement).one()
        entry.update(metadata)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return metadata

    def _insert_heartbeat(self, session: sqlm.Session) -> None:
        entry = SchedulerMetadata.init()
        session.add(entry)
        session.commit()
        session.refresh(entry)

    def _update_heartbeat(self, session: sqlm.Session) -> None:
        statement = sqlm.select(SchedulerMetadata).where(
            SchedulerMetadata.key == "heartbeat"
        )
        entry = session.exec(statement).one()
        entry.value = datetime.now().isoformat()
        session.add(entry)
        session.commit()
        session.refresh(entry)

    def load(self, asset_id: AssetId, meta_type: Type[AssetMeta]) -> AssetMeta:
        with sqlm.Session(self.db.get_engine()) as session:
            try:
                return self._load_metadata(session, asset_id, meta_type)
            except NoResultFound:
                return self._insert_metadata(session, asset_id, meta_type())

    def save(self, asset_id: AssetId, meta: MetaBase) -> None:
        with sqlm.Session(self.db.get_engine()) as session:
            try:
                self._update_metadata(session, asset_id, meta)
            except NoResultFound:
                self._insert_metadata(session, asset_id, meta)

    def heartbeat(self) -> None:
        with sqlm.Session(self.db.get_engine()) as session:
            try:
                self._update_heartbeat(session)
            except NoResultFound:
                self._insert_heartbeat(session)
