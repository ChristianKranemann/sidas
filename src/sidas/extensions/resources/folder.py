import io
from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import Iterator, Literal, Protocol, overload, runtime_checkable

import smart_open as so  # type: ignore

from .aws import AwsAccount

FolderResourceModeStr = Literal["r"] | Literal["w"]
FolderResourceModeBin = Literal["rb"] | Literal["wb"]
FolderResourceMode = FolderResourceModeStr | FolderResourceModeBin


@runtime_checkable
class FolderResource(Protocol):
    def full_path(self, path: PurePath) -> Path: ...

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeStr = "r"
    ) -> Iterator[io.TextIOWrapper]: ...

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeBin = "rb"
    ) -> Iterator[io.FileIO]: ...

    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper | io.FileIO]: ...

    def exists(self, path: PurePath) -> bool: ...


class InMemoryFolder(FolderResource):
    def __init__(self) -> None:
        self._files: dict[PurePath, io.TextIOWrapper] = {}

    def full_path(self, path: PurePath) -> Path:
        return Path(path)

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeStr = "r"
    ) -> Iterator[io.TextIOWrapper]: ...

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeBin = "rb"
    ) -> Iterator[io.FileIO]: ...

    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper | io.FileIO]:
        if path not in self._files:
            self._files[path] = io.TextIOWrapper(
                io.BytesIO(), encoding="utf-8", line_buffering=True
            )

        try:
            wrapper = self._files[path]
            wrapper.seek(0, 0)
            yield wrapper

        finally:
            pass

    def exists(self, path: PurePath) -> bool:
        return path in self._files.keys()


class LocalFolder(FolderResource):
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)

    def full_path(self, path: PurePath) -> Path:
        return Path(self.base_path, path)

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeStr = "r"
    ) -> Iterator[io.TextIOWrapper]: ...

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeBin = "rb"
    ) -> Iterator[io.FileIO]: ...

    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper | io.FileIO]:
        full_path = self.full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        yield so.open(full_path, mode)

    def exists(self, path: PurePath) -> bool:
        return self.full_path(path).is_file()


class S3Bucket(FolderResource):
    def __init__(
        self,
        account: AwsAccount,
        bucket: str,
    ) -> None:
        self.account = account
        self.bucket = bucket

    def full_path(self, path: PurePath) -> Path:
        return Path(self.bucket, path)

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeStr = "r"
    ) -> Iterator[io.TextIOWrapper]: ...

    @overload
    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceModeBin = "rb"
    ) -> Iterator[io.FileIO]: ...

    @contextmanager
    def open(
        self, path: PurePath, mode: FolderResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper | io.FileIO]:
        session = self.account.session()
        uri = f"s3://{self.full_path(path)}"
        yield so.open(
            uri,
            mode,
            transport_params={"client": session.client("s3")},
        )

    def exists(self, path: PurePath) -> bool:
        session = self.account.session()
        uri = f"s3://{self.full_path(path)}"

        try:
            with so.open(uri, transport_params={"client": session.client("s3")}):
                return True
        except ValueError:
            return False
