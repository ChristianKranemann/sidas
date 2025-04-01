from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self, TypeVar

from croniter import croniter
from pydantic import BaseModel, Field


class MetaData(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.now)

    def to_json(self) -> str:
        """
        Serialize the metadata instance to a JSON string.

        Returns:
            str: JSON representation of the metadata
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> Self:
        """
        Create a metadata instance from a JSON string.

        Args:
            data: JSON string containing metadata

        Returns:
            Self: A new instance of the metadata class

        Raises:
            ValidationError: If the JSON data doesn't match the expected schema
        """
        return cls.model_validate_json(data)


MetaDataType = TypeVar("MetaDataType", bound=MetaData)


class AssetStatus(StrEnum):
    """
    Enumeration of possible states for an asset during its lifecycle.

    Attributes:
        INITIALIZED: Asset has been created but no processing has started
        MATERIALIZING: Asset is currently executing its transformation
        MATERIALIZING_FAILED: Asset transformation failed with an error
        MATERIALIZED: Asset transformation has completed successfully
        PERSISTING: Asset is in the process of being saved
        PERSISTING_FAILED: Asset persistence failed with an error
        PERSISTED: Asset has been successfully saved
    """

    INITIALIZING = "INITIALIZING"
    INITIALIZING_FAILED = "INITIALIZING_FAILED"
    INITIALIZED = "INITIALIZED"
    MATERIALIZING = "MATERIALIZING"
    MATERIALIZING_FAILED = "MATERIALIZING_FAILED"
    MATERIALIZED = "MATERIALIZED"
    PERSISTING = "PERSISTING"
    PERSISTING_FAILED = "PERSISTING_FAILED"
    PERSISTED = "PERSISTED"


class AssetMetaData(MetaData):
    """
    Base model for asset metadata that tracks processing status and timing information.

    This class provides functionality to track the status of an asset throughout its
    lifecycle, including timestamps for each status transition. It uses a pattern matching
    approach to update timestamps based on the current status, ensuring accurate tracking
    of the asset's state changes.

    Attributes:
        status: Current status of the asset
        initialized_at: Timestamp when the asset was created
        materializing_started_at: Timestamp when transformation started (or None)
        materializing_stopped_at: Timestamp when transformation ended (or None)
        persisting_started_at: Timestamp when persistence started (or None)
        persisting_stopped_at: Timestamp when persistence ended (or None)
        updated_at: Timestamp of the last status update
    """

    status: AssetStatus = AssetStatus.INITIALIZING
    initializing_started_at: datetime = Field(default_factory=datetime.now)
    initializing_stopped_at: datetime | None = None
    materializing_started_at: datetime | None = None
    materializing_stopped_at: datetime | None = None
    persisting_started_at: datetime | None = None
    persisting_stopped_at: datetime | None = None
    updated_at: datetime = Field(default_factory=datetime.now)
    log: list[str] = Field(default_factory=list)

    def update_log(self, message: str) -> Self:
        self.log.append(message)
        return self

    def update_status(self, status: AssetStatus) -> Self:
        """
        Update the asset's status and set the corresponding timestamps.

        Args:
            status: The new status to set for the asset

        Returns:
            Self: The updated instance for method chaining
        """
        self.status = status
        timestamp = datetime.now()
        match status:
            case AssetStatus.INITIALIZING_FAILED:
                self.initializing_stopped_at = timestamp
            case AssetStatus.INITIALIZED:
                self.initializing_stopped_at = timestamp
            case AssetStatus.MATERIALIZING:
                self.materializing_started_at = timestamp
            case AssetStatus.MATERIALIZING_FAILED:
                self.materializing_stopped_at = timestamp
            case AssetStatus.MATERIALIZED:
                self.materializing_stopped_at = timestamp
            case AssetStatus.PERSISTING:
                self.persisting_started_at = timestamp
            case AssetStatus.PERSISTING_FAILED:
                self.persisting_stopped_at = timestamp
            case AssetStatus.PERSISTED:
                self.persisting_stopped_at = timestamp

        self.updated_at = timestamp
        return self

    def in_progress(self) -> bool:
        """
        Check if the asset is currently in progress (either materializing or persisting).

        Returns:
            bool: True if the asset is in progress, False otherwise.
        """
        return self.status in (AssetStatus.MATERIALIZING, AssetStatus.PERSISTING)

    def has_error(self) -> bool:
        """
        Check if the asset has encountered an error during materialization or persistence.

        Returns:
            bool: True if the asset has an error, False otherwise.
        """
        return self.status in (
            AssetStatus.INITIALIZING_FAILED,
            AssetStatus.MATERIALIZING_FAILED,
            AssetStatus.PERSISTING_FAILED,
        )

    def to_json(self) -> str:
        """
        Serialize the metadata instance to a JSON string.

        Returns:
            str: JSON representation of the metadata
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> Self:
        """
        Create a metadata instance from a JSON string.

        Args:
            data: JSON string containing metadata

        Returns:
            Self: A new instance of the metadata class

        Raises:
            ValidationError: If the JSON data doesn't match the expected schema
        """
        return cls.model_validate_json(data)


