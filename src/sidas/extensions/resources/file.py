import io
from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import Iterator, Literal, Protocol, runtime_checkable

from smart_open import open  # type: ignore

from .aws import AwsAccount

FileResourceMode = Literal["r"] | Literal["w"] | Literal["rb"] | Literal["wb"]


@runtime_checkable
class FileResource(Protocol):
    @contextmanager
    def open(
        self, path: PurePath, mode: FileResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper]: ...

    def exists(self, path: PurePath) -> bool: ...


class InMemoryFile(FileResource):
    def __init__(self) -> None:
        self._files: dict[PurePath, io.TextIOWrapper] = {}

    @contextmanager
    def open(
        self, path: PurePath, mode: FileResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper]:
        self._files[path] = io.TextIOWrapper(
            io.BytesIO(), encoding="utf-8", newline="\n"
        )
        try:
            yield self._files[path]
        finally:
            self._files[path].close()

    def exists(self, path: PurePath) -> bool:
        return path in self._files.keys()


class LocalFile(FileResource):
    def __init__(self, base_path: str | Path, suffix: str = ".txt") -> None:
        self.base_path = Path(base_path)
        self.suffix = suffix

    def full_path(self, path: PurePath) -> Path:
        return Path(self.base_path, path.with_suffix(self.suffix))

    @contextmanager
    def open(
        self, path: PurePath, mode: FileResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper]:
        full_path = self.full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        yield open(full_path, mode)

    def exists(self, path: PurePath) -> bool:
        return self.full_path(path).is_file()


class S3File(FileResource):
    def __init__(
        self,
        account: AwsAccount,
        bucket: str,
    ) -> None:
        self.account = account
        self.bucket = bucket

    @contextmanager
    def open(
        self, path: PurePath, mode: FileResourceMode = "r"
    ) -> Iterator[io.TextIOWrapper]:
        session = self.account.session()

        url = f"s3://{self.bucket}/{path}"
        yield open(url, mode, transport_params={"client": session.client("s3")})