AssetMetaDataType = TypeVar("AssetMetaDataType", bound=AssetMetaData)


class CoordinatorStatus(StrEnum):
    INITIALIZING = "INITIALIZING"
    INITIALIZING_FAILED = "INITIALIZING_FAILED"
    INITIALIZED = "INITIALIZED"

    HYDRATING = "HYDRATING"
    HYDRATING_FAILED = "HYDRATING_FAILED"
    HYDRATED = "HYDRATED"

    PROCESSING = "PROCESSING"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    PROCESSED = "PROCESSED"

    WAITING = "WAITING"

    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class CoordinatorMetaData(MetaData):
    cron_expression: str
    status: CoordinatorStatus = CoordinatorStatus.INITIALIZING
    next_schedule: datetime = Field(default_factory=datetime.now)
    initializing_started_at: datetime = Field(default_factory=datetime.now)
    initializing_stopped_at: datetime | None = None
    hydrating_started_at: datetime | None = None
    hydrating_stopped_at: datetime | None = None
    processing_started_at: datetime | None = None
    processing_stopped_at: datetime | None = None
    terminating_started_at: datetime | None = None
    terminating_stopped_at: datetime | None = None

    updated_at: datetime = Field(default_factory=datetime.now)
    log: list[str] = Field(default_factory=list)

    def update_log(self, message: str) -> Self:
        self.log.append(message)
        return self

    def update_status(self, status: CoordinatorStatus) -> Self:
        # When the terminating flag is set, only allow switch to terminated or to initializung
        if self.status == CoordinatorStatus.TERMINATING and status not in (
            CoordinatorStatus.INITIALIZING,
            CoordinatorStatus.TERMINATED,
        ):
            return self

        self.status = status
        timestamp = datetime.now()
        match status:
            case CoordinatorStatus.INITIALIZING_FAILED:
                self.initializing_stopped_at = timestamp
            case CoordinatorStatus.INITIALIZED:
                self.initializing_stopped_at = timestamp

            case CoordinatorStatus.HYDRATING:
                self.hydrating_started_at = timestamp
            case CoordinatorStatus.HYDRATING_FAILED:
                self.hydrating_stopped_at = timestamp
            case CoordinatorStatus.HYDRATED:
                self.hydrating_stopped_at = timestamp

            case CoordinatorStatus.PROCESSING:
                self.processing_started_at = timestamp
            case CoordinatorStatus.PROCESSING_FAILED:
                self.processing_stopped_at = timestamp
            case CoordinatorStatus.PROCESSED:
                self.processing_stopped_at = timestamp

            case CoordinatorStatus.WAITING:
                pass

            case CoordinatorStatus.TERMINATING:
                self.terminating_started_at = timestamp
            case CoordinatorStatus.TERMINATED:
                self.terminating_stopped_at = timestamp

        self.updated_at = timestamp
        return self

    def update_next_schedule(self) -> Self:
        self.next_schedule = croniter(self.cron_expression).next(datetime)
        return self

    def in_progress(self) -> bool:
        return self.status in (
            CoordinatorStatus.INITIALIZING,
            CoordinatorStatus.HYDRATING,
            CoordinatorStatus.PROCESSING,
        )

    def has_error(self) -> bool:
        return self.status in (
            CoordinatorStatus.INITIALIZING_FAILED,
            CoordinatorStatus.HYDRATING_FAILED,
            CoordinatorStatus.PROCESSING_FAILED,
        )

    def terminate(self) -> None:
        self.update_status(CoordinatorStatus.TERMINATING)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> Self:
        return cls.model_validate_json(data)


CoordinatorMetaDataType = TypeVar("CoordinatorMetaDataType", bound=CoordinatorMetaData)
